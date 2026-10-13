"""Checkpoint-bound ABI for deterministic economic consequence features."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

LEGACY_ECONOMIC_FEATURE_VERSION = "economic-consequences-v1"
ECONOMIC_FEATURE_VERSION = "economic-consequences-v2"
ECONOMIC_STATE_VERSION = 3
TURN_FEATURES = 50
PREFIX_FEATURES = 30
CANDIDATE_FEATURES = 20
QUANTITY_FEATURES = 12

ACTION_TOKENS = 67
UNIT_TOKENS = 44
MAXIMUM_QUANTITY = 128
ITEMS = 12
CROPS = 5
PRODUCTS = 9
ANIMALS = 3
LAND_LEVELS = 3
TILE_FIELDS = 12
HEADER_FIELDS = 14
MARKET_PROJECTION_CONDITIONAL = 13


@dataclass(frozen=True)
class EconomicStateLayout:
    """Offsets shared by native export, rollout kernels, and feature replay."""

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
    def create(cls, board_size: int, unit_limit: int) -> EconomicStateLayout:
        """Build the lossless state layout without loading the native module."""
        if board_size < 2 or unit_limit < 1:
            raise ValueError("economic state dimensions must be positive")
        positions = HEADER_FIELDS
        inventories = positions + unit_limit * 2
        inventory_order = inventories + unit_limit * ITEMS
        shed = inventory_order + unit_limit * ITEMS
        seeds = shed + ITEMS
        market_inventory = seeds + CROPS
        market_prices = market_inventory + PRODUCTS
        market_base_milli = market_prices + PRODUCTS
        market_i0 = market_base_milli + PRODUCTS
        market_t_milli = market_i0 + PRODUCTS
        market_below_function = market_t_milli + PRODUCTS
        market_below_target_milli = market_below_function + PRODUCTS
        market_above_function = market_below_target_milli + PRODUCTS
        market_above_target_milli = market_above_function + PRODUCTS
        seed_costs = market_above_target_milli + PRODUCTS
        animal_costs = seed_costs + CROPS
        land_costs = animal_costs + ANIMALS
        tiles = land_costs + LAND_LEVELS
        width = tiles + board_size * board_size * TILE_FIELDS
        return cls(
            board_size=board_size,
            unit_limit=unit_limit,
            header_fields=HEADER_FIELDS,
            positions=positions,
            inventories=inventories,
            inventory_order=inventory_order,
            shed=shed,
            seeds=seeds,
            market_inventory=market_inventory,
            market_prices=market_prices,
            market_base_milli=market_base_milli,
            market_i0=market_i0,
            market_t_milli=market_t_milli,
            market_below_function=market_below_function,
            market_below_target_milli=market_below_target_milli,
            market_above_function=market_above_function,
            market_above_target_milli=market_above_target_milli,
            seed_costs=seed_costs,
            animal_costs=animal_costs,
            land_costs=land_costs,
            tiles=tiles,
            tile_fields=TILE_FIELDS,
            width=width,
        )

    @classmethod
    def from_spec(
        cls,
        spec: Mapping[str, int],
        *,
        board_size: int,
        unit_limit: int,
    ) -> EconomicStateLayout:
        """Authenticate the native ABI against the Python construction."""
        if spec["version"] != ECONOMIC_STATE_VERSION:
            raise ValueError("native economic state version is unsupported")
        expected = cls.create(board_size, unit_limit)
        native = {
            name: spec[name]
            for name in expected.__dataclass_fields__
            if name not in {"board_size", "unit_limit"}
        }
        resolved = cls(board_size=board_size, unit_limit=unit_limit, **native)
        if resolved != expected:
            raise ValueError("native economic state layout is inconsistent")
        return resolved


__all__ = [
    "ACTION_TOKENS",
    "ANIMALS",
    "CANDIDATE_FEATURES",
    "CROPS",
    "ECONOMIC_FEATURE_VERSION",
    "LEGACY_ECONOMIC_FEATURE_VERSION",
    "ECONOMIC_STATE_VERSION",
    "EconomicStateLayout",
    "ITEMS",
    "MAXIMUM_QUANTITY",
    "MARKET_PROJECTION_CONDITIONAL",
    "PREFIX_FEATURES",
    "PRODUCTS",
    "QUANTITY_FEATURES",
    "TURN_FEATURES",
    "UNIT_TOKENS",
]
