"""Fixed-sample policy guards and transactional optimizer updates."""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from copy import deepcopy
from dataclasses import dataclass

import torch
from torch import Tensor, nn
from torch.optim import Optimizer

from kagg_revue.policy.effects.model import EffectActorCritic
from kagg_revue.rl.effects.chunked import _balanced_weights, _sequence_context, _state_rows
from kagg_revue.rl.effects.data import EffectRolloutBatch
from kagg_revue.rl.effects.replay import _autocast, _evaluate
from kagg_revue.rl.effects.reuse import evaluate_reused_work


class OptimizerTransaction:
    """Restore parameters in place together with every optimizer state field."""

    def __init__(self, model: nn.Module, optimizer: Optimizer) -> None:
        """Snapshot once before trying the already computed gradient."""
        self._model = model
        self._optimizer = optimizer
        self._weights = {name: value.detach().clone() for name, value in model.state_dict().items()}
        self._state = deepcopy(optimizer.state_dict())

    @torch.no_grad()
    def restore(self) -> None:
        """Keep captured model addresses while restoring weights and Adam clocks."""
        self._model.load_state_dict(self._weights, strict=True)
        # load_state_dict may alias its input tensors; retain an immutable backup
        # across retries, including lazily initialized optimizer state.
        self._optimizer.load_state_dict(deepcopy(self._state))


@dataclass(frozen=True)
class GuardedStep:
    """Result of accepting or undoing one logical optimizer update."""

    accepted: bool
    kl: float
    rejected_attempts: int
    maximum_trial_kl: float
    learning_rate_scale: float


def guarded_optimizer_step(
    model: nn.Module,
    optimizer: Optimizer,
    actor_parameters: Sequence[nn.Parameter],
    guard: Callable[[], float],
    *,
    target_kl: float,
    backoff_factor: float,
    maximum_retries: int,
) -> GuardedStep:
    """Check every proposed step, including the final minibatch, before accepting."""
    transaction = OptimizerTransaction(model, optimizer)
    actor_ids = {id(parameter) for parameter in actor_parameters}
    actor_groups = [
        index
        for index, group in enumerate(optimizer.param_groups)
        if any(id(parameter) in actor_ids for parameter in group["params"])
    ]
    rates = [float(optimizer.param_groups[index]["lr"]) for index in actor_groups]
    maximum_kl = 0.0
    kl = math.inf
    for attempt in range(maximum_retries + 1):
        for index, rate in zip(actor_groups, rates, strict=True):
            optimizer.param_groups[index]["lr"] = rate * backoff_factor**attempt
        optimizer.step()
        kl = guard()
        maximum_kl = max(maximum_kl, kl) if math.isfinite(kl) else math.inf
        if math.isfinite(kl) and kl <= target_kl:
            # Backtracking solves this step's trust-region constraint. Do not
            # permanently anneal the next rollout's rate when this rollout has
            # simply used up its cumulative KL budget.
            for index, rate in zip(actor_groups, rates, strict=True):
                optimizer.param_groups[index]["lr"] = rate
            return GuardedStep(True, kl, attempt, maximum_kl, backoff_factor**attempt)
        transaction.restore()
    return GuardedStep(False, kl, maximum_retries + 1, maximum_kl, 0.0)


class EffectPolicyGuard:
    """Evaluate exact categorical KL on fixed complete episodes from one rollout."""

    def __init__(
        self,
        model: EffectActorCritic,
        batch: EffectRolloutBatch,
        device: torch.device,
        *,
        episode_count: int,
        candidate_elements_per_chunk: int,
    ) -> None:
        """Retain one bounded physical microbatch, sampled across the local shard."""
        count = min(episode_count, batch.episode_count)
        episodes = tuple(index * batch.episode_count // count for index in range(count))
        self._batch = batch.subset(episodes, device)
        self._model = model
        self._chunk_elements = candidate_elements_per_chunk
        self._reference: Tensor | None = None
        self._references: dict[tuple[int, int], Tensor] = {}
        self._weights = _balanced_weights(
            self._batch.episode_index,
            self._batch.turn_index,
            self._batch.policy_mask,
            self._batch.episode_count,
            self._batch.board.shape[1],
        )
        if not self._batch.decision_shards:
            with torch.no_grad(), _autocast(device):
                output = _evaluate(model, self._batch, validate=True)
                self._reference = output.candidate_logits.float().log_softmax(-1).detach()
        elif any(
            shard.reference_candidate_log_probabilities is None
            for shard in self._batch.decision_shards
        ):
            self()

    @staticmethod
    def _kl(reference: Tensor, current: Tensor) -> Tensor:
        difference = (reference - current).masked_fill(~torch.isfinite(reference), 0.0)
        return (reference.exp() * difference).sum(-1)

    @torch.no_grad()
    def __call__(self) -> float:
        """Measure policy movement without storing a backward or full-width tape."""
        batch = self._batch
        if not batch.decision_shards:
            if self._reference is None:
                raise RuntimeError("effect guard lost its reference distribution")
            with _autocast(batch.board.device):
                output = _evaluate(self._model, batch, validate=False)
            current = output.candidate_logits.float().log_softmax(-1)
            return float((self._kl(self._reference, current) * self._weights).sum())
        if batch.state is None:
            raise RuntimeError("effect guard requires materialized state")
        sequence = _sequence_context(self._model, batch, compute_value=False)
        total = self._weights.new_zeros(())
        offset = 0
        for shard_index, shard in enumerate(batch.decision_shards):
            reference = shard.reference_candidate_log_probabilities
            width = shard.state.candidate_fields.shape[1]
            chunk_rows = max(1, self._chunk_elements // width)
            for start in range(0, shard.row_count, chunk_rows):
                stop = min(start + chunk_rows, shard.row_count)
                local = slice(start, stop)
                rows = slice(offset + start, offset + stop)
                with _autocast(batch.board.device):
                    output = evaluate_reused_work(
                        self._model,
                        sequence,
                        _state_rows(batch.state, rows),
                        batch.episode_index[rows],
                        batch.turn_index[rows],
                        _state_rows(shard.state, local),
                        validate=False,
                    )
                current = output.candidate_logits.float().log_softmax(-1)
                local_reference = (
                    reference[local]
                    if reference is not None
                    else self._references.setdefault((shard_index, start), current.detach().clone())
                )
                total += (self._kl(local_reference, current) * self._weights[rows]).sum()
            offset += shard.row_count
        return float(total)
