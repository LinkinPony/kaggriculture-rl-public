"""Candidate-bucketed CUDA Graph replay for atomic-effect decisions."""

from __future__ import annotations

import time
from typing import Any, Literal

import numpy as np
import torch
from numpy.typing import NDArray
from torch import Tensor

from kagg_revue.policy.cuda.capture import (
    capture_safe_graph_replay,
    serialized_graph_build,
    serialized_graph_capture,
)
from kagg_revue.policy.effects.conditioning import TaskEncoding, condition_tasks, encode_tasks
from kagg_revue.policy.effects.gpu.staging import (
    EffectBehaviorTape,
    PinnedEffectDecisionStaging,
    PinnedEffectMaskStaging,
    PinnedEffectSelectionStaging,
)
from kagg_revue.policy.effects.model import EffectPolicy
from kagg_revue.policy.effects.schema import EffectSelection

_Mode = Literal["root", "market"]
_CompactWidths = tuple[int, int, int, int, int, int]


def _bucket(width: int) -> int:
    """Round one positive candidate width to a power-of-two graph bucket."""
    if width < 1:
        raise ValueError("effect candidate graph width must be positive")
    return 1 << (width - 1).bit_length()


class _EffectDecisionGraph:
    """One full-policy graph for a fixed candidate bucket and phase mode."""

    def __init__(
        self,
        policy: EffectPolicy,
        generator: torch.Generator,
        turn_context: Tensor,
        tile_context: Tensor,
        strategy: Tensor | None,
        turn_values: Tensor,
        *,
        candidate_capacity: int,
        entity_capacity: int,
        row_capacity: int,
        mode: _Mode,
        sample: bool,
    ) -> None:
        """Allocate graph state; capture lazily against a prepared native row set."""
        self._policy = policy
        self._generator = generator
        self._turn_context = turn_context
        self._tile_context = tile_context
        self._strategy = strategy
        self._turn_values = turn_values
        self._mode = mode
        self._sample = sample
        self._capacity = candidate_capacity
        self._entity_capacity = entity_capacity
        self._staging = PinnedEffectDecisionStaging(
            policy.architecture,
            row_capacity,
            candidate_capacity,
            turn_context.device,
        )
        self._selection: EffectSelection | None = None
        self._outputs: PinnedEffectSelectionStaging | None = None
        self._logits: Tensor | None = None
        self._values: Tensor | None = None
        self._task_encoding: TaskEncoding | None = None
        self._work_graph: _EffectWorkGraph | None = None
        self._graph: torch.cuda.CUDAGraph | None = None
        self.capture_seconds = 0.0

    @property
    def capacity(self) -> int:
        """Return the fixed candidate width."""
        return self._capacity

    @property
    def cached_logits(self) -> Tensor:
        """Return root logits updated in place by each graph replay."""
        if self._mode != "root" or self._logits is None:
            raise RuntimeError("effect root graph has no cached logits")
        return self._logits

    @property
    def cached_values(self) -> Tensor:
        """Return root values updated in place by each graph replay."""
        if self._mode != "root" or self._values is None:
            raise RuntimeError("effect root graph has no cached values")
        return self._values

    @property
    def work_capture_seconds(self) -> float:
        """Return lazy ranked-work selection capture time."""
        return 0.0 if self._work_graph is None else self._work_graph.capture_seconds

    @property
    def has_work_graph(self) -> bool:
        """Return whether repeated work selection has been captured."""
        return self._work_graph is not None

    def _run(self) -> EffectSelection:
        rows = self._staging.model_rows
        context = self._turn_context.index_select(0, rows)
        tiles = self._tile_context.index_select(0, rows)
        strategy = None if self._strategy is None else self._strategy.index_select(0, rows)
        if self._mode == "root" and self._policy.architecture.task_conditioning:
            self._task_encoding = encode_tasks(
                self._policy,
                context,
                tiles,
                self._staging.state,
                strategy,
                entity_capacity=self._entity_capacity,
            )
            self._logits = self._task_encoding.logits
            # Independent critic is evaluated at the coarse rollout boundary.
            if self._policy.architecture.independent_critic:
                self._values = torch.zeros_like(self._logits[:, 0])
            else:
                probabilities = (
                    self._policy.value_head(self._task_encoding.hidden).float().softmax(-1)
                )
                self._values = probabilities[:, 2] - probabilities[:, 0]
        elif self._mode == "root":
            output = self._policy(
                context,
                tiles,
                self._staging.state,
                strategy,
                validate=False,
                mask_candidates=False,
                entity_capacity=self._entity_capacity,
            )
            self._logits = output.candidate_logits
            self._values = output.value
        else:
            self._logits = self._policy.forward_logits(
                context,
                tiles,
                self._staging.state,
                strategy,
                validate=False,
                entity_capacity=self._entity_capacity,
            )
            self._values = self._turn_values.index_select(0, rows)
        return EffectPolicy.select_logits(
            self._logits.masked_fill(~self._staging.state.candidate_mask, -torch.inf),
            self._values,
            sample=self._sample,
            generator=self._generator,
            compute_entropy=False,
        )

    def _capture(self, prepared_batch: Any) -> None:
        generator_state = self._generator.get_state()
        self._staging.install(prepared_batch)
        started = time.perf_counter()
        device = self._turn_context.device
        with torch.inference_mode(), torch.autocast("cuda", dtype=torch.bfloat16):
            self._selection = self._run()
        torch.cuda.current_stream(device).synchronize()
        self._generator.set_state(generator_state)
        self._staging.install(prepared_batch)
        graph = torch.cuda.CUDAGraph()
        graph.register_generator_state(self._generator)
        with (
            torch.inference_mode(),
            torch.autocast("cuda", dtype=torch.bfloat16),
            serialized_graph_capture(graph),
        ):
            self._selection = self._run()
        torch.cuda.current_stream(device).synchronize()
        self._generator.set_state(generator_state)
        if self._selection is None:
            raise RuntimeError("effect graph capture produced no selection")
        self._graph = graph
        self._outputs = PinnedEffectSelectionStaging(self._selection)
        self.capture_seconds = time.perf_counter() - started

    def decode_recording(
        self,
        prepared_batch: Any,
        live_rows: int,
        behavior_tape: EffectBehaviorTape,
    ) -> tuple[NDArray[np.int64], int]:
        """Stage, replay, and synchronize only the native causal selections."""
        if self._graph is None:
            with serialized_graph_build():
                self._capture(prepared_batch)
        self._staging.install(prepared_batch)
        graph = self._graph
        outputs = self._outputs
        if graph is None or outputs is None:
            raise RuntimeError("effect decision graph was not captured")
        capture_safe_graph_replay(graph)
        return outputs.copy_selected(live_rows, behavior_tape)

    def decode_work_recording(
        self,
        prepared_batch: Any,
        live_rows: int,
        behavior_tape: EffectBehaviorTape,
    ) -> tuple[NDArray[np.int64], int]:
        """Reuse immutable root scores under the latest native work mask."""
        if self._mode != "root":
            raise RuntimeError("market graph cannot provide ranked-work scores")
        if self._work_graph is None:
            self._work_graph = _EffectWorkGraph(
                self._generator,
                self.cached_logits,
                self.cached_values,
                sample=self._sample,
                policy=self._policy,
                task_encoding=self._task_encoding,
            )
        return self._work_graph.decode_recording(
            prepared_batch,
            live_rows,
            behavior_tape,
        )

    def close(self) -> None:
        """Release this specialization and its optional work selector."""
        if self._work_graph is not None:
            self._work_graph.close()
        if self._graph is not None:
            self._graph.reset()
        self._graph = None
        self._selection = None
        self._outputs = None
        self._logits = None
        self._values = None


class _EffectWorkGraph:
    """Selection-only graph over one immutable root score surface."""

    def __init__(
        self,
        generator: torch.Generator,
        logits: Tensor,
        values: Tensor,
        *,
        sample: bool,
        policy: EffectPolicy,
        task_encoding: TaskEncoding | None = None,
    ) -> None:
        """Bind root outputs and allocate only the changing hard-mask inputs."""
        self._generator = generator
        self._logits = logits
        self._values = values
        self._policy = policy
        self._task_encoding = task_encoding
        self._sample = sample
        self._staging = PinnedEffectMaskStaging(
            logits.shape[0],
            logits.shape[1],
            logits.device,
            prefix_capacity=policy.architecture.unit_limit if task_encoding is not None else 0,
        )
        self._selection: EffectSelection | None = None
        self._outputs: PinnedEffectSelectionStaging | None = None
        self._graph: torch.cuda.CUDAGraph | None = None
        self.capture_seconds = 0.0

    def _run(self) -> EffectSelection:
        rows = self._staging.model_rows
        if self._task_encoding is None:
            logits = self._logits.index_select(0, rows)
        else:
            logits = condition_tasks(
                self._policy,
                self._task_encoding.index_select(rows),
                self._staging.prefix,
                self._staging.prefix_mask,
                torch.zeros_like(rows),
            )
        logits = logits.masked_fill(~self._staging.candidate_mask, -torch.inf)
        values = self._values.index_select(0, rows)
        return EffectPolicy.select_logits(
            logits,
            values,
            sample=self._sample,
            generator=self._generator,
            compute_entropy=False,
        )

    def _capture(self, prepared_batch: Any) -> None:
        generator_state = self._generator.get_state()
        self._staging.install(prepared_batch)
        started = time.perf_counter()
        device = self._logits.device
        with torch.inference_mode(), torch.autocast("cuda", dtype=torch.bfloat16):
            self._selection = self._run()
        torch.cuda.current_stream(device).synchronize()
        self._generator.set_state(generator_state)
        self._staging.install(prepared_batch)
        graph = torch.cuda.CUDAGraph()
        graph.register_generator_state(self._generator)
        with (
            torch.inference_mode(),
            torch.autocast("cuda", dtype=torch.bfloat16),
            serialized_graph_capture(graph),
        ):
            self._selection = self._run()
        torch.cuda.current_stream(device).synchronize()
        self._generator.set_state(generator_state)
        if self._selection is None:
            raise RuntimeError("effect work graph capture produced no selection")
        self._graph = graph
        self._outputs = PinnedEffectSelectionStaging(self._selection)
        self.capture_seconds = time.perf_counter() - started

    def decode_recording(
        self,
        prepared_batch: Any,
        live_rows: int,
        behavior_tape: EffectBehaviorTape,
    ) -> tuple[NDArray[np.int64], int]:
        """Replay cached root selection with the latest exact native mask."""
        if self._graph is None:
            with serialized_graph_build():
                self._capture(prepared_batch)
        self._staging.install(prepared_batch)
        graph = self._graph
        outputs = self._outputs
        if graph is None or outputs is None:
            raise RuntimeError("effect work graph was not captured")
        capture_safe_graph_replay(graph)
        return outputs.copy_selected(live_rows, behavior_tape)

    def close(self) -> None:
        """Release selection-only graph allocations."""
        if self._graph is not None:
            self._graph.reset()
        self._graph = None
        self._selection = None
        self._outputs = None


class EffectDecisionGraphPool:
    """Reuse candidate-width graphs while secondary entity axes stay fixed."""

    def __init__(
        self,
        policy: EffectPolicy,
        generator: torch.Generator,
        maximum_rows: int,
        *,
        sample: bool = True,
        maximum_variants: int = 48,
        retain_behavior_distributions: bool = True,
    ) -> None:
        """Bind a CUDA policy, exact RNG stream, and bounded graph cache."""
        device = next(policy.parameters()).device
        if device.type != "cuda":
            raise ValueError("effect decision graphs require a CUDA policy")
        if maximum_rows < 1 or maximum_variants < 1:
            raise ValueError("effect graph pool requires positive capacity")
        self._policy = policy
        self._device = device
        self._generator = generator
        self._maximum_rows = maximum_rows
        self._sample = sample
        self._maximum_variants = maximum_variants
        self._retain_behavior_distributions = retain_behavior_distributions
        self._turn_context: Tensor | None = None
        self._tile_context: Tensor | None = None
        self._strategy: Tensor | None = None
        self._turn_values = torch.empty((maximum_rows,), dtype=torch.float32, device=device)
        self._variants: dict[tuple[_Mode, int, int, int], _EffectDecisionGraph] = {}
        self._current_root: _EffectDecisionGraph | None = None
        self._behavior_tape: EffectBehaviorTape | None = None

    def _validate_widths(
        self,
        widths: _CompactWidths,
        live_rows: int,
    ) -> int:
        candidates, jobs, work, market, previous, policy_rows = widths
        architecture = self._policy.architecture
        if live_rows < 1 or live_rows > self._maximum_rows:
            raise ValueError("effect graph received an invalid live row count")
        if (
            jobs > architecture.unit_limit
            or work > architecture.unit_limit
            or market > architecture.maximum_market_orders
            or previous > architecture.unit_limit + architecture.maximum_market_orders
        ):
            raise ValueError("effect native state exceeds fixed secondary axes")
        if min(jobs, work, market, previous, policy_rows) < 0:
            raise ValueError("effect compact widths cannot be negative")
        if policy_rows > live_rows:
            raise ValueError("effect policy row count exceeds live rows")
        return _bucket(candidates)

    def _graph_for(
        self,
        mode: _Mode,
        widths: _CompactWidths,
        live_rows: int,
    ) -> _EffectDecisionGraph:
        """Return the bounded candidate-only specialization for this phase."""
        context = self._turn_context
        tiles = self._tile_context
        if context is None or tiles is None:
            raise RuntimeError("effect graph pool has no initialized turn context")
        capacity = self._validate_widths(widths, live_rows)
        maximum_entities = self._policy.architecture.maximum_state_entities
        compact_entities = min(32, maximum_entities)
        entity_capacity = (
            compact_entities if 1 + sum(widths[1:5]) <= compact_entities else maximum_entities
        )
        compact_rows = max(1, self._maximum_rows // 4)
        row_capacity = (
            compact_rows if mode == "market" and live_rows <= compact_rows else self._maximum_rows
        )
        key = (mode, capacity, entity_capacity, row_capacity)
        graph = self._variants.get(key)
        if graph is None:
            if self.variant_count >= self._maximum_variants:
                raise RuntimeError("effect decision graph variant bound was exceeded")
            graph = _EffectDecisionGraph(
                self._policy,
                self._generator,
                context,
                tiles,
                self._strategy,
                self._turn_values,
                candidate_capacity=capacity,
                entity_capacity=entity_capacity,
                row_capacity=row_capacity,
                mode=mode,
                sample=self._sample,
            )
            self._variants[key] = graph
        return graph

    @property
    def capture_seconds(self) -> float:
        """Return cumulative full-policy and work-selection capture time."""
        return sum(
            graph.capture_seconds + graph.work_capture_seconds for graph in self._variants.values()
        )

    @property
    def variant_count(self) -> int:
        """Return the retained full-policy and work graph count."""
        return len(self._variants) + sum(
            int(graph.has_work_graph) for graph in self._variants.values()
        )

    def start_turn(
        self,
        context: Tensor,
        tile_context: Tensor,
        strategy: Tensor | None,
    ) -> None:
        """Copy one recurrent turn result into graph-owned stable buffers."""
        if (
            context.shape[0] != self._maximum_rows
            or tile_context.shape[0] != self._maximum_rows
            or (strategy is not None and strategy.shape != context.shape)
        ):
            raise ValueError("effect turn context changed rollout batch shape")
        if self._turn_context is None:
            self._turn_context = torch.empty_like(context)
            self._tile_context = torch.empty_like(tile_context)
            self._strategy = None if strategy is None else torch.empty_like(strategy)
        stored_context = self._turn_context
        stored_tiles = self._tile_context
        stored_strategy = self._strategy
        if (
            stored_context.shape != context.shape
            or stored_context.dtype != context.dtype
            or stored_tiles is None
            or stored_tiles.shape != tile_context.shape
            or stored_tiles.dtype != tile_context.dtype
            or (stored_strategy is None) != (strategy is None)
        ):
            raise ValueError("effect turn context changed its graph ABI")
        stored_context.copy_(context)
        stored_tiles.copy_(tile_context)
        if stored_strategy is not None and strategy is not None:
            if stored_strategy.shape != strategy.shape or stored_strategy.dtype != strategy.dtype:
                raise ValueError("effect strategy context changed its graph ABI")
            stored_strategy.copy_(strategy)
        self._current_root = None

    def start_recording(self, capacity: int) -> None:
        """Prepare one persistent device tape for a complete rollout."""
        tape = self._behavior_tape
        if (
            tape is None
            or tape.capacity < capacity
            or tape.retain_distributions != self._retain_behavior_distributions
        ):
            self._behavior_tape = EffectBehaviorTape(
                capacity,
                self._device,
                retain_distributions=self._retain_behavior_distributions,
            )
        else:
            tape.reset()

    def finish_recording(self) -> dict[str, Any] | NDArray[np.float32]:
        """Bulk-transfer behavior statistics once after the rollout."""
        if self._behavior_tape is None:
            raise RuntimeError("effect behavior recording was not started")
        return self._behavior_tape.export()

    def _tape(self) -> EffectBehaviorTape:
        tape = self._behavior_tape
        if tape is None:
            raise RuntimeError("effect behavior recording was not started")
        return tape

    def decode_root(
        self,
        widths: _CompactWidths,
        active_rows: NDArray[np.int64],
        prepared_batch: Any,
    ) -> tuple[NDArray[np.int64], int]:
        """Score work candidates and the critic once for an official turn."""
        expected = np.arange(self._maximum_rows, dtype=np.int64)
        if active_rows.shape != expected.shape or not np.array_equal(active_rows, expected):
            raise ValueError("effect root decision must cover every rollout row")
        graph = self._graph_for("root", widths, int(active_rows.size))
        selected, offset = graph.decode_recording(
            prepared_batch,
            int(active_rows.size),
            self._tape(),
        )
        self._turn_values.copy_(graph.cached_values)
        self._current_root = graph
        return selected, offset

    def decode_work(
        self,
        widths: _CompactWidths,
        active_rows: NDArray[np.int64],
        prepared_batch: Any,
    ) -> tuple[NDArray[np.int64], int]:
        """Select another work request from the immutable root logits."""
        root = self._current_root
        if root is None:
            raise RuntimeError("effect work selection has no current root scores")
        capacity = self._validate_widths(widths, int(active_rows.size))
        if capacity > root.capacity:
            raise ValueError("effect ranked-work candidate surface exceeded root width")
        if not root.has_work_graph and self.variant_count >= self._maximum_variants:
            raise RuntimeError("effect decision graph variant bound was exceeded")
        return root.decode_work_recording(
            prepared_batch,
            int(active_rows.size),
            self._tape(),
        )

    def decode_market(
        self,
        widths: _CompactWidths,
        active_rows: NDArray[np.int64],
        prepared_batch: Any,
    ) -> tuple[NDArray[np.int64], int]:
        """Rescore complete market orders after each exact projected prefix."""
        graph = self._graph_for("market", widths, int(active_rows.size))
        return graph.decode_recording(
            prepared_batch,
            int(active_rows.size),
            self._tape(),
        )

    def close(self) -> None:
        """Release every retained graph and behavior allocation."""
        for graph in self._variants.values():
            graph.close()
        self._variants.clear()
        self._turn_context = None
        self._tile_context = None
        self._strategy = None
        self._current_root = None
        self._behavior_tape = None


__all__ = ["EffectDecisionGraphPool"]
