"""Captured H200 execution of a complete CUDA-resident turn compiler."""

from __future__ import annotations

import time
from dataclasses import fields

import torch
from torch import Tensor

from kagg_revue.native import _program_cuda
from kagg_revue.policy.cuda.capture import (
    serialized_graph_build,
    serialized_graph_capture,
)
from kagg_revue.policy.programs.encoding import ProgramPreparedContext
from kagg_revue.policy.programs.gpu.compiler import (
    ProgramGpuCompiler,
    ProgramGpuCompilerOutput,
)
from kagg_revue.policy.programs.gpu.trace import ProgramGpuFullTrace
from kagg_revue.policy.programs.grammar import (
    NativeProgramMasks,
    ProgramActions,
    ProgramDecisionInputs,
    ProgramPrefixState,
)
from kagg_revue.policy.programs.model import ConditionalProgramPolicy
from kagg_revue.policy.programs.native import NativeProgramContract


class ProgramGpuTurnSwitchGraph:
    """Hopper conditional graph with power-of-two active-row dispatch."""

    _MUTABLE_COMPILER_FIELDS = (
        "option_valid",
        "option_task",
        "option_target",
        "option_argument",
        "option_quantity_mode",
        "option_exact",
        "option_phase",
        "option_created_step",
        "forced_target",
        "forced_owner",
        "last_day",
        "step",
        "state",
        "tokens",
        "quantities",
        "trace_counts",
        "turn_unit_counts",
    )

    def __init__(
        self,
        policy: ConditionalProgramPolicy,
        contract: NativeProgramContract,
        batch: int,
        generator: torch.Generator,
        *,
        episode_steps: int,
        turns_per_day: int,
        sample: bool = True,
    ) -> None:
        """Allocate one fixed production batch and its graph specializations."""
        device = next(policy.parameters()).device
        if device.type != "cuda":
            raise ValueError("conditional program switch graph requires CUDA")
        self.policy = policy
        self.contract = contract
        self.batch = batch
        self.device = device
        self.sample = sample
        self.compiler = ProgramGpuCompiler(
            contract,
            batch,
            device,
            episode_steps=episode_steps,
            turns_per_day=turns_per_day,
        )
        self.compiled_decision = torch.compile(
            self.compiler.decision,
            fullgraph=True,
            dynamic=False,
            mode="max-autotune-no-cudagraphs",
        )
        self.compiled_apply = torch.compile(
            self.compiler.apply_selection,
            fullgraph=True,
            dynamic=False,
            mode="max-autotune-no-cudagraphs",
        )
        width = policy.architecture.model_width
        self.prepared = ProgramPreparedContext(
            context=torch.empty((batch, width), dtype=torch.bfloat16, device=device),
            target_keys=torch.empty(
                (batch, contract.tile_count, width),
                dtype=torch.bfloat16,
                device=device,
            ),
        )
        self.prefix = ProgramPrefixState(
            torch.empty((batch, width), dtype=torch.bfloat16, device=device)
        )
        action_values = {
            field.name: torch.zeros(batch, dtype=torch.long, device=device)
            for field in fields(ProgramActions)
        }
        self.actions = ProgramActions(**action_values)
        self.quantity_max = torch.zeros(batch, dtype=torch.long, device=device)
        mask_width = (
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
        self.trace = ProgramGpuFullTrace(
            batch,
            contract.maximum_decisions,
            contract.root_feature_count,
            contract.option_feature_count,
            contract.tile_count,
            mask_width,
            device,
        )
        capacity = contract.maximum_decisions
        self._host_output = (
            torch.empty((batch, capacity), dtype=torch.long, device="cpu", pin_memory=True),
            torch.empty((batch, capacity), dtype=torch.long, device="cpu", pin_memory=True),
            torch.empty(batch, dtype=torch.long, device="cpu", pin_memory=True),
            torch.empty(batch, dtype=torch.long, device="cpu", pin_memory=True),
        )
        self._host_trace_counts = torch.empty(
            batch, dtype=torch.int16, device="cpu", pin_memory=True
        )
        self.active_count = torch.zeros((), dtype=torch.long, device=device)
        self.row_order = torch.arange(batch, dtype=torch.long, device=device)
        self.active = torch.ones(batch, dtype=torch.bool, device=device)
        self.inputs: ProgramDecisionInputs | None = None
        self.masks: NativeProgramMasks | None = None
        self.setup_graph: torch.cuda.CUDAGraph | None = None
        self.variant_graphs: list[torch.cuda.CUDAGraph] = []
        self.conditional: _program_cuda.ConditionalSwitchWhileGraph | None = None
        buckets = []
        bucket = 1
        while bucket < batch:
            buckets.append(bucket)
            bucket *= 2
        buckets.append(batch)
        self.buckets = tuple(buckets)
        base_seed = generator.initial_seed()
        self.generators = []
        for index in range(len(self.buckets)):
            variant_generator = torch.Generator(device=device)
            variant_generator.manual_seed(base_seed + index * 2_000_033)
            self.generators.append(variant_generator)
        self.capture_seconds = 0.0

    def manual_seed(self, seed: int) -> None:
        """Reset every shape-specialized RNG without synchronizing the host."""
        for index, generator in enumerate(self.generators):
            generator.manual_seed(seed + index * 2_000_033)

    def reset(self) -> None:
        """Drop options when this fixed collector is rebound to new games."""
        self.compiler.reset()

    def _install_static(
        self,
        prepared: ProgramPreparedContext,
        prefix: ProgramPrefixState,
    ) -> None:
        self.prepared.context.copy_(prepared.context)
        self.prepared.target_keys.copy_(prepared.target_keys)
        self.prefix.hidden.copy_(prefix.hidden)

    def _setup(self) -> None:
        inputs, masks, active = self.compiled_decision(self.prepared, self.prefix)
        count = active.sum(dtype=torch.long)
        live = torch.nonzero_static(active, size=self.batch).squeeze(1)
        dead = torch.nonzero_static(~active, size=self.batch, fill_value=0).squeeze(1)
        positions = torch.arange(self.batch, dtype=torch.long, device=self.device)
        dead_position = (positions - count).clamp(0, self.batch - 1)
        order = torch.where(positions < count, live.clamp_min(0), dead[dead_position])
        self.active_count.copy_(count)
        self.row_order.copy_(order)
        self.active.copy_(active)
        self.inputs = inputs
        self.masks = masks

    @staticmethod
    def _select_inputs(inputs: ProgramDecisionInputs, rows: Tensor) -> ProgramDecisionInputs:
        values = {
            field.name: getattr(inputs, field.name).index_select(0, rows)
            for field in fields(ProgramDecisionInputs)
        }
        return ProgramDecisionInputs(**values)

    @staticmethod
    def _select_masks(masks: NativeProgramMasks, rows: Tensor) -> NativeProgramMasks:
        values = {
            field.name: getattr(masks, field.name).index_select(0, rows)
            for field in fields(NativeProgramMasks)
        }
        return NativeProgramMasks(**values)

    def _variant(self, index: int) -> None:
        inputs = self.inputs
        masks = self.masks
        if inputs is None or masks is None:
            raise RuntimeError("program switch graph setup is absent")
        bucket = self.buckets[index]
        rows = self.row_order[:bucket]
        selected_inputs = self._select_inputs(inputs, rows)
        selected_masks = self._select_masks(masks, rows)
        selected_prefix = ProgramPrefixState(self.prefix.hidden.index_select(0, rows))
        selected_prepared = ProgramPreparedContext(
            context=self.prepared.context.index_select(0, rows),
            target_keys=self.prepared.target_keys.index_select(0, rows),
        )
        output = self.policy.rollout_step(
            selected_inputs,
            selected_masks,
            selected_prefix,
            sample=self.sample,
            generator=self.generators[index],
            compute_entropy=False,
            compute_outcome=True,
            validate_inputs=False,
            static_execution=True,
            prepared=selected_prepared,
        )
        selected_active = self.active.index_select(0, rows)
        self.trace.append(rows, selected_active, selected_inputs, output)
        for field in fields(ProgramActions):
            target = getattr(self.actions, field.name)
            source = getattr(output.actions, field.name)
            target.index_copy_(0, rows, torch.where(selected_active, source, target[rows]))
        self.quantity_max.index_copy_(
            0,
            rows,
            torch.where(
                selected_active,
                output.masks.quantity_max,
                self.quantity_max[rows],
            ),
        )
        old_prefix = self.prefix.hidden.index_select(0, rows)
        self.prefix.hidden.index_copy_(
            0,
            rows,
            torch.where(selected_active[:, None], output.next_prefix.hidden, old_prefix),
        )
        self.compiled_apply(self.actions, self.quantity_max, self.active)

    def _snapshot(self) -> tuple[dict[str, Tensor], Tensor, dict[str, Tensor], Tensor]:
        compiler = {
            name: getattr(self.compiler, name).clone() for name in self._MUTABLE_COMPILER_FIELDS
        }
        actions = {
            field.name: getattr(self.actions, field.name).clone()
            for field in fields(ProgramActions)
        }
        return compiler, self.prefix.hidden.clone(), actions, self.quantity_max.clone()

    def _restore(
        self,
        snapshot: tuple[dict[str, Tensor], Tensor, dict[str, Tensor], Tensor],
    ) -> None:
        compiler, prefix, actions, quantity_max = snapshot
        for name, value in compiler.items():
            getattr(self.compiler, name).copy_(value)
        self.prefix.hidden.copy_(prefix)
        for name, value in actions.items():
            getattr(self.actions, name).copy_(value)
        self.quantity_max.copy_(quantity_max)

    def _capture(self) -> None:
        started = time.perf_counter()
        self._setup()
        torch.cuda.current_stream(self.device).synchronize()
        setup = torch.cuda.CUDAGraph(keep_graph=True)
        with serialized_graph_capture(setup):
            self._setup()
        torch.cuda.current_stream(self.device).synchronize()
        self.setup_graph = setup
        snapshot = self._snapshot()
        for index, generator in enumerate(self.generators):
            generator_state = generator.get_state()
            self.trace.reset()
            self._variant(index)
            torch.cuda.current_stream(self.device).synchronize()
            self._restore(snapshot)
            generator.set_state(generator_state)
            self.trace.reset()
            graph = torch.cuda.CUDAGraph(keep_graph=True)
            graph.register_generator_state(generator)
            with serialized_graph_capture(graph):
                self._variant(index)
            torch.cuda.current_stream(self.device).synchronize()
            self._restore(snapshot)
            generator.set_state(generator_state)
            self.variant_graphs.append(graph)
        self.trace.reset()
        self.conditional = _program_cuda.ConditionalSwitchWhileGraph(
            setup.raw_cuda_graph(),
            [graph.raw_cuda_graph() for graph in self.variant_graphs],
            self.compiler.state.data_ptr(),
            self.active_count.data_ptr(),
            self.batch,
            self.compiler.layout.width,
        )
        self.capture_seconds = time.perf_counter() - started

    def decode(
        self,
        compact_state: Tensor,
        step: int,
        prepared: ProgramPreparedContext,
        prefix: ProgramPrefixState,
    ) -> ProgramGpuCompilerOutput:
        """Compile a turn with device-only active compaction and control flow."""
        self.compiler.begin_turn(compact_state, step)
        self.trace.reset()
        self._install_static(prepared, prefix)
        if self.conditional is None:
            with serialized_graph_build():
                self._capture()
        conditional = self.conditional
        if conditional is None:
            raise RuntimeError("conditional program switch graph capture failed")
        stream = torch.cuda.current_stream(self.device)
        conditional.launch(stream.cuda_stream)
        return self.compiler.output()

    def copy_trace_to_host(self) -> tuple[object, ...]:
        """Return the training trace after the final turn synchronization."""
        return self.trace.copy_to_host()

    def copy_turn_to_host(
        self,
        *,
        compiled_destinations: tuple[Tensor, ...] | None = None,
        trace_destinations: tuple[Tensor, ...] | None = None,
    ) -> tuple[tuple[object, ...], tuple[object, ...], object | None]:
        """Download only engine inputs while optionally retaining training data in HBM."""
        output = self.compiler.output()
        device_values = (
            output.tokens,
            output.quantities,
            output.decision_counts,
            output.unit_counts,
        )
        for host, value in zip(self._host_output, device_values, strict=True):
            host.copy_(value, non_blocking=True)
        if compiled_destinations is not None:
            if len(compiled_destinations) != 3:
                raise ValueError("compiled rollout destination count differs from its ABI")
            for destination, value in zip(
                compiled_destinations, device_values[:3], strict=True
            ):
                if (
                    destination.shape != value.shape
                    or destination.dtype != value.dtype
                    or destination.device != value.device
                ):
                    raise ValueError(
                        "compiled rollout destination changed shape, dtype, or device"
                    )
                destination.copy_(value, non_blocking=True)
        if trace_destinations is None:
            self.trace.enqueue_to_host()
            trace_counts: object | None = None
        else:
            self.trace.enqueue_to_device(trace_destinations)
            self._host_trace_counts.copy_(
                self.trace.device_values[7], non_blocking=True
            )
            trace_counts = self._host_trace_counts.numpy()
        torch.cuda.current_stream(self.device).synchronize()
        official = tuple(value.numpy() for value in self._host_output)
        trace_values: tuple[object, ...] = (
            tuple(trace_destinations)
            if trace_destinations is not None
            else self.trace.host_arrays()
        )
        return official, trace_values, trace_counts

    def close(self) -> None:
        """Release every graph and its conditional executable."""
        self.conditional = None
        for graph in self.variant_graphs:
            graph.reset()
        self.variant_graphs.clear()
        if self.setup_graph is not None:
            self.setup_graph.reset()
        self.setup_graph = None


__all__ = ["ProgramGpuTurnSwitchGraph"]
