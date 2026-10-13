"""Full-coverage stateless BC over authenticated complete teacher trajectories."""

import time
from typing import Any

import torch
import torch.distributed as dist
from torch import Tensor

from kagg_revue.datasets.demonstrations.loading import Dataset
from kagg_revue.datasets.sequences.loading import SequenceDataset
from kagg_revue.learning.distributed import rank_world
from kagg_revue.learning.optimization.learner import average_gradients, global_mean
from kagg_revue.learning.pretraining.config import GroupedLoss
from kagg_revue.learning.pretraining.optimization import Optimizer
from kagg_revue.learning.pretraining.statistics import DOMAINS, field_totals
from kagg_revue.learning.settings import RuntimeSettings
from kagg_revue.policy.compilation import options
from kagg_revue.policy.grounded.typed import TypedGroundedPolicy
from kagg_revue.policy.memory.compilation import compile_actor
from kagg_revue.policy.memory.policy import MemoryPolicy
from kagg_revue.policy.spatial.model import Policy


class FlatSequenceOptimizer(Optimizer):
    """Shuffle trajectory groups and use every eligible row once per epoch."""

    def __init__(
        self,
        actor: Policy,
        settings: RuntimeSettings,
        learning_rate: float,
        *,
        loss: GroupedLoss | None = None,
    ) -> None:
        """Keep the selected actor unchanged and compile its padding-free BC objective."""
        super().__init__(
            actor, settings.model_copy(update={"compile": False}), learning_rate, loss=loss
        )
        if not isinstance(actor, TypedGroundedPolicy) or isinstance(actor, MemoryPolicy):
            raise ValueError("flat trajectory BC requires a stateless typed actor")
        self.typed = actor
        self.micro_rows = settings.ppo.microbatch_rows // len(settings.devices)
        self.objective = self.loss
        if settings.compile:
            compile_actor(actor)
            self.objective = torch.compile(
                self.loss, fullgraph=True, dynamic=False, options=options(self.device)
            )

    def loss(
        self,
        observations: Tensor,
        actions: Tensor,
        turns: Tensor,
        eligible: Tensor,
        mass: Tensor,
        scales: Tensor,
    ) -> tuple[Tensor, Tensor, Tensor]:
        """Score a microbatch with fixed full-batch domain or historical row denominators."""
        actor = self.typed
        fields = actor.field_weights(actions, turns, observations)[:, actor.semantic_fields]
        logits = actor.compact_logits(observations, actions)
        targets = actions[:, actor.semantic_fields]
        likelihood = logits.log_softmax(-1).gather(-1, targets[..., None]).squeeze(-1)
        loss = self.supervised_loss(likelihood, fields, eligible, mass, scales, compact=True)
        active = fields * eligible[:, None]
        minimum = likelihood.detach().masked_fill(active == 0, 0).amin()
        statistics = field_totals(
            logits, targets, likelihood, active, actor.layout.observation.units
        )
        return loss, minimum, statistics

    def shard(
        self, dataset: Dataset, index: int, batch_rows: int, seed: tuple[int, ...] | None
    ) -> dict[str, Any]:
        """Accumulate each local group, including an empty tail rank, before synchronized Adam."""
        assert isinstance(dataset, SequenceDataset)
        started = time.perf_counter()
        rank, world = rank_world()
        observations, actions, eligible = dataset.episode(index, self.device, rank, world)
        loaded = time.perf_counter()
        turns, trajectories = eligible.shape
        clock = torch.arange(turns, device=self.device)[:, None].expand(-1, trajectories).flatten()
        observations, actions, eligible = (
            observations.flatten(0, 1),
            actions.flatten(0, 1),
            eligible.flatten(),
        )
        mass = global_mean(eligible.float().sum())
        rows = int(round(float(mass) * world))
        if rows <= 0:
            raise ValueError("trajectory group has no supervised decisions")
        scales = self.loss_scales(observations, actions, clock, eligible)
        training = seed is not None
        self.actor.train(training)
        total = torch.zeros((), device=self.device)
        minimum = torch.zeros_like(total)
        statistics = torch.zeros(len(DOMAINS) * 3, device=self.device)
        gradient_norm = 0.0
        if training:
            self.optimizer.zero_grad(set_to_none=True)
        with torch.set_grad_enabled(training):
            for start in range(0, len(clock), self.micro_rows):
                section = slice(start, start + self.micro_rows)
                with torch.autocast(self.device.type, dtype=torch.bfloat16, enabled=self.bf16):
                    loss, lowest, metrics = self.objective(
                        observations[section],
                        actions[section],
                        clock[section],
                        eligible[section],
                        mass,
                        scales,
                    )
                if training:
                    loss.backward()  # type: ignore[no-untyped-call]
                total += loss.detach()
                minimum = torch.minimum(minimum, lowest)
                statistics += metrics
        loss_sum = float(global_mean(total)) * rows
        if dist.is_initialized():
            dist.all_reduce(minimum, op=dist.ReduceOp.MIN)
            dist.all_reduce(statistics)
        if not 0 <= loss_sum < 1e6 * rows or float(minimum) < -1e8:
            raise ValueError("flat BC loss is nonfinite or outside teacher action support")
        if training:
            average_gradients(list(self.actor.parameters()))
            gradient_norm = float(
                torch.nn.utils.clip_grad_norm_(
                    self.actor.parameters(), 1.0, error_if_nonfinite=True
                )
            )
            self.optimizer.step()
        totals = statistics.tolist()
        return {
            "loss_sum": loss_sum,
            "rows": rows,
            "optimizer_steps": int(training),
            "field_totals": totals,
            "gradient_norm": gradient_norm,
            "performance": {
                "seconds": time.perf_counter() - started,
                "load_seconds": loaded - started,
                "learning_seconds": time.perf_counter() - loaded,
                "trajectories_per_rank": trajectories,
                "supervised_rows": rows,
                "peak_allocated_bytes": torch.cuda.max_memory_allocated(self.device)
                if self.device.type == "cuda"
                else 0,
            },
        }
