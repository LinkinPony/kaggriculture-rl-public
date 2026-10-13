"""Frozen complete-match evaluation for capability checkpoints."""

from __future__ import annotations

import argparse
import gc
import json
import time
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import cast

import numpy as np
import torch
from torch import Tensor

from kagg_revue.bc.dataset import sha256_file
from kagg_revue.core.backend import load_backend
from kagg_revue.core.provenance import source_identity
from kagg_revue.policy.capability import (
    CapabilitySelector,
    CapabilitySelectorArchitecture,
)
from kagg_revue.rl.capabilities.checkpoint import CAPABILITY_CHECKPOINT_VERSION
from kagg_revue.rl.capabilities.cli import load_settings, repository_root
from kagg_revue.rl.capabilities.config import CapabilityRlSettings
from kagg_revue.rl.capabilities.contract import CapabilityVersionContract
from kagg_revue.rl.capabilities.rollout import (
    CapabilityGameResult,
    CapabilityRolloutCollector,
)
from kagg_revue.rl.capabilities.search import FrozenTargetSearch


def _checkpoint_payload(path: Path) -> Mapping[str, object]:
    value = torch.load(path, map_location="cpu", weights_only=False)
    if not isinstance(value, Mapping):
        raise ValueError("capability evaluation checkpoint must be a mapping")
    if value.get("checkpoint_version") != CAPABILITY_CHECKPOINT_VERSION:
        raise ValueError("capability evaluation checkpoint version differs")
    return cast(Mapping[str, object], value)


def _contract(value: object) -> CapabilityVersionContract:
    if not isinstance(value, Mapping):
        raise ValueError("capability evaluation checkpoint lacks a version contract")
    return CapabilityVersionContract(
        proposal_version=str(value["proposal_version"]),
        search_version=str(value["search_version"]),
        executor_version=str(value["executor_version"]),
        record_schema_version=str(value["record_schema_version"]),
    )


def _state(value: object, name: str) -> Mapping[str, Tensor]:
    if not isinstance(value, Mapping) or any(
        not isinstance(key, str) or not isinstance(tensor, Tensor)
        for key, tensor in value.items()
    ):
        raise ValueError(f"capability evaluation {name} state is invalid")
    return cast(Mapping[str, Tensor], value)


def _outcome_summary(games: Sequence[CapabilityGameResult]) -> dict[str, object]:
    if not games:
        raise ValueError("capability evaluation needs completed games")

    def summarize(rows: Sequence[CapabilityGameResult]) -> dict[str, float | int]:
        return {
            "games": len(rows),
            "wins": sum(game.outcome > 0 for game in rows),
            "ties": sum(game.outcome == 0 for game in rows),
            "losses": sum(game.outcome < 0 for game in rows),
            "mean_terminal_cash": float(
                np.mean([game.terminal_cash for game in rows])
            ),
            "mean_cash_difference": float(
                np.mean([game.terminal_cash - game.opponent_cash for game in rows])
            ),
        }

    return {
        "all": summarize(games),
        "opponents": {
            opponent_id: summarize(
                tuple(game for game in games if game.opponent_id == opponent_id)
            )
            for opponent_id in sorted({game.opponent_id for game in games})
        },
    }


def evaluate_capability_checkpoint(
    settings: CapabilityRlSettings,
    checkpoint: Path,
    output_dir: Path,
    seeds: Sequence[int],
    *,
    device: torch.device,
    sampled: bool,
    sampling_seed: int,
    cpu_workers: int | None = None,
) -> dict[str, object]:
    """Evaluate one exact checkpoint on every opponent, seed, and paired seat."""
    root = repository_root().resolve()
    settings = settings.model_copy(
        update={
            "public_agent_manifest": (root / settings.public_agent_manifest).resolve(),
        }
    )
    torch.set_num_threads(settings.cpu_threads)
    checkpoint = (root / checkpoint).resolve() if not checkpoint.is_absolute() else checkpoint
    output_dir = (root / output_dir).resolve() if not output_dir.is_absolute() else output_dir
    outputs_root = (root / "outputs" / "evaluation").resolve()
    if not output_dir.is_relative_to(outputs_root):
        raise ValueError("capability evaluation output must be under outputs/evaluation/")
    if output_dir.exists():
        raise FileExistsError(f"capability evaluation output already exists: {output_dir}")
    if not checkpoint.is_file():
        raise FileNotFoundError(f"capability evaluation checkpoint is missing: {checkpoint}")
    if not seeds or len(set(seeds)) != len(seeds):
        raise ValueError("capability evaluation seeds must be nonempty and unique")
    resolved_cpu_workers = settings.rollout.cpu_workers if cpu_workers is None else cpu_workers
    if resolved_cpu_workers < 1:
        raise ValueError("capability evaluation cpu_workers must be positive")
    rollout_end = settings.rollout_seed_start + settings.updates * settings.rollout.seeds_per_update
    if any(settings.rollout_seed_start <= seed < rollout_end for seed in seeds):
        raise ValueError("capability evaluation seeds overlap training rollouts")

    payload = _checkpoint_payload(checkpoint)
    if payload.get("training_contract") != settings.checkpoint_contract():
        raise ValueError("capability evaluation profile differs from checkpoint training contract")
    contract = _contract(payload.get("version_contract"))
    settings.versions.contract().require_compatible(contract)
    architecture = CapabilitySelectorArchitecture.model_validate(payload.get("architecture"))
    model = CapabilitySelector(architecture).to(device)
    model.load_state_dict(_state(payload.get("model_state"), "model"), strict=True)
    model.eval()
    search = FrozenTargetSearch(
        model,
        candidate_value_scale=settings.search.candidate_value_scale,
        replay_prior_logit=settings.search.replay_prior_logit,
    )
    search.target.load_state_dict(_state(payload.get("target_state"), "target"), strict=True)
    backend = load_backend(root)
    environment = cast(
        dict[str, object],
        backend.engine(seed=0, configuration=settings.environment).configuration,
    )
    generator = torch.Generator(device=device)
    generator.manual_seed(sampling_seed)
    games: list[CapabilityGameResult] = []
    diagnostics: dict[str, object] = {}
    started = time.perf_counter()
    epsilon = settings.search.behavior_exploration_epsilon if sampled else 0.0
    for opponent_id in settings.opponents:
        collector = CapabilityRolloutCollector(
            backend,
            model,
            search,
            environment,
            {opponent_id: 1.0},
            contract,
            max_candidates=settings.abi.max_candidates,
            max_edits=settings.abi.max_edits,
            cpu_workers=resolved_cpu_workers,
            device=device,
            sampling_seed=sampling_seed,
            action_generator=generator,
            behavior_exploration_epsilon=epsilon,
            sample_actions=sampled,
        )
        result = collector.collect(seeds, update=0)
        games.extend(result.games)
        diagnostics[opponent_id] = result.diagnostics
        del result
        gc.collect()
        torch.cuda.empty_cache()

    native_identity = cast(Mapping[str, object], backend.identity["native_module"])
    checkpoint_artifacts = payload.get("artifact_identities")
    checkpoint_native = (
        checkpoint_artifacts.get("native_extension")
        if isinstance(checkpoint_artifacts, Mapping)
        else None
    )
    native_matches = checkpoint_native == native_identity.get("sha256")
    if not native_matches:
        raise ValueError("capability evaluation native extension differs from checkpoint")
    report: dict[str, object] = {
        "schema_version": "capability-complete-match-evaluation-v1",
        "checkpoint": {
            "path": str(checkpoint),
            "sha256": sha256_file(checkpoint),
            "completed_update": payload.get("completed_update"),
            "source_revision": payload.get("source_revision"),
        },
        "policy": {
            "mode": "sampled_training_behavior" if sampled else "greedy_no_exploration",
            "sampling_seed": sampling_seed if sampled else None,
            "behavior_exploration_epsilon": epsilon,
        },
        "panel": {
            "opponents": list(settings.opponents),
            "seeds": list(seeds),
            "paired_seats": True,
            "games": len(games),
        },
        "outcomes": _outcome_summary(games),
        "games": [
            {
                "opponent_id": game.opponent_id,
                "seed": game.seed,
                "seat": game.seat,
                "outcome": game.outcome,
                "terminal_cash": game.terminal_cash,
                "opponent_cash": game.opponent_cash,
            }
            for game in games
        ],
        "execution": {
            "elapsed_seconds": time.perf_counter() - started,
            "opponents": diagnostics,
            "device": str(device),
            "cpu_workers": resolved_cpu_workers,
            "native_extension": native_identity,
            "native_matches_checkpoint": native_matches,
            "official_timeout_gate": False,
        },
        "source": source_identity(root),
        "decision_surface": "complete official-rule terminal W/D/L",
        "cash_role": "terminal diagnostic only",
        "promotion_authority": False,
    }
    output_dir.mkdir(parents=True)
    (output_dir / "evaluation-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return report


def main() -> None:
    """Evaluate one checkpoint on an explicit held-out common-seed panel."""
    parser = argparse.ArgumentParser(prog="kagg-revue-capability-evaluate")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--profile", default="proposal_prior")
    parser.add_argument("--seed-start", type=int, required=True)
    parser.add_argument("--seed-count", type=int, required=True)
    parser.add_argument("--sampling-seed", type=int, default=20260830)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--cpu-workers", type=int)
    parser.add_argument("--sampled", action="store_true")
    arguments = parser.parse_args()
    if arguments.seed_count < 1:
        parser.error("--seed-count must be positive")
    settings = load_settings([f"capability_rl={arguments.profile}"])
    seeds = tuple(range(arguments.seed_start, arguments.seed_start + arguments.seed_count))
    report = evaluate_capability_checkpoint(
        settings,
        arguments.checkpoint,
        arguments.output_dir,
        seeds,
        device=torch.device(arguments.device),
        sampled=arguments.sampled,
        sampling_seed=arguments.sampling_seed,
        cpu_workers=arguments.cpu_workers,
    )
    print(json.dumps(report["outcomes"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
