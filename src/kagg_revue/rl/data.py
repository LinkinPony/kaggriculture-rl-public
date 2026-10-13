"""Bounded trajectories for complete-match actor-critic updates."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from dataclasses import dataclass, replace
from typing import Any, overload

import numpy as np
import torch
from numpy.typing import NDArray
from torch import Tensor

from kagg_revue.rl.rollout.packing import PackedBoolArray


@dataclass(frozen=True)
class TurnRecord:
    """One sampled official turn and its frozen-policy probabilities."""

    board: NDArray[np.float16]
    units: NDArray[np.float16]
    global_features: NDArray[np.float32]
    economic_state: NDArray[np.int32] | NDArray[np.int64]
    turn_facts: NDArray[np.float16]
    prefix_facts: NDArray[np.float16]
    candidate_facts: NDArray[np.float16]
    legal_mask: NDArray[np.bool_]
    actions: NDArray[np.integer[Any]]
    quantities: NDArray[np.integer[Any]]
    phases: NDArray[np.integer[Any]]
    decision_mask: NDArray[np.bool_]
    old_log_probability: NDArray[np.float32]
    skill_id: int
    old_skill_log_probability: float
    old_value: float


@dataclass(frozen=True)
class TrajectoryTurns(Sequence[TurnRecord]):
    """One episode exposed as field-major array views.

    The sequence interface preserves the small diagnostic/debug boundary while
    minibatch construction can copy complete episode fields without creating a
    Python object for every turn.
    """

    board: NDArray[np.float16]
    units: NDArray[np.float16]
    global_features: NDArray[np.float32]
    economic_state: NDArray[np.int32] | NDArray[np.int64]
    turn_facts: NDArray[np.float16]
    turn_fact_mask: NDArray[np.bool_]
    prefix_facts: NDArray[np.float16]
    candidate_facts: NDArray[np.float16]
    legal_mask: NDArray[np.bool_] | PackedBoolArray
    actions: NDArray[np.integer[Any]]
    quantities: NDArray[np.integer[Any]]
    phases: NDArray[np.integer[Any]]
    decision_mask: NDArray[np.bool_]
    old_log_probability: NDArray[np.float32]
    skill_ids: NDArray[np.int64]
    old_skill_log_probability: NDArray[np.float32]
    old_values: NDArray[np.float32]

    def __post_init__(self) -> None:
        """Validate the array ABI once, before hot-path minibatch reuse."""
        turns = self.board.shape[0]
        if turns < 1 or self.actions.ndim != 2:
            raise ValueError("stored rollout needs at least one turn")
        decisions = self.actions.shape[1]
        if decisions < 1 or self.legal_mask.ndim != 3:
            raise ValueError("stored rollout needs at least one decision slot")
        action_tokens = self.legal_mask.shape[2]
        expected = {
            "units": self.units.shape[:1],
            "global_features": self.global_features.shape[:1],
            "economic_state": self.economic_state.shape[:1],
            "turn_facts": self.turn_facts.shape[:1],
            "turn_fact_mask": self.turn_fact_mask.shape[:1],
            "prefix_facts": self.prefix_facts.shape[:1],
            "candidate_facts": self.candidate_facts.shape[:1],
            "legal_mask": self.legal_mask.shape[:1],
            "quantities": self.quantities.shape[:1],
            "phases": self.phases.shape[:1],
            "decision_mask": self.decision_mask.shape[:1],
            "old_log_probability": self.old_log_probability.shape[:1],
            "skill_ids": self.skill_ids.shape[:1],
            "old_skill_log_probability": self.old_skill_log_probability.shape[:1],
            "old_values": self.old_values.shape[:1],
        }
        if any(shape != (turns,) for shape in expected.values()):
            name = next(name for name, shape in expected.items() if shape != (turns,))
            raise ValueError(f"stored rollout {name} has a different turn count")
        decision_shape = (turns, decisions)
        if (
            self.quantities.shape != decision_shape
            or self.phases.shape != decision_shape
            or self.decision_mask.shape != decision_shape
            or self.old_log_probability.shape != decision_shape
            or self.legal_mask.shape != (turns, decisions, action_tokens)
            or self.prefix_facts.shape[:2] != decision_shape
            or self.candidate_facts.shape[:3] != (turns, decisions, action_tokens)
        ):
            raise ValueError("stored rollout decision tensors are not aligned")
        if self.turn_facts.shape[:2] != self.turn_fact_mask.shape:
            raise ValueError("stored rollout fact tensors are not aligned")
        if (
            self.skill_ids.shape != (turns,)
            or self.old_skill_log_probability.shape != (turns,)
            or self.old_values.shape != (turns,)
        ):
            raise ValueError("stored rollout turn statistics are not aligned")
        if not self.decision_mask.any(axis=1).all():
            raise ValueError("stored rollout contains an empty action")
        invalid_policy = self.decision_mask & ~np.isfinite(self.old_log_probability)
        if invalid_policy.any():
            turn, decision = np.argwhere(invalid_policy)[0]
            value = self.old_log_probability[turn, decision]
            raise ValueError(
                "stored rollout policy statistic is invalid at "
                f"turn={turn}, decision={decision}: {value}"
            )
        invalid_value = np.flatnonzero(~np.isfinite(self.old_values))
        if invalid_value.size:
            turn = int(invalid_value[0])
            raise ValueError(
                f"stored rollout value statistic is invalid at turn={turn}: {self.old_values[turn]}"
            )
        invalid_skill = np.flatnonzero(~np.isfinite(self.old_skill_log_probability))
        if invalid_skill.size:
            turn = int(invalid_skill[0])
            raise ValueError(
                "stored rollout skill statistic is invalid at "
                f"turn={turn}: {self.old_skill_log_probability[turn]}"
            )
        for value in self.arrays():
            value.flags.writeable = False

    def arrays(self) -> tuple[NDArray[np.generic], ...]:
        """Return every backing field in ABI order."""
        return (
            self.board,
            self.units,
            self.global_features,
            self.economic_state,
            self.turn_facts,
            self.turn_fact_mask,
            self.prefix_facts,
            self.candidate_facts,
            (
                self.legal_mask.data
                if isinstance(self.legal_mask, PackedBoolArray)
                else self.legal_mask
            ),
            self.actions,
            self.quantities,
            self.phases,
            self.decision_mask,
            self.old_log_probability,
            self.skill_ids,
            self.old_skill_log_probability,
            self.old_values,
        )

    def __len__(self) -> int:
        """Return the number of complete official turns."""
        return int(self.board.shape[0])

    @overload
    def __getitem__(self, index: int) -> TurnRecord: ...

    @overload
    def __getitem__(self, index: slice) -> tuple[TurnRecord, ...]: ...

    def __getitem__(self, index: int | slice) -> TurnRecord | tuple[TurnRecord, ...]:
        """Materialize only a requested diagnostic turn as array views."""
        if isinstance(index, slice):
            return tuple(self[item] for item in range(*index.indices(len(self))))
        normalized = index + len(self) if index < 0 else index
        if normalized < 0 or normalized >= len(self):
            raise IndexError("trajectory turn index is out of range")
        decisions = int(self.decision_mask[normalized].sum())
        facts = int(self.turn_fact_mask[normalized].sum())
        return TurnRecord(
            board=self.board[normalized],
            units=self.units[normalized],
            global_features=self.global_features[normalized],
            economic_state=self.economic_state[normalized],
            turn_facts=self.turn_facts[normalized, :facts],
            prefix_facts=self.prefix_facts[normalized, :decisions],
            candidate_facts=self.candidate_facts[normalized, :decisions],
            legal_mask=self.legal_mask[normalized, :decisions],
            actions=self.actions[normalized, :decisions],
            quantities=self.quantities[normalized, :decisions],
            phases=self.phases[normalized, :decisions],
            decision_mask=self.decision_mask[normalized, :decisions],
            old_log_probability=self.old_log_probability[normalized, :decisions],
            skill_id=int(self.skill_ids[normalized]),
            old_skill_log_probability=float(self.old_skill_log_probability[normalized]),
            old_value=float(self.old_values[normalized]),
        )

    def __iter__(self) -> Iterator[TurnRecord]:
        """Yield diagnostic views without retaining per-turn objects."""
        for index in range(len(self)):
            yield self[index]

    @property
    def decisions(self) -> int:
        """Return the number of valid autoregressive factors."""
        return int(np.count_nonzero(self.decision_mask))

    def with_behavior(
        self,
        log_probability: NDArray[np.float32],
        skill_log_probability: NDArray[np.float32],
        values: NDArray[np.float32],
    ) -> TrajectoryTurns:
        """Return a shared-observation view with replaced behavior statistics."""
        if (
            log_probability.shape != self.old_log_probability.shape
            or skill_log_probability.shape != self.old_skill_log_probability.shape
            or values.shape != self.old_values.shape
        ):
            raise ValueError("replacement behavior statistics have the wrong shape")
        return replace(
            self,
            old_log_probability=np.asarray(log_probability, dtype=np.float32).copy(),
            old_skill_log_probability=np.asarray(skill_log_probability, dtype=np.float32).copy(),
            old_values=np.asarray(values, dtype=np.float32).copy(),
        )


@dataclass(frozen=True)
class RolloutMatch:
    """One completed official-rule match before any training-perspective expansion."""

    match_id: str
    opponent_id: str
    seed: int
    candidate_seat: int
    outcome: int
    terminal_cash: float
    opponent_cash: float


@dataclass(frozen=True)
class Trajectory:
    """One seat-relative complete match retained until its PPO update."""

    episode_id: str
    opponent_id: str
    seed: int
    seat: int
    turns: Sequence[TurnRecord]
    outcome: int
    terminal_cash: float
    opponent_cash: float
    opening_residual: NDArray[np.float32] | None = None
    opening_residual_seed: int = -1
    opening_residual_direction: int = -1
    opening_residual_scale: float = 0.0
    opening_residual_turns: int = 0


@dataclass(frozen=True)
class TensorRolloutBatch:
    """Padded full episodes ready for exact causal sequence evaluation."""

    board: Tensor
    units: Tensor
    global_features: Tensor
    economic_state: Tensor
    turn_facts: Tensor
    turn_fact_mask: Tensor
    prefix_facts: Tensor
    candidate_facts: Tensor
    legal_mask: Tensor
    actions: Tensor
    quantities: Tensor
    phases: Tensor
    turn_mask: Tensor
    decision_mask: Tensor
    old_log_probability: Tensor
    skill_ids: Tensor
    old_skill_log_probability: Tensor
    old_values: Tensor
    opening_residual: Tensor
    opening_residual_turns: Tensor
    outcomes: Tensor
    cash_differences: Tensor

    def tensors(self) -> tuple[Tensor, ...]:
        """Return fields in stable transfer order."""
        return tuple(getattr(self, name) for name in self.__dataclass_fields__)

    def view(
        self,
        batch: int,
        turns: int,
        decisions: int,
        facts: int,
    ) -> TensorRolloutBatch:
        """Narrow one reusable allocation to the current minibatch layout."""
        return TensorRolloutBatch(
            board=self.board[:batch, :turns],
            units=self.units[:batch, :turns],
            global_features=self.global_features[:batch, :turns],
            economic_state=self.economic_state[:batch, :turns],
            turn_facts=self.turn_facts[:batch, :turns, :facts],
            turn_fact_mask=self.turn_fact_mask[:batch, :turns, :facts],
            prefix_facts=self.prefix_facts[:batch, :turns, :decisions],
            candidate_facts=self.candidate_facts[:batch, :turns, :decisions],
            legal_mask=self.legal_mask[:batch, :turns, :decisions],
            actions=self.actions[:batch, :turns, :decisions],
            quantities=self.quantities[:batch, :turns, :decisions],
            phases=self.phases[:batch, :turns, :decisions],
            turn_mask=self.turn_mask[:batch, :turns],
            decision_mask=self.decision_mask[:batch, :turns, :decisions],
            old_log_probability=self.old_log_probability[:batch, :turns, :decisions],
            skill_ids=self.skill_ids[:batch, :turns],
            old_skill_log_probability=self.old_skill_log_probability[:batch, :turns],
            old_values=self.old_values[:batch, :turns],
            opening_residual=self.opening_residual[:batch],
            opening_residual_turns=self.opening_residual_turns[:batch],
            outcomes=self.outcomes[:batch],
            cash_differences=self.cash_differences[:batch],
        )


def trajectory_old_values(trajectory: Trajectory) -> NDArray[np.float64]:
    """Return critic values without materializing contiguous turn records."""
    if isinstance(trajectory.turns, TrajectoryTurns):
        return trajectory.turns.old_values.astype(np.float64, copy=False)
    return np.fromiter(
        (turn.old_value for turn in trajectory.turns),
        dtype=np.float64,
        count=len(trajectory.turns),
    )


def trajectory_decisions(trajectory: Trajectory) -> int:
    """Count valid decisions without materializing contiguous turn records."""
    if isinstance(trajectory.turns, TrajectoryTurns):
        return trajectory.turns.decisions
    return sum(int(turn.decision_mask.sum()) for turn in trajectory.turns)


def opening_residual_inputs(
    batch: TensorRolloutBatch,
) -> tuple[Tensor | None, Tensor | None]:
    """Return compact residual weights and their exact active-turn mask."""
    residual = batch.opening_residual
    turns = batch.opening_residual_turns
    if residual.ndim != 3 or residual.shape[0] != batch.outcomes.shape[0]:
        raise ValueError("opening residual batch has an invalid shape")
    if turns.shape != batch.outcomes.shape:
        raise ValueError("opening residual horizons do not align with trajectories")
    if residual.numel() == 0:
        if bool(torch.any(turns != 0)):
            raise ValueError("opening residual horizons exist without residual weights")
        return None, None
    maximum_turns = batch.turn_mask.shape[1]
    if bool(torch.any((turns < 0) | (turns > maximum_turns))):
        raise ValueError("opening residual horizon lies outside the trajectory batch")
    indices = torch.arange(maximum_turns, device=turns.device)
    mask = (indices[None] < turns[:, None]) & batch.turn_mask
    return residual, mask


def collate_trajectories(
    trajectories: list[Trajectory], device: torch.device
) -> TensorRolloutBatch:
    """Compatibility entry point for one-off trajectory collation."""
    from kagg_revue.rl.minibatch import collate_trajectories as collate

    return collate(trajectories, device)


def move_rollout_batch(
    batch: TensorRolloutBatch,
    device: torch.device,
) -> TensorRolloutBatch:
    """Compatibility entry point for one-off device transfer."""
    from kagg_revue.rl.minibatch import move_rollout_batch as move

    return move(batch, device)


__all__ = [
    "RolloutMatch",
    "TensorRolloutBatch",
    "Trajectory",
    "TrajectoryTurns",
    "TurnRecord",
    "collate_trajectories",
    "move_rollout_batch",
    "opening_residual_inputs",
    "trajectory_decisions",
    "trajectory_old_values",
]
