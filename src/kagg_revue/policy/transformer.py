"""Compact pre-norm transformer blocks with incremental history caches."""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

import torch
from torch import Tensor, nn
from torch.nn import functional


class RMSNorm(nn.Module):
    """Root-mean-square normalization without a mean subtraction."""

    def __init__(self, width: int, epsilon: float = 1e-6) -> None:
        """Create a learned elementwise scale."""
        super().__init__()
        self.normalized_shape = (width,)
        self.epsilon = epsilon
        self.weight = nn.Parameter(torch.ones(width))

    def forward(self, inputs: Tensor) -> Tensor:
        """Normalize the final dimension with PyTorch's fused implementation."""
        return functional.rms_norm(
            inputs,
            self.normalized_shape,
            self.weight,
            self.epsilon,
        )


class SwiGLU(nn.Module):
    """Gated feed-forward network used by every policy block."""

    def __init__(self, width: int, hidden: int) -> None:
        """Create the gate, value and output projections."""
        super().__init__()
        self.input = nn.Linear(width, 2 * hidden, bias=False)
        self.output = nn.Linear(hidden, width, bias=False)

    def forward(self, inputs: Tensor) -> Tensor:
        """Apply a SiLU gate to the parallel value projection."""
        gate, value = self.input(inputs).chunk(2, dim=-1)
        return cast(Tensor, self.output(functional.silu(gate) * value))


class RotaryEmbedding(nn.Module):
    """Rotary positions for a single attention head."""

    def __init__(self, head_width: int, max_positions: int, base: float = 10_000.0) -> None:
        """Precompute the common position range outside the inference hot path."""
        super().__init__()
        if head_width % 2:
            raise ValueError("rotary head width must be even")
        if max_positions < 1:
            raise ValueError("rotary position capacity must be positive")
        inverse = 1.0 / (base ** (torch.arange(0, head_width, 2, dtype=torch.float32) / head_width))
        frequency = torch.outer(torch.arange(max_positions, dtype=torch.float32), inverse)
        self.inverse_frequency: Tensor
        self.cosine: Tensor
        self.sine: Tensor
        self.register_buffer("inverse_frequency", inverse, persistent=False)
        self.register_buffer("cosine", frequency.cos(), persistent=False)
        self.register_buffer("sine", frequency.sin(), persistent=False)

    def forward(self, inputs: Tensor, start_position: int) -> Tensor:
        """Rotate tensors shaped ``[batch, heads, sequence, head_width]``."""
        sequence = inputs.shape[-2]
        end_position = start_position + sequence
        if start_position < 0:
            raise ValueError("rotary position cannot be negative")
        if end_position <= self.cosine.shape[0]:
            cosine = self.cosine[start_position:end_position]
            sine = self.sine[start_position:end_position]
        else:
            positions = torch.arange(
                start_position,
                end_position,
                dtype=torch.float32,
                device=inputs.device,
            )
            frequency = torch.outer(positions, self.inverse_frequency)
            cosine = frequency.cos()
            sine = frequency.sin()
        cosine = cosine[None, None].to(inputs.dtype)
        sine = sine[None, None].to(inputs.dtype)
        even = inputs[..., 0::2]
        odd = inputs[..., 1::2]
        rotated_even = even * cosine - odd * sine
        rotated_odd = even * sine + odd * cosine
        return torch.stack((rotated_even, rotated_odd), dim=-1).flatten(-2)

    def at_positions(self, inputs: Tensor, position: Tensor) -> Tensor:
        """Rotate cached tokens at scalar or per-batch device positions."""
        index = position.long().reshape(-1)
        cosine = self.cosine.index_select(0, index)[:, None, None].to(inputs.dtype)
        sine = self.sine.index_select(0, index)[:, None, None].to(inputs.dtype)
        even = inputs[..., 0::2]
        odd = inputs[..., 1::2]
        rotated_even = even * cosine - odd * sine
        rotated_odd = even * sine + odd * cosine
        return torch.stack((rotated_even, rotated_odd), dim=-1).flatten(-2)

    def at_sequence_positions(self, inputs: Tensor, positions: Tensor) -> Tensor:
        """Rotate a sequence at explicit positions shared by every batch row."""
        sequence = inputs.shape[-2]
        if positions.ndim == 2:
            if positions.shape != (inputs.shape[0], sequence):
                raise ValueError("rotary batch positions must align with inputs")
            indices = positions.long().flatten()
            shape = (inputs.shape[0], sequence, -1)
            cosine = self.cosine.index_select(0, indices).view(shape)[:, None].to(inputs.dtype)
            sine = self.sine.index_select(0, indices).view(shape)[:, None].to(inputs.dtype)
        elif positions.ndim == 1 and positions.shape[0] == sequence:
            indices = positions.long()
            cosine = self.cosine.index_select(0, indices)[None, None].to(inputs.dtype)
            sine = self.sine.index_select(0, indices)[None, None].to(inputs.dtype)
        else:
            raise ValueError("rotary sequence positions must align with inputs")
        even = inputs[..., 0::2]
        odd = inputs[..., 1::2]
        rotated_even = even * cosine - odd * sine
        rotated_odd = even * sine + odd * cosine
        return torch.stack((rotated_even, rotated_odd), dim=-1).flatten(-2)


@dataclass(frozen=True)
class AttentionCache:
    """Keys and values retained by one temporal layer."""

    key: Tensor
    value: Tensor


@dataclass(frozen=True)
class CrossAttentionCache:
    """Preprojected keys and values for immutable current-turn memory."""

    key: Tensor
    value: Tensor


@dataclass(frozen=True)
class HistoryState:
    """Episode-local incremental state for the causal history."""

    layers: tuple[AttentionCache | None, ...]
    position: int


class SelfAttention(nn.Module):
    """Multi-head attention supporting full and one-token cached execution."""

    def __init__(self, width: int, heads: int, max_history: int, *, rotary: bool) -> None:
        """Create projections and optional rotary positions."""
        super().__init__()
        if width % heads:
            raise ValueError("attention width must be divisible by head count")
        self.width = width
        self.heads = heads
        self.head_width = width // heads
        self.max_history = max_history
        self.query_key_value = nn.Linear(width, 3 * width, bias=False)
        self.output = nn.Linear(width, width, bias=False)
        self.rotary = RotaryEmbedding(self.head_width, max_history) if rotary else None
        self._position_indices: Tensor
        self.register_buffer(
            "_position_indices",
            torch.arange(max_history),
            persistent=False,
        )

    def _project(
        self,
        inputs: Tensor,
        start_position: int,
        positions: Tensor | None = None,
    ) -> tuple[Tensor, Tensor, Tensor]:
        batch, sequence, _ = inputs.shape
        projected = self.query_key_value(inputs).view(
            batch, sequence, 3, self.heads, self.head_width
        )
        query, key, value = projected.unbind(dim=2)
        query = query.transpose(1, 2)
        key = key.transpose(1, 2)
        value = value.transpose(1, 2)
        if self.rotary is not None:
            if positions is None:
                query = self.rotary(query, start_position)
                key = self.rotary(key, start_position)
            else:
                query = self.rotary.at_sequence_positions(query, positions)
                key = self.rotary.at_sequence_positions(key, positions)
        return query, key, value

    def forward(
        self,
        inputs: Tensor,
        valid: Tensor | None = None,
        *,
        causal: bool,
        positions: Tensor | None = None,
    ) -> Tensor:
        """Attend over a complete training sequence."""
        sequence = inputs.shape[1]
        query, key, value = self._project(inputs, 0, positions)
        attention_mask: Tensor | None = None
        use_native_causal = causal and valid is None
        if valid is not None:
            attention_mask = valid[:, None, None, :]
            if causal:
                triangle = torch.ones(
                    (sequence, sequence), dtype=torch.bool, device=inputs.device
                ).tril()
                attention_mask = attention_mask & triangle[None, None]
        attended = functional.scaled_dot_product_attention(
            query,
            key,
            value,
            attn_mask=attention_mask,
            dropout_p=0.0,
            is_causal=use_native_causal,
        )
        merged = attended.transpose(1, 2).contiguous().view(inputs.shape)
        return cast(Tensor, self.output(merged))

    def step(
        self,
        inputs: Tensor,
        cache: AttentionCache | None,
        position: int,
    ) -> tuple[Tensor, AttentionCache]:
        """Attend one new token to all retained history and append its KV."""
        if inputs.shape[1] != 1:
            raise ValueError("cached attention accepts exactly one token")
        query, key, value = self._project(inputs, position)
        next_cache: AttentionCache
        if not torch.is_grad_enabled() and position < self.max_history:
            if cache is None or cache.key.shape[2] != self.max_history:
                key_storage = key.new_empty(
                    key.shape[0], key.shape[1], self.max_history, key.shape[3]
                )
                value_storage = value.new_empty(
                    value.shape[0], value.shape[1], self.max_history, value.shape[3]
                )
                if cache is not None:
                    retained = min(position, cache.key.shape[2], self.max_history)
                    key_storage[:, :, :retained].copy_(cache.key[:, :, -retained:])
                    value_storage[:, :, :retained].copy_(cache.value[:, :, -retained:])
                next_cache = AttentionCache(key=key_storage, value=value_storage)
            else:
                next_cache = cache
            next_cache.key[:, :, position : position + 1].copy_(key)
            next_cache.value[:, :, position : position + 1].copy_(value)
            visible = position + 1
            attended_key = next_cache.key[:, :, :visible]
            attended_value = next_cache.value[:, :, :visible]
        else:
            if cache is not None:
                retained_key = (
                    cache.key[:, :, : min(position, self.max_history)]
                    if cache.key.shape[2] == self.max_history
                    else cache.key
                )
                retained_value = (
                    cache.value[:, :, : min(position, self.max_history)]
                    if cache.value.shape[2] == self.max_history
                    else cache.value
                )
                key = torch.cat((retained_key, key), dim=2)
                value = torch.cat((retained_value, value), dim=2)
            if key.shape[2] > self.max_history:
                key = key[:, :, -self.max_history :]
                value = value[:, :, -self.max_history :]
            attended_key = key
            attended_value = value
            next_cache = AttentionCache(key=key, value=value)
        attended = functional.scaled_dot_product_attention(
            query,
            attended_key,
            attended_value,
            dropout_p=0.0,
            is_causal=False,
        )
        merged = attended.transpose(1, 2).contiguous().view(inputs.shape)
        return cast(Tensor, self.output(merged)), next_cache

    def step_fixed(
        self,
        inputs: Tensor,
        cache: AttentionCache,
        position: Tensor,
    ) -> tuple[Tensor, AttentionCache]:
        """Append one token to a fixed cache without shape specialization."""
        batch, sequence, _ = inputs.shape
        if sequence != 1:
            raise ValueError("fixed cached attention accepts exactly one token")
        projected = self.query_key_value(inputs).view(
            batch,
            sequence,
            3,
            self.heads,
            self.head_width,
        )
        query, key, value = projected.unbind(dim=2)
        query = query.transpose(1, 2)
        key = key.transpose(1, 2)
        value = value.transpose(1, 2)
        if self.rotary is not None:
            query = self.rotary.at_positions(query, position)
            key = self.rotary.at_positions(key, position)
        index = position.long().reshape(-1)
        if index.shape[0] == 1:
            index = index.expand(batch)
        elif index.shape[0] != batch:
            raise ValueError("fixed cache positions must be scalar or per batch")
        scatter_index = index[:, None, None, None].expand_as(key)
        cache.key.scatter_(2, scatter_index, key)
        cache.value.scatter_(2, scatter_index, value)
        valid = self._position_indices[None] <= index[:, None]
        attended = functional.scaled_dot_product_attention(
            query,
            cache.key,
            cache.value,
            attn_mask=valid[:, None, None],
            dropout_p=0.0,
            is_causal=False,
        )
        merged = attended.transpose(1, 2).contiguous().view(inputs.shape)
        return cast(Tensor, self.output(merged)), cache

    def prefill_fixed(
        self,
        inputs: Tensor,
        valid: Tensor,
    ) -> tuple[Tensor, AttentionCache]:
        """Decode a known causal prefix and materialize fixed-size KV storage."""
        batch, sequence, _ = inputs.shape
        if valid.shape != (batch, sequence):
            raise ValueError("fixed prefill mask differs from the prefix")
        if sequence > self.max_history:
            raise ValueError("fixed prefill exceeds attention capacity")
        query, key, value = self._project(inputs, 0)
        triangle = torch.ones(
            (sequence, sequence),
            dtype=torch.bool,
            device=inputs.device,
        ).tril()
        attention_mask = valid[:, None, None, :] & triangle[None, None]
        attended = functional.scaled_dot_product_attention(
            query,
            key,
            value,
            attn_mask=attention_mask,
            dropout_p=0.0,
            is_causal=False,
        )
        key_storage = key.new_zeros(
            batch,
            self.heads,
            self.max_history,
            self.head_width,
        )
        value_storage = value.new_zeros(
            batch,
            self.heads,
            self.max_history,
            self.head_width,
        )
        key_storage[:, :, :sequence].copy_(key)
        value_storage[:, :, :sequence].copy_(value)
        merged = attended.transpose(1, 2).contiguous().view(inputs.shape)
        return (
            cast(Tensor, self.output(merged)),
            AttentionCache(key=key_storage, value=value_storage),
        )

class CrossAttention(nn.Module):
    """Attention from compact query tokens into an external memory."""

    def __init__(self, width: int, heads: int) -> None:
        """Create query, key/value and output projections."""
        super().__init__()
        if width % heads:
            raise ValueError("attention width must be divisible by head count")
        self.heads = heads
        self.head_width = width // heads
        self.query = nn.Linear(width, width, bias=False)
        self.key_value = nn.Linear(width, 2 * width, bias=False)
        self.output = nn.Linear(width, width, bias=False)

    def prepare(self, memory: Tensor) -> CrossAttentionCache:
        """Project immutable memory once for all autoregressive decisions."""
        batch, memory_length, _ = memory.shape
        key, value = (
            self.key_value(memory)
            .view(batch, memory_length, 2, self.heads, self.head_width)
            .unbind(dim=2)
        )
        return CrossAttentionCache(key=key.transpose(1, 2), value=value.transpose(1, 2))

    def attend(
        self,
        query_inputs: Tensor,
        memory: CrossAttentionCache,
        memory_mask: Tensor,
    ) -> Tensor:
        """Attend queries to already projected current-turn memory."""
        batch, queries, width = query_inputs.shape
        query = (
            self.query(query_inputs)
            .view(batch, queries, self.heads, self.head_width)
            .transpose(1, 2)
        )
        attended = functional.scaled_dot_product_attention(
            query,
            memory.key,
            memory.value,
            attn_mask=memory_mask[:, None, None, :],
            dropout_p=0.0,
            is_causal=False,
        )
        merged = attended.transpose(1, 2).contiguous().view(batch, queries, width)
        return cast(Tensor, self.output(merged))

    def forward(self, query_inputs: Tensor, memory: Tensor, memory_mask: Tensor) -> Tensor:
        """Project memory and return query-width outputs."""
        return self.attend(query_inputs, self.prepare(memory), memory_mask)


class EncoderBlock(nn.Module):
    """Pre-norm self-attention and SwiGLU block."""

    def __init__(self, width: int, heads: int, feedforward: int, max_history: int) -> None:
        """Create one block usable for causal or bidirectional attention."""
        super().__init__()
        self.attention_norm = RMSNorm(width)
        self.attention = SelfAttention(width, heads, max_history, rotary=True)
        self.feedforward_norm = RMSNorm(width)
        self.feedforward = SwiGLU(width, feedforward)

    def forward(
        self,
        inputs: Tensor,
        valid: Tensor | None,
        *,
        causal: bool,
        positions: Tensor | None = None,
    ) -> Tensor:
        """Transform a complete sequence."""
        hidden = inputs + self.attention(
            self.attention_norm(inputs),
            valid,
            causal=causal,
            positions=positions,
        )
        return cast(Tensor, hidden + self.feedforward(self.feedforward_norm(hidden)))

    def step(
        self,
        inputs: Tensor,
        cache: AttentionCache | None,
        position: int,
    ) -> tuple[Tensor, AttentionCache]:
        """Transform one token and update this layer's cache."""
        update, next_cache = self.attention.step(self.attention_norm(inputs), cache, position)
        hidden = inputs + update
        return hidden + self.feedforward(self.feedforward_norm(hidden)), next_cache

    def forward_root(
        self,
        inputs: Tensor,
        valid: Tensor,
        *,
        positions: Tensor | None = None,
    ) -> Tensor:
        """Compute only the first output of a final bidirectional block.

        Every entity still supplies its key and value. Other query outputs and
        their pointwise feedforward updates cannot affect the returned root.
        The joint projection shares the ordinary block's parameters and GEMM.
        """
        attention = self.attention
        query, key, value = attention._project(self.attention_norm(inputs), 0, positions)
        attended = functional.scaled_dot_product_attention(
            query[:, :, :1],
            key,
            value,
            attn_mask=valid[:, None, None],
            dropout_p=0.0,
            is_causal=False,
        )
        merged = attended.transpose(1, 2).contiguous().view(inputs.shape[0], 1, -1)
        hidden = inputs[:, :1] + attention.output(merged)
        return cast(Tensor, hidden + self.feedforward(self.feedforward_norm(hidden)))


class CrossBlock(nn.Module):
    """Pre-norm cross-attention residual used by resampler and decoder."""

    def __init__(self, width: int, heads: int) -> None:
        """Create one cross-attention residual."""
        super().__init__()
        self.query_norm = RMSNorm(width)
        self.memory_norm = RMSNorm(width)
        self.attention = CrossAttention(width, heads)

    def forward(self, queries: Tensor, memory: Tensor, memory_mask: Tensor) -> Tensor:
        """Update queries from visible memory entries."""
        return cast(
            Tensor,
            queries
            + self.attention(self.query_norm(queries), self.memory_norm(memory), memory_mask),
        )

    def prepare(self, memory: Tensor) -> CrossAttentionCache:
        """Preproject immutable memory for cached decoding."""
        return self.attention.prepare(self.memory_norm(memory))

    def step(
        self,
        queries: Tensor,
        memory: CrossAttentionCache,
        memory_mask: Tensor,
    ) -> Tensor:
        """Update one decoder token from preprojected memory."""
        return queries + self.attention.attend(self.query_norm(queries), memory, memory_mask)


class DecoderBlock(nn.Module):
    """Causal action-prefix attention followed by current-state cross-attention."""

    def __init__(
        self,
        width: int,
        heads: int,
        feedforward: int,
        max_decisions: int,
        *,
        strategy: bool = False,
    ) -> None:
        """Create one action decoding block."""
        super().__init__()
        self.self_norm = RMSNorm(width)
        self.self_attention = SelfAttention(width, heads, max_decisions, rotary=True)
        self.cross = CrossBlock(width, heads)
        self.strategy_cross: CrossBlock | None = CrossBlock(width, heads) if strategy else None
        if self.strategy_cross is not None:
            nn.init.zeros_(self.strategy_cross.attention.output.weight)
        self.feedforward_norm = RMSNorm(width)
        self.feedforward = SwiGLU(width, feedforward)

    def forward(
        self,
        inputs: Tensor,
        valid: Tensor,
        memory: Tensor,
        memory_mask: Tensor,
        strategy: Tensor | None = None,
        strategy_mask: Tensor | None = None,
    ) -> Tensor:
        """Decode a complete teacher-forced action prefix."""
        hidden = inputs + self.self_attention(self.self_norm(inputs), valid, causal=True)
        hidden = self.cross(hidden, memory, memory_mask)
        if self.strategy_cross is not None:
            if strategy is None or strategy_mask is None:
                raise ValueError("strategic decoder residual requires strategy memory")
            hidden = self.strategy_cross(hidden, strategy, strategy_mask)
        return cast(Tensor, hidden + self.feedforward(self.feedforward_norm(hidden)))

    def prepare_memory(self, memory: Tensor) -> CrossAttentionCache:
        """Project current-turn memory once for this layer."""
        return self.cross.prepare(memory)

    def prepare_strategy(self, strategy: Tensor) -> CrossAttentionCache | None:
        """Preproject strategy slots when the residual is enabled."""
        if self.strategy_cross is None:
            return None
        return self.strategy_cross.prepare(strategy)

    def step(
        self,
        inputs: Tensor,
        self_cache: AttentionCache | None,
        cross_cache: CrossAttentionCache,
        memory_mask: Tensor,
        strategy_cache: CrossAttentionCache | None,
        strategy_mask: Tensor | None,
        position: int,
    ) -> tuple[Tensor, AttentionCache]:
        """Decode one new action token and append its prefix KV."""
        update, next_cache = self.self_attention.step(self.self_norm(inputs), self_cache, position)
        hidden = inputs + update
        hidden = self.cross.step(hidden, cross_cache, memory_mask)
        if self.strategy_cross is not None:
            if strategy_cache is None or strategy_mask is None:
                raise ValueError("strategic decoder cache is absent")
            hidden = self.strategy_cross.step(hidden, strategy_cache, strategy_mask)
        hidden = hidden + self.feedforward(self.feedforward_norm(hidden))
        return cast(Tensor, hidden), next_cache

    def step_fixed(
        self,
        inputs: Tensor,
        self_cache: AttentionCache,
        cross_cache: CrossAttentionCache,
        memory_mask: Tensor,
        strategy_cache: CrossAttentionCache | None,
        strategy_mask: Tensor | None,
        position: Tensor,
    ) -> tuple[Tensor, AttentionCache]:
        """Decode one token through fixed-shape self-attention storage."""
        update, next_cache = self.self_attention.step_fixed(
            self.self_norm(inputs),
            self_cache,
            position,
        )
        hidden = inputs + update
        hidden = self.cross.step(hidden, cross_cache, memory_mask)
        if self.strategy_cross is not None:
            if strategy_cache is None or strategy_mask is None:
                raise ValueError("strategic decoder cache is absent")
            hidden = self.strategy_cross.step(
                hidden,
                strategy_cache,
                strategy_mask,
            )
        hidden = hidden + self.feedforward(self.feedforward_norm(hidden))
        return cast(Tensor, hidden), next_cache

    def prefill_fixed(
        self,
        inputs: Tensor,
        valid: Tensor,
        memory: Tensor,
        memory_mask: Tensor,
        strategy: Tensor | None,
        strategy_mask: Tensor | None,
    ) -> tuple[Tensor, AttentionCache, CrossAttentionCache, CrossAttentionCache | None]:
        """Batch a compiler-known prefix and retain caches for suffix decoding."""
        memory_cache = self.prepare_memory(memory)
        update, prefix_cache = self.self_attention.prefill_fixed(
            self.self_norm(inputs),
            valid,
        )
        hidden = inputs + update
        hidden = self.cross.step(hidden, memory_cache, memory_mask)
        strategy_cache: CrossAttentionCache | None = None
        if self.strategy_cross is not None:
            if strategy is None or strategy_mask is None:
                raise ValueError("strategic decoder cache is absent")
            strategy_cache = self.prepare_strategy(strategy)
            if strategy_cache is None:
                raise RuntimeError("strategic decoder cache was not prepared")
            hidden = self.strategy_cross.step(
                hidden,
                strategy_cache,
                strategy_mask,
            )
        hidden = hidden + self.feedforward(self.feedforward_norm(hidden))
        return (
            cast(Tensor, hidden),
            prefix_cache,
            memory_cache,
            strategy_cache,
        )

class TemporalTransformer(nn.Module):
    """Deep causal turn history with an explicit per-layer KV state."""

    def __init__(
        self,
        width: int,
        heads: int,
        feedforward: int,
        layers: int,
        max_history: int,
    ) -> None:
        """Create the causal block stack."""
        super().__init__()
        self.blocks = nn.ModuleList(
            EncoderBlock(width, heads, feedforward, max_history) for _ in range(layers)
        )
        self.output_norm = RMSNorm(width)

    def initial_state(self) -> HistoryState:
        """Return an empty episode-local cache."""
        return HistoryState(layers=tuple(None for _ in self.blocks), position=0)

    def forward(self, inputs: Tensor, valid: Tensor | None = None) -> Tensor:
        """Encode complete training sequences causally."""
        hidden = inputs
        for block in self.blocks:
            hidden = cast(EncoderBlock, block)(hidden, valid, causal=True)
        return cast(Tensor, self.output_norm(hidden))

    def step(self, inputs: Tensor, state: HistoryState | None) -> tuple[Tensor, HistoryState]:
        """Encode one turn and append it to an episode cache."""
        current = self.initial_state() if state is None else state
        if len(current.layers) != len(self.blocks):
            raise ValueError("history cache depth differs from the model")
        hidden = inputs
        next_layers: list[AttentionCache] = []
        for block, cache in zip(self.blocks, current.layers, strict=True):
            hidden, next_cache = cast(EncoderBlock, block).step(hidden, cache, current.position)
            next_layers.append(next_cache)
        return cast(Tensor, self.output_norm(hidden)), HistoryState(
            layers=tuple(next_layers), position=current.position + 1
        )


__all__ = [
    "CrossBlock",
    "CrossAttentionCache",
    "DecoderBlock",
    "EncoderBlock",
    "HistoryState",
    "RMSNorm",
    "SwiGLU",
    "TemporalTransformer",
]
