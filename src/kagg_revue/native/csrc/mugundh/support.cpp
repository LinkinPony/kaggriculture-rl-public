#include "mugundh/detail.hpp"

#include <algorithm>
#include <array>
#include <cstdint>
#include <numeric>

namespace kagg::mugundh::detail {
namespace {

constexpr int64_t kFixedShedCapacity = 100;

void Deposit(int item_index, int64_t quantity,
             std::array<int64_t, kNumItems>* shed) {
  const int64_t total =
      std::accumulate(shed->begin(), shed->end(), int64_t{0});
  const int64_t room = std::max<int64_t>(0, kFixedShedCapacity - total);
  const int64_t amount =
      std::min(std::max<int64_t>(0, quantity), room);
  if (item_index >= 0 && item_index < kNumItems && amount > 0) {
    (*shed)[item_index] += amount;
  }
}

}  // namespace

UnitAction Pass() { return UnitAction{UnitOp::kPass, -1, 1}; }

void AlignHands(const Engine& engine, int player, PlayerAction* action) {
  action->hands.resize(engine.farm(player).hands.size(), Pass());
}

std::array<int64_t, kNumItems> ProjectedShed(
    const Engine& engine, int player, const PlayerAction& action) {
  std::array<int64_t, kNumItems> projected = engine.priv(player).shed;
  const Farm& farm = engine.farm(player);
  const PrivateState& priv = engine.priv(player);
  const auto access = ShedAccessTiles(engine.config().board_size);
  const int unit_count = 1 + static_cast<int>(farm.hands.size());
  for (int unit = 0; unit < unit_count; ++unit) {
    if (unit >= static_cast<int>(priv.inventories.size())) continue;
    const int x = unit == 0 ? farm.farmer_x : farm.hands[unit - 1].first;
    const int y = unit == 0 ? farm.farmer_y : farm.hands[unit - 1].second;
    if (std::find(access.begin(), access.end(), std::pair{x, y}) ==
        access.end()) {
      continue;
    }
    if (x < 0 || y < 0 || x >= engine.config().board_size ||
        y >= engine.config().board_size) {
      continue;
    }
    const UnitAction request =
        unit == 0
            ? action.farmer
            : (unit - 1 < static_cast<int>(action.hands.size())
                   ? action.hands[unit - 1]
                   : Pass());
    const Inventory& inventory = priv.inventories[unit];
    if (request.op == UnitOp::kDrop) {
      for (const auto& [item_index, quantity] : inventory.items) {
        Deposit(item_index, quantity, &projected);
      }
      continue;
    }
    if (request.op != UnitOp::kPlace || request.arg < 0 ||
        request.arg >= kNumItems) {
      continue;
    }
    if (request.arg >= item::kGoose) {
      const int animal = request.arg - item::kGoose;
      const Tile& tile = farm.tiles[
          static_cast<size_t>(y) * engine.config().board_size + x];
      if (tile.kind == TileKind::kStructure && !tile.has_animal &&
          tile.structure == kAnimals[animal].structure) {
        continue;
      }
    }
    Deposit(request.arg,
            std::min(std::max<int64_t>(0, request.n),
                     inventory.Get(request.arg)),
            &projected);
  }
  return projected;
}

}  // namespace kagg::mugundh::detail
