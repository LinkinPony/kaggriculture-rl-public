#include "tasks/session.hpp"

#include <algorithm>
#include <stdexcept>
#include <utility>

namespace kagg::tasks {
namespace {

int UnitCount(const Farm& farm) {
  return 1 + static_cast<int>(farm.hands.size());
}

std::pair<int, int> UnitPosition(const Farm& farm, int unit_index) {
  if (unit_index == 0) return {farm.farmer_x, farm.farmer_y};
  const int hand = unit_index - 1;
  if (hand < 0 || hand >= static_cast<int>(farm.hands.size())) {
    throw std::invalid_argument("unit-task unit index is outside the farm");
  }
  return farm.hands[hand];
}

int Day(const Config& config, int step) {
  return step / std::max(1, config.turns_per_day);
}

int Hour(const Config& config, int step) {
  return step % std::max(1, config.turns_per_day);
}

void ValidateState(const Config& config, const Farm& farm,
                   const PrivateState& priv, int step, int player) {
  const int units = UnitCount(farm);
  if (player < 0 || player > 1 || step < 0 ||
      farm.tiles.size() != static_cast<size_t>(config.board_size) *
                               config.board_size ||
      priv.inventories.size() < static_cast<size_t>(units)) {
    throw std::invalid_argument("unit-task visible state is malformed");
  }
}

}  // namespace

Session::Session(Config config, int unit_limit, int maximum_quantity)
    : config_(std::move(config)),
      unit_limit_(unit_limit),
      maximum_quantity_(maximum_quantity) {
  if (unit_limit_ < 1) {
    throw std::invalid_argument("unit-task unit limit must be positive");
  }
  if (maximum_quantity_ < 1) {
    throw std::invalid_argument(
        "unit-task maximum quantity must be positive");
  }
  prefix_capacity_ = unit_limit_ * std::max(1, config_.turns_per_day);
  catalog_ = BuildCatalog();
  if (catalog_.empty() || catalog_.front().operation != Operation::kEnd) {
    throw std::logic_error("unit-task catalog must begin with END");
  }
}

void Session::Reset() {
  units_.clear();
  pending_.clear();
  history_.clear();
  planning_ = PlanningState{};
  next_record_id_ = 1;
  player_ = -1;
  last_seen_step_ = -1;
  last_seen_day_ = -1;
  last_unit_count_ = 0;
  successful_tasks_ = 0;
  failed_tasks_ = 0;
  forced_ends_ = 0;
  last_action_step_ = -1;
  last_action_ = NumericUnitAction{};
}

void Session::TrimHistory() {
  while (static_cast<int>(history_.size()) > prefix_capacity_) {
    const auto removable = std::find_if(
        history_.begin(), history_.end(),
        [](const TaskRecord& record) { return record.status_token != 0; });
    if (removable == history_.end()) {
      throw std::logic_error(
          "unit-task active tape exceeds its derived history capacity");
    }
    history_.erase(removable);
  }
}

void Session::AppendRecord(int unit_index, const Task& task, int step) {
  history_.push_back(TaskRecord{unit_index, task, 0, step});
  TrimHistory();
}

void Session::UpdateRecord(uint64_t record_id, ResultStatus result, int step) {
  for (auto iterator = history_.rbegin(); iterator != history_.rend();
       ++iterator) {
    if (iterator->task.record_id == record_id) {
      iterator->status_token = 1 + static_cast<int>(result);
      iterator->step = step;
      return;
    }
  }
}

void Session::ClearTape(int unit_index, ResultStatus result, int step) {
  if (unit_index < 0 || unit_index >= static_cast<int>(units_.size())) return;
  UnitState& unit = units_[unit_index];
  for (const Task& task : unit.tape) {
    UpdateRecord(task.record_id, result, step);
  }
  unit.tape.clear();
}

void Session::MarkReplan(int unit_index, ReplanReason reason, bool optional) {
  if (unit_index < 0 || unit_index >= static_cast<int>(units_.size())) return;
  UnitState& unit = units_[unit_index];
  if (unit.replan && !unit.optional) return;
  unit.replan = true;
  unit.optional = optional;
  unit.reason = reason;
}

void Session::CompleteHead(int unit_index, ResultStatus result, int step,
                           ReplanReason reason) {
  UnitState& unit = units_.at(static_cast<size_t>(unit_index));
  if (unit.tape.empty()) return;
  const Task completed = unit.tape.front();
  unit.tape.pop_front();
  UpdateRecord(completed.record_id, result, step);
  if (result == ResultStatus::kCompleted) {
    ++successful_tasks_;
    MarkReplan(unit_index, reason, !unit.tape.empty());
    return;
  }
  ++failed_tasks_;
  ClearTape(unit_index, ResultStatus::kReplaced, step);
  MarkReplan(unit_index, reason, false);
}

void Session::Refresh(const Farm& farm, const PrivateState& priv, int step,
                      int player) {
  ValidateState(config_, farm, priv, step, player);
  if (player < 0 || player > 1) {
    throw std::invalid_argument("unit-task player must be 0 or 1");
  }
  if ((player_ >= 0 && player_ != player) ||
      (last_seen_step_ >= 0 &&
       (step < last_seen_step_ || step > last_seen_step_ + 1))) {
    Reset();
  }
  player_ = player;
  if (last_seen_step_ == step) return;

  const int count = UnitCount(farm);
  if (count > unit_limit_) {
    throw std::runtime_error(
        "unit-task actor unit capacity is below the visible unit count");
  }
  const int day = Day(config_, step);
  if (last_seen_step_ < 0) {
    units_.resize(static_cast<size_t>(count));
    pending_.resize(static_cast<size_t>(count));
    last_unit_count_ = count;
    last_seen_day_ = day;
    last_seen_step_ = step;
    for (int unit = 0; unit < count; ++unit) {
      MarkReplan(unit, ReplanReason::kDayStart, false);
    }
    return;
  }

  for (int unit = 0; unit < std::min(last_unit_count_, count); ++unit) {
    PendingOperation& pending = pending_[unit];
    if (!pending.active) continue;
    if (pending.step + 1 != step) {
      ClearTape(unit, ResultStatus::kNoOp, step);
      MarkReplan(unit, ReplanReason::kOperationFailed, false);
    } else if (pending.result == ResultStatus::kCompleted) {
      CompleteHead(unit, pending.result, step,
                   ReplanReason::kTaskCompleted);
    } else {
      const ReplanReason reason =
          pending.result == ResultStatus::kTargetInvalid
              ? ReplanReason::kTargetInvalid
              : ReplanReason::kOperationFailed;
      CompleteHead(unit, pending.result, step, reason);
    }
    pending = PendingOperation{};
  }

  if (day != last_seen_day_) {
    for (int unit = 0; unit < static_cast<int>(units_.size()); ++unit) {
      ClearTape(unit, ResultStatus::kDayEnded, step);
    }
    units_.assign(static_cast<size_t>(count), UnitState{});
    pending_.assign(static_cast<size_t>(count), PendingOperation{});
    planning_ = PlanningState{};
    for (int unit = 0; unit < count; ++unit) {
      MarkReplan(unit, ReplanReason::kDayStart, false);
    }
  } else {
    if (count < last_unit_count_) {
      for (int unit = count; unit < last_unit_count_; ++unit) {
        ClearTape(unit, ResultStatus::kUnitRemoved, step);
      }
      units_.resize(static_cast<size_t>(count));
      pending_.resize(static_cast<size_t>(count));
      if (planning_.active && planning_.unit_index >= count) {
        planning_ = PlanningState{};
      }
    } else if (count > last_unit_count_) {
      units_.resize(static_cast<size_t>(count));
      pending_.resize(static_cast<size_t>(count));
      for (int unit = last_unit_count_; unit < count; ++unit) {
        MarkReplan(unit, ReplanReason::kNewUnit, false);
      }
    }

    for (int unit = 0; unit < count; ++unit) {
      UnitState& state = units_[unit];
      if (state.replan || pending_[unit].active) continue;
      const auto [x, y] = UnitPosition(farm, unit);
      if (!state.tape.empty()) {
        const Task& task = state.tape.front();
        const bool reached =
            task.operation == Operation::kWait || (x == task.x && y == task.y);
        if (!IsOfficial(task.operation) && reached &&
            Hour(config_, step) >= task.earliest) {
          CompleteHead(unit, ResultStatus::kCompleted, step,
                       ReplanReason::kTaskCompleted);
          continue;
        }
        const int distance = task.operation == Operation::kWait
                                 ? 0
                                 : ManhattanDistance(x, y, task.x, task.y);
        const int completion =
            std::max(Hour(config_, step) + distance, task.earliest) +
            (IsOfficial(task.operation) ? 1 : 0);
        if (completion > task.deadline ||
            completion > config_.turns_per_day) {
          CompleteHead(unit, ResultStatus::kMissedDeadline, step,
                       ReplanReason::kDeadlineMissed);
          continue;
        }
      }
      if (state.tape.empty() && state.ended_step != step) {
        MarkReplan(unit, ReplanReason::kQueueEmpty, false);
      }
    }
  }

  last_unit_count_ = count;
  last_seen_day_ = day;
  last_seen_step_ = step;
  last_action_step_ = -1;
}

void Session::StartPlanning(const Farm& farm, int step) {
  if (planning_.active) return;
  for (int unit = 0; unit < static_cast<int>(units_.size()); ++unit) {
    if (!units_[unit].replan) continue;
    const auto [x, y] = UnitPosition(farm, unit);
    planning_.active = true;
    planning_.first = true;
    planning_.unit_index = unit;
    planning_.x = x;
    planning_.y = y;
    planning_.available_at = Hour(config_, step);
    planning_.tasks.clear();
    return;
  }
}

void Session::FinishPlanningUnit(const Farm& farm, int step) {
  if (!planning_.active) return;
  UnitState& unit = units_[planning_.unit_index];
  unit.replan = false;
  unit.optional = false;
  if (unit.tape.empty()) unit.ended_step = step;
  planning_ = PlanningState{};
  StartPlanning(farm, step);
}

bool Session::DecisionRequired(const Engine& engine, int player) {
  return DecisionRequired(engine.farm(player), engine.priv(player),
                          engine.step_index(), player);
}

bool Session::DecisionRequired(const Farm& farm, const PrivateState& priv,
                               int step, int player) {
  Refresh(farm, priv, step, player);
  StartPlanning(farm, step);
  return planning_.active;
}

Decision Session::Observe(const Engine& engine, int player) {
  return Observe(engine.farm(player), engine.priv(player), engine.step_index(),
                 player);
}

Decision Session::ObserveCompact(const Engine& engine, int player) {
  return ObserveCompact(engine.farm(player), engine.priv(player),
                        engine.step_index(), player);
}

Decision Session::Observe(const Farm& farm, const PrivateState& priv, int step,
                          int player) {
  Refresh(farm, priv, step, player);
  StartPlanning(farm, step);
  if (!planning_.active) {
    throw std::logic_error("unit-task observation requested without a decision");
  }
  return BuildDecision(farm, priv, step, true);
}

Decision Session::ObserveCompact(const Farm& farm, const PrivateState& priv,
                                 int step, int player) {
  Refresh(farm, priv, step, player);
  StartPlanning(farm, step);
  if (!planning_.active) {
    throw std::logic_error(
        "compact unit-task observation requested without a decision");
  }
  return BuildDecision(farm, priv, step, false);
}

void Session::Select(const Engine& engine, int player, SuffixMode mode,
                     int candidate_index, int64_t quantity, int earliest,
                     int deadline) {
  Select(engine.farm(player), engine.priv(player), engine.step_index(), player,
         mode, candidate_index, quantity, earliest, deadline);
}

void Session::Select(const Farm& farm, const PrivateState& priv, int step,
                     int player, SuffixMode mode, int candidate_index,
                     int64_t quantity, int earliest, int deadline) {
  Refresh(farm, priv, step, player);
  StartPlanning(farm, step);
  ApplySelection(farm, step, mode, candidate_index, quantity, earliest,
                 deadline);
}

void Session::ApplySelection(const Farm& farm, int step, SuffixMode mode,
                             int candidate_index, int64_t quantity,
                             int earliest, int deadline) {
  if (!planning_.active) {
    throw std::logic_error("unit-task selection has no active decision");
  }
  if (mode != SuffixMode::kContinue && mode != SuffixMode::kRewrite) {
    throw std::invalid_argument("unit-task suffix mode is invalid");
  }
  if (planning_.first && mode == SuffixMode::kContinue) {
    const UnitState& unit = units_[planning_.unit_index];
    if (!unit.optional || unit.tape.empty()) {
      throw std::invalid_argument("unit-task suffix mode is masked");
    }
    if (candidate_index != 0 || quantity != 0 || earliest != 0 ||
        deadline != 0) {
      throw std::invalid_argument(
          "continued unit-task suffix requires canonical zero task fields");
    }
    FinishPlanningUnit(farm, step);
    return;
  }
  if (mode != SuffixMode::kRewrite) {
    throw std::invalid_argument("unit-task continuation is only a boundary choice");
  }
  if (planning_.first) {
    ClearTape(planning_.unit_index, ResultStatus::kReplaced,
              step);
    planning_.first = false;
  }
  if (candidate_index < 0 || candidate_index >= candidate_count()) {
    throw std::invalid_argument("unit-task selected candidate is masked");
  }
  const Candidate& candidate = catalog_[candidate_index];
  const int day_end = std::max(1, config_.turns_per_day);
  int arrival = planning_.available_at;
  int earliest_completion = planning_.available_at;
  bool feasible = true;
  if (candidate.operation == Operation::kWait) {
    earliest_completion = planning_.available_at + 1;
    feasible = earliest_completion <= day_end;
  } else if (candidate.operation != Operation::kEnd) {
    const int distance = ManhattanDistance(
        planning_.x, planning_.y, candidate.x, candidate.y);
    arrival += distance;
    earliest_completion =
        arrival + (IsOfficial(candidate.operation) ? 1 : 0);
    feasible = earliest_completion <= day_end &&
               !(candidate.operation == Operation::kPosition &&
                 distance == 0);
  }
  if (!feasible) {
    throw std::invalid_argument("unit-task selected candidate is masked");
  }
  if (candidate.operation == Operation::kEnd) {
    if (quantity != 0 || earliest != 0 || deadline != 0) {
      throw std::invalid_argument("unit-task END requires canonical zero fields");
    }
    // WAIT is feasible whenever any time remains, so END is forced exactly at
    // the day boundary.
    if (planning_.available_at >= day_end) {
      ++forced_ends_;
    }
    FinishPlanningUnit(farm, step);
    return;
  }

  if (NeedsQuantity(candidate.operation)) {
    if (quantity < 1 || quantity > maximum_quantity_) {
      throw std::invalid_argument("unit-task quantity is outside the artifact ABI");
    }
  } else if (quantity != 0) {
    throw std::invalid_argument("quantity-free unit task requires canonical zero");
  }
  const int available = planning_.available_at;
  if (earliest < available || earliest > config_.turns_per_day) {
    throw std::invalid_argument("unit-task earliest start is outside the day");
  }
  int completion = std::max(arrival, earliest);
  if (IsOfficial(candidate.operation)) ++completion;
  if (candidate.operation == Operation::kWait && earliest <= available) {
    throw std::invalid_argument("unit-task wait must advance its time line");
  }
  if (completion <= available || completion > config_.turns_per_day ||
      deadline < completion || deadline > config_.turns_per_day) {
    throw std::invalid_argument("unit task cannot finish by its deadline");
  }
  Task task;
  task.operation = candidate.operation;
  task.argument = candidate.argument;
  task.x = candidate.x;
  task.y = candidate.y;
  task.quantity = quantity;
  task.earliest = earliest;
  task.deadline = deadline;
  task.completion = completion;
  task.record_id = next_record_id_++;
  units_[planning_.unit_index].tape.push_back(task);
  planning_.tasks.push_back(task);
  planning_.available_at = completion;
  if (candidate.operation != Operation::kWait) {
    planning_.x = candidate.x;
    planning_.y = candidate.y;
  }
  AppendRecord(planning_.unit_index, task, step);
}

PlanningSnapshot Session::Snapshot(const Engine& engine, int player) {
  return Snapshot(engine.farm(player), engine.priv(player),
                  engine.step_index(), player);
}

PlanningSnapshot Session::Snapshot(const Farm& farm,
                                   const PrivateState& priv, int step,
                                   int player) {
  Refresh(farm, priv, step, player);
  StartPlanning(farm, step);
  PlanningSnapshot result;
  result.requires_decision = planning_.active;
  result.hour = Hour(config_, step);
  result.day = Day(config_, step);
  result.days = std::max(
      1, (config_.episode_steps + std::max(1, config_.turns_per_day) - 1) /
             std::max(1, config_.turns_per_day));
  result.unit_count = static_cast<int>(units_.size());
  result.history_count = static_cast<int>(history_.size());
  result.successful_tasks = successful_tasks_;
  result.failed_tasks = failed_tasks_;
  result.forced_ends = forced_ends_;
  result.prefix_fields.assign(
      static_cast<size_t>(prefix_capacity_) * kTaskFieldCount, int16_t{0});
  for (int row = 0; row < result.history_count; ++row) {
    const TaskRecord& record = history_[row];
    int16_t* fields = result.prefix_fields.data() +
                      static_cast<size_t>(row) * kTaskFieldCount;
    fields[0] = static_cast<int16_t>(record.unit_index);
    fields[1] = static_cast<int16_t>(record.task.operation);
    fields[2] = static_cast<int16_t>(record.task.argument + 1);
    fields[3] = static_cast<int16_t>(record.task.x + 1);
    fields[4] = static_cast<int16_t>(record.task.y + 1);
    fields[5] = static_cast<int16_t>(record.task.quantity);
    fields[6] = static_cast<int16_t>(record.task.earliest);
    fields[7] = static_cast<int16_t>(record.task.deadline);
    fields[8] = static_cast<int16_t>(record.status_token);
  }
  result.replan_mask.assign(static_cast<size_t>(unit_limit_), uint8_t{0});
  result.optional_mask.assign(static_cast<size_t>(unit_limit_), uint8_t{0});
  result.replan_reasons.assign(static_cast<size_t>(unit_limit_), int16_t{0});
  result.tape_sizes.assign(static_cast<size_t>(unit_limit_), int16_t{0});
  for (int unit = 0; unit < result.unit_count; ++unit) {
    const UnitState& state = units_[unit];
    result.replan_mask[unit] = state.replan ? 1 : 0;
    result.optional_mask[unit] = state.optional ? 1 : 0;
    result.replan_reasons[unit] = static_cast<int16_t>(state.reason);
    result.tape_sizes[unit] = static_cast<int16_t>(state.tape.size());
  }
  return result;
}

void Session::ApplySelections(const Engine& engine, int player,
                              const Selection* selections, int count) {
  ApplySelections(engine.farm(player), engine.priv(player),
                  engine.step_index(), player, selections, count);
}

void Session::ApplySelections(const Farm& farm, const PrivateState& priv,
                              int step, int player,
                              const Selection* selections, int count) {
  if (count < 0 || (count > 0 && selections == nullptr)) {
    throw std::invalid_argument("unit-task selection sequence is malformed");
  }
  Refresh(farm, priv, step, player);
  StartPlanning(farm, step);
  for (int index = 0; index < count; ++index) {
    const Selection& selection = selections[index];
    ApplySelection(farm, step, selection.mode, selection.candidate_index,
                   selection.quantity, selection.earliest,
                   selection.deadline);
  }
  if (planning_.active) {
    throw std::invalid_argument("unit-task selection sequence is incomplete");
  }
}

}  // namespace kagg::tasks
