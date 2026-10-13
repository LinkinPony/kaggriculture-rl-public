"""Submit one qualified package to Kaggle exactly once and verify the new listing row."""

import json
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import hydra
from omegaconf import DictConfig, OmegaConf
from pydantic import Field

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.configuration import FrozenSettings
from kagg_revue.datasets.coverage.acquisition import Client

LISTING_ATTEMPTS = 12
LISTING_INTERVAL_SECONDS = 5.0


class Submission(FrozenSettings):
    """A qualified archive pinned by hash, and the single authorized upload."""

    archive: Path
    archive_sha256: str = Field(pattern="^[0-9a-f]{64}$")
    qualification: Path
    description: str = Field(min_length=1)
    output: Path
    competition: str = "kaggriculture"
    dry_run: bool = False


def _now() -> str:
    return datetime.now(UTC).isoformat()


def listing(client: Client, competition: str) -> list[dict[str, Any]]:
    """Read every submission of the authenticated team, page by page."""
    rows: list[dict[str, Any]] = []
    token = ""
    seen: set[str] = set()
    while True:
        fields: dict[str, Any] = {"competition_name": competition, "page_size": 100}
        if token:
            fields["page_token"] = token
        response = client.request("list_submissions", "ApiListSubmissionsRequest", **fields)
        page = json.loads(response.to_json())
        rows.extend(page.get("submissions", []))
        token = page.get("nextPageToken", "")
        if not token:
            return rows
        if token in seen:
            raise ValueError("submission pagination repeated a token")
        seen.add(token)


def _verify(config: Submission) -> None:
    if digest(config.archive) != config.archive_sha256:
        raise ValueError("archive differs from its pinned SHA256")
    report = json.loads(config.qualification.read_text())
    certified = report.get("build", report).get("archive", {}).get("sha256")
    if report.get("passed") is not True or certified != config.archive_sha256:
        raise ValueError("qualification does not certify this exact archive")


def submit(config: Submission) -> dict[str, Any]:
    """Record the attempt before the only upload call, so a rerun can never resubmit."""
    attempt_path = config.output / "submission-attempt.json"
    if attempt_path.exists():
        raise RuntimeError(f"a submission attempt is already recorded: {attempt_path}")
    _verify(config)
    client = Client()
    before = listing(client, config.competition)
    if config.dry_run:
        return {"dry_run": True, "verified_archive": config.archive_sha256, "existing": len(before)}
    write_json(config.output / "submissions-before.json", before)
    attempt = {
        "started_utc": _now(),
        "competition": config.competition,
        "archive": str(config.archive),
        "archive_sha256": config.archive_sha256,
        "description": config.description,
        "authorized_count": 1,
        "submit_calls_planned": 1,
    }
    write_json(attempt_path, attempt)
    response = client.api.competition_submit(
        str(config.archive), config.description, config.competition, quiet=True
    )
    result = {"message": response.message, "ref": response.ref}
    write_json(config.output / "submission-command-result.json", result)
    known = {row["ref"] for row in before}
    after: list[dict[str, Any]] = []
    new: list[dict[str, Any]] = []
    for _ in range(LISTING_ATTEMPTS):
        time.sleep(LISTING_INTERVAL_SECONDS)
        after = listing(client, config.competition)
        new = [row for row in after if row["ref"] not in known]
        if new:
            break
    write_json(config.output / "submissions-after.json", after)
    size = config.archive.stat().st_size
    verified = (
        len(new) == 1
        and new[0]["ref"] == result["ref"]
        and new[0].get("description") == config.description
        and int(new[0].get("totalBytes", size)) == size
    )
    receipt = {
        **attempt,
        "submit_calls": 1,
        "submission_ref": result["ref"],
        "new_rows": len(new),
        "row": new[0] if len(new) == 1 else None,
        "verified": verified,
        "verified_utc": _now(),
    }
    write_json(config.output / "submission-receipt.json", receipt)
    if not verified:
        raise RuntimeError("the listing did not show exactly the one expected new submission")
    return receipt


@hydra.main(
    version_base=None,
    config_path="../../../configs",
    config_name="kaggle_submission_s101102_u0200_20260930",
)
def main(configuration: DictConfig) -> None:
    """Submit the configured package once; never retried automatically."""
    config = Submission.model_validate(
        OmegaConf.to_container(configuration.submission, resolve=True)
    )
    print(json.dumps(submit(config), ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
