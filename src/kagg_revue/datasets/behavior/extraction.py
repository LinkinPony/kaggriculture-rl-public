"""Extract action-aligned fingerprints without executing submitted agent code."""

import hashlib
import zipfile
from collections import Counter, defaultdict
from typing import Any

import orjson

CHANNELS = ("raw", "units", "structure", "market")
CHECKPOINTS = (0, 24, 72, 144, 216, 360, 504, 648, 718)


def fingerprint(value: Any) -> int:
    """Hash canonical JSON into a stable unsigned 64-bit fingerprint."""
    raw = orjson.dumps(value, option=orjson.OPT_SORT_KEYS)
    return int.from_bytes(hashlib.blake2b(raw, digest_size=8).digest(), "little")


def normalized_action(action: Any) -> dict[str, Any]:
    """Normalize missing requests and trailing PASS padding, retaining quantities.

    This is a request fingerprint, not an environment legality or success check.
    Interior PASS entries and market order order are deliberately preserved.
    """
    action = action if isinstance(action, dict) else {}
    farmer = action.get("farmer") or ["PASS"]
    hands = list(action.get("hands") or [])
    hands = [hand or ["PASS"] for hand in hands]
    while hands and hands[-1] == ["PASS"]:
        hands.pop()
    return {"farmer": farmer, "hands": hands, "market": action.get("market") or []}


def action_fingerprints(action: Any) -> list[int]:
    """Separate complete requests, unit routes, quantity-free form and market."""
    value = normalized_action(action)
    units = [value["farmer"], *value["hands"]]
    structure = [
        [["<quantity>" if isinstance(x, (int, float)) else x for x in command] for command in group]
        for group in (units, value["market"])
    ]
    return [
        fingerprint(action),
        fingerprint(units),
        fingerprint(structure),
        fingerprint(value["market"]),
    ]


def _snapshot(observation: dict[str, Any], seat: int) -> dict[str, Any]:
    farm = observation["farms"][seat]
    tiles: Counter[str] = Counter()
    for row in farm["tiles"]:
        for tile in row:
            if isinstance(tile, dict):
                tiles[str(tile.get("crop") or tile.get("animal") or tile["kind"])] += 1
    return {
        "cash": farm["money"],
        "tiles": dict(tiles),
        "hands": len(farm["hands"]),
        "land": len(farm["unlocked_quadrants"]),
        "shed": observation["private"]["shed"],
        "prices": observation["market"]["prices"],
        "shops": observation["town"]["unlocked_shops"],
    }


def extract_episode(task: tuple[str, str, str, dict[str, Any]]) -> list[dict[str, Any]]:
    """Read one complete episode; action at frame t+1 belongs to observation t."""
    archive, episode_id, date, metadata = task
    with zipfile.ZipFile(archive) as zipped:
        replay = orjson.loads(zipped.read(f"{episode_id}.json"))
    steps = replay["steps"]
    complete = (
        replay["statuses"] == ["DONE", "DONE"]
        and len(steps) == replay["configuration"]["episodeSteps"]
    )
    if replay["name"] != "kaggriculture":
        raise ValueError(f"unexpected environment in {episode_id}")
    if len(steps) != 720:
        raise ValueError(f"nonstandard length in {episode_id}: {len(steps)}")
    rows = []
    for seat in (0, 1):
        hashes: list[list[int]] = []
        early: list[dict[str, Any]] = []
        history = hashlib.blake2b(digest_size=16)
        unit_operations: Counter[str] = Counter()
        market_operations: Counter[str] = Counter()
        quantities: dict[str, float] = defaultdict(float)
        snapshots = {}
        all_pass = 0
        money = [float(s[seat]["observation"]["farms"][seat]["money"]) for s in steps]
        overage = []
        for step, (before, after) in enumerate(zip(steps[:-1], steps[1:], strict=True)):
            observation = before[seat]["observation"]
            action = after[seat]["action"]
            hashes.append(action_fingerprints(action))
            normalized = normalized_action(action)
            units = [normalized["farmer"], *normalized["hands"]]
            unit_operations.update(str(a[0]) for a in units if a)
            all_pass += all(a == ["PASS"] for a in units)
            for order in normalized["market"]:
                if not order:
                    market_operations["EMPTY_REQUEST"] += 1
                    continue
                market_operations[str(order[0])] += 1
                if len(order) >= 3 and isinstance(order[2], (int, float)):
                    quantities[f"{order[0]}:{order[1]}"] += order[2]
            if step in CHECKPOINTS:
                snapshots[str(step)] = _snapshot(observation, seat)
            if step < 24:
                # Exclude execution time, which is not a game-state variable.
                visible = {k: v for k, v in observation.items() if k != "remainingOverageTime"}
                visible["step"] = step
                encoded = orjson.dumps(visible, option=orjson.OPT_SORT_KEYS)
                history.update(encoded)
                early.append(
                    {
                        "step": step,
                        "observation": fingerprint(visible),
                        "history": history.hexdigest(),
                        "action": hashes[-1][0],
                        "units": hashes[-1][1],
                    }
                )
                history.update(orjson.dumps(action, option=orjson.OPT_SORT_KEYS))
            overage.append(float(observation.get("remainingOverageTime", 60)))
        end = _snapshot(steps[-1][seat]["observation"], seat)
        opponent_money = float(steps[-1][1 - seat]["observation"]["farms"][1 - seat]["money"])
        final_overage = float(steps[-1][seat]["observation"].get("remainingOverageTime", 60))
        rows.append(
            {
                "episode_id": episode_id,
                "date": date,
                "create_time": metadata["create_time"],
                "average_match_rating": metadata["average_score"],
                "name": replay["info"]["TeamNames"][seat],
                "opponent": replay["info"]["TeamNames"][1 - seat],
                "seat": seat,
                "seed": replay["info"]["seed"],
                "module_version": replay["module_version"],
                "configuration_hash": fingerprint(replay["configuration"]),
                "complete": complete,
                "status": replay["statuses"][seat],
                "reward": replay["rewards"][seat],
                "cash": money[-1],
                "cash_margin": money[-1] - opponent_money,
                "result": int(money[-1] > opponent_money) - int(money[-1] < opponent_money),
                "first_action": steps[1][seat]["action"],
                "hashes": hashes,
                "early": early,
                "snapshots": snapshots,
                "terminal": end,
                "unit_operations": dict(unit_operations),
                "market_operations": dict(market_operations),
                "requested_quantities": dict(quantities),
                "all_units_pass_turns": all_pass,
                "overage_spent": max(0.0, overage[0] - final_overage),
                "money_by_game_day": [money[min(d * 24, 719)] for d in range(31)],
            }
        )
    return rows
