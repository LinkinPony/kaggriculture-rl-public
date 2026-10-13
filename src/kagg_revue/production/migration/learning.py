"""Microbatched teacher KL on the student's actual closed-loop observations."""

import time
from collections.abc import Callable

import torch
from torch import Tensor

from kagg_revue.learning.collection.population import script_games
from kagg_revue.learning.collection.sampling import Rollout
from kagg_revue.learning.optimization.learner import average_gradients, global_mean, weighted_mean
from kagg_revue.policy.spatial.model import Policy, log_probabilities
from kagg_revue.policy.spatial.work import WorkPolicy
from kagg_revue.production.migration.config import MigrationSettings
from kagg_revue.production.migration.objectives import distillation_rows
from kagg_revue.production.migration.runtime import GradientBuffers, GraphReplay, Replay


class Distiller:
    """Update only neural weights; the teacher and the student's table stay frozen."""

    def __init__(self, config: MigrationSettings, student: WorkPolicy, teacher: WorkPolicy) -> None:
        """Reuse production microbatching, CUDA Graphs and synchronized gradients."""
        self.config = config
        self.student = student
        self.teacher = teacher
        self.initial_update = True
        teacher.requires_grad_(False)
        if student.layout.network.time_prior:
            student.prior.requires_grad_(False)
        self.parameters = [
            parameter for parameter in student.parameters() if parameter.requires_grad
        ]
        self.optimizer = torch.optim.AdamW(
            self.parameters, lr=config.learning_rate, weight_decay=0, fused=True
        )
        self.gradients = GradientBuffers(self.parameters)
        settings = config.production
        torch.backends.cuda.matmul.allow_bf16_reduced_precision_reduction = (
            settings.bf16_reduced_precision_reduction
        )
        self.forward = self._replay(student)
        self.target = self._replay(teacher)

    def _replay(self, policy: Policy) -> Callable[[Tensor, Tensor, Tensor], Tensor]:
        settings = self.config.production
        if not settings.compile:
            return Replay(policy, settings.precision)
        world = len(settings.devices)
        games = settings.ppo.games_per_update // world
        rows = (2 * games - script_games(settings, games)) * policy.layout.decisions
        batch = settings.ppo.batch_rows // world
        micro = settings.ppo.microbatch_rows // world
        widths = {micro, batch % micro, rows % batch % micro} - {0}
        return GraphReplay(policy, widths, settings.precision)

    def remove_prior(self) -> None:
        """Recapture only student graphs while retaining neural optimizer state."""
        self.student.remove_prior()
        self.forward = self._replay(self.student)

    def check_likelihood(self, rollout: Rollout) -> float:
        """Measure frozen actor/learner drift without controlling the fade schedule."""
        settings = self.config.production
        micro = settings.ppo.microbatch_rows // len(settings.devices)
        indices = torch.randperm(len(rollout.steps), device=rollout.steps.device)[: micro * 4]
        divergence = torch.zeros((), device=rollout.steps.device)
        mass = global_mean(rollout.weights[indices].sum())
        for index in torch.split(indices, micro):
            actions = rollout.actions[index].long()
            logits = self.forward(rollout.observations[index], rollout.steps[index], actions)
            current = log_probabilities(logits, actions, settings.ppo.temperature)
            fields = self.student.field_weights(actions, rollout.steps[index])
            log_ratio = ((current.detach() - rollout.log_probabilities[index]) * fields).sum(-1)
            kl = torch.expm1(log_ratio) - log_ratio
            divergence += weighted_mean(kl, rollout.weights[index], mass)
        return float(global_mean(divergence))

    def update(self, rollout: Rollout) -> dict[str, float | int]:
        """Distill each compact tape in one pass with the existing global batch sizes."""
        started = time.perf_counter()
        settings = self.config.production
        world = len(settings.devices)
        batch = settings.ppo.batch_rows // world
        micro = settings.ppo.microbatch_rows // world
        indices = torch.randperm(len(rollout.steps), device=rollout.steps.device)
        loss_sum = torch.zeros((), device=rollout.steps.device)
        steps = 0
        for group in torch.split(indices, batch):
            self.gradients.zero()
            mass = global_mean(rollout.weights[group].sum())
            for micro_index, index in enumerate(torch.split(group, micro)):
                observations, times = rollout.observations[index], rollout.steps[index]
                actions = rollout.actions[index].long()
                initial = self.initial_update and steps == 0 and micro_index == 0
                if initial:
                    print(
                        {"device": str(observations.device), "phase": "teacher_forward"}, flush=True
                    )
                with torch.no_grad():
                    target = self.target(observations, times, actions)
                if initial:
                    print(
                        {"device": str(observations.device), "phase": "student_forward"}, flush=True
                    )
                logits = self.forward(observations, times, actions)
                fields = self.student.field_weights(actions, times)
                rows = distillation_rows(
                    logits, target, fields, self.config.distillation_temperature
                )
                loss = weighted_mean(rows, rollout.weights[index], mass)
                loss.backward()  # type: ignore[no-untyped-call]
                if initial:
                    print(
                        {"device": str(observations.device), "phase": "first_backward_complete"},
                        flush=True,
                    )
                loss_sum += loss.detach()
                del logits, target, rows, loss
            if self.initial_update and steps == 0:
                print(
                    {
                        "device": str(rollout.steps.device),
                        "phase": "first_gradient_sync",
                        "gradient_elements": sum(
                            p.grad.numel() for p in self.parameters if p.grad is not None
                        ),
                    },
                    flush=True,
                )
            average_gradients(self.parameters)
            torch.nn.utils.clip_grad_norm_(self.parameters, 1.0, error_if_nonfinite=True)
            self.optimizer.step()
            steps += 1
        torch.cuda.synchronize()
        self.initial_update = False
        return {
            "actor_steps": steps,
            "teacher_kl_loss": float(global_mean(loss_sum)) / steps,
            "learner_seconds": time.perf_counter() - started,
        }
