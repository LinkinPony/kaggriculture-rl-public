"""Retention races, half-hour cadence and resumable verified submission uploads."""

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.deployment.publishing import drive, queue, service, sources
from kagg_revue.deployment.publishing.config import Publishing
from kagg_revue.deployment.publishing.metadata import describe
from kagg_revue.deployment.snapshots import capture
from kagg_revue.native.settings import NativeBuildSettings


def configuration(run: Path) -> Publishing:
    """Use explicit local fixture runs with no automatic trainer discovery."""
    return Publishing(
        runs=(run,),
        discover_active=False,
        native=NativeBuildSettings(
            interpreters=(Path("/usr/bin/python3"),),
            compiler=Path("/usr/bin/c++"),
            patchelf=Path("/usr/bin/patchelf"),
            max_glibc="2.35",
            jobs=1,
        ),
    )


def fixture_run(run: Path) -> dict[str, Any]:
    """Publish a minimal committed ledger with replaceable checkpoint bytes."""
    member = "checkpoints/update-000004.pt"
    path = run / member
    path.parent.mkdir(parents=True)
    path.write_bytes(b"committed checkpoint")
    state = {
        "run_id": "fixture",
        "latest": member,
        "completed_update": 4,
        "protocol": {"output_dir": str(run), "seed": 123},
        "members": {member: digest(path)},
    }
    write_json(run / "state.json", state)
    write_json(run / "run-status.json", {"status": "running", "run_id": "fixture"})
    return state


def test_capture_survives_retention_and_rejects_wrong_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A pinned inode survives retirement; corrupt checkpoints never become queued inputs."""
    monkeypatch.chdir(tmp_path)
    run = Path("outputs/learning/test")
    state = fixture_run(run)
    snapshot = Path("outputs/deployment/snapshot")
    capture(run, state, snapshot)
    (run / state["latest"]).unlink()
    assert digest(snapshot / "checkpoint.pt") == state["members"][state["latest"]]
    (run / state["latest"]).write_bytes(b"changed bytes")
    with pytest.raises(ValueError, match="authenticated"):
        capture(run, state, snapshot.with_name("invalid"))
    assert not snapshot.with_name("invalid").exists()


def test_half_hour_restart_and_final_capture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Restart does not duplicate a slot, and completion retains the last selected model."""
    monkeypatch.chdir(tmp_path)
    run = Path("outputs/learning/test")
    fixture_run(run)
    config = configuration(run)
    monkeypatch.setattr(sources, "alive", lambda status: status["status"] == "running")
    registry: dict[str, Any] = {}
    queue.enqueue(config, registry, 1801)
    assert len(queue.pending(config, 1801)) == 1
    registry = json.loads((config.output_dir / "registry.json").read_text())
    queue.enqueue(config, registry, 1850)
    assert len(queue.pending(config, 1850)) == 1
    queue.enqueue(config, registry, 3601)
    assert len(queue.pending(config, 3601)) == 2
    write_json(run / "run-status.json", {"status": "complete", "run_id": "fixture"})
    queue.enqueue(config, registry, 3610)
    queue.enqueue(config, registry, 7201)
    assert len(queue.pending(config, 7201)) == 3


def test_partial_upload_retries_without_rebuilding(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An upload error leaves the same ready tar pending until every sidecar is verified."""
    monkeypatch.chdir(tmp_path)
    config = configuration(Path("outputs/learning/test"))
    job = config.output_dir / "jobs" / "test"
    job.mkdir(parents=True)
    archive = job / "submission.tar.gz"
    archive.write_bytes(b"stable archive")
    write_json(job / "job.json", {})
    write_json(job / "ready.json", {"path": str(archive), "sha256": digest(archive)})
    write_json(job / "smoke.json", {"ok": True})
    write_json(job / "submission-info.json", {"description": "fixture"})
    (job / "submission-info.txt").write_text("fixture\n")
    calls = []

    def upload(_: Publishing, source: Path, name: str) -> dict[str, Any]:
        calls.append(name)
        if len(calls) == 2:
            raise RuntimeError("temporary network outage")
        return {"path": name, "sha256": digest(source)}

    monkeypatch.setattr(service, "upload", upload)
    service.process(config, job)
    assert not (job / "uploaded.json").exists()
    assert (job / "failure.json").exists()
    fresh = job.with_name("fresh")
    write_json(fresh / "job.json", {"captured_utc": "later"})
    retry_at = json.loads((job / "failure.json").read_text())["retry_at"]
    assert queue.pending(config, retry_at + 1) == [fresh, job]
    service.process(config, job)
    assert (job / "uploaded.json").is_file()
    assert not (job / "failure.json").exists()
    assert archive.read_bytes() == b"stable archive"
    assert calls.count("test/submission.tar.gz") == 1


@pytest.mark.parametrize("hash_key", ["MD5", "md5"])
def test_drive_rejects_remote_checksum_mismatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, hash_key: str
) -> None:
    """A successful transfer command alone is insufficient to acknowledge delivery."""
    source = tmp_path / "archive"
    source.write_bytes(b"payload")
    wrong = hashlib.md5(b"wrong").hexdigest()
    monkeypatch.setattr(
        drive,
        "_command",
        lambda *_: json.dumps(
            {
                "Size": source.stat().st_size,
                "Hashes": {hash_key: wrong},
            }
        ),
    )
    with pytest.raises(ValueError, match="differs"):
        drive.upload(configuration(Path("outputs/learning/test")), source, "submission.tar.gz")
    expected = hashlib.md5(source.read_bytes()).hexdigest()
    monkeypatch.setattr(
        drive,
        "_command",
        lambda *_: json.dumps({"Size": source.stat().st_size, "Hashes": {hash_key: expected}}),
    )
    uploaded = drive.upload(
        configuration(Path("outputs/learning/test")), source, "submission.tar.gz"
    )
    assert uploaded["md5"] == expected


def test_bc_description_uses_selected_epoch_not_final_epoch() -> None:
    """An early-stopped BC package labels the actual selected weights and temperature."""
    run = Path("outputs/learning/bc")
    member = "pretraining/shard-000416.pt"
    state = {
        "protocol": {"seed": 101204},
        "run_id": "bc",
        "completed_update": 0,
        "members": {member: "a" * 64},
        "pretraining": {
            "records": [{}] * 12,
            "early_stopping": {"best_member": member, "best_epoch": 8},
        },
    }
    info = describe(
        configuration(run),
        {
            "member": member,
            "run": str(run),
            "captured_utc": "test",
            "training_status": "complete",
        },
        state,
    )
    assert "BC E8" in info["description"]
    assert "FP32 T=0; ckpt aaaaaaaa" in info["description"]
    assert info["bc_completed_epochs"] == 12
