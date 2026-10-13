"""Authenticate cached replays and honor server-wide replay download backoff."""

import gzip
import hashlib
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import orjson

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.bc.replay import daily_episode_metadata
from kagg_revue.datasets.coverage.acquisition import Client
from kagg_revue.datasets.ranked.throttle import RequestGate


def cached_replays(
    raw: Path, wanted: set[int], archives: tuple[Path, ...], manifests: tuple[Path, ...]
) -> dict[int, Any]:
    """Reuse authenticated files and ZIP members without copying external raw data."""
    found: dict[int, Any] = {}
    for episode_id in sorted(wanted):
        path = raw / "replays" / f"{episode_id}.json.gz"
        source = path.with_suffix(".source.json")
        if not path.exists():
            continue
        if (
            not source.exists()
            or digest(path) != json.loads(source.read_text())["compressed_sha256"]
        ):
            raise ValueError(f"incomplete cached replay requires inspection: {path}")
        found[episode_id] = {
            "episode_id": episode_id,
            "path": str(path),
            "sha256": digest(path),
            "bytes": path.stat().st_size,
        }
    for manifest in manifests:
        for row in json.loads(manifest.read_text())["replays"]:
            if row["episode_id"] in wanted - found.keys():
                if digest(Path(row["path"])) != row["sha256"]:
                    raise ValueError("existing public replay differs from its source manifest")
                found[row["episode_id"]] = {**row, "reused_from": str(manifest)}
    for path in archives:
        keys = {int(key) for key in daily_episode_metadata(path)} & (wanted - found.keys())
        if not keys:
            continue
        sha256 = digest(path)
        for episode_id in keys:
            found[episode_id] = {
                "episode_id": episode_id,
                "path": str(path),
                "member": f"{episode_id}.json",
                "sha256": sha256,
                "reused_from": str(path),
            }
    return found


def _fetch(raw: Path, episode_id: int) -> dict[str, Any]:
    """Issue one SDK request; let the coordinator stop all requests on HTTP 429."""
    try:
        client = Client()
        request = client.types.ApiGetEpisodeReplayRequest()
        request.episode_id = episode_id
        with client.api.build_kaggle_client() as session:
            response = session.competitions.competition_api_client.get_episode_replay(request)
        response.raise_for_status()
        content = response.content
        replay = orjson.loads(content)
        if replay.get("name") != "kaggriculture" or not replay.get("steps"):
            raise ValueError("invalid public replay response")
        if int(replay["info"]["EpisodeId"]) != episode_id:
            raise ValueError("downloaded replay has the wrong episode ID")
        path = raw / "replays" / f"{episode_id}.json.gz"
        path.parent.mkdir(parents=True, exist_ok=True)
        compressed = gzip.compress(content, compresslevel=3, mtime=0)
        temporary = path.with_suffix(".gz.partial")
        temporary.write_bytes(compressed)
        temporary.replace(path)
        sha256 = hashlib.sha256(compressed).hexdigest()
        write_json(
            path.with_suffix(".source.json"),
            {
                "episode_id": episode_id,
                "retrieved_utc": datetime.now(UTC).isoformat(),
                "url": f"https://www.kaggle.com/api/v1/competitions/episodes/{episode_id}/replay",
                "raw_sha256": hashlib.sha256(content).hexdigest(),
                "compressed_sha256": sha256,
                "raw_bytes": len(content),
            },
        )
        return {
            "episode_id": episode_id,
            "path": str(path),
            "sha256": sha256,
            "bytes": len(compressed),
        }
    except Exception as error:
        response = getattr(error, "response", None)
        headers = {} if response is None else response.headers
        retry_after = headers.get("Retry-After", "120")
        return {
            "episode_id": episode_id,
            "error": str(error),
            "status": getattr(response, "status_code", None),
            "retry_after": int(retry_after) if str(retry_after).isdigit() else 120,
        }


def _paced_fetch(raw: Path, episode_id: int, gate: RequestGate) -> dict[str, Any]:
    """Apply shared pacing to network work while keeping completed workers busy."""
    if not gate.wait():
        return {"episode_id": episode_id, "error": "server_rate_limit_pending", "status": 429}
    result = _fetch(raw, episode_id)
    if result.get("status") == 429:
        gate.defer(result["retry_after"])
    return result


def download_missing(
    raw: Path,
    episodes: list[dict[str, Any]],
    cached: dict[int, Any],
    workers: int,
    request_interval: float,
    maximum_backoffs: int,
) -> tuple[list[Any], list[Any]]:
    """Fetch every missing ID with shared pacing, cooldowns and bounded retries."""
    pending = [episode["id"] for episode in episodes if episode["id"] not in cached]
    completed = list(cached.values())
    failures: list[Any] = []
    gate = RequestGate(raw, request_interval, maximum_backoffs)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for attempt in range(3):
            retry = []
            futures = [pool.submit(_paced_fetch, raw, key, gate) for key in pending]
            remaining = len(futures)
            for future in as_completed(futures):
                result = future.result()
                remaining -= 1
                if "error" not in result:
                    completed.append(result)
                elif (
                    result.get("status") in (None, 429, 500, 502, 503, 504)
                    and attempt < 2
                    and not gate.stopped
                ):
                    retry.append(result["episode_id"])
                else:
                    failures.append(result)
                progress = {
                    "completed": len(completed),
                    "remaining": remaining + len(retry),
                    "failures": failures,
                    "backoffs": gate.backoffs,
                    "updated_utc": datetime.now(UTC).isoformat(),
                }
                write_json(raw / "download-progress.json", progress)
                if remaining % 25 == 0 or "error" in result:
                    print(
                        json.dumps(
                            {
                                "available": len(completed),
                                "pending": remaining + len(retry),
                                "failures": len(failures),
                                "backoffs": gate.backoffs,
                            }
                        ),
                        flush=True,
                    )
            pending = retry
            if not pending:
                break
            if gate.stopped:
                failures.extend(
                    {"episode_id": key, "error": "server_rate_limit_pending"} for key in pending
                )
                break
            time.sleep(2 ** (attempt + 1))
    return completed, failures
