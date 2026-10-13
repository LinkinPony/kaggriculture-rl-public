import torch

from kagg_revue.policy.model import ActorArchitecture, TurnPolicyNet
from kagg_revue.rl.initialization import initialize_training_actor
from kagg_revue.rl.pfsp import actor_fingerprint


def _actor() -> TurnPolicyNet:
    architecture = ActorArchitecture(
        board_shape=(2, 1, 2, 2),
        unit_shape=(2, 1, 2),
        global_features=3,
        model_width=8,
        entity_width=4,
        attention_heads=1,
        feedforward_width=12,
        latent_tokens=2,
        scene_layers=0,
        temporal_layers=1,
        action_layers=1,
        max_history=3,
        max_decisions=2,
        unit_action_tokens=2,
        market_action_tokens=2,
        maximum_quantity=4,
        derived_fact_version=None,
        turn_fact_features=0,
        prefix_fact_features=0,
        candidate_fact_features=0,
        fact_dropout=0.0,
    )
    return TurnPolicyNet(architecture)


def test_random_actor_uses_only_architecture_and_seed() -> None:
    source = _actor().eval()
    with torch.no_grad():
        for parameter in source.parameters():
            parameter.fill_(0.25)

    torch.manual_seed(17)
    first = initialize_training_actor(source, "random", torch.device("cpu"))
    torch.manual_seed(17)
    second = initialize_training_actor(source, "random", torch.device("cpu"))

    assert first is not source
    assert first.architecture == source.architecture
    assert first.training is source.training
    assert actor_fingerprint(first) == actor_fingerprint(second)
    assert actor_fingerprint(first) != actor_fingerprint(source)
    assert initialize_training_actor(source, "artifact", torch.device("cpu")) is source
