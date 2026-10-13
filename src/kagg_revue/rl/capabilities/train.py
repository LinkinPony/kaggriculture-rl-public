"""Long-running terminal-W/D/L PPO over native capability candidates."""

from __future__ import annotations

import json
import random
import subprocess
import time
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, cast

import numpy as np
import torch

from kagg_revue.bc.dataset import sha256_file
from kagg_revue.core.backend import BackendApi, load_backend
from kagg_revue.core.provenance import source_identity
from kagg_revue.opponents.registry import trusted_runtime_identity
from kagg_revue.policy.capability import CapabilitySelector, CapabilitySelectorArchitecture
from kagg_revue.rl.capabilities.checkpoint import (
    CapabilityCheckpointStore,
    build_capability_checkpoint,
    capture_capability_rng_state,
    restore_capability_checkpoint,
)
from kagg_revue.rl.capabilities.config import CapabilityRlSettings
from kagg_revue.rl.capabilities.data import TensorCapabilityRolloutBatch
from kagg_revue.rl.capabilities.learning import optimize_capability_batch
from kagg_revue.rl.capabilities.rollout import (
    CapabilityGameResult,
    CapabilityRolloutCollector,
)
from kagg_revue.rl.capabilities.search import FrozenTargetSearch


def _git_revision(root: Path) -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _resolve_settings(settings: CapabilityRlSettings, root: Path) -> CapabilityRlSettings:
    def resolve(path: Path) -> Path:
        return path.resolve() if path.is_absolute() else (root / path).resolve()

    return settings.model_copy(
        update={
            "resume_checkpoint": (
                resolve(settings.resume_checkpoint)
                if settings.resume_checkpoint is not None
                else None
            ),
            "public_agent_manifest": resolve(settings.public_agent_manifest),
            "output_dir": resolve(settings.output_dir),
        }
    )


def _validate_native_abi(backend: BackendApi, settings: CapabilityRlSettings) -> dict[str, Any]:
    spec = cast(dict[str, Any], backend.capability_spec())
    expected = {
        "version": settings.abi.version,
        "integer_field_count": settings.abi.integer_fields,
        "float_field_count": settings.abi.edit_value_features,
        "candidate_feature_count": settings.abi.candidate_features,
        "root_feature_count": settings.abi.root_features,
        "integer_vocab_sizes": settings.abi.integer_vocab_sizes,
    }
    actual = {
        "version": int(spec["version"]),
        "integer_field_count": int(spec["integer_field_count"]),
        "float_field_count": int(spec["float_field_count"]),
        "candidate_feature_count": int(spec["candidate_feature_count"]),
        "root_feature_count": int(spec["root_feature_count"]),
        "integer_vocab_sizes": tuple(int(value) for value in spec["integer_vocab_sizes"]),
    }
    if actual != expected:
        raise ValueError(f"resolved native capability ABI differs: {actual} != {expected}")
    return spec


def _artifact_identities(
    backend: BackendApi,
    settings: CapabilityRlSettings,
) -> dict[str, str]:
    manifest = backend.load_public_agent_manifest(settings.public_agent_manifest)
    records = manifest.by_id()
    identities = {"public_agent_manifest": sha256_file(settings.public_agent_manifest)}
    for opponent_id in settings.opponents:
        record = records.get(opponent_id)
        if record is None:
            raise KeyError(f"capability opponent is absent from manifest: {opponent_id}")
        runtime = trusted_runtime_identity(record)
        if runtime is None:
            raise ValueError(
                f"capability opponent lacks an authenticated native port: {opponent_id}"
            )
        identities[f"opponent:{opponent_id}:source"] = record.sha256
        identities[f"opponent:{opponent_id}:implementation"] = str(runtime["implementation"])
    native = cast(Mapping[str, object], backend.identity["native_module"])
    identities["native_extension"] = str(native["sha256"])
    identities["capability_contract"] = settings.versions.contract().fingerprint
    return identities


def _architecture(settings: CapabilityRlSettings) -> CapabilitySelectorArchitecture:
    return CapabilitySelectorArchitecture(
        state_width=settings.abi.root_features,
        model_width=settings.model.model_width,
        feedforward_width=settings.model.feedforward_width,
        mode_tokens=settings.abi.mode_tokens,
        integer_vocab_sizes=settings.abi.integer_vocab_sizes,
        edit_value_features=settings.abi.edit_value_features,
        candidate_features=settings.abi.candidate_features,
        search_features=settings.abi.search_features,
        initial_search_gate=settings.model.initial_search_gate,
        search_logit_limit=settings.model.search_logit_limit,
    )


def _outcome_metrics(games: Sequence[CapabilityGameResult]) -> dict[str, object]:
    result: dict[str, object] = {}
    for opponent_id in sorted({game.opponent_id for game in games}):
        rows = [game for game in games if game.opponent_id == opponent_id]
        result[opponent_id] = {
            "games": len(rows),
            "wins": sum(game.outcome > 0 for game in rows),
            "ties": sum(game.outcome == 0 for game in rows),
            "losses": sum(game.outcome < 0 for game in rows),
            "win_rate": sum(game.outcome > 0 for game in rows) / len(rows),
            "mean_terminal_cash": float(np.mean([game.terminal_cash for game in rows])),
            "mean_cash_difference": float(
                np.mean([game.terminal_cash - game.opponent_cash for game in rows])
            ),
        }
    outcomes = [game.outcome for game in games]
    result["overall"] = {
        "games": len(games),
        "wins": sum(outcome > 0 for outcome in outcomes),
        "ties": sum(outcome == 0 for outcome in outcomes),
        "losses": sum(outcome < 0 for outcome in outcomes),
        "win_rate": sum(outcome > 0 for outcome in outcomes) / len(outcomes),
    }
    return result


def _prepare_output(settings: CapabilityRlSettings, root: Path) -> None:
    output_root = (root / "outputs").resolve()
    if not settings.output_dir.is_relative_to(output_root):
        raise ValueError("capability training output must remain under repository outputs/")
    if settings.output_dir.exists():
        raise FileExistsError(f"capability training output already exists: {settings.output_dir}")
    settings.output_dir.mkdir(parents=True)


def _batch_bytes(batch: TensorCapabilityRolloutBatch) -> int:
    tensors: tuple[torch.Tensor, ...] = (
        batch.root_features,
        batch.mode,
        batch.int_fields,
        batch.edit_values,
        batch.edit_counts,
        batch.edit_mask,
        batch.candidate_features,
        batch.candidate_mask,
        batch.search_logits,
        batch.search_features,
        batch.selected_indices,
        batch.old_joint_log_probability,
        batch.old_values,
        batch.behavior_factor_counts,
        batch.episode_index,
        batch.start_steps,
        batch.durations,
        batch.outcomes,
    )
    if batch.direct_outcomes is not None:
        tensors += (batch.direct_outcomes,)
    return sum(tensor.numel() * tensor.element_size() for tensor in tensors)


def train_capability(
    raw_settings: CapabilityRlSettings,
    repository_root: Path,
    *,
    smoke: bool,
) -> dict[str, object]:
    """Train one immutable capability selector and return its final status."""
    root = repository_root.resolve()
    settings = _resolve_settings(raw_settings, root)
    if len(settings.devices) != 1:
        raise ValueError("capability v1 trainer currently requires exactly one CUDA device")
    device = torch.device(settings.devices[0])
    torch.set_num_threads(settings.cpu_threads)
    random.seed(settings.seed)
    np.random.seed(settings.seed % (2**32))
    torch.manual_seed(settings.seed)
    torch.cuda.manual_seed_all(settings.seed)
    randomizer = random.Random(settings.seed + 1)
    numpy_generator = np.random.default_rng(settings.seed + 2)
    action_generator = torch.Generator(device=device)
    action_generator.manual_seed(settings.seed + 3)
    torch_generators = {"capability_action": action_generator}

    backend = load_backend(root)
    native_spec = _validate_native_abi(backend, settings)
    resolved_environment = cast(
        dict[str, object],
        backend.engine(seed=0, configuration=settings.environment).configuration,
    )
    identities = _artifact_identities(backend, settings)
    source = source_identity(root)
    revision = _git_revision(root)
    if not smoke and bool(source["worktree_dirty"]):
        raise RuntimeError("long capability training requires a clean committed source revision")

    model = CapabilitySelector(_architecture(settings)).to(device)
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=settings.optimization.learning_rate,
        weight_decay=settings.optimization.weight_decay,
    )
    search = FrozenTargetSearch(
        model,
        candidate_value_scale=settings.search.candidate_value_scale,
        replay_prior_logit=settings.search.replay_prior_logit,
    )
    start_update = 1
    target_update = 0
    resume: dict[str, object] | None = None
    if settings.resume_checkpoint is not None:
        restored = restore_capability_checkpoint(
            settings.resume_checkpoint,
            model,
            search.target,
            optimizer,
            settings,
            source_revision=revision,
            artifact_identities=identities,
            randomizer=randomizer,
            numpy_generator=numpy_generator,
            torch_generators=torch_generators,
            devices=(device,),
        )
        start_update = restored.start_update
        target_update = restored.target_update
        resume = restored.checkpoint

    _prepare_output(settings, root)
    resolved_path = settings.output_dir / "resolved-settings.json"
    resolved_path.write_text(
        json.dumps(
            {
                "capability_rl": settings.model_dump(mode="json"),
                "resolved_environment": resolved_environment,
                "native_capability_spec": native_spec,
                "source": source,
                "artifact_identities": identities,
                "resume": resume,
                "decision_surface": "complete official-rule terminal W/D/L",
                "cash_role": "diagnostic only",
            },
            indent=2,
            sort_keys=True,
            default=str,
        ),
        encoding="utf-8",
    )
    checkpoint_store = CapabilityCheckpointStore(settings.output_dir, settings.checkpoint)
    if resume is None:
        initial_rng = capture_capability_rng_state(
            randomizer,
            numpy_generator,
            torch_generators,
            devices=(device,),
        )
        initial_payload = build_capability_checkpoint(
            model,
            search.target,
            optimizer,
            completed_update=0,
            target_update=0,
            settings=settings,
            source_revision=revision,
            artifact_identities=identities,
            rng_state=initial_rng,
        )
        checkpoint_store.publish(0, initial_payload, final=False)

    collector = CapabilityRolloutCollector(
        backend,
        model,
        search,
        resolved_environment,
        settings.opponent_weights,
        settings.versions.contract(),
        max_candidates=settings.abi.max_candidates,
        max_edits=settings.abi.max_edits,
        cpu_workers=settings.rollout.cpu_workers,
        device=device,
        sampling_seed=settings.seed + 4,
        action_generator=action_generator,
        behavior_exploration_epsilon=(settings.search.behavior_exploration_epsilon),
        collect_direct_control=(
            settings.objective.reward
            in {"paired_direct_terminal_wdl", "paired_direct_residual_wdl"}
        ),
    )
    metrics_path = settings.output_dir / "metrics.jsonl"
    effective_final_update = min(settings.updates, start_update if smoke else settings.updates)
    seed_count = (
        min(16, settings.rollout.seeds_per_update) if smoke else settings.rollout.seeds_per_update
    )
    latest: dict[str, object] | None = None
    training_started = time.perf_counter()
    for update in range(start_update, effective_final_update + 1):
        first_seed = settings.rollout_seed_start + (update - 1) * settings.rollout.seeds_per_update
        seeds = tuple(range(first_seed, first_seed + seed_count))
        rollout = collector.collect(seeds, update=update)
        if not smoke and len(rollout.games) != settings.rollout.batch_games:
            raise RuntimeError("resolved capability game batch differs from the profile")
        if len(rollout.games) > settings.rollout.inference_batch_size:
            raise RuntimeError("capability inference batch capacity is smaller than rollout games")
        host_bytes = _batch_bytes(rollout.batch)
        host_limit = int(settings.rollout.host_memory_limit_gib * 1024**3)
        if host_bytes > host_limit:
            raise MemoryError("capability rollout batch exceeds configured host memory")
        free_gpu, _total_gpu = torch.cuda.mem_get_info(device)
        if host_bytes > int(free_gpu * settings.rollout.gpu_memory_fraction):
            raise MemoryError("capability PPO batch exceeds configured free GPU fraction")
        device_batch = rollout.batch.to(device)
        optimized = optimize_capability_batch(
            model,
            optimizer,
            device_batch,
            settings,
            randomizer,
        )
        if update % settings.search.target_sync_interval == 0:
            search.synchronize(model)
            target_update = update

        selected_modes = device_batch.mode.gather(
            1,
            device_batch.selected_indices[:, None],
        ).squeeze(1)
        row: dict[str, object] = {
            "update": update,
            "rollout_seed_start": first_seed,
            "source_revision": revision,
            "version_contract": settings.versions.contract().fingerprint,
            "outcomes": _outcome_metrics(rollout.games),
            "rollout": rollout.diagnostics,
            "optimization": optimized,
            "search": {
                "target_update": target_update,
                "behavior_exploration_epsilon": (settings.search.behavior_exploration_epsilon),
                "selected_direct_fraction": float((selected_modes == 0).float().mean()),
                "selected_mode_fraction": {
                    str(mode): float((selected_modes == mode).float().mean())
                    for mode in range(settings.abi.mode_tokens)
                },
            },
            "batch": {
                "episodes": device_batch.episodes,
                "macro_decisions": device_batch.decisions,
                "host_bytes": host_bytes,
            },
            "elapsed_seconds": time.perf_counter() - training_started,
        }
        final = update == effective_final_update
        checkpoint_record: dict[str, object] | None = None
        if checkpoint_store.due(update, final=final):
            rng_state = capture_capability_rng_state(
                randomizer,
                numpy_generator,
                torch_generators,
                devices=(device,),
            )
            payload = build_capability_checkpoint(
                model,
                search.target,
                optimizer,
                completed_update=update,
                target_update=target_update,
                settings=settings,
                source_revision=revision,
                artifact_identities=identities,
                rng_state=rng_state,
            )
            checkpoint_record = checkpoint_store.publish(update, payload, final=final)
        row["checkpoint"] = checkpoint_record
        with metrics_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(row, sort_keys=True) + "\n")
            stream.flush()
        status_path = settings.output_dir / "run-status.json"
        temporary_status = status_path.with_suffix(".json.tmp")
        temporary_status.write_text(
            json.dumps(
                {
                    "status": "complete" if final else "running",
                    "latest": row,
                },
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        temporary_status.replace(status_path)
        latest = row
        print(json.dumps(row, sort_keys=True), flush=True)

    report = {
        "status": "smoke_complete" if smoke else "training_complete",
        "completed_update": None if latest is None else latest["update"],
        "output_dir": str(settings.output_dir),
        "source_revision": revision,
        "latest": latest,
    }
    (settings.output_dir / "training-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    return report


__all__ = ["train_capability"]
