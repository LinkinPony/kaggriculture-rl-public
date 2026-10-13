"""Register storage-only source revisions while preserving exact recovery checkpoints."""

import copy
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

import torch

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.recovery.archive import materialize
from kagg_revue.learning.retention import retire
from kagg_revue.learning.state import write_ledger
from kagg_revue.learning.storage.artifacts import compact, resolve
from kagg_revue.learning.storage.overlay import overlay
from kagg_revue.learning.storage.roles import full_members, required_members


def migrate(directory: Path, shared: dict[str, tuple[Path, str]]) -> dict[str, Any]:
    """Stage compact actors and verify the patched archived runtime before any deletion."""
    torch.set_num_threads(1)
    original = json.loads((directory / "state.json").read_text())
    state = copy.deepcopy(original)
    policy = {"checkpoint_keep_recent": 2, "checkpoint_keep_interval": 200}
    config = Experiment.model_validate({**state["protocol"], **policy})
    for name in required_members(config, state) | full_members(config, state):
        resolve(directory, state, name)
    revisions = directory / "storage-revisions"
    index = len(list(revisions.glob("[0-9][0-9][0-9][0-9]"))) + 1
    revision = revisions / f"{index:04d}"
    revision.mkdir(parents=True, exist_ok=False)
    write_json(revision / "previous-state.json", original)
    temporary = Path("tmp")
    temporary.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="storage-migration-", dir=temporary) as name:
        isolated = Path(name).resolve()
        materialize(directory, state, isolated)
        source = directory / state.get("source_directory", ".")
        identity = overlay(isolated, revision, json.loads((source / "source.json").read_text()))
        retired = retire(config, state)
        redundant = compact(
            directory, state, set(state["members"]) - full_members(config, state), shared=shared
        )
        state["protocol"].update(policy)
        state["source"] = identity["source_sha256"]
        state["source_directory"] = str(revision.relative_to(directory))
        transition = {
            "time": time.time(),
            "completed_update": state["completed_update"],
            "latest": state["latest"],
            "checkpoint_sha256": state["members"][state["latest"]],
            "previous_source": original["source"],
            "source": state["source"],
            **policy,
            "pool_size": len(state["pool"]),
            "compacted": len(state.get("inference_artifacts", {})),
            "retired_paths": retired,
            "redundant_original_paths": redundant,
            "revision": str(revision.relative_to(directory)),
            "optimizer_and_sampling_unchanged": True,
        }
        state.setdefault("storage_history", []).append(transition)
        write_json(revision / "transition.json", transition)
        write_ledger(directory, state)
        write_json(directory / "resolved-config.json", state["protocol"])
        for linked in ("outputs", "data"):
            (isolated / linked).symlink_to(Path(linked).resolve(), target_is_directory=True)
        (isolated / "tmp").mkdir()
        command = [
            sys.executable,
            "-m",
            "kagg_revue.learning.storage.verification",
            str(directory),
            str((revision / "previous-state.json").resolve()),
            str((revision / "verification.json").resolve()),
        ]
        environment = {
            **os.environ,
            "PYTHONPATH": str(isolated / "src"),
            "TMPDIR": str(isolated / "tmp"),
        }
        with (revision / "verification.log").open("w") as stream:
            result = subprocess.run(
                command, cwd=isolated, env=environment, stdout=stream, stderr=subprocess.STDOUT
            )
        if result.returncode:
            # Original files still exist: roll back metadata without losing a recovery point.
            write_ledger(directory, original)
            write_json(directory / "resolved-config.json", original["protocol"])
            raise RuntimeError(f"archived storage verification failed; see {revision}")
    if digest(directory / state["latest"]) != original["members"][original["latest"]]:
        raise ValueError("latest checkpoint changed after archived verification")
    return transition
