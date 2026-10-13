"""Synchronized direct-outcome PPO and BC retention on compact macro tapes."""

import math
import time
from collections.abc import Callable
from functools import partial
from typing import Any

import torch
import torch.distributed as dist
from torch import Tensor
from torch.nn import functional as F

from kagg_revue.learning.collection.sampling import Rollout
from kagg_revue.learning.optimization.compilation import compile_learner
from kagg_revue.learning.optimization.kernels import PrefixLosses
from kagg_revue.learning.optimization.objectives import surrogate_rows
from kagg_revue.learning.optimization.prefix import (
    PrefixCritic,
    prefix_credit,
    prefix_surrogate,
    prefix_value_rows,
)
from kagg_revue.learning.optimization.protection import guarded_step, has_return_variation
from kagg_revue.learning.optimization.returns import generalized_returns
from kagg_revue.learning.settings import RuntimeSettings
from kagg_revue.policy.spatial.model import (
    Critic,
    Policy,
    imitation_loss,
    log_probabilities,
    scale_logits,
)


def average_gradients(parameters: list[torch.nn.Parameter]) -> None:
    """Use one coalesced collective per logical optimizer step."""
    if not dist.is_initialized():
        return
    gradients = [parameter.grad for parameter in parameters if parameter.grad is not None]
    flat = torch.cat([gradient.flatten() for gradient in gradients])
    dist.all_reduce(flat)
    flat.div_(dist.get_world_size())
    offset = 0
    for gradient in gradients:
        gradient.copy_(flat[offset : offset + gradient.numel()].view_as(gradient))
        offset += gradient.numel()


def global_mean(value: Tensor) -> Tensor:
    """Average an equal-sized rank contribution."""
    result = value.detach().clone()
    if dist.is_initialized():
        dist.all_reduce(result)
        result.div_(dist.get_world_size())
    return result


def weighted_mean(values: Tensor, weights: Tensor, mass: Tensor) -> Tensor:
    """Normalize row losses by the global mean per-rank minibatch mass."""
    return (values * weights).sum() / mass


def advantage_moments(values: Tensor, weights: Tensor) -> Tensor:
    """Compute episode-balanced moments jointly across learner ranks."""
    totals = global_mean(
        torch.stack(((values * weights).sum(), (values.square() * weights).sum(), weights.sum()))
    )
    return totals[:2] / totals[2]


class Learner:
    """Independent actor/critic optimizers and rank-synchronized full-game updates."""

    def __init__(
        self,
        settings: RuntimeSettings,
        policy: Policy,
        critic: Critic,
        rehearsal: tuple[Tensor, Tensor, Tensor] | None,
    ) -> None:
        """Bind the exact production profile and a compact BC rehearsal shard."""
        self.settings = settings
        self.policy = policy
        self.critic = critic
        self.rehearsal = rehearsal
        self.device = next(policy.parameters()).device
        self.world = dist.get_world_size() if dist.is_initialized() else 1
        self.actor_optimizer = torch.optim.AdamW(
            policy.parameters(),
            lr=settings.ppo.actor_learning_rate,
            weight_decay=0.0,
            fused=self.device.type == "cuda",
        )
        self.critic_optimizer = torch.optim.AdamW(
            critic.parameters(),
            lr=settings.ppo.critic_learning_rate,
            weight_decay=0.0,
            fused=self.device.type == "cuda",
        )
        self.forward: Callable[[Tensor, Tensor, Tensor], Tensor] = policy
        self.value: Callable[[Tensor], Tensor] = critic
        self.prefix_value: Callable[[Tensor, Tensor, Tensor], tuple[Tensor, Tensor]] | None = None
        if isinstance(critic, PrefixCritic):
            self.prefix_value = critic.prefixes
        self.losses = None
        if settings.fused_loss:
            if not isinstance(critic, PrefixCritic) or settings.ppo.ratio_scope != "prefix":
                raise ValueError("fused objectives require the prefix critic and prefix ratios")
            self.losses = PrefixLosses(policy, critic, settings.ppo)
            if self.losses.compact:
                self.prefix_value = partial(critic.prefixes, compact=True)
        if settings.compile:
            compile_learner(self)

    def restore_optimizers(self, actor: dict[str, Any], critic: dict[str, Any]) -> None:
        """Restore Adam moments and steps, honoring configured constant learning rates."""
        self.actor_optimizer.load_state_dict(actor)
        self.critic_optimizer.load_state_dict(critic)
        settings = self.settings.ppo
        if settings.protection is None or settings.protection.learning_rate_decay == 1:
            for optimizer, rate in (
                (self.actor_optimizer, settings.actor_learning_rate),
                (self.critic_optimizer, settings.critic_learning_rate),
            ):
                for group in optimizer.param_groups:
                    group["lr"] = rate
                    group.pop("guard_lr_scale", None)

    def schedule(self, update: int) -> None:
        """Set both actual learning rates from the absolute PPO update before learning."""
        for optimizer, rate in (
            (self.actor_optimizer, self.settings.ppo.actor_rate_at(update)),
            (self.critic_optimizer, self.settings.ppo.critic_rate_at(update)),
        ):
            for group in optimizer.param_groups:
                group["lr"] = rate

    def update(self, rollout: Rollout, *, actor_training: bool = True) -> dict[str, Any]:
        """Accumulate bounded microbatches without changing global optimizer semantics."""
        settings = self.settings.ppo
        temperature = settings.temperature if rollout.temperature is None else rollout.temperature
        if actor_training and temperature <= 0:
            raise ValueError("deterministic rollouts support critic warmup, not PPO actor updates")
        protection = settings.protection
        constant_returns = (
            actor_training
            and protection is not None
            and protection.skip_constant_returns
            and not has_return_variation(rollout.returns)
        )
        actor_requested = actor_training
        actor_training = actor_training and not constant_returns
        rows = len(rollout.steps)
        batch_rows = settings.batch_rows // self.world
        micro_rows = min(batch_rows, settings.microbatch_rows // self.world)
        policy_parameters = list(self.policy.parameters())
        critic_parameters = list(self.critic.parameters())
        started = time.perf_counter()
        credits = None
        with (
            torch.no_grad(),
            torch.autocast(
                self.device.type,
                dtype=torch.bfloat16,
                enabled=self.device.type == "cuda" and self.settings.precision == "bf16",
            ),
        ):
            values = torch.empty_like(rollout.returns)
            if self.prefix_value is not None and actor_training:
                credits = torch.empty_like(rollout.log_probabilities)
            for start in range(0, rows, micro_rows):
                section = slice(start, start + micro_rows)
                observations = rollout.observations[section]
                if credits is None:
                    values[section] = self.value(observations).float()
                else:
                    assert self.prefix_value is not None
                    actions = rollout.actions[section].long()
                    fields = self.policy.field_weights(
                        actions, rollout.steps[section], observations
                    )
                    state, prefixes = self.prefix_value(observations, actions, fields)
                    values[section] = state
                    credits[section] = prefix_credit(
                        prefixes, fields, rollout.returns[section], settings.prefix_trace_lambda
                    )
        targets = rollout.returns
        if settings.gamma != 1 or settings.gae_lambda != 1:
            targets = generalized_returns(
                values,
                rollout.returns,
                rollout.steps,
                self.policy.layout.decisions,
                settings.gamma,
                settings.gae_lambda,
            )
            if credits is not None:
                for start in range(0, rows, micro_rows):
                    section = slice(start, start + micro_rows)
                    fields = self.policy.field_weights(
                        rollout.actions[section].long(),
                        rollout.steps[section],
                        rollout.observations[section],
                    )
                    # Full within-turn traces: replace only the future-turn target.
                    credits[section].add_(
                        (targets[section] - rollout.returns[section])[:, None] * fields
                    )
        advantages = targets - values
        moments = advantage_moments(advantages, rollout.weights)
        scale = (moments[1] - moments[0].square()).clamp_min(1e-8).sqrt()
        advantages = (advantages - moments[0]) / scale
        if credits is not None:
            # Use one common scale without subtracting action-dependent means
            # or dividing by the sampled number of active fields.
            credits.div_(scale)
        if self.device.type == "cuda":
            torch.cuda.synchronize(self.device)
        credit_seconds = time.perf_counter() - started
        actor_steps = critic_steps = 0
        rejected_steps = attempted_steps = 0
        accepted_kl_max = protection_seconds = 0.0
        kl_max = final_value_loss = final_bc_loss = final_state_loss = final_prefix_loss = 0.0
        actor_enabled = actor_training
        for _ in range(settings.epochs):
            permutation = torch.randperm(rows, device=self.device)
            for indices in torch.split(permutation, batch_rows):
                mass = global_mean(rollout.weights[indices].sum())
                self.actor_optimizer.zero_grad(set_to_none=True)
                self.critic_optimizer.zero_grad(set_to_none=True)
                kl_sum = torch.zeros((), device=self.device)
                value_sum = torch.zeros((), device=self.device)
                state_sum = torch.zeros((), device=self.device)
                prefix_sum = torch.zeros((), device=self.device)
                for micro in torch.split(indices, micro_rows):
                    weights = rollout.weights[micro]
                    observations = rollout.observations[micro]
                    actions = rollout.actions[micro].long()
                    if self.losses is None:
                        fields = self.policy.field_weights(
                            actions, rollout.steps[micro], observations
                        )
                    with torch.autocast(
                        self.device.type,
                        dtype=torch.bfloat16,
                        enabled=self.device.type == "cuda" and self.settings.precision == "bf16",
                    ):
                        if actor_enabled and self.losses is not None:
                            assert credits is not None
                            actor_loss, divergence = self.losses.actor(
                                observations,
                                rollout.steps[micro],
                                actions,
                                rollout.log_probabilities[micro],
                                credits[micro],
                                weights,
                                mass,
                                temperature,
                            )
                            kl_sum += divergence.detach()
                        elif actor_enabled:
                            logits = self.forward(observations, rollout.steps[micro], actions)
                            logits = scale_logits(logits, temperature)
                            probabilities = log_probabilities(logits, actions)
                            field_mass = fields.sum(-1).clamp_min(1)
                            log_ratio = probabilities - rollout.log_probabilities[micro]
                            joint = settings.ratio_scope == "plan"
                            if credits is None:
                                gain, kl = surrogate_rows(
                                    log_ratio, fields, advantages[micro], settings.clip, joint=joint
                                )
                            else:
                                gain, kl = prefix_surrogate(
                                    log_ratio, fields, credits[micro], settings.clip
                                )
                            kl_sum += weighted_mean(kl, weights, mass).detach()
                            actor_loss = -weighted_mean(gain, weights, mass)
                            if settings.entropy_weight:
                                entropy_rows = (
                                    -(F.softmax(logits, -1) * F.log_softmax(logits, -1))
                                    .sum(-1)
                                    .mul(fields)
                                    .sum(-1)
                                )
                                if not joint and credits is None:
                                    entropy_rows = entropy_rows / field_mass
                                actor_loss -= settings.entropy_weight * weighted_mean(
                                    entropy_rows, weights, mass
                                )
                        if self.losses is not None:
                            value_loss, state_loss, prefix_loss = self.losses.value(
                                observations,
                                rollout.steps[micro],
                                actions,
                                targets[micro],
                                weights,
                                mass,
                            )
                            state_sum += state_loss.detach()
                            prefix_sum += prefix_loss.detach()
                        elif self.prefix_value is None:
                            predictions = self.value(observations).float()
                            value_loss = weighted_mean(
                                F.smooth_l1_loss(predictions, targets[micro], reduction="none"),
                                weights,
                                mass,
                            )
                        else:
                            predictions, prefixes = self.prefix_value(observations, actions, fields)
                            losses, state_losses, prefix_losses = prefix_value_rows(
                                predictions,
                                prefixes,
                                targets[micro],
                                fields,
                                settings.prefix_value_weight,
                            )
                            value_loss = weighted_mean(losses, weights, mass)
                            state_sum += weighted_mean(state_losses, weights, mass).detach()
                            prefix_sum += weighted_mean(prefix_losses, weights, mass).detach()
                    if actor_enabled:
                        actor_loss.backward()  # type: ignore[no-untyped-call]
                    value_loss.backward()  # type: ignore[no-untyped-call]
                    value_sum += value_loss.detach()
                if actor_enabled:
                    measured_kl = float(global_mean(kl_sum))
                    if not math.isfinite(measured_kl):
                        raise FloatingPointError("nonfinite PPO KL before optimizer step")
                    kl_max = max(kl_max, measured_kl)
                    actor_enabled = measured_kl <= settings.target_kl
                    if actor_enabled and settings.bc_weight:
                        if self.rehearsal is None:
                            raise ValueError("enabled BC retention requires a rehearsal shard")
                        bc_observations, bc_actions, bc_steps = self.rehearsal
                        bc_indices = torch.randint(
                            len(bc_steps), (settings.bc_rows // self.world,), device=self.device
                        )
                        bc_sum = torch.zeros((), device=self.device)
                        for micro in torch.split(bc_indices, micro_rows):
                            weight = len(micro) / len(bc_indices)
                            with torch.autocast(
                                self.device.type,
                                dtype=torch.bfloat16,
                                enabled=self.device.type == "cuda"
                                and self.settings.precision == "bf16",
                            ):
                                bc_logits = self.forward(
                                    bc_observations[micro], bc_steps[micro], bc_actions[micro]
                                )
                                bc_loss = imitation_loss(
                                    bc_logits,
                                    bc_actions[micro],
                                    self.policy.field_weights(bc_actions[micro], bc_steps[micro]),
                                )
                            (settings.bc_weight * weight * bc_loss).backward()  # type: ignore[no-untyped-call]
                            bc_sum += weight * bc_loss.detach()
                        final_bc_loss = float(bc_sum)
                    if actor_enabled:
                        average_gradients(policy_parameters)
                        torch.nn.utils.clip_grad_norm_(
                            policy_parameters, 1.0, error_if_nonfinite=True
                        )
                        if protection is None:
                            self.actor_optimizer.step()
                            actor_steps += 1
                        else:
                            guard_started = time.perf_counter()
                            result = guarded_step(
                                self.actor_optimizer,
                                partial(
                                    self._measure_kl, rollout, indices, micro_rows, temperature
                                ),
                                maximum=settings.target_kl,
                                attempts=protection.backtrack_attempts,
                                decay=protection.learning_rate_decay,
                            )
                            protection_seconds += time.perf_counter() - guard_started
                            attempted_steps += result.attempts
                            rejected_steps += result.rejections
                            if result.accepted:
                                actor_steps += 1
                                accepted_kl_max = max(accepted_kl_max, result.divergence)
                            else:
                                actor_enabled = False
                    else:
                        self.actor_optimizer.zero_grad(set_to_none=True)
                average_gradients(critic_parameters)
                torch.nn.utils.clip_grad_norm_(critic_parameters, 1.0, error_if_nonfinite=True)
                self.critic_optimizer.step()
                critic_steps += 1
                summaries = global_mean(torch.stack((value_sum, state_sum, prefix_sum)))
                final_value_loss, final_state_loss, final_prefix_loss = summaries.tolist()
        if self.device.type == "cuda":
            torch.cuda.synchronize(self.device)
        return {
            "learner_seconds": time.perf_counter() - started,
            "credit_seconds": credit_seconds,
            "actor_steps": actor_steps,
            "critic_steps": critic_steps,
            f"maximum_{settings.ratio_scope}_kl": kl_max,
            "actor_early_stop": actor_training and not actor_enabled,
            "critic_warmup": not actor_requested,
            "actor_skipped_constant_returns": constant_returns,
            "attempted_actor_steps": attempted_steps if protection is not None else actor_steps,
            "rejected_actor_steps": rejected_steps,
            "maximum_accepted_post_step_kl": accepted_kl_max,
            "protection_seconds": protection_seconds,
            "temperature": temperature,
            "actor_learning_rate": self.actor_optimizer.param_groups[0]["lr"],
            "critic_learning_rate": self.critic_optimizer.param_groups[0]["lr"],
            "gamma": settings.gamma,
            "gae_lambda": settings.gae_lambda,
            "learning_rate_warmup_updates": settings.learning_rate_warmup_updates,
            "training_rows": rows,
            "value_loss": final_value_loss,
            "state_value_loss": final_state_loss,
            "prefix_value_loss": final_prefix_loss,
            "bc_retention_loss": final_bc_loss,
            "advantage_scale": float(scale),
        }

    @torch.no_grad()
    def _measure_kl(
        self, rollout: Rollout, indices: Tensor, micro_rows: int, temperature: float
    ) -> float:
        """Recheck the actual step on its complete minibatch against behavior likelihoods."""
        mass = global_mean(rollout.weights[indices].sum())
        total = torch.zeros((), device=self.device)
        for micro in torch.split(indices, micro_rows):
            actions = rollout.actions[micro].long()
            with torch.autocast(
                self.device.type,
                dtype=torch.bfloat16,
                enabled=self.device.type == "cuda" and self.settings.precision == "bf16",
            ):
                if self.losses is not None:
                    total += self.losses.divergence(
                        rollout.observations[micro],
                        rollout.steps[micro],
                        actions,
                        rollout.log_probabilities[micro],
                        rollout.weights[micro],
                        mass,
                        temperature,
                    )
                    continue
                fields = self.policy.field_weights(
                    actions, rollout.steps[micro], rollout.observations[micro]
                )
                logits = self.forward(rollout.observations[micro], rollout.steps[micro], actions)
                log_ratio = log_probabilities(logits, actions, temperature)
                log_ratio = log_ratio - rollout.log_probabilities[micro]
                if self.settings.ppo.ratio_scope == "prefix":
                    _, kl = prefix_surrogate(
                        log_ratio, fields, torch.zeros_like(log_ratio), self.settings.ppo.clip
                    )
                else:
                    _, kl = surrogate_rows(
                        log_ratio,
                        fields,
                        torch.zeros_like(rollout.returns[micro]),
                        self.settings.ppo.clip,
                        joint=self.settings.ppo.ratio_scope == "plan",
                    )
                total += weighted_mean(kl, rollout.weights[micro], mass)
        measured = float(global_mean(total))
        if not math.isfinite(measured):
            raise FloatingPointError("nonfinite PPO KL after optimizer step")
        return measured
