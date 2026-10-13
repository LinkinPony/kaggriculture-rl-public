"""Freeze a collector's submission date window for complete-trajectory BC."""

import hashlib
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import hydra
from omegaconf import DictConfig, OmegaConf
from pydantic import AwareDatetime, model_validator

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.configuration import FrozenSettings
from kagg_revue.datasets.exclusions import EXCLUDED_SUBMISSIONS


class WindowSettings(FrozenSettings):
    """Pin an inclusive start and an exclusive end, defaulting to snapshot time."""

    source: Path
    output: Path
    submitted_since: AwareDatetime
    submitted_before: AwareDatetime | None = None

    @model_validator(mode="after")
    def validate_bounds(self) -> "WindowSettings":
        """Reject empty or reversed submission windows."""
        if self.submitted_before is not None and self.submitted_since >= self.submitted_before:
            raise ValueError("submission window must have increasing bounds")
        return self


def _timestamp(value: str) -> datetime:
    result = datetime.fromisoformat(value)
    if result.utcoffset() is None:
        raise ValueError("official submission timestamps must include a timezone")
    return result


def select_window(manifest: dict[str, Any], since: datetime, before: datetime) -> dict[str, Any]:
    """Select versions by official date, retaining their recorded teacher games."""
    if since >= before or before > _timestamp(manifest["updated_utc"]):
        raise ValueError("submission window must end no later than the frozen snapshot")
    cutoff = manifest["configuration"].get("submitted_since")
    if cutoff and since < _timestamp(cutoff):
        raise ValueError("submission window begins before the collector's active scope")
    submissions = [
        s for s in manifest["submissions"] if since <= _timestamp(s["dateSubmitted"]) < before
    ]
    ids = {s["id"] for s in submissions}
    if not ids or len(ids) != len(submissions):
        raise ValueError("submission window is empty or contains duplicate versions")
    episodes = [
        e
        for e in manifest["episodes"]
        if any(
            a.get("teamId") == manifest["team_id"] and a["submissionId"] in ids for a in e["agents"]
        )
    ]
    episode_ids = {e["id"] for e in episodes}
    excluded = set(manifest.get("excluded_submissions", [])) | EXCLUDED_SUBMISSIONS
    if (
        episode_ids & set(manifest.get("excluded_episode_ids", []))
        or any(a["submissionId"] in excluded for e in episodes for a in e["agents"])
        or ids & excluded
    ):
        raise ValueError("excluded submission or episode reappeared in the window")
    replays = [r for r in manifest["replays"] if r["episode_id"] in episode_ids]
    if (
        not episodes
        or len(episode_ids) != len(episodes)
        or len(replays) != len(episode_ids)
        or {r["episode_id"] for r in replays} != episode_ids
    ):
        raise ValueError("selected episodes must be unique and fully downloaded")
    return {
        **{k: manifest[k] for k in ("team_id", "team_name", "updated_utc", "configuration")},
        "schema": "watched-team-replays-v1",
        "scope": "Frozen official submission date window; all recorded outcomes and ratings.",
        "submissions": submissions,
        "episodes": episodes,
        "replays": replays,
        "excluded_submissions": sorted(excluded),
        "excluded_episode_ids": manifest.get("excluded_episode_ids", []),
        "pending_episode_ids": [],
        "submission_window": {
            "field": "dateSubmitted",
            "submitted_since_inclusive": since.isoformat(),
            "submitted_before_exclusive": before.isoformat(),
            "episode_time_filter": None,
        },
    }


def freeze(config: WindowSettings) -> dict[str, Any]:
    """Keep original snapshot bytes and publish an immutable selected manifest."""
    config.output.mkdir(parents=True, exist_ok=True)
    original = config.output / "collector-original.json"
    raw = original.read_bytes() if original.exists() else config.source.read_bytes()
    manifest = json.loads(raw)
    before = config.submitted_before or _timestamp(manifest["updated_utc"])
    selected = select_window(manifest, config.submitted_since, before)
    counts = Counter(
        a["submissionId"]
        for e in selected["episodes"]
        for a in e["agents"]
        if a.get("teamId") == manifest["team_id"]
        and a["submissionId"] in {s["id"] for s in selected["submissions"]}
    )
    report = {
        "configuration": config.model_dump(mode="json"),
        "collector_snapshot": {
            "original_path": str(config.source),
            "frozen_path": str(original),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "updated_utc": manifest["updated_utc"],
            "submissions": len(manifest["submissions"]),
            "episodes": len(manifest["episodes"]),
            "discovery_errors": manifest.get("discovery_errors", []),
        },
        "window": selected["submission_window"],
        "submissions": [
            {"id": s["id"], "dateSubmitted": s["dateSubmitted"], "trajectories": counts[s["id"]]}
            for s in sorted(selected["submissions"], key=lambda s: s["dateSubmitted"])
        ],
        "episodes": len(selected["episodes"]),
        "teacher_trajectories": sum(counts.values()),
        "replay_storage": dict(Counter(r.get("storage", "gzip") for r in selected["replays"])),
        "episode_dates": dict(Counter(e["createTime"][:10] for e in selected["episodes"])),
        "scope": manifest.get("scope"),
    }
    selected["source_snapshot"] = report["collector_snapshot"]
    target = config.output / "selected.json"
    if target.exists() and json.loads(target.read_text()) != selected:
        raise ValueError("cannot change a frozen submission window in place")
    if not original.exists():
        with original.open("xb") as stream:
            stream.write(raw)
    write_json(target, selected)
    report["selected_manifest"] = {"path": str(target), "sha256": digest(target)}
    report_path = config.output / "selection.json"
    if report_path.exists() and json.loads(report_path.read_text()) != report:
        raise ValueError("cannot change frozen selection provenance in place")
    write_json(report_path, report)
    return report


@hydra.main(
    version_base=None, config_path="../../../../configs", config_name="sequences_dsm_20260921_23"
)
def main(configuration: DictConfig) -> None:
    """Freeze a date-scoped source for the existing sequence preparation command."""
    config = WindowSettings.model_validate(
        OmegaConf.to_container(configuration.snapshot, resolve=True)
    )
    print(json.dumps(freeze(config), ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
