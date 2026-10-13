#include "boatlee/detail.hpp"

#include <algorithm>
#include <array>
#include <cstdint>
#include <cstring>
#include <cstdlib>
#include <optional>
#include <tuple>
#include <utility>
#include <vector>

namespace kagg::boatlee::detail {
namespace {

constexpr int kBakery = 0;
constexpr int kBrunchSpot = 1;
constexpr int kFarmersMarket = 2;
constexpr int kIceCreamShop = 3;
constexpr int kPizzaShop = 5;
constexpr int kYarnStore = 7;
constexpr int kTomatoTarget = 3;

constexpr std::array<int, kNumProducts> kRoomPriority = {
    item::kWool, item::kMilk, item::kEgg, item::kMelon,
    item::kStrawberry, item::kTomato, item::kCarrot,
    item::kFertilizer, item::kWheat};

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

UnitAction TerminalMoveToward(const Engine& engine, const Farm& farm,
                              std::pair<int, int> position,
                              std::pair<int, int> target) {
  const int x = position.first;
  const int y = position.second;
  std::array<std::pair<UnitOp, std::pair<int, int>>, 2> choices{};
  size_t choice_count = 0;
  if (target.first < x) {
    choices[choice_count++] = {UnitOp::kWest, {x - 1, y}};
  } else if (target.first > x) {
    choices[choice_count++] = {UnitOp::kEast, {x + 1, y}};
  }
  if (target.second < y) {
    choices[choice_count++] = {UnitOp::kNorth, {x, y - 1}};
  } else if (target.second > y) {
    choices[choice_count++] = {UnitOp::kSouth, {x, y + 1}};
  }
  for (size_t index = 0; index < choice_count; ++index) {
    const auto& [operation, next] = choices[index];
    const Tile* tile = TileAt(engine, farm, next);
    if (tile != nullptr && tile->kind != TileKind::kLocked) {
      return UnitAction{operation, -1, 1};
    }
  }
  return Pass();
}

bool OpponentHasGoose(const Engine& engine, int player) {
  for (const Tile& tile : engine.farm(1 - player).tiles) {
    if (tile.kind == TileKind::kStructure &&
        (tile.structure == StructureKind::kCoop ||
         (tile.has_animal && tile.animal == 0))) {
      return true;
    }
  }
  return false;
}

}  // namespace

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
    int64_t negative_saleable;
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
        saleable +=
            std::max<int64_t>(0, priv.inventories[actor].Get(product));
      }
      if (saleable <= 0 || Unit(action, actor).op != UnitOp::kPass) continue;
      const auto position = Position(farm, actor);
      const auto target =
          NearestAccess(position, engine.config().board_size);
      const int distance = std::abs(position.first - target.first) +
                           std::abs(position.second - target.second);
      if (distance <= 2) {
        candidates.push_back(
            Candidate{distance, -saleable, actor, target});
      }
    }
    if (!candidates.empty()) {
      const auto best = std::min_element(
          candidates.begin(), candidates.end(),
          [](const Candidate& left, const Candidate& right) {
            return std::tuple{left.distance, left.negative_saleable,
                              left.actor, left.target} <
                   std::tuple{right.distance, right.negative_saleable,
                              right.actor, right.target};
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
    auto existing_sales = SellTotals(action);
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
    } else if (order.op == UnitOp::kPlace && order.arg >= item::kGoose &&
               order.arg < kNumItems) {
      ++consumed;
    }
  }
  auto planned_sells = SellTotals(action);
  int64_t planned_buys = 0;
  for (const auto& slot : action.market) {
    if (!slot.has_value()) continue;
    const int64_t quantity = std::max<int64_t>(0, slot->remaining);
    if (slot->kind == OrderKind::kBuyProduct ||
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

PlayerAction ApplyTomatoPair(const Engine& engine, int player,
                             PlayerAction action, TomatoState* state) {
  const int step = engine.step_index();
  if (step == 216) {
    int matching = 0;
    const auto& shops = engine.town_shops();
    for (size_t index = 0; index < std::min<size_t>(3, shops.size()); ++index) {
      matching += shops[index] == kFarmersMarket || shops[index] == kPizzaShop;
    }
    state->active = matching >= 2;
  }
  if (!state->active) return action;
  if (step == 264) {
    for (auto& slot : action.market) {
      if (slot.has_value() && slot->kind == OrderKind::kBuySeed &&
          slot->item == item::kStrawberry &&
          slot->remaining >= kTomatoTarget) {
        slot->remaining -= kTomatoTarget;
        state->seed_debt = kTomatoTarget;
        break;
      }
    }
  }
  if (step == 265 && state->seed_debt > 0 &&
      static_cast<int>(action.market.size()) < kMaximumOrders) {
    action.market.push_back(MarketOrder{OrderKind::kBuySeed, item::kTomato,
                                        state->seed_debt});
    state->seed_debt = 0;
  }
  AlignHands(engine, player, &action);
  const PrivateState& priv = engine.priv(player);
  const int unit_count = 1 + static_cast<int>(action.hands.size());
  if (step >= 271 && step <= 286) {
    int remaining =
        std::max(0, kTomatoTarget - state->scheduled_plants);
    int changed = 0;
    for (int actor = 0; actor < unit_count && changed < remaining; ++actor) {
      UnitAction* order = MutableUnit(&action, actor);
      if (order->op == UnitOp::kPlant &&
          order->arg == item::kStrawberry) {
        order->arg = item::kTomato;
        ++changed;
      }
    }
    state->scheduled_plants += changed;
  }
  for (int actor = 0; actor < unit_count &&
                      actor < static_cast<int>(priv.inventories.size());
       ++actor) {
    UnitAction* order = MutableUnit(&action, actor);
    if (order->op == UnitOp::kPlace &&
        order->arg == item::kStrawberry &&
        priv.inventories[actor].Get(item::kTomato) > 0) {
      order->arg = item::kTomato;
    }
  }
  std::vector<std::optional<MarketOrder>> market;
  market.reserve(action.market.size());
  for (auto slot : action.market) {
    if (!IsSell(slot, item::kTomato)) market.push_back(std::move(slot));
  }
  action.market = std::move(market);
  return action;
}

PlayerAction ApplyEggPair(const Engine& engine, int player,
                          PlayerAction action, EggState* state) {
  const int step = engine.step_index();
  const auto& shops = engine.town_shops();
  if (step == 264) {
    const size_t count = std::min<size_t>(3, shops.size());
    int egg_shops = 0;
    bool yarn = false;
    for (size_t index = 0; index < count; ++index) {
      egg_shops += shops[index] == kBakery || shops[index] == kBrunchSpot;
      yarn = yarn || shops[index] == kYarnStore;
    }
    const bool three_bakeries =
        count == 3 && shops[0] == kBakery && shops[1] == kBakery &&
        shops[2] == kBakery;
    const bool ice_bakery_bakery =
        count == 3 && shops[0] == kIceCreamShop &&
        shops[1] == kBakery && shops[2] == kBakery;
    const bool mirrored_brunch =
        count == 3 && shops[0] == kBrunchSpot &&
        shops[1] == kBrunchSpot && shops[2] == kFarmersMarket &&
        CloneDistance(engine) == 0;
    state->active = egg_shops >= 2 && !yarn && !three_bakeries &&
                    !ice_bakery_bakery && !mirrored_brunch &&
                    !OpponentHasGoose(engine, player);
  }
  if (!state->active || step < 264 || step > 275) return action;
  AlignHands(engine, player, &action);
  const int unit_count = 1 + static_cast<int>(action.hands.size());
  for (int actor = 0; actor < unit_count; ++actor) {
    UnitAction* order = MutableUnit(&action, actor);
    if ((step == 266 || step == 269) &&
        order->op == UnitOp::kBuildPasture) {
      order->op = UnitOp::kBuildCoop;
    } else if (step >= 267 &&
               (order->op == UnitOp::kPickup ||
                order->op == UnitOp::kPlace) &&
               (order->arg == item::kCow || order->arg == item::kSheep)) {
      order->arg = item::kGoose;
    }
  }
  if (step == 264) {
    for (auto& slot : action.market) {
      if (slot.has_value() && slot->kind == OrderKind::kBuyAnimal &&
          (slot->item == 1 || slot->item == 2)) {
        slot->item = 0;
      }
    }
  }
  return action;
}

PlayerAction TerminalAction(const Engine& engine, int player) {
  const Farm& farm = engine.farm(player);
  const PrivateState& priv = engine.priv(player);
  const int size = engine.config().board_size;
  const int unit_count = 1 + static_cast<int>(farm.hands.size());
  const auto access = PythonAccessOrder(size);
  std::vector<std::pair<int, int>> available;
  for (int y = 0; y < size; ++y) {
    for (int x = 0; x < size; ++x) {
      const Tile& tile = farm.tiles[static_cast<size_t>(y) * size + x];
      if (tile.kind != TileKind::kLocked && tile.yield_units > 0) {
        available.push_back({x, y});
      }
    }
  }
  PlayerAction action;
  action.hands.resize(farm.hands.size(), Pass());
  std::array<int64_t, kNumProducts> pending{};
  for (int actor = 0; actor < unit_count; ++actor) {
    const auto position = Position(farm, actor);
    const Inventory* inventory =
        actor < static_cast<int>(priv.inventories.size())
            ? &priv.inventories[actor]
            : nullptr;
    const int64_t load = inventory == nullptr ? 0 : InventoryTotal(*inventory);
    const bool at_shed =
        std::find(access.begin(), access.end(), position) != access.end();
    const Tile* tile = TileAt(engine, farm, position);
    UnitAction order = Pass();
    if (load > 0 && at_shed) {
      order = UnitAction{UnitOp::kDrop, -1, 1};
      for (const auto& [product, quantity] : inventory->items) {
        if (product >= 0 && product < kNumProducts) {
          pending[product] += std::max<int64_t>(0, quantity);
        }
      }
    } else if (tile != nullptr && tile->kind != TileKind::kLocked &&
               tile->yield_units > 0) {
      order = UnitAction{UnitOp::kHarvest, -1, 1};
      available.erase(std::remove(available.begin(), available.end(), position),
                      available.end());
    } else if (load > 0) {
      const auto target = NearestAccess(position, size);
      order = TerminalMoveToward(engine, farm, position, target);
    } else if (!available.empty()) {
      const auto target = std::min_element(
          available.begin(), available.end(),
          [&](const auto& left, const auto& right) {
            const int left_distance =
                std::abs(left.first - position.first) +
                std::abs(left.second - position.second);
            const int right_distance =
                std::abs(right.first - position.first) +
                std::abs(right.second - position.second);
            return std::tuple{left_distance, left.second, left.first} <
                   std::tuple{right_distance, right.second, right.first};
          });
      const auto target_value = *target;
      available.erase(target);
      order = TerminalMoveToward(engine, farm, position, target_value);
    } else if (tile != nullptr && tile->kind != TileKind::kLocked &&
               tile->fertilizer_available) {
      order = UnitAction{UnitOp::kCollectFertilizer, -1, 1};
    }
    *MutableUnit(&action, actor) = order;
  }
  std::array<int64_t, kNumProducts> shed{};
  for (int product = 0; product < kNumProducts; ++product) {
    shed[product] = priv.shed[product] + pending[product];
  }
  struct Sale {
    int64_t value;
    int product;
    int64_t quantity;
  };
  std::vector<Sale> sales;
  for (int product = 0; product < kNumProducts; ++product) {
    if (shed[product] > 0) {
      sales.push_back(Sale{shed[product] * engine.market().prices[product],
                           product, shed[product]});
    }
  }
  std::sort(sales.begin(), sales.end(),
            [](const Sale& left, const Sale& right) {
              if (left.value != right.value) return left.value > right.value;
              const int names = std::strcmp(kItemNames[left.product],
                                            kItemNames[right.product]);
              if (names != 0) return names > 0;
              return left.quantity > right.quantity;
            });
  for (size_t index = 0;
       index < std::min<size_t>(kMaximumOrders, sales.size()); ++index) {
    action.market.push_back(MarketOrder{OrderKind::kSell,
                                        sales[index].product,
                                        sales[index].quantity});
  }
  return action;
}

}  // namespace kagg::boatlee::detail
