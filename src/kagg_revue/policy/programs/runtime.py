"""Batched compiler-in-the-loop decoding for complete turn programs."""

from __future__ import annotations

import time
from collections.abc import Mapping, MutableMapping, Sequence
from dataclasses import dataclass
from typing import Any, cast

import numpy as np
import torch
from numpy.typing import NDArray
from torch import Tensor

from kagg_revue.policy.model import ActorArchitecture, TurnContext
from kagg_revue.policy.programs.encoding import ProgramPreparedContext
from kagg_revue.policy.programs.gpu import (
    ProgramDecisionGraph,
    ProgramDecisionGraphPool,
    ProgramDecisionGraphShards,
    ProgramGpuTrace,
    ProgramGpuTurnSwitchGraph,
)
from kagg_revue.policy.programs.grammar import (
    ProgramActionSequence,
    ProgramMaskSequence,
    ProgramPrefixState,
    ProgramSequenceInputs,
)
from kagg_revue.policy.programs.model import ConditionalProgramPolicy
from kagg_revue.policy.programs.native import (
    NativeProgramContract,
    decision_inputs,
)

IntArray = NDArray[np.int64]


@dataclass(frozen=True)
class CompiledProgramBatch:
    """Fixed-width numeric official actions from the native compiler."""

    tokens: IntArray
    quantities: IntArray
    decision_counts: IntArray
    unit_counts: IntArray

    def validate(self, batch: int, maximum_decisions: int) -> None:
        """Reject incomplete or misaligned native action buffers."""
        expected = (batch, maximum_decisions)
        if self.tokens.shape != expected or self.quantities.shape != expected:
            raise ValueError("conditional-program compiled buffers have the wrong shape")
        if self.decision_counts.shape != (batch,) or self.unit_counts.shape != (batch,):
            raise ValueError("conditional-program compiled counts have the wrong shape")
        if np.any(
            (self.decision_counts < self.unit_counts)
            | (self.decision_counts > maximum_decisions)
            | (self.unit_counts < 1)
        ):
            raise ValueError("conditional-program compiled counts are outside the ABI")


@dataclass(frozen=True)
class ProgramTurnTrace:
    """Compact exact behavior data for every microdecision in one turn."""

    scalars: NDArray[np.int16] | Tensor
    root_features: NDArray[np.float32] | Tensor
    option_features: NDArray[np.int32] | Tensor
    target_reservations: NDArray[np.int16] | Tensor
    actions: IntArray | Tensor
    conditional_masks: NDArray[np.bool_] | Tensor
    quantity_max: IntArray | Tensor
    decision_counts: NDArray[np.int16] | Tensor
    old_joint_log_probability: NDArray[np.float32] | Tensor
    old_values: NDArray[np.float32] | Tensor
    stochastic_factor_counts: NDArray[np.int16] | Tensor


@dataclass(frozen=True)
class ProgramTurnRollout:
    """One native action batch and its exact high-level policy trace."""

    compiled: CompiledProgramBatch
    trace: ProgramTurnTrace
    trace_decision_counts_host: NDArray[np.int16] | None = None


def program_context(architecture: ActorArchitecture, context: TurnContext) -> tuple[Tensor, Tensor]:
    """Extract the causal history token and all own-tile scene tokens."""
    tiles = architecture.board_shape[-1] ** 2
    start = 1 + architecture.latent_tokens
    stop = start + tiles
    if (
        context.memory.ndim != 3
        or context.memory.shape[1] < stop
        or context.memory.shape[2] != architecture.model_width
    ):
        raise ValueError("turn context cannot expose the lossless own-board pointer")
    return context.memory[:, 0], context.memory[:, start:stop]


def compact_mask_width(contract: NativeProgramContract) -> int:
    """Return the packed-by-field bool width persisted per microdecision."""
    return (
        contract.control_count
        + contract.direction_count
        + contract.task_count
        + contract.argument_count
        + contract.tile_count
        + contract.raw_operation_count
        + contract.quantity_mode_count
        + contract.market_order_count
        + contract.item_count
    )


def split_compact_masks(values: Tensor, contract: NativeProgramContract) -> tuple[Tensor, ...]:
    """Split one compact mask tensor in the stable replay-field order."""
    widths = (
        contract.control_count,
        contract.direction_count,
        contract.task_count,
        contract.argument_count,
        contract.tile_count,
        contract.raw_operation_count,
        contract.quantity_mode_count,
        contract.market_order_count,
        contract.item_count,
    )
    if values.shape[-1] != sum(widths):
        raise ValueError("conditional-program compact mask width differs from ABI")
    return torch.split(values, list(widths), dim=-1)


def _active_raw(raw: Mapping[str, Any], rows: NDArray[np.int64]) -> dict[str, Any]:
    first = np.asarray(next(iter(raw.values())))
    if rows.shape == (first.shape[0],) and np.array_equal(
        rows, np.arange(first.shape[0], dtype=np.int64)
    ):
        return dict(raw)
    return {name: np.asarray(value)[rows] for name, value in raw.items()}


def _action_tensor(output: Any) -> Tensor:
    actions = output.actions
    return torch.stack(
        (
            actions.control,
            actions.task,
            actions.target,
            actions.argument,
            actions.direction,
            actions.raw_operation,
            actions.quantity_mode,
            actions.exact_quantity,
            actions.market_order,
        ),
        dim=1,
    )


def _mask_tensor(output: Any) -> Tensor:
    masks = output.masks
    return torch.cat(
        (
            masks.control,
            masks.direction,
            masks.task,
            masks.argument,
            masks.target,
            masks.raw_operation,
            masks.quantity_mode,
            masks.market_order,
            masks.market_item,
        ),
        dim=1,
    )


def trace_sequence(
    trace: ProgramTurnTrace,
    context: Tensor,
    tile_tokens: Tensor,
    contract: NativeProgramContract,
    *,
    device: torch.device | str,
    validate: bool = False,
) -> tuple[ProgramSequenceInputs, ProgramActionSequence, ProgramMaskSequence]:
    """Move one compact behavior trace into teacher-forced sequence tensors."""
    batch = trace.decision_counts.shape[0]
    decisions = (
        trace.actions.shape[1]
        if isinstance(trace.decision_counts, Tensor)
        else int(trace.decision_counts.max(initial=0))
    )
    if decisions < 1:
        raise ValueError("conditional-program trace contains no decision")

    def tensor(value: object, dtype: torch.dtype) -> Tensor:
        if isinstance(value, Tensor):
            return value.to(device=device, dtype=dtype, non_blocking=True)
        return torch.as_tensor(np.asarray(value), dtype=dtype, device=device)

    scalars = tensor(trace.scalars[:, :decisions], torch.long)
    action_values = tensor(trace.actions[:, :decisions], torch.long)
    compact_masks = tensor(trace.conditional_masks[:, :decisions], torch.bool)
    (
        control,
        direction,
        task,
        argument,
        target,
        raw_operation,
        quantity_mode,
        market_order,
        market_item,
    ) = split_compact_masks(compact_masks, contract)
    counts = tensor(trace.decision_counts, torch.long)
    decision_mask = torch.arange(decisions, device=counts.device)[None] < counts[:, None]

    def padded(mask: Tensor) -> Tensor:
        fallback = torch.zeros_like(mask)
        fallback[..., 0] = True
        return torch.where(decision_mask[:, :, None], mask, fallback)

    control = padded(control)
    direction = padded(direction)
    task = padded(task)
    argument = padded(argument)
    target = padded(target)
    raw_operation = padded(raw_operation)
    quantity_mode = padded(quantity_mode)
    market_order = padded(market_order)
    market_item = padded(market_item)
    inputs = ProgramSequenceInputs(
        context=context.to(device),
        tile_tokens=tile_tokens.to(device),
        root_features=tensor(trace.root_features[:, :decisions], torch.float32),
        option_features=tensor(trace.option_features[:, :decisions], torch.long),
        target_reservations=tensor(trace.target_reservations[:, :decisions], torch.int16),
        phase=scalars[:, :, 0],
        unit_index=scalars[:, :, 1],
        market_slot=scalars[:, :, 2],
        unit_count=scalars[:, :, 3].clamp_min(1),
        current_x=scalars[:, :, 4],
        current_y=scalars[:, :, 5],
        forced=scalars[:, :, 6],
        decision_mask=decision_mask,
    )
    actions = ProgramActionSequence(
        control=action_values[:, :, 0],
        task=action_values[:, :, 1],
        target=action_values[:, :, 2],
        argument=action_values[:, :, 3],
        direction=action_values[:, :, 4],
        raw_operation=action_values[:, :, 5],
        quantity_mode=action_values[:, :, 6],
        exact_quantity=action_values[:, :, 7],
        market_order=action_values[:, :, 8],
    )
    masks = ProgramMaskSequence(
        control=control,
        direction=direction,
        task=task,
        argument=argument,
        target=target,
        raw_operation=raw_operation,
        quantity_mode=quantity_mode,
        market_order=market_order,
        market_item=market_item,
        quantity_max=tensor(trace.quantity_max[:, :decisions], torch.long),
    )
    if validate:
        inputs.validate(contract, context.shape[-1])
        actions.validate(batch, decisions)
        masks.validate(batch, decisions, contract)
    return inputs, actions, masks


@torch.inference_mode()
def decode_program_turn_cuda(
    policy: ConditionalProgramPolicy,
    contract: NativeProgramContract,
    graph: ProgramGpuTurnSwitchGraph,
    compact_state: Tensor,
    context: Tensor,
    tile_tokens: Tensor,
    *,
    step: int,
    compiled_destinations: tuple[Tensor, ...] | None = None,
    trace_destinations: tuple[Tensor, ...] | None = None,
) -> ProgramTurnRollout:
    """Run the complete causal program on CUDA with one turn-boundary download."""
    batch = compact_state.shape[0]
    if (
        compact_state.device.type != "cuda"
        or compact_state.dtype != torch.int32
        or context.shape != (batch, policy.architecture.context_width)
        or tile_tokens.shape != (batch, contract.tile_count, policy.architecture.context_width)
    ):
        raise ValueError("CUDA program turn inputs are not aligned")
    with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
        prefix = policy.initial_prefix(context)
        prepared = policy.prepare_rollout(context, tile_tokens)
        graph.decode(compact_state, step, prepared, prefix)
    official_values, trace_values, raw_trace_counts_host = graph.copy_turn_to_host(
        compiled_destinations=compiled_destinations,
        trace_destinations=trace_destinations,
    )
    trace_counts_host = cast(
        NDArray[np.int16] | None, raw_trace_counts_host
    )
    tokens, quantities, decision_counts, unit_counts = (
        np.asarray(value) for value in official_values
    )
    (
        scalars,
        root,
        option,
        reservations,
        actions,
        conditional_masks,
        quantity_max,
        trace_counts,
        old_joint,
        old_values,
        factor_counts,
    ) = (
        value if isinstance(value, Tensor) else np.asarray(value)
        for value in trace_values
    )
    compiled = CompiledProgramBatch(
        tokens=tokens,
        quantities=quantities,
        decision_counts=decision_counts,
        unit_counts=unit_counts,
    )
    compiled.validate(batch, contract.maximum_decisions)
    return ProgramTurnRollout(
        compiled=compiled,
        trace=ProgramTurnTrace(
            scalars=scalars,
            root_features=root,
            option_features=option,
            target_reservations=reservations,
            actions=actions,
            conditional_masks=conditional_masks,
            quantity_max=quantity_max,
            decision_counts=trace_counts,
            old_joint_log_probability=old_joint,
            old_values=old_values,
            stochastic_factor_counts=factor_counts,
        ),
        trace_decision_counts_host=trace_counts_host,
    )


@torch.inference_mode()
def decode_program_turn(
    backend: Any,
    policy: ConditionalProgramPolicy,
    contract: NativeProgramContract,
    sessions: Sequence[Any],
    engines: Sequence[Any],
    players: IntArray,
    context: Tensor,
    tile_tokens: Tensor,
    *,
    workers: int,
    sample: bool,
    generator: torch.Generator | None = None,
    validate_inputs: bool = False,
    decision_graphs: (
        tuple[ProgramDecisionGraph, ProgramDecisionGraph]
        | ProgramDecisionGraphPool
        | ProgramDecisionGraphShards
        | None
    ) = None,
    timings: MutableMapping[str, float] | None = None,
) -> ProgramTurnRollout:
    """Sample a full unit/market sequence while C++ owns all transitions."""
    batch = len(sessions)
    if (
        batch < 1
        or len(engines) != batch
        or players.shape != (batch,)
        or context.shape != (batch, policy.architecture.context_width)
        or tile_tokens.shape
        != (
            batch,
            contract.tile_count,
            policy.architecture.context_width,
        )
        or workers < 1
    ):
        raise ValueError("conditional-program rollout inputs are not aligned")
    device = context.device
    prefix = policy.initial_prefix(context)
    prepared = policy.prepare_rollout(context, tile_tokens) if decision_graphs is not None else None
    capacity = contract.maximum_decisions
    mask_width = compact_mask_width(contract)
    compact_observations = isinstance(
        decision_graphs,
        (ProgramDecisionGraphPool, ProgramDecisionGraphShards),
    )
    gpu_trace = (
        ProgramGpuTrace(batch, capacity, mask_width, prefix.hidden)
        if compact_observations
        else None
    )
    shard_ready_event = (
        torch.cuda.Event()  # type: ignore[no-untyped-call]
        if isinstance(decision_graphs, ProgramDecisionGraphShards)
        else None
    )
    if shard_ready_event is not None:
        shard_ready_event.record(torch.cuda.current_stream(device))
    scalars = np.zeros((batch, capacity, 7), dtype=np.int16)
    root = np.zeros((batch, capacity, contract.root_feature_count), dtype=np.float32)
    option = np.zeros((batch, capacity, contract.option_feature_count), dtype=np.int32)
    reservations = np.zeros((batch, capacity, contract.tile_count), dtype=np.int16)
    selected_actions = (
        None if gpu_trace is not None else np.zeros((batch, capacity, 9), dtype=np.int64)
    )
    selected_masks = (
        None if gpu_trace is not None else np.zeros((batch, capacity, mask_width), dtype=np.bool_)
    )
    quantity_max = None if gpu_trace is not None else np.zeros((batch, capacity), dtype=np.int64)
    counts = np.zeros(batch, dtype=np.int16)
    old_joint = (
        None if gpu_trace is not None else torch.zeros(batch, dtype=torch.float32, device=device)
    )
    old_values = (
        None if gpu_trace is not None else torch.zeros(batch, dtype=torch.float32, device=device)
    )
    factor_counts = (
        None if gpu_trace is not None else torch.zeros(batch, dtype=torch.int32, device=device)
    )
    recorded_value = (
        None if gpu_trace is not None else torch.zeros(batch, dtype=torch.bool, device=device)
    )
    session_list = list(sessions)
    engine_list = list(engines)
    completed = False
    for _decision in range(capacity):
        phase_started = time.perf_counter()
        raw = cast(
            Mapping[str, Any],
            (
                backend.conditional_program_active_observations_batch(
                    session_list, engine_list, players, workers
                )
                if compact_observations
                else backend.conditional_program_observations_batch(
                    session_list, engine_list, players, workers
                )
            ),
        )
        if timings is not None:
            timings["native_observe"] = timings.get("native_observe", 0.0) + (
                time.perf_counter() - phase_started
            )
        phase_started = time.perf_counter()
        raw_scalars = np.asarray(raw["scalars"], dtype=np.int64)
        if compact_observations:
            active = np.asarray(raw["active_rows"], dtype=np.int64)
            if raw_scalars.shape != (active.size, 7):
                raise ValueError("conditional-program compact scalar batch is malformed")
            source_rows = np.arange(active.size, dtype=np.int64)
        else:
            if raw_scalars.shape != (batch, 7):
                raise ValueError("conditional-program native scalar batch is malformed")
            active = np.flatnonzero(raw_scalars[:, 0] != 2).astype(np.int64, copy=False)
            source_rows = active
        if not active.size:
            completed = True
            break
        positions = counts[active].astype(np.int64, copy=False)
        indices: Tensor | None = None
        trace_rows: Tensor | None = None
        output_rows: Tensor | None = None
        output_prefix_rows: int | None = None
        output: Any | None = None
        action_values: NDArray[np.int64] | None = None
        if isinstance(decision_graphs, ProgramDecisionGraphShards):
            if prepared is None or gpu_trace is None:
                raise RuntimeError("sharded program graph lacks CUDA turn state")
            action_values = np.empty((len(active), 9), dtype=np.int64)
            if shard_ready_event is None:
                raise RuntimeError("sharded program graph lost its ready event")
            executions: list[tuple[torch.cuda.Stream, ProgramDecisionGraph, int, int]] = []
            shard_count = min(len(decision_graphs.shards), len(active))
            for shard_index in range(shard_count):
                start = len(active) * shard_index // shard_count
                stop = len(active) * (shard_index + 1) // shard_count
                shard = decision_graphs.shards[shard_index]
                shard_active = active[start:stop]
                shard_sources = source_rows[start:stop]
                padded = shard.graphs.padded_rows(shard_active)
                padded_sources = np.concatenate(
                    (
                        shard_sources,
                        np.full(
                            len(padded) - len(shard_sources),
                            shard_sources[-1],
                            dtype=np.int64,
                        ),
                    )
                )
                with torch.cuda.stream(shard.stream):
                    shard.stream.wait_event(shard_ready_event)
                    graph = shard.graphs.variant(len(padded), compute_outcome=_decision == 0)
                    if graph.captured:
                        output = graph.decode_native(
                            raw,
                            padded_sources,
                            padded,
                            prepared,
                            prefix,
                        )
                        trace_rows = graph.model_rows
                    else:
                        padded_indices = torch.as_tensor(padded, dtype=torch.long, device=device)
                        graph_raw = _active_raw(raw, padded_sources)
                        graph_prepared = ProgramPreparedContext(
                            context=prepared.context.index_select(0, padded_indices),
                            target_keys=prepared.target_keys.index_select(0, padded_indices),
                        )
                        graph_inputs, graph_masks = decision_inputs(
                            graph_raw,
                            graph_prepared.context,
                            graph_prepared.target_keys,
                            contract,
                            device=device,
                            validate=False,
                        )
                        graph_prefix = ProgramPrefixState(
                            prefix.hidden.index_select(0, padded_indices)
                        )
                        output = graph.decode(
                            graph_inputs,
                            graph_masks,
                            graph_prefix,
                            graph_prepared,
                        )
                        trace_rows = padded_indices
                    graph.record(gpu_trace, trace_rows, stop - start)
                    graph.enqueue_actions_to_host(stop - start)
                executions.append((shard.stream, graph, start, stop))
            for stream, graph, start, stop in executions:
                stream.synchronize()
                action_values[start:stop] = graph.host_actions(stop - start)
            mask_values = None
            maximum_values = None
        elif isinstance(decision_graphs, ProgramDecisionGraphPool):
            padded = decision_graphs.padded_rows(active)
            padded_source_rows = np.concatenate(
                (
                    source_rows,
                    np.full(
                        len(padded) - len(source_rows),
                        source_rows[-1],
                        dtype=np.int64,
                    ),
                )
            )
            if prepared is None:
                raise RuntimeError("program graph lacks turn-static features")
            graph = decision_graphs.variant(len(padded), compute_outcome=_decision == 0)
            if graph.captured:
                output = graph.decode_native(
                    raw,
                    padded_source_rows,
                    padded,
                    prepared,
                    prefix,
                )
                trace_rows = graph.model_rows
            else:
                padded_indices = torch.as_tensor(padded, dtype=torch.long, device=device)
                graph_raw = _active_raw(raw, padded_source_rows)
                graph_prepared = ProgramPreparedContext(
                    context=prepared.context.index_select(0, padded_indices),
                    target_keys=prepared.target_keys.index_select(0, padded_indices),
                )
                graph_inputs, graph_masks = decision_inputs(
                    graph_raw,
                    graph_prepared.context,
                    graph_prepared.target_keys,
                    contract,
                    device=device,
                    validate=False,
                )
                graph_prefix = ProgramPrefixState(prefix.hidden.index_select(0, padded_indices))
                output = graph.decode(
                    graph_inputs,
                    graph_masks,
                    graph_prefix,
                    graph_prepared,
                )
                trace_rows = padded_indices
            output_prefix_rows = len(active)
        elif decision_graphs is not None:
            indices = torch.as_tensor(active, dtype=torch.long, device=device)
            if prepared is None:
                raise RuntimeError("program graph lacks turn-static features")
            full_inputs, full_masks = decision_inputs(
                raw,
                prepared.context,
                prepared.target_keys,
                contract,
                device=device,
                validate=False,
            )
            graph = decision_graphs[0 if _decision == 0 else 1]
            output = graph.decode(
                full_inputs,
                full_masks,
                prefix,
                prepared,
            )
            output_rows = indices
        else:
            indices = torch.as_tensor(active, dtype=torch.long, device=device)
            active_raw = _active_raw(raw, active)
            active_inputs, active_masks = decision_inputs(
                active_raw,
                context.index_select(0, indices),
                tile_tokens.index_select(0, indices),
                contract,
                device=device,
                validate=validate_inputs,
            )
            active_prefix = ProgramPrefixState(prefix.hidden.index_select(0, indices))
            output = policy.rollout_step(
                active_inputs,
                active_masks,
                active_prefix,
                sample=sample,
                generator=generator,
                compute_entropy=False,
                compute_outcome=_decision == 0,
                validate_inputs=validate_inputs,
            )
        if isinstance(decision_graphs, ProgramDecisionGraphShards):
            if action_values is None:
                raise RuntimeError("sharded program graph returned no actions")
        elif gpu_trace is not None:
            if not isinstance(decision_graphs, ProgramDecisionGraphPool):
                raise RuntimeError("CUDA program trace requires graph pooling")
            if trace_rows is None:
                raise RuntimeError("program graph lost its model row mapping")
            graph.record(gpu_trace, trace_rows, len(active))
            action_values = graph.copy_actions_to_host(len(active))
            mask_values = None
            maximum_values = None
        else:
            if output is None:
                raise RuntimeError("conditional-program policy returned no output")
            joint_tensor = output.joint_log_probability
            factor_tensor = output.factor_counts
            value_tensor = output.value
            hidden_tensor = output.next_prefix.hidden
            if output_prefix_rows is not None:
                joint_tensor = joint_tensor[:output_prefix_rows]
                factor_tensor = factor_tensor[:output_prefix_rows]
                value_tensor = value_tensor[:output_prefix_rows]
                hidden_tensor = hidden_tensor[:output_prefix_rows]
            elif output_rows is not None:
                joint_tensor = joint_tensor.index_select(0, output_rows)
                factor_tensor = factor_tensor.index_select(0, output_rows)
                value_tensor = value_tensor.index_select(0, output_rows)
                hidden_tensor = hidden_tensor.index_select(0, output_rows)
            action_tensor = _action_tensor(output)
            mask_tensor = _mask_tensor(output)
            maximum_tensor = output.masks.quantity_max
            if output_rows is not None:
                action_tensor = action_tensor.index_select(0, output_rows)
                mask_tensor = mask_tensor.index_select(0, output_rows)
                maximum_tensor = maximum_tensor.index_select(0, output_rows)
            action_values = action_tensor.detach().to(device="cpu", dtype=torch.int64).numpy()
            mask_values = mask_tensor.detach().to(device="cpu", dtype=torch.bool).numpy()
            maximum_values = maximum_tensor.detach().to(device="cpu", dtype=torch.int64).numpy()
        if action_values is None:
            raise RuntimeError("conditional-program policy returned no actions")
        if timings is not None:
            timings["policy_roundtrip"] = timings.get("policy_roundtrip", 0.0) + (
                time.perf_counter() - phase_started
            )
        phase_started = time.perf_counter()
        selections = np.zeros((batch, 8), dtype=np.int64)
        phase = raw_scalars[source_rows, 0]
        selections[active, 0] = action_values[:, 0]
        selections[active, 1] = np.where(phase == 0, action_values[:, 1], action_values[:, 8])
        selections[active, 2:8] = action_values[:, 2:8]
        enabled = np.zeros(batch, dtype=np.uint8)
        enabled[active] = 1
        if timings is not None:
            timings["selection_prepare"] = timings.get("selection_prepare", 0.0) + (
                time.perf_counter() - phase_started
            )
        phase_started = time.perf_counter()
        backend.conditional_program_select_batch(
            session_list,
            engine_list,
            players,
            selections,
            enabled,
            workers,
        )
        if timings is not None:
            timings["native_select"] = timings.get("native_select", 0.0) + (
                time.perf_counter() - phase_started
            )

        phase_started = time.perf_counter()
        scalars[active, positions] = raw_scalars[source_rows].astype(np.int16)
        root[active, positions] = np.asarray(raw["root_features"], dtype=np.float32)[source_rows]
        option[active, positions] = np.asarray(raw["option_features"], dtype=np.int32)[source_rows]
        reservations[active, positions] = np.asarray(raw["target_reservations"], dtype=np.int16)[
            source_rows
        ]
        if gpu_trace is None:
            if (
                selected_actions is None
                or selected_masks is None
                or quantity_max is None
                or mask_values is None
                or maximum_values is None
                or indices is None
                or old_joint is None
                or old_values is None
                or factor_counts is None
                or recorded_value is None
            ):
                raise RuntimeError("host program trace lost its working buffers")
            selected_actions[active, positions] = action_values
            selected_masks[active, positions] = mask_values
            quantity_max[active, positions] = maximum_values
            old_joint.index_add_(0, indices, joint_tensor.detach().float())
            factor_counts.index_add_(0, indices, factor_tensor.detach().to(torch.int32))
            first = ~recorded_value.index_select(0, indices)
            current_values = old_values.index_select(0, indices)
            old_values.index_copy_(
                0,
                indices,
                torch.where(first, value_tensor.detach().float(), current_values),
            )
            recorded_value.index_fill_(0, indices, True)
            next_hidden = prefix.hidden.clone()
            next_hidden.index_copy_(0, indices, hidden_tensor)
            prefix = ProgramPrefixState(next_hidden)
        counts[active] += 1
        if timings is not None:
            timings["trace_update"] = timings.get("trace_update", 0.0) + (
                time.perf_counter() - phase_started
            )
    phase_started = time.perf_counter()
    if not completed:
        final = cast(
            Mapping[str, Any],
            (
                backend.conditional_program_active_observations_batch(
                    session_list, engine_list, players, workers
                )
                if compact_observations
                else backend.conditional_program_observations_batch(
                    session_list, engine_list, players, workers
                )
            ),
        )
        incomplete = (
            np.asarray(final["active_rows"], dtype=np.int64).size > 0
            if compact_observations
            else np.any(np.asarray(final["scalars"], dtype=np.int64)[:, 0] != 2)
        )
        if incomplete:
            raise RuntimeError("conditional-program decoding exceeded its ABI capacity")

    raw_actions = cast(
        Mapping[str, object],
        backend.conditional_program_actions_batch(session_list, engine_list, players, workers),
    )
    compiled = CompiledProgramBatch(
        tokens=np.ascontiguousarray(raw_actions["tokens"], dtype=np.int64),
        quantities=np.ascontiguousarray(raw_actions["quantities"], dtype=np.int64),
        decision_counts=np.ascontiguousarray(raw_actions["decision_counts"], dtype=np.int64),
        unit_counts=np.ascontiguousarray(raw_actions["unit_counts"], dtype=np.int64),
    )
    compiled.validate(batch, contract.maximum_decisions)
    if np.any(counts < compiled.unit_counts):
        raise RuntimeError("conditional-program trace lacks one choice per unit")
    if gpu_trace is not None:
        (
            selected_actions,
            selected_masks,
            quantity_max,
            _gpu_counts,
            old_joint_values,
            old_value_values,
            factor_count_values,
        ) = gpu_trace.copy_to_host()
    else:
        if (
            selected_actions is None
            or selected_masks is None
            or quantity_max is None
            or old_joint is None
            or old_values is None
            or factor_counts is None
        ):
            raise RuntimeError("host program trace is incomplete")
        old_joint_values = old_joint.cpu().numpy()
        old_value_values = old_values.cpu().numpy()
        factor_count_values = factor_counts.to(torch.int16).cpu().numpy()
    result = ProgramTurnRollout(
        compiled=compiled,
        trace=ProgramTurnTrace(
            scalars=scalars,
            root_features=root,
            option_features=option,
            target_reservations=reservations,
            actions=selected_actions,
            conditional_masks=selected_masks,
            quantity_max=quantity_max,
            decision_counts=counts,
            old_joint_log_probability=old_joint_values,
            old_values=old_value_values,
            stochastic_factor_counts=factor_count_values,
        ),
    )
    if timings is not None:
        timings["native_finalize"] = timings.get("native_finalize", 0.0) + (
            time.perf_counter() - phase_started
        )
    return result


__all__ = [
    "CompiledProgramBatch",
    "ProgramTurnRollout",
    "ProgramTurnTrace",
    "compact_mask_width",
    "decode_program_turn",
    "program_context",
    "split_compact_masks",
    "trace_sequence",
]
