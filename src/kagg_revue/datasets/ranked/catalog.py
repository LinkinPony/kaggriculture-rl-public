"""Select daily teachers from recorded top-ten evidence and deduplicate supplements."""

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.bc.replay import daily_episode_metadata
from kagg_revue.datasets.ranked.config import Preparation
from kagg_revue.datasets.ranked.metadata import replay_header


def ranking_evidence(paths: tuple[Path, ...], maximum_rank: int) -> dict[str, Any]:
    """Union exact team IDs and observed aliases; do not invent historical ranks."""
    teams: dict[int, Any] = {}
    observed_names: dict[int, set[str]] = {}
    for path in paths:
        board = json.loads(path.read_text())
        rows = board.get("rows", board.get("submissions", []))
        for index, row in enumerate(rows, 1):
            rank = int(row.get("rank", index))
            team_id = int(row.get("teamId", row.get("team_id")))
            name = str(row.get("teamName", row.get("team_name")))
            observed_names.setdefault(team_id, set()).add(name)
            if rank > maximum_rank:
                continue
            team = teams.setdefault(team_id, {"team_id": team_id, "names": [], "evidence": []})
            if name not in team["names"]:
                team["names"].append(name)
            team["evidence"].append({"path": str(path), "rank": rank, "sha256": digest(path)})
    aliases: dict[str, int] = {}
    for team in teams.values():
        team["names"] = sorted(observed_names[team["team_id"]])
        for name in team["names"]:
            if aliases.setdefault(name, team["team_id"]) != team["team_id"]:
                raise ValueError(f"ambiguous historical team display name: {name}")
    for team_id, names in observed_names.items():
        if any(name in aliases and aliases[name] != team_id for name in names):
            raise ValueError("another observed team shares a qualified teacher's display name")
    return {
        "teams": list(teams.values()),
        "aliases": aliases,
        "history_complete": False,
        "scope": "Historical top-ten membership is proven only at the supplied snapshots. "
        "Kaggle's current leaderboard and public submission listings do not expose complete "
        "historical ranks. Unproven daily teachers are retained in the exclusion catalog, "
        "not asserted never to have reached the top ten. Daily names identify teams, not versions.",
    }


def catalog(config: Preparation) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Choose seats before observing rewards and preserve every exclusion reason."""
    evidence = ranking_evidence(config.leaderboard_snapshots, config.maximum_rank)
    daily = json.loads(config.daily_manifest.read_text())
    public = json.loads(config.public_manifest.read_text())
    if public["failures"] or public["daily_manifest_sha256"] != digest(config.daily_manifest):
        raise ValueError("public acquisition is incomplete or belongs to different daily sources")
    selected, excluded = [], []
    seen: set[int] = set()
    all_daily: set[int] = set()
    qualified = {row["id"] for row in public["submissions"]}
    for source in daily["daily_archives"]:
        path = Path(source["path"])
        if digest(path) != source["sha256"]:
            raise ValueError("daily source fingerprint changed")
        for key in daily_episode_metadata(path):
            episode_id = int(key)
            if episode_id in all_daily:
                raise ValueError("daily archives repeat an episode")
            all_daily.add(episode_id)
            info = replay_header(path, f"{key}.json")["info"]
            seats = []
            for seat, name in enumerate(info["TeamNames"]):
                if name in evidence["aliases"]:
                    seats.append(
                        {
                            "seat": seat,
                            "name": name,
                            "team_id": evidence["aliases"][name],
                            "submission_id": None,
                            "weight": 1.0,
                        }
                    )
                else:
                    excluded.append(
                        {
                            "episode_id": episode_id,
                            "date": source["date"],
                            "seat": seat,
                            "name": name,
                            "reason": "no_top10_evidence_in_available_snapshots",
                        }
                    )
            if seats:
                selected.append(
                    {
                        "episode_id": episode_id,
                        "path": str(path),
                        "member": f"{key}.json",
                        "date": source["date"],
                        "source": "daily",
                        "seed": info["seed"],
                        "seats": seats,
                    }
                )
                seen.add(episode_id)
    metadata = {row["id"]: row for row in public["episodes"]}
    replay_ids = {row["episode_id"] for row in public["replays"]}
    if replay_ids != metadata.keys() - all_daily:
        raise ValueError("public replay coverage differs from the complete frozen selection")
    authenticated: set[Path] = set()
    for record in public["replays"]:
        path = Path(record["path"])
        if path not in authenticated and digest(path) != record["sha256"]:
            raise ValueError("public replay fingerprint changed")
        authenticated.add(path)
        episode = metadata[record["episode_id"]]
        replay = replay_header(path, record.get("member"))
        if replay["statuses"] != ["DONE", "DONE"]:
            excluded.append({"episode_id": episode["id"], "reason": "incomplete_replay_status"})
            continue
        seats = [
            {
                "seat": agent.get("index", 0),
                "name": replay["info"]["TeamNames"][agent.get("index", 0)],
                "api_name": agent["teamName"],
                "team_id": agent["teamId"],
                "submission_id": agent["submissionId"],
                "weight": 1.0,
            }
            for agent in episode["agents"]
            if agent["submissionId"] in qualified
        ]
        if not seats or episode["id"] in seen:
            raise ValueError("public supplement has no qualified teacher or repeats an episode")
        selected.append(
            {
                "episode_id": episode["id"],
                "path": str(path),
                "member": record.get("member"),
                "date": episode["createTime"][:10],
                "source": "public_supplement",
                "seed": replay["info"]["seed"],
                "seats": seats,
            }
        )
        seen.add(episode["id"])
    for task in selected:
        bucket = (
            int.from_bytes(
                hashlib.sha256(f"{config.partition_seed}:{task['seed']}".encode()).digest()[:8],
                "big",
            )
            % 10000
        )
        task["split"] = (
            "train" if bucket < 9000 else "selection" if bucket < 9500 else "confirmation"
        )
    source_catalog = config.report_dir / "source-catalog.json"
    write_json(source_catalog, selected)
    raw_selected = len(selected)
    quality_excluded: list[dict[str, Any]] = []
    if config.frame_audit is not None:
        audit = json.loads(config.frame_audit.read_text())
        if audit["catalog_sha256"] != digest(source_catalog) or audit["episodes"] != len(selected):
            raise ValueError("frame audit does not authenticate the complete source catalog")
        invalid = {record["episode_id"] for record in audit["invalid"] if record["inactive"]}
        for task in selected:
            if task["episode_id"] in invalid:
                quality_excluded.append({**task, "reason": "inactive_source_trajectory"})
        selected = [task for task in selected if task["episode_id"] not in invalid]
        excluded.extend(quality_excluded)
    screening = {
        "ranking_evidence": evidence,
        "daily_episodes": len(all_daily),
        "selected_episodes": len(selected),
        "raw_selected_episodes": raw_selected,
        "quality_excluded_episodes": len(quality_excluded),
        "quality_excluded_trajectories": sum(len(task["seats"]) for task in quality_excluded),
        "selected_trajectories": sum(len(task["seats"]) for task in selected),
        "source_episodes": dict(Counter(task["source"] for task in selected)),
        "excluded": excluded,
        "sampling": "All retained rows have equal weight; no outcome filtering or resampling.",
    }
    config.report_dir.mkdir(parents=True, exist_ok=True)
    write_json(config.report_dir / "catalog.json", selected)
    write_json(config.report_dir / "screening.json", screening)
    return selected, screening
