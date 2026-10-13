"""Publish reduced ledgers before retiring bytes, synchronizing every learner rank."""

from typing import Any

import torch

from kagg_revue.learning.config import Experiment
from kagg_revue.learning.distributed import rank_world
from kagg_revue.learning.retention import remove_retired, retire
from kagg_revue.learning.storage.artifacts import compact
from kagg_revue.learning.storage.roles import full_members


def publish(config: Experiment, state: dict[str, Any]) -> None:
    """Commit retention and actor storage atomically before deleting redundant files."""
    from kagg_revue.learning.state import write_ledger

    rank, world = rank_world()
    messages: list[Any] = [None]
    if rank == 0:
        try:
            retired = retire(config, state)
            redundant = compact(
                config.output_dir, state, set(state["members"]) - full_members(config, state)
            )
            write_ledger(config.output_dir, state)
            remove_retired(config.output_dir, [*retired, *redundant])
            messages[0] = {
                key: state.get(key, {})
                for key in ("members", "retired_members", "inference_artifacts")
            }
        except Exception as error:
            messages[0] = {"error": f"{type(error).__name__}: {error}"}
    if world > 1:
        torch.distributed.broadcast_object_list(messages, src=0)
    if "error" in messages[0]:
        raise RuntimeError(f"checkpoint storage publication failed: {messages[0]['error']}")
    state.update(messages[0])
