"""Hopper conditional graph for a complete canonical intent transaction."""

from __future__ import annotations

import time
from collections.abc import Mapping
from dataclasses import dataclass

import numpy as np
import torch
from numpy.typing import NDArray
from torch import Tensor

from kagg_revue.native import _intent_cuda, _program_cuda
from kagg_revue.policy.cuda.capture import (
    serialized_graph_build,
    serialized_graph_capture,
)
from kagg_revue.policy.intents.data import IntentTensorState
from kagg_revue.policy.intents.gpu.ledger import (
    IntentGpuDecision,
    IntentGpuLedger,
)
from kagg_revue.policy.intents.gpu.staging import (
    IntentBehaviorTape,
    PinnedIntentTransactionStaging,
)
from kagg_revue.policy.intents.model import IntentPolicy
from kagg_revue.policy.intents.schema import IntentPolicyOutput, IntentSelection

_GRAPH_RECOMPILE_LIMIT = 64


@dataclass(frozen=True)
class IntentTransactionTrace:
    """Host-visible choices after one device-controlled transaction."""

    selected: NDArray[np.int64]
    selected_fields: NDArray[np.int64]
    counts: NDArray[np.int64]
    behavior_offset: int


class IntentGpuTransactionGraph:
    """Keep all causally dependent pseudo-steps inside one CUDA launch."""

    _MUTABLE_LEDGER_FIELDS = (
        "ledger",
        "work_orders",
        "work_mask",
        "positions",
        "market_prefix",
        "market_mask",
        "phase",
        "active",
        "pending_kind",
        "pending_target",
        "pending_role",
        "pending_unit",
        "pending_directive_operation",
        "pending_item",
        "pending_quantity",
        "pending_market_kind",
        "pending_market_item",
        "pending_market_upper",
        "last_ledger_key",
        "market_phase",
        "trace_counts",
        "trace_selected",
        "trace_fields",
        "trace_log_probability",
        "trace_value",
        "live_candidate_count",
        "live_batch_count",
        "work_removed_fields",
        "work_removed_mask",
        "work_added_fields",
        "work_added_mask",
    )

    def __init__(
        self,
        policy: IntentPolicy,
        generator: torch.Generator,
        batch: int,
        unit_limit: int,
        *,
        maximum_steps: int,
        episode_steps: int,
        turns_per_day: int,
        sample: bool = True,
    ) -> None:
        """Allocate the shadow ledger, trace, and bounded policy variants."""
        device = next(policy.parameters()).device
        if device.type != "cuda":
            raise ValueError("intent transaction graph requires CUDA")
        generator_device = torch.device(generator.device)
        generator_index = (
            torch.cuda.current_device()
            if generator_device.index is None
            else generator_device.index
        )
        if generator_device.type != "cuda" or (generator_index != device.index):
            raise ValueError("intent transaction generator is on the wrong CUDA device")
        self.policy = policy
        self.device = device
        self.batch = batch
        self.sample = sample
        self.generator = generator
        self.ledger = IntentGpuLedger(
            policy.architecture,
            batch,
            unit_limit,
            device,
            maximum_steps=maximum_steps,
            episode_steps=episode_steps,
            turns_per_day=turns_per_day,
        )
        self.staging = PinnedIntentTransactionStaging(
            batch=batch,
            cells=self.ledger.cells,
            work_capacity=self.ledger.work_capacity,
            work_field_count=policy.architecture.work_field_count,
            market_capacity=policy.architecture.maximum_market_orders,
            economic_width=self.ledger.layout.width,
            device=device,
        )
        context_width = policy.architecture.context_width
        self.context = torch.empty((batch, context_width), dtype=torch.bfloat16, device=device)
        self.tile_context = torch.empty(
            (batch, self.ledger.cells, context_width),
            dtype=torch.bfloat16,
            device=device,
        )
        self.work_sum = torch.zeros(
            (batch, policy.architecture.model_width),
            dtype=torch.float32,
            device=device,
        )
        self.work_count = torch.zeros(batch, dtype=torch.float32, device=device)
        self.encoded_context = torch.empty_like(self.work_sum, dtype=torch.bfloat16)
        self.encoded_tiles = torch.empty(
            (batch, self.ledger.cells, policy.architecture.model_width),
            dtype=torch.bfloat16,
            device=device,
        )
        candidate_fields = torch.empty(
            (
                batch,
                self.ledger.candidate_capacity,
                policy.architecture.candidate_field_count,
            ),
            dtype=torch.long,
            device=device,
        )
        candidate_features = torch.empty(
            (
                batch,
                self.ledger.candidate_capacity,
                policy.architecture.candidate_feature_count,
            ),
            dtype=torch.float32,
            device=device,
        )
        candidate_mask = torch.empty(
            (batch, self.ledger.candidate_capacity),
            dtype=torch.bool,
            device=device,
        )
        self.decision: IntentGpuDecision | None = IntentGpuDecision(
            state=IntentTensorState(
                candidate_fields=candidate_fields,
                candidate_features=candidate_features,
                candidate_mask=candidate_mask,
                ledger=self.ledger.ledger,
                status=torch.empty(
                    (batch, self.ledger.cells, policy.architecture.status_field_count),
                    dtype=torch.long,
                    device=device,
                ),
                work_priorities=torch.empty(
                    (batch, self.ledger.cells, 8),
                    dtype=torch.long,
                    device=device,
                ),
                work_orders=self.ledger.work_orders,
                work_mask=self.ledger.work_mask,
                positions=self.ledger.positions,
                market_prefix=self.ledger.market_prefix,
                market_mask=self.ledger.market_mask,
                phase=self.ledger.phase,
            ),
            candidate_counts=torch.empty(batch, dtype=torch.long, device=device),
        )
        self.work_scratch = torch.empty_like(self.ledger.work_orders)
        self.work_mask_scratch = torch.empty_like(self.ledger.work_mask)
        self.work_mutation = torch.zeros(batch, dtype=torch.long, device=device)
        self.work_priority_target = torch.full_like(self.work_mutation, -1)
        model_width = policy.architecture.model_width
        self.ledger_entities = torch.empty(
            (batch, self.ledger.cells, model_width),
            dtype=torch.float32,
            device=device,
        )
        self.ledger_sum = torch.empty(
            (batch, model_width), dtype=torch.float32, device=device
        )
        self.position_entities = torch.empty(
            (batch, 2, model_width), dtype=torch.float32, device=device
        )
        self.position_sum = torch.empty_like(self.ledger_sum)
        self.market_entities = torch.empty(
            (
                batch,
                policy.architecture.maximum_market_orders,
                model_width,
            ),
            dtype=torch.float32,
            device=device,
        )
        self.market_sum = torch.empty_like(self.ledger_sum)
        self.market_count = torch.empty(batch, dtype=torch.float32, device=device)
        self.market_entity_mask = torch.empty_like(self.ledger.market_mask)
        self.ledger_dirty_target = torch.full(
            (batch,), -1, dtype=torch.long, device=device
        )
        self.position_dirty_role = torch.full_like(self.ledger_dirty_target, -1)
        self.market_dirty_slot = torch.full_like(self.ledger_dirty_target, -1)
        self._rows = torch.arange(batch, dtype=torch.long, device=device)
        self._ledger_targets = torch.arange(
            self.ledger.cells, dtype=torch.long, device=device
        )[None].expand(batch, -1)
        self._market_positions = torch.arange(
            policy.architecture.maximum_market_orders,
            dtype=torch.long,
            device=device,
        )[None].expand(batch, -1)
        setup_capacities = {
            min(capacity, self.ledger.candidate_capacity)
            for capacity in (64, 128, 256, 512, self.ledger.candidate_capacity)
        }
        self.setup_capacities = tuple(sorted(setup_capacities))
        phase_variants = [
            next(
                index
                for index, capacity in enumerate(self.setup_capacities)
                if capacity >= required
            )
            for required in self.ledger.phase_candidate_capacities
        ]
        self.phase_variants = torch.tensor(phase_variants, dtype=torch.long, device=device)
        self.decision_variant = torch.zeros((), dtype=torch.long, device=device)
        self._compiled_initialize = torch.compile(
            self._initialize_state_cache,
            fullgraph=True,
            dynamic=False,
        )
        self._compiled_cache_update = torch.compile(
            self._update_state_cache,
            fullgraph=True,
            dynamic=False,
        )
        self._compiled_policy = torch.compile(
            self.policy.forward_cached,
            fullgraph=True,
            dynamic=True,
            options={"triton.cudagraphs": False},
        )
        self.selection: IntentSelection | None = None
        self.initial_state_graph: torch.cuda.CUDAGraph | None = None
        self.setup_graphs: list[torch.cuda.CUDAGraph] = []
        self.variant_graphs: list[torch.cuda.CUDAGraph] = []
        self.conditional: _program_cuda.ConditionalCountSwitchWhileGraph | None = None
        buckets: list[int] = []
        capacity = 1
        while capacity < self.ledger.candidate_capacity:
            buckets.append(capacity)
            capacity *= 2
        buckets.append(self.ledger.candidate_capacity)
        self.buckets = tuple(buckets)
        self.uniform = torch.full(
            (batch, self.ledger.trace_capacity),
            0.5,
            dtype=torch.float32,
            device=device,
        )
        self._host_selected = torch.empty(
            (batch, self.ledger.trace_capacity),
            dtype=torch.long,
            device="cpu",
            pin_memory=True,
        )
        self._host_counts = torch.empty(batch, dtype=torch.long, device="cpu", pin_memory=True)
        self._host_fields = torch.empty(
            (batch, self.ledger.trace_capacity, policy.architecture.candidate_field_count),
            dtype=torch.long,
            device="cpu",
            pin_memory=True,
        )
        self._behavior: IntentBehaviorTape | None = None
        self.capture_seconds = 0.0
        decision = self.decision
        if decision is None:
            raise RuntimeError("intent transaction decision buffers are absent")
        pointers = {
            "candidate_fields": decision.state.candidate_fields.data_ptr(),
            "candidate_features": decision.state.candidate_features.data_ptr(),
            "candidate_mask": decision.state.candidate_mask.data_ptr(),
            "candidate_counts": decision.candidate_counts.data_ptr(),
            "ledger": self.ledger.ledger.data_ptr(),
            "status": decision.state.status.data_ptr(),
            "work_priorities": decision.state.work_priorities.data_ptr(),
            "status_deadline": self.ledger.status_deadline.data_ptr(),
            "inactive_status": self.ledger.inactive_status.data_ptr(),
            "asset_risk": self.ledger.asset_risk.data_ptr(),
            "work_orders": self.ledger.work_orders.data_ptr(),
            "work_mask": self.ledger.work_mask.data_ptr(),
            "work_scratch": self.work_scratch.data_ptr(),
            "work_mask_scratch": self.work_mask_scratch.data_ptr(),
            "work_removed_fields": self.ledger.work_removed_fields.data_ptr(),
            "work_removed_mask": self.ledger.work_removed_mask.data_ptr(),
            "work_added_fields": self.ledger.work_added_fields.data_ptr(),
            "work_added_mask": self.ledger.work_added_mask.data_ptr(),
            "work_mutation": self.work_mutation.data_ptr(),
            "work_priority_target": self.work_priority_target.data_ptr(),
            "positions": self.ledger.positions.data_ptr(),
            "market_prefix": self.ledger.market_prefix.data_ptr(),
            "market_mask": self.ledger.market_mask.data_ptr(),
            "economic": self.ledger.economic.data_ptr(),
            "carried": self.ledger.carried.data_ptr(),
            "unit_inventories": self.ledger.unit_inventories.data_ptr(),
            "shed": self.ledger.shed.data_ptr(),
            "unit_positions": self.ledger.unit_positions.data_ptr(),
            "owned": self.ledger.owned.data_ptr(),
            "tiles": self.ledger.tiles.data_ptr(),
            "work_applies": self.ledger.work_applies.data_ptr(),
            "market_product_ratio": self.ledger.market_product_ratio.data_ptr(),
            "phase": self.ledger.phase.data_ptr(),
            "active": self.ledger.active.data_ptr(),
            "pending_kind": self.ledger.pending_kind.data_ptr(),
            "pending_target": self.ledger.pending_target.data_ptr(),
            "pending_role": self.ledger.pending_role.data_ptr(),
            "pending_unit": self.ledger.pending_unit.data_ptr(),
            "pending_directive_operation": (
                self.ledger.pending_directive_operation.data_ptr()
            ),
            "pending_item": self.ledger.pending_item.data_ptr(),
            "pending_quantity": self.ledger.pending_quantity.data_ptr(),
            "pending_market_kind": self.ledger.pending_market_kind.data_ptr(),
            "pending_market_item": self.ledger.pending_market_item.data_ptr(),
            "pending_market_upper": self.ledger.pending_market_upper.data_ptr(),
            "last_ledger_key": self.ledger.last_ledger_key.data_ptr(),
            "market_phase": self.ledger.market_phase.data_ptr(),
            "trace_counts": self.ledger.trace_counts.data_ptr(),
            "trace_selected": self.ledger.trace_selected.data_ptr(),
            "trace_fields": self.ledger.trace_fields.data_ptr(),
            "trace_log_probability": self.ledger.trace_log_probability.data_ptr(),
            "trace_value": self.ledger.trace_value.data_ptr(),
            "live_candidate_count": self.ledger.live_candidate_count.data_ptr(),
            "live_batch_count": self.ledger.live_batch_count.data_ptr(),
            "decision_variant": self.decision_variant.data_ptr(),
            "phase_variants": self.phase_variants.data_ptr(),
            "ledger_dirty_target": self.ledger_dirty_target.data_ptr(),
            "position_dirty_role": self.position_dirty_role.data_ptr(),
            "market_dirty_slot": self.market_dirty_slot.data_ptr(),
        }
        dimensions = {
            "batch": batch,
            "board_size": policy.architecture.board_size,
            "cells": self.ledger.cells,
            "unit_limit": unit_limit,
            "work_capacity": self.ledger.work_capacity,
            "market_capacity": policy.architecture.maximum_market_orders,
            "economic_width": self.ledger.layout.width,
            "seeds_offset": self.ledger.layout.seeds,
            "tile_fields": self.ledger.layout.tile_fields,
            "candidate_capacity": self.ledger.candidate_capacity,
            "trace_capacity": self.ledger.trace_capacity,
            "maximum_steps": maximum_steps,
            "episode_steps": episode_steps,
            "turns_per_day": turns_per_day,
        }
        self._kernels = _intent_cuda.IntentTransactionKernels(pointers, dimensions)

    def manual_seed(self, seed: int) -> None:
        """Reset the checkpoint-owned transaction sampling stream."""
        self.generator.manual_seed(seed)

    def start_recording(self, capacity: int) -> None:
        """Prepare the device behavior tape for one complete rollout."""
        tape = self._behavior
        if tape is None or tape.capacity < capacity:
            self._behavior = IntentBehaviorTape(capacity, self.device)
        else:
            tape.reset()

    def finish_recording(self) -> NDArray[np.float32]:
        """Bulk-transfer behavior values after every native replay is done."""
        if self._behavior is None:
            raise RuntimeError("intent transaction behavior recording was not started")
        return self._behavior.export()

    @property
    def variant_count(self) -> int:
        """Return the number of retained candidate-width policy graphs."""
        return len(self.variant_graphs)

    def _setup_variant(self, capacity: int) -> None:
        stream = torch.cuda.current_stream(self.device)
        self._kernels.candidates(stream.cuda_stream, capacity)

    def _initialize_state_cache(self) -> None:
        decision = self.decision
        if decision is None:
            raise RuntimeError("intent transaction decision buffers are absent")
        state_encoder = self.policy.state_encoder
        encoded_context, encoded_tiles = self.policy.prepare_turn(
            self.context,
            self.tile_context,
        )
        status = self.ledger._status(self.ledger.tiles, self.ledger.owned)
        priorities = self.ledger._work_priorities()
        ledger_entities = state_encoder.encode_ledger_entities(
            self.ledger.ledger,
            status,
            priorities,
            encoded_tiles,
            self._ledger_targets,
        )
        work_entities = state_encoder.encode_work_entities(self.ledger.work_orders)
        position_entities = state_encoder.encode_position_entities(self.ledger.positions)
        market_entities = state_encoder.encode_market_entities(
            self.ledger.market_prefix,
            self._market_positions,
        )
        work_weights = self.ledger.work_mask[:, :, None]
        market_weights = self.ledger.market_mask[:, :, None]
        self.encoded_context.copy_(encoded_context)
        self.encoded_tiles.copy_(encoded_tiles)
        decision.state.status.copy_(status)
        decision.state.work_priorities.copy_(priorities)
        self.ledger_entities.copy_(ledger_entities)
        self.ledger_sum.copy_(ledger_entities.sum(1))
        self.work_sum.copy_((work_entities * work_weights).sum(1))
        self.work_count.copy_(self.ledger.work_mask.sum(1).float())
        self.position_entities.copy_(position_entities)
        self.position_sum.copy_(position_entities.sum(1))
        self.market_entities.copy_(market_entities)
        self.market_sum.copy_((market_entities * market_weights).sum(1))
        self.market_count.copy_(self.ledger.market_mask.sum(1).float())
        self.market_entity_mask.copy_(self.ledger.market_mask)
        self.ledger_dirty_target.fill_(-1)
        self.position_dirty_role.fill_(-1)
        self.market_dirty_slot.fill_(-1)

    def _update_ledger_cache(self) -> None:
        """Refresh tile-ledger summaries for rows changed by one transition."""
        decision = self.decision
        if decision is None:
            raise RuntimeError("intent transaction decision buffers are absent")
        state_encoder = self.policy.state_encoder
        rows = self._rows
        ledger_mask = self.ledger_dirty_target >= 0
        target = self.ledger_dirty_target.clamp(0, self.ledger.cells - 1)
        new_ledger = state_encoder.encode_ledger_entities(
            self.ledger.ledger[rows, target, None],
            decision.state.status[rows, target, None],
            decision.state.work_priorities[rows, target, None],
            self.encoded_tiles[rows, target, None],
            target[:, None],
        ).squeeze(1)
        old_ledger = self.ledger_entities[rows, target]
        ledger_delta = (new_ledger - old_ledger) * ledger_mask[:, None]
        self.ledger_sum.add_(ledger_delta)
        self.ledger_entities[rows, target] = torch.where(
            ledger_mask[:, None], new_ledger, old_ledger
        )

    def _update_position_cache(self) -> None:
        """Refresh the one position entity changed by a transition."""
        state_encoder = self.policy.state_encoder
        rows = self._rows
        role_mask = self.position_dirty_role >= 0
        role = self.position_dirty_role.clamp(0, 1)
        new_position = state_encoder.encode_position_entities(
            self.ledger.positions[rows, role, None]
        ).squeeze(1)
        old_position = self.position_entities[rows, role]
        position_delta = (new_position - old_position) * role_mask[:, None]
        self.position_sum.add_(position_delta)
        self.position_entities[rows, role] = torch.where(
            role_mask[:, None], new_position, old_position
        )

    def _update_market_cache(self) -> None:
        """Append newly selected market entities to the cached reduction."""
        state_encoder = self.policy.state_encoder
        rows = self._rows
        market_mask = self.market_dirty_slot >= 0
        market_slot = self.market_dirty_slot.clamp(
            0, self.policy.architecture.maximum_market_orders - 1
        )
        new_market = state_encoder.encode_market_entities(
            self.ledger.market_prefix[rows, market_slot, None],
            market_slot[:, None],
        ).squeeze(1)
        old_market = self.market_entities[rows, market_slot]
        was_active = self.market_entity_mask[rows, market_slot] & market_mask
        market_delta = (
            new_market - old_market * was_active[:, None]
        ) * market_mask[:, None]
        self.market_sum.add_(market_delta)
        self.market_count.add_((market_mask & ~was_active).float())
        self.market_entities[rows, market_slot] = torch.where(
            market_mask[:, None], new_market, old_market
        )
        self.market_entity_mask[rows, market_slot] |= market_mask

    def _update_work_cache(self) -> None:
        """Apply the exact removed/added work-entity delta."""
        removed = self.policy.state_encoder.encode_work_entities(
            self.ledger.work_removed_fields[:, None]
        ).squeeze(1)
        added = self.policy.state_encoder.encode_work_entities(
            self.ledger.work_added_fields[:, None]
        ).squeeze(1)
        removed_mask = self.ledger.work_removed_mask[:, None]
        added_mask = self.ledger.work_added_mask[:, None]
        self.work_sum.copy_(self.work_sum - removed * removed_mask + added * added_mask)
        self.work_count.copy_(
            self.work_count
            - self.ledger.work_removed_mask.float()
            + self.ledger.work_added_mask.float()
        )

    def _update_state_cache(self) -> None:
        """Refresh every state summary after one transition."""
        self._update_ledger_cache()
        self._update_position_cache()
        self._update_market_cache()
        self._update_work_cache()

    @staticmethod
    def _candidate_slice(state: IntentTensorState, width: int) -> IntentTensorState:
        return IntentTensorState(
            candidate_fields=state.candidate_fields[:, :width],
            candidate_features=state.candidate_features[:, :width],
            candidate_mask=state.candidate_mask[:, :width],
            ledger=state.ledger,
            status=state.status,
            work_priorities=state.work_priorities,
            work_orders=state.work_orders,
            work_mask=state.work_mask,
            positions=state.positions,
            market_prefix=state.market_prefix,
            market_mask=state.market_mask,
            phase=state.phase,
        )

    def _variant(self, index: int) -> None:
        decision = self.decision
        if decision is None:
            raise RuntimeError("intent transaction setup is absent")
        state = self._candidate_slice(decision.state, self.buckets[index])
        ledger_summary = self.ledger_sum / float(self.ledger.cells)
        work_summary = self.work_sum / self.work_count.clamp_min(1.0)[:, None]
        position_summary = self.position_sum / 2.0
        market_summary = self.market_sum / self.market_count.clamp_min(1.0)[:, None]
        output = self._compiled_policy(
            self.encoded_context,
            self.encoded_tiles,
            state,
            ledger_summary,
            work_summary,
            position_summary,
            market_summary,
        )
        if not isinstance(output, IntentPolicyOutput):
            raise TypeError("compiled intent policy returned an invalid output")
        selection = self._select_output(output)
        self.selection = selection
        stream = torch.cuda.current_stream(self.device)
        self._kernels.transition(
            stream.cuda_stream,
            decision.state.candidate_fields.data_ptr(),
            selection.indices.data_ptr(),
            selection.log_probability.data_ptr(),
            selection.value.data_ptr(),
        )
        self._compiled_cache_update()

    def _select_output(self, output: IntentPolicyOutput) -> IntentSelection:
        """Select using the transaction's checkpointed external random tape."""
        if not self.sample:
            return self.policy._select_output(
                output,
                sample=False,
                generator=None,
                compute_entropy=False,
            )
        probabilities = torch.softmax(output.candidate_logits.float(), dim=-1)
        rows = torch.arange(self.batch, device=self.device)
        steps = self.ledger.trace_counts.clamp(0, self.ledger.trace_capacity - 1)
        quantile = self.uniform[rows, steps]
        indices = (probabilities.cumsum(dim=-1) <= quantile[:, None]).sum(dim=-1)
        indices = indices.clamp_max(probabilities.shape[1] - 1)
        selected = probabilities.gather(1, indices[:, None]).squeeze(1)
        log_probability = selected.clamp_min(torch.finfo(selected.dtype).tiny).log()
        return IntentSelection(
            indices=indices,
            log_probability=log_probability,
            entropy=torch.zeros_like(log_probability),
            value=output.value,
        )

    def _snapshot(self) -> dict[str, Tensor]:
        snapshot = {
            name: getattr(self.ledger, name).clone() for name in self._MUTABLE_LEDGER_FIELDS
        }
        decision = self.decision
        if decision is None:
            raise RuntimeError("intent transaction decision buffers are absent")
        snapshot["transaction_status"] = decision.state.status.clone()
        snapshot["transaction_work_priorities"] = decision.state.work_priorities.clone()
        snapshot["transaction_work_sum"] = self.work_sum.clone()
        snapshot["transaction_work_count"] = self.work_count.clone()
        snapshot["transaction_ledger_entities"] = self.ledger_entities.clone()
        snapshot["transaction_ledger_sum"] = self.ledger_sum.clone()
        snapshot["transaction_position_entities"] = self.position_entities.clone()
        snapshot["transaction_position_sum"] = self.position_sum.clone()
        snapshot["transaction_market_entities"] = self.market_entities.clone()
        snapshot["transaction_market_sum"] = self.market_sum.clone()
        snapshot["transaction_market_count"] = self.market_count.clone()
        snapshot["transaction_market_entity_mask"] = self.market_entity_mask.clone()
        snapshot["transaction_ledger_dirty_target"] = self.ledger_dirty_target.clone()
        snapshot["transaction_position_dirty_role"] = self.position_dirty_role.clone()
        snapshot["transaction_market_dirty_slot"] = self.market_dirty_slot.clone()
        snapshot["transaction_decision_variant"] = self.decision_variant.clone()
        return snapshot

    def _restore(self, snapshot: dict[str, Tensor]) -> None:
        decision = self.decision
        if decision is None:
            raise RuntimeError("intent transaction decision buffers are absent")
        for name, value in snapshot.items():
            if name == "transaction_status":
                decision.state.status.copy_(value)
            elif name == "transaction_work_priorities":
                decision.state.work_priorities.copy_(value)
            elif name == "transaction_work_sum":
                self.work_sum.copy_(value)
            elif name == "transaction_work_count":
                self.work_count.copy_(value)
            elif name == "transaction_ledger_entities":
                self.ledger_entities.copy_(value)
            elif name == "transaction_ledger_sum":
                self.ledger_sum.copy_(value)
            elif name == "transaction_position_entities":
                self.position_entities.copy_(value)
            elif name == "transaction_position_sum":
                self.position_sum.copy_(value)
            elif name == "transaction_market_entities":
                self.market_entities.copy_(value)
            elif name == "transaction_market_sum":
                self.market_sum.copy_(value)
            elif name == "transaction_market_count":
                self.market_count.copy_(value)
            elif name == "transaction_market_entity_mask":
                self.market_entity_mask.copy_(value)
            elif name == "transaction_ledger_dirty_target":
                self.ledger_dirty_target.copy_(value)
            elif name == "transaction_position_dirty_role":
                self.position_dirty_role.copy_(value)
            elif name == "transaction_market_dirty_slot":
                self.market_dirty_slot.copy_(value)
            elif name == "transaction_decision_variant":
                self.decision_variant.copy_(value)
            else:
                getattr(self.ledger, name).copy_(value)

    def _capture(self) -> None:
        # Every retained capacity is intentionally shape-static. Multiple
        # rollout streams specialize the same Python code object for distinct
        # ledger buffers, so the framework's default limit of eight is below
        # this bounded graph family even though no shape is created online.
        recompile_limit = max(
            int(torch.compiler.config.recompile_limit),
            _GRAPH_RECOMPILE_LIMIT,
        )
        with torch.compiler.config.patch(  # type: ignore[attr-defined]
            recompile_limit=recompile_limit
        ):
            self._capture_graphs()

    def _capture_graphs(self) -> None:
        """Compile and capture the bounded setup and policy graph family."""
        started = time.perf_counter()
        for capacity in self.setup_capacities:
            self._setup_variant(capacity)
            torch.cuda.current_stream(self.device).synchronize()
            setup = torch.cuda.CUDAGraph(keep_graph=True)
            with serialized_graph_capture(setup):
                self._setup_variant(capacity)
            setup.replay()
            torch.cuda.current_stream(self.device).synchronize()
            self.setup_graphs.append(setup)
        snapshot = self._snapshot()
        for index in range(len(self.buckets)):
            with torch.inference_mode(), torch.autocast(device_type="cuda", dtype=torch.bfloat16):
                self._variant(index)
            torch.cuda.current_stream(self.device).synchronize()
            self._restore(snapshot)
            graph = torch.cuda.CUDAGraph(keep_graph=True)
            with (
                torch.inference_mode(),
                torch.autocast(device_type="cuda", dtype=torch.bfloat16),
                serialized_graph_capture(graph),
            ):
                self._variant(index)
            torch.cuda.current_stream(self.device).synchronize()
            self._restore(snapshot)
            self.variant_graphs.append(graph)
        self.conditional = _program_cuda.ConditionalCountSwitchWhileGraph(
            [graph.raw_cuda_graph() for graph in self.setup_graphs],
            self.decision_variant.data_ptr(),
            [graph.raw_cuda_graph() for graph in self.variant_graphs],
            self.ledger.live_candidate_count.data_ptr(),
            self.ledger.live_batch_count.data_ptr(),
            self.buckets[0],
        )
        self.capture_seconds += time.perf_counter() - started

    def _capture_initial_state(self) -> None:
        """Capture turn initialization into fixed cache buffers."""
        started = time.perf_counter()
        with torch.inference_mode(), torch.autocast(device_type="cuda", dtype=torch.bfloat16):
            self._compiled_initialize()
        torch.cuda.current_stream(self.device).synchronize()
        graph = torch.cuda.CUDAGraph(keep_graph=True)
        with (
            torch.inference_mode(),
            torch.autocast(device_type="cuda", dtype=torch.bfloat16),
            serialized_graph_capture(graph),
        ):
            self._compiled_initialize()
        graph.replay()
        torch.cuda.current_stream(self.device).synchronize()
        self.initial_state_graph = graph
        self.capture_seconds += time.perf_counter() - started

    def _install(
        self,
        raw: Mapping[str, object],
        auxiliary: Mapping[str, object],
        economic: NDArray[np.int32],
        context: Tensor,
        tile_context: Tensor,
    ) -> None:
        if context.shape != self.context.shape or tile_context.shape != self.tile_context.shape:
            raise ValueError("intent transaction context changed fixed batch shape")
        self.context.copy_(context)
        self.tile_context.copy_(tile_context)
        self.staging.install(raw, auxiliary, economic)
        values = self.staging.device
        self.ledger.begin_turn(
            values["ledger"],
            values["status"],
            values["work_orders"],
            values["work_mask"],
            values["positions"],
            values["market_prefix"],
            values["market_mask"],
            values["economic"],
            values["inactive_status"],
            values["asset_risk"],
        )
        self.decision_variant.zero_()
        if self.initial_state_graph is None:
            with serialized_graph_build():
                self._capture_initial_state()
        else:
            self.initial_state_graph.replay()

    def replay(
        self,
        raw: Mapping[str, object],
        auxiliary: Mapping[str, object],
        economic: NDArray[np.int32],
        context: Tensor,
        tile_context: Tensor,
    ) -> IntentTransactionTrace:
        """Run one complete transaction and synchronize its compact trace once."""
        self._install(raw, auxiliary, economic, context, tile_context)
        if self.conditional is None:
            with serialized_graph_build():
                self._capture()
            # Capture warms and restores the installed snapshot.
        conditional = self.conditional
        tape = self._behavior
        if conditional is None or tape is None:
            raise RuntimeError("intent transaction graph is not ready")
        stream = torch.cuda.current_stream(self.device)
        if self.sample:
            self.uniform.uniform_(generator=self.generator)
        conditional.launch(stream.cuda_stream)
        behavior_offset = tape.append_dense(
            self.ledger.trace_log_probability,
            self.ledger.trace_value,
        )
        self._host_selected.copy_(self.ledger.trace_selected, non_blocking=True)
        self._host_fields.copy_(self.ledger.trace_fields, non_blocking=True)
        self._host_counts.copy_(self.ledger.trace_counts, non_blocking=True)
        stream.synchronize()
        return IntentTransactionTrace(
            selected=self._host_selected.numpy().copy(),
            selected_fields=self._host_fields.numpy().copy(),
            counts=self._host_counts.numpy().copy(),
            behavior_offset=behavior_offset,
        )

    def close(self) -> None:
        """Release conditional and child graph resources."""
        self.conditional = None
        if self.initial_state_graph is not None:
            self.initial_state_graph.reset()
            self.initial_state_graph = None
        for graph in self.variant_graphs:
            graph.reset()
        self.variant_graphs.clear()
        for graph in self.setup_graphs:
            graph.reset()
        self.setup_graphs.clear()
        self.decision = None
        self.selection = None
        self._behavior = None


__all__ = ["IntentGpuTransactionGraph", "IntentTransactionTrace"]
