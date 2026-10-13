"""Teacher market requests reduced to their realized, order-preserving effects."""

from collections import Counter
from typing import Any

from kagg_revue.native import _revue_core as native

ATOMIC = frozenset({"HIRE", "BUY_LAND"})
QUANTITY_LIMIT = 100
STATE_KEYS = ("farms", "private", "market", "town")


def orders(trace: list[dict[str, Any]], player: int) -> list[list[Any]]:
    """Drop requests that filled nothing; merge adjacent identical countable requests.

    Slots settle in order against the opponent's same slot, while cash and shed
    capacity make the order between different requests meaningful. Only
    neighbours of the same kind and item are merged, within the q100 vocabulary.
    """
    result: list[list[Any]] = []
    for entry in sorted((e for e in trace if e["player"] == player), key=lambda e: e["slot_index"]):
        request = entry["requested"]
        if request is None or entry["committed"] <= 0:
            continue
        if request[0] in ATOMIC:
            result.append([request[0]])
            continue
        kind, item, quantity = request[0], request[1], int(request[2])
        last = result[-1] if result else None
        if last is not None and last[:2] == [kind, item] and last[2] + quantity <= QUANTITY_LIMIT:
            last[2] += quantity
        else:
            result.append([kind, item, quantity])
    return result


def canonicalize(replay: dict[str, Any], seats: list[int]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Rewrite teacher market lists and test each turn from the same official state.

    Observations are untouched, so encoded features are unchanged. The native
    replay must reproduce every official teacher state; otherwise its settlement
    trace cannot identify realized requests and the episode is rejected.
    """
    steps = replay["steps"]
    engine = native.Engine(replay["info"]["seed"], replay["configuration"])
    rewritten = [list(pair) for pair in steps]
    counts: Counter[str] = Counter()
    cash = {"teacher": 0.0, "opponent": 0.0}
    for turn in range(len(steps) - 1):
        official = [steps[turn + 1][seat]["action"] for seat in (0, 1)]
        branch = engine.clone()
        trace = engine.step_with_trace(*official)["market_trace"]
        reference = [engine.observation(seat) for seat in (0, 1)]
        actions = list(official)
        for seat in seats:
            expected = steps[turn + 1][seat]["observation"]
            if any(reference[seat][key] != expected[key] for key in STATE_KEYS):
                raise ValueError(f"native replay differs from the official state at turn {turn}")
            market = orders(trace, seat)
            actions[seat] = {**official[seat], "market": market}
            rewritten[turn + 1][seat] = {**steps[turn + 1][seat], "action": actions[seat]}
            requested = [e for e in trace if e["player"] == seat]
            counts["requests"] += len(requested)
            counts["malformed"] += sum(e["requested"] is None for e in requested)
            counts["unfilled"] += sum(
                e["requested"] is not None and e["committed"] <= 0 for e in requested
            )
            counts["orders"] += len(market)
        branch.step(*actions)
        observed = [branch.observation(seat) for seat in (0, 1)]
        counts["turns"] += 1
        counts["identical_turns"] += all(
            observed[seat][key] == reference[seat][key] for seat in (0, 1) for key in STATE_KEYS
        )
        counts["teacher_identical_turns"] += all(
            observed[seat]["private"] == reference[seat]["private"]
            and observed[seat]["farms"][seat] == reference[seat]["farms"][seat]
            for seat in seats
        )
        for seat in (0, 1):
            role = "teacher" if seat in seats else "opponent"
            cash[role] = max(cash[role], abs(branch.money(seat) - engine.money(seat)))
    summary = {
        **dict(sorted(counts.items())),
        "merged": counts["requests"] - counts["malformed"] - counts["unfilled"] - counts["orders"],
        "maximum_cash_difference": cash,
    }
    return {**replay, "steps": rewritten}, summary


def aggregate(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Combine per-episode canonicalization audits into dataset totals."""
    totals: Counter[str] = Counter()
    worst = {"teacher": 0.0, "opponent": 0.0}
    for record in records:
        audit = record["canonical_market"]
        totals.update({k: v for k, v in audit.items() if k != "maximum_cash_difference"})
        for role, value in audit["maximum_cash_difference"].items():
            worst[role] = max(worst[role], value)
    return {
        **dict(sorted(totals.items())),
        "identical_turn_rate": totals["identical_turns"] / max(totals["turns"], 1),
        "teacher_identical_turn_rate": totals["teacher_identical_turns"] / max(totals["turns"], 1),
        "maximum_cash_difference": worst,
        "rules": [
            "drop malformed requests and requests with zero realized fill",
            "merge adjacent requests of identical kind and item up to quantity 100",
            "retain order and requested quantities of all other requests",
        ],
    }
