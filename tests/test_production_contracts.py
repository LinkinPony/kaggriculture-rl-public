import numpy as np
import pytest
import torch

from kagg_revue.native import _revue_native as native
from kagg_revue.production.contracts import ContractLayout
from kagg_revue.production.model import Policy, log_probabilities
from kagg_revue.production.native import Layout


def test_macro_execution_matches_primitive_boundary_and_rejects_invalid_contract() -> None:
    environment = {
        "boardSize": 4,
        "episodeSteps": 17,
        "turnsPerDay": 3,
        "maxMarketOrdersPerTurn": 3,
    }
    units = 3
    batch = native.ParallelBatch(environment, [7], [1], ["pass"], [None], [], units, 1, [1])
    reference = native.Engine(7, environment)
    cells = environment["boardSize"] ** 2
    plan = np.zeros((1, cells * 4 + 23), dtype=np.int64)
    plan[:, : cells * 4] = np.tile([1, 1, 1, 1], cells)
    plan[0, cells * 4 : cells * 4 + 5] = [2, 1, 0, 4, 2]
    while not reference.done:
        action = batch.contract_action(0, plan)
        reference.step({}, action)
        batch.advance(plan, 1)
        assert batch.observation(0) == reference.observation(1)
    assert batch.completed_games == 1
    assert batch.transitions == reference.step_index
    np.testing.assert_array_equal(batch.cash()[0], [reference.money(1), reference.money(0)])

    grouped = native.ParallelBatch(environment, [7], [1], ["pass"], [None], [], units, 1, [1])
    malformed = plan.copy()
    malformed[0, 0] = -1
    with pytest.raises(ValueError):
        grouped.advance(malformed, 5)
    assert grouped.step_index == 0
    grouped.advance(plan, environment["episodeSteps"])
    assert grouped.observation(0) == reference.observation(1)


def test_sampled_contract_probabilities_replay_with_valid_field_support() -> None:
    spec = native.parallel_spec()
    cells, units = 4, 2
    base = Layout(
        2 * spec["board_channels"] * cells,
        spec["unit_features"],
        spec["global_features"],
        units,
        2,
        7,
        (1,),
        8,
        spec["version"],
    )
    layout = ContractLayout(base, 2, 3)
    policy = Policy(layout)
    observations = torch.randn(3, base.features)
    steps = torch.arange(3)
    actions, behavior = policy.act(observations, steps, sample=True)
    logits = policy(observations, steps)
    torch.testing.assert_close(behavior, log_probabilities(logits, actions))
    assert torch.all(actions < torch.tensor(layout.cardinalities))
    loss = -log_probabilities(logits, actions).mean()
    loss.backward()
    assert policy.prior.grad is not None
    assert torch.isfinite(policy.prior.grad).all()


def test_selfplay_shares_state_and_encodes_only_each_seats_private_view() -> None:
    environment = {
        "boardSize": 4,
        "episodeSteps": 19,
        "turnsPerDay": 3,
        "maxMarketOrdersPerTurn": 3,
    }
    units = 3
    batch = native.ParallelBatch(environment, [11], [0], [], [], [], units, 1, [1])
    reference = native.Engine(11, environment)
    cells = environment["boardSize"] ** 2
    plans = np.zeros((2, cells * 4 + 23), dtype=np.int64)
    plans[0, : cells * 4] = np.tile([1, 1, 1, 2], cells)
    plans[1, : cells * 4] = np.tile([2, 2, 2, 1], cells)
    plans[:, cells * 4 : cells * 4 + 5] = [2, 1, 0, 4, 2]
    encoded = np.empty((2, batch.features), dtype=np.float16)
    for seat in range(2):
        single = native.ParallelBatch(environment, [11], [seat], [], [], [], units, 1, [1])
        expected = np.empty((1, batch.features), dtype=np.float16)
        single.observe_into(expected)
        batch.observe_selfplay_into(encoded)
        np.testing.assert_array_equal(encoded[seat], expected[0])
    malformed = plans.copy()
    malformed[1, 0] = -1
    with pytest.raises(ValueError):
        batch.advance_selfplay(malformed, 2)
    assert batch.step_index == 0
    while not reference.done:
        left = batch.contract_action(0, plans[:1], player=0)
        right = batch.contract_action(0, plans[1:], player=1)
        reference.step(left, right)
        batch.advance_selfplay(plans, 1)
        assert batch.observation(0) == reference.observation(0)
    assert batch.completed_games == 1
    assert batch.transitions == reference.step_index
    np.testing.assert_array_equal(batch.cash()[0], [reference.money(0), reference.money(1)])
    grouped = native.ParallelBatch(environment, [11], [0], [], [], [], units, 1, [1])
    grouped.advance_selfplay(plans, environment["episodeSteps"])
    assert grouped.observation(0) == reference.observation(0)
