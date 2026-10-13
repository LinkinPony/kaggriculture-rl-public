#include "opponents/router.hpp"

namespace kagg::opponents {
namespace {

std::array<double, 64> Features(const Engine& engine, int player) {
  std::array<double, 64> result{};
  int index = 0;
  for (int64_t value : engine.market().inventory)
    result[index++] = value - 10000;
  for (int64_t value : engine.market().prices) result[index++] = value;
  for (int i = 0; i < kNumProducts; ++i)
    result[index++] = ShopDemand(engine.town_shops(), i);
  for (int shop : engine.town_shops()) result[index + shop] += 1;
  index += kNumShops;
  for (int seat : {player, 1 - player}) {
    for (const auto& tile : engine.farm(seat).tiles) {
      if (tile.kind == TileKind::kPlant)
        result[index + tile.crop] += 1;
      else if (tile.kind == TileKind::kStructure && tile.has_animal)
        result[index + 5 + tile.animal] += 1;
    }
    index += 8;
  }
  result[index++] = engine.farm(player).money;
  result[index++] = engine.farm(1 - player).money;
  result[index++] = engine.farm(player).money - engine.farm(1 - player).money;
  for (int item = 0; item < kNumProducts; ++item)
    result[index++] = engine.priv(player).shed[item];
  result[index] = engine.farm(player).extra_unlocked + 1;
  return result;
}

}  // namespace

PlayerAction Router::Act(const Engine& engine, int player) {
  const int step = engine.step_index();
  if (step < 0 || step >= 719) return {};
  auto& state = states_[player];
  if (step == 0 || step < state.last) state = State{};
  const int block = step / 72;
  if (block != state.block) {
    const auto& tree = portfolio_->trees.at(block);
    const auto features = Features(engine, player);
    int at = 0;
    while (true) {
      const auto& node = tree.at(at);
      if (node.feature >= 0)
        at = features.at(node.feature) <= node.cut ? node.yes : node.no;
      else if (node.feature == -2)
        at = state.route == static_cast<int>(node.cut) ? node.yes : node.no;
      else {
        if (node.route >= 0) state.route = node.route;
        break;
      }
    }
    state.block = block;
  }
  state.last = step;
  auto action = portfolio_->Action(state.route, step);
  if (action.market.size() > 10) action.market.resize(10);
  for (auto& slot : action.market) {
    if (!slot) slot = MarketOrder{OrderKind::kSell, item::kWheat, 0};
  }
  return action;
}

}  // namespace kagg::opponents
