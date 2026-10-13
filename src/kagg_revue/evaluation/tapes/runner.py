"""Isolated interpreter entry: one deployment package against recorded tapes.

Executed by path with a clean environment so the package's own ``kagg_revue``
copy is the only one imported; this file must not import the repository package.
"""

import gzip
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path
from typing import Any


def _tiles(farm: dict[str, Any]) -> str:
    text = json.dumps(farm["tiles"], sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def _game(agent: Any, native: Any, tape: dict[str, Any], checkpoints: set[int]) -> dict[str, Any]:
    engine = native.Engine(int(tape["seed"]), tape["configuration"])
    configuration = engine.configuration
    seat = tape["seat"]
    ours = 1 - seat
    fidelity = {}
    started = time.perf_counter()
    for turn, recorded in enumerate(tape["actions"]):
        actions: list[Any] = [None, None]
        actions[ours] = agent(engine.observation(ours), configuration)
        actions[seat] = recorded
        engine.step(actions[0], actions[1])
        if turn + 1 in checkpoints:
            farm = engine.observation(seat)["farms"][seat]
            reference = tape["recorded"]["checkpoints"][str(turn + 1)]
            fidelity[str(turn + 1)] = {
                "tiles_match": _tiles(farm) == reference["tiles"],
                "money_delta": farm["money"] - reference["money"],
            }
    if not engine.done:
        raise RuntimeError("engine did not finish after the recorded season")
    own, other = engine.money(ours), engine.money(seat)
    return {
        "episode_id": tape["episode_id"],
        "team": tape["team"],
        "submission": tape["submission"],
        "seat": seat,
        "own_money": own,
        "tape_money": other,
        "score": 1.0 if own > other else 0.5 if own == other else 0.0,
        "recorded_rewards": tape["recorded"]["rewards"],
        "opponent_team": tape["recorded"]["opponent_team"],
        "fidelity": fidelity,
        "seconds": time.perf_counter() - started,
    }


def main() -> None:
    """Load the candidate once, play every assigned tape, publish atomically."""
    here = Path(__file__).resolve().parent
    sys.path[:] = [p for p in sys.path if Path(p or ".").resolve() != here]
    task = json.loads(Path(sys.argv[1]).read_text())
    sys.path.insert(0, task["engine"])
    import _revue_native as native  # type: ignore[import-not-found]

    spec = importlib.util.spec_from_file_location(
        "candidate_main", Path(task["package"]) / "main.py"
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load candidate package: {task['package']}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    games = []
    for job in task["jobs"]:
        tape = json.loads(gzip.decompress(Path(job).read_bytes()))
        try:
            games.append(_game(module.agent, native, tape, set(task["checkpoints"])))
        except Exception as error:
            games.append(
                {"episode_id": tape["episode_id"], "seat": tape["seat"], "error": repr(error)}
            )
    output = Path(task["output"])
    temporary = output.with_suffix(".partial")
    temporary.write_text(json.dumps({"label": task["label"], "games": games}))
    temporary.replace(output)


if __name__ == "__main__":
    main()
