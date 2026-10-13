"""Atomic demonstration progress and an explicit post-initialization RL control."""

from typing import Any

import torch

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.distributed import rank_world, rng_snapshot
from kagg_revue.learning.pretraining.optimization import Optimizer
from kagg_revue.learning.settings import RuntimeSettings
from kagg_revue.learning.storage.publication import publish as publish_storage
from kagg_revue.policy.checkpoints import save_policy


def checkpoint(
    config: Experiment,
    settings: RuntimeSettings,
    state: dict[str, Any],
    optimizer: Optimizer,
    progress: dict[str, Any],
    *,
    complete: bool,
) -> None:
    """Register one same-run descendant with cursor, optimizer, RNG and data identity."""
    assert config.demonstrations is not None
    name = f"pretraining/shard-{progress['cursor']:06d}.pt"
    rank, world = rank_world()
    rng = (
        rng_snapshot(optimizer.device)
        if optimizer.device.type == "cuda"
        else {
            "cpu": torch.get_rng_state(),
            "cuda": None,
        }
    )
    if rank == 0:
        _save(config, settings, state, optimizer, progress, name, rng)
    hashes = [digest(config.output_dir / name) if rank == 0 else None]
    if world > 1:
        torch.distributed.broadcast_object_list(hashes, src=0)
    state["members"][name] = hashes[0]
    state.update(latest=name, pretraining=progress.copy())
    if complete:
        selected = progress.get("early_stopping", {}).get("best_member", name)
        if selected not in state["members"]:
            raise ValueError("BC selected checkpoint is not a registered member")
        state.update(rl_initial=selected, latest=selected, pool=[selected])
        if config.demonstrations.early_stopping is not None:
            state["bc_final"] = name
    if (
        progress["epoch_rows"] == 0
        and len(progress["records"]) % config.demonstrations.epoch_checkpoint_interval == 0
    ):
        state.setdefault("pretraining_epoch_members", []).append(name)
    publish_storage(config, state)
    if rank == 0:
        write_json(config.output_dir / "pretraining" / "progress.json", progress)


def _save(
    config: Experiment,
    settings: RuntimeSettings,
    state: dict[str, Any],
    optimizer: Optimizer,
    progress: dict[str, Any],
    name: str,
    rng: dict[str, Any],
) -> None:
    assert config.demonstrations is not None
    save_policy(
        config.output_dir / name,
        optimizer.actor,
        settings,
        pretraining=progress,
        optimizer=optimizer.optimizer.state_dict(),
        rng=rng,
        lineage={
            "run_id": state["run_id"],
            "kind": "multi_source_demonstrations",
            "root_sha256": state["members"]["initial.pt"],
            "parent_sha256": state["members"][state["latest"]],
            "dataset_sha256": config.demonstrations.sha256,
        },
    )
