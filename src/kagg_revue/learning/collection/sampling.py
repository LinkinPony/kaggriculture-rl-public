"""Complete-game rollout tapes with physical-game weighting and terminal credit."""

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch import Tensor

from kagg_revue.learning.collection.population import (
    TrainingBatch,
    create_training_batch,
    episode_weights,
    historical_games,
    policy_rows,
    script_games,
)
from kagg_revue.learning.collection.prefetch import ScriptPrefetch
from kagg_revue.learning.collection.quadrants import measure
from kagg_revue.learning.optimization.objectives import terminal_rewards
from kagg_revue.learning.settings import RuntimeSettings
from kagg_revue.policy.inference import ActorRuntime
from kagg_revue.policy.spatial.model import Policy


def _advance(
    batch: TrainingBatch, runtime: ActorRuntime, span: int, decision: int, seeds: list[int]
) -> None:
    """Keep rejected native programs and their exact observations available for diagnosis."""
    try:
        batch.advance(runtime.selected.numpy(), span)
    except ValueError as error:
        directory = Path("outputs/analysis/collection-failures")
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{time.time_ns()}-{runtime.device.index}.npz"
        np.savez_compressed(
            path,
            observations=runtime.host.numpy(),
            programs=runtime.selected.numpy(),
            device_programs=runtime.actions.cpu().numpy(),
            seeds=seeds,
            decision=decision,
        )
        error.add_note(f"Rejected programs at decision {decision}: {path}")
        raise


@dataclass
class Rollout:
    """Compact device tape plus direct outcomes for physical games."""

    observations: Tensor
    actions: Tensor
    log_probabilities: Tensor
    steps: Tensor
    returns: Tensor
    cash: np.ndarray[Any, np.dtype[np.float64]]
    timing: dict[str, float]
    weights: Tensor
    opponents: tuple[str, ...]
    temperature: float | None = None
    land: dict[str, Any] | None = None


def collect(
    settings: RuntimeSettings,
    policy: Policy,
    runtime: ActorRuntime,
    seeds: list[int],
    history_runtime: ActorRuntime | None = None,
    *,
    prepared_batch: TrainingBatch | None = None,
    start_decision: int = 0,
    initial_cash: np.ndarray[Any, np.dtype[np.float64]] | None = None,
) -> Rollout:
    """Collect only learned seats in whole self-play and native script games."""
    layout = policy.layout
    games = len(seeds)
    single_seat = script_games(settings, games) + historical_games(settings, games)
    selfplay = games - single_seat
    count = 2 * selfplay + single_seat
    device = runtime.device
    if not 0 <= start_decision < layout.decisions:
        raise ValueError("rollout start must be a nonterminal decision boundary")
    if start_decision and prepared_batch is None:
        raise ValueError("a noninitial rollout needs an already restored native batch")
    batch = prepared_batch or create_training_batch(settings, seeds, history_runtime)
    if batch.step_index != layout.starts[start_decision]:
        raise ValueError("rollout boundary differs from the native state clock")
    decisions = layout.decisions - start_decision
    observations = torch.empty(
        (decisions, count, layout.observation.features), dtype=torch.float16, device=device
    )
    actions = torch.empty((decisions, count, layout.factors), dtype=torch.int16, device=device)
    probabilities = torch.empty_like(actions, dtype=torch.float32)
    native_seconds = inference_seconds = encoding_seconds = 0.0
    history_stream = (
        torch.cuda.Stream(device=device)  # type: ignore[no-untyped-call]
        if history_runtime is not None
        and settings.ppo.concurrent_history_inference
        and device.type == "cuda"
        else None
    )
    started = time.perf_counter()
    with ScriptPrefetch(batch.prepare_opponents) as scripts:
        for offset, span in enumerate(layout.spans[start_decision:]):
            decision = start_decision + offset
            scripts.start()
            phase = time.perf_counter()
            batch.observe_into(runtime.host.numpy())
            encoding_seconds += time.perf_counter() - phase
            phase = time.perf_counter()
            current = torch.cuda.current_stream(device) if history_stream is not None else None
            if history_stream is not None:
                assert current is not None and history_runtime is not None
                history_stream.wait_stream(current)
            selected, likelihood = runtime.act(decision, synchronize=history_runtime is None)
            if history_runtime is not None:
                if history_stream is None:
                    history_runtime.act(decision)
                else:
                    assert current is not None
                    with torch.cuda.stream(history_stream):
                        history_runtime.act(decision, synchronize=False)
                    current.wait_stream(history_stream)
                    current.synchronize()
            observations[offset].copy_(runtime.observations)
            actions[offset].copy_(selected)
            probabilities[offset].copy_(likelihood)
            inference_seconds += time.perf_counter() - phase
            phase = time.perf_counter()
            scripts.wait()
            _advance(batch, runtime, span, decision, seeds)
            native_seconds += time.perf_counter() - phase
    if device.type == "cuda":
        torch.cuda.synchronize(device)
    cash = batch.cash(layout.observation.turns)
    rewards = terminal_rewards(
        cash,
        cash_weight=settings.ppo.cash_weight,
        cash_scale=settings.ppo.cash_scale,
        win_weight=settings.ppo.win_weight,
        cash_margin=settings.ppo.cash_margin,
    )
    if initial_cash is not None:
        if initial_cash.shape != cash.shape:
            raise ValueError("reward baseline must match both seats of every physical game")
        rewards -= settings.ppo.cash_weight * initial_cash / settings.ppo.cash_scale
    returns = torch.tensor(
        policy_rows(rewards, selfplay), dtype=torch.float32, device=device
    ).repeat(decisions)
    steps = torch.arange(start_decision, layout.decisions, device=device).repeat_interleave(count)
    monitoring_started = time.perf_counter()
    batch.observe_into(runtime.host.numpy())
    land = measure(observations, runtime.host, layout)
    monitoring_seconds = time.perf_counter() - monitoring_started
    elapsed = time.perf_counter() - started
    return Rollout(
        observations.flatten(0, 1),
        actions.flatten(0, 1),
        probabilities.flatten(0, 1),
        steps,
        returns,
        cash,
        {
            "rollout_seconds": elapsed,
            "native_seconds": native_seconds,
            "encoding_seconds": encoding_seconds,
            "inference_seconds": inference_seconds,
            "script_compute_seconds": scripts.compute_seconds,
            "script_wait_seconds": scripts.wait_seconds,
            "physical_games_per_second": games / elapsed,
            "collation_seconds": 0.0,
            "quadrant_monitor_seconds": monitoring_seconds,
        },
        torch.tensor(episode_weights(selfplay, single_seat), device=device).repeat(decisions),
        batch.opponents,
        runtime.temperature,
        land,
    )
