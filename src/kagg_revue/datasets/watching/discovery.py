"""Discover public versions and historical opponent identities from own games."""

import time
from datetime import UTC, datetime
from typing import Any

from kagg_revue.datasets.coverage.acquisition import Client
from kagg_revue.datasets.watching.config import WatchSettings
from kagg_revue.datasets.watching.dates import resolve_dates
from kagg_revue.datasets.watching.history import ingest, mine_local_history, mine_own_history
from kagg_revue.datasets.watching.records import save_manifest
from kagg_revue.datasets.watching.scope import eligible, known


def discover(config: WatchSettings, manifest: dict[str, Any]) -> list[dict[str, Any]]:
    """Refresh every known submission while preserving successful partial discovery."""
    client = Client()
    snapshot = config.raw / "snapshots" / datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    submissions = {row["id"]: row for row in known(manifest, "submissions")}
    episodes = {row["id"]: row for row in known(manifest, "episodes")}
    for key in config.seed_submissions:
        submissions.setdefault(key, {"id": key, "source": "user_seed"})
    for key in config.seed_episodes:
        if key not in manifest.get("excluded_episode_ids", []):
            episodes.setdefault(key, {"id": key, "source": "user_seed"})
    errors = mine_local_history(config, manifest, submissions, episodes)
    try:
        response = client.metadata(
            snapshot / "team.json",
            "list_team_public_submissions",
            "ApiListTeamPublicSubmissionsRequest",
            team_id=config.team_id,
        )
        for row in response["submissions"]:
            if row["id"] not in config.excluded_submissions:
                submissions[row["id"]] = {**submissions.get(row["id"], {}), **row}
    except Exception as error:
        errors.append({"stage": "team", "error_type": type(error).__name__})
    errors.extend(mine_own_history(client, config, snapshot, manifest, submissions, episodes))
    errors.extend(resolve_dates(config, submissions))
    manifest["submissions"] = sorted(submissions.values(), key=lambda row: row["id"])
    manifest["episodes"] = sorted(episodes.values(), key=lambda row: row["id"])
    save_manifest(config, manifest)
    for submission in sorted(submissions, reverse=True):
        if not eligible(config, submissions[submission]):
            continue
        time.sleep(config.request_interval)
        try:
            response = client.metadata(
                snapshot / "submissions" / f"{submission}.json",
                "list_submission_episodes",
                "ApiListSubmissionEpisodesRequest",
                submission_id=submission,
            )
            ingest(
                response["episodes"],
                config.team_id,
                submissions,
                episodes,
                str(snapshot / "submissions" / f"{submission}.json"),
                config.excluded_submissions,
            )
            manifest["submissions"] = sorted(submissions.values(), key=lambda row: row["id"])
            manifest["episodes"] = sorted(episodes.values(), key=lambda row: row["id"])
            save_manifest(config, manifest)
        except Exception as error:
            errors.append(
                {
                    "stage": "submission",
                    "submission_id": submission,
                    "error_type": type(error).__name__,
                }
            )
    manifest["latest_snapshot"] = str(snapshot)
    return errors
