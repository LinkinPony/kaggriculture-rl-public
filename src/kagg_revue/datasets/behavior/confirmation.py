"""Confirm selected public controllers on their observed replay state streams."""

import zipfile
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

import orjson

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.datasets.behavior.extraction import normalized_action
from kagg_revue.opponents.native_batch import create_native_opponent_session
from kagg_revue.opponents.portfolios.native import ASSET_SHA256, native_action


def _confirm(task: dict[str, Any]) -> dict[str, Any]:
    from kagg_revue.native import _revue_native as native

    with zipfile.ZipFile(task["archive"]) as archive:
        replay = orjson.loads(archive.read(f"{task['episode_id']}.json"))
    engine = native.Engine(replay["info"]["seed"], replay["configuration"])
    session = create_native_opponent_session(task["reference"], 10)
    matches: dict[str, int] = defaultdict(int)
    first_mismatch = None
    state_checks = 0
    seat = task["seat"]
    for step in range(719):
        if step % 72 == 0:
            actual_state = engine.observation(seat)
            expected_state = replay["steps"][step][seat]["observation"]
            for key in ("farms", "market", "town", "private"):
                if actual_state[key] != expected_state[key]:
                    raise ValueError(f"native replay state mismatch at {step}: {key}")
            state_checks += 1
        recorded = replay["steps"][step + 1][seat]["action"]
        proposed = native_action(session, engine, seat)
        matches["raw_normalized"] += normalized_action(recorded) == normalized_action(proposed)
        expected = normalized_action(native.canonical_opponent_action(recorded, 10))
        actual = normalized_action(native.canonical_opponent_action(proposed, 10))
        # The native parser has already applied the market-order cap. Empty
        # commands within that cap have no effect and can now be discarded.
        expected["market"] = [command for command in expected["market"] if command]
        actual["market"] = [command for command in actual["market"] if command]
        for key in ("farmer", "hands", "market"):
            matches[key] += actual[key] == expected[key]
        matches["full"] += actual == expected
        if actual != expected and first_mismatch is None:
            first_mismatch = {"step": step, "expected": expected, "actual": actual}
        engine.step(*(state["action"] for state in replay["steps"][step + 1]))
    for player in (0, 1):
        if (
            engine.money(player)
            != replay["steps"][-1][player]["observation"]["farms"][player]["money"]
        ):
            raise ValueError("native terminal cash differs from the official replay")
    return {
        **task,
        "matches": dict(matches),
        "turns": 719,
        "all_actions_identical": matches["full"] == 719,
        "checked_state_frames": state_checks,
        "first_mismatch": first_mismatch,
    }


def confirm(output: Path, workers: int) -> dict[str, Any]:
    """Test each >=95%-covered group's closest active controller on all its games."""
    report = orjson.loads((output / "report.json").read_bytes())
    overlap = orjson.loads((output / "route-overlap.json").read_bytes())
    trajectories = orjson.loads((output / "trajectories.json").read_bytes())
    dates = {(row["episode_id"], row["seat"]): row["date"] for row in trajectories}
    sources = orjson.loads((output / "sources.json").read_bytes())
    archives = {row["date"]: row["path"] for row in sources["daily_archives"]}
    teams = {team["name"] for team in report["teams"] if team["category"] == "public_route_family"}
    tasks = []
    for row in overlap:
        reference = row["best_reference"].split(":")[0]
        if row["name"] in teams and reference in ASSET_SHA256:
            tasks.append(
                {
                    "episode_id": row["episode_id"],
                    "seat": row["seat"],
                    "name": row["name"],
                    "reference": reference,
                    "archive": archives[dates[(row["episode_id"], row["seat"])]],
                }
            )
    with ProcessPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(_confirm, tasks))
    summary = []
    for name in sorted(teams):
        selected = [row for row in results if row["name"] == name]
        if not selected:
            continue
        summary.append(
            {
                "name": name,
                "trajectories": len(selected),
                "complete_action_matches": sum(row["all_actions_identical"] for row in selected),
                "action_agreement": sum(row["matches"]["full"] for row in selected)
                / (719 * len(selected)),
                "references": sorted({row["reference"] for row in selected}),
            }
        )
    from kagg_revue.native import _revue_native as native

    result = {
        "selection": "all >=10-game groups with >=95% median public-route union overlap",
        "method": "Native controller consumes recorded states; engine advances recorded actions. "
        "Native canonicalization resolves default quantities and applies the order cap before "
        "discarding empty commands. Complete matches establish behavior, not code identity.",
        "native_sha256": digest(Path(native.__file__)),
        "asset_sha256": ASSET_SHA256,
        "summary": summary,
        "results": results,
    }
    write_json(output / "native-confirmation.json", result)
    return result
