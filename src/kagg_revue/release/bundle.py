"""Prepare private dataset files from authenticated final submission archives."""

import gzip
import hashlib
import io
import json
import tarfile
from pathlib import Path
from typing import Any

import hydra
from omegaconf import DictConfig, OmegaConf
from pydantic import Field

from kagg_revue.configuration import FrozenSettings
from kagg_revue.release.redaction import redact_actor, redact_elf, redact_text


class Artifact(FrozenSettings):
    """Identify one original, immutable competition submission."""

    name: str = Field(pattern=r"^[a-z0-9-]+$")
    submission_id: int
    source: Path
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class Release(FrozenSettings):
    """Select explicit inputs and a separate output directory."""

    output: Path
    artifacts: tuple[Artifact, ...]


def digest(data: bytes) -> str:
    """Hash serialized bytes consistently across nested archive formats."""
    return hashlib.sha256(data).hexdigest()


def json_bytes(value: Any) -> bytes:
    """Encode deterministic readable metadata."""
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def read_archive(path: Path, expected: str) -> dict[str, bytes]:
    """Authenticate all regular files without extracting links or unsafe paths."""
    raw = path.read_bytes()
    if digest(raw) != expected:
        raise ValueError("original submission archive hash differs")
    files = {}
    with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
        for member in archive.getmembers():
            path = Path(member.name)
            if path.is_absolute() or ".." in path.parts or member.issym() or member.islnk():
                raise ValueError("unsafe submission archive member")
            if member.isdir():
                continue
            stream = archive.extractfile(member)
            if not member.isfile() or stream is None or member.name in files:
                raise ValueError("unsupported or duplicated archive member")
            files[member.name] = stream.read()
    manifest = json.loads(files["manifest.json"])
    expected_names = {row["path"] for row in manifest["files"]} | {"manifest.json"}
    if set(files) != expected_names:
        raise ValueError("archive members differ from manifest")
    for row in manifest["files"]:
        data = files[row["path"]]
        if digest(data) != row["sha256"] or len(data) != row["size_bytes"]:
            raise ValueError("original submission member hash or size differs")
    return files


def write_archive(files: dict[str, bytes], target: Path) -> None:
    """Write a deterministic tar with anonymous ownership and timestamps."""
    with (
        target.open("wb") as stream,
        gzip.GzipFile(fileobj=stream, mode="wb", mtime=0, filename="") as compressed,
        tarfile.open(fileobj=compressed, mode="w") as archive,
    ):
        for name, data in sorted(files.items()):
            member = tarfile.TarInfo(name)
            member.size = len(data)
            member.mode = 0o644
            archive.addfile(member, io.BytesIO(data))


def prepare(artifact: Artifact, output: Path, root: Path) -> dict[str, Any]:
    """Sanitize metadata and debug paths, then bind the revised package hashes."""
    files = read_archive(artifact.source, artifact.sha256)
    original_actor = digest(files["actor.pt"])
    files["actor.pt"], debug_changes = redact_actor(files["actor.pt"])
    elf_changes = {}
    for name in files:
        if name.endswith(".so"):
            files[name], elf_changes[name] = redact_elf(files[name])
    profile = json.loads(redact_text(files["agent_profile.json"].decode()))
    manifest = json.loads(redact_text(files["manifest.json"].decode()))
    profile["actor_sha256"] = digest(files["actor.pt"])
    for metadata in (profile, manifest):
        for binary in metadata["native_binaries"]:
            binary["sha256"] = digest(files[binary["archive_path"]])
            binary["size_bytes"] = len(files[binary["archive_path"]])
    files["agent_profile.json"] = json_bytes(profile)
    manifest["actor_artifact"].update(
        sha256=profile["actor_sha256"], size_bytes=len(files["actor.pt"])
    )
    provenance = {
        "schema_version": 1,
        "submission_id": artifact.submission_id,
        "original_archive_sha256": artifact.sha256,
        "original_actor_sha256": original_actor,
        "checkpoint_sha256": manifest["checkpoint_sha256"],
        "changes": {
            "torchscript_debug_members": debug_changes,
            "unused_elf_path_strings": elf_changes,
            "metadata": "Local build paths replaced; hashes regenerated; license notices added.",
        },
        "invariant": "Every non-debug TorchScript ZIP member is byte-identical to the original.",
        "scope": (
            "Sanitized distribution of the final submitted policy; "
            "not the byte-identical competition tar."
        ),
    }
    files["release-provenance.json"] = json_bytes(provenance)
    for path in (root / "LICENSE", root / "NOTICE", *sorted((root / "LICENSES").glob("*.txt"))):
        files[str(path.relative_to(root))] = path.read_bytes()
    manifest["release"] = provenance
    manifest["files"] = [
        {"path": name, "sha256": digest(data), "size_bytes": len(data)}
        for name, data in sorted(files.items())
        if name != "manifest.json"
    ]
    files["manifest.json"] = json_bytes(manifest)
    destination = output / f"{artifact.name}.tar.gz"
    write_archive(files, destination)
    released = destination.read_bytes()
    read_archive(destination, digest(released))
    return {
        "name": artifact.name,
        "filename": destination.name,
        "submission_id": artifact.submission_id,
        "sha256": digest(released),
        "size_bytes": len(released),
        "provenance": provenance,
    }


@hydra.main(version_base=None, config_path=None, config_name=None)
def main(configuration: DictConfig) -> None:
    """Prepare local artifacts only; this command never uploads or changes visibility."""
    config = Release.model_validate(OmegaConf.to_container(configuration.release, resolve=True))
    config.output.mkdir(parents=True, exist_ok=False)
    root = Path(__file__).resolve().parents[3]
    rows = [prepare(artifact, config.output, root) for artifact in config.artifacts]
    (config.output / "manifest.json").write_bytes(
        json_bytes({"schema_version": 1, "artifacts": rows})
    )
    print(
        json.dumps(
            {"artifacts": [{k: v for k, v in row.items() if k != "provenance"} for row in rows]}
        )
    )


if __name__ == "__main__":
    main()
