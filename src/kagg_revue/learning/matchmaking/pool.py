"""Deterministic temporal coverage of authenticated own-run checkpoint members."""

from pathlib import Path
from typing import Any

from kagg_revue.learning.config import Experiment


def member_update(name: str) -> int:
    """Assign the fixed RL initialization to online update zero."""
    stem = Path(name).stem
    return int(stem.removeprefix("update-")) if stem.startswith("update-") else 0


def retain(names: list[str], capacity: int, recent: int) -> list[str]:
    """Keep the initial control, recent snapshots, and spread older training eras."""
    result = sorted(set(names), key=lambda name: (member_update(name), name))
    while len(result) > capacity:
        # Remove a crowded older point, retaining the endpoints of its small gap.
        index = min(
            range(1, len(result) - recent),
            key=lambda i: (member_update(result[i + 1]) - member_update(result[i - 1]), i),
        )
        result.pop(index)
    return result


def initialize(config: Experiment, state: dict[str, Any]) -> None:
    """Seed PFSP once from retained lineage members, never from evaluation anchors."""
    pfsp = config.population.pfsp
    if pfsp is None or "pfsp" in state:
        return
    names = [
        str(state.get("rl_initial", "initial.pt")),
        *(name for name in state["members"] if name.startswith("checkpoints/update-")),
    ]
    state["pool"] = retain(names, config.population.capacity, pfsp.recent_snapshots)
    state["pfsp"] = {
        "version": 1,
        "started_update": state["completed_update"] + 1,
        "last_update": state["completed_update"],
        "records": {},
    }


def snapshot(config: Experiment, state: dict[str, Any], name: str) -> None:
    """Add an immutable completed policy without collapsing the pool into recent updates."""
    names = [*state["pool"], name]
    if config.population.pfsp is not None:
        external = list(state.get("external_opponents", {}))
        own = retain(
            [member for member in names if member not in external],
            config.population.capacity - len(external),
            config.population.pfsp.recent_snapshots,
        )
        state["pool"] = [own[0], *external, *own[1:]]
    else:
        state["pool"] = names
        if len(names) > config.population.capacity:
            state["pool"].pop(1)
