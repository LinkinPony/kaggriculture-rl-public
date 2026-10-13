import numpy as np
import torch

from kagg_revue.rl.data import (
    Trajectory,
    TurnRecord,
    collate_trajectories,
    opening_residual_inputs,
)


def _turn(decisions: int) -> TurnRecord:
    return TurnRecord(
        board=np.zeros((2, 1, 1, 1), dtype=np.float16),
        units=np.zeros((2, 1, 1), dtype=np.float16),
        global_features=np.zeros(1, dtype=np.float32),
        economic_state=np.zeros(0, dtype=np.int32),
        turn_facts=np.zeros((1, 2), dtype=np.float16),
        prefix_facts=np.zeros((decisions, 3), dtype=np.float16),
        candidate_facts=np.zeros((decisions, 4, 5), dtype=np.float16),
        legal_mask=np.ones((decisions, 4), dtype=np.bool_),
        actions=np.zeros(decisions, dtype=np.int64),
        quantities=np.zeros(decisions, dtype=np.float32),
        phases=np.zeros(decisions, dtype=np.int64),
        decision_mask=np.ones(decisions, dtype=np.bool_),
        old_log_probability=np.zeros(decisions, dtype=np.float32),
        skill_id=-1,
        old_skill_log_probability=0.0,
        old_value=0.0,
    )


def test_rollout_collation_pads_variable_decision_prefixes() -> None:
    trajectory = Trajectory(
        episode_id="synthetic",
        opponent_id="synthetic",
        seed=0,
        seat=0,
        turns=(_turn(1), _turn(3)),
        outcome=1,
        terminal_cash=1.0,
        opponent_cash=0.0,
    )

    batch = collate_trajectories([trajectory], torch.device("cpu"))

    assert batch.actions.shape == (1, 2, 3)
    assert batch.decision_mask.sum(dim=-1).tolist() == [[1, 3]]
    assert not batch.legal_mask[0, 0, 1:].any()
    assert batch.cash_differences.tolist() == [1.0]


def test_opening_residual_and_prefix_mask_enter_ppo_collation() -> None:
    trajectory = Trajectory(
        episode_id="proposal",
        opponent_id="synthetic",
        seed=0,
        seat=0,
        turns=(_turn(1),),
        outcome=1,
        terminal_cash=1.0,
        opponent_cash=0.0,
        opening_residual=np.ones((4, 8), dtype=np.float32),
        opening_residual_turns=1,
    )

    batch = collate_trajectories([trajectory], torch.device("cpu"))
    residual, mask = opening_residual_inputs(batch)

    assert residual is not None
    assert mask is not None
    torch.testing.assert_close(residual, torch.ones((1, 4, 8)))
    assert mask.tolist() == [[True]]
