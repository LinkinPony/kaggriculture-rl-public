"""Measure SE land from observed states throughout each complete replay prefix."""

import gzip
import hashlib
import zipfile
from pathlib import Path
from typing import Any

import orjson


def analyze(replay: dict[str, Any], task: dict[str, Any]) -> list[dict[str, Any]]:
    """Count unlocking separately from construction, crops, and stocked animals."""
    if replay["name"] != "kaggriculture" or str(replay["info"]["EpisodeId"]) != task["episode_id"]:
        raise ValueError("replay identity or environment mismatch")
    steps = replay["steps"]
    if not steps or any(len(states) != 2 for states in steps):
        raise ValueError("expected nonempty two-seat replay")
    size = int(replay["configuration"]["boardSize"])
    if size % 2 or size < 2:
        raise ValueError("expected an even-sized board")
    midpoint = size // 2
    complete = (
        replay["statuses"] == ["DONE", "DONE"]
        and len(steps) == replay["configuration"]["episodeSteps"]
    )
    rows = []
    for seat in (0, 1):
        first: dict[str, int | None] = dict.fromkeys(("unlocked", "developed", "productive"))
        frames = {key: 0 for key in first}
        decisions = {key: 0 for key in first}
        types: set[str] = set()
        maximum = 0
        for step, states in enumerate(steps):
            observation = states[seat]["observation"]
            farm = observation["farms"][seat]
            if "SE" not in farm["unlocked_quadrants"]:
                if first["unlocked"] is not None:
                    raise ValueError("land became locked again")
                continue
            if len(farm["tiles"]) != size or any(len(row) != size for row in farm["tiles"]):
                raise ValueError("tile dimensions differ from configuration")
            developed = productive = 0
            for row in farm["tiles"][midpoint:]:
                for tile in row[midpoint:]:
                    if not isinstance(tile, dict):
                        continue
                    kind = tile.get("kind")
                    developed += kind in {"PLANT", "COOP", "PASTURE"}
                    used = kind == "PLANT" or (
                        kind in {"COOP", "PASTURE"} and bool(tile.get("animal"))
                    )
                    productive += used
                    if used:
                        types.add(str(tile.get("crop") or tile.get("animal")))
            maximum = max(maximum, productive)
            values = {"unlocked": True, "developed": developed > 0, "productive": productive > 0}
            for key, present in values.items():
                if present:
                    if first[key] is None:
                        first[key] = step
                    frames[key] += 1
                    decisions[key] += step < len(steps) - 1 and states[seat]["status"] == "ACTIVE"
        rows.append(
            {
                "episode_id": task["episode_id"],
                "date": task["date"],
                "source": task["source"],
                "seat": seat,
                "name": replay["info"]["TeamNames"][seat],
                "opponent": replay["info"]["TeamNames"][1 - seat],
                "complete": complete,
                "status": replay["statuses"][seat],
                "frames": len(steps),
                "module_version": replay["module_version"],
                "seed": replay["info"].get("seed"),
                "path": task["path"],
                "member": task["member"],
                **{f"se_{key}": value is not None for key, value in first.items()},
                **{f"first_{key}_step": value for key, value in first.items()},
                **{f"{key}_frames": value for key, value in frames.items()},
                **{f"{key}_decision_turns": value for key, value in decisions.items()},
                "maximum_productive_tiles": maximum,
                "production_types": sorted(types),
            }
        )
    return rows


def extract(task: dict[str, Any]) -> dict[str, Any]:
    """Read one canonical source and return auditable statistics or an explicit error."""
    try:
        path = Path(task["path"])
        if task["member"]:
            with zipfile.ZipFile(path) as archive:
                raw = archive.read(task["member"])
        elif path.suffix == ".gz":
            with gzip.open(path, "rb") as stream:
                raw = stream.read()
        else:
            raw = path.read_bytes()
        replay = orjson.loads(raw)
        rows = analyze(replay, task)
        return {
            "episode_id": task["episode_id"],
            "raw_sha256": hashlib.sha256(raw).hexdigest(),
            "rows": rows,
        }
    except Exception as error:
        return {
            "episode_id": task["episode_id"],
            "path": task["path"],
            "member": task["member"],
            "error": f"{type(error).__name__}: {error}",
        }
