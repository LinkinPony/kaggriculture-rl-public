import hashlib
import io
import json
import tarfile
from pathlib import Path

import pytest

from kagg_revue.deployment.archive import unpack


@pytest.mark.parametrize("mutation", [None, "content", "escape", "symlink"])
def test_archive_checks_members_and_manifest_even_with_matching_archive_digest(
    tmp_path: Path, mutation: str | None
) -> None:
    source = b"def agent(observation, configuration): return {}\n"
    manifest = {
        "schema_version": "random-root-grounded-submission-v1",
        "files": [
            {
                "path": "main.py",
                "sha256": hashlib.sha256(source).hexdigest(),
                "size_bytes": len(source),
            }
        ],
    }
    archive = tmp_path / "candidate.tar.gz"
    with tarfile.open(archive, "w:gz") as stream:
        content = source + b"# changed\n" if mutation == "content" else source
        info = tarfile.TarInfo("../escaped.py" if mutation == "escape" else "main.py")
        if mutation == "symlink":
            info.type = tarfile.SYMTYPE
            info.linkname = "../escaped.py"
        else:
            info.size = len(content)
        stream.addfile(info, io.BytesIO(content) if info.isfile() else None)
        encoded = json.dumps(manifest).encode()
        info = tarfile.TarInfo("manifest.json")
        info.size = len(encoded)
        stream.addfile(info, io.BytesIO(encoded))
    expected = hashlib.sha256(archive.read_bytes()).hexdigest()
    destination = tmp_path / "unpacked"
    if mutation is None:
        unpack(archive, expected, destination)
        assert (destination / "main.py").read_bytes() == source
    else:
        with pytest.raises(ValueError):
            unpack(archive, expected, destination)
        assert not destination.exists()
        assert not (tmp_path / "escaped.py").exists()
