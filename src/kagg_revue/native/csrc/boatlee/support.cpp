#include "boatlee/detail.hpp"

#include <algorithm>
#include <array>
#include <cstdint>
#include <numeric>
#include <optional>
#include <utility>
#include <vector>

namespace kagg::boatlee::detail {
namespace {

bool UnitsEqual(const UnitAction& left, const UnitAction& right) {
  return left.op == right.op && left.arg == right.arg && left.n == right.n;
}

bool OrdersEqual(const std::optional<MarketOrder>& left,
                 const std::optional<MarketOrder>& right) {
  if (left.has_value() != right.has_value()) return false;
  if (!left.has_value()) return true;
  return left->kind == right->kind && left->item == right->item &&
         left->remaining == right->remaining;
}

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

std::pair<int, int> Position(const Farm& farm, int actor) {
  return actor == 0 ? std::pair{farm.farmer_x, farm.farmer_y}
                    : farm.hands[actor - 1];
}

const Tile* TileAt(const Engine& engine, const Farm& farm,
                   std::pair<int, int> position) {
  const auto [x, y] = position;
  const int size = engine.config().board_size;
  if (x < 0 || y < 0 || x >= size || y >= size) return nullptr;
  return &farm.tiles[static_cast<size_t>(y) * size + x];
}

UnitAction* MutableUnit(PlayerAction* action, int actor) {
  return actor == 0 ? &action->farmer : &action->hands[actor - 1];
}

const UnitAction& Unit(const PlayerAction& action, int actor) {
  return actor == 0 ? action.farmer : action.hands[actor - 1];
}

bool IsSell(const std::optional<MarketOrder>& slot, int product) {
  return slot.has_value() && slot->kind == OrderKind::kSell &&
         slot->item >= 0 && slot->item < kNumProducts &&
         (product < 0 || slot->item == product);
}

std::optional<MarketOrder>* FirstSell(PlayerAction* action, int product) {
  for (auto& slot : action->market) {
    if (IsSell(slot, product)) return &slot;
  }
  return nullptr;
}

void AddSell(PlayerAction* action, int product, int64_t quantity) {
  if (auto* existing = FirstSell(action, product); existing != nullptr) {
    (*existing)->remaining =
        std::max<int64_t>(0, (*existing)->remaining) + quantity;
  } else if (static_cast<int>(action->market.size()) < kMaximumOrders) {
    action->market.push_back(
        MarketOrder{OrderKind::kSell, product, quantity});
  }
}

int64_t InventoryTotal(const Inventory& inventory) {
  int64_t total = 0;
  for (const auto& [unused_item, quantity] : inventory.items) {
    static_cast<void>(unused_item);
    total += std::max<int64_t>(0, quantity);
  }
  return total;
}

UnitAction MoveToward(std::pair<int, int> position,
                      std::pair<int, int> target) {
  if (position.first < target.first) {
    return UnitAction{UnitOp::kEast, -1, 1};
  }
  if (position.first > target.first) {
    return UnitAction{UnitOp::kWest, -1, 1};
  }
  if (position.second < target.second) {
    return UnitAction{UnitOp::kSouth, -1, 1};
  }
  if (position.second > target.second) {
    return UnitAction{UnitOp::kNorth, -1, 1};
  }
  return Pass();
}

std::array<std::pair<int, int>, 4> PythonAccessOrder(int board_size) {
  const int half = board_size / 2;
  // CPython 3.11 integer-tuple set order on the official 10x10 board.
  return {{{half - 1, half - 1}, {half, half - 1},
           {half, half}, {half - 1, half}}};
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
    const auto [x, y] = Position(farm, unit);
    if (std::find(access.begin(), access.end(), std::pair{x, y}) ==
        access.end()) {
      continue;
    }
    if (x < 0 || y < 0 || x >= engine.config().board_size ||
        y >= engine.config().board_size) {
      continue;
    }
    const UnitAction request = Unit(action, unit);
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

std::array<int64_t, kNumProducts> SellTotals(const PlayerAction& action) {
  std::array<int64_t, kNumProducts> totals{};
  for (const auto& slot : action.market) {
    if (IsSell(slot)) {
      totals[slot->item] += std::max<int64_t>(0, slot->remaining);
    }
  }
  return totals;
}

bool ActionsEqual(const PlayerAction& left, const PlayerAction& right) {
  if (!UnitsEqual(left.farmer, right.farmer) ||
      left.hands.size() != right.hands.size() ||
      left.market.size() != right.market.size()) {
    return false;
  }
  for (size_t index = 0; index < left.hands.size(); ++index) {
    if (!UnitsEqual(left.hands[index], right.hands[index])) return false;
  }
  for (size_t index = 0; index < left.market.size(); ++index) {
    if (!OrdersEqual(left.market[index], right.market[index])) return false;
  }
  return true;
}

PlayerAction ApplyMarketDelta(PlayerAction action,
                              const PlayerAction& base_action,
                              const PlayerAction& shifted_action) {
  const auto base = SellTotals(base_action);
  const auto shifted = SellTotals(shifted_action);
  for (int product = 0; product < kNumProducts; ++product) {
    const int64_t delta = shifted[product] - base[product];
    if (delta > 0) {
      AddSell(&action, product, delta);
      continue;
    }
    int64_t remaining = -delta;
    if (remaining <= 0) continue;
    std::vector<std::optional<MarketOrder>> kept;
    kept.reserve(action.market.size());
    for (auto slot : action.market) {
      if (remaining > 0 && IsSell(slot, product)) {
        int64_t quantity = std::max<int64_t>(0, slot->remaining);
        const int64_t reduction = std::min(quantity, remaining);
        quantity -= reduction;
        remaining -= reduction;
        if (quantity <= 0) continue;
        slot->remaining = quantity;
      }
      kept.push_back(std::move(slot));
    }
    action.market = std::move(kept);
  }
  if (action.market.size() > kMaximumOrders) {
    action.market.resize(kMaximumOrders);
  }
  return action;
}

}  // namespace kagg::boatlee::detail
