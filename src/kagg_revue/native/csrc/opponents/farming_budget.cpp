#include <algorithm>
#include <cmath>
#include <numeric>

#include "opponents/farming.hpp"

namespace kagg::opponents {

void Farming::Budget(const Engine& engine, int player, int route,
                     PlayerAction* action) const {
  const int step = engine.step_index();
  if (step % 72 != 0) return;
  const int end =
      std::min(static_cast<int>(portfolio_->routes[route].size()), step + 72);
  const auto& farm = engine.farm(player);
  const auto& priv = engine.priv(player);
  Stock balance{}, need{};
  std::array<int, 3> hires{};
  int quadrants = farm.extra_unlocked + 1;
  double cost = 0;
  for (int turn = step; turn < end; ++turn) {
    const auto& planned = portfolio_->Action(route, turn);
    for (int i = 0; i <= static_cast<int>(planned.hands.size()); ++i) {
      const auto& unit = Unit(planned, i);
      int item = -1;
      if (unit.op == UnitOp::kFeed)
        item = item::kWheat;
      else if (unit.op == UnitOp::kFertilize)
        item = item::kFertilizer;
      else if (unit.op == UnitOp::kPlace && unit.arg >= item::kGoose)
        item = unit.arg;
      if (item >= 0) {
        --balance[item];
        need[item] = std::max(need[item], -balance[item]);
      }
    }
    for (const auto& order : planned.market) {
      if (!order) continue;
      const int item = order->item;
      const int64_t quantity = std::max<int64_t>(1, order->remaining);
      switch (order->kind) {
        case OrderKind::kHire:
          ++hires[(turn - step) / 24];
          break;
        case OrderKind::kBuyLand:
          if (quadrants >= 1 && quadrants <= 3)
            cost += kLandPrices[quadrants++ - 1];
          break;
        case OrderKind::kBuySeed:
          cost += kCrops[item].seed_cost * quantity;
          break;
        case OrderKind::kBuyProduct:
          if (item == item::kWheat || item == item::kFertilizer) {
            cost += engine.market().prices[item] * quantity;
            balance[item] += quantity;
          }
          break;
        case OrderKind::kBuyAnimal:
          cost += kAnimals[item].cost * quantity;
          balance[item::kGoose + item] += quantity;
          break;
        default:
          break;
      }
    }
  }
  for (int day = 0; day < 3; ++day) {
    for (int i = 0; i < hires[day]; ++i)
      cost += Fibonacci(i + (day == 0 ? farm.hires_today : 0));
  }
  double cash = farm.money;
  for (int item = 0; item < kNumProducts; ++item) {
    const int64_t planned = portfolio_->FutureSells(route, step, item) -
                            portfolio_->FutureSells(route, end, item);
    cash += std::min(priv.shed[item], std::max<int64_t>(0, planned)) *
            engine.market().prices[item];
  }
  double shortfall = cost - cash;
  if (shortfall <= 0) return;
  const auto existing = SellTotals(*action);
  std::array<int, kNumProducts> priority{};
  std::iota(priority.begin(), priority.end(), 0);
  std::stable_sort(priority.begin(), priority.end(), [&](int a, int b) {
    return engine.market().prices[a] > engine.market().prices[b];
  });
  bool changed = false;
  for (int item : priority) {
    const int64_t price = engine.market().prices[item];
    if (price < 2 || shortfall <= 0) continue;
    const int64_t reserve =
        std::max<int64_t>(0, need[item] - Carried(priv, item));
    const int64_t available =
        std::max<int64_t>(0, priv.shed[item] - reserve - existing[item]);
    const int64_t quantity = std::min(
        available,
        static_cast<int64_t>(std::floor((shortfall + price - 1) / price)));
    if (quantity > 0 && MergeSale(action, item, quantity)) {
      changed = true;
      shortfall -= quantity * price;
    }
  }
  if (changed) {
    std::stable_partition(action->market.begin(), action->market.end(),
                          [](const auto& order) {
                            return order && order->kind == OrderKind::kSell;
                          });
  }
}
}  // namespace kagg::opponents
