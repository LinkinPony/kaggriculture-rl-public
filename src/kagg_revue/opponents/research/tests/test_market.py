"""Regression checks for sale reservations and invalid-order filtering."""

from types import SimpleNamespace
from typing import Any

from kagg_revue.opponents.research.market import _priority, apply_market
from kagg_revue.opponents.research.settings import Variant


def test_priority_skips_empty_orders_and_preserves_purchase_barriers() -> None:
    """An unavailable sale cannot consume a slot before a purchase or reorder across it."""
    stock = {"A": 2, "B": 5, "C": 0}
    orders = [
        [],
        ["SELL", "C", 4],
        ["SELL", "A", 2],
        ["BUY_PRODUCT", "C", 4],
        ["SELL", "B", 5],
        ["SELL", "C", 4],
    ]
    namespace = {
        "_r37_quote_priority": lambda _obs, order, _stock: {"A": 1, "B": 2, "C": 3}[order[1]]
    }
    result = _priority({}, {}, orders, stock, namespace, {})
    assert result["market"] == [
        ["SELL", "A", 2],
        ["BUY_PRODUCT", "C", 4],
        ["SELL", "C", 4],
        ["SELL", "B", 5],
    ]
    assert stock == {"A": 2, "B": 5, "C": 0}


def test_advance_respects_debt_pending_pickups_and_route_boundary() -> None:
    """Only unreserved own sales before the next route change may move forward."""
    tape: list[dict[str, Any]] = [{"market": []} for _ in range(720)]
    tape[286] = {"market": [["SELL", "EGG", 8], ["SELL", "MILK", 4]]}
    tape[288] = {"market": [["SELL", "WOOL", 9]]}
    state: dict[str, Any] = {
        "pending": {0: [(290, ["PICKUP", "MILK", 1])]},
        "sell_state": {"r36_debts": {286: {"EGG": 3}}},
        "route": 0,
    }
    stock = {"EGG": 20, "MILK": 8, "WOOL": 9, "WHEAT": 50}
    namespace = {
        "FarmView": lambda obs: obs,
        "projected_shed": lambda _action, _view: stock,
        "_IMPL": SimpleNamespace(chassis=SimpleNamespace(players={0: state}, routes={0: tape})),
    }
    observation = {"step": 284, "player": 0, "market": {"prices": dict.fromkeys(stock, 10)}}
    action = {"farmer": ["PASS"], "hands": [], "market": []}
    variant = Variant(name="check", market="lead", lead=6)
    result = apply_market(observation, action, namespace, variant, {})
    assert result["market"] == [["SELL", "EGG", 5]]
    assert state["sell_state"]["r36_debts"][286]["EGG"] == 8
    assert apply_market(observation, action, namespace, variant, {})["market"] == []
