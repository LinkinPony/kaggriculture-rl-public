"""Apply an approved exact-content extent-sharing manifest without deleting files."""

import fcntl
import hashlib
import json
import os
import shutil
import struct
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
from pathlib import Path
from typing import Any

import hydra
from omegaconf import DictConfig, OmegaConf

from kagg_revue.artifacts.io import write_json
from kagg_revue.configuration import FrozenSettings

_DEDUPE_RANGE = 0xC0189436
_CHUNK = 16 * 1024 * 1024


class Deduplication(FrozenSettings):
    """Require an explicit approved manifest and separate execution report."""

    plan: Path
    report: Path
    apply: bool = False


def _identity(path: Path) -> tuple[int, int, int, int, int]:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"not a regular file: {path}")
    record = path.stat()
    return (
        record.st_dev,
        record.st_ino,
        record.st_size,
        record.st_mtime_ns,
        record.st_nlink,
    )


def _digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _verify(
    paths: dict[str, dict[str, Any]], identities: dict[str, tuple[int, int, int, int, int]]
) -> None:
    def check(item: tuple[str, dict[str, Any]]) -> None:
        name, spec = item
        path = Path(name)
        if _identity(path) != identities[name] or _digest(path) != spec["sha256"]:
            raise ValueError(f"model identity changed: {path}")
        if _identity(path) != identities[name]:
            raise ValueError(f"model changed while hashing: {path}")

    with ThreadPoolExecutor(max_workers=4) as executor:
        list(executor.map(check, paths.items()))


def _share(source: Path, destination: Path, size: int) -> int:
    offset = 0
    with source.open("rb") as original, destination.open("r+b") as duplicate:
        while offset < size:
            length = min(_CHUNK, size - offset)
            buffer = bytearray(
                struct.pack(
                    "=QQHHIqQQiI", offset, length, 1, 0, 0, duplicate.fileno(), offset, 0, 0, 0
                )
            )
            fcntl.ioctl(original.fileno(), _DEDUPE_RANGE, buffer, True)
            shared, status = struct.unpack_from("=Qi", buffer, 40)
            if status != 0 or shared != length:
                raise RuntimeError(f"extent sharing failed: {destination}: {status}, {shared}")
            offset += shared
        os.fsync(duplicate.fileno())
    return offset


def run(config: Deduplication) -> dict[str, Any]:
    """Validate every file, share only listed ranges, and validate all bytes again."""
    root = Path.cwd().resolve()
    plan = json.loads(config.plan.read_text())
    if plan["scope_root"] != str(root / "outputs") or plan["planned_file_deletions"] != 0:
        raise ValueError("the approved plan has an unexpected scope")
    manifest = config.plan.parent / "dedup-operations.json"
    if _digest(manifest) != plan["operations_sha256"]:
        raise ValueError("the approved operation manifest changed")
    operations = json.loads(manifest.read_text())
    if len(operations) != plan["destinations"]:
        raise ValueError("the operation count differs from the plan")
    paths: dict[str, dict[str, Any]] = {}
    identities: dict[str, tuple[int, int, int, int, int]] = {}
    aliases: dict[str, tuple[int, int, int, int, int]] = {}
    for operation in operations:
        for role in ("source", "destination"):
            name = operation[role]
            path = Path(name)
            if path.is_absolute() or ".." in path.parts or path.parts[0] != "outputs":
                raise ValueError(f"operation escapes repository outputs: {path}")
            if not path.resolve().is_relative_to(root / "outputs"):
                raise ValueError(f"operation follows an external link: {path}")
            identity = _identity(path)
            expected = (
                operation["device"],
                operation[f"{role}_inode"],
                operation["size_bytes"],
                operation[f"{role}_mtime_ns"],
            )
            if identity[:4] != expected:
                raise ValueError(f"approved file identity changed: {path}")
            if role == "destination" and identity[4] != operation["destination_hard_links"]:
                raise ValueError(f"hardlink count changed: {path}")
            paths[name] = {"sha256": operation["sha256"]}
            identities[name] = identity
        for name in operation["aliases_preserved"]:
            identity = _identity(Path(name))
            if identity != identities[operation["destination"]]:
                raise ValueError(f"hardlink alias changed: {name}")
            aliases[name] = identity
    config.report.mkdir(parents=True, exist_ok=True)
    result: dict[str, Any] = {
        "started_at": time.time(),
        "plan_sha256": _digest(config.plan),
        "manifest_sha256": _digest(manifest),
        "apply": config.apply,
        "disk_before": shutil.disk_usage(root)._asdict(),
        "operations": len(operations),
        "verified_files": len(paths),
    }
    with ExitStack() as locks:
        for run_record in plan["recovery_verification"]:
            for name in ("run.lock", "recovery.lock"):
                stream = locks.enter_context((Path(run_record["run"]) / name).open("a"))
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        print("Verifying all approved sources and destinations", flush=True)
        _verify(paths, identities)
        write_json(config.report / "preflight.json", result)
        if config.apply:
            log_path = config.report / "operations.jsonl"
            if log_path.exists():
                raise FileExistsError("inspect the previous execution before reapplying")
            with log_path.open("x") as log:
                for index, operation in enumerate(operations, 1):
                    source, destination = Path(operation["source"]), Path(operation["destination"])
                    for path in (source, destination):
                        if _identity(path) != identities[str(path)]:
                            raise ValueError(f"file changed before sharing: {path}")
                    shared = _share(source, destination, operation["size_bytes"])
                    if _identity(destination) != identities[str(destination)]:
                        raise ValueError(f"sharing changed file metadata: {destination}")
                    row = {"index": index, **operation, "bytes_shared": shared}
                    log.write(json.dumps(row) + "\n")
                    log.flush()
                    if index % 50 == 0 or index == len(operations):
                        print(f"Shared {index}/{len(operations)} duplicate files", flush=True)
                os.fsync(log.fileno())
            print("Rechecking full hashes and existing hardlink aliases", flush=True)
            _verify(paths, identities)
            for name, alias_identity in aliases.items():
                if _identity(Path(name)) != alias_identity:
                    raise ValueError(f"sharing changed a hardlink alias: {name}")
        result.update(
            passed=True,
            completed_at=time.time(),
            disk_after=shutil.disk_usage(root)._asdict(),
            file_paths_deleted=0,
            independent_hashes_unchanged=True,
            inode_mtime_hardlinks_unchanged=True,
        )
        result["disk_free_increase_bytes"] = (
            result["disk_after"]["free"] - result["disk_before"]["free"]
        )
        write_json(config.report / "result.json", result)
    return result


@hydra.main(
    version_base=None,
    config_path=str(Path(__file__).resolve().parents[3] / "configs"),
    config_name="artifact_deduplication",
)
def main(configuration: DictConfig) -> None:
    """Resolve the explicit operation manifest through Hydra."""
    config = Deduplication.model_validate(
        OmegaConf.to_container(configuration.deduplication, resolve=True)
    )
    print(json.dumps(run(config)), flush=True)


if __name__ == "__main__":
    main()
