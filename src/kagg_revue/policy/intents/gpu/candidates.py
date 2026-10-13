"""CUDA candidate generation for the resident intent ledger."""

from __future__ import annotations

from typing import TYPE_CHECKING

import torch
from torch import Tensor

from kagg_revue.policy.intents.data import IntentTensorState
from kagg_revue.policy.intents.gpu._ledger_abi import (
    _ADD_STORE,
    _ADD_WORK,
    _ASSET_PROFILE,
    _ASSET_TARGET,
    _BEGIN_CANCEL_DIRECTIVE,
    _BEGIN_CANCEL_FETCH,
    _BEGIN_DIRECTIVE,
    _BEGIN_FETCH,
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
    _DIRECTIVE_CARE,
    _DIRECTIVE_ITEM,
    _DIRECTIVE_OPERATION,
    _DIRECTIVE_PICKUP,
    _DIRECTIVE_PLACE,
    _DIRECTIVE_PLANT,
    _DIRECTIVE_QUANTITY,
    _DIRECTIVE_TARGET,
    _DIRECTIVE_UNIT,
    _DIRECTIVE_WAIT,
    _FERTILIZER,
    _FETCH_ITEM,
    _FETCH_QUANTITY,
    _FETCH_UNIT,
    _GOOSE,
    _ITEMS,
    _MARKET_BUY_ANIMAL,
    _MARKET_BUY_LAND,
    _MARKET_BUY_PRODUCT,
    _MARKET_BUY_SEED,
    _MARKET_HIRE,
    _MARKET_QUANTITY,
    _MARKET_SELL,
    _MARKET_SKIP_SLOT,
    _POSITION_ROLE,
    _POSITION_TARGET,
    _PRODUCTS,
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
    _STORE_ITEM,
    _STORE_PRIORITY,
    _STORE_QUANTITY,
    _WORK_PROFILE,
    _WORK_TARGET,
    _gather_rows,
)
from kagg_revue.policy.intents.gpu.types import IntentGpuDecision

if TYPE_CHECKING:
    from kagg_revue.policy.intents.gpu.ledger import IntentGpuLedger


def _market_sell_upper(ledger: IntentGpuLedger, owned: Tensor) -> Tensor:
    result = owned[:, :_PRODUCTS].clone()
    for item in range(_PRODUCTS):
        same = ledger.market_mask & (ledger.market_prefix[..., 1] == item)
        sold = torch.where(
            same & (ledger.market_prefix[..., 0] == 3),
            ledger.market_prefix[..., 2],
            0,
        ).sum(1)
        bought = torch.where(
            same & (ledger.market_prefix[..., 0] == 1),
            ledger.market_prefix[..., 2],
            0,
        ).sum(1)
        result[:, item] = result[:, item] - sold + bought
    return result.clamp_min(0)


def _candidate_templates(
    ledger: IntentGpuLedger,
    tiles: Tensor,
    carried: Tensor,
    owned: Tensor,
    applies: Tensor,
    service: Tensor,
    capacity: int,
) -> tuple[Tensor, Tensor]:
    slots = ledger._slots[:, :capacity]
    phase = ledger.phase[:, None]
    fields = torch.zeros(
        (ledger.batch, capacity, ledger.architecture.candidate_field_count),
        dtype=torch.long,
        device=ledger.device,
    )
    fields[..., 1] = -1
    valid = torch.zeros((ledger.batch, capacity), dtype=torch.bool, device=ledger.device)

    root = phase == _ROOT
    root_choice = torch.zeros_like(slots).expand(ledger.batch, -1).clone()
    root_choice[:, 1:8] = torch.arange(1, 8, device=ledger.device)
    root_choice[:, 8] = _BEGIN_FETCH
    root_choice[:, 9] = _BEGIN_CANCEL_FETCH
    root_choice[:, 10] = _BEGIN_DIRECTIVE
    root_choice[:, 11] = _BEGIN_CANCEL_DIRECTIVE
    root_choice[:, 12:21] = _MARKET_SELL
    root_choice[:, 21:26] = _MARKET_BUY_SEED
    root_choice[:, 26:28] = _MARKET_BUY_PRODUCT
    root_choice[:, 28:31] = _MARKET_BUY_ANIMAL
    root_choice[:, 31] = _MARKET_HIRE
    root_choice[:, 32] = _MARKET_BUY_LAND
    root_choice[:, 33] = _MARKET_SKIP_SLOT
    root_fields = torch.zeros_like(fields)
    root_fields[..., 1] = -1
    root_fields[..., 0] = root_choice
    root_fields[:, 12:21, 2] = torch.arange(1, 10, device=ledger.device)
    root_fields[:, 21:26, 2] = torch.arange(1, 6, device=ledger.device)
    root_fields[:, 26, 2] = 1
    root_fields[:, 27, 2] = _FERTILIZER + 1
    root_fields[:, 28:31, 2] = torch.arange(1, 4, device=ledger.device)
    sell_upper = _market_sell_upper(ledger, owned)
    root_fields[:, 12:21, 7] = sell_upper
    root_fields[:, 21:26, 7] = ledger.cells
    root_fields[:, 26:28, 7] = ledger.economic[:, 5].long()[:, None].clamp_min(1)
    root_fields[:, 28:31, 7] = ledger.cells
    work_keys = ledger._targets[None, :, None] * 16 + 1 + ledger._work_kinds[None, None]
    work_available = applies & ~service & (work_keys > ledger.last_ledger_key[:, None, None])
    fetch_unit = ledger.work_orders[..., 8] - 1
    order_key = torch.where(
        ledger.work_orders[..., 0] == 8,
        ledger.cells * 16 + 2 + ledger.work_orders[..., 2] - 1,
        torch.where(
            ledger.work_orders[..., 0] == 9,
            ledger.cells * 16 + 2 + _ITEMS + fetch_unit,
            torch.where(
                ledger.work_orders[..., 0] >= 10,
                ledger.cells * 16 + 2 + _ITEMS + 256 + fetch_unit,
                ledger.work_orders[..., 1] * 16 + 1 + ledger.work_orders[..., 0],
            ),
        ),
    )
    position_key = ledger.cells * 16 + ledger.positions[..., 3]
    store_key = ledger.cells * 16 + 2 + ledger._items[None]
    ledger_allowed = ~ledger.market_phase
    root_valid = torch.zeros_like(valid)
    root_valid[:, 0] = True
    root_valid[:, 1] = ledger_allowed & ((ledger.cells - 1) * 16 > ledger.last_ledger_key)
    asset_keys = ledger._targets[None] * 16
    root_valid[:, 2] = ledger_allowed & (
        (ledger.ledger[..., 0] != 0) & (asset_keys > ledger.last_ledger_key[:, None])
    ).any(1)
    root_valid[:, 3] = ledger_allowed & work_available.any(dim=(1, 2))
    root_valid[:, 4] = ledger_allowed & (
        ledger.work_mask
        & (ledger.work_orders[..., 0] <= 8)
        & (order_key > ledger.last_ledger_key[:, None])
    ).any(1)
    root_valid[:, 5] = ledger_allowed & (ledger.cells * 16 + 1 > ledger.last_ledger_key)
    root_valid[:, 6] = ledger_allowed & (
        (ledger.positions[..., 0] != 0) & (position_key > ledger.last_ledger_key[:, None])
    ).any(1)
    root_valid[:, 7] = ledger_allowed & (
        (carried > 0) & (store_key > ledger.last_ledger_key[:, None])
    ).any(1)
    unit_count = ledger.economic[:, 1].long().clamp(1, ledger.layout.unit_limit)
    unit_present = ledger._units[None] < unit_count[:, None]
    fetch_keys = (ledger.cells * 16 + 2 + _ITEMS + ledger._units[None]).expand(ledger.batch, -1)
    fetch_available = (
        unit_present[:, :, None]
        & (fetch_keys > ledger.last_ledger_key[:, None])[:, :, None]
        & (ledger.shed[:, None, :] > 0)
        & (ledger.unit_inventories < ledger.economic[:, 5].long()[:, None, None])
    )
    root_valid[:, 8] = ledger_allowed & fetch_available.any(dim=(1, 2))
    active_fetch = ledger.work_mask & (ledger.work_orders[..., 0] == 9)
    root_valid[:, 9] = ledger_allowed & (
        active_fetch & (order_key > ledger.last_ledger_key[:, None])
    ).any(1)
    directive_keys = (ledger.cells * 16 + 2 + _ITEMS + 256 + ledger._units[None]).expand(
        ledger.batch, -1
    )
    active_directive = ledger.work_mask & (ledger.work_orders[..., 0] >= 10)
    root_valid[:, 10] = ledger_allowed & (
        unit_present & (directive_keys > ledger.last_ledger_key[:, None])
    ).any(1)
    root_valid[:, 11] = ledger_allowed & (
        active_directive & (order_key > ledger.last_ledger_key[:, None])
    ).any(1)
    market_count = ledger.market_mask.sum(1)
    market_room = market_count < ledger.architecture.maximum_market_orders
    root_valid[:, 12:21] = market_room[:, None] & (sell_upper > 0)
    root_valid[:, 21:31] = market_room[:, None]
    root_valid[:, 31] = market_room
    land_count = (ledger.market_mask & (ledger.market_prefix[..., 0] == 5)).sum(1)
    root_valid[:, 32] = market_room & (ledger.economic[:, 11].long() + land_count < 3)
    root_valid[:, 33] = market_room
    fields = torch.where(root[..., None], root_fields, fields)
    valid |= root & root_valid

    target = slots.clamp_max(ledger.cells - 1)
    target_fields = torch.zeros_like(fields)
    target_fields[..., 0] = _SELECT_TARGET
    target_fields[..., 1] = target
    asset_target = phase == _ASSET_TARGET
    asset_target_valid = (slots < ledger.cells) & (target * 16 > ledger.last_ledger_key[:, None])
    fields = torch.where(asset_target[..., None], target_fields, fields)
    valid |= asset_target & asset_target_valid

    profile_fields = torch.zeros_like(fields)
    crop_slot = slots.clamp(0, 44)
    crop = crop_slot // 9
    crop_remainder = crop_slot % 9
    animal_slot = (slots - 45).clamp(0, 107)
    animal = animal_slot // 36
    animal_remainder = animal_slot % 36
    animal_maintenance = torch.where(
        animal_remainder // 12 == 2,
        3,
        animal_remainder // 12,
    )
    is_crop_profile = slots < 45
    profile_fields[..., 0] = _SET_ASSET
    profile_fields[..., 1] = ledger.pending_target[:, None]
    profile_fields[..., 2] = torch.where(is_crop_profile, crop + 1, _GOOSE + animal + 1)
    profile_fields[..., 3] = torch.where(is_crop_profile, crop_remainder // 3, animal_maintenance)
    profile_fields[..., 4] = torch.where(is_crop_profile, 0, (animal_remainder % 12) // 6)
    profile_fields[..., 5] = torch.where(is_crop_profile, 0, (animal_remainder % 6) // 3)
    profile_fields[..., 6] = torch.where(is_crop_profile, crop_remainder % 3, animal_remainder % 3)
    safe_pending = ledger.pending_target.clamp(0, ledger.cells - 1)
    current = ledger.ledger.gather(1, safe_pending[:, None, None].expand(-1, 1, 8)).squeeze(1)
    proposed_kind = torch.where(is_crop_profile, 1, 2)
    same_profile = (
        (current[:, None, 0] != 0)
        & (current[:, None, 1] == proposed_kind)
        & (current[:, None, 2] == profile_fields[..., 2])
        & (current[:, None, 3] == profile_fields[..., 3])
        & (current[:, None, 4] == profile_fields[..., 4])
        & (current[:, None, 5] == profile_fields[..., 5])
        & (current[:, None, 6] == profile_fields[..., 6])
    )
    asset_profile = phase == _ASSET_PROFILE
    asset_profile_valid = (slots < 153) & ~same_profile
    fields = torch.where(asset_profile[..., None], profile_fields, fields)
    valid |= asset_profile & asset_profile_valid

    cancel_asset_fields = target_fields.clone()
    cancel_asset_fields[..., 0] = _CANCEL_ASSET_CHOICE
    cancel_asset = phase == _CANCEL_ASSET
    target_active = ledger.ledger[..., 0].gather(1, target.expand(ledger.batch, -1))
    cancel_asset_valid = (
        (slots < ledger.cells)
        & (target_active != 0)
        & (target * 16 > ledger.last_ledger_key[:, None])
    )
    fields = torch.where(cancel_asset[..., None], cancel_asset_fields, fields)
    valid |= cancel_asset & cancel_asset_valid

    work_target = phase == _WORK_TARGET
    target_work_available = work_available.any(2).gather(1, target.expand(ledger.batch, -1))
    work_target_valid = (slots < ledger.cells) & target_work_available
    fields = torch.where(work_target[..., None], target_fields, fields)
    valid |= work_target & work_target_valid

    work_profile_fields = torch.zeros_like(fields)
    profile_kind = (slots // 3).clamp(0, 7)
    profile_priority = slots % 3
    work_profile_fields[..., 0] = _ADD_WORK
    work_profile_fields[..., 1] = ledger.pending_target[:, None]
    work_profile_fields[..., 2] = profile_kind + 1
    work_profile_fields[..., 6] = profile_priority
    pending_available = work_available.gather(
        1,
        safe_pending[:, None, None].expand(-1, 1, 8),
    ).squeeze(1)
    existing_same = (
        ledger.work_mask[:, :, None]
        & (ledger.work_orders[:, :, 1, None] == ledger.pending_target[:, None, None])
        & (ledger.work_orders[:, :, 0, None] == profile_kind[:, None])
        & (ledger.work_orders[:, :, 4, None] == profile_priority[:, None])
    ).any(1)
    work_profile = phase == _WORK_PROFILE
    work_profile_valid = (
        (slots < 24)
        & pending_available.gather(1, profile_kind.expand(ledger.batch, -1))
        & ~existing_same
    )
    fields = torch.where(work_profile[..., None], work_profile_fields, fields)
    valid |= work_profile & work_profile_valid

    cancel_work_fields = torch.zeros_like(fields)
    cancel_work_fields[..., 0] = _CANCEL_WORK_CHOICE
    cancel_width = min(capacity, ledger.work_capacity)
    cancel_work_fields[:, :cancel_width, 1] = ledger.work_orders[:, :cancel_width, 1]
    cancel_work_fields[:, :cancel_width, 2] = ledger.work_orders[:, :cancel_width, 0] + 1
    cancel_work_fields[:, :cancel_width, 3] = ledger.work_orders[:, :cancel_width, 2]
    cancel_work = phase == _CANCEL_WORK
    cancel_work_valid = torch.zeros_like(valid)
    cancel_work_valid[:, :cancel_width] = ledger.work_mask[:, :cancel_width] & (
        order_key[:, :cancel_width] > ledger.last_ledger_key[:, None]
    )
    fields = torch.where(cancel_work[..., None], cancel_work_fields, fields)
    valid |= cancel_work & cancel_work_valid

    role = slots.clamp(0, 1)
    role_fields = torch.zeros_like(fields)
    role_fields[..., 1] = -1
    role_fields[..., 0] = _SELECT_ROLE
    role_fields[..., 2] = role + 1
    position_role = phase == _POSITION_ROLE
    role_valid = (slots < 2) & (ledger.cells * 16 + role > ledger.last_ledger_key[:, None])
    fields = torch.where(position_role[..., None], role_fields, fields)
    valid |= position_role & role_valid

    position_fields = torch.zeros_like(fields)
    position_target = (slots // 3).clamp_max(ledger.cells - 1)
    position_priority = slots % 3
    position_fields[..., 0] = _SET_POSITION
    position_fields[..., 1] = position_target
    position_fields[..., 2] = ledger.pending_role[:, None] + 1
    position_fields[..., 6] = position_priority
    current_position = ledger.positions.gather(
        1, ledger.pending_role[:, None, None].expand(-1, 1, 4)
    ).squeeze(1)
    same_position = (
        (current_position[:, None, 0] != 0)
        & (current_position[:, None, 1] == position_target)
        & (current_position[:, None, 2] == position_priority)
    )
    position_target_phase = phase == _POSITION_TARGET
    position_target_valid = (slots < ledger.cells * 3) & ~same_position
    fields = torch.where(position_target_phase[..., None], position_fields, fields)
    valid |= position_target_phase & position_target_valid

    cancel_position_fields = torch.zeros_like(fields)
    cancel_position_fields[..., 1] = -1
    cancel_position_fields[..., 0] = _CANCEL_POSITION_CHOICE
    cancel_position_fields[..., 2] = role + 1
    cancel_position = phase == _CANCEL_POSITION
    selected_position_active = ledger.positions[..., 0].gather(1, role.expand(ledger.batch, -1))
    selected_position_key = position_key.gather(1, role.expand(ledger.batch, -1))
    cancel_position_valid = (
        (slots < 2)
        & (selected_position_active != 0)
        & (selected_position_key > ledger.last_ledger_key[:, None])
    )
    fields = torch.where(cancel_position[..., None], cancel_position_fields, fields)
    valid |= cancel_position & cancel_position_valid

    item = slots.clamp_max(_ITEMS - 1)
    store_item_fields = torch.zeros_like(fields)
    store_item_fields[..., 1] = -1
    store_item_fields[..., 0] = _SELECT_STORE_ITEM
    store_item_fields[..., 2] = item + 1
    store_item = phase == _STORE_ITEM
    store_item_valid = (
        (slots < _ITEMS)
        & (carried.gather(1, item.expand(ledger.batch, -1)) > 0)
        & (ledger.cells * 16 + 2 + item > ledger.last_ledger_key[:, None])
    )
    fields = torch.where(store_item[..., None], store_item_fields, fields)
    valid |= store_item & store_item_valid

    safe_item = ledger.pending_item.clamp(0, _ITEMS - 1)
    selected_carried = _gather_rows(carried, safe_item)
    quantity = slots + 1
    store_quantity_fields = torch.zeros_like(fields)
    store_quantity_fields[..., 1] = -1
    store_quantity_fields[..., 0] = _SELECT_STORE_QUANTITY
    store_quantity_fields[..., 2] = ledger.pending_item[:, None] + 1
    store_quantity_fields[..., 7] = quantity
    store_quantity = phase == _STORE_QUANTITY
    store_quantity_valid = quantity <= selected_carried[:, None]
    fields = torch.where(store_quantity[..., None], store_quantity_fields, fields)
    valid |= store_quantity & store_quantity_valid

    store_priority_fields = torch.zeros_like(fields)
    store_priority_fields[..., 1] = -1
    store_priority_fields[..., 0] = _ADD_STORE
    store_priority_fields[..., 2] = ledger.pending_item[:, None] + 1
    store_priority_fields[..., 6] = slots
    store_priority_fields[..., 7] = ledger.pending_quantity[:, None]
    same_store = (
        ledger.work_mask[:, :, None]
        & (ledger.work_orders[:, :, 0, None] == 8)
        & (ledger.work_orders[:, :, 2, None] == ledger.pending_item[:, None, None] + 1)
        & (ledger.work_orders[:, :, 3, None] == ledger.pending_quantity[:, None, None])
        & (ledger.work_orders[:, :, 4, None] == slots[:, None])
    ).any(1)
    store_priority = phase == _STORE_PRIORITY
    store_priority_valid = (slots < 3) & ~same_store
    fields = torch.where(store_priority[..., None], store_priority_fields, fields)
    valid |= store_priority & store_priority_valid

    market_quantity_fields = torch.zeros_like(fields)
    market_quantity_fields[..., 1] = -1
    market_quantity_fields[..., 0] = _SELECT_MARKET_QUANTITY
    market_quantity_fields[..., 2] = ledger.pending_market_item[:, None] + 1
    market_quantity_fields[..., 7] = quantity
    market_quantity = phase == _MARKET_QUANTITY
    market_quantity_valid = quantity <= ledger.pending_market_upper[:, None]
    fields = torch.where(market_quantity[..., None], market_quantity_fields, fields)
    valid |= market_quantity & market_quantity_valid

    fetch_unit_fields = torch.zeros_like(fields)
    fetch_unit_fields[..., 1] = -1
    fetch_unit_fields[..., 0] = _SELECT_FETCH_UNIT
    fetch_unit_fields[..., 8] = slots + 1
    fetch_unit_phase = phase == _FETCH_UNIT
    fetch_unit_valid = (
        (slots < ledger.layout.unit_limit)
        & unit_present.gather(
            1, slots.clamp_max(ledger.layout.unit_limit - 1).expand(ledger.batch, -1)
        )
        & (
            fetch_keys.gather(
                1,
                slots.clamp_max(ledger.layout.unit_limit - 1).expand(ledger.batch, -1),
            )
            > ledger.last_ledger_key[:, None]
        )
        & fetch_available.any(2).gather(
            1, slots.clamp_max(ledger.layout.unit_limit - 1).expand(ledger.batch, -1)
        )
    )
    fields = torch.where(fetch_unit_phase[..., None], fetch_unit_fields, fields)
    valid |= fetch_unit_phase & fetch_unit_valid

    pending_unit = ledger.pending_unit.clamp(0, ledger.layout.unit_limit - 1)
    selected_inventory = ledger.unit_inventories.gather(
        1, pending_unit[:, None, None].expand(-1, 1, _ITEMS)
    ).squeeze(1)
    fetch_item_fields = torch.zeros_like(fields)
    fetch_item_fields[..., 1] = -1
    fetch_item_fields[..., 0] = _SELECT_FETCH_ITEM
    fetch_item_fields[..., 2] = item + 1
    fetch_item_fields[..., 8] = ledger.pending_unit[:, None] + 1
    fetch_item_phase = phase == _FETCH_ITEM
    fetch_item_valid = (
        (slots < _ITEMS)
        & (ledger.shed.gather(1, item.expand(ledger.batch, -1)) > 0)
        & (
            selected_inventory.gather(1, item.expand(ledger.batch, -1))
            < ledger.economic[:, 5].long()[:, None]
        )
    )
    fields = torch.where(fetch_item_phase[..., None], fetch_item_fields, fields)
    valid |= fetch_item_phase & fetch_item_valid

    fetch_safe_item = ledger.pending_item.clamp(0, _ITEMS - 1)
    selected_unit_carried = selected_inventory.gather(1, fetch_safe_item[:, None]).squeeze(1)
    selected_shed = ledger.shed.gather(1, fetch_safe_item[:, None]).squeeze(1)
    fetch_upper = torch.minimum(ledger.economic[:, 5].long(), selected_unit_carried + selected_shed)
    fetch_quantity_fields = torch.zeros_like(fields)
    fetch_quantity_fields[..., 1] = -1
    fetch_quantity_fields[..., 0] = _SET_FETCH
    fetch_quantity_fields[..., 2] = ledger.pending_item[:, None] + 1
    fetch_quantity_fields[..., 6] = 2
    fetch_quantity_fields[..., 7] = quantity
    fetch_quantity_fields[..., 8] = ledger.pending_unit[:, None] + 1
    fetch_quantity_phase = phase == _FETCH_QUANTITY
    fetch_quantity_valid = (quantity > selected_unit_carried[:, None]) & (
        quantity <= fetch_upper[:, None]
    )
    fields = torch.where(fetch_quantity_phase[..., None], fetch_quantity_fields, fields)
    valid |= fetch_quantity_phase & fetch_quantity_valid

    cancel_fetch_fields = torch.zeros_like(fields)
    cancel_fetch_fields[..., 1] = -1
    cancel_fetch_fields[..., 0] = _CANCEL_FETCH_CHOICE
    candidate_unit = slots.clamp_max(ledger.layout.unit_limit - 1)
    fetch_match = active_fetch[:, :, None] & (
        ledger.work_orders[:, :, 8, None] == candidate_unit[None] + 1
    )
    fetch_row_index = fetch_match.long().argmax(1)
    fetch_row = ledger.work_orders.gather(
        1,
        fetch_row_index[..., None].expand(-1, -1, ledger.architecture.work_field_count),
    )
    cancel_fetch_fields[..., 2] = fetch_row[..., 2]
    cancel_fetch_fields[..., 6] = 2
    cancel_fetch_fields[..., 7] = fetch_row[..., 3]
    cancel_fetch_fields[..., 8] = candidate_unit + 1
    cancel_fetch_phase = phase == _CANCEL_FETCH
    candidate_fetch_key = (ledger.cells * 16 + 2 + _ITEMS + candidate_unit).expand(ledger.batch, -1)
    cancel_fetch_valid = (
        (slots < ledger.layout.unit_limit)
        & fetch_match.any(1)
        & (candidate_fetch_key > ledger.last_ledger_key[:, None])
    )
    fields = torch.where(cancel_fetch_phase[..., None], cancel_fetch_fields, fields)
    valid |= cancel_fetch_phase & cancel_fetch_valid

    directive_unit_fields = torch.zeros_like(fields)
    directive_unit_fields[..., 1] = -1
    directive_unit_fields[..., 0] = _SELECT_DIRECTIVE_UNIT
    directive_unit_fields[..., 8] = slots + 1
    directive_unit_phase = phase == _DIRECTIVE_UNIT
    directive_unit_index = slots.clamp_max(ledger.layout.unit_limit - 1).expand(ledger.batch, -1)
    directive_unit_valid = (
        (slots < ledger.layout.unit_limit)
        & unit_present.gather(1, directive_unit_index)
        & (directive_keys.gather(1, directive_unit_index) > ledger.last_ledger_key[:, None])
    )
    fields = torch.where(directive_unit_phase[..., None], directive_unit_fields, fields)
    valid |= directive_unit_phase & directive_unit_valid

    directive_operation_fields = torch.zeros_like(fields)
    directive_operation_fields[..., 1] = -1
    directive_operation_fields[..., 0] = _SELECT_DIRECTIVE_OPERATION
    directive_operation_fields[..., 8] = ledger.pending_unit[:, None] + 1
    directive_operation_fields[..., 9] = slots + 1
    directive_operation_phase = phase == _DIRECTIVE_OPERATION
    directive_operation_valid = slots < _DIRECTIVE_CARE
    fields = torch.where(
        directive_operation_phase[..., None],
        directive_operation_fields,
        fields,
    )
    valid |= directive_operation_phase & directive_operation_valid

    directive_target_fields = torch.zeros_like(fields)
    directive_target_fields[..., 1] = target
    directive_target_fields[..., 6] = 2
    directive_target_fields[..., 8] = ledger.pending_unit[:, None] + 1
    directive_target_fields[..., 9] = ledger.pending_directive_operation[:, None]
    directive_needs_item = (
        (ledger.pending_directive_operation == _DIRECTIVE_PICKUP)
        | (ledger.pending_directive_operation == _DIRECTIVE_PLACE)
        | (ledger.pending_directive_operation == _DIRECTIVE_PLANT)
    )
    directive_target_fields[..., 0] = torch.where(
        directive_needs_item[:, None], _SELECT_DIRECTIVE_TARGET, _SET_DIRECTIVE
    )
    directive_target_phase = phase == _DIRECTIVE_TARGET
    directive_target_valid = slots < ledger.cells
    fields = torch.where(directive_target_phase[..., None], directive_target_fields, fields)
    valid |= directive_target_phase & directive_target_valid

    directive_item_fields = torch.zeros_like(fields)
    directive_item_fields[..., 0] = torch.where(
        (
            (ledger.pending_directive_operation == _DIRECTIVE_PICKUP)
            | (ledger.pending_directive_operation == _DIRECTIVE_PLACE)
        )[:, None],
        _SELECT_DIRECTIVE_ITEM,
        _SET_DIRECTIVE,
    )
    directive_item_fields[..., 1] = ledger.pending_target[:, None]
    directive_item_fields[..., 2] = item + 1
    directive_item_fields[..., 6] = 2
    directive_item_fields[..., 8] = ledger.pending_unit[:, None] + 1
    directive_item_fields[..., 9] = ledger.pending_directive_operation[:, None]
    directive_item_phase = phase == _DIRECTIVE_ITEM
    directive_item_upper = torch.where(
        ledger.pending_directive_operation == _DIRECTIVE_PLANT,
        torch.full_like(ledger.pending_directive_operation, 5),
        torch.full_like(ledger.pending_directive_operation, _ITEMS),
    )
    directive_item_valid = slots < directive_item_upper[:, None]
    fields = torch.where(directive_item_phase[..., None], directive_item_fields, fields)
    valid |= directive_item_phase & directive_item_valid

    directive_quantity_fields = torch.zeros_like(fields)
    directive_quantity_fields[..., 0] = _SET_DIRECTIVE
    directive_quantity_fields[..., 1] = ledger.pending_target[:, None]
    directive_quantity_fields[..., 2] = ledger.pending_item[:, None] + 1
    directive_quantity_fields[..., 6] = 2
    directive_quantity_fields[..., 7] = quantity
    directive_quantity_fields[..., 8] = ledger.pending_unit[:, None] + 1
    directive_quantity_fields[..., 9] = ledger.pending_directive_operation[:, None]
    directive_quantity_phase = phase == _DIRECTIVE_QUANTITY
    step = (
        (ledger.economic[:, 0].long() + 1) * ledger.turns_per_day - 1 - ledger.status_deadline[:, 0]
    )
    hour = step.remainder(ledger.turns_per_day)
    directive_wait = ledger.pending_directive_operation == _DIRECTIVE_WAIT
    directive_quantity_upper = torch.where(
        directive_wait,
        torch.full_like(hour, ledger.turns_per_day),
        ledger.economic[:, 5].long(),
    )
    directive_quantity_valid = quantity <= directive_quantity_upper[:, None]
    directive_quantity_valid &= ~directive_wait[:, None] | (quantity > hour[:, None])
    fields = torch.where(
        directive_quantity_phase[..., None],
        directive_quantity_fields,
        fields,
    )
    valid |= directive_quantity_phase & directive_quantity_valid

    cancel_directive_fields = torch.zeros_like(fields)
    cancel_directive_fields[..., 1] = -1
    cancel_directive_fields[..., 0] = _CANCEL_DIRECTIVE_CHOICE
    directive_candidate_unit = slots.clamp_max(ledger.layout.unit_limit - 1)
    directive_match = active_directive[:, :, None] & (
        ledger.work_orders[:, :, 8, None] == directive_candidate_unit[None] + 1
    )
    directive_row_index = directive_match.long().argmax(1)
    directive_row = ledger.work_orders.gather(
        1,
        directive_row_index[..., None].expand(-1, -1, ledger.architecture.work_field_count),
    )
    cancel_directive_fields[..., 1] = directive_row[..., 1]
    cancel_directive_fields[..., 2] = directive_row[..., 2]
    cancel_directive_fields[..., 6] = 2
    cancel_directive_fields[..., 7] = directive_row[..., 3]
    cancel_directive_fields[..., 8] = directive_candidate_unit + 1
    cancel_directive_fields[..., 9] = directive_row[..., 0] - 9
    cancel_directive_phase = phase == _CANCEL_DIRECTIVE
    candidate_directive_key = (
        ledger.cells * 16 + 2 + _ITEMS + 256 + directive_candidate_unit
    ).expand(ledger.batch, -1)
    cancel_directive_valid = (
        (slots < ledger.layout.unit_limit)
        & directive_match.any(1)
        & (candidate_directive_key > ledger.last_ledger_key[:, None])
    )
    fields = torch.where(cancel_directive_phase[..., None], cancel_directive_fields, fields)
    valid |= cancel_directive_phase & cancel_directive_valid
    return fields, valid


def _candidate_features(ledger: IntentGpuLedger, fields: Tensor, owned: Tensor) -> Tensor:
    features = torch.zeros(
        (ledger.batch, fields.shape[1], 12),
        dtype=torch.float32,
        device=ledger.device,
    )
    choice = fields[..., 0]
    target = fields[..., 1]
    item = fields[..., 2] - 1
    features[..., 0] = choice.float() / 40.0
    features[..., 1] = ledger.phase[:, None].float() / 24.0
    market = ((choice >= _MARKET_SELL) & (choice <= _SELECT_MARKET_QUANTITY)) | (
        choice == _MARKET_SKIP_SLOT
    )
    features[..., 2] = ((choice != _COMMIT) & ~market).float()
    features[..., 3] = market.float()
    valid_target = (target >= 0) & (target < ledger.cells)
    safe_target = target.clamp(0, ledger.cells - 1)
    features[..., 4] = torch.where(
        valid_target,
        (safe_target % ledger.architecture.board_size).float()
        / max(1, ledger.architecture.board_size - 1),
        0.0,
    )
    features[..., 5] = torch.where(
        valid_target,
        (safe_target // ledger.architecture.board_size).float()
        / max(1, ledger.architecture.board_size - 1),
        0.0,
    )
    unit = fields[..., 8] - 1
    valid_unit = (unit >= 0) & (unit < ledger.layout.unit_limit)
    safe_unit = unit.clamp(0, ledger.layout.unit_limit - 1)
    unit_position = ledger.unit_positions.gather(1, safe_unit[..., None].expand(-1, -1, 2))
    features[..., 4] = torch.where(
        valid_unit,
        unit_position[..., 0].float() / max(1, ledger.architecture.board_size - 1),
        features[..., 4],
    )
    features[..., 5] = torch.where(
        valid_unit,
        unit_position[..., 1].float() / max(1, ledger.architecture.board_size - 1),
        features[..., 5],
    )
    features[..., 6] = fields[..., 7].float() / ledger.economic[:, 5].float().clamp_min(1)[:, None]
    valid_item = (item >= 0) & (item < _ITEMS)
    safe_item = item.clamp(0, _ITEMS - 1)
    features[..., 7] = torch.where(valid_item, (safe_item + 1).float() / _ITEMS, 0.0)
    features[..., 9] = torch.where(
        valid_item,
        owned.gather(1, safe_item).float() / ledger.economic[:, 5].float().clamp_min(1)[:, None],
        0.0,
    )
    product = valid_item & (safe_item < _PRODUCTS)
    safe_product = safe_item.clamp_max(_PRODUCTS - 1)
    ratio = ledger.market_product_ratio.gather(1, safe_product)
    features[..., 8] = torch.where(product, ratio.float(), 0.0)
    active = ledger.ledger[..., 0].gather(1, safe_target)
    features[..., 10] = torch.where(valid_target, active.float(), 0.0)
    features[..., 11] = ledger.market_mask.sum(1).float()[:, None] / max(
        1, ledger.architecture.maximum_market_orders
    )
    return features


def compile_decision(
    ledger: IntentGpuLedger,
    candidate_capacity: int | None = None,
) -> IntentGpuDecision:
    """Generate a compact, padded candidate batch entirely on device."""
    capacity = ledger.candidate_capacity if candidate_capacity is None else candidate_capacity
    if capacity < 34 or capacity > ledger.candidate_capacity:
        raise ValueError("intent candidate capacity is outside the ledger allocation")
    carried = ledger.carried
    owned = ledger.owned
    tiles = ledger.tiles
    applies, service = ledger._work_applicability(tiles)
    fields, valid = _candidate_templates(
        ledger,
        tiles,
        carried,
        owned,
        applies,
        service,
        capacity,
    )
    order = torch.argsort(~valid, dim=1, stable=True)
    fields = fields.gather(
        1,
        order[..., None].expand(-1, -1, ledger.architecture.candidate_field_count),
    )
    mask = valid.gather(1, order)
    features = _candidate_features(ledger, fields, owned)
    counts = mask.sum(1)
    force = (ledger.trace_counts >= ledger.maximum_steps - 1) & (ledger.phase == _ROOT)
    commit_mask = mask & (fields[..., 0] == _COMMIT)
    mask = torch.where(force[:, None], commit_mask, mask)
    dead = ~ledger.active
    mask[:, 0] |= dead
    fields[:, 0, 0] = torch.where(dead, _COMMIT, fields[:, 0, 0])
    counts = torch.where(ledger.active, counts, 0)
    ledger.live_candidate_count.copy_(counts.max())
    return IntentGpuDecision(
        state=IntentTensorState(
            candidate_fields=fields,
            candidate_features=features,
            candidate_mask=mask,
            ledger=ledger.ledger,
            status=ledger._status(tiles, owned),
            work_priorities=ledger._work_priorities(),
            work_orders=ledger.work_orders,
            work_mask=ledger.work_mask,
            positions=ledger.positions,
            market_prefix=ledger.market_prefix,
            market_mask=ledger.market_mask,
            phase=ledger.phase,
        ),
        candidate_counts=counts,
    )


__all__ = ["compile_decision"]
