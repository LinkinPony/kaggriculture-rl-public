"""Immutable v5b supplement geometry and an exact projection to v4 observations."""

from dataclasses import replace
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kagg_revue.native.features import Layout

VERSION = "grounded-derived-context-v5b"
GLOBAL_FEATURES = 24
BOARD_FEATURES = 20
UNIT_FEATURES = 16
PRODUCT_FEATURES = 96


def legacy_layout(layout: "Layout") -> "Layout":
    """Remove only the versioned supplement, retaining every v4 field and action."""
    if layout.version != VERSION or (
        layout.derived_global_features,
        layout.derived_board_features,
        layout.derived_unit_features,
        layout.derived_product_features,
    ) != (GLOBAL_FEATURES, BOARD_FEATURES, UNIT_FEATURES, PRODUCT_FEATURES):
        raise ValueError("legacy projection requires the complete v5b supplement")
    return replace(
        layout,
        version="grounded-production-context-v4",
        derived_global_features=0,
        derived_board_features=0,
        derived_unit_features=0,
        derived_product_features=0,
    )
