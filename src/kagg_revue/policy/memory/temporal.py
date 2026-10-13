"""Transformer-XL relative attention over complete-turn summary groups."""

import math
from typing import NamedTuple, cast

import torch
from torch import Tensor, nn
from torch.nn import functional as F

from kagg_revue.policy.memory.attention import relative_attention
from kagg_revue.policy.memory.blocks import Gate


class MemoryState(NamedTuple):
    """Detached layer inputs and their absolute turn IDs; -1 marks padding."""

    layers: tuple[Tensor, ...]
    turns: Tensor


class InferenceState(NamedTuple):
    """Projected keys and values valid only while episode weights stay fixed."""

    keys: tuple[Tensor, ...]
    values: tuple[Tensor, ...]
    turns: Tensor


class TemporalBlock(nn.Module):
    """Read relative-time memory with GTrXL residual gates."""

    def __init__(self, width: int, heads: int, turns: int) -> None:
        """Allocate independent content and relative-position attention terms."""
        super().__init__()
        self.heads = heads
        self.norm = nn.LayerNorm(width)
        self.qkv = nn.Linear(width, 3 * width)
        self.position = nn.Linear(width, width, bias=False)
        self.content_bias = nn.Parameter(torch.zeros(heads, width // heads))
        self.position_bias = nn.Parameter(torch.zeros(heads, width // heads))
        frequencies = torch.exp(torch.arange(0, width, 2) * (-math.log(10000.0) / width))
        angles = torch.arange(turns + 1)[:, None] * frequencies[None]
        self.register_buffer("relative", torch.stack((angles.sin(), angles.cos()), -1).flatten(1))
        self.output = nn.Linear(width, width)
        self.attention_gate = Gate(width)
        self.feedforward = nn.Sequential(
            nn.LayerNorm(width), nn.Linear(width, 2 * width), nn.GELU(), nn.Linear(2 * width, width)
        )
        self.feedforward_gate = Gate(width)
        self.memory_turns = turns

    def forward(self, values: Tensor, memory: Tensor, steps: Tensor, old_steps: Tensor) -> Tensor:
        """Allow all summaries of the same observation and only earlier valid turns."""
        batch, length, width = values.shape
        source = torch.cat((memory, values), 1)
        qkv = self.qkv(self.norm(source)).view(
            batch, source.shape[1], 3, self.heads, width // self.heads
        )
        query, key, content = qkv.permute(2, 0, 3, 1, 4).unbind(0)
        query = query[:, :, -length:]
        return self._attend(values, query, key, content, steps, old_steps)

    def step(
        self, values: Tensor, key: Tensor, content: Tensor, steps: Tensor, old_steps: Tensor
    ) -> tuple[Tensor, Tensor, Tensor]:
        """Project each new observation once when weights are fixed for inference."""
        batch, length, width = values.shape
        # Training concatenates these summaries with the FP32 detached input cache.
        qkv = self.qkv(self.norm(values.float())).view(
            batch, length, 3, self.heads, width // self.heads
        )
        query, current_key, current_value = qkv.permute(2, 0, 3, 1, 4).unbind(0)
        key = torch.cat((key.to(query.dtype), current_key), -2)
        content = torch.cat((content.to(query.dtype), current_value), -2)
        hidden = self._attend(values, query, key, content, steps, old_steps)
        return hidden, key, content

    def _attend(
        self,
        values: Tensor,
        query: Tensor,
        key: Tensor,
        content: Tensor,
        steps: Tensor,
        old_steps: Tensor,
    ) -> Tensor:
        batch, length, width = values.shape
        keys = torch.cat((old_steps, steps))
        positions = self.position(self.relative).view(-1, self.heads, width // self.heads)
        relative = (query + self.position_bias[None, :, None]) @ positions.permute(1, 2, 0)
        if (
            query.is_cuda
            and torch.compiler.is_compiling()
            and torch.is_grad_enabled()
            and key.dtype == torch.bfloat16
        ):
            attended = relative_attention(
                (query + self.content_bias[None, :, None]).to(key.dtype),
                key,
                content,
                relative,
                steps,
                keys,
            )
        else:
            # Dense SDPA is faster for inference and the no-gradient target pass.
            distance = steps[:, None] - keys[None]
            allowed = (keys[None] >= 0) & (distance >= 0) & (distance <= self.memory_turns)
            indices = distance.clamp(0, self.memory_turns)[None, None].expand(
                batch, self.heads, -1, -1
            )
            bias = relative.gather(-1, indices) / math.sqrt(width // self.heads)
            bias = bias.masked_fill(~allowed[None, None], -float("inf"))
            attended = F.scaled_dot_product_attention(
                query + self.content_bias[None, :, None],
                key,
                content,
                attn_mask=bias,
            )
        update = self.output(attended.transpose(1, 2).reshape(batch, length, width))
        hidden = self.attention_gate(values, F.relu(update))
        return cast(Tensor, self.feedforward_gate(hidden, F.relu(self.feedforward(hidden))))


class TemporalMemory(nn.Module):
    """Keep a fixed number of past turns, independently for every policy seat."""

    def __init__(self, width: int, layers: int, heads: int, turns: int, tokens: int) -> None:
        """Use turn units for capacity; each turn owns a group of summary tokens."""
        super().__init__()
        self.width, self.capacity, self.tokens = width, turns * tokens, tokens
        self.heads = heads
        self.blocks = nn.ModuleList(TemporalBlock(width, heads, turns) for _ in range(layers))
        self.norm = nn.LayerNorm(width)

    def empty(self, batch: int, device: torch.device) -> MemoryState:
        """Initialize padding without borrowing memory from another episode."""
        return MemoryState(
            tuple(
                torch.zeros(batch, self.capacity, self.width, device=device) for _ in self.blocks
            ),
            torch.full((self.capacity,), -1, dtype=torch.long, device=device),
        )

    def forward(
        self, values: Tensor, state: MemoryState, steps: Tensor
    ) -> tuple[Tensor, MemoryState]:
        """Process a contiguous segment and stop gradients at its memory boundary."""
        positions = steps[:, None].expand(-1, self.tokens).reshape(-1)
        hidden = values.flatten(1, 2)
        saved = []
        for block, previous in zip(self.blocks, state.layers, strict=True):
            saved.append(torch.cat((previous, hidden), 1)[:, -self.capacity :].detach())
            hidden = block(hidden, previous, positions, state.turns)
        turns = torch.cat((state.turns, positions))[-self.capacity :]
        return self.norm(hidden).reshape_as(values), MemoryState(tuple(saved), turns)

    def inference_empty(
        self, batch: int, device: torch.device, dtype: torch.dtype = torch.float32
    ) -> InferenceState:
        """Allocate fixed runtime buffers without registering ephemeral model state."""
        heads = self.heads
        shape = (batch, heads, self.capacity, self.width // heads)
        return InferenceState(
            tuple(torch.zeros(shape, device=device, dtype=dtype) for _ in self.blocks),
            tuple(torch.zeros(shape, device=device, dtype=dtype) for _ in self.blocks),
            torch.full((self.capacity,), -1, dtype=torch.long, device=device),
        )

    def step(
        self, values: Tensor, state: InferenceState, step: Tensor
    ) -> tuple[Tensor, InferenceState]:
        """Append one summary group, evicting the oldest whole turn in each layer."""
        positions = step.expand(self.tokens)
        hidden = values
        keys, contents = [], []
        for block, key, content in zip(self.blocks, state.keys, state.values, strict=True):
            assert isinstance(block, TemporalBlock)
            hidden, key, content = block.step(hidden, key, content, positions, state.turns)
            keys.append(key[..., -self.capacity :, :].detach())
            contents.append(content[..., -self.capacity :, :].detach())
        turns = torch.cat((state.turns, positions))[-self.capacity :]
        return self.norm(hidden), InferenceState(tuple(keys), tuple(contents), turns)
