#include "opponents/boatlee.hpp"

#include <algorithm>
#include <cmath>

namespace kagg::opponents {
namespace {
constexpr std::array<int, 3> kItems{item::kStrawberry, item::kMilk,
                                    item::kWool};
constexpr std::array<double, 3> kBases{120, 160, 200};

std::array<int, 3> Counts(const Farm& farm) {
  std::array<int, 3> counts{};
  for (const auto& tile : farm.tiles) {
    if (tile.kind == TileKind::kPlant && tile.crop == item::kStrawberry)
      ++counts[0];
    if (tile.kind == TileKind::kStructure && tile.has_animal) {
      if (tile.animal == 1) ++counts[1];
      if (tile.animal == 2) ++counts[2];
    }
  }
  return counts;
}

int Reserve(int step, int64_t total) {
  int value = step < 528   ? 12
              : step < 600 ? 8
              : step < 648 ? 6
              : step < 684 ? 3
              : step < 704 ? 2
                           : 0;
  if (total >= 88) return 0;
  return total >= 72 ? std::max(0, value - 7) : value;
}
}  // namespace

PlayerAction Boatlee::Act(const Engine& engine, int player) {
  const int step = engine.step_index();
  auto action = portfolio_->Action(0, step);
  WeedRepair(*portfolio_, 0, engine, player, &action, &repair_[player]);
  // _FR_ITEMS is empty in the authenticated source, so its debt is always
  // empty.
  auto& state = states_[player];
  if (step == 0 || step <= state.last) {
    state = State{};
    state.last = step;
  }
  if (state.last == step - 1) {
    for (int item : kItems) {
      const int64_t external =
          engine.market().inventory[item] - state.inventory[item] +
          Demand(state.shops, item, step - 1) - state.sold[item];
      state.pressure[item] = std::max(
          0.0, state.pressure[item] * 0.72 +
                   std::clamp(static_cast<double>(external), 0.0, 24.0));
    }
  }
  state.last = step;
  const auto own = Counts(engine.farm(player));
  const auto rival = Counts(engine.farm(1 - player));
  if (state.mirror < 0 && step >= 289) {
    int distance = 0;
    for (int i = 0; i < 3; ++i) distance += std::abs(own[i] - rival[i]);
    const auto& a = engine.farm(player);
    const auto& b = engine.farm(1 - player);
    state.mirror = distance <= 2 && a.hands.size() == b.hands.size() &&
                   a.extra_unlocked == b.extra_unlocked &&
                   std::abs(a.money - b.money) <= 250;
  }
  const auto& shed = engine.priv(player).shed;
  const int64_t total = Total(shed);
  if (step >= 456) {
    for (int index = 0; index < 3; ++index) {
      const int item = kItems[index];
      const int64_t stock = std::max<int64_t>(0, shed[item]);
      const int64_t pickup = PickupReserve(action, item);
      const int64_t scheduled = std::min(std::max<int64_t>(0, stock - pickup),
                                         SellTotals(action)[item]);
      const int64_t unscheduled =
          std::max<int64_t>(0, stock - pickup - scheduled);
      const int demand = ShopDemand(engine.town_shops(), item);
      const int reserve =
          Reserve(step, total) + (step < 684 ? std::min(14, demand * 2) : 0);
      const int64_t excess = std::max<int64_t>(0, unscheduled - reserve);
      const int64_t budget = std::max<int64_t>(
          0, (state.mirror == 1 ? 0 : 18) - state.added[item]);
      if (excess == 0 || budget == 0) continue;
      double gate = 0.66;
      if (step < 684) gate += std::min(0.24, demand * 0.045);
      if (step >= 648) gate -= 0.12;
      if (step >= 684) gate -= 0.18;
      if (state.pressure[item] >= 2.0) gate -= 0.18;
      if (rival[index] >= own[index]) gate -= 0.08;
      if (total < 88 && step < 704 &&
          engine.market().prices[item] / kBases[index] < std::max(0.2, gate))
        continue;
      const int64_t tranche = 4 + (state.pressure[item] >= 2.0 ? 4 : 0) +
                              (total >= 72 ? 4 : 0) + (step >= 684 ? 5 : 0);
      const int64_t quantity = std::min({excess, tranche, budget});
      MergeSale(&action, item, quantity, true);
      // Source charges the budget even when its full market queue blocks
      // insertion.
      state.added[item] += quantity;
    }
  }
  const auto sold = SellTotals(action);
  for (int item : kItems) {
    state.inventory[item] = engine.market().inventory[item];
    state.sold[item] = std::min(std::max<int64_t>(0, shed[item]), sold[item]);
  }
  state.shops = engine.town_shops();
  Align(engine, player, &action);
  return action;
}
}  // namespace kagg::opponents
