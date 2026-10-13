"""Select the authenticated account's collected seats by episode creation time."""

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
from kagg_revue.datasets.sequences.submissions import _inventory
from kagg_revue.datasets.sequences.window import _timestamp


class OwnSettings(FrozenSettings):
    """Pin collected payloads and the account identity to an inclusive game cutoff."""

    output: Path
    sources: dict[str, Path] = Field(min_length=1)
    team_id: int = Field(gt=0)
    team_name: str
    created_since: AwareDatetime


def freeze(config: OwnSettings) -> dict[str, Any]:
    """Keep own seats only, while preserving the full replay as their context."""
    _publish(config.output / "configuration.json", config.model_dump(mode="json"))
    snapshots = {}
    for name, source in config.sources.items():
        if not name or Path(name).name != name or name in {".", ".."}:
            raise ValueError("collector names must be simple directory names")
        snapshots[name] = _snapshot(source, config.output / "sources" / f"{name}.json")
    excluded = set(EXCLUDED_SUBMISSIONS) | {
        key for m in snapshots.values() for key in m.get("excluded_submissions", [])
    }
    blocked = {key for m in snapshots.values() for key in m.get("excluded_episode_ids", [])}
    episodes, replays = _inventory(snapshots, excluded, blocked)
    account_versions = {key for m in snapshots.values() for key in m["own_submission_ids"]}
    matching = {
        key
        for key, row in episodes.items()
        if _timestamp(row["createTime"]) >= config.created_since
        and any(a.get("teamId") == config.team_id for a in row["agents"])
    }
    available = matching & replays.keys()
    seats = [
        a
        for key in sorted(available)
        for a in episodes[key]["agents"]
        if a.get("teamId") == config.team_id
    ]
    counts = Counter(a["submissionId"] for a in seats)
    if not seats or not counts.keys() <= account_versions:
        raise ValueError("selected own seats lack authenticated account submission evidence")
    if any(a["teamName"] != config.team_name for a in seats):
        raise ValueError("own team name differs from collected official metadata")
    selection = {
        "schema": "watched-team-replays-v1",
        "team_id": config.team_id,
        "team_name": config.team_name,
        "updated_utc": max(m["updated_utc"] for m in snapshots.values()),
        "configuration": {"submitted_since": None},
        "scope": "Own collected seats with createTime >= cutoff; all outcomes and versions.",
        "episode_window": {"created_since_inclusive": config.created_since.isoformat()},
        "submissions": [
            {"id": key, "source": "authenticated_own_history"} for key in sorted(counts)
        ],
        "episodes": [episodes[key] for key in sorted(available)],
        "replays": [replays[key] for key in sorted(available)],
        "excluded_submissions": sorted(excluded),
        "excluded_episode_ids": sorted(blocked),
        "pending_episode_ids": [],
    }
    target = config.output / "selected.json"
    _publish(target, selection)
    report = {
        "configuration": config.model_dump(mode="json"),
        "source_snapshots": {
            name: {
                "path": str(config.output / "sources" / f"{name}.json"),
                "sha256": digest(config.output / "sources" / f"{name}.json"),
            }
            for name in snapshots
        },
        "selected_sha256": digest(target),
        "episodes": len(available),
        "teacher_trajectories": len(seats),
        "submissions": [{"id": key, "trajectories": counts[key]} for key in sorted(counts)],
        "not_collected_episode_ids": sorted(matching - available),
    }
    _publish(config.output / "selection.json", report)
    return report


@hydra.main(
    version_base=None,
    config_path="../../../../configs",
    config_name="sequences_watch6_active_recent_20260926",
)
def main(configuration: DictConfig) -> None:
    """Freeze own games for a separately configured BC dataset."""
    config = OwnSettings.model_validate(OmegaConf.to_container(configuration.own, resolve=True))
    report = freeze(config)
    print(
        json.dumps(
            {k: v for k, v in report.items() if k not in {"source_snapshots", "configuration"}}
        )
    )


if __name__ == "__main__":
    main()
