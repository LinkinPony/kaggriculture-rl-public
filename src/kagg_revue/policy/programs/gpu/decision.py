"""Fixed-batch CUDA Graph for one conditional-program decision."""

from __future__ import annotations

import time
from collections.abc import Mapping
from dataclasses import dataclass

import numpy as np
import torch
from numpy.typing import NDArray

from kagg_revue.policy.cuda.capture import (
    capture_safe_graph_replay,
    serialized_graph_build,
    serialized_graph_capture,
)
from kagg_revue.policy.programs.encoding import ProgramPreparedContext
from kagg_revue.policy.programs.gpu.staging import (
    PinnedProgramDecisionStaging,
    PinnedProgramOutputStaging,
)
from kagg_revue.policy.programs.gpu.trace import ProgramGpuTrace
from kagg_revue.policy.programs.grammar import (
    NativeProgramMasks,
    ProgramDecisionInputs,
    ProgramPrefixState,
)
from kagg_revue.policy.programs.model import ConditionalProgramPolicy
from kagg_revue.policy.programs.schema import ProgramStepOutput


def _compact_actions(output: ProgramStepOutput) -> torch.Tensor:
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


def _compact_masks(output: ProgramStepOutput) -> torch.Tensor:
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


class ProgramDecisionGraph:
    """Replay the launch-heavy conditional policy at one fixed batch size."""

    def __init__(
        self,
        policy: ConditionalProgramPolicy,
        generator: torch.Generator,
        *,
        compute_outcome: bool,
        sample: bool = True,
    ) -> None:
        """Bind one policy, RNG stream, and static outcome-head mode."""
        if next(policy.parameters()).device.type != "cuda":
            raise ValueError("program decision graph requires a CUDA policy")
        self._policy = policy
        self._generator = generator
        self._compute_outcome = compute_outcome
        self._sample = sample
        self._inputs: ProgramDecisionInputs | None = None
        self._masks: NativeProgramMasks | None = None
        self._prefix: ProgramPrefixState | None = None
        self._prepared: ProgramPreparedContext | None = None
        self._output: ProgramStepOutput | None = None
        self._action_output: torch.Tensor | None = None
        self._mask_output: torch.Tensor | None = None
        self._factor_count_output: torch.Tensor | None = None
        self._decision_staging: PinnedProgramDecisionStaging | None = None
        self._output_staging: PinnedProgramOutputStaging | None = None
        self._graph: torch.cuda.CUDAGraph | None = None
        self.capture_seconds = 0.0

    @staticmethod
    def _allocate_inputs(
        inputs: ProgramDecisionInputs,
        prepared: ProgramPreparedContext | None,
    ) -> ProgramDecisionInputs:
        return ProgramDecisionInputs(
            context=(torch.empty_like(inputs.context) if prepared is None else prepared.context),
            tile_tokens=(
                torch.empty_like(inputs.tile_tokens) if prepared is None else prepared.target_keys
            ),
            root_features=torch.empty_like(inputs.root_features),
            option_features=torch.empty_like(inputs.option_features),
            target_reservations=torch.empty_like(inputs.target_reservations),
            phase=torch.empty_like(inputs.phase),
            unit_index=torch.empty_like(inputs.unit_index),
            market_slot=torch.empty_like(inputs.market_slot),
            unit_count=torch.empty_like(inputs.unit_count),
            current_x=torch.empty_like(inputs.current_x),
            current_y=torch.empty_like(inputs.current_y),
            forced=torch.empty_like(inputs.forced),
        )

    @staticmethod
    def _allocate_masks(masks: NativeProgramMasks) -> NativeProgramMasks:
        return NativeProgramMasks(
            control=torch.empty_like(masks.control),
            direction=torch.empty_like(masks.direction),
            task=torch.empty_like(masks.task),
            task_argument=torch.empty_like(masks.task_argument),
            task_target=torch.empty_like(masks.task_target),
            task_quantity_mode=torch.empty_like(masks.task_quantity_mode),
            task_quantity_max=torch.empty_like(masks.task_quantity_max),
            raw_operation=torch.empty_like(masks.raw_operation),
            raw_argument=torch.empty_like(masks.raw_argument),
            raw_quantity_mode=torch.empty_like(masks.raw_quantity_mode),
            raw_quantity_max=torch.empty_like(masks.raw_quantity_max),
            market_order=torch.empty_like(masks.market_order),
            market_item=torch.empty_like(masks.market_item),
            market_quantity_mode=torch.empty_like(masks.market_quantity_mode),
            market_quantity_max=torch.empty_like(masks.market_quantity_max),
        )

    @staticmethod
    def _allocate_prepared(
        prepared: ProgramPreparedContext,
    ) -> ProgramPreparedContext:
        return ProgramPreparedContext(
            context=torch.empty_like(prepared.context),
            target_keys=torch.empty_like(prepared.target_keys),
        )

    @staticmethod
    def _copy_fields(
        target: object,
        source: object,
        *,
        skip: frozenset[str] = frozenset(),
    ) -> None:
        for name in source.__dataclass_fields__:  # type: ignore[attr-defined]
            if name in skip:
                continue
            target_value = getattr(target, name)
            source_value = getattr(source, name)
            if target_value.shape != source_value.shape or target_value.dtype != source_value.dtype:
                raise ValueError("program decision graph tensor ABI changed")
            target_value.copy_(source_value)

    def _install(
        self,
        inputs: ProgramDecisionInputs,
        masks: NativeProgramMasks,
        prefix: ProgramPrefixState,
        prepared: ProgramPreparedContext | None,
    ) -> None:
        stored_inputs = self._inputs
        stored_masks = self._masks
        stored_prefix = self._prefix
        if stored_inputs is None or stored_masks is None or stored_prefix is None:
            raise RuntimeError("program decision graph has not been allocated")
        stored_prepared = self._prepared
        if (stored_prepared is None) != (prepared is None):
            raise ValueError("program decision graph preparation mode changed")
        if stored_prepared is not None and prepared is not None:
            self._copy_fields(stored_prepared, prepared)
            self._copy_fields(
                stored_inputs,
                inputs,
                skip=frozenset(("context", "tile_tokens")),
            )
        else:
            self._copy_fields(stored_inputs, inputs)
        self._copy_fields(stored_masks, masks)
        if (
            stored_prefix.hidden.shape != prefix.hidden.shape
            or stored_prefix.hidden.dtype != prefix.hidden.dtype
        ):
            raise ValueError("program decision graph prefix ABI changed")
        stored_prefix.hidden.copy_(prefix.hidden)

    def _run(
        self,
    ) -> tuple[ProgramStepOutput, torch.Tensor, torch.Tensor, torch.Tensor]:
        inputs = self._inputs
        masks = self._masks
        prefix = self._prefix
        if inputs is None or masks is None or prefix is None:
            raise RuntimeError("program decision graph inputs are absent")
        output = self._policy.rollout_step(
            inputs,
            masks,
            prefix,
            sample=self._sample,
            generator=self._generator,
            compute_entropy=False,
            compute_outcome=self._compute_outcome,
            validate_inputs=False,
            static_execution=True,
            prepared=self._prepared,
        )
        return (
            output,
            _compact_actions(output),
            _compact_masks(output),
            output.factor_counts,
        )

    def _capture(
        self,
        inputs: ProgramDecisionInputs,
        masks: NativeProgramMasks,
        prefix: ProgramPrefixState,
        prepared: ProgramPreparedContext | None,
    ) -> None:
        self._prepared = self._allocate_prepared(prepared) if prepared is not None else None
        self._inputs = self._allocate_inputs(inputs, self._prepared)
        self._masks = self._allocate_masks(masks)
        self._prefix = ProgramPrefixState(torch.empty_like(prefix.hidden))
        self._install(inputs, masks, prefix, prepared)
        device = inputs.context.device
        generator_state = self._generator.get_state()
        started = time.perf_counter()
        (
            self._output,
            self._action_output,
            self._mask_output,
            self._factor_count_output,
        ) = self._run()
        torch.cuda.current_stream(device).synchronize()
        self._generator.set_state(generator_state)
        self._install(inputs, masks, prefix, prepared)
        graph = torch.cuda.CUDAGraph()
        graph.register_generator_state(self._generator)
        with serialized_graph_capture(graph):
            (
                self._output,
                self._action_output,
                self._mask_output,
                self._factor_count_output,
            ) = self._run()
        torch.cuda.current_stream(device).synchronize()
        self._generator.set_state(generator_state)
        self._graph = graph
        if self._prepared is not None:
            self._decision_staging = PinnedProgramDecisionStaging(
                self._inputs,
                self._masks,
                self._prefix,
                self._prepared,
            )
        if self._action_output is None or self._mask_output is None or self._output is None:
            raise RuntimeError("program decision graph lost its compact outputs")
        self._output_staging = PinnedProgramOutputStaging(self._action_output)
        self.capture_seconds = time.perf_counter() - started

    def decode(
        self,
        inputs: ProgramDecisionInputs,
        masks: NativeProgramMasks,
        prefix: ProgramPrefixState,
        prepared: ProgramPreparedContext | None = None,
    ) -> ProgramStepOutput:
        """Install one full live batch and replay its sampled decision."""
        if self._graph is None:
            with serialized_graph_build():
                self._capture(inputs, masks, prefix, prepared)
        self._install(inputs, masks, prefix, prepared)
        graph = self._graph
        output = self._output
        if graph is None or output is None:
            raise RuntimeError("program decision graph capture produced no output")
        capture_safe_graph_replay(graph)
        return output

    @property
    def captured(self) -> bool:
        """Return whether this fixed-row specialization is ready for replay."""
        return self._graph is not None

    def decode_native(
        self,
        raw: Mapping[str, object],
        raw_rows: NDArray[np.int64],
        model_rows: NDArray[np.int64],
        prepared: ProgramPreparedContext,
        prefix: ProgramPrefixState,
    ) -> ProgramStepOutput:
        """Replay from pinned native arrays without intermediate CUDA tensors."""
        graph = self._graph
        output = self._output
        staging = self._decision_staging
        if graph is None or output is None or staging is None:
            raise RuntimeError("program decision graph lacks native staging")
        staging.install(raw, raw_rows, model_rows, prepared, prefix)
        capture_safe_graph_replay(graph)
        return output

    def copy_actions_to_host(self, rows: int) -> NDArray[np.int64]:
        """Copy only compiler-required actions and synchronize once."""
        if self._output_staging is None:
            raise RuntimeError("program decision graph lacks output staging")
        return self._output_staging.copy(rows)

    def enqueue_actions_to_host(self, rows: int) -> None:
        """Queue compiler-required actions without waiting for this stream."""
        if self._output_staging is None:
            raise RuntimeError("program decision graph lacks output staging")
        self._output_staging.enqueue(rows)

    def host_actions(self, rows: int) -> NDArray[np.int64]:
        """Expose actions after the caller has synchronized the graph stream."""
        if self._output_staging is None:
            raise RuntimeError("program decision graph lacks output staging")
        return self._output_staging.host_actions(rows)

    @property
    def model_rows(self) -> torch.Tensor:
        """Return the staged padded-to-model row mapping."""
        staging = self._decision_staging
        if staging is None:
            raise RuntimeError("program decision graph lacks native staging")
        return staging.model_rows

    def record(
        self,
        trace: ProgramGpuTrace,
        model_rows: torch.Tensor,
        rows: int,
    ) -> None:
        """Append graph outputs to the CUDA-resident complete-turn trace."""
        output = self._output
        actions = self._action_output
        masks = self._mask_output
        factor_counts = self._factor_count_output
        if (
            output is None
            or actions is None
            or masks is None
            or factor_counts is None
        ):
            raise RuntimeError("program decision graph has no output to record")
        trace.append(
            model_rows,
            actions,
            masks,
            output.masks.quantity_max,
            output.joint_log_probability,
            factor_counts,
            output.value,
            output.next_prefix.hidden,
            rows,
        )

    def close(self) -> None:
        """Release graph-private allocations at the collector boundary."""
        if self._graph is not None:
            self._graph.reset()
        self._graph = None
        self._inputs = None
        self._masks = None
        self._prefix = None
        self._prepared = None
        self._output = None
        self._action_output = None
        self._mask_output = None
        self._factor_count_output = None
        self._decision_staging = None
        self._output_staging = None


class ProgramDecisionGraphPool:
    """Power-of-two graph variants for compacted live decision rows."""

    def __init__(
        self,
        policy: ConditionalProgramPolicy,
        generator: torch.Generator,
        maximum_rows: int,
        *,
        sample: bool = True,
    ) -> None:
        """Bind graph variants to one fixed rollout group and RNG stream."""
        if maximum_rows < 1:
            raise ValueError("program graph pool needs a positive row capacity")
        self._policy = policy
        self._generator = generator
        self._maximum_rows = maximum_rows
        self._sample = sample
        self._variants: dict[tuple[int, bool], ProgramDecisionGraph] = {}

    @property
    def capture_seconds(self) -> float:
        """Return cumulative warmup and capture time across variants."""
        return sum(graph.capture_seconds for graph in self._variants.values())

    def padded_rows(self, active_rows: NDArray[np.int64]) -> NDArray[np.int64]:
        """Pad live row identities to the smallest reusable graph bucket."""
        if active_rows.ndim != 1 or not active_rows.size:
            raise ValueError("program graph pool needs live row identities")
        if int(active_rows.min()) < 0 or int(active_rows.max()) >= self._maximum_rows:
            raise ValueError("program graph pool row lies outside its batch")
        active_count = int(active_rows.size)
        bucket = min(
            self._maximum_rows,
            1 << (active_count - 1).bit_length(),
        )
        if bucket == active_count:
            return active_rows
        padding = np.full(
            bucket - active_count,
            active_rows[-1],
            dtype=np.int64,
        )
        return np.concatenate((active_rows, padding))

    def variant(self, rows: int, *, compute_outcome: bool) -> ProgramDecisionGraph:
        """Return one lazily captured fixed-row graph specialization."""
        if rows < 1 or rows > self._maximum_rows:
            raise ValueError("program graph variant row count is outside its pool")
        key = (rows, compute_outcome)
        graph = self._variants.get(key)
        if graph is None:
            graph = ProgramDecisionGraph(
                self._policy,
                self._generator,
                compute_outcome=compute_outcome,
                sample=self._sample,
            )
            self._variants[key] = graph
        return graph

    def close(self) -> None:
        """Release every captured bucket specialization."""
        for graph in self._variants.values():
            graph.close()
        self._variants.clear()


@dataclass(frozen=True)
class ProgramDecisionGraphShard:
    """One independent CUDA stream, RNG, and shape-specialized graph pool."""

    stream: torch.cuda.Stream
    generator: torch.Generator
    graphs: ProgramDecisionGraphPool


class ProgramDecisionGraphShards:
    """Concurrent within-decision CUDA execution for one native engine batch."""

    def __init__(
        self,
        policy: ConditionalProgramPolicy,
        maximum_rows: int,
        shard_count: int,
        *,
        sample: bool = True,
    ) -> None:
        """Allocate stream-local graph pools while keeping one model replica."""
        if shard_count < 1 or shard_count > maximum_rows:
            raise ValueError("program graph shard count is outside its batch")
        device = next(policy.parameters()).device
        if device.type != "cuda":
            raise ValueError("program graph shards require a CUDA policy")
        shards = []
        for _ in range(shard_count):
            generator = torch.Generator(device=device)
            shards.append(
                ProgramDecisionGraphShard(
                    stream=torch.cuda.Stream(device=device),  # type: ignore[no-untyped-call]
                    generator=generator,
                    graphs=ProgramDecisionGraphPool(
                        policy,
                        generator,
                        maximum_rows,
                        sample=sample,
                    ),
                )
            )
        self.shards = tuple(shards)

    @property
    def capture_seconds(self) -> float:
        """Return cumulative lazy graph construction time."""
        return sum(shard.graphs.capture_seconds for shard in self.shards)

    def manual_seed(self, seed: int) -> None:
        """Reset every shard RNG deterministically for one rollout group."""
        for index, shard in enumerate(self.shards):
            shard.generator.manual_seed(seed + index * 2_000_033)

    def close(self) -> None:
        """Release all stream-local graph variants."""
        for shard in self.shards:
            shard.graphs.close()


__all__ = [
    "ProgramDecisionGraph",
    "ProgramDecisionGraphPool",
    "ProgramDecisionGraphShard",
    "ProgramDecisionGraphShards",
]
