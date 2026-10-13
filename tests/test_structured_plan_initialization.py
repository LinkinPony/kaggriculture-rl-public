from __future__ import annotations

import torch

from kagg_revue.policy.model import TurnPolicyNet
from kagg_revue.policy.plans import (
    GLOBAL_FIELDS,
    LINE_FIELDS,
    PRODUCTION_LINES,
    StructuredPlanArchitecture,
    StructuredPlanPolicy,
)
from kagg_revue.rl.plans.initialization import transfer_plan_backbone


def test_bc_initialization_transfers_only_shared_representation() -> None:
    architecture = StructuredPlanArchitecture(
        observation_features=6,
        journal_features=3,
        event_features=4,
        production_lines=PRODUCTION_LINES,
        line_fields=LINE_FIELDS,
        global_fields=GLOBAL_FIELDS,
        model_width=24,
        entity_width=16,
        attention_heads=4,
        feedforward_width=48,
        latent_tokens=8,
        scene_layers=1,
        temporal_layers=2,
        action_layers=1,
        strategy_tokens=4,
    )
    target = StructuredPlanPolicy(architecture)
    source = TurnPolicyNet(target.backbone.scene.architecture)
    for index, module in enumerate(
        (source.scene, source.temporal, source.strategy),
        start=1,
    ):
        assert module is not None
        with torch.no_grad():
            for parameter in module.parameters():
                parameter.fill_(index / 10)

    excluded_before = {
        name: value.detach().clone()
        for name, value in target.state_dict().items()
        if not name.startswith(
            (
                "backbone.scene.",
                "backbone.temporal.",
                "backbone.strategy.",
            )
        )
    }
    report = transfer_plan_backbone(target, source)

    assert report["total"] == sum(report[name] for name in ("scene", "temporal", "strategy"))
    for destination, origin in (
        (target.backbone.scene, source.scene),
        (target.backbone.temporal, source.temporal),
        (target.backbone.strategy, source.strategy),
    ):
        assert destination is not None and origin is not None
        for name, value in destination.state_dict().items():
            torch.testing.assert_close(value, origin.state_dict()[name])
    for name, value in excluded_before.items():
        torch.testing.assert_close(target.state_dict()[name], value)
