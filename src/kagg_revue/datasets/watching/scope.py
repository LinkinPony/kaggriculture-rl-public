"""Apply a fixed submission cutoff while preserving earlier acquisition history."""

from datetime import datetime
from typing import Any

from kagg_revue.datasets.watching.config import WatchSettings
from kagg_revue.datasets.watching.exclusions import excluded_episode


def eligible(config: WatchSettings, submission: dict[str, Any]) -> bool:
    """Use the official submission timestamp, never a match or download date."""
    if submission["id"] in config.excluded_submissions:
        return False
    if config.submitted_since is None:
        return True
    value = submission.get("dateSubmitted")
    if not value:
        return False
    timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return timestamp.tzinfo is not None and timestamp >= config.submitted_since


def known(manifest: dict[str, Any], field: str) -> list[dict[str, Any]]:
    """Combine preserved historical rows with the currently selected catalog."""
    key = "episode_id" if field == "replays" else "id"
    rows = manifest.get("outside_scope", {}).get(field, []) + manifest[field]
    return list({row[key]: row for row in rows}.values())


def apply_scope(config: WatchSettings, manifest: dict[str, Any]) -> None:
    """Move earlier or undated records out of the active dataset and queue."""
    if config.submitted_since is None:
        return
    submissions = [
        r for r in known(manifest, "submissions") if r["id"] not in config.excluded_submissions
    ]
    active = {r["id"] for r in submissions if eligible(config, r)}
    episodes = [
        r
        for r in known(manifest, "episodes")
        if not excluded_episode(r, config.excluded_submissions)
        and r["id"] not in manifest.get("excluded_episode_ids", [])
    ]
    selected = {
        r["id"]
        for r in episodes
        if any(
            a.get("teamId") == config.team_id and a.get("submissionId") in active
            for a in r.get("agents", [])
        )
    }
    outside: dict[str, Any] = {"submitted_since": config.submitted_since.isoformat()}
    for field, rows, key, keys in (
        ("submissions", submissions, "id", active),
        ("episodes", episodes, "id", selected),
        (
            "replays",
            [
                r
                for r in known(manifest, "replays")
                if not excluded_episode(r, config.excluded_submissions)
                and r["episode_id"] not in manifest.get("excluded_episode_ids", [])
            ],
            "episode_id",
            selected,
        ),
    ):
        manifest[field] = sorted((r for r in rows if r[key] in keys), key=lambda r: r[key])
        outside[field] = sorted((r for r in rows if r[key] not in keys), key=lambda r: r[key])
    outside["undated_submission_ids"] = sorted(
        r["id"] for r in submissions if not r.get("dateSubmitted")
    )
    manifest["outside_scope"] = outside
