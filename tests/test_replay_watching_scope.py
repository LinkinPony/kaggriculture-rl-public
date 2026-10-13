import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from kagg_revue.artifacts.io import write_json
from kagg_revue.datasets.watching import collection, discovery
from kagg_revue.datasets.watching.config import WatchSettings
from kagg_revue.datasets.watching.records import load_manifest, save_manifest


def episode(key: int, submission: int) -> dict[str, Any]:
    return {
        "id": key,
        "createTime": "2026-09-22T01:00:00Z",
        "state": "COMPLETED",
        "type": "EPISODE_TYPE_PUBLIC",
        "agents": [{"teamId": 2, "submissionId": submission}],
    }


def test_fixed_submission_cutoff_preserves_history_and_does_not_expire(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = WatchSettings(
        raw=tmp_path,
        team_id=2,
        team_name="DSM",
        scan_own_history=False,
        submitted_since=datetime(2026, 9, 17, tzinfo=UTC),
        seed_episodes=(1,),
    )
    manifest = load_manifest(config)
    manifest["submissions"] = [
        {"id": 19, "dateSubmitted": "2026-09-16T23:59:59Z"},
        {"id": 20, "dateSubmitted": "2026-09-17T00:00:00Z"},
        {"id": 21, "dateSubmitted": "2026-10-10T00:00:00Z"},
        {"id": 22},
    ]
    manifest["episodes"] = [episode(1, 19), episode(2, 20)]
    existing = tmp_path / "old-replay.gz"
    existing.write_bytes(b"preserve previous download")
    manifest["replays"] = [{"episode_id": 1, "path": str(existing), "bytes": 26}]
    save_manifest(config, manifest)
    write_json(
        tmp_path / "submission-dates/22.json",
        {
            "submissions": [{"id": 22, "teamId": 2, "dateSubmitted": "2026-09-16T01:00:00Z"}],
        },
    )
    queried = []

    class Client:
        def metadata(self, path: Path, method: str, request_type: str, **fields: Any) -> Any:
            if method == "list_team_public_submissions":
                return {"submissions": []}
            queried.append(fields["submission_id"])
            return {"episodes": [episode(fields["submission_id"], fields["submission_id"])]}

    monkeypatch.setattr(discovery, "Client", Client)
    monkeypatch.setattr(discovery.time, "sleep", lambda _: None)
    for _ in range(2):
        manifest = load_manifest(config)
        assert not discovery.discover(config, manifest)
        assert {r["id"] for r in manifest["submissions"]} == {20, 21}
        assert {r["id"] for r in manifest["episodes"]} == {2, 20, 21}
        assert {r["id"] for r in manifest["outside_scope"]["submissions"]} == {19, 22}
        assert manifest["outside_scope"]["replays"][0]["episode_id"] == 1
        assert existing.read_bytes() == b"preserve previous download"
    assert queried == [21, 20, 21, 20]


def test_daily_members_remain_in_dataset_and_are_never_downloaded_twice(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    daily = tmp_path / "daily"
    daily.mkdir()
    config = WatchSettings(raw=tmp_path, team_id=2, team_name="DSM", daily_archive_root=daily)
    manifest = load_manifest(config)
    manifest["episodes"] = [episode(1, 20), episode(2, 20)]
    save_manifest(config, manifest)
    payload = json.dumps({"name": "kaggriculture", "steps": [[{"status": "DONE"}]]})
    with zipfile.ZipFile(daily / "kaggriculture-episodes-2026-09-21.zip", "w") as archive:
        archive.writestr("1.json", payload)
    fetched = []

    def download(raw: Path, rows: list[Any], cached: dict[int, Any], *args: Any) -> Any:
        fetched.extend(r["id"] for r in rows)
        return [], [{"episode_id": r["id"], "status": 404} for r in rows]

    monkeypatch.setattr(collection, "discover", lambda *args: [])
    monkeypatch.setattr(collection, "download_missing", download)
    first = collection.collect(config)
    assert first["episodes"] == 2 and first["available"] == first["reused_daily"] == 1
    assert fetched == [2]
    manifest = load_manifest(config)
    assert {r["id"] for r in manifest["episodes"]} == {1, 2}
    reference = manifest["replays"][0]
    with zipfile.ZipFile(reference["path"]) as archive:
        assert archive.read(reference["member"]).decode() == payload
    assert not (tmp_path / "replays/1.json.gz").exists()
    with zipfile.ZipFile(daily / "kaggriculture-episodes-2026-09-22.zip", "w") as archive:
        archive.writestr("2.json", payload)
    second = collection.collect(config)
    assert second["episodes"] == second["available"] == second["reused_daily"] == 2
    assert second["pending"] == 0 and fetched == [2]
