#include "opponents/farming.hpp"

#include <algorithm>
#include <cstring>
#include <numeric>

namespace kagg::opponents {
namespace {

bool WeedNoop(const Engine& engine, int player, const PlayerAction& action,
              int unit) {
  const auto [x, y] = Position(engine.farm(player), unit);
  const int board = engine.config().board_size;
  const bool adjacent = IsShedAdjacent(x, y, board);
  const auto& inv = engine.priv(player).inventories[unit];
  const auto& request = Unit(action, unit);
  switch (request.op) {
    case UnitOp::kNorth:
      return y == 0;
    case UnitOp::kSouth:
      return y == board - 1;
    case UnitOp::kEast:
      return x == board - 1;
    case UnitOp::kWest:
      return x == 0;
    case UnitOp::kDrop:
      return !adjacent || inv.items.empty();
    case UnitOp::kPickup:
      return !adjacent;
    case UnitOp::kPlace:
      return !adjacent || request.arg < 0 || inv.Get(request.arg) <= 0;
    case UnitOp::kDig:
      return false;
    default:
      return true;
  }
}

void Terminal(const Stock& shed, const MarketState& market,
              PlayerAction* action) {
  std::array<bool, kNumProducts> covered{};
  std::vector<std::optional<MarketOrder>> result;
  for (auto slot : action->market) {
    if (slot && slot->kind == OrderKind::kSell) {
      const int item = slot->item;
      if (covered[item] || shed[item] <= 0) continue;
      slot->remaining = shed[item];
      covered[item] = true;
    }
    result.push_back(slot);
  }
  std::vector<int> missing;
  for (int item = 0; item < kNumProducts; ++item) {
    if (!covered[item] && shed[item] > 0) missing.push_back(item);
  }
  std::sort(missing.begin(), missing.end(), [&](int a, int b) {
    const int64_t left = shed[a] * std::max<int64_t>(1, market.prices[a]);
    const int64_t right = shed[b] * std::max<int64_t>(1, market.prices[b]);
    return left != right ? left > right
                         : std::strcmp(kItemNames[a], kItemNames[b]) < 0;
  });
  for (int item : missing) {
    if (result.size() >= 10) break;
    result.push_back(MarketOrder{OrderKind::kSell, item, shed[item]});
  }
  action->market = std::move(result);
}

}  // namespace

PlayerAction Farming::Act(const Engine& engine, int player) {
  const int step = engine.step_index();
  auto& state = states_[player];
  if (step == 0 || step < state.last) state = State{};
  state.last = step;
  int target = -1;
  if (step == 226 && std::count(engine.town_shops().begin(),
                                engine.town_shops().end(), 7) >= 1)
    target = 1;
  if (step == 360 && engine.market().prices[item::kCarrot] >= 42) target = 2;
  if (step == 433 && engine.market().inventory[item::kMilk] >= 10067)
    target = 3;
  if (target >= 0 && target != state.route &&
      portfolio_->prefixes[state.route][target] >= step) {
    state.route = target;
  }
  auto action = portfolio_->Action(state.route, step);
  Align(engine, player, &action);
  for (int i = 0; i <= static_cast<int>(action.hands.size()); ++i) {
    if (UnitTile(engine, player, i).kind == TileKind::kWeed &&
        WeedNoop(engine, player, action, i)) {
      Unit(action, i) = {UnitOp::kDig, -1, 1};
    }
  }
  const Stock projected = ProjectShed(engine, player, action, true, false);
  Budget(engine, player, state.route, &action);
  if (step % 24 == 23) Capacity(engine, player, state.route, &action);
  Stock available = projected;
  for (auto& order : action.market) {
    if (!order) continue;
    if (order->kind == OrderKind::kSell) {
      order->remaining = std::min(std::max<int64_t>(0, order->remaining),
                                  std::max<int64_t>(0, available[order->item]));
      available[order->item] -= order->remaining;
    } else if (order->kind == OrderKind::kBuyProduct) {
      available[order->item] += std::max<int64_t>(0, order->remaining);
    }
  }
  const auto planned = SellTotals(action);
  std::vector<MarketOrder> extra;
  for (int item = 0; item < kNumProducts; ++item) {
    const int64_t have = projected[item] - planned[item];
    if (have <= 0) continue;
    const int64_t surplus =
        have - (step / engine.config().turns_per_day >= 29
                    ? 0
                    : portfolio_->FutureSells(state.route, step + 1, item));
    if (surplus > 0 && engine.market().prices[item] > 1) {
      extra.push_back({OrderKind::kSell, item, surplus});
    }
  }
  std::stable_sort(extra.begin(), extra.end(),
                   [&](const auto& a, const auto& b) {
                     return engine.market().prices[a.item] * a.remaining >
                            engine.market().prices[b.item] * b.remaining;
                   });
  for (const auto& sale : extra) action.market.push_back(sale);
  if (action.market.size() > 10) action.market.resize(10);
  if (step == 718) Terminal(projected, engine.market(), &action);
  return action;
}

void Farming::Capacity(const Engine& engine, int player, int route,
                       PlayerAction* action) const {
  const auto& priv = engine.priv(player);
  const int step = engine.step_index();
  int64_t carried = 0, produced = 0, consumed = 0, bought = 0, sold = 0;
  for (const auto& inventory : priv.inventories) {
    for (const auto& [item, quantity] : inventory.items)
      carried += std::max<int64_t>(0, quantity);
  }
  for (int i = 0; i <= static_cast<int>(action->hands.size()); ++i) {
    const auto& tile = UnitTile(engine, player, i);
    const auto& unit = Unit(*action, i);
    if (unit.op == UnitOp::kHarvest)
      produced += std::max(0, tile.yield_units);
    else if (unit.op == UnitOp::kCollectFertilizer && tile.fertilizer_available)
      ++produced;
    else if (unit.op == UnitOp::kFeed || unit.op == UnitOp::kFertilize ||
             (unit.op == UnitOp::kPlace && unit.arg >= item::kGoose))
      ++consumed;
  }
  auto planned = SellTotals(*action);
  for (int item = 0; item < kNumProducts; ++item)
    sold += std::min(priv.shed[item], planned[item]);
  for (const auto& order : action->market) {
    if (order && (order->kind == OrderKind::kBuyProduct ||
                  order->kind == OrderKind::kBuyAnimal)) {
      bought += std::max<int64_t>(0, order->remaining);
    }
  }
  int64_t needed =
      Total(priv.shed) + carried + produced - consumed + bought - sold - 99;
  if (needed <= 0) return;
  std::array<int, kNumProducts> priority{};
  std::iota(priority.begin(), priority.end(), 0);
  std::sort(priority.begin(), priority.end(), [&](int a, int b) {
    const bool future_a = portfolio_->FutureSells(route, step + 1, a) > 0;
    const bool future_b = portfolio_->FutureSells(route, step + 1, b) > 0;
    if (future_a != future_b) return future_a < future_b;
    if (engine.market().prices[a] != engine.market().prices[b])
      return engine.market().prices[a] > engine.market().prices[b];
    return std::strcmp(kItemNames[a], kItemNames[b]) < 0;
  });
  for (int item : priority) {
    const int64_t quantity =
        std::min(needed, std::max<int64_t>(0, priv.shed[item] - planned[item]));
    if (quantity <= 0 || !MergeSale(action, item, quantity)) continue;
    planned[item] += quantity;
    needed -= quantity;
    if (needed <= 0) break;
  }
}
}  // namespace kagg::opponents
