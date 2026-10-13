#include "kaito_v39/policy.hpp"

#include <algorithm>
#include <array>
#include <cstdint>
#include <cstring>
#include <optional>
#include <utility>
#include <vector>

#include "kaito_v39/market.hpp"
#include "kaito_v48_support.hpp"

namespace kagg::kaito_v39 {
namespace {

constexpr int kReplaySteps = 8;
constexpr int kCloneDetectionStart = 48;
constexpr int kCloneActiveStop = 679;
constexpr int kCloneStreakRequired = 24;
constexpr int kMaximumSellBatch = 100;
constexpr int kMaximumMarketOrders = 10;
constexpr std::array<int, kNumProducts> kAlphabeticalProducts = {
    item::kCarrot, item::kEgg, item::kFertilizer,
    item::kMelon,  item::kMilk, item::kStrawberry,
    item::kTomato, item::kWheat, item::kWool,
};

bool IsWeedAt(const Engine& engine, int player, int unit) {
  const Farm& farm = engine.farm(player);
  const int x = unit == 0 ? farm.farmer_x : farm.hands[unit - 1].first;
  const int y = unit == 0 ? farm.farmer_y : farm.hands[unit - 1].second;
  const int board_size = engine.config().board_size;
  if (x < 0 || y < 0 || x >= board_size || y >= board_size) return false;
  return farm.tiles[static_cast<size_t>(y) * board_size + x].kind ==
         TileKind::kWeed;
}

PlayerAction ApplyRepair(const Portfolio& portfolio, const Engine& engine,
                         int player, Route route, PlayerAction action,
                         RepairState* state) {
  const int step = engine.step_index();
  kaito::AlignHands(engine, player, &action);
  const int unit_count = 1 + static_cast<int>(action.hands.size());
  if (step == 0 || !state->initialized || step < state->last_step) {
    *state = RepairState{};
    state->initialized = true;
  }
  state->last_step = step;
  state->active.resize(unit_count);
  const auto set_unit = [&action](int unit, const UnitAction& request) {
    if (unit == 0) {
      action.farmer = request;
    } else {
      action.hands[unit - 1] = request;
    }
  };
  const auto get_unit = [&action](int unit) -> UnitAction {
    return unit == 0 ? action.farmer : action.hands[unit - 1];
  };
  for (int unit = 0; unit < unit_count; ++unit) {
    RepairTransaction& transaction = state->active[unit];
    if (!transaction.active) continue;
    const int age = step - transaction.start;
    if (age == 1) {
      set_unit(unit, transaction.intended);
    } else if (age >= 2 && age <= 1 + kReplaySteps) {
      set_unit(unit, portfolio.unit_action(route, step - 1, unit));
    } else {
      transaction = RepairTransaction{};
    }
  }
  for (int unit = 0; unit < unit_count; ++unit) {
    RepairTransaction& transaction = state->active[unit];
    const UnitAction intended = get_unit(unit);
    if (transaction.active ||
        (intended.op != UnitOp::kBuildPasture &&
         intended.op != UnitOp::kPlant) ||
        !IsWeedAt(engine, player, unit)) {
      continue;
    }
    transaction.active = true;
    transaction.start = step;
    transaction.intended = intended;
    set_unit(unit, UnitAction{UnitOp::kDig, -1, 1});
  }
  kaito::AlignHands(engine, player, &action);
  return action;
}

std::array<int64_t, kNumProducts> SellTotals(const PlayerAction& action) {
  std::array<int64_t, kNumProducts> totals{};
  for (const auto& slot : action.market) {
    if (slot.has_value() && slot->kind == OrderKind::kSell &&
        slot->item >= 0 && slot->item < kNumProducts) {
      totals[slot->item] += std::max<int64_t>(0, slot->remaining);
    }
  }
  return totals;
}

PlayerAction ApplyPreemption(const Portfolio& portfolio, const Engine& engine,
                             int player, Route route, PlayerAction action,
                             PreemptionState* state) {
  kaito::AlignHands(engine, player, &action);
  const int step = engine.step_index();
  if (step == 0 || !state->initialized || step < state->last_step) {
    *state = PreemptionState{};
    state->initialized = true;
  }
  state->last_step = step;
  if (kaito::CloneDistance(engine) <= 2.0) {
    ++state->near_streak;
  } else {
    state->near_streak = 0;
  }
  if (!state->latched && step >= kCloneDetectionStart &&
      state->near_streak >= kCloneStreakRequired) {
    state->latched = true;
  }
  if (!state->latched) return action;

  std::array<int64_t, kNumProducts> due_now{};
  if (const auto found = state->due.find(step); found != state->due.end()) {
    due_now = found->second;
    state->due.erase(found);
  }
  std::vector<std::optional<MarketOrder>> adjusted;
  adjusted.reserve(action.market.size());
  for (auto slot : action.market) {
    if (slot.has_value() && slot->kind == OrderKind::kSell &&
        slot->item >= 0 && slot->item < kNumProducts) {
      int64_t& debt = due_now[slot->item];
      if (debt > 0) {
        int64_t quantity = std::max<int64_t>(0, slot->remaining);
        const int64_t reduction = std::min(quantity, debt);
        quantity -= reduction;
        debt -= reduction;
        if (quantity <= 0) continue;
        slot->remaining = quantity;
      }
    }
    adjusted.push_back(std::move(slot));
  }
  if (step < 718) {
    for (int product = 0; product < kNumProducts; ++product) {
      if (due_now[product] > 0) {
        state->due[step + 1][product] += due_now[product];
      }
    }
  }
  action.market = std::move(adjusted);

  if (step < kCloneDetectionStart || step >= kCloneActiveStop ||
      step + 1 >= kRouteTurns ||
      static_cast<int>(action.market.size()) >= kMaximumMarketOrders) {
    return action;
  }
  const auto future = portfolio.sell_totals(route, step + 1);
  if (std::all_of(future.begin(), future.end(),
                  [](int64_t quantity) { return quantity <= 0; })) {
    return action;
  }
  auto available = kaito::ProjectedShed(engine, player, action);
  const auto existing = SellTotals(action);
  for (int product = 0; product < kNumProducts; ++product) {
    available[product] =
        std::max<int64_t>(0, available[product] - existing[product]);
  }

  int64_t shifted = 0;
  for (const int product : kAlphabeticalProducts) {
    if (static_cast<int>(action.market.size()) >= kMaximumMarketOrders) break;
    const int64_t quantity = std::min(
        {std::max<int64_t>(0, future[product]),
         std::max<int64_t>(0, available[product]),
         std::max<int64_t>(0, kMaximumSellBatch - shifted)});
    if (quantity <= 0) continue;
    action.market.push_back(
        MarketOrder{OrderKind::kSell, product, quantity});
    available[product] = std::max<int64_t>(0, available[product] - quantity);
    state->due[step + 1][product] += quantity;
    shifted += quantity;
  }
  if (shifted > 0) ReorderSellSlots(engine, &action, 0.25);
  return action;
}

bool UnitActionsEqual(const UnitAction& left, const UnitAction& right) {
  return left.op == right.op && left.arg == right.arg && left.n == right.n;
}

bool MarketOrdersEqual(const std::optional<MarketOrder>& left,
                       const std::optional<MarketOrder>& right) {
  if (left.has_value() != right.has_value()) return false;
  if (!left.has_value()) return true;
  return left->kind == right->kind && left->item == right->item &&
         left->remaining == right->remaining;
}

}  // namespace

PlayerAction ApplyRoute(const Portfolio& portfolio, const Engine& engine,
                        int player, Route route, RouteState* state) {
  PlayerAction action = portfolio.action(route, engine.step_index());
  action = ApplyRepair(portfolio, engine, player, route, std::move(action),
                       &state->repair);
  ReorderSellSlots(engine, &action,
                   engine.config().center_sell_interval >= 24 ? 0.25 : 0.0);
  action = ApplyPreemption(portfolio, engine, player, route, std::move(action),
                           &state->preemption);
  return ApplyMarketMaker(portfolio, engine, player, route, std::move(action),
                          &state->market_maker);
}

bool ActionsEqual(const PlayerAction& left, const PlayerAction& right) {
  if (!UnitActionsEqual(left.farmer, right.farmer) ||
      left.hands.size() != right.hands.size() ||
      left.market.size() != right.market.size()) {
    return false;
  }
  for (size_t index = 0; index < left.hands.size(); ++index) {
    if (!UnitActionsEqual(left.hands[index], right.hands[index])) return false;
  }
  for (size_t index = 0; index < left.market.size(); ++index) {
    if (!MarketOrdersEqual(left.market[index], right.market[index])) return false;
  }
  return true;
}

}  // namespace kagg::kaito_v39
