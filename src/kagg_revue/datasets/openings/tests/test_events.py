"""Guard inventory accounting and the explicit scope of recovery diagnostics."""

from typing import Any

from kagg_revue.datasets.openings.extraction import production, recoveries


def test_production_counts_animals_carried_between_shed_and_placement() -> None:
    """Moving livestock stays in production totals; harvested crops do not."""
    state = {
        "assets": {"COW": 1, "MELON": 6},
        "shed": {"COW": 1, "MELON": 20},
        "carried_animals": {"COW": 2, "SHEEP": 1},
    }
    result = production(state)
    assert result["COW"] == 4
    assert result["SHEEP"] == 1
    assert result["MELON"] == 6


def test_catchup_requires_matching_actual_purchases_in_the_following_twelve_turns() -> None:
    """Ignore null orders, same-turn buys, other products and late purchases."""
    orders: list[dict[str, Any]] = [
        {"turn": 0, "requested": ["BUY_ANIMAL", "SHEEP", 2], "committed": 0},
        {"turn": 0, "requested": ["BUY_ANIMAL", "SHEEP", 1], "committed": 1},
        {"turn": 1, "requested": ["SELL", "WHEAT", 1000], "committed": 5},
        {"turn": 1, "requested": None, "committed": 0},
        {"turn": 2, "requested": ["BUY_ANIMAL", "COW", 2], "committed": 2},
        {"turn": 3, "requested": ["BUY_ANIMAL", "SHEEP", 1], "committed": 1},
        {"turn": 12, "requested": ["BUY_ANIMAL", "SHEEP", 1], "committed": 1},
        {"turn": 20, "requested": ["BUY_SEED", "WHEAT", 2], "committed": 1},
        {"turn": 33, "requested": ["BUY_SEED", "WHEAT", 1], "committed": 1},
        {"turn": 34, "requested": ["BUY_SEED", "WHEAT", 1000], "committed": 0},
    ]
    events = recoveries(orders, 144)
    assert len(events) == 2
    assert events[0]["catchup_turns"] == 12
    assert events[0]["followup_purchased_12"] == 2
    assert events[1]["catchup_turns"] is None
    assert all(event["followup_complete"] for event in events)
