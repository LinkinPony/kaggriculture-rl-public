"""Shared actor encoder and conditional-program terminal-WDL critic."""

from __future__ import annotations

from dataclasses import dataclass, replace

import torch
from torch import Tensor, nn

from kagg_revue.policy.model import TurnPolicyNet
from kagg_revue.policy.programs.grammar import (
    ProgramActionSequence,
    ProgramMaskSequence,
    ProgramSequenceInputs,
)
from kagg_revue.policy.programs.model import ConditionalProgramPolicy
from kagg_revue.policy.programs.schema import ProgramSequenceOutput


@dataclass(frozen=True)
class ProgramEvaluation:
    """One full-turn structured policy and direct outcome evaluation."""

    programs: ProgramSequenceOutput


class ProgramActorCritic(nn.Module):
    """Attach the conditional language to one verified causal actor encoder."""

    def __init__(
        self,
        actor: TurnPolicyNet,
        programs: ConditionalProgramPolicy,
    ) -> None:
        """Validate shared dimensions before binding trainable modules."""
        super().__init__()
        actor_architecture = actor.architecture
        program_architecture = programs.architecture
        if actor_architecture.model_width != program_architecture.context_width:
            raise ValueError("program context width differs from the actor history token")
        if actor_architecture.board_shape[-1] != program_architecture.board_size:
            raise ValueError("program pointer and actor board dimensions differ")
        if actor_architecture.unit_shape[1] != program_architecture.unit_limit:
            raise ValueError("program compiler and actor unit capacities differ")
        if actor_architecture.max_decisions < (
            program_architecture.unit_limit
            + program_architecture.maximum_market_orders
        ):
            raise ValueError("actor action history cannot hold a complete program")
        if actor_architecture.skill_tokens:
            raise ValueError("conditional program requires deterministic turn context")
        self.actor = actor
        self.programs = programs

    def forward(
        self,
        board: Tensor,
        units: Tensor,
        global_features: Tensor,
        actions: Tensor,
        quantities: Tensor,
        turn_mask: Tensor,
        decision_mask: Tensor,
        program_inputs: ProgramSequenceInputs,
        program_actions: ProgramActionSequence,
        program_masks: ProgramMaskSequence,
        program_episode_index: Tensor,
        program_turn_index: Tensor,
        turn_facts: Tensor | None = None,
        turn_fact_mask: Tensor | None = None,
        economic_state: Tensor | None = None,
        *,
        validate_inputs: bool = True,
    ) -> ProgramEvaluation:
        """Recompute causal contexts and one joint ratio per official turn."""
        encoding = self.actor.encode_sequence(
            board,
            units,
            global_features,
            actions,
            quantities,
            turn_mask,
            decision_mask,
            turn_facts,
            turn_fact_mask,
            economic_state,
            compute_strategy=False,
        )
        episodes, turns = encoding.history.shape[:2]
        if (
            program_episode_index.shape != program_turn_index.shape
            or program_episode_index.ndim != 1
            or program_episode_index.shape[0] != program_inputs.batch_size
        ):
            raise ValueError("program-to-turn indices must be aligned vectors")
        episode_indices = program_episode_index.long()
        turn_indices = program_turn_index.long()
        if validate_inputs and (
            bool(torch.any((episode_indices < 0) | (episode_indices >= episodes)))
            or bool(torch.any((turn_indices < 0) | (turn_indices >= turns)))
        ):
            raise ValueError("program sequence refers outside the actor batch")
        memory = encoding.memory.reshape(
            episodes, turns, encoding.memory.shape[1], encoding.memory.shape[2]
        )
        tile_start = 1 + self.actor.architecture.latent_tokens
        tile_stop = tile_start + self.programs.architecture.tile_count
        if memory.shape[2] < tile_stop:
            raise ValueError("actor memory lost the full own-board tile surface")
        contexts = encoding.history[episode_indices, turn_indices]
        tiles = memory[
            episode_indices,
            turn_indices,
            tile_start:tile_stop,
        ]
        current_inputs = replace(
            program_inputs,
            context=contexts,
            tile_tokens=tiles,
        )
        return ProgramEvaluation(
            programs=self.programs.evaluate_sequence(
                current_inputs,
                program_actions,
                program_masks,
                validate=validate_inputs,
            )
        )


__all__ = ["ProgramActorCritic", "ProgramEvaluation"]
