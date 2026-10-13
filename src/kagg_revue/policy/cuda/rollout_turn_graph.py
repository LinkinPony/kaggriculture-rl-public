"""CUDA Graph joining scene, history, and a complete rollout turn."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass

import torch
from torch import Tensor

from kagg_revue.policy.cuda.capture import serialized_graph_capture
from kagg_revue.policy.cuda.history import CudaStaticHistory
from kagg_revue.policy.cuda.policy_turn_graph import _PolicyTurnProgram
from kagg_revue.policy.cuda.session import GpuPolicyStateLayout
from kagg_revue.policy.model import ActionState, TurnContext, TurnPolicyNet
from kagg_revue.policy.skills import SkillStep


@dataclass(frozen=True)
class CudaRolloutTurnInputs:
    """Stable-address tensors updated before each episode-graph replay."""

    board: Tensor
    units: Tensor
    global_features: Tensor
    previous_actions: Tensor
    previous_quantities: Tensor
    previous_mask: Tensor
    policy_state: Tensor
    action_head_noise: Tensor | None = None

    def tensors(self) -> tuple[Tensor, ...]:
        """Return fields in a stable order for pointer validation."""
        required = (
            self.board,
            self.units,
            self.global_features,
            self.previous_actions,
            self.previous_quantities,
            self.previous_mask,
            self.policy_state,
        )
        return required + (() if self.action_head_noise is None else (self.action_head_noise,))


class CudaRolloutTurnGraph:
    """Capture visible-state encoding and the stateful action turn together."""

    def __init__(
        self,
        actor: TurnPolicyNet,
        inputs: CudaRolloutTurnInputs,
        layout: GpuPolicyStateLayout,
        has_quantity: Tensor,
        generator: torch.Generator,
        *,
        behavior_value: Callable[
            [Tensor, Tensor, Tensor, Tensor, Tensor | None, Tensor | None], Tensor
        ]
        | None = None,
    ) -> None:
        """Warm and capture one fixed-batch episode program."""
        tensors = inputs.tensors()
        device = inputs.board.device
        if device.type != "cuda" or any(tensor.device != device for tensor in tensors):
            raise ValueError("rollout-turn CUDA Graph inputs must share one CUDA device")
        batch = inputs.board.shape[0]
        if any(tensor.shape[0] != batch for tensor in tensors):
            raise ValueError("rollout-turn CUDA Graph inputs have different batches")
        if inputs.policy_state.dtype not in {torch.int32, torch.int64}:
            raise ValueError("rollout-turn policy state must use int32 or int64")
        if inputs.action_head_noise is not None and inputs.action_head_noise.shape != (
            batch,
            actor.architecture.action_tokens,
            actor.architecture.model_width,
        ):
            raise ValueError("rollout-turn action-head noise differs from the actor architecture")
        self._actor = actor
        self._behavior_value = behavior_value
        self._inputs = inputs
        self._input_pointers = tuple(tensor.data_ptr() for tensor in tensors)
        self._device = device
        self._maximum_replays = actor.architecture.max_history
        self._replays = 0
        history_dtype = (
            torch.get_autocast_dtype("cuda")
            if torch.is_autocast_enabled("cuda")
            else next(actor.parameters()).dtype
        )
        self._history = CudaStaticHistory(actor, batch, history_dtype)
        self._skill_uniform = (
            torch.empty(
                (batch, actor.architecture.skill_tokens),
                dtype=torch.float32,
                device=device,
            )
            if actor.skills is not None
            else None
        )
        self._skill: SkillStep | None = None
        self._program = _PolicyTurnProgram(
            actor,
            batch,
            device,
            layout,
            has_quantity,
            generator,
            track_log_probability=behavior_value is not None,
        )
        initial_policy_state = inputs.policy_state.clone()
        started = time.perf_counter()
        self._context, self._decoder_state, self._value = self._run(conditional=False)
        torch.cuda.current_stream(device).synchronize()
        self._history.reset()
        inputs.policy_state.copy_(initial_policy_state)
        torch.cuda.current_stream(device).synchronize()
        self._graph = torch.cuda.CUDAGraph()
        self._graph.register_generator_state(generator)
        with serialized_graph_capture(self._graph):
            self._context, self._decoder_state, self._value = self._run(conditional=True)
        torch.cuda.current_stream(device).synchronize()
        self._history.reset()
        inputs.policy_state.copy_(initial_policy_state)
        torch.cuda.current_stream(device).synchronize()
        self.capture_seconds = time.perf_counter() - started

    def _run(self, *, conditional: bool) -> tuple[TurnContext, ActionState, Tensor | None]:
        economic_features = (
            None
            if self._actor.economics is None
            else self._actor.economics.turn_features(
                self._inputs.policy_state,
                self._inputs.global_features,
            )
        )
        scene = self._actor.scene(
            self._inputs.board,
            self._inputs.units,
            self._inputs.global_features,
            self._inputs.previous_actions,
            self._inputs.previous_quantities,
            self._inputs.previous_mask,
            economic_features=economic_features,
        )
        skill_uniform: Tensor | None = None
        if self._skill_uniform is not None:
            skill_uniform = torch.rand(
                self._skill_uniform.shape,
                dtype=torch.float32,
                device=self._device,
                generator=self._program.generator,
                out=self._skill_uniform,
            )
        context, self._skill = self._history.start_turn(scene, skill_uniform)
        value = (
            None
            if self._behavior_value is None
            else self._behavior_value(
                context.memory[:, 0],
                self._inputs.global_features,
                scene.memory,
                scene.memory_mask,
                economic_features,
                context.strategy,
            )
        )
        decoder_state = self._program.run(
            context,
            self._inputs.policy_state,
            conditional=conditional,
            action_head_noise=self._inputs.action_head_noise,
        )
        return context, decoder_state, value

    def start_turn(self, inputs: CudaRolloutTurnInputs) -> None:
        """Validate that the exchange retained every captured input address."""
        pointers = tuple(tensor.data_ptr() for tensor in inputs.tensors())
        if pointers != self._input_pointers:
            raise ValueError("rollout-turn CUDA Graph input address changed")
        if self._replays >= self._maximum_replays:
            raise RuntimeError("rollout-turn CUDA Graph exceeded history capacity")

    def replay(self) -> None:
        """Execute one complete visible-state-to-action turn."""
        self._graph.replay()
        self._replays += 1

    def reset_episode(self) -> None:
        """Reuse the captured program with an empty temporal history."""
        with torch.inference_mode():
            self._history.reset()
        self._replays = 0

    def close(self) -> None:
        """Release graph-private allocations at the runner ownership boundary."""
        self._graph.reset()
        del self._graph
        del self._context
        del self._decoder_state
        del self._value
        del self._program
        del self._history
        del self._inputs
        del self._actor
        del self._behavior_value

    @property
    def tokens(self) -> Tensor:
        """Return graph-owned selected tokens as ``[decision, batch]``."""
        return self._program.tokens

    @property
    def quantities(self) -> Tensor:
        """Return graph-owned selected quantities as ``[decision, batch]``."""
        return self._program.quantities

    @property
    def phases(self) -> Tensor:
        """Return graph-owned pre-selection phases as ``[decision, batch]``."""
        return self._program.phases

    @property
    def decisions(self) -> Tensor:
        """Return exact active prefixes as ``[decision, batch]``."""
        return self._program.decisions

    @property
    def legal(self) -> Tensor:
        """Return exact legal masks as ``[decision, batch, action]``."""
        return self._program.legal

    @property
    def log_probabilities(self) -> Tensor | None:
        """Return selected action and quantity behavior log probabilities."""
        return self._program.log_probabilities

    @property
    def value(self) -> Tensor | None:
        """Return the behavior critic value for the current visible turn."""
        return self._value

    @property
    def final_phases(self) -> Tensor:
        """Return each session phase after the graph's last transition."""
        return self._inputs.policy_state[:, 4]

    @property
    def skill_ids(self) -> Tensor | None:
        """Return graph-owned causal latent choices for the current turn."""
        return None if self._skill is None else self._skill.ids

    @property
    def skill_log_probability(self) -> Tensor | None:
        """Return behavior selector log probability for each latent choice."""
        return None if self._skill is None else self._skill.log_probability


__all__ = ["CudaRolloutTurnGraph", "CudaRolloutTurnInputs"]
