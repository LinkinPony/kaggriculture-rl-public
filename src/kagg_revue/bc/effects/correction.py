"""Generate Rank8 supervision on complete frozen-student effect rollouts."""

from __future__ import annotations

import hashlib
import shutil
import time
from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import numpy as np
import orjson
import torch

from kagg_revue.bc.dataset import sha256_file
from kagg_revue.bc.effects.config import EffectCorrectionDataSettings
from kagg_revue.bc.effects.correction_observer import (
    Rank8EffectCorrectionObserver,
)
from kagg_revue.bc.effects.dataset import (
    EffectTeacherManifest,
    EffectTeacherShard,
    pack_effect_teacher_arrays,
)
from kagg_revue.core.backend import load_backend
from kagg_revue.core.provenance import source_identity
from kagg_revue.policy.effects.contract import NativeEffectContract
from kagg_revue.rl.effects.checkpoint import load_checkpoint
from kagg_revue.rl.effects.population import effect_opponent_identities
from kagg_revue.rl.effects.rollout import EffectRolloutCollector
from kagg_revue.teacher.npz import write_compressed_npz
from kagg_revue.teacher.submission import load_submission_teacher


def _integer(values: Mapping[str, object], name: str) -> int:
    value = values.get(name)
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"effect correction environment {name} must be an integer")
    return value


def _write_json(path: Path, value: Mapping[str, object]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(
        orjson.dumps(value, option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS)
    )
    temporary.replace(path)


def _resolved(
    settings: EffectCorrectionDataSettings,
    root: Path,
) -> EffectCorrectionDataSettings:
    return settings.model_copy(
        update={
            "teacher": settings.teacher.model_copy(
                update={"archive_path": (root / settings.teacher.archive_path).resolve()}
            ),
            "student_checkpoint": (root / settings.student_checkpoint).resolve(),
            "public_agent_manifest": (
                root / settings.public_agent_manifest
            ).resolve(),
            "output_dir": (root / settings.output_dir).resolve(),
            "report_dir": (root / settings.report_dir).resolve(),
        }
    )


def _relative_settings(
    settings: EffectCorrectionDataSettings,
    root: Path,
) -> dict[str, object]:
    result = settings.model_dump(mode="json")
    for name in (
        "student_checkpoint",
        "public_agent_manifest",
        "output_dir",
        "report_dir",
    ):
        result[name] = str(Path(cast(str, result[name])).relative_to(root))
    teacher = cast(dict[str, object], result["teacher"])
    teacher["archive_path"] = str(settings.teacher.archive_path.relative_to(root))
    return result


def _route_codes(artifact: Any) -> dict[str, int]:
    route_ids = [artifact.route.default_route_id]
    route_ids.extend(branch.route_id for branch in artifact.route.branches)
    result = {route_id: index for index, route_id in enumerate(route_ids)}
    if len(result) > 256:
        raise ValueError("effect correction route vocabulary exceeds uint8 storage")
    return result


def _student_base_arrays(
    result: Any,
    *,
    seed: int,
    episode_start: int,
    route_ids: Sequence[str],
    event_days: Sequence[int],
    route_codes: Mapping[str, int],
    bucket_widths: np.ndarray[Any, np.dtype[np.int32]],
) -> dict[str, np.ndarray[Any, np.dtype[Any]]]:
    batch = result.batch
    episode_stop = episode_start + 2
    games = result.games[episode_start:episode_stop]
    if episode_stop > batch.episode_count or len(games) != 2:
        raise RuntimeError("effect correction seed escaped its rollout batch")
    if tuple((game.seed, game.seat) for game in games) != ((seed, 0), (seed, 1)):
        raise RuntimeError("effect correction paired-seat order changed")
    return {
        "board": batch.board[episode_start:episode_stop].numpy(),
        "units": batch.units[episode_start:episode_stop].numpy(),
        "global_features": batch.global_features[episode_start:episode_stop].numpy(),
        "economic_state": batch.economic_state[episode_start:episode_stop].numpy(),
        "actions": batch.actions[episode_start:episode_stop].numpy(),
        "quantities": batch.quantities[episode_start:episode_stop].numpy(),
        "decision_counts": batch.decision_mask[
            episode_start:episode_stop
        ].sum(dim=-1).numpy(),
        "outcomes": batch.outcomes[episode_start:episode_stop].numpy(),
        "seeds": np.asarray([seed, seed], dtype=np.int64),
        "seats": np.asarray([0, 1], dtype=np.uint8),
        "terminal_cash": np.asarray(
            [game.terminal_cash for game in games],
            dtype=np.float64,
        ),
        "opponent_cash": np.asarray(
            [game.opponent_cash for game in games],
            dtype=np.float64,
        ),
        "route_codes": np.asarray(
            [route_codes[route_id] for route_id in route_ids],
            dtype=np.uint8,
        ),
        "first_event_days": np.asarray(event_days, dtype=np.int16),
        "bucket_widths": bucket_widths,
    }


def _episode_decisions(
    buckets: Sequence[Mapping[str, Any]],
    episode_start: int,
) -> list[dict[str, Any]]:
    """Extract one paired seed while retaining native width buckets."""
    episode_stop = episode_start + 2
    result: list[dict[str, Any]] = []
    for payload in buckets:
        episodes = np.asarray(payload["episode_index"], dtype=np.int64)
        rows = (episodes >= episode_start) & (episodes < episode_stop)
        if not bool(rows.any()):
            continue
        selected: dict[str, Any] = {}
        for name, raw in payload.items():
            values = np.asarray(raw)
            if values.ndim < 1 or values.shape[0] != episodes.shape[0]:
                raise ValueError("effect correction bucket field rows do not align")
            selected[name] = values[rows].copy()
        selected["episode_index"] -= episode_start
        result.append(selected)
    if not result:
        raise RuntimeError("effect correction paired seed has no factor rows")
    return result


def _transaction_maximum(
    decisions: Sequence[Mapping[str, Any]],
    turns: int,
) -> int:
    episodes = np.concatenate(
        [np.asarray(payload["episode_index"], dtype=np.int64) for payload in decisions]
    )
    turn_indices = np.concatenate(
        [np.asarray(payload["turn_index"], dtype=np.int64) for payload in decisions]
    )
    keys = episodes * turns + turn_indices
    counts = np.bincount(keys, minlength=2 * turns)
    return int(counts.max(initial=0))


def _teacher_identity(
    settings: EffectCorrectionDataSettings,
    root: Path,
    artifact: Any,
) -> dict[str, object]:
    identity = artifact.identity()
    identity["archive_path"] = str(settings.teacher.archive_path.relative_to(root))
    return {
        **identity,
        "submission_id": settings.teacher.submission_id,
        "submission_record_commit": settings.submission_record_commit,
        "event_shop": artifact.route.event_shop,
        "default_route_id": artifact.route.default_route_id,
        "default_support": artifact.route.default_support,
        "branches": [
            {
                "route_id": branch.route_id,
                "first_event_day": branch.first_event_day,
                "activation_step": branch.activation_step,
                "support": branch.support,
            }
            for branch in artifact.route.branches
        ],
        "route_source": artifact.route.source,
        "causality": "current student-visited actor observation and prefix only",
    }


def prepare_effect_corrections(
    raw_settings: EffectCorrectionDataSettings,
    repository_root: Path,
    *,
    smoke: bool = False,
) -> dict[str, object]:
    """Generate compact DAgger labels from paired external-opponent matches."""
    root = repository_root.resolve()
    settings = _resolved(raw_settings, root)
    if smoke:
        settings = settings.model_copy(
            update={
                "output_dir": settings.output_dir.with_name(
                    f"{settings.output_dir.name}-smoke"
                ),
                "report_dir": settings.report_dir.with_name(
                    f"{settings.report_dir.name}-smoke"
                ),
                "seeds": 1,
                "batch_seeds": 1,
            }
        )
    data_root = (root / "data" / "external").resolve()
    output_root = (root / "outputs").resolve()
    if not settings.teacher.archive_path.is_relative_to(data_root):
        raise ValueError("effect correction teacher archive escaped data/external/")
    if not settings.public_agent_manifest.is_relative_to(data_root):
        raise ValueError("effect correction public manifest escaped data/external/")
    if not settings.student_checkpoint.is_relative_to(output_root):
        raise ValueError("effect correction student checkpoint escaped outputs/")
    if not settings.output_dir.is_relative_to(data_root):
        raise ValueError("effect correction dataset escaped data/external/")
    if not settings.report_dir.is_relative_to(output_root):
        raise ValueError("effect correction report escaped outputs/")
    if settings.output_dir.exists() or settings.report_dir.exists():
        raise FileExistsError("effect correction output or report already exists")
    if not settings.student_checkpoint.is_file():
        raise FileNotFoundError("effect correction student checkpoint is absent")
    source = source_identity(root)
    if bool(source["worktree_dirty"]) and not smoke:
        raise RuntimeError("effect correction production data requires a clean revision")

    backend = load_backend(root)
    engine = backend.engine(settings.seed_start, dict(settings.environment))
    environment = cast(dict[str, object], dict(engine.configuration))
    raw_contract = backend.effect_policy_spec()
    if not isinstance(raw_contract, Mapping):
        raise TypeError("effect correction native specification is invalid")
    contract = NativeEffectContract.from_spec(
        raw_contract,
        board_size=_integer(environment, "boardSize"),
    )
    device = torch.device(settings.device)
    if device.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("effect correction requested CUDA without a GPU")
    model, checkpoint_metadata = load_checkpoint(
        settings.student_checkpoint,
        contract,
        device,
    )
    architecture = model.effects.architecture
    if architecture.state_position_encoding != "canonical_group_v2":
        raise ValueError("effect correction requires canonical group positions")
    if model.actor.architecture.unit_shape[1] != settings.unit_limit:
        raise ValueError("effect correction unit limit differs from its checkpoint")
    artifact = load_submission_teacher(
        settings.teacher.archive_path,
        settings.teacher.archive_sha256,
        settings.teacher.source_commit,
        settings.teacher.route_sha256,
    )
    actor_spec = cast(Mapping[str, object], backend.actor_encoder_spec())
    codec_spec = cast(Mapping[str, object], backend.action_codec_spec())
    item_names = cast(Sequence[object], actor_spec["item_names"])
    route_codes = _route_codes(artifact)
    opponent_weights = {name: 1.0 for name in settings.opponents}
    opponent_identities = effect_opponent_identities(
        backend,
        root,
        opponent_weights,
        settings.public_agent_manifest.relative_to(root),
    )
    observer = Rank8EffectCorrectionObserver(artifact, raw_contract, item_names)
    generator = torch.Generator(device=device).manual_seed(settings.seed_start)
    collector = EffectRolloutCollector(
        backend,
        model,
        contract,
        environment,
        unit_limit=settings.unit_limit,
        cpu_workers=settings.cpu_workers,
        device=device,
        action_generator=generator,
        maximum_graph_variants=settings.maximum_graph_variants,
        sample_actions=False,
        observer=observer,
        retain_behavior_distributions=False,
    )

    staging_data = settings.output_dir.with_name(settings.output_dir.name + ".incomplete")
    staging_report = settings.report_dir.with_name(
        settings.report_dir.name + ".incomplete"
    )
    if staging_data.exists() or staging_report.exists():
        raise FileExistsError("incomplete effect correction generation already exists")
    staging_data.mkdir(parents=True)
    staging_report.mkdir(parents=True)
    resolved = _relative_settings(settings, root)
    _write_json(
        staging_report / "resolved-settings.json",
        {"effect_correction_data": resolved},
    )
    records: list[EffectTeacherShard] = []
    label_counts: Counter[str] = Counter()
    route_counts: Counter[str] = Counter()
    opponent_counts: Counter[str] = Counter()
    started = time.perf_counter()
    try:
        for first in range(0, settings.seeds, settings.batch_seeds):
            batch_seeds = tuple(
                range(
                    settings.seed_start + first,
                    settings.seed_start + first + settings.batch_seeds,
                )
            )
            opponents = tuple(
                settings.opponents[(first + offset) % len(settings.opponents)]
                for offset in range(settings.batch_seeds)
            )
            jobs = tuple(
                (seed, seat, opponent)
                for seed, opponent in zip(batch_seeds, opponents, strict=True)
                for seat in (0, 1)
            )
            rollout = collector.collect_jobs(jobs)
            labels = observer.take_labels()
            if labels.keys != tuple((seed, seat) for seed in batch_seeds for seat in (0, 1)):
                raise RuntimeError("effect correction observer changed paired-seat order")
            label_counts.update(labels.statistics)
            route_counts.update(labels.route_ids)
            for local, (seed, opponent) in enumerate(
                zip(batch_seeds, opponents, strict=True)
            ):
                index = first + local
                episode_start = 2 * local
                episode_stop = episode_start + 2
                decisions = _episode_decisions(labels.buckets, episode_start)
                widths = np.asarray(
                    [
                        np.asarray(payload["candidate_fields"]).shape[1]
                        for payload in decisions
                    ],
                    dtype=np.int32,
                )
                arrays = pack_effect_teacher_arrays(
                    base=_student_base_arrays(
                        rollout,
                        seed=seed,
                        episode_start=episode_start,
                        route_ids=labels.route_ids[episode_start:episode_stop],
                        event_days=labels.first_event_days[
                            episode_start:episode_stop
                        ],
                        route_codes=route_codes,
                        bucket_widths=widths,
                    ),
                    decisions=decisions,
                )
                path = staging_data / f"effect-{index:05d}.npz"
                write_compressed_npz(path, arrays, settings.compression_level)
                outcomes = rollout.batch.outcomes[episode_start:episode_stop].numpy()
                games = rollout.games[episode_start:episode_stop]
                terminal = np.asarray(
                    [game.terminal_cash for game in games], dtype=np.float64
                )
                opponent_cash = np.asarray(
                    [game.opponent_cash for game in games], dtype=np.float64
                )
                factors = sum(
                    int(np.asarray(payload["selected"]).shape[0])
                    for payload in decisions
                )
                policy_factors = sum(
                    int(np.count_nonzero(payload["policy_mask"]))
                    for payload in decisions
                )
                turns = int(rollout.batch.board.shape[1])
                records.append(
                    EffectTeacherShard(
                        index=index,
                        path=path.name,
                        seed_start=seed,
                        games=1,
                        physical_games=2,
                        episodes=2,
                        turns_per_episode=turns,
                        factors=factors,
                        policy_factors=policy_factors,
                        maximum_transaction_steps=_transaction_maximum(
                            decisions,
                            turns,
                        ),
                        bucket_widths=tuple(int(value) for value in widths),
                        terminal_cash_sum=float(terminal.sum()),
                        opponent_cash_sum=float(opponent_cash.sum()),
                        better=int(np.count_nonzero(outcomes > 0)),
                        ties=int(np.count_nonzero(outcomes == 0)),
                        worse=int(np.count_nonzero(outcomes < 0)),
                        size_bytes=path.stat().st_size,
                        sha256=sha256_file(path),
                    )
                )
                opponent_counts[opponent] += 2
            print(
                orjson.dumps(
                    {
                        "completed_seeds": first + len(batch_seeds),
                        "seeds": settings.seeds,
                        "opponent": opponent,
                        "elapsed_seconds": time.perf_counter() - started,
                        "labels": label_counts["labels"],
                        "student_agreements": label_counts["student_agreements"],
                    }
                ).decode(),
                flush=True,
            )
        effect_spec_sha256 = hashlib.sha256(
            orjson.dumps(raw_contract, option=orjson.OPT_SORT_KEYS)
        ).hexdigest()
        checkpoint_identity = cast(
            Mapping[str, object], checkpoint_metadata["checkpoint_identity"]
        )
        teacher_identity = _teacher_identity(settings, root, artifact)
        seed_digest = hashlib.sha256()
        for seed in range(settings.seed_start, settings.seed_start + settings.seeds):
            seed_digest.update(seed.to_bytes(8, "little", signed=False))
        manifest: dict[str, object] = {
            "schema_version": "atomic-effect-teacher-dataset-v1",
            "source": dict(source),
            "native_backend": dict(backend.identity),
            "teacher": {
                **teacher_identity,
                "labeling": "rank8_on_turn_prefix_consistent_student_states_v3",
                "student_checkpoint": dict(checkpoint_identity),
                "student_training_source": checkpoint_metadata.get("source_revision"),
                "opponents": opponent_identities,
            },
            "effect_abi_version": contract.version,
            "effect_spec_sha256": effect_spec_sha256,
            "actor_encoder_version": str(actor_spec["version"]),
            "action_codec_version": str(codec_spec["version"]),
            "unit_limit": settings.unit_limit,
            "maximum_quantity": model.actor.architecture.maximum_quantity,
            "environment": environment,
            "collection": {
                "policy_pairing": (
                    "greedy frozen student in paired seats against round-robin frozen "
                    "authenticated opponents"
                ),
                "seed_start": settings.seed_start,
                "games": settings.seeds,
                "physical_games": 2 * settings.seeds,
                "seed_sequence_sha256": seed_digest.hexdigest(),
                "opponent_schedule": "stable round robin in configured order",
                "label_surface": "student-visited dynamic native atomic-effect candidates",
                "official_history": "actions actually compiled from greedy student choices",
                "hindsight_oracle_used": False,
                "translation": (
                    "Rank8 intent queried before each student turn; work labels choose the "
                    "earliest still-legal planned unit effect and market labels use the "
                    "student's actual slot prefix; policy supervision in each official "
                    "turn ends after the first student disagreement across work or market"
                ),
            },
            "route_codes": route_codes,
            "shards": [record.model_dump(mode="json") for record in records],
        }
        manifest["dataset_id"] = hashlib.sha256(
            orjson.dumps(manifest, option=orjson.OPT_SORT_KEYS)
        ).hexdigest()
        manifest["generated_at"] = datetime.now(UTC).isoformat()
        EffectTeacherManifest.model_validate(manifest)
        _write_json(staging_data / "manifest.json", manifest)
        elapsed = time.perf_counter() - started
        outcome_counts = Counter(
            outcome
            for record in records
            for outcome, count in ((1, record.better), (0, record.ties), (-1, record.worse))
            for _ in range(count)
        )
        report: dict[str, object] = {
            "schema_version": "atomic-effect-correction-report-v1",
            "generated_at": datetime.now(UTC).isoformat(),
            "status": "complete",
            "source": dict(source),
            "dataset_id": manifest["dataset_id"],
            "student_checkpoint": dict(checkpoint_identity),
            "seeds": settings.seeds,
            "physical_games": 2 * settings.seeds,
            "factors": sum(record.factors for record in records),
            "student_outcomes": {
                "wins": outcome_counts[1],
                "ties": outcome_counts[0],
                "losses": outcome_counts[-1],
            },
            "labels": {
                **dict(label_counts),
                "agreement_rate": label_counts["student_agreements"]
                / max(1, label_counts["labels"]),
            },
            "coverage": {
                "opponents": dict(sorted(opponent_counts.items())),
                "routes": dict(sorted(route_counts.items())),
            },
            "execution": {
                "device": str(device),
                "elapsed_seconds": elapsed,
                "physical_games_per_second": 2 * settings.seeds / elapsed,
                "compressed_bytes": sum(record.size_bytes for record in records),
            },
        }
        _write_json(staging_report / "generation-report.json", report)
        settings.output_dir.parent.mkdir(parents=True, exist_ok=True)
        settings.report_dir.parent.mkdir(parents=True, exist_ok=True)
        staging_data.replace(settings.output_dir)
        staging_report.replace(settings.report_dir)
        return {
            "dataset_dir": str(settings.output_dir),
            "dataset_id": manifest["dataset_id"],
            "manifest_sha256": sha256_file(settings.output_dir / "manifest.json"),
            "report_dir": str(settings.report_dir),
            "seeds": settings.seeds,
            "factors": report["factors"],
            "student_agreement_rate": cast(Mapping[str, object], report["labels"])[
                "agreement_rate"
            ],
        }
    except BaseException:
        shutil.rmtree(staging_data, ignore_errors=True)
        shutil.rmtree(staging_report, ignore_errors=True)
        raise
    finally:
        collector.close()


__all__ = ["prepare_effect_corrections"]
