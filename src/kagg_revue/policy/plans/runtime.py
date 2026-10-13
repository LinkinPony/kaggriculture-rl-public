"""Stateful inference and teacher-forced entry points for plan policies."""

from __future__ import annotations

from typing import cast

import torch
from torch import Tensor

from kagg_revue.policy.plans.backbone import (
    PlanBackboneEncoding,
    PlanTemporalState,
    StructuredPlanBackbone,
)
from kagg_revue.policy.plans.grammar import (
    PlanActions,
    PlanConditionalMasks,
    PlanInputs,
)
from kagg_revue.policy.plans.schema import (
    StructuredPlanArchitecture,
    StructuredPlanBehaviorOutput,
    StructuredPlanPolicyOutput,
)


class StructuredPlanRuntimeMixin:
    """Expose full learner outputs and an execution-only opponent path."""

    architecture: StructuredPlanArchitecture
    backbone: StructuredPlanBackbone

    def _decode(
        self,
        inputs: PlanInputs,
        actions: PlanActions | None,
        masks: PlanConditionalMasks | None,
        *,
        sample: bool,
        generator: torch.Generator | None,
        validate: bool,
        validate_inputs: bool,
        statistics: bool = True,
        behavior_only: bool = False,
        episode_index: Tensor | None = None,
        encoding: PlanBackboneEncoding | None = None,
    ) -> StructuredPlanPolicyOutput | StructuredPlanBehaviorOutput | PlanActions:
        raise NotImplementedError

    def _validate_runtime_inputs(
        self,
        inputs: PlanInputs,
        *,
        validate_values: bool,
    ) -> None:
        architecture = self.architecture
        inputs.validate(
            observation_features=architecture.observation_features,
            journal_features=architecture.journal_features,
            event_features=architecture.event_features,
            production_lines=architecture.production_lines,
            line_fields=architecture.line_fields,
            global_fields=architecture.global_fields,
            board_shape=architecture.board_shape,
            unit_shape=architecture.unit_shape,
            global_features=architecture.rich_global_features,
            economic_state_features=architecture.economic_state_features,
            validate_values=validate_values,
        )

    def rollout(
        self,
        inputs: PlanInputs,
        *,
        sample: bool,
        generator: torch.Generator | None = None,
        validate_inputs: bool = True,
    ) -> StructuredPlanPolicyOutput:
        """Sample or greedily decode one on-policy portfolio action."""
        return cast(
            StructuredPlanPolicyOutput,
            self._decode(
                inputs,
                None,
                None,
                sample=sample,
                generator=generator,
                validate=False,
                validate_inputs=validate_inputs,
            ),
        )

    def rollout_advance(
        self,
        inputs: PlanInputs,
        state: PlanTemporalState | None,
        *,
        sample: bool,
        generator: torch.Generator | None = None,
        validate_inputs: bool = True,
    ) -> tuple[StructuredPlanPolicyOutput, PlanTemporalState]:
        """Advance a synchronized day anchor and decode its portfolio action."""
        self._validate_runtime_inputs(inputs, validate_values=validate_inputs)
        scene = self.backbone.encode_scene(inputs)
        encoding, next_state = self.backbone.advance(scene, state)
        output = cast(
            StructuredPlanPolicyOutput,
            self._decode(
                inputs,
                None,
                None,
                sample=sample,
                generator=generator,
                validate=False,
                validate_inputs=False,
                encoding=encoding,
            ),
        )
        return output, next_state

    def sample_actions_advance(
        self,
        inputs: PlanInputs,
        state: PlanTemporalState | None,
        *,
        generator: torch.Generator,
        validate_inputs: bool = True,
    ) -> tuple[PlanActions, PlanTemporalState]:
        """Advance a day anchor without unused learner statistics."""
        self._validate_runtime_inputs(inputs, validate_values=validate_inputs)
        scene = self.backbone.encode_scene(inputs)
        encoding, next_state = self.backbone.advance(scene, state)
        actions = cast(
            PlanActions,
            self._decode(
                inputs,
                None,
                None,
                sample=True,
                generator=generator,
                validate=False,
                validate_inputs=False,
                statistics=False,
                encoding=encoding,
            ),
        )
        return actions, next_state

    def rollout_behavior_advance(
        self,
        inputs: PlanInputs,
        state: PlanTemporalState | None,
        *,
        generator: torch.Generator,
        validate_inputs: bool = True,
    ) -> tuple[StructuredPlanBehaviorOutput, PlanTemporalState]:
        """Advance a day anchor and retain only persisted PPO behavior fields."""
        self._validate_runtime_inputs(inputs, validate_values=validate_inputs)
        scene = self.backbone.encode_scene(inputs)
        encoding, next_state = self.backbone.advance(scene, state)
        output = cast(
            StructuredPlanBehaviorOutput,
            self._decode(
                inputs,
                None,
                None,
                sample=True,
                generator=generator,
                validate=False,
                validate_inputs=False,
                behavior_only=True,
                encoding=encoding,
            ),
        )
        return output, next_state

    def rollout_event(
        self,
        inputs: PlanInputs,
        history: Tensor,
        strategy: Tensor | None,
        *,
        sample: bool,
        generator: torch.Generator | None = None,
        validate_inputs: bool = True,
    ) -> StructuredPlanPolicyOutput:
        """Decode an intra-day event without advancing long-term memory."""
        self._validate_runtime_inputs(inputs, validate_values=validate_inputs)
        scene = self.backbone.encode_scene(inputs)
        encoding = self.backbone.condition(scene, history, strategy)
        return cast(
            StructuredPlanPolicyOutput,
            self._decode(
                inputs,
                None,
                None,
                sample=sample,
                generator=generator,
                validate=False,
                validate_inputs=False,
                encoding=encoding,
            ),
        )

    def sample_actions_event(
        self,
        inputs: PlanInputs,
        history: Tensor,
        strategy: Tensor | None,
        *,
        generator: torch.Generator,
        validate_inputs: bool = True,
    ) -> PlanActions:
        """Sample an event action without unused learner statistics."""
        self._validate_runtime_inputs(inputs, validate_values=validate_inputs)
        scene = self.backbone.encode_scene(inputs)
        encoding = self.backbone.condition(scene, history, strategy)
        return cast(
            PlanActions,
            self._decode(
                inputs,
                None,
                None,
                sample=True,
                generator=generator,
                validate=False,
                validate_inputs=False,
                statistics=False,
                encoding=encoding,
            ),
        )

    def rollout_behavior_event(
        self,
        inputs: PlanInputs,
        history: Tensor,
        strategy: Tensor | None,
        *,
        generator: torch.Generator,
        validate_inputs: bool = True,
    ) -> StructuredPlanBehaviorOutput:
        """Decode an event and retain only persisted PPO behavior fields."""
        self._validate_runtime_inputs(inputs, validate_values=validate_inputs)
        scene = self.backbone.encode_scene(inputs)
        encoding = self.backbone.condition(scene, history, strategy)
        return cast(
            StructuredPlanBehaviorOutput,
            self._decode(
                inputs,
                None,
                None,
                sample=True,
                generator=generator,
                validate=False,
                validate_inputs=False,
                behavior_only=True,
                encoding=encoding,
            ),
        )

    def evaluate_actions(
        self,
        inputs: PlanInputs,
        actions: PlanActions,
        masks: PlanConditionalMasks,
        *,
        episode_index: Tensor | None = None,
        validate: bool = False,
        validate_inputs: bool = True,
    ) -> StructuredPlanPolicyOutput:
        """Recompute exact joint likelihood under stored masks and prefixes."""
        return cast(
            StructuredPlanPolicyOutput,
            self._decode(
                inputs,
                actions,
                masks,
                sample=False,
                generator=None,
                validate=validate,
                validate_inputs=validate_inputs,
                episode_index=episode_index,
            ),
        )


__all__ = ["StructuredPlanRuntimeMixin"]
