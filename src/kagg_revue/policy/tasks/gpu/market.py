"""Whole-turn CUDA Graph for a compiler-forced unit prefix and market suffix."""

from __future__ import annotations

from typing import Any

import numpy as np
import torch
from numpy.typing import NDArray
from torch import Tensor

from kagg_revue.policy.cuda.policy_turn_graph import CudaPolicyTurnGraph
from kagg_revue.policy.cuda.session import GpuPolicyStateLayout
from kagg_revue.policy.model import TurnContext, TurnPolicyNet
from kagg_revue.policy.tasks.runtime import CompiledUnitActions, MarketRollout


def _stage(
    tensors: tuple[Tensor, ...],
    targets: tuple[Tensor, ...] | None,
) -> tuple[tuple[Tensor, ...], tuple[NDArray[Any], ...]]:
    """Download graph outputs into reusable pinned storage."""
    if targets is None:
        targets = tuple(
            torch.empty_like(source, device="cpu", pin_memory=True) for source in tensors
        )
    if len(targets) != len(tensors) or any(
        target.shape != source.shape or target.dtype != source.dtype
        for source, target in zip(tensors, targets, strict=True)
    ):
        raise ValueError("market graph staging layout changed")
    for source, target in zip(tensors, targets, strict=True):
        target.copy_(source, non_blocking=True)
    torch.cuda.current_stream(tensors[0].device).synchronize()
    return targets, tuple(target.numpy() for target in targets)


class TaskMarketGraph:
    """Sample only market factors after forcing task-compiled unit actions."""

    def __init__(
        self,
        actor: TurnPolicyNet,
        layout: GpuPolicyStateLayout,
        has_quantity: NDArray[np.bool_],
        generator: torch.Generator,
    ) -> None:
        """Bind one actor and fixed device-side policy-session ABI."""
        architecture = actor.architecture
        if architecture.prefix_fact_features or architecture.candidate_fact_features:
            raise ValueError("task market graph does not support legacy fact tensors")
        self._actor = actor
        self._layout = layout
        self._generator = generator
        self._device = next(actor.parameters()).device
        self._has_quantity = torch.as_tensor(
            has_quantity,
            dtype=torch.bool,
            device=self._device,
        )
        self._graph: CudaPolicyTurnGraph | None = None
        self._host_outputs: tuple[Tensor, ...] | None = None

    @property
    def capture_seconds(self) -> float:
        """Return one-time CUDA graph construction work."""
        return 0.0 if self._graph is None else self._graph.capture_seconds

    def _forced(self, compiled: CompiledUnitActions) -> tuple[Tensor, Tensor]:
        decisions = self._actor.architecture.max_decisions
        batch = compiled.tokens.shape[0]
        tokens = torch.zeros((decisions, batch), dtype=torch.long, device=self._device)
        quantities = torch.zeros_like(tokens)
        width = compiled.tokens.shape[1]
        tokens[:width].copy_(
            torch.as_tensor(compiled.tokens.T, dtype=torch.long, device=self._device)
        )
        quantities[:width].copy_(
            torch.as_tensor(
                compiled.quantities.T,
                dtype=torch.long,
                device=self._device,
            )
        )
        return tokens, quantities

    def decode(
        self,
        context: TurnContext,
        policy_state: Tensor,
        compiled: CompiledUnitActions,
        policy_batch: Any,
    ) -> MarketRollout:
        """Replay one fixed-batch graph and advance native sessions once."""
        batch = compiled.tokens.shape[0]
        compiled.validate(batch, self._layout.unit_limit)
        forced_tokens, forced_quantities = self._forced(compiled)
        if self._graph is None:
            self._graph = CudaPolicyTurnGraph(
                self._actor,
                context,
                policy_state,
                self._layout,
                self._has_quantity,
                self._generator,
                forced_tokens=forced_tokens,
                forced_quantities=forced_quantities,
                track_log_probability=True,
            )
        self._graph.start_turn(
            context,
            policy_state,
            forced_tokens,
            forced_quantities,
        )
        self._graph.replay()
        log_probability = self._graph.log_probabilities
        if log_probability is None:
            raise RuntimeError("task market graph omitted behavior probability")
        self._host_outputs, staged = _stage(
            (
                self._graph.tokens,
                self._graph.quantities,
                self._graph.phases,
                self._graph.decisions,
                self._graph.legal,
                log_probability,
                self._graph.final_phases,
            ),
            self._host_outputs,
        )
        (
            token_values,
            quantity_values,
            phase_values,
            decision_values,
            legal_values,
            log_probability_values,
            final_phases,
        ) = staged
        if np.any(final_phases != 2):
            raise RuntimeError("task market graph exceeded actor decision capacity")
        tokens = np.ascontiguousarray(token_values.T, dtype=np.int64)
        quantities = np.ascontiguousarray(quantity_values.T, dtype=np.int64)
        phases = np.ascontiguousarray(phase_values.T, dtype=np.int64)
        decision_mask = np.ascontiguousarray(decision_values.T, dtype=np.bool_)
        legal_mask = np.ascontiguousarray(legal_values.transpose(1, 0, 2), dtype=np.bool_)
        old_log_probability = np.ascontiguousarray(log_probability_values.T, dtype=np.float32)
        decision_counts = decision_mask.sum(axis=1, dtype=np.int64)
        chosen_legal = np.take_along_axis(
            legal_mask,
            tokens[..., None],
            axis=2,
        )[..., 0]
        illegal = decision_mask & ~chosen_legal
        if illegal.any():
            row, decision = np.argwhere(illegal)[0]
            raise RuntimeError(
                "task market graph selected an illegal token: "
                f"row={row}, decision={decision}, phase={phases[row, decision]}, "
                f"token={tokens[row, decision]}"
            )
        unit_positions = decision_mask & (phases == 0)
        expected_units = np.zeros_like(tokens)
        expected_units[:, : compiled.tokens.shape[1]] = compiled.tokens
        mismatch = unit_positions & (tokens != expected_units)
        if mismatch.any():
            row, decision = np.argwhere(mismatch)[0]
            raise RuntimeError(
                "task market graph lost a forced unit token: "
                f"row={row}, decision={decision}, "
                f"actual={tokens[row, decision]}, "
                f"expected={expected_units[row, decision]}"
            )
        policy_batch.select_sequences(
            tokens,
            quantities,
            decision_counts,
            compiled.unit_counts,
        )
        decisions = self._actor.architecture.max_decisions
        return MarketRollout(
            tokens=tokens,
            quantities=quantities,
            phases=phases,
            decision_mask=decision_mask,
            policy_factor_mask=decision_mask & (phases == 1),
            legal_mask=legal_mask,
            old_log_probability=old_log_probability,
            entropy=np.zeros_like(old_log_probability),
            prefix_facts=np.zeros((batch, decisions, 0), dtype=np.float16),
            candidate_facts=np.zeros(
                (batch, decisions, self._actor.architecture.action_tokens, 0),
                dtype=np.float16,
            ),
            decision_counts=decision_counts,
            unit_counts=compiled.unit_counts.copy(),
        )

    def close(self) -> None:
        """Release the lazily captured market graph, if present."""
        if self._graph is not None:
            self._graph.close()
            self._graph = None
            self._host_outputs = None


__all__ = ["TaskMarketGraph"]
