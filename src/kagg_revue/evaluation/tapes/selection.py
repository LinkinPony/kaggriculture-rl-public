"""Freeze recorded strong-team seats from the watched collectors as open-loop tapes."""

import gzip
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.evaluation.tapes.config import Tapes

TURNS = 719


def tiles_key(farm: dict[str, Any]) -> str:
    """Short identity of a farm grid for recorded-versus-replayed comparisons."""
    text = json.dumps(farm["tiles"], sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def _rank(salt: str, episode: int) -> bytes:
    return hashlib.sha256(f"{salt}:{episode}".encode()).digest()


def _tape(
    row: dict[str, Any],
    episode: dict[str, Any],
    seat: int,
    team: str,
    checkpoints: tuple[int, ...],
) -> dict[str, Any]:
    path = Path(row["path"])
    if digest(path) != row["sha256"]:
        raise ValueError(f"replay bytes differ from collector manifest: {path}")
    replay = json.loads(gzip.decompress(path.read_bytes()))
    steps = replay["steps"]
    if len(steps) != TURNS + 1 or replay["statuses"] != ["DONE", "DONE"]:
        raise ValueError(f"incomplete official episode: {episode['id']}")
    if replay["info"]["TeamNames"][seat] != team:
        raise ValueError(f"seat order disagrees with team names: {episode['id']}")
    other = episode["agents"][1 - seat]
    return {
        "episode_id": episode["id"],
        "team": team,
        "submission": episode["agents"][seat]["submissionId"],
        "seat": seat,
        "seed": replay["info"]["seed"],
        "configuration": replay["configuration"],
        "actions": [steps[turn + 1][seat]["action"] for turn in range(TURNS)],
        "recorded": {
            "rewards": replay["rewards"],
            "opponent_team": other.get("teamName"),
            "opponent_submission": other["submissionId"],
            "checkpoints": {
                str(step): {
                    "money": steps[step][0]["observation"]["farms"][seat]["money"],
                    "tiles": tiles_key(steps[step][0]["observation"]["farms"][seat]),
                }
                for step in checkpoints
            },
        },
        "source": {"path": str(path), "sha256": row["sha256"]},
    }


def freeze(options: Tapes, output: Path, checkpoints: tuple[int, ...]) -> Path:
    """Select recorded games by a salted hash only; never by outcome or opponent."""
    target = output / "tapes" / "selection.json"
    if target.exists():
        return target
    rows: list[dict[str, Any]] = []
    sources = []
    for source in options.manifests:
        manifest = json.loads(source.read_text())
        sources.append({"path": str(source), "sha256": digest(source)})
        replays = {row["episode_id"]: row for row in manifest["replays"]}
        for submission in options.submissions:
            games = []
            for episode in manifest["episodes"]:
                agents = episode["agents"]
                seats = [
                    index
                    for index, agent in enumerate(agents)
                    if agent["submissionId"] == submission
                    and agent.get("teamId") == manifest["team_id"]
                ]
                if (
                    len(agents) == 2
                    and len(seats) == 1
                    and episode.get("state") == "COMPLETED"
                    and episode["id"] in replays
                    and replays[episode["id"]]["statuses"] == ["DONE", "DONE"]
                ):
                    games.append((episode, seats[0]))
            games.sort(key=lambda item: _rank(options.salt, item[0]["id"]))
            for episode, seat in games[: options.games_per_submission]:
                tape = _tape(
                    replays[episode["id"]], episode, seat, manifest["team_name"], checkpoints
                )
                path = output / "tapes" / f"{episode['id']}-{seat}.json.gz"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(gzip.compress(json.dumps(tape).encode()))
                rows.append(
                    {key: tape[key] for key in ("episode_id", "team", "submission", "seat", "seed")}
                    | {"path": str(path), "sha256": digest(path)}
                )
    missing = set(options.submissions) - {row["submission"] for row in rows}
    if missing:
        raise ValueError(f"no complete recorded games for submissions: {sorted(missing)}")
    write_json(
        target,
        {
            "created_utc": datetime.now(UTC).isoformat(),
            "sources": sources,
            "options": options.model_dump(mode="json"),
            "tapes": rows,
        },
    )
    return target
