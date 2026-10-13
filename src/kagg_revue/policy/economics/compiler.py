"""Actor-safe economic state, candidate, and per-quantity feature compiler."""

from __future__ import annotations

import math

import torch
from torch import Tensor

from kagg_revue.policy.economics.layout import (
    ACTION_TOKENS,
    CANDIDATE_FEATURES,
    MARKET_PROJECTION_CONDITIONAL,
    MAXIMUM_QUANTITY,
    PREFIX_FEATURES,
    QUANTITY_FEATURES,
    TURN_FEATURES,
    EconomicStateLayout,
)
from kagg_revue.policy.economics.pricing import (
    fibonacci,
    market_curves,
    market_price,
    signed_log,
)
from kagg_revue.policy.economics.transition import apply_selection
from kagg_revue.policy.vocabulary import (
    CURRENT_ACTIONS,
    action_vocabulary,
)


def _rows(state: Tensor) -> Tensor:
    return torch.arange(state.shape[0], device=state.device)


def _gather(state: Tensor, index: Tensor) -> Tensor:
    return state[_rows(state), index.long()]


def _cumulative_at(curve: Tensor, count: Tensor) -> Tensor:
    index = (count.long() - 1).clamp(0, curve.shape[-1] - 1)
    selected = curve.gather(-1, index)
    return torch.where(count > 0, selected, torch.zeros_like(selected))


class EconomicFeatureCompiler:
    """Compile only causal, deployment-visible deterministic rule features."""

    def __init__(self, layout: EconomicStateLayout, action_tokens: int = ACTION_TOKENS) -> None:
        """Bind one authenticated native economic-state layout."""
        self.layout = layout
        self.vocabulary = action_vocabulary(action_tokens)

    def validate_state(self, state: Tensor) -> None:
        """Reject a tensor that differs from the checkpoint-bound state ABI."""
        if state.dtype not in {torch.int32, torch.int64}:
            raise ValueError("economic state must use int32 or int64")
        if state.ndim != 2 or state.shape[1] != self.layout.width:
            raise ValueError("economic state has the wrong compact layout")

    def turn_features(self, state: Tensor, global_features: Tensor) -> Tensor:
        """Describe the full decision-preceding economy for actor and critic."""
        self.validate_state(state)
        if global_features.shape != (state.shape[0], 82):
            raise ValueError("economic state and global observation differ")
        if state.device.type == "cuda":
            if self.vocabulary != CURRENT_ACTIONS:
                return self.turn_features(
                    state.cpu(), global_features.cpu()
                ).to(state.device)
            from kagg_revue.policy.economics.gpu import turn_features

            return turn_features(state, global_features, self.layout)
        capacity = state[:, 5].float().clamp_min(1.0)
        shed_total = state[:, 8].float()
        land_level = state[:, 11].long()
        rows = _rows(state)
        next_land = state[
            rows,
            self.layout.land_costs + land_level.clamp(0, 2),
        ].float()
        next_land = torch.where(land_level < 3, next_land, torch.zeros_like(next_land))
        next_hire = state[:, 12].float() * fibonacci(state[:, 10])
        values = [
            torch.ones_like(shed_total),
            global_features[:, 2].float(),
            global_features[:, 3].float(),
            global_features[:, 4].float(),
            signed_log(state[:, 9]),
            global_features[:, 8].float(),
            global_features[:, 9].float(),
            (shed_total / capacity).clamp(0.0, 2.0),
            ((capacity - shed_total).clamp_min(0.0) / capacity).clamp(0.0, 1.0),
        ]
        values.extend(
            signed_log(state[:, self.layout.shed + item]) for item in range(12)
        )
        values.extend(
            signed_log(state[:, self.layout.seeds + crop]) for crop in range(5)
        )
        values.extend(
            signed_log(state[:, self.layout.market_inventory + product])
            for product in range(9)
        )
        values.extend(
            signed_log(state[:, self.layout.market_prices + product])
            for product in range(9)
        )
        values.extend(
            (
                (state[:, 1].float() / 16.0).clamp(0.0, 2.0),
                signed_log(state[:, 10]),
                (state[:, 11].float() / 3.0).clamp(0.0, 1.0),
                signed_log(next_hire),
                signed_log(next_land),
                (state[:, 6].float() / 10.0).clamp(0.0, 2.0),
            )
        )
        result = torch.stack(values, dim=-1)
        if result.shape[-1] != TURN_FEATURES:
            raise RuntimeError("economic turn feature width drifted")
        return result

    def prefix_features(self, state: Tensor, phases: Tensor) -> Tensor:
        """Describe exact own state after the already selected turn prefix."""
        self.validate_state(state)
        if state.device.type == "cuda":
            if self.vocabulary != CURRENT_ACTIONS:
                return self.prefix_features(state.cpu(), phases.cpu()).to(state.device)
            from kagg_revue.policy.economics.gpu import prefix_features

            return prefix_features(state, phases, self.layout)
        phase_unit = phases == 0
        phase_market = phases == 1
        capacity = state[:, 5].float().clamp_min(1.0)
        shed_total = state[:, 8].float()
        unit_count = state[:, 1].float().clamp_min(1.0)
        values = [
            torch.ones_like(shed_total),
            phase_unit.float(),
            phase_market.float(),
            (state[:, 2].float() / unit_count).clamp(0.0, 1.0),
            ((unit_count - state[:, 2].float()).clamp_min(0.0) / unit_count).clamp(0.0, 1.0),
            (state[:, 3].float() / state[:, 6].float().clamp_min(1.0)).clamp(0.0, 1.0),
            (
                (state[:, 6].float() - state[:, 3].float()).clamp_min(0.0)
                / state[:, 6].float().clamp_min(1.0)
            ).clamp(0.0, 1.0),
            signed_log(state[:, 9]),
            (shed_total / capacity).clamp(0.0, 2.0),
            ((capacity - shed_total).clamp_min(0.0) / capacity).clamp(0.0, 1.0),
        ]
        values.extend(
            signed_log(state[:, self.layout.shed + item]) for item in range(12)
        )
        values.extend(
            signed_log(state[:, self.layout.seeds + crop]) for crop in range(5)
        )
        conditional = state[:, MARKET_PROJECTION_CONDITIONAL] != 0
        values.extend(
            (
                (
                    (state[:, 2] + state[:, 3]).float()
                    / 26.0
                ).clamp(0.0, 1.0),
                (~conditional).float(),
                conditional.float(),
            )
        )
        result = torch.stack(values, dim=-1)
        if result.shape[-1] != PREFIX_FEATURES:
            raise RuntimeError("economic prefix feature width drifted")
        return result

    def sequence_prefix_features(
        self,
        initial_state: Tensor,
        actions: Tensor,
        quantities: Tensor,
        phases: Tensor,
        decision_mask: Tensor,
    ) -> Tensor:
        """Replay stored choices and return facts before every decision."""
        if initial_state.device.type == "cuda" and self.vocabulary != CURRENT_ACTIONS:
            return self.sequence_prefix_features(
                initial_state.cpu(),
                actions.cpu(),
                quantities.cpu(),
                phases.cpu(),
                decision_mask.cpu(),
            ).to(initial_state.device)
        state = initial_state.clone()
        features = []
        for position in range(actions.shape[1]):
            features.append(self.prefix_features(state, phases[:, position]))
            apply_selection(
                state,
                actions[:, position].clamp_min(0),
                quantities[:, position],
                decision_mask[:, position],
                self.layout,
                self.vocabulary,
            )
        return torch.stack(features, dim=1)

    def _unit_quantity_maximum(
        self, state: Tensor, tokens: Tensor
    ) -> tuple[Tensor, Tensor, Tensor]:
        unit_index = state[:, 2].long().clamp(0, self.layout.unit_limit - 1)
        vocabulary = self.vocabulary
        item = torch.where(
            tokens < vocabulary.drop,
            (tokens - vocabulary.pickup_first) // vocabulary.pickup_stride,
            (tokens - vocabulary.place_first) // vocabulary.place_stride,
        ).clamp(0, 11)
        rows = _rows(state)
        shed = state[rows, self.layout.shed + item].long().clamp_min(0)
        carried = state[
            rows,
            self.layout.inventories + unit_index * 12 + item,
        ].long().clamp_min(0)
        pickup = (tokens >= vocabulary.pickup_first) & (
            tokens < vocabulary.pickup_stop
        )
        place = (tokens >= vocabulary.place_first) & (
            tokens < vocabulary.place_stop
        )
        free = (state[:, 5] - state[:, 8]).long().clamp_min(0)
        x = state[rows, self.layout.positions + unit_index * 2].long()
        y = state[rows, self.layout.positions + unit_index * 2 + 1].long()
        half = self.layout.board_size // 2
        adjacent = ((x == half - 1) | (x == half)) & (
            (y == half - 1) | (y == half)
        )
        tile = self.layout.tiles + (y * self.layout.board_size + x) * self.layout.tile_fields
        animal = item >= 9
        expected = (item != 9).to(state.dtype)
        animal_place = (
            place
            & animal
            & (_gather(state, tile) == 4)
            & (_gather(state, tile + 7) == 0)
            & (_gather(state, tile + 6) == expected)
        )
        place_max = torch.where(
            animal_place,
            torch.minimum(carried, torch.ones_like(carried)),
            torch.where(
                adjacent,
                torch.minimum(carried, free),
                torch.zeros_like(carried),
            ),
        )
        pickup_max = torch.where(adjacent, shed, torch.zeros_like(shed))
        maximum = torch.where(
            pickup,
            pickup_max,
            torch.where(place, place_max, torch.zeros_like(shed)),
        )
        return maximum.clamp(0, MAXIMUM_QUANTITY), item, animal_place

    def quantity_features(self, state: Tensor, selected_actions: Tensor) -> Tensor:
        """Return one consequence vector for every deployable quantity tier."""
        self.validate_state(state)
        if state.device.type == "cuda":
            if self.vocabulary != CURRENT_ACTIONS:
                return self.quantity_features(
                    state.cpu(), selected_actions.cpu()
                ).to(state.device)
            from kagg_revue.policy.economics.gpu import quantity_features

            return quantity_features(state, selected_actions, self.layout)
        vocabulary = self.vocabulary
        tokens = selected_actions.long().clamp(0, vocabulary.action_tokens - 1)
        rows = _rows(state)
        q = torch.arange(
            1,
            MAXIMUM_QUANTITY + 1,
            dtype=torch.long,
            device=state.device,
        )[None].expand(state.shape[0], -1)
        money = state[:, 9].float().clamp_min(0.0)
        free = (state[:, 5] - state[:, 8]).long().clamp_min(0)
        is_sell = (tokens >= vocabulary.sell_first) & (
            tokens < vocabulary.sell_first + 9
        )
        is_seed = (tokens >= vocabulary.seed_first) & (
            tokens < vocabulary.seed_first + 5
        )
        is_product = (tokens >= vocabulary.product_first) & (
            tokens < vocabulary.product_first + 2
        )
        is_animal = (tokens >= vocabulary.animal_first) & (
            tokens < vocabulary.animal_first + 3
        )
        is_market_quantity = is_sell | is_seed | is_product | is_animal
        is_unit_quantity = (
            (
                (tokens >= vocabulary.pickup_first)
                & (tokens < vocabulary.pickup_stop)
                & (
                    (tokens - vocabulary.pickup_first) % vocabulary.pickup_stride
                    == vocabulary.pickup_stride - 1
                )
            )
            | (
                (tokens >= vocabulary.place_first)
                & (tokens < vocabulary.place_stop)
                & (
                    (tokens - vocabulary.place_first) % vocabulary.place_stride
                    == vocabulary.place_stride - 1
                )
            )
        )
        product = torch.where(
            tokens == vocabulary.product_first + 1,
            torch.full_like(tokens, 8),
            tokens - vocabulary.product_first,
        )
        relevant = torch.where(
            is_sell,
            tokens - vocabulary.sell_first,
            torch.where(
                is_seed,
                tokens - vocabulary.seed_first,
                torch.where(
                    is_product,
                    product,
                    torch.where(
                        is_animal,
                        tokens - vocabulary.animal_first + 9,
                        torch.zeros_like(tokens),
                    ),
                ),
            ),
        ).clamp(0, 11)
        curve_product = torch.where(is_sell, relevant, product).clamp(0, 8)
        sell_price, sell_cumulative, buy_price, buy_cumulative = market_curves(
            state,
            curve_product,
            MAXIMUM_QUANTITY,
            self.layout,
        )
        shed = state[rows, self.layout.shed + relevant].long().clamp_min(0)
        seed_cost = state[
            rows,
            self.layout.seed_costs + (tokens - vocabulary.seed_first).clamp(0, 4),
        ].float()
        animal_cost = state[
            rows,
            self.layout.animal_costs
            + (tokens - vocabulary.animal_first).clamp(0, 2),
        ].float()
        affordable_product = (buy_cumulative <= money[:, None]).sum(dim=-1).long()
        market_maximum = torch.where(
            is_sell,
            shed,
            torch.where(
                is_seed,
                torch.floor(money / seed_cost.clamp_min(1.0)).long(),
                torch.where(
                    is_product,
                    torch.minimum(free, affordable_product),
                    torch.minimum(
                        free,
                        torch.floor(money / animal_cost.clamp_min(1.0)).long(),
                    ),
                ),
            ),
        )
        unit_maximum, unit_item, unit_animal_place = self._unit_quantity_maximum(
            state, tokens
        )
        maximum = torch.where(is_market_quantity, market_maximum, unit_maximum).clamp(
            0, MAXIMUM_QUANTITY
        )
        committed = torch.minimum(q, maximum[:, None])
        sell_cash = _cumulative_at(sell_cumulative, committed)
        buy_cash = _cumulative_at(buy_cumulative, committed)
        fixed_cost = torch.where(is_seed, seed_cost, animal_cost)
        cash_delta = torch.where(
            is_sell[:, None],
            sell_cash,
            torch.where(
                is_product[:, None],
                -buy_cash,
                torch.where(
                    (is_seed | is_animal)[:, None],
                    -fixed_cost[:, None] * committed.float(),
                    torch.zeros_like(sell_cash),
                ),
            ),
        )
        pickup = (tokens >= vocabulary.pickup_first) & (
            tokens < vocabulary.pickup_stop
        )
        place = (tokens >= vocabulary.place_first) & (
            tokens < vocabulary.place_stop
        )
        unit_place_to_shed = place & ~unit_animal_place
        shed_delta = torch.where(
            is_sell[:, None] | pickup[:, None],
            -committed,
            torch.where(
                is_product[:, None]
                | is_animal[:, None]
                | unit_place_to_shed[:, None],
                committed,
                torch.zeros_like(committed),
            ),
        )
        relevant = torch.where(is_unit_quantity, unit_item, relevant)
        relevant_before = torch.where(
            is_seed,
            state[rows, self.layout.seeds + relevant.clamp(0, 4)],
            state[rows, self.layout.shed + relevant],
        ).long().clamp_min(0)
        relevant_after = relevant_before[:, None] + shed_delta
        relevant_after = torch.where(
            is_seed[:, None],
            relevant_before[:, None] + committed,
            relevant_after,
        )
        shed_after = state[:, 8].long()[:, None] + shed_delta
        sell_market_delta = _cumulative_at(
            (sell_price > 1.0).long().cumsum(dim=-1),
            committed,
        ).long()
        market_delta = torch.where(
            is_sell[:, None],
            sell_market_delta,
            torch.where(is_product[:, None], -committed, torch.zeros_like(committed)),
        )
        marginal = torch.where(
            is_sell[:, None],
            sell_price,
            torch.where(
                is_product[:, None],
                buy_price,
                torch.where(
                    (is_seed | is_animal)[:, None],
                    fixed_cost[:, None].expand_as(sell_price),
                    torch.zeros_like(sell_price),
                ),
            ),
        )
        present = is_market_quantity | is_unit_quantity
        conditional = (
            (state[:, MARKET_PROJECTION_CONDITIONAL] != 0) | is_sell | is_product
        )
        result = torch.stack(
            (
                present[:, None].float().expand_as(sell_price),
                torch.log1p(q.float()) / math.log(129.0),
                signed_log(committed),
                (committed == q).float(),
                (committed > 0).float(),
                conditional[:, None].float().expand_as(sell_price),
                signed_log(cash_delta),
                signed_log(money[:, None] + cash_delta),
                signed_log(relevant_after),
                (
                    (state[:, 5].long()[:, None] - shed_after).clamp_min(0).float()
                    / state[:, 5].float().clamp_min(1.0)[:, None]
                ).clamp(0.0, 1.0),
                signed_log(market_delta),
                signed_log(marginal),
            ),
            dim=-1,
        )
        if result.shape[-1] != QUANTITY_FEATURES:
            raise RuntimeError("economic quantity feature width drifted")
        return result

    def candidate_features(self, state: Tensor, phases: Tensor) -> Tensor:
        """Describe immediate consequences for every action identity."""
        self.validate_state(state)
        if state.device.type == "cuda":
            if self.vocabulary != CURRENT_ACTIONS:
                return self.candidate_features(state.cpu(), phases.cpu()).to(state.device)
            from kagg_revue.policy.economics.gpu import candidate_features

            return candidate_features(state, phases, self.layout)
        batch = state.shape[0]
        device = state.device
        vocabulary = self.vocabulary
        action_tokens = vocabulary.action_tokens
        unit_tokens = vocabulary.unit_tokens
        tokens = torch.arange(action_tokens, device=device)
        unit_phase = phases == 0
        market_phase = phases == 1
        phase_valid = torch.where(
            unit_phase[:, None],
            tokens[None] < unit_tokens,
            market_phase[:, None] & (tokens[None] >= unit_tokens),
        )
        maximum = torch.zeros((batch, action_tokens), device=device, dtype=torch.long)
        cash_delta = torch.zeros_like(maximum, dtype=torch.float32)
        shed_delta = torch.zeros_like(maximum)
        relevant_after = torch.zeros_like(maximum)
        market_delta = torch.zeros_like(maximum)
        price = torch.zeros_like(maximum, dtype=torch.float32)
        next_price = torch.zeros_like(price)
        inherited_conditional = state[:, MARKET_PROJECTION_CONDITIONAL] != 0
        conditional = inherited_conditional[:, None].expand(-1, action_tokens).clone()
        maximum[:, :unit_tokens] = 1

        rows = _rows(state)
        free = (state[:, 5] - state[:, 8]).long().clamp_min(0)
        items = torch.arange(12, device=device)
        pickup_tokens = (
            vocabulary.pickup_first
            + vocabulary.pickup_stride * items
            + vocabulary.pickup_stride
            - 1
        )
        place_tokens = (
            vocabulary.place_first
            + vocabulary.place_stride * items
            + vocabulary.place_stride
            - 1
        )
        shed = state[:, self.layout.shed : self.layout.shed + 12].long().clamp_min(0)
        unit_index = state[:, 2].long().clamp(0, self.layout.unit_limit - 1)
        inventory_indices = (
            self.layout.inventories + unit_index[:, None] * 12 + items[None]
        )
        carried = state.gather(1, inventory_indices).long().clamp_min(0)
        x = state[
            rows,
            self.layout.positions + unit_index * 2,
        ].long()
        y = state[
            rows,
            self.layout.positions + unit_index * 2 + 1,
        ].long()
        half = self.layout.board_size // 2
        adjacent = ((x == half - 1) | (x == half)) & (
            (y == half - 1) | (y == half)
        )
        tile = self.layout.tiles + (
            y * self.layout.board_size + x
        ) * self.layout.tile_fields
        tile_kind = _gather(state, tile)
        tile_structure = _gather(state, tile + 6)
        tile_animal = _gather(state, tile + 7)
        expected_structure = items != 9
        animal_place = (
            (items[None] >= 9)
            & (tile_kind[:, None] == 4)
            & (tile_animal[:, None] == 0)
            & (tile_structure[:, None] == expected_structure[None])
        )
        place_maximum = torch.where(
            animal_place,
            torch.minimum(carried, torch.ones_like(carried)),
            torch.where(
                adjacent[:, None],
                torch.minimum(carried, free[:, None]),
                torch.zeros_like(carried),
            ),
        ).clamp(0, MAXIMUM_QUANTITY)
        maximum[:, pickup_tokens] = shed.clamp(0, MAXIMUM_QUANTITY)
        maximum[:, place_tokens] = place_maximum
        pickup_one = maximum[:, pickup_tokens] > 0
        placed_in_shed = (place_maximum > 0) & ~animal_place
        relevant_after[:, pickup_tokens] = shed - pickup_one.long()
        relevant_after[:, place_tokens] = shed + placed_in_shed.long()
        shed_delta[:, pickup_tokens] = -pickup_one.long()
        shed_delta[:, place_tokens] = placed_in_shed.long()

        money = state[:, 9].float().clamp_min(0.0)
        products = torch.arange(9, device=device)[None].expand(batch, -1)
        product_inventory = state[
            :, self.layout.market_inventory : self.layout.market_inventory + 9
        ].float()
        sell_price = market_price(
            state,
            products,
            product_inventory,
            self.layout,
        )
        sell_next_price = market_price(
            state,
            products,
            product_inventory + (sell_price > 1.0).float(),
            self.layout,
        )
        sell_count = shed[:, :9]
        sell_one = sell_count > 0
        sell_slice = slice(vocabulary.sell_first, vocabulary.sell_first + 9)
        maximum[:, sell_slice] = sell_count.clamp(0, MAXIMUM_QUANTITY)
        price[:, sell_slice] = sell_price
        next_price[:, sell_slice] = sell_next_price
        cash_delta[:, sell_slice] = torch.where(sell_one, sell_price, 0.0)
        shed_delta[:, sell_slice] = -sell_one.long()
        relevant_after[:, sell_slice] = (sell_count - sell_one.long()).clamp_min(0)
        market_delta[:, sell_slice] = (sell_one & (sell_price > 1.0)).long()
        conditional[:, sell_slice] = True

        seed_costs = state[
            :, self.layout.seed_costs : self.layout.seed_costs + 5
        ].float().clamp_min(1.0)
        seed_maximum = torch.floor(money[:, None] / seed_costs).long().clamp(
            0, MAXIMUM_QUANTITY
        )
        seed_one = seed_maximum > 0
        seed_slice = slice(vocabulary.seed_first, vocabulary.seed_first + 5)
        maximum[:, seed_slice] = seed_maximum
        price[:, seed_slice] = seed_costs
        next_price[:, seed_slice] = seed_costs
        cash_delta[:, seed_slice] = torch.where(seed_one, -seed_costs, 0.0)
        relevant_after[:, seed_slice] = state[
            :, self.layout.seeds : self.layout.seeds + 5
        ].long() + seed_one.long()

        buy_products = (torch.arange(2, device=device) * 8)[None].expand(batch, -1)
        _, _, buy_prices, buy_cumulative = market_curves(
            state,
            buy_products,
            MAXIMUM_QUANTITY,
            self.layout,
        )
        affordable = (buy_cumulative <= money[:, None, None]).sum(dim=-1).long()
        buy_maximum = torch.minimum(free[:, None], affordable).clamp(
            0, MAXIMUM_QUANTITY
        )
        buy_one = buy_maximum > 0
        product_slice = slice(vocabulary.product_first, vocabulary.product_first + 2)
        maximum[:, product_slice] = buy_maximum
        price[:, product_slice] = buy_prices[..., 0]
        next_price[:, product_slice] = buy_prices[..., 1]
        cash_delta[:, product_slice] = torch.where(buy_one, -buy_prices[..., 0], 0.0)
        shed_delta[:, product_slice] = buy_one.long()
        relevant_after[:, product_slice] = state.gather(
            1,
            self.layout.shed + buy_products,
        ).long() + buy_one.long()
        market_delta[:, product_slice] = -buy_one.long()
        conditional[:, product_slice] = True

        animal_costs = state[
            :, self.layout.animal_costs : self.layout.animal_costs + 3
        ].float().clamp_min(1.0)
        animal_maximum = torch.minimum(
            free[:, None],
            torch.floor(money[:, None] / animal_costs).long(),
        ).clamp(0, MAXIMUM_QUANTITY)
        animal_one = animal_maximum > 0
        animal_slice = slice(vocabulary.animal_first, vocabulary.animal_first + 3)
        maximum[:, animal_slice] = animal_maximum
        price[:, animal_slice] = animal_costs
        next_price[:, animal_slice] = animal_costs
        cash_delta[:, animal_slice] = torch.where(animal_one, -animal_costs, 0.0)
        shed_delta[:, animal_slice] = animal_one.long()
        relevant_after[:, animal_slice] = shed[:, 9:12] + animal_one.long()
        hire_cost = state[:, 12].float() * fibonacci(state[:, 10])
        next_hire_cost = state[:, 12].float() * fibonacci(state[:, 10] + 1)
        maximum[:, vocabulary.hire] = (
            (money >= hire_cost) & (state[:, 1] < self.layout.unit_limit)
        ).long()
        price[:, vocabulary.hire] = hire_cost
        next_price[:, vocabulary.hire] = next_hire_cost
        cash_delta[:, vocabulary.hire] = torch.where(
            maximum[:, vocabulary.hire] > 0, -hire_cost, 0.0
        )
        land_level = state[:, 11].long()
        land_cost = state[
            rows,
            self.layout.land_costs + land_level.clamp(0, 2),
        ].float()
        maximum[:, vocabulary.buy_land] = (
            (land_level < 3) & (money >= land_cost)
        ).long()
        price[:, vocabulary.buy_land] = torch.where(land_level < 3, land_cost, 0.0)
        next_land_level = land_level + 1
        next_land_cost = state[
            rows,
            self.layout.land_costs + next_land_level.clamp(0, 2),
        ].float()
        next_price[:, vocabulary.buy_land] = torch.where(
            next_land_level < 3,
            next_land_cost,
            0.0,
        )
        cash_delta[:, vocabulary.buy_land] = torch.where(
            maximum[:, vocabulary.buy_land] > 0, -land_cost, 0.0
        )
        maximum[:, vocabulary.market_stop : vocabulary.market_skip + 1] = 1

        quantity_dependent = torch.zeros(action_tokens, dtype=torch.bool, device=device)
        quantity_dependent[pickup_tokens] = True
        quantity_dependent[place_tokens] = True
        quantity_dependent[
            vocabulary.sell_first : vocabulary.animal_first + 3
        ] = True
        one_committed = maximum > 0
        executable = phase_valid & one_committed
        present = phase_valid
        resulting_free = (
            state[:, 5].long()[:, None] - state[:, 8].long()[:, None] - shed_delta
        ).clamp_min(0).float() / state[:, 5].float().clamp_min(1.0)[:, None]
        facts = torch.stack(
            (
                present.float(),
                phase_valid.float(),
                executable.float(),
                (~conditional).float(),
                conditional.float(),
                quantity_dependent[None].float().expand(batch, -1),
                signed_log(maximum),
                one_committed.float(),
                signed_log(cash_delta),
                signed_log(money[:, None] + cash_delta),
                signed_log(shed_delta),
                signed_log(relevant_after),
                signed_log(market_delta),
                signed_log(price),
                signed_log(next_price),
                resulting_free.clamp(0.0, 1.0),
                ((tokens == vocabulary.hire)[None] & one_committed).float(),
                ((tokens == vocabulary.buy_land)[None] & one_committed).float() * 0.25,
                (tokens[None] < unit_tokens).float().expand(batch, -1),
                (tokens[None] >= unit_tokens).float().expand(batch, -1),
            ),
            dim=-1,
        )
        if facts.shape[-1] != CANDIDATE_FEATURES:
            raise RuntimeError("economic candidate feature width drifted")
        return facts


__all__ = ["EconomicFeatureCompiler"]
