#include "tasks/session.hpp"

#include <algorithm>
#include <stdexcept>

namespace kagg::tasks {
namespace {

std::pair<int, int> UnitPosition(const Farm& farm, int unit_index) {
  if (unit_index == 0) return {farm.farmer_x, farm.farmer_y};
  return farm.hands.at(static_cast<size_t>(unit_index - 1));
}

UnitAction Movement(int x, int y, int target_x, int target_y) {
  if (x < target_x) return UnitAction{UnitOp::kEast, -1, 1};
  if (x > target_x) return UnitAction{UnitOp::kWest, -1, 1};
  if (y < target_y) return UnitAction{UnitOp::kSouth, -1, 1};
  if (y > target_y) return UnitAction{UnitOp::kNorth, -1, 1};
  return UnitAction{UnitOp::kPass, -1, 1};
}

UnitOp OfficialOperation(Operation operation) {
  switch (operation) {
    case Operation::kPickup:
      return UnitOp::kPickup;
    case Operation::kDrop:
      return UnitOp::kDrop;
    case Operation::kPlace:
      return UnitOp::kPlace;
    case Operation::kPlant:
      return UnitOp::kPlant;
    case Operation::kWater:
      return UnitOp::kWater;
    case Operation::kHarvest:
      return UnitOp::kHarvest;
    case Operation::kFertilize:
      return UnitOp::kFertilize;
    case Operation::kDig:
      return UnitOp::kDig;
    case Operation::kBuildCoop:
      return UnitOp::kBuildCoop;
    case Operation::kBuildPasture:
      return UnitOp::kBuildPasture;
    case Operation::kFeed:
      return UnitOp::kFeed;
    case Operation::kCollectFertilizer:
      return UnitOp::kCollectFertilizer;
    case Operation::kCare:
      return UnitOp::kCare;
    default:
      throw std::invalid_argument(
          "unit-task operation has no official non-movement action");
  }
}

UnitAction OfficialAction(const Task& task) {
  return UnitAction{OfficialOperation(task.operation), task.argument,
                    NeedsQuantity(task.operation) ? task.quantity : 1};
}

const Inventory* UnitInventory(const PrivateState& priv, int unit_index) {
  if (unit_index < 0 ||
      unit_index >= static_cast<int>(priv.inventories.size())) {
    return nullptr;
  }
  return &priv.inventories[unit_index];
}

int64_t Carried(const Inventory* inventory, int item_index) {
  return inventory == nullptr ? int64_t{0} : inventory->Get(item_index);
}

bool ResourceMissing(const Config& config, const PrivateState& priv,
                     int unit_index, const Task& task) {
  const Inventory* inventory = UnitInventory(priv, unit_index);
  switch (task.operation) {
    case Operation::kPickup:
      return task.argument < 0 || task.argument >= kNumItems ||
             priv.shed[task.argument] <= 0;
    case Operation::kPlace:
      return task.argument < 0 || task.argument >= kNumItems ||
             Carried(inventory, task.argument) <= 0 ||
             (IsShedAdjacent(task.x, task.y, config.board_size) &&
              ShedTotal(priv) >= config.shed_capacity);
    case Operation::kPlant:
      return task.argument < 0 || task.argument >= kNumCrops ||
             priv.seeds[task.argument] <= 0;
    case Operation::kFertilize:
      return Carried(inventory, item::kFertilizer) <= 0;
    case Operation::kFeed:
      return Carried(inventory, item::kWheat) <= 0;
    default:
      return false;
  }
}

ResultStatus ResultForTrace(const Config& config, const PrivateState& priv,
                            int unit_index, const Task& task,
                            const UnitActionTrace& trace) {
  switch (trace.status) {
    case UnitActionStatus::kApplied:
      return ResultStatus::kCompleted;
    case UnitActionStatus::kAtomicPlantConflict:
      return ResultStatus::kResourceConflict;
    case UnitActionStatus::kIllegal:
      return ResourceMissing(config, priv, unit_index, task)
                 ? ResultStatus::kResourceConflict
                 : ResultStatus::kTargetInvalid;
    case UnitActionStatus::kPass:
    case UnitActionStatus::kMalformed:
    case UnitActionStatus::kGhostUnit:
      return ResultStatus::kNoOp;
  }
  return ResultStatus::kNoOp;
}

}  // namespace

NumericUnitAction Session::CompileAction(const Farm& farm,
                                         const PrivateState& priv, int step) {
  const int unit_count = 1 + static_cast<int>(farm.hands.size());
  PlayerAction requested;
  requested.hands.assign(static_cast<size_t>(unit_count - 1),
                         UnitAction{UnitOp::kPass, -1, 1});
  std::vector<bool> submitted(static_cast<size_t>(unit_count), false);
  for (int unit = 0; unit < unit_count; ++unit) {
    UnitAction action{UnitOp::kPass, -1, 1};
    UnitState& state = units_[unit];
    if (!state.tape.empty()) {
      const Task& task = state.tape.front();
      const auto [x, y] = UnitPosition(farm, unit);
      if (task.operation != Operation::kWait &&
          (x != task.x || y != task.y)) {
        action = Movement(x, y, task.x, task.y);
      } else if (step % std::max(1, config_.turns_per_day) <
                 task.earliest) {
        action = UnitAction{UnitOp::kPass, -1, 1};
      } else if (IsOfficial(task.operation)) {
        action = OfficialAction(task);
        submitted[unit] = true;
      }
    }
    if (unit == 0) {
      requested.farmer = action;
    } else {
      requested.hands[unit - 1] = action;
    }
  }

  const UnitPhaseResult compiled = CompileUnitPhase(
      config_, farm, priv, requested,
      step / std::max(1, config_.turns_per_day));
  NumericUnitAction result;
  result.unit_count = unit_count;
  result.tokens.resize(static_cast<size_t>(unit_count));
  result.quantities.resize(static_cast<size_t>(unit_count));
  result.task_results.assign(static_cast<size_t>(unit_count), int64_t{-1});
  const int decisions = policy::EncodePlayerAction(
      requested, unit_count, result.tokens.data(), result.quantities.data(),
      unit_count);
  if (decisions != unit_count ||
      compiled.trace.size() < static_cast<size_t>(unit_count)) {
    throw std::logic_error("unit-task compiler emitted an invalid unit prefix");
  }
  for (int unit = 0; unit < unit_count; ++unit) {
    if (!submitted[unit]) continue;
    if (units_[unit].tape.empty()) {
      throw std::logic_error("unit-task submitted operation lost its head task");
    }
    const Task& task = units_[unit].tape.front();
    const ResultStatus status =
        ResultForTrace(config_, priv, unit, task, compiled.trace[unit]);
    pending_[unit] = PendingOperation{
        true, step, task.record_id, status};
    result.task_results[unit] = static_cast<int64_t>(status);
  }
  return result;
}

NumericUnitAction Session::Action(const Engine& engine, int player) {
  return Action(engine.farm(player), engine.priv(player), engine.step_index(),
                player);
}

NumericUnitAction Session::Action(const Farm& farm, const PrivateState& priv,
                                  int step, int player) {
  Refresh(farm, priv, step, player);
  StartPlanning(farm, step);
  if (planning_.active) {
    NumericUnitAction blocked;
    blocked.unit_count = 1 + static_cast<int>(farm.hands.size());
    blocked.requires_decision = true;
    return blocked;
  }
  if (last_action_step_ == step) return last_action_;
  last_action_ = CompileAction(farm, priv, step);
  last_action_step_ = step;
  return last_action_;
}

}  // namespace kagg::tasks
