"""Shared observation encoder with task units and direct market actions."""

from __future__ import annotations

from dataclasses import dataclass, replace

import torch
from torch import Tensor, nn
from torch.utils.checkpoint import checkpoint

from kagg_revue.policy.model import PolicyOutput, TurnPolicyNet
from kagg_revue.policy.tasks.grammar import (
    FactorizedTaskDecisionInputs,
    FactorizedTaskMasks,
    TaskActions,
    TaskConditionalMasks,
    TaskDecisionInputs,
)
from kagg_revue.policy.tasks.model import UnitTaskPolicy
from kagg_revue.policy.tasks.schema import TaskPolicyOutput
from kagg_revue.rl.outcome import ActorCriticOutput, OutcomeActorCritic

_TASK_TRAINING_CHUNK_ROWS = 2048


@dataclass(frozen=True)
class TaskTapeEvaluation:
    """Market-turn and task-boundary likelihoods from one encoder pass."""

    market: ActorCriticOutput
    tasks: TaskPolicyOutput


def _checkpointed_task_evaluation(
    policy: UnitTaskPolicy,
    inputs: TaskDecisionInputs | FactorizedTaskDecisionInputs,
    actions: TaskActions,
    masks: TaskConditionalMasks | FactorizedTaskMasks,
    *,
    validate: bool,
    retained_rows: int = 0,
) -> TaskPolicyOutput:
    """Bound task-row activations and recompute them during backward."""
    if retained_rows < 0:
        raise ValueError("retained task rows cannot be negative")
    chunks: list[tuple[Tensor, ...]] = []
    for start in range(0, inputs.batch_size, _TASK_TRAINING_CHUNK_ROWS):
        rows = slice(start, start + _TASK_TRAINING_CHUNK_ROWS)
        chunk_inputs = replace(
            inputs,
            **{
                name: value[rows]
                for name in inputs.__dataclass_fields__
                if name != "prefix_length"
                for value in (getattr(inputs, name),)
            },
        )
        chunk_actions = TaskActions(
            mode=actions.mode[rows],
            candidate=actions.candidate[rows],
            quantity=actions.quantity[rows],
            earliest=actions.earliest[rows],
            deadline=actions.deadline[rows],
        )
        chunk_masks = replace(
            masks,
            **{name: getattr(masks, name)[rows] for name in masks.__dataclass_fields__},
        )

        def evaluate(
            context: Tensor,
            current_inputs: TaskDecisionInputs | FactorizedTaskDecisionInputs = chunk_inputs,
            current_actions: TaskActions = chunk_actions,
            current_masks: TaskConditionalMasks | FactorizedTaskMasks = chunk_masks,
        ) -> tuple[Tensor, ...]:
            output = policy.evaluate_actions(
                replace(current_inputs, context=context),
                current_actions,
                current_masks,
                validate=validate,
                validate_inputs=validate,
            )
            return (
                output.joint_log_probability,
                output.factor_log_probability,
                output.entropy,
                output.factor_entropy,
                output.outcome_logits,
                output.value,
            )

        chunks.append(
            evaluate(chunk_inputs.context)
            if start < retained_rows
            else checkpoint(
                evaluate,
                chunk_inputs.context,
                use_reentrant=False,
                preserve_rng_state=False,
            )
        )
    values = tuple(torch.cat([chunk[index] for chunk in chunks]) for index in range(6))
    return TaskPolicyOutput(
        actions=actions,
        masks=masks,
        joint_log_probability=values[0],
        factor_log_probability=values[1],
        entropy=values[2],
        factor_entropy=values[3],
        outcome_logits=values[4],
        value=values[5],
    )


class TaskTapeActorCritic(nn.Module):
    """Terminal-WDL actor-critic retaining the official market action ABI."""

    def __init__(
        self,
        actor: TurnPolicyNet,
        task_policy: UnitTaskPolicy,
    ) -> None:
        """Attach a task head and market critic to one verified actor encoder."""
        super().__init__()
        if task_policy.architecture.context_width != actor.architecture.model_width:
            raise ValueError("task context width differs from the actor history token")
        if task_policy.architecture.unit_limit != actor.architecture.unit_shape[1]:
            raise ValueError("task and observation encoders use different unit capacities")
        if task_policy.architecture.maximum_quantity != actor.architecture.maximum_quantity:
            raise ValueError("task and market quantity vocabularies differ")
        self.market = OutcomeActorCritic(actor)
        self.tasks = task_policy

    @property
    def actor(self) -> TurnPolicyNet:
        """Return the shared verified turn actor."""
        return self.market.actor

    def forward(
        self,
        board: Tensor,
        units: Tensor,
        global_features: Tensor,
        actions: Tensor,
        quantities: Tensor,
        phases: Tensor,
        turn_mask: Tensor,
        decision_mask: Tensor,
        skill_ids: Tensor,
        task_inputs: TaskDecisionInputs | FactorizedTaskDecisionInputs,
        task_actions: TaskActions,
        task_masks: TaskConditionalMasks | FactorizedTaskMasks,
        task_episode_index: Tensor,
        task_turn_index: Tensor,
        turn_facts: Tensor | None = None,
        turn_fact_mask: Tensor | None = None,
        prefix_facts: Tensor | None = None,
        candidate_facts: Tensor | None = None,
        economic_state: Tensor | None = None,
        *,
        validate_inputs: bool = True,
        policy_grad: bool = True,
        compute_market_outcome: bool = True,
        checkpoint_task_evaluation: bool = True,
        retained_task_rows: int = 0,
    ) -> TaskTapeEvaluation:
        """Recompute all policy factors from stored causal observations."""
        actor = self.actor
        architecture = actor.architecture
        encoding = actor.encode_sequence(
            board,
            units,
            global_features,
            actions,
            quantities,
            turn_mask,
            decision_mask,
            turn_facts if architecture.turn_fact_features else None,
            turn_fact_mask if architecture.turn_fact_features else None,
            economic_state if architecture.economic_feature_version else None,
        )
        skills = actor.select_sequence_skills(
            encoding,
            turn_mask,
            skill_ids=skill_ids,
            sample=False,
            validate_ids=validate_inputs,
        )
        market_policy: PolicyOutput = actor.decode_sequence(
            encoding,
            actions,
            quantities,
            phases,
            decision_mask,
            prefix_facts if architecture.prefix_fact_features else None,
            candidate_facts if architecture.candidate_fact_features else None,
            skills,
            economic_state if architecture.economic_feature_version else None,
        )
        batch, turns = encoding.history.shape[:2]
        scene_memory = encoding.memory[:, 1:].reshape(batch, turns, -1, architecture.model_width)
        scene_memory_mask = encoding.memory_mask[:, 1:].reshape(batch, turns, -1)
        market_logits = (
            self.market.outcome(
                encoding.history,
                global_features,
                scene_memory,
                scene_memory_mask,
                encoding.economic_features,
                encoding.strategy,
            )
            if compute_market_outcome
            else encoding.history.new_zeros((batch, turns, 3))
        )

        if task_episode_index.shape != task_turn_index.shape or task_episode_index.ndim != 1:
            raise ValueError("task-to-turn indices must be aligned vectors")
        episode_indices = task_episode_index.long()
        turn_indices = task_turn_index.long()
        if validate_inputs and (
            bool(torch.any((episode_indices < 0) | (episode_indices >= batch)))
            or bool(torch.any((turn_indices < 0) | (turn_indices >= turns)))
        ):
            raise ValueError("task decision refers to a turn outside the market batch")
        contexts = encoding.history[episode_indices, turn_indices]
        current_task_inputs = replace(task_inputs, context=contexts)
        task_output = (
            _checkpointed_task_evaluation(
                self.tasks,
                current_task_inputs,
                task_actions,
                task_masks,
                validate=validate_inputs,
                retained_rows=retained_task_rows,
            )
            if (self.training and torch.is_grad_enabled() and checkpoint_task_evaluation)
            else self.tasks.evaluate_actions(
                current_task_inputs,
                task_actions,
                task_masks,
                validate=validate_inputs,
                validate_inputs=validate_inputs,
            )
        )
        market_policy = replace(
            market_policy,
            action_logits=(
                market_policy.action_logits if policy_grad else market_policy.action_logits.detach()
            ),
            quantity_logits=(
                market_policy.quantity_logits
                if policy_grad
                else market_policy.quantity_logits.detach()
            ),
            skills=None,
            hidden=None,
        )
        if not policy_grad:
            task_output = replace(
                task_output,
                joint_log_probability=task_output.joint_log_probability.detach(),
                factor_log_probability=task_output.factor_log_probability.detach(),
                entropy=task_output.entropy.detach(),
                factor_entropy=task_output.factor_entropy.detach(),
            )
        return TaskTapeEvaluation(
            market=ActorCriticOutput(
                policy=market_policy,
                outcome_logits=market_logits,
            ),
            tasks=task_output,
        )


__all__ = ["TaskTapeActorCritic", "TaskTapeEvaluation"]
