"""Entity-resampled turn-recurrent joint policy model."""

from __future__ import annotations

from collections.abc import Mapping
from contextlib import nullcontext
from dataclasses import dataclass
from typing import Any, Literal, cast

import torch
from pydantic import BaseModel, ConfigDict, Field, model_validator
from torch import Tensor, nn

from kagg_revue.policy.economics import (
    CANDIDATE_FEATURES,
    ECONOMIC_FEATURE_VERSION,
    LEGACY_ECONOMIC_FEATURE_VERSION,
    PREFIX_FEATURES,
    QUANTITY_FEATURES,
    TURN_FEATURES,
    EconomicFeatureCompiler,
    EconomicStateLayout,
)
from kagg_revue.policy.economics.transition import apply_selection
from kagg_revue.policy.quantity import quantity_mode, sample_quantity
from kagg_revue.policy.skills import LatentSkillModel, SkillSequence, SkillStep
from kagg_revue.policy.strategy import (
    AttentionStrategyWorkspace,
    StrategyWorkspace,
)
from kagg_revue.policy.transformer import (
    AttentionCache,
    CrossAttentionCache,
    CrossBlock,
    DecoderBlock,
    EncoderBlock,
    HistoryState,
    RMSNorm,
    TemporalTransformer,
)


class ActorArchitecture(BaseModel):
    """Validated, checkpoint-bound actor shape."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    board_shape: tuple[int, int, int, int]
    unit_shape: tuple[int, int, int]
    global_features: int = Field(gt=0)
    model_width: int = Field(gt=0)
    entity_width: int = Field(gt=0)
    attention_heads: int = Field(gt=0)
    feedforward_width: int = Field(gt=0)
    latent_tokens: int = Field(gt=0)
    register_tokens: int = Field(default=0, ge=0)
    scene_layers: int = Field(ge=0)
    temporal_layers: int = Field(gt=0)
    action_layers: int = Field(gt=0)
    max_history: int = Field(gt=0)
    max_decisions: int = Field(gt=0)
    unit_action_tokens: int = Field(gt=0)
    market_action_tokens: int = Field(gt=0)
    maximum_quantity: int = Field(gt=0)
    derived_fact_version: str | None
    turn_fact_features: int = Field(ge=0)
    prefix_fact_features: int = Field(ge=0)
    candidate_fact_features: int = Field(ge=0)
    fact_dropout: float = Field(ge=0.0, lt=1.0)
    skill_tokens: int = Field(default=0, ge=0)
    strategy_tokens: int = Field(default=0, ge=0)
    strategy_version: Literal["attention-v1", "gru-v1"] | None = None
    economic_feature_version: str | None = None
    economic_turn_features: int = Field(default=0, ge=0)
    economic_prefix_features: int = Field(default=0, ge=0)
    economic_candidate_features: int = Field(default=0, ge=0)
    economic_quantity_features: int = Field(default=0, ge=0)

    @model_validator(mode="before")
    @classmethod
    def discard_legacy_auxiliary_shape(cls, value: Any) -> Any:
        """Accept old artifacts after removing their hindsight-only shape field."""
        if not isinstance(value, Mapping) or "hindsight_horizon" not in value:
            return value
        normalized = dict(value)
        normalized.pop("hindsight_horizon")
        return normalized

    @model_validator(mode="before")
    @classmethod
    def identify_legacy_strategy(cls, value: Any) -> Any:
        """Bind pre-versioned strategy artifacts to their serial implementation."""
        if not isinstance(value, Mapping):
            return value
        if value.get("strategy_tokens", 0) and "strategy_version" not in value:
            normalized = dict(value)
            normalized["strategy_version"] = "attention-v1"
            return normalized
        return value

    @model_validator(mode="after")
    def validate_shape(self) -> ActorArchitecture:
        """Reject incompatible token and attention dimensions."""
        farms, channels, height, width = self.board_shape
        unit_farms, unit_limit, unit_features = self.unit_shape
        if farms != 2 or unit_farms != 2:
            raise ValueError("actor tensors must contain own and opponent farms")
        if min(channels, height, width, unit_limit, unit_features) < 1:
            raise ValueError("actor tensor dimensions must be positive")
        if self.model_width % self.attention_heads:
            raise ValueError("model width must be divisible by attention heads")
        if (self.model_width // self.attention_heads) % 2:
            raise ValueError("attention head width must be even for rotary positions")
        fact_widths = (
            self.turn_fact_features,
            self.prefix_fact_features,
            self.candidate_fact_features,
        )
        if any(fact_widths) != all(fact_widths):
            raise ValueError("derived-fact widths must be enabled or disabled together")
        if all(fact_widths) != (self.derived_fact_version is not None):
            raise ValueError("derived-fact version and tensor widths disagree")
        economic_widths = (
            self.economic_turn_features,
            self.economic_prefix_features,
            self.economic_candidate_features,
            self.economic_quantity_features,
        )
        if any(economic_widths) != all(economic_widths):
            raise ValueError("economic feature widths must be enabled or disabled together")
        if all(economic_widths) != (self.economic_feature_version is not None):
            raise ValueError("economic feature version and tensor widths disagree")
        if self.economic_feature_version is not None:
            if self.economic_feature_version not in {
                ECONOMIC_FEATURE_VERSION,
                LEGACY_ECONOMIC_FEATURE_VERSION,
            } or economic_widths != (
                TURN_FEATURES,
                PREFIX_FEATURES,
                CANDIDATE_FEATURES,
                QUANTITY_FEATURES,
            ):
                raise ValueError("economic feature ABI is unsupported")
            expected_actions = (
                91 if self.economic_feature_version == LEGACY_ECONOMIC_FEATURE_VERSION else 67
            )
            if self.global_features != 82 or self.action_tokens != expected_actions:
                raise ValueError("economic features require the native observation/action ABI")
            if self.maximum_quantity != 128:
                raise ValueError("economic features require the deployable quantity ABI")
        if self.skill_tokens == 1:
            raise ValueError("enabled latent skills need at least two tokens")
        if self.strategy_tokens == 1:
            raise ValueError("enabled strategy workspace needs at least two tokens")
        if self.skill_tokens and self.strategy_tokens:
            raise ValueError("latent skills and recurrent strategy cannot coexist")
        if bool(self.strategy_tokens) != (self.strategy_version is not None):
            raise ValueError("strategy tokens and implementation version must coexist")
        return self

    @property
    def action_tokens(self) -> int:
        """Return the unified unit and market vocabulary width."""
        return self.unit_action_tokens + self.market_action_tokens


@dataclass(frozen=True)
class SceneEncoding:
    """Task memory, history summary, and separate register-token diagnostics."""

    summary: Tensor
    latents: Tensor
    memory: Tensor
    memory_mask: Tensor
    registers: Tensor


@dataclass(frozen=True)
class TurnContext:
    """Memory used for every autoregressive decision in one turn."""

    memory: Tensor
    memory_mask: Tensor
    strategy: Tensor | None = None
    strategy_mask: Tensor | None = None


@dataclass(frozen=True)
class SequenceEncoding:
    """Causal history and current-turn memory for a sequence batch."""

    history: Tensor
    memory: Tensor
    memory_mask: Tensor
    strategy: Tensor | None = None
    economic_features: Tensor | None = None


@dataclass(frozen=True)
class ActionLayerState:
    """Autoregressive prefix and immutable memory cache for one decoder layer."""

    prefix: AttentionCache | None
    memory: CrossAttentionCache
    strategy: CrossAttentionCache | None = None


@dataclass(frozen=True)
class ActionState:
    """Per-turn incremental state for the action decoder."""

    layers: tuple[ActionLayerState, ...]
    position: int


@dataclass(frozen=True)
class PolicyOutput:
    """Teacher-forced action and quantity predictions."""

    action_logits: Tensor
    quantity_logits: Tensor
    skills: SkillSequence | None = None
    hidden: Tensor | None = None


class FeatureEncoder(nn.Module):
    """Small shared MLP for one structured entity type."""

    def __init__(self, inputs: int, entity_width: int, model_width: int) -> None:
        """Create a two-projection entity encoder."""
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(inputs, entity_width),
            nn.SiLU(),
            nn.Linear(entity_width, model_width, bias=False),
            RMSNorm(model_width),
        )

    def forward(self, inputs: Tensor) -> Tensor:
        """Encode the final feature dimension."""
        return cast(Tensor, self.network(inputs.float()))


class ResidualFeatureEncoder(nn.Module):
    """Unnormalized MLP whose zero output projection grows in smoothly."""

    def __init__(self, inputs: int, entity_width: int, model_width: int) -> None:
        """Create an additive encoder without a zero-point RMS singularity."""
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(inputs, entity_width),
            nn.SiLU(),
            nn.Linear(entity_width, model_width, bias=False),
        )
        output = cast(nn.Linear, self.network[2])
        nn.init.zeros_(output.weight)

    def forward(self, inputs: Tensor) -> Tensor:
        """Encode one deterministic residual feature vector."""
        return cast(Tensor, self.network(inputs.float()))


class SceneEncoder(nn.Module):
    """Tokenize visible state and exact derived facts into scene latents."""

    def __init__(self, architecture: ActorArchitecture) -> None:
        """Create typed tokenizers, resampler and optional fact residual."""
        super().__init__()
        self.architecture = architecture
        _, board_channels, height, width = architecture.board_shape
        _, unit_limit, unit_features = architecture.unit_shape
        model_width = architecture.model_width
        self.tile_encoder = FeatureEncoder(board_channels, architecture.entity_width, model_width)
        self.unit_encoder = FeatureEncoder(unit_features, architecture.entity_width, model_width)
        self.global_value = nn.Linear(1, model_width, bias=False)
        self.global_identity = nn.Embedding(architecture.global_features, model_width)
        self.action_embedding = nn.Embedding(architecture.action_tokens, model_width)
        self.quantity_encoder = nn.Linear(1, model_width, bias=False)
        self.role_embedding = nn.Embedding(2, model_width)
        self.row_embedding = nn.Embedding(height, model_width)
        self.column_embedding = nn.Embedding(width, model_width)
        self.unit_slot_embedding = nn.Embedding(unit_limit, model_width)
        self.entity_type_embedding = nn.Embedding(4, model_width)
        self.raw_norm = RMSNorm(model_width)
        self.latents = nn.Parameter(
            torch.empty(architecture.latent_tokens, model_width).normal_(std=0.02)
        )
        self.register_tokens: nn.Parameter | None
        if architecture.register_tokens:
            self.register_tokens = nn.Parameter(
                torch.empty(architecture.register_tokens, model_width).normal_(std=0.02)
            )
        else:
            self.register_parameter("register_tokens", None)
        self.resample = CrossBlock(model_width, architecture.attention_heads)
        self.scene_blocks = nn.ModuleList(
            EncoderBlock(
                model_width,
                architecture.attention_heads,
                architecture.feedforward_width,
                architecture.latent_tokens + architecture.register_tokens,
            )
            for _ in range(architecture.scene_layers)
        )
        self.output_norm = RMSNorm(model_width)
        self.fact_gate: nn.Parameter | None
        if architecture.turn_fact_features:
            self.fact_encoder: nn.Module | None = FeatureEncoder(
                architecture.turn_fact_features,
                architecture.entity_width,
                model_width,
            )
            self.fact_cross: CrossBlock | None = CrossBlock(
                model_width, architecture.attention_heads
            )
            self.fact_gate = nn.Parameter(torch.tensor(-2.0))
        else:
            self.fact_encoder = None
            self.fact_cross = None
            self.register_parameter("fact_gate", None)
        if architecture.economic_turn_features:
            self.economic_encoder: nn.Module | None = ResidualFeatureEncoder(
                architecture.economic_turn_features,
                architecture.entity_width,
                model_width,
            )
        else:
            self.economic_encoder = None

        tile_role = torch.arange(2).repeat_interleave(height * width)
        row = torch.arange(height).repeat_interleave(width).repeat(2)
        column = torch.arange(width).repeat(height).repeat(2)
        unit_role = torch.arange(2).repeat_interleave(unit_limit)
        unit_slot = torch.arange(unit_limit).repeat(2)
        self.register_buffer("tile_role", tile_role, persistent=False)
        self.register_buffer("tile_row", row, persistent=False)
        self.register_buffer("tile_column", column, persistent=False)
        self.register_buffer("unit_role", unit_role, persistent=False)
        self.register_buffer("unit_slot", unit_slot, persistent=False)

    def _raw_tokens(
        self,
        board: Tensor,
        units: Tensor,
        global_features: Tensor,
        previous_actions: Tensor,
        previous_quantities: Tensor,
        previous_mask: Tensor,
    ) -> tuple[Tensor, Tensor]:
        batch = board.shape[0]
        tiles = board.permute(0, 1, 3, 4, 2).reshape(batch, -1, self.architecture.board_shape[1])
        tile_tokens = self.tile_encoder(tiles)
        tile_tokens = (
            tile_tokens
            + self.role_embedding(self.tile_role)[None]
            + self.row_embedding(self.tile_row)[None]
            + self.column_embedding(self.tile_column)[None]
            + self.entity_type_embedding.weight[0][None, None]
        )
        tile_mask = torch.ones(tile_tokens.shape[:2], dtype=torch.bool, device=board.device)

        unit_tokens = self.unit_encoder(units.reshape(batch, -1, units.shape[-1]))
        unit_tokens = (
            unit_tokens
            + self.role_embedding(self.unit_role)[None]
            + self.unit_slot_embedding(self.unit_slot)[None]
            + self.entity_type_embedding.weight[1][None, None]
        )
        unit_mask = units[..., 0].reshape(batch, -1) > 0.5

        scalar_tokens = self.global_value(global_features.float().unsqueeze(-1))
        scalar_tokens = (
            scalar_tokens
            + self.global_identity.weight[None]
            + self.entity_type_embedding.weight[2][None, None]
        )
        scalar_mask = torch.ones(scalar_tokens.shape[:2], dtype=torch.bool, device=board.device)

        safe_actions = previous_actions.clamp(min=0)
        action_tokens = self.action_embedding(safe_actions)
        action_tokens = (
            action_tokens
            + self.quantity_encoder(torch.log1p(previous_quantities.float()).unsqueeze(-1))
            + self.entity_type_embedding.weight[3][None, None]
        )
        raw = torch.cat((tile_tokens, unit_tokens, scalar_tokens, action_tokens), dim=1)
        mask = torch.cat((tile_mask, unit_mask, scalar_mask, previous_mask), dim=1)
        return self.raw_norm(raw), mask

    def _derived_fact_update(
        self,
        latents: Tensor,
        facts: Tensor | None,
        fact_mask: Tensor | None,
    ) -> Tensor:
        if (
            self.fact_encoder is None
            or self.fact_cross is None
            or self.fact_gate is None
            or facts is None
        ):
            return latents
        if facts.shape[1] == 0:
            return latents
        encoded = cast(Tensor, self.fact_encoder(facts))
        visible = (
            torch.ones(facts.shape[:2], dtype=torch.bool, device=facts.device)
            if fact_mask is None
            else fact_mask.bool()
        )
        if self.training and self.architecture.fact_dropout:
            keep = torch.rand(visible.shape, device=visible.device) >= (
                self.architecture.fact_dropout
            )
            visible = visible & keep
        encoded = torch.cat((encoded, torch.zeros_like(encoded[:, :1])), dim=1)
        visible = torch.cat(
            (
                visible,
                torch.ones((visible.shape[0], 1), dtype=torch.bool, device=visible.device),
            ),
            dim=1,
        )
        informed = self.fact_cross(latents, encoded, visible)
        gate = torch.sigmoid(self.fact_gate)
        return cast(Tensor, latents + gate * (informed - latents))

    def _economic_update(
        self,
        workspace: Tensor,
        economic_features: Tensor | None,
    ) -> Tensor:
        """Add a function-preserving residual from exact economic state."""
        if self.economic_encoder is None or economic_features is None:
            return workspace
        encoded = cast(Tensor, self.economic_encoder(economic_features))
        if self.training and self.architecture.fact_dropout:
            keep = torch.rand(encoded.shape[0], device=encoded.device) >= (
                self.architecture.fact_dropout
            )
            encoded = encoded * keep[:, None]
        return workspace + encoded[:, None]

    def forward(
        self,
        board: Tensor,
        units: Tensor,
        global_features: Tensor,
        previous_actions: Tensor,
        previous_quantities: Tensor,
        previous_mask: Tensor,
        turn_facts: Tensor | None = None,
        turn_fact_mask: Tensor | None = None,
        economic_features: Tensor | None = None,
    ) -> SceneEncoding:
        """Encode one or more independent current turns."""
        raw, raw_mask = self._raw_tokens(
            board,
            units,
            global_features,
            previous_actions,
            previous_quantities,
            previous_mask,
        )
        latents = self.latents[None].expand(board.shape[0], -1, -1)
        if self.register_tokens is not None:
            registers = self.register_tokens[None].expand(board.shape[0], -1, -1)
            workspace = torch.cat((latents, registers), dim=1)
        else:
            workspace = latents
        workspace = self.resample(workspace, raw, raw_mask)
        for block in self.scene_blocks:
            workspace = block(workspace, None, causal=False)
        workspace = self._economic_update(workspace, economic_features)
        workspace = self._derived_fact_update(workspace, turn_facts, turn_fact_mask)
        workspace = self.output_norm(workspace)
        latents = workspace[:, : self.architecture.latent_tokens]
        registers = workspace[:, self.architecture.latent_tokens :]
        memory = torch.cat((latents, raw), dim=1)
        latent_mask = torch.ones(latents.shape[:2], dtype=torch.bool, device=latents.device)
        return SceneEncoding(
            summary=latents[:, 0],
            latents=latents,
            memory=memory,
            memory_mask=torch.cat((latent_mask, raw_mask), dim=1),
            registers=registers,
        )


class ActionDecoder(nn.Module):
    """Autoregressive decoder with optional prefix and candidate facts."""

    def __init__(self, architecture: ActorArchitecture) -> None:
        """Create action-prefix blocks and categorical/quantity heads."""
        super().__init__()
        self.architecture = architecture
        width = architecture.model_width
        self.begin_token = architecture.action_tokens
        self.action_embedding = nn.Embedding(architecture.action_tokens + 1, width)
        self.quantity_embedding = nn.Linear(1, width, bias=False)
        self.phase_embedding = nn.Embedding(2, width)
        self.position_embedding = nn.Embedding(architecture.max_decisions, width)
        self.blocks = nn.ModuleList(
            DecoderBlock(
                width,
                architecture.attention_heads,
                architecture.feedforward_width,
                architecture.max_decisions,
                strategy=bool(architecture.strategy_tokens),
            )
            for _ in range(architecture.action_layers)
        )
        self.output_norm = RMSNorm(width)
        self.action_head = nn.Linear(width, architecture.action_tokens, bias=False)
        self.quantity_head = nn.Linear(width, architecture.maximum_quantity, bias=False)
        self.prefix_fact_gate: nn.Parameter | None
        if architecture.prefix_fact_features:
            self.prefix_fact_encoder: nn.Module | None = FeatureEncoder(
                architecture.prefix_fact_features,
                architecture.entity_width,
                width,
            )
            self.prefix_fact_gate = nn.Parameter(torch.tensor(-2.0))
        else:
            self.prefix_fact_encoder = None
            self.register_parameter("prefix_fact_gate", None)
        self.candidate_fact_gate: nn.Parameter | None
        self.quantity_fact_gate: nn.Parameter | None
        if architecture.candidate_fact_features:
            self.candidate_query: nn.Module | None = nn.Linear(
                width,
                architecture.candidate_fact_features,
                bias=False,
            )
            self.candidate_fact_bias: nn.Module | None = nn.Linear(
                architecture.candidate_fact_features,
                1,
                bias=False,
            )
            self.quantity_fact_encoder: nn.Module | None = FeatureEncoder(
                architecture.candidate_fact_features,
                architecture.entity_width,
                width,
            )
            self.candidate_fact_gate = nn.Parameter(torch.tensor(-2.0))
            self.quantity_fact_gate = nn.Parameter(torch.tensor(-2.0))
        else:
            self.candidate_query = None
            self.candidate_fact_bias = None
            self.quantity_fact_encoder = None
            self.register_parameter("candidate_fact_gate", None)
            self.register_parameter("quantity_fact_gate", None)
        self.fact_logit_scale = max(1, architecture.candidate_fact_features) ** -0.5
        if architecture.economic_prefix_features:
            self.economic_prefix_encoder: nn.Module | None = ResidualFeatureEncoder(
                architecture.economic_prefix_features,
                architecture.entity_width,
                width,
            )
            self.economic_candidate_query: nn.Module | None = nn.Linear(
                width,
                architecture.economic_candidate_features,
                bias=False,
            )
            self.economic_candidate_bias: nn.Module | None = nn.Linear(
                architecture.economic_candidate_features,
                1,
                bias=False,
            )
            self.economic_quantity_query: nn.Module | None = nn.Linear(
                width,
                architecture.economic_quantity_features,
                bias=False,
            )
            self.economic_quantity_bias: nn.Module | None = nn.Linear(
                architecture.economic_quantity_features,
                1,
                bias=False,
            )
            self.economic_candidate_gate: nn.Parameter | None = nn.Parameter(torch.tensor(0.0))
            self.economic_quantity_gate: nn.Parameter | None = nn.Parameter(torch.tensor(0.0))
        else:
            self.economic_prefix_encoder = None
            self.economic_candidate_query = None
            self.economic_candidate_bias = None
            self.economic_quantity_query = None
            self.economic_quantity_bias = None
            self.register_parameter("economic_candidate_gate", None)
            self.register_parameter("economic_quantity_gate", None)
        self.economic_candidate_scale = max(1, architecture.economic_candidate_features) ** -0.5
        self.economic_quantity_scale = max(1, architecture.economic_quantity_features) ** -0.5

    def _prefix_fact_update(self, hidden: Tensor, prefix_facts: Tensor | None) -> Tensor:
        if (
            self.prefix_fact_encoder is None
            or self.prefix_fact_gate is None
            or prefix_facts is None
        ):
            return hidden
        encoded = cast(Tensor, self.prefix_fact_encoder(prefix_facts))
        if self.training and self.architecture.fact_dropout:
            keep = torch.rand(encoded.shape[:-1], device=encoded.device) >= (
                self.architecture.fact_dropout
            )
            encoded = encoded * keep[..., None]
        return hidden + torch.sigmoid(self.prefix_fact_gate) * encoded

    def _action_logits(
        self,
        hidden: Tensor,
        candidate_facts: Tensor | None,
        action_head_noise: Tensor | None = None,
    ) -> Tensor:
        raw = cast(Tensor, self.action_head(hidden))
        if (
            self.candidate_query is None
            or self.candidate_fact_bias is None
            or self.candidate_fact_gate is None
            or candidate_facts is None
        ):
            result = raw
        else:
            facts = candidate_facts.float()
            present = candidate_facts[..., 0] > 0.5
            if self.training and self.architecture.fact_dropout:
                keep = torch.rand(present.shape, device=present.device) >= (
                    self.architecture.fact_dropout
                )
                present = present & keep
            query = cast(Tensor, self.candidate_query(hidden)).unsqueeze(-2)
            score = (query * facts).sum(dim=-1) * self.fact_logit_scale
            score = score + cast(Tensor, self.candidate_fact_bias(facts)).squeeze(-1)
            score = score.masked_fill(~present, 0.0)
            result = cast(Tensor, raw + torch.sigmoid(self.candidate_fact_gate) * score)
        return self._apply_action_head_noise(result, hidden, action_head_noise)

    def _apply_action_head_noise(
        self,
        logits: Tensor,
        hidden: Tensor,
        action_head_noise: Tensor | None,
    ) -> Tensor:
        """Add one episode-level residual after deterministic action biases."""
        if action_head_noise is None:
            return logits
        if (
            action_head_noise.ndim != 3
            or action_head_noise.shape[0] != hidden.shape[0]
            or action_head_noise.shape[1:] != self.action_head.weight.shape
        ):
            raise ValueError("action-head noise must provide one weight residual per episode")
        correction = torch.einsum(
            "b...d,bad->b...a",
            hidden,
            action_head_noise,
        )
        if correction.shape != logits.shape:
            raise ValueError("action-head noise correction differs from action logits")
        return logits + correction

    def _economic_prefix_update(
        self,
        hidden: Tensor,
        economic_prefix_facts: Tensor | None,
    ) -> Tensor:
        if self.economic_prefix_encoder is None or economic_prefix_facts is None:
            return hidden
        encoded = cast(Tensor, self.economic_prefix_encoder(economic_prefix_facts))
        if self.training and self.architecture.fact_dropout:
            keep = torch.rand(encoded.shape[:-1], device=encoded.device) >= (
                self.architecture.fact_dropout
            )
            encoded = encoded * keep[..., None]
        return hidden + encoded

    def _economic_action_logits(
        self,
        raw: Tensor,
        hidden: Tensor,
        facts: Tensor | None,
    ) -> Tensor:
        if (
            self.economic_candidate_query is None
            or self.economic_candidate_bias is None
            or self.economic_candidate_gate is None
            or facts is None
        ):
            return raw
        present = facts[..., 0] > 0.5
        query = cast(Tensor, self.economic_candidate_query(hidden)).unsqueeze(-2)
        score = (query * facts.float()).sum(dim=-1) * self.economic_candidate_scale
        score = score + cast(Tensor, self.economic_candidate_bias(facts.float())).squeeze(-1)
        score = score.masked_fill(~present, 0.0)
        return cast(Tensor, raw + self.economic_candidate_gate * score)

    def _inputs(
        self,
        prefix_actions: Tensor,
        prefix_quantities: Tensor,
        prediction_phases: Tensor,
        prefix_facts: Tensor | None = None,
        economic_prefix_facts: Tensor | None = None,
    ) -> Tensor:
        batch, sequence = prediction_phases.shape
        if sequence > self.architecture.max_decisions:
            raise ValueError("action sequence exceeds the architecture")
        begin = torch.full(
            (batch, 1), self.begin_token, dtype=torch.long, device=prefix_actions.device
        )
        shifted_actions = torch.cat((begin, prefix_actions[:, : sequence - 1]), dim=1)
        shifted_quantities = torch.cat(
            (
                torch.zeros((batch, 1), device=prefix_quantities.device),
                prefix_quantities[:, : sequence - 1].float(),
            ),
            dim=1,
        )
        positions = torch.arange(sequence, device=prefix_actions.device)
        hidden = cast(
            Tensor,
            self.action_embedding(shifted_actions.clamp(min=0))
            + self.quantity_embedding(torch.log1p(shifted_quantities).unsqueeze(-1))
            + self.phase_embedding(prediction_phases.clamp(min=0))
            + self.position_embedding(positions)[None],
        )
        hidden = self._prefix_fact_update(hidden, prefix_facts)
        return self._economic_prefix_update(hidden, economic_prefix_facts)

    def forward(
        self,
        target_actions: Tensor,
        target_quantities: Tensor,
        prediction_phases: Tensor,
        decision_mask: Tensor,
        memory: Tensor,
        memory_mask: Tensor,
        prefix_facts: Tensor | None = None,
        candidate_facts: Tensor | None = None,
        economic_state: Tensor | None = None,
        economic_compiler: EconomicFeatureCompiler | None = None,
        strategy: Tensor | None = None,
        strategy_mask: Tensor | None = None,
        action_head_noise: Tensor | None = None,
    ) -> PolicyOutput:
        """Predict a complete teacher-forced decision sequence."""
        economic_prefix: Tensor | None = None
        if economic_compiler is not None:
            if economic_state is None:
                raise ValueError("economic actor decoding requires compact state")
            economic_prefix = economic_compiler.sequence_prefix_features(
                economic_state,
                target_actions,
                target_quantities,
                prediction_phases,
                decision_mask,
            )
        hidden = self._inputs(
            target_actions,
            target_quantities,
            prediction_phases,
            prefix_facts,
            economic_prefix,
        )
        for block in self.blocks:
            hidden = block(
                hidden,
                decision_mask,
                memory,
                memory_mask,
                strategy,
                strategy_mask,
            )
        hidden = self.output_norm(hidden)
        if economic_compiler is None:
            return PolicyOutput(
                action_logits=self._action_logits(
                    hidden,
                    candidate_facts,
                    action_head_noise,
                ),
                quantity_logits=self.quantity_logits(
                    hidden,
                    target_actions,
                    self._selected_candidate_facts(candidate_facts, target_actions),
                ),
                hidden=hidden,
            )
        if economic_state is None:
            raise RuntimeError("economic state disappeared during decoding")
        replay = economic_state.clone()
        action_logits = []
        quantity_logits = []
        selected_candidate_facts = self._selected_candidate_facts(
            candidate_facts,
            target_actions,
        )
        base_action_logits = self._action_logits(
            hidden,
            candidate_facts,
        )
        base_quantity_logits = self.quantity_logits(
            hidden,
            target_actions,
            selected_candidate_facts,
        )
        for position in range(target_actions.shape[1]):
            step_hidden = hidden[:, position]
            candidates = economic_compiler.candidate_features(
                replay,
                prediction_phases[:, position],
            )
            action_logits.append(
                self._economic_action_logits(
                    base_action_logits[:, position],
                    step_hidden,
                    candidates,
                )
            )
            quantity_facts = economic_compiler.quantity_features(
                replay,
                target_actions[:, position],
            )
            quantity_logits.append(
                self._economic_quantity_logits(
                    base_quantity_logits[:, position],
                    step_hidden,
                    quantity_facts,
                )
            )
            apply_selection(
                replay,
                target_actions[:, position].clamp_min(0),
                target_quantities[:, position],
                decision_mask[:, position],
                economic_compiler.layout,
                economic_compiler.vocabulary,
            )
        return PolicyOutput(
            action_logits=self._apply_action_head_noise(
                torch.stack(action_logits, dim=1),
                hidden,
                action_head_noise,
            ),
            quantity_logits=torch.stack(quantity_logits, dim=1),
            hidden=hidden,
        )

    @staticmethod
    def _selected_candidate_facts(
        candidate_facts: Tensor | None, selected_actions: Tensor
    ) -> Tensor | None:
        if candidate_facts is None:
            return None
        index = selected_actions.clamp(min=0)[..., None, None].expand(
            *selected_actions.shape,
            1,
            candidate_facts.shape[-1],
        )
        return candidate_facts.gather(-2, index).squeeze(-2)

    def quantity_logits(
        self,
        hidden: Tensor,
        selected_actions: Tensor,
        selected_candidate_facts: Tensor | None = None,
        economic_quantity_facts: Tensor | None = None,
    ) -> Tensor:
        """Condition exact positive-integer logits on the chosen action."""
        selected = self.action_embedding(selected_actions.clamp(min=0))
        if (
            self.quantity_fact_encoder is not None
            and self.quantity_fact_gate is not None
            and selected_candidate_facts is not None
        ):
            fact = cast(Tensor, self.quantity_fact_encoder(selected_candidate_facts))
            if self.training and self.architecture.fact_dropout:
                keep = torch.rand(fact.shape[:-1], device=fact.device) >= (
                    self.architecture.fact_dropout
                )
                fact = fact * keep[..., None]
            selected = selected + torch.sigmoid(self.quantity_fact_gate) * fact
        raw = cast(Tensor, self.quantity_head(hidden + selected))
        return self._economic_quantity_logits(raw, hidden, economic_quantity_facts)

    def _economic_quantity_logits(
        self,
        raw: Tensor,
        hidden: Tensor,
        economic_quantity_facts: Tensor | None,
    ) -> Tensor:
        """Add a zero-gated candidate-specific residual to quantity tiers."""
        if (
            self.economic_quantity_query is None
            or self.economic_quantity_bias is None
            or self.economic_quantity_gate is None
            or economic_quantity_facts is None
        ):
            return raw
        query = cast(Tensor, self.economic_quantity_query(hidden)).unsqueeze(-2)
        facts = economic_quantity_facts.float()
        score = (query * facts).sum(dim=-1) * self.economic_quantity_scale
        score = score + cast(Tensor, self.economic_quantity_bias(facts)).squeeze(-1)
        present = facts[..., 0] > 0.5
        score = score.masked_fill(~present, 0.0)
        return cast(Tensor, raw + self.economic_quantity_gate * score)

    def initial_state(self, context: TurnContext) -> ActionState:
        """Preproject current-turn memory once for incremental decoding."""
        return ActionState(
            layers=tuple(
                ActionLayerState(
                    prefix=None,
                    memory=cast(DecoderBlock, block).prepare_memory(context.memory),
                    strategy=cast(DecoderBlock, block).prepare_strategy(context.strategy)
                    if context.strategy is not None
                    else None,
                )
                for block in self.blocks
            ),
            position=0,
        )

    def initial_fixed_state(self, context: TurnContext) -> ActionState:
        """Preproject memory and allocate fixed-shape inference-only KV caches."""
        batch = context.memory.shape[0]
        layers: list[ActionLayerState] = []
        for block in self.blocks:
            decoder_block = cast(DecoderBlock, block)
            attention = decoder_block.self_attention
            memory = decoder_block.prepare_memory(context.memory)
            strategy = (
                decoder_block.prepare_strategy(context.strategy)
                if context.strategy is not None
                else None
            )
            prefix = AttentionCache(
                key=memory.key.new_zeros(
                    batch,
                    attention.heads,
                    self.architecture.max_decisions,
                    attention.head_width,
                ),
                value=memory.value.new_zeros(
                    batch,
                    attention.heads,
                    self.architecture.max_decisions,
                    attention.head_width,
                ),
            )
            layers.append(
                ActionLayerState(
                    prefix=prefix,
                    memory=memory,
                    strategy=strategy,
                )
            )
        return ActionState(layers=tuple(layers), position=0)

    def prefill_fixed(
        self,
        prefix_actions: Tensor,
        prefix_quantities: Tensor,
        prediction_phases: Tensor,
        valid: Tensor,
        context: TurnContext,
        economic_prefix_facts: Tensor | None = None,
    ) -> ActionState:
        """Batch a compiler-known prefix into fixed caches for suffix sampling."""
        if prefix_actions.shape != prefix_quantities.shape:
            raise ValueError("fixed prefix actions and quantities differ")
        if prediction_phases.shape != prefix_actions.shape:
            raise ValueError("fixed prefix phases differ from the actions")
        if valid.shape != prefix_actions.shape:
            raise ValueError("fixed prefix mask differs from the actions")
        hidden = self._inputs(
            prefix_actions,
            prefix_quantities,
            prediction_phases,
            economic_prefix_facts=economic_prefix_facts,
        )
        next_layers: list[ActionLayerState] = []
        for block in self.blocks:
            (
                hidden,
                prefix_cache,
                memory_cache,
                strategy_cache,
            ) = cast(DecoderBlock, block).prefill_fixed(
                hidden,
                valid,
                context.memory,
                context.memory_mask,
                context.strategy,
                context.strategy_mask,
            )
            next_layers.append(
                ActionLayerState(
                    prefix=prefix_cache,
                    memory=memory_cache,
                    strategy=strategy_cache,
                )
            )
        return ActionState(layers=tuple(next_layers), position=0)

    def _cached_fixed_hidden(
        self,
        previous_action: Tensor,
        previous_quantity: Tensor,
        next_phase: Tensor,
        context: TurnContext,
        state: ActionState,
        position: Tensor,
        prefix_facts: Tensor | None = None,
        economic_prefix_facts: Tensor | None = None,
    ) -> tuple[Tensor, ActionState]:
        """Advance one fixed cache position without evaluating policy heads."""
        if len(state.layers) != len(self.blocks):
            raise ValueError("action cache depth differs from the model")
        hidden = (
            self.action_embedding(previous_action.clamp(min=0))
            + self.quantity_embedding(torch.log1p(previous_quantity.float()).unsqueeze(-1))
            + self.phase_embedding(next_phase.clamp(min=0))
            + self.position_embedding(position.long().reshape(-1))
        )[:, None]
        if prefix_facts is not None:
            prefix_facts = prefix_facts[:, None]
        hidden = self._prefix_fact_update(hidden, prefix_facts)
        if economic_prefix_facts is not None:
            economic_prefix_facts = economic_prefix_facts[:, None]
        hidden = self._economic_prefix_update(hidden, economic_prefix_facts)
        next_layers: list[ActionLayerState] = []
        for block, layer_state in zip(self.blocks, state.layers, strict=True):
            if layer_state.prefix is None:
                raise ValueError("fixed action cache storage is absent")
            hidden, prefix = cast(DecoderBlock, block).step_fixed(
                hidden,
                layer_state.prefix,
                layer_state.memory,
                context.memory_mask,
                layer_state.strategy,
                context.strategy_mask,
                position,
            )
            next_layers.append(
                ActionLayerState(
                    prefix=prefix,
                    memory=layer_state.memory,
                    strategy=layer_state.strategy,
                )
            )
        return hidden[:, 0], ActionState(
            layers=tuple(next_layers), position=0
        )

    def advance_cached_fixed(
        self,
        previous_action: Tensor,
        previous_quantity: Tensor,
        next_phase: Tensor,
        context: TurnContext,
        state: ActionState,
        position: Tensor,
        prefix_facts: Tensor | None = None,
        economic_prefix_facts: Tensor | None = None,
    ) -> ActionState:
        """Advance a compiler-forced token without unused output heads."""
        _hidden, next_state = self._cached_fixed_hidden(
            previous_action,
            previous_quantity,
            next_phase,
            context,
            state,
            position,
            prefix_facts,
            economic_prefix_facts,
        )
        return next_state

    def next_cached_fixed(
        self,
        previous_action: Tensor,
        previous_quantity: Tensor,
        next_phase: Tensor,
        context: TurnContext,
        state: ActionState,
        position: Tensor,
        prefix_facts: Tensor | None = None,
        candidate_facts: Tensor | None = None,
        economic_prefix_facts: Tensor | None = None,
        economic_candidate_facts: Tensor | None = None,
        action_head_noise: Tensor | None = None,
    ) -> tuple[Tensor, Tensor, ActionState]:
        """Decode one position through a reusable fixed-shape cache graph."""
        hidden, next_state = self._cached_fixed_hidden(
            previous_action,
            previous_quantity,
            next_phase,
            context,
            state,
            position,
            prefix_facts,
            economic_prefix_facts,
        )
        hidden = self.output_norm(hidden)
        return (
            self._apply_action_head_noise(
                self._economic_action_logits(
                    self._action_logits(hidden, candidate_facts),
                    hidden,
                    economic_candidate_facts,
                ),
                hidden,
                action_head_noise,
            ),
            hidden,
            next_state,
        )

    def next_cached(
        self,
        previous_action: Tensor | None,
        previous_quantity: Tensor | None,
        next_phase: Tensor,
        context: TurnContext,
        state: ActionState,
        prefix_facts: Tensor | None = None,
        candidate_facts: Tensor | None = None,
        economic_prefix_facts: Tensor | None = None,
        economic_candidate_facts: Tensor | None = None,
        action_head_noise: Tensor | None = None,
    ) -> tuple[Tensor, Tensor, ActionState]:
        """Decode one decision and return logits, hidden state, and caches."""
        if state.position >= self.architecture.max_decisions:
            raise ValueError("action sequence exceeds the architecture")
        if len(state.layers) != len(self.blocks):
            raise ValueError("action cache depth differs from the model")
        batch = next_phase.shape[0]
        if state.position == 0:
            shifted_action = torch.full(
                (batch,), self.begin_token, dtype=torch.long, device=next_phase.device
            )
            shifted_quantity = torch.zeros((batch,), dtype=torch.float32, device=next_phase.device)
        else:
            if previous_action is None or previous_quantity is None:
                raise ValueError("previous decision is required after the first token")
            shifted_action = previous_action
            shifted_quantity = previous_quantity.float()
        hidden = (
            self.action_embedding(shifted_action.clamp(min=0))
            + self.quantity_embedding(torch.log1p(shifted_quantity).unsqueeze(-1))
            + self.phase_embedding(next_phase.clamp(min=0))
            + self.position_embedding.weight[state.position][None]
        )[:, None]
        if prefix_facts is not None:
            prefix_facts = prefix_facts[:, None]
        hidden = self._prefix_fact_update(hidden, prefix_facts)
        if economic_prefix_facts is not None:
            economic_prefix_facts = economic_prefix_facts[:, None]
        hidden = self._economic_prefix_update(hidden, economic_prefix_facts)
        next_layers: list[ActionLayerState] = []
        for block, layer_state in zip(self.blocks, state.layers, strict=True):
            hidden, prefix = cast(DecoderBlock, block).step(
                hidden,
                layer_state.prefix,
                layer_state.memory,
                context.memory_mask,
                layer_state.strategy,
                context.strategy_mask,
                state.position,
            )
            next_layers.append(
                ActionLayerState(
                    prefix=prefix,
                    memory=layer_state.memory,
                    strategy=layer_state.strategy,
                )
            )
        hidden = self.output_norm(hidden[:, 0])
        return (
            self._apply_action_head_noise(
                self._economic_action_logits(
                    self._action_logits(hidden, candidate_facts),
                    hidden,
                    economic_candidate_facts,
                ),
                hidden,
                action_head_noise,
            ),
            hidden,
            ActionState(layers=tuple(next_layers), position=state.position + 1),
        )


class TurnPolicyNet(nn.Module):
    """Unified every-turn actor with full-history incremental inference."""

    def __init__(self, architecture: ActorArchitecture) -> None:
        """Construct scene, temporal and action modules."""
        super().__init__()
        self.architecture = architecture
        self.scene = SceneEncoder(architecture)
        self.temporal = TemporalTransformer(
            architecture.model_width,
            architecture.attention_heads,
            architecture.feedforward_width,
            architecture.temporal_layers,
            architecture.max_history,
        )
        self.action = ActionDecoder(architecture)
        self.economics = (
            EconomicFeatureCompiler(
                EconomicStateLayout.create(
                    architecture.board_shape[-1],
                    architecture.unit_shape[1],
                ),
                architecture.action_tokens,
            )
            if architecture.economic_feature_version is not None
            else None
        )
        self.skills = (
            LatentSkillModel(
                architecture.model_width,
                architecture.skill_tokens,
            )
            if architecture.skill_tokens
            else None
        )
        strategy_type = (
            StrategyWorkspace
            if architecture.strategy_version == "gru-v1"
            else AttentionStrategyWorkspace
        )
        self.strategy = (
            strategy_type(
                architecture.model_width,
                architecture.attention_heads,
                architecture.feedforward_width,
                architecture.strategy_tokens,
            )
            if architecture.strategy_tokens
            else None
        )

    def _previous_actions(
        self, actions: Tensor, quantities: Tensor, decision_mask: Tensor
    ) -> tuple[Tensor, Tensor, Tensor]:
        previous_actions = torch.zeros_like(actions)
        previous_quantities = torch.zeros_like(quantities)
        previous_mask = torch.zeros_like(decision_mask)
        previous_actions[:, 1:] = actions[:, :-1].clamp(min=0)
        previous_quantities[:, 1:] = quantities[:, :-1]
        previous_mask[:, 1:] = decision_mask[:, :-1]
        return previous_actions, previous_quantities, previous_mask

    def encode_sequence(
        self,
        board: Tensor,
        units: Tensor,
        global_features: Tensor,
        actions: Tensor,
        quantities: Tensor,
        turn_mask: Tensor,
        decision_mask: Tensor,
        turn_facts: Tensor | None = None,
        turn_fact_mask: Tensor | None = None,
        economic_state: Tensor | None = None,
        *,
        compute_strategy: bool = True,
        full_precision_history: bool = False,
    ) -> SequenceEncoding:
        """Encode actor-visible turns without decoding their target actions."""
        batch, turns = board.shape[:2]
        previous_actions, previous_quantities, previous_mask = self._previous_actions(
            actions, quantities, decision_mask
        )
        flat_turn_facts = turn_facts.flatten(0, 1) if turn_facts is not None else None
        flat_turn_fact_mask = turn_fact_mask.flatten(0, 1) if turn_fact_mask is not None else None
        economic_features: Tensor | None = None
        if self.economics is not None:
            if economic_state is None:
                raise ValueError("economic actor encoding requires compact state")
            flat_economic_state = economic_state.flatten(0, 1)
            economic_features = self.economics.turn_features(
                flat_economic_state,
                global_features.flatten(0, 1),
            )
        scene = self.scene(
            board.flatten(0, 1),
            units.flatten(0, 1),
            global_features.flatten(0, 1),
            previous_actions.flatten(0, 1),
            previous_quantities.flatten(0, 1),
            previous_mask.flatten(0, 1),
            flat_turn_facts,
            flat_turn_fact_mask,
            economic_features,
        )
        summary = scene.summary.view(batch, turns, -1)
        scene_latents = scene.latents.view(
            batch, turns, scene.latents.shape[1], scene.latents.shape[2]
        )
        with (
            torch.autocast(board.device.type, enabled=False)
            if full_precision_history else nullcontext()
        ):
            history = self.temporal(
                summary.float() if full_precision_history else summary, turn_mask
            )
            strategy = (
                self.strategy.sequence(
                    history,
                    scene_latents.float() if full_precision_history else scene_latents,
                    turn_mask,
                )
                if compute_strategy and self.strategy is not None
                else None
            )
        scene_memory = scene.memory.view(batch, turns, scene.memory.shape[1], -1)
        scene_mask = scene.memory_mask.view(batch, turns, -1)
        memory = torch.cat((history[:, :, None], scene_memory), dim=2).flatten(0, 1)
        history_mask = turn_mask[:, :, None]
        memory_mask = torch.cat((history_mask, scene_mask), dim=2).flatten(0, 1)
        return SequenceEncoding(
            history=history,
            memory=memory,
            memory_mask=memory_mask,
            strategy=strategy,
            economic_features=(
                None if economic_features is None else economic_features.view(batch, turns, -1)
            ),
        )

    def select_sequence_skills(
        self,
        encoding: SequenceEncoding,
        turn_mask: Tensor,
        *,
        skill_ids: Tensor | None = None,
        sample: bool,
        validate_ids: bool = True,
    ) -> SkillSequence | None:
        """Choose causal skills or evaluate stored causal choices."""
        if self.skills is None:
            if skill_ids is not None and torch.any(skill_ids[turn_mask] >= 0):
                raise ValueError("legacy actor cannot consume stored latent skills")
            return None
        return self.skills.sequence(
            encoding.history,
            turn_mask,
            skill_ids=skill_ids,
            sample=sample,
            validate_ids=validate_ids,
        )

    @staticmethod
    def _condition_memory(
        memory: Tensor,
        memory_mask: Tensor,
        skill_embeddings: Tensor,
    ) -> tuple[Tensor, Tensor]:
        """Insert one learned skill token after the causal history token."""
        if skill_embeddings.shape != (memory.shape[0], memory.shape[-1]):
            raise ValueError("skill embedding and decoder memory must align")
        conditioned = torch.cat(
            (memory[:, :1], skill_embeddings[:, None], memory[:, 1:]),
            dim=1,
        )
        skill_mask = torch.ones(
            (memory.shape[0], 1),
            dtype=torch.bool,
            device=memory.device,
        )
        return conditioned, torch.cat(
            (memory_mask[:, :1], skill_mask, memory_mask[:, 1:]),
            dim=1,
        )

    def decode_sequence(
        self,
        encoding: SequenceEncoding,
        actions: Tensor,
        quantities: Tensor,
        phases: Tensor,
        decision_mask: Tensor,
        prefix_facts: Tensor | None = None,
        candidate_facts: Tensor | None = None,
        skills: SkillSequence | None = None,
        economic_state: Tensor | None = None,
        action_head_noise: Tensor | None = None,
        action_head_noise_turn_mask: Tensor | None = None,
    ) -> PolicyOutput:
        """Decode teacher-forced actions from an already encoded sequence."""
        batch, turns = actions.shape[:2]
        memory = encoding.memory
        memory_mask = encoding.memory_mask
        if self.skills is not None:
            if skills is None:
                raise ValueError("latent actor decoding requires a skill sequence")
            memory, memory_mask = self._condition_memory(
                memory,
                memory_mask,
                skills.embeddings.flatten(0, 1),
            )
        if action_head_noise is not None:
            expected = (
                batch,
                self.architecture.action_tokens,
                self.architecture.model_width,
            )
            if action_head_noise.shape != expected:
                raise ValueError("sequence action-head noise differs from the actor architecture")
            if action_head_noise_turn_mask is not None and action_head_noise_turn_mask.shape != (
                batch,
                turns,
            ):
                raise ValueError("sequence action-head noise mask differs from the turn batch")
        elif action_head_noise_turn_mask is not None:
            raise ValueError("sequence action-head noise mask requires action-head noise")
        output = self.action(
            actions.flatten(0, 1),
            quantities.flatten(0, 1),
            phases.flatten(0, 1),
            decision_mask.flatten(0, 1),
            memory,
            memory_mask,
            strategy=(encoding.strategy.flatten(0, 1) if encoding.strategy is not None else None),
            strategy_mask=(
                torch.ones(
                    (batch * turns, self.architecture.strategy_tokens),
                    dtype=torch.bool,
                    device=memory.device,
                )
                if encoding.strategy is not None
                else None
            ),
            prefix_facts=(prefix_facts.flatten(0, 1) if prefix_facts is not None else None),
            candidate_facts=(
                candidate_facts.flatten(0, 1) if candidate_facts is not None else None
            ),
            economic_state=(economic_state.flatten(0, 1) if economic_state is not None else None),
            economic_compiler=self.economics,
        )
        if output.hidden is None:
            raise RuntimeError("action decoder omitted its normalized hidden state")
        action_logits = output.action_logits.view(
            batch,
            turns,
            *output.action_logits.shape[1:],
        )
        hidden = output.hidden.view(batch, turns, *output.hidden.shape[1:])
        if action_head_noise is not None:
            correction = torch.einsum("bt...d,bad->bt...a", hidden, action_head_noise)
            if action_head_noise_turn_mask is not None:
                correction = correction * action_head_noise_turn_mask[:, :, None, None]
            action_logits = action_logits + correction
        return PolicyOutput(
            action_logits=action_logits,
            quantity_logits=output.quantity_logits.view(
                batch, turns, *output.quantity_logits.shape[1:]
            ),
            skills=skills,
            hidden=hidden,
        )

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
        turn_facts: Tensor | None = None,
        turn_fact_mask: Tensor | None = None,
        prefix_facts: Tensor | None = None,
        candidate_facts: Tensor | None = None,
        economic_state: Tensor | None = None,
        *,
        skill_ids: Tensor | None = None,
        sample_skills: bool | None = None,
        action_head_noise: Tensor | None = None,
        action_head_noise_turn_mask: Tensor | None = None,
    ) -> PolicyOutput:
        """Train over contiguous sequences using causal history and teacher forcing."""
        encoding = self.encode_sequence(
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
        )
        skills = self.select_sequence_skills(
            encoding,
            turn_mask,
            skill_ids=skill_ids,
            sample=self.training if sample_skills is None else sample_skills,
        )
        return self.decode_sequence(
            encoding,
            actions,
            quantities,
            phases,
            decision_mask,
            prefix_facts,
            candidate_facts,
            skills,
            economic_state,
            action_head_noise,
            action_head_noise_turn_mask,
        )

    def start_turn(
        self,
        board: Tensor,
        units: Tensor,
        global_features: Tensor,
        previous_actions: Tensor,
        previous_quantities: Tensor,
        previous_mask: Tensor,
        history: HistoryState | None,
        turn_facts: Tensor | None = None,
        turn_fact_mask: Tensor | None = None,
        economic_state: Tensor | None = None,
        strategy_state: Tensor | None = None,
        *,
        sample_skill: bool = False,
        generator: torch.Generator | None = None,
        skill_uniform: Tensor | None = None,
        full_precision_history: bool = False,
    ) -> tuple[TurnContext, HistoryState, Tensor | None, SkillStep | None]:
        """Encode one visible turn and append exactly one history token."""
        economic_features: Tensor | None = None
        if self.economics is not None:
            if economic_state is None:
                raise ValueError("economic actor turn requires compact state")
            economic_features = self.economics.turn_features(
                economic_state,
                global_features,
            )
        scene = self.scene(
            board,
            units,
            global_features,
            previous_actions,
            previous_quantities,
            previous_mask,
            turn_facts,
            turn_fact_mask,
            economic_features,
        )
        next_strategy: Tensor | None = None
        strategy_output: Tensor | None = None
        strategy_mask: Tensor | None = None
        with (
            torch.autocast(board.device.type, enabled=False)
            if full_precision_history else nullcontext()
        ):
            summary = scene.summary[:, None]
            temporal, next_history = self.temporal.step(
                summary.float() if full_precision_history else summary, history
            )
            if self.strategy is not None:
                previous_strategy = (
                    self.strategy.initial_state(board.shape[0])
                    if strategy_state is None
                    else strategy_state
                )
                transition = self.strategy.step(
                    previous_strategy.float() if full_precision_history else previous_strategy,
                    temporal[:, 0],
                    scene.latents.float() if full_precision_history else scene.latents,
                )
                next_strategy = transition.state
                strategy_output = transition.output
                strategy_mask = torch.ones(
                    next_strategy.shape[:2], dtype=torch.bool, device=board.device
                )
            elif strategy_state is not None:
                raise ValueError("legacy actor cannot consume recurrent strategy state")
        memory = torch.cat((temporal, scene.memory), dim=1)
        memory_mask = torch.cat(
            (
                torch.ones((board.shape[0], 1), dtype=torch.bool, device=board.device),
                scene.memory_mask,
            ),
            dim=1,
        )
        skill: SkillStep | None = None
        if self.skills is not None:
            skill = self.skills.step(
                temporal[:, 0],
                sample=sample_skill,
                generator=generator,
                uniform=skill_uniform,
            )
            memory, memory_mask = self._condition_memory(
                memory,
                memory_mask,
                skill.embeddings,
            )
        return (
            TurnContext(
                memory=memory,
                memory_mask=memory_mask,
                strategy=strategy_output,
                strategy_mask=strategy_mask,
            ),
            next_history,
            next_strategy,
            skill,
        )

    def choose_quantity(
        self,
        logits: Tensor,
        *,
        sample: bool,
        generator: torch.Generator | None = None,
    ) -> Tensor:
        """Choose an exact positive request quantity from decoder logits."""
        if sample:
            return sample_quantity(logits, generator)
        return quantity_mode(logits)

    def architecture_json(self) -> dict[str, Any]:
        """Return the checkpoint-safe resolved actor shape."""
        return self.architecture.model_dump(mode="json")


def parameter_count(model: nn.Module) -> int:
    """Return the measured trainable and non-trainable parameter count."""
    return sum(parameter.numel() for parameter in model.parameters())


__all__ = [
    "ActionState",
    "ActorArchitecture",
    "PolicyOutput",
    "SequenceEncoding",
    "TurnContext",
    "TurnPolicyNet",
    "parameter_count",
]
