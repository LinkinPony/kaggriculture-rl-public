"""Recurrent pointer actor and W/D/L critic for atomic effects."""

from __future__ import annotations

from collections.abc import Sequence
from typing import cast

import torch
from torch import Tensor, nn
from torch.nn import functional as F

from kagg_revue.policy.effects.critic import EffectCritic
from kagg_revue.policy.effects.data import EffectTensorState
from kagg_revue.policy.effects.pointer import EffectPolicy
from kagg_revue.policy.effects.schema import (
    EffectPolicyOutput,
    EffectSequenceContext,
)
from kagg_revue.policy.model import TurnPolicyNet
from kagg_revue.policy.transformer import HistoryState


class EffectActorCritic(nn.Module):
    """Attach atomic-effect heads to a causal pretrained turn encoder."""

    def __init__(self, actor: TurnPolicyNet, effects: EffectPolicy) -> None:
        """Validate and bind the shared observation representation."""
        super().__init__()
        if actor.architecture.model_width != effects.architecture.context_width:
            raise ValueError("effect context width differs from the turn encoder")
        if actor.architecture.board_shape[-1] != effects.architecture.board_size:
            raise ValueError("effect and turn encoder board sizes differ")
        if effects.architecture.independent_critic and (
            effects.architecture.critic_representation != "entity_recurrent_v2"
        ):
            raise ValueError(
                "critic representation is unsupported; use its recorded source revision"
            )
        self.actor = actor
        self.effects = effects
        self.critic = (
            EffectCritic(actor.architecture) if effects.architecture.independent_critic else None
        )

    @staticmethod
    def _strategy_summary(strategy: Tensor | None) -> Tensor | None:
        """Reduce recurrent strategy slots without introducing a new recurrence."""
        return None if strategy is None else strategy.mean(dim=-2)

    def start_turn(
        self,
        board: Tensor,
        units: Tensor,
        global_features: Tensor,
        previous_actions: Tensor,
        previous_quantities: Tensor,
        previous_mask: Tensor,
        history: HistoryState | None,
        strategy_state: Tensor | None,
        economic_state: Tensor | None,
    ) -> tuple[Tensor, Tensor, Tensor | None, HistoryState, Tensor | None]:
        """Encode one official state exactly once for all of its factors."""
        turn, next_history, next_strategy, _skill = self.actor.start_turn(
            board,
            units,
            global_features,
            previous_actions,
            previous_quantities,
            previous_mask,
            history,
            economic_state=economic_state,
            strategy_state=strategy_state,
            sample_skill=False,
            full_precision_history=True,
        )
        tile_start = 1 + self.actor.architecture.latent_tokens
        tile_stop = tile_start + self.effects.architecture.tile_count
        return (
            turn.memory[:, 0],
            turn.memory[:, tile_start:tile_stop],
            self._strategy_summary(turn.strategy),
            next_history,
            next_strategy,
        )

    def encode_effect_sequences(
        self,
        board: Tensor,
        units: Tensor,
        global_features: Tensor,
        actions: Tensor,
        quantities: Tensor,
        turn_mask: Tensor,
        decision_mask: Tensor,
        economic_state: Tensor | None,
        *,
        value_only: bool = False,
        compute_value: bool = True,
    ) -> EffectSequenceContext:
        """Encode official turns once before evaluating flattened factors."""
        if value_only and not compute_value:
            raise ValueError("value-only replay cannot disable its value prediction")
        outcomes = (
            None
            if self.critic is None or not compute_value
            else self.critic(
                board, units, global_features, actions, quantities, turn_mask, decision_mask
            )
        )
        if self.critic is not None and not compute_value:
            # Policy-only guards must not evaluate an independent value model.
            outcomes = global_features.new_zeros((*turn_mask.shape, 3))
        if value_only and outcomes is not None:
            dummy = outcomes.new_zeros(
                (*outcomes.shape[:2], self.effects.architecture.context_width)
            )
            return EffectSequenceContext(dummy, dummy[:, :, None], None, outcomes)
        encoding = self.actor.encode_sequence(
            board,
            units,
            global_features,
            actions,
            quantities,
            turn_mask,
            decision_mask,
            economic_state=economic_state,
            compute_strategy=True,
            full_precision_history=True,
        )
        episodes, turns = encoding.history.shape[:2]
        memory = encoding.memory.view(
            episodes,
            turns,
            encoding.memory.shape[1],
            encoding.memory.shape[2],
        )
        tile_start = 1 + self.actor.architecture.latent_tokens
        tile_stop = tile_start + self.effects.architecture.tile_count
        return EffectSequenceContext(
            outcome_logits=outcomes,
            context=encoding.history,
            tile_context=memory[:, :, tile_start:tile_stop],
            strategy=(
                None if encoding.strategy is None else self._strategy_summary(encoding.strategy)
            ),
        )

    def evaluate_effect_sequence_context(
        self,
        sequence: EffectSequenceContext,
        state: EffectTensorState,
        episode_index: Tensor,
        turn_index: Tensor,
        *,
        candidate_counts: Tensor | None = None,
        candidate_states: Sequence[EffectTensorState] | None = None,
        value_only: bool = False,
        critic_actor_gradient: bool = True,
        validate: bool = True,
    ) -> EffectPolicyOutput:
        """Attach the independent once-per-turn critic to causal factor scores."""
        outcomes = sequence.outcome_logits
        if value_only and outcomes is not None:
            return EffectPolicyOutput(
                outcomes.new_zeros((episode_index.numel(), 1)),
                outcomes[episode_index.long(), turn_index.long()],
            )
        if self.effects.architecture.task_conditioning and not value_only:
            from kagg_revue.policy.effects.replay import evaluate_reused_work

            if candidate_states is None:
                candidate_states = (state,)
            outputs = []
            offset = 0
            for candidates in candidate_states:
                stop = offset + candidates.batch_size
                small = EffectTensorState(
                    **{
                        name: getattr(state, name)[offset:stop]
                        for name in EffectTensorState.__dataclass_fields__
                    }
                )
                outputs.append(
                    evaluate_reused_work(
                        self,
                        sequence,
                        small,
                        episode_index[offset:stop],
                        turn_index[offset:stop],
                        candidates,
                        validate=validate,
                        critic_actor_gradient=critic_actor_gradient,
                    )
                )
                offset = stop
            maximum = max(output.candidate_logits.shape[1] for output in outputs)
            return EffectPolicyOutput(
                torch.cat(
                    [
                        F.pad(
                            output.candidate_logits,
                            (0, maximum - output.candidate_logits.shape[1]),
                            value=-torch.inf,
                        )
                        for output in outputs
                    ]
                ),
                torch.cat([output.outcome_logits for output in outputs]),
            )
        output = self._evaluate_effect_sequence_context(
            sequence,
            state,
            episode_index,
            turn_index,
            candidate_counts=candidate_counts,
            candidate_states=candidate_states,
            value_only=value_only,
            critic_actor_gradient=critic_actor_gradient,
            validate=validate,
        )
        if outcomes is None:
            return output
        return EffectPolicyOutput(
            output.candidate_logits, outcomes[episode_index.long(), turn_index.long()]
        )

    def _evaluate_effect_sequence_context(
        self,
        sequence: EffectSequenceContext,
        state: EffectTensorState,
        episode_index: Tensor,
        turn_index: Tensor,
        *,
        candidate_counts: Tensor | None = None,
        candidate_states: Sequence[EffectTensorState] | None = None,
        value_only: bool = False,
        critic_actor_gradient: bool = True,
        validate: bool = True,
    ) -> EffectPolicyOutput:
        """Evaluate factors against one already encoded official-turn sequence."""
        episodes, turns = sequence.context.shape[:2]
        if episode_index.shape != turn_index.shape or episode_index.ndim != 1:
            raise ValueError("effect factor-to-turn indices must be aligned")
        rows = episode_index.long()
        columns = turn_index.long()
        if validate and bool(
            ((rows < 0) | (rows >= episodes) | (columns < 0) | (columns >= turns)).any()
        ):
            raise ValueError("effect factor refers outside its episode sequence")
        context = sequence.context[rows, columns]
        tiles = sequence.tile_context[rows, columns]
        strategy = None if sequence.strategy is None else sequence.strategy[rows, columns]
        if value_only:
            return self.effects.forward_value(
                context,
                state,
                strategy,
                critic_actor_gradient=critic_actor_gradient,
                validate=validate,
            )
        if candidate_counts is not None and candidate_states is not None:
            raise ValueError("effect sequence received two candidate layouts")
        if candidate_states is not None:
            return self.effects.forward_sharded(
                context,
                tiles,
                state,
                candidate_states,
                strategy,
                critic_actor_gradient=critic_actor_gradient,
                validate=validate,
            )
        if candidate_counts is not None:
            return self.effects.forward_bucketed(
                context,
                tiles,
                state,
                candidate_counts,
                strategy,
                critic_actor_gradient=critic_actor_gradient,
                validate=validate,
            )
        return cast(
            EffectPolicyOutput,
            self.effects(
                context,
                tiles,
                state,
                strategy,
                critic_actor_gradient=critic_actor_gradient,
                validate=validate,
            ),
        )

    def evaluate_sequences(
        self,
        board: Tensor,
        units: Tensor,
        global_features: Tensor,
        actions: Tensor,
        quantities: Tensor,
        turn_mask: Tensor,
        decision_mask: Tensor,
        state: EffectTensorState,
        episode_index: Tensor,
        turn_index: Tensor,
        economic_state: Tensor | None,
        *,
        candidate_counts: Tensor | None = None,
        value_only: bool = False,
        critic_actor_gradient: bool = True,
        validate: bool = True,
    ) -> EffectPolicyOutput:
        """Reconstruct causal turn context for flattened policy factors."""
        sequence = self.encode_effect_sequences(
            board,
            units,
            global_features,
            actions,
            quantities,
            turn_mask,
            decision_mask,
            economic_state,
            value_only=value_only,
        )
        return self.evaluate_effect_sequence_context(
            sequence,
            state,
            episode_index,
            turn_index,
            candidate_counts=candidate_counts,
            value_only=value_only,
            critic_actor_gradient=critic_actor_gradient,
            validate=validate,
        )


__all__ = ["EffectActorCritic"]
