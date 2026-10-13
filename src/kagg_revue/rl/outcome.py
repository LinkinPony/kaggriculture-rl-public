"""Terminal outcome critic and policy losses for complete-match learning."""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

import torch
from torch import Tensor, nn
from torch.nn import functional

from kagg_revue.policy.model import PolicyOutput, TurnPolicyNet
from kagg_revue.policy.quantity import quantity_log_probability
from kagg_revue.policy.transformer import CrossBlock, RMSNorm


@dataclass(frozen=True)
class ActorCriticOutput:
    """Teacher-forced policy factors and outcome logits."""

    policy: PolicyOutput
    outcome_logits: Tensor


@dataclass(frozen=True)
class PpoLoss:
    """Differentiable objective and detached optimization diagnostics."""

    total: Tensor
    policy: Tensor
    value: Tensor
    entropy: Tensor
    approximate_kl: Tensor
    clip_fraction: Tensor
    policy_factors: Tensor
    value_factors: Tensor


class OutcomeHead(nn.Module):
    """W/D/L critic jointly training actor-visible causal representations."""

    def __init__(
        self,
        width: int,
        global_features: int,
        attention_heads: int,
        economic_features: int = 0,
        strategy_tokens: int = 0,
    ) -> None:
        """Create critic-owned adapters over shared causal actor representations."""
        super().__init__()
        if global_features < 1:
            raise ValueError("outcome critic needs at least one global feature")
        self.network = nn.Sequential(
            RMSNorm(width),
            nn.Linear(width, width, bias=False),
            nn.SiLU(),
            nn.Linear(width, 3),
        )
        self.global_encoder = nn.Sequential(
            nn.Linear(global_features, width),
            nn.SiLU(),
            nn.Linear(width, width, bias=False),
            RMSNorm(width),
        )
        self.scene_query = nn.Parameter(torch.empty(width).normal_(std=0.02))
        self.scene_cross = CrossBlock(width, attention_heads)
        self.context_network = nn.Sequential(
            RMSNorm(3 * width),
            nn.Linear(3 * width, width, bias=False),
            nn.SiLU(),
            nn.Linear(width, 3),
        )
        output = cast(nn.Linear, self.context_network[-1])
        nn.init.zeros_(output.weight)
        nn.init.zeros_(output.bias)
        if economic_features:
            self.economic_network: nn.Module | None = nn.Sequential(
                nn.Linear(economic_features, width),
                nn.SiLU(),
                nn.Linear(width, 3),
            )
            economic_output = cast(nn.Linear, self.economic_network[-1])
            nn.init.zeros_(economic_output.weight)
            nn.init.zeros_(economic_output.bias)
        else:
            self.economic_network = None
        if strategy_tokens:
            self.strategy_query: nn.Parameter | None = nn.Parameter(
                torch.empty(width).normal_(std=0.02)
            )
            self.strategy_cross: CrossBlock | None = CrossBlock(width, attention_heads)
            self.strategy_output: nn.Module | None = nn.Linear(width, 3)
            strategy_output = self.strategy_output
            nn.init.zeros_(strategy_output.weight)
            nn.init.zeros_(strategy_output.bias)
        else:
            self.register_parameter("strategy_query", None)
            self.strategy_cross = None
            self.strategy_output = None

    def forward(
        self,
        history: Tensor,
        global_features: Tensor,
        scene_memory: Tensor,
        scene_memory_mask: Tensor,
        economic_features: Tensor | None = None,
        strategy: Tensor | None = None,
    ) -> Tensor:
        """Predict W/D/L logits with gradients into actor-produced representations."""
        width = history.shape[-1]
        leading = history.shape[:-1]
        if global_features.shape[:-1] != leading:
            raise ValueError("critic history and global features must have matching batches")
        if scene_memory.shape[:-2] != leading or scene_memory.shape[-1] != width:
            raise ValueError("critic history and scene memory must have matching batches")
        if scene_memory_mask.shape != scene_memory.shape[:-1]:
            raise ValueError("critic scene memory and mask must have matching shapes")

        flat = history.reshape(-1, width)
        flat_scene = scene_memory.reshape(-1, scene_memory.shape[-2], width)
        flat_mask = scene_memory_mask.reshape(-1, scene_memory_mask.shape[-1])
        queries = self.scene_query.view(1, 1, width).expand(flat.shape[0], 1, width)
        scene_context = self.scene_cross(queries, flat_scene, flat_mask)[:, 0]
        global_context = self.global_encoder(global_features.reshape(flat.shape[0], -1))
        context = torch.cat((flat, global_context, scene_context), dim=-1)
        residual = self.context_network(context).view(*leading, 3)
        result = self.network(history) + residual
        if self.economic_network is not None:
            if economic_features is None or economic_features.shape[:-1] != leading:
                raise ValueError("critic economic features must match history batches")
            economic = self.economic_network(economic_features.reshape(flat.shape[0], -1)).view(
                *leading, 3
            )
            result = result + economic
        if self.strategy_cross is not None and self.strategy_output is not None:
            if self.strategy_query is None or strategy is None:
                raise ValueError("critic strategy state is absent")
            if strategy.shape[:-2] != leading or strategy.shape[-1] != width:
                raise ValueError("critic strategy state must match history batches")
            flat_strategy = strategy.reshape(-1, strategy.shape[-2], width)
            strategy_mask = torch.ones(
                flat_strategy.shape[:2], dtype=torch.bool, device=strategy.device
            )
            strategy_query = self.strategy_query.view(1, 1, width).expand(flat.shape[0], 1, width)
            strategy_context = self.strategy_cross(strategy_query, flat_strategy, strategy_mask)[
                :, 0
            ]
            strategy_residual = self.strategy_output(strategy_context).view(*leading, 3)
            result = result + strategy_residual
        return cast(Tensor, result)


class OutcomeActorCritic(nn.Module):
    """Joint actor plus a removable outcome head over shared representations."""

    def __init__(self, actor: TurnPolicyNet) -> None:
        """Attach a critic to one initialized actor."""
        super().__init__()
        self.actor = actor
        architecture = actor.architecture
        self.outcome = OutcomeHead(
            architecture.model_width,
            architecture.global_features,
            architecture.attention_heads,
            architecture.economic_turn_features,
            architecture.strategy_tokens,
        )

    def behavior_value(
        self,
        history: Tensor,
        global_features: Tensor,
        scene_memory: Tensor,
        scene_memory_mask: Tensor,
        economic_features: Tensor | None = None,
        strategy: Tensor | None = None,
    ) -> Tensor:
        """Evaluate the rollout critic from the current actor-visible context."""
        return outcome_values(
            self.outcome(
                history,
                global_features,
                scene_memory,
                scene_memory_mask,
                economic_features,
                strategy,
            )
        )

    def forward(
        self,
        board: Tensor,
        units: Tensor,
        global_features: Tensor,
        turn_facts: Tensor,
        turn_fact_mask: Tensor,
        prefix_facts: Tensor,
        candidate_facts: Tensor,
        actions: Tensor,
        quantities: Tensor,
        phases: Tensor,
        turn_mask: Tensor,
        decision_mask: Tensor,
        skill_ids: Tensor,
        economic_state: Tensor | None = None,
        *,
        actor_grad: bool = True,
        critic_actor_gradient: bool = True,
        validate_inputs: bool = True,
        action_head_noise: Tensor | None = None,
        action_head_noise_turn_mask: Tensor | None = None,
    ) -> ActorCriticOutput:
        """Evaluate stored causal trajectories under current parameters."""
        architecture = self.actor.architecture
        with torch.set_grad_enabled(actor_grad):
            encoding = self.actor.encode_sequence(
                board,
                units,
                global_features,
                actions,
                quantities,
                turn_mask,
                decision_mask,
                turn_facts if architecture.turn_fact_features else None,
                turn_fact_mask if architecture.turn_fact_features else None,
                economic_state if architecture.economic_feature_version else None,
            )
            skills = self.actor.select_sequence_skills(
                encoding,
                turn_mask,
                skill_ids=skill_ids,
                sample=False,
                validate_ids=validate_inputs,
            )
            policy = self.actor.decode_sequence(
                encoding,
                actions,
                quantities,
                phases,
                decision_mask,
                prefix_facts if architecture.prefix_fact_features else None,
                candidate_facts if architecture.candidate_fact_features else None,
                skills,
                economic_state if architecture.economic_feature_version else None,
                action_head_noise,
                action_head_noise_turn_mask,
            )
        batch, turns = encoding.history.shape[:2]
        scene_memory = encoding.memory[:, 1:].reshape(batch, turns, -1, architecture.model_width)
        scene_memory_mask = encoding.memory_mask[:, 1:].reshape(batch, turns, -1)
        critic_history = encoding.history if critic_actor_gradient else encoding.history.detach()
        critic_scene_memory = scene_memory if critic_actor_gradient else scene_memory.detach()
        critic_economic_features = (
            encoding.economic_features
            if critic_actor_gradient or encoding.economic_features is None
            else encoding.economic_features.detach()
        )
        critic_strategy = (
            encoding.strategy
            if critic_actor_gradient or encoding.strategy is None
            else encoding.strategy.detach()
        )
        return ActorCriticOutput(
            policy=policy,
            outcome_logits=self.outcome(
                critic_history,
                global_features,
                critic_scene_memory,
                scene_memory_mask,
                critic_economic_features,
                critic_strategy,
            ),
        )


def outcome_labels(outcomes: Tensor, *, validate: bool = True) -> Tensor:
    """Map seat-relative ``{-1, 0, 1}`` outcomes to class indices."""
    if validate and torch.any((outcomes < -1) | (outcomes > 1)):
        raise ValueError("outcomes must be loss, tie or win")
    if validate and outcomes.is_floating_point() and torch.any(outcomes != outcomes.round()):
        raise ValueError("outcomes must be integral")
    return outcomes.long() + 1


def outcome_values(logits: Tensor) -> Tensor:
    """Return expected seat-relative W/D/L value in ``[-1, 1]``."""
    if logits.shape[-1] != 3:
        raise ValueError("outcome logits must have loss, tie and win classes")
    probabilities = torch.softmax(logits.float(), dim=-1)
    return probabilities[..., 2] - probabilities[..., 0]


def monte_carlo_advantages(
    outcomes: Tensor,
    old_values: Tensor,
    turn_mask: Tensor,
    *,
    normalize: bool,
) -> tuple[Tensor, bool]:
    """Broadcast terminal outcomes and optionally normalize the full panel."""
    if old_values.shape != turn_mask.shape:
        raise ValueError("old values and turn mask must have matching shapes")
    if outcomes.shape != old_values.shape[:1]:
        raise ValueError("one outcome is required per trajectory")
    labels = outcome_labels(outcomes)
    actor_update = torch.unique(labels).numel() >= 2
    advantages = outcomes.float()[:, None] - old_values.float()
    valid = turn_mask.bool()
    if normalize and actor_update:
        selected = advantages[valid]
        if selected.numel() > 1:
            scale = selected.std(unbiased=False)
            if torch.isfinite(scale) and float(scale.item()) > 1e-6:
                advantages = (advantages - selected.mean()) / scale
    return advantages.masked_fill(~valid, 0.0), actor_update


def potential_rewards(outcomes: Tensor, values: Tensor, turn_mask: Tensor) -> Tensor:
    """Return undiscounted value-potential rewards with exact telescoping sums."""
    if values.shape != turn_mask.shape:
        raise ValueError("values and turn mask must have matching shapes")
    if outcomes.shape != values.shape[:1]:
        raise ValueError("one outcome is required per trajectory")
    valid = turn_mask.bool()
    next_values = torch.zeros_like(values)
    next_values[:, :-1] = torch.where(valid[:, 1:], values[:, 1:], torch.zeros_like(values[:, 1:]))
    rewards = (next_values - values).masked_fill(~valid, 0.0)
    lengths = valid.sum(dim=1)
    if torch.any(lengths < 1):
        raise ValueError("every trajectory needs at least one valid turn")
    terminal = lengths - 1
    rewards[torch.arange(values.shape[0], device=values.device), terminal] += outcomes.float()
    return rewards


def _policy_log_probability_terms(
    output: PolicyOutput,
    actions: Tensor,
    quantities: Tensor,
    legal_mask: Tensor,
    decision_mask: Tensor,
    has_quantity: Tensor,
    *,
    validate: bool = True,
) -> tuple[Tensor, Tensor, Tensor]:
    if legal_mask.shape != output.action_logits.shape:
        raise ValueError("legal mask and action logits must have matching shapes")
    if actions.shape != decision_mask.shape or quantities.shape != actions.shape:
        raise ValueError("stored decision tensors must have matching shapes")
    safe_actions = actions.clamp(min=0)
    selected_legal = legal_mask.gather(-1, safe_actions[..., None]).squeeze(-1)
    if validate and torch.any(decision_mask & ~selected_legal):
        raise ValueError("stored action is absent from its legal mask")
    safe_legal = legal_mask.bool().clone()
    safe_legal[..., 0] |= ~decision_mask
    logits = output.action_logits.float().masked_fill(~safe_legal, -torch.inf)
    log_probabilities = torch.log_softmax(logits, dim=-1)
    action_log_probability = log_probabilities.gather(-1, safe_actions[..., None]).squeeze(-1)
    quantity_log_probability_value = quantity_log_probability(
        output.quantity_logits,
        quantities,
    )
    quantity_mask = has_quantity[safe_actions] & decision_mask
    selected = action_log_probability + torch.where(
        quantity_mask,
        quantity_log_probability_value,
        torch.zeros_like(quantity_log_probability_value),
    )
    return selected, log_probabilities, safe_legal


def selected_log_probability(
    output: PolicyOutput,
    actions: Tensor,
    quantities: Tensor,
    legal_mask: Tensor,
    decision_mask: Tensor,
    has_quantity: Tensor,
    *,
    validate: bool = True,
) -> Tensor:
    """Evaluate sampled conditional factors without entropy bookkeeping."""
    selected, _, _ = _policy_log_probability_terms(
        output,
        actions,
        quantities,
        legal_mask,
        decision_mask,
        has_quantity,
        validate=validate,
    )
    return selected


def _selected_log_probability(
    output: PolicyOutput,
    actions: Tensor,
    quantities: Tensor,
    legal_mask: Tensor,
    decision_mask: Tensor,
    has_quantity: Tensor,
    *,
    validate: bool = True,
) -> tuple[Tensor, Tensor]:
    selected, log_probabilities, safe_legal = _policy_log_probability_terms(
        output,
        actions,
        quantities,
        legal_mask,
        decision_mask,
        has_quantity,
        validate=validate,
    )
    probabilities = log_probabilities.exp()
    finite_log_probabilities = log_probabilities.masked_fill(~safe_legal, 0.0)
    entropy = -(probabilities * finite_log_probabilities).sum(dim=-1)
    return selected, entropy


def selected_skill_log_probability(
    output: PolicyOutput,
    skill_ids: Tensor,
    turn_mask: Tensor,
    *,
    validate: bool = True,
) -> Tensor:
    """Evaluate stored causal latent choices under the current selector."""
    if skill_ids.shape != turn_mask.shape:
        raise ValueError("stored skill ids must align with turns")
    if output.skills is None:
        if validate and torch.any(skill_ids[turn_mask] != -1):
            raise ValueError("legacy actor received latent rollout choices")
        return torch.zeros_like(turn_mask, dtype=output.action_logits.dtype)
    logits = output.skills.prior_logits.float()
    if validate:
        valid_ids = skill_ids[turn_mask]
        if torch.any((valid_ids < 0) | (valid_ids >= logits.shape[-1])):
            raise ValueError("stored skill id is outside the current actor codebook")
    safe_ids = skill_ids.clamp(min=0)
    selected = torch.log_softmax(logits, dim=-1).gather(-1, safe_ids[..., None]).squeeze(-1)
    return selected.masked_fill(~turn_mask, 0.0)


def ppo_loss(
    output: ActorCriticOutput,
    actions: Tensor,
    quantities: Tensor,
    legal_mask: Tensor,
    old_log_probability: Tensor,
    skill_ids: Tensor,
    old_skill_log_probability: Tensor,
    advantages: Tensor,
    outcomes: Tensor,
    turn_mask: Tensor,
    decision_mask: Tensor,
    has_quantity: Tensor,
    clip_epsilon: float,
    value_loss_weight: float,
    entropy_weight: float,
    *,
    actor_update: bool,
    validate_inputs: bool = True,
) -> PpoLoss:
    """Compute conditional-factor PPO and all-prefix W/D/L classification."""
    if not 0.0 < clip_epsilon < 1.0:
        raise ValueError("PPO clip epsilon must be between zero and one")
    if old_log_probability.shape != actions.shape:
        raise ValueError("old log probability must align with stored actions")
    if advantages.shape != turn_mask.shape:
        raise ValueError("advantages must align with stored turns")
    new_log_probability, entropy_values = _selected_log_probability(
        output.policy,
        actions,
        quantities,
        legal_mask,
        decision_mask,
        has_quantity,
        validate=validate_inputs,
    )
    optimized_decisions = decision_mask & turn_mask[..., None]
    if validate_inputs and torch.any(optimized_decisions & ~torch.isfinite(old_log_probability)):
        raise ValueError("stored policy log probability is not finite")
    if validate_inputs and torch.any(optimized_decisions & ~torch.isfinite(new_log_probability)):
        raise ValueError("current policy log probability is not finite")
    if old_skill_log_probability.shape != turn_mask.shape:
        raise ValueError("old skill log probability must align with stored turns")
    new_skill_log_probability = selected_skill_log_probability(
        output.policy,
        skill_ids,
        turn_mask,
        validate=validate_inputs,
    )
    if validate_inputs and (
        torch.any(turn_mask & ~torch.isfinite(old_skill_log_probability))
        or torch.any(turn_mask & ~torch.isfinite(new_skill_log_probability))
    ):
        raise ValueError("latent selector log probability is not finite")
    action_log_ratio = new_log_probability - old_log_probability
    action_ratio = torch.exp(action_log_ratio)
    action_advantage = advantages[..., None]
    action_surrogate = torch.minimum(
        action_ratio * action_advantage,
        action_ratio.clamp(1.0 - clip_epsilon, 1.0 + clip_epsilon) * action_advantage,
    )
    skill_optimized = turn_mask if output.policy.skills is not None else torch.zeros_like(turn_mask)
    skill_log_ratio = new_skill_log_probability - old_skill_log_probability
    skill_ratio = torch.exp(skill_log_ratio)
    skill_surrogate = torch.minimum(
        skill_ratio * advantages,
        skill_ratio.clamp(1.0 - clip_epsilon, 1.0 + clip_epsilon) * advantages,
    )
    denominator = (optimized_decisions.sum() + skill_optimized.sum()).clamp_min(1)
    policy = (
        -(
            (action_surrogate * optimized_decisions).sum()
            + (skill_surrogate * skill_optimized).sum()
        )
        / denominator
        if actor_update
        else torch.zeros((), dtype=action_ratio.dtype, device=action_ratio.device)
    )
    action_entropy = (entropy_values * optimized_decisions).sum()
    if output.policy.skills is None:
        skill_entropy = torch.zeros((), dtype=action_ratio.dtype, device=action_ratio.device)
    else:
        skill_probabilities = torch.softmax(output.policy.skills.prior_logits.float(), dim=-1)
        skill_log_probabilities = torch.log_softmax(
            output.policy.skills.prior_logits.float(), dim=-1
        )
        skill_entropy_items = -(skill_probabilities * skill_log_probabilities).sum(dim=-1)
        skill_entropy = (skill_entropy_items * skill_optimized).sum()
    entropy = (action_entropy + skill_entropy) / denominator

    labels = outcome_labels(outcomes, validate=validate_inputs)[:, None].expand_as(turn_mask)
    value_items = functional.cross_entropy(
        output.outcome_logits.flatten(0, -2),
        labels.flatten(),
        reduction="none",
    ).view_as(turn_mask)
    value_factors = turn_mask.sum()
    value = (value_items * turn_mask).sum() / value_factors.clamp_min(1)
    entropy_objective = entropy_weight * entropy if actor_update else entropy.detach() * 0.0
    total = policy + value_loss_weight * value - entropy_objective

    detached_action_log_ratio = action_log_ratio.detach()
    detached_skill_log_ratio = skill_log_ratio.detach()
    action_kl = (
        ((torch.exp(detached_action_log_ratio) - 1.0) - detached_action_log_ratio)
        * optimized_decisions
    ).sum()
    skill_kl = (
        ((torch.exp(detached_skill_log_ratio) - 1.0) - detached_skill_log_ratio) * skill_optimized
    ).sum()
    approximate_kl = (action_kl + skill_kl) / denominator
    action_clipped = (
        (torch.abs(action_ratio.detach() - 1.0) > clip_epsilon) & optimized_decisions
    ).sum()
    skill_clipped = ((torch.abs(skill_ratio.detach() - 1.0) > clip_epsilon) & skill_optimized).sum()
    clip_fraction = (action_clipped + skill_clipped) / denominator
    return PpoLoss(
        total=total,
        policy=policy,
        value=value,
        entropy=entropy,
        approximate_kl=approximate_kl,
        clip_fraction=clip_fraction,
        policy_factors=denominator,
        value_factors=value_factors,
    )


__all__ = [
    "ActorCriticOutput",
    "OutcomeActorCritic",
    "OutcomeHead",
    "PpoLoss",
    "monte_carlo_advantages",
    "outcome_labels",
    "outcome_values",
    "potential_rewards",
    "ppo_loss",
    "selected_log_probability",
    "selected_skill_log_probability",
]
