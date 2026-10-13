"""Spatial attention policy over production contracts, with an independent critic."""

from typing import cast

import torch
from torch import Tensor, nn
from torch.nn import functional as F

from kagg_revue.policy.contracts import ContractLayout


class AttentionBlock(nn.Module):
    """Graphable spatial interactions using the shared PyTorch SDPA boundary."""

    def __init__(self, width: int, heads: int = 4) -> None:
        """Construct pre-normalized attention and a residual feedforward layer."""
        super().__init__()
        self.heads = heads
        self.norm = nn.LayerNorm(width)
        self.qkv = nn.Linear(width, 3 * width)
        self.output = nn.Linear(width, width)
        self.feedforward = nn.Sequential(
            nn.LayerNorm(width), nn.Linear(width, 3 * width), nn.GELU(), nn.Linear(3 * width, width)
        )

    def forward(self, value: Tensor) -> Tensor:
        """Mix all locations within a single official observation."""
        batch, tokens, width = value.shape
        qkv = self.qkv(self.norm(value)).view(batch, tokens, 3, self.heads, width // self.heads)
        query, key, val = qkv.permute(2, 0, 3, 1, 4).unbind(0)
        attention = F.scaled_dot_product_attention(query, key, val)
        value = value + self.output(attention.transpose(1, 2).reshape(batch, tokens, width))
        return value + cast(Tensor, self.feedforward(value))


class Policy(nn.Module):
    """Joint spatial state feedback; no directions, raw unit actions or teacher calls."""

    vocabulary: Tensor

    @staticmethod
    def from_layout(layout: ContractLayout) -> "Policy":
        """Reconstruct the exact checkpointed architecture, including legacy baselines."""
        if layout.network.memory_turns:
            from kagg_revue.policy.memory.policy import MemoryPolicy

            return MemoryPolicy(layout)
        if layout.network.architecture == "grounded-v2":
            from kagg_revue.policy.grounded.typed import TypedGroundedPolicy

            return TypedGroundedPolicy(layout)
        if layout.network.architecture == "grounded-v1":
            from kagg_revue.policy.grounded.model import GroundedPolicy

            return GroundedPolicy(layout)
        if layout.work:
            from kagg_revue.policy.spatial.work import WorkPolicy

            return WorkPolicy(layout)
        if layout.network.architecture == "entities-v2":
            from kagg_revue.policy.spatial.entity import EntityPolicy

            return EntityPolicy(layout)
        return Policy(layout)

    def __init__(self, layout: ContractLayout) -> None:
        """Build one graphable actor for BC, rollout and PPO."""
        super().__init__()
        self.layout = layout
        base = layout.observation
        width = base.width
        self.tiles = nn.Linear(base.board_features // layout.cells, width)
        self.context = nn.Sequential(
            nn.Linear(base.units * base.unit_features + base.global_features, width),
            nn.GELU(),
            nn.Linear(width, width),
        )
        self.position = nn.Parameter(torch.zeros(layout.cells + 1, width))
        self.blocks = nn.Sequential(AttentionBlock(width), AttentionBlock(width))
        self.cell_head = nn.Linear(width, 4 * 32)
        self.global_head = nn.Linear(width, 23 * 32)
        self.prior = nn.Parameter(torch.zeros(layout.decisions, layout.factors, 32))
        nn.init.zeros_(self.cell_head.weight)
        nn.init.zeros_(self.cell_head.bias)
        nn.init.zeros_(self.global_head.weight)
        nn.init.zeros_(self.global_head.bias)
        valid = torch.arange(32)[None] < torch.tensor(layout.cardinalities)[:, None]
        self.register_buffer("vocabulary", valid)

    def forward(self, observations: Tensor, steps: Tensor, actions: Tensor | None = None) -> Tensor:
        """Score the entire operating plan with one spatial attention pass."""
        base = self.layout.observation
        board = observations[:, : base.board_features].reshape(
            -1, 2, base.board_features // (2 * self.layout.cells), self.layout.cells
        )
        tiles = board.permute(0, 3, 1, 2).flatten(2)
        context = self.context(observations[:, base.board_features :].float())
        tokens = torch.cat((context[:, None], self.tiles(tiles.float())), dim=1)
        tokens = self.blocks(tokens + self.position)
        cell_logits = self.cell_head(tokens[:, 1:]).reshape(-1, self.layout.cells * 4, 32)
        controls = self.global_head(tokens[:, 0]).reshape(-1, 23, 32)
        logits = torch.cat((cell_logits, controls), dim=1).float() + self.prior[steps]
        return logits.masked_fill(~self.vocabulary, -1e9)

    def act(
        self,
        observations: Tensor,
        steps: Tensor,
        *,
        sample: bool,
        temperature: float | Tensor = 1.0,
    ) -> tuple[Tensor, Tensor]:
        """Sample complete categorical contract fields without a CPU inner loop."""
        logits = self(observations, steps)
        actions = sample_categorical(logits, temperature) if sample else logits.argmax(-1)
        return actions, log_probabilities(logits, actions, temperature)

    def field_weights(
        self,
        actions: Tensor,
        steps: Tensor,
        observations: Tensor | None = None,
    ) -> Tensor:
        """Return causal field participation for the exact action language."""
        return torch.ones_like(actions, dtype=torch.float32)


class Critic(nn.Module):
    """Independent direct terminal-outcome prediction with no actor gradient path."""

    def __init__(self, layout: ContractLayout) -> None:
        """Build a separate public-state encoder."""
        super().__init__()
        width = layout.observation.width
        self.entity_encoder: nn.Module | None = None
        if layout.network.critic_depth:
            from kagg_revue.policy.spatial.encoder import EntityEncoder

            width = layout.network.critic_width
            if layout.network.architecture == "grounded-v2":
                from kagg_revue.policy.grounded.encoder import ContextEncoder

                self.entity_encoder = ContextEncoder(layout, width, layout.network.critic_depth)
            else:
                self.entity_encoder = EntityEncoder(layout, width, layout.network.critic_depth)
            self.network = nn.Sequential(nn.Linear(width, width), nn.GELU(), nn.Linear(width, 1))
            return
        self.network = nn.Sequential(
            nn.Linear(layout.observation.features, width),
            nn.GELU(),
            nn.Linear(width, width),
            nn.GELU(),
            nn.Linear(width, 1),
        )

    def forward(self, observations: Tensor) -> Tensor:
        """Predict the configured direct terminal reward."""
        inputs = (
            observations.float()
            if self.entity_encoder is None
            else self.entity_encoder(observations)[:, 0]
        )
        return cast(Tensor, self.network(inputs)).squeeze(-1)


def scale_logits(logits: Tensor, temperature: float | Tensor) -> Tensor:
    """Apply the same fixed temperature to sampling, likelihood and entropy."""
    return logits if isinstance(temperature, float) and temperature == 1.0 else logits / temperature


def sample_categorical(logits: Tensor, temperature: float | Tensor) -> Tensor:
    """Draw categorical fields without infinite noise at a random-number endpoint."""
    if isinstance(temperature, Tensor):
        scaled = scale_logits(logits, torch.where(temperature > 0, temperature, 1.0))
        limits = torch.finfo(scaled.dtype)
        noise = torch.empty_like(scaled).exponential_().clamp_(limits.tiny, limits.max)
        sampled = (scaled - noise.log()).argmax(-1)
        return torch.where(temperature > 0, sampled, logits.argmax(-1))
    if temperature == 0:
        return logits.argmax(-1)
    logits = scale_logits(logits, temperature)
    limits = torch.finfo(logits.dtype)
    noise = torch.empty_like(logits).exponential_().clamp_(limits.tiny, limits.max)
    return (logits - noise.log()).argmax(-1)


def log_probabilities(logits: Tensor, actions: Tensor, temperature: float | Tensor = 1.0) -> Tensor:
    """Return field probabilities; PPO never forms an unstable product of ratios."""
    if isinstance(temperature, Tensor):
        safe = torch.where(temperature > 0, temperature, 1.0)
        sampled = (
            F.log_softmax(scale_logits(logits, safe), -1).gather(-1, actions[..., None]).squeeze(-1)
        )
        greedy = torch.where(actions == logits.argmax(-1), 0.0, -torch.inf)
        return torch.where(temperature > 0, sampled, greedy)
    if temperature == 0:
        return torch.where(actions == logits.argmax(-1), 0.0, -torch.inf)
    return (
        F.log_softmax(scale_logits(logits, temperature), -1)
        .gather(-1, actions[..., None])
        .squeeze(-1)
    )


def imitation_loss(logits: Tensor, actions: Tensor, weights: Tensor | None = None) -> Tensor:
    """Fit categorical operating decisions with equal complete-plan weight."""
    probabilities = log_probabilities(logits, actions)
    if weights is None:
        return -probabilities.mean()
    return -((probabilities * weights).sum(-1) / weights.sum(-1).clamp_min(1)).mean()
