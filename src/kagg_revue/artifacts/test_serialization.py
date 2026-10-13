"""Archive fidelity, portable fallback and atomic failure behavior."""

import errno
import zipfile
from pathlib import Path
from typing import Any

import pytest
import torch

from kagg_revue.artifacts import serialization


def test_roundtrip_views_and_crc(tmp_path: Path) -> None:
    """Keep shared storage, noncontiguous views, scalars and valid ZIP CRCs."""
    source = torch.arange(14000, dtype=torch.float32)
    payload: dict[str, Any] = {
        "base": source,
        "view": source[3::7],
        "scalar": torch.tensor(9),
        "step": 23,
    }
    path = tmp_path / "checkpoint.pt"
    serialization.save(payload, path)
    restored = torch.load(path, weights_only=False)
    assert all(torch.equal(payload[key], restored[key]) for key in ("base", "view", "scalar"))
    assert restored["step"] == 23
    restored["base"][3] = 777
    assert restored["view"][0] == 777
    with zipfile.ZipFile(path) as archive:
        assert archive.testzip() is None
    assert not path.with_suffix(".partial").exists()


def test_unsupported_direct_write_falls_back(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Restart a partial direct write through the portable writer on unsupported filesystems."""

    def unavailable(path: Path, data: memoryview) -> None:
        path.write_bytes(b"partial")
        raise OSError(errno.EINVAL, "unsupported direct I/O")

    monkeypatch.setattr(serialization, "_direct", unavailable)
    path = tmp_path / "checkpoint.pt"
    serialization.save({"value": torch.arange(11)}, path)
    assert torch.equal(torch.load(path, weights_only=False)["value"], torch.arange(11))


def test_write_failure_preserves_previous(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """An actual storage failure must preserve the published checkpoint and propagate."""

    def full(path: Path, data: memoryview) -> None:
        path.write_bytes(b"partial")
        raise OSError(errno.ENOSPC, "disk full")

    path = tmp_path / "checkpoint.pt"
    path.write_bytes(b"previous")
    monkeypatch.setattr(serialization, "_direct", full)
    with pytest.raises(OSError, match="disk full"):
        serialization.save({"value": torch.arange(11)}, path)
    assert path.read_bytes() == b"previous"
    assert not path.with_suffix(".partial").exists()
