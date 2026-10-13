#include "programs/session.hpp"

#include <algorithm>
#include <cmath>
#include <limits>
#include <stdexcept>
#include <utility>

#include "market_phase.hpp"

namespace kagg::programs {
namespace {

std::pair<int, int> UnitPosition(const Farm& farm, int unit_index) {
  if (unit_index == 0) return {farm.farmer_x, farm.farmer_y};
  return farm.hands.at(static_cast<size_t>(unit_index - 1));
}

UnitAction MoveToward(int x, int y, int target_x, int target_y) {
  if (x < target_x) return UnitAction{UnitOp::kEast, -1, 1};
  if (x > target_x) return UnitAction{UnitOp::kWest, -1, 1};
  if (y < target_y) return UnitAction{UnitOp::kSouth, -1, 1};
  if (y > target_y) return UnitAction{UnitOp::kNorth, -1, 1};
  return UnitAction{UnitOp::kPass, -1, 1};
}

std::pair<int, int> NextPosition(int x, int y, const UnitAction& action) {
  switch (action.op) {
    case UnitOp::kNorth:
      --y;
      break;
    case UnitOp::kSouth:
      ++y;
      break;
    case UnitOp::kEast:
      ++x;
      break;
    case UnitOp::kWest:
      --x;
      break;
    default:
      break;
  }
  return {x, y};
}

std::pair<int, int> NearestShed(int x, int y, int board_size) {
  const auto access = ShedAccessTiles(board_size);
  auto best = access.front();
  int best_distance = std::abs(x - best.first) + std::abs(y - best.second);
  for (size_t index = 1; index < access.size(); ++index) {
    const int distance = std::abs(x - access[index].first) +
                         std::abs(y - access[index].second);
    if (distance < best_distance) {
      best = access[index];
      best_distance = distance;
    }
  }
  return best;
}

int64_t InventoryCount(const PrivateState& priv, int unit_index, int item_index) {
  if (unit_index < 0 ||
      unit_index >= static_cast<int>(priv.inventories.size()) ||
      item_index < 0 || item_index >= kNumItems) {
    return 0;
  }
  return priv.inventories[unit_index].Get(item_index);
}

int64_t InventoryTotal(const PrivateState& priv, int unit_index) {
  if (unit_index < 0 ||
      unit_index >= static_cast<int>(priv.inventories.size())) {
    return 0;
  }
  int64_t total = 0;
  for (const auto& [item_index, count] : priv.inventories[unit_index].items) {
    static_cast<void>(item_index);
    total += count;
  }
  return total;
}

bool IsAnimalTile(const Tile& tile) {
  return tile.kind == TileKind::kStructure && tile.has_animal;
}

bool IsHarvestable(const Tile& tile, int day) {
  if (tile.yield_units <= 0) return false;
  if (tile.kind == TileKind::kPlant) {
    return day - tile.planted_day >= kCrops[tile.crop].first_yield_day;
  }
  return IsAnimalTile(tile);
}

bool Targeted(Task task) {
  return task != Task::kWait;
}

}  // namespace

bool Session::CanKeep(int unit_index) const {
  if (unit_index < 0 || unit_index >= unit_count_) return false;
  if (forced_water_targets_[unit_index] >= 0) return true;
  return options_[unit_index].has_value() &&
         ValidateOption(*options_[unit_index], unit_index);
}

int Session::FindLaterWaterer(int target, int unit_index) const {
  for (int later = unit_index + 1; later < unit_count_; ++later) {
    if (forced_water_targets_[later] >= 0) continue;
    const auto [x, y] = UnitPosition(shadow_farm_, later);
    if (target == y * config_.board_size + x) return later;
  }
  return -1;
}

bool Session::ValidateOption(const Option& option, int unit_index) const {
  if (option.argument < 0 || option.argument >= kArgumentCount ||
      option.exact_quantity < 1) {
    return false;
  }
  const int tiles = config_.board_size * config_.board_size;
  if (Targeted(option.task) &&
      (option.target < 0 || option.target >= tiles)) {
    return false;
  }
  if ((option.task == Task::kFetch || option.task == Task::kStore ||
       option.task == Task::kStoreAll) &&
      !IsShedAdjacent(option.target % config_.board_size,
                      option.target / config_.board_size,
                      config_.board_size)) {
    return false;
  }
  if (option.task == Task::kFetch) {
    if (option.argument >= kNumItems) return false;
  }
  if (option.task == Task::kStore) {
    if (option.argument >= kNumItems) return false;
  }
  if (option.task == Task::kFetch || option.task == Task::kStore) {
    const int64_t maximum =
        UnitQuantityMaximum(option.task, option.argument, unit_index);
    if (maximum < 1) return false;
    switch (option.quantity_mode) {
      case QuantityMode::kOne:
      case QuantityMode::kAllAvailable:
        return true;
      case QuantityMode::kPlanDeficit:
        return option.task == Task::kFetch;
      case QuantityMode::kExact:
        return option.exact_quantity <= maximum;
      case QuantityMode::kMaxAffordable:
        return false;
    }
    return false;
  }
  if (option.task == Task::kStoreAll) {
    return InventoryTotal(shadow_priv_, unit_index) > 0;
  }
  if (option.task == Task::kWait) return true;
  if (option.task == Task::kGoTo) {
    const auto [x, y] = UnitPosition(shadow_farm_, unit_index);
    return option.target != y * config_.board_size + x;
  }

  const Tile& tile = shadow_farm_.tiles[option.target];
  switch (option.task) {
    case Task::kSafePlant:
      if (option.phase == OptionPhase::kWater) {
        return tile.kind == TileKind::kPlant && !tile.watered_today;
      }
      if (option.argument >= kNumCrops || tile.kind != TileKind::kEmpty ||
          shadow_priv_.seeds[option.argument] <= 0) {
        return false;
      }
      if (step_ % config_.turns_per_day == config_.turns_per_day - 1) {
        const auto [x, y] = UnitPosition(shadow_farm_, unit_index);
        if (option.target == y * config_.board_size + x &&
            FindLaterWaterer(option.target, unit_index) < 0) {
          return false;
        }
      }
      return true;
    case Task::kPlant:
      return option.argument < kNumCrops && tile.kind == TileKind::kEmpty &&
             shadow_priv_.seeds[option.argument] > 0;
    case Task::kWater:
      return tile.kind == TileKind::kPlant && !tile.watered_today;
    case Task::kHarvest:
      return IsHarvestable(tile, day_);
    case Task::kFertilize:
      return tile.kind == TileKind::kPlant &&
             (InventoryCount(shadow_priv_, unit_index, item::kFertilizer) > 0 ||
              shadow_priv_.shed[item::kFertilizer] > 0);
    case Task::kDig:
      return tile.kind != TileKind::kEmpty && tile.kind != TileKind::kLocked &&
             !(tile.kind == TileKind::kStructure && tile.has_animal);
    case Task::kBuild:
      return (option.argument == kCoopArgument ||
              option.argument == kPastureArgument) &&
             tile.kind == TileKind::kEmpty;
    case Task::kDeployAnimal: {
      if (option.argument < item::kGoose || option.argument >= kNumItems) {
        return false;
      }
      const int animal = option.argument - item::kGoose;
      const bool supply =
          InventoryCount(shadow_priv_, unit_index, option.argument) > 0 ||
          shadow_priv_.shed[option.argument] > 0;
      const bool target = tile.kind == TileKind::kEmpty ||
                          (tile.kind == TileKind::kStructure &&
                           !tile.has_animal &&
                           tile.structure == kAnimals[animal].structure);
      return supply && target;
    }
    case Task::kFeed:
      return IsAnimalTile(tile) && !tile.fed_today &&
             (InventoryCount(shadow_priv_, unit_index, item::kWheat) > 0 ||
              shadow_priv_.shed[item::kWheat] > 0);
    case Task::kCare:
      return IsAnimalTile(tile) && !tile.cared_today;
    case Task::kCollect:
      return IsAnimalTile(tile) && tile.fertilizer_available;
    case Task::kFetch:
    case Task::kStore:
    case Task::kStoreAll:
    case Task::kGoTo:
    case Task::kWait:
      break;
  }
  return false;
}

UnitAction Session::CompileOption(int unit_index, bool* completed) {
  if (!options_[unit_index] || !ValidateOption(*options_[unit_index], unit_index)) {
    throw std::logic_error("conditional program attempted to keep an invalid option");
  }
  Option& option = *options_[unit_index];
  const auto [x, y] = UnitPosition(shadow_farm_, unit_index);

  int required_item = -1;
  if (option.task == Task::kFertilize) required_item = item::kFertilizer;
  if (option.task == Task::kFeed) required_item = item::kWheat;
  if (option.task == Task::kDeployAnimal) required_item = option.argument;
  if (required_item >= 0 &&
      InventoryCount(shadow_priv_, unit_index, required_item) <= 0) {
    const auto [shed_x, shed_y] = NearestShed(x, y, config_.board_size);
    if (x != shed_x || y != shed_y) {
      option.phase = OptionPhase::kFetch;
      return MoveToward(x, y, shed_x, shed_y);
    }
    option.phase = OptionPhase::kApproach;
    return UnitAction{UnitOp::kPickup, required_item, 1};
  }

  if (option.task == Task::kWait) {
    return UnitAction{UnitOp::kPass, -1, 1};
  }

  if (option.task == Task::kFetch || option.task == Task::kStore ||
      option.task == Task::kStoreAll) {
    const int shed_x = option.target % config_.board_size;
    const int shed_y = option.target / config_.board_size;
    if (x != shed_x || y != shed_y) {
      return MoveToward(x, y, shed_x, shed_y);
    }
    if (option.task == Task::kStoreAll) {
      *completed = true;
      return UnitAction{UnitOp::kDrop, -1, 1};
    }
    const int64_t quantity = ResolveUnitQuantity(
        option.task, option.argument, option.quantity_mode,
        option.exact_quantity, unit_index);
    *completed = true;
    return UnitAction{
        option.task == Task::kFetch ? UnitOp::kPickup : UnitOp::kPlace,
        option.argument,
        quantity};
  }

  const int target_x = option.target % config_.board_size;
  const int target_y = option.target / config_.board_size;
  if (x != target_x || y != target_y) {
    const UnitAction movement = MoveToward(x, y, target_x, target_y);
    if (option.task == Task::kGoTo &&
        NextPosition(x, y, movement) == std::pair(target_x, target_y)) {
      *completed = true;
    }
    return movement;
  }

  switch (option.task) {
    case Task::kSafePlant:
      if (option.phase == OptionPhase::kWater) {
        *completed = true;
        return UnitAction{UnitOp::kWater, -1, 1};
      }
      option.phase = OptionPhase::kWater;
      if (step_ % config_.turns_per_day == config_.turns_per_day - 1) {
        const int waterer = FindLaterWaterer(option.target, unit_index);
        if (waterer < 0) {
          throw std::logic_error("last-hour SAFE_PLANT lost its reserved waterer");
        }
        forced_water_targets_[waterer] = option.target;
        forced_water_owners_[waterer] = unit_index;
      }
      return UnitAction{UnitOp::kPlant, option.argument, 1};
    case Task::kPlant:
      *completed = true;
      return UnitAction{UnitOp::kPlant, option.argument, 1};
    case Task::kWater:
      *completed = true;
      return UnitAction{UnitOp::kWater, -1, 1};
    case Task::kHarvest:
      *completed = true;
      return UnitAction{UnitOp::kHarvest, -1, 1};
    case Task::kFertilize:
      *completed = true;
      return UnitAction{UnitOp::kFertilize, -1, 1};
    case Task::kDig:
      *completed = true;
      return UnitAction{UnitOp::kDig, -1, 1};
    case Task::kBuild:
      *completed = true;
      return UnitAction{
          option.argument == kCoopArgument ? UnitOp::kBuildCoop
                                           : UnitOp::kBuildPasture,
          -1,
          1};
    case Task::kDeployAnimal: {
      const Tile& tile = shadow_farm_.tiles[option.target];
      const int animal = option.argument - item::kGoose;
      if (tile.kind == TileKind::kEmpty) {
        option.phase = OptionPhase::kPlace;
        return UnitAction{
            kAnimals[animal].structure == StructureKind::kCoop
                ? UnitOp::kBuildCoop
                : UnitOp::kBuildPasture,
            -1,
            1};
      }
      *completed = true;
      return UnitAction{UnitOp::kPlace, option.argument, 1};
    }
    case Task::kFeed:
      *completed = true;
      return UnitAction{UnitOp::kFeed, -1, 1};
    case Task::kCare:
      *completed = true;
      return UnitAction{UnitOp::kCare, -1, 1};
    case Task::kCollect:
      *completed = true;
      return UnitAction{UnitOp::kCollectFertilizer, -1, 1};
    case Task::kGoTo:
      *completed = true;
      return UnitAction{UnitOp::kPass, -1, 1};
    case Task::kFetch:
    case Task::kStore:
    case Task::kStoreAll:
      throw std::logic_error("logistics option escaped its compiler branch");
    case Task::kWait:
      throw std::logic_error("WAIT option escaped its compiler branch");
  }
  throw std::logic_error("conditional program option is unknown");
}

UnitAction Session::CompileForcedWater(int unit_index, bool* completed) {
  *completed = false;
  const int target = forced_water_targets_[unit_index];
  const int owner = forced_water_owners_[unit_index];
  const auto [x, y] = UnitPosition(shadow_farm_, unit_index);
  if (target < 0 || target >= config_.board_size * config_.board_size ||
      target != y * config_.board_size + x) {
    throw std::logic_error("SAFE_PLANT water reservation changed position");
  }
  const Tile& tile = shadow_farm_.tiles[target];
  if (tile.kind != TileKind::kPlant || tile.watered_today) {
    throw std::logic_error("SAFE_PLANT water reservation lost its fresh plant");
  }
  if (owner >= 0 && owner < static_cast<int>(options_.size())) {
    options_[owner].reset();
  }
  forced_water_targets_[unit_index] = -1;
  forced_water_owners_[unit_index] = -1;
  return UnitAction{UnitOp::kWater, -1, 1};
}

UnitAction Session::CompileRaw(const Selection& selection) const {
  const RawOperation operation =
      static_cast<RawOperation>(selection.raw_operation);
  UnitAction result;
  switch (operation) {
    case RawOperation::kPickup:
      result = UnitAction{UnitOp::kPickup, static_cast<int>(selection.argument), 1};
      break;
    case RawOperation::kDrop:
      return UnitAction{UnitOp::kDrop, -1, 1};
    case RawOperation::kPlace:
      result = UnitAction{UnitOp::kPlace, static_cast<int>(selection.argument), 1};
      break;
    case RawOperation::kPlant:
      return UnitAction{UnitOp::kPlant, static_cast<int>(selection.argument), 1};
    case RawOperation::kWater:
      return UnitAction{UnitOp::kWater, -1, 1};
    case RawOperation::kHarvest:
      return UnitAction{UnitOp::kHarvest, -1, 1};
    case RawOperation::kFertilize:
      return UnitAction{UnitOp::kFertilize, -1, 1};
    case RawOperation::kDig:
      return UnitAction{UnitOp::kDig, -1, 1};
    case RawOperation::kBuildCoop:
      return UnitAction{UnitOp::kBuildCoop, -1, 1};
    case RawOperation::kBuildPasture:
      return UnitAction{UnitOp::kBuildPasture, -1, 1};
    case RawOperation::kFeed:
      return UnitAction{UnitOp::kFeed, -1, 1};
    case RawOperation::kCollectFertilizer:
      return UnitAction{UnitOp::kCollectFertilizer, -1, 1};
    case RawOperation::kCare:
      return UnitAction{UnitOp::kCare, -1, 1};
  }
  const int argument = static_cast<int>(selection.argument);
  int64_t maximum = 0;
  if (operation == RawOperation::kPickup) {
    maximum = shadow_priv_.shed[argument];
  } else {
    const auto [x, y] = UnitPosition(shadow_farm_, unit_index_);
    const Tile& tile = shadow_farm_.tiles[y * config_.board_size + x];
    if (argument >= item::kGoose && tile.kind == TileKind::kStructure &&
        !tile.has_animal) {
      maximum = 1;
    } else {
      maximum = std::min<int64_t>(
          InventoryCount(shadow_priv_, unit_index_, argument),
          std::max<int64_t>(0, config_.shed_capacity - ShedTotal(shadow_priv_)));
    }
  }
  const QuantityMode mode =
      static_cast<QuantityMode>(selection.quantity_mode);
  if (mode == QuantityMode::kOne) {
    result.n = 1;
  } else if (mode == QuantityMode::kAllAvailable) {
    result.n = maximum;
  } else if (mode == QuantityMode::kExact &&
             selection.exact_quantity >= 1 &&
             selection.exact_quantity <= maximum) {
    result.n = selection.exact_quantity;
  } else {
    throw std::invalid_argument("conditional raw quantity is outside its mask");
  }
  return result;
}

int64_t Session::UnitQuantityMaximum(Task task, int argument,
                                     int unit_index) const {
  if (argument < 0 || argument >= kNumItems) return 0;
  if (task == Task::kFetch) {
    return shadow_priv_.shed[argument];
  }
  if (task == Task::kStore) {
    return std::min<int64_t>(
        InventoryCount(shadow_priv_, unit_index, argument),
        std::max<int64_t>(0, config_.shed_capacity - ShedTotal(shadow_priv_)));
  }
  return 0;
}

int64_t Session::ResolveUnitQuantity(Task task, int argument,
                                     QuantityMode mode, int64_t exact,
                                     int unit_index) const {
  if (task != Task::kFetch && task != Task::kStore) {
    throw std::invalid_argument("only logistics tasks carry quantities");
  }
  const int64_t maximum = UnitQuantityMaximum(task, argument, unit_index);
  if (mode == QuantityMode::kOne) return 1;
  if (mode == QuantityMode::kAllAvailable) return maximum;
  if (mode == QuantityMode::kPlanDeficit) {
    int64_t deficit = 0;
    for (const auto& planned : options_) {
      if (!planned) continue;
      if (planned->task == Task::kFeed && argument == item::kWheat) ++deficit;
      if (planned->task == Task::kFertilize && argument == item::kFertilizer) {
        ++deficit;
      }
      if (planned->task == Task::kDeployAnimal &&
          argument == planned->argument) {
        ++deficit;
      }
    }
    return std::clamp<int64_t>(deficit, 1, maximum);
  }
  if (mode == QuantityMode::kExact && exact >= 1 && exact <= maximum) {
    return exact;
  }
  throw std::invalid_argument("conditional task quantity is outside its mask");
}

int64_t Session::MarketQuantityMaximum(MarketOrderType order_type,
                                       int item_index) const {
  if (item_index < 0 || item_index >= kNumItems) return 0;
  if (order_type == MarketOrderType::kSell) {
    return item_index < kNumProducts ? shadow_priv_.shed[item_index] : 0;
  }
  if (order_type == MarketOrderType::kBuySeed) {
    if (item_index >= kNumCrops) return 0;
    return std::min<int64_t>(
        kMaxMarketUnitsPerSlot,
        static_cast<int64_t>(shadow_farm_.money / kCrops[item_index].seed_cost));
  }
  const int64_t room =
      std::max<int64_t>(0, config_.shed_capacity - ShedTotal(shadow_priv_));
  if (order_type == MarketOrderType::kBuyAnimal) {
    if (item_index < item::kGoose || item_index >= kNumItems) return 0;
    const int animal = item_index - item::kGoose;
    return std::min<int64_t>(
        room, static_cast<int64_t>(shadow_farm_.money / kAnimals[animal].cost));
  }
  if (order_type != MarketOrderType::kBuyProduct ||
      (item_index != item::kWheat && item_index != item::kFertilizer)) {
    return 0;
  }
  double money = shadow_farm_.money;
  int64_t inventory = shadow_market_.inventory[item_index];
  int64_t count = 0;
  while (count < room && count < kMaxMarketUnitsPerSlot) {
    const int64_t price =
        ComputeMarketPrice(config_, item_index, inventory - 1);
    if (money < static_cast<double>(price)) break;
    money -= static_cast<double>(price);
    --inventory;
    ++count;
  }
  return count;
}

int64_t Session::PlanDeficit(MarketOrderType order_type, int item_index) const {
  int64_t required = 0;
  for (const auto& option : options_) {
    if (!option) continue;
    if (order_type == MarketOrderType::kBuySeed &&
        (option->task == Task::kSafePlant || option->task == Task::kPlant) &&
        option->argument == item_index &&
        option->phase != OptionPhase::kWater) {
      ++required;
    }
    if (order_type == MarketOrderType::kBuyProduct &&
        ((option->task == Task::kFeed && item_index == item::kWheat) ||
         (option->task == Task::kFertilize &&
          item_index == item::kFertilizer))) {
      ++required;
    }
    if (order_type == MarketOrderType::kBuyAnimal &&
        option->task == Task::kDeployAnimal &&
        option->argument == item_index) {
      ++required;
    }
  }
  int64_t available = 0;
  if (order_type == MarketOrderType::kBuySeed && item_index < kNumCrops) {
    available = shadow_priv_.seeds[item_index];
  } else if (item_index < kNumItems) {
    available = shadow_priv_.shed[item_index];
    for (const Inventory& inventory : shadow_priv_.inventories) {
      available += inventory.Get(item_index);
    }
  }
  return std::max<int64_t>(0, required - available);
}

int64_t Session::ResolveMarketQuantity(MarketOrderType order_type, int item_index,
                                       QuantityMode mode, int64_t exact) const {
  const int64_t maximum = MarketQuantityMaximum(order_type, item_index);
  if (maximum < 1) {
    throw std::logic_error("conditional market quantity has no legal unit");
  }
  switch (mode) {
    case QuantityMode::kOne:
      return 1;
    case QuantityMode::kAllAvailable:
    case QuantityMode::kMaxAffordable:
      return maximum;
    case QuantityMode::kPlanDeficit:
      return std::clamp<int64_t>(PlanDeficit(order_type, item_index), 1, maximum);
    case QuantityMode::kExact:
      if (exact >= 1 && exact <= maximum) return exact;
      break;
  }
  throw std::invalid_argument("conditional market exact quantity is outside its mask");
}

void Session::ProjectMarket(const MarketOrder& order) {
  Farm other_farm;
  other_farm.tiles.assign(
      static_cast<size_t>(config_.board_size) * config_.board_size, Tile{});
  PrivateState other_priv;
  other_priv.inventories.emplace_back();
  std::array<Farm*, 2> farms;
  std::array<PrivateState*, 2> privates;
  std::array<PlayerAction, 2> actions;
  if (player_ == 0) {
    farms = {&shadow_farm_, &other_farm};
    privates = {&shadow_priv_, &other_priv};
  } else {
    farms = {&other_farm, &shadow_farm_};
    privates = {&other_priv, &shadow_priv_};
  }
  actions[player_].market.emplace_back(order);
  std::vector<MarketSlotTrace> trace;
  ApplyMarketPhase(config_, farms, privates, &shadow_market_, actions[0],
                   actions[1], &trace);
  const auto found = std::find_if(
      trace.begin(), trace.end(),
      [this](const MarketSlotTrace& entry) { return entry.player == player_; });
  if (found == trace.end() || found->status != MarketOrderStatus::kApplied) {
    throw std::logic_error("conditional market shadow rejected a masked order");
  }
}

}  // namespace kagg::programs
