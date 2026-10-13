"""Carry script evidence across manifests only when the strategy identity is unchanged."""

import copy
from typing import Any

from kagg_revue.opponents.settings import PublicPopulation


def restored_statistics(
    saved: dict[str, Any] | None, state: dict[str, Any]
) -> dict[str, Any] | None:
    """Replay registered boundary migrations in memory without changing checkpoint bytes."""
    if saved is None:
        return None
    restored = copy.deepcopy(saved)
    for migration in state.get("script_identity_history", []):
        if migration["completed_update"] != saved["last_update"]:
            continue
        for move in migration["moved"]:
            source, target = move["source"], move["target"]
            if source not in restored["records"] or target in restored["records"]:
                raise ValueError(
                    "checkpoint cannot replay its registered script identity migration"
                )
            restored["records"][target] = restored["records"].pop(source)
    for event in state.get("pfsp_inheritance_history", []):
        if event["completed_update"] != saved["last_update"]:
            continue
        if restored["records"].keys() & event["records"].keys():
            raise ValueError("checkpoint cannot replay its registered PFSP inheritance")
        restored["records"].update(copy.deepcopy(event["records"]))
    return restored


def preserve_script_evidence(
    state: dict[str, Any], previous: PublicPopulation | None, following: PublicPopulation | None
) -> None:
    """Authenticate both manifests before moving any sufficient statistics."""
    if previous is None or following is None or previous.sha256 == following.sha256:
        return
    from kagg_revue.learning.collection.public import records

    old, new = records(previous), records(following)
    evidence = dict(state["pfsp"]["records"])
    moved = []
    for name in sorted(old.keys() & new.keys()):
        left, right = old[name], new[name]
        if (left.sha256, left.files, left.entrypoint) != (
            right.sha256,
            right.files,
            right.entrypoint,
        ):
            continue
        source = f"script:{previous.sha256}:{name}"
        target = f"script:{following.sha256}:{name}"
        if source not in evidence:
            continue
        if target in evidence:
            raise ValueError("new script identity already has evidence; cannot merge histories")
        evidence[target] = evidence.pop(source)
        moved.append({"agent": name, "source": source, "target": target, "sha256": left.sha256})
    state["pfsp"]["records"] = evidence
    state["script_identity_history"] = [
        *state.get("script_identity_history", []),
        {"completed_update": state["completed_update"], "moved": moved},
    ]
