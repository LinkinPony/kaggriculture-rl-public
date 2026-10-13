#include "tasks/session.hpp"

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <stdexcept>
#include <unordered_map>
#include <utility>

namespace kagg::tasks {
namespace {

int UnitCount(const Farm& farm) {
  return 1 + static_cast<int>(farm.hands.size());
}

int Hour(const Config& config, int step) {
  return step % std::max(1, config.turns_per_day);
}

int ResourceKey(Operation operation, int argument, int unit_index) {
  switch (operation) {
    case Operation::kPlant:
      return 100 + argument;
    case Operation::kPickup:
      return 200 + argument;
    case Operation::kPlace:
      return 300 + unit_index * kNumItems + argument;
    case Operation::kFertilize:
      return 300 + unit_index * kNumItems + item::kFertilizer;
    case Operation::kFeed:
      return 300 + unit_index * kNumItems + item::kWheat;
    default:
      return -1;
  }
}

int ResourceKey(const Task& task, int unit_index) {
  return ResourceKey(task.operation, task.argument, unit_index);
}

const Inventory* UnitInventory(const PrivateState& priv, int unit_index) {
  if (unit_index < 0 ||
      unit_index >= static_cast<int>(priv.inventories.size())) {
    return nullptr;
  }
  return &priv.inventories[unit_index];
}

int64_t InventoryCount(const Inventory* inventory, int item_index) {
  return inventory == nullptr ? int64_t{0} : inventory->Get(item_index);
}

bool CurrentlyLegal(const Config& config, const Farm& farm,
                    const PrivateState& priv, int step, int unit_index,
                    const Candidate& candidate) {
  if (candidate.operation == Operation::kEnd ||
      candidate.operation == Operation::kWait ||
      candidate.operation == Operation::kPosition) {
    return true;
  }
  if (candidate.x < 0 || candidate.x >= config.board_size ||
      candidate.y < 0 || candidate.y >= config.board_size) {
    return false;
  }
  const Inventory* inventory = UnitInventory(priv, unit_index);
  const Tile& tile = farm.tiles[candidate.y * config.board_size + candidate.x];
  switch (candidate.operation) {
    case Operation::kPickup:
      return IsShedAdjacent(candidate.x, candidate.y, config.board_size) &&
             candidate.argument >= 0 && candidate.argument < kNumItems &&
             priv.shed[candidate.argument] > 0;
    case Operation::kDrop:
      return IsShedAdjacent(candidate.x, candidate.y, config.board_size);
    case Operation::kPlace: {
      if (candidate.argument < 0 || candidate.argument >= kNumItems) {
        return false;
      }
      const int64_t carried = InventoryCount(inventory, candidate.argument);
      if (candidate.argument >= item::kGoose &&
          tile.kind == TileKind::kStructure && !tile.has_animal &&
          tile.structure ==
              kAnimals[candidate.argument - item::kGoose].structure) {
        return carried > 0;
      }
      const int64_t room =
          std::max<int64_t>(0, config.shed_capacity - ShedTotal(priv));
      return IsShedAdjacent(candidate.x, candidate.y, config.board_size) &&
             carried > 0 && room > 0;
    }
    default:
      break;
  }
  if (tile.kind == TileKind::kLocked) return false;
  const int day = step / std::max(1, config.turns_per_day);
  switch (candidate.operation) {
    case Operation::kPlant:
      return candidate.argument >= 0 && candidate.argument < kNumCrops &&
             tile.kind == TileKind::kEmpty &&
             priv.seeds[candidate.argument] > 0;
    case Operation::kWater:
      return tile.kind == TileKind::kPlant && !tile.watered_today;
    case Operation::kHarvest:
      if (tile.yield_units <= 0) return false;
      if (tile.kind == TileKind::kPlant) {
        return day - tile.planted_day >=
               kCrops[tile.crop].first_yield_day;
      }
      return tile.kind == TileKind::kStructure && tile.has_animal;
    case Operation::kFertilize:
      return tile.kind == TileKind::kPlant &&
             InventoryCount(inventory, item::kFertilizer) > 0;
    case Operation::kDig:
      return tile.kind != TileKind::kEmpty &&
             !(tile.kind == TileKind::kStructure && tile.has_animal);
    case Operation::kBuildCoop:
    case Operation::kBuildPasture:
      return tile.kind == TileKind::kEmpty;
    case Operation::kFeed:
      return tile.kind == TileKind::kStructure && tile.has_animal &&
             !tile.fed_today &&
             InventoryCount(inventory, item::kWheat) > 0;
    case Operation::kCollectFertilizer:
      return tile.kind == TileKind::kStructure && tile.has_animal &&
             tile.fertilizer_available;
    case Operation::kCare:
      return tile.kind == TileKind::kStructure && tile.has_animal &&
             !tile.cared_today;
    default:
      return false;
  }
}

float Ratio(double numerator, double denominator) {
  return static_cast<float>(numerator / std::max(1.0, denominator));
}

}  // namespace

Decision Session::BuildDecision(const Farm& farm, const PrivateState& priv,
                                int step,
                                bool include_candidate_surface) const {
  if (!planning_.active || planning_.unit_index < 0 ||
      planning_.unit_index >= static_cast<int>(units_.size())) {
    throw std::logic_error("unit-task decision lacks a planning cursor");
  }
  const int unit = planning_.unit_index;
  const UnitState& unit_state = units_[unit];
  const int day_end = std::max(1, config_.turns_per_day);
  Decision result;
  result.unit_index = unit;
  result.current_x = planning_.x;
  result.current_y = planning_.y;
  result.available_at = planning_.available_at;
  result.day_end = day_end;
  result.replan_reason = static_cast<int>(unit_state.reason);
  result.mode_mask[static_cast<int>(SuffixMode::kRewrite)] = 1;
  if (planning_.first && unit_state.optional && !unit_state.tape.empty()) {
    result.mode_mask[static_cast<int>(SuffixMode::kContinue)] = 1;
  }

  std::vector<int> target_conflicts(
      static_cast<size_t>(config_.board_size) * config_.board_size, 0);
  std::unordered_map<int, int> resource_conflicts;
  const auto declare = [&](const Task& task, int owner) {
    if (task.x >= 0 && task.x < config_.board_size && task.y >= 0 &&
        task.y < config_.board_size) {
      ++target_conflicts[static_cast<size_t>(task.y) * config_.board_size +
                         task.x];
    }
    const int resource = ResourceKey(task, owner);
    if (resource >= 0) ++resource_conflicts[resource];
  };
  for (int other = 0; other < static_cast<int>(units_.size()); ++other) {
    if (other == unit) continue;
    for (const Task& task : units_[other].tape) declare(task, other);
  }
  for (const Task& task : planning_.tasks) declare(task, unit);
  result.target_conflicts.assign(target_conflicts.begin(),
                                 target_conflicts.end());
  result.resource_conflicts.assign(kCompactResourceCount, int16_t{0});
  const auto compact_conflict = [&resource_conflicts](int resource) {
    const auto found = resource_conflicts.find(resource);
    return found == resource_conflicts.end() ? 0 : found->second;
  };
  for (int crop = 0; crop < kNumCrops; ++crop) {
    result.resource_conflicts[crop] =
        static_cast<int16_t>(compact_conflict(100 + crop));
  }
  for (int item_index = 0; item_index < kNumItems; ++item_index) {
    result.resource_conflicts[kNumCrops + item_index] =
        static_cast<int16_t>(compact_conflict(200 + item_index));
    result.resource_conflicts[kNumCrops + kNumItems + item_index] =
        static_cast<int16_t>(
            compact_conflict(300 + unit * kNumItems + item_index));
  }

  const int candidates = include_candidate_surface ? candidate_count() : 0;
  result.candidate_mask.assign(static_cast<size_t>(candidates), 0);
  result.candidate_arrivals.assign(static_cast<size_t>(candidates), 0);
  result.candidate_reasons.assign(static_cast<size_t>(candidates), 0);
  result.candidate_features.assign(
      static_cast<size_t>(candidates) * kCandidateFeatureCount, 0.0F);
  for (int index = 0; index < candidates; ++index) {
    const Candidate& candidate = catalog_[index];
    FeasibilityReason reason = FeasibilityReason::kFeasible;
    int arrival = planning_.available_at;
    int completion = planning_.available_at;
    int wait = 0;
    if (candidate.operation == Operation::kEnd) {
      reason = FeasibilityReason::kEnd;
    } else if (candidate.operation == Operation::kWait) {
      completion = planning_.available_at + 1;
      wait = 1;
      if (completion > day_end) reason = FeasibilityReason::kOutOfTime;
    } else {
      const int distance = ManhattanDistance(
          planning_.x, planning_.y, candidate.x, candidate.y);
      arrival = planning_.available_at + distance;
      completion = arrival + (IsOfficial(candidate.operation) ? 1 : 0);
      if (candidate.operation == Operation::kPosition && distance == 0) {
        reason = FeasibilityReason::kNoProgress;
      } else if (completion > day_end) {
        reason = FeasibilityReason::kOutOfTime;
      }
    }
    const bool feasible = reason == FeasibilityReason::kFeasible ||
                          reason == FeasibilityReason::kEnd;
    result.candidate_mask[index] = feasible ? 1 : 0;
    result.candidate_arrivals[index] = arrival;
    result.candidate_reasons[index] = static_cast<int64_t>(reason);
    const int distance = candidate.x < 0
                             ? 0
                             : ManhattanDistance(planning_.x, planning_.y,
                                                 candidate.x, candidate.y);
    const int target_conflict =
        candidate.x < 0
            ? 0
            : target_conflicts[static_cast<size_t>(candidate.y) *
                                   config_.board_size +
                               candidate.x];
    const int resource =
        ResourceKey(candidate.operation, candidate.argument, unit);
    const auto resource_iterator = resource_conflicts.find(resource);
    const int resource_conflict =
        resource_iterator == resource_conflicts.end()
            ? 0
            : resource_iterator->second;
    float* features = result.candidate_features.data() +
                      static_cast<size_t>(index) * kCandidateFeatureCount;
    features[0] = 1.0F;
    features[1] = Ratio(distance, day_end);
    features[2] = Ratio(arrival, day_end);
    features[3] = Ratio(completion, day_end);
    features[4] = Ratio(std::max(0, day_end - completion), day_end);
    features[5] = Ratio(wait, day_end);
    features[6] = feasible ? 1.0F : 0.0F;
    features[7] =
        CurrentlyLegal(config_, farm, priv, step, unit, candidate) ? 1.0F
                                                                   : 0.0F;
    features[8] = Ratio(target_conflict, std::max(1, unit_limit_ - 1));
    features[9] = Ratio(resource_conflict, std::max(1, unit_limit_ - 1));
    if (reason == FeasibilityReason::kFeasible) features[10] = 1.0F;
    if (reason == FeasibilityReason::kEnd) features[11] = 1.0F;
    if (reason == FeasibilityReason::kOutOfTime) features[12] = 1.0F;
    if (reason == FeasibilityReason::kNoProgress) features[13] = 1.0F;
    if (reason == FeasibilityReason::kInvalidGeometry) features[14] = 1.0F;
    if (candidate.x >= 0) {
      features[15] = Ratio(candidate.x, config_.board_size - 1);
      features[16] = Ratio(candidate.y, config_.board_size - 1);
    }
    features[17] = IsOfficial(candidate.operation) ? 1.0F : 0.0F;
  }
  if (include_candidate_surface && !result.candidate_mask.front()) {
    throw std::logic_error("unit-task END must remain legal");
  }

  result.prefix_fields.assign(
      static_cast<size_t>(prefix_capacity_) * kTaskFieldCount, 0);
  result.prefix_mask.assign(static_cast<size_t>(prefix_capacity_), 0);
  const int records = std::min(prefix_capacity_,
                               static_cast<int>(history_.size()));
  const int first = static_cast<int>(history_.size()) - records;
  for (int row = 0; row < records; ++row) {
    const TaskRecord& record = history_[first + row];
    int64_t* fields = result.prefix_fields.data() +
                      static_cast<size_t>(row) * kTaskFieldCount;
    fields[0] = record.unit_index;
    fields[1] = static_cast<int64_t>(record.task.operation);
    fields[2] = record.task.argument + 1;
    fields[3] = record.task.x + 1;
    fields[4] = record.task.y + 1;
    fields[5] = record.task.quantity;
    fields[6] = record.task.earliest;
    fields[7] = record.task.deadline;
    fields[8] = record.status_token;
    result.prefix_mask[row] = 1;
  }

  const int turns = std::max(1, config_.turns_per_day);
  const int days = std::max(1, (config_.episode_steps + turns - 1) / turns);
  result.root_features[0] = Ratio(Hour(config_, step), turns);
  result.root_features[1] = Ratio(step / turns, days);
  result.root_features[2] = Ratio(unit, std::max(1, unit_limit_ - 1));
  result.root_features[3] = Ratio(UnitCount(farm), unit_limit_);
  result.root_features[4] = Ratio(planning_.x, config_.board_size - 1);
  result.root_features[5] = Ratio(planning_.y, config_.board_size - 1);
  result.root_features[6] = Ratio(planning_.available_at, turns);
  result.root_features[7] =
      Ratio(std::max(0, turns - planning_.available_at), turns);
  result.root_features[8] = Ratio(planning_.tasks.size(), turns);
  result.root_features[9] = Ratio(unit_state.tape.size(), turns);
  result.root_features[10] = Ratio(records, prefix_capacity_);
  const int completed = successful_tasks_ + failed_tasks_;
  result.root_features[11] = Ratio(successful_tasks_, std::max(1, completed));
  result.root_features[12] = Ratio(failed_tasks_, std::max(1, completed));
  result.root_features[13] = Ratio(forced_ends_, std::max(1, completed));
  const int reason = static_cast<int>(unit_state.reason);
  if (reason >= 0 && reason < 7) result.root_features[14 + reason] = 1.0F;
  result.root_features[21] = result.mode_mask[0] ? 1.0F : 0.0F;
  result.root_features[22] = result.mode_mask[1] ? 1.0F : 0.0F;
  result.root_features[23] = planning_.first ? 1.0F : 0.0F;
  return result;
}

}  // namespace kagg::tasks
