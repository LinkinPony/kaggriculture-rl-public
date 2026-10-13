"""Rich scene, portfolio, temporal, and persistent-strategy encoding."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

import torch
from torch import Tensor, nn

from kagg_revue.policy.economics.compiler import EconomicFeatureCompiler
from kagg_revue.policy.economics.layout import (
    ACTION_TOKENS,
    CANDIDATE_FEATURES,
    ECONOMIC_FEATURE_VERSION,
    MAXIMUM_QUANTITY,
    PREFIX_FEATURES,
    QUANTITY_FEATURES,
    TURN_FEATURES,
    EconomicStateLayout,
)
from kagg_revue.policy.model import ActorArchitecture, SceneEncoder
from kagg_revue.policy.plans.grammar import (
    GLOBAL_FIELD_CARDINALITIES,
    GLOBAL_FIELDS,
    LINE_FIELD_CARDINALITIES,
    PRODUCTION_LINES,
    PlanInputs,
)
from kagg_revue.policy.strategy import StrategyWorkspace
from kagg_revue.policy.transformer import (
    CrossBlock,
    HistoryState,
    RMSNorm,
    TemporalTransformer,
)

if TYPE_CHECKING:
    from kagg_revue.policy.plans.schema import StructuredPlanArchitecture


@dataclass(frozen=True)
class PlanSceneEncoding:
    """Current visible scene before causal history aggregation."""

    summary: Tensor
    latents: Tensor
    memory: Tensor
    memory_mask: Tensor
    economic_features: Tensor


@dataclass(frozen=True)
class PlanBackboneEncoding:
    """Current scene conditioned on causal strategic history."""

    history: Tensor
    scene_latents: Tensor
    scene_memory: Tensor
    scene_memory_mask: Tensor
    decoder_memory: Tensor
    decoder_memory_mask: Tensor
    strategy: Tensor | None
    economic_features: Tensor


@dataclass(frozen=True)
class PlanTemporalState:
    """Fixed-group day history retained across event decisions."""

    history_cache: HistoryState
    strategy_state: Tensor | None
    current_history: Tensor
    current_strategy: Tensor | None


class _VectorToken(nn.Module):
    """Encode one dense observation vector as one model-width token."""

    def __init__(self, inputs: int, hidden: int, width: int) -> None:
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(inputs, hidden),
            nn.SiLU(),
            nn.Linear(hidden, width, bias=False),
            RMSNorm(width),
        )

    def forward(self, value: Tensor) -> Tensor:
        """Return one token per input row."""
        return cast(Tensor, self.network(value.float()))


class PortfolioEncoder(nn.Module):
    """Tokenize committed lines, global controls, journal, and explicit events."""

    def __init__(self, architecture: StructuredPlanArchitecture) -> None:
        """Create typed discrete and dense portfolio tokenizers."""
        super().__init__()
        width = architecture.model_width
        hidden = architecture.entity_width
        self.line_identity = nn.Embedding(PRODUCTION_LINES, width)
        self.line_active = nn.Embedding(2, width)
        self.line_fields = nn.ModuleList(
            nn.Embedding(cardinality, width) for cardinality in LINE_FIELD_CARDINALITIES
        )
        self.global_identity = nn.Embedding(GLOBAL_FIELDS, width)
        self.global_fields = nn.ModuleList(
            nn.Embedding(cardinality, width) for cardinality in GLOBAL_FIELD_CARDINALITIES
        )
        self.features = _VectorToken(architecture.observation_features, hidden, width)
        self.journal = _VectorToken(architecture.journal_features, hidden, width)
        self.events = _VectorToken(architecture.event_features, hidden, width)
        self.dense_type = nn.Embedding(3, width)
        self.output_norm = RMSNorm(width)

    def forward(self, inputs: PlanInputs) -> tuple[Tensor, Tensor]:
        """Return always-visible typed portfolio tokens and their mask."""
        batch = inputs.batch_size
        line_tokens = self.line_identity.weight[None].expand(batch, -1, -1)
        line_tokens = line_tokens + self.line_active(inputs.active_line_mask.long())
        for field, embedding in enumerate(self.line_fields):
            line_tokens = line_tokens + embedding(inputs.active_lines[..., field].long())

        global_tokens = torch.stack(
            tuple(
                self.global_identity.weight[field][None]
                + embedding(inputs.global_plan[:, field].long())
                for field, embedding in enumerate(self.global_fields)
            ),
            dim=1,
        )

        dense = torch.stack(
            (
                self.features(inputs.features),
                self.journal(inputs.journal),
                self.events(inputs.events),
            ),
            dim=1,
        )
        dense = dense + self.dense_type.weight[None]
        tokens = self.output_norm(torch.cat((line_tokens, global_tokens, dense), dim=1))
        mask = torch.ones(tokens.shape[:2], dtype=torch.bool, device=tokens.device)
        return tokens, mask


def _turn_architecture(
    architecture: StructuredPlanArchitecture,
) -> ActorArchitecture:
    """Build the authenticated old-policy scene feature contract."""
    return ActorArchitecture(
        board_shape=architecture.board_shape,
        unit_shape=architecture.unit_shape,
        global_features=architecture.rich_global_features,
        model_width=architecture.model_width,
        entity_width=architecture.entity_width,
        attention_heads=architecture.attention_heads,
        feedforward_width=architecture.feedforward_width,
        latent_tokens=architecture.latent_tokens,
        register_tokens=architecture.register_tokens,
        scene_layers=architecture.scene_layers,
        temporal_layers=architecture.temporal_layers,
        action_layers=architecture.action_layers,
        max_history=architecture.max_history,
        max_decisions=architecture.factor_width,
        unit_action_tokens=44,
        market_action_tokens=23,
        maximum_quantity=MAXIMUM_QUANTITY,
        derived_fact_version=None,
        turn_fact_features=0,
        prefix_fact_features=0,
        candidate_fact_features=0,
        fact_dropout=architecture.fact_dropout,
        skill_tokens=0,
        strategy_tokens=architecture.strategy_tokens,
        strategy_version=("gru-v1" if architecture.strategy_tokens else None),
        economic_feature_version=ECONOMIC_FEATURE_VERSION,
        economic_turn_features=TURN_FEATURES,
        economic_prefix_features=PREFIX_FEATURES,
        economic_candidate_features=CANDIDATE_FEATURES,
        economic_quantity_features=QUANTITY_FEATURES,
    )


class StructuredPlanBackbone(nn.Module):
    """Reuse the old PPO scene/temporal/strategy stack for plan decisions."""

    def __init__(self, architecture: StructuredPlanArchitecture) -> None:
        """Build the reused rich scene, temporal, and GRU modules."""
        super().__init__()
        self.architecture = architecture
        turn_architecture = _turn_architecture(architecture)
        self.scene = SceneEncoder(turn_architecture)
        self.portfolio = PortfolioEncoder(architecture)
        self.portfolio_cross = CrossBlock(
            architecture.model_width,
            architecture.attention_heads,
        )
        self.portfolio_norm = RMSNorm(architecture.model_width)
        self.temporal = TemporalTransformer(
            architecture.model_width,
            architecture.attention_heads,
            architecture.feedforward_width,
            architecture.temporal_layers,
            architecture.max_history,
        )
        self.strategy = (
            StrategyWorkspace(
                architecture.model_width,
                architecture.attention_heads,
                architecture.feedforward_width,
                architecture.strategy_tokens,
            )
            if architecture.strategy_tokens
            else None
        )
        self.economics = EconomicFeatureCompiler(
            EconomicStateLayout.create(
                architecture.board_shape[-1],
                architecture.unit_shape[1],
            ),
            ACTION_TOKENS,
        )

    def encode_scene(self, inputs: PlanInputs) -> PlanSceneEncoding:
        """Encode all restored old features plus the committed portfolio."""
        batch = inputs.batch_size
        empty_actions = torch.empty((batch, 0), dtype=torch.long, device=inputs.board.device)
        empty_quantities = torch.empty(
            (batch, 0),
            dtype=inputs.global_features.dtype,
            device=inputs.board.device,
        )
        empty_mask = torch.empty((batch, 0), dtype=torch.bool, device=inputs.board.device)
        economic_features = self.economics.turn_features(
            inputs.economic_state,
            inputs.global_features,
        )
        scene = self.scene(
            inputs.board,
            inputs.units,
            inputs.global_features,
            empty_actions,
            empty_quantities,
            empty_mask,
            economic_features=economic_features,
        )
        portfolio, portfolio_mask = self.portfolio(inputs)
        latents = self.portfolio_norm(
            self.portfolio_cross(scene.latents, portfolio, portfolio_mask)
        )
        raw_scene = scene.memory[:, self.architecture.latent_tokens :]
        raw_mask = scene.memory_mask[:, self.architecture.latent_tokens :]
        memory = torch.cat((latents, raw_scene, portfolio), dim=1)
        latent_mask = torch.ones(
            latents.shape[:2],
            dtype=torch.bool,
            device=latents.device,
        )
        return PlanSceneEncoding(
            summary=latents[:, 0],
            latents=latents,
            memory=memory,
            memory_mask=torch.cat((latent_mask, raw_mask, portfolio_mask), dim=1),
            economic_features=economic_features,
        )

    def encode_current(self, inputs: PlanInputs) -> PlanBackboneEncoding:
        """Encode one independent decision as a one-step causal sequence."""
        scene = self.encode_scene(inputs)
        encoding, _state = self.advance(scene, None)
        return encoding

    @staticmethod
    def condition(
        scene: PlanSceneEncoding,
        history: Tensor,
        strategy: Tensor | None,
    ) -> PlanBackboneEncoding:
        """Condition a current event scene on the latest day-level state."""
        if history.shape != scene.summary.shape:
            raise ValueError("structured-plan history and event scene do not align")
        if strategy is not None and strategy.shape[0] != history.shape[0]:
            raise ValueError("structured-plan strategy and event scene do not align")
        decoder_memory = torch.cat((history[:, None], scene.memory), dim=1)
        history_mask = torch.ones(
            (history.shape[0], 1),
            dtype=torch.bool,
            device=history.device,
        )
        return PlanBackboneEncoding(
            history=history,
            scene_latents=scene.latents,
            scene_memory=scene.memory,
            scene_memory_mask=scene.memory_mask,
            decoder_memory=decoder_memory,
            decoder_memory_mask=torch.cat((history_mask, scene.memory_mask), dim=1),
            strategy=strategy,
            economic_features=scene.economic_features,
        )

    def advance(
        self,
        scene: PlanSceneEncoding,
        state: PlanTemporalState | None,
    ) -> tuple[PlanBackboneEncoding, PlanTemporalState]:
        """Advance one synchronized day anchor for a fixed rollout group."""
        if state is not None and state.current_history.shape != scene.summary.shape:
            raise ValueError("structured-plan temporal group batch size changed")
        temporal, history_cache = self.temporal.step(
            scene.summary[:, None],
            None if state is None else state.history_cache,
        )
        history = temporal[:, 0]
        strategy_state: Tensor | None = None
        strategy_output: Tensor | None = None
        if self.strategy is not None:
            previous = (
                self.strategy.initial_state(scene.summary.shape[0])
                if state is None or state.strategy_state is None
                else state.strategy_state
            )
            transition = self.strategy.step(previous, history, scene.latents)
            strategy_state = transition.state
            strategy_output = transition.output
        next_state = PlanTemporalState(
            history_cache=history_cache,
            strategy_state=strategy_state,
            current_history=history,
            current_strategy=strategy_output,
        )
        return self.condition(scene, history, strategy_output), next_state

    def encode_sequence(
        self,
        inputs: PlanInputs,
        episode_index: Tensor,
    ) -> PlanBackboneEncoding:
        """Replay day anchors causally and forward-fill them to event rows."""
        if episode_index.shape != (inputs.batch_size,) or episode_index.is_floating_point():
            raise ValueError("structured-plan episode index has the wrong shape or dtype")
        indices = episode_index.long()
        if bool(torch.any(indices < 0)):
            raise ValueError("structured-plan episode index cannot be negative")
        episode_count = int(indices.max().item()) + 1
        if bool(torch.any(torch.bincount(indices, minlength=episode_count) == 0)):
            raise ValueError("structured-plan sequence episode indices must be contiguous")
        scene = self.encode_scene(inputs)
        anchor = inputs.events[:, 0].bool() | inputs.events[:, 1].bool()
        episode_one_hot = torch.nn.functional.one_hot(
            indices,
            num_classes=episode_count,
        ).long()
        anchor_progress = torch.cumsum(
            episode_one_hot * anchor.long()[:, None],
            dim=0,
        )
        row_position = anchor_progress.gather(1, indices[:, None]).squeeze(1) - 1
        if bool(torch.any(row_position < 0)):
            raise ValueError("structured-plan event preceded its episode day anchor")
        anchor_episode = indices[anchor]
        anchor_position = row_position[anchor]
        counts = torch.bincount(anchor_episode, minlength=episode_count)
        if bool(torch.any(counts == 0)):
            raise ValueError("structured-plan episode has no initial/day-start anchor")
        capacity = int(counts.max().item())
        width = scene.summary.shape[-1]
        summary = scene.summary.new_zeros((episode_count, capacity, width))
        summary = summary.index_put(
            (anchor_episode, anchor_position),
            scene.summary[anchor],
        )
        latents = scene.latents.new_zeros(
            (
                episode_count,
                capacity,
                scene.latents.shape[1],
                scene.latents.shape[2],
            )
        )
        latents = latents.index_put(
            (anchor_episode, anchor_position),
            scene.latents[anchor],
        )
        valid = torch.arange(capacity, device=indices.device)[None] < counts[:, None]
        history_sequence = self.temporal(summary, valid)
        strategy_sequence = (
            self.strategy.sequence(history_sequence, latents, valid)
            if self.strategy is not None
            else None
        )
        history = history_sequence[indices, row_position]
        strategy = (
            strategy_sequence[indices, row_position]
            if strategy_sequence is not None
            else None
        )
        return self.condition(scene, history, strategy)


__all__ = [
    "PlanBackboneEncoding",
    "PlanSceneEncoding",
    "PlanTemporalState",
    "PortfolioEncoder",
    "StructuredPlanBackbone",
]
