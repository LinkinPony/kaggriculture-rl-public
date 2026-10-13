"""Fused CUDA construction of the complete unit-task candidate surface."""

# mypy: disable-error-code="no-untyped-def,untyped-decorator"

from __future__ import annotations

import torch
import triton  # type: ignore[import-untyped]
import triton.language as tl  # type: ignore[import-untyped]
from torch import Tensor

from kagg_revue.policy.economics.layout import EconomicStateLayout
from kagg_revue.policy.tasks.grammar import TaskCatalog

_FEATURES = tl.constexpr(18)


@triton.jit
def _candidate_kernel(
    rows,
    state,
    units,
    simulated_x,
    simulated_y,
    available_at,
    target_counts,
    resource_counts,
    operations,
    arguments,
    targets,
    operation_turns,
    output_features,
    output_mask,
    output_arrivals,
    STATE_WIDTH: tl.constexpr,
    UNIT_LIMIT: tl.constexpr,
    BOARD_SIZE: tl.constexpr,
    CANDIDATES: tl.constexpr,
    POSITIONS: tl.constexpr,
    INVENTORIES: tl.constexpr,
    SHED: tl.constexpr,
    SEEDS: tl.constexpr,
    TILES: tl.constexpr,
    TILE_FIELDS: tl.constexpr,
    RESOURCE_WIDTH: tl.constexpr,
    TURNS: tl.constexpr,
    BLOCK: tl.constexpr,
):
    local_row = tl.program_id(0)
    row = tl.load(rows + local_row)
    block = tl.program_id(1)
    candidate = block * BLOCK + tl.arange(0, BLOCK)
    valid = candidate < CANDIDATES
    operation = tl.load(operations + candidate, mask=valid, other=0)
    argument = tl.load(arguments + candidate, mask=valid, other=-1)
    target_x = tl.load(targets + candidate * 2, mask=valid, other=-1)
    target_y = tl.load(targets + candidate * 2 + 1, mask=valid, other=-1)
    official = tl.load(operation_turns + candidate, mask=valid, other=0)
    unit = tl.load(units + row)
    x = tl.load(simulated_x + row)
    y = tl.load(simulated_y + row)
    available = tl.load(available_at + row)
    targeted = target_x >= 0
    distance = tl.where(
        targeted, tl.abs(x - target_x) + tl.abs(y - target_y), 0
    )
    is_end = operation == 0
    is_wait = operation == 2
    is_position = operation == 1
    arrival = tl.where(is_end | is_wait, available, available + distance)
    completion = arrival + official
    completion = tl.where(is_wait, available + 1, completion)
    completion = tl.where(is_end, available, completion)
    no_progress = is_position & (distance == 0)
    out_of_time = ~is_end & ~no_progress & (completion > TURNS)
    normal_feasible = ~is_end & ~no_progress & ~out_of_time
    feasible = is_end | normal_feasible

    state_base = state + row * STATE_WIDTH
    tile_index = tl.maximum(target_y, 0) * BOARD_SIZE + tl.maximum(target_x, 0)
    tile = state_base + TILES + tile_index * TILE_FIELDS
    tile_kind = tl.load(tile, mask=valid, other=0)
    tile_crop = tl.load(tile + 1, mask=valid, other=0)
    tile_planted_day = tl.load(tile + 2, mask=valid, other=0)
    tile_watered = tl.load(tile + 3, mask=valid, other=0)
    tile_yield = tl.load(tile + 5, mask=valid, other=0)
    tile_structure = tl.load(tile + 6, mask=valid, other=0)
    tile_has_animal = tl.load(tile + 7, mask=valid, other=0)
    tile_fed = tl.load(tile + 9, mask=valid, other=0)
    tile_cared = tl.load(tile + 10, mask=valid, other=0)
    tile_fertilizer = tl.load(tile + 11, mask=valid, other=0)
    safe_argument = tl.maximum(0, tl.minimum(argument, 11))
    shed = tl.load(state_base + SHED + safe_argument)
    carried = tl.load(state_base + INVENTORIES + unit * 12 + safe_argument)
    fertilizer = tl.load(state_base + INVENTORIES + unit * 12 + 8)
    wheat = tl.load(state_base + INVENTORIES + unit * 12)
    seed = tl.load(state_base + SEEDS + tl.maximum(0, tl.minimum(argument, 4)))
    capacity = tl.load(state_base + 5)
    shed_total = tl.load(state_base + 8)
    room = tl.maximum(capacity - shed_total, 0)
    day = tl.load(state_base)
    half = BOARD_SIZE // 2
    adjacent = ((target_x == half - 1) | (target_x == half)) & (
        (target_y == half - 1) | (target_y == half)
    )
    animal_place = (
        (argument >= 9)
        & (argument < 12)
        & (tile_kind == 4)
        & (tile_has_animal == 0)
        & (tile_structure == (argument != 9))
    )
    unlocked = targeted & (tile_kind != 1)
    first_yield = tl.where(tile_crop <= 1, 2, tl.where(tile_crop == 2, 8, 10))
    currently_legal = is_end | is_wait | is_position
    currently_legal |= (
        (operation == 3)
        & adjacent
        & (argument >= 0)
        & (argument < 12)
        & (shed > 0)
    )
    currently_legal |= (operation == 4) & adjacent
    currently_legal |= (
        (operation == 5)
        & (argument >= 0)
        & (argument < 12)
        & (carried > 0)
        & (animal_place | (adjacent & (room > 0)))
    )
    currently_legal |= (
        (operation == 6)
        & unlocked
        & (argument >= 0)
        & (argument < 5)
        & (tile_kind == 0)
        & (seed > 0)
    )
    currently_legal |= (
        (operation == 7) & unlocked & (tile_kind == 3) & (tile_watered == 0)
    )
    currently_legal |= (
        (operation == 8)
        & unlocked
        & (tile_yield > 0)
        & (
            ((tile_kind == 3) & (day - tile_planted_day >= first_yield))
            | ((tile_kind == 4) & (tile_has_animal != 0))
        )
    )
    currently_legal |= (
        (operation == 9) & unlocked & (tile_kind == 3) & (fertilizer > 0)
    )
    currently_legal |= (
        (operation == 10)
        & unlocked
        & (tile_kind != 0)
        & ~((tile_kind == 4) & (tile_has_animal != 0))
    )
    currently_legal |= (
        ((operation == 11) | (operation == 12))
        & unlocked
        & (tile_kind == 0)
    )
    currently_legal |= (
        (operation == 13)
        & unlocked
        & (tile_kind == 4)
        & (tile_has_animal != 0)
        & (tile_fed == 0)
        & (wheat > 0)
    )
    currently_legal |= (
        (operation == 14)
        & unlocked
        & (tile_kind == 4)
        & (tile_has_animal != 0)
        & (tile_fertilizer != 0)
    )
    currently_legal |= (
        (operation == 15)
        & unlocked
        & (tile_kind == 4)
        & (tile_has_animal != 0)
        & (tile_cared == 0)
    )

    target_base = target_counts + row * BOARD_SIZE * BOARD_SIZE
    target_conflict = tl.load(target_base + tile_index, mask=valid, other=0)
    target_conflict = tl.where(targeted, target_conflict, 0)
    resource = tl.full((BLOCK,), -1, tl.int64)
    resource = tl.where(operation == 6, 100 + argument, resource)
    resource = tl.where(operation == 3, 200 + argument, resource)
    resource = tl.where(operation == 5, 300 + unit * 12 + argument, resource)
    resource = tl.where(operation == 9, 300 + unit * 12 + 8, resource)
    resource = tl.where(operation == 13, 300 + unit * 12, resource)
    safe_resource = tl.maximum(0, tl.minimum(resource, RESOURCE_WIDTH - 1))
    resource_base = resource_counts + row * RESOURCE_WIDTH
    resource_conflict = tl.load(
        resource_base + safe_resource, mask=valid, other=0
    )
    resource_conflict = tl.where(
        resource >= 0,
        resource_conflict,
        0,
    )
    denominator = float(TURNS)
    unit_denominator = float(max(1, UNIT_LIMIT - 1))
    values = (
        1.0,
        distance.to(tl.float32) / denominator,
        arrival.to(tl.float32) / denominator,
        completion.to(tl.float32) / denominator,
        tl.maximum(TURNS - completion, 0).to(tl.float32) / denominator,
        is_wait.to(tl.float32) / denominator,
        feasible.to(tl.float32),
        currently_legal.to(tl.float32),
        target_conflict.to(tl.float32) / unit_denominator,
        resource_conflict.to(tl.float32) / unit_denominator,
        normal_feasible.to(tl.float32),
        is_end.to(tl.float32),
        out_of_time.to(tl.float32),
        no_progress.to(tl.float32),
        0.0,
        tl.where(targeted, target_x.to(tl.float32) / (BOARD_SIZE - 1), 0.0),
        tl.where(targeted, target_y.to(tl.float32) / (BOARD_SIZE - 1), 0.0),
        official.to(tl.float32),
    )
    feature_base = (
        output_features + (local_row * CANDIDATES + candidate) * _FEATURES
    )
    for feature in tl.static_range(0, _FEATURES):
        tl.store(feature_base + feature, values[feature], mask=valid)
    tl.store(
        output_mask + local_row * CANDIDATES + candidate,
        feasible,
        mask=valid,
    )
    tl.store(
        output_arrivals + local_row * CANDIDATES + candidate,
        arrival,
        mask=valid,
    )


def candidate_surface(
    rows: Tensor,
    economic_state: Tensor,
    units: Tensor,
    x: Tensor,
    y: Tensor,
    available: Tensor,
    target_counts: Tensor,
    resource_counts: Tensor,
    catalog: TaskCatalog,
    layout: EconomicStateLayout,
    turns: int,
) -> tuple[Tensor, Tensor, Tensor]:
    """Build features, feasibility mask, and arrivals with one GPU launch."""
    batch = rows.numel()
    state_batch = economic_state.shape[0]
    vectors = (units, x, y, available)
    if economic_state.device.type != "cuda" or not economic_state.is_contiguous():
        raise ValueError("unit-task candidate kernel requires contiguous CUDA state")
    if rows.shape != (batch,) or not rows.is_contiguous():
        raise ValueError("unit-task candidate rows must be a contiguous vector")
    if any(
        value.shape != (state_batch,) or not value.is_contiguous()
        for value in vectors
    ):
        raise ValueError("unit-task candidate cursors must be contiguous vectors")
    if target_counts.shape != (
        state_batch,
        layout.board_size * layout.board_size,
    ):
        raise ValueError("unit-task target counts have the wrong shape")
    resource_width = 300 + layout.unit_limit * 12
    if resource_counts.shape != (state_batch, resource_width):
        raise ValueError("unit-task resource counts have the wrong shape")
    candidates = catalog.candidate_count
    features = torch.empty(
        (batch, candidates, 18), dtype=torch.float16, device=economic_state.device
    )
    mask = torch.empty(
        (batch, candidates), dtype=torch.bool, device=economic_state.device
    )
    arrivals = torch.empty(
        (batch, candidates), dtype=torch.int16, device=economic_state.device
    )
    block = 128
    _candidate_kernel[(batch, triton.cdiv(candidates, block))](
        rows,
        economic_state,
        units,
        x,
        y,
        available,
        target_counts,
        resource_counts,
        catalog.operations,
        catalog.arguments,
        catalog.targets,
        catalog.operation_turns,
        features,
        mask,
        arrivals,
        STATE_WIDTH=layout.width,
        UNIT_LIMIT=layout.unit_limit,
        BOARD_SIZE=layout.board_size,
        CANDIDATES=candidates,
        POSITIONS=layout.positions,
        INVENTORIES=layout.inventories,
        SHED=layout.shed,
        SEEDS=layout.seeds,
        TILES=layout.tiles,
        TILE_FIELDS=layout.tile_fields,
        RESOURCE_WIDTH=resource_width,
        TURNS=turns,
        BLOCK=block,
        num_warps=4,
    )
    return features, mask, arrivals


__all__ = ["candidate_surface"]
