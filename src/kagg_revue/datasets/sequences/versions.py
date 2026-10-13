"""Freeze teacher versions chosen by measured strength from collector snapshots."""

import json
from collections import Counter
from pathlib import Path
from typing import Any

import hydra
from omegaconf import DictConfig, OmegaConf
from pydantic import AwareDatetime, Field

from kagg_revue.artifacts.io import digest
from kagg_revue.configuration import FrozenSettings
from kagg_revue.datasets.exclusions import EXCLUDED_SUBMISSIONS
from kagg_revue.datasets.sequences.cohort import _publish
from kagg_revue.datasets.sequences.collected import _snapshot
from kagg_revue.datasets.sequences.strength import outcomes, ratings, select
from kagg_revue.datasets.sequences.window import _timestamp


class VersionSettings(FrozenSettings):
    """Rate every collected team, then admit only recent versions near the best."""

    output: Path
    sources: dict[str, Path] = Field(min_length=1)
    rated_since: AwareDatetime
    submitted_since: AwareDatetime
    margin: float = Field(gt=0, allow_inf_nan=False)
    uncertainty: float = Field(default=2.0, ge=0, allow_inf_nan=False)
    precision: float = Field(default=0.25, gt=0, allow_inf_nan=False)
    excluded_submissions: tuple[int, ...] = ()


def _record(games: list[tuple[int, int, float]], key: int) -> dict[str, float]:
    """Summarize the decisive games that entered one version's rating."""
    played = [game for game in games if key in game[:2]]
    wins = sum(game[2] if game[0] == key else 1 - game[2] for game in played)
    return {"decisive_games": len(played), "wins": wins}


def _team_manifest(
    manifest: dict[str, Any],
    chosen: dict[int, list[str]],
    blocked: set[int],
    excluded: set[int],
) -> tuple[dict[str, Any], list[int]]:
    """Retain downloaded games of chosen versions; report the undownloaded remainder."""
    team = manifest["team_id"]
    versions = [
        {**row, "selection_reasons": chosen[row["id"]]}
        for row in manifest["submissions"]
        if row["id"] in chosen
    ]
    active = {row["id"] for row in versions}
    replays = {row["episode_id"]: row for row in manifest["replays"]}
    matching = [
        episode
        for episode in manifest["episodes"]
        if episode["id"] not in blocked
        and episode.get("state") == "COMPLETED"
        and episode.get("type") == "EPISODE_TYPE_PUBLIC"
        and any(a.get("teamId") == team and a["submissionId"] in active for a in episode["agents"])
    ]
    available = [episode for episode in matching if episode["id"] in replays]
    selected = {
        "schema": "watched-team-replays-v1",
        **{key: manifest[key] for key in ("team_id", "team_name", "updated_utc", "configuration")},
        "scope": "Strength-selected versions; every downloaded game of those versions.",
        "submissions": versions,
        "episodes": available,
        "replays": [replays[episode["id"]] for episode in available],
        "excluded_submissions": sorted(excluded),
        "excluded_episode_ids": sorted(blocked),
        "pending_episode_ids": [],
    }
    return selected, sorted(e["id"] for e in matching if e["id"] not in replays)


def freeze(config: VersionSettings) -> dict[str, Any]:
    """Publish immutable per-team selections and the complete rating evidence."""
    _publish(config.output / "configuration.json", config.model_dump(mode="json"))
    snapshots = {}
    for name, source in config.sources.items():
        if not name or Path(name).name != name or name in {".", ".."}:
            raise ValueError("collector names must be simple directory names")
        snapshots[name] = _snapshot(source, config.output / name / "collector-original.json")
    if len({m["team_id"] for m in snapshots.values()}) != len(snapshots):
        raise ValueError("collector snapshots must identify distinct teams")
    excluded = (
        set(EXCLUDED_SUBMISSIONS)
        | set(config.excluded_submissions)
        | {key for m in snapshots.values() for key in m.get("excluded_submissions", [])}
    )
    blocked = {key for m in snapshots.values() for key in m.get("excluded_episode_ids", [])}
    blocked |= {
        e["id"]
        for m in snapshots.values()
        for e in m["episodes"]
        if any(a["submissionId"] in excluded for a in e["agents"])
    }
    games = outcomes(snapshots.values(), config.rated_since, excluded)
    strength = ratings(games, config.precision)
    candidates = {
        row["id"]: {"team": name, **row}
        for name, manifest in snapshots.items()
        for row in manifest["submissions"]
        if row["id"] not in excluded
        and row.get("dateSubmitted")
        and _timestamp(row["dateSubmitted"]) >= config.submitted_since
    }
    chosen, threshold = select(candidates, strength, config.margin, config.uncertainty)
    reports = []
    for name, manifest in snapshots.items():
        if not any(candidates[key]["team"] == name for key in chosen):
            continue
        selected, missing = _team_manifest(manifest, chosen, blocked, excluded)
        target = config.output / name / "selected.json"
        _publish(target, selected)
        seats = Counter(
            a["submissionId"]
            for e in selected["episodes"]
            for a in e["agents"]
            if a.get("teamId") == manifest["team_id"] and a["submissionId"] in chosen
        )
        reports.append(
            {
                "name": name,
                "team_name": manifest["team_name"],
                "snapshot_utc": manifest["updated_utc"],
                "original_sha256": digest(config.output / name / "collector-original.json"),
                "selected_manifest": str(target),
                "selected_sha256": digest(target),
                "episodes": len(selected["episodes"]),
                "teacher_trajectories": dict(sorted(seats.items())),
                "not_downloaded_episode_ids": missing,
            }
        )
    table = [
        {
            "submission_id": key,
            "team": row["team"],
            "date_submitted": row["dateSubmitted"],
            "public_score": row.get("publicScore"),
            "strength": strength[key][0] if key in strength else None,
            "deviation": strength[key][1] if key in strength else None,
            **(_record(games, key) if key in strength else {}),
            "selection_reasons": chosen.get(key, []),
        }
        for key, row in candidates.items()
    ]
    table.sort(key=lambda row: -(row["strength"] if row["strength"] is not None else -1e9))
    report: dict[str, Any] = json.loads(
        json.dumps(
            {
                "configuration": config.model_dump(mode="json"),
                "rating_model": {
                    "kind": "bradley_terry_logit",
                    "prior_precision": config.precision,
                    "decisive_games": len(games),
                    "rated_submissions": len(strength),
                    "deviation": "diagonal posterior curvature",
                },
                "threshold": threshold,
                "candidates": table,
                "sources": reports,
                "snapshot_sha256": {
                    name: digest(config.output / name / "collector-original.json")
                    for name in snapshots
                },
            }
        )
    )
    _publish(config.output / "selection.json", report)
    return report


@hydra.main(
    version_base=None,
    config_path="../../../../configs",
    config_name="sequences_strength_canonical_20260928",
)
def main(configuration: DictConfig) -> None:
    """Freeze the strength-selected teacher versions for the sequence encoder."""
    config = VersionSettings.model_validate(
        OmegaConf.to_container(configuration.selection, resolve=True)
    )
    report = freeze(config)
    chosen = [row for row in report["candidates"] if row["selection_reasons"]]
    print(json.dumps({"threshold": report["threshold"], "chosen": chosen}), flush=True)


if __name__ == "__main__":
    main()
