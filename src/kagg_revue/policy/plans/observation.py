"""Rich actor-visible observation ABI shared with the turn policy."""

from __future__ import annotations

from kagg_revue.policy.economics.layout import EconomicStateLayout

BOARD_SHAPE = (2, 29, 10, 10)
UNIT_SHAPE = (2, 32, 60)
GLOBAL_FEATURES = 82
ECONOMIC_STATE_FEATURES = EconomicStateLayout.create(
    BOARD_SHAPE[-1],
    UNIT_SHAPE[1],
).width

__all__ = [
    "BOARD_SHAPE",
    "ECONOMIC_STATE_FEATURES",
    "GLOBAL_FEATURES",
    "UNIT_SHAPE",
]
