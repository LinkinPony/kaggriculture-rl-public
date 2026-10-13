"""Compact exact behavior records for compiler-in-the-loop task PPO."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, cast

import numpy as np
import torch
from numpy.typing import NDArray
from torch import Tensor

from kagg_revue.policy.tasks.grammar import (
    FactorizedTaskDecisionInputs,
    FactorizedTaskMasks,
    TaskActions,
    TaskCatalog,
    TaskConditionalMasks,
    TaskDecisionInputs,
)
from kagg_revue.policy.tasks.native import NativeTaskContract
from kagg_revue.policy.tasks.runtime import TaskDecisionTrace
from kagg_revue.rl.data import (
    TensorRolloutBatch,
    Trajectory,
    TrajectoryTurns,
    collate_trajectories,
)
from kagg_revue.rl.tasks.compact import (
    CompactTaskTurnRecord,
    collate_compact_task_records,
)
from kagg_revue.rl.tasks.storage import CompactTaskEpisodeTurns

IntArray = NDArray[np.int64]
FloatArray = NDArray[np.float32]
HalfArray = NDArray[np.float16]
BoolArray = NDArray[np.bool_]


def _stage_numpy_batches(
    values: tuple[tuple[Tensor, torch.dtype], ...],
) -> tuple[NDArray[Any], ...]:
    """Stage aligned tensors to host with one CUDA stream synchronization."""
    if not values:
        return ()
    device = values[0][0].device
    sources: list[Tensor] = []
    staged: list[Tensor] = []
    for value, dtype in values:
        if value.device != device:
            raise ValueError("task trace tensors must share one device")
        source = value.detach().to(dtype=dtype)
        sources.append(source)
        if device.type == "cuda":
            target = torch.empty_like(source, device="cpu", pin_memory=True)
            target.copy_(source, non_blocking=True)
        else:
            target = source.cpu()
        staged.append(target)
    if device.type == "cuda":
        torch.cuda.current_stream(device).synchronize()
    return tuple(value.numpy() for value in staged)


def _copy(value: object, dtype: np.dtype[Any]) -> NDArray[Any]:
    result = np.array(value, dtype=dtype, order="C", copy=True)
    result.flags.writeable = False
    return result


@dataclass(frozen=True)
class TaskDecisionRecord:
    """One task-level policy sample with every exact conditional mask."""

    episode_index: int
    turn_index: int
    root_features: FloatArray
    prefix_fields: NDArray[np.int16]
    prefix_mask: BoolArray
    candidate_features: HalfArray
    candidate_mask: BoolArray
    candidate_arrivals: NDArray[np.int16]
    mode_mask: BoolArray
    available_at: int
    day_end: int
    action: IntArray
    quantity_mask: BoolArray
    earliest_mask: BoolArray
    deadline_mask: BoolArray
    factor_mask: BoolArray
    old_joint_log_probability: float
    old_value: float

    def __post_init__(self) -> None:
        """Canonicalize, validate, and freeze a durable task sample."""
        if self.episode_index < 0 or self.turn_index < 0:
            raise ValueError("task record episode and turn indices must be non-negative")
        root = cast(FloatArray, _copy(self.root_features, np.dtype(np.float32)))
        prefix_fields = cast(NDArray[np.int16], _copy(self.prefix_fields, np.dtype(np.int16)))
        prefix_mask = cast(BoolArray, _copy(self.prefix_mask, np.dtype(np.bool_)))
        candidate_features = cast(HalfArray, _copy(self.candidate_features, np.dtype(np.float16)))
        candidate_mask = cast(BoolArray, _copy(self.candidate_mask, np.dtype(np.bool_)))
        arrivals = cast(
            NDArray[np.int16],
            _copy(self.candidate_arrivals, np.dtype(np.int16)),
        )
        mode = cast(BoolArray, _copy(self.mode_mask, np.dtype(np.bool_)))
        action = cast(IntArray, _copy(self.action, np.dtype(np.int64)))
        quantity = cast(BoolArray, _copy(self.quantity_mask, np.dtype(np.bool_)))
        earliest = cast(BoolArray, _copy(self.earliest_mask, np.dtype(np.bool_)))
        deadline = cast(BoolArray, _copy(self.deadline_mask, np.dtype(np.bool_)))
        factors = cast(BoolArray, _copy(self.factor_mask, np.dtype(np.bool_)))
        candidates = candidate_mask.shape[0]
        prefix = prefix_mask.shape[0]
        if (
            root.ndim != 1
            or prefix_fields.ndim != 2
            or prefix_fields.shape[0] != prefix
            or candidate_features.ndim != 2
            or candidate_features.shape[0] != candidates
            or arrivals.shape != (candidates,)
            or mode.shape != (2,)
            or action.shape != (5,)
            or factors.shape != (5,)
            or quantity.ndim != 1
            or earliest.ndim != 1
            or deadline.shape != earliest.shape
        ):
            raise ValueError("task record tensors do not follow the task ABI")
        if not candidate_mask[0] or not mode.any():
            raise ValueError("task record lacks canonical END or a suffix mode")
        if not quantity.any() or not earliest.any() or not deadline.any():
            raise ValueError("task record contains an empty conditional mask")
        if (
            not np.isfinite(root).all()
            or not np.isfinite(candidate_features).all()
            or not np.isfinite(self.old_joint_log_probability)
            or not np.isfinite(self.old_value)
        ):
            raise ValueError("task record contains a non-finite model value")
        for name, value in (
            ("root_features", root),
            ("prefix_fields", prefix_fields),
            ("prefix_mask", prefix_mask),
            ("candidate_features", candidate_features),
            ("candidate_mask", candidate_mask),
            ("candidate_arrivals", arrivals),
            ("mode_mask", mode),
            ("action", action),
            ("quantity_mask", quantity),
            ("earliest_mask", earliest),
            ("deadline_mask", deadline),
            ("factor_mask", factors),
        ):
            object.__setattr__(self, name, value)


@dataclass(frozen=True)
class TaskDecisionBatch:
    """Device tensors for a set of task samples from complete episodes."""

    inputs: TaskDecisionInputs | FactorizedTaskDecisionInputs
    actions: TaskActions
    masks: TaskConditionalMasks | FactorizedTaskMasks
    old_joint_log_probability: Tensor
    old_values: Tensor
    episode_index: Tensor
    turn_index: Tensor


@dataclass(frozen=True)
class TaskTapeEpisode:
    """One complete official match with market and task behavior factors."""

    trajectory: Trajectory
    market_factor_mask: BoolArray
    task_records: tuple[TaskDecisionRecord, ...]
    compact_task_turns: Sequence[CompactTaskTurnRecord] = ()

    def __post_init__(self) -> None:
        """Require one market-factor row per stored official turn."""
        mask = cast(BoolArray, _copy(self.market_factor_mask, np.dtype(np.bool_)))
        if mask.ndim != 2 or mask.shape[0] != len(self.trajectory.turns):
            raise ValueError("market factor mask must align with episode turns")
        if self.task_records and self.compact_task_turns:
            raise ValueError("task episode cannot mix expanded and compact records")
        if not self.task_records and not self.compact_task_turns:
            raise ValueError("task episode must contain task decisions")
        maximum_compact_turn = (
            self.compact_task_turns.maximum_turn_index
            if isinstance(self.compact_task_turns, CompactTaskEpisodeTurns)
            else max(
                (record.turn_index for record in self.compact_task_turns),
                default=-1,
            )
        )
        if maximum_compact_turn >= len(self.trajectory.turns):
            raise ValueError("compact task turn lies outside its episode")
        object.__setattr__(self, "market_factor_mask", mask)


@dataclass(frozen=True)
class TaskTapeBatch:
    """Collated complete episodes and their variable task decisions."""

    market: TensorRolloutBatch
    market_factor_mask: Tensor
    tasks: TaskDecisionBatch


def records_from_trace(
    trace: TaskDecisionTrace,
    episode_indices: IntArray,
    turn_index: int,
) -> tuple[TaskDecisionRecord, ...]:
    """Copy one inference batch into durable compact task records."""
    return records_from_traces((trace,), episode_indices, turn_index)


def records_from_traces(
    traces: tuple[TaskDecisionTrace, ...],
    episode_indices: IntArray,
    turn_index: int,
) -> tuple[TaskDecisionRecord, ...]:
    """Stage every task decision from one turn with one CUDA synchronization."""
    if episode_indices.ndim != 1:
        raise ValueError("task episode identities must be a vector")
    if not traces:
        return ()
    row_batches: list[IntArray] = []
    for trace in traces:
        rows = trace.row_indices
        if rows.ndim != 1:
            raise ValueError("task trace row identities must be vectors")
        if rows.size != trace.output.joint_log_probability.shape[0]:
            raise ValueError("task trace identities and policy output differ")
        if rows.size and int(rows.max()) >= episode_indices.shape[0]:
            raise ValueError("task trace row lies outside the episode map")
        row_batches.append(rows)
    rows = np.concatenate(row_batches)

    def inputs(name: str) -> Tensor:
        return torch.cat([getattr(trace.inputs, name) for trace in traces])

    def outputs(name: str) -> Tensor:
        return torch.cat([getattr(trace.output, name) for trace in traces])

    def masks(name: str) -> Tensor:
        return torch.cat([getattr(trace.output.masks, name) for trace in traces])

    action_tensor = torch.cat(
        [
            torch.stack(
                (
                    trace.output.actions.mode,
                    trace.output.actions.candidate,
                    trace.output.actions.quantity,
                    trace.output.actions.earliest,
                    trace.output.actions.deadline,
                ),
                dim=1,
            )
            for trace in traces
        ]
    )
    (
        root_features,
        prefix_fields,
        prefix_mask,
        candidate_features,
        candidate_mask,
        candidate_arrivals,
        mode_mask,
        available_at,
        day_end,
        action_values,
        quantity_mask,
        earliest_mask,
        deadline_mask,
        factor_mask,
        old_joint_log_probability,
        old_value,
    ) = _stage_numpy_batches(
        (
            (inputs("root_features"), torch.float32),
            (inputs("prefix_fields"), torch.int16),
            (inputs("prefix_mask"), torch.bool),
            (inputs("candidate_features"), torch.float16),
            (inputs("candidate_mask"), torch.bool),
            (inputs("candidate_arrivals"), torch.int16),
            (masks("mode"), torch.bool),
            (inputs("available_at"), torch.int64),
            (inputs("day_end"), torch.int64),
            (action_tensor, torch.int64),
            (masks("quantity"), torch.bool),
            (masks("earliest"), torch.bool),
            (masks("deadline"), torch.bool),
            (masks("factors"), torch.bool),
            (outputs("joint_log_probability"), torch.float32),
            (outputs("value"), torch.float32),
        )
    )
    records: list[TaskDecisionRecord] = []
    for local, row in enumerate(rows):
        records.append(
            TaskDecisionRecord(
                episode_index=int(episode_indices[int(row)]),
                turn_index=turn_index,
                root_features=root_features[local],
                prefix_fields=prefix_fields[local],
                prefix_mask=prefix_mask[local],
                candidate_features=candidate_features[local],
                candidate_mask=candidate_mask[local],
                candidate_arrivals=candidate_arrivals[local],
                mode_mask=mode_mask[local],
                available_at=int(available_at[local]),
                day_end=int(day_end[local]),
                action=action_values[local],
                quantity_mask=quantity_mask[local],
                earliest_mask=earliest_mask[local],
                deadline_mask=deadline_mask[local],
                factor_mask=factor_mask[local],
                old_joint_log_probability=float(old_joint_log_probability[local]),
                old_value=float(old_value[local]),
            )
        )
    return tuple(records)


def collate_task_records(
    records: list[TaskDecisionRecord],
    *,
    context_width: int,
    device: torch.device,
) -> TaskDecisionBatch:
    """Stack exact task records; the shared encoder replaces zero contexts."""
    if not records:
        raise ValueError("cannot collate an empty task decision batch")

    def tensor(name: str, dtype: torch.dtype) -> Tensor:
        values = np.stack([getattr(record, name) for record in records])
        return torch.as_tensor(values, dtype=dtype, device=device)

    action = tensor("action", torch.long)
    inputs = TaskDecisionInputs(
        context=torch.zeros((len(records), context_width), dtype=torch.float32, device=device),
        root_features=tensor("root_features", torch.float32),
        prefix_fields=tensor("prefix_fields", torch.long),
        prefix_mask=tensor("prefix_mask", torch.bool),
        candidate_features=tensor("candidate_features", torch.float32),
        candidate_mask=tensor("candidate_mask", torch.bool),
        candidate_arrivals=tensor("candidate_arrivals", torch.long),
        mode_mask=tensor("mode_mask", torch.bool),
        available_at=torch.tensor(
            [record.available_at for record in records],
            dtype=torch.long,
            device=device,
        ),
        day_end=torch.tensor(
            [record.day_end for record in records],
            dtype=torch.long,
            device=device,
        ),
        prefix_length=max(int(np.count_nonzero(record.prefix_mask)) for record in records),
    )
    return TaskDecisionBatch(
        inputs=inputs,
        actions=TaskActions(
            mode=action[:, 0],
            candidate=action[:, 1],
            quantity=action[:, 2],
            earliest=action[:, 3],
            deadline=action[:, 4],
        ),
        masks=TaskConditionalMasks(
            mode=inputs.mode_mask,
            candidate=inputs.candidate_mask,
            quantity=tensor("quantity_mask", torch.bool),
            earliest=tensor("earliest_mask", torch.bool),
            deadline=tensor("deadline_mask", torch.bool),
            factors=tensor("factor_mask", torch.bool),
        ),
        old_joint_log_probability=torch.tensor(
            [record.old_joint_log_probability for record in records],
            dtype=torch.float32,
            device=device,
        ),
        old_values=torch.tensor(
            [record.old_value for record in records],
            dtype=torch.float32,
            device=device,
        ),
        episode_index=torch.tensor(
            [record.episode_index for record in records],
            dtype=torch.long,
            device=device,
        ),
        turn_index=torch.tensor(
            [record.turn_index for record in records],
            dtype=torch.long,
            device=device,
        ),
    )


def collate_task_episodes(
    episodes: list[TaskTapeEpisode],
    *,
    context_width: int,
    device: torch.device,
    contract: NativeTaskContract | None = None,
    factorized: bool = False,
    history_window: int = 64,
    task_catalog: TaskCatalog | None = None,
) -> TaskTapeBatch:
    """Collate whole matches while remapping task rows to local episode ids."""
    if not episodes:
        raise ValueError("cannot collate an empty task-tape episode batch")
    trajectories = [episode.trajectory for episode in episodes]
    market = collate_trajectories(trajectories, device)
    decisions = market.actions.shape[2]
    factor_mask = torch.zeros_like(market.decision_mask)
    records: list[TaskDecisionRecord] = []
    compact_records: list[CompactTaskTurnRecord] = []
    compact_economic_states: list[NDArray[Any]] = []
    compact_episode_indices: list[int] = []
    for episode_index, episode in enumerate(episodes):
        turns, width = episode.market_factor_mask.shape
        if width < decisions:
            raise ValueError("stored market factor width is below the collated actions")
        factor_mask[episode_index, :turns] = torch.tensor(
            episode.market_factor_mask[:, :decisions],
            dtype=torch.bool,
            device=device,
        )
        records.extend(
            replace(record, episode_index=episode_index) for record in episode.task_records
        )
        for record in episode.compact_task_turns:
            compact_records.append(record)
            trajectory_turns = episode.trajectory.turns
            compact_economic_states.append(
                trajectory_turns.economic_state[record.turn_index]
                if isinstance(trajectory_turns, TrajectoryTurns)
                else trajectory_turns[record.turn_index].economic_state
            )
            compact_episode_indices.append(episode_index)
    if records and compact_records:
        raise ValueError("task minibatch cannot mix expanded and compact episodes")
    if compact_records:
        if contract is None:
            raise ValueError("compact task collation requires the native contract")
        tasks = collate_compact_task_records(
            compact_records,
            compact_economic_states,
            np.asarray(compact_episode_indices, dtype=np.int64),
            context_width=context_width,
            contract=contract,
            device=device,
            factorized=factorized,
            history_window=history_window,
            catalog=task_catalog,
        )
    else:
        tasks = collate_task_records(
            records,
            context_width=context_width,
            device=device,
        )
    return TaskTapeBatch(
        market=market,
        market_factor_mask=factor_mask,
        tasks=tasks,
    )


def save_task_records(
    path: Path,
    records: list[TaskDecisionRecord],
    *,
    abi_version: str,
    catalog_fingerprint: str,
) -> None:
    """Write one bounded field-major NPZ shard with artifact identities."""
    if path.suffix != ".npz" or not records:
        raise ValueError("task decision shard must be a nonempty .npz file")
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = (
        "root_features",
        "prefix_fields",
        "prefix_mask",
        "candidate_features",
        "candidate_mask",
        "candidate_arrivals",
        "mode_mask",
        "action",
        "quantity_mask",
        "earliest_mask",
        "deadline_mask",
        "factor_mask",
    )
    arrays = {name: np.stack([getattr(record, name) for record in records]) for name in fields}
    arrays.update(
        episode_index=np.asarray([record.episode_index for record in records], dtype=np.int64),
        turn_index=np.asarray([record.turn_index for record in records], dtype=np.int64),
        available_at=np.asarray([record.available_at for record in records], dtype=np.int16),
        day_end=np.asarray([record.day_end for record in records], dtype=np.int16),
        old_joint_log_probability=np.asarray(
            [record.old_joint_log_probability for record in records], dtype=np.float32
        ),
        old_value=np.asarray([record.old_value for record in records], dtype=np.float32),
        abi_version=np.asarray(abi_version),
        catalog_fingerprint=np.asarray(catalog_fingerprint),
    )
    np.savez_compressed(str(path), **cast(dict[str, Any], arrays))


__all__ = [
    "TaskDecisionBatch",
    "TaskDecisionRecord",
    "TaskTapeBatch",
    "TaskTapeEpisode",
    "collate_task_episodes",
    "collate_task_records",
    "records_from_trace",
    "save_task_records",
]
