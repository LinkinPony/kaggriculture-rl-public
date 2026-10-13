"""Field names and units for the immutable production-context-v4 extension.

Board counts use /6, ages and event counts /30, and time offsets /episode turns.
Distances use Manhattan steps / (2 * board size); shed round trips use twice that.
Harvest quantities use log1p(x)/5. Missing event times are zero with an explicit
event flag. Product counts use /board area; inventories use log1p(x)/5. Price
ratios are unit price / base price clamped to 4 then /4; unit counts until a
price threshold and unit-turns use log1p(x)/7 (thresholds cap at 1024 units);
cumulative market flow uses symlog(x / T)/2 with the product's curve width T.
Labor pressure is due tiles per remaining unit-turn, clamped to 2 then /2, and
the travel estimate is log1p(sum of nearest-unit distances)/8. Forecasts assume daily
maintenance and earliest harvest, with available resources and labor, no newly
purchased fertilizer and no future CARE. They are conditional production
potential, not predictions of either player's decisions or proceeds.

Rule forecasts fill productive tiles only; geometry fills every unlocked tile on
both farms; resource reachability is own-farm only because it reads inventories.
The unit block lists both farms' present units in the official order; the ledger
fields accumulate visible yield drops and market inventory changes net of town
consumption, so they are public estimates rather than exact private totals.
"""

BOARD_FIELDS = (
    "harvestable",
    "harvestable_quantity",
    "age_days",
    "capacity_remaining",
    "next_production_turns",
    "remaining_production_events",
    "decay_start_turns",
    "has_decay_deadline",
    "watering_bonus_window",
    "water_immediate_yield_gain",
    "fertilize_then_water_extra_gain",
    "remaining_watering_bonus_days",
    "new_fertilizer_covered_events",
    "next_maintained_production",
    "next_production_overflow_without_harvest",
    "day_end_idle_yield_delta",
    "day_end_maintained_yield_delta",
    "day_end_idle_loss",
    "maintenance_prevents_day_end_loss",
    "feeding_preserves_banked_bonus",
    "new_care_payout_turns",
    "new_care_can_pay_before_end",
    "first_harvest_terminal_slack",
    "nearest_unit_distance",
    "units_within_two",
    "reachable_before_day_end",
    "shed_distance",
    "harvest_sellable_before_end",
    "feed_carrier_distance",
    "has_feed_carrier",
    "feed_via_shed_distance",
    "shed_has_wheat",
    "fertilizer_carrier_distance",
    "has_fertilizer_carrier",
    "fertilizer_via_shed_distance",
    "shed_has_fertilizer",
)

PRODUCT_FIELDS = (
    "own_immature_tiles",
    "own_harvestable_tiles",
    "own_exhausted_ongoing_tiles",
    "own_day_end_idle_loss_tiles",
    "own_needs_water",
    "own_needs_feed",
    "own_useful_care_available",
    "own_fertilizer_collectable",
    "own_harvestable_quantity",
    "own_remaining_production_events",
    "own_additional_harvest_1_day",
    "own_additional_harvest_2_days",
    "own_additional_harvest_4_days",
    "own_next_production_overflow",
    "opponent_immature_tiles",
    "opponent_harvestable_tiles",
    "opponent_exhausted_ongoing_tiles",
    "opponent_harvestable_quantity",
    "opponent_additional_harvest_1_day",
    "opponent_additional_harvest_2_days",
    "opponent_additional_harvest_4_days",
    "unplanted_seeds_or_stored_animals",
    "carried_animals",
    "empty_compatible_tiles",
    "town_consumption_per_day",
    "next_town_consumption_turns",
    "has_town_consumption_before_end",
    "own_available_tasks",
    "new_placement_first_harvest_terminal_slack",
    "new_placement_total_yield",
    "new_placement_total_yield_boosted",
    "sell_average_price_2",
    "sell_average_price_4",
    "sell_average_price_8",
    "sell_average_price_16",
    "sell_average_price_32",
    "sell_average_price_64",
    "sell_average_price_all_stock",
    "units_until_price_below_75pct",
    "units_until_price_below_50pct",
    "units_until_price_floor",
    "price_after_visible_supply",
    "market_glutted",
    "glut_recovery_days",
    "buy_average_price_10",
    "buy_average_price_50",
    "own_harvested_cumulative",
    "opponent_harvested_cumulative",
    "players_net_market_flow_cumulative",
)

GLOBAL_FIELDS = (
    "farm_feed_due_today",
    "farm_wheat_total",
    "farm_wheat_stored",
    "farm_wheat_carried",
    "farm_feed_shortfall",
    "farm_fertilizer_stored",
    "farm_fertilizer_carried",
    "turns_left_today",
    "final_day",
    "shed_room",
    "carried_total",
    "shed_overflow_tonight",
    "own_due_task_tiles",
    "own_dying_tonight_tiles",
    "own_unit_turns_left",
    "own_task_pressure",
    "own_travel_estimate",
    "opponent_due_task_tiles",
    "opponent_dying_tonight_tiles",
    "opponent_unit_turns_left",
    "opponent_task_pressure",
    "opponent_travel_estimate",
)

UNIT_FIELDS = (
    "nearest_needs_water",
    "nearest_needs_feed",
    "nearest_needs_care",
    "nearest_fertilizer_collectable",
    "nearest_harvestable",
    "nearest_plantable",
    "has_needs_water",
    "has_needs_feed",
    "has_needs_care",
    "has_fertilizer_collectable",
    "has_harvestable",
    "has_plantable",
    "due_tiles_north",
    "due_tiles_south",
    "due_tiles_east",
    "due_tiles_west",
)
