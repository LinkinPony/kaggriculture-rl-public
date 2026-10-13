"""Deterministic replay of the economic state used by feature compilation."""

from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import Tensor

from kagg_revue.policy.economics.layout import (
    ITEMS,
    MARKET_PROJECTION_CONDITIONAL,
    MAXIMUM_QUANTITY,
    EconomicStateLayout,
)
from kagg_revue.policy.economics.pricing import (
    fibonacci,
    gather_cumulative,
    market_curves,
)
from kagg_revue.policy.vocabulary import CURRENT_ACTIONS, ActionVocabulary


@dataclass(frozen=True)
class MarketConsequence:
    """No-opponent projection for one selected market order."""

    committed: Tensor
    cash_delta: Tensor
    item: Tensor
    shed_delta: Tensor
    seed_delta: Tensor
    market_delta: Tensor
    unit_price: Tensor
    conditional: Tensor


def _rows(state: Tensor) -> Tensor:
    return torch.arange(state.shape[0], device=state.device)


def _gather(state: Tensor, index: Tensor) -> Tensor:
    return state[_rows(state), index.long()]


def market_consequence(
    state: Tensor,
    tokens: Tensor,
    requested: Tensor,
    layout: EconomicStateLayout,
    vocabulary: ActionVocabulary = CURRENT_ACTIONS,
) -> MarketConsequence:
    """Project selected market actions with explicit opponent-conditional flags."""
    rows = _rows(state)
    tokens = tokens.long()
    requested = requested.long().clamp(0, MAXIMUM_QUANTITY)
    money = state[:, 9].float().clamp_min(0.0)
    capacity = state[:, 5].long()
    shed_total = state[:, 8].long()
    free = (capacity - shed_total).clamp_min(0)

    is_sell = (tokens >= vocabulary.sell_first) & (
        tokens < vocabulary.sell_first + 9
    )
    is_seed = (tokens >= vocabulary.seed_first) & (
        tokens < vocabulary.seed_first + 5
    )
    is_product = (tokens >= vocabulary.product_first) & (
        tokens < vocabulary.product_first + 2
    )
    is_animal = (tokens >= vocabulary.animal_first) & (
        tokens < vocabulary.animal_first + 3
    )
    is_hire = tokens == vocabulary.hire
    is_land = tokens == vocabulary.buy_land
    product = torch.where(
        tokens == vocabulary.product_first + 1,
        torch.full_like(tokens, 8),
        tokens - vocabulary.product_first,
    )
    item = torch.where(
        is_sell,
        tokens - vocabulary.sell_first,
        torch.where(
            is_seed,
            tokens - vocabulary.seed_first,
            torch.where(
                is_product,
                product,
                torch.where(
                    is_animal,
                    tokens - vocabulary.animal_first + 9,
                    torch.zeros_like(tokens),
                ),
            ),
        ),
    ).clamp(0, ITEMS - 1)

    shed_count = state[rows, layout.shed + item].long().clamp_min(0)
    seed_cost = state[
        rows, layout.seed_costs + (tokens - vocabulary.seed_first).clamp(0, 4)
    ].float()
    animal_cost = state[
        rows,
        layout.animal_costs + (tokens - vocabulary.animal_first).clamp(0, 2),
    ].float()
    hires = state[:, 10].long()
    hire_cost = state[:, 12].float() * fibonacci(hires)
    land_level = state[:, 11].long()
    land_cost = state[
        rows,
        layout.land_costs + land_level.clamp(0, 2),
    ].float()

    curve_product = torch.where(is_sell, item, product).clamp(0, 8)
    sell_prices, sell_cumulative, buy_prices, buy_cumulative = market_curves(
        state,
        curve_product,
        MAXIMUM_QUANTITY,
        layout,
    )
    affordable_product = (buy_cumulative <= money[:, None]).sum(dim=-1).long()
    seed_max = torch.floor(money / seed_cost.clamp_min(1.0)).long()
    animal_max = torch.minimum(
        free,
        torch.floor(money / animal_cost.clamp_min(1.0)).long(),
    )
    maximum = torch.where(
        is_sell,
        shed_count,
        torch.where(
            is_seed,
            seed_max,
            torch.where(
                is_product,
                torch.minimum(free, affordable_product),
                torch.where(
                    is_animal,
                    animal_max,
                    torch.where(
                        is_hire,
                        (
                            (money >= hire_cost)
                            & (state[:, 1] < layout.unit_limit)
                        ).long(),
                        torch.where(
                            is_land,
                            ((land_level < 3) & (money >= land_cost)).long(),
                            torch.zeros_like(requested),
                        ),
                    ),
                ),
            ),
        ),
    ).clamp(0, MAXIMUM_QUANTITY)
    atomic = is_hire | is_land
    effective_request = torch.where(atomic, torch.ones_like(requested), requested)
    committed = torch.minimum(effective_request, maximum)

    sell_revenue = gather_cumulative(sell_cumulative, committed)
    buy_cost = gather_cumulative(buy_cumulative, committed)
    fixed_cost = torch.where(
        is_seed,
        seed_cost,
        torch.where(
            is_animal,
            animal_cost,
            torch.where(is_hire, hire_cost, land_cost),
        ),
    )
    cash_delta = torch.where(
        is_sell,
        sell_revenue,
        torch.where(
            is_product,
            -buy_cost,
            -fixed_cost * committed.float(),
        ),
    )
    shed_delta = torch.where(
        is_sell,
        -committed,
        torch.where(is_product | is_animal, committed, torch.zeros_like(committed)),
    )
    seed_delta = torch.where(is_seed, committed, torch.zeros_like(committed))
    sell_inventory_units = gather_cumulative(
        (sell_prices > 1.0).long().cumsum(dim=-1),
        committed,
    ).long()
    market_delta = torch.where(
        is_sell,
        sell_inventory_units,
        torch.where(is_product, -committed, torch.zeros_like(committed)),
    )
    first_sell = sell_prices[:, 0]
    first_buy = buy_prices[:, 0]
    unit_price = torch.where(
        is_sell,
        first_sell,
        torch.where(is_product, first_buy, fixed_cost),
    )
    active = is_sell | is_seed | is_product | is_animal | is_hire | is_land
    committed = torch.where(active, committed, torch.zeros_like(committed))
    return MarketConsequence(
        committed=committed,
        cash_delta=torch.where(active, cash_delta, torch.zeros_like(cash_delta)),
        item=item,
        shed_delta=torch.where(active, shed_delta, torch.zeros_like(shed_delta)),
        seed_delta=torch.where(active, seed_delta, torch.zeros_like(seed_delta)),
        market_delta=torch.where(active, market_delta, torch.zeros_like(market_delta)),
        unit_price=torch.where(active, unit_price, torch.zeros_like(unit_price)),
        conditional=is_sell | is_product,
    )


def project_market_selection(
    state: Tensor,
    tokens: Tensor,
    quantities: Tensor,
    phases: Tensor,
    active: Tensor,
    layout: EconomicStateLayout,
    vocabulary: ActionVocabulary = CURRENT_ACTIONS,
) -> None:
    """Apply the visible no-opponent market projection in place."""
    if state.device.type == "cuda":
        if vocabulary != CURRENT_ACTIONS:
            raise ValueError("legacy economic transitions require CPU tensors")
        from kagg_revue.policy.economics.gpu import (
            project_market_selection as project_market_selection_cuda,
        )

        project_market_selection_cuda(
            state,
            tokens,
            quantities,
            phases,
            active,
            layout,
        )
        return
    market = active.bool() & (phases == 1)
    if state.shape[0] == 0:
        return
    consequence = market_consequence(state, tokens, quantities, layout, vocabulary)
    state[:, MARKET_PROJECTION_CONDITIONAL] = torch.where(
        market & consequence.conditional,
        torch.ones_like(state[:, MARKET_PROJECTION_CONDITIONAL]),
        state[:, MARKET_PROJECTION_CONDITIONAL],
    )
    rows = _rows(state)
    commit = consequence.committed.long()
    applied = market & (commit > 0)
    state[:, 9] = torch.where(
        applied,
        state[:, 9] + consequence.cash_delta.round().to(state.dtype),
        state[:, 9],
    )
    item_index = layout.shed + consequence.item
    old_shed = _gather(state, item_index)
    state[rows, item_index] = torch.where(
        applied,
        old_shed + consequence.shed_delta.to(state.dtype),
        old_shed,
    )
    state[:, 8] = torch.where(
        applied,
        state[:, 8] + consequence.shed_delta.to(state.dtype),
        state[:, 8],
    )
    seed = (tokens - vocabulary.seed_first).clamp(0, 4)
    seed_index = layout.seeds + seed
    old_seed = _gather(state, seed_index)
    state[rows, seed_index] = torch.where(
        applied & (consequence.seed_delta > 0),
        old_seed + consequence.seed_delta.to(state.dtype),
        old_seed,
    )
    product = torch.where(
        tokens == vocabulary.product_first + 1,
        torch.full_like(tokens, 8),
        consequence.item,
    ).clamp(0, 8)
    market_index = layout.market_inventory + product
    old_market = _gather(state, market_index)
    state[rows, market_index] = torch.where(
        applied & (consequence.market_delta != 0),
        old_market + consequence.market_delta.to(state.dtype),
        old_market,
    )
    hire = applied & (tokens == vocabulary.hire)
    land = applied & (tokens == vocabulary.buy_land)
    state[:, 10] = state[:, 10] + hire.to(state.dtype)
    state[:, 11] = state[:, 11] + land.to(state.dtype)


def _append_inventory_key(
    state: Tensor,
    order_base: Tensor,
    item: Tensor,
    mask: Tensor,
) -> None:
    slots = torch.arange(ITEMS, device=state.device)
    indices = order_base[:, None] + slots[None]
    order = state.gather(1, indices.long())
    empty = order < 0
    first = empty.long().argmax(dim=1)
    rows = _rows(state)
    state[rows, order_base + first] = torch.where(
        mask & empty.any(dim=1),
        item.to(state.dtype),
        state[rows, order_base + first],
    )


def _remove_inventory_key(
    state: Tensor,
    order_base: Tensor,
    item: Tensor,
    mask: Tensor,
) -> None:
    found = torch.zeros_like(mask)
    rows = _rows(state)
    for slot in range(ITEMS):
        index = order_base + slot
        current = state[rows, index]
        following = (
            state[rows, order_base + slot + 1]
            if slot + 1 < ITEMS
            else torch.full_like(current, -1)
        )
        found = found | (current == item)
        state[rows, index] = torch.where(mask & found, following, current)


def _write_tile_field(
    state: Tensor,
    tile: Tensor,
    offset: int,
    value: Tensor,
    mask: Tensor,
) -> None:
    rows = _rows(state)
    index = tile + offset
    current = state[rows, index]
    state[rows, index] = torch.where(mask, value.to(state.dtype), current)


def _clear_tile(state: Tensor, tile: Tensor, mask: Tensor) -> None:
    zero = torch.zeros(state.shape[0], dtype=state.dtype, device=state.device)
    for offset in range(12):
        value = torch.full_like(zero, -1) if offset == 4 else zero
        _write_tile_field(state, tile, offset, value, mask)


def _reset_tile(
    state: Tensor,
    tile: Tensor,
    structure: Tensor,
    mask: Tensor,
) -> None:
    zero = torch.zeros(state.shape[0], dtype=state.dtype, device=state.device)
    for offset in range(12):
        if offset == 0:
            value = torch.full_like(zero, 4)
        elif offset == 4:
            value = torch.full_like(zero, -1)
        elif offset == 6:
            value = structure
        else:
            value = zero
        _write_tile_field(state, tile, offset, value, mask)


def apply_unit_selection(
    state: Tensor,
    tokens: Tensor,
    quantities: Tensor,
    phases: Tensor,
    active: Tensor,
    layout: EconomicStateLayout,
    vocabulary: ActionVocabulary = CURRENT_ACTIONS,
) -> None:
    """Replay unit-prefix economic effects needed by later market facts."""
    rows = _rows(state)
    unit = active.bool() & (phases == 0)
    unit_index = state[:, 2].long().clamp(0, layout.unit_limit - 1)
    inventory_base = layout.inventories + unit_index * ITEMS
    order_base = layout.inventory_order + unit_index * ITEMS
    x_index = layout.positions + unit_index * 2
    y_index = x_index + 1
    x = _gather(state, x_index).long()
    y = _gather(state, y_index).long()

    north = unit & (tokens == 1)
    south = unit & (tokens == 2)
    east = unit & (tokens == 3)
    west = unit & (tokens == 4)
    state[rows, x_index] = (
        x + east.to(x.dtype) - west.to(x.dtype)
    ).to(state.dtype)
    state[rows, y_index] = (
        y + south.to(y.dtype) - north.to(y.dtype)
    ).to(state.dtype)

    pickup = unit & (tokens >= vocabulary.pickup_first) & (
        tokens < vocabulary.pickup_stop
    )
    pickup_item = (
        (tokens - vocabulary.pickup_first) // vocabulary.pickup_stride
    ).clamp(0, ITEMS - 1)
    pickup_request = torch.where(
        (tokens - vocabulary.pickup_first) % vocabulary.pickup_stride == 0,
        1,
        quantities,
    ).clamp_min(0)
    if vocabulary.pickup_stride == 1:
        pickup_request = quantities.clamp_min(0)
    shed_index = layout.shed + pickup_item
    inventory_index = inventory_base + pickup_item
    old_shed = _gather(state, shed_index)
    old_inventory = _gather(state, inventory_index)
    pickup_count = torch.minimum(pickup_request.to(old_shed.dtype), old_shed.clamp_min(0))
    state[rows, shed_index] = torch.where(pickup, old_shed - pickup_count, old_shed)
    state[rows, inventory_index] = torch.where(
        pickup,
        old_inventory + pickup_count,
        old_inventory,
    )
    state[:, 8] = state[:, 8] - torch.where(
        pickup,
        pickup_count,
        torch.zeros_like(pickup_count),
    )
    _append_inventory_key(state, order_base, pickup_item, pickup & (old_inventory == 0))

    drop = unit & (tokens == vocabulary.drop)
    for slot in range(ITEMS):
        order_index = order_base + slot
        drop_item = _gather(state, order_index).long()
        valid = drop & (drop_item >= 0)
        safe_item = drop_item.clamp(0, ITEMS - 1)
        carried_index = inventory_base + safe_item
        destination_index = layout.shed + safe_item
        carried = _gather(state, carried_index).clamp_min(0)
        room = (state[:, 5] - state[:, 8]).clamp_min(0)
        take = torch.minimum(carried, room)
        destination = _gather(state, destination_index)
        state[rows, destination_index] = torch.where(
            valid,
            destination + take,
            destination,
        )
        state[rows, carried_index] = torch.where(valid, torch.zeros_like(carried), carried)
        state[rows, order_index] = torch.where(
            valid,
            torch.full_like(drop_item, -1),
            drop_item,
        ).to(state.dtype)
        state[:, 8] = state[:, 8] + torch.where(valid, take, torch.zeros_like(take))

    place = unit & (tokens >= vocabulary.place_first) & (
        tokens < vocabulary.place_stop
    )
    place_item = (
        (tokens - vocabulary.place_first) // vocabulary.place_stride
    ).clamp(0, ITEMS - 1)
    place_request = torch.where(
        (tokens - vocabulary.place_first) % vocabulary.place_stride == 0,
        1,
        quantities,
    ).clamp_min(0)
    if vocabulary.place_stride == 1:
        place_request = quantities.clamp_min(0)
    place_inventory_index = inventory_base + place_item
    place_inventory = _gather(state, place_inventory_index).clamp_min(0)
    tile_index = layout.tiles + (y * layout.board_size + x) * layout.tile_fields
    tile_kind = _gather(state, tile_index)
    tile_structure = _gather(state, tile_index + 6)
    tile_animal = _gather(state, tile_index + 7)
    expected_structure = (place_item != 9).to(state.dtype)
    animal_place = (
        place
        & (place_item >= 9)
        & (tile_kind == 4)
        & (tile_animal == 0)
        & (tile_structure == expected_structure)
    )
    room = (state[:, 5] - state[:, 8]).clamp_min(0)
    shed_place = place & ~animal_place
    place_count = torch.minimum(
        torch.minimum(place_request.to(state.dtype), place_inventory),
        room,
    )
    committed = torch.where(
        animal_place,
        torch.minimum(place_inventory, torch.ones_like(place_count)),
        place_count,
    )
    next_inventory = place_inventory - torch.where(place, committed, torch.zeros_like(committed))
    state[rows, place_inventory_index] = torch.where(place, next_inventory, place_inventory)
    place_shed_index = layout.shed + place_item
    old_place_shed = _gather(state, place_shed_index)
    state[rows, place_shed_index] = torch.where(
        shed_place,
        old_place_shed + place_count,
        old_place_shed,
    )
    state[:, 8] = state[:, 8] + torch.where(
        shed_place,
        place_count,
        torch.zeros_like(place_count),
    )
    _remove_inventory_key(state, order_base, place_item, place & (next_inventory == 0))
    _reset_tile(state, tile_index, expected_structure, animal_place)
    state[rows, tile_index + 7] = torch.where(
        animal_place,
        torch.ones_like(tile_animal),
        state[rows, tile_index + 7],
    )
    state[rows, tile_index + 8] = torch.where(
        animal_place,
        place_item - 9,
        state[rows, tile_index + 8],
    ).to(state.dtype)

    plant = unit & (tokens >= vocabulary.plant_first) & (
        tokens < vocabulary.plant_first + 5
    )
    crop = (tokens - vocabulary.plant_first).clamp(0, 4)
    seed_index = layout.seeds + crop
    old_seed = _gather(state, seed_index)
    state[rows, seed_index] = torch.where(plant, old_seed - 1, old_seed)
    state[rows, tile_index] = torch.where(
        plant,
        torch.full_like(tile_kind, 3),
        state[rows, tile_index],
    )
    state[rows, tile_index + 1] = torch.where(
        plant,
        crop,
        state[rows, tile_index + 1],
    ).to(state.dtype)
    _write_tile_field(state, tile_index, 2, state[:, 0], plant)
    _write_tile_field(
        state,
        tile_index,
        3,
        torch.zeros_like(state[:, 0]),
        plant,
    )
    _write_tile_field(
        state,
        tile_index,
        4,
        torch.full_like(state[:, 0], -1),
        plant,
    )
    ongoing = (crop == 2) | (crop == 3)
    _write_tile_field(state, tile_index, 5, (~ongoing).to(state.dtype), plant)
    for offset in range(6, 12):
        _write_tile_field(
            state,
            tile_index,
            offset,
            torch.zeros_like(state[:, 0]),
            plant,
        )

    water = unit & (tokens == vocabulary.water)
    water_crop = _gather(state, tile_index + 1).long()
    planted_day = _gather(state, tile_index + 2).long()
    fertilized_until = _gather(state, tile_index + 4).long()
    old_water_yield = _gather(state, tile_index + 5).long()
    max_yield_day = torch.where(
        water_crop == 0,
        torch.full_like(water_crop, 4),
        torch.where(
            water_crop == 1,
            torch.full_like(water_crop, 3),
            torch.where(
                water_crop == 2,
                torch.full_like(water_crop, 8),
                torch.where(
                    water_crop == 3,
                    torch.full_like(water_crop, 10),
                    torch.full_like(water_crop, 12),
                ),
            ),
        ),
    )
    max_yield = torch.where(
        water_crop == 0,
        torch.full_like(water_crop, 6),
        torch.where(
            water_crop == 1,
            torch.full_like(water_crop, 4),
            torch.where(
                water_crop == 4,
                torch.full_like(water_crop, 6),
                torch.full_like(water_crop, 4),
            ),
        ),
    )
    age = state[:, 0].long() - planted_day
    window_start = (max_yield_day + 1) // 2
    water_bonus = torch.where(
        fertilized_until >= state[:, 0].long(),
        torch.full_like(old_water_yield, 2),
        torch.ones_like(old_water_yield),
    )
    increase = (
        ~((water_crop == 2) | (water_crop == 3))
        & (age >= window_start)
        & (age <= max_yield_day)
    )
    next_water_yield = torch.minimum(
        max_yield,
        old_water_yield + torch.where(increase, water_bonus, torch.zeros_like(water_bonus)),
    )
    _write_tile_field(state, tile_index, 3, torch.ones_like(state[:, 0]), water)
    _write_tile_field(state, tile_index, 5, next_water_yield, water)

    harvest = unit & (tokens == vocabulary.harvest)
    harvest_kind = _gather(state, tile_index)
    harvest_crop = _gather(state, tile_index + 1).long()
    harvest_animal = _gather(state, tile_index + 8).long()
    harvest_yield = _gather(state, tile_index + 5).clamp_min(0)
    harvest_item = torch.where(
        harvest_kind == 3,
        harvest_crop,
        torch.where(harvest_animal == 0, 5, torch.where(harvest_animal == 1, 6, 7)),
    ).clamp(0, ITEMS - 1)
    harvest_inventory_index = inventory_base + harvest_item
    old_harvest_inventory = _gather(state, harvest_inventory_index)
    state[rows, harvest_inventory_index] = torch.where(
        harvest,
        old_harvest_inventory + harvest_yield,
        old_harvest_inventory,
    )
    _append_inventory_key(
        state,
        order_base,
        harvest_item,
        harvest & (old_harvest_inventory == 0),
    )
    state[rows, tile_index + 5] = torch.where(
        harvest,
        torch.zeros_like(harvest_yield),
        harvest_yield,
    )
    finite_crop = (harvest_kind == 3) & ~(
        (harvest_crop == 2) | (harvest_crop == 3)
    )
    _clear_tile(state, tile_index, harvest & finite_crop)

    consume_item = torch.where(
        tokens == vocabulary.feed,
        torch.zeros_like(tokens),
        torch.full_like(tokens, 8),
    )
    consume = unit & (
        (tokens == vocabulary.fertilize) | (tokens == vocabulary.feed)
    )
    consume_index = inventory_base + consume_item
    old_consume = _gather(state, consume_index)
    state[rows, consume_index] = torch.where(consume, old_consume - 1, old_consume)
    _remove_inventory_key(state, order_base, consume_item, consume & (old_consume == 1))

    fertilize = unit & (tokens == vocabulary.fertilize)
    old_fertilized = _gather(state, tile_index + 4)
    _write_tile_field(
        state,
        tile_index,
        4,
        torch.maximum(old_fertilized, state[:, 0] + 2),
        fertilize,
    )

    _clear_tile(state, tile_index, unit & (tokens == vocabulary.dig))
    _reset_tile(
        state,
        tile_index,
        torch.zeros_like(state[:, 0]),
        unit & (tokens == vocabulary.build_coop),
    )
    _reset_tile(
        state,
        tile_index,
        torch.ones_like(state[:, 0]),
        unit & (tokens == vocabulary.build_pasture),
    )
    _write_tile_field(
        state,
        tile_index,
        9,
        torch.ones_like(state[:, 0]),
        unit & (tokens == vocabulary.feed),
    )

    collect = unit & (tokens == vocabulary.collect_fertilizer)
    fertilizer_index = inventory_base + 8
    old_fertilizer = _gather(state, fertilizer_index)
    state[rows, fertilizer_index] = torch.where(
        collect,
        old_fertilizer + 1,
        old_fertilizer,
    )
    _append_inventory_key(
        state,
        order_base,
        torch.full_like(tokens, 8),
        collect & (old_fertilizer == 0),
    )
    _write_tile_field(
        state,
        tile_index,
        11,
        torch.zeros_like(state[:, 0]),
        collect,
    )
    _write_tile_field(
        state,
        tile_index,
        10,
        torch.ones_like(state[:, 0]),
        unit & (tokens == vocabulary.care),
    )

    next_unit = state[:, 2] + unit.to(state.dtype)
    state[:, 2] = next_unit
    state[:, 4] = torch.where(
        unit & (next_unit >= state[:, 1]),
        torch.ones_like(state[:, 4]),
        state[:, 4],
    )


def apply_selection(
    state: Tensor,
    tokens: Tensor,
    quantities: Tensor,
    active: Tensor,
    layout: EconomicStateLayout,
    vocabulary: ActionVocabulary = CURRENT_ACTIONS,
) -> None:
    """Replay one selected decision for teacher-forced feature generation."""
    if state.device.type == "cuda":
        if vocabulary != CURRENT_ACTIONS:
            raise ValueError("legacy economic replay requires CPU tensors")
        from kagg_revue.policy.cuda.session import (
            GpuPolicyStateLayout,
            select_policy_actions,
        )

        gpu_layout = GpuPolicyStateLayout(
            board_size=layout.board_size,
            unit_limit=layout.unit_limit,
            header_fields=layout.header_fields,
            positions=layout.positions,
            inventories=layout.inventories,
            inventory_order=layout.inventory_order,
            shed=layout.shed,
            seeds=layout.seeds,
            market_inventory=layout.market_inventory,
            market_prices=layout.market_prices,
            market_base_milli=layout.market_base_milli,
            market_i0=layout.market_i0,
            market_t_milli=layout.market_t_milli,
            market_below_function=layout.market_below_function,
            market_below_target_milli=layout.market_below_target_milli,
            market_above_function=layout.market_above_function,
            market_above_target_milli=layout.market_above_target_milli,
            seed_costs=layout.seed_costs,
            animal_costs=layout.animal_costs,
            land_costs=layout.land_costs,
            tiles=layout.tiles,
            tile_fields=layout.tile_fields,
            width=layout.width,
        )
        phases = state[:, 4].long().clone()
        selected = active.bool().contiguous()
        select_policy_actions(
            state,
            tokens.long().contiguous(),
            quantities.long().contiguous(),
            gpu_layout,
            selected,
        )
        project_market_selection(
            state,
            tokens,
            quantities,
            phases,
            selected,
            layout,
        )
        return
    phases = state[:, 4].long().clone()
    apply_unit_selection(
        state, tokens, quantities, phases, active, layout, vocabulary
    )
    project_market_selection(
        state, tokens, quantities, phases, active, layout, vocabulary
    )
    market = active.bool() & (phases == 1)
    hire = market & (tokens == vocabulary.hire) & (
        state[:, 1] < layout.unit_limit
    )
    state[:, 1] = state[:, 1] + hire.to(state.dtype)
    stop = market & (tokens == vocabulary.market_stop)
    non_stop = market & ~stop
    next_slot = state[:, 3] + non_stop.to(state.dtype)
    state[:, 3] = next_slot
    state[:, 4] = torch.where(
        stop | (non_stop & (next_slot >= state[:, 6])),
        torch.full_like(state[:, 4], 2),
        state[:, 4],
    )


__all__ = [
    "MarketConsequence",
    "apply_selection",
    "apply_unit_selection",
    "market_consequence",
    "project_market_selection",
]
