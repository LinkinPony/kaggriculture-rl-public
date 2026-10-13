import numpy as np
import torch

from kagg_revue.native import _revue_native as native
from kagg_revue.production.history import HistoricalBatch
from kagg_revue.production.learning import advantage_moments, weighted_mean
from kagg_revue.production.population import TrainingBatch, episode_weights, outcomes, policy_rows


def test_historical_seat_routing_matches_native_two_actor_games() -> None:
    environment = {
        "boardSize": 4,
        "episodeSteps": 9,
        "turnsPerDay": 3,
        "maxMarketOrdersPerTurn": 2,
    }
    seeds, units, span = [5, 9], 2, 2
    owner = native.ParallelBatch(environment, seeds, [0, 0], [], [], [], units, 1, [1])
    reference = native.ParallelBatch(environment, seeds, [0, 0], [], [], [], units, 1, [1])
    work = units * (span + 1) * 4
    width = work + span * environment["maxMarketOrdersPerTurn"] * 2
    learned = np.zeros((len(seeds), width), dtype=np.int64)
    frozen = np.zeros_like(learned)
    frozen[:, work : work + 2] = [11, 0]
    learner_views = np.empty((len(seeds), owner.entity_features), np.float16)
    frozen_views = np.empty_like(learner_views)
    batch = HistoricalBatch(owner, np.array([0, 1]), frozen_views, frozen)
    expected_views = np.empty((2 * len(seeds), owner.entity_features), np.float16)
    # The learner is left in the first game and right in the second game.
    expected_plans = np.stack((learned[0], frozen[0], frozen[1], learned[1]))
    for _ in range(0, environment["episodeSteps"] - 1, span):
        batch.observe_into(learner_views)
        reference.observe_selfplay_into(expected_views)
        np.testing.assert_array_equal(learner_views, expected_views[[0, 3]])
        np.testing.assert_array_equal(frozen_views, expected_views[[1, 2]])
        batch.advance_programs(learned, span, span)
        reference.advance_programs(expected_plans, span, span, True)
    expected_cash = reference.cash()
    np.testing.assert_array_equal(
        batch.cash(), np.stack((expected_cash[0], expected_cash[1, ::-1]))
    )
    assert batch.completed_games == len(seeds)
    assert batch.transitions == len(seeds) * (environment["episodeSteps"] - 1)
    assert np.all(batch.cash()[:, 0] > batch.cash()[:, 1])


def test_mixed_native_rows_preserve_both_selfplay_seats_and_script_candidate_seats() -> None:
    environment = {
        "boardSize": 4,
        "episodeSteps": 17,
        "turnsPerDay": 3,
        "maxMarketOrdersPerTurn": 3,
    }
    seeds = [7, 11, 13]
    units = 3
    selfplay = native.ParallelBatch(environment, seeds[:1], [0], [], [], [], units, 1, [1])
    scripts = native.ParallelBatch(
        environment, seeds[1:], [0, 1], ["pass", "pass"], [None, None], [], units, 1, [1]
    )
    mixed = TrainingBatch(selfplay, scripts, 1, ("self_play", "control", "control"))
    references = [native.Engine(seed, environment) for seed in seeds]
    cells = environment["boardSize"] ** 2
    plans = np.zeros((4, cells * 4 + 23), dtype=np.int64)
    plans[:, : cells * 4] = np.tile([1, 1, 1, 2], cells)
    plans[:, cells * 4 : cells * 4 + 5] = [2, 1, 0, 4, 2]
    plans[1, : cells * 4 : 4] = 2
    encoded = np.empty((len(plans), selfplay.entity_features), dtype=np.float16)
    expected = np.empty_like(encoded)
    while not references[0].done:
        mixed.observe_into(encoded)
        selfplay.observe_selfplay_into(expected[:2])
        scripts.observe_into(expected[2:])
        np.testing.assert_array_equal(encoded, expected)
        references[0].step(
            selfplay.contract_action(0, plans[:1], player=0),
            selfplay.contract_action(0, plans[1:2], player=1),
        )
        references[1].step(scripts.contract_action(0, plans[2:]), {})
        references[2].step({}, scripts.contract_action(1, plans[2:]))
        mixed.advance(plans, 1)
    cash = mixed.cash(environment["episodeSteps"] - 1)
    expected_cash = np.array(
        [
            [references[0].money(0), references[0].money(1)],
            [references[1].money(0), references[1].money(1)],
            [references[2].money(1), references[2].money(0)],
        ],
        dtype=np.float64,
    )
    np.testing.assert_array_equal(cash, expected_cash)
    learned = policy_rows(cash, 1)
    np.testing.assert_array_equal(learned, [*expected_cash[0], *expected_cash[1:, 0]])
    changed_script_cash = cash.copy()
    changed_script_cash[1:, 1] += 12345
    np.testing.assert_array_equal(policy_rows(changed_script_cash, 1), learned)


def test_episode_weighted_gradients_and_moments_are_independent_of_seat_duplication() -> None:
    # One game has two learned seats; the other has one. Each game's total mass is equal.
    parameter = torch.tensor(2.0, requires_grad=True)
    losses = parameter * torch.tensor([1.0, 3.0, 8.0])
    weights = torch.from_numpy(episode_weights(1, 1))
    expected = ((losses[0] + losses[1]) / 2 + losses[2]) / 2
    actual = weighted_mean(losses, weights, weights.sum())
    torch.testing.assert_close(actual, expected)
    expected_gradient = torch.autograd.grad(expected, parameter, retain_graph=True)[0]
    # Emulate unequal rank masses and bounded microbatches before averaged gradients.
    rank_mass = weights.sum() / 2
    sharded = (
        sum(
            weighted_mean(v, w, rank_mass)
            for v, w in zip(losses.split(1), weights.split(1), strict=True)
        )
        / 2
    )
    torch.testing.assert_close(torch.autograd.grad(sharded, parameter)[0], expected_gradient)
    values = torch.tensor([1.0, 3.0, 8.0])
    torch.testing.assert_close(
        advantage_moments(values, weights),
        torch.stack(
            (
                torch.tensor([1.0, 3.0, 8.0, 8.0]).mean(),
                torch.tensor([1.0, 3.0, 8.0, 8.0]).square().mean(),
            )
        ),
    )


def test_opponent_metrics_use_physical_games_and_exclude_script_cash() -> None:
    cash = np.array([[20, 30], [10, 99], [40, 2]], dtype=np.float64)
    result = outcomes(cash, ["self_play", "control", "control"])
    assert sum(row["training_fraction"] for row in result.values()) == 1
    assert result["control"]["mean_terminal_cash"] == cash[1:, 0].mean()
    assert result["control"]["training_fraction"] == len(cash[1:]) / len(cash)
    assert sum(row["training_trajectories"] for row in result.values()) == len(policy_rows(cash, 1))
