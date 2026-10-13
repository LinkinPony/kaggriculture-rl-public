"""Fixed-shape neural selection over compiled capability candidates.

The native capability compiler owns legality and candidate construction.  This
module deliberately sees only dense tensors, encodes the visible state once,
and scores all candidates in one batched operation.  Search is an explicit,
bounded contribution to the behavior logits so PPO can replay the exact policy
distribution that generated a macro action.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from typing import cast

import torch
from pydantic import BaseModel, ConfigDict, Field, model_validator
from torch import Tensor, nn

from kagg_revue.policy.transformer import RMSNorm, SwiGLU


class CapabilitySelectorArchitecture(BaseModel):
    """Checkpoint-bound shape of a capability selector."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    state_width: int = Field(gt=0)
    model_width: int = Field(gt=0)
    feedforward_width: int = Field(gt=0)
    mode_tokens: int = Field(gt=1)
    integer_vocab_sizes: tuple[int, ...]
    edit_value_features: int = Field(gt=0)
    candidate_features: int = Field(gt=0)
    search_features: int = Field(default=0, ge=0)
    initial_search_gate: float = Field(default=0.5, gt=0.0, lt=1.0)
    search_logit_limit: float = Field(default=8.0, gt=0.0)

    @model_validator(mode="after")
    def validate_shape(self) -> CapabilitySelectorArchitecture:
        """Reject integer fields that cannot be embedded exactly."""
        if not self.integer_vocab_sizes:
            raise ValueError("capability candidates need at least one integer field")
        if any(size < 1 for size in self.integer_vocab_sizes):
            raise ValueError("capability integer vocabularies must be positive")
        return self


@dataclass(frozen=True)
class CapabilityCandidates:
    """One native-produced fixed-shape candidate panel.

    Shapes are ``mode [B,K]``, ``int_fields [B,K,L,I]``,
    ``edit_values [B,K,L,V]``, ``edit_counts [B,K]``,
    ``candidate_features [B,K,F]`` and ``mask [B,K]``.  Candidate zero is the
    required legal fallback.  Padding values are ignored through ``edit_counts``
    and ``mask``.
    """

    mode: Tensor
    int_fields: Tensor
    edit_values: Tensor
    edit_counts: Tensor
    candidate_features: Tensor
    mask: Tensor


@dataclass(frozen=True)
class CapabilitySelectorOutput:
    """Behavior distribution, critic predictions and search diagnostics."""

    prior_logits: Tensor
    search_logits: Tensor
    search_bonus: Tensor
    logits: Tensor
    log_probabilities: Tensor
    probabilities: Tensor
    entropy: Tensor
    value_logits: Tensor
    value: Tensor
    candidate_value_logits: Tensor
    candidate_values: Tensor
    search_gate: Tensor
    candidate_mask: Tensor


@dataclass(frozen=True)
class CapabilityActionOutput:
    """Selected macro action factor used by rollout and PPO evaluation."""

    ids: Tensor
    log_probability: Tensor
    entropy: Tensor
    value: Tensor
    selected_candidate_value: Tensor
    policy: CapabilitySelectorOutput


def _wdl_values(logits: Tensor) -> Tensor:
    """Return expected values for loss, draw and win logits."""
    probabilities = torch.softmax(logits.float(), dim=-1)
    return probabilities[..., 2] - probabilities[..., 0]


class CapabilityCandidateEncoder(nn.Module):
    """Encode all structured candidates without repeating state encoding."""

    def __init__(self, architecture: CapabilitySelectorArchitecture) -> None:
        """Create compact embeddings for mode, edit and candidate features."""
        super().__init__()
        self.architecture = architecture
        width = architecture.model_width
        self.mode_embedding = nn.Embedding(architecture.mode_tokens, width)

        offsets: list[int] = []
        offset = 0
        for size in architecture.integer_vocab_sizes:
            offsets.append(offset)
            offset += size
        self.integer_embedding = nn.Embedding(offset, width)
        self.integer_offsets: Tensor
        self.register_buffer(
            "integer_offsets",
            torch.tensor(offsets, dtype=torch.long),
            persistent=False,
        )
        self.integer_scale: float = len(architecture.integer_vocab_sizes) ** -0.5
        self.edit_value_encoder = nn.Linear(
            architecture.edit_value_features,
            width,
            bias=False,
        )
        self.edit_norm = RMSNorm(width)
        self.edit_feedforward = SwiGLU(width, architecture.feedforward_width)
        self.candidate_feature_encoder = nn.Sequential(
            nn.Linear(architecture.candidate_features, width),
            nn.SiLU(),
            nn.Linear(width, width, bias=False),
        )
        if architecture.search_features:
            self.search_feature_encoder: nn.Module | None = nn.Sequential(
                nn.Linear(architecture.search_features, width),
                nn.SiLU(),
                nn.Linear(width, width, bias=False),
            )
        else:
            self.search_feature_encoder = None
        self.output_norm = RMSNorm(width)
        self.output_feedforward = SwiGLU(width, architecture.feedforward_width)

    def _integer_edits(self, fields: Tensor) -> Tensor:
        """Embed integer fields without materializing an ``I * width`` tensor."""
        encoded = self.integer_embedding(fields[..., 0] + self.integer_offsets[0])
        for field in range(1, len(self.architecture.integer_vocab_sizes)):
            encoded = encoded + self.integer_embedding(
                fields[..., field] + self.integer_offsets[field]
            )
        return cast(Tensor, encoded * self.integer_scale)

    def forward(
        self,
        candidates: CapabilityCandidates,
        search_features: Tensor | None = None,
    ) -> Tensor:
        """Return candidate embeddings shaped ``[batch, candidates, width]``."""
        mode = candidates.mode.long()
        integer_edits = self._integer_edits(candidates.int_fields.long())
        edit_hidden = integer_edits + self.edit_value_encoder(candidates.edit_values.float())
        edit_hidden = edit_hidden + self.edit_feedforward(self.edit_norm(edit_hidden))

        edit_slots = candidates.int_fields.shape[-2]
        positions = torch.arange(edit_slots, device=mode.device)
        edit_mask = positions.view(1, 1, -1) < candidates.edit_counts.long()[..., None]
        masked_edits = edit_hidden * edit_mask[..., None].to(edit_hidden.dtype)
        edit_scale = edit_mask.sum(dim=-1).clamp_min(1).sqrt().to(edit_hidden.dtype)
        pooled_edits = masked_edits.sum(dim=-2) / edit_scale[..., None]

        hidden = (
            self.mode_embedding(mode)
            + pooled_edits
            + self.candidate_feature_encoder(candidates.candidate_features.float())
        )
        if self.search_feature_encoder is not None:
            if search_features is None:
                raise ValueError("capability selector requires configured search features")
            hidden = hidden + self.search_feature_encoder(search_features.detach().float())
        elif search_features is not None:
            raise ValueError("capability selector architecture has no search features")
        hidden = self.output_norm(hidden)
        return cast(Tensor, hidden + self.output_feedforward(hidden))


class CapabilitySelector(nn.Module):
    """PPO policy and W/D/L critic over native capability candidates."""

    def __init__(self, architecture: CapabilitySelectorArchitecture) -> None:
        """Create one state encoder and vectorized candidate-scoring heads."""
        super().__init__()
        self.architecture = architecture
        width = architecture.model_width
        self.state_encoder = nn.Sequential(
            RMSNorm(architecture.state_width),
            nn.Linear(architecture.state_width, width, bias=False),
            nn.SiLU(),
            nn.Linear(width, width, bias=False),
            RMSNorm(width),
        )
        self.candidate_encoder = CapabilityCandidateEncoder(architecture)
        self.policy_query = nn.Linear(width, width, bias=False)
        self.policy_key = nn.Linear(width, width, bias=False)
        self.state_condition = nn.Linear(width, width, bias=False)
        self.joint_norm = RMSNorm(width)
        self.policy_residual = nn.Sequential(
            nn.Linear(width, architecture.feedforward_width, bias=False),
            nn.SiLU(),
            nn.Linear(architecture.feedforward_width, 1),
        )
        self.value_head = nn.Sequential(
            RMSNorm(width),
            nn.Linear(width, architecture.feedforward_width, bias=False),
            nn.SiLU(),
            nn.Linear(architecture.feedforward_width, 3),
        )
        self.candidate_value_head = nn.Sequential(
            RMSNorm(width),
            nn.Linear(width, architecture.feedforward_width, bias=False),
            nn.SiLU(),
            nn.Linear(architecture.feedforward_width, 3),
        )
        self.search_gate_head = nn.Linear(width, 1)
        nn.init.zeros_(self.search_gate_head.weight)
        initial_gate_logit = math.log(
            architecture.initial_search_gate / (1.0 - architecture.initial_search_gate)
        )
        nn.init.constant_(self.search_gate_head.bias, initial_gate_logit)
        self.policy_scale = width**-0.5

    def _validate_inputs(
        self,
        state: Tensor,
        candidates: CapabilityCandidates,
        search_logits: Tensor,
        search_features: Tensor | None,
    ) -> None:
        batch, candidate_count = candidates.mode.shape
        if candidate_count < 1:
            raise ValueError("capability panel must contain a fallback candidate")
        if state.shape != (batch, self.architecture.state_width):
            raise ValueError("capability state has the wrong shape")
        if candidates.int_fields.ndim != 4:
            raise ValueError("capability integer edits must have shape [B,K,L,I]")
        if candidates.int_fields.shape[-2] < 1:
            raise ValueError("capability panel needs at least one edit slot")
        if candidates.int_fields.shape[:2] != (batch, candidate_count):
            raise ValueError("capability integer edits do not align with modes")
        if candidates.int_fields.shape[-1] != len(self.architecture.integer_vocab_sizes):
            raise ValueError("capability integer field count differs from architecture")
        edit_shape = candidates.int_fields.shape[:3]
        if candidates.edit_values.shape != (
            *edit_shape,
            self.architecture.edit_value_features,
        ):
            raise ValueError("capability edit values have the wrong shape")
        if candidates.edit_counts.shape != (batch, candidate_count):
            raise ValueError("capability edit counts do not align with modes")
        if candidates.candidate_features.shape != (
            batch,
            candidate_count,
            self.architecture.candidate_features,
        ):
            raise ValueError("capability candidate features have the wrong shape")
        if candidates.mask.shape != (batch, candidate_count):
            raise ValueError("capability candidate mask does not align with modes")
        if search_logits.shape != (batch, candidate_count):
            raise ValueError("capability search logits do not align with candidates")
        if self.architecture.search_features:
            expected_search_shape = (
                batch,
                candidate_count,
                self.architecture.search_features,
            )
            if search_features is None or search_features.shape != expected_search_shape:
                raise ValueError("capability search features have the wrong shape")
        elif search_features is not None:
            raise ValueError("capability selector architecture has no search features")

    @staticmethod
    def _safe_candidate_mask(mask: Tensor) -> Tensor:
        """Make an invalid all-padding row fall back to candidate zero."""
        valid = mask.bool()
        fallback = torch.arange(valid.shape[-1], device=valid.device) == 0
        return valid | ((~valid.any(dim=-1, keepdim=True)) & fallback[None])

    def _bounded_search_logits(self, search_logits: Tensor, mask: Tensor) -> Tensor:
        """Center and bound frozen search evidence on each candidate panel."""
        limit = self.architecture.search_logit_limit
        bounded = limit * torch.tanh(search_logits.detach().float() / limit)
        bounded = bounded.masked_fill(~mask, 0.0)
        weights = mask.to(bounded.dtype)
        center = (bounded * weights).sum(dim=-1, keepdim=True) / weights.sum(
            dim=-1,
            keepdim=True,
        ).clamp_min(1.0)
        return (bounded - center).masked_fill(~mask, 0.0)

    @staticmethod
    def _distribution(logits: Tensor, mask: Tensor) -> tuple[Tensor, Tensor, Tensor]:
        """Return a numerically stable explicit masked categorical policy."""
        floor = torch.finfo(torch.float32).min
        masked_logits = logits.float().masked_fill(~mask, floor)
        log_probabilities = torch.log_softmax(masked_logits, dim=-1)
        probabilities = torch.softmax(masked_logits, dim=-1)
        log_probabilities = log_probabilities.masked_fill(~mask, floor)
        entropy = -(probabilities * log_probabilities.masked_fill(~mask, 0.0)).sum(dim=-1)
        return log_probabilities, probabilities, entropy

    @staticmethod
    def _with_exploration(
        output: CapabilitySelectorOutput,
        exploration_epsilon: float,
    ) -> CapabilitySelectorOutput:
        """Mix valid-candidate uniform exploration into the behavior policy."""
        if (
            isinstance(exploration_epsilon, bool)
            or not isinstance(exploration_epsilon, int | float)
            or not math.isfinite(exploration_epsilon)
            or not 0.0 <= exploration_epsilon < 1.0
        ):
            raise ValueError("capability exploration epsilon must be finite in [0, 1)")
        epsilon = float(exploration_epsilon)
        if epsilon == 0.0:
            return output
        mask = output.candidate_mask
        valid = mask.to(output.probabilities.dtype)
        uniform = valid / valid.sum(dim=-1, keepdim=True).clamp_min(1.0)
        probabilities = (1.0 - epsilon) * output.probabilities + epsilon * uniform
        probabilities = probabilities.masked_fill(~mask, 0.0)
        floor = torch.finfo(torch.float32).min
        tiny = torch.finfo(probabilities.dtype).tiny
        log_probabilities = torch.log(probabilities.clamp_min(tiny)).masked_fill(~mask, floor)
        entropy = -(probabilities * log_probabilities.masked_fill(~mask, 0.0)).sum(dim=-1)
        return replace(
            output,
            logits=log_probabilities,
            log_probabilities=log_probabilities,
            probabilities=probabilities,
            entropy=entropy,
        )

    def forward(
        self,
        state: Tensor,
        candidates: CapabilityCandidates,
        search_logits: Tensor,
        search_features: Tensor | None = None,
    ) -> CapabilitySelectorOutput:
        """Score one fixed-shape candidate panel and expose its full policy."""
        self._validate_inputs(state, candidates, search_logits, search_features)
        candidate_mask = self._safe_candidate_mask(candidates.mask)
        state_hidden = cast(Tensor, self.state_encoder(state.float()))
        candidate_hidden = self.candidate_encoder(candidates, search_features)

        query = self.policy_query(state_hidden)
        keys = self.policy_key(candidate_hidden)
        prior_logits = (query[:, None] * keys).sum(dim=-1) * self.policy_scale
        joint = self.joint_norm(candidate_hidden + self.state_condition(state_hidden)[:, None])
        prior_logits = prior_logits + self.policy_residual(joint).squeeze(-1)

        bounded_search = self._bounded_search_logits(search_logits, candidate_mask)
        search_gate = torch.sigmoid(self.search_gate_head(state_hidden)).squeeze(-1)
        search_bonus = search_gate[:, None].float() * bounded_search
        logits = prior_logits.float() + search_bonus
        log_probabilities, probabilities, entropy = self._distribution(
            logits,
            candidate_mask,
        )
        value_logits = cast(Tensor, self.value_head(state_hidden)).float()
        candidate_value_logits = cast(
            Tensor,
            self.candidate_value_head(joint),
        ).float()
        candidate_value_logits = candidate_value_logits.masked_fill(
            ~candidate_mask[..., None],
            0.0,
        )
        return CapabilitySelectorOutput(
            prior_logits=prior_logits.float().masked_fill(
                ~candidate_mask,
                torch.finfo(torch.float32).min,
            ),
            search_logits=bounded_search,
            search_bonus=search_bonus,
            logits=logits.masked_fill(~candidate_mask, torch.finfo(torch.float32).min),
            log_probabilities=log_probabilities,
            probabilities=probabilities,
            entropy=entropy,
            value_logits=value_logits,
            value=_wdl_values(value_logits),
            candidate_value_logits=candidate_value_logits,
            candidate_values=_wdl_values(candidate_value_logits),
            search_gate=search_gate.float(),
            candidate_mask=candidate_mask,
        )

    @staticmethod
    def _action_output(
        output: CapabilitySelectorOutput,
        ids: Tensor,
    ) -> CapabilityActionOutput:
        selected = ids.long()
        return CapabilityActionOutput(
            ids=selected,
            log_probability=output.log_probabilities.gather(
                -1,
                selected[:, None],
            ).squeeze(-1),
            entropy=output.entropy,
            value=output.value,
            selected_candidate_value=output.candidate_values.gather(
                -1,
                selected[:, None],
            ).squeeze(-1),
            policy=output,
        )

    def rollout(
        self,
        state: Tensor,
        candidates: CapabilityCandidates,
        search_logits: Tensor,
        search_features: Tensor | None = None,
        *,
        sample: bool,
        exploration_epsilon: float = 0.0,
        generator: torch.Generator | None = None,
        uniform: Tensor | None = None,
    ) -> CapabilityActionOutput:
        """Sample or greedily select one macro action for environment rollout.

        Supplying pre-generated ``uniform [B,K]`` noise gives the static-shape
        CUDA Graph path and makes a sampled behavior action exactly replayable.
        """
        output = self._with_exploration(
            self(state, candidates, search_logits, search_features),
            exploration_epsilon,
        )
        if not sample:
            ids = output.logits.argmax(dim=-1)
        elif uniform is not None:
            if uniform.shape != output.logits.shape:
                raise ValueError("capability sampling noise must match policy logits")
            tiny = torch.finfo(torch.float32).tiny
            epsilon = torch.finfo(torch.float32).eps
            noise = uniform.float().clamp(min=tiny, max=1.0 - epsilon)
            gumbel = -torch.log(-torch.log(noise))
            ids = (output.logits + gumbel).argmax(dim=-1)
        else:
            ids = torch.multinomial(
                output.probabilities,
                1,
                generator=generator,
            ).squeeze(-1)
        return self._action_output(output, ids)

    def evaluate_actions(
        self,
        state: Tensor,
        candidates: CapabilityCandidates,
        search_logits: Tensor,
        selected_ids: Tensor,
        search_features: Tensor | None = None,
        *,
        exploration_epsilon: float = 0.0,
        validate_ids: bool = False,
    ) -> CapabilityActionOutput:
        """Recompute exact PPO factors on a stored candidate/search context.

        ``validate_ids`` is intended for ingestion and artifact audits.  Leave
        it disabled in the GPU minibatch path because tensor validation would
        introduce a device synchronization.
        """
        output = self._with_exploration(
            self(state, candidates, search_logits, search_features),
            exploration_epsilon,
        )
        if selected_ids.shape != state.shape[:1]:
            raise ValueError("stored capability ids must have one entry per state")
        if validate_ids:
            invalid = (selected_ids < 0) | (selected_ids >= output.logits.shape[-1])
            safe_ids = selected_ids.clamp(min=0, max=output.logits.shape[-1] - 1)
            selected_mask = output.candidate_mask.gather(-1, safe_ids[:, None]).squeeze(-1)
            if torch.any(invalid | ~selected_mask):
                raise ValueError("stored capability id is not in the candidate support")
        return self._action_output(output, selected_ids)

    def architecture_json(self) -> dict[str, object]:
        """Return the checkpoint-safe resolved selector shape."""
        return cast(dict[str, object], self.architecture.model_dump(mode="json"))


__all__ = [
    "CapabilityActionOutput",
    "CapabilityCandidateEncoder",
    "CapabilityCandidates",
    "CapabilitySelector",
    "CapabilitySelectorArchitecture",
    "CapabilitySelectorOutput",
]
