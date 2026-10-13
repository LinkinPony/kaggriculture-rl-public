"""Lossless K=2 replay translation with exact native decision masks."""

from __future__ import annotations

import hashlib
import random
from collections import Counter, deque
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, cast

import numpy as np
import torch
from numpy.typing import NDArray

from kagg_revue.bc.replay import ReplayRejected
from kagg_revue.bc.tasks.replay import ReplaySequence
from kagg_revue.policy.tasks.contract import ITEMS, SuffixMode, UnitTask
from kagg_revue.policy.tasks.grammar import (
    FactorizedTaskDecisionInputs,
    TaskActions,
    TaskDecisionInputs,
    conditional_masks,
    factorized_conditional_masks,
)
from kagg_revue.policy.tasks.native import NativeTaskContract
from kagg_revue.rl.tasks.data import TaskDecisionRecord
from kagg_revue.rl.tasks.replay import UnitTraceStep, compress_unit_trace


@dataclass(frozen=True)
class SampledTaskRecord:
    """One uniformly sampled exact task decision and its stream identity."""

    stream_index: int
    record: TaskDecisionRecord | FactorizedTaskRecord


@dataclass(frozen=True)
class FactorizedTaskRecord:
    """One sampled typed decision backed by compact planner facts."""

    turn_index: int
    root_features: NDArray[np.float32]
    prefix_fields: NDArray[np.int16]
    prefix_mask: NDArray[np.bool_]
    current_unit: int
    current_x: int
    current_y: int
    target_counts: NDArray[np.int16]
    resource_counts: NDArray[np.int16]
    mode_mask: NDArray[np.bool_]
    available_at: int
    day_end: int
    action: NDArray[np.int64]
    operation_mask: NDArray[np.bool_]
    argument_mask: NDArray[np.bool_]
    target_mask: NDArray[np.bool_]
    quantity_mask: NDArray[np.bool_]
    earliest_mask: NDArray[np.bool_]
    deadline_mask: NDArray[np.bool_]
    factor_mask: NDArray[np.bool_]


@dataclass(frozen=True)
class TranslatedSequence:
    """One seat's sampled BC records after complete-stream reconstruction."""

    episode_id: str
    seat: int
    context: NDArray[np.float16]
    economic_state: NDArray[np.int32] | None
    records: tuple[SampledTaskRecord, ...]
    statistics: Mapping[str, object]
    factorized: bool = False


@dataclass(frozen=True)
class _RawSample:
    stream_index: int
    turn_index: int
    root_features: NDArray[np.float32]
    prefix_fields: NDArray[np.int16]
    prefix_mask: NDArray[np.bool_]
    candidate_features: NDArray[np.float16]
    candidate_mask: NDArray[np.bool_]
    candidate_arrivals: NDArray[np.int16]
    mode_mask: NDArray[np.bool_]
    available_at: int
    day_end: int
    action: NDArray[np.int64]


@dataclass(frozen=True)
class _FactorizedRawSample:
    """Compact retained row for factorized BC preparation."""

    stream_index: int
    turn_index: int
    root_features: NDArray[np.float32]
    prefix_fields: NDArray[np.int16]
    prefix_mask: NDArray[np.bool_]
    current_unit: int
    current_x: int
    current_y: int
    target_counts: NDArray[np.int16]
    resource_counts: NDArray[np.int16]
    mode_mask: NDArray[np.bool_]
    available_at: int
    day_end: int
    action: NDArray[np.int64]


class _Reservoir:
    """Deterministic uniform sample without retaining the complete decision stream."""

    def __init__(self, capacity: int, seed: int) -> None:
        self._capacity = capacity
        self._random = random.Random(seed)
        self._samples: list[_RawSample | _FactorizedRawSample] = []
        self.seen = 0

    def offer(self) -> int | None:
        """Return the retained slot, avoiding copies for discarded stream rows."""
        self.seen += 1
        if len(self._samples) < self._capacity:
            return len(self._samples)
        replacement = self._random.randrange(self.seen)
        if replacement < self._capacity:
            return replacement
        return None

    def store(self, slot: int, sample: _RawSample | _FactorizedRawSample) -> None:
        """Install a copied sample in the slot returned by :meth:`offer`."""
        if slot == len(self._samples):
            self._samples.append(sample)
        else:
            self._samples[slot] = sample

    def selected(self) -> list[_RawSample | _FactorizedRawSample]:
        """Return sampled rows in original stream order."""
        return sorted(self._samples, key=lambda sample: sample.stream_index)


def _sample_seed(seed: int, episode_id: str, seat: int) -> int:
    digest = hashlib.sha256(f"{seed}:{episode_id}:{seat}".encode()).digest()
    return int.from_bytes(digest[:8], byteorder="little", signed=False)


def _candidate_lookup(contract: NativeTaskContract) -> dict[tuple[int, int, int, int], int]:
    catalog = contract.catalog
    return {
        (int(operation), int(argument), int(target[0]), int(target[1])): index
        for index, (operation, argument, target) in enumerate(
            zip(
                catalog.operations.tolist(),
                catalog.arguments.tolist(),
                catalog.targets.tolist(),
                strict=True,
            )
        )
    }


def _candidate_index(
    task: UnitTask,
    lookup: Mapping[tuple[int, int, int, int], int],
) -> int:
    argument = -1 if task.argument is None else ITEMS.index(task.argument)
    target = (-1, -1) if task.target is None else task.target
    try:
        return lookup[(int(task.operation), argument, target[0], target[1])]
    except KeyError as error:
        raise ReplayRejected(
            "task_catalog_mismatch",
            f"compressed replay task is absent from native catalog: {task!r}",
        ) from error


def _suffix_tasks(
    sequence: ReplaySequence,
    seat: int,
    turn: int,
    unit_index: int,
    *,
    board_size: int,
    turns_per_day: int,
) -> tuple[UnitTask, ...]:
    stop = min(((turn // turns_per_day) + 1) * turns_per_day, sequence.turns)
    trace: list[UnitTraceStep] = []
    for source_turn in range(turn, stop):
        positions = sequence.positions[seat][source_turn]
        actions = sequence.unit_actions[seat][source_turn]
        if unit_index >= len(positions):
            break
        trace.append(
            UnitTraceStep(
                step=source_turn % turns_per_day,
                position=positions[unit_index],
                action=actions[unit_index],
            )
        )
    if not trace:
        raise ReplayRejected(
            "task_trace_missing", "native task unit has no replay suffix"
        )
    audit = compress_unit_trace(
        tuple(trace),
        board_size=board_size,
        day_end=turns_per_day,
    )
    if not audit.exact_reconstruction:
        raise ReplayRejected(
            "task_trace_not_lossless", "compressed task tape differs from replay actions"
        )
    return audit.tasks


def _copy_sample(
    raw: Mapping[str, Any],
    action: tuple[int, int, int, int, int],
    stream_index: int,
    turn_index: int,
) -> _RawSample:
    return _RawSample(
        stream_index=stream_index,
        turn_index=turn_index,
        root_features=np.array(raw["root_features"], dtype=np.float32, copy=True),
        prefix_fields=np.array(raw["prefix_fields"], dtype=np.int16, copy=True),
        prefix_mask=np.array(raw["prefix_mask"], dtype=np.bool_, copy=True),
        candidate_features=np.array(
            raw["candidate_features"], dtype=np.float16, copy=True
        ),
        candidate_mask=np.array(raw["candidate_mask"], dtype=np.bool_, copy=True),
        candidate_arrivals=np.array(
            raw["candidate_arrivals"], dtype=np.int16, copy=True
        ),
        mode_mask=np.array(raw["mode_mask"], dtype=np.bool_, copy=True),
        available_at=int(raw["available_at"]),
        day_end=int(raw["day_end"]),
        action=np.asarray(action, dtype=np.int64),
    )


def _copy_factorized_sample(
    raw: Mapping[str, Any],
    action: tuple[int, int, int, int, int],
    stream_index: int,
    turn_index: int,
    history_window: int,
) -> _FactorizedRawSample:
    """Copy only compact typed facts into the sampling reservoir."""
    source_fields = np.asarray(raw["prefix_fields"], dtype=np.int16)
    source_mask = np.asarray(raw["prefix_mask"], dtype=np.bool_)
    count = int(np.count_nonzero(source_mask))
    active = min(count, history_window)
    prefix_fields = np.zeros((history_window, source_fields.shape[1]), np.int16)
    prefix_mask = np.zeros(history_window, np.bool_)
    if active:
        prefix_fields[:active] = source_fields[count - active : count]
        prefix_mask[:active] = True
    return _FactorizedRawSample(
        stream_index=stream_index,
        turn_index=turn_index,
        root_features=np.array(raw["root_features"], dtype=np.float32, copy=True),
        prefix_fields=prefix_fields,
        prefix_mask=prefix_mask,
        current_unit=int(raw["unit_index"]),
        current_x=int(raw["current_x"]),
        current_y=int(raw["current_y"]),
        target_counts=np.array(
            raw["target_conflicts"], dtype=np.int16, copy=True
        ),
        resource_counts=np.array(
            raw["resource_conflicts"], dtype=np.int16, copy=True
        ),
        mode_mask=np.array(raw["mode_mask"], dtype=np.bool_, copy=True),
        available_at=int(raw["available_at"]),
        day_end=int(raw["day_end"]),
        action=np.asarray(action, dtype=np.int64),
    )


def _records(
    samples: list[_RawSample],
    contexts: NDArray[np.float16],
    contract: NativeTaskContract,
) -> tuple[SampledTaskRecord, ...]:
    if not samples:
        raise ReplayRejected("task_sample_empty", "task stream produced no BC samples")
    device = torch.device("cpu")

    def tensor(name: str, dtype: torch.dtype) -> torch.Tensor:
        return torch.as_tensor(
            np.stack([getattr(sample, name) for sample in samples]),
            dtype=dtype,
            device=device,
        )

    action = tensor("action", torch.long)
    turn_indices = np.asarray([sample.turn_index for sample in samples], dtype=np.int64)
    inputs = TaskDecisionInputs(
        context=torch.as_tensor(contexts[turn_indices], dtype=torch.float32),
        root_features=tensor("root_features", torch.float32),
        prefix_fields=tensor("prefix_fields", torch.long),
        prefix_mask=tensor("prefix_mask", torch.bool),
        candidate_features=tensor("candidate_features", torch.float32),
        candidate_mask=tensor("candidate_mask", torch.bool),
        candidate_arrivals=tensor("candidate_arrivals", torch.long),
        mode_mask=tensor("mode_mask", torch.bool),
        available_at=torch.tensor(
            [sample.available_at for sample in samples], dtype=torch.long
        ),
        day_end=torch.tensor([sample.day_end for sample in samples], dtype=torch.long),
        prefix_length=max(
            int(np.count_nonzero(sample.prefix_mask)) for sample in samples
        ),
    )
    actions = TaskActions(
        mode=action[:, 0],
        candidate=action[:, 1],
        quantity=action[:, 2],
        earliest=action[:, 3],
        deadline=action[:, 4],
    )
    masks = conditional_masks(
        inputs,
        contract.catalog,
        actions,
        maximum_quantity=contract.maximum_quantity,
        time_tokens=contract.time_token_count,
    )
    masks.validate(
        len(samples),
        contract.candidate_count,
        contract.maximum_quantity,
        contract.time_token_count,
    )
    result: list[SampledTaskRecord] = []
    for index, sample in enumerate(samples):
        result.append(
            SampledTaskRecord(
                stream_index=sample.stream_index,
                record=TaskDecisionRecord(
                    episode_index=0,
                    turn_index=sample.turn_index,
                    root_features=sample.root_features,
                    prefix_fields=sample.prefix_fields,
                    prefix_mask=sample.prefix_mask,
                    candidate_features=sample.candidate_features,
                    candidate_mask=sample.candidate_mask,
                    candidate_arrivals=sample.candidate_arrivals,
                    mode_mask=sample.mode_mask,
                    available_at=sample.available_at,
                    day_end=sample.day_end,
                    action=sample.action,
                    quantity_mask=masks.quantity[index].numpy(),
                    earliest_mask=masks.earliest[index].numpy(),
                    deadline_mask=masks.deadline[index].numpy(),
                    factor_mask=masks.factors[index].numpy(),
                    old_joint_log_probability=0.0,
                    old_value=0.0,
                ),
            )
        )
    return tuple(result)


def _factorized_records(
    samples: list[_RawSample | _FactorizedRawSample],
    contexts: NDArray[np.float16],
    economic_state: NDArray[np.int32],
    contract: NativeTaskContract,
) -> tuple[SampledTaskRecord, ...]:
    """Derive typed masks once from compact sampled state."""
    if not samples or not all(
        isinstance(sample, _FactorizedRawSample) for sample in samples
    ):
        raise ReplayRejected(
            "task_sample_contract", "factorized reservoir contains a legacy row"
        )
    compact = cast(list[_FactorizedRawSample], samples)
    turn_indices = np.asarray(
        [sample.turn_index for sample in compact], dtype=np.int64
    )

    def tensor(name: str, dtype: torch.dtype) -> torch.Tensor:
        return torch.as_tensor(
            np.stack([getattr(sample, name) for sample in compact]), dtype=dtype
        )

    action = tensor("action", torch.long)
    inputs = FactorizedTaskDecisionInputs(
        context=torch.as_tensor(contexts[turn_indices], dtype=torch.float32),
        root_features=tensor("root_features", torch.float32),
        prefix_fields=tensor("prefix_fields", torch.long),
        prefix_mask=tensor("prefix_mask", torch.bool),
        economic_state=torch.as_tensor(
            economic_state[turn_indices], dtype=torch.int32
        ),
        current_unit=torch.tensor(
            [sample.current_unit for sample in compact], dtype=torch.long
        ),
        current_x=torch.tensor(
            [sample.current_x for sample in compact], dtype=torch.long
        ),
        current_y=torch.tensor(
            [sample.current_y for sample in compact], dtype=torch.long
        ),
        target_counts=tensor("target_counts", torch.int32),
        resource_counts=tensor("resource_counts", torch.int32),
        mode_mask=tensor("mode_mask", torch.bool),
        available_at=torch.tensor(
            [sample.available_at for sample in compact], dtype=torch.long
        ),
        day_end=torch.tensor(
            [sample.day_end for sample in compact], dtype=torch.long
        ),
        prefix_length=max(
            int(np.count_nonzero(sample.prefix_mask)) for sample in compact
        ),
    )
    actions = TaskActions(
        mode=action[:, 0],
        candidate=action[:, 1],
        quantity=action[:, 2],
        earliest=action[:, 3],
        deadline=action[:, 4],
    )
    masks = factorized_conditional_masks(
        inputs,
        contract.catalog,
        actions,
        maximum_quantity=contract.maximum_quantity,
        time_tokens=contract.time_token_count,
    )
    masks.validate(
        len(compact),
        16,
        13,
        contract.board_size * contract.board_size + 1,
        contract.maximum_quantity,
        contract.time_token_count,
    )
    result: list[SampledTaskRecord] = []
    for index, sample in enumerate(compact):
        result.append(
            SampledTaskRecord(
                stream_index=sample.stream_index,
                record=FactorizedTaskRecord(
                    turn_index=sample.turn_index,
                    root_features=sample.root_features,
                    prefix_fields=sample.prefix_fields,
                    prefix_mask=sample.prefix_mask,
                    current_unit=sample.current_unit,
                    current_x=sample.current_x,
                    current_y=sample.current_y,
                    target_counts=sample.target_counts,
                    resource_counts=sample.resource_counts,
                    mode_mask=sample.mode_mask,
                    available_at=sample.available_at,
                    day_end=sample.day_end,
                    action=sample.action,
                    operation_mask=masks.operation[index].numpy(),
                    argument_mask=masks.argument[index].numpy(),
                    target_mask=masks.target[index].numpy(),
                    quantity_mask=masks.quantity[index].numpy(),
                    earliest_mask=masks.earliest[index].numpy(),
                    deadline_mask=masks.deadline[index].numpy(),
                    factor_mask=masks.factors[index].numpy(),
                ),
            )
        )
    return tuple(result)


def translate_sequence(
    backend: Any,
    sequence: ReplaySequence,
    contexts: NDArray[np.float16],
    contract: NativeTaskContract,
    seat: int,
    *,
    tasks_per_suffix: int,
    sample_capacity: int,
    sampling_seed: int,
    factorized: bool = False,
    history_window: int = 64,
) -> TranslatedSequence:
    """Validate every compiler action, retaining an unbiased bounded BC sample."""
    if tasks_per_suffix != 2:
        raise ValueError("unit-task BC v1 implements the declared K=2 convention")
    if contexts.ndim != 2 or contexts.shape[0] != sequence.turns:
        raise ValueError("task BC contexts do not align with replay turns")
    turns_per_day = int(sequence.configuration.get("turnsPerDay", 0))
    if turns_per_day + 1 != contract.time_token_count:
        raise ReplayRejected(
            "task_time_mismatch", "replay day length differs from native task ABI"
        )
    session = backend.unit_task_session(
        dict(sequence.configuration),
        contract.unit_limit,
        contract.maximum_quantity,
    )
    lookup = _candidate_lookup(contract)
    operations = contract.catalog.operations.numpy()
    reservoir = _Reservoir(
        sample_capacity,
        _sample_seed(sampling_seed, sequence.episode_id, seat),
    )
    counts: Counter[str] = Counter()
    operation_counts: Counter[str] = Counter()
    factor_pressure: Counter[str] = Counter()
    legal_sum = 0
    legal_min = contract.candidate_count
    legal_max = 0
    maximum_prefix = 0

    for turn in range(sequence.turns):
        visible = session.visible_state(sequence.observations[seat][turn])
        proposed: dict[int, deque[UnitTask | None]] = {}
        decisions_this_turn = 0
        while bool(session.decision_required_visible(visible)):
            raw = cast(
                Mapping[str, Any],
                session.compact_observation_visible(visible)
                if factorized
                else session.observation_visible(visible),
            )
            unit_index = int(raw["unit_index"])
            mode_mask = np.asarray(raw["mode_mask"], dtype=np.bool_)
            candidate_mask = (
                None
                if factorized
                else np.asarray(raw["candidate_mask"], dtype=np.bool_)
            )
            prefix_length = int(np.asarray(raw["prefix_mask"], dtype=np.bool_).sum())
            legal = 0 if candidate_mask is None else int(candidate_mask.sum())
            maximum_prefix = max(maximum_prefix, prefix_length)
            if candidate_mask is not None:
                legal_sum += legal
                legal_min = min(legal_min, legal)
                legal_max = max(legal_max, legal)
            if prefix_length == contract.prefix_capacity:
                factor_pressure["prefix_capacity"] += 1
            if candidate_mask is not None and legal == 1:
                factor_pressure["forced_end_surface"] += 1

            if bool(mode_mask[int(SuffixMode.CONTINUE)]):
                selection = (int(SuffixMode.CONTINUE), 0, 0, 0, 0)
                counts["continue"] += 1
            else:
                queue = proposed.get(unit_index)
                if queue is None:
                    tasks = _suffix_tasks(
                        sequence,
                        seat,
                        turn,
                        unit_index,
                        board_size=contract.board_size,
                        turns_per_day=turns_per_day,
                    )
                    queue = deque(tasks[:tasks_per_suffix])
                    queue.append(None)
                    proposed[unit_index] = queue
                    counts["suffixes"] += 1
                    counts["proposed_tasks"] += min(tasks_per_suffix, len(tasks))
                task = queue.popleft()
                if task is None:
                    selection = (int(SuffixMode.REWRITE), 0, 0, 0, 0)
                    counts["end"] += 1
                    operation_counts["END"] += 1
                else:
                    candidate = _candidate_index(task, lookup)
                    selection = (
                        int(SuffixMode.REWRITE),
                        candidate,
                        task.quantity,
                        task.earliest_start,
                        task.deadline,
                    )
                    counts["task"] += 1
                    operation_counts[str(int(operations[candidate]))] += 1
                    if candidate_mask is not None and not bool(
                        candidate_mask[candidate]
                    ):
                        raise ReplayRejected(
                            "task_label_illegal",
                            f"compressed task is masked at turn {turn}, unit {unit_index}",
                        )
            if not bool(mode_mask[selection[0]]):
                raise ReplayRejected(
                    "task_mode_illegal", f"suffix mode is masked at turn {turn}"
                )
            stream_index = reservoir.seen
            slot = reservoir.offer()
            if slot is not None:
                reservoir.store(
                    slot,
                    (
                        _copy_factorized_sample(
                            raw,
                            selection,
                            stream_index,
                            turn,
                            history_window,
                        )
                        if factorized
                        else _copy_sample(raw, selection, stream_index, turn)
                    ),
                )
            try:
                session.select_visible(visible, *selection)
            except (KeyError, TypeError, ValueError, RuntimeError) as error:
                raise ReplayRejected(
                    "task_selection_failed",
                    f"native selection failed at turn {turn}: {type(error).__name__}: {error}",
                ) from error
            decisions_this_turn += 1
            if decisions_this_turn > contract.prefix_capacity + contract.unit_limit:
                raise ReplayRejected(
                    "task_decoding_unbounded", "task translation exceeded daily capacity"
                )

        compiled = cast(Mapping[str, Any], session.action_numeric_visible(visible))
        count = int(compiled["unit_count"])
        expected = sequence.encoded_actions[seat][turn]
        expected_tokens = expected.tokens[: expected.unit_decisions]
        expected_quantities = expected.quantities[: expected.unit_decisions]
        actual_tokens = tuple(
            int(value) for value in np.asarray(compiled["tokens"])[:count]
        )
        actual_quantities = tuple(
            int(value) for value in np.asarray(compiled["quantities"])[:count]
        )
        if (
            count != expected.unit_decisions
            or actual_tokens != expected_tokens
            or actual_quantities != expected_quantities
        ):
            raise ReplayRejected(
                "task_compiler_mismatch",
                f"K=2 task compiler differs from replay at turn {turn}",
            )
        counts["exact_turns"] += 1

    selected = reservoir.selected()
    records = (
        _factorized_records(
            selected, contexts, sequence.economic_state[seat], contract
        )
        if factorized
        else _records(cast(list[_RawSample], selected), contexts, contract)
    )
    factor_counts: Counter[str] = Counter()
    sampled_operations: Counter[str] = Counter()
    for sampled in records:
        factor_counts.update(
            str(index)
            for index, active in enumerate(sampled.record.factor_mask)
            if bool(active)
        )
        action = sampled.record.action
        if int(action[0]) == int(SuffixMode.CONTINUE):
            sampled_operations["CONTINUE"] += 1
        else:
            sampled_operations[str(int(operations[int(action[1])]))] += 1
    statistics: dict[str, object] = {
        "stream_decisions": reservoir.seen,
        "sampled_decisions": len(records),
        "sampling_fraction": len(records) / reservoir.seen,
        "decision_kinds": dict(sorted(counts.items())),
        "operation_counts": dict(sorted(operation_counts.items())),
        "sampled_operation_counts": dict(sorted(sampled_operations.items())),
        "sampled_active_factor_counts": dict(sorted(factor_counts.items())),
        "replay_repairs": dict(sorted(sequence.repairs[seat].items())),
        "maximum_prefix_length": maximum_prefix,
        "pressure": dict(sorted(factor_pressure.items())),
        "legal_candidates": (
            None
            if factorized
            else {
                "minimum": legal_min,
                "maximum": legal_max,
                "mean": legal_sum / reservoir.seen,
            }
        ),
        "exact_compiler_turns": counts["exact_turns"],
    }
    return TranslatedSequence(
        episode_id=sequence.episode_id,
        seat=seat,
        context=np.ascontiguousarray(contexts, dtype=np.float16),
        economic_state=(
            np.ascontiguousarray(sequence.economic_state[seat], dtype=np.int32)
            if factorized
            else None
        ),
        records=records,
        statistics=statistics,
        factorized=factorized,
    )


__all__ = [
    "FactorizedTaskRecord",
    "SampledTaskRecord",
    "TranslatedSequence",
    "translate_sequence",
]
