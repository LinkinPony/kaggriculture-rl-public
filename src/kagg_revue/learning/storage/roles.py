"""Separate live file dependencies from permanent checkpoint identity records."""

from typing import Any

from kagg_revue.learning.config import Experiment


def checkpoint_due(config: Experiment, update: int) -> bool:
    """Save regular recovery points, permanent milestones and the final update."""
    return (
        update % config.checkpoint_interval == 0
        or update == config.updates
        or (
            config.checkpoint_keep_interval is not None
            and update % config.checkpoint_keep_interval == 0
        )
    )


def required_members(config: Experiment, state: dict[str, Any]) -> set[str]:
    """Identify policies that continuation, matchmaking and fixed controls can load."""
    required = {
        "initial.pt",
        str(state["latest"]),
        *state["pool"],
        *state.get("external_opponents", {}),
        *state.get("pretraining_epoch_members", []),
        *(event["checkpoint"] for event in state.get("feature_history", [])),
        *(f"anchors/seed-{seed}.pt" for seed in config.evaluation.anchor_seeds),
    }
    if "rl_initial" in state:
        required.add(state["rl_initial"])
    else:
        best = state.get("pretraining", {}).get("early_stopping", {}).get("best_member")
        if best:
            required.add(best)
    return required


def full_members(config: Experiment, state: dict[str, Any]) -> set[str]:
    """Keep recent recovery points, periodic RL milestones and unfinished BC best."""
    if config.checkpoint_keep_recent is None:
        return set(state["members"])
    prefix = (
        "checkpoints/update-"
        if state["latest"].startswith("checkpoints/")
        else "pretraining/shard-"
    )
    names = sorted(
        name
        for name in state["members"]
        if name.startswith(prefix) and name not in state.get("inference_artifacts", {})
    )
    full = {
        str(state["latest"]),
        *names[-config.checkpoint_keep_recent :],
        *(event["checkpoint"] for event in state.get("feature_history", [])),
    }
    if config.checkpoint_keep_interval is not None:
        # Previously compacted milestones cannot regain their discarded optimizer state.
        for name in names:
            if name.startswith("checkpoints/update-") and name.endswith(".pt"):
                update = int(name.removeprefix("checkpoints/update-").removesuffix(".pt"))
                if update % config.checkpoint_keep_interval == 0:
                    full.add(name)
    if "rl_initial" not in state:
        best = state.get("pretraining", {}).get("early_stopping", {}).get("best_member")
        if best:
            full.add(best)
    return full
