"""Focused native-fork parity with the unchanged neural and scripted actors."""

import numpy as np

from kagg_revue.learning.collection.population import create_training_batch, script_games
from kagg_revue.policy.inference import ActorRuntime
from kagg_revue.policy.spatial.model import Policy
from kagg_revue.production.branching.rollout import fork_batch
from kagg_revue.production.config import Settings


def verify_forks(settings: Settings, policy: Policy) -> dict[str, object]:
    """Replay one common trace through two fork points, including every frozen script lineage."""
    games = 8 * len(settings.ppo.script_opponents)
    scripts = script_games(settings, games)
    selfplay = games - scripts
    seeds = [settings.evaluation_seed - games + i // 2 for i in range(games)]
    batch = create_training_batch(settings, seeds)
    actor = ActorRuntime(
        policy,
        2 * selfplay + scripts,
        sample=False,
        precision=settings.precision,
        bf16_reduced_precision_reduction=settings.bf16_reduced_precision_reduction,
    )
    checkpoints = {policy.layout.decisions // 3, 2 * policy.layout.decisions // 3}
    forks = []
    observations = np.empty_like(actor.host.numpy())
    for decision, span in enumerate(policy.layout.spans):
        batch.observe_into(actor.host.numpy())
        if decision in checkpoints:
            child = fork_batch(batch, np.arange(selfplay), np.arange(scripts))
            child.observe_into(observations)
            if not np.array_equal(observations, actor.host.numpy()):
                raise RuntimeError("fork lost actor-visible state or public history")
            forks.append(child)
        actor.act(decision)
        batch.advance(actor.selected.numpy(), span)
        for child in forks:
            child.advance(actor.selected.numpy(), span)
    batch.observe_into(actor.host.numpy())
    expected = batch.cash(settings.turns)
    for child in forks:
        child.observe_into(observations)
        if not np.array_equal(observations, actor.host.numpy()) or not np.array_equal(
            child.cash(settings.turns), expected
        ):
            raise RuntimeError(
                "fork changed the common trace's state, opponent response or terminal outcome"
            )
    return {
        "passed": True,
        "games": games,
        "forks": len(forks),
        "opponents": list(settings.ppo.script_opponents),
        "boundary": "engine, public history, scripted memory; identical selected programs",
        "deployment_budget_qualified": False,
    }
