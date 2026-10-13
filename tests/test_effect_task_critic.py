"""Causal learning and native/graph boundaries for the task critic challenger."""

import numpy as np
import pytest
import torch

from kagg_revue.core.backend import load_backend
from kagg_revue.policy.effects import EffectActorCritic, EffectPolicy, tensor_state_from_native
from kagg_revue.policy.effects.conditioning import TaskEncoding, condition_tasks, encode_tasks
from kagg_revue.policy.model import TurnPolicyNet
from kagg_revue.rl.effects.chunked import _sequence_context
from kagg_revue.rl.effects.initialization import configure_effect_trainable
from kagg_revue.rl.effects.learning import audit_effect_behavior
from kagg_revue.rl.effects.objective import terminal_effect_advantages
from kagg_revue.rl.effects.optimizers import IndependentAdamW
from kagg_revue.rl.effects.rollout import EffectRolloutCollector
from test_effect_training import _model, _root


def test_independent_optimizer_restores_both_adam_states() -> None:
    import copy

    actor = torch.nn.Linear(2, 1)
    critic = torch.nn.Linear(2, 1)
    optimizer = IndependentAdamW(
        tuple(actor.parameters()),
        tuple(critic.parameters()),
        actor_lr=0.03,
        critic_lr=0.04,
        weight_decay=0.0,
        fused=False,
    )
    x = torch.tensor([[0.2, -0.7]])
    (actor(x).square().sum() + critic(x).square().sum()).backward()
    optimizer.step()
    copied_actor, copied_critic = copy.deepcopy(actor), copy.deepcopy(critic)
    restored = IndependentAdamW(
        tuple(copied_actor.parameters()),
        tuple(copied_critic.parameters()),
        actor_lr=0.01,
        critic_lr=0.01,
        weight_decay=0.0,
        fused=False,
    )
    restored.load_state_dict(copy.deepcopy(optimizer.state_dict()))
    frozen_actor = copy.deepcopy(actor.state_dict())
    for module, optim in ((critic, optimizer), (copied_critic, restored)):
        optim.zero_grad()
        module(x).square().sum().backward()
        optim.step()
    for name, weight in actor.state_dict().items():
        torch.testing.assert_close(weight, frozen_actor[name])
        torch.testing.assert_close(weight, copied_actor.state_dict()[name])
    for name, weight in critic.state_dict().items():
        torch.testing.assert_close(weight, copied_critic.state_dict()[name])


def test_independent_critic_has_causal_features_and_owns_its_gradients() -> None:
    backend = load_backend(_root())
    base, _ = _model(backend, {"boardSize": 2, "maxMarketOrdersPerTurn": 2})
    effects = EffectPolicy(
        base.effects.architecture.model_copy(update={"independent_critic": True})
    )
    model = EffectActorCritic(base.actor, effects)
    configure_effect_trainable(model, train_turn_encoder=True)
    architecture = model.actor.architecture
    board = torch.randn(2, 5, *architecture.board_shape)
    units = torch.randn(2, 5, *architecture.unit_shape)
    globals_ = torch.randn(2, 5, architecture.global_features)
    actions = torch.zeros(2, 5, 2, dtype=torch.long)
    quantities = torch.ones_like(actions)
    turns = torch.ones(2, 5, dtype=torch.bool)
    decisions = torch.ones_like(actions, dtype=torch.bool)
    critic = model.critic
    assert critic is not None
    first = critic(board, units, globals_, actions, quantities, turns, decisions)
    changed = board.clone()
    changed[:, 3:] += 10
    later = critic(changed, units, globals_, actions, quantities, turns, decisions)
    torch.testing.assert_close(first[:, :3], later[:, :3])
    changed_actions = actions.clone()
    changed_actions[:, 2:] += 1
    later_action = critic(board, units, globals_, changed_actions, quantities, turns, decisions)
    torch.testing.assert_close(first[:, :3], later_action[:, :3])
    first.square().mean().backward()
    assert critic.board[0].weight.grad.abs().sum() > 0
    assert critic.memory.weight_ih_l0.grad.abs().sum() > 0
    assert all(parameter.grad is None for parameter in model.actor.parameters())
    assert all(parameter.grad is None for parameter in model.effects.parameters())


def test_task_candidates_preserve_destinations_and_prefix_changes_odds() -> None:
    backend = load_backend(_root())
    env = {"boardSize": 3, "episodeSteps": 16, "maxMarketOrdersPerTurn": 2}
    engine = backend.engine(31, env)
    engine.step({"farmer": ["PASS"], "market": [["HIRE"]]}, {})
    old = backend.effect_policy_session(env, 4, 8)
    task = backend.effect_policy_session(env, 4, 8, task_conditioning=True)
    before = old.observe(engine, 0)
    after = task.observe(engine, 0)
    kinds = backend.effect_policy_spec()["request_kinds"]
    old_fields = np.asarray(before["candidate_fields"])
    new_fields = np.asarray(after["candidate_fields"])
    assert ((old_fields[:, 0] == kinds["STAGE"]) & (old_fields[:, 5] > 0)).any()
    assert not ((new_fields[:, 0] == kinds["STAGE"]) & (new_fields[:, 5] > 0)).any()
    kept = old_fields[~((old_fields[:, 0] == kinds["STAGE"]) & (old_fields[:, 5] > 0))]
    # Canonical candidate position is regenerated after removing aliases.
    np.testing.assert_array_equal(kept[:, :10], new_fields[:, :10])
    batch = backend.effect_policy_batch([task], [engine], np.array([0]), 1, True)
    root = tensor_state_from_native(batch.observe(np.array([0])), "cpu")
    candidates = root.candidate_fields[0]
    chosen = int(((candidates[:, 0] == kinds["STAGE"]) & root.candidate_mask[0]).nonzero()[0])
    batch.advance(np.array([chosen]), np.array([0], np.float32), np.array([0], np.float32), 0)
    prefix = tensor_state_from_native(batch.observe(np.array([0])), "cpu")
    assert prefix.work_mask.sum() == 1
    assert prefix.work_prefix[0, 0, 5] > 0
    base, _ = _model(backend, env)
    policy = EffectPolicy(base.effects.architecture.model_copy(update={"task_conditioning": True}))
    policy.load_state_dict(base.effects.state_dict(), strict=False)
    context = torch.randn(1, policy.architecture.context_width)
    tiles = torch.randn(1, policy.architecture.tile_count, policy.architecture.context_width)
    encoding = encode_tasks(policy, context, tiles, root, None)
    initial = condition_tasks(policy, encoding, prefix.work_prefix, prefix.work_mask, prefix.phase)
    original = base.effects(context, tiles, root, mask_candidates=False).candidate_logits
    torch.testing.assert_close(initial[prefix.candidate_mask], original[prefix.candidate_mask])
    torch.nn.init.normal_(policy.prefix_query[-1].weight, std=0.1)
    logits = condition_tasks(policy, encoding, prefix.work_prefix, prefix.work_mask, prefix.phase)
    direct = policy(context, tiles, prefix).candidate_logits
    torch.testing.assert_close(logits[prefix.candidate_mask], direct[prefix.candidate_mask])
    correction = (logits - encoding.logits)[prefix.candidate_mask]
    assert correction.std() > 1e-5
    logits[prefix.candidate_mask].square().mean().backward()
    assert policy.prefix_query[-1].weight.grad.abs().sum() > 0


def test_gae_uses_official_time_and_shares_factor_advantages() -> None:
    episodes = torch.tensor([0, 0, 0, 0])
    turns = torch.tensor([0, 0, 1, 2])
    root = torch.tensor([True, False, True, True])
    old = torch.tensor([0.2, 0.2, 0.4, 0.6])
    result = terminal_effect_advantages(
        torch.tensor([1.0]),
        old,
        episodes,
        turns,
        root,
        turn_horizon=3,
        normalize=False,
        gae_lambda=0.5,
    )
    torch.testing.assert_close(result.values, torch.tensor([0.4, 0.4, 0.4, 0.4]))
    mc = terminal_effect_advantages(
        torch.tensor([1.0]),
        old,
        episodes,
        turns,
        root,
        turn_horizon=3,
        normalize=False,
    )
    torch.testing.assert_close(mc.values, 1 - old)


def test_task_prefix_retains_which_unit_owns_each_request() -> None:
    backend = load_backend(_root())
    base, _ = _model(backend, {"boardSize": 2, "maxMarketOrdersPerTurn": 2})
    policy = EffectPolicy(base.effects.architecture.model_copy(update={"task_conditioning": True}))
    torch.nn.init.normal_(policy.prefix_query[-1].weight, std=0.1)
    width = policy.architecture.model_width
    encoding = TaskEncoding(torch.zeros(1, 3), torch.randn(1, width), torch.randn(1, 3, width))
    first = torch.tensor([[[1, 0, 1, 1, 0, 1], [2, 1, 0, 1, 0, 2]]])
    swapped = first.clone()
    swapped[..., 5] = first[..., 5].flip(1)
    mask = torch.ones(1, 2, dtype=torch.bool)
    phase = torch.zeros(1, dtype=torch.long)
    a = condition_tasks(policy, encoding, first, mask, phase)
    b = condition_tasks(policy, encoding, swapped, mask, phase)
    assert abs(float(((a[0, 0] - a[0, 1]) - (b[0, 0] - b[0, 1])).detach())) > 1e-6


@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA graph boundary")
def test_task_cuda_rollout_replays_conditional_probabilities_and_values() -> None:
    backend = load_backend(_root())
    env = {"boardSize": 3, "episodeSteps": 12, "maxMarketOrdersPerTurn": 2}
    base, contract = _model(backend, env)
    actor = TurnPolicyNet(base.actor.architecture.model_copy(update={"max_history": 11}))
    effects = EffectPolicy(
        base.effects.architecture.model_copy(
            update={
                "independent_critic": True,
                "task_conditioning": True,
                "destination_tasks": False,
            }
        )
    )
    torch.nn.init.normal_(effects.prefix_query[-1].weight, std=0.05)
    model = EffectActorCritic(actor, effects).cuda().eval()
    collector = EffectRolloutCollector(
        backend,
        model,
        contract,
        env,
        unit_limit=4,
        cpu_workers=1,
        device=torch.device("cuda:0"),
        action_generator=torch.Generator(device="cuda").manual_seed(9),
    )
    try:
        result = collector.collect_jobs([(7, 0, "self_play")])
        audit = audit_effect_behavior(
            model, result.batch, torch.device("cuda:0"), episodes_per_batch=2
        )
        assert audit["maximum_absolute_value_error"] < 1e-4
        selected = result.batch.subset((0, 1), torch.device("cuda:0"))
        with torch.no_grad():
            full = _sequence_context(model, selected)

            def reject_unused_value(*args: object) -> None:
                raise AssertionError("policy guard evaluated the independent critic")

            hook = model.critic.register_forward_pre_hook(reject_unused_value)
            try:
                policy_only = _sequence_context(model, selected, compute_value=False)
            finally:
                hook.remove()
            torch.testing.assert_close(full.context, policy_only.context)
            torch.testing.assert_close(full.tile_context, policy_only.tile_context)
    finally:
        collector.close()
