"""High-risk pure-self-play invariants for unit-task PPO."""

from kagg_revue.rl.tasks.rollout import task_rollout_jobs
from kagg_revue.rl.tasks.train import _outcome_metrics_from_rows


def test_task_self_play_uses_one_match_and_two_training_perspectives() -> None:
    jobs = task_rollout_jobs((7, 11), ("self_play",))

    assert jobs == [(7, 0, "self_play"), (11, 0, "self_play")]
    metrics = _outcome_metrics_from_rows(
        (
            ("self_play", 7, 0, 1, 9.0, 4.0),
            ("self_play", 7, 1, -1, 4.0, 9.0),
            ("self_play", 11, 0, 0, 6.0, 6.0),
            ("self_play", 11, 1, 0, 6.0, 6.0),
        )
    )

    assert metrics["self_play"] == {
        "games": 2,
        "training_episodes": 4,
        "wins": 1,
        "ties": 1,
        "losses": 0,
        "mean_terminal_cash": 7.5,
        "mean_cash_difference": 2.5,
    }
    assert metrics["overall"] == {
        "games": 2,
        "training_episodes": 4,
        "wins": 1,
        "ties": 1,
        "losses": 0,
    }
