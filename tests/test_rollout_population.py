from collections import Counter, defaultdict

import pytest

from kagg_revue.rl.data import RolloutMatch
from kagg_revue.rl.rollout.population import (
    opponent_outcome_metrics,
    weighted_rollout_jobs,
)
from kagg_revue.rl.rollout.scheduler import _group_rollout_jobs


def test_weighted_jobs_balance_global_counts_and_keep_paired_external_seats() -> None:
    weights = {"self_play": 0.5, "alpha": 0.3, "beta": 0.2}
    seeds = tuple(range(20))
    rank_jobs = [
        weighted_rollout_jobs(
            seeds,
            weights,
            rank=rank,
            world_size=2,
            sampling_seed=31,
        )
        for rank in range(2)
    ]

    seed_counts = Counter(opponent for jobs in rank_jobs for _, seat, opponent in jobs if seat == 0)
    assert seed_counts == {"self_play": 10, "alpha": 6, "beta": 4}
    for jobs in rank_jobs:
        training_trajectories = sum(
            2 if opponent == "self_play" else 1 for _, _, opponent in jobs
        )
        assert training_trajectories == 20
        seats_by_external_seed: defaultdict[tuple[str, int], set[int]] = defaultdict(set)
        for seed, seat, opponent in jobs:
            if opponent != "self_play":
                seats_by_external_seed[(opponent, seed)].add(seat)
        assert all(seats == {0, 1} for seats in seats_by_external_seed.values())


def test_opponent_metrics_use_matches_for_wdl_and_trajectories_for_mix() -> None:
    matches = (
        RolloutMatch("self:1:0", "self_play", 1, 0, 1, 8.0, 5.0),
        RolloutMatch("alpha:2:0", "alpha", 2, 0, -1, 3.0, 7.0),
        RolloutMatch("alpha:2:1", "alpha", 2, 1, 0, 6.0, 6.0),
    )

    metrics = opponent_outcome_metrics(
        matches,
        ("self_play", "self_play", "alpha", "alpha"),
    )

    assert metrics["self_play"]["games"] == 1
    assert metrics["self_play"]["training_fraction"] == pytest.approx(0.5)
    assert metrics["alpha"]["wins"] == 0
    assert metrics["alpha"]["ties"] == 1
    assert metrics["alpha"]["losses"] == 1
    assert metrics["alpha"]["mean_cash_difference"] == pytest.approx(-2.0)


def test_gpu_actor_opponent_batches_do_not_mix_lineages() -> None:
    jobs = (
        (1, 0, "self_play"),
        (2, 0, "self_play"),
        (3, 0, "snapshot"),
        (3, 1, "snapshot"),
        (4, 0, "snapshot"),
        (4, 1, "snapshot"),
    )

    groups = _group_rollout_jobs(jobs, 3, isolate_opponents=True)

    assert [[job[2] for job in group] for group in groups] == [
        ["self_play", "self_play"],
        ["snapshot", "snapshot", "snapshot"],
        ["snapshot"],
    ]
