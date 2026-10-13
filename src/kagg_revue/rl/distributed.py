"""Distributed topology and collectives for one synchronized RL lineage."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import Any, TypeVar, cast

import numpy as np
import torch
from torch import Tensor
from torch import distributed as dist

from kagg_revue.core.observability import throughput
from kagg_revue.rl.data import RolloutMatch
from kagg_revue.rl.rollout.population import opponent_outcome_metrics

_T = TypeVar("_T")


def even_shard(total: int, rank: int, world_size: int) -> range:
    """Return one contiguous equal shard of a global item range."""
    if total < 1:
        raise ValueError("distributed shard total must be positive")
    if world_size < 1 or rank < 0 or rank >= world_size:
        raise ValueError("distributed rank is outside the world")
    if total % world_size:
        raise ValueError("distributed shard total must divide evenly across ranks")
    width = total // world_size
    start = rank * width
    return range(start, start + width)


def local_value(total: int, world_size: int, name: str) -> int:
    """Convert one validated global capacity into its per-rank value."""
    if total < 1 or world_size < 1 or total % world_size:
        raise ValueError(f"{name} must divide evenly across distributed ranks")
    return total // world_size


def _as_int(value: object, name: str) -> int:
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise TypeError(f"distributed {name} is not numeric")
    return int(value)


def _as_float(value: object, name: str) -> float:
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise TypeError(f"distributed {name} is not numeric")
    return float(value)


def aggregate_optimization_summaries(
    summaries: list[dict[str, float]],
) -> dict[str, float]:
    """Combine rank-local PPO diagnostics without duplicating optimizer steps."""
    if not summaries:
        raise ValueError("distributed optimization produced no rank summaries")
    epochs = {summary["epochs_completed"] for summary in summaries}
    minibatches = {summary["minibatches"] for summary in summaries}
    if len(epochs) != 1 or len(minibatches) != 1:
        raise ValueError("distributed ranks completed different optimizer steps")
    turns = sum(summary["optimized_turns"] for summary in summaries)
    decisions = sum(summary["optimized_decisions"] for summary in summaries)
    policy_factors = sum(summary["optimized_policy_factors"] for summary in summaries)

    def weighted(name: str, denominator: str, total: float) -> float:
        if total <= 0.0:
            return 0.0
        return sum(summary[name] * summary[denominator] for summary in summaries) / total

    return {
        "total_loss": sum(summary["total_loss"] for summary in summaries) / len(summaries),
        "policy_loss": weighted("policy_loss", "optimized_policy_factors", policy_factors),
        "value_nll": weighted("value_nll", "optimized_turns", turns),
        "entropy": weighted("entropy", "optimized_policy_factors", policy_factors),
        "approximate_kl": weighted("approximate_kl", "optimized_policy_factors", policy_factors),
        "clip_fraction": weighted("clip_fraction", "optimized_policy_factors", policy_factors),
        "value_accuracy": weighted("value_accuracy", "optimized_turns", turns),
        "value_brier": weighted("value_brier", "optimized_turns", turns),
        "maximum_gradient_norm": max(summary["maximum_gradient_norm"] for summary in summaries),
        "optimized_turns": turns,
        "optimized_decisions": decisions,
        "optimized_policy_factors": policy_factors,
        "epochs_completed": epochs.pop(),
        "minibatches": minibatches.pop(),
    }


def aggregate_rollout_shards(
    payloads: list[dict[str, object]],
) -> tuple[dict[str, object], tuple[RolloutMatch, ...]]:
    """Combine concurrent rank-local rollout summaries into one global panel."""
    if not payloads:
        raise ValueError("distributed rollout produced no rank payloads")
    summaries = [cast(dict[str, object], payload["summary"]) for payload in payloads]
    matches = tuple(
        match
        for payload in payloads
        for match in cast(tuple[RolloutMatch, ...], payload["matches"])
    )
    matches = tuple(
        sorted(
            matches,
            key=lambda match: (match.seed, match.opponent_id, match.candidate_seat),
        )
    )
    elapsed = max(_as_float(summary["elapsed_seconds"], "rollout elapsed") for summary in summaries)
    turns = sum(_as_int(summary["turns"], "rollout turns") for summary in summaries)
    decisions = sum(_as_int(summary["decisions"], "rollout decisions") for summary in summaries)
    trajectories = sum(
        _as_int(summary["training_trajectories"], "training trajectories") for summary in summaries
    )
    mean_training_return = (
        sum(
            _as_float(summary["mean_training_return"], "mean training return")
            * _as_int(summary["training_trajectories"], "training trajectories")
            for summary in summaries
        )
        / trajectories
    )
    training_return_minimum = min(
        _as_float(summary["training_return_minimum"], "minimum training return")
        for summary in summaries
    )
    training_return_maximum = max(
        _as_float(summary["training_return_maximum"], "maximum training return")
        for summary in summaries
    )
    trajectory_outcomes = {
        outcome
        for payload in payloads
        for outcome in cast(tuple[int, ...], payload["trajectory_outcomes"])
    }
    trajectory_opponents = tuple(
        opponent_id
        for payload in payloads
        for opponent_id in cast(tuple[str, ...], payload["trajectory_opponents"])
    )
    actor_seconds = max(
        _as_float(summary["actor_elapsed_seconds"], "rollout actor elapsed")
        for summary in summaries
    )
    environment_seconds = max(
        _as_float(summary["environment_elapsed_seconds"], "rollout environment elapsed")
        for summary in summaries
    )
    behavior_seconds = max(
        _as_float(summary["behavior_evaluation_seconds"], "behavior elapsed")
        for summary in summaries
    )

    def pipeline_sum(name: str) -> float:
        return sum(
            _as_float(
                cast(Mapping[str, object], summary["pipeline"]).get(name, 0.0),
                f"rollout pipeline {name}",
            )
            for summary in summaries
        )

    def pipeline_max(name: str) -> float:
        return max(
            _as_float(
                cast(Mapping[str, object], summary["pipeline"]).get(name, 0.0),
                f"rollout pipeline {name}",
            )
            for summary in summaries
        )

    pipeline = {
        "device": "distributed",
        "distributed_world_size": len(payloads),
        "actor_seconds": actor_seconds,
        "actor_work_seconds": pipeline_sum("actor_work_seconds"),
        "actor_input_work_seconds": pipeline_sum("actor_input_work_seconds"),
        "actor_policy_work_seconds": pipeline_sum("actor_policy_work_seconds"),
        "actor_postprocess_work_seconds": pipeline_sum("actor_postprocess_work_seconds"),
        "environment_seconds": environment_seconds,
        "environment_tasks": pipeline_sum("environment_tasks"),
        "environment_wait_seconds": pipeline_sum("environment_wait_seconds"),
        "cuda_graph_capture_seconds": pipeline_max("cuda_graph_capture_seconds"),
        "cuda_graph_groups": pipeline_sum("cuda_graph_groups"),
        "cuda_graph_reuse_groups": pipeline_sum("cuda_graph_reuse_groups"),
        "full_actor_turn_cuda_graph_groups": pipeline_sum("full_actor_turn_cuda_graph_groups"),
        "whole_turn_cuda_graph_groups": pipeline_sum("whole_turn_cuda_graph_groups"),
        "whole_turn_cuda_graph_reuse_groups": pipeline_sum("whole_turn_cuda_graph_reuse_groups"),
        "historical_serial_turns": pipeline_sum("historical_serial_turns"),
        "actor_streams": pipeline_sum("actor_streams"),
        "cpu_workers": pipeline_sum("cpu_workers"),
        "groups": pipeline_sum("groups"),
        "resident_rollout_lanes": pipeline_sum("resident_rollout_lanes"),
        "pipeline_depth": pipeline_max("pipeline_depth"),
        "gpu_policy_session": all(
            bool(cast(Mapping[str, object], summary["pipeline"])["gpu_policy_session"])
            for summary in summaries
        ),
        "workers": [
            {
                "rank": payload["rank"],
                "device": payload["device"],
                "diagnostics": cast(dict[str, object], payload["summary"])["pipeline"],
            }
            for payload in payloads
        ],
    }
    capacities = [cast(Mapping[str, object], summary["capacity"]) for summary in summaries]
    capacity = {
        "distributed_world_size": len(payloads),
        "games": len(matches),
        "training_trajectories": trajectories,
        "maximum_actor_rows_per_rank": max(
            _as_int(value["maximum_actor_rows"], "maximum actor rows") for value in capacities
        ),
        "total_actor_rows": sum(
            _as_int(value["total_actor_rows"], "total actor rows") for value in capacities
        ),
        "concurrent_actor_rows": sum(
            _as_int(value["concurrent_actor_rows"], "concurrent actor rows") for value in capacities
        ),
        "host_estimated_bytes": sum(
            _as_int(value["host_estimated_bytes"], "host estimated bytes") for value in capacities
        ),
        "gpu_estimated_bytes": sum(
            _as_int(value["gpu_estimated_bytes"], "GPU estimated bytes") for value in capacities
        ),
        "workers": [dict(value) for value in capacities],
    }
    coverage_rows = [
        cast(Mapping[str, object], summary["migration_coverage"]) for summary in summaries
    ]

    def coverage_vector(name: str, *, sum_values: bool) -> list[int]:
        rows = [cast(list[object], coverage[name]) for coverage in coverage_rows]
        lengths = {len(row) for row in rows}
        if len(lengths) != 1:
            raise ValueError(f"distributed migration coverage {name} has mixed shapes")
        if not rows:
            return []
        if sum_values:
            return [
                sum(_as_int(row[index], f"migration coverage {name}") for row in rows)
                for index in range(len(rows[0]))
            ]
        reference = [_as_int(value, f"migration coverage {name}") for value in rows[0]]
        if any(
            [_as_int(value, f"migration coverage {name}") for value in row] != reference
            for row in rows[1:]
        ):
            raise ValueError(f"distributed migration coverage {name} differs by rank")
        return reference

    migration_coverage = {
        "unit_slot_indices": coverage_vector("unit_slot_indices", sum_values=False),
        "own_unit_slot_turns": coverage_vector("own_unit_slot_turns", sum_values=True),
        "opponent_unit_slot_turns": coverage_vector("opponent_unit_slot_turns", sum_values=True),
        "decision_position_indices": coverage_vector("decision_position_indices", sum_values=False),
        "decision_position_turns": coverage_vector("decision_position_turns", sum_values=True),
        "inventory_order_nonzero_by_item": coverage_vector(
            "inventory_order_nonzero_by_item", sum_values=True
        ),
        "maximum_own_units": max(
            _as_int(row["maximum_own_units"], "maximum own units") for row in coverage_rows
        ),
        "maximum_opponent_units": max(
            _as_int(row["maximum_opponent_units"], "maximum opponent units")
            for row in coverage_rows
        ),
    }
    absolute_reward = (
        sum(
            _as_float(summary["mean_absolute_potential_reward"], "mean reward")
            * _as_int(summary["turns"], "rollout turns")
            for summary in summaries
        )
        / turns
    )
    outcomes = [match.outcome for match in matches]
    rollout: dict[str, object] = {
        "games": len(matches),
        "training_trajectories": trajectories,
        "wins": sum(outcome > 0 for outcome in outcomes),
        "ties": sum(outcome == 0 for outcome in outcomes),
        "losses": sum(outcome < 0 for outcome in outcomes),
        "outcome_classes": len(set(outcomes)),
        "training_outcome_classes": len(trajectory_outcomes),
        "training_return_minimum": training_return_minimum,
        "training_return_maximum": training_return_maximum,
        "mean_training_return": mean_training_return,
        "turns": turns,
        "decisions": decisions,
        "elapsed_seconds": elapsed,
        "games_per_second": throughput(len(matches), elapsed),
        "training_trajectories_per_second": throughput(trajectories, elapsed),
        "turns_per_second": throughput(turns, elapsed),
        "decisions_per_second": throughput(decisions, elapsed),
        "mean_terminal_cash": float(np.mean([match.terminal_cash for match in matches])),
        "mean_cash_difference": float(
            np.mean([match.terminal_cash - match.opponent_cash for match in matches])
        ),
        "opponents": opponent_outcome_metrics(matches, trajectory_opponents),
        "mean_absolute_potential_reward": absolute_reward,
        "maximum_telescoping_residual": max(
            _as_float(summary["maximum_telescoping_residual"], "telescoping residual")
            for summary in summaries
        ),
        "actor_elapsed_seconds": actor_seconds,
        "environment_elapsed_seconds": environment_seconds,
        "behavior_evaluation_seconds": behavior_seconds,
        "pipeline_unattributed_seconds": max(
            0.0,
            elapsed - actor_seconds - environment_seconds - behavior_seconds,
        ),
        "pipeline": pipeline,
        "capacity": capacity,
        "migration_coverage": migration_coverage,
    }
    return rollout, matches


def partition_cpus(cpus: tuple[int, ...], rank: int, world_size: int) -> tuple[int, ...]:
    """Return one non-overlapping balanced CPU-affinity partition."""
    if len(cpus) < world_size:
        raise ValueError("distributed training has fewer CPUs than ranks")
    if len(set(cpus)) != len(cpus):
        raise ValueError("CPU affinity contains duplicates")
    base, remainder = divmod(len(cpus), world_size)
    width = base + int(rank < remainder)
    start = rank * base + min(rank, remainder)
    return cpus[start : start + width]


@dataclass(frozen=True)
class DistributedContext:
    """One rank's immutable device identity and collective boundary."""

    rank: int
    world_size: int
    device: torch.device
    cpu_affinity: tuple[int, ...]
    control_group: Any | None = None

    @property
    def enabled(self) -> bool:
        """Whether collectives span more than one process."""
        return self.world_size > 1

    @property
    def primary(self) -> bool:
        """Whether this rank owns artifacts and human-readable logging."""
        return self.rank == 0

    def all_gather(self, value: _T) -> list[_T]:
        """Gather one small Python payload on every rank."""
        if not self.enabled:
            return [value]
        gathered: list[Any] = [None] * self.world_size
        dist.all_gather_object(gathered, value, group=self.control_group)
        return cast(list[_T], gathered)

    def broadcast(self, value: _T | None) -> _T:
        """Broadcast one small primary-rank payload to the full world."""
        if not self.enabled:
            if value is None:
                raise ValueError("single-rank broadcast value is absent")
            return value
        payload: list[Any] = [value if self.primary else None]
        if self.control_group is None:
            dist.broadcast_object_list(payload, src=0, device=self.device)
        else:
            dist.broadcast_object_list(payload, src=0, group=self.control_group)
        if payload[0] is None:
            raise RuntimeError("distributed primary broadcast an absent value")
        return cast(_T, payload[0])

    def consistent_text(self, value: str, label: str) -> str:
        """Require the same compact model identity on every rank."""
        values = self.all_gather(value)
        if any(candidate != values[0] for candidate in values[1:]):
            raise RuntimeError(f"distributed {label} differs across ranks")
        return values[0]

    def barrier(self) -> None:
        """Wait until every rank reaches an update boundary."""
        if self.enabled:
            if self.control_group is None:
                dist.barrier(device_ids=[self.device.index])
            else:
                dist.barrier(group=self.control_group)

    def broadcast_tensors(self, tensors: tuple[Tensor, ...], source_rank: int) -> None:
        """Copy a small fixed tensor state from one rank without object serialization."""
        if source_rank < 0 or source_rank >= self.world_size:
            raise ValueError("distributed tensor source rank is outside the world")
        if not self.enabled:
            if source_rank != 0:
                raise ValueError("single-rank tensor broadcast source must be rank zero")
            return
        for tensor in tensors:
            if tensor.device != self.device:
                raise ValueError("distributed tensor broadcast must use the rank device")
            dist.broadcast(tensor, src=source_rank)

    def maximum(self, value: float) -> float:
        """Return the maximum scalar observed on any rank."""
        if not self.enabled:
            return value
        tensor = torch.tensor(value, dtype=torch.float64, device=self.device)
        dist.all_reduce(tensor, op=dist.ReduceOp.MAX)
        return float(tensor.item())

    def loss_scales(self, local_counts: Tensor) -> Tensor:
        """Scale local means so DDP's gradient average equals the global mean."""
        if local_counts.ndim != 1 or not local_counts.is_floating_point():
            raise ValueError("distributed loss counts must be one floating vector")
        if not self.enabled:
            return torch.ones_like(local_counts)
        global_counts = local_counts.detach().clone()
        dist.all_reduce(global_counts, op=dist.ReduceOp.SUM)
        scale = self.world_size * local_counts.detach() / global_counts.clamp_min(1.0)
        return torch.where(global_counts > 0.0, scale, torch.zeros_like(scale))


def initialize_context(
    rank: int,
    devices: tuple[str, ...],
    rendezvous: Path,
) -> DistributedContext:
    """Bind one CUDA rank, partition CPUs, and initialize NCCL."""
    world_size = len(devices)
    device = torch.device(devices[rank])
    if device.type != "cuda" or device.index is None:
        raise ValueError("distributed training requires indexed CUDA devices")
    torch.cuda.set_device(device)
    allowed = tuple(sorted(os.sched_getaffinity(0)))
    affinity = partition_cpus(allowed, rank, world_size)
    os.sched_setaffinity(0, affinity)
    dist.init_process_group(
        backend="nccl",
        init_method=f"file://{rendezvous.resolve()}",
        rank=rank,
        world_size=world_size,
        timeout=timedelta(minutes=30),
    )
    os.environ.setdefault("GLOO_SOCKET_IFNAME", "lo")
    control_group = dist.new_group(backend="gloo", timeout=timedelta(minutes=30))
    return DistributedContext(
        rank=rank,
        world_size=world_size,
        device=device,
        cpu_affinity=affinity,
        control_group=control_group,
    )


def single_process_context(device: torch.device) -> DistributedContext:
    """Return the collective-free compatibility topology."""
    affinity = tuple(sorted(os.sched_getaffinity(0)))
    return DistributedContext(rank=0, world_size=1, device=device, cpu_affinity=affinity)


def destroy_context(context: DistributedContext) -> None:
    """Close NCCL after every rank has left the training loop."""
    if context.enabled and dist.is_initialized():
        if context.control_group is not None:
            dist.destroy_process_group(context.control_group)
        dist.destroy_process_group()


__all__ = [
    "DistributedContext",
    "aggregate_optimization_summaries",
    "aggregate_rollout_shards",
    "destroy_context",
    "even_shard",
    "initialize_context",
    "local_value",
    "partition_cpus",
    "single_process_context",
]
