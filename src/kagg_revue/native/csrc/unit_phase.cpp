// Shared unit-action transition and sequential turn workspace.

#include "unit_phase.hpp"
#include "production/rules.hpp"

#include <algorithm>
#include <array>
#include <cstdint>

namespace kagg {
namespace {

UnitAction PassAction() { return UnitAction{UnitOp::kPass, -1, 1}; }

UnitActionTrace Rejected(int unit_index, const UnitAction& requested,
                         UnitActionStatus status) {
  return UnitActionTrace{unit_index, requested, PassAction(), status};
}

std::array<bool, kNumCrops> BlockedPlants(const PlayerAction& action,
                                          const PrivateState& priv) {
  std::array<int64_t, kNumCrops> demand{};
  const auto count = [&demand](const UnitAction& unit_action) {
    if (unit_action.op == UnitOp::kPlant && unit_action.arg >= 0 &&
        unit_action.arg < kNumCrops) {
      demand[unit_action.arg] += 1;
    }
  };
  count(action.farmer);
  for (const UnitAction& hand : action.hands) count(hand);

  std::array<bool, kNumCrops> blocked{};
  for (int crop = 0; crop < kNumCrops; ++crop) {
    blocked[crop] = demand[crop] > priv.seeds[crop];
  }
  return blocked;
}

bool IsBlockedPlant(const UnitAction& action,
                    const std::array<bool, kNumCrops>& blocked) {
  return action.op == UnitOp::kPlant && action.arg >= 0 && action.arg < kNumCrops &&
         blocked[action.arg];
}

UnitActionTrace ApplyGatedUnitAction(const Config& config, Farm* farm, PrivateState* priv,
                                     int unit_index, const UnitAction& action, int day,
                                     const std::array<bool, kNumCrops>& blocked) {
  if (IsBlockedPlant(action, blocked)) {
    return Rejected(unit_index, action, UnitActionStatus::kAtomicPlantConflict);
  }
  return ApplyUnitAction(config, farm, priv, unit_index, action, day);
}

}  // namespace

const char* UnitActionStatusName(UnitActionStatus status) {
  switch (status) {
    case UnitActionStatus::kApplied:
      return "applied";
    case UnitActionStatus::kPass:
      return "pass";
    case UnitActionStatus::kMalformed:
      return "malformed";
    case UnitActionStatus::kGhostUnit:
      return "ghost_unit";
    case UnitActionStatus::kIllegal:
      return "illegal";
    case UnitActionStatus::kAtomicPlantConflict:
      return "atomic_plant_conflict";
  }
  return "illegal";
}

bool WouldApplyUnitAction(const Config& config, const Farm& farm,
                          const PrivateState& priv, int unit_index,
                          const UnitAction& requested, int day) {
  if (requested.op == UnitOp::kInvalid || unit_index < 0) return false;

  int x;
  int y;
  if (unit_index == 0) {
    x = farm.farmer_x;
    y = farm.farmer_y;
  } else {
    const int hand_index = unit_index - 1;
    if (hand_index >= static_cast<int>(farm.hands.size())) return false;
    x = farm.hands[hand_index].first;
    y = farm.hands[hand_index].second;
  }
  const Inventory* inventory =
      unit_index < static_cast<int>(priv.inventories.size())
          ? &priv.inventories[unit_index]
          : nullptr;
  const auto inventory_count = [inventory](int item_index) {
    return inventory == nullptr ? int64_t{0} : inventory->Get(item_index);
  };

  int dx = 0;
  int dy = 0;
  switch (requested.op) {
    case UnitOp::kNorth:
      dy = -1;
      break;
    case UnitOp::kSouth:
      dy = 1;
      break;
    case UnitOp::kEast:
      dx = 1;
      break;
    case UnitOp::kWest:
      dx = -1;
      break;
    default:
      break;
  }
  if (dx != 0 || dy != 0) {
    const int next_x = x + dx;
    const int next_y = y + dy;
    return next_x >= 0 && next_x < config.board_size && next_y >= 0 &&
           next_y < config.board_size;
  }
  if (requested.op == UnitOp::kPass) return true;

  if (requested.op == UnitOp::kDrop) {
    return IsShedAdjacent(x, y, config.board_size);
  }
  if (requested.op == UnitOp::kPickup) {
    return IsShedAdjacent(x, y, config.board_size) && requested.arg >= 0 &&
           requested.arg < kNumItems && requested.n > 0 &&
           priv.shed[requested.arg] > 0;
  }

  const Tile& tile = farm.tiles[y * config.board_size + x];
  if (requested.op == UnitOp::kPlace) {
    const int item_index = requested.arg;
    if (item_index < 0 || item_index >= kNumItems) return false;
    if (item_index >= item::kGoose && tile.kind == TileKind::kStructure &&
        !tile.has_animal &&
        tile.structure == kAnimals[item_index - item::kGoose].structure) {
      return inventory_count(item_index) > 0;
    }
    if (!IsShedAdjacent(x, y, config.board_size) || requested.n <= 0) {
      return false;
    }
    const int64_t room =
        std::max<int64_t>(0, config.shed_capacity - ShedTotal(priv));
    return std::min(requested.n, inventory_count(item_index)) > 0 && room > 0;
  }

  if (tile.kind == TileKind::kLocked) return false;
  switch (requested.op) {
    case UnitOp::kPlant:
      return requested.arg >= 0 && requested.arg < kNumCrops &&
             tile.kind == TileKind::kEmpty && priv.seeds[requested.arg] > 0;
    case UnitOp::kWater:
      return tile.kind == TileKind::kPlant && !tile.watered_today;
    case UnitOp::kHarvest:
      if (tile.kind == TileKind::kEmpty || tile.yield_units <= 0) return false;
      if (tile.kind == TileKind::kPlant) {
        return day - tile.planted_day >= kCrops[tile.crop].first_yield_day;
      }
      return tile.kind == TileKind::kStructure && tile.has_animal;
    case UnitOp::kFertilize:
      return tile.kind == TileKind::kPlant &&
             inventory_count(item::kFertilizer) > 0;
    case UnitOp::kDig:
      return tile.kind != TileKind::kEmpty &&
             !(tile.kind == TileKind::kStructure && tile.has_animal);
    case UnitOp::kBuildCoop:
    case UnitOp::kBuildPasture:
      return tile.kind == TileKind::kEmpty;
    case UnitOp::kFeed:
      return tile.kind == TileKind::kStructure && tile.has_animal &&
             !tile.fed_today && inventory_count(item::kWheat) > 0;
    case UnitOp::kCollectFertilizer:
      return tile.kind == TileKind::kStructure && tile.has_animal &&
             tile.fertilizer_available;
    case UnitOp::kCare:
      return tile.kind == TileKind::kStructure && tile.has_animal &&
             !tile.cared_today;
    default:
      return false;
  }
}

UnitActionTrace ApplyUnitAction(const Config& config, Farm* farm, PrivateState* priv,
                                int unit_index, const UnitAction& requested, int day) {
  if (requested.op == UnitOp::kInvalid) {
    return Rejected(unit_index, requested, UnitActionStatus::kMalformed);
  }

  int x;
  int y;
  if (unit_index == 0) {
    x = farm->farmer_x;
    y = farm->farmer_y;
  } else {
    const int hand_index = unit_index - 1;
    if (hand_index < 0 || hand_index >= static_cast<int>(farm->hands.size())) {
      return Rejected(unit_index, requested, UnitActionStatus::kGhostUnit);
    }
    x = farm->hands[hand_index].first;
    y = farm->hands[hand_index].second;
  }

  while (priv->inventories.size() <= static_cast<size_t>(unit_index)) {
    priv->inventories.emplace_back();
  }
  Inventory& inventory = priv->inventories[unit_index];

  int dx = 0;
  int dy = 0;
  switch (requested.op) {
    case UnitOp::kNorth:
      dy = -1;
      break;
    case UnitOp::kSouth:
      dy = 1;
      break;
    case UnitOp::kEast:
      dx = 1;
      break;
    case UnitOp::kWest:
      dx = -1;
      break;
    default:
      break;
  }
  if (dx != 0 || dy != 0) {
    const int next_x = x + dx;
    const int next_y = y + dy;
    if (next_x < 0 || next_x >= config.board_size || next_y < 0 ||
        next_y >= config.board_size) {
      return Rejected(unit_index, requested, UnitActionStatus::kIllegal);
    }
    if (unit_index == 0) {
      farm->farmer_x = next_x;
      farm->farmer_y = next_y;
    } else {
      farm->hands[unit_index - 1] = {next_x, next_y};
    }
    return UnitActionTrace{unit_index, requested, requested, UnitActionStatus::kApplied};
  }
  if (requested.op == UnitOp::kPass) {
    return UnitActionTrace{unit_index, requested, PassAction(), UnitActionStatus::kPass};
  }

  Tile& tile = farm->tiles[y * config.board_size + x];

  if (requested.op == UnitOp::kDrop) {
    if (!IsShedAdjacent(x, y, config.board_size)) {
      return Rejected(unit_index, requested, UnitActionStatus::kIllegal);
    }
    for (const auto& [item_index, count] : inventory.items) {
      const int64_t room = std::max<int64_t>(0, config.shed_capacity - ShedTotal(*priv));
      const int64_t take = std::min(count, room);
      if (take > 0) priv->shed[item_index] += take;
    }
    inventory.items.clear();
    return UnitActionTrace{unit_index, requested, requested, UnitActionStatus::kApplied};
  }

  if (requested.op == UnitOp::kPickup) {
    if (!IsShedAdjacent(x, y, config.board_size) || requested.arg < 0 ||
        requested.arg >= kNumItems || requested.n <= 0) {
      return Rejected(unit_index, requested, UnitActionStatus::kIllegal);
    }
    const int64_t count = std::min(requested.n, priv->shed[requested.arg]);
    if (count <= 0) return Rejected(unit_index, requested, UnitActionStatus::kIllegal);
    priv->shed[requested.arg] -= count;
    inventory.Add(requested.arg, count);
    UnitAction actual = requested;
    actual.n = count;
    return UnitActionTrace{unit_index, requested, actual, UnitActionStatus::kApplied};
  }

  if (requested.op == UnitOp::kPlace) {
    const int item_index = requested.arg;
    if (item_index < 0 || item_index >= kNumItems) {
      return Rejected(unit_index, requested, UnitActionStatus::kIllegal);
    }
    if (item_index >= item::kGoose && tile.kind == TileKind::kStructure &&
        !tile.has_animal &&
        tile.structure == kAnimals[item_index - item::kGoose].structure) {
      if (!inventory.Take(item_index, 1)) {
        return Rejected(unit_index, requested, UnitActionStatus::kIllegal);
      }
      tile = MakeAnimal(item_index - item::kGoose, day);
      UnitAction actual = requested;
      actual.n = 1;
      return UnitActionTrace{unit_index, requested, actual, UnitActionStatus::kApplied};
    }
    if (!IsShedAdjacent(x, y, config.board_size) || requested.n <= 0) {
      return Rejected(unit_index, requested, UnitActionStatus::kIllegal);
    }
    int64_t count = std::min(requested.n, inventory.Get(item_index));
    const int64_t room = std::max<int64_t>(0, config.shed_capacity - ShedTotal(*priv));
    count = std::min(count, room);
    if (count <= 0) return Rejected(unit_index, requested, UnitActionStatus::kIllegal);
    inventory.Take(item_index, count);
    priv->shed[item_index] += count;
    UnitAction actual = requested;
    actual.n = count;
    return UnitActionTrace{unit_index, requested, actual, UnitActionStatus::kApplied};
  }

  if (tile.kind == TileKind::kLocked) {
    return Rejected(unit_index, requested, UnitActionStatus::kIllegal);
  }

  switch (requested.op) {
    case UnitOp::kPlant: {
      if (requested.arg < 0 || requested.arg >= kNumCrops ||
          tile.kind != TileKind::kEmpty || priv->seeds[requested.arg] <= 0) {
        return Rejected(unit_index, requested, UnitActionStatus::kIllegal);
      }
      priv->seeds[requested.arg] -= 1;
      tile = MakePlant(requested.arg, day, config.turns_per_day);
      break;
    }
    case UnitOp::kWater: {
      if (tile.kind != TileKind::kPlant || tile.watered_today) {
        return Rejected(unit_index, requested, UnitActionStatus::kIllegal);
      }
      production::Water(tile, day);
      break;
    }
    case UnitOp::kHarvest: {
      if (tile.kind == TileKind::kEmpty) {
        return Rejected(unit_index, requested, UnitActionStatus::kIllegal);
      }
      const int yield_units =
          (tile.kind == TileKind::kPlant || tile.kind == TileKind::kStructure)
              ? tile.yield_units
              : 0;
      if (yield_units <= 0) {
        return Rejected(unit_index, requested, UnitActionStatus::kIllegal);
      }
      if (tile.kind == TileKind::kPlant) {
        const CropData& crop = kCrops[tile.crop];
        if (day - tile.planted_day < crop.first_yield_day) {
          return Rejected(unit_index, requested, UnitActionStatus::kIllegal);
        }
        tile.yield_units = 0;
        inventory.Add(tile.crop, yield_units);
        if (!crop.ongoing) tile = Tile{};
      } else if (tile.has_animal) {
        tile.yield_units = 0;
        inventory.Add(kAnimals[tile.animal].product, yield_units);
      } else {
        return Rejected(unit_index, requested, UnitActionStatus::kIllegal);
      }
      break;
    }
    case UnitOp::kFertilize:
      if (tile.kind != TileKind::kPlant || !inventory.Take(item::kFertilizer, 1)) {
        return Rejected(unit_index, requested, UnitActionStatus::kIllegal);
      }
      production::Fertilize(tile, day);
      break;
    case UnitOp::kDig:
      if (tile.kind == TileKind::kEmpty ||
          (tile.kind == TileKind::kStructure && tile.has_animal)) {
        return Rejected(unit_index, requested, UnitActionStatus::kIllegal);
      }
      tile = Tile{};
      break;
    case UnitOp::kBuildCoop:
      if (tile.kind != TileKind::kEmpty) {
        return Rejected(unit_index, requested, UnitActionStatus::kIllegal);
      }
      tile = MakeBareStructure(StructureKind::kCoop);
      break;
    case UnitOp::kBuildPasture:
      if (tile.kind != TileKind::kEmpty) {
        return Rejected(unit_index, requested, UnitActionStatus::kIllegal);
      }
      tile = MakeBareStructure(StructureKind::kPasture);
      break;
    case UnitOp::kFeed:
      if (!(tile.kind == TileKind::kStructure && tile.has_animal) || tile.fed_today ||
          !inventory.Take(item::kWheat, 1)) {
        return Rejected(unit_index, requested, UnitActionStatus::kIllegal);
      }
      tile.fed_today = true;
      break;
    case UnitOp::kCollectFertilizer:
      if (!(tile.kind == TileKind::kStructure && tile.has_animal) ||
          !tile.fertilizer_available) {
        return Rejected(unit_index, requested, UnitActionStatus::kIllegal);
      }
      tile.fertilizer_available = false;
      inventory.Add(item::kFertilizer, 1);
      break;
    case UnitOp::kCare:
      if (!(tile.kind == TileKind::kStructure && tile.has_animal) || tile.cared_today) {
        return Rejected(unit_index, requested, UnitActionStatus::kIllegal);
      }
      tile.cared_today = true;
      break;
    default:
      return Rejected(unit_index, requested, UnitActionStatus::kIllegal);
  }
  return UnitActionTrace{unit_index, requested, requested, UnitActionStatus::kApplied};
}

void ApplyPlayerUnitPhase(const Config& config, Farm* farm, PrivateState* priv,
                          const PlayerAction& action, int day) {
  const auto blocked = BlockedPlants(action, *priv);
  ApplyGatedUnitAction(config, farm, priv, 0, action.farmer, day, blocked);
  for (size_t hand = 0; hand < action.hands.size(); ++hand) {
    ApplyGatedUnitAction(config, farm, priv, static_cast<int>(hand) + 1,
                         action.hands[hand], day, blocked);
  }
}

UnitPhaseResult CompileUnitPhase(const Config& config, const Farm& farm,
                                 const PrivateState& priv, const PlayerAction& requested,
                                 int day) {
  UnitPhaseResult result;
  result.farm = farm;
  result.priv = priv;
  result.actual.hands.resize(farm.hands.size(), PassAction());

  const auto blocked = BlockedPlants(requested, priv);
  UnitActionTrace farmer = ApplyGatedUnitAction(config, &result.farm, &result.priv, 0,
                                                requested.farmer, day, blocked);
  result.actual.farmer = farmer.actual;
  result.trace.push_back(farmer);

  for (size_t hand = 0; hand < farm.hands.size(); ++hand) {
    const UnitAction intent =
        hand < requested.hands.size() ? requested.hands[hand] : PassAction();
    UnitActionTrace trace = ApplyGatedUnitAction(
        config, &result.farm, &result.priv, static_cast<int>(hand) + 1, intent, day, blocked);
    result.actual.hands[hand] = trace.actual;
    result.trace.push_back(trace);
  }
  for (size_t hand = farm.hands.size(); hand < requested.hands.size(); ++hand) {
    result.trace.push_back(ApplyGatedUnitAction(
        config, &result.farm, &result.priv, static_cast<int>(hand) + 1,
        requested.hands[hand], day, blocked));
  }
  return result;
}

}  // namespace kagg
