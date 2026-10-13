"""Stateful day-history inference for one fixed self-play policy group."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import numpy as np
import torch
from numpy.typing import NDArray

from kagg_revue.policy.plans.backbone import PlanTemporalState
from kagg_revue.policy.plans.grammar import PlanActions
from kagg_revue.policy.plans.model import (
    StructuredPlanBehaviorOutput,
    StructuredPlanPolicy,
)
from kagg_revue.rl.plans.exchange import PlanTensorExchange
from kagg_revue.rl.plans.graphs import PlanEventGraphCache


@dataclass(frozen=True)
class PlanInferenceResult:
    """One decoded chunk and its source/panel row identities."""

    sources: NDArray[np.int64]
    panel_rows: NDArray[np.int64]
    actions: PlanActions
    policy_output: StructuredPlanBehaviorOutput | None


class PlanPolicyRuntime:
    """Retain fixed-batch day KV/GRU state across sparse explicit events."""

    def __init__(
        self,
        policy: StructuredPlanPolicy,
        generator: torch.Generator,
        group_sources: NDArray[np.int64],
        *,
        decision_capacity: int,
        inference_capacity: int,
        device: torch.device,
        record_statistics: bool,
        event_graphs: PlanEventGraphCache | None = None,
    ) -> None:
        """Bind a fixed source ordering and its persistent model state."""
        if group_sources.ndim != 1 or group_sources.size < 1:
            raise ValueError("structured-plan inference group cannot be empty")
        if np.unique(group_sources).size != group_sources.size:
            raise ValueError("structured-plan inference group sources must be unique")
        if bool(np.any((group_sources < 0) | (group_sources >= decision_capacity))):
            raise ValueError("structured-plan inference group source is outside capacity")
        self._policy = policy
        self._generator = generator
        self._sources = group_sources.astype(np.int64, copy=True)
        self._source_row = np.full(decision_capacity, -1, dtype=np.int64)
        self._source_row[self._sources] = np.arange(self._sources.size, dtype=np.int64)
        self._inference_capacity = inference_capacity
        self._device = device
        self._record_statistics = record_statistics
        if event_graphs is not None and not event_graphs.matches(policy, generator):
            raise ValueError("structured-plan event graph cache binding differs")
        self._event_graphs = event_graphs
        self._state: PlanTemporalState | None = None
        self._day_advances = 0

    @property
    def day_advances(self) -> int:
        """Return the number of synchronized long-history updates."""
        return self._day_advances

    def _infer_anchor(
        self,
        panel: Mapping[str, Any],
        rich: Mapping[str, NDArray[Any]],
        events: NDArray[np.float32],
        ready_sources: NDArray[np.int64],
        policy_rows: NDArray[np.int64],
        exchange: PlanTensorExchange,
    ) -> PlanInferenceResult:
        if self._sources.size > self._inference_capacity:
            raise ValueError(
                "structured-plan synchronized day group exceeds inference capacity"
            )
        sources = ready_sources[policy_rows]
        group_rows = self._source_row[sources]
        if (
            sources.size != self._sources.size
            or bool(np.any(group_rows < 0))
            or np.unique(group_rows).size != self._sources.size
        ):
            raise RuntimeError("structured-plan day anchor omitted a fixed policy source")
        order = np.argsort(group_rows, kind="stable")
        panel_rows = policy_rows[order]
        sources = sources[order]
        if not np.array_equal(sources, self._sources):
            raise RuntimeError("structured-plan day anchor source ordering drifted")
        inputs = exchange.inputs(panel, rich, events, panel_rows)
        with torch.cuda.device(self._device), torch.inference_mode(), torch.autocast(
            device_type="cuda",
            dtype=torch.bfloat16,
        ):
            if self._record_statistics:
                output, self._state = self._policy.rollout_behavior_advance(
                    inputs,
                    self._state,
                    generator=self._generator,
                    validate_inputs=False,
                )
                actions = output.actions
            else:
                actions, self._state = self._policy.sample_actions_advance(
                    inputs,
                    self._state,
                    generator=self._generator,
                    validate_inputs=False,
                )
                output = None
        self._day_advances += 1
        return PlanInferenceResult(sources, panel_rows, actions, output)

    def _infer_events(
        self,
        panel: Mapping[str, Any],
        rich: Mapping[str, NDArray[Any]],
        events: NDArray[np.float32],
        ready_sources: NDArray[np.int64],
        policy_rows: NDArray[np.int64],
        exchange: PlanTensorExchange,
    ) -> tuple[PlanInferenceResult, ...]:
        state = self._state
        if state is None:
            raise RuntimeError("structured-plan event preceded initial day history")
        results: list[PlanInferenceResult] = []
        for start in range(0, policy_rows.size, self._inference_capacity):
            panel_rows = policy_rows[start : start + self._inference_capacity]
            sources = ready_sources[panel_rows]
            group_rows = self._source_row[sources]
            if bool(np.any(group_rows < 0)):
                raise RuntimeError("structured-plan event entered the wrong policy group")
            inputs = exchange.inputs(panel, rich, events, panel_rows)
            index = torch.as_tensor(group_rows, dtype=torch.long, device=self._device)
            history = state.current_history[index]
            strategy = (
                state.current_strategy[index]
                if state.current_strategy is not None
                else None
            )
            if self._event_graphs is not None:
                graph_output = self._event_graphs.infer(inputs, history, strategy)
                if self._record_statistics:
                    if not isinstance(graph_output, StructuredPlanBehaviorOutput):
                        raise TypeError("structured-plan event graph omitted behavior")
                    actions = graph_output.actions
                    policy_output = graph_output
                else:
                    if not isinstance(graph_output, PlanActions):
                        raise TypeError("structured-plan event graph retained behavior")
                    actions = graph_output
                    policy_output = None
            else:
                with (
                    torch.cuda.device(self._device),
                    torch.inference_mode(),
                    torch.autocast(device_type="cuda", dtype=torch.bfloat16),
                    ):
                    if self._record_statistics:
                        policy_output = self._policy.rollout_behavior_event(
                            inputs,
                            history,
                            strategy,
                            generator=self._generator,
                            validate_inputs=False,
                        )
                        actions = policy_output.actions
                    else:
                        actions = self._policy.sample_actions_event(
                            inputs,
                            history,
                            strategy,
                            generator=self._generator,
                            validate_inputs=False,
                        )
                        policy_output = None
            results.append(
                PlanInferenceResult(sources, panel_rows, actions, policy_output)
            )
        return tuple(results)

    def infer(
        self,
        panel: Mapping[str, Any],
        rich: Mapping[str, NDArray[Any]],
        events: NDArray[np.float32],
        ready_sources: NDArray[np.int64],
        policy_rows: NDArray[np.int64],
        exchange: PlanTensorExchange,
    ) -> tuple[PlanInferenceResult, ...]:
        """Decode ready events and advance only a complete synchronized day group."""
        if policy_rows.size == 0:
            return ()
        anchor = events[policy_rows, 0].astype(np.bool_) | events[
            policy_rows,
            1,
        ].astype(np.bool_)
        event_rows = policy_rows[~anchor]
        results = list(
            self._infer_events(
                panel,
                rich,
                events,
                ready_sources,
                event_rows,
                exchange,
            )
            if event_rows.size
            else ()
        )
        anchor_rows = policy_rows[anchor]
        if anchor_rows.size == self._sources.size:
            results.append(
                self._infer_anchor(
                    panel,
                    rich,
                    events,
                    ready_sources,
                    anchor_rows,
                    exchange,
                )
            )
        elif anchor_rows.size > self._sources.size:
            raise RuntimeError("structured-plan day anchor duplicated a policy source")
        return tuple(results)


__all__ = ["PlanInferenceResult", "PlanPolicyRuntime"]
