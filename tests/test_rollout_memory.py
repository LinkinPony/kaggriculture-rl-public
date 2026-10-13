from collections.abc import Sequence
from dataclasses import replace
from types import SimpleNamespace
from typing import cast

import numpy as np
import torch

from kagg_revue.policy.model import ActorArchitecture
from kagg_revue.rl.data import RolloutMatch, Trajectory, TurnRecord
from kagg_revue.rl.minibatch import RolloutBatchPipeline
from kagg_revue.rl.rollout.scheduler import rollout_jobs
from kagg_revue.rl.rollout.storage import (
    BatchedStoredTurns,
    RolloutPanel,
    StoredTurn,
)
from kagg_revue.rl.train import _rollout_summary


def _architecture() -> ActorArchitecture:
    return ActorArchitecture(
        board_shape=(2, 1, 2, 2),
        unit_shape=(2, 1, 2),
        global_features=2,
        model_width=8,
        entity_width=4,
        attention_heads=1,
        feedforward_width=8,
        latent_tokens=1,
        scene_layers=0,
        temporal_layers=1,
        action_layers=1,
        max_history=2,
        max_decisions=3,
        unit_action_tokens=2,
        market_action_tokens=2,
        maximum_quantity=2,
        derived_fact_version=None,
        turn_fact_features=0,
        prefix_fact_features=0,
        candidate_fact_features=0,
        fact_dropout=0.0,
    )


def _turn(architecture: ActorArchitecture, marker: float) -> StoredTurn:
    decisions = architecture.max_decisions
    tokens = architecture.action_tokens
    decision_mask = np.zeros(decisions, dtype=np.bool_)
    decision_mask[:2] = True
    legal = np.zeros((decisions, tokens), dtype=np.bool_)
    legal[:2, 0] = True
    actions = np.full(decisions, 3, dtype=np.int64)
    actions[:2] = (0, 1)
    return cast(
        StoredTurn,
        SimpleNamespace(
            board=np.full(architecture.board_shape, marker, dtype=np.float32),
            units=np.full(architecture.unit_shape, marker, dtype=np.float32),
            globals_=np.full(architecture.global_features, marker, dtype=np.float32),
            economic_state=np.zeros(0, dtype=np.int32),
            turn_facts=np.empty((0, 0), dtype=np.float32),
            prefix_facts=np.empty((decisions, 0), dtype=np.float16),
            candidate_facts=np.empty((decisions, tokens, 0), dtype=np.float16),
            legal=legal,
            actions=actions,
            quantities=np.arange(decisions, dtype=np.int64),
            phases=np.arange(decisions, dtype=np.int64),
            decisions=decision_mask,
            log_probability=np.arange(decisions, dtype=np.float32),
            skill_id=-1,
            skill_log_probability=0.0,
            old_value=marker,
        ),
    )


def _trajectory(
    episode_id: str,
    turns: Sequence[TurnRecord],
    outcome: int,
    opponent_id: str = "synthetic",
) -> Trajectory:
    return Trajectory(
        episode_id=episode_id,
        opponent_id=opponent_id,
        seed=0,
        seat=0,
        turns=turns,
        outcome=outcome,
        terminal_cash=float(outcome > 0),
        opponent_cash=float(outcome < 0),
    )


def _batched(turns: Sequence[StoredTurn]) -> BatchedStoredTurns:
    return BatchedStoredTurns(
        board=np.stack([turn.board for turn in turns]),
        units=np.stack([turn.units for turn in turns]),
        global_features=np.stack([turn.globals_ for turn in turns]),
        economic_state=np.stack([turn.economic_state for turn in turns]),
        legal_mask=np.stack([turn.legal for turn in turns], axis=1),
        actions=np.stack([turn.actions for turn in turns], axis=1),
        quantities=np.stack([turn.quantities for turn in turns], axis=1),
        phases=np.stack([turn.phases for turn in turns], axis=1),
        decision_mask=np.stack([turn.decisions for turn in turns], axis=1),
        old_log_probability=np.stack([turn.log_probability for turn in turns], axis=1),
        skill_ids=np.asarray([turn.skill_id for turn in turns], dtype=np.int64),
        old_skill_log_probability=np.asarray(
            [turn.skill_log_probability for turn in turns], dtype=np.float32
        ),
        old_values=np.asarray([turn.old_value for turn in turns], dtype=np.float32),
    )


def test_rollout_panel_copies_into_immutable_episode_views() -> None:
    architecture = _architecture()
    panel = RolloutPanel(2, 2, architecture)
    first = _turn(architecture, 1.0)
    panel.append([first, _turn(architecture, 2.0)])
    first.board.fill(9.0)
    panel.append([_turn(architecture, 3.0), _turn(architecture, 4.0)])

    episode = panel.trajectory(0)

    assert len(episode) == 2
    assert episode.board[:, 0, 0, 0, 0].tolist() == [1.0, 3.0]
    assert episode.actions[:, 2].tolist() == [-1, -1]
    assert not episode.decision_mask[:, 2].any()
    assert not episode.board.flags.writeable


def test_rollout_global_features_preserve_small_late_game_cash_difference() -> None:
    architecture = _architecture()
    panel = RolloutPanel(1, 1, architecture)
    turn = _turn(architecture, 0.0)
    cash_features = np.asarray([100_000.0 / 100_000.0, 12.0 / 100_000.0], dtype=np.float32)
    turn.globals_[:] = cash_features

    panel.append([turn])
    trajectory = _trajectory("late-game-cash", panel.trajectory(0), 1)
    pipeline = RolloutBatchPipeline([trajectory], 1, torch.device("cpu"))
    slot = pipeline.prepare(0, [trajectory])
    batch = pipeline.upload(slot)

    assert panel.global_features.dtype == np.float32
    assert batch.global_features.dtype == torch.float32
    assert batch.actions.shape[-1] == 2
    np.testing.assert_array_equal(batch.global_features[0, 0].numpy(), cash_features)
    pipeline.finish(slot)


def test_rollout_batch_preserves_full_unit_capacity() -> None:
    architecture = _architecture().model_copy(update={"unit_shape": (2, 3, 2)})
    panel = RolloutPanel(1, 1, architecture)
    turn = _turn(architecture, 1.0)
    turn.units[:, 1:] = 0.0
    panel.append([turn])
    trajectory = _trajectory("unit-capacity", panel.trajectory(0), 1)

    pipeline = RolloutBatchPipeline([trajectory], 1, torch.device("cpu"))
    prepared = pipeline.prepare(0, [trajectory])
    batch = pipeline.upload(prepared)

    assert batch.units.shape[-2] == architecture.unit_shape[1]
    np.testing.assert_array_equal(batch.units[0, 0].numpy(), turn.units)
    pipeline.finish(prepared)


def test_rollout_batch_expands_when_a_later_decision_becomes_active() -> None:
    architecture = _architecture()
    panel = RolloutPanel(2, 1, architecture)
    narrow = _turn(architecture, 1.0)
    narrow.decisions[1:] = False
    narrow.legal[1:] = False
    expanded = _turn(architecture, 2.0)
    expanded.decisions[:] = True
    expanded.legal[2, 0] = True
    expanded.actions[2] = 0
    panel.append([narrow, expanded])
    trajectories = [
        _trajectory("narrow-decisions", panel.trajectory(0), 1),
        _trajectory("expanded-decisions", panel.trajectory(1), -1),
    ]

    pipeline = RolloutBatchPipeline(trajectories, 1, torch.device("cpu"))
    prepared = pipeline.prepare(0, trajectories[1:])
    batch = pipeline.upload(prepared)

    assert batch.actions.shape[-1] == architecture.max_decisions
    assert batch.decision_mask[0, 0, -1]
    assert batch.actions[0, 0, -1].item() == expanded.actions[-1]
    pipeline.finish(prepared)


def test_batched_rollout_write_matches_row_storage() -> None:
    architecture = _architecture()
    selected = [_turn(architecture, 1.0), _turn(architecture, 2.0)]
    source = [
        selected[0],
        _turn(architecture, 9.0),
        selected[1],
        _turn(architecture, 8.0),
    ]
    row_panel = RolloutPanel(2, 1, architecture)
    batch_panel = RolloutPanel(2, 1, architecture)
    row_panel.append(selected)
    batch_panel.append_batched(_batched(source), slice(0, 4, 2))

    for row in range(2):
        expected = row_panel.trajectory(row)
        actual = batch_panel.trajectory(row)
        for expected_value, actual_value in zip(expected.arrays(), actual.arrays(), strict=True):
            np.testing.assert_array_equal(actual_value, expected_value)


def test_initialized_batched_rollout_sanitizes_inactive_phases() -> None:
    architecture = _architecture()
    source = [_turn(architecture, 1.0), _turn(architecture, 2.0)]
    turns = replace(_batched(source), inactive_values_initialized=True)
    panel = RolloutPanel(2, 1, architecture)

    panel.append_batched(turns, slice(None))

    for row in range(2):
        trajectory = panel.trajectory(row)
        assert trajectory.phases[0, :2].tolist() == [0, 1]
        assert trajectory.phases[0, 2] == 0
        assert not trajectory.decision_mask[0, 2]


def test_reserved_rollout_columns_can_finish_out_of_order() -> None:
    architecture = _architecture()
    panel = RolloutPanel(1, 2, architecture)
    first = panel.reserve()
    second = panel.reserve()

    panel.append_reserved(second, [_turn(architecture, 2.0)])
    panel.append_reserved(first, [_turn(architecture, 1.0)])

    episode = panel.trajectory(0)
    assert episode.board[:, 0, 0, 0, 0].tolist() == [1.0, 2.0]


def test_self_play_uses_one_match_and_two_training_perspectives() -> None:
    jobs = rollout_jobs([7, 11], ("self_play", "historical"))

    assert [job for job in jobs if job[2] == "self_play"] == [
        (7, 0, "self_play"),
        (11, 0, "self_play"),
    ]
    assert [job for job in jobs if job[2] == "historical"] == [
        (7, 0, "historical"),
        (7, 1, "historical"),
        (11, 0, "historical"),
        (11, 1, "historical"),
    ]


def test_rollout_summary_does_not_count_perspectives_as_matches() -> None:
    architecture = _architecture()
    panel = RolloutPanel(2, 1, architecture)
    panel.append([_turn(architecture, 1.0), _turn(architecture, 2.0)])
    trajectories = [
        _trajectory("seat-zero", panel.trajectory(0), 1, "self_play"),
        _trajectory("seat-one", panel.trajectory(1), -1, "self_play"),
    ]
    matches = (
        RolloutMatch(
            match_id="self-play:7:0",
            opponent_id="self_play",
            seed=7,
            candidate_seat=0,
            outcome=1,
            terminal_cash=4.0,
            opponent_cash=3.0,
        ),
    )

    summary = _rollout_summary(trajectories, matches, 1.0)

    assert summary["games"] == 1
    assert summary["training_trajectories"] == 2
    assert summary["wins"] == 1
    assert summary["training_outcome_classes"] == 2


def test_rollout_batch_pipeline_reuses_fixed_cpu_slots() -> None:
    architecture = _architecture()
    panel = RolloutPanel(2, 1, architecture)
    first_turn = _turn(architecture, 1.0)
    second_turn = _turn(architecture, 2.0)
    second_turn.decisions[1:] = False
    second_turn.legal[1:] = False
    panel.append([first_turn, second_turn])
    trajectories = [
        _trajectory("first", panel.trajectory(0), 1),
        _trajectory("second", panel.trajectory(1), -1),
    ]
    pipeline = RolloutBatchPipeline(trajectories, 1, torch.device("cpu"))

    first = pipeline.prepare(0, trajectories[:1])
    first_batch = pipeline.upload(first)
    first_pointer = first_batch.board.data_ptr()
    pipeline.finish(first)
    pipeline.prepare(1, trajectories[1:])
    reused = pipeline.prepare(0, trajectories[1:])
    reused_batch = pipeline.upload(reused)

    assert reused_batch.board.data_ptr() == first_pointer
    assert reused_batch.board[0, 0, 0, 0, 0, 0].item() == 2.0
    assert reused_batch.actions[0, 0, 1].item() == -1
