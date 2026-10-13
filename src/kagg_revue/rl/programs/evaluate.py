"""Official-rule evaluation of one conditional-program checkpoint."""

from __future__ import annotations

import json
import time
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

import torch

from kagg_revue.bc.dataset import sha256_file
from kagg_revue.core.backend import BackendApi, load_backend
from kagg_revue.core.provenance import source_identity
from kagg_revue.policy.model import parameter_count
from kagg_revue.policy.programs.native import NativeProgramContract
from kagg_revue.rl.programs.checkpoint import load_program_checkpoint
from kagg_revue.rl.programs.config import ProgramRlSettings
from kagg_revue.rl.programs.metrics import outcome_metrics, outcome_rows
from kagg_revue.rl.programs.model import ProgramActorCritic
from kagg_revue.rl.programs.parallel import create_program_rollout
from kagg_revue.rl.programs.train import resolve_program_settings


def _integer(value: object, name: str) -> int:
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise TypeError(f"{name} is not numeric")
    return int(value)


def _contract(
    backend: BackendApi,
    settings: ProgramRlSettings,
) -> NativeProgramContract:
    raw = cast(
        Mapping[str, object],
        backend.conditional_program_spec(settings.environment, settings.abi.unit_limit),
    )
    return NativeProgramContract.from_spec(raw)


def _validate_architecture(
    model: ProgramActorCritic,
    contract: NativeProgramContract,
    settings: ProgramRlSettings,
) -> None:
    expected = contract.architecture(
        context_width=model.actor.architecture.model_width,
        model_width=settings.model.model_width,
        feedforward_width=settings.model.feedforward_width,
    )
    if model.programs.architecture != expected:
        raise ValueError("conditional-program checkpoint architecture differs from profile")


def _resolve_output(output_dir: Path, repository_root: Path) -> Path:
    resolved = (
        output_dir.resolve()
        if output_dir.is_absolute()
        else (repository_root / output_dir).resolve()
    )
    output_root = (repository_root / "outputs").resolve()
    if not resolved.is_relative_to(output_root):
        raise ValueError("conditional-program evaluation must remain under outputs/")
    if resolved.exists():
        raise FileExistsError(
            f"conditional-program evaluation output already exists: {resolved}"
        )
    return resolved


def _resolve_checkpoint(
    checkpoint: Path | None,
    settings: ProgramRlSettings,
    repository_root: Path,
) -> Path:
    selected = checkpoint or settings.resume_checkpoint or settings.initial_checkpoint
    if selected is None:
        raise ValueError("conditional-program evaluation requires a checkpoint")
    resolved = (
        selected.resolve()
        if selected.is_absolute()
        else (repository_root / selected).resolve()
    )
    if not resolved.is_relative_to((repository_root / "outputs").resolve()):
        raise ValueError("conditional-program checkpoint must remain under outputs/")
    if not resolved.is_file():
        raise FileNotFoundError(f"conditional-program checkpoint is absent: {resolved}")
    return resolved


def _write_json(path: Path, value: object) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    temporary.replace(path)


def evaluate_conditional_program(
    raw_settings: ProgramRlSettings,
    repository_root: Path,
    output_dir: Path,
    *,
    checkpoint: Path | None = None,
    sample: bool = False,
) -> dict[str, object]:
    """Run one held-out paired panel through the production rollout path."""
    settings = resolve_program_settings(raw_settings, repository_root)
    source = source_identity(repository_root)
    if source["worktree_dirty"]:
        raise RuntimeError("conditional-program evaluation requires a clean revision")
    destination = _resolve_output(output_dir, repository_root)
    checkpoint_path = _resolve_checkpoint(checkpoint, settings, repository_root)
    device = torch.device(settings.device)
    if device.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA conditional-program evaluation requested without a GPU")
    torch.set_num_threads(settings.cpu_threads)
    backend = load_backend(repository_root)
    environment = cast(
        dict[str, object],
        backend.engine(seed=0, configuration=settings.environment).configuration,
    )
    settings = settings.model_copy(update={"environment": environment})
    contract = _contract(backend, settings)
    model, checkpoint_metadata = load_program_checkpoint(
        checkpoint_path,
        contract,
        device,
    )
    _validate_architecture(model, contract, settings)
    model.eval()
    collector = create_program_rollout(
        settings,
        repository_root,
        backend,
        model,
        contract,
        environment,
        use_cuda_graphs=False,
    )
    try:
        seeds = tuple(
            range(
                settings.rollout_seed_start,
                settings.rollout_seed_start + settings.rollout.seeds_per_update,
            )
        )
        started = time.perf_counter()
        rollout = collector.collect(
            seeds,
            update=_integer(checkpoint_metadata.get("update", 0), "checkpoint update"),
            sample=sample,
        )
        elapsed = time.perf_counter() - started
        opponents = dict(collector.opponent_identities)
    finally:
        collector.close()
    expected_episodes = 2 * len(seeds)
    expected_turns = expected_episodes * (
        _integer(environment["episodeSteps"], "episodeSteps") - 1
    )
    complete = (
        len(rollout.episodes) == expected_episodes
        and rollout.official_turns == expected_turns
        and rollout.remaining_overage_seconds >= 0.0
    )
    checkpoint_identity = checkpoint_metadata.get("checkpoint_identity")
    if not isinstance(checkpoint_identity, Mapping):
        raise ValueError("conditional-program checkpoint lacks its measured identity")
    destination.mkdir(parents=True)
    report: dict[str, object] = {
        "schema_version": "conditional-program-evaluation-v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "purpose": "held-out complete-match checkpoint gate",
        "decision_surface": ["win", "loss", "tie"],
        "diagnostic_surface": ["terminal_cash", "cash_difference"],
        "source": source,
        "checkpoint": dict(checkpoint_identity),
        "checkpoint_update": checkpoint_metadata.get("update"),
        "checkpoint_training_source": checkpoint_metadata.get("source_identity"),
        "source_actor": checkpoint_metadata.get("source_actor_identity"),
        "backend": backend.identity,
        "opponents": opponents,
        "paired_seats": True,
        "sampling": "sample" if sample else "greedy",
        "seeds": list(seeds),
        "outcomes": outcome_metrics(outcome_rows(rollout.episodes)),
        "completion": {
            "valid": complete,
            "expected_episodes": expected_episodes,
            "observed_episodes": len(rollout.episodes),
            "expected_official_turns": expected_turns,
            "observed_official_turns": rollout.official_turns,
        },
        "execution": {
            "devices": list(settings.rollout.devices),
            "elapsed_seconds": elapsed,
            "physical_games": rollout.physical_games,
            "games_per_second": rollout.physical_games / elapsed,
            "program_decisions": rollout.program_decisions,
            "official_decisions": rollout.official_decisions,
            "maximum_actor_seconds": rollout.maximum_actor_seconds,
            "remaining_overage_seconds": rollout.remaining_overage_seconds,
            "act_timeout_seconds": settings.act_timeout_seconds,
            "initial_overage_seconds": settings.remaining_overage_seconds,
            "timeout_enforced": True,
            "phase_seconds": dict(rollout.phase_seconds),
            "program_phase_seconds": dict(rollout.program_phase_seconds),
            "rank_seconds": list(rollout.rank_seconds),
        },
        "model": {
            "parameter_count": parameter_count(model),
            "actor_architecture": model.actor.architecture_json(),
            "program_architecture": model.programs.architecture.model_dump(mode="json"),
        },
        "resolved_profile": settings.model_dump(mode="json"),
    }
    report_path = destination / "evaluation-report.json"
    _write_json(report_path, report)
    report["report_artifact"] = {
        "path": str(report_path),
        "sha256": sha256_file(report_path),
        "size_bytes": report_path.stat().st_size,
    }
    return report


__all__ = ["evaluate_conditional_program"]
