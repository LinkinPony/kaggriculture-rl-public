#include "opponents/shop.hpp"

#include <algorithm>
#include <cstdint>

namespace kagg::opponents {

PlayerAction ShopRouter::Act(const Engine& engine, int player) {
  const int step = engine.step_index();
  auto& state = states_[player];
  if (step == 0) state = State{};
  for (const auto& stage : portfolio_->shop_stages) {
    if (step != stage.step || state.last_decision == step) continue;
    // These are the only features read by the authenticated frozen model.
    // Match observation.py's eight-shop cap and signed int32 market packing.
    const auto& shops = engine.town_shops();
    const double value = stage.feature == 23
        ? std::count(shops.begin(), shops.begin() + std::min<size_t>(8, shops.size()), 7)
        : static_cast<int32_t>(engine.market().inventory[item::kEgg]);
    state.route = value <= stage.threshold ? stage.left : stage.right;
    state.last_decision = step;
  }
  if (step < 0 || step >= 719) return {};
  return portfolio_->Action(state.route, step);
}

}  // namespace kagg::opponents
