"""Replay-suffix proposals for the persistent conditional action language."""

from __future__ import annotations

from kagg_revue.bc.tasks.replay import ReplaySequence
from kagg_revue.policy.programs.contract import (
    COOP_ARGUMENT,
    ITEM_NAMES,
    NONE_ARGUMENT,
    PASTURE_ARGUMENT,
    ControlType,
    Direction,
    MarketOrderType,
    QuantityMode,
    RawOperation,
    TaskType,
)
from kagg_revue.policy.tasks.contract import TaskOperation, UnitTask
from kagg_revue.rl.tasks.replay import UnitTraceStep, compress_unit_trace

ProgramSelection = tuple[int, int, int, int, int, int, int, int, int]
ProgramProposals = tuple[ProgramSelection, ...]


def _selection(
    task: TaskType,
    *,
    board_size: int,
    target: tuple[int, int] | None = None,
    argument: int = NONE_ARGUMENT,
    quantity: int = 1,
) -> ProgramSelection:
    tile = -1 if target is None else target[1] * board_size + target[0]
    mode = QuantityMode.ONE if quantity == 1 else QuantityMode.EXACT
    return (
        int(ControlType.ASSIGN),
        int(task),
        tile,
        argument,
        int(Direction.NORTH),
        int(RawOperation.DROP),
        int(mode),
        quantity,
        int(MarketOrderType.END),
    )


def _next_official(tasks: tuple[UnitTask, ...], start: int) -> UnitTask | None:
    for task in tasks[start:]:
        if task.operation.is_official:
            return task
    return None


def _proposals_from_tasks(
    tasks: tuple[UnitTask, ...], board_size: int
) -> ProgramProposals:
    first = tasks[0]
    operation = first.operation

    if operation is TaskOperation.POSITION:
        return (_selection(TaskType.GO_TO, board_size=board_size, target=first.target),)
    if operation is TaskOperation.WAIT:
        return (_selection(TaskType.WAIT, board_size=board_size),)
    if operation is TaskOperation.DROP:
        return (
            _selection(TaskType.STORE_ALL, board_size=board_size, target=first.target),
        )

    following = _next_official(tasks, 1)
    if operation is TaskOperation.PLANT:
        if (
            following is None
            or following.operation is not TaskOperation.WATER
            or following.target != first.target
            or following.earliest_start != first.deadline
        ):
            if first.argument is None:
                return ()
            return (
                _selection(
                    TaskType.PLANT,
                    board_size=board_size,
                    target=first.target,
                    argument=ITEM_NAMES.index(first.argument),
                ),
            )
        if first.argument is None:
            return ()
        argument = ITEM_NAMES.index(first.argument)
        return (
            _selection(
                TaskType.SAFE_PLANT,
                board_size=board_size,
                target=first.target,
                argument=argument,
            ),
            _selection(
                TaskType.PLANT,
                board_size=board_size,
                target=first.target,
                argument=argument,
            ),
        )

    if operation in {TaskOperation.BUILD_COOP, TaskOperation.BUILD_PASTURE}:
        if (
            following is not None
            and following.operation is TaskOperation.PLACE
            and following.target == first.target
            and following.argument in ITEM_NAMES[9:]
        ):
            return (
                _selection(
                    TaskType.DEPLOY_ANIMAL,
                    board_size=board_size,
                    target=first.target,
                    argument=ITEM_NAMES.index(following.argument),
                ),
                _selection(
                    TaskType.BUILD,
                    board_size=board_size,
                    target=first.target,
                    argument=(
                        COOP_ARGUMENT
                        if operation is TaskOperation.BUILD_COOP
                        else PASTURE_ARGUMENT
                    ),
                ),
            )
        argument = (
            COOP_ARGUMENT
            if operation is TaskOperation.BUILD_COOP
            else PASTURE_ARGUMENT
        )
        return (
            _selection(
                TaskType.BUILD,
                board_size=board_size,
                target=first.target,
                argument=argument,
            ),
        )

    if operation is TaskOperation.PICKUP:
        if first.argument is None:
            return ()
        item = ITEM_NAMES.index(first.argument)
        proposals: list[ProgramSelection] = []
        if following is not None:
            if item == ITEM_NAMES.index("FERTILIZER") and (
                following.operation is TaskOperation.FERTILIZE
            ):
                proposals.append(
                    _selection(
                        TaskType.FERTILIZE,
                        board_size=board_size,
                        target=following.target,
                    )
                )
            if item == ITEM_NAMES.index("WHEAT") and (
                following.operation is TaskOperation.FEED
            ):
                proposals.append(
                    _selection(
                        TaskType.FEED,
                        board_size=board_size,
                        target=following.target,
                    )
                )
            if (
                item >= 9
                and following.operation is TaskOperation.PLACE
                and following.argument == first.argument
            ):
                proposals.append(
                    _selection(
                        TaskType.DEPLOY_ANIMAL,
                        board_size=board_size,
                        target=following.target,
                        argument=item,
                    )
                )
        proposals.append(
            _selection(
                TaskType.FETCH,
                board_size=board_size,
                target=first.target,
                argument=item,
                quantity=first.quantity,
            )
        )
        return tuple(proposals)

    if operation is TaskOperation.PLACE:
        if first.argument is None:
            return ()
        item = ITEM_NAMES.index(first.argument)
        proposals = []
        if item >= 9:
            proposals.append(
                _selection(
                    TaskType.DEPLOY_ANIMAL,
                    board_size=board_size,
                    target=first.target,
                    argument=item,
                )
            )
        proposals.append(
            _selection(
                TaskType.STORE,
                board_size=board_size,
                target=first.target,
                argument=item,
                quantity=first.quantity,
            )
        )
        return tuple(proposals)

    direct = {
        TaskOperation.WATER: TaskType.WATER,
        TaskOperation.HARVEST: TaskType.HARVEST,
        TaskOperation.FERTILIZE: TaskType.FERTILIZE,
        TaskOperation.DIG: TaskType.DIG,
        TaskOperation.FEED: TaskType.FEED,
        TaskOperation.COLLECT_FERTILIZER: TaskType.COLLECT,
        TaskOperation.CARE: TaskType.CARE,
    }
    task = direct.get(operation)
    if task is None:
        return ()
    return (_selection(task, board_size=board_size, target=first.target),)


def propose_replay_unit(
    sequence: ReplaySequence,
    seat: int,
    turn: int,
    unit_index: int,
    *,
    board_size: int,
    turns_per_day: int,
) -> ProgramProposals:
    """Propose ordered intent-level options from the remaining daily trace."""
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
        return ()
    audit = compress_unit_trace(
        tuple(trace),
        board_size=board_size,
        day_end=turns_per_day,
    )
    if not audit.exact_reconstruction or not audit.tasks:
        return ()
    proposals = _proposals_from_tasks(audit.tasks, board_size)
    if audit.tasks[0].target != trace[0].position:
        # A moving SAFE_PLANT reserves a future seed and can incorrectly mask a
        # later unit's replay plant. Keep the independent PLANT fallback, but
        # assign SAFE_PLANT only at the actual plant boundary.
        proposals = tuple(
            proposal
            for proposal in proposals
            if proposal[1] != int(TaskType.SAFE_PLANT)
        )
    return proposals


__all__ = ["ProgramProposals", "ProgramSelection", "propose_replay_unit"]
