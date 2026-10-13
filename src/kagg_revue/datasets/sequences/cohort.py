"""Freeze several collector snapshots with one submission window and exclusion list."""

import copy
import json
from collections import Counter
from pathlib import Path
from typing import Any

import hydra
from omegaconf import DictConfig, OmegaConf
from pydantic import AwareDatetime, Field

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.configuration import FrozenSettings
from kagg_revue.datasets.exclusions import EXCLUDED_SUBMISSIONS
from kagg_revue.datasets.sequences.window import _timestamp, select_window
from kagg_revue.datasets.watching.config import WatchSettings
from kagg_revue.datasets.watching.dates import resolve_dates
from kagg_revue.datasets.watching.exclusions import apply_exclusions


class CohortSettings(FrozenSettings):
    """Bind named collectors and explicit blocked versions to immutable inputs."""

    output: Path
    sources: dict[str, Path]
    submitted_since: AwareDatetime
    excluded_submissions: tuple[int, ...] = Field(min_length=1)


def _publish(path: Path, value: dict[str, Any]) -> None:
    """Refuse to replace a published selection with different data."""
    if path.exists() and json.loads(path.read_text()) != value:
        raise ValueError(f"cannot change frozen cohort artifact: {path}")
    write_json(path, value)


def freeze(config: CohortSettings) -> dict[str, Any]:
    """Resolve official dates on frozen copies, then exclude entire contaminated games."""
    snapshots: dict[str, dict[str, Any]] = {}
    for name, source in config.sources.items():
        if not name or Path(name).name != name or name in {".", ".."}:
            raise ValueError("collector names must be simple directory names")
        original_path = config.output / name / "collector-original.json"
        original_path.parent.mkdir(parents=True, exist_ok=True)
        if not original_path.exists():
            with original_path.open("xb") as stream:
                stream.write(source.read_bytes())
        snapshots[name] = json.loads(original_path.read_text())
    if not snapshots or len({m["team_id"] for m in snapshots.values()}) != len(snapshots):
        raise ValueError("cohort collectors must identify distinct teams")
    before = min(_timestamp(m["updated_utc"]) for m in snapshots.values())
    reports = []
    unique_episodes: set[int] = set()
    excluded_episodes: set[int] = set()
    for name, original in snapshots.items():
        directory = config.output / name
        dated_path = directory / "dated.json"
        if dated_path.exists():
            manifest = json.loads(dated_path.read_text())
        else:
            manifest = copy.deepcopy(original)
            options = WatchSettings.model_validate(manifest["configuration"]).model_copy(
                update={"submitted_since": config.submitted_since}
            )
            dates = {s["id"]: s for s in manifest["submissions"]}
            errors = resolve_dates(options, dates)
            if errors:
                raise ValueError(f"cannot authenticate submission dates: {errors}")
            _publish(dated_path, manifest)
        excluded = tuple(
            sorted(
                EXCLUDED_SUBMISSIONS
                | set(config.excluded_submissions)
                | set(manifest.get("excluded_submissions", []))
            )
        )
        options = WatchSettings.model_validate(manifest["configuration"]).model_copy(
            update={"excluded_submissions": excluded}
        )
        removed = [
            e["id"]
            for e in manifest["episodes"]
            if any(a["submissionId"] in excluded for a in e["agents"])
        ]
        apply_exclusions(options, manifest)
        selected = select_window(manifest, config.submitted_since, before)
        selected_path = directory / "selected.json"
        _publish(selected_path, selected)
        counts = Counter(
            a["submissionId"]
            for e in selected["episodes"]
            for a in e["agents"]
            if a.get("teamId") == selected["team_id"]
            and a["submissionId"] in {s["id"] for s in selected["submissions"]}
        )
        unique_episodes.update(e["id"] for e in selected["episodes"])
        excluded_episodes.update(removed)
        reports.append(
            {
                "name": name,
                "team_id": selected["team_id"],
                "team_name": selected["team_name"],
                "collector_updated_utc": original["updated_utc"],
                "original_sha256": digest(directory / "collector-original.json"),
                "dated_sha256": digest(dated_path),
                "selected_manifest": str(selected_path),
                "selected_sha256": digest(selected_path),
                "submissions": [
                    {**s, "teacher_trajectories": counts[s["id"]]} for s in selected["submissions"]
                ],
                "episodes": len(selected["episodes"]),
                "teacher_trajectories": sum(counts.values()),
                "excluded_episode_ids": sorted(removed),
                "discovery_errors": original.get("discovery_errors", []),
            }
        )
    report = {
        "configuration": config.model_dump(mode="json"),
        "submitted_since_inclusive": config.submitted_since.isoformat(),
        "submitted_before_exclusive": before.isoformat(),
        "sources": reports,
        "unique_episodes": len(unique_episodes),
        "teacher_trajectories": sum(r["teacher_trajectories"] for r in reports),
        "excluded_episode_ids": sorted(excluded_episodes),
    }
    _publish(config.output / "selection.json", report)
    return report


@hydra.main(
    version_base=None, config_path="../../../../configs", config_name="sequences_watch3_20260924"
)
def main(configuration: DictConfig) -> None:
    """Freeze named teachers before running the standard BC sequence encoder."""
    config = CohortSettings.model_validate(
        OmegaConf.to_container(configuration.cohort, resolve=True)
    )
    report = freeze(config)
    print(json.dumps({k: v for k, v in report.items() if k != "sources"}), flush=True)


if __name__ == "__main__":
    main()
