"""Triton kernels for policy-session legality and prefix transitions."""

# mypy: disable-error-code="no-untyped-def,untyped-decorator"

from __future__ import annotations

import triton  # type: ignore[import-untyped]
import triton.language as tl  # type: ignore[import-untyped]


@triton.jit
def _compile_legal_kernel(
    state,
    legal,
    phases,
    decisions,
    STATE_WIDTH: tl.constexpr,
    POSITIONS: tl.constexpr,
    INVENTORIES: tl.constexpr,
    SHED: tl.constexpr,
    SEEDS: tl.constexpr,
    TILES: tl.constexpr,
    TILE_FIELDS: tl.constexpr,
    BOARD_SIZE: tl.constexpr,
    UNIT_LIMIT: tl.constexpr,
    ACTION_TOKENS: tl.constexpr,
    BLOCK: tl.constexpr,
):
    row = tl.program_id(0)
    token = tl.arange(0, BLOCK)
    base = state + row * STATE_WIDTH
    phase = tl.load(base + 4)
    unit_index = tl.load(base + 2)
    unit_count = tl.load(base + 1)
    active = phase != 2
    tl.store(phases + row, phase)
    tl.store(decisions + row, active)

    x = tl.load(base + POSITIONS + unit_index * 2, mask=phase == 0, other=0)
    y = tl.load(base + POSITIONS + unit_index * 2 + 1, mask=phase == 0, other=0)
    tile = base + TILES + (y * BOARD_SIZE + x) * TILE_FIELDS
    tile_kind = tl.load(tile, mask=phase == 0, other=0)
    crop = tl.load(tile + 1, mask=phase == 0, other=0)
    planted_day = tl.load(tile + 2, mask=phase == 0, other=0)
    watered = tl.load(tile + 3, mask=phase == 0, other=0)
    tile_yield = tl.load(tile + 5, mask=phase == 0, other=0)
    structure = tl.load(tile + 6, mask=phase == 0, other=0)
    has_animal = tl.load(tile + 7, mask=phase == 0, other=0)
    fed = tl.load(tile + 9, mask=phase == 0, other=0)
    cared = tl.load(tile + 10, mask=phase == 0, other=0)
    fertilizer_available = tl.load(tile + 11, mask=phase == 0, other=0)
    day = tl.load(base)
    capacity = tl.load(base + 5)
    shed_total = tl.load(base + 8)

    half = BOARD_SIZE // 2
    adjacent = ((x == half - 1) | (x == half)) & ((y == half - 1) | (y == half))
    item = tl.where(
        (token >= 5) & (token < 17),
        token - 5,
        token - 18,
    )
    valid_item = (item >= 0) & (item < 12)
    inventory = tl.load(
        base + INVENTORIES + unit_index * 12 + item,
        mask=(phase == 0) & valid_item,
        other=0,
    )
    shed_count = tl.load(
        base + SHED + item,
        mask=(phase == 0) & valid_item,
        other=0,
    )

    unit_legal = token == 0
    unit_legal |= (token == 1) & (y > 0)
    unit_legal |= (token == 2) & (y + 1 < BOARD_SIZE)
    unit_legal |= (token == 3) & (x + 1 < BOARD_SIZE)
    unit_legal |= (token == 4) & (x > 0)
    unit_legal |= (token >= 5) & (token < 17) & adjacent & (shed_count > 0)
    unit_legal |= (token == 17) & adjacent

    is_place = (token >= 18) & (token < 30)
    animal_item = item >= 9
    expected_structure = tl.where(item == 9, 0, 1)
    animal_place = (
        animal_item & (tile_kind == 4) & (has_animal == 0) & (structure == expected_structure)
    )
    shed_place = adjacent & (capacity > shed_total)
    unit_legal |= is_place & (inventory > 0) & (animal_place | shed_place)

    plant_crop = token - 30
    valid_crop = (plant_crop >= 0) & (plant_crop < 5)
    seed_count = tl.load(
        base + SEEDS + plant_crop,
        mask=(phase == 0) & valid_crop,
        other=0,
    )
    unit_legal |= valid_crop & (tile_kind == 0) & (seed_count > 0)
    unit_legal |= (token == 35) & (tile_kind == 3) & (watered == 0)
    first_yield = tl.where(
        crop == 0,
        2,
        tl.where(crop == 1, 2, tl.where(crop == 2, 8, tl.where(crop == 3, 10, 10))),
    )
    harvest_plant = (tile_kind == 3) & (tile_yield > 0) & (day - planted_day >= first_yield)
    harvest_animal = (tile_kind == 4) & (has_animal != 0) & (tile_yield > 0)
    unit_legal |= (token == 36) & (harvest_plant | harvest_animal)
    fertilizer_count = tl.load(
        base + INVENTORIES + unit_index * 12 + 8,
        mask=phase == 0,
        other=0,
    )
    wheat_count = tl.load(
        base + INVENTORIES + unit_index * 12,
        mask=phase == 0,
        other=0,
    )
    unit_legal |= (token == 37) & (tile_kind == 3) & (fertilizer_count > 0)
    unit_legal |= (
        (token == 38)
        & (tile_kind != 0)
        & (tile_kind != 1)
        & ~((tile_kind == 4) & (has_animal != 0))
    )
    unit_legal |= ((token == 39) | (token == 40)) & (tile_kind == 0)
    unit_legal |= (
        (token == 41) & (tile_kind == 4) & (has_animal != 0) & (fed == 0) & (wheat_count > 0)
    )
    unit_legal |= (token == 42) & (tile_kind == 4) & (has_animal != 0) & (fertilizer_available != 0)
    unit_legal |= (token == 43) & (tile_kind == 4) & (has_animal != 0) & (cared == 0)
    unit_legal &= token < 44
    market_legal = (token >= 44) & (token < ACTION_TOKENS)
    market_legal &= (token != 65) | (unit_count < UNIT_LIMIT)
    result = ((phase == 0) & (unit_index < unit_count) & unit_legal) | ((phase == 1) & market_legal)
    tl.store(legal + row * ACTION_TOKENS + token, result, mask=token < ACTION_TOKENS)


@triton.jit
def _reset_tile(tile, structure, mask):
    tl.store(tile, 4, mask=mask)
    tl.store(tile + 1, 0, mask=mask)
    tl.store(tile + 2, 0, mask=mask)
    tl.store(tile + 3, 0, mask=mask)
    tl.store(tile + 4, -1, mask=mask)
    tl.store(tile + 5, 0, mask=mask)
    tl.store(tile + 6, structure, mask=mask)
    tl.store(tile + 7, 0, mask=mask)
    tl.store(tile + 8, 0, mask=mask)
    tl.store(tile + 9, 0, mask=mask)
    tl.store(tile + 10, 0, mask=mask)
    tl.store(tile + 11, 0, mask=mask)


@triton.jit
def _clear_tile(tile, mask):
    tl.store(tile, 0, mask=mask)
    tl.store(tile + 1, 0, mask=mask)
    tl.store(tile + 2, 0, mask=mask)
    tl.store(tile + 3, 0, mask=mask)
    tl.store(tile + 4, -1, mask=mask)
    tl.store(tile + 5, 0, mask=mask)
    tl.store(tile + 6, 0, mask=mask)
    tl.store(tile + 7, 0, mask=mask)
    tl.store(tile + 8, 0, mask=mask)
    tl.store(tile + 9, 0, mask=mask)
    tl.store(tile + 10, 0, mask=mask)
    tl.store(tile + 11, 0, mask=mask)


@triton.jit
def _append_order(order, item, mask):
    inserted = False
    for slot in tl.static_range(0, 12):
        current = tl.load(order + slot)
        insert = mask & ~inserted & (current < 0)
        tl.store(order + slot, item, mask=insert)
        inserted |= insert


@triton.jit
def _remove_order(order, item, mask):
    found = False
    for slot in tl.static_range(0, 12):
        current = tl.load(order + slot)
        following = tl.load(order + slot + 1, mask=slot + 1 < 12, other=-1)
        found |= current == item
        tl.store(order + slot, following, mask=mask & found)


@triton.jit
def _select_kernel(
    state,
    tokens,
    quantities,
    active,
    STATE_WIDTH: tl.constexpr,
    POSITIONS: tl.constexpr,
    INVENTORIES: tl.constexpr,
    INVENTORY_ORDER: tl.constexpr,
    SHED: tl.constexpr,
    SEEDS: tl.constexpr,
    TILES: tl.constexpr,
    TILE_FIELDS: tl.constexpr,
    BOARD_SIZE: tl.constexpr,
    UNIT_LIMIT: tl.constexpr,
):
    row = tl.program_id(0)
    base = state + row * STATE_WIDTH
    token = tl.load(tokens + row)
    quantity = tl.load(quantities + row)
    selected = tl.load(active + row) != 0
    phase = tl.load(base + 4)
    unit_index = tl.load(base + 2)
    unit_count = tl.load(base + 1)
    is_unit = selected & (phase == 0)
    x_pointer = base + POSITIONS + unit_index * 2
    y_pointer = x_pointer + 1
    x = tl.load(x_pointer, mask=is_unit, other=0)
    y = tl.load(y_pointer, mask=is_unit, other=0)
    tile = base + TILES + (y * BOARD_SIZE + x) * TILE_FIELDS
    inventory = base + INVENTORIES + unit_index * 12
    order = base + INVENTORY_ORDER + unit_index * 12
    day = tl.load(base)
    capacity = tl.load(base + 5)
    shed_total = tl.load(base + 8)

    north = is_unit & (token == 1)
    south = is_unit & (token == 2)
    east = is_unit & (token == 3)
    west = is_unit & (token == 4)
    tl.store(x_pointer, x + east.to(tl.int32) - west.to(tl.int32), mask=east | west)
    tl.store(y_pointer, y + south.to(tl.int32) - north.to(tl.int32), mask=north | south)

    is_pickup = is_unit & (token >= 5) & (token < 17)
    pickup_item = token - 5
    pickup_requested = quantity
    pickup_shed = tl.load(base + SHED + pickup_item, mask=is_pickup, other=0)
    pickup_count = tl.minimum(pickup_requested, pickup_shed)
    pickup_inventory = tl.load(inventory + pickup_item, mask=is_pickup, other=0)
    tl.store(base + SHED + pickup_item, pickup_shed - pickup_count, mask=is_pickup)
    tl.store(
        inventory + pickup_item,
        pickup_inventory + pickup_count,
        mask=is_pickup,
    )
    _append_order(order, pickup_item, is_pickup & (pickup_inventory == 0))
    shed_total -= tl.where(is_pickup, pickup_count, 0)

    is_drop = is_unit & (token == 17)
    for slot in tl.static_range(0, 12):
        drop_item = tl.load(order + slot)
        valid = is_drop & (drop_item >= 0)
        held = tl.load(inventory + drop_item, mask=valid, other=0)
        room = tl.maximum(0, capacity - shed_total)
        take = tl.minimum(held, room)
        old_shed = tl.load(base + SHED + drop_item, mask=valid, other=0)
        tl.store(base + SHED + drop_item, old_shed + take, mask=valid)
        tl.store(inventory + drop_item, 0, mask=valid)
        tl.store(order + slot, -1, mask=is_drop)
        shed_total += tl.where(valid, take, 0)

    is_place = is_unit & (token >= 18) & (token < 30)
    place_item = token - 18
    place_requested = quantity
    place_inventory = tl.load(inventory + place_item, mask=is_place, other=0)
    tile_kind = tl.load(tile, mask=is_unit, other=0)
    tile_structure = tl.load(tile + 6, mask=is_unit, other=0)
    tile_animal = tl.load(tile + 7, mask=is_unit, other=0)
    expected_structure = tl.where(place_item == 9, 0, 1)
    place_animal = (
        is_place
        & (place_item >= 9)
        & (tile_kind == 4)
        & (tile_animal == 0)
        & (tile_structure == expected_structure)
    )
    place_shed = is_place & ~place_animal
    place_room = tl.maximum(0, capacity - shed_total)
    place_count = tl.minimum(tl.minimum(place_requested, place_inventory), place_room)
    placed_inventory = tl.where(place_animal, place_inventory - 1, place_inventory - place_count)
    tl.store(inventory + place_item, placed_inventory, mask=is_place)
    _remove_order(order, place_item, is_place & (placed_inventory == 0))
    old_place_shed = tl.load(base + SHED + place_item, mask=place_shed, other=0)
    tl.store(
        base + SHED + place_item,
        old_place_shed + place_count,
        mask=place_shed,
    )
    shed_total += tl.where(place_shed, place_count, 0)
    _reset_tile(tile, expected_structure, place_animal)
    tl.store(tile + 7, 1, mask=place_animal)
    tl.store(tile + 8, place_item - 9, mask=place_animal)

    is_plant = is_unit & (token >= 30) & (token < 35)
    plant_crop = token - 30
    old_seeds = tl.load(base + SEEDS + plant_crop, mask=is_plant, other=0)
    tl.store(base + SEEDS + plant_crop, old_seeds - 1, mask=is_plant)
    tl.store(tile, 3, mask=is_plant)
    tl.store(tile + 1, plant_crop, mask=is_plant)
    tl.store(tile + 2, day, mask=is_plant)
    tl.store(tile + 3, 0, mask=is_plant)
    tl.store(tile + 4, -1, mask=is_plant)
    ongoing = (plant_crop == 2) | (plant_crop == 3)
    tl.store(tile + 5, tl.where(ongoing, 0, 1), mask=is_plant)
    tl.store(tile + 6, 0, mask=is_plant)
    tl.store(tile + 7, 0, mask=is_plant)
    tl.store(tile + 8, 0, mask=is_plant)
    tl.store(tile + 9, 0, mask=is_plant)
    tl.store(tile + 10, 0, mask=is_plant)
    tl.store(tile + 11, 0, mask=is_plant)

    is_water = is_unit & (token == 35)
    water_crop = tl.load(tile + 1, mask=is_water, other=0)
    planted_day = tl.load(tile + 2, mask=is_water, other=0)
    fertilized_until = tl.load(tile + 4, mask=is_water, other=-1)
    old_yield = tl.load(tile + 5, mask=is_water, other=0)
    max_yield_day = tl.where(
        water_crop == 0,
        4,
        tl.where(
            water_crop == 1,
            3,
            tl.where(water_crop == 2, 8, tl.where(water_crop == 3, 10, 12)),
        ),
    )
    max_yield = tl.where(
        water_crop == 0,
        6,
        tl.where(water_crop == 1, 4, tl.where(water_crop == 4, 6, 4)),
    )
    age = day - planted_day
    window_start = (max_yield_day + 1) // 2
    water_bonus = tl.where(fertilized_until >= day, 2, 1)
    increase = (
        (~((water_crop == 2) | (water_crop == 3))) & (age >= window_start) & (age <= max_yield_day)
    )
    next_yield = tl.minimum(max_yield, old_yield + tl.where(increase, water_bonus, 0))
    tl.store(tile + 3, 1, mask=is_water)
    tl.store(tile + 5, next_yield, mask=is_water)

    is_harvest = is_unit & (token == 36)
    harvest_kind = tl.load(tile, mask=is_harvest, other=0)
    harvest_crop = tl.load(tile + 1, mask=is_harvest, other=0)
    harvest_animal = tl.load(tile + 8, mask=is_harvest, other=0)
    harvest_yield = tl.load(tile + 5, mask=is_harvest, other=0)
    harvest_item = tl.where(
        harvest_kind == 3,
        harvest_crop,
        tl.where(harvest_animal == 0, 5, tl.where(harvest_animal == 1, 6, 7)),
    )
    harvest_inventory = tl.load(inventory + harvest_item, mask=is_harvest, other=0)
    tl.store(
        inventory + harvest_item,
        harvest_inventory + harvest_yield,
        mask=is_harvest,
    )
    _append_order(order, harvest_item, is_harvest & (harvest_inventory == 0))
    tl.store(tile + 5, 0, mask=is_harvest)
    finite_crop = (harvest_kind == 3) & ~((harvest_crop == 2) | (harvest_crop == 3))
    _clear_tile(tile, is_harvest & finite_crop)

    is_fertilize = is_unit & (token == 37)
    fertilizer_inventory = tl.load(inventory + 8, mask=is_fertilize, other=0)
    tl.store(inventory + 8, fertilizer_inventory - 1, mask=is_fertilize)
    _remove_order(order, 8, is_fertilize & (fertilizer_inventory == 1))
    old_fertilized = tl.load(tile + 4, mask=is_fertilize, other=-1)
    tl.store(tile + 4, tl.maximum(old_fertilized, day + 2), mask=is_fertilize)

    is_dig = is_unit & (token == 38)
    _clear_tile(tile, is_dig)
    is_coop = is_unit & (token == 39)
    is_pasture = is_unit & (token == 40)
    _reset_tile(tile, 0, is_coop)
    _reset_tile(tile, 1, is_pasture)

    is_feed = is_unit & (token == 41)
    wheat_inventory = tl.load(inventory, mask=is_feed, other=0)
    tl.store(inventory, wheat_inventory - 1, mask=is_feed)
    _remove_order(order, 0, is_feed & (wheat_inventory == 1))
    tl.store(tile + 9, 1, mask=is_feed)

    is_collect = is_unit & (token == 42)
    collected_inventory = tl.load(inventory + 8, mask=is_collect, other=0)
    tl.store(inventory + 8, collected_inventory + 1, mask=is_collect)
    _append_order(order, 8, is_collect & (collected_inventory == 0))
    tl.store(tile + 11, 0, mask=is_collect)
    tl.store(tile + 10, 1, mask=is_unit & (token == 43))

    tl.store(base + 8, shed_total, mask=is_unit)
    next_unit = unit_index + 1
    tl.store(base + 2, next_unit, mask=is_unit)
    tl.store(base + 4, 1, mask=is_unit & (next_unit >= unit_count))

    is_market = selected & (phase == 1)
    is_stop = is_market & (token == 44)
    is_hire = is_market & (token == 65) & (unit_count < UNIT_LIMIT)
    tl.store(base + 1, unit_count + 1, mask=is_hire)
    next_slot = tl.load(base + 3) + 1
    max_orders = tl.load(base + 6)
    tl.store(base + 3, next_slot, mask=is_market & ~is_stop)
    tl.store(base + 4, 2, mask=is_stop | (is_market & (next_slot >= max_orders)))


__all__ = ["_compile_legal_kernel", "_select_kernel"]
