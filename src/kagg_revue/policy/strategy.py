"""Episode-local persistent strategy memory."""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

import torch
from torch import Tensor, nn

from kagg_revue.policy.transformer import CrossBlock, RMSNorm, SelfAttention, SwiGLU


@dataclass(frozen=True)
class StrategyTransition:
    """One persistent state update and its current-turn decoder readout."""

    state: Tensor
    output: Tensor


class _StrategyWorkspaceBase(nn.Module):
    """Shared observation and slot-mixing weights across workspace versions."""

    def __init__(
        self,
        width: int,
        heads: int,
        feedforward: int,
        slots: int,
    ) -> None:
        super().__init__()
        self.slots = slots
        self.initial_slots = nn.Parameter(torch.empty(slots, width).normal_(std=0.02))
        self.cross = CrossBlock(width, heads)
        self.self_norm = RMSNorm(width)
        self.self_attention = SelfAttention(width, heads, slots, rotary=False)
        self.feedforward_norm = RMSNorm(width)
        self.feedforward = SwiGLU(width, feedforward)

    def initial_state(self, batch: int) -> Tensor:
        """Expand the learned episode initial state without materializing a copy."""
        return self.initial_slots[None].expand(batch, -1, -1)

    def _validate_step(self, previous: Tensor, history: Tensor, scene_latents: Tensor) -> None:
        if previous.shape[1:] != self.initial_slots.shape:
            raise ValueError("strategy state shape differs from the architecture")
        if history.shape != (previous.shape[0], previous.shape[-1]):
            raise ValueError("strategy history input has the wrong shape")
        if scene_latents.ndim != 3 or scene_latents.shape[0] != previous.shape[0]:
            raise ValueError("strategy scene latents have the wrong shape")

    @staticmethod
    def _validate_sequence(history: Tensor, scene_latents: Tensor, valid: Tensor) -> None:
        if history.ndim != 3 or scene_latents.ndim != 4 or valid.ndim != 2:
            raise ValueError("strategy sequence tensors have invalid ranks")
        if history.shape[:2] != valid.shape or scene_latents.shape[:2] != valid.shape:
            raise ValueError("strategy sequence tensors do not align")

    def _observe(self, queries: Tensor, history: Tensor, scene_latents: Tensor) -> Tensor:
        memory = torch.cat((history[:, None], scene_latents), dim=1)
        memory_mask = torch.ones(
            memory.shape[:2], dtype=torch.bool, device=memory.device
        )
        return cast(Tensor, self.cross(queries, memory, memory_mask))

    def _readout(self, state: Tensor) -> Tensor:
        hidden = state + self.self_attention(
            self.self_norm(state), None, causal=False
        )
        return cast(
            Tensor,
            hidden + self.feedforward(self.feedforward_norm(hidden)),
        )


class AttentionStrategyWorkspace(_StrategyWorkspaceBase):
    """Legacy serial attention recurrence retained for old actor artifacts."""

    def step(
        self,
        previous: Tensor,
        history: Tensor,
        scene_latents: Tensor,
    ) -> StrategyTransition:
        """Update every slot through the legacy attention recurrence."""
        self._validate_step(previous, history, scene_latents)
        state = self._readout(self._observe(previous, history, scene_latents))
        return StrategyTransition(state=state, output=state)

    def sequence(
        self,
        history: Tensor,
        scene_latents: Tensor,
        valid: Tensor,
    ) -> Tensor:
        """Run the legacy transition for an authenticated old architecture."""
        self._validate_sequence(history, scene_latents, valid)
        state = self.initial_state(history.shape[0])
        outputs: list[Tensor] = []
        for turn in range(history.shape[1]):
            transition = self.step(state, history[:, turn], scene_latents[:, turn])
            state = torch.where(
                valid[:, turn, None, None], transition.state, state
            )
            outputs.append(state)
        if not outputs:
            return history.new_empty(
                history.shape[0], 0, self.slots, history.shape[-1]
            )
        return torch.stack(outputs, dim=1)


class StrategyWorkspace(_StrategyWorkspaceBase):
    """Parallel observation encoding with a fused persistent GRU scan."""

    def __init__(
        self,
        width: int,
        heads: int,
        feedforward: int,
        slots: int,
    ) -> None:
        """Create reusable attention readout weights and one fused recurrence."""
        super().__init__(width, heads, feedforward, slots)
        self.recurrent = nn.GRU(width, width, batch_first=True)
        self._reset_recurrent_parameters()

    def _reset_recurrent_parameters(self) -> None:
        """Initialize a stable, persistence-biased GRU without changing old weights."""
        input_weight = cast(Tensor, self.recurrent.weight_ih_l0)
        hidden_weight = cast(Tensor, self.recurrent.weight_hh_l0)
        input_bias = cast(Tensor, self.recurrent.bias_ih_l0)
        hidden_bias = cast(Tensor, self.recurrent.bias_hh_l0)
        for weight in input_weight.chunk(3, dim=0):
            nn.init.xavier_uniform_(weight)
        for weight in hidden_weight.chunk(3, dim=0):
            nn.init.orthogonal_(weight)
        nn.init.zeros_(input_bias)
        nn.init.zeros_(hidden_bias)
        width = self.initial_slots.shape[-1]
        with torch.no_grad():
            input_bias[width : 2 * width].fill_(1.0)

    def _observations(self, history: Tensor, scene_latents: Tensor) -> Tensor:
        batch, turns, width = history.shape
        queries = self.initial_slots.view(1, 1, self.slots, width).expand(
            batch, turns, -1, -1
        )
        return self._observe(
            queries.flatten(0, 1),
            history.flatten(0, 1),
            scene_latents.flatten(0, 1),
        ).view(batch, turns, self.slots, width)

    def _scan(self, observations: Tensor, valid: Tensor) -> Tensor:
        """Scan valid observations, compacting only genuinely non-prefix masks."""
        batch, turns, slots, width = observations.shape
        valid_positions = valid.long().cumsum(dim=1) - 1
        seen_padding = (~valid).long().cumsum(dim=1) > 0
        if bool(torch.any(valid & seen_padding).item()):
            scatter_index = valid_positions.clamp_min(0)[..., None, None].expand_as(
                observations
            )
            observations = torch.zeros_like(observations).scatter_add(
                1,
                scatter_index,
                observations * valid[..., None, None],
            )

        recurrent_inputs = observations.permute(0, 2, 1, 3).reshape(
            batch * slots, turns, width
        )
        initial = self.initial_state(batch)
        recurrent, _ = self.recurrent(
            recurrent_inputs,
            initial.reshape(1, batch * slots, width).contiguous(),
        )
        compact_states = recurrent.view(batch, slots, turns, width).permute(0, 2, 1, 3)
        gather_index = valid_positions.clamp_min(0)[..., None, None].expand(
            -1, -1, slots, width
        )
        states = compact_states.gather(1, gather_index)
        return torch.where(
            (valid_positions >= 0)[..., None, None],
            states,
            initial[:, None],
        )

    def step(
        self,
        previous: Tensor,
        history: Tensor,
        scene_latents: Tensor,
    ) -> StrategyTransition:
        """Advance the persistent GRU state and produce mixed strategy tokens."""
        self._validate_step(previous, history, scene_latents)
        queries = self.initial_slots[None].expand(previous.shape[0], -1, -1)
        observations = self._observe(queries, history, scene_latents)
        recurrent_inputs = observations.reshape(
            previous.shape[0] * self.slots, 1, previous.shape[-1]
        )
        recurrent, _ = self.recurrent(
            recurrent_inputs,
            previous.reshape(1, previous.shape[0] * self.slots, previous.shape[-1])
            .contiguous(),
        )
        state = recurrent[:, -1].view_as(previous)
        return StrategyTransition(state=state, output=self._readout(state))

    def sequence(
        self,
        history: Tensor,
        scene_latents: Tensor,
        valid: Tensor,
    ) -> Tensor:
        """Encode all turns in parallel and run one fused persistent scan."""
        self._validate_sequence(history, scene_latents, valid)
        if not history.shape[1]:
            return history.new_empty(
                history.shape[0], 0, self.slots, history.shape[-1]
            )
        states = self._scan(self._observations(history, scene_latents), valid)
        return self._readout(states.flatten(0, 1)).view_as(states)


__all__ = [
    "AttentionStrategyWorkspace",
    "StrategyTransition",
    "StrategyWorkspace",
]
