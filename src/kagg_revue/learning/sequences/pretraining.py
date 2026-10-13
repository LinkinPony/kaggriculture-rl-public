"""Synchronous BC with fixed-weight full episodes and truncated memory gradients."""

import time
from typing import Any

import torch
import torch.distributed as dist

from kagg_revue.datasets.demonstrations.loading import Dataset
from kagg_revue.datasets.sequences.loading import SequenceDataset
from kagg_revue.learning.distributed import rank_world
from kagg_revue.learning.optimization.learner import average_gradients, global_mean
from kagg_revue.learning.pretraining.config import GroupedLoss
from kagg_revue.learning.pretraining.optimization import Optimizer
from kagg_revue.learning.pretraining.statistics import DOMAINS, field_totals
from kagg_revue.learning.settings import RuntimeSettings
from kagg_revue.policy.memory.policy import MemoryPolicy
from kagg_revue.policy.spatial.model import Policy, log_probabilities


class SequenceOptimizer(Optimizer):
    """Commit Adam only after every context chunk in a teacher episode was consumed."""

    def __init__(
        self,
        actor: Policy,
        settings: RuntimeSettings,
        learning_rate: float,
        *,
        loss: GroupedLoss | None = None,
        joint_learning_rate: float | None = None,
    ) -> None:
        """Compile the explicit-state interface instead of the independent-row interface."""
        super().__init__(
            actor,
            settings.model_copy(update={"compile": False}),
            learning_rate,
            loss=loss,
            joint_learning_rate=joint_learning_rate,
        )
        assert isinstance(actor, MemoryPolicy)
        self.sequence_actor = actor
        if settings.compile:
            from kagg_revue.policy.memory.compilation import compile_actor

            compile_actor(actor)
        self.sequence = actor.sequence
        self.chunk_turns = settings.sequence_chunk_turns

    def shard(
        self, dataset: Dataset, index: int, batch_rows: int, seed: tuple[int, ...] | None
    ) -> dict[str, Any]:
        """Visit each retained teacher choice once; context-only rows never reset memory."""
        assert isinstance(dataset, SequenceDataset)
        started = time.perf_counter()
        rank, world = rank_world()
        observations, actions, mask = dataset.episode(index, self.device, rank, world)
        loaded = time.perf_counter()
        turns, batch = observations.shape[:2]
        training = seed is not None
        actor = self.sequence_actor
        actor.train(training)
        mass = global_mean(mask.float().sum())
        rows = int(round(float(mass) * world))
        if rows <= 0:
            raise ValueError("teacher episode has no supervised decisions")
        scales = self.loss_scales(
            observations.flatten(0, 1),
            actions.flatten(0, 1),
            torch.arange(turns, device=self.device)[:, None].expand(-1, batch).flatten(),
            mask.flatten(),
        )
        state = actor.memory.temporal.empty(batch, self.device)
        total = torch.zeros((), device=self.device)
        minimum = torch.zeros((), device=self.device)
        statistics = torch.zeros(len(DOMAINS) * 3, device=self.device)
        gradient_norm = 0.0
        if training:
            self.optimizer.zero_grad(set_to_none=True)
        with torch.set_grad_enabled(training):
            for start in range(0, turns, self.chunk_turns):
                stop = min(start + self.chunk_turns, turns)
                current = observations[start:stop]
                targets = actions[start:stop]
                eligible = mask[start:stop]
                missing = self.chunk_turns - len(current)
                if missing:
                    current = torch.cat((current, current[-1:].expand(missing, -1, -1)))
                    targets = torch.cat((targets, targets[-1:].expand(missing, -1, -1)))
                    eligible = torch.cat((eligible, eligible.new_zeros((missing, batch))))
                clock = torch.arange(start, start + self.chunk_turns, device=self.device)
                with torch.autocast(self.device.type, dtype=torch.bfloat16, enabled=self.bf16):
                    _, logits, state = self.sequence(current, clock, state, targets)
                    fields = actor.field_weights(
                        targets.flatten(0, 1),
                        clock.clamp_max(turns - 1)[:, None].expand(-1, batch).flatten(),
                        current.flatten(0, 1),
                    )
                    likelihood = log_probabilities(logits.flatten(0, 1), targets.flatten(0, 1))
                    loss = self.supervised_loss(
                        likelihood, fields, eligible.flatten(), mass, scales
                    )
                    lowest = (
                        likelihood.detach()
                        .masked_fill((fields == 0) | ~eligible.flatten()[:, None], 0)
                        .amin()
                    )
                    minimum = torch.minimum(minimum, lowest)
                with torch.no_grad():
                    selected = actor.semantic_fields
                    statistics += field_totals(
                        logits.detach().flatten(0, 1)[:, selected],
                        targets.flatten(0, 1)[:, selected],
                        likelihood.detach()[:, selected],
                        fields[:, selected] * eligible.flatten()[:, None],
                        actor.layout.observation.units,
                    )
                if training:
                    loss.backward()  # type: ignore[no-untyped-call]
                total += loss.detach()
        loss_sum = float(global_mean(total)) * rows
        if dist.is_initialized():
            dist.all_reduce(minimum, op=dist.ReduceOp.MIN)
            dist.all_reduce(statistics)
        if not 0 <= loss_sum < 1e6 * rows or float(minimum) < -1e8:
            raise ValueError("recurrent imitation loss is nonfinite or outside policy support")
        if training:
            average_gradients(list(actor.parameters()))
            gradient_norm = float(
                torch.nn.utils.clip_grad_norm_(actor.parameters(), 1.0, error_if_nonfinite=True)
            )
            self.optimizer.step()
        return {
            "loss_sum": loss_sum,
            "rows": rows,
            "optimizer_steps": int(training),
            "field_totals": statistics.tolist(),
            "gradient_norm": gradient_norm,
            "performance": {
                "seconds": time.perf_counter() - started,
                "load_seconds": loaded - started,
                "learning_seconds": time.perf_counter() - loaded,
                "trajectories_per_rank": batch,
                "supervised_rows": rows,
                "peak_allocated_bytes": torch.cuda.max_memory_allocated(self.device)
                if self.device.type == "cuda"
                else 0,
            },
        }
