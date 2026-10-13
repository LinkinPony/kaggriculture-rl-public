"""Expand a complete v4 PPO checkpoint without restarting training or matchmaking."""

from dataclasses import asdict
from typing import Any

import torch

from kagg_revue.learning.matchmaking.imports import layout_from_payload
from kagg_revue.learning.matchmaking.verification import finite
from kagg_revue.learning.optimization.migration import expand_adam
from kagg_revue.learning.sequences.critic import MemoryCritic
from kagg_revue.learning.settings import RuntimeSettings
from kagg_revue.policy.contracts import ContractLayout
from kagg_revue.policy.grounded.migration import copy_parameters, migrate_policy
from kagg_revue.policy.memory.policy import MemoryPolicy
from kagg_revue.policy.spatial.model import Policy


def expand(
    payload: dict[str, Any], settings: RuntimeSettings, parent_sha256: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Keep all old tensors, named Adam state, RNG, PFSP and the absolute update."""
    layout = layout_from_payload(payload)
    target_layout = ContractLayout.resolve(settings)
    with torch.random.fork_rng(devices=[]):
        actor = Policy.from_layout(layout)
        if not isinstance(actor, MemoryPolicy):
            raise ValueError("feature continuation requires the recurrent v4 PPO architecture")
        actor.load_state_dict(payload["model"], strict=True)
        expanded, actor_report = migrate_policy(actor, target_layout)
        critic, new_critic = MemoryCritic(layout), MemoryCritic(target_layout)
        critic.load_state_dict(payload["critic"], strict=True)
        critic_report = copy_parameters(critic, new_critic, "entity_encoder")
    optimizers = {}
    reports = {}
    for key, before, after in (
        ("actor_optimizer", actor, expanded),
        ("critic_optimizer", critic, new_critic),
    ):
        weights = payload["model" if key == "actor_optimizer" else "critic"]
        names = dict(before.named_parameters())
        if [name for name in weights if name in names] != list(names):
            raise ValueError("saved model order differs from its Adam parameter registration")
        optimizers[key], reports[key] = expand_adam(payload[key], before, after)
    migrated = {
        **payload,
        "layout": asdict(target_layout),
        "model": expanded.state_dict(),
        "critic": new_critic.state_dict(),
        "settings": settings.model_dump(mode="json"),
        **optimizers,
        "lineage": {
            **payload["lineage"],
            "parent_sha256": parent_sha256,
            "feature_migration": {
                "source": layout.observation.version,
                "target": target_layout.observation.version,
            },
        },
    }
    if not finite(migrated):
        raise ValueError("migrated PPO checkpoint contains nonfinite tensors")
    return migrated, {
        "actor": actor_report,
        "critic": critic_report,
        "optimizers": reports,
        "update": payload["update"],
        "rng_workers": len(payload["rng"]["workers"]),
        "rng_and_pfsp_unchanged": True,
        "all_checkpoint_tensors_finite": True,
    }
