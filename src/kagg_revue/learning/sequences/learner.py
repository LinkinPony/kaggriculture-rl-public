"""Full-episode PPO with fresh causal state and KL early stopping."""

import time
from typing import Any

import torch
from torch import Tensor

from kagg_revue.learning.collection.sampling import Rollout
from kagg_revue.learning.optimization.learner import (
    Learner,
    advantage_moments,
    average_gradients,
    global_mean,
)
from kagg_revue.learning.optimization.prefix import prefix_credit
from kagg_revue.learning.optimization.protection import has_return_variation
from kagg_revue.learning.sequences.critic import MemoryCritic
from kagg_revue.learning.sequences.objectives import SequenceObjectives
from kagg_revue.learning.sequences.tape import SequenceTape
from kagg_revue.learning.settings import RuntimeSettings
from kagg_revue.policy.memory.policy import MemoryPolicy


class SequenceLearner(Learner):
    """Keep model parameters fixed while traversing each episode minibatch."""

    def __init__(
        self,
        settings: RuntimeSettings,
        policy: MemoryPolicy,
        critic: MemoryCritic,
        reference: MemoryPolicy | None = None,
    ) -> None:
        """Reuse independent Adam state and expose explicit-state training functions."""
        if settings.ppo.protection is not None:
            raise ValueError("recurrent learning requires explicit kl_control=early_stop")
        if (settings.ppo.reference_kl_weight > 0) != (reference is not None):
            raise ValueError("a reference policy is required exactly when its KL weight is set")
        super().__init__(
            settings.model_copy(update={"compile": False, "fused_loss": False}),
            policy,
            critic,
            None,
        )
        self.settings = settings
        self.actor = policy
        self.sequence_critic = critic
        self.reference = reference
        if reference is not None:
            reference.eval().requires_grad_(False)
        if settings.compile:
            from kagg_revue.policy.memory.compilation import compile_actor, compile_critic

            compile_actor(policy)
            compile_critic(critic)
            if reference is not None:
                compile_actor(reference)
        self.actor_sequence = policy.sequence
        self.critic_sequence = critic.sequence
        self.episodes = settings.sequence_games_per_rank
        self.objectives = SequenceObjectives(settings.ppo, settings.compile, self.device)

    @torch.no_grad()
    def targets(self, tape: SequenceTape) -> tuple[Tensor, Tensor]:
        """Freeze pre-update baselines using complete prefixes under one critic version."""
        values = torch.empty_like(tape.returns)
        credits = torch.empty_like(tape.behavior)
        for indices in tape.batches(self.episodes):
            present = indices[indices >= 0]
            count = len(present)
            state = self.sequence_critic.memory.temporal.empty(len(indices), self.device)
            for chunk in tape.chunks(indices):
                value, prefixes, state = self.critic_sequence(
                    chunk.observations,
                    chunk.steps,
                    state,
                    chunk.actions,
                    chunk.fields,
                )
                length = chunk.section.stop - chunk.section.start
                values[chunk.section, present] = value[:length, :count]
                credit = prefix_credit(
                    prefixes.flatten(0, 1),
                    chunk.fields.flatten(0, 1),
                    chunk.returns.flatten(),
                    self.settings.ppo.prefix_trace_lambda,
                )
                credits[chunk.section, present] = credit.reshape_as(prefixes)[:length, :count]
        moments = advantage_moments((tape.returns - values).flatten(), tape.weights.flatten())
        scale = (moments[1] - moments[0].square()).clamp_min(1e-8).sqrt()
        return credits / scale, scale

    def update(self, rollout: Rollout, *, actor_training: bool = True) -> dict[str, Any]:
        """Optimize terminal outcomes without shuffling or truncating observations."""
        options = self.settings.ppo
        if options.cash_weight or options.win_weight != 1:
            raise ValueError("recurrent learning requires WDL with optional bounded cash margin")
        tape = SequenceTape(rollout, self.actor, self.settings.sequence_chunk_turns)
        temperature = options.temperature if rollout.temperature is None else rollout.temperature
        if temperature <= 0:
            raise ValueError("recurrent PPO needs a stochastic behavior policy")
        started = time.perf_counter()
        constant = actor_training and not has_return_variation(rollout.returns)
        actor_enabled = actor_training and not constant
        autocast: dict[str, Any] = dict(
            device_type=self.device.type,
            dtype=torch.bfloat16,
            enabled=self.device.type == "cuda" and self.settings.precision == "bf16",
        )
        with torch.autocast(**autocast):
            credits, scale = self.targets(tape)
        credit_seconds = time.perf_counter() - started
        actor_steps = critic_steps = 0
        maximum_kl = 0.0
        reference_kls: list[float] = []
        losses = torch.zeros(3, device=self.device)
        for _ in range(options.epochs):
            for indices in tape.batches(self.episodes, shuffle=True):
                self.actor_optimizer.zero_grad(set_to_none=True)
                self.critic_optimizer.zero_grad(set_to_none=True)
                actor_state = self.actor.memory.temporal.empty(len(indices), self.device)
                critic_state = self.sequence_critic.memory.temporal.empty(len(indices), self.device)
                reference_state = (
                    None
                    if self.reference is None
                    else self.reference.memory.temporal.empty(len(indices), self.device)
                )
                mass = global_mean(tape.mass(indices))
                kl_total = torch.zeros((), device=self.device)
                reference_total = torch.zeros((), device=self.device)
                losses.zero_()
                for chunk in tape.chunks(indices):
                    weights, fields = chunk.weights.flatten(), chunk.fields.flatten(0, 1)
                    with torch.autocast(**autocast):
                        if actor_enabled:
                            _, logits, actor_state = self.actor_sequence(
                                chunk.observations,
                                chunk.steps,
                                actor_state,
                                chunk.actions,
                            )
                            actor_loss, kl = self.objectives.actor(
                                logits.flatten(0, 1),
                                chunk.actions.flatten(0, 1),
                                chunk.behavior.flatten(0, 1),
                                tape.select(credits, chunk.section, indices).flatten(0, 1),
                                fields,
                                weights,
                                mass,
                                temperature,
                            )
                            kl_total += kl.detach()
                            if self.reference is not None:
                                assert reference_state is not None
                                with torch.no_grad():
                                    _, reference_logits, reference_state = self.reference.sequence(
                                        chunk.observations,
                                        chunk.steps,
                                        reference_state,
                                        chunk.actions,
                                    )
                                anchor = self.objectives.anchor(
                                    logits.flatten(0, 1),
                                    reference_logits.flatten(0, 1),
                                    fields,
                                    weights,
                                    mass,
                                    temperature,
                                )
                                actor_loss = actor_loss + options.reference_kl_weight * anchor
                                reference_total += anchor.detach()
                        value, prefixes, critic_state = self.critic_sequence(
                            chunk.observations,
                            chunk.steps,
                            critic_state,
                            chunk.actions,
                            chunk.fields,
                        )
                        combined = self.objectives.value(
                            value.flatten(),
                            prefixes.flatten(0, 1),
                            chunk.returns.flatten(),
                            fields,
                            weights,
                            mass,
                        )
                    if actor_enabled:
                        actor_loss.backward()  # type: ignore[no-untyped-call]
                    combined[0].backward()  # type: ignore[no-untyped-call]
                    losses += combined.detach()
                if actor_enabled:
                    measured = float(global_mean(kl_total))
                    maximum_kl = max(maximum_kl, measured)
                    if self.reference is not None:
                        reference_kls.append(float(global_mean(reference_total)))
                    actor_enabled = measured <= options.target_kl
                    if actor_enabled:
                        average_gradients(list(self.actor.parameters()))
                        torch.nn.utils.clip_grad_norm_(
                            self.actor.parameters(), 1.0, error_if_nonfinite=True
                        )
                        self.actor_optimizer.step()
                        actor_steps += 1
                average_gradients(list(self.sequence_critic.parameters()))
                torch.nn.utils.clip_grad_norm_(
                    self.sequence_critic.parameters(), 1.0, error_if_nonfinite=True
                )
                self.critic_optimizer.step()
                critic_steps += 1
        values = global_mean(losses).tolist()
        if self.device.type == "cuda":
            torch.cuda.synchronize(self.device)
        return {
            "learner_seconds": time.perf_counter() - started,
            "credit_seconds": credit_seconds,
            "protection_seconds": 0.0,
            "actor_steps": actor_steps,
            "critic_steps": critic_steps,
            "maximum_prefix_kl": maximum_kl,
            "actor_early_stop": actor_training and not actor_enabled,
            "critic_warmup": not actor_training,
            "actor_skipped_constant_returns": constant,
            "attempted_actor_steps": actor_steps,
            "rejected_actor_steps": 0,
            "kl_control": "early_stop",
            "target_kl": options.target_kl,
            "temperature": temperature,
            "actor_learning_rate": self.actor_optimizer.param_groups[0]["lr"],
            "critic_learning_rate": self.critic_optimizer.param_groups[0]["lr"],
            "learning_rate_warmup_updates": options.learning_rate_warmup_updates,
            "value_loss": values[0],
            "state_value_loss": values[1],
            "prefix_value_loss": values[2],
            "bc_retention_loss": 0.0,
            "reference_kl_weight": options.reference_kl_weight,
            "reference_kl": sum(reference_kls) / len(reference_kls) if reference_kls else 0.0,
            "advantage_scale": float(scale),
            "sequence_chunk_turns": tape.chunk_turns,
            "minibatch_trajectories": self.episodes,
            "memory_turns": self.actor.layout.network.memory_turns,
        }
