"""Submission retirements that apply to collection and every BC data entry point."""

from collections.abc import Iterable
from typing import Any

# Explicit user retirements. These also protect against old, frozen configurations.
EXCLUDED_SUBMISSIONS = frozenset({56414341, 56484772})


def submission_ids(record: dict[str, Any]) -> set[int]:
    """Read official identities and selected teacher identities without name matching."""
    rows = [record]
    for field in ("agents", "agent_identity", "seats", "selected_seats"):
        rows.extend(row for row in record.get(field, []) if isinstance(row, dict))
    return {
        int(row[key])
        for row in rows
        for key in ("submissionId", "submission_id")
        if row.get(key) is not None
    }


def excluded_in_shard(
    shard: dict[str, Any], submissions: Iterable[int] = EXCLUDED_SUBMISSIONS
) -> set[int]:
    """Check both participants, including opponents of a selected teacher."""
    identities = submission_ids(shard) | submission_ids(shard.get("task", {}))
    for episode in shard.get("episodes", []):
        identities.update(submission_ids(episode))
    return identities.intersection(submissions)


def validate_manifest(manifest: dict[str, Any]) -> None:
    """Reject retired submissions even when an old manifest's hashes still match."""
    excluded = {key for shard in manifest["shards"] for key in excluded_in_shard(shard)}
    if excluded:
        raise ValueError(
            f"BC dataset contains retired submissions {sorted(excluded)}; "
            "use the cleaned dataset revision"
        )
