import torch

from kagg_revue.policy.model import ActorArchitecture, PolicyOutput, TurnPolicyNet
from kagg_revue.policy.skills import SkillSequence
from kagg_revue.policy.strategy import StrategyWorkspace
from kagg_revue.rl.outcome import (
    ActorCriticOutput,
    OutcomeActorCritic,
    OutcomeHead,
    monte_carlo_advantages,
    potential_rewards,
    ppo_loss,
)


def test_potential_rewards_telescope_for_padded_trajectories() -> None:
    outcomes = torch.tensor([1, -1])
    values = torch.tensor([[0.2, 0.5, 0.4], [-0.3, -0.1, 0.0]])
    mask = torch.tensor([[True, True, True], [True, True, False]])

    rewards = potential_rewards(outcomes, values, mask)

    expected = outcomes.float() - values[:, 0]
    assert torch.allclose((rewards * mask).sum(dim=1), expected)
    assert rewards[1, 2] == 0


def test_single_outcome_panel_cannot_enable_actor_update() -> None:
    outcomes = torch.tensor([-1, -1])
    old_values = torch.zeros(2, 3)
    mask = torch.ones_like(old_values, dtype=torch.bool)

    advantages, actor_update = monte_carlo_advantages(outcomes, old_values, mask, normalize=True)

    assert not actor_update
    assert torch.all(advantages == -1)


def test_outcome_head_backpropagates_into_actor_context() -> None:
    history = torch.randn(2, 3, 8, requires_grad=True)
    global_features = torch.randn(2, 3, 5, requires_grad=True)
    scene_memory = torch.randn(2, 3, 4, 8, requires_grad=True)
    scene_mask = torch.ones(2, 3, 4, dtype=torch.bool)
    head = OutcomeHead(8, 5, 2)

    logits = head(history, global_features, scene_memory, scene_mask)

    torch.testing.assert_close(logits, head.network(history), rtol=0, atol=0)
    with torch.no_grad():
        head.context_network[-1].weight.fill_(0.01)
    head(history, global_features, scene_memory, scene_mask).sum().backward()

    assert history.grad is not None
    assert global_features.grad is not None
    assert scene_memory.grad is not None
    assert all(parameter.grad is not None for parameter in head.parameters())


def test_strategy_critic_residual_is_zero_initialized_and_joint() -> None:
    history = torch.randn(2, 8, requires_grad=True)
    global_features = torch.randn(2, 5, requires_grad=True)
    scene_memory = torch.randn(2, 4, 8, requires_grad=True)
    scene_mask = torch.ones(2, 4, dtype=torch.bool)
    strategy = torch.randn(2, 3, 8, requires_grad=True)
    head = OutcomeHead(8, 5, 2, strategy_tokens=3)

    baseline = head(history, global_features, scene_memory, scene_mask, strategy=strategy)

    torch.testing.assert_close(baseline, head.network(history), rtol=0, atol=0)
    assert head.strategy_output is not None
    with torch.no_grad():
        head.strategy_output.weight.fill_(0.01)
    head(
        history,
        global_features,
        scene_memory,
        scene_mask,
        strategy=strategy,
    ).sum().backward()

    assert history.grad is not None
    assert global_features.grad is not None
    assert scene_memory.grad is not None
    assert strategy.grad is not None
    assert all(parameter.grad is not None for parameter in head.parameters())


def test_critic_gradient_reaches_persistent_gru() -> None:
    workspace = StrategyWorkspace(width=8, heads=2, feedforward=16, slots=3)
    history = torch.randn(2, 4, 8)
    scene = torch.randn(2, 4, 5, 8)
    valid = torch.ones(2, 4, dtype=torch.bool)
    strategy = workspace.sequence(history, scene, valid)
    head = OutcomeHead(8, 5, 2, strategy_tokens=3)
    assert head.strategy_output is not None
    with torch.no_grad():
        head.strategy_output.weight.fill_(0.01)

    head(
        history,
        torch.randn(2, 4, 5),
        scene,
        torch.ones(2, 4, 5, dtype=torch.bool),
        strategy=strategy,
    ).sum().backward()

    gradient = workspace.recurrent.weight_ih_l0.grad
    assert gradient is not None
    assert torch.count_nonzero(gradient).item() > 0


def test_detached_critic_preserves_policy_gradients_without_actor_value_gradients() -> None:
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
        strategy_tokens=3,
        strategy_version="gru-v1",
    )
    model = OutcomeActorCritic(TurnPolicyNet(architecture))
    batch = 2
    turns = 2
    decisions = architecture.max_decisions
    forward_args = (
        torch.randn(batch, turns, *architecture.board_shape),
        torch.randn(batch, turns, *architecture.unit_shape),
        torch.randn(batch, turns, architecture.global_features),
        torch.empty(batch, turns, 0, 0),
        torch.empty(batch, turns, 0, dtype=torch.bool),
        torch.empty(batch, turns, decisions, 0),
        torch.empty(batch, turns, decisions, architecture.action_tokens, 0),
        torch.zeros(batch, turns, decisions, dtype=torch.long),
        torch.zeros(batch, turns, decisions, dtype=torch.long),
        torch.zeros(batch, turns, decisions, dtype=torch.long),
        torch.ones(batch, turns, dtype=torch.bool),
        torch.ones(batch, turns, decisions, dtype=torch.bool),
        torch.full((batch, turns), -1, dtype=torch.long),
    )

    critic_output = model(*forward_args, critic_actor_gradient=False)
    critic_output.outcome_logits.square().mean().backward()  # type: ignore[no-untyped-call]

    assert all(parameter.grad is None for parameter in model.actor.parameters())
    assert any(parameter.grad is not None for parameter in model.outcome.parameters())

    model.zero_grad(set_to_none=True)
    policy_output = model(*forward_args, critic_actor_gradient=False)
    policy_output.policy.action_logits.square().mean().backward()  # type: ignore[no-untyped-call]

    assert any(parameter.grad is not None for parameter in model.actor.parameters())
    assert all(parameter.grad is None for parameter in model.outcome.parameters())


def test_ppo_identity_ratio_is_unclipped_and_finite() -> None:
    action_logits = torch.tensor(
        [
            [[[1.0, 0.0, -1.0], [0.0, 1.0, -1.0]]],
            [[[0.0, -1.0, 1.0], [1.0, -1.0, 0.0]]],
        ],
        requires_grad=True,
    )
    quantity_logits = torch.zeros(2, 1, 2, 4, requires_grad=True)
    outcome_logits = torch.zeros(2, 1, 3, requires_grad=True)
    actions = torch.tensor([[[0, 1]], [[2, 0]]])
    quantities = torch.zeros_like(actions, dtype=torch.float32)
    legal = torch.ones(2, 1, 2, 3, dtype=torch.bool)
    decision_mask = torch.ones_like(actions, dtype=torch.bool)
    turn_mask = torch.ones(2, 1, dtype=torch.bool)
    selected = torch.log_softmax(action_logits.detach(), dim=-1).gather(-1, actions[..., None])[
        ..., 0
    ]
    output = ActorCriticOutput(
        policy=PolicyOutput(
            action_logits=action_logits,
            quantity_logits=quantity_logits,
        ),
        outcome_logits=outcome_logits,
    )

    loss = ppo_loss(
        output,
        actions,
        quantities,
        legal,
        selected,
        torch.full((2, 1), -1, dtype=torch.long),
        torch.zeros(2, 1),
        torch.tensor([[-1.0], [1.0]]),
        torch.tensor([-1, 1]),
        turn_mask,
        decision_mask,
        torch.zeros(3, dtype=torch.bool),
        0.2,
        1.0,
        0.0,
        actor_update=True,
    )
    loss.total.backward()  # type: ignore[no-untyped-call]

    assert torch.isfinite(loss.total)
    assert loss.approximate_kl == 0
    assert loss.clip_fraction == 0
    assert action_logits.grad is not None
    assert outcome_logits.grad is not None


def test_critic_only_loss_leaves_policy_without_gradients() -> None:
    action_logits = torch.zeros(1, 1, 1, 2, requires_grad=True)
    outcome_logits = torch.zeros(1, 1, 3, requires_grad=True)
    actions = torch.zeros(1, 1, 1, dtype=torch.long)
    output = ActorCriticOutput(
        policy=PolicyOutput(
            action_logits=action_logits,
            quantity_logits=torch.zeros(1, 1, 1, 4),
        ),
        outcome_logits=outcome_logits,
    )

    loss = ppo_loss(
        output,
        actions,
        torch.zeros_like(actions, dtype=torch.float32),
        torch.ones(1, 1, 1, 2, dtype=torch.bool),
        torch.full_like(actions, -0.6931471805599453, dtype=torch.float32),
        torch.full((1, 1), -1, dtype=torch.long),
        torch.zeros(1, 1),
        torch.zeros(1, 1),
        torch.zeros(1, dtype=torch.long),
        torch.ones(1, 1, dtype=torch.bool),
        torch.ones_like(actions, dtype=torch.bool),
        torch.zeros(2, dtype=torch.bool),
        0.2,
        1.0,
        0.1,
        actor_update=False,
    )
    loss.total.backward()  # type: ignore[no-untyped-call]

    assert action_logits.grad is None
    assert outcome_logits.grad is not None


def test_ppo_updates_causal_skill_path() -> None:
    action_logits = torch.tensor([[[[1.0, 0.0]]], [[[0.0, 1.0]]]], requires_grad=True)
    prior_logits = torch.tensor([[[1.0, 0.0, -1.0]], [[0.0, 1.0, -1.0]]], requires_grad=True)
    skill_ids = torch.tensor([[0], [1]])
    actions = torch.tensor([[[0]], [[1]]])
    turn_mask = torch.ones(2, 1, dtype=torch.bool)
    decision_mask = torch.ones_like(actions, dtype=torch.bool)
    selected_actions = torch.log_softmax(action_logits.detach(), dim=-1).gather(
        -1, actions[..., None]
    )[..., 0]
    selected_skills = torch.log_softmax(prior_logits.detach(), dim=-1).gather(
        -1, skill_ids[..., None]
    )[..., 0]
    output = ActorCriticOutput(
        policy=PolicyOutput(
            action_logits=action_logits,
            quantity_logits=torch.zeros(2, 1, 1, 4),
            skills=SkillSequence(
                prior_logits=prior_logits,
                ids=skill_ids,
                embeddings=torch.zeros(2, 1, 4),
            ),
        ),
        outcome_logits=torch.zeros(2, 1, 3, requires_grad=True),
    )

    loss = ppo_loss(
        output,
        actions,
        torch.zeros_like(actions),
        torch.ones(2, 1, 1, 2, dtype=torch.bool),
        selected_actions,
        skill_ids,
        selected_skills,
        torch.tensor([[-1.0], [1.0]]),
        torch.tensor([-1, 1]),
        turn_mask,
        decision_mask,
        torch.zeros(2, dtype=torch.bool),
        0.2,
        1.0,
        0.0,
        actor_update=True,
    )
    loss.total.backward()  # type: ignore[no-untyped-call]

    assert loss.approximate_kl == 0
    assert prior_logits.grad is not None


def test_single_outcome_skips_causal_latent_actor_update() -> None:
    action_logits = torch.zeros(1, 1, 1, 2, requires_grad=True)
    prior_logits = torch.zeros(1, 1, 2, requires_grad=True)
    skill_ids = torch.zeros(1, 1, dtype=torch.long)
    turn_mask = torch.ones(1, 1, dtype=torch.bool)
    output = ActorCriticOutput(
        policy=PolicyOutput(
            action_logits=action_logits,
            quantity_logits=torch.zeros(1, 1, 1, 2),
            skills=SkillSequence(
                prior_logits=prior_logits,
                ids=skill_ids,
                embeddings=torch.zeros(1, 1, 3),
            ),
        ),
        outcome_logits=torch.zeros(1, 1, 3, requires_grad=True),
    )

    loss = ppo_loss(
        output,
        torch.zeros(1, 1, 1, dtype=torch.long),
        torch.zeros(1, 1, 1, dtype=torch.long),
        torch.ones(1, 1, 1, 2, dtype=torch.bool),
        torch.full((1, 1, 1), -0.6931471805599453),
        skill_ids,
        torch.full((1, 1), -0.6931471805599453),
        torch.zeros(1, 1),
        torch.zeros(1, dtype=torch.long),
        turn_mask,
        torch.ones(1, 1, 1, dtype=torch.bool),
        torch.zeros(2, dtype=torch.bool),
        0.2,
        1.0,
        0.0,
        actor_update=False,
    )
    loss.total.backward()  # type: ignore[no-untyped-call]

    assert action_logits.grad is None
    assert prior_logits.grad is None
    assert output.outcome_logits.grad is not None
