import torch

from kagg_revue.rl.data import Trajectory
from kagg_revue.rl.pfsp import HistoricalPfsp


def _trajectory(outcome: int) -> Trajectory:
    return Trajectory(
        episode_id=str(outcome),
        opponent_id="synthetic",
        seed=0,
        seat=0,
        turns=(),
        outcome=outcome,
        terminal_cash=0.0,
        opponent_cash=0.0,
    )


def test_pfsp_excludes_current_actor_and_records_direct_outcomes() -> None:
    league = HistoricalPfsp(capacity=2, self_play_probability=0.0, seed=7)
    actor = torch.nn.Linear(2, 2)
    league.add("old", {"sha256": "old"}, actor)
    league.add("current", {"sha256": "current"}, actor)

    selected = league.select("current")

    assert selected is not None
    assert selected.identity == "old"
    league.record(selected, [_trajectory(1), _trajectory(0), _trajectory(-1)])
    summary = selected.summary()
    assert (summary["wins"], summary["ties"], summary["losses"]) == (1, 1, 1)
    assert summary["win_probability"] == 0.5


def test_pfsp_clones_an_explicit_anchor_state() -> None:
    league = HistoricalPfsp(capacity=2, self_play_probability=0.0, seed=11)
    state = {"weight": torch.ones(2)}
    league.add_state("anchor", {"kind": "initial_actor"}, state)
    state["weight"].zero_()
    league.add_state("current", {"kind": "checkpoint"}, {"weight": torch.zeros(2)})

    selected = league.select("current")

    assert selected is not None
    assert torch.equal(selected.actor_state["weight"], torch.ones(2))


def test_pfsp_state_round_trip_restores_population_and_sampler() -> None:
    league = HistoricalPfsp(capacity=3, self_play_probability=0.25, seed=13)
    league.add_state("old", {"kind": "checkpoint"}, {"weight": torch.ones(2)})
    league.add_state("current", {"kind": "checkpoint"}, {"weight": torch.zeros(2)})
    selected = league.select("current")
    if selected is not None:
        league.record(selected, [_trajectory(1), _trajectory(-1)])
    state = league.state_dict()
    restored = HistoricalPfsp(capacity=3, self_play_probability=0.25, seed=99)

    restored.load_state_dict(state)

    assert restored.report() == league.report()
    restored_state = restored.state_dict()
    policies = restored_state["policies"]
    assert isinstance(policies, list)
    assert torch.equal(policies[0]["actor_state"]["weight"], torch.ones(2))
    for _ in range(8):
        original_choice = league.select("current")
        restored_choice = restored.select("current")
        assert (None if original_choice is None else original_choice.identity) == (
            None if restored_choice is None else restored_choice.identity
        )
