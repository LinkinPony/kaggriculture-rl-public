import torch

from kagg_revue.policy.model import ActorArchitecture, TurnPolicyNet
from kagg_revue.rl import distillation
from kagg_revue.rl.memory_migration import (
    migrate_actor_weights as migrate_memory_weights,
)
from kagg_revue.rl.memory_migration import target_architecture as memory_architecture
from kagg_revue.rl.strategy_migration import migrate_actor_weights


def _architecture(
    *,
    unit_features: int,
    unit_limit: int,
    decisions: int,
    unit_actions: int,
    market_actions: int,
    skills: int = 0,
    strategy: int = 0,
) -> ActorArchitecture:
    return ActorArchitecture(
        board_shape=(2, 3, 2, 2),
        unit_shape=(2, unit_limit, unit_features),
        global_features=3,
        model_width=8,
        entity_width=4,
        attention_heads=1,
        feedforward_width=12,
        latent_tokens=2,
        scene_layers=1,
        temporal_layers=1,
        action_layers=1,
        max_history=8,
        max_decisions=decisions,
        unit_action_tokens=unit_actions,
        market_action_tokens=market_actions,
        maximum_quantity=7,
        derived_fact_version=None,
        turn_fact_features=0,
        prefix_fact_features=0,
        candidate_fact_features=0,
        fact_dropout=0.0,
        skill_tokens=skills,
        strategy_tokens=strategy,
    )


def test_actor_migration_copies_semantic_rows_and_expanded_prefixes() -> None:
    torch.manual_seed(41)
    source = TurnPolicyNet(
        _architecture(
            unit_features=4,
            unit_limit=2,
            decisions=3,
            unit_actions=4,
            market_actions=3,
            skills=2,
        )
    )
    target = TurnPolicyNet(
        _architecture(
            unit_features=5,
            unit_limit=3,
            decisions=4,
            unit_actions=3,
            market_actions=2,
            strategy=2,
        )
    )
    source_state = source.state_dict()
    row_map = (0, 2, 3, 5, 6)

    report = migrate_actor_weights(source_state, target, row_map)
    migrated = target.state_dict()

    torch.testing.assert_close(
        migrated["scene.action_embedding.weight"],
        source_state["scene.action_embedding.weight"][list(row_map)],
    )
    torch.testing.assert_close(
        migrated["action.action_head.weight"],
        source_state["action.action_head.weight"][list(row_map)],
    )
    torch.testing.assert_close(
        migrated["action.action_embedding.weight"][:-1],
        source_state["action.action_embedding.weight"][list(row_map)],
    )
    torch.testing.assert_close(
        migrated["action.action_embedding.weight"][-1],
        source_state["action.action_embedding.weight"][-1],
    )
    unit_input = migrated["scene.unit_encoder.network.0.weight"]
    source_unit_input = source_state["scene.unit_encoder.network.0.weight"]
    torch.testing.assert_close(unit_input[:, : source_unit_input.shape[1]], source_unit_input)
    assert torch.count_nonzero(unit_input[:, source_unit_input.shape[1] :]) == 0
    torch.testing.assert_close(
        migrated["scene.unit_slot_embedding.weight"][:2],
        source_state["scene.unit_slot_embedding.weight"],
    )
    torch.testing.assert_close(
        migrated["action.position_embedding.weight"][:3],
        source_state["action.position_embedding.weight"],
    )
    assert report["copied_elements"] > 0
    assert any(
        name.startswith("skills.") for name in report["deleted_by_tensor"]
    )
    assert any(
        ".strategy_cross." in name or name.startswith("strategy.")
        for name in report["initialized_by_tensor"]
    )


def test_semantic_kl_ignores_zero_probability_illegal_entries() -> None:
    target = torch.tensor([1.0, 0.0])
    log_probabilities = torch.tensor([0.0, -torch.inf])

    value = distillation._kl(target, log_probabilities)

    assert torch.isfinite(value)
    assert value == 0


def test_memory_migration_reuses_workspace_and_initializes_only_gru() -> None:
    torch.manual_seed(43)
    source = TurnPolicyNet(
        _architecture(
            unit_features=4,
            unit_limit=2,
            decisions=3,
            unit_actions=4,
            market_actions=3,
            strategy=2,
        )
    )
    target = TurnPolicyNet(memory_architecture(source.architecture))

    report = migrate_memory_weights(source.state_dict(), target)
    migrated = target.state_dict()

    for name, value in source.state_dict().items():
        torch.testing.assert_close(migrated[name], value)
    initialized = report["initialized_by_tensor"]
    assert isinstance(initialized, dict)
    assert initialized
    assert all(name.startswith("strategy.recurrent.") for name in initialized)
