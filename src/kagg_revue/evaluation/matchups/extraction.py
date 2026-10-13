"""Reconstruct actual trades, production and daily cash from official replays."""

from collections import Counter
from pathlib import Path
from typing import Any

from kagg_revue.artifacts.io import digest
from kagg_revue.datasets.coverage.extraction import snapshot
from kagg_revue.datasets.observations import ReplayObservations, difference
from kagg_revue.datasets.openings.extraction import load, recoveries
from kagg_revue.native import _revue_core as native
from kagg_revue.native._revue_native import compile_unit_prefix_from_obs

FIELDS = ("player", "step", "day", "hour", "farms", "private", "market", "town")


def inventory(private: dict[str, Any]) -> Counter[str]:
    """Count shed and carried items together, excluding seeds."""
    result: Counter[str] = Counter(private["shed"])
    for carried in private["inventories"]:
        result.update(carried)
    return result


def extract(task: dict[str, Any]) -> dict[str, Any]:
    """Reproduce both seats completely before trusting per-order accounting."""
    if digest(Path(task["path"])) != task["sha256"]:
        raise ValueError("replay fingerprint differs from acquisition manifest")
    replay, raw_hash = load(task)
    steps = replay["steps"]
    if int(replay["info"]["EpisodeId"]) != task["episode_id"]:
        raise ValueError("replay identity differs from API episode")
    if replay["statuses"] != ["DONE", "DONE"] or len(steps) != 720:
        raise ValueError("this accounting requires two complete 720-frame trajectories")
    if any(frame[s]["status"] != "ACTIVE" for frame in steps[:-1] for s in (0, 1)):
        raise ValueError("a midgame timeout or error invalidates strategic-only accounting")
    engine = native.Engine(replay["info"]["seed"], replay["configuration"])
    sequences = [ReplayObservations(), ReplayObservations()]
    orders: list[list[dict[str, Any]]] = [[], []]
    snapshots: list[dict[str, Any]] = [{}, {}]
    events: list[list[dict[str, Any]]] = [[], []]
    operations: list[Counter[str]] = [Counter(), Counter()]
    invalid: list[list[dict[str, Any]]] = [[], []]
    harvested: list[Counter[str]] = [Counter(), Counter()]
    overflow: list[Counter[str]] = [Counter(), Counter()]
    ledger: list[dict[str, Any]] = [{}, {}]
    cash: list[list[float]] = [[], []]
    for turn, frame in enumerate(steps):
        observed = []
        for seat in (0, 1):
            expected = sequences[seat].update(frame[seat]["observation"], turn)
            actual = engine.observation(seat)
            mismatch = difference({k: actual[k] for k in FIELDS}, {k: expected[k] for k in FIELDS})
            if mismatch:
                raise ValueError(f"{task['episode_id']}:{turn}:{seat}: {mismatch}")
            observed.append(actual)
            cash[seat].append(actual["farms"][seat]["money"])
            if turn % 24 == 0 or turn in (1, 2, 4, 12, 20, 21, 23, 719):
                snapshots[seat][str(turn)] = {
                    **snapshot(actual, seat),
                    "inventory": dict(inventory(actual["private"])),
                    "prices": actual["market"]["prices"],
                }
        if turn == len(steps) - 1:
            break
        actions = [steps[turn + 1][s]["action"] for s in (0, 1)]
        post = []
        for seat in (0, 1):
            compiled = compile_unit_prefix_from_obs(
                observed[seat], replay["configuration"], actions[seat]
            )
            post.append(compiled["post_unit"])
            for entry in compiled["trace"]:
                operation = entry["actual"][0]
                operations[seat][operation] += 1
                if entry["requested"] != entry["actual"]:
                    invalid[seat].append({"turn": turn, **entry})
            before = inventory(observed[seat]["private"])
            after_inventory = inventory(post[seat]["private"])
            # Transfers within the farm cancel; positive changes are harvested products.
            harvested[seat].update(after_inventory - before)
        trace = engine.step_with_trace(*actions)
        balances = [inventory(p["private"]) for p in post]
        for order in trace["market_trace"]:
            seat = order["player"]
            order = {"turn": turn, **order}
            orders[seat].append(order)
            request = order["requested"]
            if not request:
                continue
            key = ":".join(request[:2])
            entry = ledger[seat].setdefault(key, {"quantity": 0, "cash": 0, "orders": 0})
            entry["quantity"] += order["committed"]
            entry["cash"] += order["money_after"] - order["money_before"]
            entry["orders"] += 1
            if request[0] in ("SELL", "BUY_PRODUCT", "BUY_ANIMAL"):
                balances[seat][request[1]] += order["committed"] * (
                    -1 if request[0] == "SELL" else 1
                )
        for seat in (0, 1):
            after = engine.observation(seat)
            lost = balances[seat] - inventory(after["private"])
            if lost:
                overflow[seat].update(lost)
                events[seat].append({"turn": turn, "overflow": dict(lost)})
            if (turn + 1) % 24:
                continue
            missed: Counter[str] = Counter()
            for y, row in enumerate(post[seat]["farm"]["tiles"]):
                for x, tile in enumerate(row):
                    if not isinstance(tile, dict):
                        continue
                    name = tile.get("crop") or tile.get("animal")
                    if not name:
                        continue
                    watered = tile.get("watered_today", tile.get("fed_today", True))
                    if not watered:
                        missed[name] += 1
                    new = after["farms"][seat]["tiles"][y][x]
                    new_name = (
                        (new.get("crop") or new.get("animal")) if isinstance(new, dict) else None
                    )
                    if new_name != name:
                        events[seat].append(
                            {
                                "turn": turn,
                                "asset_lost_at_refresh": name,
                                "x": x,
                                "y": y,
                                "before": tile,
                                "after": new,
                            }
                        )
            if missed:
                events[seat].append({"turn": turn, "unwatered_or_unfed": dict(missed)})
    rows = []
    for seat in (0, 1):
        agent = next(a for a in task["agents"] if a.get("index", 0) == seat)
        total_cash = sum(entry["cash"] for entry in ledger[seat].values())
        if total_cash != cash[seat][-1] - cash[seat][0]:
            raise ValueError("market cash ledger does not reconcile to final bank balance")
        if cash[seat][-1] != agent["reward"]:
            raise ValueError("API reward differs from final replay cash")
        rows.append(
            {
                "seat": seat,
                "submission_id": agent["submissionId"],
                "name": agent["teamName"],
                "cash": cash[seat],
                "ledger": ledger[seat],
                "harvested": dict(harvested[seat]),
                "overflow": dict(overflow[seat]),
                "snapshots": snapshots[seat],
                "events": events[seat],
                "operations": dict(operations[seat]),
                "invalid_units": invalid[seat],
                "shortfalls": recoveries(orders[seat], 719),
                "orders": orders[seat],
                "opening_actions": [f[seat]["action"] for f in steps[1:25]],
            }
        )
    return {
        "episode_id": task["episode_id"],
        "seed": replay["info"]["seed"],
        "date": task["createTime"],
        "statuses": replay["statuses"],
        "module_version": replay.get("module_version"),
        "raw_sha256": raw_hash,
        "checked_observations": len(steps) * 2,
        "cash_ledger_reconciled": True,
        "shops": steps[-1][0]["observation"]["town"]["unlocked_shops"],
        "players": rows,
    }
