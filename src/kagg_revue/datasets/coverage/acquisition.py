"""Archive public submission episodes using the authenticated Kaggle SDK."""

import gzip
import hashlib
import importlib
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import hydra
from omegaconf import DictConfig, OmegaConf
from pydantic import BaseModel, Field

from kagg_revue.artifacts.io import digest, write_json


class Acquisition(BaseModel):
    """Bound a frozen leaderboard survey independently of observed outcomes."""

    raw: Path
    ranks: list[int]
    second_version_top: int = 6
    episodes_per_submission: int = 24
    extra_submissions: list[int] = Field(default_factory=list)
    workers: int = 4
    seed: int = 65111


class Client:
    """Load the optional Kaggle SDK without exposing authentication material."""

    def __init__(self) -> None:
        """Use the user's existing authenticated CLI installation."""
        self.api: Any = importlib.import_module("kaggle.api.kaggle_api_extended").KaggleApi()
        self.api.authenticate()
        self.types: Any = importlib.import_module(
            "kagglesdk.competitions.types.competition_api_service"
        )

    def request(self, method: str, request_type: str, **fields: Any) -> Any:
        """Issue a read request, with bounded backoff for transient failures."""
        for attempt in range(4):
            try:
                request = getattr(self.types, request_type)()
                for name, value in fields.items():
                    setattr(request, name, value)
                with self.api.build_kaggle_client() as client:
                    return getattr(client.competitions.competition_api_client, method)(request)
            except Exception:
                if attempt == 3:
                    raise
                time.sleep(2 ** (attempt + 1))
        raise AssertionError("unreachable")

    def metadata(self, path: Path, method: str, request_type: str, **fields: Any) -> Any:
        """Preserve the first successful response and its retrieval provenance."""
        if not path.exists():
            response = self.request(method, request_type, **fields)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(response.to_json())
            write_json(
                path.with_suffix(".source.json"),
                {
                    "method": method,
                    "request": fields,
                    "sha256": digest(path),
                    "retrieved_utc": datetime.now(UTC).isoformat(),
                },
            )
        return json.loads(path.read_text())


def select_episodes(episodes: list[Any], submission: int, count: int, seed: int) -> list[Any]:
    """Sample each seat by stable random priority, without consulting rewards."""
    result = []
    for seat in (0, 1):
        candidates = [
            episode
            for episode in episodes
            if episode.get("state") == "COMPLETED"
            and any(
                a["submissionId"] == submission and a.get("index", 0) == seat
                for a in episode["agents"]
            )
        ]
        candidates.sort(key=lambda e: hashlib.sha256(f"{seed}:{e['id']}".encode()).digest())
        result.extend(candidates[: count // 2])
    return result


def _download(raw: Path, episode: dict[str, Any]) -> dict[str, Any]:
    path = raw / "replays" / f"{episode['id']}.json.gz"
    if not path.exists():
        response = Client().request(
            "get_episode_replay", "ApiGetEpisodeReplayRequest", episode_id=episode["id"]
        )
        response.raise_for_status()
        content = response.content
        replay = json.loads(content)
        if replay.get("name") != "kaggriculture" or not replay.get("steps"):
            raise ValueError(f"invalid replay for {episode['id']}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(gzip.compress(content, compresslevel=3, mtime=0))
        write_json(
            path.with_suffix(".source.json"),
            {
                "episode_id": episode["id"],
                "retrieved_utc": datetime.now(UTC).isoformat(),
                "url": f"https://www.kaggle.com/api/v1/competitions/episodes/{episode['id']}/replay",
                "raw_sha256": hashlib.sha256(content).hexdigest(),
                "compressed_sha256": digest(path),
                "raw_bytes": len(content),
            },
        )
    return {
        "episode_id": episode["id"],
        "path": str(path),
        "sha256": digest(path),
        "bytes": path.stat().st_size,
    }


def acquire(config: Acquisition) -> None:
    """Freeze metadata first, then download a reproducible public replay sample."""
    client = Client()
    board = client.metadata(
        config.raw / "leaderboard.json",
        "get_leaderboard",
        "ApiGetLeaderboardRequest",
        competition_name="kaggriculture",
        page_size=max(config.ranks),
        override_public=True,
    )
    selected: dict[int, Any] = {}
    submissions: dict[int, Any] = {}
    for rank in config.ranks:
        row = board["submissions"][rank - 1]
        versions = client.metadata(
            config.raw / "teams" / f"{row['teamId']}.json",
            "list_team_public_submissions",
            "ApiListTeamPublicSubmissionsRequest",
            team_id=row["teamId"],
        )["submissions"]
        versions.sort(key=lambda v: v["dateSubmitted"], reverse=True)
        for version in versions[: 2 if rank <= config.second_version_top else 1]:
            submissions[version["id"]] = {**version, **row, "rank": rank}
    for submission in config.extra_submissions:
        submissions.setdefault(submission, {"id": submission, "selection": "explicit diagnostic"})
    for submission, row in submissions.items():
        episodes = client.metadata(
            config.raw / "submissions" / f"{submission}.json",
            "list_submission_episodes",
            "ApiListSubmissionEpisodesRequest",
            submission_id=submission,
        )["episodes"]
        sample = select_episodes(episodes, submission, config.episodes_per_submission, config.seed)
        row["listed_episodes"] = len(episodes)
        row["selected_episodes"] = [e["id"] for e in sample]
        selected.update((e["id"], e) for e in sample)
        print(
            json.dumps(
                {"submission": submission, "listed": len(episodes), "selected": len(sample)}
            ),
            flush=True,
        )
    manifest = {
        "schema": "public-coverage-v1",
        "created_utc": datetime.now(UTC).isoformat(),
        "config": config.model_dump(mode="json"),
        "submissions": list(submissions.values()),
        "episodes": list(selected.values()),
        "selection": "latest public versions per selected "
        "leaderboard team; stable random sample per submission and seat, independent of reward; "
        "deduplicate episode IDs. API listing truncation and matchmaking remain selection biases.",
    }
    write_json(config.raw / "selection.json", manifest)
    completed, failures = [], []
    with ThreadPoolExecutor(max_workers=config.workers) as pool:
        futures = {pool.submit(_download, config.raw, e): e["id"] for e in selected.values()}
        for future in as_completed(futures):
            try:
                completed.append(future.result())
            except Exception as error:
                failures.append({"episode_id": futures[future], "error": type(error).__name__})
            if (len(completed) + len(failures)) % 20 == 0:
                print(
                    json.dumps(
                        {
                            "downloaded": len(completed),
                            "failed": len(failures),
                            "total": len(selected),
                        }
                    ),
                    flush=True,
                )
    write_json(
        config.raw / "manifest.json",
        {
            **manifest,
            "replays": sorted(completed, key=lambda r: r["episode_id"]),
            "failures": failures,
            "completed_utc": datetime.now(UTC).isoformat(),
        },
    )
    print(json.dumps({"complete": len(completed), "failed": len(failures)}), flush=True)


@hydra.main(version_base=None, config_path="../../../../configs", config_name="coverage_survey")
def main(config: DictConfig) -> None:
    """Acquire new public data with an explicit, archived Hydra protocol."""
    acquire(Acquisition.model_validate(OmegaConf.to_container(config.acquisition, resolve=True)))


if __name__ == "__main__":
    main()
