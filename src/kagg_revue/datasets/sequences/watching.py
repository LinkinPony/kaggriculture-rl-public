"""Select teacher seats from immutable snapshots of continuous replay collectors."""

import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from kagg_revue.artifacts.io import digest
from kagg_revue.datasets.exclusions import EXCLUDED_SUBMISSIONS
from kagg_revue.datasets.openings.catalog import partition
from kagg_revue.datasets.ranked.metadata import replay_header


def _seats(manifest: dict[str, Any], episode: dict[str, Any]) -> list[dict[str, Any]]:
    """Respect each collector's active submission scope, including fixed cutoffs."""
    submissions = {s["id"]: s for s in manifest["submissions"]}
    cutoff = manifest["configuration"].get("submitted_since")
    if cutoff and any(
        datetime.fromisoformat(s["dateSubmitted"]) < datetime.fromisoformat(cutoff)
        for s in submissions.values()
    ):
        raise ValueError("active collector submissions violate their fixed date cutoff")
    result = []
    for agent in episode["agents"]:
        if agent.get("teamId") != manifest["team_id"]:
            continue
        if agent["submissionId"] not in submissions:
            continue
        result.append(
            {
                "seat": int(agent.get("index", 0)),
                "name": agent["teamName"],
                "teacher_name": manifest["team_name"],
                "team_id": manifest["team_id"],
                "submission_id": agent["submissionId"],
            }
        )
    if not result or len({s["seat"] for s in result}) != len(result):
        raise ValueError("collector episode lacks unambiguous in-scope teacher seats")
    return result


def catalog(
    paths: tuple[Path, ...], teachers: tuple[str, ...], partition_seed: int
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    """Deduplicate games, retaining only seats selected by their own collector."""
    manifests = [json.loads(path.read_text()) for path in paths]
    if len({m["team_id"] for m in manifests}) != len(manifests) or {
        m["team_name"] for m in manifests
    } != set(teachers):
        raise ValueError("collector snapshots must match the requested distinct teachers")
    excluded = EXCLUDED_SUBMISSIONS | {
        s for m in manifests for s in m.get("excluded_submissions", [])
    }
    excluded_episodes = {e for m in manifests for e in m.get("excluded_episode_ids", [])}
    selected: dict[int, dict[str, Any]] = {}
    sources = []
    for path, manifest in zip(paths, manifests, strict=True):
        episodes = {e["id"]: e for e in manifest["episodes"]}
        replays = {r["episode_id"]: r for r in manifest["replays"]}
        if len(replays) != len(manifest["replays"]) or episodes.keys() != replays.keys():
            raise ValueError("freeze a collector snapshot only after its download backlog clears")
        sources.append(
            {
                "path": str(path),
                "sha256": digest(path),
                "team_id": manifest["team_id"],
                "team_name": manifest["team_name"],
                "updated_utc": manifest["updated_utc"],
                "episodes": len(episodes),
                "submissions": sorted(s["id"] for s in manifest["submissions"]),
                "configuration": manifest["configuration"],
            }
        )
        for key, episode in episodes.items():
            if key in excluded_episodes or any(
                a["submissionId"] in excluded for a in episode["agents"]
            ):
                raise ValueError("excluded submission or episode reappeared in active data")
            seats = _seats(manifest, episode)
            previous = selected.get(key)
            if previous is not None:
                if previous["agent_identity"] != episode["agents"]:
                    raise ValueError("collectors disagree about shared episode identities")
                for seat in seats:
                    existing = [s for s in previous["seats"] if s["seat"] == seat["seat"]]
                    if existing and existing != [seat]:
                        raise ValueError("shared teacher seat identity differs")
                    if not existing:
                        previous["seats"].append(seat)
                previous["seats"].sort(key=lambda s: s["seat"])
                continue
            record = replays[key]
            source = Path(record["path"])
            daily = record.get("storage") == "daily_zip"
            header = replay_header(source, record["member"] if daily else None)
            info = header["info"]
            if any(info["TeamNames"][s["seat"]] != s["name"] for s in seats):
                raise ValueError("official metadata and replay teacher seats disagree")
            provenance = (
                {
                    "storage": "daily_zip",
                    "member_crc32": record["member_crc32"],
                    "raw_bytes": record["raw_bytes"],
                }
                if daily
                else {
                    "storage": "gzip",
                    "compressed_sha256": record["sha256"],
                    "raw_sha256": json.loads(Path(record["source"]).read_text())["raw_sha256"],
                    "download_source": record["source"],
                }
            )
            selected[key] = {
                "episode_id": key,
                "path": str(source),
                "member": record["member"] if daily else f"{key}.json",
                "date": episode["createTime"][:10],
                "create_time": episode["createTime"],
                "average_score": None,
                "minimum_score": None,
                "seats": seats,
                "seed": info["seed"],
                "split": partition(info["seed"], partition_seed),
                "agent_identity": episode["agents"],
                **provenance,
            }
    tasks = sorted(selected.values(), key=lambda t: t["episode_id"])
    counts = Counter(s["teacher_name"] for t in tasks for s in t["seats"])
    return (
        tasks,
        {
            "collector_snapshots": sources,
            "episodes": len(tasks),
            "dates": sorted({t["date"] for t in tasks}),
        },
        {
            "teacher_selection": {
                "method": "collector-team-id-and-active-submission",
                "names": list(teachers),
                "excluded_submissions": sorted(excluded),
                "matching": "official agent teamId/index/submissionId; each collector's scope",
            },
            "selected_teacher_trajectories": dict(sorted(counts.items())),
        },
    )
