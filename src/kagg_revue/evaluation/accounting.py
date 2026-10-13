"""Passive per-seat cash, production and inventory records for complete games."""

import math
from collections import Counter
from typing import Any


def _snapshot(observation: dict[str, Any], seat: int, step: int) -> dict[str, Any]:
    farm = observation["farms"][seat]
    private = observation["private"]
    tiles = [tile for row in farm["tiles"] for tile in row if isinstance(tile, dict)]
    carried: Counter[str] = Counter()
    for inventory in private["inventories"]:
        carried.update(inventory)
    return {
        "step": step,
        "cash": farm["money"],
        "units": 1 + len(farm["hands"]),
        "unlocked_quadrants": len(farm["unlocked_quadrants"]),
        "plants": Counter(str(tile["crop"]) for tile in tiles if tile["kind"] == "PLANT"),
        "animals": Counter(str(tile["animal"]) for tile in tiles if tile.get("animal")),
        "uncollected_yield": sum(tile.get("yield_units", 0) for tile in tiles),
        "shed": dict(private["shed"]),
        "seeds": dict(private["seeds"]),
        "carried": dict(carried),
    }


class GameAccounting:
    """Observe actions and exact market settlements without touching either actor."""

    def __init__(self, turns_per_day: int) -> None:
        """Create counters and choose the interval for passive state snapshots."""
        if turns_per_day <= 0:
            raise ValueError("accounting needs a positive day length")
        self.turns_per_day = turns_per_day
        self.steps = 0
        self.cash: list[float] | None = None
        self.players: list[dict[str, Any]] = [
            {
                "seat": seat,
                "sales_revenue": 0.0,
                "market_expenditure": 0.0,
                "nonmarket_cash_delta": 0.0,
                "revenue_by_item": Counter(),
                "expenditure_by_order": Counter(),
                "committed_quantities": Counter(),
                "market_status": Counter(),
                "submitted_unit_actions": Counter(),
                "unit_turns": 0,
                "plant_tile_turns": 0,
                "animal_tile_turns": 0,
                "uncollected_yield_turns": 0,
                "timeline": [],
            }
            for seat in (0, 1)
        ]

    def record(
        self,
        observations: list[dict[str, Any]],
        actions: list[dict[str, Any]],
        trace: dict[str, Any],
        after_cash: list[float],
    ) -> None:
        """Reconcile each step against its own prior cash and settled market orders."""
        if trace["step"] != self.steps or len(observations) != 2 or len(after_cash) != 2:
            raise ValueError("accounting requires consecutive two-seat game steps")
        before = [
            float(observation["farms"][seat]["money"])
            for seat, observation in enumerate(observations)
        ]
        if self.cash is not None and before != self.cash:
            raise ValueError("accounting cash differs from the preceding final state")
        market_delta = [0.0, 0.0]
        for entry in trace["market_trace"]:
            seat = entry["player"]
            player = self.players[seat]
            change = float(entry["money_after"] - entry["money_before"])
            market_delta[seat] += change
            player["sales_revenue"] += max(0, change)
            player["market_expenditure"] += max(0, -change)
            requested = entry["requested"]
            order = str(requested[0]) if requested else "MALFORMED"
            player["market_status"][f"{order}:{entry['status']}"] += 1
            actual = entry["actual"]
            if actual:
                key = ":".join(str(value) for value in actual[:2])
                player["committed_quantities"][key] += entry["committed"]
                player["expenditure_by_order"][key] += max(0, -change)
                if change > 0:
                    player["revenue_by_item"][key] += change
        for seat, player in enumerate(self.players):
            snapshot = _snapshot(observations[seat], seat, self.steps)
            if not self.steps:
                player["initial_cash"] = before[seat]
            if self.steps % self.turns_per_day == 0:
                player["timeline"].append(snapshot)
            player["unit_turns"] += snapshot["units"]
            player["plant_tile_turns"] += sum(snapshot["plants"].values())
            player["animal_tile_turns"] += sum(snapshot["animals"].values())
            player["uncollected_yield_turns"] += snapshot["uncollected_yield"]
            for action in [actions[seat].get("farmer"), *actions[seat].get("hands", [])]:
                operation = (
                    str(action[0])
                    if isinstance(action, (list, tuple)) and action
                    else "OMITTED_OR_MALFORMED"
                )
                player["submitted_unit_actions"][operation] += 1
            player["nonmarket_cash_delta"] += after_cash[seat] - before[seat] - market_delta[seat]
        self.cash = after_cash
        self.steps += 1

    def finish(self, observations: list[dict[str, Any]]) -> dict[str, Any]:
        """Keep terminal unsold stock and verify the complete per-seat cash identity."""
        if self.cash is None or len(observations) != 2:
            raise ValueError("accounting cannot finish an empty game")
        for seat, player in enumerate(self.players):
            terminal = _snapshot(observations[seat], seat, self.steps)
            expected = (
                player["initial_cash"]
                + player["sales_revenue"]
                - player["market_expenditure"]
                + player["nonmarket_cash_delta"]
            )
            if terminal["cash"] != self.cash[seat] or not math.isclose(
                expected, terminal["cash"], abs_tol=1e-6
            ):
                raise ValueError("terminal cash accounting does not reconcile")
            player["timeline"].append(terminal)
            player["terminal_cash"] = terminal["cash"]
        return {
            "steps": self.steps,
            "players": self.players,
            "cash_reconciled": True,
            "scope": "Passive per-seat observations and exact market settlements. Unit action "
            "counts are submitted commands, not successful executions. Uncollected yield and "
            "inventory are units, not marked-to-market cash or a causal explanation of losses.",
        }
