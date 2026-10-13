"""Publish BC revisions with retired matches removed, preserving historical inputs."""

import copy
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import hydra
from omegaconf import DictConfig, OmegaConf
from pydantic import Field

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.configuration import FrozenSettings
from kagg_revue.datasets.exclusions import (
    EXCLUDED_SUBMISSIONS,
    excluded_in_shard,
    validate_manifest,
)
from kagg_revue.datasets.watching.config import WatchSettings
from kagg_revue.datasets.watching.exclusions import apply_exclusions


class RetirementSettings(FrozenSettings):
    """Pin source manifests and require a new output directory for each revision."""

    sources: tuple[Path, ...] = Field(min_length=1)
    suffix: str = Field(pattern=r"^-[a-z0-9-]+$")
    report: Path


def _snapshots(manifest: dict[str, Any], output: Path) -> None:
    """Filter copied selection manifests and refresh their authenticated references."""
    paths = []
    sources = []
    episodes: dict[int, dict[str, Any]] = {}
    for reference in manifest["sources"]["collector_snapshots"]:
        source = Path(reference["path"])
        if digest(source) != reference["sha256"]:
            raise ValueError(f"source collector snapshot changed: {source}")
        snapshot = json.loads(source.read_text())
        config = WatchSettings(
            raw=source.parent,
            team_id=snapshot["team_id"],
            team_name=snapshot["team_name"],
            excluded_submissions=tuple(snapshot.get("excluded_submissions", [])),
        )
        apply_exclusions(config, snapshot)
        options = snapshot["configuration"]
        options["excluded_submissions"] = list(config.excluded_submissions)
        for field, excluded in (
            ("seed_submissions", config.excluded_submissions),
            ("seed_episodes", snapshot["excluded_episode_ids"]),
        ):
            if field in options:
                options[field] = [key for key in options[field] if key not in excluded]
        selection = snapshot.get("submission_selection", {})
        if "public_submission_ids" in selection:
            selection["public_submission_ids"] = [
                key
                for key in selection["public_submission_ids"]
                if key not in config.excluded_submissions
            ]
        target = output / "source-manifests" / f"{snapshot['team_id']}.json"
        write_json(target, snapshot)
        paths.append(str(target))
        sources.append(
            {
                **reference,
                "path": str(target),
                "sha256": digest(target),
                "episodes": len(snapshot["episodes"]),
                "submissions": sorted(row["id"] for row in snapshot["submissions"]),
                "configuration": options,
            }
        )
        episodes.update((row["id"], row) for row in snapshot["episodes"])
    manifest["configuration"]["watch_manifests"] = paths
    manifest["sources"] = {
        "collector_snapshots": sources,
        "episodes": len(episodes),
        "dates": sorted({row["createTime"][:10] for row in episodes.values()}),
    }


def _coverage(shards: list[dict[str, Any]], splits: list[str]) -> dict[str, Any]:
    """Count only retained games and teacher trajectories in their original splits."""
    coverage = {}
    for split in splits:
        group = [row for row in shards if row["split"] == split]
        coverage[split] = {
            "episodes": len(group),
            "usable_rows": sum(row["usable_rows"] for row in group),
            "context_rows": sum(row["rows"] for row in group),
            "trajectories": sum(len(row["task"]["seats"]) for row in group),
            "dates": dict(Counter(row["source_date"] for row in group)),
        }
    return coverage


def revise(source: Path, output: Path) -> dict[str, Any]:
    """Remove complete affected matches; hard-link unchanged arrays into a new dataset."""
    original = json.loads(source.read_text())
    if original.get("sequence_format") != "complete-turn-seat-v1":
        raise ValueError("retirement requires complete game sequence shards")
    removed = [row for row in original["shards"] if excluded_in_shard(row)]
    if not removed:
        raise ValueError(f"source contains no retired submissions: {source}")
    output.mkdir(parents=True, exist_ok=False)
    manifest = copy.deepcopy(original)
    manifest["shards"] = [row for row in original["shards"] if not excluded_in_shard(row)]
    manifest["exclusions"] = [row for row in original["exclusions"] if not excluded_in_shard(row)]
    manifest["configuration"]["output"] = str(output)
    _snapshots(manifest, output)
    manifest["coverage"] = _coverage(manifest["shards"], list(original["coverage"]))
    teachers = Counter(
        seat.get("teacher_name", seat["name"])
        for row in manifest["shards"]
        for seat in row["task"]["seats"]
    )
    manifest["selected_teacher_trajectories"] = dict(sorted(teachers.items()))
    selection = manifest["teacher_selection"]
    selection["excluded_submissions"] = sorted(
        set(selection.get("excluded_submissions", [])) | EXCLUDED_SUBMISSIONS
    )
    manifest["scope"] += " User-retired submissions excluded from either seat of every match."
    origin = source.parent.resolve()
    arrays = 0
    for row in manifest["shards"]:
        for name in row["hashes"]:
            path = (origin / row[name]).resolve()
            target = output / row[name]
            if not path.is_relative_to(origin) or not target.resolve().is_relative_to(
                output.resolve()
            ):
                raise ValueError("sequence array escapes its dataset")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.hardlink_to(path)
            if not target.samefile(path):
                raise ValueError("retained array differs from its historical source")
            arrays += 1
        write_json(output / f"episode-{row['task']['episode_id']}.json", row)
    validate_manifest(manifest)
    revision = {
        "schema": "sequence-submission-retirement-v1",
        "created_utc": datetime.now(UTC).isoformat(),
        "source": str(source),
        "source_sha256": digest(source),
        "excluded_submissions": sorted(EXCLUDED_SUBMISSIONS),
        "removed_episode_ids": [row["task"]["episode_id"] for row in removed],
        "removed_trajectories": sum(len(row["task"]["seats"]) for row in removed),
        "before": original["coverage"],
        "after": manifest["coverage"],
        "retained_arrays_same_inode": arrays,
        "historical_source_preserved": True,
    }
    manifest["submission_retirement"] = revision
    write_json(output / "sources.json", manifest["sources"])
    write_json(
        output / "catalog.json",
        [row["task"] for row in manifest["shards"] + manifest["exclusions"]],
    )
    preparation = {
        key: value
        for key, value in manifest["configuration"].items()
        if key not in {"partition", "split_mapping"}
    }
    write_json(output / "preparation.json", preparation)
    write_json(output / "manifest.json", manifest)
    receipt = {
        **revision,
        "replacement": str(output / "manifest.json"),
        "replacement_sha256": digest(output / "manifest.json"),
        "teacher_trajectories": dict(sorted(teachers.items())),
    }
    write_json(output / "retirement.json", receipt)
    write_json(source.parent / "retired.json", receipt)
    return receipt


@hydra.main(
    version_base=None, config_path="../../../../configs", config_name="sequences_retire_submissions"
)
def main(configuration: DictConfig) -> None:
    """Publish reviewed revisions without changing any frozen training provenance."""
    config = RetirementSettings.model_validate(
        OmegaConf.to_container(configuration.retirement, resolve=True)
    )
    receipts = []
    for source in config.sources:
        output = source.parent.with_name(source.parent.name + config.suffix)
        receipt = revise(source, output)
        receipts.append(receipt)
        write_json(config.report, receipts)
        print(
            json.dumps(
                {"source": str(source), "removed_games": len(receipt["removed_episode_ids"])}
            ),
            flush=True,
        )


if __name__ == "__main__":
    main()
