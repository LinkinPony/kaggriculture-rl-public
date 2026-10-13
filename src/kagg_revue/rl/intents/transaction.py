"""Canonical transaction selection for the hindsight intent translator."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, cast

import numpy as np

from kagg_revue.policy.tasks.contract import ANIMALS, ITEMS

_MARKET_CHOICES = {
    "SELL": "MARKET_SELL",
    "BUY_SEED": "MARKET_BUY_SEED",
    "BUY_PRODUCT": "MARKET_BUY_PRODUCT",
    "BUY_ANIMAL": "MARKET_BUY_ANIMAL",
    "HIRE": "MARKET_HIRE",
    "BUY_LAND": "MARKET_BUY_LAND",
}


@dataclass(frozen=True, slots=True)
class Edit:
    """One desired canonical ledger mutation."""

    key: int
    kind: str
    target: int = -1
    item: int = -1
    work_kind: int = -1
    role: int = -1
    unit: int = -1
    operation: int = 0
    quantity: int = 0
    priority: int = 2
    asset_kind: int = 0
    maintenance: int = 0
    product_collection: int = 0
    fertilizer_collection: int = 0


def canonical_unit_action(action: Sequence[object]) -> tuple[object, ...]:
    """Normalize optional quantities exactly as the official parser does."""
    result = tuple(action)
    if result and str(result[0]) in {"PICKUP", "PLACE"} and len(result) == 2:
        return (*result, 1)
    return result


class Editor:
    """Select native candidates while retaining their canonical identities."""

    def __init__(self, session: Any, engine: Any, player: int) -> None:
        """Bind one native intent transaction to its live engine state."""
        self._session = session
        self._engine = engine
        self._player = player
        self.ids: list[int] = []

    def observation(self) -> Mapping[str, object]:
        """Return the native observation at the current transaction phase."""
        return cast(Mapping[str, object], self._session.observe(self._engine, self._player))

    def select(self, **fields: int) -> bool:
        """Select the unique candidate matching the requested canonical fields."""
        observation = self.observation()
        candidates = np.asarray(observation["candidate_fields"], dtype=np.int64)
        selected = np.ones(len(candidates), dtype=np.bool_)
        for column, value in fields.items():
            selected &= candidates[:, int(column)] == value
        matches = np.flatnonzero(selected)
        if len(matches) != 1:
            return False
        index = int(matches[0])
        ids = np.asarray(observation["canonical_id"], dtype=np.uint64)
        self.ids.append(int(ids[index]))
        self._session.select(index)
        return True


def apply_edit(
    editor: Editor,
    edit: Edit,
    choices: Mapping[str, int],
    unavailable: Counter[str],
) -> None:
    """Apply one prevalidated edit through native candidate IDs."""

    def required(ok: bool, stage: str) -> None:
        if not ok:
            raise RuntimeError(f"oracle intent editor lost required {stage} candidate")

    if edit.kind == "asset":
        if not editor.select(**{"0": choices["BEGIN_ASSET"]}):
            unavailable["asset_root_candidate_missing"] += 1
            return
        required(
            editor.select(**{"0": choices["SELECT_TARGET"], "1": edit.target}),
            "asset target",
        )
        required(
            editor.select(
                **{
                    "0": choices["SET_ASSET"],
                    "1": edit.target,
                    "2": edit.item + 1,
                    "3": edit.maintenance,
                    "4": edit.product_collection,
                    "5": edit.fertilizer_collection,
                    "6": edit.priority,
                }
            ),
            "asset profile",
        )
        return
    if edit.kind == "work":
        if not editor.select(**{"0": choices["BEGIN_WORK"]}):
            unavailable["work_root_candidate_missing"] += 1
            return
        required(
            editor.select(**{"0": choices["SELECT_TARGET"], "1": edit.target}),
            "work target",
        )
        required(
            editor.select(
                **{
                    "0": choices["ADD_WORK"],
                    "1": edit.target,
                    "2": edit.work_kind + 1,
                    "6": edit.priority,
                }
            ),
            "work profile",
        )
        return
    if edit.kind == "position":
        if not editor.select(**{"0": choices["BEGIN_POSITION"]}):
            unavailable["position_root_candidate_missing"] += 1
            return
        required(
            editor.select(**{"0": choices["SELECT_ROLE"], "2": edit.role + 1}),
            "position role",
        )
        required(
            editor.select(
                **{
                    "0": choices["SET_POSITION"],
                    "1": edit.target,
                    "2": edit.role + 1,
                    "6": edit.priority,
                }
            ),
            "position target",
        )
        return
    if edit.kind == "store":
        if not editor.select(**{"0": choices["BEGIN_STORE"]}):
            unavailable["store_root_candidate_missing"] += 1
            return
        required(
            editor.select(**{"0": choices["SELECT_STORE_ITEM"], "2": edit.item + 1}),
            "store item",
        )
        required(
            editor.select(
                **{
                    "0": choices["SELECT_STORE_QUANTITY"],
                    "2": edit.item + 1,
                    "7": edit.quantity,
                }
            ),
            "store quantity",
        )
        required(
            editor.select(
                **{
                    "0": choices["ADD_STORE"],
                    "2": edit.item + 1,
                    "6": edit.priority,
                    "7": edit.quantity,
                }
            ),
            "store priority",
        )
        return
    if edit.kind == "fetch":
        if not editor.select(**{"0": choices["BEGIN_FETCH"]}):
            unavailable["fetch_root_candidate_missing"] += 1
            return
        required(
            editor.select(
                **{
                    "0": choices["SELECT_FETCH_UNIT"],
                    "8": edit.unit + 1,
                }
            ),
            "fetch unit",
        )
        required(
            editor.select(
                **{
                    "0": choices["SELECT_FETCH_ITEM"],
                    "2": edit.item + 1,
                    "8": edit.unit + 1,
                }
            ),
            "fetch item",
        )
        required(
            editor.select(
                **{
                    "0": choices["SET_FETCH"],
                    "2": edit.item + 1,
                    "7": edit.quantity,
                    "8": edit.unit + 1,
                }
            ),
            "fetch quantity",
        )
        return
    if edit.kind == "directive":
        if not editor.select(**{"0": choices["BEGIN_DIRECTIVE"]}):
            unavailable["directive_root_candidate_missing"] += 1
            return
        required(
            editor.select(
                **{
                    "0": choices["SELECT_DIRECTIVE_UNIT"],
                    "8": edit.unit + 1,
                }
            ),
            "directive unit",
        )
        required(
            editor.select(
                **{
                    "0": choices["SELECT_DIRECTIVE_OPERATION"],
                    "8": edit.unit + 1,
                    "9": edit.operation,
                }
            ),
            "directive operation",
        )
        if edit.operation == 2:
            required(
                editor.select(
                    **{
                        "0": choices["SET_DIRECTIVE"],
                        "7": edit.quantity,
                        "8": edit.unit + 1,
                        "9": edit.operation,
                    }
                ),
                "directive wait",
            )
            return
        target_choice = (
            "SELECT_DIRECTIVE_TARGET" if edit.operation in {3, 5, 6} else "SET_DIRECTIVE"
        )
        required(
            editor.select(
                **{
                    "0": choices[target_choice],
                    "1": edit.target,
                    "8": edit.unit + 1,
                    "9": edit.operation,
                }
            ),
            "directive target",
        )
        if edit.operation not in {3, 5, 6}:
            return
        item_choice = "SELECT_DIRECTIVE_ITEM" if edit.operation in {3, 5} else "SET_DIRECTIVE"
        required(
            editor.select(
                **{
                    "0": choices[item_choice],
                    "1": edit.target,
                    "2": edit.item + 1,
                    "8": edit.unit + 1,
                    "9": edit.operation,
                }
            ),
            "directive item",
        )
        if edit.operation == 6:
            return
        required(
            editor.select(
                **{
                    "0": choices["SET_DIRECTIVE"],
                    "1": edit.target,
                    "2": edit.item + 1,
                    "7": edit.quantity,
                    "8": edit.unit + 1,
                    "9": edit.operation,
                }
            ),
            "directive quantity",
        )
        return
    if edit.kind == "cancel_directive":
        if not editor.select(**{"0": choices["BEGIN_CANCEL_DIRECTIVE"]}):
            unavailable["cancel_directive_root_candidate_missing"] += 1
            return
        required(
            editor.select(
                **{
                    "0": choices["CANCEL_DIRECTIVE"],
                    "8": edit.unit + 1,
                }
            ),
            "directive cancellation",
        )
        return
    raise ValueError(f"unknown oracle intent edit {edit.kind!r}")


def append_market(
    editor: Editor,
    choices: Mapping[str, int],
    expected: Sequence[Sequence[object]],
    unavailable: Counter[str],
    adjustments: Counter[str],
) -> None:
    """Append the source queue through canonical market candidates."""
    for order in expected:
        if not order:
            unavailable["empty_market_order"] += 1
            continue
        order_kind = str(order[0])
        choice_name = _MARKET_CHOICES.get(order_kind)
        if choice_name is None:
            unavailable["unknown_market_order"] += 1
            continue
        item = None
        if order_kind not in {"HIRE", "BUY_LAND"}:
            if len(order) != 3 or not isinstance(order[1], str):
                unavailable["malformed_market_order"] += 1
                continue
            vocabulary = ANIMALS if order_kind == "BUY_ANIMAL" else ITEMS
            try:
                item = vocabulary.index(order[1]) + 1
            except ValueError:
                unavailable["unknown_market_item"] += 1
                continue
        fields = {"0": choices[choice_name]}
        if item is not None:
            fields["2"] = item
        if not editor.select(**fields):
            if order_kind == "SELL":
                if not editor.select(**{"0": choices["MARKET_SKIP_SLOT"]}):
                    raise RuntimeError("intent editor lost required market skip candidate")
                adjustments["replace_unavailable_sell_with_skip"] += 1
            else:
                unavailable["market_root_candidate_missing"] += 1
            continue
        if order_kind in {"HIRE", "BUY_LAND"}:
            continue
        quantity = order[2]
        if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity < 1:
            raise ValueError("source market quantity must be a positive integer")
        quantity_fields = {
            "0": choices["SELECT_MARKET_QUANTITY"],
            "2": cast(int, item),
            "7": quantity,
        }
        if editor.select(**quantity_fields):
            continue
        observation = editor.observation()
        candidates = np.asarray(observation["candidate_fields"], dtype=np.int64)
        rows = candidates[candidates[:, 0] == choices["SELECT_MARKET_QUANTITY"]]
        available = rows[rows[:, 7] <= quantity, 7]
        if not len(available):
            raise RuntimeError("market quantity phase has no positive successor")
        clipped = int(np.max(available))
        if not editor.select(
            **{
                "0": choices["SELECT_MARKET_QUANTITY"],
                "2": cast(int, item),
                "7": clipped,
            }
        ):
            raise RuntimeError("oracle market quantity lookup is ambiguous")
        adjustments[f"clip_{order_kind.lower()}_quantity"] += 1


__all__ = [
    "Edit",
    "Editor",
    "append_market",
    "apply_edit",
    "canonical_unit_action",
]
