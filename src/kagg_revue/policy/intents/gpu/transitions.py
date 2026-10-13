"""CUDA state transitions for one selected canonical intent."""

from __future__ import annotations

from typing import TYPE_CHECKING

import torch
from torch import Tensor

from kagg_revue.policy.intents.gpu._ledger_abi import (
    _ADD_STORE,
    _ADD_WORK,
    _ASSET_PROFILE,
    _ASSET_TARGET,
    _BEGIN_ASSET,
    _BEGIN_CANCEL_ASSET,
    _BEGIN_CANCEL_DIRECTIVE,
    _BEGIN_CANCEL_FETCH,
    _BEGIN_CANCEL_POSITION,
    _BEGIN_CANCEL_WORK,
    _BEGIN_DIRECTIVE,
    _BEGIN_FETCH,
    _BEGIN_POSITION,
    _BEGIN_STORE,
    _BEGIN_WORK,
    _CANCEL_ASSET,
    _CANCEL_ASSET_CHOICE,
    _CANCEL_DIRECTIVE,
    _CANCEL_DIRECTIVE_CHOICE,
    _CANCEL_FETCH,
    _CANCEL_FETCH_CHOICE,
    _CANCEL_POSITION,
    _CANCEL_POSITION_CHOICE,
    _CANCEL_WORK,
    _CANCEL_WORK_CHOICE,
    _COMMIT,
    _CROPS,
    _DIRECTIVE_ITEM,
    _DIRECTIVE_OPERATION,
    _DIRECTIVE_QUANTITY,
    _DIRECTIVE_TARGET,
    _DIRECTIVE_UNIT,
    _DIRECTIVE_WAIT,
    _DONE,
    _EMPTY,
    _FERTILIZER,
    _FETCH_ITEM,
    _FETCH_QUANTITY,
    _FETCH_UNIT,
    _ITEMS,
    _LOCKED,
    _MARKET_BUY_ANIMAL,
    _MARKET_BUY_LAND,
    _MARKET_BUY_PRODUCT,
    _MARKET_BUY_SEED,
    _MARKET_HIRE,
    _MARKET_QUANTITY,
    _MARKET_SELL,
    _MARKET_SKIP_KIND,
    _MARKET_SKIP_SLOT,
    _PLANT,
    _POSITION_ROLE,
    _POSITION_TARGET,
    _REASON_FERTILIZER_SHORTFALL,
    _REASON_SHED_CAPACITY,
    _REASON_SHED_ITEM_SHORTFALL,
    _REASON_WHEAT_SHORTFALL,
    _ROOT,
    _SELECT_DIRECTIVE_ITEM,
    _SELECT_DIRECTIVE_OPERATION,
    _SELECT_DIRECTIVE_TARGET,
    _SELECT_DIRECTIVE_UNIT,
    _SELECT_FETCH_ITEM,
    _SELECT_FETCH_UNIT,
    _SELECT_MARKET_QUANTITY,
    _SELECT_ROLE,
    _SELECT_STORE_ITEM,
    _SELECT_STORE_QUANTITY,
    _SELECT_TARGET,
    _SET_ASSET,
    _SET_DIRECTIVE,
    _SET_FETCH,
    _SET_POSITION,
    _STATUS_BLOCKED,
    _STATUS_PENDING,
    _STATUS_RUNNING,
    _STORE_ITEM,
    _STORE_PRIORITY,
    _STORE_QUANTITY,
    _STRUCTURE,
    _WORK_PROFILE,
    _WORK_TARGET,
    _gather_rows,
    _replace_rows,
)

if TYPE_CHECKING:
    from kagg_revue.policy.intents.gpu.ledger import IntentGpuLedger


def _work_key(ledger: IntentGpuLedger, fields: Tensor) -> Tensor:
    """Return the native canonical key for every work-like row."""
    kind = fields[..., 0]
    return torch.where(
        kind == 8,
        ledger.cells * 16 + 2 + fields[..., 2] - 1,
        torch.where(
            kind == 9,
            ledger.cells * 16 + 2 + _ITEMS + fields[..., 8] - 1,
            torch.where(
                kind >= 10,
                ledger.cells * 16 + 2 + _ITEMS + 256 + fields[..., 8] - 1,
                fields[..., 1] * 16 + 1 + kind,
            ),
        ),
    )


def _filter_work(
    ledger: IntentGpuLedger, remove: Tensor, append: Tensor, append_row: Tensor
) -> None:
    removed = remove.any(1)
    removed_index = remove.long().argmax(1)
    removed_fields = ledger.work_orders[
        torch.arange(ledger.batch, device=ledger.device), removed_index
    ]
    ledger.work_removed_fields.copy_(
        torch.where(removed[:, None], removed_fields, ledger.work_removed_fields)
    )
    ledger.work_removed_mask |= removed
    ledger.work_added_fields.copy_(
        torch.where(append[:, None], append_row, ledger.work_added_fields)
    )
    ledger.work_added_mask |= append
    keep = ledger.work_mask & ~remove
    order = torch.argsort(~keep, dim=1, stable=True)
    compact = ledger.work_orders.gather(
        1, order[..., None].expand(-1, -1, ledger.architecture.work_field_count)
    )
    count = keep.sum(1)
    slots = torch.arange(ledger.work_capacity, device=ledger.device)[None]
    compact_mask = slots < count[:, None]
    compact = torch.where((slots == count[:, None])[..., None], append_row[:, None], compact)
    compact_mask |= append[:, None] & (slots == count[:, None])
    sort_key = torch.where(
        compact_mask,
        _work_key(ledger, compact),
        torch.iinfo(torch.long).max,
    )
    canonical_order = torch.argsort(sort_key, dim=1, stable=True)
    compact = compact.gather(
        1,
        canonical_order[..., None].expand(-1, -1, ledger.architecture.work_field_count),
    )
    compact_mask = compact_mask.gather(1, canonical_order)
    changed = remove.any(1) | append
    ledger.work_orders.copy_(_replace_rows(ledger.work_orders, compact, changed))
    ledger.work_mask.copy_(_replace_rows(ledger.work_mask, compact_mask, changed))


def _new_work_status(
    ledger: IntentGpuLedger, fields: Tensor, tiles: Tensor, owned: Tensor
) -> Tensor:
    kind = fields[:, 2] - 1
    target = fields[:, 1].clamp(0, ledger.cells - 1)
    tile = tiles.gather(1, target[:, None, None].expand(-1, 1, ledger.layout.tile_fields)).squeeze(
        1
    )
    tile_kind = tile[:, 0]
    animal = (tile_kind == _STRUCTURE) & (tile[:, 7] != 0)
    crop = tile[:, 1].clamp(0, _CROPS - 1)
    first_yield = _gather_rows(ledger._first_yield_day[None].expand(ledger.batch, -1), crop)
    day = ledger.economic[:, 0].long()
    ready = torch.zeros(ledger.batch, dtype=torch.bool, device=ledger.device)
    ready |= (
        (kind == 0) & (tile_kind == _PLANT) & (tile[:, 5] > 0) & (day - tile[:, 2] >= first_yield)
    )
    ready |= (kind == 1) & (tile_kind == _PLANT)
    ready |= (kind == 2) & animal & (tile[:, 10] == 0)
    ready |= (kind == 3) & animal & (tile[:, 5] > 0)
    ready |= (kind == 4) & animal & (tile[:, 11] != 0)
    ready |= (kind == 5) & (tile_kind != _EMPTY) & (tile_kind != _LOCKED) & ~animal
    ready |= (kind == 6) & (tile_kind == _PLANT) & (tile[:, 3] == 0)
    ready |= (kind == 7) & animal & (tile[:, 9] == 0)
    ready |= kind == 8
    status = torch.where(ready, _STATUS_RUNNING, _STATUS_PENDING)
    reason = torch.zeros_like(status)
    store_blocked = (kind == 8) & (ledger.economic[:, 8].long() >= ledger.economic[:, 5].long())
    feed_blocked = (kind == 7) & (owned[:, 0] <= 0)
    fertilizer_blocked = (kind == 1) & (owned[:, _FERTILIZER] <= 0)
    status = torch.where(
        store_blocked | feed_blocked | fertilizer_blocked,
        _STATUS_BLOCKED,
        status,
    )
    reason = torch.where(store_blocked, _REASON_SHED_CAPACITY, reason)
    reason = torch.where(feed_blocked, _REASON_WHEAT_SHORTFALL, reason)
    reason = torch.where(fertilizer_blocked, _REASON_FERTILIZER_SHORTFALL, reason)
    return torch.stack((status, reason), dim=1)


def apply_choice(
    ledger: IntentGpuLedger,
    choice_fields: Tensor,
    selected: Tensor,
    log_probability: Tensor,
    value: Tensor,
) -> None:
    """Apply already gathered candidate fields to the resident ledger."""
    ledger.work_removed_fields.zero_()
    ledger.work_removed_mask.zero_()
    ledger.work_added_fields.zero_()
    ledger.work_added_mask.zero_()
    rows = torch.arange(ledger.batch, device=ledger.device)
    choice = choice_fields[:, 0]
    live = ledger.active.clone()
    trace_index = ledger.trace_counts.clamp(0, ledger.trace_capacity - 1)
    trace_slots = torch.arange(ledger.trace_capacity, device=ledger.device)[None]
    write = live[:, None] & (trace_slots == trace_index[:, None])
    ledger.trace_selected.copy_(torch.where(write, selected[:, None], ledger.trace_selected))
    ledger.trace_fields.copy_(
        torch.where(write[..., None], choice_fields[:, None], ledger.trace_fields)
    )
    step_write = write.transpose(0, 1)
    ledger.trace_log_probability.copy_(
        torch.where(
            step_write,
            log_probability[None],
            ledger.trace_log_probability,
        )
    )
    ledger.trace_value.copy_(torch.where(step_write, value[None], ledger.trace_value))
    ledger.trace_counts.add_(live.long())

    def action(kind: int) -> Tensor:
        return live & (choice == kind)

    ledger.phase.copy_(torch.where(action(_COMMIT), _DONE, ledger.phase))
    ledger.active.copy_(live & ~action(_COMMIT))
    ledger.pending_kind.copy_(torch.where(action(_BEGIN_ASSET), _BEGIN_ASSET, ledger.pending_kind))
    ledger.pending_kind.copy_(torch.where(action(_BEGIN_WORK), _BEGIN_WORK, ledger.pending_kind))
    transitions = (
        (_BEGIN_ASSET, _ASSET_TARGET),
        (_BEGIN_CANCEL_ASSET, _CANCEL_ASSET),
        (_BEGIN_WORK, _WORK_TARGET),
        (_BEGIN_CANCEL_WORK, _CANCEL_WORK),
        (_BEGIN_POSITION, _POSITION_ROLE),
        (_BEGIN_CANCEL_POSITION, _CANCEL_POSITION),
        (_BEGIN_STORE, _STORE_ITEM),
        (_BEGIN_FETCH, _FETCH_UNIT),
        (_BEGIN_CANCEL_FETCH, _CANCEL_FETCH),
        (_BEGIN_DIRECTIVE, _DIRECTIVE_UNIT),
        (_BEGIN_CANCEL_DIRECTIVE, _CANCEL_DIRECTIVE),
    )
    for kind, phase in transitions:
        ledger.phase.copy_(torch.where(action(kind), phase, ledger.phase))

    select_target = action(_SELECT_TARGET)
    ledger.pending_target.copy_(
        torch.where(select_target, choice_fields[:, 1], ledger.pending_target)
    )
    next_target_phase = torch.where(
        ledger.pending_kind == _BEGIN_ASSET, _ASSET_PROFILE, _WORK_PROFILE
    )
    ledger.phase.copy_(torch.where(select_target, next_target_phase, ledger.phase))

    set_asset = action(_SET_ASSET)
    target = ledger.pending_target.clamp(0, ledger.cells - 1)
    proposed = torch.zeros((ledger.batch, 8), dtype=torch.long, device=ledger.device)
    proposed[:, 0] = 1
    proposed[:, 1] = torch.where(choice_fields[:, 2] - 1 < _CROPS, 1, 2)
    proposed[:, 2:7] = choice_fields[:, 2:7]
    proposed[:, 7] = 0
    current = ledger.ledger[rows, target]
    ledger.ledger[rows, target] = torch.where(set_asset[:, None], proposed, current)
    ledger.last_ledger_key.copy_(torch.where(set_asset, target * 16, ledger.last_ledger_key))
    ledger.phase.copy_(torch.where(set_asset, _ROOT, ledger.phase))

    cancel_asset = action(_CANCEL_ASSET_CHOICE)
    cancel_target = choice_fields[:, 1].clamp(0, ledger.cells - 1)
    inactive_asset = torch.zeros_like(proposed)
    inactive_asset[:, 6] = 1
    current = ledger.ledger[rows, cancel_target]
    ledger.ledger[rows, cancel_target] = torch.where(cancel_asset[:, None], inactive_asset, current)
    ledger.last_ledger_key.copy_(
        torch.where(cancel_asset, cancel_target * 16, ledger.last_ledger_key)
    )
    ledger.phase.copy_(torch.where(cancel_asset, _ROOT, ledger.phase))

    tiles = ledger.tiles
    owned = ledger.owned
    work_status = _new_work_status(ledger, choice_fields, tiles, owned)
    step = (
        (ledger.economic[:, 0].long() + 1) * ledger.turns_per_day - 1 - ledger.status_deadline[:, 0]
    )
    new_work = torch.zeros(
        (ledger.batch, ledger.architecture.work_field_count),
        dtype=torch.long,
        device=ledger.device,
    )
    new_work[:, 0] = choice_fields[:, 2] - 1
    new_work[:, 1] = choice_fields[:, 1]
    new_work[:, 2] = 0
    new_work[:, 3] = 0
    new_work[:, 4] = choice_fields[:, 6]
    new_work[:, 5:7] = work_status
    new_work[:, 7] = ledger.episode_steps - step
    add_work = action(_ADD_WORK)
    same_work = (
        ledger.work_mask
        & (ledger.work_orders[..., 0] == new_work[:, None, 0])
        & (ledger.work_orders[..., 1] == new_work[:, None, 1])
    )
    _filter_work(ledger, same_work & add_work[:, None], add_work, new_work)
    new_work_key = new_work[:, 1] * 16 + 1 + new_work[:, 0]
    ledger.last_ledger_key.copy_(torch.where(add_work, new_work_key, ledger.last_ledger_key))
    ledger.phase.copy_(torch.where(add_work, _ROOT, ledger.phase))

    cancel_work = action(_CANCEL_WORK_CHOICE)
    cancel_kind = choice_fields[:, 2] - 1
    cancel_store_item = choice_fields[:, 3] - 1
    remove = (
        ledger.work_mask
        & (ledger.work_orders[..., 0] == cancel_kind[:, None])
        & torch.where(
            cancel_kind[:, None] == 8,
            ledger.work_orders[..., 2] - 1 == cancel_store_item[:, None],
            ledger.work_orders[..., 1] == choice_fields[:, None, 1],
        )
    )
    _filter_work(ledger, remove & cancel_work[:, None], torch.zeros_like(cancel_work), new_work)
    cancelled_key = torch.where(
        cancel_kind == 8,
        ledger.cells * 16 + 2 + cancel_store_item,
        choice_fields[:, 1] * 16 + 1 + cancel_kind,
    )
    ledger.last_ledger_key.copy_(torch.where(cancel_work, cancelled_key, ledger.last_ledger_key))
    ledger.phase.copy_(torch.where(cancel_work, _ROOT, ledger.phase))

    select_role = action(_SELECT_ROLE)
    ledger.pending_role.copy_(
        torch.where(select_role, choice_fields[:, 2] - 1, ledger.pending_role)
    )
    ledger.phase.copy_(torch.where(select_role, _POSITION_TARGET, ledger.phase))

    set_position = action(_SET_POSITION)
    role = (choice_fields[:, 2] - 1).clamp(0, 1)
    position = torch.stack(
        (
            torch.ones_like(role),
            choice_fields[:, 1],
            choice_fields[:, 6],
            role,
        ),
        dim=1,
    )
    current_position = ledger.positions[rows, role]
    ledger.positions[rows, role] = torch.where(set_position[:, None], position, current_position)
    position_key = ledger.cells * 16 + role
    ledger.last_ledger_key.copy_(torch.where(set_position, position_key, ledger.last_ledger_key))
    ledger.phase.copy_(torch.where(set_position, _ROOT, ledger.phase))

    cancel_position = action(_CANCEL_POSITION_CHOICE)
    current_position = ledger.positions[rows, role]
    empty_position = torch.zeros_like(current_position)
    ledger.positions[rows, role] = torch.where(
        cancel_position[:, None], empty_position, current_position
    )
    ledger.last_ledger_key.copy_(torch.where(cancel_position, position_key, ledger.last_ledger_key))
    ledger.phase.copy_(torch.where(cancel_position, _ROOT, ledger.phase))

    select_item = action(_SELECT_STORE_ITEM)
    ledger.pending_item.copy_(
        torch.where(select_item, choice_fields[:, 2] - 1, ledger.pending_item)
    )
    ledger.phase.copy_(torch.where(select_item, _STORE_QUANTITY, ledger.phase))
    select_quantity = action(_SELECT_STORE_QUANTITY)
    ledger.pending_quantity.copy_(
        torch.where(select_quantity, choice_fields[:, 7], ledger.pending_quantity)
    )
    ledger.phase.copy_(torch.where(select_quantity, _STORE_PRIORITY, ledger.phase))

    add_store = action(_ADD_STORE)
    store_row = new_work.clone()
    store_row[:, 0] = 8
    store_row[:, 1] = -1
    store_row[:, 2] = choice_fields[:, 2]
    store_row[:, 3] = choice_fields[:, 7]
    store_row[:, 4] = choice_fields[:, 6]
    store_row[:, 5:7] = _new_work_status(
        ledger,
        torch.stack(
            (
                choice_fields[:, 0],
                choice_fields[:, 1],
                torch.full_like(choice_fields[:, 2], 9),
                choice_fields[:, 3],
                choice_fields[:, 4],
                choice_fields[:, 5],
                choice_fields[:, 6],
                choice_fields[:, 7],
            ),
            dim=1,
        ),
        tiles,
        owned,
    )
    store_same = (
        ledger.work_mask
        & (ledger.work_orders[..., 0] == 8)
        & (ledger.work_orders[..., 2] == store_row[:, None, 2])
    )
    _filter_work(ledger, store_same & add_store[:, None], add_store, store_row)
    store_key = ledger.cells * 16 + 2 + choice_fields[:, 2] - 1
    ledger.last_ledger_key.copy_(torch.where(add_store, store_key, ledger.last_ledger_key))
    ledger.phase.copy_(torch.where(add_store, _ROOT, ledger.phase))

    select_fetch_unit = action(_SELECT_FETCH_UNIT)
    ledger.pending_unit.copy_(
        torch.where(select_fetch_unit, choice_fields[:, 8] - 1, ledger.pending_unit)
    )
    ledger.phase.copy_(torch.where(select_fetch_unit, _FETCH_ITEM, ledger.phase))

    select_fetch_item = action(_SELECT_FETCH_ITEM)
    ledger.pending_item.copy_(
        torch.where(select_fetch_item, choice_fields[:, 2] - 1, ledger.pending_item)
    )
    ledger.phase.copy_(torch.where(select_fetch_item, _FETCH_QUANTITY, ledger.phase))

    set_fetch = action(_SET_FETCH)
    fetch_unit = (choice_fields[:, 8] - 1).clamp(0, ledger.layout.unit_limit - 1)
    fetch_item = (choice_fields[:, 2] - 1).clamp(0, _ITEMS - 1)
    fetch_shed = ledger.shed.gather(1, fetch_item[:, None]).squeeze(1)
    fetch_status = torch.where(
        fetch_shed > 0,
        torch.full_like(fetch_shed, _STATUS_RUNNING),
        torch.full_like(fetch_shed, _STATUS_BLOCKED),
    )
    fetch_reason = torch.where(
        fetch_shed > 0,
        torch.zeros_like(fetch_shed),
        torch.full_like(fetch_shed, _REASON_SHED_ITEM_SHORTFALL),
    )
    fetch_row = torch.zeros_like(new_work)
    fetch_row[:, 0] = 9
    fetch_row[:, 1] = -1
    fetch_row[:, 2] = choice_fields[:, 2]
    fetch_row[:, 3] = choice_fields[:, 7]
    fetch_row[:, 4] = 2
    fetch_row[:, 5] = fetch_status
    fetch_row[:, 6] = fetch_reason
    fetch_row[:, 7] = ledger.episode_steps - step
    fetch_row[:, 8] = choice_fields[:, 8]
    same_fetch = (
        ledger.work_mask
        & (ledger.work_orders[..., 0] == 9)
        & (ledger.work_orders[..., 8] == choice_fields[:, None, 8])
    )
    _filter_work(
        ledger,
        same_fetch & set_fetch[:, None],
        set_fetch,
        fetch_row,
    )
    fetch_key = ledger.cells * 16 + 2 + _ITEMS + fetch_unit
    ledger.last_ledger_key.copy_(torch.where(set_fetch, fetch_key, ledger.last_ledger_key))
    ledger.phase.copy_(torch.where(set_fetch, _ROOT, ledger.phase))

    cancel_fetch = action(_CANCEL_FETCH_CHOICE)
    cancel_fetch_unit = choice_fields[:, 8] - 1
    remove_fetch = (
        ledger.work_mask
        & (ledger.work_orders[..., 0] == 9)
        & (ledger.work_orders[..., 8] == choice_fields[:, None, 8])
    )
    _filter_work(
        ledger,
        remove_fetch & cancel_fetch[:, None],
        torch.zeros_like(cancel_fetch),
        fetch_row,
    )
    cancelled_fetch_key = ledger.cells * 16 + 2 + _ITEMS + cancel_fetch_unit
    ledger.last_ledger_key.copy_(
        torch.where(cancel_fetch, cancelled_fetch_key, ledger.last_ledger_key)
    )
    ledger.phase.copy_(torch.where(cancel_fetch, _ROOT, ledger.phase))

    select_directive_unit = action(_SELECT_DIRECTIVE_UNIT)
    ledger.pending_unit.copy_(
        torch.where(
            select_directive_unit,
            choice_fields[:, 8] - 1,
            ledger.pending_unit,
        )
    )
    ledger.phase.copy_(torch.where(select_directive_unit, _DIRECTIVE_OPERATION, ledger.phase))

    select_directive_operation = action(_SELECT_DIRECTIVE_OPERATION)
    ledger.pending_directive_operation.copy_(
        torch.where(
            select_directive_operation,
            choice_fields[:, 9],
            ledger.pending_directive_operation,
        )
    )
    ledger.pending_target.copy_(
        torch.where(
            select_directive_operation,
            torch.full_like(ledger.pending_target, -1),
            ledger.pending_target,
        )
    )
    ledger.pending_item.copy_(
        torch.where(
            select_directive_operation,
            torch.full_like(ledger.pending_item, -1),
            ledger.pending_item,
        )
    )
    ledger.pending_quantity.copy_(
        torch.where(
            select_directive_operation,
            torch.zeros_like(ledger.pending_quantity),
            ledger.pending_quantity,
        )
    )
    next_directive_phase = torch.where(
        choice_fields[:, 9] == _DIRECTIVE_WAIT,
        _DIRECTIVE_QUANTITY,
        _DIRECTIVE_TARGET,
    )
    ledger.phase.copy_(torch.where(select_directive_operation, next_directive_phase, ledger.phase))

    select_directive_target = action(_SELECT_DIRECTIVE_TARGET)
    ledger.pending_target.copy_(
        torch.where(
            select_directive_target,
            choice_fields[:, 1],
            ledger.pending_target,
        )
    )
    ledger.phase.copy_(torch.where(select_directive_target, _DIRECTIVE_ITEM, ledger.phase))

    select_directive_item = action(_SELECT_DIRECTIVE_ITEM)
    ledger.pending_item.copy_(
        torch.where(
            select_directive_item,
            choice_fields[:, 2] - 1,
            ledger.pending_item,
        )
    )
    ledger.phase.copy_(torch.where(select_directive_item, _DIRECTIVE_QUANTITY, ledger.phase))

    set_directive = action(_SET_DIRECTIVE)
    directive_row = new_work.clone()
    directive_row[:, 0] = 9 + choice_fields[:, 9]
    directive_row[:, 1] = choice_fields[:, 1]
    directive_row[:, 2] = choice_fields[:, 2]
    directive_row[:, 3] = choice_fields[:, 7]
    directive_row[:, 4] = 2
    directive_row[:, 5] = _STATUS_RUNNING
    directive_row[:, 6] = 0
    directive_row[:, 7] = ledger.turns_per_day - step.remainder(ledger.turns_per_day)
    directive_row[:, 8] = choice_fields[:, 8]
    same_directive = (
        ledger.work_mask
        & (ledger.work_orders[..., 0] >= 10)
        & (ledger.work_orders[..., 8] == choice_fields[:, None, 8])
    )
    _filter_work(
        ledger,
        same_directive & set_directive[:, None],
        set_directive,
        directive_row,
    )
    directive_unit = choice_fields[:, 8] - 1
    directive_key = ledger.cells * 16 + 2 + _ITEMS + 256 + directive_unit
    ledger.last_ledger_key.copy_(torch.where(set_directive, directive_key, ledger.last_ledger_key))
    ledger.phase.copy_(torch.where(set_directive, _ROOT, ledger.phase))

    cancel_directive = action(_CANCEL_DIRECTIVE_CHOICE)
    remove_directive = (
        ledger.work_mask
        & (ledger.work_orders[..., 0] >= 10)
        & (ledger.work_orders[..., 8] == choice_fields[:, None, 8])
    )
    _filter_work(
        ledger,
        remove_directive & cancel_directive[:, None],
        torch.zeros_like(cancel_directive),
        directive_row,
    )
    cancelled_directive_key = ledger.cells * 16 + 2 + _ITEMS + 256 + choice_fields[:, 8] - 1
    ledger.last_ledger_key.copy_(
        torch.where(
            cancel_directive,
            cancelled_directive_key,
            ledger.last_ledger_key,
        )
    )
    ledger.phase.copy_(torch.where(cancel_directive, _ROOT, ledger.phase))

    hire = action(_MARKET_HIRE)
    land = action(_MARKET_BUY_LAND)
    skip_market = action(_MARKET_SKIP_SLOT)
    immediate_market = hire | land | skip_market
    market_count = ledger.market_mask.sum(1).clamp_max(
        ledger.architecture.maximum_market_orders - 1
    )
    market_row = torch.stack(
        (
            torch.where(hire, 4, torch.where(land, 5, _MARKET_SKIP_KIND)),
            torch.where(skip_market, -1, 0),
            torch.zeros_like(choice),
        ),
        dim=1,
    )
    current_market = ledger.market_prefix[rows, market_count]
    ledger.market_prefix[rows, market_count] = torch.where(
        immediate_market[:, None], market_row, current_market
    )
    ledger.market_mask[rows, market_count] |= immediate_market
    ledger.market_phase |= immediate_market
    ledger.phase.copy_(torch.where(immediate_market, _ROOT, ledger.phase))

    pending_market = live & (choice >= _MARKET_SELL) & (choice <= _MARKET_BUY_ANIMAL)
    market_kind = torch.where(
        choice == _MARKET_SELL,
        3,
        torch.where(
            choice == _MARKET_BUY_SEED,
            0,
            torch.where(choice == _MARKET_BUY_PRODUCT, 1, 2),
        ),
    )
    ledger.pending_market_kind.copy_(
        torch.where(pending_market, market_kind, ledger.pending_market_kind)
    )
    ledger.pending_market_item.copy_(
        torch.where(pending_market, choice_fields[:, 2] - 1, ledger.pending_market_item)
    )
    ledger.pending_market_upper.copy_(
        torch.where(pending_market, choice_fields[:, 7], ledger.pending_market_upper)
    )
    ledger.market_phase |= pending_market
    ledger.phase.copy_(torch.where(pending_market, _MARKET_QUANTITY, ledger.phase))

    select_market_quantity = action(_SELECT_MARKET_QUANTITY)
    market_count = ledger.market_mask.sum(1).clamp_max(
        ledger.architecture.maximum_market_orders - 1
    )
    market_row = torch.stack(
        (
            ledger.pending_market_kind,
            ledger.pending_market_item,
            choice_fields[:, 7],
        ),
        dim=1,
    )
    current_market = ledger.market_prefix[rows, market_count]
    ledger.market_prefix[rows, market_count] = torch.where(
        select_market_quantity[:, None], market_row, current_market
    )
    ledger.market_mask[rows, market_count] |= select_market_quantity
    ledger.phase.copy_(torch.where(select_market_quantity, _ROOT, ledger.phase))
    ledger.live_candidate_count.copy_(ledger.active.sum())


__all__ = ["apply_choice"]
