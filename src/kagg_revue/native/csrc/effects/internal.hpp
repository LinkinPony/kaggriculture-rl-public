// Shared mechanical helpers for the atomic-effect native implementation.
#pragma once

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <limits>
#include <tuple>
#include <utility>

#include "effects/session.hpp"

namespace kagg::effects::internal {

inline int Distance(int x0, int y0, int x1, int y1) {
  return std::abs(x0 - x1) + std::abs(y0 - y1);
}

inline std::pair<int, int> TargetPosition(int target, int board_size) {
  return {target % board_size, target / board_size};
}

inline std::pair<int, int> UnitPosition(const Farm& farm, int unit) {
  if (unit == 0) return {farm.farmer_x, farm.farmer_y};
  return farm.hands.at(static_cast<std::size_t>(unit - 1));
}

inline void SetUnitPosition(Farm* farm, int unit, int x, int y) {
  if (unit == 0) {
    farm->farmer_x = x;
    farm->farmer_y = y;
  } else {
    farm->hands.at(static_cast<std::size_t>(unit - 1)) = {x, y};
  }
}

inline UnitAction MoveToward(int x, int y, int target_x, int target_y) {
  if (x < target_x) return {UnitOp::kEast, -1, 1};
  if (x > target_x) return {UnitOp::kWest, -1, 1};
  if (y < target_y) return {UnitOp::kSouth, -1, 1};
  if (y > target_y) return {UnitOp::kNorth, -1, 1};
  return {UnitOp::kPass, -1, 1};
}

inline std::pair<int, int> BestShedForRoute(int x, int y, int target_x,
                                            int target_y, int board_size) {
  auto best = ShedAccessTiles(board_size).front();
  auto best_key = std::tuple{
      Distance(x, y, best.first, best.second) +
          Distance(best.first, best.second, target_x, target_y),
      Distance(x, y, best.first, best.second), best.second, best.first};
  for (const auto& shed : ShedAccessTiles(board_size)) {
    const auto key = std::tuple{
        Distance(x, y, shed.first, shed.second) +
            Distance(shed.first, shed.second, target_x, target_y),
        Distance(x, y, shed.first, shed.second), shed.second, shed.first};
    if (key < best_key) {
      best = shed;
      best_key = key;
    }
  }
  return best;
}

inline std::pair<int, int> NearestShed(int x, int y, int board_size) {
  return BestShedForRoute(x, y, x, y, board_size);
}

inline int RequiredItem(RequestKind kind, int item_index) {
  switch (kind) {
    case RequestKind::kFertilize:
      return item::kFertilizer;
    case RequestKind::kFeed:
      return item::kWheat;
    case RequestKind::kPlaceAnimal:
      return item_index;
    default:
      return -1;
  }
}

inline ResourceKind RequiredResource(RequestKind kind) {
  if (kind == RequestKind::kPlant) return ResourceKind::kSeed;
  if (kind == RequestKind::kLoad) return ResourceKind::kItem;
  if (kind == RequestKind::kBank || kind == RequestKind::kUnload) {
    return ResourceKind::kShedRoom;
  }
  if (RequiredItem(kind, -1) >= 0 || kind == RequestKind::kPlaceAnimal) {
    return ResourceKind::kItem;
  }
  return ResourceKind::kNone;
}

inline UnitAction EffectAction(RequestKind kind, int item_index) {
  switch (kind) {
    case RequestKind::kPlant:
      return {UnitOp::kPlant, item_index, 1};
    case RequestKind::kWater:
      return {UnitOp::kWater, -1, 1};
    case RequestKind::kHarvest:
      return {UnitOp::kHarvest, -1, 1};
    case RequestKind::kFertilize:
      return {UnitOp::kFertilize, -1, 1};
    case RequestKind::kDig:
      return {UnitOp::kDig, -1, 1};
    case RequestKind::kBuildCoop:
      return {UnitOp::kBuildCoop, -1, 1};
    case RequestKind::kBuildPasture:
      return {UnitOp::kBuildPasture, -1, 1};
    case RequestKind::kPlaceAnimal:
      return {UnitOp::kPlace, item_index, 1};
    case RequestKind::kFeed:
      return {UnitOp::kFeed, -1, 1};
    case RequestKind::kCare:
      return {UnitOp::kCare, -1, 1};
    case RequestKind::kCollectFertilizer:
      return {UnitOp::kCollectFertilizer, -1, 1};
    default:
      return {UnitOp::kPass, -1, 1};
  }
}

inline bool IsTransforming(RequestKind kind) {
  return kind == RequestKind::kPlant || kind == RequestKind::kDig ||
         kind == RequestKind::kBuildCoop ||
         kind == RequestKind::kBuildPasture ||
         kind == RequestKind::kPlaceAnimal;
}

inline bool RequestsConflict(RequestKind left_kind, int left_target,
                             int left_item, RequestKind right_kind,
                             int right_target, int right_item,
                             const Farm& farm) {
  if (left_kind == RequestKind::kCancel || right_kind == RequestKind::kCancel) {
    return false;
  }
  if (left_kind == RequestKind::kBank || right_kind == RequestKind::kBank ||
      left_kind == RequestKind::kLoad || right_kind == RequestKind::kLoad ||
      left_kind == RequestKind::kUnload ||
      right_kind == RequestKind::kUnload ||
      left_kind == RequestKind::kStage || right_kind == RequestKind::kStage) {
    return false;
  }
  if (left_target < 0 || left_target != right_target) return false;
  if (left_kind == right_kind && left_item == right_item) return true;
  if (IsTransforming(left_kind) || IsTransforming(right_kind)) return true;
  if (left_kind == RequestKind::kHarvest || right_kind == RequestKind::kHarvest) {
    const Tile& tile = farm.tiles.at(static_cast<std::size_t>(left_target));
    return tile.kind == TileKind::kPlant && !kCrops[tile.crop].ongoing;
  }
  return false;
}

inline bool TargetSupports(const Farm& farm, int day, RequestKind kind,
                           int target, int item_index) {
  if (kind == RequestKind::kStage || kind == RequestKind::kBank ||
      kind == RequestKind::kLoad || kind == RequestKind::kUnload) {
    return true;
  }
  if (target < 0 || target >= static_cast<int>(farm.tiles.size())) return false;
  const Tile& tile = farm.tiles[target];
  switch (kind) {
    case RequestKind::kPlant:
      return item_index >= 0 && item_index < kNumCrops &&
             tile.kind == TileKind::kEmpty;
    case RequestKind::kWater:
      return tile.kind == TileKind::kPlant && !tile.watered_today;
    case RequestKind::kHarvest:
      if (tile.yield_units <= 0) return false;
      if (tile.kind == TileKind::kPlant) {
        return day - tile.planted_day >= kCrops[tile.crop].first_yield_day;
      }
      return tile.kind == TileKind::kStructure && tile.has_animal;
    case RequestKind::kFertilize:
      return tile.kind == TileKind::kPlant;
    case RequestKind::kDig:
      return tile.kind != TileKind::kEmpty && tile.kind != TileKind::kLocked &&
             !(tile.kind == TileKind::kStructure && tile.has_animal);
    case RequestKind::kBuildCoop:
    case RequestKind::kBuildPasture:
      return tile.kind == TileKind::kEmpty;
    case RequestKind::kPlaceAnimal:
      return item_index >= item::kGoose && item_index < kNumItems &&
             tile.kind == TileKind::kStructure && !tile.has_animal &&
             tile.structure == kAnimals[item_index - item::kGoose].structure;
    case RequestKind::kFeed:
      return tile.kind == TileKind::kStructure && tile.has_animal &&
             !tile.fed_today;
    case RequestKind::kCare:
      return tile.kind == TileKind::kStructure && tile.has_animal &&
             !tile.cared_today;
    case RequestKind::kCollectFertilizer:
      return tile.kind == TileKind::kStructure && tile.has_animal &&
             tile.fertilizer_available;
    default:
      return false;
  }
}

inline std::array<int64_t, kActionFieldCount> EncodeAction(
    const SemanticAction& action) {
  return {static_cast<int64_t>(action.kind), action.target, action.item + 1,
          action.quantity, static_cast<int64_t>(action.job_id),
          action.unit + 1};
}

inline int64_t InventoryTotal(const Inventory& inventory) {
  int64_t result = 0;
  for (const auto& [unused_item, count] : inventory.items) {
    (void)unused_item;
    result += count;
  }
  return result;
}

struct AssignmentPlan {
  int unit = -1;
  int cost = std::numeric_limits<int>::max();
  bool uses_shed = false;
};

inline AssignmentPlan BestAssignment(
    const Config& config, const Farm& farm, const PrivateState& priv,
    const Candidate& candidate, const std::vector<uint8_t>& busy,
    const std::array<int64_t, kNumItems>& reserved_shed,
    int maximum_cost = std::numeric_limits<int>::max()) {
  const RequestKind kind = candidate.kind;
  const int target = static_cast<int>(candidate.fields[1]);
  const int item_index = static_cast<int>(candidate.fields[2]) - 1;
  const int bound_unit = static_cast<int>(candidate.fields[5]) - 1;
  const int required = RequiredItem(kind, item_index);
  AssignmentPlan best;
  for (int unit = 0; unit < static_cast<int>(priv.inventories.size()); ++unit) {
    if (busy[unit] || (bound_unit >= 0 && bound_unit != unit)) continue;
    const auto [x, y] = UnitPosition(farm, unit);
    int cost = 0;
    bool uses_shed = false;
    if (kind == RequestKind::kBank || kind == RequestKind::kLoad ||
        kind == RequestKind::kUnload) {
      const auto shed = NearestShed(x, y, config.board_size);
      cost = Distance(x, y, shed.first, shed.second) + 1;
    } else if (kind == RequestKind::kStage) {
      const auto destination = TargetPosition(target, config.board_size);
      cost = Distance(x, y, destination.first, destination.second);
    } else {
      const auto destination = TargetPosition(target, config.board_size);
      if (required >= 0 && priv.inventories[unit].Get(required) <= 0) {
        if (priv.shed[required] - reserved_shed[required] <= 0) continue;
        const auto shed = BestShedForRoute(
            x, y, destination.first, destination.second, config.board_size);
        cost = Distance(x, y, shed.first, shed.second) + 1 +
               Distance(shed.first, shed.second, destination.first,
                        destination.second) +
               1;
        uses_shed = true;
      } else {
        cost = Distance(x, y, destination.first, destination.second) + 1;
      }
    }
    if (cost <= maximum_cost &&
        std::tie(cost, unit) < std::tie(best.cost, best.unit)) {
      best = {unit, cost, uses_shed};
    }
  }
  return best;
}

inline uint64_t HashWord(uint64_t word, uint64_t hash) {
  constexpr uint64_t kPrime = 1099511628211ULL;
  for (int byte = 0; byte < 8; ++byte) {
    hash ^= (word >> (byte * 8)) & 0xffU;
    hash *= kPrime;
  }
  return hash;
}

}  // namespace kagg::effects::internal
