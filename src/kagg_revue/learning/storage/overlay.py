"""Patch storage functions into an archived runtime without changing training math."""

import ast
import hashlib
import json
import tarfile
from pathlib import Path
from typing import Any

from kagg_revue.artifacts.io import digest, write_json

_PACKAGE = Path("src/kagg_revue/learning")
_RUNTIME = ("__init__.py", "roles.py", "artifacts.py", "publication.py", "verification.py")


def _replace_function(old: str, new: str, name: str) -> str:
    def locate(source: str) -> ast.FunctionDef:
        matches = [
            node
            for node in ast.walk(ast.parse(source))
            if isinstance(node, ast.FunctionDef) and node.name == name
        ]
        if len(matches) != 1:
            raise ValueError(f"expected exactly one archived function {name}")
        return matches[0]

    previous, replacement = locate(old), locate(new)
    lines = old.splitlines(keepends=True)
    lines[previous.lineno - 1 : previous.end_lineno] = new.splitlines(keepends=True)[
        replacement.lineno - 1 : replacement.end_lineno
    ]
    return "".join(lines)


def _add_retention_setting(source: str) -> str:
    """Extend the archived schema without importing newer experimental controls."""
    for node in ast.walk(ast.parse(source)):
        if (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "checkpoint_keep_interval"
        ):
            return source
    lines = source.splitlines(keepends=True)
    for index, line in enumerate(lines):
        if line.startswith("    checkpoint_keep_recent:"):
            lines.insert(
                index + 1,
                "    checkpoint_keep_interval: int | None = Field(default=200, gt=0)\n",
            )
            return "".join(lines)
    raise ValueError("archived checkpoint configuration has an unsupported implementation")


def overlay(target: Path, revision: Path, original: dict[str, Any]) -> dict[str, Any]:
    """Archive a small allowlisted storage overlay on the verified original source tree."""
    files = dict(original["files"])
    state_path = _PACKAGE / "state.py"
    text = (target / state_path).read_text()
    current = state_path.read_text()
    for function in ("restore", "member_path", "checkpoint", "commit_pending"):
        text = _replace_function(text, current, function)
    text = text.replace(
        "from kagg_revue.learning.retention import remove_retired, retire\n",
        "from kagg_revue.learning.storage.artifacts import resolve\n"
        "from kagg_revue.learning.storage.publication import publish as publish_storage\n"
        "from kagg_revue.learning.storage.roles import checkpoint_due, required_members\n",
    )
    text = text.replace(
        "from kagg_revue.learning.storage.roles import required_members\n",
        "from kagg_revue.learning.storage.roles import checkpoint_due, required_members\n",
    )
    (target / state_path).write_text(text)
    config_path = _PACKAGE / "config.py"
    (target / config_path).write_text(_add_retention_setting((target / config_path).read_text()))
    retention = _PACKAGE / "retention.py"
    (target / retention).write_bytes(retention.read_bytes())
    for name in _RUNTIME:
        path = _PACKAGE / "storage" / name
        (target / path).parent.mkdir(parents=True, exist_ok=True)
        (target / path).write_bytes(path.read_bytes())
        files[str(path)] = ""
    serialization = Path("src/kagg_revue/artifacts/serialization.py")
    if not (target / serialization).exists():
        (target / serialization).write_bytes(serialization.read_bytes())
        files[str(serialization)] = ""
    writer_path = _PACKAGE / "checkpointing/writer.py"
    if (target / writer_path).exists():
        text = (target / writer_path).read_text()
        for function in ("record", "finish"):
            text = _replace_function(text, writer_path.read_text(), function)
        text = text.replace(
            "from kagg_revue.learning.retention import remove_retired, retire\n",
            "from kagg_revue.learning.storage.publication import publish as publish_storage\n",
        )
        if "from kagg_revue.learning.storage.roles import checkpoint_due\n" not in text:
            text = text.replace(
                "from kagg_revue.learning.config import Experiment\n",
                "from kagg_revue.learning.config import Experiment\n"
                "from kagg_revue.learning.storage.roles import checkpoint_due\n",
            )
        (target / writer_path).write_text(text)
    pretraining = _PACKAGE / "pretraining/artifacts.py"
    text = (target / pretraining).read_text()
    before = """    if rank == 0:
        if progress["epoch_rows"] == 0:
            state.setdefault("pretraining_epoch_members", []).append(name)
        retired = retire(config, state)
        write_json(config.output_dir / "state.json", state)
        remove_retired(config.output_dir, retired)
"""
    after = """    if progress["epoch_rows"] == 0:
        state.setdefault("pretraining_epoch_members", []).append(name)
    publish_storage(config, state)
    if rank == 0:
"""
    if text.count(before) != 1 and text.count(after) != 1:
        raise ValueError("archived BC publication has an unsupported implementation")
    text = text.replace(before, after).replace(
        "from kagg_revue.learning.retention import remove_retired, retire\n",
        "from kagg_revue.learning.storage.publication import publish as publish_storage\n",
    )
    (target / pretraining).write_text(text)
    changed = []
    for name in files:
        checksum = digest(target / name)
        if files[name] != checksum:
            changed.append(name)
        files[name] = checksum
    allowed = {
        str(state_path),
        str(config_path),
        str(retention),
        str(writer_path),
        str(pretraining),
        str(serialization),
        *(str(_PACKAGE / "storage" / name) for name in _RUNTIME),
    }
    if set(changed) - allowed:
        raise ValueError("storage overlay modified a training implementation outside its scope")
    identity = {
        **original,
        "files": files,
        "source_sha256": hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest(),
        "storage_overlay": {"parent_source": original["source_sha256"], "changed": changed},
    }
    write_json(revision / "source.json", identity)
    with tarfile.open(revision / "source.tar.gz", "w:gz") as archive:
        for name in files:
            archive.add(target / name, arcname=name, recursive=False)
    return identity
