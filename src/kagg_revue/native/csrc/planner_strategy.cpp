#include "planner.hpp"

#include <algorithm>
#include <iomanip>
#include <numeric>
#include <sstream>
#include <string>
#include <tuple>

namespace kagg::planner {
namespace {

struct CandidateOrder {
  MarketOrder order;
  StrategyTrace trace;
  int priority = 0;
  int original_index = 0;
};

int64_t Carried(const PrivateState& priv, int item_index) {
  int64_t result = 0;
  for (const Inventory& inventory : priv.inventories) {
    result += inventory.Get(item_index);
  }
  return result;
}

std::string OrderKey(const MarketOrder& order) {
  return std::to_string(static_cast<int>(order.kind)) + ":" +
         std::to_string(order.item);
}

int64_t BaseFloorSellable(const PlannerStateView& state, int product,
                          int64_t available) {
  int64_t result = 0;
  const double base = state.config.market_params[product].base;
  while (result < available &&
         static_cast<double>(ComputeMarketPrice(
             state.config, product, state.market.inventory[product] + result)) >=
             base) {
    ++result;
  }
  return result;
}

std::string RetryState(const MarketOrder& order, const Farm& farm,
                       const PrivateState& priv, const MarketState& market) {
  const int state_item = order.kind == OrderKind::kBuyAnimal
                             ? item::kGoose + order.item
                             : order.item;
  std::ostringstream out;
  out << std::setprecision(17) << farm.money << ':' << farm.hands.size() << ':'
      << farm.hires_today << ':' << farm.extra_unlocked << ':' << order.remaining;
  if (state_item >= 0 && state_item < kNumItems) {
    out << ':' << priv.shed[state_item] << ':' << Carried(priv, state_item);
  }
  if (order.item >= 0 && order.item < kNumProducts) {
    out << ':' << market.prices[order.item] << ':'
        << market.inventory[order.item];
  }
  if (order.kind == OrderKind::kBuySeed && order.item >= 0 &&
      order.item < kNumCrops) {
    out << ':' << priv.seeds[order.item];
  }
  return out.str();
}

void AddCandidate(std::vector<CandidateOrder>* candidates, MarketOrder order,
                  std::string kind, int priority, std::string action = "") {
  StrategyTrace trace;
  trace.kind = std::move(kind);
  trace.item = order.item;
  trace.count = order.remaining;
  trace.action = std::move(action);
  switch (order.kind) {
    case OrderKind::kBuyAnimal:
      trace.operation = "BUY_ANIMAL";
      break;
    case OrderKind::kBuyProduct:
      trace.operation = "BUY_PRODUCT";
      break;
    case OrderKind::kBuySeed:
      trace.operation = "BUY_SEED";
      break;
    case OrderKind::kSell:
      trace.operation = "SELL";
      break;
    case OrderKind::kHire:
      trace.operation = "HIRE";
      break;
    case OrderKind::kBuyLand:
      trace.operation = "BUY_LAND";
      break;
  }
  candidates->push_back(CandidateOrder{order, std::move(trace), priority,
                                       static_cast<int>(candidates->size())});
  if (order.kind == OrderKind::kHire || order.kind == OrderKind::kBuyLand) {
    candidates->back().trace.item = -1;
  }
}

std::pair<std::optional<MarketOrder>, MarketSlotTrace> CompileCandidate(
    const PlannerStateView& state, const Farm& post_farm,
    const PrivateState& post_priv,
    const std::vector<std::optional<MarketOrder>>& feasible,
    const MarketOrder& candidate) {
  std::array<Farm, 2> farms;
  farms[state.player] = post_farm;
  farms[1 - state.player] = state.opponent_farm;
  std::array<PrivateState, 2> privates;
  privates[state.player] = post_priv;
  std::array<PlayerAction, 2> actions;
  actions[state.player].market = feasible;
  actions[state.player].market.push_back(candidate);
  MarketState market = state.market;
  const std::array<Farm*, 2> farm_ptrs = {&farms[0], &farms[1]};
  const std::array<PrivateState*, 2> private_ptrs = {&privates[0], &privates[1]};
  std::vector<MarketSlotTrace> trace;
  ApplyMarketPhase(state.config, farm_ptrs, private_ptrs, &market, actions[0],
                   actions[1], &trace);
  for (auto it = trace.rbegin(); it != trace.rend(); ++it) {
    if (it->player == state.player) return {it->actual, *it};
  }
  MarketSlotTrace missing;
  missing.player = state.player;
  missing.status = MarketOrderStatus::kMalformed;
  return {std::nullopt, missing};
}

}  // namespace

std::pair<std::vector<std::optional<MarketOrder>>, std::vector<StrategyTrace>>
ChooseMarketOrders(const PlannerStateView& state, const Farm& post_farm,
                   const PrivateState& post_priv,
                   const StrategyOptions& options, double cash_reserve_anchor,
                   const std::array<int64_t, kNumItems>& supply_reservations,
                   std::unordered_map<std::string, std::string>* rejected_states) {
  const int turns_per_day = std::max(1, state.config.turns_per_day);
  const int day = state.step / turns_per_day;
  const int hour = state.step % turns_per_day;
  const int final_day = (std::max(2, state.config.episode_steps) - 2) /
                        turns_per_day;
  const int remaining_days = final_day - day;
  std::vector<CandidateOrder> candidates;

  int64_t capacity_release = std::max<int64_t>(
      0, ShedTotal(post_priv) - (state.config.shed_capacity * 3) / 4);

  for (int product = 0; product < kNumProducts; ++product) {
    const int64_t protected_count =
        std::max<int64_t>(
            0, supply_reservations[product] - Carried(post_priv, product)) +
        options.product_reserves[product];
    int64_t sellable =
        std::max<int64_t>(0, post_priv.shed[product] - protected_count);
    if (!options.liquidation_only && remaining_days > 0) {
      if (state.market.prices[product] <
          options.minimum_sale_prices[product]) {
        sellable = 0;
      }
      switch (options.sale_mode) {
        case SaleMode::kHold:
          sellable = 0;
          break;
        case SaleMode::kCapacity:
          sellable = std::min(sellable, capacity_release);
          capacity_release -= sellable;
          break;
        case SaleMode::kValue:
          if (state.market.prices[product] <
              state.config.market_params[product].base) {
            sellable = 0;
          }
          break;
        case SaleMode::kImpact: {
          const int64_t capacity_units = std::min(sellable, capacity_release);
          sellable = std::max(BaseFloorSellable(state, product, sellable),
                              capacity_units);
          capacity_release -= capacity_units;
          break;
        }
        case SaleMode::kAggressive:
          break;
      }
    }
    if (sellable > 0) {
      AddCandidate(&candidates,
                   MarketOrder{OrderKind::kSell, product, sellable},
                   "liquidate", options.liquidation_only ? 600 : 400);
    }
  }

  for (int item_index = 0; item_index < kNumItems; ++item_index) {
    const int64_t total =
        post_priv.shed[item_index] + Carried(post_priv, item_index);
    const int64_t inventory_target =
        options.replenish_product_reserves && item_index < kNumProducts
            ? options.product_reserves[item_index]
            : 0;
    const int64_t deficit =
        std::max<int64_t>(
            0, std::max(supply_reservations[item_index], inventory_target) -
                   total);
    if (deficit <= 0 || hour >= turns_per_day - 1) continue;
    // The numeric policy ABI intentionally exposes BUY_PRODUCT only for
    // consumables that the deterministic executor can use directly.
    if (item_index < kNumProducts && item_index != item::kWheat &&
        item_index != item::kFertilizer) {
      continue;
    }
    const OrderKind kind = item_index >= item::kGoose
                               ? OrderKind::kBuyAnimal
                               : OrderKind::kBuyProduct;
    AddCandidate(&candidates,
                 MarketOrder{kind,
                             item_index >= item::kGoose
                                 ? item_index - item::kGoose
                                 : item_index,
                             deficit},
                 "intraday_supply", 500);
    candidates.back().trace.item = item_index;
  }

  if (!options.liquidation_only && hour < turns_per_day - 2) {
    const int workers = 1 + static_cast<int>(post_farm.hands.size());
    for (int count = workers; count < options.target_workers; ++count) {
      AddCandidate(&candidates, MarketOrder{OrderKind::kHire, 0, 0},
                   "capacity", 300, "HIRE");
    }
  }

  int owned = 0;
  int occupied = 0;
  std::array<int, kNumCrops> planted{};
  for (const Tile& tile : post_farm.tiles) {
    if (tile.kind == TileKind::kLocked) continue;
    ++owned;
    if (tile.kind != TileKind::kEmpty) ++occupied;
    if (tile.kind == TileKind::kPlant) ++planted[tile.crop];
  }
  const double utilization =
      static_cast<double>(occupied) / std::max(1, owned);
  if (!options.liquidation_only) {
    const int quadrants = post_farm.extra_unlocked + 1;
    const bool needs_land = options.target_land_quadrants > 0
                                ? quadrants < options.target_land_quadrants
                                : utilization >= 0.8;
    if (options.allow_land && needs_land && post_farm.extra_unlocked < 3) {
      AddCandidate(&candidates, MarketOrder{OrderKind::kBuyLand, 0, 0},
                   "expansion", 200, "BUY_LAND");
    }
    for (int crop = 0; options.allow_crop_investment && crop < kNumCrops;
         ++crop) {
      if (remaining_days <= kCrops[crop].first_yield_day) continue;
      if (!options.has_crop_targets && crop != options.preferred_crop) continue;
      const int target = options.has_crop_targets
                             ? options.target_crops[crop]
                             : std::min(options.target_plants, owned);
      const int64_t deficit = std::max<int64_t>(
          0, target - planted[crop] - post_priv.seeds[crop]);
      if (deficit > 0) {
        AddCandidate(&candidates,
                     MarketOrder{OrderKind::kBuySeed, crop, deficit},
                     "replenish", 250);
      }
    }
  }

  const int max_orders = std::max(1, state.config.max_market_orders);
  std::vector<int> selected(candidates.size());
  std::iota(selected.begin(), selected.end(), 0);
  std::stable_sort(selected.begin(), selected.end(), [&](int left, int right) {
    return std::tuple(-candidates[left].priority,
                      candidates[left].original_index) <
           std::tuple(-candidates[right].priority,
                      candidates[right].original_index);
  });
  if (static_cast<int>(selected.size()) > max_orders) {
    selected.resize(max_orders);
  }
  std::vector<bool> is_selected(candidates.size(), false);
  for (int index : selected) is_selected[index] = true;
  for (size_t index = 0; index < candidates.size(); ++index) {
    candidates[index].trace.selected = is_selected[index];
    if (!is_selected[index]) {
      candidates[index].trace.reason =
          "market_order_slots_reserved_for_higher_priority_intents";
    }
  }
  std::stable_sort(selected.begin(), selected.end(), [&](int left, int right) {
    return std::tuple(candidates[left].order.kind != OrderKind::kSell,
                      -candidates[left].priority,
                      candidates[left].original_index) <
           std::tuple(candidates[right].order.kind != OrderKind::kSell,
                      -candidates[right].priority,
                      candidates[right].original_index);
  });

  std::vector<std::optional<MarketOrder>> feasible;
  for (int index : selected) {
    CandidateOrder& candidate = candidates[index];
    const std::string key = OrderKey(candidate.order);
    const std::string state_token =
        RetryState(candidate.order, post_farm, post_priv, state.market);
    const auto rejected = rejected_states->find(key);
    if (rejected != rejected_states->end() && rejected->second == state_token) {
      candidate.trace.selected = false;
      candidate.trace.reason =
          "awaiting_relevant_state_change_after_rejection";
      continue;
    }
    if (rejected != rejected_states->end()) rejected_states->erase(rejected);

    auto [actual, trace] = CompileCandidate(state, post_farm, post_priv,
                                            feasible, candidate.order);
    if (trace.status != MarketOrderStatus::kApplied &&
        trace.status != MarketOrderStatus::kPartial) {
      candidate.trace.selected = false;
      candidate.trace.reason = "not_executable_from_post_unit_state";
      candidate.trace.retry_state = state_token;
      (*rejected_states)[key] = state_token;
      continue;
    }
    const bool discretionary_investment =
        candidate.trace.kind != "intraday_supply" &&
        candidate.order.kind != OrderKind::kSell;
    const double cash_reserve =
        std::max(cash_reserve_anchor * options.cash_reserve_fraction,
                 options.cash_reserve_amount);
    if (discretionary_investment && trace.money_after < cash_reserve) {
      candidate.trace.selected = false;
      candidate.trace.reason = "cash_reserve_budget";
      continue;
    }
    if (!actual) {
      candidate.trace.selected = false;
      candidate.trace.reason = "compiler_returned_no_effect";
      candidate.trace.retry_state = state_token;
      (*rejected_states)[key] = state_token;
      continue;
    }
    feasible.push_back(actual);
    rejected_states->erase(key);
    if (trace.status == MarketOrderStatus::kPartial) {
      candidate.trace.normalized_count = trace.committed;
    }
  }

  std::vector<StrategyTrace> trace;
  trace.reserve(candidates.size());
  for (CandidateOrder& candidate : candidates) {
    trace.push_back(std::move(candidate.trace));
  }
  return {std::move(feasible), std::move(trace)};
}

}  // namespace kagg::planner
