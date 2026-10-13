#include "mugundh/detail.hpp"

#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdlib>
#include <optional>
#include <tuple>
#include <utility>
#include <vector>

namespace kagg::mugundh::detail {
namespace {

constexpr int kIceCreamShop = 3;
constexpr int kPizzaShop = 5;
constexpr int kSmoothieShop = 6;
constexpr int kYarnStore = 7;
constexpr int kMaximumOrders = 10;
constexpr int kWeedReplaySteps = 8;
constexpr int64_t kFixedShedCapacity = 100;

constexpr std::array<int, kNumProducts> kRoomPriority = {
    item::kWool,       item::kMilk,   item::kEgg,
    item::kMelon,      item::kStrawberry, item::kTomato,
    item::kCarrot,     item::kFertilizer, item::kWheat,
};

bool Contains(const std::vector<int>& values, int expected, size_t limit) {
  const size_t stop = std::min(values.size(), limit);
  return std::find(values.begin(), values.begin() + stop, expected) !=
         values.begin() + stop;
}

bool UsesMilk(const std::vector<int>& shops) {
  return Contains(shops, kPizzaShop, 3) ||
         Contains(shops, kIceCreamShop, 3) ||
         Contains(shops, kSmoothieShop, 3);
}

bool LegacyLayout(const Engine& engine, int player, SeatState* state) {
  const int step = engine.step_index();
  if (step == 0) state->legacy_layout.reset();
  if (!state->legacy_layout.has_value() && step >= 24 && step < 72) {
    int wheat = 0;
    int melon = 0;
    int cow = 0;
    int sheep = 0;
    int bare_pasture = 0;
    const Farm& opponent = engine.farm(1 - player);
    for (const Tile& tile : opponent.tiles) {
      if (tile.kind == TileKind::kPlant) {
        if (tile.crop == item::kWheat) ++wheat;
        if (tile.crop == item::kMelon) ++melon;
      } else if (tile.kind == TileKind::kStructure && tile.has_animal) {
        if (tile.animal == 1) ++cow;
        if (tile.animal == 2) ++sheep;
      } else if (tile.kind == TileKind::kStructure &&
                 tile.structure == StructureKind::kPasture) {
        ++bare_pasture;
      }
    }
    state->legacy_layout =
        wheat == 5 && melon == 5 && cow == 1 && sheep == 4 &&
        bare_pasture == 0 && opponent.money <= 12.0;
  }
  return state->legacy_layout.value_or(false);
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

bool IsSell(const std::optional<MarketOrder>& slot, int product = -1) {
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
  // CPython's deterministic iteration order for the integer tuple set used by
  // the frozen notebook on the official 10x10 board: NW, NE, SE, SW.
  return {{{half - 1, half - 1}, {half, half - 1},
           {half, half}, {half - 1, half}}};
}

std::pair<int, int> NearestAccess(std::pair<int, int> position,
                                  int board_size) {
  const auto access = PythonAccessOrder(board_size);
  std::pair<int, int> best = access[0];
  int best_distance = std::abs(position.first - best.first) +
                      std::abs(position.second - best.second);
  for (size_t index = 1; index < access.size(); ++index) {
    const int distance = std::abs(position.first - access[index].first) +
                         std::abs(position.second - access[index].second);
    if (distance < best_distance) {
      best = access[index];
      best_distance = distance;
    }
  }
  return best;
}

int64_t InventoryTotal(const Inventory& inventory) {
  int64_t total = 0;
  for (const auto& [unused_item, quantity] : inventory.items) {
    static_cast<void>(unused_item);
    total += std::max<int64_t>(0, quantity);
  }
  return total;
}

}  // namespace

Tape SelectTape(const Engine& engine, int player, SeatState* state) {
  const auto& shops = engine.town_shops();
  int route;
  if (!shops.empty() && shops[0] == kYarnStore) {
    route = 3;
  } else if (Contains(shops, kYarnStore, 2)) {
    route = 4;
  } else if (Contains(shops, kYarnStore, 3)) {
    route = 2;
  } else if (UsesMilk(shops)) {
    route = 0;
  } else {
    route = 1;
  }
  if (LegacyLayout(engine, player, state)) route += 5;
  return static_cast<Tape>(route);
}

PlayerAction ApplyWeedRepair(const Portfolio& portfolio, const Engine& engine,
                             int player, Tape tape, PlayerAction action,
                             RepairState* state) {
  AlignHands(engine, player, &action);
  const int step = engine.step_index();
  const Farm& farm = engine.farm(player);
  const int unit_count = 1 + static_cast<int>(farm.hands.size());
  state->active.resize(unit_count);
  for (int actor = 0; actor < unit_count; ++actor) {
    RepairTransaction& transaction = state->active[actor];
    if (!transaction.active) continue;
    const int age = step - transaction.start;
    if (age == 1) {
      *MutableUnit(&action, actor) = transaction.intended;
    } else if (age >= 2 && age <= 1 + kWeedReplaySteps) {
      *MutableUnit(&action, actor) =
          portfolio.unit_action(tape, step - 1, actor);
    } else {
      transaction = RepairTransaction{};
    }
  }
  for (int actor = 0; actor < unit_count; ++actor) {
    RepairTransaction& transaction = state->active[actor];
    const UnitAction intended = Unit(action, actor);
    if (transaction.active ||
        (intended.op != UnitOp::kBuildPasture &&
         intended.op != UnitOp::kPlant)) {
      continue;
    }
    const Tile* tile = TileAt(engine, farm, Position(farm, actor));
    if (tile == nullptr || tile->kind != TileKind::kWeed) continue;
    transaction.active = true;
    transaction.start = step;
    transaction.intended = intended;
    *MutableUnit(&action, actor) = UnitAction{UnitOp::kDig, -1, 1};
  }
  AlignHands(engine, player, &action);
  return action;
}

PlayerAction ApplyRoomEvac(const Engine& engine, int player,
                           PlayerAction action, RoomState* state) {
  const int step = engine.step_index();
  if (step < 648) return action;
  const int turns_per_day = std::max(1, engine.config().turns_per_day);
  const int hour = step % turns_per_day;
  const int day = step / turns_per_day;
  if (state->day != day) {
    *state = RoomState{};
    state->day = day;
  }
  if (hour < 21) return action;
  AlignHands(engine, player, &action);
  const Farm& farm = engine.farm(player);
  const PrivateState& priv = engine.priv(player);
  const int unit_count = 1 + static_cast<int>(farm.hands.size());
  int64_t total = 0;
  for (const int64_t quantity : priv.shed) {
    total += std::max<int64_t>(0, quantity);
  }
  for (const Inventory& inventory : priv.inventories) {
    total += InventoryTotal(inventory);
  }
  struct Candidate {
    int distance;
    int64_t saleable;
    int actor;
    std::pair<int, int> target;
  };
  if (hour == 21 && !state->active && total > kFixedShedCapacity) {
    std::vector<Candidate> candidates;
    for (int actor = 0; actor < unit_count &&
                        actor < static_cast<int>(priv.inventories.size());
         ++actor) {
      int64_t saleable = 0;
      for (int product = 0; product < kNumProducts; ++product) {
        saleable += std::max<int64_t>(
            0, priv.inventories[actor].Get(product));
      }
      if (saleable <= 0 || Unit(action, actor).op != UnitOp::kPass) continue;
      const auto position = Position(farm, actor);
      const auto target =
          NearestAccess(position, engine.config().board_size);
      const int distance = std::abs(position.first - target.first) +
                           std::abs(position.second - target.second);
      if (distance <= 2) {
        candidates.push_back(Candidate{distance, saleable, actor, target});
      }
    }
    if (!candidates.empty()) {
      const auto best = std::min_element(
          candidates.begin(), candidates.end(),
          [](const Candidate& left, const Candidate& right) {
            return std::tuple{left.distance, -left.saleable, left.actor,
                              left.target} <
                   std::tuple{right.distance, -right.saleable, right.actor,
                              right.target};
          });
      state->active = true;
      state->actor = best->actor;
      state->target = best->target;
    }
  }
  if (!state->active) return action;
  const int actor = state->actor;
  if (actor < 0 || actor >= unit_count ||
      actor >= static_cast<int>(priv.inventories.size())) {
    state->active = false;
    return action;
  }
  const auto position = Position(farm, actor);
  if (position != state->target) {
    *MutableUnit(&action, actor) = MoveToward(position, state->target);
  } else if (hour == 23) {
    *MutableUnit(&action, actor) = UnitAction{UnitOp::kDrop, -1, 1};
    std::array<int64_t, kNumProducts> existing_sales{};
    for (const auto& slot : action.market) {
      if (IsSell(slot)) {
        existing_sales[slot->item] +=
            std::max<int64_t>(0, slot->remaining);
      }
    }
    int64_t needed = std::max<int64_t>(0, total - kFixedShedCapacity);
    const Inventory& inventory = priv.inventories[actor];
    for (const int product : kRoomPriority) {
      const int64_t available = std::max<int64_t>(
          0, inventory.Get(product) - existing_sales[product]);
      const int64_t quantity = std::min(needed, available);
      if (quantity <= 0) continue;
      if (auto* existing = FirstSell(&action, product); existing != nullptr) {
        (*existing)->remaining += quantity;
      } else if (static_cast<int>(action.market.size()) < kMaximumOrders) {
        action.market.push_back(
            MarketOrder{OrderKind::kSell, product, quantity});
      } else {
        continue;
      }
      needed -= quantity;
      if (needed <= 0) break;
    }
  }
  return action;
}

PlayerAction ApplyRoomGuard(const Engine& engine, int player,
                            PlayerAction action) {
  if (engine.step_index() % 24 != 23) return action;
  const Farm& farm = engine.farm(player);
  const PrivateState& priv = engine.priv(player);
  const int unit_count = 1 + static_cast<int>(farm.hands.size());
  int64_t shed_total = 0;
  for (const int64_t quantity : priv.shed) {
    shed_total += std::max<int64_t>(0, quantity);
  }
  int64_t carried = 0;
  for (const Inventory& inventory : priv.inventories) {
    carried += InventoryTotal(inventory);
  }
  int64_t produced = 0;
  int64_t consumed = 0;
  for (int actor = 0; actor < unit_count; ++actor) {
    const UnitAction& order = Unit(action, actor);
    const Tile* tile = TileAt(engine, farm, Position(farm, actor));
    if (order.op == UnitOp::kHarvest && tile != nullptr) {
      produced += std::max(0, tile->yield_units);
    } else if (order.op == UnitOp::kCollectFertilizer && tile != nullptr &&
               tile->fertilizer_available) {
      ++produced;
    } else if (order.op == UnitOp::kFeed ||
               order.op == UnitOp::kFertilize) {
      ++consumed;
    } else if (order.op == UnitOp::kPlace &&
               order.arg >= item::kGoose && order.arg < kNumItems) {
      ++consumed;
    }
  }
  std::array<int64_t, kNumProducts> planned_sells{};
  int64_t planned_buys = 0;
  for (const auto& slot : action.market) {
    if (!slot.has_value()) continue;
    const int64_t quantity = std::max<int64_t>(0, slot->remaining);
    if (slot->kind == OrderKind::kSell && slot->item >= 0 &&
        slot->item < kNumProducts) {
      planned_sells[slot->item] += quantity;
    } else if (slot->kind == OrderKind::kBuyProduct ||
               slot->kind == OrderKind::kBuyAnimal) {
      planned_buys += quantity;
    }
  }
  int64_t actual_existing_sells = 0;
  for (int product = 0; product < kNumProducts; ++product) {
    actual_existing_sells +=
        std::min(priv.shed[product], planned_sells[product]);
  }
  int64_t needed = std::max<int64_t>(
      0, shed_total + carried + produced - consumed + planned_buys -
             actual_existing_sells - kFixedShedCapacity);
  if (needed <= 0) return action;
  for (const int product : kRoomPriority) {
    const int64_t available =
        std::max<int64_t>(0, priv.shed[product] - planned_sells[product]);
    const int64_t quantity = std::min(needed, available);
    if (quantity <= 0) continue;
    if (auto* existing = FirstSell(&action, product); existing != nullptr) {
      (*existing)->remaining += quantity;
    } else if (static_cast<int>(action.market.size()) < kMaximumOrders) {
      action.market.push_back(
          MarketOrder{OrderKind::kSell, product, quantity});
    } else {
      continue;
    }
    planned_sells[product] += quantity;
    needed -= quantity;
    if (needed <= 0) break;
  }
  return action;
}

}  // namespace kagg::mugundh::detail
