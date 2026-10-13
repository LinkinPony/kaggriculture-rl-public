"""Graphable fixed-capacity history for CUDA policy inference."""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

import torch
from torch import Tensor

from kagg_revue.policy.cuda.history_attention import history_attention_step
from kagg_revue.policy.model import SceneEncoding, TurnContext, TurnPolicyNet
from kagg_revue.policy.skills import SkillStep
from kagg_revue.policy.transformer import (
    AttentionCache,
    EncoderBlock,
    RotaryEmbedding,
    SelfAttention,
)


@dataclass(frozen=True)
class CudaHistoryState:
    """Fixed-address KV storage and a device-resident write position."""

    layers: tuple[AttentionCache, ...]
    position: Tensor


def _rotate_at(rotary: RotaryEmbedding, inputs: Tensor, position: Tensor) -> Tensor:
    """Apply one rotary position selected by a device scalar."""
    cosine = rotary.cosine.index_select(0, position).to(inputs.dtype)[None, None]
    sine = rotary.sine.index_select(0, position).to(inputs.dtype)[None, None]
    even = inputs[..., 0::2]
    odd = inputs[..., 1::2]
    return torch.stack(
        (even * cosine - odd * sine, even * sine + odd * cosine),
        dim=-1,
    ).flatten(-2)


def _static_attention_step(
    attention: SelfAttention,
    inputs: Tensor,
    cache: AttentionCache,
    position: Tensor,
) -> Tensor:
    """Append one KV entry and attend only over the current valid prefix."""
    batch = inputs.shape[0]
    projected = attention.query_key_value(inputs).view(
        batch,
        1,
        3,
        attention.heads,
        attention.head_width,
    )
    query, key, value = projected.unbind(dim=2)
    query = query.transpose(1, 2)
    key = key.transpose(1, 2)
    value = value.transpose(1, 2)
    if attention.rotary is not None:
        query = _rotate_at(attention.rotary, query, position)
        key = _rotate_at(attention.rotary, key, position)
    attended = history_attention_step(
        query,
        key,
        value,
        cache.key,
        cache.value,
        position,
    )
    merged = attended.transpose(1, 2).contiguous().view(inputs.shape)
    return cast(Tensor, attention.output(merged))


class CudaStaticHistory:
    """Run exact causal history updates with shapes safe for one CUDA Graph."""

    def __init__(
        self,
        actor: TurnPolicyNet,
        batch: int,
        dtype: torch.dtype,
        *,
        include_strategy: bool = True,
    ) -> None:
        """Allocate the full episode KV capacity once on the actor device."""
        parameter = next(actor.parameters())
        architecture = actor.architecture
        heads = architecture.attention_heads
        head_width = architecture.model_width // heads
        shape = (batch, heads, architecture.max_history, head_width)
        self._actor = actor
        self._state = CudaHistoryState(
            layers=tuple(
                AttentionCache(
                    key=torch.zeros(shape, dtype=dtype, device=parameter.device),
                    value=torch.zeros(shape, dtype=dtype, device=parameter.device),
                )
                for _ in range(architecture.temporal_layers)
            ),
            position=torch.zeros(1, dtype=torch.long, device=parameter.device),
        )
        self._strategy_state = (
            actor.strategy.initial_state(batch).detach().clone().to(dtype=dtype)
            if include_strategy and actor.strategy is not None
            else None
        )

    def reset(self) -> None:
        """Reset episode position; masked stale KV entries remain unreachable."""
        self._state.position.zero_()
        if self._strategy_state is not None:
            if self._actor.strategy is None:
                raise RuntimeError("CUDA strategy module disappeared")
            self._strategy_state.copy_(
                self._actor.strategy.initial_state(self._strategy_state.shape[0])
            )

    def start_turn(
        self,
        scene: SceneEncoding,
        skill_uniform: Tensor | None = None,
    ) -> tuple[TurnContext, SkillStep | None]:
        """Append a scene summary and return current-turn decoder memory."""
        hidden = scene.summary[:, None]
        for module, cache in zip(
            self._actor.temporal.blocks,
            self._state.layers,
            strict=True,
        ):
            block = cast(EncoderBlock, module)
            update = _static_attention_step(
                block.attention,
                block.attention_norm(hidden),
                cache,
                self._state.position,
            )
            hidden = hidden + update
            hidden = hidden + block.feedforward(block.feedforward_norm(hidden))
        temporal = self._actor.temporal.output_norm(hidden)
        memory = torch.cat((temporal, scene.memory), dim=1)
        history_mask = torch.ones(
            (memory.shape[0], 1),
            dtype=torch.bool,
            device=memory.device,
        )
        memory_mask = torch.cat((history_mask, scene.memory_mask), dim=1)
        strategy_output: Tensor | None = None
        strategy_mask: Tensor | None = None
        if self._strategy_state is not None:
            if self._actor.strategy is None:
                raise RuntimeError("CUDA strategy module disappeared")
            transition = self._actor.strategy.step(
                self._strategy_state,
                temporal[:, 0],
                scene.latents,
            )
            self._strategy_state.copy_(transition.state)
            strategy_output = transition.output
            strategy_mask = torch.ones(
                self._strategy_state.shape[:2],
                dtype=torch.bool,
                device=memory.device,
            )
        skill: SkillStep | None = None
        if self._actor.skills is not None:
            if skill_uniform is None:
                raise ValueError("CUDA latent actor requires captured skill sampling noise")
            skill = self._actor.skills.step(
                temporal[:, 0],
                sample=True,
                uniform=skill_uniform,
            )
            memory, memory_mask = self._actor._condition_memory(
                memory,
                memory_mask,
                skill.embeddings,
            )
        self._state.position.add_(1)
        return (
            TurnContext(
                memory=memory,
                memory_mask=memory_mask,
                strategy=strategy_output,
                strategy_mask=strategy_mask,
            ),
            skill,
        )

    @property
    def position(self) -> Tensor:
        """Return the device-resident next write position."""
        return self._state.position


__all__ = ["CudaStaticHistory"]
