#include "programs/session.hpp"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <limits>
#include <utility>

#include "unit_phase.hpp"

namespace kagg::programs {
namespace {

std::pair<int, int> UnitPosition(const Farm& farm, int unit_index) {
  if (unit_index == 0) return {farm.farmer_x, farm.farmer_y};
  return farm.hands.at(static_cast<size_t>(unit_index - 1));
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

uint64_t Fibonacci(int n) {
  uint64_t left = 1;
  uint64_t right = 1;
  for (int index = 0; index < n; ++index) {
    const uint64_t next = left + right;
    if (next < right) return std::numeric_limits<uint64_t>::max();
    left = right;
    right = next;
  }
  return left;
}

size_t TaskArgumentIndex(Task task, int argument) {
  return static_cast<size_t>(task) * kArgumentCount + argument;
}

size_t TaskTargetIndex(Task task, int argument, int target, int tiles) {
  return (static_cast<size_t>(task) * kArgumentCount + argument) * tiles +
         target;
}

size_t TaskQuantityModeIndex(Task task, int argument, QuantityMode mode) {
  return ((static_cast<size_t>(task) * kArgumentCount + argument) *
          kQuantityModeCount) +
         static_cast<int>(mode);
}

size_t TaskQuantityIndex(Task task, int argument) {
  return static_cast<size_t>(task) * kArgumentCount + argument;
}

size_t RawArgumentIndex(RawOperation operation, int argument) {
  return static_cast<size_t>(operation) * kArgumentCount + argument;
}

size_t RawQuantityModeIndex(RawOperation operation, int argument,
                            QuantityMode mode) {
  return ((static_cast<size_t>(operation) * kArgumentCount + argument) *
          kQuantityModeCount) +
         static_cast<int>(mode);
}

size_t RawQuantityIndex(RawOperation operation, int argument) {
  return static_cast<size_t>(operation) * kArgumentCount + argument;
}

size_t MarketItemIndex(MarketOrderType order, int item_index) {
  return static_cast<size_t>(order) * kNumItems + item_index;
}

size_t MarketQuantityModeIndex(MarketOrderType order, int item_index,
                               QuantityMode mode) {
  return ((static_cast<size_t>(order) * kNumItems + item_index) *
          kQuantityModeCount) +
         static_cast<int>(mode);
}

size_t MarketQuantityIndex(MarketOrderType order, int item_index) {
  return static_cast<size_t>(order) * kNumItems + item_index;
}

bool IsExclusive(Task task) {
  return task == Task::kSafePlant || task == Task::kPlant ||
         task == Task::kHarvest ||
         task == Task::kDig || task == Task::kBuild ||
         task == Task::kDeployAnimal;
}

}  // namespace

Decision Session::BuildDecision() const {
  Decision result;
  result.phase = phase_;
  result.unit_count = unit_count_;
  result.unit_index = phase_ == Phase::kUnit ? unit_index_ : -1;
  result.market_slot = phase_ == Phase::kMarket ? market_slot_ : -1;
  const int tiles = config_.board_size * config_.board_size;
  result.task_argument_mask.assign(
      static_cast<size_t>(kTaskCount) * kArgumentCount, 0);
  result.task_target_mask.assign(
      static_cast<size_t>(kTaskCount) * kArgumentCount * tiles, 0);
  result.task_quantity_mode_mask.assign(
      static_cast<size_t>(kTaskCount) * kArgumentCount * kQuantityModeCount,
      0);
  result.task_quantity_max.assign(
      static_cast<size_t>(kTaskCount) * kArgumentCount, 0);
  result.raw_argument_mask.assign(
      static_cast<size_t>(kRawOperationCount) * kArgumentCount, 0);
  result.raw_quantity_mode_mask.assign(
      static_cast<size_t>(kRawOperationCount) * kArgumentCount *
          kQuantityModeCount,
      0);
  result.raw_quantity_max.assign(
      static_cast<size_t>(kRawOperationCount) * kArgumentCount, 0);
  result.market_item_mask.assign(
      static_cast<size_t>(kMarketOrderCount) * kNumItems, 0);
  result.market_quantity_mode_mask.assign(
      static_cast<size_t>(kMarketOrderCount) * kNumItems *
          kQuantityModeCount,
      0);
  result.market_quantity_max.assign(
      static_cast<size_t>(kMarketOrderCount) * kNumItems, 0);
  result.target_reservations.assign(static_cast<size_t>(tiles), 0);
  for (const auto& option : options_) {
    if (option && option->target >= 0 && option->target < tiles) {
      ++result.target_reservations[option->target];
    }
  }

  const double turns = std::max(1, config_.turns_per_day);
  const double days = std::max(
      1, (config_.episode_steps + config_.turns_per_day - 1) /
             config_.turns_per_day);
  result.root_features[0] = 1.0F;
  result.root_features[1] = static_cast<float>(phase_ == Phase::kUnit);
  result.root_features[2] = static_cast<float>(phase_ == Phase::kMarket);
  result.root_features[3] = static_cast<float>(step_ % config_.turns_per_day / turns);
  result.root_features[4] = static_cast<float>(day_ / days);
  result.root_features[5] = static_cast<float>(
      std::max(0, config_.episode_steps - step_ - 1) /
      static_cast<double>(std::max(1, config_.episode_steps - 1)));
  result.root_features[6] = static_cast<float>(unit_count_) / unit_limit_;
  result.root_features[7] = static_cast<float>(
      std::log1p(std::max(0.0, shadow_farm_.money)) / 16.0);
  result.root_features[8] = static_cast<float>(ShedTotal(shadow_priv_)) /
                            std::max<int64_t>(1, config_.shed_capacity);
  result.root_features[9] = static_cast<float>(
      std::max<int64_t>(0, config_.shed_capacity - ShedTotal(shadow_priv_))) /
                            std::max<int64_t>(1, config_.shed_capacity);
  result.root_features[10] = static_cast<float>(market_slot_) /
                             std::max(1, config_.max_market_orders);
  result.root_features[11] = static_cast<float>(
      std::max(0, config_.max_market_orders - market_slot_)) /
                             std::max(1, config_.max_market_orders);
  int active_options = 0;
  for (const auto& option : options_) active_options += option.has_value();
  result.root_features[12] = static_cast<float>(active_options) / unit_limit_;

  if (phase_ == Phase::kMarket) {
    result.market_order_mask[static_cast<int>(MarketOrderType::kEnd)] = 1;
    const auto add_quantity = [&](MarketOrderType order, int item_index,
                                  int64_t maximum) {
      if (maximum < 1) return;
      result.market_item_mask[MarketItemIndex(order, item_index)] = 1;
      result.market_quantity_max[MarketQuantityIndex(order, item_index)] =
          maximum;
      result.market_quantity_mode_mask[MarketQuantityModeIndex(
          order, item_index, QuantityMode::kOne)] = 1;
      if (order == MarketOrderType::kSell && maximum > 1) {
        result.market_quantity_mode_mask[MarketQuantityModeIndex(
            order, item_index, QuantityMode::kAllAvailable)] = 1;
      }
      if (order != MarketOrderType::kSell && maximum > 1) {
        result.market_quantity_mode_mask[MarketQuantityModeIndex(
            order, item_index, QuantityMode::kMaxAffordable)] = 1;
      }
      if (order != MarketOrderType::kSell &&
          PlanDeficit(order, item_index) > 0) {
        result.market_quantity_mode_mask[MarketQuantityModeIndex(
            order, item_index, QuantityMode::kPlanDeficit)] = 1;
      }
      if (maximum > 1) {
        result.market_quantity_mode_mask[MarketQuantityModeIndex(
            order, item_index, QuantityMode::kExact)] = 1;
      }
      result.market_order_mask[static_cast<int>(order)] = 1;
    };
    for (int product = 0; product < kNumProducts; ++product) {
      add_quantity(MarketOrderType::kSell, product,
                   MarketQuantityMaximum(MarketOrderType::kSell, product));
    }
    for (int crop = 0; crop < kNumCrops; ++crop) {
      add_quantity(MarketOrderType::kBuySeed, crop,
                   MarketQuantityMaximum(MarketOrderType::kBuySeed, crop));
    }
    for (const int product : {item::kWheat, item::kFertilizer}) {
      add_quantity(
          MarketOrderType::kBuyProduct, product,
          MarketQuantityMaximum(MarketOrderType::kBuyProduct, product));
    }
    for (int animal = item::kGoose; animal < kNumItems; ++animal) {
      add_quantity(
          MarketOrderType::kBuyAnimal, animal,
          MarketQuantityMaximum(MarketOrderType::kBuyAnimal, animal));
    }
    const uint64_t raw_hire =
        Fibonacci(std::max(0, shadow_farm_.hires_today));
    const double hire_cost = static_cast<double>(config_.farm_hand_cost_mult) *
                             static_cast<double>(raw_hire);
    if (1 + static_cast<int>(shadow_farm_.hands.size()) < unit_limit_ &&
        shadow_farm_.money >= hire_cost) {
      result.market_order_mask[static_cast<int>(MarketOrderType::kHire)] = 1;
    }
    if (shadow_farm_.extra_unlocked < static_cast<int>(kLandPrices.size()) &&
        shadow_farm_.money >=
            static_cast<double>(kLandPrices[shadow_farm_.extra_unlocked])) {
      result.market_order_mask[static_cast<int>(MarketOrderType::kBuyLand)] = 1;
    }
    return result;
  }

  const int unit = unit_index_;
  const auto [x, y] = UnitPosition(shadow_farm_, unit);
  result.current_x = x;
  result.current_y = y;
  result.root_features[13] = static_cast<float>(unit) /
                             std::max(1, unit_limit_ - 1);
  result.root_features[14] = static_cast<float>(x) /
                             std::max(1, config_.board_size - 1);
  result.root_features[15] = static_cast<float>(y) /
                             std::max(1, config_.board_size - 1);
  result.root_features[16] = static_cast<float>(
      InventoryTotal(shadow_priv_, unit)) /
      std::max<int64_t>(1, config_.shed_capacity);
  result.forced = forced_water_targets_[unit] >= 0 ? 1 : 0;
  result.root_features[17] = static_cast<float>(result.forced);

  if (options_[unit]) {
    const Option& option = *options_[unit];
    result.option_features[0] = 1;
    result.option_features[1] = 1 + static_cast<int>(option.task);
    result.option_features[2] = option.target + 1;
    result.option_features[3] = option.argument + 1;
    result.option_features[4] = 1 + static_cast<int>(option.quantity_mode);
    result.option_features[5] = option.exact_quantity;
    result.option_features[6] = 1 + static_cast<int>(option.phase);
    result.option_features[7] = std::max(0, step_ - option.created_step);
    result.option_features[8] = ValidateOption(option, unit) ? 1 : 0;
    if (option.target >= 0 && option.target < tiles) {
      result.option_features[9] = option.target % config_.board_size + 1;
      result.option_features[10] = option.target / config_.board_size + 1;
      result.option_features[11] = result.target_reservations[option.target];
    }
  }

  if (result.forced) {
    result.control_mask[static_cast<int>(Control::kKeep)] = 1;
    return result;
  }
  result.control_mask[static_cast<int>(Control::kCancelPass)] = 1;
  if (CanKeep(unit)) {
    result.control_mask[static_cast<int>(Control::kKeep)] = 1;
  }
  result.direction_mask[static_cast<int>(Direction::kNorth)] = y > 0;
  result.direction_mask[static_cast<int>(Direction::kSouth)] =
      y + 1 < config_.board_size;
  result.direction_mask[static_cast<int>(Direction::kEast)] =
      x + 1 < config_.board_size;
  result.direction_mask[static_cast<int>(Direction::kWest)] = x > 0;
  if (std::any_of(result.direction_mask.begin(), result.direction_mask.end(),
                  [](uint8_t value) { return value != 0; })) {
    result.control_mask[static_cast<int>(Control::kStep)] = 1;
  }

  const auto reserved_seed = [&](int crop) {
    int64_t reserved = 0;
    for (int other = 0; other < static_cast<int>(options_.size()); ++other) {
      if (other == unit || !options_[other]) continue;
      const Option& option = *options_[other];
      if ((option.task == Task::kSafePlant ||
           option.task == Task::kPlant) &&
          option.argument == crop &&
          option.phase != OptionPhase::kWater) {
        ++reserved;
      }
    }
    return reserved;
  };
  const auto item_supply = [&](int item_index) {
    int64_t supply = InventoryCount(shadow_priv_, unit, item_index) +
                     shadow_priv_.shed[item_index];
    for (int other = 0; other < static_cast<int>(options_.size()); ++other) {
      if (other == unit || !options_[other] ||
          InventoryCount(shadow_priv_, other, item_index) > 0) {
        continue;
      }
      const Option& option = *options_[other];
      if ((option.task == Task::kFeed && item_index == item::kWheat) ||
          (option.task == Task::kFertilize &&
           item_index == item::kFertilizer) ||
          (option.task == Task::kDeployAnimal &&
           item_index == option.argument)) {
        --supply;
      }
    }
    return std::max<int64_t>(0, supply);
  };
  const auto target_conflict = [&](Task task, int target) {
    if (task == Task::kGoTo) return false;
    for (int other = 0; other < static_cast<int>(options_.size()); ++other) {
      if (other == unit || !options_[other] ||
          options_[other]->target != target) {
        continue;
      }
      const Task reserved = options_[other]->task;
      if ((IsExclusive(task) && IsExclusive(reserved)) || task == reserved) {
        if ((task == Task::kBuild && reserved == Task::kDeployAnimal) ||
            (task == Task::kDeployAnimal && reserved == Task::kBuild)) {
          continue;
        }
        return true;
      }
    }
    return false;
  };
  const auto has_later_waterer = [&](int target) {
    if (step_ % config_.turns_per_day != config_.turns_per_day - 1) return true;
    for (int later = unit + 1; later < unit_count_; ++later) {
      const auto position = UnitPosition(shadow_farm_, later);
      if (forced_water_targets_[later] < 0 &&
          target == position.second * config_.board_size + position.first) {
        return true;
      }
    }
    return false;
  };
  const auto set_target = [&](Task task, int argument, int target) {
    result.task_target_mask[
        TaskTargetIndex(task, argument, target, tiles)] = 1;
    result.task_mask[static_cast<int>(task)] = 1;
  };
  const auto set_argument = [&](Task task, int argument) {
    result.task_argument_mask[TaskArgumentIndex(task, argument)] = 1;
  };

  for (int target = 0; target < tiles; ++target) {
    const Tile& tile = shadow_farm_.tiles[target];
    if (tile.kind == TileKind::kEmpty &&
        !target_conflict(Task::kSafePlant, target) &&
        has_later_waterer(target)) {
      for (int crop = 0; crop < kNumCrops; ++crop) {
        if (shadow_priv_.seeds[crop] > 0 &&
            (shadow_priv_.seeds[crop] - reserved_seed(crop) > 0 ||
             target == y * config_.board_size + x)) {
          set_argument(Task::kSafePlant, crop);
          set_target(Task::kSafePlant, crop, target);
        }
      }
    }
    if (tile.kind == TileKind::kEmpty &&
        !target_conflict(Task::kPlant, target)) {
      for (int crop = 0; crop < kNumCrops; ++crop) {
        if (shadow_priv_.seeds[crop] > 0 &&
            (shadow_priv_.seeds[crop] - reserved_seed(crop) > 0 ||
             target == y * config_.board_size + x)) {
          set_argument(Task::kPlant, crop);
          set_target(Task::kPlant, crop, target);
        }
      }
    }
    if (tile.kind == TileKind::kPlant && !tile.watered_today) {
      set_target(Task::kWater, kNoneArgument, target);
    }
    if (IsHarvestable(tile, day_) &&
        !target_conflict(Task::kHarvest, target)) {
      set_target(Task::kHarvest, kNoneArgument, target);
    }
    if (tile.kind == TileKind::kPlant && item_supply(item::kFertilizer) > 0) {
      set_target(Task::kFertilize, kNoneArgument, target);
    }
    if (tile.kind != TileKind::kEmpty && tile.kind != TileKind::kLocked &&
        !(tile.kind == TileKind::kStructure && tile.has_animal) &&
        !target_conflict(Task::kDig, target)) {
      set_target(Task::kDig, kNoneArgument, target);
    }
    if (tile.kind == TileKind::kEmpty &&
        !target_conflict(Task::kBuild, target)) {
      for (const int argument : {kCoopArgument, kPastureArgument}) {
        set_argument(Task::kBuild, argument);
        set_target(Task::kBuild, argument, target);
      }
    }
    for (int animal = 0; animal < kNumAnimals; ++animal) {
      const int argument = item::kGoose + animal;
      const bool compatible =
          tile.kind == TileKind::kEmpty ||
          (tile.kind == TileKind::kStructure && !tile.has_animal &&
           tile.structure == kAnimals[animal].structure);
      if (compatible && item_supply(argument) > 0 &&
          !target_conflict(Task::kDeployAnimal, target)) {
        set_argument(Task::kDeployAnimal, argument);
        set_target(Task::kDeployAnimal, argument, target);
      }
    }
    if (IsAnimalTile(tile) && !tile.fed_today &&
        item_supply(item::kWheat) > 0) {
      set_target(Task::kFeed, kNoneArgument, target);
    }
    if (IsAnimalTile(tile) && !tile.cared_today) {
      set_target(Task::kCare, kNoneArgument, target);
    }
    if (IsAnimalTile(tile) && tile.fertilizer_available) {
      set_target(Task::kCollect, kNoneArgument, target);
    }
    if (target != y * config_.board_size + x) {
      set_target(Task::kGoTo, kNoneArgument, target);
    }
  }
  for (const Task task : {Task::kWater, Task::kHarvest, Task::kFertilize,
                          Task::kDig, Task::kFeed, Task::kCare,
                          Task::kCollect, Task::kGoTo, Task::kStoreAll,
                          Task::kWait}) {
    set_argument(task, kNoneArgument);
  }

  result.task_mask[static_cast<int>(Task::kWait)] = 1;

  const auto add_task_quantity = [&](Task task, int argument, int64_t maximum,
                                     int64_t deficit) {
    if (maximum < 1) return;
    set_argument(task, argument);
    for (const auto& [shed_x, shed_y] : ShedAccessTiles(config_.board_size)) {
      set_target(task, argument, shed_y * config_.board_size + shed_x);
    }
    result.task_quantity_max[TaskQuantityIndex(task, argument)] = maximum;
    result.task_quantity_mode_mask[TaskQuantityModeIndex(
        task, argument, QuantityMode::kOne)] = 1;
    if (maximum > 1) {
      result.task_quantity_mode_mask[TaskQuantityModeIndex(
          task, argument, QuantityMode::kAllAvailable)] = 1;
      result.task_quantity_mode_mask[TaskQuantityModeIndex(
          task, argument, QuantityMode::kExact)] = 1;
    }
    if (deficit > 0) {
      result.task_quantity_mode_mask[TaskQuantityModeIndex(
          task, argument, QuantityMode::kPlanDeficit)] = 1;
    }
  };
  const int64_t room =
      std::max<int64_t>(0, config_.shed_capacity - ShedTotal(shadow_priv_));
  for (int item_index = 0; item_index < kNumItems; ++item_index) {
    int64_t deficit = 0;
    for (const auto& option : options_) {
      if (!option) continue;
      if ((option->task == Task::kFeed && item_index == item::kWheat) ||
          (option->task == Task::kFertilize &&
           item_index == item::kFertilizer) ||
          (option->task == Task::kDeployAnimal &&
           item_index == option->argument)) {
        ++deficit;
      }
    }
    add_task_quantity(Task::kFetch, item_index,
                      shadow_priv_.shed[item_index], deficit);
    add_task_quantity(
        Task::kStore, item_index,
        std::min<int64_t>(InventoryCount(shadow_priv_, unit, item_index), room),
        0);
  }
  if (InventoryTotal(shadow_priv_, unit) > 0) {
    for (const auto& [shed_x, shed_y] : ShedAccessTiles(config_.board_size)) {
      set_target(Task::kStoreAll, kNoneArgument,
                 shed_y * config_.board_size + shed_x);
    }
  }
  if (std::any_of(result.task_mask.begin(), result.task_mask.end(),
                  [](uint8_t value) { return value != 0; })) {
    result.control_mask[static_cast<int>(Control::kAssign)] = 1;
  }

  const auto add_raw_quantity = [&](RawOperation operation, int argument,
                                    int64_t maximum) {
    if (maximum < 1) return;
    result.raw_argument_mask[RawArgumentIndex(operation, argument)] = 1;
    result.raw_quantity_max[RawQuantityIndex(operation, argument)] = maximum;
    result.raw_quantity_mode_mask[RawQuantityModeIndex(
        operation, argument, QuantityMode::kOne)] = 1;
    if (maximum > 1) {
      result.raw_quantity_mode_mask[RawQuantityModeIndex(
          operation, argument, QuantityMode::kAllAvailable)] = 1;
      result.raw_quantity_mode_mask[RawQuantityModeIndex(
          operation, argument, QuantityMode::kExact)] = 1;
    }
    result.raw_operation_mask[static_cast<int>(operation)] = 1;
  };
  for (int item_index = 0; item_index < kNumItems; ++item_index) {
    const UnitAction pickup{UnitOp::kPickup, item_index, 1};
    if (WouldApplyUnitAction(config_, shadow_farm_, shadow_priv_, unit, pickup,
                             day_)) {
      add_raw_quantity(RawOperation::kPickup, item_index,
                       shadow_priv_.shed[item_index]);
    }
    const UnitAction place{UnitOp::kPlace, item_index, 1};
    if (WouldApplyUnitAction(config_, shadow_farm_, shadow_priv_, unit, place,
                             day_)) {
      const Tile& tile = shadow_farm_.tiles[y * config_.board_size + x];
      const int64_t maximum =
          item_index >= item::kGoose && tile.kind == TileKind::kStructure &&
                  !tile.has_animal
              ? 1
              : std::min<int64_t>(
                    InventoryCount(shadow_priv_, unit, item_index), room);
      add_raw_quantity(RawOperation::kPlace, item_index, maximum);
    }
  }
  for (int crop = 0; crop < kNumCrops; ++crop) {
    const UnitAction plant{UnitOp::kPlant, crop, 1};
    if (shadow_priv_.seeds[crop] > 0 &&
        WouldApplyUnitAction(config_, shadow_farm_, shadow_priv_, unit, plant,
                             day_)) {
      result.raw_argument_mask[
          RawArgumentIndex(RawOperation::kPlant, crop)] = 1;
      result.raw_operation_mask[static_cast<int>(RawOperation::kPlant)] = 1;
    }
  }
  const std::array<std::pair<RawOperation, UnitOp>, 9> raw_actions = {{
      {RawOperation::kWater, UnitOp::kWater},
      {RawOperation::kHarvest, UnitOp::kHarvest},
      {RawOperation::kFertilize, UnitOp::kFertilize},
      {RawOperation::kDig, UnitOp::kDig},
      {RawOperation::kBuildCoop, UnitOp::kBuildCoop},
      {RawOperation::kBuildPasture, UnitOp::kBuildPasture},
      {RawOperation::kFeed, UnitOp::kFeed},
      {RawOperation::kCollectFertilizer, UnitOp::kCollectFertilizer},
      {RawOperation::kCare, UnitOp::kCare},
  }};
  for (const auto& [raw, official] : raw_actions) {
    if (WouldApplyUnitAction(
            config_, shadow_farm_, shadow_priv_, unit,
            UnitAction{official, -1, 1}, day_)) {
      result.raw_operation_mask[static_cast<int>(raw)] = 1;
      result.raw_argument_mask[RawArgumentIndex(raw, kNoneArgument)] = 1;
    }
  }
  if (IsShedAdjacent(x, y, config_.board_size) &&
      InventoryTotal(shadow_priv_, unit) > 0) {
    result.raw_operation_mask[static_cast<int>(RawOperation::kDrop)] = 1;
    result.raw_argument_mask[
        RawArgumentIndex(RawOperation::kDrop, kNoneArgument)] = 1;
  }
  if (std::any_of(result.raw_operation_mask.begin(),
                  result.raw_operation_mask.end(),
                  [](uint8_t value) { return value != 0; })) {
    result.control_mask[static_cast<int>(Control::kRawLocal)] = 1;
  }
  return result;
}

std::vector<const char*> RootFeatureNames() {
  return {
      "present",          "phase_unit",       "phase_market",
      "hour_fraction",    "day_fraction",     "remaining_fraction",
      "unit_count",       "log_money",        "shed_fill",
      "shed_room",        "market_slot",      "market_slots_remaining",
      "active_options",   "unit_index",       "unit_x",
      "unit_y",           "unit_inventory",   "forced_subtask",
  };
}

std::vector<const char*> OptionFeatureNames() {
  return {
      "present",       "task_plus_one",   "target_plus_one",
      "argument_plus_one", "quantity_mode_plus_one", "exact_quantity",
      "phase_plus_one", "age",            "currently_valid",
      "target_x_plus_one", "target_y_plus_one", "target_reservations",
  };
}

}  // namespace kagg::programs
