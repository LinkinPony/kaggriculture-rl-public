"""Bound checkpoint storage while retaining recovery, population and evaluation roles."""

from pathlib import Path
from typing import Any

from kagg_revue.learning.config import Experiment
from kagg_revue.learning.storage.roles import full_members, required_members


def retire(config: Experiment, state: dict[str, Any]) -> list[str]:
    """Retire ledger entries before publishing; delete their files only after publication."""
    keep = config.checkpoint_keep_recent
    if keep is None:
        return []
    protected = required_members(config, state) | full_members(config, state)
    candidates = [
        name
        for name in state["members"]
        if name.startswith(("checkpoints/update-", "pretraining/shard-", "historical/"))
    ]
    retired = [name for name in candidates if name not in protected]
    storage = state.get("inference_artifacts", {})
    removed_paths = []
    for name in retired:
        state.setdefault("retired_members", {})[name] = state["members"].pop(name)
        record = storage.pop(name, None)
        if record:
            removed_paths.append(record["path"])
    live_paths = {record["path"] for record in storage.values()}
    return [*retired, *(path for path in removed_paths if path not in live_paths)]


def remove_retired(directory: Path, names: list[str]) -> None:
    """Remove only retired checkpoint files after an authoritative ledger has been saved."""
    root = directory.resolve()
    for name in names:
        path = (root / name).resolve()
        if not path.is_relative_to(root) or path.suffix != ".pt":
            raise ValueError("retired checkpoint escapes the run directory")
        path.unlink(missing_ok=True)
