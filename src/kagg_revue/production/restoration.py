"""Explicit full-state continuations and separately identified training forks."""

from typing import TYPE_CHECKING, Any

import torch

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.policy.spatial.model import Critic
from kagg_revue.production.config import Settings

if TYPE_CHECKING:
    from kagg_revue.learning.optimization.learner import Learner


def restore_training(
    settings: Settings,
    checkpoint: dict[str, Any],
    critic: Critic,
    learner: "Learner",
    rank: int,
) -> int:
    """Restore actor-associated critic, optimizers and rank RNG without relabeling history."""
    if "update" not in checkpoint:
        if settings.checkpoint_mode == "fork":
            raise ValueError("a training fork needs a full training checkpoint")
        if "critic" in checkpoint:
            critic.load_state_dict(checkpoint["critic"])
        torch.manual_seed(settings.seed + rank)
        torch.cuda.manual_seed(settings.seed + rank)
        return 1
    previous = Settings.model_validate(checkpoint["settings"])
    if settings.checkpoint_mode == "resume":
        if (
            previous.ppo.temperature_schedule != settings.ppo.temperature_schedule
            or previous.ppo.temperature != settings.ppo.temperature
            or previous.ppo.prefix_warmup_updates != settings.ppo.prefix_warmup_updates
            or previous.ppo.protection != settings.ppo.protection
            or previous.ppo.prefix_trace_lambda != settings.ppo.prefix_trace_lambda
        ):
            raise ValueError("resume cannot change temperature, warmup, credit or actor protection")
    elif (
        settings.output_dir == previous.output_dir
        or (settings.output_dir / "metrics.jsonl").exists()
    ):
        raise ValueError("a training fork requires a new output directory without training history")
    if len(checkpoint["rank_rng"]) != len(settings.devices):
        raise ValueError("full-state restoration requires the checkpoint's learner rank count")
    critic.load_state_dict(checkpoint["critic"])
    learner.actor_optimizer.load_state_dict(checkpoint["actor_optimizer"])
    learner.critic_optimizer.load_state_dict(checkpoint["critic_optimizer"])
    rng = checkpoint["rank_rng"][rank]
    torch.set_rng_state(rng["cpu"].cpu())
    torch.cuda.set_rng_state(rng["cuda"].cpu(), learner.device)
    first_update = int(checkpoint["update"]) + 1
    if rank == 0:
        assert settings.checkpoint is not None
        write_json(
            settings.output_dir / "restoration.json",
            {
                "kind": settings.checkpoint_mode,
                "checkpoint": {
                    "path": str(settings.checkpoint),
                    "sha256": digest(settings.checkpoint),
                },
                "source_update": checkpoint["update"],
                "source_revision": checkpoint.get("provenance", {}).get("revision"),
                "first_update": first_update,
                "inherited": ["actor", "critic", "actor_optimizer", "critic_optimizer", "rank_rng"],
                "previous_ppo": previous.ppo.model_dump(mode="json"),
                "resolved_ppo": settings.ppo.model_dump(mode="json"),
            },
        )
    return first_update
