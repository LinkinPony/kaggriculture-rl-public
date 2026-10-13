#include "effects/session.hpp"

#include <algorithm>
#include <array>
#include <cstdint>
#include <limits>
#include <stdexcept>
#include <tuple>
#include <utility>
#include <vector>

#include "effects/internal.hpp"

namespace kagg::effects {
namespace {

bool TraceCompletes(const Job& job, const UnitActionTrace& trace,
                    const Farm& post_farm, int board_size) {
  if (job.kind == RequestKind::kStage) {
    const auto actual = internal::UnitPosition(post_farm, job.unit);
    return actual == internal::TargetPosition(job.target, board_size);
  }
  if (trace.status != UnitActionStatus::kApplied) return false;
  if (job.kind == RequestKind::kBank) {
    return trace.actual.op == UnitOp::kDrop;
  }
  if (job.kind == RequestKind::kLoad) {
    return trace.actual.op == UnitOp::kPickup &&
           trace.actual.arg == job.item && trace.actual.n == job.quantity;
  }
  if (job.kind == RequestKind::kUnload) {
    return trace.actual.op == UnitOp::kPlace &&
           trace.actual.arg == job.item && trace.actual.n == job.quantity;
  }
  return trace.actual.op == internal::EffectAction(job.kind, job.item).op;
}

}  // namespace

void Session::FinalizeWork(const Engine& engine, int player) {
  if (phase_ != Phase::kWork) {
    throw std::logic_error("effect work phase was already finalized");
  }
  std::vector<uint64_t> cancelled;
  for (const SemanticAction& action : turn_work_) {
    if (action.kind == RequestKind::kCancel) cancelled.push_back(action.job_id);
  }
  jobs_.erase(std::remove_if(jobs_.begin(), jobs_.end(), [&](const Job& job) {
                return std::find(cancelled.begin(), cancelled.end(), job.id) !=
                       cancelled.end();
              }),
              jobs_.end());

  const Farm& farm = engine.farm(player);
  const PrivateState& priv = engine.priv(player);
  const int day_remaining =
      config_.turns_per_day - engine.step_index() % config_.turns_per_day;
  std::vector<uint8_t> busy(priv.inventories.size(), 0);
  for (const Job& job : jobs_) {
    if (job.unit >= 0 && job.unit < static_cast<int>(busy.size())) {
      busy[job.unit] = 1;
    }
  }
  std::array<int64_t, kNumItems> reserved_shed{};
  for (int rank = 0; rank < static_cast<int>(selected_work_.size()); ++rank) {
    const Candidate& candidate = candidates_[selected_work_[rank]];
    if (candidate.kind == RequestKind::kCancel) continue;
    const internal::AssignmentPlan plan = internal::BestAssignment(
        config_, farm, priv, candidate, busy, reserved_shed, day_remaining);
    if (plan.unit < 0) {
      throw std::logic_error(
          "effect hard mask accepted an unassignable request");
    }
    const int item_index = static_cast<int>(candidate.fields[2]) - 1;
    const int required = internal::RequiredItem(candidate.kind, item_index);
    if (plan.uses_shed && required >= 0) ++reserved_shed[required];
    busy[plan.unit] = 1;
    Job job{
        .id = next_job_id_++,
        .kind = candidate.kind,
        .target = static_cast<int>(candidate.fields[1]),
        .item = item_index,
        .unit = plan.unit,
        .created_step = engine.step_index(),
        .priority = rank,
        .quantity = candidate.fields[3],
    };
    jobs_.push_back(job);
    SemanticAction& action = turn_work_[rank];
    action.job_id = job.id;
    action.unit = job.unit;
  }

  const UnitPhaseResult compiled = CompileJobs(engine, player);
  compiled_action_ = compiled.actual;
  projected_farm_ = compiled.farm;
  projected_priv_ = compiled.priv;
  projected_market_ = engine.market();
  compiled_ready_ = true;
  phase_ = Phase::kMarket;
  GenerateMarketCandidates(engine, player);
}

UnitPhaseResult Session::CompileJobs(const Engine& engine, int player) {
  const Farm& farm = engine.farm(player);
  const PrivateState& priv = engine.priv(player);
  const int day = engine.step_index() / config_.turns_per_day;
  const int unit_count = static_cast<int>(priv.inventories.size());
  PlayerAction requested;
  requested.hands.resize(farm.hands.size(), {UnitOp::kPass, -1, 1});
  std::vector<int> job_for_unit(static_cast<std::size_t>(unit_count), -1);
  std::vector<int> order(jobs_.size());
  for (int index = 0; index < static_cast<int>(jobs_.size()); ++index) {
    order[index] = index;
  }
  std::stable_sort(order.begin(), order.end(), [&](int left, int right) {
    const Job& a = jobs_[left];
    const Job& b = jobs_[right];
    return std::tie(a.created_step, a.priority, a.id) <
           std::tie(b.created_step, b.priority, b.id);
  });

  std::array<int64_t, kNumItems> reserved_pickups{};
  std::array<int64_t, kNumCrops> reserved_plants{};
  for (const int job_index : order) {
    const Job& job = jobs_[job_index];
    if (job.unit < 0 || job.unit >= unit_count ||
        job_for_unit[job.unit] >= 0) {
      continue;
    }
    job_for_unit[job.unit] = job_index;
    const auto [x, y] = internal::UnitPosition(farm, job.unit);
    UnitAction action{UnitOp::kPass, -1, 1};
    if (job.kind == RequestKind::kStage) {
      const auto target =
          internal::TargetPosition(job.target, config_.board_size);
      action = internal::MoveToward(x, y, target.first, target.second);
    } else if (job.kind == RequestKind::kBank) {
      const int64_t load = internal::InventoryTotal(priv.inventories[job.unit]);
      if (load > 0) {
        const auto shed = internal::NearestShed(x, y, config_.board_size);
        action = x == shed.first && y == shed.second
                     ? UnitAction{UnitOp::kDrop, -1, 1}
                     : internal::MoveToward(x, y, shed.first, shed.second);
      }
    } else if (job.kind == RequestKind::kLoad) {
      if (job.item >= 0 && job.item < kNumItems && job.quantity > 0) {
        const auto shed = internal::NearestShed(x, y, config_.board_size);
        action = x == shed.first && y == shed.second
                     ? UnitAction{UnitOp::kPickup, job.item, job.quantity}
                     : internal::MoveToward(x, y, shed.first, shed.second);
        if (action.op == UnitOp::kPickup) {
          reserved_pickups[job.item] += job.quantity;
        }
      }
    } else if (job.kind == RequestKind::kUnload) {
      if (job.item >= 0 && job.item < kNumItems && job.quantity > 0 &&
          priv.inventories[job.unit].Get(job.item) >= job.quantity) {
        const auto shed = internal::NearestShed(x, y, config_.board_size);
        action = x == shed.first && y == shed.second
                     ? UnitAction{UnitOp::kPlace, job.item, job.quantity}
                     : internal::MoveToward(x, y, shed.first, shed.second);
      }
    } else if (internal::TargetSupports(farm, day, job.kind, job.target,
                                        job.item)) {
      const int required = internal::RequiredItem(job.kind, job.item);
      const auto target =
          internal::TargetPosition(job.target, config_.board_size);
      if (required >= 0 && priv.inventories[job.unit].Get(required) <= 0) {
        if (priv.shed[required] - reserved_pickups[required] > 0) {
          const auto shed = internal::BestShedForRoute(
              x, y, target.first, target.second, config_.board_size);
          if (x == shed.first && y == shed.second) {
            action = {UnitOp::kPickup, required, 1};
            ++reserved_pickups[required];
          } else {
            action = internal::MoveToward(x, y, shed.first, shed.second);
          }
        }
      } else if (x != target.first || y != target.second) {
        action = internal::MoveToward(x, y, target.first, target.second);
      } else if (job.kind == RequestKind::kPlant) {
        if (job.item >= 0 && job.item < kNumCrops &&
            priv.seeds[job.item] - reserved_plants[job.item] > 0) {
          action = internal::EffectAction(job.kind, job.item);
          ++reserved_plants[job.item];
        }
      } else {
        action = internal::EffectAction(job.kind, job.item);
      }
    }
    if (job.unit == 0) {
      requested.farmer = action;
    } else {
      requested.hands[job.unit - 1] = action;
    }
  }

  UnitPhaseResult compiled =
      CompileUnitPhase(config_, farm, priv, requested, day);
  std::vector<uint64_t> completed;
  for (int unit = 0; unit < unit_count; ++unit) {
    const int job_index = job_for_unit[unit];
    if (job_index < 0) continue;
    const Job& job = jobs_[job_index];
    if (TraceCompletes(job, compiled.trace[unit], compiled.farm,
                       config_.board_size)) {
      completed.push_back(job.id);
    }
  }
  jobs_.erase(std::remove_if(jobs_.begin(), jobs_.end(), [&](const Job& job) {
                return std::find(completed.begin(), completed.end(), job.id) !=
                       completed.end();
              }),
              jobs_.end());
  return compiled;
}

}  // namespace kagg::effects
