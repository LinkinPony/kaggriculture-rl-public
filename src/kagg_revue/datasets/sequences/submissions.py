"""Freeze collected games for current public submissions or a fixed date window."""

import json
from collections import Counter
from pathlib import Path
from typing import Any

import hydra
from omegaconf import DictConfig, OmegaConf
from pydantic import AwareDatetime, Field

from kagg_revue.artifacts.io import digest
from kagg_revue.configuration import FrozenSettings
from kagg_revue.datasets.coverage.acquisition import Client
from kagg_revue.datasets.exclusions import EXCLUDED_SUBMISSIONS
from kagg_revue.datasets.sequences.cohort import _publish
from kagg_revue.datasets.sequences.collected import _snapshot
from kagg_revue.datasets.sequences.window import _timestamp
from kagg_revue.datasets.watching.config import WatchSettings
from kagg_revue.datasets.watching.dates import resolve_dates
from kagg_revue.datasets.watching.scope import known


class SubmissionSettings(FrozenSettings):
    """Pin public-version evidence and an inclusive official submission cutoff."""

    output: Path
    raw: Path
    sources: dict[str, Path] = Field(min_length=1)
    submitted_since: AwareDatetime
    excluded_submissions: tuple[int, ...] = ()


def _inventory(
    snapshots: dict[str, dict[str, Any]], excluded: set[int], blocked: set[int]
) -> tuple[dict[int, Any], dict[int, Any]]:
    """Merge existing payloads across collectors, including preserved older scopes."""
    excluded = excluded | EXCLUDED_SUBMISSIONS
    episodes: dict[int, Any] = {}
    replays: dict[int, Any] = {}
    for manifest in snapshots.values():
        for row in known(manifest, "episodes"):
            key = row["id"]
            if any(a["submissionId"] in excluded for a in row["agents"]):
                blocked.add(key)
            if row.get("state") != "COMPLETED" or row.get("type") != "EPISODE_TYPE_PUBLIC":
                continue
            previous = episodes.get(key)
            if previous is not None and (
                previous["agents"] != row["agents"] or previous["createTime"] != row["createTime"]
            ):
                raise ValueError(f"collectors disagree about episode identity: {key}")
            episodes[key] = row
        for row in known(manifest, "replays"):
            replays.setdefault(row["episode_id"], row)
    return (
        {key: row for key, row in episodes.items() if key not in blocked},
        {key: row for key, row in replays.items() if key not in blocked},
    )


def _versions(
    config: SubmissionSettings,
    name: str,
    manifest: dict[str, Any],
    episodes: dict[int, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Authenticate the public list and dates without changing the live collector."""
    directory = config.output / name
    public_path = config.raw / name / "public-submissions.json"
    if not public_path.exists():
        Client().metadata(
            public_path,
            "list_team_public_submissions",
            "ApiListTeamPublicSubmissionsRequest",
            team_id=manifest["team_id"],
        )
    public = _snapshot(public_path, directory / "public-submissions.json")
    source = _snapshot(
        public_path.with_suffix(".source.json"), directory / "public-submissions.source.json"
    )
    if (
        source["method"] != "list_team_public_submissions"
        or source["request"] != {"team_id": manifest["team_id"]}
        or source["sha256"] != digest(directory / "public-submissions.json")
    ):
        raise ValueError("public submission list provenance differs")
    public_ids = {row["id"] for row in public["submissions"]}
    if len(public_ids) != len(public["submissions"]):
        raise ValueError("public submission list has duplicate versions")
    dated_path = directory / "dated-submissions.json"
    if dated_path.exists():
        dated = json.loads(dated_path.read_text())["submissions"]
    else:
        versions = {row["id"]: dict(row) for row in known(manifest, "submissions")}
        for episode in episodes.values():
            for agent in episode["agents"]:
                if agent.get("teamId") == manifest["team_id"]:
                    versions.setdefault(agent["submissionId"], {"id": agent["submissionId"]})
        for row in public["submissions"]:
            versions[row["id"]] = {**versions.get(row["id"], {}), **row}
        options = WatchSettings(
            raw=config.raw / name,
            team_id=manifest["team_id"],
            team_name=manifest["team_name"],
            submitted_since=config.submitted_since,
            excluded_submissions=config.excluded_submissions,
        )
        errors = resolve_dates(options, versions)
        if errors:
            raise ValueError(f"cannot authenticate submission dates: {errors}")
        dated = sorted(versions.values(), key=lambda row: row["id"])
        _publish(dated_path, {"submissions": dated})
    selected = []
    for row in dated:
        reasons = []
        if row["id"] in public_ids:
            reasons.append("current_public")
        if row.get("dateSubmitted") and _timestamp(row["dateSubmitted"]) >= config.submitted_since:
            reasons.append("submitted_since")
        if reasons and row["id"] not in set(config.excluded_submissions) | EXCLUDED_SUBMISSIONS:
            selected.append({**row, "selection_reasons": reasons})
    return selected, {**source, "public_submission_ids": sorted(public_ids)}


def freeze(config: SubmissionSettings) -> dict[str, Any]:
    """Select the union once, preserving all source snapshots and unselected data."""
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
    episodes, replays = _inventory(snapshots, excluded, blocked)
    reports = []
    selected_ids: set[int] = set()
    for name, manifest in snapshots.items():
        versions, public = _versions(config, name, manifest, episodes)
        versions = [row for row in versions if row["id"] not in excluded]
        active = {row["id"] for row in versions}
        matching = {
            key
            for key, row in episodes.items()
            if any(
                a.get("teamId") == manifest["team_id"] and a["submissionId"] in active
                for a in row["agents"]
            )
        }
        available = matching & replays.keys()
        counts = Counter(
            a["submissionId"]
            for key in available
            for a in episodes[key]["agents"]
            if a.get("teamId") == manifest["team_id"] and a["submissionId"] in active
        )
        selected = {
            "schema": "watched-team-replays-v1",
            **{key: manifest[key] for key in ("team_id", "team_name", "updated_utc")},
            # This dataset uses a union, so an old live-collector cutoff cannot apply.
            "configuration": {**manifest["configuration"], "submitted_since": None},
            "scope": "Current public OR official dateSubmitted >= cutoff; collected games only.",
            "submission_selection": {
                "submitted_since_inclusive": config.submitted_since.isoformat(),
                "public_submission_ids": public["public_submission_ids"],
            },
            "submissions": versions,
            "episodes": [episodes[key] for key in sorted(available)],
            "replays": [replays[key] for key in sorted(available)],
            "excluded_submissions": sorted(excluded),
            "excluded_episode_ids": sorted(blocked),
            "pending_episode_ids": [],
        }
        target = config.output / name / "selected.json"
        _publish(target, selected)
        selected_ids.update(available)
        reports.append(
            {
                "name": name,
                "team_id": manifest["team_id"],
                "team_name": manifest["team_name"],
                "snapshot_utc": manifest["updated_utc"],
                "original_sha256": digest(config.output / name / "collector-original.json"),
                "selected_manifest": str(target),
                "selected_sha256": digest(target),
                "public_evidence": public,
                "submissions": [{**row, "trajectories": counts[row["id"]]} for row in versions],
                "episodes": len(available),
                "teacher_trajectories": sum(counts.values()),
                "not_collected_episode_ids": sorted(matching - available),
                "reused_other_collector_episode_ids": sorted(
                    available - {r["episode_id"] for r in known(manifest, "replays")}
                ),
            }
        )
    report = {
        "configuration": config.model_dump(mode="json"),
        "sources": reports,
        "unique_episodes": len(selected_ids),
        "teacher_trajectories": sum(r["teacher_trajectories"] for r in reports),
        "excluded_submissions": sorted(excluded),
    }
    _publish(config.output / "selection.json", report)
    return report


@hydra.main(
    version_base=None,
    config_path="../../../../configs",
    config_name="sequences_watch5_active_recent_20260926",
)
def main(configuration: DictConfig) -> None:
    """Freeze a submission union for the existing complete-sequence encoder."""
    config = SubmissionSettings.model_validate(
        OmegaConf.to_container(configuration.selection, resolve=True)
    )
    report = freeze(config)
    print(json.dumps({k: report[k] for k in ("unique_episodes", "teacher_trajectories")}))


if __name__ == "__main__":
    main()
