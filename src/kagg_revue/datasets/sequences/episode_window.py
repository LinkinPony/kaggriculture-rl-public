"""Freeze collected teacher games by their official episode creation time."""

import json
from collections import Counter
from pathlib import Path
from typing import Any

import hydra
from omegaconf import DictConfig, OmegaConf
from pydantic import AwareDatetime, Field, model_validator

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.configuration import FrozenSettings
from kagg_revue.datasets.exclusions import EXCLUDED_SUBMISSIONS
from kagg_revue.datasets.sequences.window import _timestamp


class EpisodeWindowSettings(FrozenSettings):
    """Pin episode dates independently of the collector's submission scope."""

    source: Path
    output: Path
    created_since: AwareDatetime
    created_before: AwareDatetime
    expected_episodes: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_bounds(self) -> "EpisodeWindowSettings":
        """Reject an empty or reversed episode window."""
        if self.created_since >= self.created_before:
            raise ValueError("episode window must have increasing bounds")
        return self


def select_window(manifest: dict[str, Any], config: EpisodeWindowSettings) -> dict[str, Any]:
    """Keep complete available games in the inclusive-start, exclusive-end window."""
    if config.created_before > _timestamp(manifest["updated_utc"]):
        raise ValueError("episode window ends after the collector snapshot")
    episodes = [
        e
        for e in manifest["episodes"]
        if config.created_since <= _timestamp(e["createTime"]) < config.created_before
    ]
    ids = {e["id"] for e in episodes}
    replays = [r for r in manifest["replays"] if r["episode_id"] in ids]
    if (
        len(episodes) != config.expected_episodes
        or len(ids) != len(episodes)
        or len(replays) != len(ids)
        or {r["episode_id"] for r in replays} != ids
    ):
        raise ValueError("episode count differs or selected games are not uniquely available")
    excluded = set(manifest.get("excluded_submissions", [])) | EXCLUDED_SUBMISSIONS
    if ids & set(manifest.get("excluded_episode_ids", [])) or any(
        a["submissionId"] in excluded for e in episodes for a in e["agents"]
    ):
        raise ValueError("excluded submission or episode reappeared")
    versions = {
        a["submissionId"]
        for e in episodes
        for a in e["agents"]
        if a.get("teamId") == manifest["team_id"]
    }
    submissions = [s for s in manifest["submissions"] if s["id"] in versions]
    if {s["id"] for s in submissions} != versions or any(
        not any(a.get("teamId") == manifest["team_id"] for a in e["agents"]) for e in episodes
    ):
        raise ValueError("episode teacher identity is outside the collector scope")
    return {
        **{k: manifest[k] for k in ("team_id", "team_name", "updated_utc", "configuration")},
        "schema": "watched-team-replays-v1",
        "scope": "Frozen episode createTime window; all recorded outcomes and ratings.",
        "submissions": submissions,
        "episodes": episodes,
        "replays": replays,
        "excluded_submissions": sorted(excluded),
        "excluded_episode_ids": manifest.get("excluded_episode_ids", []),
        "pending_episode_ids": [],
        "episode_window": {
            "field": "createTime",
            "created_since_inclusive": config.created_since.isoformat(),
            "created_before_exclusive": config.created_before.isoformat(),
        },
    }


def freeze(config: EpisodeWindowSettings) -> dict[str, Any]:
    """Preserve the exact source and refuse to change an existing selection."""
    config.output.mkdir(parents=True, exist_ok=True)
    original = config.output / "collector-original.json"
    raw = original.read_bytes() if original.exists() else config.source.read_bytes()
    manifest = json.loads(raw)
    selected = select_window(manifest, config)
    target = config.output / "selected.json"
    if target.exists() and json.loads(target.read_text()) != selected:
        raise ValueError("cannot change a frozen episode window in place")
    if not original.exists():
        with original.open("xb") as stream:
            stream.write(raw)
    write_json(target, selected)
    report = {
        "configuration": config.model_dump(mode="json"),
        "original_sha256": digest(original),
        "selected_sha256": digest(target),
        "snapshot_utc": manifest["updated_utc"],
        "episodes": len(selected["episodes"]),
        "episode_dates": dict(Counter(e["createTime"][:10] for e in selected["episodes"])),
        "replay_storage": dict(Counter(r.get("storage", "gzip") for r in selected["replays"])),
        "submissions": [s["id"] for s in selected["submissions"]],
    }
    report_path = config.output / "selection.json"
    if report_path.exists() and json.loads(report_path.read_text()) != report:
        raise ValueError("cannot change frozen selection provenance in place")
    write_json(report_path, report)
    return report


@hydra.main(
    version_base=None, config_path="../../../../configs", config_name="sequences_dsm_games_20260924"
)
def main(configuration: DictConfig) -> None:
    """Freeze a game-date selection for the standard sequence encoder."""
    config = EpisodeWindowSettings.model_validate(
        OmegaConf.to_container(configuration.snapshot, resolve=True)
    )
    print(json.dumps(freeze(config)), flush=True)


if __name__ == "__main__":
    main()
