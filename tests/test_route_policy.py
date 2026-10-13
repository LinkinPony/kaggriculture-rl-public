from __future__ import annotations

import torch

from kagg_revue.rl.routes.model import RouteActorArchitecture, RouteActorCritic


def test_route_actor_initial_greedy_action_is_behavior_prior() -> None:
    architecture = RouteActorArchitecture(
        feature_width=7,
        hidden_width=8,
        feedforward_width=11,
        prior_logit=0.75,
    )
    model = RouteActorCritic(architecture)
    features = torch.randn(6, architecture.feature_width)
    prior = torch.tensor([0, 1, 1, 0, 1, 0])

    logits, values = model(features, prior)

    assert torch.equal(logits.argmax(dim=-1), prior)
    assert torch.equal(values, torch.zeros_like(values))
