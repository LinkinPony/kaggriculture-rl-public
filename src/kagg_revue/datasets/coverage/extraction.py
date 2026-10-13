"""Compare quantities, visible histories and settled opening purchases."""

import gzip
import hashlib
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any

import orjson

from kagg_revue.datasets.behavior.extraction import fingerprint, normalized_action
from kagg_revue.native import _revue_core as native

HORIZONS = (1, 2, 4, 12, 24, 72)


def snapshot(observation: dict[str, Any], seat: int) -> dict[str, Any]:
    """Describe actual production assets, including undeployed animals."""
    farm = observation["farms"][seat]
    assets = Counter(
        str(tile.get("crop") or tile.get("animal") or tile["kind"])
        for row in farm["tiles"]
        for tile in row
        if isinstance(tile, dict)
    )
    return {
        "cash": farm["money"],
        "assets": dict(assets),
        "hands": len(farm["hands"]),
        "shed": observation["private"]["shed"],
        "seeds": observation["private"]["seeds"],
        "wheat_inventory": observation["market"]["inventory"]["WHEAT"],
        "shops": observation["town"]["unlocked_shops"],
    }


def extract(task: dict[str, Any]) -> list[dict[str, Any]]:
    """Load one source replay and align each request with the preceding state."""
    path = Path(task["path"])
    if task.get("member"):
        with zipfile.ZipFile(path) as archive:
            replay = orjson.loads(archive.read(task["member"]))
    else:
        replay = orjson.loads(gzip.decompress(path.read_bytes()))
    if replay["name"] != "kaggriculture" or len(replay["steps"]) != 720:
        return [{"rejected": task["episode_id"], "reason": "environment_or_length"}]
    if replay["statuses"] != ["DONE", "DONE"]:
        return [{"rejected": task["episode_id"], "reason": "incomplete"}]
    steps = replay["steps"]
    engine = native.Engine(replay["info"]["seed"], replay["configuration"])
    purchases: list[list[dict[str, Any]]] = [[], []]
    settled = True
    for turn in range(4):
        trace = engine.step_with_trace(*[steps[turn + 1][s]["action"] for s in (0, 1)])
        for seat in (0, 1):
            actual = engine.observation(seat)
            expected = steps[turn + 1][seat]["observation"]
            settled &= all(actual[k] == expected[k] for k in ("farms", "private", "market", "town"))
        for order in trace["market_trace"]:
            request = order["requested"]
            if request and isinstance(request[0], str) and request[0].startswith("BUY_"):
                purchases[order["player"]].append({"turn": turn, **order})
    rows = []
    for seat in (0, 1):
        actions = [normalized_action(frame[seat]["action"]) for frame in steps[1:73]]
        units = [[a["farmer"], *a["hands"]] for a in actions]
        market = [a["market"] for a in actions]
        structure = [
            [
                [["Q" if isinstance(v, (float, int)) else v for v in command] for command in group]
                for group in (unit, orders)
            ]
            for unit, orders in zip(units, market, strict=True)
        ]
        history = hashlib.sha256()
        early = []
        for turn in range(12):
            observation = {
                k: v
                for k, v in steps[turn][seat]["observation"].items()
                if k != "remainingOverageTime"
            }
            observation["step"] = turn
            history.update(orjson.dumps(observation, option=orjson.OPT_SORT_KEYS))
            early.append(
                {
                    "observation": str(fingerprint(observation)),
                    "history": history.hexdigest(),
                    "action": str(fingerprint(actions[turn])),
                }
            )
            history.update(orjson.dumps(actions[turn], option=orjson.OPT_SORT_KEYS))
        agents = task.get("agents", [])
        agent: dict[str, Any] = next((a for a in agents if a.get("index", 0) == seat), {})
        observations = {
            str(t): snapshot(steps[t][seat]["observation"], seat)
            for t in (0, 1, 2, 4, 12, 24, 72, 144, 360, 719)
        }
        cash = observations["719"]["cash"]
        opponent_cash = steps[-1][seat]["observation"]["farms"][1 - seat]["money"]
        result = int(cash > opponent_cash) - int(cash < opponent_cash)
        channels: list[tuple[str, Any]] = [
            ("full", actions),
            ("units", units),
            ("market", market),
            ("structure", structure),
        ]
        rows.append(
            {
                "episode_id": task["episode_id"],
                "source": task["source"],
                "date": task["date"],
                "split": task.get("split", "unassigned"),
                "seat": seat,
                "seed": replay["info"]["seed"],
                "version": replay["module_version"],
                "name": replay["info"]["TeamNames"][seat],
                "opponent": replay["info"]["TeamNames"][1 - seat],
                "submission_id": agent.get("submissionId"),
                "team_id": agent.get("teamId"),
                "result": result,
                "cash": cash,
                "margin": cash - opponent_cash,
                "prefixes": {
                    channel: {str(h): str(fingerprint(values[:h])) for h in HORIZONS}
                    for channel, values in channels
                },
                "early": early,
                "first_actions": actions[:4],
                "snapshots": observations,
                "purchases": purchases[seat],
                "native_first_four_exact": settled,
            }
        )
    return rows
