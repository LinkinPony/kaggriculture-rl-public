"""Checksum-verified immutable uploads through rclone's renewable OAuth credentials."""

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from kagg_revue.deployment.publishing.config import Publishing


def _command(config: Publishing, arguments: list[str]) -> str:
    result = subprocess.run(
        [
            str(config.rclone),
            *arguments,
            "--config",
            str(config.rclone_config),
            "--contimeout",
            "15s",
            "--timeout",
            "60s",
            "--retries",
            "3",
            "--low-level-retries",
            "5",
            "--log-level",
            "INFO",
            "--log-file",
            str(config.output_dir / "transfer.log"),
            "--stats",
            "30s",
            "--stats-one-line",
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=config.upload_timeout_seconds,
    )
    return result.stdout


def upload(config: Publishing, source: Path, name: str) -> dict[str, Any]:
    """Copy one file, refusing replacement, and verify Drive's returned MD5 and size."""
    target = f"{config.remote}:{config.folder}/{name}"
    _command(config, ["copyto", str(source), target, "--immutable", "--checksum"])
    remote = json.loads(_command(config, ["lsjson", target, "--stat", "--hash"]))
    with source.open("rb") as stream:
        expected = hashlib.file_digest(stream, "md5").hexdigest()
    hashes = {key.lower(): value for key, value in remote.get("Hashes", {}).items()}
    if remote["Size"] != source.stat().st_size or hashes.get("md5") != expected:
        raise ValueError("uploaded file differs from the local archive")
    return {
        "path": target,
        "id": remote.get("ID"),
        "md5": expected,
        "size_bytes": remote["Size"],
        "url": f"https://drive.google.com/file/d/{remote['ID']}/view" if remote.get("ID") else None,
    }
