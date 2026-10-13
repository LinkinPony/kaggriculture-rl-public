"""CUDA-resident shadow compiler for complete conditional turn programs."""

from __future__ import annotations

import math
from dataclasses import dataclass

import torch
from torch import Tensor

from kagg_revue.policy.cuda.session import (
    GpuPolicyStateLayout,
    compile_policy_legal,
)
from kagg_revue.policy.economics.gpu.transition import project_market_selection
from kagg_revue.policy.economics.layout import EconomicStateLayout
from kagg_revue.policy.economics.pricing import fibonacci, market_curves
from kagg_revue.policy.programs.encoding import ProgramPreparedContext
from kagg_revue.policy.programs.grammar import (
    NativeProgramMasks,
    ProgramActions,
    ProgramDecisionInputs,
    ProgramPrefixState,
)
from kagg_revue.policy.programs.native import NativeProgramContract
from kagg_revue.policy.programs.schema import ProgramStepOutput

_ITEMS = 12
_PRODUCTS = 9
_CROPS = 5
_ANIMALS = 3
_NONE = 14
_COOP = 12
_PASTURE = 13
_MAX_QUANTITY = 128


def _rows(batch: int, device: torch.device) -> Tensor:
    return torch.arange(batch, dtype=torch.long, device=device)


def _gather(state: Tensor, index: Tensor) -> Tensor:
    return state.gather(1, index[:, None]).squeeze(1)


def _quantity_modes(
    maximum: Tensor, *, deficit: Tensor | None = None, affordable: bool = False, sell: bool = False
) -> Tensor:
    """Build the five compiler quantity modes from an exact maximum."""
    result = torch.zeros((*maximum.shape, 5), dtype=torch.bool, device=maximum.device)
    present = maximum > 0
    result[..., 0] = present
    if sell:
        result[..., 1] = maximum > 1
    elif affordable:
        result[..., 3] = maximum > 1
    else:
        result[..., 1] = maximum > 1
    if deficit is not None:
        result[..., 2] = present & (deficit > 0)
    result[..., 4] = maximum > 1
    return result


@dataclass(frozen=True)
class ProgramGpuCompilerOutput:
    """Device-resident official action buffers produced for one turn."""

    tokens: Tensor
    quantities: Tensor
    decision_counts: Tensor
    unit_counts: Tensor


class ProgramGpuCompiler:
    """Own persistent options and mutate a lossless CUDA shadow state."""

    def __init__(
        self,
        contract: NativeProgramContract,
        batch: int,
        device: torch.device,
        *,
        episode_steps: int,
        turns_per_day: int,
    ) -> None:
        """Allocate fixed H200 rollout buffers and persistent option state."""
        if device.type != "cuda" or batch < 1:
            raise ValueError("program CUDA compiler requires a nonempty CUDA batch")
        self.contract = contract
        self.batch = batch
        self.device = device
        self.episode_steps = episode_steps
        self.turns_per_day = turns_per_day
        self.layout = EconomicStateLayout.create(contract.board_size, contract.unit_limit)
        self.policy_layout = GpuPolicyStateLayout(
            board_size=self.layout.board_size,
            unit_limit=self.layout.unit_limit,
            header_fields=self.layout.header_fields,
            positions=self.layout.positions,
            inventories=self.layout.inventories,
            inventory_order=self.layout.inventory_order,
            shed=self.layout.shed,
            seeds=self.layout.seeds,
            market_inventory=self.layout.market_inventory,
            market_prices=self.layout.market_prices,
            market_base_milli=self.layout.market_base_milli,
            market_i0=self.layout.market_i0,
            market_t_milli=self.layout.market_t_milli,
            market_below_function=self.layout.market_below_function,
            market_below_target_milli=self.layout.market_below_target_milli,
            market_above_function=self.layout.market_above_function,
            market_above_target_milli=self.layout.market_above_target_milli,
            seed_costs=self.layout.seed_costs,
            animal_costs=self.layout.animal_costs,
            land_costs=self.layout.land_costs,
            tiles=self.layout.tiles,
            tile_fields=self.layout.tile_fields,
            width=self.layout.width,
        )
        shape = (batch, contract.unit_limit)
        self.option_valid = torch.zeros(shape, dtype=torch.bool, device=device)
        self.option_task = torch.zeros(shape, dtype=torch.long, device=device)
        self.option_target = torch.full(shape, -1, dtype=torch.long, device=device)
        self.option_argument = torch.full(shape, _NONE, dtype=torch.long, device=device)
        self.option_quantity_mode = torch.zeros(shape, dtype=torch.long, device=device)
        self.option_exact = torch.ones(shape, dtype=torch.long, device=device)
        self.option_phase = torch.zeros(shape, dtype=torch.long, device=device)
        self.option_created_step = torch.zeros(shape, dtype=torch.long, device=device)
        self.forced_target = torch.full(shape, -1, dtype=torch.long, device=device)
        self.forced_owner = torch.full(shape, -1, dtype=torch.long, device=device)
        self.last_day = torch.full((batch,), -1, dtype=torch.long, device=device)
        self.step = torch.zeros(batch, dtype=torch.long, device=device)
        self.state = torch.empty((batch, self.layout.width), dtype=torch.int32, device=device)
        capacity = contract.maximum_decisions
        self.tokens = torch.zeros((batch, capacity), dtype=torch.long, device=device)
        self.quantities = torch.zeros_like(self.tokens)
        self.trace_counts = torch.zeros(batch, dtype=torch.int16, device=device)
        self.turn_unit_counts = torch.ones(batch, dtype=torch.long, device=device)
        self._legal = torch.zeros((batch, 67), dtype=torch.bool, device=device)
        self._legal_phases = torch.zeros(batch, dtype=torch.long, device=device)
        self._decisions = torch.zeros(batch, dtype=torch.bool, device=device)
        self._item_ids = torch.arange(_ITEMS, dtype=torch.long, device=device)
        self._unit_ids = torch.arange(contract.unit_limit, dtype=torch.long, device=device)
        self._target_ids = torch.arange(contract.tile_count, dtype=torch.long, device=device)
        self._product_purchase_ids = torch.arange(2, dtype=torch.long, device=device) * 8
        self._raw_tokens = torch.as_tensor(
            (5, 17, 18, 30, 35, 36, 37, 38, 39, 40, 41, 42, 43),
            dtype=torch.long,
            device=device,
        )
        self._task_tokens = torch.as_tensor(
            (30, 35, 36, 37, 38, 39, 18, 41, 43, 42, 0, 0, 0, 30, 17, 0),
            dtype=torch.long,
            device=device,
        )

    def reset(self) -> None:
        """Drop persistent option state when a rollout group is rebound."""
        self.option_valid.zero_()
        self.forced_target.fill_(-1)
        self.forced_owner.fill_(-1)
        self.last_day.fill_(-1)

    def begin_turn(self, compact_state: Tensor, step: int) -> None:
        """Upload one official snapshot and initialize its device-only turn."""
        if compact_state.shape != self.state.shape or compact_state.dtype != torch.int32:
            raise ValueError("program CUDA compiler received a different compact state ABI")
        self.state.copy_(compact_state)
        self.step.fill_(step)
        day = self.state[:, 0].long()
        changed = (self.last_day >= 0) & (day != self.last_day)
        if self.contract.unit_limit > 1:
            self.option_valid[:, 1:] &= ~changed[:, None]
        self.last_day.copy_(day)
        self.forced_target.fill_(-1)
        self.forced_owner.fill_(-1)
        self.state[:, 2].zero_()
        self.state[:, 3].zero_()
        self.state[:, 4].zero_()
        self.tokens.zero_()
        self.quantities.zero_()
        self.trace_counts.zero_()
        self.turn_unit_counts.copy_(self.state[:, 1])

    def _current(self, values: Tensor) -> Tensor:
        unit = self.state[:, 2].long().clamp(0, self.contract.unit_limit - 1)
        return values.gather(1, unit[:, None]).squeeze(1)

    def _inventory(self) -> Tensor:
        unit = self.state[:, 2].long().clamp(0, self.contract.unit_limit - 1)
        items = torch.arange(_ITEMS, device=self.device)
        indices = self.layout.inventories + unit[:, None] * _ITEMS + items[None]
        return self.state.gather(1, indices).long()

    def _positions(self) -> tuple[Tensor, Tensor]:
        unit = self.state[:, 2].long().clamp(0, self.contract.unit_limit - 1)
        index = self.layout.positions + unit * 2
        return _gather(self.state, index).long(), _gather(self.state, index + 1).long()

    def _tiles(self) -> Tensor:
        count = self.contract.tile_count * self.layout.tile_fields
        return (
            self.state[:, self.layout.tiles : self.layout.tiles + count]
            .view(self.batch, self.contract.tile_count, self.layout.tile_fields)
            .long()
        )

    def _planned_requirements(self, option_live: Tensor) -> Tensor:
        """Count item consumers represented by the live unit options."""
        requirements = torch.zeros((self.batch, _ITEMS), dtype=torch.long, device=self.device)
        for item in range(_ITEMS):
            consumes = (
                ((self.option_task == 7) & (item == 0))
                | ((self.option_task == 3) & (item == 8))
                | ((self.option_task == 6) & (self.option_argument == item))
            )
            requirements[:, item] = (option_live & consumes).sum(1)
        return requirements

    def _market_deficits(self, option_live: Tensor) -> Tensor:
        """Return exact per-order deficits after all currently held supply."""
        deficits = torch.zeros((self.batch, 7, _ITEMS), dtype=torch.long, device=self.device)
        seed_requirements = torch.stack(
            [
                (
                    option_live
                    & ((self.option_task == 0) | (self.option_task == 13))
                    & (self.option_argument == crop)
                    & (self.option_phase != 5)
                ).sum(1)
                for crop in range(_CROPS)
            ],
            dim=1,
        )
        seeds = self.state[:, self.layout.seeds : self.layout.seeds + _CROPS].long()
        deficits[:, 2, :_CROPS] = (seed_requirements - seeds).clamp_min(0)

        requirements = self._planned_requirements(option_live)
        inventories = self.state[
            :,
            self.layout.inventories : self.layout.inventories + self.contract.unit_limit * _ITEMS,
        ].view(self.batch, self.contract.unit_limit, _ITEMS)
        unit_count = self.turn_unit_counts.clamp(1, self.contract.unit_limit)
        present = self._unit_ids[None, :, None] < unit_count[:, None, None]
        shed = self.state[:, self.layout.shed : self.layout.shed + _ITEMS].long()
        available = shed + (inventories * present).sum(1)
        item_deficits = (requirements - available).clamp_min(0)
        deficits[:, 3, 0] = item_deficits[:, 0]
        deficits[:, 3, 8] = item_deficits[:, 8]
        deficits[:, 4, 9:12] = item_deficits[:, 9:12]
        return deficits

    def _option_is_valid(self, x: Tensor, y: Tensor, tiles: Tensor) -> Tensor:
        task = self._current(self.option_task)
        target = self._current(self.option_target)
        argument = self._current(self.option_argument)
        mode = self._current(self.option_quantity_mode)
        exact = self._current(self.option_exact)
        valid = self._current(self.option_valid) & (argument >= 0) & (argument < 15) & (exact > 0)
        targeted = task != 15
        valid &= ~targeted | ((target >= 0) & (target < self.contract.tile_count))
        safe_target = target.clamp(0, self.contract.tile_count - 1)
        selected = tiles.gather(
            1, safe_target[:, None, None].expand(-1, 1, self.layout.tile_fields)
        ).squeeze(1)
        inventory = self._inventory()
        shed = self.state[:, self.layout.shed : self.layout.shed + _ITEMS].long()
        room = (self.state[:, 5].long() - self.state[:, 8].long()).clamp_min(0)
        safe_item = argument.clamp(0, _ITEMS - 1)
        held = inventory.gather(1, safe_item[:, None]).squeeze(1)
        stored = shed.gather(1, safe_item[:, None]).squeeze(1)
        fetch_max = stored
        store_max = torch.minimum(held, room)
        quantity_max = torch.where(task == 10, fetch_max, store_max)
        logistics = (task == 10) | (task == 11)
        half = self.contract.board_size // 2
        target_x = safe_target % self.contract.board_size
        target_y = safe_target // self.contract.board_size
        target_is_shed = ((target_x == half - 1) | (target_x == half)) & (
            (target_y == half - 1) | (target_y == half)
        )
        valid &= ~((task == 10) | (task == 11) | (task == 14)) | target_is_shed
        logistics_valid = (argument < _ITEMS) & (quantity_max > 0)
        logistics_valid &= (
            (mode == 0)
            | (mode == 1)
            | ((mode == 2) & (task == 10))
            | ((mode == 4) & (exact <= quantity_max))
        )
        valid &= ~logistics | logistics_valid
        current = y * self.contract.board_size + x
        valid &= (task != 12) | (target != current)
        kind = selected[:, 0]
        has_animal = selected[:, 7] != 0
        animal_tile = (kind == 4) & has_animal
        supply = held > 0
        safe_task = (
            (argument < _CROPS)
            & (kind == 0)
            & (
                self.state.gather(1, (self.layout.seeds + argument.clamp(0, 4))[:, None]).squeeze(1)
                > 0
            )
        )
        safe_task = torch.where(
            self._current(self.option_phase) == 5, (kind == 3) & (selected[:, 3] == 0), safe_task
        )
        task_valid = torch.ones_like(valid)
        task_valid = torch.where(task == 0, safe_task, task_valid)
        task_valid = torch.where(task == 13, safe_task, task_valid)
        task_valid = torch.where(task == 1, (kind == 3) & (selected[:, 3] == 0), task_valid)
        first_yield = torch.where(selected[:, 1] < 2, 2, torch.where(selected[:, 1] == 2, 8, 10))
        harvestable = (selected[:, 5] > 0) & (
            ((kind == 3) & (self.state[:, 0].long() - selected[:, 2] >= first_yield)) | animal_tile
        )
        task_valid = torch.where(task == 2, harvestable, task_valid)
        fertilizer = inventory[:, 8] > 0
        wheat = inventory[:, 0] > 0
        task_valid = torch.where(
            task == 3, (kind == 3) & (fertilizer | (shed[:, 8] > 0)), task_valid
        )
        task_valid = torch.where(task == 4, (kind != 0) & (kind != 1) & ~animal_tile, task_valid)
        task_valid = torch.where(
            task == 5, ((argument == _COOP) | (argument == _PASTURE)) & (kind == 0), task_valid
        )
        animal = (argument - 9).clamp(0, 2)
        expected_structure = animal != 0
        deploy_target = (kind == 0) | (
            (kind == 4) & ~has_animal & (selected[:, 6] == expected_structure)
        )
        task_valid = torch.where(
            task == 6,
            (argument >= 9) & (argument < 12) & (supply | (stored > 0)) & deploy_target,
            task_valid,
        )
        task_valid = torch.where(
            task == 7, animal_tile & (selected[:, 9] == 0) & (wheat | (shed[:, 0] > 0)), task_valid
        )
        task_valid = torch.where(task == 8, animal_tile & (selected[:, 10] == 0), task_valid)
        task_valid = torch.where(task == 9, animal_tile & (selected[:, 11] != 0), task_valid)
        task_valid = torch.where(task == 14, inventory.sum(1) > 0, task_valid)
        valid &= logistics | (task == 12) | (task == 15) | task_valid
        return valid

    def decision(
        self,
        prepared: ProgramPreparedContext,
        prefix: ProgramPrefixState,
    ) -> tuple[ProgramDecisionInputs, NativeProgramMasks, Tensor]:
        """Compile exact policy inputs and masks for all still-live rows."""
        contract = self.contract
        batch = self.batch
        state = self.state
        rows = _rows(batch, self.device)
        compile_policy_legal(
            state, self._legal, self._legal_phases, self._decisions, self.policy_layout
        )
        phase_raw = state[:, 4].long()
        active = phase_raw != 2
        phase = phase_raw.clamp(0, 1)
        unit_phase = phase_raw == 0
        unit = state[:, 2].long().clamp(0, contract.unit_limit - 1)
        unit_count = self.turn_unit_counts.clamp(1, contract.unit_limit)
        market_slot = state[:, 3].long()
        x, y = self._positions()
        tiles = self._tiles()
        inventory = self._inventory()
        shed = state[:, self.layout.shed : self.layout.shed + _ITEMS].long()
        seeds = state[:, self.layout.seeds : self.layout.seeds + _CROPS].long()
        option_valid_now = self._option_is_valid(x, y, tiles)
        forced = self._current(self.forced_target) >= 0

        unit_ids = self._unit_ids[None]
        option_live = self.option_valid & (unit_ids < unit_count[:, None])
        target_ids = self._target_ids
        reservations = (
            (option_live[:, :, None] & (self.option_target[:, :, None] == target_ids[None, None]))
            .sum(dim=1)
            .to(torch.int16)
        )

        root = torch.zeros(
            (batch, contract.root_feature_count), dtype=torch.float32, device=self.device
        )
        turns = float(max(1, self.turns_per_day))
        days = float(max(1, math.ceil(self.episode_steps / self.turns_per_day)))
        root[:, 0] = 1.0
        root[:, 1] = unit_phase
        root[:, 2] = phase_raw == 1
        root[:, 3] = (self.step % self.turns_per_day).float() / turns
        root[:, 4] = state[:, 0].float() / days
        root[:, 5] = (self.episode_steps - self.step - 1).clamp_min(0).float() / max(
            1, self.episode_steps - 1
        )
        root[:, 6] = unit_count.float() / contract.unit_limit
        root[:, 7] = torch.log1p(state[:, 9].clamp_min(0).float()) / 16.0
        root[:, 8] = state[:, 8].float() / state[:, 5].clamp_min(1).float()
        root[:, 9] = (state[:, 5] - state[:, 8]).clamp_min(0).float() / state[:, 5].clamp_min(
            1
        ).float()
        root[:, 10] = market_slot.float() / contract.maximum_market_orders
        root[:, 11] = (contract.maximum_market_orders - market_slot).clamp_min(
            0
        ).float() / contract.maximum_market_orders
        root[:, 12] = option_live.sum(1).float() / contract.unit_limit
        root[:, 13] = torch.where(unit_phase, unit.float() / max(1, contract.unit_limit - 1), 0.0)
        root[:, 14] = torch.where(unit_phase, x.float() / max(1, contract.board_size - 1), 0.0)
        root[:, 15] = torch.where(unit_phase, y.float() / max(1, contract.board_size - 1), 0.0)
        root[:, 16] = torch.where(
            unit_phase,
            inventory.sum(1).float() / state[:, 5].clamp_min(1).float(),
            0.0,
        )
        root[:, 17] = torch.where(unit_phase, forced.float(), 0.0)

        option_present = self._current(self.option_valid) & unit_phase
        option_task = self._current(self.option_task)
        option_target = self._current(self.option_target)
        option_argument = self._current(self.option_argument)
        option_mode = self._current(self.option_quantity_mode)
        option_exact = self._current(self.option_exact)
        option_phase = self._current(self.option_phase)
        option_created = self._current(self.option_created_step)
        safe_target = option_target.clamp(0, contract.tile_count - 1)
        option = torch.zeros(
            (batch, contract.option_feature_count), dtype=torch.long, device=self.device
        )
        option[:, 0] = option_present
        option[:, 1] = torch.where(option_present, option_task + 1, 0)
        option[:, 2] = torch.where(option_present, option_target + 1, 0)
        option[:, 3] = torch.where(option_present, option_argument + 1, 0)
        option[:, 4] = torch.where(option_present, option_mode + 1, 0)
        option[:, 5] = torch.where(option_present, option_exact, 0)
        option[:, 6] = torch.where(option_present, option_phase + 1, 0)
        option[:, 7] = torch.where(option_present, (self.step - option_created).clamp_min(0), 0)
        option[:, 8] = option_present & option_valid_now
        option[:, 9] = torch.where(
            option_present & (option_target >= 0), safe_target % contract.board_size + 1, 0
        )
        option[:, 10] = torch.where(
            option_present & (option_target >= 0), safe_target // contract.board_size + 1, 0
        )
        option[:, 11] = torch.where(
            option_present & (option_target >= 0), reservations[rows, safe_target].long(), 0
        )

        control = torch.zeros((batch, 5), dtype=torch.bool, device=self.device)
        direction = torch.zeros((batch, 4), dtype=torch.bool, device=self.device)
        control[:, 4] = unit_phase & ~forced
        control[:, 0] = unit_phase & (forced | option_valid_now)
        direction[:, 0] = unit_phase & ~forced & (y > 0)
        direction[:, 1] = unit_phase & ~forced & (y + 1 < contract.board_size)
        direction[:, 2] = unit_phase & ~forced & (x + 1 < contract.board_size)
        direction[:, 3] = unit_phase & ~forced & (x > 0)
        control[:, 2] = direction.any(1)

        task_argument = torch.zeros(
            (batch, contract.task_count, contract.argument_count),
            dtype=torch.bool,
            device=self.device,
        )
        task_target = torch.zeros(
            (
                batch,
                contract.task_count,
                contract.argument_count,
                contract.tile_count,
            ),
            dtype=torch.bool,
            device=self.device,
        )
        kind = tiles[:, :, 0]
        has_animal = tiles[:, :, 7] != 0
        animal_tile = (kind == 4) & has_animal
        current_tile = y * contract.board_size + x
        other = option_live & (unit_ids != unit[:, None])
        option_targets = self.option_target[:, :, None] == target_ids[None, None]
        exact_reservations = other[:, :, None] & option_targets
        exclusive_tasks = (
            ((self.option_task <= 6) & (self.option_task != 1) & (self.option_task != 3))
            | (self.option_task == 13)
        )
        exclusive_at = (exact_reservations & exclusive_tasks[:, :, None]).any(1)

        def conflict(task_id: int) -> Tensor:
            same = (exact_reservations & (self.option_task[:, :, None] == task_id)).any(1)
            if task_id in (0, 2, 4, 5, 6, 13):
                value = same | exclusive_at
                if task_id in (5, 6):
                    paired = 6 if task_id == 5 else 5
                    pair_only = (exact_reservations & (self.option_task[:, :, None] == paired)).any(
                        1
                    )
                    value &= ~pair_only | same
                return value
            return same

        reserved_seed = torch.stack(
            [
                (
                    other
                    & ((self.option_task == 0) | (self.option_task == 13))
                    & (self.option_argument == crop)
                    & (self.option_phase != 5)
                ).sum(1)
                for crop in range(_CROPS)
            ],
            dim=1,
        )
        last_hour = (self.step % self.turns_per_day) == self.turns_per_day - 1
        all_positions = (
            state[:, self.layout.positions : self.layout.positions + contract.unit_limit * 2]
            .view(batch, contract.unit_limit, 2)
            .long()
        )
        later = (unit_ids > unit[:, None]) & (unit_ids < unit_count[:, None])
        later_tiles = all_positions[:, :, 1] * contract.board_size + all_positions[:, :, 0]
        later_water = (
            later[:, :, None]
            & (self.forced_target < 0)[:, :, None]
            & (later_tiles[:, :, None] == target_ids[None, None])
        ).any(1)
        waterer = ~last_hour[:, None] | later_water
        empty = kind == 0
        for crop in range(_CROPS):
            available = (seeds[:, crop] > 0)[:, None] & (
                ((seeds[:, crop] - reserved_seed[:, crop]) > 0)[:, None]
                | (target_ids[None] == current_tile[:, None])
            )
            valid = (
                empty
                & ~conflict(0)
                & waterer
                & available
            )
            task_target[:, 0, crop] = valid
            task_argument[:, 0, crop] = valid.any(1)
            plant = empty & ~conflict(13) & available
            task_target[:, 13, crop] = plant
            task_argument[:, 13, crop] = plant.any(1)
        task_target[:, 1, _NONE] = (kind == 3) & (tiles[:, :, 3] == 0)
        first_yield = torch.where(tiles[:, :, 1] < 2, 2, torch.where(tiles[:, :, 1] == 2, 8, 10))
        harvestable = (tiles[:, :, 5] > 0) & (
            ((kind == 3) & (state[:, 0, None].long() - tiles[:, :, 2] >= first_yield)) | animal_tile
        )
        task_target[:, 2, _NONE] = harvestable & ~conflict(2)
        planned_need = torch.zeros((batch, _ITEMS), dtype=torch.long, device=self.device)
        all_inventory = state[
            :,
            self.layout.inventories : self.layout.inventories + contract.unit_limit * _ITEMS,
        ].view(batch, contract.unit_limit, _ITEMS)
        for item in range(_ITEMS):
            consumes = (
                ((self.option_task == 7) & (item == 0))
                | ((self.option_task == 3) & (item == 8))
                | ((self.option_task == 6) & (self.option_argument == item))
            )
            planned_need[:, item] = (other & consumes & (all_inventory[:, :, item] == 0)).sum(1)
        supply = (inventory + shed - planned_need).clamp_min(0)
        task_target[:, 3, _NONE] = (kind == 3) & (supply[:, 8] > 0)[:, None]
        task_target[:, 4, _NONE] = (kind != 0) & (kind != 1) & ~animal_tile & ~conflict(4)
        for argument in (_COOP, _PASTURE):
            valid = empty & ~conflict(5)
            task_target[:, 5, argument] = valid
            task_argument[:, 5, argument] = valid.any(1)
        for animal in range(_ANIMALS):
            argument = 9 + animal
            compatible = empty | ((kind == 4) & ~has_animal & (tiles[:, :, 6] == (animal != 0)))
            valid = compatible & ~conflict(6) & (supply[:, argument] > 0)[:, None]
            task_target[:, 6, argument] = valid
            task_argument[:, 6, argument] = valid.any(1)
        task_target[:, 7, _NONE] = animal_tile & (tiles[:, :, 9] == 0) & (supply[:, 0] > 0)[:, None]
        task_target[:, 8, _NONE] = animal_tile & (tiles[:, :, 10] == 0)
        task_target[:, 9, _NONE] = animal_tile & (tiles[:, :, 11] != 0)
        task_target[:, 12, _NONE] = target_ids[None] != current_tile[:, None]
        for task_id in (1, 2, 3, 4, 7, 8, 9, 12, 14, 15):
            task_argument[:, task_id, _NONE] = True

        room = (state[:, 5].long() - state[:, 8].long()).clamp_min(0)
        task_max = torch.zeros(
            (batch, contract.task_count, contract.argument_count),
            dtype=torch.long,
            device=self.device,
        )
        task_max[:, 10, :_ITEMS] = shed
        task_max[:, 11, :_ITEMS] = torch.minimum(inventory, room[:, None])
        planned_requirements = self._planned_requirements(option_live)
        task_argument[:, 10, :_ITEMS] = task_max[:, 10, :_ITEMS] > 0
        task_argument[:, 11, :_ITEMS] = task_max[:, 11, :_ITEMS] > 0
        task_qmode = torch.zeros(
            (batch, contract.task_count, contract.argument_count, 5),
            dtype=torch.bool,
            device=self.device,
        )
        task_qmode[:, 10, :_ITEMS] = _quantity_modes(
            task_max[:, 10, :_ITEMS], deficit=planned_requirements
        )
        task_qmode[:, 11, :_ITEMS] = _quantity_modes(task_max[:, 11, :_ITEMS])
        target_x_ids = target_ids % contract.board_size
        target_y_ids = target_ids // contract.board_size
        half = contract.board_size // 2
        shed_targets = ((target_x_ids == half - 1) | (target_x_ids == half)) & (
            (target_y_ids == half - 1) | (target_y_ids == half)
        )
        task_target[:, 10, :_ITEMS] = (
            task_argument[:, 10, :_ITEMS, None] & shed_targets[None, None]
        )
        task_target[:, 11, :_ITEMS] = (
            task_argument[:, 11, :_ITEMS, None] & shed_targets[None, None]
        )
        task_target[:, 14, _NONE] = (
            inventory.sum(1) > 0
        )[:, None] & shed_targets[None]
        task = task_target.any(3).any(2)
        task[:, 15] = True
        task &= unit_phase[:, None] & ~forced[:, None]
        control[:, 1] = task.any(1)

        raw_operation = torch.zeros((batch, 13), dtype=torch.bool, device=self.device)
        raw_argument = torch.zeros((batch, 13, 15), dtype=torch.bool, device=self.device)
        raw_max = torch.zeros((batch, 13, 15), dtype=torch.long, device=self.device)
        raw_qmode = torch.zeros((batch, 13, 15, 5), dtype=torch.bool, device=self.device)
        raw_argument[:, 0, :_ITEMS] = self._legal[:, 5:17]
        raw_max[:, 0, :_ITEMS] = torch.where(raw_argument[:, 0, :_ITEMS], shed, 0)
        raw_argument[:, 2, :_ITEMS] = self._legal[:, 18:30]
        animal_place = (
            (self._item_ids[None] >= 9)
            & (kind[rows, current_tile][:, None] == 4)
            & (tiles[rows, current_tile, 7][:, None] == 0)
        )
        raw_max[:, 2, :_ITEMS] = torch.where(
            raw_argument[:, 2, :_ITEMS],
            torch.where(animal_place, 1, torch.minimum(inventory, room[:, None])),
            0,
        )
        raw_argument[:, 3, :_CROPS] = self._legal[:, 30:35] & (seeds > 0)
        raw_argument[:, 1, _NONE] = self._legal[:, 17] & (inventory.sum(1) > 0)
        tail_tokens = (35, 36, 37, 38, 39, 40, 41, 42, 43)
        for raw_id, token in enumerate(tail_tokens, start=4):
            raw_argument[:, raw_id, _NONE] = self._legal[:, token]
        raw_qmode[:, 0] = _quantity_modes(raw_max[:, 0])
        raw_qmode[:, 2] = _quantity_modes(raw_max[:, 2])
        raw_operation = raw_argument.any(2)
        raw_operation &= unit_phase[:, None] & ~forced[:, None]
        control[:, 3] = raw_operation.any(1)

        in_unit = unit_phase[:, None]
        task_argument &= in_unit[:, :, None]
        task_target &= in_unit[:, :, None, None]
        task_qmode &= in_unit[:, :, None, None]
        task_max *= in_unit[:, :, None]
        raw_argument &= in_unit[:, :, None]
        raw_qmode &= in_unit[:, :, None, None]
        raw_max *= in_unit[:, :, None]

        market_max = torch.zeros((batch, 7, _ITEMS), dtype=torch.long, device=self.device)
        market_max[:, 1, :_PRODUCTS] = shed[:, :_PRODUCTS]
        money = state[:, 9].long().clamp_min(0)
        seed_cost = (
            state[:, self.layout.seed_costs : self.layout.seed_costs + _CROPS].long().clamp_min(1)
        )
        market_max[:, 2, :_CROPS] = torch.minimum(
            money[:, None] // seed_cost,
            torch.full_like(seed_cost, self.contract.maximum_exact_quantity),
        )
        products = self._product_purchase_ids[None].expand(batch, -1)
        _, _, _, buy_cumulative = market_curves(state, products, _MAX_QUANTITY, self.layout)
        affordable = (buy_cumulative <= money[:, None, None]).sum(2)
        market_max[:, 3, 0] = torch.minimum(room, affordable[:, 0])
        market_max[:, 3, 8] = torch.minimum(room, affordable[:, 1])
        animal_cost = (
            state[:, self.layout.animal_costs : self.layout.animal_costs + _ANIMALS]
            .long()
            .clamp_min(1)
        )
        market_max[:, 4, 9:12] = torch.minimum(room[:, None], money[:, None] // animal_cost)
        market_item = market_max > 0
        market_qmode = torch.zeros((batch, 7, _ITEMS, 5), dtype=torch.bool, device=self.device)
        market_qmode[:, 1] = _quantity_modes(market_max[:, 1], sell=True)
        market_deficits = self._market_deficits(option_live)
        for order_id in (2, 3, 4):
            market_qmode[:, order_id] = _quantity_modes(
                market_max[:, order_id],
                deficit=market_deficits[:, order_id],
                affordable=True,
            )
        market_order = market_item.any(2)
        market_order[:, 0] = True
        hire_cost = state[:, 12].long() * fibonacci(state[:, 10].long()).long()
        market_order[:, 5] = (state[:, 1] < contract.unit_limit) & (money >= hire_cost)
        land_level = state[:, 11].long()
        land_cost = state.gather(
            1, (self.layout.land_costs + land_level.clamp(0, 2))[:, None]
        ).squeeze(1)
        market_order[:, 6] = (land_level < 3) & (money >= land_cost)
        in_market = phase_raw == 1
        market_order &= in_market[:, None]
        market_item &= in_market[:, None, None]
        market_qmode &= in_market[:, None, None, None]
        market_max *= in_market[:, None, None]

        inputs = ProgramDecisionInputs(
            context=prepared.context,
            tile_tokens=prepared.target_keys,
            root_features=root,
            option_features=option,
            target_reservations=reservations,
            phase=phase,
            unit_index=torch.where(unit_phase, unit, torch.full_like(unit, -1)),
            market_slot=torch.where(phase_raw == 1, market_slot, torch.full_like(market_slot, -1)),
            unit_count=unit_count,
            current_x=torch.where(unit_phase, x, torch.zeros_like(x)),
            current_y=torch.where(unit_phase, y, torch.zeros_like(y)),
            forced=forced.long(),
        )
        masks = NativeProgramMasks(
            control=control,
            direction=direction,
            task=task,
            task_argument=task_argument,
            task_target=task_target,
            task_quantity_mode=task_qmode,
            task_quantity_max=task_max,
            raw_operation=raw_operation,
            raw_argument=raw_argument,
            raw_quantity_mode=raw_qmode,
            raw_quantity_max=raw_max,
            market_order=market_order,
            market_item=market_item,
            market_quantity_mode=market_qmode,
            market_quantity_max=market_max,
        )
        return inputs, masks, active

    def _resolved_quantity(
        self, mode: Tensor, exact: Tensor, maximum: Tensor, deficit: Tensor | None = None
    ) -> Tensor:
        result = torch.ones_like(maximum)
        result = torch.where((mode == 1) | (mode == 3), maximum, result)
        if deficit is not None:
            planned = torch.minimum(deficit.clamp_min(1), maximum)
            result = torch.where(mode == 2, planned, result)
        return torch.where(mode == 4, exact, result).clamp_min(1)

    def apply(self, output: ProgramStepOutput, active: Tensor) -> None:
        """Compile sampled fields, apply the official shadow transition, and advance."""
        self.apply_selection(output.actions, output.masks.quantity_max, active)

    def apply_selection(
        self,
        actions: ProgramActions,
        selected_quantity_max: Tensor,
        active: Tensor,
    ) -> None:
        """Apply already sampled full-batch actions without a host round trip."""
        state = self.state
        phase = state[:, 4].long()
        unit_phase = active & (phase == 0)
        market_phase = active & (phase == 1)
        unit = state[:, 2].long().clamp(0, self.contract.unit_limit - 1)
        rows = _rows(self.batch, self.device)
        x, y = self._positions()
        tiles = self._tiles()
        inventory = self._inventory()
        shed = state[:, self.layout.shed : self.layout.shed + _ITEMS].long()
        forced = self._current(self.forced_target) >= 0
        assign = unit_phase & ~forced & (actions.control == 1)
        clear = (
            unit_phase
            & ~forced
            & ((actions.control == 2) | (actions.control == 3) | (actions.control == 4))
        )
        self.option_valid[rows, unit] = torch.where(clear, False, self.option_valid[rows, unit])
        self.option_valid[rows, unit] = torch.where(assign, True, self.option_valid[rows, unit])
        self.option_task[rows, unit] = torch.where(
            assign, actions.task, self.option_task[rows, unit]
        )
        self.option_target[rows, unit] = torch.where(
            assign, actions.target, self.option_target[rows, unit]
        )
        self.option_argument[rows, unit] = torch.where(
            assign, actions.argument, self.option_argument[rows, unit]
        )
        self.option_quantity_mode[rows, unit] = torch.where(
            assign, actions.quantity_mode, self.option_quantity_mode[rows, unit]
        )
        self.option_exact[rows, unit] = torch.where(
            assign, actions.exact_quantity, self.option_exact[rows, unit]
        )
        self.option_phase[rows, unit] = torch.where(assign, 0, self.option_phase[rows, unit])
        self.option_created_step[rows, unit] = torch.where(
            assign, self.step, self.option_created_step[rows, unit]
        )

        task = self._current(self.option_task)
        target = self._current(self.option_target)
        argument = self._current(self.option_argument)
        mode = self._current(self.option_quantity_mode)
        exact = self._current(self.option_exact)
        option_phase = self._current(self.option_phase)
        target_x = target.clamp_min(0) % self.contract.board_size
        target_y = target.clamp_min(0) // self.contract.board_size
        required_item = torch.where(
            task == 3, 8, torch.where(task == 7, 0, torch.where(task == 6, argument, -1))
        )
        safe_item = required_item.clamp(0, _ITEMS - 1)
        held = inventory.gather(1, safe_item[:, None]).squeeze(1)
        needs_fetch = (
            unit_phase
            & ~forced
            & self._current(self.option_valid)
            & (required_item >= 0)
            & (held <= 0)
        )
        half = self.contract.board_size // 2
        access_x = torch.where(x < half, half - 1, half)
        access_y = torch.where(y < half, half - 1, half)
        at_shed = (x == access_x) & (y == access_y)
        at_target = (x == target_x) & (y == target_y)
        logistics = (task == 10) | (task == 11) | (task == 14)
        approach_shed = (
            unit_phase
            & ~forced
            & self._current(self.option_valid)
            & needs_fetch
            & ~at_shed
        )
        approach_logistics = (
            unit_phase
            & ~forced
            & self._current(self.option_valid)
            & logistics
            & ~at_target
        )
        approach_target = (
            unit_phase
            & ~forced
            & self._current(self.option_valid)
            & ~needs_fetch
            & ~logistics
            & (task != 15)
            & ~at_target
        )

        move_x = torch.where(approach_shed, access_x, target_x)
        move_y = torch.where(approach_shed, access_y, target_y)
        move_token = torch.where(
            x < move_x,
            3,
            torch.where(x > move_x, 4, torch.where(y < move_y, 2, torch.where(y > move_y, 1, 0))),
        )
        token = torch.zeros(self.batch, dtype=torch.long, device=self.device)
        quantity = torch.zeros_like(token)
        token = torch.where(
            unit_phase & ~forced & (actions.control == 2), actions.direction + 1, token
        )
        raw_base = self._raw_tokens[actions.raw_operation.clamp(0, 12)]
        raw_token = torch.where(
            (actions.raw_operation == 0) | (actions.raw_operation == 2),
            raw_base + actions.argument,
            torch.where(actions.raw_operation == 3, raw_base + actions.argument, raw_base),
        )
        raw_max = selected_quantity_max.long().clamp_min(1)
        raw_quantity = self._resolved_quantity(
            actions.quantity_mode, actions.exact_quantity, raw_max
        )
        raw_branch = unit_phase & ~forced & (actions.control == 3)
        token = torch.where(raw_branch, raw_token, token)
        quantity = torch.where(
            raw_branch & ((actions.raw_operation == 0) | (actions.raw_operation == 2)),
            raw_quantity,
            quantity,
        )
        keep_or_assign = unit_phase & ~forced & ((actions.control == 0) | assign)
        token = torch.where(
            keep_or_assign & (approach_shed | approach_logistics | approach_target),
            move_token,
            token,
        )
        self.option_phase[rows, unit] = torch.where(
            needs_fetch & ~at_shed, 2, self.option_phase[rows, unit]
        )
        pickup_required = keep_or_assign & needs_fetch & at_shed
        token = torch.where(pickup_required, 5 + safe_item, token)
        quantity = torch.where(pickup_required, torch.ones_like(quantity), quantity)
        self.option_phase[rows, unit] = torch.where(
            pickup_required, 0, self.option_phase[rows, unit]
        )
        logistics_at_target = keep_or_assign & logistics & at_target
        logistics_max = torch.where(
            task == 10,
            shed.gather(1, argument.clamp(0, 11)[:, None]).squeeze(1),
            torch.minimum(
                inventory.gather(1, argument.clamp(0, 11)[:, None]).squeeze(1),
                (state[:, 5].long() - state[:, 8].long()).clamp_min(0),
            ),
        )
        live_units = self._unit_ids[None] < self.turn_unit_counts[:, None]
        planned_requirements = self._planned_requirements(self.option_valid & live_units)
        logistics_deficit = planned_requirements.gather(
            1, argument.clamp(0, _ITEMS - 1)[:, None]
        ).squeeze(1)
        logistics_quantity = self._resolved_quantity(mode, exact, logistics_max, logistics_deficit)
        token = torch.where(
            logistics_at_target,
            torch.where(
                task == 10,
                5 + argument,
                torch.where(task == 11, 18 + argument, 17),
            ),
            token,
        )
        quantity = torch.where(
            logistics_at_target & ((task == 10) | (task == 11)),
            logistics_quantity,
            quantity,
        )
        option_at_target = (
            keep_or_assign & ~logistics & ~needs_fetch & (task != 15) & at_target
        )
        safe_water = option_at_target & (task == 0) & (option_phase == 5)
        task_token = self._task_tokens[task.clamp(0, self.contract.task_count - 1)]
        task_token = torch.where(
            task == 0, torch.where(option_phase == 5, 35, 30 + argument), task_token
        )
        task_token = torch.where(task == 13, 30 + argument, task_token)
        task_token = torch.where(task == 5, torch.where(argument == _COOP, 39, 40), task_token)
        selected_tile_kind = tiles[rows, target.clamp(0, self.contract.tile_count - 1), 0]
        animal_structure = (argument - 9) != 0
        task_token = torch.where(
            (task == 6) & (selected_tile_kind == 0),
            torch.where(animal_structure, 40, 39),
            task_token,
        )
        task_token = torch.where((task == 6) & (selected_tile_kind != 0), 18 + argument, task_token)
        token = torch.where(option_at_target, task_token, token)
        quantity = torch.where(
            option_at_target & (task == 6) & (selected_tile_kind != 0), 1, quantity
        )

        last_hour = (self.step % self.turns_per_day) == self.turns_per_day - 1
        fresh_plant = option_at_target & (task == 0) & (option_phase != 5)
        all_positions = (
            state[:, self.layout.positions : self.layout.positions + self.contract.unit_limit * 2]
            .view(self.batch, self.contract.unit_limit, 2)
            .long()
        )
        later = self._unit_ids[None] > unit[:, None]
        later_at = (
            all_positions[:, :, 1] * self.contract.board_size + all_positions[:, :, 0]
        ) == target[:, None]
        waterer = (later & later_at & (self.forced_target < 0)).to(torch.int8).argmax(1).long()
        reserve_water = fresh_plant & last_hour
        self.forced_target[rows, waterer] = torch.where(
            reserve_water, target, self.forced_target[rows, waterer]
        )
        self.forced_owner[rows, waterer] = torch.where(
            reserve_water, unit, self.forced_owner[rows, waterer]
        )
        self.option_phase[rows, unit] = torch.where(fresh_plant, 5, self.option_phase[rows, unit])

        forced_target = self._current(self.forced_target)
        forced_owner = self._current(self.forced_owner).clamp(0, self.contract.unit_limit - 1)
        token = torch.where(unit_phase & forced, 35, token)
        self.option_valid[rows, forced_owner] = torch.where(
            unit_phase & forced, False, self.option_valid[rows, forced_owner]
        )
        self.forced_target[rows, unit] = torch.where(unit_phase & forced, -1, forced_target)
        self.forced_owner[rows, unit] = torch.where(
            unit_phase & forced, -1, self._current(self.forced_owner)
        )

        completed = (
            logistics_at_target
            | safe_water
            | (option_at_target & (task != 0) & (task != 6))
        )
        completed |= option_at_target & (task == 6) & (selected_tile_kind != 0)
        completed |= (
            approach_target
            & (task == 12)
            & (move_token != 0)
            & ((torch.abs(x - target_x) + torch.abs(y - target_y)) == 1)
        )
        self.option_valid[rows, unit] = torch.where(completed, False, self.option_valid[rows, unit])

        order = actions.market_order
        market_token = torch.full_like(token, 44)
        market_token = torch.where(order == 1, 46 + actions.argument, market_token)
        market_token = torch.where(order == 2, 55 + actions.argument, market_token)
        market_token = torch.where(
            order == 3, torch.where(actions.argument == 0, 60, 61), market_token
        )
        market_token = torch.where(order == 4, 53 + actions.argument, market_token)
        market_token = torch.where(order == 5, 65, market_token)
        market_token = torch.where(order == 6, 66, market_token)
        market_deficits = self._market_deficits(self.option_valid & live_units)
        market_deficit = market_deficits[
            rows,
            order.clamp(0, 6),
            actions.argument.clamp(0, _ITEMS - 1),
        ]
        market_quantity = self._resolved_quantity(
            actions.quantity_mode,
            actions.exact_quantity,
            selected_quantity_max.long().clamp_min(1),
            market_deficit,
        )
        token = torch.where(market_phase, market_token, token)
        quantity = torch.where(
            market_phase & (order >= 1) & (order <= 4), market_quantity, quantity
        )

        official_position = torch.where(
            unit_phase, unit, self.turn_unit_counts + state[:, 3].long()
        )
        write_official = active & (unit_phase | (market_phase & (order != 0)))
        self.tokens[rows, official_position.clamp(0, self.contract.maximum_decisions - 1)] = (
            torch.where(
                write_official,
                token,
                self.tokens[rows, official_position.clamp(0, self.contract.maximum_decisions - 1)],
            )
        )
        self.quantities[rows, official_position.clamp(0, self.contract.maximum_decisions - 1)] = (
            torch.where(
                write_official,
                quantity,
                self.quantities[
                    rows, official_position.clamp(0, self.contract.maximum_decisions - 1)
                ],
            )
        )
        prior_phase = phase.clone()
        from kagg_revue.policy.cuda.session import select_policy_actions

        select_policy_actions(state, token, quantity, self.policy_layout, active)
        project_market_selection(state, token, quantity, prior_phase, active, self.layout)
        self.trace_counts += active.to(torch.int16)

    def advance_prefix(
        self,
        prefix: ProgramPrefixState,
        output: ProgramStepOutput,
        active: Tensor,
    ) -> None:
        """Advance only live recurrent rows after one device decision."""
        prefix.hidden.copy_(torch.where(active[:, None], output.next_prefix.hidden, prefix.hidden))

    def output(self) -> ProgramGpuCompilerOutput:
        """Expose official actions without copying them to the host."""
        unit_counts = self.turn_unit_counts
        market_orders = self.state[:, 3].long()
        return ProgramGpuCompilerOutput(
            tokens=self.tokens,
            quantities=self.quantities,
            decision_counts=unit_counts + market_orders,
            unit_counts=unit_counts,
        )


__all__ = ["ProgramGpuCompiler", "ProgramGpuCompilerOutput"]
