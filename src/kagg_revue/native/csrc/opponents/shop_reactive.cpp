#include "opponents/shop_reactive.hpp"

#include <algorithm>

namespace kagg::opponents {
namespace {

int Plan(const std::vector<int>& shops) {
  if (shops.size() < 2) return 0;
  // Exact SHOP_PLANS mapping, in the engine's sorted shop-name order.
  constexpr std::array<int, 8> kSecondYarn{3, 4, 5, 6, 5, 7, 8, 12};
  constexpr std::array<int, 8> kFirstYarn{9, 9, 1, 9, 10, 6, 11, 12};
  if (shops[1] == 7) return kSecondYarn.at(shops[0]);
  if (shops[0] == 7) return kFirstYarn.at(shops[1]);
  return 0;
}

Stock Project(const Engine& engine, int player, const PlayerAction& action) {
  // The source visits only workers present in both the plan and observation.
  auto bounded = action;
  if (bounded.hands.size() > engine.farm(player).hands.size())
    bounded.hands.resize(engine.farm(player).hands.size());
  return ProjectShed(engine, player, bounded, true, false, 100, 0);
}

PlayerAction Liquidate(const Engine& engine, int player) {
  PlayerAction action;
  const auto& farm = engine.farm(player);
  const auto& inventories = engine.priv(player).inventories;
  action.hands.resize(farm.hands.size());
  for (size_t worker = 0; worker <= farm.hands.size(); ++worker) {
    const auto [x, y] = Position(farm, worker);
    if (IsShedAdjacent(x, y, engine.config().board_size) &&
        worker < inventories.size() && !inventories[worker].items.empty())
      Unit(action, worker) = {UnitOp::kDrop, -1, 1};
  }
  const auto stock = Project(engine, player, action);
  for (int item = 0; item < kNumProducts; ++item) {
    if (stock[item] > 0)
      action.market.push_back(MarketOrder{OrderKind::kSell, item, stock[item]});
  }
  const auto& prices = engine.market().prices;
  std::stable_sort(action.market.begin(), action.market.end(),
                   [&](const auto& left, const auto& right) {
                     return prices[left->item] * left->remaining >
                            prices[right->item] * right->remaining;
                   });
  return action;
}

}  // namespace

void ReactiveShopRouter::Repair(const Engine& engine, int player,
                                PlayerAction* action, State* state) {
  const int day = engine.step_index() / 24;
  if (day != state->day) {
    state->day = day;
    state->queues.clear();
  }
  const size_t count = 1 + std::min(action->hands.size(), engine.farm(player).hands.size());
  if (state->queues.size() < count) state->queues.resize(count);
  for (size_t worker = 0; worker < count; ++worker) {
    auto& queue = state->queues[worker];
    queue.push_back(Unit(*action, worker));
    const auto operation = queue.front().op;
    const bool blocked = (operation == UnitOp::kPlant || operation == UnitOp::kBuildCoop ||
                          operation == UnitOp::kBuildPasture) &&
                         UnitTile(engine, player, worker).kind == TileKind::kWeed;
    if (blocked) {
      Unit(*action, worker) = {UnitOp::kDig, -1, 1};
    } else {
      Unit(*action, worker) = queue.front();
      queue.pop_front();
    }
  }
}

void ReactiveShopRouter::Sales(const Engine& engine, int player,
                               PlayerAction* action, State* state) {
  const int step = engine.step_index();
  if (state->sale_due_step == step) {
    auto remaining = state->advanced_sales;
    for (auto& order : action->market) {
      if (!order || order->kind != OrderKind::kSell) continue;
      const int item = order->item;
      const int64_t removed = std::min(std::max<int64_t>(0, order->remaining), remaining[item]);
      order->remaining -= removed;
      remaining[item] -= removed;
    }
  }
  state->advanced_sales = {};
  state->sale_due_step = -1;
  const int next = step + 1;
  if (next > 718 || next % 72 == 0 || step % 4 == 0) return;
  const auto planned = SellTotals(portfolio_->Action(state->plan, next));
  std::array<bool, kNumProducts> selling{};
  for (const auto& order : action->market) {
    if (order && order->kind == OrderKind::kSell) selling[order->item] = true;
  }
  const auto stock = Project(engine, player, *action);
  for (int item = 0; item < kNumProducts; ++item) {
    if (item == item::kWheat || item == item::kFertilizer || selling[item]) continue;
    const int64_t quantity = std::min(stock[item], planned[item]);
    if (quantity <= 0 || engine.market().prices[item] < 2) continue;
    if (action->market.size() >= 10) break;
    action->market.push_back(MarketOrder{OrderKind::kSell, item, quantity});
    state->advanced_sales[item] = quantity;
    state->sale_due_step = next;
  }
}

PlayerAction ReactiveShopRouter::Act(const Engine& engine, int player) {
  const int step = engine.step_index();
  auto& state = states_[player];
  if (step <= state.last_step) state = State{};
  state.last_step = step;
  if (step == 144) state.plan = Plan(engine.town_shops());
  if (step == 648) state.plan = 2;
  auto action = portfolio_->Action(state.plan, step);
  Repair(engine, player, &action, &state);
  Sales(engine, player, &action, &state);
  if (action.market.size() > 10) action.market.resize(10);
  return step == 718 ? Liquidate(engine, player) : action;
}

}  // namespace kagg::opponents
