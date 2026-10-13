"""Configurable supervised likelihood with exact grounded causal field support."""

from typing import Any

import torch
import torch.distributed as dist
from torch import Tensor

from kagg_revue.datasets.demonstrations.loading import Dataset
from kagg_revue.learning.distributed import rank_world
from kagg_revue.learning.optimization.learner import average_gradients
from kagg_revue.learning.pretraining.config import GroupedLoss
from kagg_revue.learning.pretraining.objectives import SupervisedLoss
from kagg_revue.learning.pretraining.statistics import DOMAINS, field_totals
from kagg_revue.learning.settings import RuntimeSettings
from kagg_revue.policy.grounded.typed import TypedGroundedPolicy
from kagg_revue.policy.spatial.model import Policy, log_probabilities


class Optimizer:
    """Keep demonstration optimization separate from all subsequent PPO state."""

    def __init__(
        self,
        actor: Policy,
        settings: RuntimeSettings,
        learning_rate: float,
        *,
        loss: GroupedLoss | None = None,
        joint_learning_rate: float | None = None,
    ) -> None:
        """Use one fixed-width forward graph for training and held-out likelihood."""
        self.actor = actor
        self.device = next(actor.parameters()).device
        if loss is not None and not isinstance(actor, TypedGroundedPolicy):
            raise ValueError("grouped BC loss requires a single-turn typed actor")
        self.supervised_loss = SupervisedLoss(loss, actor.layout.observation.units)
        self.bf16 = settings.precision == "bf16" and self.device.type == "cuda"
        if self.device.type == "cuda":
            # Apply the evaluation precision policy before either rank compiles BC.
            # Otherwise rank zero changes this global flag at its first control panel.
            torch.backends.cuda.matmul.allow_bf16_reduced_precision_reduction = (
                settings.bf16_reduced_precision_reduction
            )
        self.forward = torch.compile(actor, dynamic=False) if settings.compile else actor
        named = list(actor.named_parameters())
        groups: list[dict[str, Any]] = [
            {"params": [p for name, p in named if not name.startswith("joint.")]}
        ]
        joint = [p for name, p in named if name.startswith("joint.")]
        if joint:
            groups.append({"params": joint, "lr": joint_learning_rate or learning_rate})
        self.optimizer = torch.optim.AdamW(
            groups, lr=learning_rate, weight_decay=0.0, fused=self.device.type == "cuda"
        )

    @torch.no_grad()
    def loss_scales(
        self, observations: Tensor, actions: Tensor, turns: Tensor, eligible: Tensor
    ) -> Tensor:
        """Prepare denominators without a neural forward or a retained gradient graph."""
        if self.supervised_loss.config is None:
            return observations.new_zeros(len(DOMAINS), dtype=torch.float32)
        fields = self.actor.field_weights(actions, turns, observations)
        return self.supervised_loss.scales(fields, eligible)

    def shard(
        self,
        dataset: Dataset,
        index: int,
        batch_rows: int,
        seed: tuple[int, ...] | None,
    ) -> dict[str, Any]:
        """Optimize sampled training rows or enumerate held-out rows; ignore padding."""
        training = seed is not None
        rank, world = rank_world()
        local_rows = batch_rows // world
        self.actor.train(training)
        total, rows, steps = 0.0, 0, 0
        totals = torch.zeros(len(DOMAINS) * 3, device=self.device)
        with torch.set_grad_enabled(training):
            for observations, actions, turns, count in dataset.batches(
                index, batch_rows, self.device, seed, rank=rank, world=world
            ):
                if training:
                    self.optimizer.zero_grad(set_to_none=True)
                mask = torch.arange(local_rows, device=self.device) + rank * local_rows < count
                scales = self.loss_scales(observations, actions, turns, mask)
                with torch.autocast(self.device.type, dtype=torch.bfloat16, enabled=self.bf16):
                    logits = self.forward(observations, turns, actions)
                    weights = self.actor.field_weights(actions, turns, observations)
                    likelihood = log_probabilities(logits, actions)
                    loss = self.supervised_loss(
                        likelihood, weights, mask, likelihood.new_tensor(count / world), scales
                    )
                if self.supervised_loss.config is not None:
                    assert isinstance(self.actor, TypedGroundedPolicy)
                    selected = self.actor.semantic_fields
                    totals += field_totals(
                        logits[:, selected],
                        actions[:, selected],
                        likelihood[:, selected],
                        weights[:, selected] * mask[:, None],
                        self.actor.layout.observation.units,
                    )
                statistics = torch.stack(
                    (
                        loss.detach(),
                        likelihood.detach().masked_fill((weights == 0) | ~mask[:, None], 0).amin(),
                    )
                )
                if world > 1:
                    dist.all_reduce(statistics[:1])
                    statistics[0] /= world
                    dist.all_reduce(statistics[1:], op=dist.ReduceOp.MIN)
                value, minimum = statistics.tolist()
                if not 0 <= value < 1e6 or minimum < -1e8:
                    raise ValueError("demonstration loss is nonfinite or outside policy support")
                if training:
                    loss.backward()  # type: ignore[no-untyped-call]
                    average_gradients(list(self.actor.parameters()))
                    torch.nn.utils.clip_grad_norm_(
                        self.actor.parameters(), 1.0, error_if_nonfinite=True
                    )
                    self.optimizer.step()
                    steps += 1
                total += value * count
                rows += count
        result: dict[str, Any] = {"loss_sum": total, "rows": rows, "optimizer_steps": steps}
        if self.supervised_loss.config is not None:
            if world > 1:
                dist.all_reduce(totals)
            result["field_totals"] = totals.tolist()
        return result
