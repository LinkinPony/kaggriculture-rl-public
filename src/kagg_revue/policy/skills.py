"""Data-discovered latent skills shared by BC and on-policy RL."""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

import torch
from torch import Tensor, nn
from torch.nn import functional

from kagg_revue.policy.transformer import RMSNorm


@dataclass(frozen=True)
class SkillSequence:
    """One causal latent choice per visible turn."""

    prior_logits: Tensor
    ids: Tensor
    embeddings: Tensor


@dataclass(frozen=True)
class SkillStep:
    """One causal latent choice used by incremental inference."""

    ids: Tensor
    log_probability: Tensor
    entropy: Tensor
    embeddings: Tensor


class LatentSkillModel(nn.Module):
    """Infer discrete behavior modes without assigning them hand-written names."""

    def __init__(
        self,
        width: int,
        skill_tokens: int,
    ) -> None:
        """Create the causal selector and learned codebook."""
        super().__init__()
        if skill_tokens < 2:
            raise ValueError("latent skill model needs at least two skill tokens")
        self.skill_tokens = skill_tokens
        self.prior = nn.Sequential(
            RMSNorm(width),
            nn.Linear(width, width, bias=False),
            nn.SiLU(),
            nn.Linear(width, skill_tokens),
        )
        self.codebook = nn.Embedding(skill_tokens, width)
        nn.init.normal_(self.codebook.weight, std=0.02)

    @staticmethod
    def _one_hot_choice(logits: Tensor, *, sample: bool) -> Tensor:
        """Return a hard choice with straight-through gradients during BC."""
        if sample:
            return functional.gumbel_softmax(logits.float(), tau=1.0, hard=True, dim=-1).to(
                logits.dtype
            )
        ids = logits.float().argmax(dim=-1)
        return functional.one_hot(ids, num_classes=logits.shape[-1]).to(logits.dtype)

    def sequence(
        self,
        history: Tensor,
        turn_mask: Tensor,
        *,
        skill_ids: Tensor | None = None,
        sample: bool,
        validate_ids: bool = True,
    ) -> SkillSequence:
        """Select from causal history or evaluate stored RL choices."""
        if history.shape[:2] != turn_mask.shape:
            raise ValueError("causal skill history and turn mask must align")
        prior_logits = cast(Tensor, self.prior(history))
        if skill_ids is not None:
            if skill_ids.shape != turn_mask.shape:
                raise ValueError("stored skill ids must align with turns")
            if validate_ids:
                valid_ids = skill_ids[turn_mask]
                if torch.any((valid_ids < 0) | (valid_ids >= self.skill_tokens)):
                    raise ValueError("stored skill id is outside the actor codebook")
            safe_ids = skill_ids.clamp(min=0)
            choices = functional.one_hot(safe_ids, num_classes=self.skill_tokens).to(history.dtype)
        else:
            choices = self._one_hot_choice(prior_logits, sample=sample)
            safe_ids = choices.argmax(dim=-1)
        embeddings = choices @ self.codebook.weight.to(choices.dtype)
        return SkillSequence(
            prior_logits=prior_logits,
            ids=safe_ids,
            embeddings=embeddings,
        )

    def step(
        self,
        history: Tensor,
        *,
        sample: bool,
        generator: torch.Generator | None = None,
        uniform: Tensor | None = None,
    ) -> SkillStep:
        """Sample or greedily choose a causal skill for one visible turn."""
        if history.ndim != 2:
            raise ValueError("incremental skill history must have shape [batch, width]")
        logits = cast(Tensor, self.prior(history)).float()
        probabilities = torch.softmax(logits, dim=-1)
        if sample:
            if uniform is not None:
                if uniform.shape != logits.shape:
                    raise ValueError("skill sampling noise must match selector logits")
                tiny = torch.finfo(uniform.dtype).tiny
                gumbel = -torch.log(-torch.log(uniform.clamp_min(tiny)))
                ids = (logits + gumbel).argmax(dim=-1)
            else:
                ids = torch.multinomial(probabilities, 1, generator=generator).squeeze(-1)
        else:
            ids = logits.argmax(dim=-1)
        log_probabilities = torch.log_softmax(logits, dim=-1)
        selected = log_probabilities.gather(-1, ids[:, None]).squeeze(-1)
        entropy = -(probabilities * log_probabilities).sum(dim=-1)
        return SkillStep(
            ids=ids,
            log_probability=selected,
            entropy=entropy,
            embeddings=self.codebook(ids).to(history.dtype),
        )

__all__ = [
    "LatentSkillModel",
    "SkillSequence",
    "SkillStep",
]
