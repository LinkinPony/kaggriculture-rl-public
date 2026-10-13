"""Resolve immutable submission dates from public Kaggle match metadata."""

import json
import time
from datetime import UTC, datetime
from typing import Any
from urllib.request import Request, urlopen

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.datasets.watching.config import WatchSettings


def resolve_dates(config: WatchSettings, submissions: dict[int, Any]) -> list[dict[str, Any]]:
    """Cache official dates for historical versions absent from the public board."""
    errors: list[dict[str, Any]] = []
    if config.submitted_since is None:
        return errors
    url = "https://www.kaggle.com/api/i/competitions.EpisodeService/ListEpisodes"
    for key, row in sorted(submissions.items(), reverse=True):
        if row.get("dateSubmitted") or key in config.excluded_submissions:
            continue
        path = config.raw / "submission-dates" / f"{key}.json"
        try:
            if not path.exists():
                time.sleep(config.request_interval)
                request = Request(
                    url,
                    data=json.dumps({"submissionId": key}).encode(),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urlopen(request, timeout=30) as response:
                    payload = json.load(response)
                record = next(
                    r
                    for r in payload["submissions"]
                    if r["id"] == key and r["teamId"] == config.team_id
                )
                if not record.get("dateSubmitted"):
                    raise ValueError("public metadata omitted the submission date")
                write_json(path, payload)
                write_json(
                    path.with_suffix(".source.json"),
                    {
                        "url": url,
                        "request": {"submissionId": key},
                        "sha256": digest(path),
                        "retrieved_utc": datetime.now(UTC).isoformat(),
                    },
                )
            payload = json.loads(path.read_text())
            record = next(
                r
                for r in payload["submissions"]
                if r["id"] == key and r["teamId"] == config.team_id
            )
            row.update(dateSubmitted=record["dateSubmitted"], date_source=str(path))
        except Exception as error:
            errors.append(
                {
                    "stage": "submission_date",
                    "submission_id": key,
                    "error_type": type(error).__name__,
                }
            )
    return errors
