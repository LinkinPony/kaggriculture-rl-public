"""PPO-primary training over synchronized Kaito route forks."""

from __future__ import annotations

import json
import random
import subprocess
import time
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import cast

import numpy as np
import torch

from kagg_revue.bc.dataset import sha256_file
from kagg_revue.core.backend import BackendApi, load_backend
from kagg_revue.core.provenance import source_identity
from kagg_revue.opponents.registry import trusted_runtime_identity
from kagg_revue.rl.routes.config import RoutePpoSettings
from kagg_revue.rl.routes.contract import (
    ROUTE_DECISIONS,
    ROUTE_FEATURE_VERSION,
    ROUTE_POLICY_VERSION,
)
from kagg_revue.rl.routes.features import ROUTE_FEATURE_WIDTH
from kagg_revue.rl.routes.learning import optimize_route_batch
from kagg_revue.rl.routes.model import RouteActorArchitecture, RouteActorCritic
from kagg_revue.rl.routes.rollout import (
    RouteGameResult,
    RouteJob,
    RouteRolloutBatch,
    RouteRolloutCollector,
)


def _git_revision(root: Path) -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _resolve(settings: RoutePpoSettings, root: Path) -> RoutePpoSettings:
    def path(value: Path) -> Path:
        return value.resolve() if value.is_absolute() else (root / value).resolve()

    return settings.model_copy(
        update={
            "output_dir": path(settings.output_dir),
            "public_agent_manifest": path(settings.public_agent_manifest),
        }
    )


def _artifact_identities(
    backend: BackendApi,
    settings: RoutePpoSettings,
) -> dict[str, str]:
    manifest = backend.load_public_agent_manifest(settings.public_agent_manifest)
    records = manifest.by_id()
    identities = {"public_agent_manifest": sha256_file(settings.public_agent_manifest)}
    for opponent_id in settings.opponents:
        record = records.get(opponent_id)
        if record is None:
            raise KeyError(f"route PPO opponent is absent from manifest: {opponent_id}")
        runtime = trusted_runtime_identity(record)
        if runtime is None:
            raise ValueError(f"route PPO opponent lacks a native port: {opponent_id}")
        identities[f"opponent:{opponent_id}:source"] = record.sha256
        identities[f"opponent:{opponent_id}:implementation"] = str(runtime["implementation"])
    native = cast(Mapping[str, object], backend.identity["native_module"])
    identities["native_extension"] = str(native["sha256"])
    identities["route_policy"] = ROUTE_POLICY_VERSION
    identities["route_features"] = ROUTE_FEATURE_VERSION
    return identities


def _architecture(settings: RoutePpoSettings) -> RouteActorArchitecture:
    return RouteActorArchitecture(
        feature_width=ROUTE_FEATURE_WIDTH,
        hidden_width=settings.model.hidden_width,
        feedforward_width=settings.model.feedforward_width,
        prior_logit=settings.model.prior_logit,
    )


def _jobs(
    settings: RoutePpoSettings,
    update: int,
    randomizer: random.Random,
    *,
    smoke: bool,
) -> tuple[RouteJob, ...]:
    seeds_per_update = min(4, settings.rollout.seeds_per_update) if smoke else (
        settings.rollout.seeds_per_update
    )
    first_seed = settings.rollout_seed_start + (update - 1) * settings.rollout.seeds_per_update
    weights = tuple(settings.opponent_weights.values())
    sampled = randomizer.choices(settings.opponents, weights=weights, k=seeds_per_update)
    return tuple(
        (first_seed + offset, seat, sampled[offset])
        for offset in range(seeds_per_update)
        for seat in (0, 1)
    )


def _wdl(rows: Sequence[RouteGameResult], *, direct: bool) -> dict[str, object]:
    values = [game.direct_outcome if direct else game.outcome for game in rows]
    return {
        "games": len(rows),
        "wins": sum(value > 0 for value in values),
        "ties": sum(value == 0 for value in values),
        "losses": sum(value < 0 for value in values),
    }


def _batch_metrics(batch: RouteRolloutBatch) -> dict[str, object]:
    games = batch.games
    route_names = {
        0: "default",
        **{value.route_index: value.route_name for value in ROUTE_DECISIONS},
    }
    paired = [game.outcome - game.direct_outcome for game in games]
    result: dict[str, object] = {
        "candidate": _wdl(games, direct=False),
        "direct_control": _wdl(games, direct=True),
        "paired_terminal_outcome": {
            "better": sum(value > 0 for value in paired),
            "same": sum(value == 0 for value in paired),
            "worse": sum(value < 0 for value in paired),
            "mean_residual": float(np.mean(batch.game_rewards)),
        },
        "mean_terminal_cash": float(np.mean([game.terminal_cash for game in games])),
        "mean_direct_terminal_cash": float(
            np.mean([game.direct_terminal_cash for game in games])
        ),
        "selected_routes": {
            route_names[index]: sum(game.selected_route == index for game in games)
            for index in sorted(route_names)
        },
        "decisions": int(batch.actions.size),
        "actor_decisions": int(np.sum(batch.actor_weights > 0.0)),
        "prior_agreement": float(np.mean(batch.actions == batch.prior_actions)),
        "switch_fraction": float(np.mean(batch.actions == 1)),
        "execution": batch.diagnostics,
    }
    result["opponents"] = {
        opponent: {
            "candidate": _wdl(
                tuple(game for game in games if game.opponent_id == opponent),
                direct=False,
            ),
            "direct_control": _wdl(
                tuple(game for game in games if game.opponent_id == opponent),
                direct=True,
            ),
        }
        for opponent in sorted({game.opponent_id for game in games})
    }
    return result


def _checkpoint_payload(
    model: RouteActorCritic,
    optimizer: torch.optim.Optimizer,
    settings: RoutePpoSettings,
    *,
    update: int,
    revision: str,
    source: Mapping[str, object],
    identities: Mapping[str, str],
    randomizer: random.Random,
    action_generator: torch.Generator,
    minibatch_generator: torch.Generator,
) -> dict[str, object]:
    return {
        "schema_version": "event-route-ppo-checkpoint-v1",
        "update": update,
        "architecture": model.architecture.record(),
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
        "settings_contract": settings.checkpoint_contract(),
        "source_revision": revision,
        "source": dict(source),
        "artifact_identities": dict(identities),
        "rng": {
            "python": randomizer.getstate(),
            "numpy": np.random.get_state(),
            "torch_cpu": torch.get_rng_state(),
            "torch_cuda": torch.cuda.get_rng_state_all(),
            "action_generator": action_generator.get_state(),
            "minibatch_generator": minibatch_generator.get_state(),
        },
    }


def _save_checkpoint(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    torch.save(dict(payload), temporary)
    temporary.replace(path)


def train_route_ppo(
    raw_settings: RoutePpoSettings,
    repository_root: Path,
    *,
    smoke: bool,
) -> dict[str, object]:
    """Train route PPO and preserve direct-outcome evidence and checkpoints."""
    root = repository_root.resolve()
    settings = _resolve(raw_settings, root)
    output_root = (root / "outputs").resolve()
    if not settings.output_dir.is_relative_to(output_root):
        raise ValueError("route PPO output escaped repository outputs/")
    if settings.output_dir.exists():
        raise FileExistsError(f"route PPO output already exists: {settings.output_dir}")
    device = torch.device(settings.device)
    if not torch.cuda.is_available():
        raise RuntimeError("route PPO requested CUDA but no GPU is available")
    torch.set_num_threads(settings.cpu_threads)
    random.seed(settings.seed)
    np.random.seed(settings.seed % (2**32))
    torch.manual_seed(settings.seed)
    torch.cuda.manual_seed_all(settings.seed)
    randomizer = random.Random(settings.seed + 1)
    action_generator = torch.Generator(device=device)
    action_generator.manual_seed(settings.seed + 2)
    minibatch_generator = torch.Generator(device=device)
    minibatch_generator.manual_seed(settings.seed + 3)

    backend = load_backend(root)
    resolved_environment = cast(
        dict[str, object],
        backend.engine(
            seed=settings.rollout_seed_start,
            configuration=settings.environment,
        ).configuration,
    )
    source = cast(Mapping[str, object], source_identity(root))
    revision = _git_revision(root)
    if not smoke and bool(source["worktree_dirty"]):
        raise RuntimeError("long route PPO training requires a clean committed revision")
    identities = _artifact_identities(backend, settings)
    model = RouteActorCritic(_architecture(settings)).to(device)
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=settings.optimization.learning_rate,
        weight_decay=settings.optimization.weight_decay,
    )
    collector = RouteRolloutCollector(
        backend,
        model,
        resolved_environment,
        unit_limit=settings.rollout.unit_limit,
        cpu_workers=settings.rollout.cpu_workers,
        action_generator=action_generator,
    )

    settings.output_dir.mkdir(parents=True)
    resolved_path = settings.output_dir / "resolved-settings.json"
    resolved_path.write_text(
        json.dumps(
            {
                "route_ppo": settings.model_dump(mode="json"),
                "resolved_environment": resolved_environment,
                "source": dict(source),
                "source_revision": revision,
                "artifact_identities": identities,
                "route_decisions": [
                    {
                        "step": value.step,
                        "route_index": value.route_index,
                        "route_name": value.route_name,
                    }
                    for value in ROUTE_DECISIONS
                ],
                "decision_surface": "complete official-rule terminal W/D/L",
                "reward": "same-job Kaito DIRECT terminal-W/D/L residual",
                "cash_role": "diagnostic only",
            },
            indent=2,
            sort_keys=True,
            default=str,
        ),
        encoding="utf-8",
    )
    initial = _checkpoint_payload(
        model,
        optimizer,
        settings,
        update=0,
        revision=revision,
        source=source,
        identities=identities,
        randomizer=randomizer,
        action_generator=action_generator,
        minibatch_generator=minibatch_generator,
    )
    _save_checkpoint(
        settings.output_dir / "checkpoints" / "permanent" / "checkpoint-00000000.pt",
        initial,
    )
    metrics_path = settings.output_dir / "metrics.jsonl"
    updates = min(2, settings.updates) if smoke else settings.updates
    started = time.perf_counter()
    last_metrics: dict[str, object] = {}
    for update in range(1, updates + 1):
        jobs = _jobs(settings, update, randomizer, smoke=smoke)
        rollout = collector.collect(jobs, sample=True)
        learning = optimize_route_batch(
            model,
            optimizer,
            rollout,
            settings.optimization,
            device=device,
            generator=minibatch_generator,
        )
        last_metrics = {
            "update": update,
            "elapsed_seconds": time.perf_counter() - started,
            "outcomes": _batch_metrics(rollout),
            "learning": learning,
        }
        with metrics_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(last_metrics, sort_keys=True) + "\n")
        print(json.dumps(last_metrics, sort_keys=True), flush=True)
        should_roll = update % settings.checkpoint.rolling_interval == 0
        should_preserve = (
            update % settings.checkpoint.permanent_interval == 0 or update == updates
        )
        if should_roll or should_preserve:
            payload = _checkpoint_payload(
                model,
                optimizer,
                settings,
                update=update,
                revision=revision,
                source=source,
                identities=identities,
                randomizer=randomizer,
                action_generator=action_generator,
                minibatch_generator=minibatch_generator,
            )
            if should_roll:
                _save_checkpoint(
                    settings.output_dir
                    / "checkpoints"
                    / "rolling"
                    / f"checkpoint-{update:08d}.pt",
                    payload,
                )
            if should_preserve:
                _save_checkpoint(
                    settings.output_dir
                    / "checkpoints"
                    / "permanent"
                    / f"checkpoint-{update:08d}.pt",
                    payload,
                )
    return {
        "status": "smoke_complete" if smoke else "complete",
        "updates": updates,
        "elapsed_seconds": time.perf_counter() - started,
        "output_dir": str(settings.output_dir),
        "last_metrics": last_metrics,
    }


__all__ = ["train_route_ppo"]
