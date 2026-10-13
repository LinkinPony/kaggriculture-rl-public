"""CUDA-resident state owner for canonical intent transactions."""

from __future__ import annotations

import torch
from torch import Tensor

from kagg_revue.policy.economics.layout import EconomicStateLayout
from kagg_revue.policy.intents.gpu._ledger_abi import (
    _ANIMALS,
    _CROPS,
    _EMPTY,
    _GOOSE,
    _ITEMS,
    _LOCKED,
    _MAX_QUANTITY,
    _PLANT,
    _PRODUCTS,
    _REASON_ANIMAL_SHORTFALL,
    _REASON_CONFLICTING_ASSET,
    _REASON_LAND_LOCKED,
    _REASON_SEED_SHORTFALL,
    _REASON_WHEAT_SHORTFALL,
    _ROOT,
    _STATUS_AT_RISK,
    _STATUS_BLOCKED,
    _STATUS_RUNNING,
    _STATUS_SATISFIED,
    _STRUCTURE,
    _WEED,
    _WHEAT,
)
from kagg_revue.policy.intents.gpu.candidates import compile_decision
from kagg_revue.policy.intents.gpu.transitions import apply_choice
from kagg_revue.policy.intents.gpu.types import IntentGpuDecision
from kagg_revue.policy.intents.schema import IntentArchitecture


class IntentGpuLedger:
    """Mutate a lossless visible shadow of one native intent transaction."""

    def __init__(
        self,
        architecture: IntentArchitecture,
        batch: int,
        unit_limit: int,
        device: torch.device,
        *,
        maximum_steps: int,
        episode_steps: int,
        turns_per_day: int,
    ) -> None:
        """Allocate fixed transaction state and dense device trace buffers."""
        if device.type != "cuda" or batch < 1 or maximum_steps < 2:
            raise ValueError("intent GPU ledger requires a nonempty CUDA batch")
        if architecture.item_count != _ITEMS:
            raise ValueError("intent GPU ledger requires the native item vocabulary")
        if architecture.unit_limit != unit_limit:
            raise ValueError("intent GPU ledger unit limit differs from the model")
        self.architecture = architecture
        self.batch = batch
        self.device = device
        self.maximum_steps = maximum_steps
        self.episode_steps = episode_steps
        self.turns_per_day = turns_per_day
        self.layout = EconomicStateLayout.create(architecture.board_size, unit_limit)
        self.cells = architecture.tile_count
        self.work_capacity = self.cells * 8 + _ITEMS + 2 * unit_limit
        self.candidate_capacity = max(
            self.work_capacity,
            self.cells * 3,
            _CROPS * 9 + _ANIMALS * 36,
            _MAX_QUANTITY,
        )
        self.phase_candidate_capacities = (
            34,
            self.cells,
            _CROPS * 9 + _ANIMALS * 36,
            self.cells,
            self.cells,
            24,
            self.work_capacity,
            2,
            self.cells * 3,
            2,
            _ITEMS,
            _MAX_QUANTITY,
            3,
            _MAX_QUANTITY,
            unit_limit,
            _ITEMS,
            _MAX_QUANTITY,
            unit_limit,
            unit_limit,
            15,
            self.cells,
            _ITEMS,
            _MAX_QUANTITY,
            unit_limit,
            1,
        )
        self.trace_capacity = maximum_steps + 9
        self.ledger = torch.empty(
            (batch, self.cells, architecture.ledger_field_count),
            dtype=torch.long,
            device=device,
        )
        self.status_deadline = torch.empty((batch, self.cells), dtype=torch.long, device=device)
        self.inactive_status = torch.empty((batch, self.cells, 2), dtype=torch.long, device=device)
        self.asset_risk = torch.empty((batch, self.cells), dtype=torch.bool, device=device)
        self.work_orders = torch.empty(
            (batch, self.work_capacity, architecture.work_field_count),
            dtype=torch.long,
            device=device,
        )
        self.work_mask = torch.empty((batch, self.work_capacity), dtype=torch.bool, device=device)
        self.work_removed_fields = torch.zeros(
            (batch, architecture.work_field_count), dtype=torch.long, device=device
        )
        self.work_removed_mask = torch.zeros(batch, dtype=torch.bool, device=device)
        self.work_added_fields = torch.zeros_like(self.work_removed_fields)
        self.work_added_mask = torch.zeros_like(self.work_removed_mask)
        self.positions = torch.empty((batch, 2, 4), dtype=torch.long, device=device)
        self.market_prefix = torch.empty(
            (batch, architecture.maximum_market_orders, 3),
            dtype=torch.long,
            device=device,
        )
        self.market_mask = torch.empty(
            (batch, architecture.maximum_market_orders),
            dtype=torch.bool,
            device=device,
        )
        self.economic = torch.empty((batch, self.layout.width), dtype=torch.int32, device=device)
        self.carried = torch.empty((batch, _ITEMS), dtype=torch.long, device=device)
        self.unit_inventories = torch.empty(
            (batch, unit_limit, _ITEMS), dtype=torch.long, device=device
        )
        self.shed = torch.empty((batch, _ITEMS), dtype=torch.long, device=device)
        self.unit_positions = torch.empty((batch, unit_limit, 2), dtype=torch.long, device=device)
        self.owned = torch.empty_like(self.carried)
        self.tiles = torch.empty(
            (batch, self.cells, self.layout.tile_fields),
            dtype=torch.long,
            device=device,
        )
        self.work_applies = torch.empty((batch, self.cells, 8), dtype=torch.bool, device=device)
        self.market_product_ratio = torch.empty(
            (batch, _PRODUCTS),
            dtype=torch.float64,
            device=device,
        )
        self.phase = torch.full((batch,), _ROOT, dtype=torch.long, device=device)
        self.active = torch.ones(batch, dtype=torch.bool, device=device)
        self.pending_kind = torch.zeros(batch, dtype=torch.long, device=device)
        self.pending_target = torch.full((batch,), -1, dtype=torch.long, device=device)
        self.pending_role = torch.zeros(batch, dtype=torch.long, device=device)
        self.pending_unit = torch.full((batch,), -1, dtype=torch.long, device=device)
        self.pending_directive_operation = torch.zeros(batch, dtype=torch.long, device=device)
        self.pending_item = torch.full((batch,), -1, dtype=torch.long, device=device)
        self.pending_quantity = torch.zeros(batch, dtype=torch.long, device=device)
        self.pending_market_kind = torch.zeros(batch, dtype=torch.long, device=device)
        self.pending_market_item = torch.zeros(batch, dtype=torch.long, device=device)
        self.pending_market_upper = torch.zeros(batch, dtype=torch.long, device=device)
        self.last_ledger_key = torch.full((batch,), -1, dtype=torch.long, device=device)
        self.market_phase = torch.zeros(batch, dtype=torch.bool, device=device)
        self.trace_counts = torch.zeros(batch, dtype=torch.long, device=device)
        self.trace_selected = torch.zeros(
            (batch, self.trace_capacity), dtype=torch.long, device=device
        )
        self.trace_fields = torch.zeros(
            (batch, self.trace_capacity, architecture.candidate_field_count),
            dtype=torch.long,
            device=device,
        )
        self.trace_log_probability = torch.zeros(
            (self.trace_capacity, batch), dtype=torch.float32, device=device
        )
        self.trace_value = torch.zeros_like(self.trace_log_probability)
        self.live_candidate_count = torch.zeros((), dtype=torch.long, device=device)
        self.live_batch_count = torch.zeros((), dtype=torch.long, device=device)
        self._slots = torch.arange(self.candidate_capacity, dtype=torch.long, device=device)[None]
        self._targets = torch.arange(self.cells, dtype=torch.long, device=device)
        self._work_kinds = torch.arange(8, dtype=torch.long, device=device)
        self._items = torch.arange(_ITEMS, dtype=torch.long, device=device)
        self._units = torch.arange(unit_limit, dtype=torch.long, device=device)
        self._first_yield_day = torch.as_tensor((2, 2, 8, 10, 10), dtype=torch.long, device=device)

    def begin_turn(
        self,
        ledger: Tensor,
        status: Tensor,
        work_orders: Tensor,
        work_mask: Tensor,
        positions: Tensor,
        market_prefix: Tensor,
        market_mask: Tensor,
        economic: Tensor,
        inactive_status: Tensor,
        asset_risk: Tensor,
    ) -> None:
        """Install one native root snapshot and reset transaction-only fields."""
        self.ledger.copy_(ledger)
        self.status_deadline.copy_(status[..., 3])
        self.work_orders.copy_(work_orders)
        self.work_mask.copy_(work_mask)
        self.positions.copy_(positions)
        self.market_prefix.copy_(market_prefix)
        self.market_mask.copy_(market_mask)
        self.economic.copy_(economic)
        self.inactive_status.copy_(inactive_status)
        self.asset_risk.copy_(asset_risk)
        self.phase.fill_(_ROOT)
        self.active.fill_(True)
        self.pending_kind.zero_()
        self.pending_target.fill_(-1)
        self.pending_role.zero_()
        self.pending_unit.fill_(-1)
        self.pending_directive_operation.zero_()
        self.pending_item.fill_(-1)
        self.pending_quantity.zero_()
        self.pending_market_kind.zero_()
        self.pending_market_item.zero_()
        self.pending_market_upper.zero_()
        self.last_ledger_key.fill_(-1)
        self.market_phase.zero_()
        self.trace_counts.zero_()
        self.trace_selected.zero_()
        self.trace_fields.zero_()
        self.trace_log_probability.zero_()
        self.trace_value.zero_()
        self.live_candidate_count.zero_()
        self.live_batch_count.fill_(self.batch)
        self.work_removed_fields.zero_()
        self.work_removed_mask.zero_()
        self.work_added_fields.zero_()
        self.work_added_mask.zero_()
        self._prepare_turn_static()

    def _prepare_turn_static(self) -> None:
        """Decode official-turn values that cannot change inside a transaction."""
        carried, shed, owned, inventories = self._inventories()
        tiles = self._tiles()
        self.carried.copy_(carried)
        self.unit_inventories.copy_(inventories)
        self.shed.copy_(shed)
        self.owned.copy_(owned)
        self.tiles.copy_(tiles)
        self.unit_positions.copy_(
            self.economic[
                :,
                self.layout.positions : self.layout.positions + self.layout.unit_limit * 2,
            ].view(self.batch, self.layout.unit_limit, 2)
        )
        kind = tiles[..., 0]
        plant = kind == _PLANT
        animal = (kind == _STRUCTURE) & (tiles[..., 7] != 0)
        structure_without_animal = (kind == _STRUCTURE) & ~animal
        self.work_applies.copy_(
            torch.stack(
                (
                    plant | animal,
                    plant,
                    animal,
                    animal,
                    animal,
                    (kind == _WEED) | plant | structure_without_animal,
                    plant,
                    animal,
                ),
                dim=-1,
            )
        )
        prices = self.economic[
            :, self.layout.market_prices : self.layout.market_prices + _PRODUCTS
        ].double()
        bases = self.economic[
            :, self.layout.market_base_milli : self.layout.market_base_milli + _PRODUCTS
        ].double()
        self.market_product_ratio.copy_(prices * 1000.0 / bases.clamp_min(1.0))

    def _inventories(self) -> tuple[Tensor, Tensor, Tensor, Tensor]:
        inventories = (
            self.economic[
                :,
                self.layout.inventories : self.layout.inventories + self.layout.unit_limit * _ITEMS,
            ]
            .view(self.batch, self.layout.unit_limit, _ITEMS)
            .long()
        )
        unit_count = self.economic[:, 1].long().clamp(1, self.layout.unit_limit)
        present = self._units[None, :, None] < unit_count[:, None, None]
        carried = (inventories * present).sum(1)
        shed = self.economic[:, self.layout.shed : self.layout.shed + _ITEMS].long()
        return carried, shed, carried + shed, inventories

    def _tiles(self) -> Tensor:
        width = self.cells * self.layout.tile_fields
        return (
            self.economic[:, self.layout.tiles : self.layout.tiles + width]
            .view(self.batch, self.cells, self.layout.tile_fields)
            .long()
        )

    def _work_applicability(self, tiles: Tensor) -> tuple[Tensor, Tensor]:
        kind = tiles[..., 0]
        plant = kind == _PLANT
        animal = (kind == _STRUCTURE) & (tiles[..., 7] != 0)
        ledger_item = self.ledger[..., 2] - 1
        crop_match = (
            (self.ledger[..., 0] != 0)
            & (self.ledger[..., 1] == 1)
            & plant
            & (ledger_item == tiles[..., 1])
        )
        animal_match = (
            (self.ledger[..., 0] != 0)
            & (self.ledger[..., 1] == 2)
            & animal
            & (ledger_item == _GOOSE + tiles[..., 8])
        )
        service = torch.zeros_like(self.work_applies)
        service[..., 2] = animal_match & (self.ledger[..., 3] == 3)
        service[..., 4] = animal_match & (self.ledger[..., 5] == 1)
        service[..., 6] = crop_match & (self.ledger[..., 3] == 2)
        service[..., 7] = animal_match & (self.ledger[..., 3] == 3)
        return self.work_applies, service

    def _status(self, tiles: Tensor, owned: Tensor) -> Tensor:
        item = (self.ledger[..., 2] - 1).clamp(0, _ITEMS - 1)
        tile_kind = tiles[..., 0]
        plant = tile_kind == _PLANT
        animal = (tile_kind == _STRUCTURE) & (tiles[..., 7] != 0)
        crop_contract = self.ledger[..., 1] == 1
        animal_contract = self.ledger[..., 1] == 2
        item_owned = owned.gather(1, item)
        seed_count = self.economic[:, self.layout.seeds : self.layout.seeds + _CROPS].long()
        crop_item = item.clamp(0, _CROPS - 1)
        seeds = seed_count.gather(1, crop_item)
        matches = (crop_contract & plant & (item == tiles[..., 1])) | (
            animal_contract & animal & (item == _GOOSE + tiles[..., 8])
        )
        active = self.ledger[..., 0] != 0
        risk = matches & self.asset_risk
        status = self.inactive_status[..., 0]
        reason = self.inactive_status[..., 1]
        shortfall = torch.zeros_like(status)
        status = torch.where(matches, torch.where(risk, _STATUS_AT_RISK, _STATUS_SATISFIED), status)
        wheat_shortfall = risk & animal_contract & (owned[:, _WHEAT] <= 0)[:, None]
        reason = torch.where(wheat_shortfall, _REASON_WHEAT_SHORTFALL, reason)
        shortfall = torch.where(wheat_shortfall, 1, shortfall)
        land_locked = active & ~matches & (tile_kind == _LOCKED)
        seed_shortfall = active & ~matches & crop_contract & (tile_kind == _EMPTY) & (seeds <= 0)
        animal_shortfall = (
            active
            & ~matches
            & animal_contract
            & (tile_kind == _STRUCTURE)
            & ~animal
            & (item_owned <= 0)
        )
        runnable = (
            active
            & ~matches
            & ((tile_kind == _EMPTY) | (tile_kind == _WEED) | ((tile_kind == _STRUCTURE) & ~animal))
        )
        conflict = (
            active & ~matches & ~land_locked & ~seed_shortfall & ~animal_shortfall & ~runnable
        )
        status = torch.where(land_locked, _STATUS_BLOCKED, status)
        reason = torch.where(land_locked, _REASON_LAND_LOCKED, reason)
        status = torch.where(seed_shortfall, _STATUS_BLOCKED, status)
        reason = torch.where(seed_shortfall, _REASON_SEED_SHORTFALL, reason)
        shortfall = torch.where(seed_shortfall, item + 1, shortfall)
        status = torch.where(animal_shortfall, _STATUS_BLOCKED, status)
        reason = torch.where(animal_shortfall, _REASON_ANIMAL_SHORTFALL, reason)
        shortfall = torch.where(animal_shortfall, item + 1, shortfall)
        status = torch.where(runnable, _STATUS_RUNNING, status)
        status = torch.where(conflict, _STATUS_BLOCKED, status)
        reason = torch.where(conflict, _REASON_CONFLICTING_ASSET, reason)
        return torch.stack((status, reason, shortfall, self.status_deadline), dim=-1)

    def _work_priorities(self) -> Tensor:
        result = torch.full((self.batch, self.cells * 8), -1, dtype=torch.long, device=self.device)
        valid = self.work_mask & (self.work_orders[..., 0] < 8)
        index = self.work_orders[..., 1].clamp(0, self.cells - 1) * 8 + self.work_orders[
            ..., 0
        ].clamp(0, 7)
        priority = torch.where(valid, self.work_orders[..., 4], -1)
        result.scatter_reduce_(1, index, priority, reduce="amax", include_self=True)
        return result.view(self.batch, self.cells, 8)

    def decision(self, candidate_capacity: int | None = None) -> IntentGpuDecision:
        """Generate one compact padded candidate batch on the device."""
        return compile_decision(self, candidate_capacity)

    def apply_selection(
        self,
        decision: IntentGpuDecision,
        selected: Tensor,
        log_probability: Tensor,
        value: Tensor,
    ) -> None:
        """Record and apply one sampled successor for every live lane."""
        rows = torch.arange(self.batch, device=self.device)
        choice_fields = decision.state.candidate_fields[rows, selected]
        self.apply_choice(choice_fields, selected, log_probability, value)

    def apply_choice(
        self,
        choice_fields: Tensor,
        selected: Tensor,
        log_probability: Tensor,
        value: Tensor,
    ) -> None:
        """Apply already gathered candidate fields to the resident ledger."""
        apply_choice(self, choice_fields, selected, log_probability, value)


__all__ = ["IntentGpuDecision", "IntentGpuLedger"]
