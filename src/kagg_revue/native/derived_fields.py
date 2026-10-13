"""Ordered names for the complete v5b supplement, excluding the unchanged v4 prefix.

Counts use signed log1p(abs(x))/log(1025); cash uses signed
log1p(abs(x)/100)/log(1001). Time uses actionable season length except
board service/slack and unit work/drop fields, which use turns per day.
Prices and price changes use the product base price. Probabilities and
flags are untransformed. Missing or inapplicable fields are zero with
the accompanying applicability, private-known, or history-coverage flag.
"""

HORIZONS = ("1d", "2d", "4d", "8d", "12d", "remaining")
GLOBAL_FIELDS = (
    *(f"actual_horizon_{horizon}" for horizon in HORIZONS),
    "own_critical_work_lower_bound",
    "own_critical_work_pressure",
    "feed_purchase_quote_2d",
    "cash_after_feed_reserve",
    "own_visible_liquidation_quote",
    "tonight_overflow_liquidation_loss",
    "own_unreachable_critical_tiles",
    "opponent_critical_work_lower_bound",
    "next_land_available",
    "next_land_new_empty_cells",
    "reusable_empty_structures",
    "next_land_cost_per_cell",
    "next_land_cash_shortfall_after_feed",
    "next_land_first_service_delay",
    "new_tiles_today_operations_upper_bound",
    "next_hire_cost_per_remaining_turn",
    "new_hand_exclusive_critical_reach",
    "new_hand_turns_remaining_today",
)
BOARD_FIELDS = (
    *(
        f"{action}_{field}"
        for action in ("water", "feed", "care", "fertilize")
        for field in ("applicable", "terminal_yield_delta", "current_quote_delta")
    ),
    "service_delay",
    "deadline_slack",
    "harvest_sale_delay",
    "terminal_delivery_slack",
    "reachable_workers",
    "nearest_worker_partition_load",
    "feed_material_shortfall",
    "private_known",
)
UNIT_FIELDS = (
    *(
        f"reachable_{task}_tiles"
        for task in ("water", "feed", "care", "collect", "harvest", "plant")
    ),
    "partition_critical_tasks",
    "partition_operations_plus_radius",
    "bag_liquidation_quote",
    "bag_drop_delay",
    "terminal_delivery_slack",
    "tonight_overflow_contribution",
    "bag_feed_reachable_capacity",
    "bag_fertilizer_reachable_capacity",
    "private_known",
    "overlapping_critical_candidate_tiles",
)
PRODUCT_FIELDS = (
    *(
        f"{horizon}_{field}"
        for horizon in HORIZONS
        for field in (
            "known_shop_drain",
            "own_net_supply_maintained",
            "opponent_net_supply_maintained",
            "own_net_supply_boosted",
            "opponent_net_supply_boosted",
            "gap_maintained",
            "price_maintained",
            "price_boosted",
        )
    ),
    "new_asset_available",
    "new_asset_setup_delay",
    "new_asset_first_sale_terminal_slack",
    "new_asset_purchase_quote",
    "new_asset_relative_cash_maintained",
    "new_asset_feed_units",
    "new_asset_boost_fertilizer_units",
    "new_asset_service_operations",
    "new_asset_boost_extra_operations",
    "new_asset_own_cash_maintained",
    "new_asset_own_cash_boosted",
    "new_asset_breakeven_delay_maintained",
    "new_asset_breakeven_delay_boosted",
    "new_asset_breaks_even_maintained",
    "new_asset_breaks_even_boosted",
    "new_asset_relative_cash_boosted",
    "last_unlock_demand_delta",
    "turns_since_last_unlock",
    "future_drain_mean_8d",
    "future_drain_std_8d",
    "future_drain_mean_remaining",
    "future_drain_std_remaining",
    "unlock_before_first_new_sale",
    "new_shop_demands_product_probability",
    "shed_solo_liquidation_cash",
    "carried_marginal_liquidation_quote",
    "carried_first_sale_delay_lower_bound",
    "parallel_seed_shortfall",
    "tonight_overflow_units",
    "feed_reserve_2d",
    "stock_after_feed_reserve",
    "ready_harvest_operations",
    *(
        f"history_{window}_{field}"
        for window in ("2d", "4d")
        for field in (
            "own_harvest_estimate",
            "opponent_harvest_estimate",
            "players_inventory_effect",
            "price_change",
            "coverage",
            "floor_censor_possible",
            "harvest_ambiguity_possible",
            "producer_balance_change",
        )
    ),
)
