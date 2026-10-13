"""Planner-facing rule data generated from the native engine tables."""

from typing import Any, cast

from kagg_revue.native._revue_native import game_rules

_RULES = game_rules()
CROP_RULES = cast(dict[str, dict[str, Any]], _RULES["crops"])
ANIMAL_RULES = cast(dict[str, dict[str, Any]], _RULES["animals"])
PRODUCTS = cast(tuple[str, ...], tuple(_RULES["products"]))
PRODUCT_BASE_PRICES = cast(dict[str, float], _RULES["product_base_prices"])
LAND_PRICES = cast(tuple[int, ...], tuple(int(value) for value in _RULES["land_prices"]))
TOWN_SHOP_RULES = cast(dict[str, dict[str, Any]], _RULES["shops"])

__all__ = [
    "ANIMAL_RULES",
    "CROP_RULES",
    "LAND_PRICES",
    "PRODUCTS",
    "PRODUCT_BASE_PRICES",
    "TOWN_SHOP_RULES",
]
