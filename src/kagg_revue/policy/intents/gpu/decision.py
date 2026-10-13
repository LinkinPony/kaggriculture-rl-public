"""Shape-bucketed CUDA Graph replay for canonical intent decisions."""

from __future__ import annotations

import time
from collections.abc import Mapping
from typing import Any

import numpy as np
import torch
from numpy.typing import NDArray
from torch import Tensor

from kagg_revue.policy.cuda.capture import (
    capture_safe_graph_replay,
    serialized_graph_build,
    serialized_graph_capture,
)
from kagg_revue.policy.intents.data import IntentTensorState
from kagg_revue.policy.intents.gpu.staging import (
    IntentBehaviorTape,
    PinnedIntentDecisionStaging,
    PinnedIntentOutputStaging,
)
from kagg_revue.policy.intents.model import IntentPolicy
from kagg_revue.policy.intents.schema import IntentSelection


def _bucket(width: int) -> int:
    if width < 0:
        raise ValueError("intent graph width cannot be negative")
    return 0 if width == 0 else 1 << (width - 1).bit_length()


def _shape(raw: Mapping[str, object], name: str) -> tuple[int, ...]:
    return tuple(int(value) for value in np.asarray(raw[name]).shape)


def _empty_state(
    shapes: Mapping[str, tuple[int, ...]],
    *,
    rows: int,
    candidates: int,
    work_orders: int,
    market_orders: int,
    device: torch.device,
) -> tuple[IntentTensorState, Tensor, dict[torch.dtype, Tensor]]:
    """Allocate a graph-static state from the measured native tensor ABI."""

    def state_shape(
        name: str,
        width: int | None = None,
    ) -> torch.Size:
        source = shapes[name]
        shape = (rows, *source)
        if width is not None:
            shape = (rows, width, *source[1:])
        return torch.Size(shape)

    specifications = {
        "candidate_fields": (state_shape("candidate_fields", candidates), torch.long),
        "candidate_features": (
            state_shape("candidate_features", candidates),
            torch.float32,
        ),
        "candidate_mask": (state_shape("candidate_mask", candidates), torch.bool),
        "ledger": (state_shape("ledger"), torch.long),
        "status": (state_shape("status"), torch.long),
        "work_priorities": (state_shape("work_priorities"), torch.long),
        "work_orders": (state_shape("work_orders", work_orders), torch.long),
        "work_mask": (state_shape("work_mask", work_orders), torch.bool),
        "positions": (state_shape("positions"), torch.long),
        "market_prefix": (state_shape("market_prefix", market_orders), torch.long),
        "market_mask": (torch.Size((rows, market_orders)), torch.bool),
        "phase": (state_shape("phase"), torch.long),
        "model_rows": (torch.Size((rows,)), torch.long),
    }
    packs: dict[torch.dtype, Tensor] = {}
    values: dict[str, Tensor] = {}
    for dtype in (torch.long, torch.float32, torch.bool):
        fields = [
            (name, shape)
            for name, (shape, field_dtype) in specifications.items()
            if field_dtype == dtype
        ]
        pack = torch.empty(
            sum(int(np.prod(shape)) for _name, shape in fields),
            dtype=dtype,
            device=device,
        )
        packs[dtype] = pack
        offset = 0
        for name, shape in fields:
            elements = int(np.prod(shape))
            values[name] = pack.narrow(0, offset, elements).view(shape)
            offset += elements
    return (
        IntentTensorState(
            candidate_fields=values["candidate_fields"],
            candidate_features=values["candidate_features"],
            candidate_mask=values["candidate_mask"],
            ledger=values["ledger"],
            status=values["status"],
            work_priorities=values["work_priorities"],
            work_orders=values["work_orders"],
            work_mask=values["work_mask"],
            positions=values["positions"],
            market_prefix=values["market_prefix"],
            market_mask=values["market_mask"],
            phase=values["phase"],
        ),
        values["model_rows"],
        packs,
    )


class IntentDecisionGraph:
    """One candidate/work-width specialization over a fixed rollout batch."""

    def __init__(
        self,
        policy: IntentPolicy,
        generator: torch.Generator,
        turn_context: Tensor,
        tile_context: Tensor,
        shapes: Mapping[str, tuple[int, ...]],
        *,
        candidate_capacity: int,
        work_capacity: int,
        market_capacity: int,
        sample: bool,
    ) -> None:
        """Allocate staging and lazily capture the policy on first decode."""
        self._policy = policy
        self._generator = generator
        self._turn_context = turn_context
        self._tile_context = tile_context
        self._sample = sample
        rows = turn_context.shape[0]
        device = turn_context.device
        self._state, model_rows, device_packs = _empty_state(
            shapes,
            rows=rows,
            candidates=candidate_capacity,
            work_orders=work_capacity,
            market_orders=market_capacity,
            device=device,
        )
        self._staging = PinnedIntentDecisionStaging(
            self._state,
            model_rows,
            device_packs,
        )
        self._selection: IntentSelection | None = None
        self._outputs: PinnedIntentOutputStaging | None = None
        self._graph: torch.cuda.CUDAGraph | None = None
        self.capture_seconds = 0.0

    def _run(self) -> IntentSelection:
        rows = self._staging.model_rows
        context = torch.index_select(self._turn_context, 0, rows)
        tiles = torch.index_select(self._tile_context, 0, rows)
        return self._policy.select(
            context,
            tiles,
            self._state,
            sample=self._sample,
            generator=self._generator,
            validate=False,
            compute_entropy=False,
        )

    def _capture(
        self,
        raw: Mapping[str, object] | None,
        candidate_mask: NDArray[np.bool_] | None,
        active_rows: NDArray[np.int64],
        prepared_batch: Any | None,
    ) -> None:
        generator_state = self._generator.get_state()
        self._staging.install(raw, candidate_mask, active_rows, prepared_batch)
        started = time.perf_counter()
        device = self._turn_context.device
        with torch.inference_mode(), torch.autocast(device_type="cuda", dtype=torch.bfloat16):
            self._selection = self._run()
        torch.cuda.current_stream(device).synchronize()
        self._generator.set_state(generator_state)
        self._staging.install(raw, candidate_mask, active_rows, prepared_batch)
        graph = torch.cuda.CUDAGraph()
        graph.register_generator_state(self._generator)
        with (
            torch.inference_mode(),
            torch.autocast(device_type="cuda", dtype=torch.bfloat16),
            serialized_graph_capture(graph),
        ):
            self._selection = self._run()
        torch.cuda.current_stream(device).synchronize()
        self._generator.set_state(generator_state)
        if self._selection is None:
            raise RuntimeError("intent graph capture produced no selection")
        self._graph = graph
        self._outputs = PinnedIntentOutputStaging(self._selection)
        self.capture_seconds = time.perf_counter() - started

    def decode(
        self,
        raw: Mapping[str, object] | None,
        candidate_mask: NDArray[np.bool_] | None,
        active_rows: NDArray[np.int64],
        prepared_batch: Any | None = None,
    ) -> tuple[NDArray[np.int64], NDArray[np.float32], NDArray[np.float32]]:
        """Stage, replay, and return only outputs consumed by the native session."""
        if self._graph is None:
            with serialized_graph_build():
                self._capture(raw, candidate_mask, active_rows, prepared_batch)
        self._staging.install(raw, candidate_mask, active_rows, prepared_batch)
        graph = self._graph
        outputs = self._outputs
        if graph is None or outputs is None:
            raise RuntimeError("intent graph was not captured")
        capture_safe_graph_replay(graph)
        return outputs.copy(int(active_rows.size))

    def decode_recording(
        self,
        raw: Mapping[str, object] | None,
        candidate_mask: NDArray[np.bool_] | None,
        active_rows: NDArray[np.int64],
        behavior_tape: IntentBehaviorTape,
        prepared_batch: Any | None = None,
    ) -> tuple[NDArray[np.int64], int]:
        """Replay while retaining log-probability and value on the device tape."""
        if self._graph is None:
            with serialized_graph_build():
                self._capture(raw, candidate_mask, active_rows, prepared_batch)
        self._staging.install(raw, candidate_mask, active_rows, prepared_batch)
        graph = self._graph
        outputs = self._outputs
        if graph is None or outputs is None:
            raise RuntimeError("intent graph was not captured")
        capture_safe_graph_replay(graph)
        return outputs.copy_selected(int(active_rows.size), behavior_tape)

    def close(self) -> None:
        """Release graph-private allocations."""
        if self._graph is not None:
            self._graph.reset()
        self._graph = None
        self._selection = None
        self._outputs = None


class IntentDecisionGraphPool:
    """Reuse width-bucketed graphs while every native state stays exact."""

    def __init__(
        self,
        policy: IntentPolicy,
        generator: torch.Generator,
        maximum_rows: int,
        *,
        sample: bool = True,
    ) -> None:
        """Bind one fixed rollout batch and its exact sampling stream."""
        device = next(policy.parameters()).device
        if device.type != "cuda":
            raise ValueError("intent decision graphs require a CUDA policy")
        if maximum_rows < 1:
            raise ValueError("intent decision graph pool needs positive rows")
        self._policy = policy
        self._device = device
        self._generator = generator
        self._maximum_rows = maximum_rows
        self._sample = sample
        self._turn_context: Tensor | None = None
        self._tile_context: Tensor | None = None
        self._native_shapes: dict[str, tuple[int, ...]] | None = None
        self._variants: dict[tuple[int, int], IntentDecisionGraph] = {}
        self._behavior_tape: IntentBehaviorTape | None = None

    def _graph_for_raw(
        self,
        raw: Mapping[str, object],
        active_rows: NDArray[np.int64],
    ) -> IntentDecisionGraph:
        """Authenticate the native ABI and return its shape specialization."""
        if self._native_shapes is None:
            self._native_shapes = {
                name: _shape(raw, name)[1:]
                for name in (
                    "candidate_fields",
                    "candidate_features",
                    "candidate_mask",
                    "ledger",
                    "status",
                    "work_priorities",
                    "work_orders",
                    "work_mask",
                    "positions",
                    "market_prefix",
                    "phase",
                )
            }
        candidate_shape = _shape(raw, "candidate_fields")
        work_shape = _shape(raw, "work_orders")
        market_shape = _shape(raw, "market_prefix")
        if candidate_shape[0] != active_rows.size:
            raise ValueError("intent native rows do not align with active rows")
        return self._graph_for_widths(
            (candidate_shape[1], work_shape[1], market_shape[1], 0),
            active_rows,
        )

    def _graph_for_widths(
        self,
        widths: tuple[int, int, int, int],
        active_rows: NDArray[np.int64],
    ) -> IntentDecisionGraph:
        """Return one graph specialization for authenticated compact widths."""
        context = self._turn_context
        tiles = self._tile_context
        shapes = self._native_shapes
        if context is None or tiles is None or shapes is None:
            raise RuntimeError("intent graph pool has no initialized turn context")
        if active_rows.ndim != 1 or not active_rows.size:
            raise ValueError("intent graph requires active row identities")
        candidate_width, work_width, market_width, _singleton_masks = widths
        candidate_capacity = _bucket(candidate_width)
        work_capacity = _bucket(work_width)
        market_capacity = self._policy.architecture.maximum_market_orders
        if market_width > market_capacity:
            raise ValueError("intent market prefix exceeds the policy architecture")
        key = (candidate_capacity, work_capacity)
        graph = self._variants.get(key)
        if graph is None:
            graph = IntentDecisionGraph(
                self._policy,
                self._generator,
                context,
                tiles,
                shapes,
                candidate_capacity=candidate_capacity,
                work_capacity=work_capacity,
                market_capacity=market_capacity,
                sample=self._sample,
            )
            self._variants[key] = graph
        return graph

    @property
    def capture_seconds(self) -> float:
        """Return cumulative warmup and graph-capture time."""
        return sum(graph.capture_seconds for graph in self._variants.values())

    @property
    def variant_count(self) -> int:
        """Return the number of observed shape buckets."""
        return len(self._variants)

    @property
    def native_layout_initialized(self) -> bool:
        """Return whether one full observation authenticated trailing shapes."""
        return self._native_shapes is not None

    def start_turn(self, context: Tensor, tile_context: Tensor) -> None:
        """Install one encoder result into stable graph-owned storage."""
        if context.shape[0] != self._maximum_rows or tile_context.shape[0] != self._maximum_rows:
            raise ValueError("intent turn context changed rollout batch size")
        if self._turn_context is None:
            self._turn_context = torch.empty_like(context)
            self._tile_context = torch.empty_like(tile_context)
        stored_context = self._turn_context
        stored_tiles = self._tile_context
        if (
            stored_context.shape != context.shape
            or stored_context.dtype != context.dtype
            or stored_tiles is None
            or stored_tiles.shape != tile_context.shape
            or stored_tiles.dtype != tile_context.dtype
        ):
            raise ValueError("intent turn context changed its graph ABI")
        stored_context.copy_(context)
        stored_tiles.copy_(tile_context)

    def decode(
        self,
        raw: Mapping[str, object],
        candidate_mask: NDArray[np.bool_],
        active_rows: NDArray[np.int64],
        prepared_batch: Any | None = None,
    ) -> tuple[NDArray[np.int64], NDArray[np.float32], NDArray[np.float32]]:
        """Use the smallest reusable width buckets for one live decision."""
        graph = self._graph_for_raw(raw, active_rows)
        return graph.decode(raw, candidate_mask, active_rows, prepared_batch)

    def decode_compact(
        self,
        widths: tuple[int, int, int, int],
        active_rows: NDArray[np.int64],
        prepared_batch: Any,
    ) -> tuple[NDArray[np.int64], NDArray[np.float32], NDArray[np.float32]]:
        """Replay a prepared native observation without materializing a dict."""
        graph = self._graph_for_widths(widths, active_rows)
        return graph.decode(None, None, active_rows, prepared_batch)

    def start_recording(self, capacity: int) -> None:
        """Prepare one persistent device tape for a complete rollout."""
        tape = self._behavior_tape
        if tape is None or tape.capacity < capacity:
            self._behavior_tape = IntentBehaviorTape(capacity, self._device)
        else:
            tape.reset()

    def finish_recording(self) -> NDArray[np.float32]:
        """Bulk-transfer the completed behavior tape to host storage."""
        if self._behavior_tape is None:
            raise RuntimeError("intent graph pool has no behavior recording")
        return self._behavior_tape.export()

    def decode_recording(
        self,
        raw: Mapping[str, object],
        candidate_mask: NDArray[np.bool_],
        active_rows: NDArray[np.int64],
        prepared_batch: Any | None = None,
    ) -> tuple[NDArray[np.int64], int]:
        """Decode one eager-native payload into the device behavior tape."""
        graph = self._graph_for_raw(raw, active_rows)
        tape = self._behavior_tape
        if tape is None:
            raise RuntimeError("intent behavior recording was not started")
        return graph.decode_recording(
            raw,
            candidate_mask,
            active_rows,
            tape,
            prepared_batch,
        )

    def decode_compact_recording(
        self,
        widths: tuple[int, int, int, int],
        active_rows: NDArray[np.int64],
        prepared_batch: Any,
    ) -> tuple[NDArray[np.int64], int]:
        """Decode one compact-native payload into the device behavior tape."""
        graph = self._graph_for_widths(widths, active_rows)
        tape = self._behavior_tape
        if tape is None:
            raise RuntimeError("intent behavior recording was not started")
        return graph.decode_recording(None, None, active_rows, tape, prepared_batch)

    def close(self) -> None:
        """Release every shape specialization."""
        for graph in self._variants.values():
            graph.close()
        self._variants.clear()
        self._turn_context = None
        self._tile_context = None
        self._behavior_tape = None


__all__ = ["IntentDecisionGraph", "IntentDecisionGraphPool"]
