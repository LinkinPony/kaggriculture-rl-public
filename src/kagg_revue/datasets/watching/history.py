"""Mine target submission IDs from authenticated historical match listings."""

import json
import time
from pathlib import Path
from typing import Any

from kagg_revue.artifacts.io import digest
from kagg_revue.datasets.coverage.acquisition import Client
from kagg_revue.datasets.watching.config import WatchSettings
from kagg_revue.datasets.watching.exclusions import excluded_episode
from kagg_revue.datasets.watching.records import save_manifest, utc_now


def mine_local_history(
    config: WatchSettings,
    manifest: dict[str, Any],
    submissions: dict[int, Any],
    episodes: dict[int, Any],
) -> list[dict[str, Any]]:
    """Import named archived match listings, retaining their exact source hashes."""
    errors = []
    sources = manifest.setdefault("local_history_sources", {})
    for path in config.history_sources:
        try:
            sha256 = digest(path)
            if sources.get(str(path), {}).get("sha256") == sha256:
                continue
            payload = json.loads(path.read_text())
            rows = payload.get("episodes", [])
            for matches in payload.get("by_submission", {}).values():
                rows.extend(matches)
            ingest(
                rows, config.team_id, submissions, episodes, str(path), config.excluded_submissions
            )
            sources[str(path)] = {"sha256": sha256, "imported_utc": utc_now()}
        except Exception as error:
            errors.append(
                {"stage": "local_history", "path": str(path), "error_type": type(error).__name__}
            )
    return errors


def ingest(
    rows: list[dict[str, Any]],
    team_id: int,
    submissions: dict[int, Any],
    episodes: dict[int, Any],
    source: str,
    excluded_submissions: tuple[int, ...] = (),
) -> None:
    """Retain completed target games and attach evidence to inferred submissions."""
    for row in rows:
        if excluded_episode(row, excluded_submissions):
            episodes.pop(row["id"], None)
            continue
        if row.get("state") != "COMPLETED" or row.get("type") != "EPISODE_TYPE_PUBLIC":
            continue
        target_agents = [agent for agent in row["agents"] if agent.get("teamId") == team_id]
        if not target_agents:
            continue
        previous = episodes.get(row["id"], {})
        episodes[row["id"]] = {
            **previous,
            **row,
            "first_seen_utc": previous.get("first_seen_utc", utc_now()),
            "discovered_from": sorted(set(previous.get("discovered_from", [])) | {source}),
        }
        for agent in target_agents:
            key = agent["submissionId"]
            submission = submissions.setdefault(key, {"id": key, "source": "match_history"})
            submission["evidence_episode_ids"] = sorted(
                set(submission.get("evidence_episode_ids", [])) | {row["id"]}
            )


def mine_own_history(
    client: Client,
    config: WatchSettings,
    snapshot: Path,
    manifest: dict[str, Any],
    submissions: dict[int, Any],
    episodes: dict[int, Any],
) -> list[dict[str, Any]]:
    """Page through our submissions and preserve target matches after each listing."""
    errors: list[dict[str, Any]] = []
    if not config.scan_own_history:
        return errors
    elapsed = time.time() - manifest.get("own_history_checked_at", 0)
    if elapsed < config.own_history_interval_seconds:
        return errors
    own = set(manifest.get("own_submission_ids", []))
    token = ""
    tokens: set[str] = set()
    try:
        while True:
            time.sleep(config.request_interval)
            fields: dict[str, Any] = {"competition_name": "kaggriculture", "page_size": 100}
            if token:
                fields["page_token"] = token
            response = client.metadata(
                snapshot / "own" / f"page-{len(tokens)}.json",
                "list_submissions",
                "ApiListSubmissionsRequest",
                **fields,
            )
            own.update(row["ref"] for row in response["submissions"])
            token = response.get("nextPageToken", "")
            if not token:
                break
            if token in tokens:
                raise ValueError("own submission pagination repeated a token")
            tokens.add(token)
    except Exception as error:
        errors.append({"stage": "own_submissions", "error_type": type(error).__name__})
    manifest["own_submission_ids"] = sorted(own)
    for key in sorted(own, reverse=True):
        time.sleep(config.request_interval)
        try:
            path = snapshot / "own" / "episodes" / f"{key}.json"
            response = client.metadata(
                path,
                "list_submission_episodes",
                "ApiListSubmissionEpisodesRequest",
                submission_id=key,
            )
            ingest(
                response["episodes"],
                config.team_id,
                submissions,
                episodes,
                str(path),
                config.excluded_submissions,
            )
            manifest["submissions"] = sorted(submissions.values(), key=lambda row: row["id"])
            manifest["episodes"] = sorted(episodes.values(), key=lambda row: row["id"])
            save_manifest(config, manifest)
        except Exception as error:
            errors.append(
                {"stage": "own_episodes", "submission_id": key, "error_type": type(error).__name__}
            )
    if not errors:
        manifest["own_history_checked_at"] = time.time()
    return errors
