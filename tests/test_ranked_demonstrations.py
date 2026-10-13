import gzip
import json
import zipfile
from pathlib import Path
from typing import Any

import pytest

from kagg_revue.artifacts.io import write_json
from kagg_revue.datasets.ranked import acquisition, downloads
from kagg_revue.datasets.ranked.metadata import replay_header


@pytest.mark.parametrize("container", ["zip", "gzip"])
def test_bounded_replay_header_preserves_unicode_and_rejects_wrong_identity(
    tmp_path: Path, container: str
) -> None:
    payload = json.dumps(
        {
            "info": {"EpisodeId": 121, "TeamNames": ["队伍", "B"]},
            "statuses": ["DONE", "DONE"],
            "steps": "é" * 65536,
        },
        ensure_ascii=False,
    ).encode()
    if container == "zip":
        path, member, wrong = tmp_path / "archive.zip", "121.json", "122.json"
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr(member, payload)
            archive.writestr(wrong, payload)
        header = replay_header(path, member)
        with pytest.raises(ValueError, match="identity differs"):
            replay_header(path, wrong)
    else:
        path = tmp_path / "121.json.gz"
        path.write_bytes(gzip.compress(payload))
        header = replay_header(path)
        wrong_path = tmp_path / "122.json.gz"
        wrong_path.write_bytes(path.read_bytes())
        with pytest.raises(ValueError, match="identity differs"):
            replay_header(wrong_path)
    assert header["info"]["TeamNames"] == ["队伍", "B"]
    assert header["statuses"] == ["DONE", "DONE"]


def test_supplements_require_submission_score_and_keep_both_wins_and_losses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    write_json(raw / "leaderboard.source.json", {"retrieved_utc": "2026-09-13T00:00:00+00:00"})
    write_json(raw / "leaderboard.json", {})
    daily = raw / "daily.json"
    write_json(daily, {"daily_archives": []})
    episodes = [
        {
            "id": key,
            "state": "COMPLETED",
            "type": "EPISODE_TYPE_PUBLIC",
            "endTime": "2026-09-12T01:00:00Z",
            "agents": [{"submissionId": 12, "reward": reward}],
        }
        for key, reward in ((1, 100), (2, 0))
    ]
    episodes += [
        {**episodes[0], "id": 3, "type": "EPISODE_TYPE_VALIDATION"},
        {**episodes[0], "id": 4, "endTime": "2026-09-13T01:00:00Z"},
    ]

    class Client:
        def metadata(self, path: Path, method: str, request_type: str, **fields: Any) -> Any:
            if method == "get_leaderboard":
                return {
                    "submissions": [
                        {"teamId": 1, "teamName": "A", "score": "3100"},
                        {"teamId": 2, "teamName": "B", "score": "3050"},
                    ]
                }
            if method == "list_team_public_submissions":
                assert fields["team_id"] == 1
                return {
                    "submissions": [
                        {"id": 11, "publicScore": "2900"},
                        {"id": 12, "publicScore": "3000"},
                        {"id": 13, "publicScore": "2500"},
                    ]
                }
            assert fields["submission_id"] == 12
            return {"episodes": episodes + [episodes[0]]}

    monkeypatch.setattr(acquisition, "Client", Client)
    monkeypatch.setattr(acquisition, "cached_replays", lambda *args: {})
    monkeypatch.setattr(
        acquisition,
        "download_missing",
        lambda raw, items, *args: ([{"episode_id": item["id"]} for item in items], []),
    )
    path = acquisition.acquire(
        acquisition.Acquisition(raw=raw, daily_manifest=daily, maximum_rank=1)
    )
    manifest = json.loads(path.read_text())
    assert [version["id"] for version in manifest["submissions"]] == [12]
    assert {episode["episode_id"] for episode in manifest["replays"]} == {1, 2}
    assert {version["id"] for version in manifest["excluded_submissions"]} == {11, 13}


def test_retry_after_delays_all_new_episode_requests(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[int] = []
    sleeps: list[float] = []
    now = [0.0]

    def sleep(seconds: float) -> None:
        sleeps.append(seconds)
        now[0] += seconds

    def fetch(raw: Path, episode_id: int) -> dict[str, Any]:
        calls.append(episode_id)
        if len(calls) == 1:
            return {
                "episode_id": episode_id,
                "error": "rate limited",
                "status": 429,
                "retry_after": 65,
            }
        assert sum(sleeps) >= 65
        return {"episode_id": episode_id}

    monkeypatch.setattr(downloads, "_fetch", fetch)
    monkeypatch.setattr(downloads.time, "sleep", sleep)
    monkeypatch.setattr(downloads.time, "time", lambda: now[0])
    completed, failures = downloads.download_missing(tmp_path, [{"id": 1}, {"id": 2}], {}, 1, 0, 1)
    assert calls == [1, 2, 1]
    assert all(pause <= 30 for pause in sleeps)
    assert {row["episode_id"] for row in completed} == {1, 2}
    assert not failures
