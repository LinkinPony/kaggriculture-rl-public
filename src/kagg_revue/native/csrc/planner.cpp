#include "planner.hpp"

#include <algorithm>

namespace kagg::planner {

NativePlanner::NativePlanner(Config config, PlannerOptions options)
    : config_(std::move(config)), options_(std::move(options)) {}

void NativePlanner::Reset() {
  commitments_.clear();
  rejected_market_states_.clear();
  last_step_ = -1;
  day_ = -1;
  player_ = -1;
  cash_reserve_anchor_ = 0.0;
}

PlanResult NativePlanner::Plan(const Farm& farm, const Farm& opponent_farm,
                               const PrivateState& priv,
                               const MarketState& market, int player,
                               int step) {
  const int day = step / std::max(1, config_.turns_per_day);
  const bool new_budget_window =
      last_step_ < 0 || step <= last_step_ || day_ != day || player_ != player;
  if ((last_step_ >= 0 && step <= last_step_) || (day_ >= 0 && day != day_) ||
      (player_ >= 0 && player != player_)) {
    commitments_.clear();
  }
  if (new_budget_window) cash_reserve_anchor_ = farm.money;
  if (last_step_ >= 0 && step <= last_step_) rejected_market_states_.clear();
  last_step_ = step;
  day_ = day;
  player_ = player;

  const PlannerStateView state{config_, farm, opponent_farm, priv, market,
                               player, step};
  PlanResult result;
  result.tasks = GenerateTasks(state, options_.strategy,
                               options_.project_layout,
                               options_.animal_zone_cells,
                               options_.crop_zone_cells,
                               options_.project_layout_start_day);
  result.schedule = Schedule(state, result.tasks, options_.scheduler,
                             options_.supply_route_capacity,
                             options_.supply_route_mode,
                             options_.task_continuation_mode,
                             options_.continuation_travel_value, &commitments_);

  UnitPhaseResult compiled_units =
      CompileUnitPhase(config_, farm, priv, result.schedule.requested, day);
  result.unit_trace = compiled_units.trace;
  result.action = compiled_units.actual;

  auto [market_orders, strategy_trace] = ChooseMarketOrders(
      state, compiled_units.farm, compiled_units.priv, options_.strategy,
      cash_reserve_anchor_, result.schedule.supply_reservations,
      &rejected_market_states_);
  result.strategy_trace = std::move(strategy_trace);

  std::array<Farm, 2> farms;
  farms[player] = compiled_units.farm;
  farms[1 - player] = opponent_farm;
  std::array<PrivateState, 2> privates;
  privates[player] = compiled_units.priv;
  std::array<PlayerAction, 2> actions;
  actions[player].market = std::move(market_orders);
  MarketState market_shadow = market;
  const std::array<Farm*, 2> farm_ptrs = {&farms[0], &farms[1]};
  const std::array<PrivateState*, 2> private_ptrs = {&privates[0], &privates[1]};
  std::vector<MarketSlotTrace> all_market_trace;
  ApplyMarketPhase(config_, farm_ptrs, private_ptrs, &market_shadow, actions[0],
                   actions[1], &all_market_trace);
  result.action.market.resize(actions[player].market.size());
  for (const MarketSlotTrace& trace : all_market_trace) {
    if (trace.player != player) continue;
    result.market_trace.push_back(trace);
    result.action.market[trace.slot_index] = trace.actual;
  }
  return result;
}

}  // namespace kagg::planner
