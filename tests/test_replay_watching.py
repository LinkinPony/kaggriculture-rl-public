import gzip
import json
from pathlib import Path
from typing import Any

import pytest

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.datasets.watching import collection, discovery
from kagg_revue.datasets.watching.config import WatchSettings
from kagg_revue.datasets.watching.exclusions import purge
from kagg_revue.datasets.watching.records import cached_record, load_manifest, save_manifest


def episode(key: int, submission: int = 20) -> dict[str, Any]:
    return {
        "id": key,
        "state": "COMPLETED",
        "type": "EPISODE_TYPE_PUBLIC",
        "agents": [{"teamId": 2, "submissionId": submission, "reward": key % 2}],
    }


def artifact(raw: Path, key: int) -> dict[str, Any]:
    path = raw / "replays" / f"{key}.json.gz"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        gzip.compress(
            json.dumps(
                {
                    "info": {"EpisodeId": key, "TeamNames": ["A", "Target"]},
                    "statuses": ["DONE", "DONE"],
                    "steps": [],
                }
            ).encode()
        )
    )
    write_json(
        path.with_suffix(".source.json"),
        {
            "compressed_sha256": digest(path),
            "retrieved_utc": "2026-09-22T00:00:00Z",
            "url": f"https://www.kaggle.com/api/v1/competitions/episodes/{key}/replay",
        },
    )
    return {"episode_id": key}


def test_history_pages_discover_old_versions_and_survive_public_disappearance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = WatchSettings(raw=tmp_path, team_id=2, team_name="Target")
    manifest = load_manifest(config)
    calls = []
    second_cycle = False

    class Client:
        def metadata(self, path: Path, method: str, request_type: str, **fields: Any) -> Any:
            calls.append((method, fields))
            if method == "list_team_public_submissions":
                return {"submissions": [] if second_cycle else [{"id": 20}]}
            if method == "list_submissions":
                if "page_token" not in fields:
                    return {"submissions": [{"ref": 100}], "nextPageToken": "next"}
                assert fields["page_token"] == "next"
                return {"submissions": [{"ref": 101}]}
            key = fields["submission_id"]
            if key == 100:
                return {"episodes": [episode(1, 19), episode(1, 19)]}
            if key == 101:
                return {
                    "episodes": [
                        {**episode(2), "state": "ACTIVE"},
                        {**episode(3), "type": "EPISODE_TYPE_VALIDATION"},
                    ]
                }
            if key == 19 and second_cycle:
                raise RuntimeError("temporarily unavailable")
            return {"episodes": [episode(4, key)]}

    monkeypatch.setattr(discovery, "Client", Client)
    monkeypatch.setattr(discovery.time, "sleep", lambda _: None)
    assert not discovery.discover(config, manifest)
    assert manifest["own_submission_ids"] == [100, 101]
    assert {row["id"] for row in manifest["submissions"]} == {19, 20}
    assert {row["id"] for row in manifest["episodes"]} == {1, 4}
    assert next(row for row in manifest["submissions"] if row["id"] == 19)[
        "evidence_episode_ids"
    ] == [1, 4]
    second_cycle = True
    calls.clear()
    errors = discovery.discover(config, manifest)
    assert errors[0]["submission_id"] == 19
    assert {row["id"] for row in manifest["episodes"]} == {1, 4}
    assert not any(method == "list_submissions" for method, _ in calls)


def test_restart_reuses_published_files_and_failures_do_not_starve_new_games(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = WatchSettings(raw=tmp_path, team_id=2, team_name="Target", downloads_per_cycle=2)
    manifest = load_manifest(config)
    manifest["episodes"] = [episode(key) for key in (1, 2, 3)]
    write_json(tmp_path / "manifest.json", manifest)
    artifact(tmp_path, 1)  # Simulate a kill after download, before manifest publication.
    monkeypatch.setattr(collection, "discover", lambda *args: [])
    fetched = []

    def download(raw: Path, rows: list[Any], cached: dict[int, Any], *args: Any) -> Any:
        result = list(cached.values())
        failures = []
        for row in rows:
            key = row["id"]
            if key in cached:
                continue
            fetched.append(key)
            if key == 2:
                failures.append({"episode_id": 2, "error": "unavailable", "status": 404})
            else:
                result.append(artifact(raw, key))
        return result, failures

    monkeypatch.setattr(collection, "download_missing", download)
    first = collection.collect(config)
    assert first["available"] == 1
    assert first["failures"] == 1
    second = collection.collect(config.model_copy(update={"downloads_per_cycle": 1}))
    assert second["available"] == 2
    assert fetched == [2, 3]
    saved = load_manifest(config)
    assert saved["pending_episode_ids"] == [2]
    assert {row["episode_id"] for row in saved["replays"]} == {1, 3}


def test_interrupted_provenance_is_preserved_and_hash_corruption_is_rejected(
    tmp_path: Path,
) -> None:
    artifact(tmp_path, 1)
    path = tmp_path / "replays/1.json.gz"
    path.with_suffix(".source.json").unlink()
    assert cached_record(tmp_path, episode(1)) is None
    assert len(list(path.parent.glob("*.unverified-*"))) == 1
    artifact(tmp_path, 1)
    path.write_bytes(path.read_bytes() + b"corrupt")
    with pytest.raises(ValueError, match="hash differs"):
        cached_record(tmp_path, episode(1))


def test_excluded_submission_is_purged_and_not_rediscovered(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = WatchSettings(
        raw=tmp_path,
        team_id=2,
        team_name="Target",
        seed_submissions=(21,),
        seed_episodes=(1,),
        excluded_submissions=(20,),
        history_sources=(tmp_path / "local-history.json",),
    )
    rejected = episode(1, 20)
    mixed = episode(3, 21)
    mixed["agents"].append({"teamId": 3, "submissionId": 20})
    accepted = episode(2, 21)
    rows = [rejected, accepted, mixed]
    manifest = load_manifest(config)
    manifest["submissions"] = [{"id": 20}, {"id": 21, "evidence_episode_ids": [2, 3]}]
    manifest["episodes"] = rows
    manifest["replays"] = [artifact(tmp_path, key) for key in (1, 2, 3)]
    manifest["download_attempts"] = {str(key): 1 for key in (1, 2, 3)}
    write_json(tmp_path / "manifest.json", manifest)
    write_json(config.history_sources[0], {"episodes": rows})
    original = (tmp_path / "replays/2.json.gz").read_bytes()
    receipt = purge(config, tmp_path / "purge-receipt.json")
    assert receipt["after"] == {"submissions": 1, "episodes": 1, "replays": 1}
    assert not (tmp_path / "replays/1.json.gz").exists()
    assert not (tmp_path / "replays/3.json.source.json").exists()
    assert (tmp_path / "replays/2.json.gz").read_bytes() == original
    manifest = load_manifest(config)
    calls = []

    class Client:
        def metadata(self, path: Path, method: str, request_type: str, **fields: Any) -> Any:
            if method == "list_team_public_submissions":
                return {"submissions": [{"id": 20}, {"id": 21}]}
            if method == "list_submissions":
                return {"submissions": [{"ref": 100}]}
            calls.append(fields["submission_id"])
            return {"episodes": [*rows, episode(4, 21), episode(5, 20)]}

    monkeypatch.setattr(discovery, "Client", Client)
    monkeypatch.setattr(discovery.time, "sleep", lambda _: None)
    assert not discovery.discover(config, manifest)
    assert {r["id"] for r in manifest["submissions"]} == {21}
    assert {r["id"] for r in manifest["episodes"]} == {2, 4}
    assert manifest["excluded_episode_ids"] == [1, 3]
    assert 20 not in calls
    restarted = load_manifest(config)
    assert not discovery.discover(config, restarted)
    assert {r["id"] for r in restarted["episodes"]} == {2, 4}


def test_submission_cannot_be_seeded_and_excluded(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="seed submission"):
        WatchSettings(
            raw=tmp_path,
            team_id=2,
            team_name="Target",
            seed_submissions=(20,),
            excluded_submissions=(20,),
        )


def test_retired_submission_is_removed_from_active_and_outside_scope(tmp_path: Path) -> None:
    config = WatchSettings(raw=tmp_path, team_id=2, team_name="Target", excluded_submissions=())
    assert 56484772 in config.excluded_submissions
    manifest = load_manifest(config)
    manifest["submissions"] = [{"id": 21, "evidence_episode_ids": [1, 2, 3]}]
    manifest["episodes"] = [episode(1, 56484772), episode(2, 21)]
    manifest["replays"] = [artifact(tmp_path, key) for key in (1, 2)]
    manifest["outside_scope"] = {
        "submissions": [{"id": 56484772}],
        "episodes": [episode(3, 56484772)],
        "replays": [artifact(tmp_path, 3)],
        "undated_submission_ids": [56484772],
    }
    save_manifest(config, manifest)
    reloaded = load_manifest(config)
    assert [e["id"] for e in reloaded["episodes"]] == [2]
    assert reloaded["excluded_episode_ids"] == [1, 3]
    assert reloaded["submissions"][0]["evidence_episode_ids"] == [2]
    assert all(not value for value in reloaded["outside_scope"].values())
    assert all((tmp_path / f"replays/{key}.json.gz").exists() for key in (1, 2, 3))
