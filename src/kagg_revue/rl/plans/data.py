"""Finite in-memory rollout tensors for structured-plan SMDP-PPO."""

from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import Tensor

from kagg_revue.policy.plans import PlanActions, PlanConditionalMasks, PlanInputs
from kagg_revue.rl.plans.contract import PlanVersionContract


@dataclass(frozen=True)
class TensorPlanRolloutBatch:
    """One frozen on-policy panel with one row per event decision."""

    inputs: PlanInputs
    actions: PlanActions
    masks: PlanConditionalMasks
    old_joint_log_probability: Tensor
    old_values: Tensor
    episode_index: Tensor
    start_steps: Tensor
    durations: Tensor
    outcomes: Tensor
    contract: PlanVersionContract
    episode_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        """Validate SMDP alignment, W/D/L labels, masks, and episode coverage."""
        decisions = self.inputs.batch_size
        lines = self.inputs.production_lines
        line_fields = int(self.inputs.active_lines.shape[2])
        global_fields = int(self.inputs.global_plan.shape[1])
        self.actions.validate(decisions, lines, line_fields, global_fields)
        self.masks.validate(decisions, lines, line_fields, global_fields)
        expected = (decisions,)
        for name in (
            "old_joint_log_probability",
            "old_values",
            "episode_index",
            "start_steps",
            "durations",
        ):
            if getattr(self, name).shape != expected:
                raise ValueError(f"structured-plan rollout {name} must have shape [decisions]")
        if self.outcomes.ndim != 1 or self.outcomes.numel() < 1:
            raise ValueError("structured-plan rollout needs terminal outcomes")
        if len(self.episode_ids) != self.outcomes.numel():
            raise ValueError("structured-plan episode identities must align with outcomes")
        if len(set(self.episode_ids)) != len(self.episode_ids):
            raise ValueError("structured-plan episode identities must be unique")
        if self.episode_index.is_floating_point() or self.episode_index.dtype == torch.bool:
            raise ValueError("structured-plan episode indices must use an integer dtype")
        indices = self.episode_index.long()
        if bool(torch.any((indices < 0) | (indices >= self.outcomes.numel()))):
            raise ValueError("structured-plan decision refers to an unknown episode")
        if bool(torch.any(torch.bincount(indices, minlength=self.outcomes.numel()) == 0)):
            raise ValueError("every structured-plan episode needs a decision")
        if self.durations.is_floating_point() or self.durations.dtype == torch.bool:
            raise ValueError("structured-plan durations must use an integer dtype")
        if bool(torch.any(self.durations < 1)):
            raise ValueError("structured-plan SMDP durations must be positive")
        if self.start_steps.is_floating_point() or self.start_steps.dtype == torch.bool:
            raise ValueError("structured-plan start steps must use an integer dtype")
        if bool(torch.any(self.start_steps < 0)):
            raise ValueError("structured-plan start steps must be non-negative")
        if not torch.isfinite(self.old_joint_log_probability).all():
            raise ValueError("structured-plan behavior likelihood must be finite")
        if not torch.isfinite(self.old_values).all() or bool(
            torch.any((self.old_values < -1) | (self.old_values > 1))
        ):
            raise ValueError("structured-plan old values must lie in [-1, 1]")
        if not torch.isfinite(self.outcomes).all() or bool(
            torch.any(
                (self.outcomes < -1)
                | (self.outcomes > 1)
                | (self.outcomes != self.outcomes.round())
            )
        ):
            raise ValueError("structured-plan outcomes must be loss, tie, or win")
        if bool(torch.any(self.masks.factors.sum(dim=1) < 1)):
            raise ValueError("structured-plan decisions need a stochastic factor")

    @property
    def decisions(self) -> int:
        """Return the number of real event decisions."""
        return self.inputs.batch_size

    @property
    def episodes(self) -> int:
        """Return the number of complete official-rule games."""
        return int(self.outcomes.numel())

    def to(
        self,
        device: torch.device | str,
        *,
        non_blocking: bool = False,
    ) -> TensorPlanRolloutBatch:
        """Move the finite rollout panel to an optimizer device."""

        def move(value: Tensor) -> Tensor:
            return value.to(device, non_blocking=non_blocking)

        return TensorPlanRolloutBatch(
            inputs=PlanInputs(
                board=move(self.inputs.board),
                units=move(self.inputs.units),
                global_features=move(self.inputs.global_features),
                economic_state=move(self.inputs.economic_state),
                features=move(self.inputs.features),
                journal=move(self.inputs.journal),
                events=move(self.inputs.events),
                active_lines=move(self.inputs.active_lines),
                active_line_mask=move(self.inputs.active_line_mask),
                global_plan=move(self.inputs.global_plan),
            ),
            actions=PlanActions(
                mode=move(self.actions.mode),
                line_operations=move(self.actions.line_operations),
                line_values=move(self.actions.line_values),
                global_operation=move(self.actions.global_operation),
                global_values=move(self.actions.global_values),
            ),
            masks=self.masks.to(device, non_blocking=non_blocking),
            old_joint_log_probability=move(self.old_joint_log_probability),
            old_values=move(self.old_values),
            episode_index=move(self.episode_index),
            start_steps=move(self.start_steps),
            durations=move(self.durations),
            outcomes=move(self.outcomes),
            contract=self.contract,
            episode_ids=self.episode_ids,
        )

    def tensor_bytes(self) -> int:
        """Return exact storage bytes held by the in-memory rollout tensors."""
        tensors = (
            self.inputs.board,
            self.inputs.units,
            self.inputs.global_features,
            self.inputs.economic_state,
            self.inputs.features,
            self.inputs.journal,
            self.inputs.events,
            self.inputs.active_lines,
            self.inputs.active_line_mask,
            self.inputs.global_plan,
            self.actions.mode,
            self.actions.line_operations,
            self.actions.line_values,
            self.actions.global_operation,
            self.actions.global_values,
            self.masks.mode,
            self.masks.line_operations,
            self.masks.line_values,
            self.masks.global_operation,
            self.masks.global_values,
            self.masks.factors,
            self.old_joint_log_probability,
            self.old_values,
            self.episode_index,
            self.start_steps,
            self.durations,
            self.outcomes,
        )
        return sum(value.numel() * value.element_size() for value in tensors)


__all__ = ["TensorPlanRolloutBatch"]
