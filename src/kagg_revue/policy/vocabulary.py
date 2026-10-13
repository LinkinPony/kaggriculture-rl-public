"""Checkpoint-bound numeric action vocabularies."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ActionVocabulary:
    """Numeric ranges for one actor action ABI."""

    version: str
    action_tokens: int
    unit_tokens: int
    pickup_first: int
    pickup_stop: int
    pickup_stride: int
    drop: int
    place_first: int
    place_stop: int
    place_stride: int
    plant_first: int
    water: int
    harvest: int
    fertilize: int
    dig: int
    build_coop: int
    build_pasture: int
    feed: int
    collect_fertilizer: int
    care: int

    @property
    def market_stop(self) -> int:
        """Return the first market token."""
        return self.unit_tokens

    @property
    def market_skip(self) -> int:
        """Return the empty market-slot token."""
        return self.unit_tokens + 1

    @property
    def sell_first(self) -> int:
        """Return the first SELL token."""
        return self.unit_tokens + 2

    @property
    def seed_first(self) -> int:
        """Return the first BUY_SEED token."""
        return self.unit_tokens + 11

    @property
    def product_first(self) -> int:
        """Return the first BUY_PRODUCT token."""
        return self.unit_tokens + 16

    @property
    def animal_first(self) -> int:
        """Return the first BUY_ANIMAL token."""
        return self.unit_tokens + 18

    @property
    def hire(self) -> int:
        """Return the HIRE token."""
        return self.unit_tokens + 21

    @property
    def buy_land(self) -> int:
        """Return the BUY_LAND token."""
        return self.unit_tokens + 22

    def item_token(self, first: int, item: int) -> int:
        """Return the explicit-quantity token for an item range."""
        return first + item * self.pickup_stride + (self.pickup_stride - 1)


LEGACY_ACTIONS = ActionVocabulary(
    version="turn-policy-actions-v1",
    action_tokens=91,
    unit_tokens=68,
    pickup_first=5,
    pickup_stop=29,
    pickup_stride=2,
    drop=29,
    place_first=30,
    place_stop=54,
    place_stride=2,
    plant_first=54,
    water=59,
    harvest=60,
    fertilize=61,
    dig=62,
    build_coop=63,
    build_pasture=64,
    feed=65,
    collect_fertilizer=66,
    care=67,
)

CURRENT_ACTIONS = ActionVocabulary(
    version="turn-policy-actions-v2",
    action_tokens=67,
    unit_tokens=44,
    pickup_first=5,
    pickup_stop=17,
    pickup_stride=1,
    drop=17,
    place_first=18,
    place_stop=30,
    place_stride=1,
    plant_first=30,
    water=35,
    harvest=36,
    fertilize=37,
    dig=38,
    build_coop=39,
    build_pasture=40,
    feed=41,
    collect_fertilizer=42,
    care=43,
)


def action_vocabulary(action_tokens: int) -> ActionVocabulary:
    """Resolve an authenticated vocabulary from its total width."""
    for vocabulary in (CURRENT_ACTIONS, LEGACY_ACTIONS):
        if vocabulary.action_tokens == action_tokens:
            return vocabulary
    raise ValueError(f"unsupported action vocabulary width: {action_tokens}")


__all__ = [
    "ActionVocabulary",
    "CURRENT_ACTIONS",
    "LEGACY_ACTIONS",
    "action_vocabulary",
]
