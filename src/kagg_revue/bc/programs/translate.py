"""Lossless visible-state translation from replay actions to programs."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, cast

import numpy as np
from numpy.typing import NDArray

from kagg_revue.bc.actions import EncodedTurnAction, ReplayActionEncoder
from kagg_revue.bc.programs.semantics import ProgramProposals, propose_replay_unit
from kagg_revue.bc.tasks.replay import ReplaySequence
from kagg_revue.policy.programs.contract import (
    ITEM_NAMES,
    NONE_ARGUMENT,
    TASKS_REQUIRING_ARGUMENT,
    TASKS_REQUIRING_QUANTITY,
    TASKS_REQUIRING_TARGET,
    ControlType,
    Direction,
    MarketOrderType,
    QuantityMode,
    RawOperation,
    TaskType,
)
from kagg_revue.policy.programs.native import NativeProgramContract
from kagg_revue.policy.programs.runtime import compact_mask_width


@dataclass(frozen=True)
class ProgramReplaySeat:
    """One complete replay perspective with compiler-canonical behavior."""

    board: NDArray[np.float16]
    units: NDArray[np.float16]
    global_features: NDArray[np.float16]
    economic_state: NDArray[np.int32]
    actions: NDArray[np.int64]
    quantities: NDArray[np.int64]
    action_decision_counts: NDArray[np.int16]
    program_scalars: NDArray[np.int16]
    program_root_features: NDArray[np.float32]
    program_option_features: NDArray[np.int32]
    program_target_reservations: NDArray[np.int16]
    program_actions: NDArray[np.int64]
    program_conditional_masks: NDArray[np.bool_]
    program_quantity_max: NDArray[np.int64]
    program_decision_counts: NDArray[np.int16]
    outcome: int
    statistics: Mapping[str, int]


def _fallback(width: int, index: int = 0) -> NDArray[np.bool_]:
    result = np.zeros(width, dtype=np.bool_)
    result[index] = True
    return result


def _integer(raw: Mapping[str, object], name: str) -> int:
    value = raw[name]
    if not isinstance(value, (int, np.integer)) or isinstance(value, bool):
        raise ValueError(f"program replay {name} must be an integer")
    return int(value)


def _quantity(
    mask: NDArray[np.bool_], maximum: int, requested: int, repairs: Counter[str]
) -> tuple[QuantityMode, int] | None:
    """Choose a lossless effective quantity under the native dynamic bound."""
    if maximum < 1 or requested < 1:
        return None
    effective = min(requested, maximum)
    if effective != requested:
        repairs["quantities_clipped_to_effective_maximum"] += 1
    if effective == 1 and bool(mask[int(QuantityMode.ONE)]):
        return QuantityMode.ONE, 1
    if bool(mask[int(QuantityMode.EXACT)]):
        return QuantityMode.EXACT, effective
    return None


def _unit_selection(
    key: str,
    quantity: int,
    raw: Mapping[str, object],
    contract: NativeProgramContract,
    repairs: Counter[str],
) -> tuple[NDArray[np.int64], int]:
    """Return one legal semantic equivalent and its selected quantity maximum."""
    control_mask = np.asarray(raw["control_mask"], dtype=np.bool_)
    selection = np.asarray(
        [
            int(ControlType.CANCEL_PASS),
            0,
            -1,
            NONE_ARGUMENT,
            int(Direction.NORTH),
            int(RawOperation.DROP),
            int(QuantityMode.ONE),
            1,
            int(MarketOrderType.END),
        ],
        dtype=np.int64,
    )

    def cancel() -> tuple[NDArray[np.int64], int]:
        if not bool(control_mask[int(ControlType.CANCEL_PASS)]):
            raise ValueError("program replay cannot express a forced unit decision")
        selection[0] = int(ControlType.CANCEL_PASS)
        return selection, 0

    fields = key.split(":")
    if len(fields) < 2 or fields[0] != "UNIT":
        raise ValueError("program replay unit prefix contains a market action")
    operation = fields[1]
    if operation == "PASS":
        return cancel()
    if operation in Direction.__members__:
        direction = Direction[operation]
        direction_mask = np.asarray(raw["direction_mask"], dtype=np.bool_)
        if not (bool(control_mask[int(ControlType.STEP)]) and bool(direction_mask[int(direction)])):
            repairs["ineffective_unit_requests_to_pass"] += 1
            return cancel()
        selection[0] = int(ControlType.STEP)
        selection[4] = int(direction)
        return selection, 0
    try:
        raw_operation = RawOperation[operation]
    except KeyError as error:
        raise ValueError(f"program replay has an unknown unit operation: {operation}") from error
    raw_mask = np.asarray(raw["raw_operation_mask"], dtype=np.bool_)
    if not (bool(control_mask[int(ControlType.RAW_LOCAL)]) and bool(raw_mask[int(raw_operation)])):
        repairs["ineffective_unit_requests_to_pass"] += 1
        return cancel()
    argument = NONE_ARGUMENT
    if len(fields) == 3:
        argument = ITEM_NAMES.index(fields[2])
        argument_mask = np.asarray(raw["raw_argument_mask"], dtype=np.bool_)
        if not bool(argument_mask[int(raw_operation), argument]):
            repairs["ineffective_unit_requests_to_pass"] += 1
            return cancel()
    selected_maximum = 0
    if raw_operation in {RawOperation.PICKUP, RawOperation.PLACE}:
        mode_mask = np.asarray(raw["raw_quantity_mode_mask"], dtype=np.bool_)[
            int(raw_operation), argument
        ]
        selected_maximum = int(
            np.asarray(raw["raw_quantity_max"], dtype=np.int64)[int(raw_operation), argument]
        )
        selected_quantity = _quantity(mode_mask, selected_maximum, quantity, repairs)
        if selected_quantity is None:
            repairs["ineffective_unit_requests_to_pass"] += 1
            return cancel()
        selection[6] = int(selected_quantity[0])
        selection[7] = selected_quantity[1]
    selection[0] = int(ControlType.RAW_LOCAL)
    selection[3] = argument
    selection[5] = int(raw_operation)
    return selection, selected_maximum


def _market_selection(
    key: str,
    quantity: int,
    raw: Mapping[str, object],
    repairs: Counter[str],
) -> tuple[NDArray[np.int64], int] | None:
    """Return a legal compacted market order, omitting semantic no-ops."""
    fields = key.split(":")
    if len(fields) < 2 or fields[0] != "MARKET":
        raise ValueError("program replay market suffix contains a unit action")
    if fields[1] == "SKIP_SLOT":
        repairs["market_skip_slots_compacted"] += 1
        return None
    if fields[1] == "STOP":
        order_type = MarketOrderType.END
    else:
        try:
            order_type = MarketOrderType[fields[1]]
        except KeyError as error:
            raise ValueError(f"program replay has an unknown market order: {fields[1]}") from error
    order_mask = np.asarray(raw["market_order_mask"], dtype=np.bool_)
    if not bool(order_mask[int(order_type)]):
        repairs["ineffective_market_requests_omitted"] += 1
        return None
    item = 0
    selected_maximum = 0
    mode = QuantityMode.ONE
    exact = 1
    if len(fields) == 3:
        item = ITEM_NAMES.index(fields[2])
        item_mask = np.asarray(raw["market_item_mask"], dtype=np.bool_)
        if not bool(item_mask[int(order_type), item]):
            repairs["ineffective_market_requests_omitted"] += 1
            return None
        mode_mask = np.asarray(raw["market_quantity_mode_mask"], dtype=np.bool_)[
            int(order_type), item
        ]
        selected_maximum = int(
            np.asarray(raw["market_quantity_max"], dtype=np.int64)[int(order_type), item]
        )
        selected_quantity = _quantity(mode_mask, selected_maximum, quantity, repairs)
        if selected_quantity is None:
            repairs["ineffective_market_requests_omitted"] += 1
            return None
        mode, exact = selected_quantity
    selection = np.asarray(
        [
            int(ControlType.KEEP),
            0,
            -1,
            item,
            int(Direction.NORTH),
            int(RawOperation.DROP),
            int(mode),
            exact,
            int(order_type),
        ],
        dtype=np.int64,
    )
    return selection, selected_maximum


def _compact_masks(
    raw: Mapping[str, object],
    selection: NDArray[np.int64],
    contract: NativeProgramContract,
    quantity_maximum: int,
) -> NDArray[np.bool_]:
    """Select the same conditional mask slices retained by online rollouts."""
    phase = _integer(raw, "phase")
    control = int(selection[0])
    raw_operation = int(selection[5])
    market_order = int(selection[8])
    argument = int(selection[3])
    task = int(selection[1])
    unit = phase == 0
    market = phase == 1
    direction_mask = (
        np.asarray(raw["direction_mask"], dtype=np.bool_)
        if unit and control == int(ControlType.STEP)
        else _fallback(contract.direction_count)
    )
    raw_mask = (
        np.asarray(raw["raw_operation_mask"], dtype=np.bool_)
        if unit and control == int(ControlType.RAW_LOCAL)
        else _fallback(contract.raw_operation_count)
    )
    raw_needs_argument = (
        unit
        and control == int(ControlType.RAW_LOCAL)
        and raw_operation
        in {
            int(RawOperation.PICKUP),
            int(RawOperation.PLACE),
            int(RawOperation.PLANT),
        }
    )
    task_type = TaskType(task)
    task_needs_argument = (
        unit
        and control == int(ControlType.ASSIGN)
        and task_type in TASKS_REQUIRING_ARGUMENT
    )
    raw_argument_mask = (
        np.asarray(raw["raw_argument_mask"], dtype=np.bool_)[raw_operation]
        if raw_needs_argument
        else _fallback(contract.argument_count, NONE_ARGUMENT)
    )
    task_argument_mask = (
        np.asarray(raw["task_argument_mask"], dtype=np.bool_)[task]
        if task_needs_argument
        else _fallback(contract.argument_count, NONE_ARGUMENT)
    )
    argument_mask = task_argument_mask if task_needs_argument else raw_argument_mask
    raw_needs_quantity = (
        unit
        and control == int(ControlType.RAW_LOCAL)
        and raw_operation
        in {
            int(RawOperation.PICKUP),
            int(RawOperation.PLACE),
        }
    )
    task_needs_quantity = (
        unit
        and control == int(ControlType.ASSIGN)
        and task_type in TASKS_REQUIRING_QUANTITY
    )
    market_item = market and market_order in {
        int(MarketOrderType.SELL),
        int(MarketOrderType.BUY_SEED),
        int(MarketOrderType.BUY_PRODUCT),
        int(MarketOrderType.BUY_ANIMAL),
    }
    if raw_needs_quantity:
        quantity_mask = np.asarray(raw["raw_quantity_mode_mask"], dtype=np.bool_)[
            raw_operation, argument
        ]
    elif task_needs_quantity:
        quantity_mask = np.asarray(raw["task_quantity_mode_mask"], dtype=np.bool_)[
            task, argument
        ]
    elif market_item:
        quantity_mask = np.asarray(raw["market_quantity_mode_mask"], dtype=np.bool_)[
            market_order, argument
        ]
    else:
        quantity_mask = _fallback(contract.quantity_mode_count)
    market_item_mask = (
        np.asarray(raw["market_item_mask"], dtype=np.bool_)[market_order]
        if market_item
        else _fallback(contract.item_count)
    )
    task_mask = (
        np.asarray(raw["task_mask"], dtype=np.bool_)
        if unit and control == int(ControlType.ASSIGN)
        else _fallback(contract.task_count)
    )
    task_argument = argument if task_needs_argument else NONE_ARGUMENT
    target_mask = (
        np.asarray(raw["task_target_mask"], dtype=np.bool_)[task, task_argument]
        if unit
        and control == int(ControlType.ASSIGN)
        and task_type in TASKS_REQUIRING_TARGET
        else _fallback(contract.tile_count)
    )
    values = (
        np.asarray(raw["control_mask"], dtype=np.bool_)
        if unit
        else _fallback(contract.control_count),
        direction_mask,
        task_mask,
        argument_mask,
        target_mask,
        raw_mask,
        quantity_mask,
        np.asarray(raw["market_order_mask"], dtype=np.bool_)
        if market
        else _fallback(contract.market_order_count),
        market_item_mask,
    )
    result = np.concatenate(values).astype(np.bool_, copy=False)
    if result.shape != (compact_mask_width(contract),):
        raise ValueError("program replay compact mask width differs from native ABI")
    if quantity_maximum < 0:
        raise ValueError("program replay selected a negative quantity maximum")
    return result


def _record_decision(
    raw: Mapping[str, object],
    selection: NDArray[np.int64],
    contract: NativeProgramContract,
    quantity_maximum: int,
) -> tuple[
    NDArray[np.int16],
    NDArray[np.float32],
    NDArray[np.int32],
    NDArray[np.int16],
    NDArray[np.int64],
    NDArray[np.bool_],
    int,
]:
    scalars = np.asarray(
        [
            _integer(raw, "phase"),
            _integer(raw, "unit_index"),
            _integer(raw, "market_slot"),
            _integer(raw, "unit_count"),
            _integer(raw, "current_x"),
            _integer(raw, "current_y"),
            _integer(raw, "forced"),
        ],
        dtype=np.int16,
    )
    return (
        scalars,
        np.asarray(raw["root_features"], dtype=np.float32),
        np.asarray(raw["option_features"], dtype=np.int32),
        np.asarray(raw["target_reservations"], dtype=np.int16),
        selection,
        _compact_masks(raw, selection, contract, quantity_maximum),
        quantity_maximum,
    )


def _turn_trace(
    handle: Any,
    observation: Mapping[str, object],
    encoded: EncodedTurnAction,
    codec: ReplayActionEncoder,
    contract: NativeProgramContract,
    repairs: Counter[str],
    semantic_proposals: Sequence[ProgramProposals] | None = None,
) -> tuple[dict[str, NDArray[np.generic] | int], Mapping[str, object]]:
    rows: list[tuple[Any, ...]] = []
    unit_actions = tuple(
        zip(
        encoded.tokens[: encoded.unit_decisions],
        encoded.quantities[: encoded.unit_decisions],
        strict=True,
        )
    )
    if semantic_proposals is not None and len(semantic_proposals) != len(unit_actions):
        raise ValueError("semantic proposal count differs from replay units")
    for unit_index, (token, quantity) in enumerate(unit_actions):
        raw = cast(Mapping[str, object], handle.observation_visible(dict(observation)))
        selection, maximum = _unit_selection(codec.keys[token], quantity, raw, contract, repairs)
        if semantic_proposals is not None:
            proposals = semantic_proposals[unit_index]
            if proposals:
                repairs["semantic_proposals"] += 1
                repairs["semantic_proposal_candidates"] += len(proposals)
            selected = handle.select_replay_unit_visible(
                dict(observation),
                np.ascontiguousarray(selection[:8], dtype=np.int64),
                (
                    None
                    if not proposals
                    else np.ascontiguousarray(
                        np.asarray(proposals, dtype=np.int64)[:, :8]
                    )
                ),
            )
            selection[:8] = np.asarray(selected, dtype=np.int64)
            control = ControlType(int(selection[0]))
            if control is ControlType.KEEP:
                repairs["semantic_keep"] += 1
                maximum = 0
            elif control is ControlType.ASSIGN:
                repairs["semantic_assign"] += 1
                maximum = 0
                task = TaskType(int(selection[1]))
                if task in TASKS_REQUIRING_QUANTITY:
                    maximum = int(
                        np.asarray(raw["task_quantity_max"], dtype=np.int64)[
                            int(task), int(selection[3])
                        ]
                    )
            else:
                repairs["semantic_raw_fallback"] += 1
        rows.append(_record_decision(raw, selection, contract, maximum))
        if semantic_proposals is None:
            handle.select_visible(dict(observation), *selection[:8].tolist())

    stopped = False
    for token, quantity in zip(
        encoded.tokens[encoded.unit_decisions :],
        encoded.quantities[encoded.unit_decisions :],
        strict=True,
    ):
        key = codec.keys[token]
        if key == "MARKET:SKIP_SLOT":
            repairs["market_skip_slots_compacted"] += 1
            continue
        raw = cast(Mapping[str, object], handle.observation_visible(dict(observation)))
        selected = _market_selection(key, quantity, raw, repairs)
        if selected is None:
            continue
        selection, maximum = selected
        rows.append(_record_decision(raw, selection, contract, maximum))
        handle.select_visible(
            dict(observation),
            int(selection[0]),
            int(selection[8]),
            int(selection[2]),
            int(selection[3]),
            int(selection[4]),
            int(selection[5]),
            int(selection[6]),
            int(selection[7]),
        )
        if int(selection[8]) == int(MarketOrderType.END):
            stopped = True
            break
    if not stopped and int(handle.phase) == 1:
        raw = cast(Mapping[str, object], handle.observation_visible(dict(observation)))
        selected = _market_selection("MARKET:STOP", 0, raw, repairs)
        if selected is None:
            raise ValueError("program replay cannot terminate its market program")
        selection, maximum = selected
        rows.append(_record_decision(raw, selection, contract, maximum))
        handle.select_visible(
            dict(observation),
            int(selection[0]),
            int(selection[8]),
            int(selection[2]),
            int(selection[3]),
            int(selection[4]),
            int(selection[5]),
            int(selection[6]),
            int(selection[7]),
        )
    compiled = cast(Mapping[str, object], handle.action_numeric_visible(dict(observation)))
    if bool(compiled["requires_decision"]):
        raise ValueError("program replay teacher left an incomplete turn")
    capacity = contract.maximum_decisions

    def padded(index: int, shape: tuple[int, ...], dtype: np.dtype[Any]) -> NDArray[np.generic]:
        output = np.zeros((capacity, *shape), dtype=dtype)
        for row_index, row in enumerate(rows):
            output[row_index] = row[index]
        return output

    trace: dict[str, NDArray[np.generic] | int] = {
        "scalars": padded(0, (7,), np.dtype(np.int16)),
        "root_features": padded(1, (contract.root_feature_count,), np.dtype(np.float32)),
        "option_features": padded(2, (contract.option_feature_count,), np.dtype(np.int32)),
        "target_reservations": padded(3, (contract.tile_count,), np.dtype(np.int16)),
        "actions": padded(4, (9,), np.dtype(np.int64)),
        "conditional_masks": padded(5, (compact_mask_width(contract),), np.dtype(np.bool_)),
        "quantity_max": padded(6, (), np.dtype(np.int64)),
        "decision_count": len(rows),
    }
    return trace, compiled


def translate_program_replay(
    replay: ReplaySequence,
    seat: int,
    codec: ReplayActionEncoder,
    contract: NativeProgramContract,
    backend: Any,
    *,
    semantic: bool = False,
) -> ProgramReplaySeat:
    """Compile every replay turn into an exact legal program teacher."""
    if seat not in {0, 1}:
        raise ValueError("program replay seat must be zero or one")
    session_factory = getattr(backend, "conditional_program_session", None)
    if session_factory is None:
        session_factory = getattr(backend, "ConditionalProgramSession", None)
    if not callable(session_factory):
        raise TypeError("program replay backend lacks a conditional session")
    handle = session_factory(dict(replay.configuration), contract.unit_limit)
    reference_handle = (
        session_factory(dict(replay.configuration), contract.unit_limit)
        if semantic
        else None
    )
    turns = replay.turns
    capacity = contract.maximum_decisions
    mask_width = compact_mask_width(contract)
    actions = np.zeros((turns, capacity), dtype=np.int64)
    quantities = np.zeros_like(actions)
    action_counts = np.zeros(turns, dtype=np.int16)
    scalars = np.zeros((turns, capacity, 7), dtype=np.int16)
    roots = np.zeros((turns, capacity, contract.root_feature_count), dtype=np.float32)
    options = np.zeros((turns, capacity, contract.option_feature_count), dtype=np.int32)
    reservations = np.zeros((turns, capacity, contract.tile_count), dtype=np.int16)
    program_actions = np.zeros((turns, capacity, 9), dtype=np.int64)
    masks = np.zeros((turns, capacity, mask_width), dtype=np.bool_)
    quantity_max = np.zeros((turns, capacity), dtype=np.int64)
    program_counts = np.zeros(turns, dtype=np.int16)
    repairs: Counter[str] = Counter(replay.repairs[seat])
    turns_per_day = int(replay.configuration["turnsPerDay"])
    for turn in range(turns):
        proposals = (
            tuple(
                propose_replay_unit(
                    replay,
                    seat,
                    turn,
                    unit_index,
                    board_size=contract.board_size,
                    turns_per_day=turns_per_day,
                )
                for unit_index in range(replay.encoded_actions[seat][turn].unit_decisions)
            )
            if semantic
            else None
        )
        trace, compiled = _turn_trace(
            handle,
            replay.observations[seat][turn],
            replay.encoded_actions[seat][turn],
            codec,
            contract,
            repairs,
            proposals,
        )
        if reference_handle is not None:
            _, reference = _turn_trace(
                reference_handle,
                replay.observations[seat][turn],
                replay.encoded_actions[seat][turn],
                codec,
                contract,
                Counter(),
            )
            reference_count = int(cast(int, reference["decision_count"]))
            compiled_count = int(cast(int, compiled["decision_count"]))
            reference_tokens = np.asarray(reference["tokens"], dtype=np.int64)
            compiled_tokens = np.asarray(compiled["tokens"], dtype=np.int64)
            reference_quantities = np.asarray(reference["quantities"], dtype=np.int64)
            compiled_quantities = np.asarray(compiled["quantities"], dtype=np.int64)
            if (
                compiled_count != reference_count
                or not np.array_equal(
                    compiled_tokens[:compiled_count],
                    reference_tokens[:reference_count],
                )
                or not np.array_equal(
                    compiled_quantities[:compiled_count],
                    reference_quantities[:reference_count],
                )
            ):
                raise ValueError(
                    f"semantic program differs from raw replay baseline at turn {turn}"
                )
        decision_count = int(cast(int, compiled["decision_count"]))
        actions[turn] = np.asarray(compiled["tokens"], dtype=np.int64)
        quantities[turn] = np.asarray(compiled["quantities"], dtype=np.int64)
        action_counts[turn] = decision_count
        scalars[turn] = cast(NDArray[np.int16], trace["scalars"])
        roots[turn] = cast(NDArray[np.float32], trace["root_features"])
        options[turn] = cast(NDArray[np.int32], trace["option_features"])
        reservations[turn] = cast(NDArray[np.int16], trace["target_reservations"])
        program_actions[turn] = cast(NDArray[np.int64], trace["actions"])
        masks[turn] = cast(NDArray[np.bool_], trace["conditional_masks"])
        quantity_max[turn] = cast(NDArray[np.int64], trace["quantity_max"])
        program_counts[turn] = int(cast(int, trace["decision_count"]))
    opponent = 1 - seat
    outcome = int(np.sign(replay.rewards[seat] - replay.rewards[opponent]))
    return ProgramReplaySeat(
        board=np.asarray(replay.board[seat], dtype=np.float16),
        units=np.asarray(replay.units[seat], dtype=np.float16),
        global_features=np.asarray(replay.global_features[seat], dtype=np.float16),
        economic_state=np.asarray(replay.economic_state[seat], dtype=np.int32),
        actions=actions,
        quantities=quantities,
        action_decision_counts=action_counts,
        program_scalars=scalars,
        program_root_features=roots,
        program_option_features=options,
        program_target_reservations=reservations,
        program_actions=program_actions,
        program_conditional_masks=masks,
        program_quantity_max=quantity_max,
        program_decision_counts=program_counts,
        outcome=outcome,
        statistics=dict(sorted(repairs.items())),
    )


__all__ = ["ProgramReplaySeat", "translate_program_replay"]
