"""Reproducible complete-match throughput benchmark for program PPO."""

from __future__ import annotations

import json
import platform
import statistics
import time
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, cast

import numpy as np
import torch
from numpy.typing import NDArray

from kagg_revue.core.backend import load_backend
from kagg_revue.core.provenance import source_identity
from kagg_revue.policy.programs.native import NativeProgramContract
from kagg_revue.rl.programs.config import ProgramRlSettings
from kagg_revue.rl.programs.data import ProgramEpisode
from kagg_revue.rl.programs.initialization import initialize_program_model
from kagg_revue.rl.programs.learning import audit_program_behavior
from kagg_revue.rl.programs.parallel import (
    ProgramRolloutDriver,
    create_program_rollout,
)
from kagg_revue.rl.programs.rollout import ProgramRolloutReport
from kagg_revue.rl.programs.train import resolve_program_settings

_COMPILED_ACTION_ARRAYS = (
    "actions",
    "quantities",
    "action_decision_counts",
)


def _contract(
    backend: Any,
    environment: Mapping[str, object],
    unit_limit: int,
) -> NativeProgramContract:
    raw = cast(
        Mapping[str, object],
        backend.conditional_program_spec(environment, unit_limit),
    )
    return NativeProgramContract.from_spec(raw)


def _collector(
    settings: ProgramRlSettings,
    repository_root: Path,
    backend: Any,
    model: Any,
    contract: NativeProgramContract,
    environment: Mapping[str, object],
    device: torch.device,
    *,
    use_cuda_graphs: bool,
) -> ProgramRolloutDriver:
    if torch.device(settings.rollout.devices[0]) != device:
        raise ValueError("program benchmark primary rollout device changed")
    return create_program_rollout(
        settings,
        repository_root,
        backend,
        model,
        contract,
        environment,
        use_cuda_graphs=use_cuda_graphs,
    )


def _outcomes(episodes: Sequence[ProgramEpisode]) -> dict[str, int]:
    counts = Counter(episode.outcome for episode in episodes)
    return {
        "wins": counts[1],
        "ties": counts[0],
        "losses": counts[-1],
    }


def _timed_collect(
    collector: ProgramRolloutDriver,
    seeds: Sequence[int],
    devices: Sequence[torch.device],
    *,
    sample: bool,
) -> tuple[ProgramRolloutReport, float, int, int]:
    for device in devices:
        if device.type == "cuda":
            torch.cuda.reset_peak_memory_stats(device)
            torch.cuda.synchronize(device)
    started = time.perf_counter()
    report = collector.collect(seeds, update=1, sample=sample)
    for device in devices:
        if device.type == "cuda":
            torch.cuda.synchronize(device)
    elapsed = time.perf_counter() - started
    allocated = sum(
        torch.cuda.max_memory_allocated(device) for device in devices if device.type == "cuda"
    )
    reserved = sum(
        torch.cuda.max_memory_reserved(device) for device in devices if device.type == "cuda"
    )
    return report, elapsed, allocated, reserved


def _measurement(
    report: ProgramRolloutReport,
    elapsed: float,
    allocated: int,
    reserved: int,
) -> dict[str, object]:
    return {
        "elapsed_seconds": elapsed,
        "physical_games": report.physical_games,
        "physical_games_per_second": report.physical_games / elapsed,
        "training_trajectories": len(report.episodes),
        "training_trajectories_per_second": len(report.episodes) / elapsed,
        "official_turns": report.official_turns,
        "official_turns_per_second": report.official_turns / elapsed,
        "program_decisions": report.program_decisions,
        "program_decisions_per_second": report.program_decisions / elapsed,
        "official_decisions": report.official_decisions,
        "official_decisions_per_second": report.official_decisions / elapsed,
        "maximum_actor_seconds": report.maximum_actor_seconds,
        "remaining_overage_seconds": report.remaining_overage_seconds,
        "host_bytes": report.host_bytes,
        "rollout_device_bytes": report.device_bytes,
        "peak_gpu_allocated_bytes": allocated,
        "peak_gpu_reserved_bytes": reserved,
        "phase_seconds": dict(report.phase_seconds),
        "program_phase_seconds": dict(report.program_phase_seconds),
        "rank_seconds": list(report.rank_seconds),
        "outcomes": _outcomes(report.episodes),
    }


def _closed_loop_comparison(
    accelerated: ProgramRolloutReport,
    reference: ProgramRolloutReport,
) -> dict[str, object]:
    outcome_deltas = []
    cash_margin_deltas = []
    field_mismatches = {name: 0 for name in _COMPILED_ACTION_ARRAYS}
    for accelerated_episode, reference_episode in zip(
        accelerated.episodes, reference.episodes, strict=True
    ):
        outcome_deltas.append(accelerated_episode.outcome - reference_episode.outcome)
        accelerated_margin = accelerated_episode.terminal_cash - accelerated_episode.opponent_cash
        reference_margin = reference_episode.terminal_cash - reference_episode.opponent_cash
        cash_margin_deltas.append(accelerated_margin - reference_margin)
        for name in _COMPILED_ACTION_ARRAYS:
            accelerated_values = cast(NDArray[np.generic], getattr(accelerated_episode, name))
            reference_values = cast(NDArray[np.generic], getattr(reference_episode, name))
            field_mismatches[name] += int(np.count_nonzero(accelerated_values != reference_values))
    return {
        "compiled_action_mismatches": field_mismatches,
        "outcome_better_episodes": sum(delta > 0 for delta in outcome_deltas),
        "outcome_equal_episodes": sum(delta == 0 for delta in outcome_deltas),
        "outcome_worse_episodes": sum(delta < 0 for delta in outcome_deltas),
        "mean_cash_margin_delta": statistics.fmean(cash_margin_deltas),
        "minimum_cash_margin_delta": min(cash_margin_deltas),
        "maximum_cash_margin_delta": max(cash_margin_deltas),
    }


def _write_report(path: Path, report: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    temporary.replace(path)


def benchmark_conditional_program(
    raw_settings: ProgramRlSettings,
    repository_root: Path,
    output_path: Path,
    *,
    warmups: int,
    repeats: int,
    check_reference: bool,
) -> dict[str, object]:
    """Benchmark one resolved profile without changing its policy semantics."""
    if warmups < 1 or repeats < 1:
        raise ValueError("program benchmark needs positive warmup and repeat counts")
    settings = resolve_program_settings(raw_settings, repository_root)
    resolved_output = (
        output_path.resolve()
        if output_path.is_absolute()
        else (repository_root / output_path).resolve()
    )
    output_root = (repository_root / "outputs").resolve()
    if not resolved_output.is_relative_to(output_root) or resolved_output.suffix != ".json":
        raise ValueError("program benchmark report must be a JSON file under outputs/")
    if resolved_output.exists():
        raise FileExistsError(f"program benchmark report already exists: {resolved_output}")
    device = torch.device(settings.device)
    devices = tuple(torch.device(value) for value in settings.rollout.devices)
    if any(value.type == "cuda" for value in devices) and (
        not torch.cuda.is_available()
        or any(
            value.index is not None and value.index >= torch.cuda.device_count()
            for value in devices
        )
    ):
        raise RuntimeError("program benchmark requested unavailable CUDA")
    torch.manual_seed(settings.seed)
    np.random.seed(settings.seed)
    if device.type == "cuda":
        torch.cuda.set_device(device)
        torch.cuda.manual_seed_all(settings.seed)
    backend = load_backend(repository_root)
    environment = cast(
        dict[str, object],
        backend.engine(seed=0, configuration=settings.environment).configuration,
    )
    contract = _contract(backend, environment, settings.abi.unit_limit)
    model, actor_identity = initialize_program_model(
        settings.initial_actor, contract, settings.model, device
    )
    collector = _collector(
        settings,
        repository_root,
        backend,
        model,
        contract,
        environment,
        device,
        use_cuda_graphs=True,
    )
    seeds = tuple(
        range(
            settings.rollout_seed_start,
            settings.rollout_seed_start + settings.rollout.seeds_per_update,
        )
    )
    try:
        for _ in range(warmups):
            warmup, _elapsed, _allocated, _reserved = _timed_collect(
                collector, seeds, devices, sample=True
            )
            del warmup
        measurements = []
        for _ in range(repeats):
            rollout, elapsed, allocated, reserved = _timed_collect(
                collector, seeds, devices, sample=True
            )
            measurements.append(_measurement(rollout, elapsed, allocated, reserved))
        behavior_replay: dict[str, float] | None = None
        closed_loop_reference: dict[str, object] | None = None
        if check_reference:
            behavior_replay = audit_program_behavior(
                model,
                rollout.episodes,
                contract,
                device,
                episodes_per_batch=(
                    settings.optimization.effective_episodes_per_microbatch
                ),
            )
            accelerated, _elapsed, _allocated, _reserved = _timed_collect(
                collector, seeds, devices, sample=False
            )
            reference_collector = _collector(
                settings,
                repository_root,
                backend,
                model,
                contract,
                environment,
                device,
                use_cuda_graphs=False,
            )
            try:
                reference, _elapsed, _allocated, _reserved = _timed_collect(
                    reference_collector, seeds, devices, sample=False
                )
            finally:
                reference_collector.close()
            closed_loop_reference = _closed_loop_comparison(accelerated, reference)
    finally:
        collector.close()
    throughputs = [
        cast(float, measurement["official_turns_per_second"]) for measurement in measurements
    ]
    game_throughputs = [
        cast(float, measurement["physical_games_per_second"]) for measurement in measurements
    ]
    source = source_identity(repository_root)
    hardware: dict[str, object] = {
        "platform": platform.platform(),
        "python": platform.python_version(),
        "torch": torch.__version__,
        "device": str(device),
        "rollout_devices": [str(value) for value in devices],
    }
    if device.type == "cuda":
        properties = torch.cuda.get_device_properties(device)
        hardware.update(
            {
                "gpu_name": properties.name,
                "gpu_total_memory_bytes": properties.total_memory,
                "cuda": torch.version.cuda,
            }
        )
    result: dict[str, object] = {
        "schema_version": "conditional-program-throughput-v1",
        "source": source,
        "backend": backend.identity,
        "source_actor": actor_identity,
        "resolved_config": settings.model_dump(mode="json"),
        "environment": environment,
        "hardware": hardware,
        "warmups": warmups,
        "repeats": repeats,
        "measurements": measurements,
        "summary": {
            "official_turns_per_second_median": statistics.median(throughputs),
            "official_turns_per_second_minimum": min(throughputs),
            "official_turns_per_second_maximum": max(throughputs),
            "physical_games_per_second_median": statistics.median(game_throughputs),
            "physical_games_per_second_minimum": min(game_throughputs),
            "physical_games_per_second_maximum": max(game_throughputs),
        },
        "behavior_replay": behavior_replay,
        "closed_loop_reference": closed_loop_reference,
    }
    _write_report(resolved_output, result)
    return result


__all__ = ["benchmark_conditional_program"]
