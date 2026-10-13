"""Full-network preference updates on fresh, counterfactually compared root programs."""

import time
from typing import Any

import torch

from kagg_revue.learning.optimization.learner import average_gradients, global_mean
from kagg_revue.policy.spatial.model import log_probabilities
from kagg_revue.policy.spatial.work import WorkPolicy
from kagg_revue.production.branching.config import BranchSettings
from kagg_revue.production.branching.data import BranchTape
from kagg_revue.production.branching.objectives import preference_rows, preference_weights
from kagg_revue.production.migration.runtime import GradientBuffers, GraphReplay


class BranchLearner:
    """Use joint-program likelihood ratios so conditional action bundles stay together."""

    def __init__(self, config: BranchSettings, student: WorkPolicy) -> None:
        """Allocate fixed graph and gradient buffers for all trainable actor parameters."""
        self.config, self.student = config, student
        student.requires_grad_(True)
        self.parameters = list(student.parameters())
        self.optimizer = torch.optim.AdamW(
            self.parameters, lr=config.learning_rate, weight_decay=0, fused=True
        )
        self.gradients = GradientBuffers(self.parameters)
        width = config.microbatch_rows // len(config.production.devices)
        if width % config.candidates:
            raise ValueError(
                "learner microbatches must keep each root and all its candidates together"
            )
        self.root_width = width // config.candidates
        self.forward = GraphReplay(student, {width}, config.production.precision)

    def update(self, tape: BranchTape) -> dict[str, Any]:
        """Compare informative wins and losses only at roots with an improved alternative."""
        started = time.perf_counter()
        c, device = self.config, tape.steps.device
        signs, weights = preference_weights(tape.outcomes)
        indices = (weights.sum(-1) > 0).nonzero().flatten()
        normalization = global_mean(torch.tensor(float(len(indices)), device=device))
        if float(normalization) == 0:
            return {
                "actor_steps": 0,
                "learner_seconds": time.perf_counter() - started,
                "encoder_parameter_delta_l2": 0.0,
                "reason": "no_improved_root",
                "learning_rate": c.learning_rate,
            }
        encoder_before = {
            n: p.detach().clone()
            for n, p in self.student.named_parameters()
            if n.startswith("encoder.")
        }
        # Build root lookup once. Padding stays inside one bounded root-aligned graph bucket.
        count = len(indices)
        padded = max(
            self.root_width, ((count + self.root_width - 1) // self.root_width) * self.root_width
        )
        lookup = torch.zeros(padded, dtype=torch.long, device=device)
        lookup[:count] = indices
        valid = torch.arange(padded, device=device) < count
        total_loss = torch.zeros((), device=device)
        maximum_norm = 0.0
        for _ in range(c.learner_steps):
            self.gradients.zero()
            for start in range(0, padded, self.root_width):
                selected, mask = (
                    lookup[start : start + self.root_width],
                    valid[start : start + self.root_width],
                )
                observations = tape.observations[selected].repeat_interleave(c.candidates, 0)
                steps = tape.steps[selected].repeat_interleave(c.candidates)
                actions = tape.actions[selected].flatten(0, 1).long()
                logits = self.forward(observations, steps, actions)
                current = (
                    log_probabilities(logits, actions)
                    .sum(-1)
                    .reshape(self.root_width, c.candidates)
                )
                losses = preference_rows(
                    current,
                    tape.previous[selected],
                    signs[selected],
                    weights[selected],
                    c.preference_beta,
                )
                loss = (losses * mask).sum() / normalization
                loss.backward()  # type: ignore[no-untyped-call]
                total_loss += loss.detach()
            average_gradients(self.parameters)
            norm = torch.nn.utils.clip_grad_norm_(self.parameters, 1.0, error_if_nonfinite=True)
            maximum_norm = max(maximum_norm, float(norm))
            self.optimizer.step()
        delta = (
            torch.stack(
                [
                    (p.detach() - encoder_before[n]).square().sum()
                    for n, p in self.student.named_parameters()
                    if n in encoder_before
                ]
            )
            .sum()
            .sqrt()
        )
        total_loss = global_mean(total_loss)
        torch.cuda.synchronize(device)
        return {
            "actor_steps": c.learner_steps,
            "preference_loss": float(total_loss) / c.learner_steps,
            "useful_roots": round(float(normalization) * len(c.production.devices)),
            "encoder_parameter_delta_l2": float(delta),
            "maximum_gradient_norm": maximum_norm,
            "learner_seconds": time.perf_counter() - started,
            "learning_rate": c.learning_rate,
        }
