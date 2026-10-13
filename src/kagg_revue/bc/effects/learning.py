"""Streaming GPU optimization for atomic-effect behavior cloning."""

from __future__ import annotations

import random
import time
from collections.abc import Iterator, Sequence
from concurrent.futures import Future, ThreadPoolExecutor
from contextlib import nullcontext
from pathlib import Path
from typing import Any, Literal

import torch
from torch import distributed as dist
from torch.nn import functional

from kagg_revue.bc.effects.config import EffectBcSettings
from kagg_revue.bc.effects.dataset import (
    EffectTeacherShard,
    load_effect_teacher_shard,
)
from kagg_revue.policy.effects.data import EffectTensorState
from kagg_revue.policy.effects.model import EffectActorCritic
from kagg_revue.policy.effects.schema import EffectSequenceContext
from kagg_revue.rl.effects.data import EffectRolloutBatch
from kagg_revue.rl.outcome import outcome_labels

Partition = Literal["train", "validation", "test"]


def _load_batch(
    dataset_dir: Path,
    shards: Sequence[EffectTeacherShard],
) -> EffectRolloutBatch:
    batches = [load_effect_teacher_shard(dataset_dir, shard).batch for shard in shards]
    return batches[0] if len(batches) == 1 else EffectRolloutBatch.concatenate(batches)


def _prefetched_batches(
    dataset_dir: Path,
    batches: Sequence[Sequence[EffectTeacherShard]],
    *,
    workers: int,
    depth: int,
) -> Iterator[tuple[EffectRolloutBatch, float, float]]:
    """Authenticate and decompress a bounded number of complete-game batches."""

    def load(shards: Sequence[EffectTeacherShard]) -> tuple[EffectRolloutBatch, float]:
        started = time.perf_counter()
        return _load_batch(dataset_dir, shards), time.perf_counter() - started

    with ThreadPoolExecutor(
        max_workers=workers,
        thread_name_prefix="effect-bc-shard",
    ) as executor:
        iterator = iter(batches)
        pending: list[Future[tuple[EffectRolloutBatch, float]]] = []
        for _ in range(min(depth, len(batches))):
            pending.append(executor.submit(load, next(iterator)))
        while pending:
            future = pending.pop(0)
            wait_started = time.perf_counter()
            batch, load_seconds = future.result()
            yield batch, load_seconds, time.perf_counter() - wait_started
            try:
                shards = next(iterator)
            except StopIteration:
                continue
            pending.append(executor.submit(load, shards))


def _local_batches(
    shards: Sequence[EffectTeacherShard],
    *,
    games_per_batch: int,
    rank: int,
    world_size: int,
) -> tuple[tuple[EffectTeacherShard, ...], ...]:
    if games_per_batch % world_size:
        raise ValueError("effect BC global game batch must divide across DDP ranks")
    local_games = games_per_batch // world_size
    if local_games < 1:
        raise ValueError("effect BC needs at least one physical game per rank")
    if len(shards) % games_per_batch:
        raise ValueError("effect BC partition must fill every global game batch")
    result: list[tuple[EffectTeacherShard, ...]] = []
    for offset in range(0, len(shards), games_per_batch):
        global_batch = shards[offset : offset + games_per_batch]
        local = tuple(global_batch[rank::world_size])
        if len(local) != local_games:
            raise RuntimeError("effect BC rank received an incomplete game batch")
        result.append(local)
    return tuple(result)


def _autocast(device: torch.device) -> Any:
    return (
        torch.autocast(device_type="cuda", dtype=torch.bfloat16)
        if device.type == "cuda"
        else nullcontext()
    )


def _step_events(
    device: torch.device,
) -> tuple[torch.cuda.Event, torch.cuda.Event] | None:
    if device.type != "cuda":
        return None
    return (
        torch.cuda.Event(enable_timing=True),  # type: ignore[no-untyped-call]
        torch.cuda.Event(enable_timing=True),  # type: ignore[no-untyped-call]
    )


def _balanced_weights(
    episode_index: torch.Tensor,
    turn_index: torch.Tensor,
    mask: torch.Tensor,
    episode_count: int,
    turn_horizon: int,
) -> torch.Tensor:
    """Return factor weights for mean-within-turn, then episode reduction."""
    active = mask.bool()
    result = torch.zeros_like(episode_index, dtype=torch.float32)
    if not bool(active.any()):
        return result
    episodes = episode_index.long()
    keys = episodes * turn_horizon + turn_index.long()
    surface = episode_count * turn_horizon
    counts = torch.zeros(surface, dtype=torch.float32, device=episodes.device)
    counts.scatter_add_(0, keys[active], torch.ones_like(keys[active], dtype=torch.float32))
    represented_turns = counts > 0
    turn_episodes = torch.arange(surface, device=episodes.device) // turn_horizon
    episode_turns = torch.zeros(
        episode_count,
        dtype=torch.float32,
        device=episodes.device,
    )
    episode_turns.scatter_add_(
        0,
        turn_episodes[represented_turns],
        torch.ones_like(turn_episodes[represented_turns], dtype=torch.float32),
    )
    represented_episodes = int(torch.count_nonzero(episode_turns))
    result[active] = (
        counts[keys[active]].reciprocal()
        * episode_turns[episodes[active]].reciprocal()
        / represented_episodes
    )
    return result


def _state_rows(
    state: EffectTensorState,
    rows: slice,
) -> EffectTensorState:
    """Select contiguous factor rows without copying semantic tensors."""
    return EffectTensorState(
        **{
            name: getattr(state, name)[rows]
            for name in EffectTensorState.__dataclass_fields__
        }
    )


def _detached_sequence(
    sequence: EffectSequenceContext,
) -> EffectSequenceContext:
    """Create leaf turn context so candidate chunks can backpropagate independently."""

    def leaf(value: torch.Tensor) -> torch.Tensor:
        return value.detach().requires_grad_(value.requires_grad)

    return EffectSequenceContext(
        context=leaf(sequence.context),
        tile_context=leaf(sequence.tile_context),
        strategy=None if sequence.strategy is None else leaf(sequence.strategy),
    )


def _backward_sequence(
    sequence: EffectSequenceContext,
    leaves: EffectSequenceContext,
) -> None:
    """Propagate accumulated leaf gradients through the actor exactly once."""
    outputs: list[torch.Tensor] = []
    gradients: list[torch.Tensor] = []
    for output, leaf in (
        (sequence.context, leaves.context),
        (sequence.tile_context, leaves.tile_context),
        (sequence.strategy, leaves.strategy),
    ):
        if output is not None and leaf is not None and leaf.grad is not None:
            outputs.append(output)
            gradients.append(leaf.grad)
    if outputs:
        torch.autograd.backward(outputs, gradients)


def _synchronize_gradients(model: EffectActorCritic, world_size: int) -> None:
    """Average complete local-game gradients across learner ranks."""
    if world_size <= 1:
        return
    for parameter in model.parameters():
        if not parameter.requires_grad:
            continue
        if parameter.grad is None:
            raise RuntimeError("effect BC trainable parameter received no gradient")
        dist.all_reduce(parameter.grad, op=dist.ReduceOp.SUM)
        parameter.grad.div_(world_size)


def run_effect_bc_partition(
    model: EffectActorCritic,
    dataset_dir: Path,
    shards: Sequence[EffectTeacherShard],
    partition: Partition,
    settings: EffectBcSettings,
    device: torch.device,
    optimizer: torch.optim.Optimizer | None,
    epoch: int,
    *,
    rank: int = 0,
    world_size: int = 1,
) -> dict[str, object]:
    """Run one complete-game partition without materializing the dataset."""
    training = optimizer is not None
    ordered = list(shards)
    if training:
        random.Random(settings.optimization.seed + epoch).shuffle(ordered)
    local_batches = _local_batches(
        ordered,
        games_per_batch=settings.optimization.games_per_batch,
        rank=rank,
        world_size=world_size,
    )
    model.train(training)
    model.actor.eval()
    if training:
        for module in model.actor.modules():
            if isinstance(module, torch.nn.GRU | torch.nn.LSTM | torch.nn.RNN) and any(
                parameter.requires_grad for parameter in module.parameters()
            ):
                module.train()
    started = time.perf_counter()
    # policy, outcome, total, entropy, W/D/L accuracy, correct choices,
    # non-forced choices, factors, episodes, official turns.
    sums = torch.zeros(10, dtype=torch.float64, device=device)
    loader_wait_seconds = 0.0
    loader_cpu_seconds = 0.0
    materialization_seconds = 0.0
    batches = 0
    optimizer_steps = 0
    cpu_step_seconds: list[float] = []
    gpu_step_events: list[tuple[torch.cuda.Event, torch.cuda.Event]] = []
    context = nullcontext() if training else torch.inference_mode()
    with context:
        for cpu_batch, load_seconds, wait_seconds in _prefetched_batches(
            dataset_dir,
            local_batches,
            workers=settings.optimization.loader_workers,
            depth=settings.optimization.prefetch_batches,
        ):
            loader_wait_seconds += wait_seconds
            loader_cpu_seconds += load_seconds
            materialize_started = time.perf_counter()
            batch = cpu_batch.subset(
                tuple(range(cpu_batch.episode_count)),
                device,
                critic_only=False,
            )
            materialization_seconds += time.perf_counter() - materialize_started
            if optimizer is not None:
                optimizer.zero_grad(set_to_none=True)
            events = _step_events(device)
            step_started = time.perf_counter()
            if events is not None:
                events[0].record()
            if batch.state is None or not batch.decision_shards:
                raise ValueError("effect BC requires materialized compact factor shards")
            turn_horizon = int(batch.board.shape[1])
            policy_weights = _balanced_weights(
                batch.episode_index,
                batch.turn_index,
                batch.policy_mask,
                batch.episode_count,
                turn_horizon,
            )
            value_weights = _balanced_weights(
                batch.episode_index,
                batch.turn_index,
                batch.value_mask,
                batch.episode_count,
                turn_horizon,
            )
            economic_state = (
                batch.economic_state
                if model.actor.architecture.economic_feature_version is not None
                else None
            )
            with _autocast(device):
                sequence = model.encode_effect_sequences(
                    batch.board,
                    batch.units,
                    batch.global_features,
                    batch.actions,
                    batch.quantities,
                    batch.turn_mask,
                    batch.decision_mask,
                    economic_state,
                )
            evaluated_sequence = _detached_sequence(sequence) if training else sequence
            policy = torch.zeros((), dtype=torch.float32, device=device)
            outcome = torch.zeros_like(policy)
            entropy = torch.zeros_like(policy)
            outcome_accuracy = torch.zeros_like(policy)
            correct = torch.zeros((), dtype=torch.int64, device=device)
            offset = 0
            for decision_shard in batch.decision_shards:
                width = int(decision_shard.state.candidate_fields.shape[1])
                rows_per_chunk = max(
                    1,
                    settings.optimization.candidate_elements_per_chunk // width,
                )
                for local_start in range(0, decision_shard.row_count, rows_per_chunk):
                    local_stop = min(
                        decision_shard.row_count,
                        local_start + rows_per_chunk,
                    )
                    start = offset + local_start
                    stop = offset + local_stop
                    rows = slice(start, stop)
                    local_rows = slice(local_start, local_stop)
                    with _autocast(device):
                        output = model.evaluate_effect_sequence_context(
                            evaluated_sequence,
                            _state_rows(batch.state, rows),
                            batch.episode_index[rows],
                            batch.turn_index[rows],
                            candidate_states=(
                                _state_rows(decision_shard.state, local_rows),
                            ),
                            validate=batches == 0 and start == 0,
                        )
                        log_probability = (
                            torch.log_softmax(
                                output.candidate_logits.float(),
                                dim=-1,
                            )
                            .gather(1, batch.selected[rows].long()[:, None])
                            .squeeze(1)
                        )
                        policy_chunk = -(
                            log_probability * policy_weights[rows]
                        ).sum()
                        labels = outcome_labels(batch.outcomes)[
                            batch.episode_index[rows]
                        ]
                        outcome_items = functional.cross_entropy(
                            output.outcome_logits.float(),
                            labels,
                            reduction="none",
                        )
                        outcome_chunk = (
                            outcome_items * value_weights[rows]
                        ).sum()
                        total_chunk = (
                            policy_chunk
                            + settings.optimization.outcome_loss_weight
                            * outcome_chunk
                        )
                    if not bool(torch.isfinite(total_chunk)):
                        raise FloatingPointError("effect BC loss is not finite")
                    if training:
                        total_chunk.backward()  # type: ignore[no-untyped-call]
                    probabilities = torch.softmax(
                        output.candidate_logits.detach().float(),
                        dim=-1,
                    )
                    entropy_items = -(
                        probabilities
                        * probabilities.clamp_min(1e-30).log()
                    ).sum(dim=-1)
                    policy += policy_chunk.detach()
                    outcome += outcome_chunk.detach()
                    entropy += (
                        entropy_items * policy_weights[rows]
                    ).sum()
                    outcome_accuracy += (
                        (
                            output.outcome_logits.detach().argmax(dim=-1)
                            == labels
                        ).float()
                        * value_weights[rows]
                    ).sum()
                    predictions = output.candidate_logits.detach().argmax(dim=-1)
                    correct += (
                        (predictions == batch.selected[rows])
                        & batch.policy_mask[rows]
                    ).sum()
                    del output, probabilities
                offset += decision_shard.row_count
            if offset != batch.factor_count:
                raise RuntimeError("effect BC factor shards lost row alignment")
            total = policy + settings.optimization.outcome_loss_weight * outcome
            if training:
                _backward_sequence(sequence, evaluated_sequence)
                _synchronize_gradients(model, world_size)
                torch.nn.utils.clip_grad_norm_(
                    (
                        parameter
                        for parameter in model.parameters()
                        if parameter.requires_grad
                    ),
                    settings.optimization.gradient_clip,
                )
                if optimizer is None:
                    raise RuntimeError("effect BC training lost its optimizer")
                optimizer.step()
                optimizer_steps += 1
            if events is not None:
                events[1].record()
                gpu_step_events.append(events)
            else:
                cpu_step_seconds.append(time.perf_counter() - step_started)

            policy_step_tensor = batch.policy_mask.sum()
            episodes = batch.episode_count
            turns = episodes * int(batch.board.shape[1])
            sums.add_(
                torch.stack(
                    (
                        policy.detach() * episodes,
                        outcome.detach() * episodes,
                        total.detach() * episodes,
                        entropy.detach() * episodes,
                        outcome_accuracy.detach() * episodes,
                        correct.detach(),
                        policy_step_tensor.detach(),
                        batch.selected.new_tensor(batch.factor_count),
                        batch.selected.new_tensor(episodes),
                        batch.selected.new_tensor(turns),
                    )
                ).double()
            )
            batches += 1
            del sequence, evaluated_sequence, batch, cpu_batch
    if device.type == "cuda":
        torch.cuda.synchronize(device)
        step_seconds = [
            start.elapsed_time(stop) / 1000.0
            for start, stop in gpu_step_events
        ]
    else:
        step_seconds = cpu_step_seconds
    elapsed = time.perf_counter() - started
    if not step_seconds:
        raise RuntimeError(f"effect BC {partition} partition produced no learner steps")
    first_step = step_seconds[0]
    steady_steps = step_seconds[1:]
    steady_step = (
        sum(steady_steps) / len(steady_steps) if steady_steps else first_step
    )
    learner_seconds = sum(step_seconds)
    timing = torch.tensor(
        [
            elapsed,
            loader_wait_seconds,
            loader_cpu_seconds,
            materialization_seconds,
            first_step,
            steady_step,
            learner_seconds,
        ],
        dtype=torch.float64,
        device=device,
    )
    counters = torch.tensor(
        [batches, optimizer_steps],
        dtype=torch.int64,
        device=device,
    )
    if world_size > 1:
        dist.all_reduce(sums)
        dist.all_reduce(timing, op=dist.ReduceOp.MAX)
        dist.all_reduce(counters, op=dist.ReduceOp.MAX)
    values = sums.cpu().tolist()
    (
        elapsed,
        loader_wait_seconds,
        loader_cpu_seconds,
        materialization_seconds,
        first_step,
        steady_step,
        learner_seconds,
    ) = timing.cpu().tolist()
    batches, optimizer_steps = (int(value) for value in counters.cpu().tolist())
    episodes = int(values[8])
    turns = int(values[9])
    factors = int(values[7])
    policy_step_count = int(values[6])
    if not episodes or not batches:
        raise RuntimeError(f"effect BC {partition} partition produced no batches")
    return {
        "official_turn_nll": values[0] / episodes,
        "terminal_wdl_nll": values[1] / episodes,
        "total_loss": values[2] / episodes,
        "policy_entropy": values[3] / episodes,
        "terminal_wdl_accuracy": values[4] / episodes,
        "teacher_choice_accuracy": values[5] / max(policy_step_count, 1),
        "games": episodes // 2,
        "episodes": episodes,
        "official_turns": turns,
        "factors": factors,
        "policy_factors": policy_step_count,
        "batches": batches,
        "optimizer_steps": optimizer_steps,
        "elapsed_seconds": elapsed,
        "games_per_second": (episodes // 2) / max(elapsed, 1e-9),
        "factors_per_second": factors / max(elapsed, 1e-9),
        "loader_wait_seconds": loader_wait_seconds,
        "loader_cpu_seconds": loader_cpu_seconds,
        "input_materialization_seconds": materialization_seconds,
        "learner_device_seconds": learner_seconds,
        "first_learner_step_seconds": first_step,
        "steady_learner_step_mean_seconds": steady_step,
    }


__all__ = ["Partition", "run_effect_bc_partition"]
