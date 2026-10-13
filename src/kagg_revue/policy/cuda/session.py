"""CUDA-resident policy-session ABI and checked kernel launches."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

import torch
from torch import Tensor

from kagg_revue.policy.cuda.kernels import (
    _compile_legal_kernel,
    _select_kernel,
)

_STATE_VERSION = 3
_ACTION_TOKENS = 67
_ITEMS = 12
_CROPS = 5


@dataclass(frozen=True)
class GpuPolicyStateLayout:
    """Validated offsets for the native compact PolicySession state."""

    board_size: int
    unit_limit: int
    header_fields: int
    positions: int
    inventories: int
    inventory_order: int
    shed: int
    seeds: int
    market_inventory: int
    market_prices: int
    market_base_milli: int
    market_i0: int
    market_t_milli: int
    market_below_function: int
    market_below_target_milli: int
    market_above_function: int
    market_above_target_milli: int
    seed_costs: int
    animal_costs: int
    land_costs: int
    tiles: int
    tile_fields: int
    width: int

    @classmethod
    def from_spec(
        cls,
        spec: Mapping[str, int],
        *,
        board_size: int,
        unit_limit: int,
    ) -> GpuPolicyStateLayout:
        """Validate the native ABI before a CUDA kernel consumes it."""
        if spec["version"] != _STATE_VERSION:
            raise ValueError("native GPU policy state version is unsupported")
        layout = cls(
            board_size=board_size,
            unit_limit=unit_limit,
            header_fields=spec["header_fields"],
            positions=spec["positions"],
            inventories=spec["inventories"],
            inventory_order=spec["inventory_order"],
            shed=spec["shed"],
            seeds=spec["seeds"],
            market_inventory=spec["market_inventory"],
            market_prices=spec["market_prices"],
            market_base_milli=spec["market_base_milli"],
            market_i0=spec["market_i0"],
            market_t_milli=spec["market_t_milli"],
            market_below_function=spec["market_below_function"],
            market_below_target_milli=spec["market_below_target_milli"],
            market_above_function=spec["market_above_function"],
            market_above_target_milli=spec["market_above_target_milli"],
            seed_costs=spec["seed_costs"],
            animal_costs=spec["animal_costs"],
            land_costs=spec["land_costs"],
            tiles=spec["tiles"],
            tile_fields=spec["tile_fields"],
            width=spec["width"],
        )
        expected = (
            layout.header_fields,
            layout.positions + unit_limit * 2,
            layout.inventories + unit_limit * _ITEMS,
            layout.inventory_order + unit_limit * _ITEMS,
            layout.shed + _ITEMS,
            layout.seeds + _CROPS,
            layout.market_inventory + 9,
            layout.market_prices + 9,
            layout.market_base_milli + 9,
            layout.market_i0 + 9,
            layout.market_t_milli + 9,
            layout.market_below_function + 9,
            layout.market_below_target_milli + 9,
            layout.market_above_function + 9,
            layout.market_above_target_milli + 9,
            layout.seed_costs + 5,
            layout.animal_costs + 3,
            layout.land_costs + 3,
            layout.tiles + board_size * board_size * layout.tile_fields,
        )
        actual = (
            layout.positions,
            layout.inventories,
            layout.inventory_order,
            layout.shed,
            layout.seeds,
            layout.market_inventory,
            layout.market_prices,
            layout.market_base_milli,
            layout.market_i0,
            layout.market_t_milli,
            layout.market_below_function,
            layout.market_below_target_milli,
            layout.market_above_function,
            layout.market_above_target_milli,
            layout.seed_costs,
            layout.animal_costs,
            layout.land_costs,
            layout.tiles,
            layout.width,
        )
        if layout.header_fields != 14 or layout.tile_fields != 12 or actual != expected:
            raise ValueError("native GPU policy state layout is inconsistent")
        return layout


def _validate_state(state: Tensor, layout: GpuPolicyStateLayout) -> None:
    if state.device.type != "cuda" or state.dtype not in {torch.int32, torch.int64}:
        raise ValueError("GPU policy state must be a CUDA int32 or int64 tensor")
    if state.ndim != 2 or state.shape[1] != layout.width or not state.is_contiguous():
        raise ValueError("GPU policy state has the wrong compact layout")


def compile_policy_legal(
    state: Tensor,
    legal: Tensor,
    phases: Tensor,
    decisions: Tensor,
    layout: GpuPolicyStateLayout,
) -> None:
    """Compile exact current-prefix legality for every CUDA-resident session."""
    _validate_state(state, layout)
    batch = state.shape[0]
    if legal.shape != (batch, _ACTION_TOKENS) or legal.dtype != torch.bool:
        raise ValueError("GPU policy legal output has the wrong shape or dtype")
    if phases.shape != (batch,) or phases.dtype != torch.int64:
        raise ValueError("GPU policy phase output has the wrong shape or dtype")
    if decisions.shape != (batch,) or decisions.dtype != torch.bool:
        raise ValueError("GPU policy decision output has the wrong shape or dtype")
    if legal.device != state.device or phases.device != state.device:
        raise ValueError("GPU policy outputs must share the state device")
    if decisions.device != state.device:
        raise ValueError("GPU policy decision output must share the state device")
    _compile_legal_kernel[(batch,)](
        state,
        legal,
        phases,
        decisions,
        STATE_WIDTH=layout.width,
        POSITIONS=layout.positions,
        INVENTORIES=layout.inventories,
        SHED=layout.shed,
        SEEDS=layout.seeds,
        TILES=layout.tiles,
        TILE_FIELDS=layout.tile_fields,
        BOARD_SIZE=layout.board_size,
        UNIT_LIMIT=layout.unit_limit,
        ACTION_TOKENS=_ACTION_TOKENS,
        BLOCK=128,
        num_warps=4,
    )


def select_policy_actions(
    state: Tensor,
    tokens: Tensor,
    quantities: Tensor,
    layout: GpuPolicyStateLayout,
    active: Tensor | None = None,
) -> None:
    """Apply one legal selection per active session entirely on CUDA."""
    _validate_state(state, layout)
    batch = state.shape[0]
    if tokens.shape != (batch,) or quantities.shape != (batch,):
        raise ValueError("GPU policy selections must have one value per session")
    if tokens.dtype != torch.int64 or quantities.dtype != torch.int64:
        raise ValueError("GPU policy selections must use int64")
    if tokens.device != state.device or quantities.device != state.device:
        raise ValueError("GPU policy selections must share the state device")
    selected = state[:, 4] != 2 if active is None else active
    if selected.shape != (batch,) or selected.dtype != torch.bool:
        raise ValueError("GPU policy active mask must use one boolean per session")
    if selected.device != state.device:
        raise ValueError("GPU policy active mask must share the state device")
    _select_kernel[(batch,)](
        state,
        tokens,
        quantities,
        selected,
        STATE_WIDTH=layout.width,
        POSITIONS=layout.positions,
        INVENTORIES=layout.inventories,
        INVENTORY_ORDER=layout.inventory_order,
        SHED=layout.shed,
        SEEDS=layout.seeds,
        TILES=layout.tiles,
        TILE_FIELDS=layout.tile_fields,
        BOARD_SIZE=layout.board_size,
        UNIT_LIMIT=layout.unit_limit,
        num_warps=1,
    )


__all__ = [
    "GpuPolicyStateLayout",
    "compile_policy_legal",
    "select_policy_actions",
]
