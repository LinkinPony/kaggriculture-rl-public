"""Batched compiler-in-the-loop task and direct-market decoding."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, cast

import numpy as np
import torch
from numpy.typing import NDArray
from torch import Tensor

from kagg_revue.policy.economics.transition import apply_selection
from kagg_revue.policy.model import TurnContext, TurnPolicyNet
from kagg_revue.policy.quantity import quantity_log_probability
from kagg_revue.policy.tasks.gpu import TaskPlanningState
from kagg_revue.policy.tasks.gpu.decision import TaskDecisionGraph
from kagg_revue.policy.tasks.gpu.planning import TaskPlanningGraph
from kagg_revue.policy.tasks.gpu.recording import record_task_selections
from kagg_revue.policy.tasks.grammar import (
    FactorizedTaskDecisionInputs,
    FactorizedTaskMasks,
    TaskActions,
    TaskConditionalMasks,
    TaskDecisionInputs,
    selected_arrivals,
)
from kagg_revue.policy.tasks.model import UnitTaskPolicy
from kagg_revue.policy.tasks.native import (
    NativeTaskContract,
    decision_inputs,
    factorized_decision_inputs,
)
from kagg_revue.policy.tasks.schema import TaskPolicyOutput

IntArray = NDArray[np.int64]
FloatArray = NDArray[np.float32]
BoolArray = NDArray[np.bool_]

# Two steps amortize H200 polling under four actor streams; larger chunks regress.
_TASK_PLANNING_REPLAY_STEPS = 2


@dataclass(frozen=True)
class TaskDecisionTrace:
    """One sampled task batch and its original rollout-row identities."""

    row_indices: IntArray
    output: TaskPolicyOutput
    inputs: TaskDecisionInputs | FactorizedTaskDecisionInputs


@dataclass(frozen=True)
class CompactTaskTrace:
    """One native turn snapshot and its lightweight device-recorded suffixes."""

    snapshot: Mapping[str, Any]
    actions: NDArray[np.int16]
    counts: NDArray[np.int16]
    old_joint_log_probability: NDArray[np.float32]
    old_values: NDArray[np.float32]


TaskTrace = tuple[TaskDecisionTrace, ...] | CompactTaskTrace


@dataclass(frozen=True)
class CompiledUnitActions:
    """One deterministic official unit prefix per actor row."""

    tokens: IntArray
    quantities: IntArray
    task_results: IntArray
    unit_counts: IntArray

    def validate(self, batch_size: int, unit_limit: int) -> None:
        """Validate the native compiler's fixed-width batch output."""
        expected = (batch_size, unit_limit)
        if (
            self.tokens.shape != expected
            or self.quantities.shape != expected
            or self.task_results.shape != expected
            or self.unit_counts.shape != (batch_size,)
        ):
            raise ValueError("compiled unit-task tensors differ from their native ABI")
        if np.any((self.unit_counts < 1) | (self.unit_counts > unit_limit)):
            raise ValueError("compiled unit count lies outside the artifact capacity")


@dataclass(frozen=True)
class MarketRollout:
    """Autoregressive action record with compiler tokens marked non-policy."""

    tokens: IntArray
    quantities: IntArray
    phases: IntArray
    decision_mask: BoolArray
    policy_factor_mask: BoolArray
    legal_mask: BoolArray
    old_log_probability: FloatArray
    entropy: FloatArray
    prefix_facts: NDArray[np.float16]
    candidate_facts: NDArray[np.float16]
    decision_counts: IntArray
    unit_counts: IntArray


def _int_array(value: object) -> IntArray:
    return cast(IntArray, np.ascontiguousarray(value, dtype=np.int64))


def _task_selections(output: TaskPolicyOutput) -> IntArray:
    return cast(
        IntArray,
        torch.stack(
            (
                output.actions.mode,
                output.actions.candidate,
                output.actions.quantity,
                output.actions.earliest,
                output.actions.deadline,
            ),
            dim=1,
        )
        .detach()
        .to(device="cpu", dtype=torch.int64)
        .numpy(),
    )


def _compact_observations(
    sessions: Sequence[Any],
    engines: Sequence[Any],
    players: IntArray,
) -> dict[str, object]:
    """Stack compact per-session observations without a dense native surface."""
    rows = [
        cast(Mapping[str, object], session.compact_observation(engine, int(player)))
        for session, engine, player in zip(sessions, engines, players, strict=True)
    ]
    array_fields = (
        "root_features",
        "prefix_fields",
        "prefix_mask",
        "target_conflicts",
        "resource_conflicts",
        "mode_mask",
    )
    result: dict[str, object] = {
        name: np.stack([np.asarray(row[name]) for row in rows])
        for name in array_fields
    }
    for source, target in (
        ("unit_index", "unit_indices"),
        ("current_x", "current_x"),
        ("current_y", "current_y"),
        ("available_at", "available_at"),
        ("day_end", "day_end"),
    ):
        result[target] = np.asarray([row[source] for row in rows], dtype=np.int64)
    return result


def _select_inputs(
    inputs: TaskDecisionInputs | FactorizedTaskDecisionInputs,
    rows: Tensor,
) -> TaskDecisionInputs | FactorizedTaskDecisionInputs:
    """Gather durable active rows from a fixed-batch graph input."""
    if isinstance(inputs, FactorizedTaskDecisionInputs):
        return FactorizedTaskDecisionInputs(
            **{
                name: (
                    value
                    if name == "prefix_length"
                    else value.index_select(0, rows)
                )
                for name in inputs.__dataclass_fields__
                for value in (getattr(inputs, name),)
            }
        )
    return TaskDecisionInputs(
        context=inputs.context.index_select(0, rows),
        root_features=inputs.root_features.index_select(0, rows),
        prefix_fields=inputs.prefix_fields.index_select(0, rows),
        prefix_mask=inputs.prefix_mask.index_select(0, rows),
        candidate_features=inputs.candidate_features.index_select(0, rows),
        candidate_mask=inputs.candidate_mask.index_select(0, rows),
        candidate_arrivals=inputs.candidate_arrivals.index_select(0, rows),
        mode_mask=inputs.mode_mask.index_select(0, rows),
        available_at=inputs.available_at.index_select(0, rows),
        day_end=inputs.day_end.index_select(0, rows),
        prefix_length=inputs.prefix_length,
    )


def _select_output(output: TaskPolicyOutput, rows: Tensor) -> TaskPolicyOutput:
    """Gather policy outputs before the next graph replay overwrites them."""
    actions = TaskActions(
        **{
            name: getattr(output.actions, name).index_select(0, rows)
            for name in output.actions.__dataclass_fields__
        }
    )
    mask_values = {
        name: getattr(output.masks, name).index_select(0, rows)
        for name in output.masks.__dataclass_fields__
    }
    masks = (
        FactorizedTaskMasks(**mask_values)
        if isinstance(output.masks, FactorizedTaskMasks)
        else TaskConditionalMasks(**mask_values)
    )
    return TaskPolicyOutput(
        actions=actions,
        masks=masks,
        joint_log_probability=output.joint_log_probability.index_select(0, rows),
        factor_log_probability=output.factor_log_probability.index_select(0, rows),
        entropy=output.entropy.index_select(0, rows),
        factor_entropy=output.factor_entropy.index_select(0, rows),
        outcome_logits=output.outcome_logits.index_select(0, rows),
        value=output.value.index_select(0, rows),
    )


def plan_unit_tasks(
    backend: Any,
    policy: UnitTaskPolicy,
    contract: NativeTaskContract,
    sessions: Sequence[Any],
    engines: Sequence[Any],
    players: IntArray,
    context: Tensor,
    task_state: Tensor | None = None,
    *,
    workers: int,
    sample: bool,
    generator: torch.Generator | None = None,
    record: bool = False,
    decision_graph: TaskDecisionGraph | TaskPlanningGraph | None = None,
) -> tuple[CompiledUnitActions, TaskTrace]:
    """Decode all open task suffixes before compiling one unit action per row."""
    batch = len(sessions)
    if batch < 1 or len(engines) != batch or players.shape != (batch,):
        raise ValueError("unit-task rollout rows must be nonempty and aligned")
    if context.ndim != 2 or context.shape[0] != batch:
        raise ValueError("unit-task context must have one row per native session")
    if workers < 1:
        raise ValueError("unit-task native worker count must be positive")
    if context.device.type == "cuda" and task_state is not None:
        return _plan_unit_tasks_gpu(
            backend,
            policy,
            contract,
            sessions,
            engines,
            players,
            context,
            task_state,
            workers=workers,
            sample=sample,
            generator=generator,
            record=record,
            decision_graph=decision_graph,
        )
    if policy.factorized is not None and task_state is None:
        raise ValueError("factorized task planning requires compact economic state")
    compact_snapshot = (
        cast(
            Mapping[str, Any],
            backend.unit_task_snapshots_batch(
                list(sessions), list(engines), players, workers
            ),
        )
        if policy.factorized is not None and record
        else None
    )
    traces: list[TaskDecisionTrace] = []
    maximum_decisions = contract.prefix_capacity + contract.unit_limit
    compact_actions = np.zeros(
        (batch, maximum_decisions, 5), dtype=np.int16
    )
    compact_counts = np.zeros(batch, dtype=np.int16)
    compact_log_probability = np.zeros(
        (batch, maximum_decisions), dtype=np.float32
    )
    compact_values = np.zeros_like(compact_log_probability)
    for _ in range(maximum_decisions):
        required = np.asarray(
            backend.unit_task_decision_required_batch(
                list(sessions), list(engines), players, workers
            ),
            dtype=np.bool_,
        )
        if required.shape != (batch,):
            raise ValueError("native unit-task readiness vector has the wrong shape")
        active = np.flatnonzero(required).astype(np.int64, copy=False)
        if active.size == 0:
            break
        active_sessions = [sessions[int(index)] for index in active]
        active_engines = [engines[int(index)] for index in active]
        active_players = np.ascontiguousarray(players[active], dtype=np.int64)
        raw = cast(
            Mapping[str, Any],
            _compact_observations(
                active_sessions, active_engines, active_players
            )
            if policy.factorized is not None
            else backend.unit_task_observations_batch(
                active_sessions,
                active_engines,
                active_players,
                workers,
            ),
        )
        indices = torch.as_tensor(active, dtype=torch.long, device=context.device)
        active_context = context.index_select(0, indices)
        inputs = (
            factorized_decision_inputs(
                raw,
                active_context,
                task_state.index_select(0, indices),
                contract,
                device=context.device,
                history_window=policy.architecture.history_window,
            )
            if policy.factorized is not None and task_state is not None
            else decision_inputs(
                raw,
                active_context,
                contract,
                device=context.device,
            )
        )
        output = policy.rollout(
            inputs,
            sample=sample,
            generator=generator,
            validate_inputs=False,
            compute_entropy=False,
        )
        selections = _task_selections(output)
        backend.unit_task_select_batch(
            active_sessions,
            active_engines,
            active_players,
            selections[:, 0],
            selections[:, 1],
            selections[:, 2],
            selections[:, 3],
            selections[:, 4],
            workers,
        )
        if compact_snapshot is not None:
            positions = compact_counts[active].astype(np.int64, copy=False)
            compact_actions[active, positions] = selections.astype(
                np.int16, copy=False
            )
            compact_log_probability[active, positions] = (
                output.joint_log_probability.detach()
                .to(device="cpu", dtype=torch.float32)
                .numpy()
            )
            compact_values[active, positions] = (
                output.value.detach()
                .to(device="cpu", dtype=torch.float32)
                .numpy()
            )
            compact_counts[active] += 1
        elif record:
            traces.append(TaskDecisionTrace(active.copy(), output, inputs))
    else:
        raise RuntimeError("unit-task decoding exceeded its derived daily capacity")

    raw_actions = cast(
        Mapping[str, object],
        backend.unit_task_actions_batch(list(sessions), list(engines), players, workers),
    )
    if np.asarray(raw_actions["requires_decision"], dtype=np.bool_).any():
        raise RuntimeError("unit-task compiler still requires an actor decision")
    compiled = CompiledUnitActions(
        tokens=_int_array(raw_actions["tokens"]),
        quantities=_int_array(raw_actions["quantities"]),
        task_results=_int_array(raw_actions["task_results"]),
        unit_counts=_int_array(raw_actions["unit_counts"]),
    )
    compiled.validate(batch, contract.unit_limit)
    if compact_snapshot is not None:
        return compiled, CompactTaskTrace(
            snapshot=compact_snapshot,
            actions=compact_actions,
            counts=compact_counts,
            old_joint_log_probability=compact_log_probability,
            old_values=compact_values,
        )
    return compiled, tuple(traces)


def _plan_unit_tasks_gpu(
    backend: Any,
    policy: UnitTaskPolicy,
    contract: NativeTaskContract,
    sessions: Sequence[Any],
    engines: Sequence[Any],
    players: IntArray,
    context: Tensor,
    task_state: Tensor,
    *,
    workers: int,
    sample: bool,
    generator: torch.Generator | None,
    record: bool,
    decision_graph: TaskDecisionGraph | TaskPlanningGraph | None,
) -> tuple[CompiledUnitActions, TaskTrace]:
    """Generate complete task suffixes while all AR state remains on CUDA."""
    batch = len(sessions)
    raw_snapshot = cast(
        Mapping[str, Any],
        backend.unit_task_snapshots_batch(
            list(sessions), list(engines), players, workers
        ),
    )
    state = TaskPlanningState.from_native(raw_snapshot, task_state, contract)
    catalog = policy.catalog()
    factorized = policy.factorized is not None
    maximum_decisions = contract.prefix_capacity + contract.unit_limit
    if isinstance(decision_graph, TaskPlanningGraph):
        decision_graph.begin(state, context)
        decision = 0
        graph_active = np.asarray(
            raw_snapshot["requires_decision"], dtype=np.bool_
        )
        if graph_active.shape != (batch,):
            raise ValueError("unit-task snapshot activity has the wrong shape")
        chunk_size = _TASK_PLANNING_REPLAY_STEPS
        while graph_active.any() and decision < maximum_decisions:
            steps = min(chunk_size, maximum_decisions - decision)
            graph_active_rows = np.flatnonzero(graph_active).astype(
                np.int64, copy=False
            )
            decision_graph.replay(graph_active_rows, steps)
            graph_active = decision_graph.active_host()
            decision += steps
        if graph_active.any():
            raise RuntimeError("unit-task GPU decoding exceeded its daily capacity")
        (
            selection_values,
            count_values,
            graph_old_log_probability,
            graph_old_values,
        ) = decision_graph.host_tape()
        backend.unit_task_apply_sequences_batch(
            list(sessions),
            list(engines),
            players,
            selection_values,
            count_values,
            workers,
        )
        raw_actions = cast(
            Mapping[str, object],
            backend.unit_task_actions_batch(
                list(sessions), list(engines), players, workers
            ),
        )
        if np.asarray(raw_actions["requires_decision"], dtype=np.bool_).any():
            raise RuntimeError("unit-task GPU compiler still requires an actor decision")
        compiled = CompiledUnitActions(
            tokens=_int_array(raw_actions["tokens"]),
            quantities=_int_array(raw_actions["quantities"]),
            task_results=_int_array(raw_actions["task_results"]),
            unit_counts=_int_array(raw_actions["unit_counts"]),
        )
        compiled.validate(batch, contract.unit_limit)
        trace: TaskTrace = (
            CompactTaskTrace(
                snapshot=raw_snapshot,
                actions=selection_values,
                counts=count_values,
                old_joint_log_probability=graph_old_log_probability,
                old_values=graph_old_values,
            )
            if record
            else ()
        )
        return compiled, trace

    selections = torch.zeros(
        (batch, maximum_decisions, 5),
        dtype=torch.int16,
        device=context.device,
    )
    counts = torch.zeros(batch, dtype=torch.int16, device=context.device)
    old_log_probability = torch.zeros(
        (batch, maximum_decisions), dtype=torch.float32, device=context.device
    )
    old_values = torch.zeros_like(old_log_probability)
    all_rows = torch.arange(batch, dtype=torch.long, device=context.device)
    traces: list[TaskDecisionTrace] = []
    active_host = state.active.detach().to(device="cpu").numpy()
    active = np.flatnonzero(active_host).astype(np.int64, copy=False)
    decision = 0
    chunk_size = 4
    while active.size and decision < maximum_decisions:
        use_graph = (
            decision_graph is not None
            and sample
            and active.size * 4 >= batch
        )
        if use_graph and decision_graph is not None:
            chunk: list[
                tuple[
                    Tensor,
                    TaskDecisionInputs | FactorizedTaskDecisionInputs,
                    TaskPolicyOutput,
                ]
            ] = []
            steps = min(chunk_size, maximum_decisions - decision)
            for _step in range(steps):
                active_before = state.active.clone()
                inputs = state.inputs(
                    all_rows,
                    context,
                    catalog,
                    prefix_length=contract.prefix_capacity,
                    factorized=factorized,
                    history_window=policy.architecture.history_window,
                )
                graph_output = decision_graph.decode(inputs)
                output = _select_output(graph_output, all_rows)
                positions = counts.long().clone()
                record_task_selections(
                    active_before,
                    output.actions,
                    selections,
                    counts,
                )
                active_tensor_rows = torch.nonzero(
                    active_before, as_tuple=False
                ).flatten()
                old_log_probability[
                    active_tensor_rows, positions[active_tensor_rows]
                ] = (
                    output.joint_log_probability[active_tensor_rows]
                )
                old_values[
                    active_tensor_rows, positions[active_tensor_rows]
                ] = output.value[
                    active_tensor_rows
                ]
                arrivals = selected_arrivals(inputs, catalog, output.actions)
                state.apply(all_rows, output.actions, catalog, arrivals)
                if record:
                    chunk.append((active_before, inputs, output))
            activity = torch.stack(
                tuple(value[0] for value in chunk) + (state.active,)
                if record
                else (state.active,)
            ).detach().to(device="cpu").numpy()
            if record:
                for index, (_mask, inputs, output) in enumerate(chunk):
                    trace_rows = np.flatnonzero(activity[index]).astype(
                        np.int64, copy=False
                    )
                    rows = torch.as_tensor(
                        trace_rows, dtype=torch.long, device=context.device
                    )
                    traces.append(
                        TaskDecisionTrace(
                            trace_rows.copy(),
                            _select_output(output, rows),
                            _select_inputs(inputs, rows),
                        )
                    )
            active_host = activity[-1]
            active = np.flatnonzero(active_host).astype(np.int64, copy=False)
            decision += steps
            continue

        rows = torch.as_tensor(active, dtype=torch.long, device=context.device)
        inputs = state.inputs(
            rows,
            context,
            catalog,
            prefix_length=min(
                contract.prefix_capacity,
                state.initial_prefix_length + decision,
            ),
            factorized=factorized,
            history_window=policy.architecture.history_window,
        )
        output = policy.rollout(
            inputs,
            sample=sample,
            generator=generator,
            validate_inputs=False,
            compute_entropy=False,
        )
        selection = torch.stack(
            (
                output.actions.mode,
                output.actions.candidate,
                output.actions.quantity,
                output.actions.earliest,
                output.actions.deadline,
            ),
            dim=1,
        )
        positions = counts.index_select(0, rows).long()
        selections[rows, positions] = selection.to(torch.int16)
        old_log_probability[rows, positions] = output.joint_log_probability
        old_values[rows, positions] = output.value
        counts[rows] += 1
        arrivals = selected_arrivals(inputs, catalog, output.actions)
        state.apply(rows, output.actions, catalog, arrivals)
        if record:
            traces.append(TaskDecisionTrace(active.copy(), output, inputs))
        active_host = state.active.detach().to(device="cpu").numpy()
        active = np.flatnonzero(active_host).astype(np.int64, copy=False)
        decision += 1
    if active.size:
        raise RuntimeError("unit-task GPU decoding exceeded its daily capacity")

    selection_values = (
        selections.detach().to(device="cpu", dtype=torch.int16).numpy()
    )
    count_values = counts.detach().to(device="cpu", dtype=torch.int16).numpy()
    backend.unit_task_apply_sequences_batch(
        list(sessions),
        list(engines),
        players,
        selection_values,
        count_values,
        workers,
    )
    raw_actions = cast(
        Mapping[str, object],
        backend.unit_task_actions_batch(
            list(sessions), list(engines), players, workers
        ),
    )
    if np.asarray(raw_actions["requires_decision"], dtype=np.bool_).any():
        raise RuntimeError("unit-task GPU compiler still requires an actor decision")
    compiled = CompiledUnitActions(
        tokens=_int_array(raw_actions["tokens"]),
        quantities=_int_array(raw_actions["quantities"]),
        task_results=_int_array(raw_actions["task_results"]),
        unit_counts=_int_array(raw_actions["unit_counts"]),
    )
    compiled.validate(batch, contract.unit_limit)
    if factorized and record:
        compact_trace = CompactTaskTrace(
            snapshot=raw_snapshot,
            actions=selection_values,
            counts=count_values,
            old_joint_log_probability=(
                old_log_probability.detach().to(device="cpu").numpy()
            ),
            old_values=old_values.detach().to(device="cpu").numpy(),
        )
        return compiled, compact_trace
    return compiled, tuple(traces)


def _categorical_statistics(
    logits: Tensor, mask: Tensor, selected: Tensor
) -> tuple[Tensor, Tensor]:
    masked = logits.float().masked_fill(~mask, -torch.inf)
    log_probabilities = torch.log_softmax(masked, dim=-1)
    probabilities = log_probabilities.exp()
    selected_log_probability = log_probabilities.gather(-1, selected[:, None]).squeeze(-1)
    entropy = -(probabilities * log_probabilities.masked_fill(~mask, 0.0)).sum(dim=-1)
    return selected_log_probability, entropy


def _quantity_entropy(logits: Tensor) -> Tensor:
    log_probabilities = torch.log_softmax(logits.float(), dim=-1)
    return -(log_probabilities.exp() * log_probabilities).sum(dim=-1)


def decode_market_actions(
    actor: TurnPolicyNet,
    context: TurnContext,
    policy_sessions: Sequence[Any],
    policy_batch: Any,
    compiled: CompiledUnitActions,
    has_quantity: BoolArray,
    *,
    sample: bool,
    generator: torch.Generator | None = None,
) -> MarketRollout:
    """Teacher-force compiler units, then sample only official market orders."""
    batch = compiled.tokens.shape[0]
    architecture = actor.architecture
    compiled.validate(batch, architecture.unit_shape[1])
    if len(policy_sessions) != batch or int(policy_batch.size) != batch:
        raise ValueError("market policy sessions and compiled units differ")
    if context.memory.shape[0] != batch or context.memory_mask.shape[0] != batch:
        raise ValueError("market decoder context has a different batch size")
    if has_quantity.shape != (architecture.action_tokens,):
        raise ValueError("market quantity flags differ from the action vocabulary")
    device = context.memory.device
    include_facts = bool(architecture.prefix_fact_features)
    include_state = actor.economics is not None
    compiled_inputs = cast(
        Mapping[str, object],
        policy_batch.compiled_unit_inputs(
            compiled.tokens,
            compiled.quantities,
            compiled.unit_counts,
            include_facts,
            include_state,
        ),
    )
    unit_prefix = (
        None if not include_facts else np.asarray(compiled_inputs["prefix_facts"], dtype=np.float32)
    )
    unit_candidates = (
        None
        if not include_facts
        else np.asarray(compiled_inputs["candidate_facts"], dtype=np.float32)
    )
    unit_state = (
        None if not include_state else np.asarray(compiled_inputs["gpu_state"], dtype=np.int64)
    )
    policy_batch.select_compiled_units(
        compiled.tokens,
        compiled.quantities,
        compiled.unit_counts,
    )

    decisions = architecture.max_decisions
    tokens = np.zeros((batch, decisions), dtype=np.int64)
    quantities = np.zeros_like(tokens)
    phases = np.zeros_like(tokens)
    decision_mask = np.zeros((batch, decisions), dtype=np.bool_)
    policy_mask = np.zeros_like(decision_mask)
    legal_mask = np.zeros((batch, decisions, architecture.action_tokens), dtype=np.bool_)
    old_log_probability = np.zeros((batch, decisions), dtype=np.float32)
    entropy = np.zeros_like(old_log_probability)
    stored_prefix_facts = np.zeros(
        (batch, decisions, architecture.prefix_fact_features), dtype=np.float16
    )
    stored_candidate_facts = np.zeros(
        (
            batch,
            decisions,
            architecture.action_tokens,
            architecture.candidate_fact_features,
        ),
        dtype=np.float16,
    )
    unit_cursor = np.zeros(batch, dtype=np.int64)
    action_state = actor.action.initial_state(context)
    previous_token: Tensor | None = None
    previous_quantity: Tensor | None = None
    behavior_statistics: list[Tensor] = []
    quantity_tokens = torch.as_tensor(
        has_quantity,
        dtype=torch.bool,
        device=device,
    )
    market_economic_state = (
        torch.as_tensor(np.asarray(policy_batch.gpu_state(), dtype=np.int64), device=device)
        if actor.economics is not None
        else None
    )

    for decision in range(decisions):
        unit_rows = unit_cursor < compiled.unit_counts
        raw_market_phases, raw_market_legal = policy_batch.decision_inputs()
        market_phases = np.asarray(raw_market_phases, dtype=np.int64)
        market_legal = np.asarray(raw_market_legal, dtype=np.bool_)
        market_rows = ~unit_rows & (market_phases != 2)
        active = unit_rows | market_rows
        if not active.any():
            break
        phase_values = np.zeros(batch, dtype=np.int64)
        phase_values[market_rows] = 1
        phase = torch.as_tensor(phase_values, dtype=torch.long, device=device)

        prefix_facts: Tensor | None = None
        candidate_facts: Tensor | None = None
        if include_facts:
            if unit_prefix is None or unit_candidates is None:
                raise RuntimeError("native compiled unit facts are absent")
            market_prefix_raw, market_candidates_raw = policy_batch.decision_facts()
            prefix_values = np.zeros((batch, architecture.prefix_fact_features), dtype=np.float32)
            candidate_values = np.zeros(
                (
                    batch,
                    architecture.action_tokens,
                    architecture.candidate_fact_features,
                ),
                dtype=np.float32,
            )
            for row in np.flatnonzero(unit_rows):
                cursor = int(unit_cursor[row])
                prefix_values[row] = unit_prefix[row, cursor]
                candidate_values[row] = unit_candidates[row, cursor]
            prefix_values[market_rows] = np.asarray(market_prefix_raw, dtype=np.float32)[
                market_rows
            ]
            candidate_values[market_rows] = np.asarray(market_candidates_raw, dtype=np.float32)[
                market_rows
            ]
            # Behavior and PPO replay must see byte-identical persisted facts.
            # Quantize before inference instead of only while recording.
            prefix_values_half = prefix_values.astype(np.float16)
            candidate_values_half = candidate_values.astype(np.float16)
            prefix_facts = torch.as_tensor(prefix_values_half, device=device).float()
            candidate_facts = torch.as_tensor(candidate_values_half, device=device).float()
            stored_prefix_facts[:, decision] = prefix_values_half
            stored_candidate_facts[:, decision] = candidate_values_half

        economic_state: Tensor | None = None
        economic_prefix: Tensor | None = None
        economic_candidates: Tensor | None = None
        if actor.economics is not None:
            if unit_state is None:
                raise RuntimeError("native compiled economic states are absent")
            if market_economic_state is None:
                raise RuntimeError("market economic state is absent")
            economic_state = market_economic_state.clone()
            for row in np.flatnonzero(unit_rows):
                economic_state[row] = torch.as_tensor(
                    unit_state[row, int(unit_cursor[row])], device=device
                )
            economic_prefix = actor.economics.prefix_features(economic_state, phase)
            economic_candidates = actor.economics.candidate_features(economic_state, phase)

        logits, hidden, action_state = actor.action.next_cached(
            previous_token,
            previous_quantity,
            phase,
            context,
            action_state,
            prefix_facts,
            candidate_facts,
            economic_prefix,
            economic_candidates,
        )
        allowed_values = np.zeros((batch, architecture.action_tokens), dtype=np.bool_)
        allowed_values[market_rows] = market_legal[market_rows]
        for row in np.flatnonzero(unit_rows):
            allowed_values[row, compiled.tokens[row, unit_cursor[row]]] = True
        allowed_values[~active, 0] = True
        allowed = torch.as_tensor(allowed_values, dtype=torch.bool, device=device)
        selected = torch.zeros(batch, dtype=torch.long, device=device)
        if market_rows.any():
            market_index = torch.as_tensor(
                np.flatnonzero(market_rows), dtype=torch.long, device=device
            )
            masked_market_logits = (
                logits.index_select(0, market_index)
                .float()
                .masked_fill(~allowed.index_select(0, market_index), -torch.inf)
            )
            market_tokens = (
                torch.multinomial(
                    torch.softmax(masked_market_logits, dim=-1),
                    1,
                    generator=generator,
                ).squeeze(-1)
                if sample
                else masked_market_logits.argmax(dim=-1)
            )
            selected[market_index] = market_tokens
        unit_index = torch.as_tensor(np.flatnonzero(unit_rows), dtype=torch.long, device=device)
        if unit_index.numel():
            forced = torch.as_tensor(
                compiled.tokens[unit_rows, unit_cursor[unit_rows]],
                dtype=torch.long,
                device=device,
            )
            selected[unit_index] = forced

        selected_candidate_facts = (
            candidate_facts[torch.arange(batch, device=device), selected]
            if candidate_facts is not None
            else None
        )
        economic_quantities = (
            actor.economics.quantity_features(economic_state, selected)
            if actor.economics is not None and economic_state is not None
            else None
        )
        quantity_logits = actor.action.quantity_logits(
            hidden,
            selected,
            selected_candidate_facts,
            economic_quantities,
        )
        market_factor = torch.as_tensor(
            market_rows,
            dtype=torch.bool,
            device=device,
        )
        quantity_factor = market_factor & quantity_tokens[selected]
        sampled_quantity = actor.choose_quantity(
            quantity_logits,
            sample=sample,
            generator=generator,
        )
        selected_quantity = torch.where(
            quantity_factor,
            sampled_quantity,
            torch.zeros_like(sampled_quantity),
        )
        if unit_index.numel():
            selected_quantity[unit_index] = torch.as_tensor(
                compiled.quantities[unit_rows, unit_cursor[unit_rows]],
                dtype=torch.long,
                device=device,
            )

        # Native legality depends on both sampled fields, so one D2H transfer is
        # unavoidable. Pack them together instead of synchronizing once per
        # field; behavior statistics stay resident until the full turn ends.
        selected_values = (
            torch.stack((selected, selected_quantity), dim=1).detach().to(device="cpu").numpy()
        )
        selected_cpu = selected_values[:, 0]
        quantity_cpu = selected_values[:, 1]

        action_log_probability, action_entropy = _categorical_statistics(logits, allowed, selected)
        quantity_log = quantity_log_probability(quantity_logits, selected_quantity.clamp_min(1))
        quantity_entropy = _quantity_entropy(quantity_logits)
        joint_log_probability = torch.where(
            market_factor,
            action_log_probability
            + torch.where(quantity_factor, quantity_log, torch.zeros_like(quantity_log)),
            torch.zeros_like(action_log_probability),
        )
        joint_entropy = torch.where(
            market_factor,
            action_entropy
            + torch.where(quantity_factor, quantity_entropy, torch.zeros_like(quantity_entropy)),
            torch.zeros_like(action_entropy),
        )
        behavior_statistics.append(
            torch.stack((joint_log_probability, joint_entropy), dim=1).detach()
        )
        policy_batch.select(
            np.ascontiguousarray(selected_cpu, dtype=np.int64),
            np.ascontiguousarray(quantity_cpu, dtype=np.int64),
            np.ascontiguousarray(market_rows, dtype=np.uint8),
        )
        if actor.economics is not None and market_economic_state is not None:
            apply_selection(
                market_economic_state,
                selected,
                selected_quantity,
                torch.as_tensor(market_rows, dtype=torch.bool, device=device),
                actor.economics.layout,
                actor.economics.vocabulary,
            )
        tokens[:, decision] = selected_cpu
        quantities[:, decision] = quantity_cpu
        phases[:, decision] = phase_values
        decision_mask[:, decision] = active
        policy_mask[:, decision] = market_rows
        legal_mask[:, decision] = allowed_values
        unit_cursor[unit_rows] += 1
        previous_token = selected
        previous_quantity = selected_quantity
    if behavior_statistics:
        statistics = torch.stack(behavior_statistics, dim=1).to(device="cpu").numpy()
        count = statistics.shape[1]
        old_log_probability[:, :count] = statistics[:, :, 0]
        entropy[:, :count] = statistics[:, :, 1]
    if np.any(np.asarray(policy_batch.phases(), dtype=np.int64) != 2):
        raise RuntimeError("market decoder ended before every official action was complete")
    decision_counts = decision_mask.sum(axis=1, dtype=np.int64)
    return MarketRollout(
        tokens=tokens,
        quantities=quantities,
        phases=phases,
        decision_mask=decision_mask,
        policy_factor_mask=policy_mask,
        legal_mask=legal_mask,
        old_log_probability=old_log_probability,
        entropy=entropy,
        prefix_facts=stored_prefix_facts,
        candidate_facts=stored_candidate_facts,
        decision_counts=decision_counts,
        unit_counts=compiled.unit_counts.copy(),
    )


def task_context(context: TurnContext) -> Tensor:
    """Return the verified causal history token shared with task decisions."""
    if context.memory.ndim != 3 or context.memory.shape[1] < 1:
        raise ValueError("turn context lacks its causal history token")
    return context.memory[:, 0]


__all__ = [
    "CompactTaskTrace",
    "CompiledUnitActions",
    "MarketRollout",
    "TaskDecisionTrace",
    "decode_market_actions",
    "plan_unit_tasks",
    "task_context",
]
