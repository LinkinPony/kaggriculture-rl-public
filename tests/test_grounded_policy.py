from pathlib import Path

import numpy as np
import torch

from kagg_revue.learning.adapter import runtime_settings
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.initialization import random_policy
from kagg_revue.native import _revue_native as native
from kagg_revue.policy.grounded.model import GroundedPolicy
from kagg_revue.production.contracts import ContractLayout
from kagg_revue.production.evaluation.matches import PairedPolicy
from kagg_revue.production.model import log_probabilities


def _configuration() -> Experiment:
    return Experiment(
        output_dir=Path("outputs/learning/component-check"),
        architecture="grounded-v1",
        decision_interval=1,
        width=16,
        depth=1,
        critic_width=16,
        critic_depth=1,
        unit_limit=4,
        environment={
            "boardSize": 4,
            "episodeSteps": 25,
            "turnsPerDay": 4,
            "maxMarketOrdersPerTurn": 2,
        },
    )


def test_single_turn_sampling_replays_and_ignores_missing_unit_fields() -> None:
    torch.set_num_threads(1)
    config = _configuration()
    layout = ContractLayout.resolve(runtime_settings(config))
    policy = random_policy(layout, 3, config.exploration)
    observation = native.Engine(9, config.environment).observation(0)
    session = native.ContractSession(config.environment, config.unit_limit)
    session.update(observation)
    packed = np.empty((1, layout.observation.features), dtype=np.float16)
    session.observe_into(packed)
    inputs = torch.from_numpy(packed).float().expand(32, -1)
    steps = torch.zeros(32, dtype=torch.long)
    actions, behavior = policy.act(inputs, steps, sample=True)
    replay = policy(inputs, steps, actions)
    torch.testing.assert_close(behavior, log_probabilities(replay, actions))
    jobs = actions[:, : layout.work_factors].reshape(32, config.unit_limit, 2, 4)
    assert not jobs[:, 1:].any()
    assert not jobs[:, :, 1].any()
    assert not jobs[..., 3].any()
    weights = policy.field_weights(actions, steps, inputs)
    assert not weights[:, 8 : layout.work_factors].any()
    assert not behavior[weights == 0].any()
    changed = inputs.clone()
    start = layout.observation.board_features + layout.observation.unit_features
    absent = changed[:, start : start + 3 * layout.observation.unit_features].reshape(32, 3, -1)
    absent[..., 1:] += 100
    torch.testing.assert_close(policy(changed, steps, actions), replay)
    loss = -(log_probabilities(replay, actions) * weights).sum(-1).mean()
    loss.backward()
    assert any(p.grad is not None and p.grad.abs().sum() > 0 for p in policy.encoder.parameters())
    assert all(torch.isfinite(p.grad).all() for p in policy.parameters() if p.grad is not None)


def test_operation_quantity_exploration_preserves_buys_and_can_learn_large_sales() -> None:
    config = _configuration()
    layout = ContractLayout.resolve(runtime_settings(config))
    shared = random_policy(layout, 7, config.exploration)
    config = config.model_copy(update={"operation_quantity_bias": True})
    expanded = random_policy(
        ContractLayout.resolve(runtime_settings(config)), 7, config.exploration
    )
    assert isinstance(expanded, GroundedPolicy)
    for key, value in shared.state_dict().items():
        torch.testing.assert_close(value, expanded.state_dict()[key])
    observation = native.Engine(9, config.environment).observation(0)
    session = native.ContractSession(config.environment, config.unit_limit)
    session.update(observation)
    packed = np.empty((1, layout.observation.features), dtype=np.float16)
    session.observe_into(packed)
    inputs = torch.from_numpy(packed).float().expand(2, -1)
    steps = torch.zeros(2, dtype=torch.long)
    actions = torch.zeros((2, layout.factors), dtype=torch.long)
    actions[:, layout.work_factors] = torch.tensor([2, 11])
    before = shared(inputs, steps, actions)
    after = expanded(inputs, steps, actions)
    quantity = layout.work_factors + 1
    torch.testing.assert_close(before[1, : quantity + 1], after[1, : quantity + 1])
    probabilities = after[0, quantity].softmax(-1)
    large = torch.tensor(layout.observation.quantities) > 16
    assert probabilities[: len(large)][large].sum() > 0.3
    (-after[0, quantity].log_softmax(-1)[len(large) - 1]).backward()
    assert expanded.quantity_offsets.grad is not None
    assert expanded.quantity_offsets.grad[2].abs().sum() > 0
    paired = PairedPolicy(shared, expanded, 2)
    chosen, _ = paired.act(inputs.repeat(2, 1), steps.repeat(2), sample=False)
    left, _ = shared.act(inputs, steps, sample=False)
    right, _ = expanded.act(inputs, steps, sample=False)
    torch.testing.assert_close(chosen[paired.learner_rows], left)
    torch.testing.assert_close(chosen[paired.opponent_rows], right)


def test_native_support_matches_independent_unit_requests() -> None:
    config = _configuration()
    layout = ContractLayout.resolve(runtime_settings(config))
    engine = native.Engine(11, config.environment)
    packed = np.empty((1, layout.observation.features), dtype=np.float16)
    tiles = [
        None,
        {"kind": "WEED"},
        {"kind": "COOP"},
        {"kind": "PASTURE"},
        {
            "kind": "PLANT",
            "crop": "WHEAT",
            "planted_day": -10,
            "yield_units": 3,
            "watered_today": False,
            "consecutive_unwatered": 0,
            "max_lifespan_step": -1,
            "fertilized_until_day": -1,
        },
        {
            "kind": "COOP",
            "animal": "GOOSE",
            "placed_day": -10,
            "yield_units": 2,
            "fertilizer_available": True,
            "consecutive_unfed": 0,
            "fed_today": False,
            "cared_today": False,
            "pending_care_bonus": 0,
        },
    ]
    for tile in tiles:
        observation = engine.observation(0)
        farm = observation["farms"][0]
        farm["farmer"] = [1, 1]
        farm["tiles"][1][1] = tile
        private = observation["private"]
        private["shed"] = {name: 7 for name in private["shed"]}
        private["seeds"] = {name: 7 for name in private["seeds"]}
        private["inventories"] = [{name: 2 for name in private["shed"]}]
        session = native.ContractSession(config.environment, config.unit_limit)
        session.update(observation)
        session.observe_into(packed)
        support = packed[0, -layout.observation.support_features :].reshape(config.unit_limit, 44)
        assert not support[1:].any()
        for token in range(44):
            raw = native.decode_action_tokens(np.array([token, 44]), np.array([1, 1]), 2, 1, 2)
            actual = native.compile_unit_prefix_from_obs(observation, config.environment, raw)
            assert bool(support[0, token]) == (actual["action"]["farmer"] == raw["farmer"])


def test_grounded_batch_and_deployment_match_each_official_transition() -> None:
    torch.set_num_threads(1)
    config = _configuration()
    layout = ContractLayout.resolve(runtime_settings(config))
    policy = random_policy(layout, 19, config.exploration)
    batch = native.ParallelBatch(
        config.environment,
        [7],
        [0],
        [],
        [],
        [],
        config.unit_limit,
        1,
        list(layout.observation.quantities),
    )
    engine = native.Engine(7, config.environment)
    sessions = [native.ContractSession(config.environment, config.unit_limit) for _ in range(2)]
    packed = np.empty((2, layout.observation.features), dtype=np.float16)
    expected = np.empty_like(packed)
    for turn in range(layout.observation.turns):
        batch.observe_selfplay_into(packed)
        for seat, session in enumerate(sessions):
            session.update(engine.observation(seat))
            session.observe_into(expected[seat : seat + 1])
        np.testing.assert_array_equal(packed, expected)
        with torch.no_grad():
            selected, _ = policy.act(
                torch.from_numpy(packed).float(), torch.full((2,), turn), sample=True
            )
        plans = selected.numpy()
        for seat, session in enumerate(sessions):
            session.set_program(plans[seat : seat + 1], 1, list(layout.observation.quantities))
        engine.step(*(session.program_action() for session in sessions))
        batch.advance_programs(plans, 1, 1, True)
        assert batch.observation(0) == engine.observation(0)
    assert batch.completed_games == 1
    assert engine.done
