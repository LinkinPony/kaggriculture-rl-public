"""Compare opening requests with independently replayed execution and recovery."""

import gzip
import hashlib
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any

import orjson

from kagg_revue.datasets.behavior.extraction import fingerprint, normalized_action
from kagg_revue.datasets.coverage.extraction import snapshot
from kagg_revue.datasets.observations import ReplayObservations, difference
from kagg_revue.native import _revue_core as native

HORIZONS = (1, 2, 4, 12, 24, 48, 72, 144)
PRODUCTS = ("COW", "SHEEP", "GOOSE", "MELON", "WHEAT", "CARROT", "TOMATO", "STRAWBERRY")
FIELDS = ("player", "step", "day", "hour", "farms", "private", "market", "town")


def load(task: dict[str, Any]) -> tuple[dict[str, Any], str]:
    """Read preserved raw data without executing any submitted agent code."""
    path = Path(task["path"])
    if task.get("member"):
        with zipfile.ZipFile(path) as archive:
            raw = archive.read(task["member"])
    else:
        raw = gzip.decompress(path.read_bytes())
    return orjson.loads(raw), hashlib.sha256(raw).hexdigest()


def production(state: dict[str, Any]) -> dict[str, int]:
    """Separate production composition from tiny cash changes and route geometry."""
    return {
        name: state["assets"].get(name, 0)
        + (state["shed"].get(name, 0) if name in PRODUCTS[:3] else 0)
        + state["carried_animals"].get(name, 0)
        for name in PRODUCTS
    }


def recoveries(orders: list[dict[str, Any]], horizon: int) -> list[dict[str, Any]]:
    """Describe bounded procurement deficits and subsequent actual purchases.

    A later purchase covering the deficit is an observed catch-up, not proof of
    intentional recovery or restored counterfactual assets. Oversize sell orders
    and large 'buy as many as possible' requests are excluded from this screen.
    """
    result = []
    for index, order in enumerate(orders):
        request = order["requested"]
        operation = request[0] if request else ""
        if operation not in {"BUY_ANIMAL", "BUY_SEED", "HIRE"}:
            continue
        quantity = request[2] if len(request) >= 3 else 1
        maximum = 10 if operation == "BUY_ANIMAL" else 20
        if not isinstance(quantity, int) or not 0 < quantity <= maximum:
            continue
        deficit = quantity - order["committed"]
        if deficit <= 0 or order["turn"] >= 72:
            continue
        key = request[:2] if operation != "HIRE" else [operation]
        later, covered = 0, None
        for following in orders[index + 1 :]:
            if following["turn"] > order["turn"] + 12:
                break
            if following["turn"] <= order["turn"]:
                continue
            if (following["requested"] or [])[: len(key)] == key:
                later += following["committed"]
                if later >= deficit:
                    covered = following["turn"] - order["turn"]
                    break
        result.append(
            {
                **order,
                "deficit": deficit,
                "followup_purchased_12": later,
                "catchup_turns": covered,
                "followup_complete": order["turn"] + 12 < horizon,
            }
        )
    return result


def extract(task: dict[str, Any]) -> dict[str, Any]:
    """Audit every opening frame and retain diagnostic records for both seats."""
    replay, raw_hash = load(task)
    if (
        replay.get("name") != "kaggriculture"
        or replay.get("module_version") != "1.32.7"
        or len(replay["steps"]) != 720
        or replay["statuses"] != ["DONE", "DONE"]
    ):
        return {"episode_id": task["episode_id"], "rejected": "header_or_completion"}
    if (
        int(replay["info"]["EpisodeId"]) != task["episode_id"]
        or replay["info"]["seed"] != task["seed"]
    ):
        raise ValueError("replay episode identity differs")
    horizon = task["horizon"]
    steps = replay["steps"]
    inactive = [
        [turn, seat, frame[seat]["status"]]
        for turn, frame in enumerate(steps[:-1])
        for seat in (0, 1)
        if frame[seat]["status"] != "ACTIVE"
    ]
    if inactive:
        return {"episode_id": task["episode_id"], "rejected": "inactive", "frames": inactive[:8]}
    engine = native.Engine(replay["info"]["seed"], replay["configuration"])
    sequences = [ReplayObservations(), ReplayObservations()]
    purchases: list[list[dict[str, Any]]] = [[], []]
    executed: list[list[Any]] = [[], []]
    states: list[dict[str, Any]] = [{}, {}]
    histories: list[list[Any]] = [[], []]
    history_hashes = [hashlib.sha256(), hashlib.sha256()]
    actions = [
        [normalized_action(frame[seat]["action"]) for frame in steps[1 : horizon + 1]]
        for seat in (0, 1)
    ]
    for turn in range(horizon + 1):
        for seat in (0, 1):
            expected = sequences[seat].update(steps[turn][seat]["observation"], turn)
            actual = engine.observation(seat)
            mismatch = difference({k: actual[k] for k in FIELDS}, {k: expected[k] for k in FIELDS})
            if mismatch:
                return {
                    "episode_id": task["episode_id"],
                    "rejected": mismatch,
                    "turn": turn,
                    "seat": seat,
                }
            if turn in (0, *HORIZONS):
                states[seat][str(turn)] = snapshot(actual, seat)
                states[seat][str(turn)]["carried_animals"] = {
                    name: sum(
                        inventory.get(name, 0) for inventory in actual["private"]["inventories"]
                    )
                    for name in PRODUCTS[:3]
                }
            if turn < 24:
                visible = {k: expected[k] for k in FIELDS}
                history_hashes[seat].update(orjson.dumps(visible, option=orjson.OPT_SORT_KEYS))
                histories[seat].append(
                    {
                        "turn": turn,
                        "history": history_hashes[seat].hexdigest(),
                        "action": str(fingerprint(actions[seat][turn])),
                    }
                )
                history_hashes[seat].update(
                    orjson.dumps(actions[seat][turn], option=orjson.OPT_SORT_KEYS)
                )
        if turn == horizon:
            break
        trace = engine.step_with_trace(*[steps[turn + 1][s]["action"] for s in (0, 1)])
        applied: list[list[Any]] = [[], []]
        for order in trace["market_trace"]:
            seat = order["player"]
            purchases[seat].append({"turn": turn, **order})
            if order["committed"]:
                applied[seat].append(
                    [order["slot_index"], order["requested"][:2], order["committed"]]
                )
        for seat in (0, 1):
            executed[seat].append(applied[seat])
    rows = []
    for seat in (0, 1):
        own = actions[seat]
        units = [[a["farmer"], *a["hands"]] for a in own]
        channels: dict[str, list[Any]] = {
            "full": own,
            "units": units,
            "market": [a["market"] for a in own],
            "settled_market": executed[seat],
        }
        metadata: dict[str, Any] = next(
            (r for r in task["baseline_seats"] if r["seat"] == seat), {}
        )
        if metadata and metadata["name"] != replay["info"]["TeamNames"][seat]:
            raise ValueError("BC teacher identity differs from source replay")
        cash = [steps[-1][s]["observation"]["farms"][s]["money"] for s in (0, 1)]
        buys = [
            r
            for r in purchases[seat]
            if r["requested"]
            and r["requested"][0] in {"BUY_ANIMAL", "BUY_SEED", "BUY_PRODUCT", "HIRE"}
        ]
        first = own[0]["market"]
        wheat_buy = sum(o[2] for o in first if len(o) >= 3 and o[:2] == ["BUY_PRODUCT", "WHEAT"])
        wheat_sell = sum(o[2] for o in first if len(o) >= 3 and o[:2] == ["SELL", "WHEAT"])
        rows.append(
            {
                "episode_id": task["episode_id"],
                "seat": seat,
                "date": task["date"],
                "daily": task["daily"],
                "seed": replay["info"]["seed"],
                "split": task["split"],
                "name": replay["info"]["TeamNames"][seat],
                "opponent": replay["info"]["TeamNames"][1 - seat],
                "baseline_selected": bool(metadata),
                "submission_id": metadata.get("submission_id"),
                "historical_teacher": any(
                    r["seat"] == seat for r in task.get("historical_teacher_seats", [])
                ),
                "result": int(cash[seat] > cash[1 - seat]) - int(cash[seat] < cash[1 - seat]),
                "cash": cash[seat],
                "opponent_cash": cash[1 - seat],
                "snapshots": states[seat],
                "production": {k: production(v) for k, v in states[seat].items()},
                "prefixes": {
                    c: {str(h): str(fingerprint(v[:h])) for h in HORIZONS if h <= horizon}
                    for c, v in channels.items()
                },
                "first_action": own[0],
                "first_four": own[:4],
                "wheat_buy": wheat_buy,
                "wheat_sell": wheat_sell,
                "wheat_roundtrip_requested": wheat_buy > 0 and wheat_sell > 0,
                "purchases": buys,
                "shortfalls": recoveries(purchases[seat], horizon),
                "hires24": sum(
                    r["committed"] for r in buys if r["turn"] < 24 and r["requested"][0] == "HIRE"
                ),
                "purchase_statuses": dict(Counter(r["status"] for r in buys)),
                "histories": histories[seat],
                "raw_sha256": raw_hash,
            }
        )
    return {"rows": rows, "checked_observations": (horizon + 1) * 2}
