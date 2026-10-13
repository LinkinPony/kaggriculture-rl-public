"""Freeze qualifying public versions and acquire every listed missing episode."""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import hydra
from omegaconf import DictConfig, OmegaConf
from pydantic import Field

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.bc.replay import daily_episode_metadata
from kagg_revue.configuration import FrozenSettings
from kagg_revue.datasets.coverage.acquisition import Client
from kagg_revue.datasets.ranked.downloads import cached_replays, download_missing


class Acquisition(FrozenSettings):
    """Use an immutable ranking snapshot and strict per-submission score cutoff."""

    raw: Path
    daily_manifest: Path
    maximum_rank: int = Field(default=10, gt=0)
    minimum_score: float = 2900
    workers: int = Field(default=4, gt=0)
    request_interval: float = Field(default=1.0, ge=0)
    maximum_backoffs: int = Field(default=5, ge=0)
    reuse_archives: tuple[Path, ...] = ()
    reuse_manifests: tuple[Path, ...] = ()


def acquire(config: Acquisition) -> Path:
    """Keep all completed public episodes; never sample by seat or outcome."""
    client = Client()
    board = client.metadata(
        config.raw / "leaderboard.json",
        "get_leaderboard",
        "ApiGetLeaderboardRequest",
        competition_name="kaggriculture",
        page_size=1000,
        override_public=True,
    )
    source = json.loads((config.raw / "leaderboard.source.json").read_text())
    cutoff = datetime.fromisoformat(source["retrieved_utc"])
    daily = json.loads(config.daily_manifest.read_text())
    daily_ids = {
        int(episode)
        for row in daily["daily_archives"]
        for episode in daily_episode_metadata(Path(row["path"]))
    }
    submissions, excluded = [], []
    episodes: dict[int, Any] = {}
    for rank, team in enumerate(board["submissions"][: config.maximum_rank], 1):
        if float(team["score"]) <= config.minimum_score:
            continue
        versions = client.metadata(
            config.raw / "teams" / f"{team['teamId']}.json",
            "list_team_public_submissions",
            "ApiListTeamPublicSubmissionsRequest",
            team_id=team["teamId"],
        )["submissions"]
        for version in versions:
            row = {**team, **version, "rank": rank}
            if float(version["publicScore"]) <= config.minimum_score:
                excluded.append({**row, "reason": "submission_score_not_above_cutoff"})
                continue
            response = client.metadata(
                config.raw / "submissions" / f"{version['id']}.json",
                "list_submission_episodes",
                "ApiListSubmissionEpisodesRequest",
                submission_id=version["id"],
            )
            listed = response["episodes"]
            selected = [
                episode
                for episode in listed
                if episode.get("state") == "COMPLETED"
                and episode.get("type") == "EPISODE_TYPE_PUBLIC"
                and datetime.fromisoformat(episode["endTime"]) <= cutoff
            ]
            row.update(
                listed_episodes=len(listed),
                selected_episodes=[e["id"] for e in selected],
                daily_overlap=sum(e["id"] in daily_ids for e in selected),
            )
            submissions.append(row)
            episodes.update((e["id"], e) for e in selected)
            print(
                json.dumps(
                    {
                        "submission": version["id"],
                        "team": team["teamName"],
                        "listed": len(listed),
                        "selected": len(selected),
                        "daily_overlap": row["daily_overlap"],
                    }
                ),
                flush=True,
            )
    selection = {
        "schema": "ranked-public-replays-v1",
        "configuration": config.model_dump(mode="json"),
        "snapshot_utc": cutoff.isoformat(),
        "leaderboard_sha256": digest(config.raw / "leaderboard.json"),
        "daily_manifest_sha256": digest(config.daily_manifest),
        "submissions": submissions,
        "excluded_submissions": excluded,
        "episodes": sorted(episodes.values(), key=lambda e: e["id"]),
        "daily_overlap": sorted(daily_ids & episodes.keys()),
        "scope": "Every completed public episode returned by the frozen submission listings, "
        "ending no later than the ranking snapshot. No date lower bound for supplements; "
        "exclude validation, deduplicate IDs and reuse daily episodes. The public API exposes "
        "only currently public versions and has no pagination field on episode listings; "
        "this is not a claim to recover unavailable historical versions or unlisted episodes.",
    }
    write_json(config.raw / "selection.json", selection)
    missing = [e for e in episodes.values() if e["id"] not in daily_ids]
    cached = cached_replays(
        config.raw, {e["id"] for e in missing}, config.reuse_archives, config.reuse_manifests
    )
    print(
        json.dumps(
            {"authenticated_available": len(cached), "need_download": len(missing) - len(cached)}
        ),
        flush=True,
    )
    completed, failures = download_missing(
        config.raw,
        missing,
        cached,
        config.workers,
        config.request_interval,
        config.maximum_backoffs,
    )
    path = config.raw / "manifest.json"
    write_json(
        path,
        {
            **selection,
            "replays": sorted(completed, key=lambda e: e["episode_id"]),
            "failures": failures,
            "completed_utc": datetime.now(UTC).isoformat(),
        },
    )
    if failures:
        raise ValueError(f"{len(failures)} public replay downloads failed; rerun to resume")
    return path


@hydra.main(version_base=None, config_path="../../../../configs", config_name="ranked_acquisition")
def main(configuration: DictConfig) -> None:
    """Resolve and preserve the acquisition recipe before constructing BC data."""
    config = Acquisition.model_validate(
        OmegaConf.to_container(configuration.acquisition, resolve=True)
    )
    print(acquire(config), flush=True)


if __name__ == "__main__":
    main()
