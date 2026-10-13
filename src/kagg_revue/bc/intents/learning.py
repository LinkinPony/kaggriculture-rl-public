"""Streaming GPU optimization for canonical-intent behavior cloning."""

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
from torch import nn
from torch.nn import functional

from kagg_revue.bc.intents.config import IntentBcSettings
from kagg_revue.bc.intents.dataset import (
    IntentTeacherShard,
    load_intent_teacher_shard,
)
from kagg_revue.policy.intents.model import IntentActorCritic
from kagg_revue.rl.intents.data import IntentRolloutBatch
from kagg_revue.rl.intents.learning import IntentSequenceEvaluator
from kagg_revue.rl.intents.objective import (
    episode_balanced_mean,
    intent_behavior_cloning_loss,
)
from kagg_revue.rl.outcome import outcome_labels

Partition = Literal["train", "validation", "test"]


def _load_batch(dataset_dir: Path, shards: Sequence[IntentTeacherShard]) -> IntentRolloutBatch:
    batches = [load_intent_teacher_shard(dataset_dir, shard).batch for shard in shards]
    return batches[0] if len(batches) == 1 else IntentRolloutBatch.concatenate(batches)


def _prefetched_batches(
    dataset_dir: Path,
    batches: Sequence[Sequence[IntentTeacherShard]],
    *,
    workers: int,
    depth: int,
) -> Iterator[tuple[IntentRolloutBatch, float, float]]:
    """Authenticate and decompress a bounded number of complete-game batches."""

    def load(shards: Sequence[IntentTeacherShard]) -> tuple[IntentRolloutBatch, float]:
        started = time.perf_counter()
        return _load_batch(dataset_dir, shards), time.perf_counter() - started

    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="intent-bc-shard") as executor:
        iterator = iter(batches)
        pending: list[Future[tuple[IntentRolloutBatch, float]]] = []
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
    shards: Sequence[IntentTeacherShard],
    *,
    games_per_batch: int,
    rank: int,
    world_size: int,
) -> tuple[tuple[IntentTeacherShard, ...], ...]:
    if games_per_batch % world_size:
        raise ValueError("intent BC global game batch must divide across DDP ranks")
    local_games = games_per_batch // world_size
    if local_games < 1:
        raise ValueError("intent BC needs at least one physical game per rank")
    if len(shards) % games_per_batch:
        raise ValueError("intent BC partition must fill every global game batch")
    result: list[tuple[IntentTeacherShard, ...]] = []
    for offset in range(0, len(shards), games_per_batch):
        global_batch = shards[offset : offset + games_per_batch]
        local = tuple(global_batch[rank::world_size])
        if len(local) != local_games:
            raise RuntimeError("intent BC rank received an incomplete game batch")
        result.append(local)
    return tuple(result)


def _autocast(device: torch.device) -> Any:
    return (
        torch.autocast(device_type="cuda", dtype=torch.bfloat16)
        if device.type == "cuda"
        else nullcontext()
    )


def _step_events(device: torch.device) -> tuple[torch.cuda.Event, torch.cuda.Event] | None:
    if device.type != "cuda":
        return None
    return (
        torch.cuda.Event(enable_timing=True),  # type: ignore[no-untyped-call]
        torch.cuda.Event(enable_timing=True),  # type: ignore[no-untyped-call]
    )


def run_intent_bc_partition(
    model: IntentActorCritic,
    dataset_dir: Path,
    shards: Sequence[IntentTeacherShard],
    partition: Partition,
    settings: IntentBcSettings,
    device: torch.device,
    optimizer: torch.optim.Optimizer | None,
    epoch: int,
    *,
    training_model: nn.Module | None = None,
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
    evaluator = training_model or IntentSequenceEvaluator(model)
    evaluator.train(training)
    model.actor.eval()
    started = time.perf_counter()
    # policy, outcome, total, entropy, W/D/L accuracy, correct choices,
    # non-forced choices, pseudo-steps, episodes, official turns.
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
            with _autocast(device):
                output = evaluator(
                    batch,
                    value_only=False,
                    validate=batches == 0,
                )
                policy = intent_behavior_cloning_loss(
                    output,
                    batch.selected,
                    batch.policy_mask,
                    batch.episode_index,
                    batch.turn_index,
                    batch.episode_count,
                    int(batch.board.shape[1]),
                )
                labels = outcome_labels(batch.outcomes)[batch.episode_index]
                outcome_items = functional.cross_entropy(
                    output.outcome_logits.float(), labels, reduction="none"
                )
                outcome = episode_balanced_mean(
                    outcome_items,
                    batch.episode_index,
                    batch.episode_count,
                )
                total = policy + settings.optimization.outcome_loss_weight * outcome
            if not bool(torch.isfinite(total)):
                raise FloatingPointError("intent BC loss is not finite")
            if optimizer is not None:
                total.backward()  # type: ignore[no-untyped-call]
                torch.nn.utils.clip_grad_norm_(
                    (parameter for parameter in model.parameters() if parameter.requires_grad),
                    settings.optimization.gradient_clip,
                )
                optimizer.step()
                optimizer_steps += 1
            if events is not None:
                events[1].record()
                gpu_step_events.append(events)
            else:
                cpu_step_seconds.append(time.perf_counter() - step_started)

            probabilities = torch.softmax(output.candidate_logits.detach().float(), dim=-1)
            entropy_items = -(probabilities * probabilities.clamp_min(1e-30).log()).sum(dim=-1)
            entropy = episode_balanced_mean(
                entropy_items,
                batch.episode_index,
                batch.episode_count,
                batch.policy_mask,
            )
            predictions = output.candidate_logits.detach().argmax(dim=-1)
            correct = ((predictions == batch.selected) & batch.policy_mask).sum()
            policy_step_tensor = batch.policy_mask.sum()
            outcome_accuracy = episode_balanced_mean(
                (output.outcome_logits.detach().argmax(dim=-1) == labels).float(),
                batch.episode_index,
                batch.episode_count,
            )
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
                        batch.selected.new_tensor(batch.decision_count),
                        batch.selected.new_tensor(episodes),
                        batch.selected.new_tensor(turns),
                    )
                ).double()
            )
            batches += 1
            del output, batch, cpu_batch
    if device.type == "cuda":
        torch.cuda.synchronize(device)
        step_seconds = [start.elapsed_time(stop) / 1000.0 for start, stop in gpu_step_events]
    else:
        step_seconds = cpu_step_seconds
    elapsed = time.perf_counter() - started
    if not step_seconds:
        raise RuntimeError(f"intent BC {partition} partition produced no learner steps")
    first_step = step_seconds[0]
    steady_steps = step_seconds[1:]
    steady_step = sum(steady_steps) / len(steady_steps) if steady_steps else first_step
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
    counters = torch.tensor([batches, optimizer_steps], dtype=torch.int64, device=device)
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
    decisions = int(values[7])
    policy_step_count = int(values[6])
    if not episodes or not batches:
        raise RuntimeError(f"intent BC {partition} partition produced no batches")
    result: dict[str, object] = {
        "joint_turn_nll": values[0] / episodes,
        "terminal_wdl_nll": values[1] / episodes,
        "total_loss": values[2] / episodes,
        "policy_entropy": values[3] / episodes,
        "terminal_wdl_accuracy": values[4] / episodes,
        "teacher_choice_accuracy": values[5] / max(policy_step_count, 1),
        "games": episodes // 2,
        "episodes": episodes,
        "official_turns": turns,
        "pseudo_steps": decisions,
        "policy_steps": policy_step_count,
        "batches": batches,
        "optimizer_steps": optimizer_steps,
        "elapsed_seconds": elapsed,
        "games_per_second": (episodes // 2) / max(elapsed, 1e-9),
        "pseudo_steps_per_second": decisions / max(elapsed, 1e-9),
        "loader_wait_seconds": loader_wait_seconds,
        "loader_cpu_seconds": loader_cpu_seconds,
        "input_materialization_seconds": materialization_seconds,
        "learner_device_seconds": learner_seconds,
        "first_learner_step_seconds": first_step,
        "steady_learner_step_mean_seconds": steady_step,
    }
    return result


__all__ = ["Partition", "run_intent_bc_partition"]
