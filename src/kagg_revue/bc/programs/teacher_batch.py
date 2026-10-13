"""Batched native compilation of teacher actions on student states."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import cache
from typing import Any, cast

import numpy as np
from numpy.typing import NDArray

from kagg_revue.bc.actions import ReplayActionEncoder
from kagg_revue.bc.programs.translate import (
    _market_selection,
    _record_decision,
    _unit_selection,
)
from kagg_revue.core.backend import BackendApi
from kagg_revue.policy.programs.contract import (
    ITEM_NAMES,
    NONE_ARGUMENT,
    ControlType,
    Direction,
    MarketOrderType,
    RawOperation,
)
from kagg_revue.policy.programs.native import NativeProgramContract
from kagg_revue.policy.programs.runtime import compact_mask_width


@dataclass(frozen=True)
class TeacherProgramTurnBatch:
    """One compiler-canonical teacher program for every active game."""

    scalars: NDArray[np.int16]
    root_features: NDArray[np.float32]
    option_features: NDArray[np.int32]
    target_reservations: NDArray[np.int16]
    actions: NDArray[np.int64]
    conditional_masks: NDArray[np.bool_]
    quantity_max: NDArray[np.int64]
    decision_counts: NDArray[np.int16]


_SCALAR_NAMES = (
    "phase",
    "unit_index",
    "market_slot",
    "unit_count",
    "current_x",
    "current_y",
    "forced",
)

_REPAIR_NAMES = (
    "quantities_clipped_to_effective_maximum",
    "ineffective_unit_requests_to_pass",
    "market_skip_slots_compacted",
    "ineffective_market_requests_omitted",
)


@cache
def _program_token_specs(keys: tuple[str, ...]) -> NDArray[np.int64]:
    """Encode the fixed action vocabulary for the native trace compiler."""
    specs = np.zeros((len(keys), 6), dtype=np.int64)
    for token, key in enumerate(keys):
        fields = key.split(":")
        if len(fields) < 2:
            raise ValueError("teacher action token is malformed")
        specs[token] = (
            0,
            int(ControlType.CANCEL_PASS),
            NONE_ARGUMENT,
            int(Direction.NORTH),
            int(RawOperation.DROP),
            int(MarketOrderType.END),
        )
        if fields[0] == "UNIT":
            operation = fields[1]
            if operation == "PASS":
                continue
            if operation in Direction.__members__:
                specs[token, 1] = int(ControlType.STEP)
                specs[token, 3] = int(Direction[operation])
                continue
            try:
                raw_operation = RawOperation[operation]
            except KeyError as error:
                raise ValueError(
                    f"teacher action token has unknown unit operation: {key}"
                ) from error
            specs[token, 1] = int(ControlType.RAW_LOCAL)
            specs[token, 4] = int(raw_operation)
            if len(fields) == 3:
                specs[token, 2] = ITEM_NAMES.index(fields[2])
            continue
        if fields[0] != "MARKET":
            raise ValueError(f"teacher action token has unknown phase: {key}")
        if fields[1] == "SKIP_SLOT":
            specs[token, 0] = 2
            continue
        specs[token, 0] = 1
        if fields[1] == "STOP":
            specs[token, 5] = int(MarketOrderType.END)
            continue
        try:
            specs[token, 5] = int(MarketOrderType[fields[1]])
        except KeyError as error:
            raise ValueError(
                f"teacher action token has unknown market operation: {key}"
            ) from error
        if len(fields) == 3:
            specs[token, 2] = ITEM_NAMES.index(fields[2])
    specs.setflags(write=False)
    return specs


def _native_teacher_trace(
    compiler: Any,
    sessions: Sequence[Any],
    engines: Sequence[Any],
    players: NDArray[np.int64],
    teacher_tokens: NDArray[np.int64],
    teacher_quantities: NDArray[np.int64],
    teacher_counts: NDArray[np.int64],
    teacher_unit_counts: NDArray[np.int64],
    codec: ReplayActionEncoder,
    workers: int,
    repairs: Sequence[Counter[str]],
) -> TeacherProgramTurnBatch:
    """Run the complete trace compiler behind one native boundary."""
    raw = cast(
        Mapping[str, object],
        compiler(
            list(sessions),
            list(engines),
            players,
            teacher_tokens,
            teacher_quantities,
            teacher_counts,
            teacher_unit_counts,
            _program_token_specs(codec.keys),
            workers,
        ),
    )
    repair_counts = np.asarray(raw["repair_counts"], dtype=np.int64)
    if repair_counts.shape != (len(engines), len(_REPAIR_NAMES)):
        raise ValueError("native teacher trace returned malformed repair counts")
    for row, counter in enumerate(repairs):
        for column, name in enumerate(_REPAIR_NAMES):
            count = int(repair_counts[row, column])
            if count:
                counter[name] += count
    return TeacherProgramTurnBatch(
        scalars=np.asarray(raw["scalars"], dtype=np.int16),
        root_features=np.asarray(raw["root_features"], dtype=np.float32),
        option_features=np.asarray(raw["option_features"], dtype=np.int32),
        target_reservations=np.asarray(raw["target_reservations"], dtype=np.int16),
        actions=np.asarray(raw["actions"], dtype=np.int64),
        conditional_masks=np.asarray(raw["conditional_masks"], dtype=np.bool_),
        quantity_max=np.asarray(raw["quantity_max"], dtype=np.int64),
        decision_counts=np.asarray(raw["decision_counts"], dtype=np.int16),
    )


def _row(raw: Mapping[str, object], row: int) -> dict[str, object]:
    """Expand one row from the native struct-of-arrays decision batch."""
    scalars = np.asarray(raw["scalars"], dtype=np.int64)[row]
    result: dict[str, object] = {
        name: int(scalars[index]) for index, name in enumerate(_SCALAR_NAMES)
    }
    result.update(
        {
            name: np.asarray(value)[row]
            for name, value in raw.items()
            if name != "scalars"
        }
    )
    return result


def compile_teacher_program_turn_batch(
    backend: BackendApi,
    sessions: Sequence[Any],
    engines: Sequence[Any],
    players: NDArray[np.int64],
    teacher_tokens: NDArray[np.int64],
    teacher_quantities: NDArray[np.int64],
    teacher_counts: NDArray[np.int64],
    teacher_unit_counts: NDArray[np.int64],
    codec: ReplayActionEncoder,
    contract: NativeProgramContract,
    workers: int,
    repairs: Sequence[Counter[str]],
) -> TeacherProgramTurnBatch:
    """Compile exact teacher actions with batched native observe/select calls."""
    batch = len(engines)
    width = teacher_tokens.shape[1]
    if (
        len(sessions) != batch
        or players.shape != (batch,)
        or teacher_quantities.shape != (batch, width)
        or teacher_counts.shape != (batch,)
        or teacher_unit_counts.shape != (batch,)
        or len(repairs) != batch
    ):
        raise ValueError("batched teacher compiler inputs are misaligned")
    if np.any(
        (teacher_unit_counts < 1)
        | (teacher_unit_counts > teacher_counts)
        | (teacher_counts > width)
    ):
        raise ValueError("batched teacher action counts are invalid")

    native_compiler = getattr(
        backend, "conditional_program_compile_teacher_batch", None
    )
    if callable(native_compiler):
        return _native_teacher_trace(
            native_compiler,
            sessions,
            engines,
            players,
            teacher_tokens,
            teacher_quantities,
            teacher_counts,
            teacher_unit_counts,
            codec,
            workers,
            repairs,
        )

    capacity = contract.maximum_decisions
    mask_width = compact_mask_width(contract)
    scalars = np.zeros((batch, capacity, 7), dtype=np.int16)
    roots = np.zeros(
        (batch, capacity, contract.root_feature_count), dtype=np.float32
    )
    options = np.zeros(
        (batch, capacity, contract.option_feature_count), dtype=np.int32
    )
    reservations = np.zeros(
        (batch, capacity, contract.tile_count), dtype=np.int16
    )
    actions = np.zeros((batch, capacity, 9), dtype=np.int64)
    masks = np.zeros((batch, capacity, mask_width), dtype=np.bool_)
    quantity_max = np.zeros((batch, capacity), dtype=np.int64)
    decision_counts = np.zeros(batch, dtype=np.int16)
    cursors = np.zeros(batch, dtype=np.int64)
    session_list = list(sessions)
    engine_list = list(engines)

    completed = False
    for _decision in range(capacity):
        raw = cast(
            Mapping[str, object],
            backend.conditional_program_observations_batch(
                session_list,
                engine_list,
                players,
                workers,
            ),
        )
        raw_scalars = np.asarray(raw["scalars"], dtype=np.int64)
        active = np.flatnonzero(raw_scalars[:, 0] != 2).astype(
            np.int64, copy=False
        )
        if not active.size:
            completed = True
            break
        selections = np.zeros((batch, 8), dtype=np.int64)
        enabled = np.zeros(batch, dtype=np.uint8)
        for row_index in active:
            row = int(row_index)
            visible = _row(raw, row)
            phase = cast(int, visible["phase"])
            if phase == 0:
                cursor = int(cursors[row])
                if cursor >= int(teacher_unit_counts[row]):
                    raise ValueError("teacher program exhausted unit actions")
                key = codec.keys[int(teacher_tokens[row, cursor])]
                selected, maximum = _unit_selection(
                    key,
                    int(teacher_quantities[row, cursor]),
                    visible,
                    contract,
                    repairs[row],
                )
                cursors[row] += 1
            else:
                selected_market = None
                while cursors[row] < teacher_counts[row]:
                    cursor = int(cursors[row])
                    key = codec.keys[int(teacher_tokens[row, cursor])]
                    cursors[row] += 1
                    selected_market = _market_selection(
                        key,
                        int(teacher_quantities[row, cursor]),
                        visible,
                        repairs[row],
                    )
                    if selected_market is not None:
                        break
                if selected_market is None:
                    selected_market = _market_selection(
                        "MARKET:STOP",
                        0,
                        visible,
                        repairs[row],
                    )
                if selected_market is None:
                    raise ValueError("teacher program cannot terminate its market phase")
                selected, maximum = selected_market
            position = int(decision_counts[row])
            record = _record_decision(visible, selected, contract, maximum)
            scalars[row, position] = record[0]
            roots[row, position] = record[1]
            options[row, position] = record[2]
            reservations[row, position] = record[3]
            actions[row, position] = record[4]
            masks[row, position] = record[5]
            quantity_max[row, position] = record[6]
            decision_counts[row] += 1
            selections[row, 0] = selected[0]
            selections[row, 1] = selected[1] if phase == 0 else selected[8]
            selections[row, 2:8] = selected[2:8]
            enabled[row] = 1
        backend.conditional_program_select_batch(
            session_list,
            engine_list,
            players,
            selections,
            enabled,
            workers,
        )
    if not completed:
        final = cast(
            Mapping[str, object],
            backend.conditional_program_observations_batch(
                session_list,
                engine_list,
                players,
                workers,
            ),
        )
        if np.any(np.asarray(final["scalars"], dtype=np.int64)[:, 0] != 2):
            raise ValueError("teacher program exceeds the native decision capacity")
    return TeacherProgramTurnBatch(
        scalars=scalars,
        root_features=roots,
        option_features=options,
        target_reservations=reservations,
        actions=actions,
        conditional_masks=masks,
        quantity_max=quantity_max,
        decision_counts=decision_counts,
    )


__all__ = ["TeacherProgramTurnBatch", "compile_teacher_program_turn_batch"]
