#include <algorithm>

#include "kaito_v48_support.hpp"
#include "opponents/kaito.hpp"

namespace kagg::opponents {

void Kaito::Flow(const Engine& engine, Controller* state) {
  const int step = engine.step_index();
  Products current = engine.market().inventory;
  for (auto& value : current)
    if (value == 0) value = 10000;
  if (state->inventory_seen && state->last == step - 1) {
    int64_t own_total = 0, opponent_total = 0, overlap = 0;
    for (int item = 0; item < kNumProducts; ++item) {
      const int64_t inferred = std::clamp<int64_t>(
          current[item] - state->inventory[item] - state->own_net[item] +
              Demand(state->shops, item, step - 1,
                     engine.config().shop_sell_interval,
                     engine.config().center_sell_interval),
          0, 80);
      state->supply[item] =
          (1.0 - 0.35) * state->supply[item] + 0.35 * inferred;
      if (item >= item::kCarrot && item <= item::kWool) {
        const int64_t own = std::max<int64_t>(0, state->own_net[item]);
        own_total += own;
        opponent_total += inferred;
        overlap += std::min(own, inferred);
      }
    }
    if (own_total > 0 || opponent_total > 0) {
      const double agreement =
          2.0 * overlap /
          std::max(1.0, static_cast<double>(own_total + opponent_total));
      const double alpha = agreement < state->confidence ? 0.55 : 0.35;
      state->confidence = std::clamp(
          (1.0 - alpha) * state->confidence + alpha * agreement, 0.0, 1.0);
      ++state->evidence;
    } else
      state->confidence *= 0.99;
  }
  state->inventory = current;
  state->inventory_seen = true;
}

void Kaito::Repay(int step, PlayerAction* action, Controller* state) {
  auto found = state->due.find(step);
  if (found == state->due.end()) return;
  Products due = found->second;
  state->due.erase(found);
  std::vector<std::optional<MarketOrder>> adjusted;
  for (auto order : action->market) {
    if (order && order->kind == OrderKind::kSell && due[order->item] > 0) {
      const int64_t reduction =
          std::min(std::max<int64_t>(0, order->remaining), due[order->item]);
      order->remaining -= reduction;
      due[order->item] -= reduction;
      if (order->remaining <= 0) continue;
    }
    adjusted.push_back(order);
  }
  if (step < 718) {
    for (int item = 0; item < kNumProducts; ++item) {
      if (due[item] > 0) state->due[step + 1][item] += due[item];
    }
  }
  action->market = std::move(adjusted);
}

Products Kaito::ExecutableNet(const Engine& engine, int player,
                              const PlayerAction& action) {
  const int64_t capacity = engine.config().shed_capacity;
  Stock shed = ProjectShed(engine, player, action, true, true, capacity, 0);
  Products result{};
  for (const auto& order : action.market) {
    if (!order) continue;
    const int item = order->item;
    const int64_t quantity = std::max<int64_t>(0, order->remaining);
    if (order->kind == OrderKind::kSell) {
      const int64_t executed =
          std::min(quantity, std::max<int64_t>(0, shed[item]));
      shed[item] -= executed;
      result[item] += executed;
    } else if (order->kind == OrderKind::kBuyProduct &&
               (item == item::kWheat || item == item::kFertilizer)) {
      const int64_t executed =
          std::min(quantity, std::max<int64_t>(0, capacity - Total(shed)));
      shed[item] += executed;
      result[item] -= executed;
    }
  }
  return result;
}

PlayerAction Kaito::Control(const Engine& engine, int player, int route,
                            Controller* state) {
  const int step = engine.step_index();
  if (step == 0 || step < state->last) *state = Controller{};
  Flow(engine, state);
  if (kaito::CloneDistance(engine) <= 8.0)
    ++state->near_streak;
  else
    state->near_streak = 0;
  if (state->near_streak >= 12) state->near = true;
  auto action = portfolio_->Action(route, step);
  WeedRepair(*portfolio_, route, engine, player, &action, &state->repair);
  kaito::ReorderSellSlots(
      engine, &action, engine.config().center_sell_interval >= 24 ? 0.25 : 0.0);
  Repay(step, &action, state);
  // Frozen _V54_CONFIG disables deferral and the market maker.
  Preempt(engine, player, route, &action, state);
  const double deficit =
      engine.farm(1 - player).money - engine.farm(player).money;
  const double peak =
      *std::max_element(state->supply.begin() + item::kCarrot,
                        state->supply.begin() + item::kWool + 1);
  kaito::ReorderSellSlots(engine, &action, 0.25);
  if (state->near || deficit >= 4500.0 || peak >= 3.0) {
    std::stable_partition(
        action.market.begin(), action.market.end(), [](const auto& order) {
          return order && order->kind == OrderKind::kSell &&
                 order->item >= item::kCarrot && order->item <= item::kWool;
        });
  }
  if (step == 718) kaito::ReplaceTerminalMarket(engine, player, &action);
  Align(engine, player, &action);
  if (action.market.size() > 10) action.market.resize(10);
  state->own_net = ExecutableNet(engine, player, action);
  state->shops = engine.town_shops();
  state->last = step;
  return action;
}

}  // namespace kagg::opponents
