"""A complete feature migration preserves trained tensors, optimizer state and RNG."""

from dataclasses import asdict
from pathlib import Path
from typing import Any

import torch

from kagg_revue.learning.adapter import runtime_settings
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.features.checkpoint import expand
from kagg_revue.learning.sequences.critic import MemoryCritic
from kagg_revue.learning.storage.roles import full_members, required_members
from kagg_revue.policy.contracts import ContractLayout
from kagg_revue.policy.spatial.model import Policy


def test_full_checkpoint_expansion_preserves_continuation_and_retention() -> None:
    """Only new projections have fresh Adam state, and the boundary remains recoverable."""
    torch.set_num_threads(1)
    config = Experiment(
        output_dir=Path("outputs/learning/migration-test"),
        device="cpu",
        width=16,
        depth=1,
        heads=4,
        critic_width=16,
        critic_depth=1,
        architecture="grounded-v2",
        agronomy=True,
        market_budget=True,
        memory_turns=8,
        memory_width=16,
        memory_layers=1,
        memory_tokens=2,
        sequence_chunk_turns=4,
        decision_interval=1,
        unit_limit=3,
        quantity_max=4,
        quantity_extra=(),
        compile=False,
        environment={
            "boardSize": 4,
            "episodeSteps": 13,
            "turnsPerDay": 6,
            "maxMarketOrdersPerTurn": 2,
        },
    )
    settings = runtime_settings(config)
    layout = ContractLayout.resolve(settings)
    actor, critic = Policy.from_layout(layout), MemoryCritic(layout)
    actor_opt = torch.optim.AdamW(actor.parameters(), lr=config.actor_learning_rate)
    critic_opt = torch.optim.AdamW(critic.parameters(), lr=config.critic_learning_rate)
    for module, optimizer in ((actor, actor_opt), (critic, critic_opt)):
        for parameter in module.parameters():
            parameter.grad = torch.full_like(parameter, 0.01)
        optimizer.step()
    payload: dict[str, Any] = {
        "layout": asdict(layout),
        "settings": settings.model_dump(mode="json"),
        "model": actor.state_dict(),
        "critic": critic.state_dict(),
        "actor_optimizer": actor_opt.state_dict(),
        "critic_optimizer": critic_opt.state_dict(),
        "update": 4,
        "rng": {"workers": [torch.get_rng_state()]},
        "pfsp": {"last_update": 4},
        "lineage": {"run_id": "source", "kind": "reinforcement_learning", "parent_sha256": "old"},
    }
    before_rng = torch.get_rng_state().clone()
    migrated, report = expand(
        payload, runtime_settings(config.model_copy(update={"derived": True})), "parent"
    )
    assert torch.equal(before_rng, torch.get_rng_state())
    assert migrated["rng"] is payload["rng"] and migrated["pfsp"] is payload["pfsp"]
    assert migrated["update"] == 4 and migrated["lineage"]["parent_sha256"] == "parent"
    for field in ("model", "critic"):
        assert all(
            torch.equal(value, migrated[field][name]) for name, value in payload[field].items()
        )
        added = migrated[field].keys() - payload[field].keys()
        assert len(added) == 4 and all(
            not torch.count_nonzero(migrated[field][name]) for name in added
        )
    assert report["optimizers"]["actor_optimizer"]["retained_steps"] == [1]
    boundary = "feature-revisions/0001/migrated.pt"
    state = {
        "latest": "checkpoints/update-000008.pt",
        "pool": ["initial.pt"],
        "members": {boundary: "hash", "checkpoints/update-000008.pt": "new"},
        "feature_history": [{"checkpoint": boundary}],
    }
    assert boundary in required_members(config, state) and boundary in full_members(config, state)
