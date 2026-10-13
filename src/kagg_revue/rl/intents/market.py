"""Canonical market round trip used by the Rank8 language audit."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, cast

import numpy as np

from kagg_revue.core.backend import BackendApi
from kagg_revue.policy.tasks.contract import ANIMALS

_MARKET_CHOICES = {
    "SELL": "MARKET_SELL",
    "BUY_SEED": "MARKET_BUY_SEED",
    "BUY_PRODUCT": "MARKET_BUY_PRODUCT",
    "BUY_ANIMAL": "MARKET_BUY_ANIMAL",
    "HIRE": "MARKET_HIRE",
    "BUY_LAND": "MARKET_BUY_LAND",
}
_ITEMS = (
    "WHEAT",
    "CARROT",
    "TOMATO",
    "STRAWBERRY",
    "MELON",
    "EGG",
    "MILK",
    "WOOL",
    "FERTILIZER",
    "GOOSE",
    "COW",
    "SHEEP",
)


@dataclass(frozen=True, slots=True)
class MarketAudit:
    """Canonical queue and any source request adjustments."""

    exact_request: bool
    canonical_market: tuple[tuple[object, ...], ...] | None
    adjustments: tuple[str, ...] = ()
    reason: str | None = None


def _candidate(
    observation: Mapping[str, object],
    *,
    kind: int,
    item: int | None = None,
    quantity: int | None = None,
) -> int | None:
    fields = np.asarray(observation["candidate_fields"], dtype=np.int64)
    selected = fields[:, 0] == kind
    if item is not None:
        selected &= fields[:, 2] == item
    if quantity is not None:
        selected &= fields[:, 7] == quantity
    matches = np.flatnonzero(selected)
    return int(matches[0]) if len(matches) == 1 else None


def _market_item(order_kind: str, item_name: str) -> int:
    vocabulary = ANIMALS if order_kind == "BUY_ANIMAL" else _ITEMS
    try:
        return vocabulary.index(item_name) + 1
    except ValueError as error:
        raise ValueError(
            f"Rank8 route contains unsupported {order_kind} item {item_name!r}"
        ) from error


def market_round_trip(
    backend: BackendApi,
    configuration: Mapping[str, object],
    engine: Any,
    player: int,
    expected: Sequence[Sequence[object]],
) -> MarketAudit:
    """Canonicalize one source queue through the production candidate ABI."""
    session = backend.intent_ledger_session(dict(configuration))
    spec = cast(Mapping[str, object], backend.intent_ledger_spec())
    choices = cast(Mapping[str, int], spec["choice_kinds"])
    exact_request = True
    adjustments: list[str] = []
    for order in expected:
        if not order:
            return MarketAudit(False, None, tuple(adjustments), "empty_market_order")
        order_kind = str(order[0])
        choice_name = _MARKET_CHOICES.get(order_kind)
        if choice_name is None:
            return MarketAudit(False, None, tuple(adjustments), "unknown_market_order")
        item = None
        if order_kind not in {"HIRE", "BUY_LAND"}:
            if len(order) != 3 or not isinstance(order[1], str):
                return MarketAudit(False, None, tuple(adjustments), "malformed_market_order")
            item = _market_item(order_kind, order[1])
        root = cast(Mapping[str, object], session.observe(engine, player))
        selected = _candidate(root, kind=choices[choice_name], item=item)
        if selected is None:
            if order_kind == "SELL":
                selected = _candidate(root, kind=choices["MARKET_SKIP_SLOT"])
                if selected is None:
                    return MarketAudit(
                        False,
                        None,
                        tuple(adjustments),
                        "market_skip_candidate_missing",
                    )
                session.select(selected)
                exact_request = False
                adjustments.append("replace_unavailable_sell_with_skip")
                continue
            return MarketAudit(False, None, tuple(adjustments), "root_candidate_missing")
        session.select(selected)
        if order_kind in {"HIRE", "BUY_LAND"}:
            continue
        quantity = order[2]
        if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity < 1:
            return MarketAudit(False, None, tuple(adjustments), "invalid_market_quantity")
        quantity_observation = cast(Mapping[str, object], session.observe(engine, player))
        selected = _candidate(
            quantity_observation,
            kind=choices["SELECT_MARKET_QUANTITY"],
            quantity=quantity,
        )
        if selected is None:
            fields = np.asarray(quantity_observation["candidate_fields"], dtype=np.int64)
            quantity_rows = fields[fields[:, 0] == choices["SELECT_MARKET_QUANTITY"]]
            available = quantity_rows[quantity_rows[:, 7] <= quantity, 7]
            if not len(available):
                return MarketAudit(False, None, tuple(adjustments), "quantity_candidate_missing")
            selected = _candidate(
                quantity_observation,
                kind=choices["SELECT_MARKET_QUANTITY"],
                quantity=int(np.max(available)),
            )
            if selected is None:
                raise RuntimeError("canonical market quantity lookup is ambiguous")
            exact_request = False
            adjustments.append(f"clip_{order_kind.lower()}_quantity")
        session.select(selected)
    root = cast(Mapping[str, object], session.observe(engine, player))
    commit = _candidate(root, kind=choices["COMMIT"])
    if commit is None:
        return MarketAudit(False, None, tuple(adjustments), "commit_candidate_missing")
    session.select(commit)
    compiled = cast(Mapping[str, object], session.action(engine, player))
    market = cast(Sequence[Sequence[object]], compiled["market"])
    canonical = tuple(tuple(order) for order in market)
    if exact_request and canonical != tuple(tuple(order) for order in expected):
        return MarketAudit(False, None, tuple(adjustments), "compiled_queue_mismatch")
    return MarketAudit(exact_request, canonical, tuple(adjustments))


def same_engine_state(left: Any, right: Any) -> bool:
    """Compare every player-visible state after one market round trip."""
    return bool(left.done) == bool(right.done) and all(
        left.observation(player) == right.observation(player) for player in (0, 1)
    )


__all__ = ["MarketAudit", "market_round_trip", "same_engine_state"]
