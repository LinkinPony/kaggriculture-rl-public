#include "planner.hpp"

#include <algorithm>
#include <array>
#include <limits>
#include <map>
#include <set>
#include <string>
#include <tuple>
#include <unordered_map>
#include <unordered_set>

namespace kagg::planner {
namespace {

struct UnitView {
  int index = 0;
  std::pair<int, int> position;
  const Inventory* inventory = nullptr;
};

struct Candidate {
  const Task* task = nullptr;
  const Intent* intent = nullptr;
  std::string node;
};

using Identity = std::pair<std::string, std::string>;

int Distance(std::pair<int, int> left, std::pair<int, int> right) {
  return std::abs(left.first - right.first) +
         std::abs(left.second - right.second);
}

UnitAction MoveToward(std::pair<int, int> origin,
                      std::pair<int, int> target) {
  if (origin.first < target.first) return {UnitOp::kEast, -1, 1};
  if (origin.first > target.first) return {UnitOp::kWest, -1, 1};
  if (origin.second < target.second) return {UnitOp::kSouth, -1, 1};
  if (origin.second > target.second) return {UnitOp::kNorth, -1, 1};
  return {UnitOp::kPass, -1, 1};
}

bool Enabled(const Intent& intent) {
  return !intent.proposal_only && !intent.requires_command;
}

bool HasItem(const UnitView& unit, const Intent& intent) {
  return intent.required_item < 0 ||
         (unit.inventory != nullptr && unit.inventory->Get(intent.required_item) > 0);
}

bool IsHard(const Task& task, const Intent& intent) {
  return intent.hard || (intent.priority == 0 && task.priority >= 1000);
}

int Priority(const Task& task, const Intent& intent) {
  return intent.priority == 0 ? task.priority : intent.priority;
}

bool Ready(const Intent& intent, const std::set<std::string>& completed) {
  return std::all_of(intent.predecessors.begin(), intent.predecessors.end(),
                     [&](const std::string& predecessor) {
                       return completed.contains(predecessor);
                     });
}

int SameTileOrder(UnitOp op) {
  switch (op) {
    case UnitOp::kFertilize:
      return 0;
    case UnitOp::kWater:
      return 1;
    case UnitOp::kHarvest:
      return 2;
    case UnitOp::kDig:
      return 3;
    default:
      return 100;
  }
}

std::tuple<int, int, int, int, int, int, int, std::string, std::string, int>
CandidateRank(const UnitView& unit, const Candidate& candidate, int step,
              const std::unordered_map<int, Commitment>& commitments,
              SchedulerKind scheduler,
              const std::unordered_map<std::string, int>& territories) {
  const Task& task = *candidate.task;
  const Intent& intent = *candidate.intent;
  const int priority = Priority(task, intent);
  const int deadline = intent.deadline_step.value_or(
      task.deadline_step.value_or(step + 10'000));
  const auto commitment_it = commitments.find(unit.index);
  const bool same_commitment =
      commitment_it != commitments.end() &&
      commitment_it->second.kind == CommitmentKind::kTask &&
      commitment_it->second.task_key == task.key;
  int route_cost = Distance(unit.position, task.position);
  if (scheduler != SchedulerKind::kGreedy && commitment_it != commitments.end() &&
      commitment_it->second.kind == CommitmentKind::kTask && !same_commitment) {
    ++route_cost;
  }
  const bool route_priority = scheduler == SchedulerKind::kRouteAware ||
                              scheduler == SchedulerKind::kTerritoryAware;
  const int priority_band = route_priority ? 150 : 1;
  int territory_penalty = 0;
  const auto territory = territories.find(task.key);
  if (scheduler == SchedulerKind::kTerritoryAware &&
      !IsHard(task, intent) && territory != territories.end()) {
    territory_penalty = std::abs(unit.index - territory->second);
  }
  return {IsHard(task, intent) ? 0 : 1,
          std::max(0, deadline - step),
          -priority / priority_band,
          same_commitment ? 0 : 1,
          territory_penalty,
          task.layout_cost,
          route_cost,
          task.key,
          candidate.node,
          unit.index};
}

std::unordered_map<std::string, int> BuildTerritories(
    const PlannerStateView& state, const std::vector<Task>& tasks,
    const std::vector<UnitView>& units) {
  std::unordered_map<std::string, int> result;
  const int unit_count = static_cast<int>(units.size());
  if (unit_count <= 1) return result;
  std::vector<std::pair<int, int>> cells;
  std::map<std::pair<int, int>, int> route_index;
  for (int y = 0; y < state.config.board_size; ++y) {
    for (int offset = 0; offset < state.config.board_size; ++offset) {
      const int x = y % 2 == 0 ? offset : state.config.board_size - 1 - offset;
      const Tile& tile = state.farm.tiles[y * state.config.board_size + x];
      if (tile.kind == TileKind::kLocked) continue;
      route_index[{x, y}] = static_cast<int>(cells.size());
      cells.push_back({x, y});
    }
  }
  if (cells.empty()) return result;

  std::vector<UnitView> route_units = units;
  const int missing_position = static_cast<int>(cells.size());
  std::sort(route_units.begin(), route_units.end(), [&](const UnitView& left,
                                                        const UnitView& right) {
    const auto left_it = route_index.find(left.position);
    const auto right_it = route_index.find(right.position);
    const int left_route = left_it == route_index.end()
                               ? missing_position
                               : left_it->second;
    const int right_route = right_it == route_index.end()
                                ? missing_position
                                : right_it->second;
    return std::tuple(left_route, left.index) <
           std::tuple(right_route, right.index);
  });

  std::map<std::pair<int, int>, int> preferred;
  for (size_t index = 0; index < cells.size(); ++index) {
    const int midpoint = static_cast<int>(index * 2 + 1);
    const int slot = std::min(
        unit_count - 1,
        static_cast<int>((static_cast<int64_t>(midpoint) * unit_count) /
                         (2LL * static_cast<int>(cells.size()))));
    preferred[cells[index]] = route_units[slot].index;
  }
  for (const Task& task : tasks) {
    const auto it = preferred.find(task.position);
    if (it != preferred.end()) result[task.key] = it->second;
  }
  return result;
}

bool ConstraintsAllow(const Intent& intent,
                      const std::set<std::string>& claimed_exclusive,
                      const std::unordered_map<std::string, int>& claimed_resources) {
  if (!intent.exclusive_group.empty() &&
      claimed_exclusive.contains(intent.exclusive_group)) {
    return false;
  }
  if (!intent.resource_group.empty()) {
    const auto it = claimed_resources.find(intent.resource_group);
    const int used = it == claimed_resources.end() ? 0 : it->second;
    if (intent.resource_limit <= 0 || used >= intent.resource_limit) return false;
  }
  return true;
}

void Claim(const Intent& intent, std::set<std::string>* claimed_exclusive,
           std::unordered_map<std::string, int>* claimed_resources) {
  if (!intent.exclusive_group.empty()) {
    claimed_exclusive->insert(intent.exclusive_group);
  }
  if (!intent.resource_group.empty()) {
    ++(*claimed_resources)[intent.resource_group];
  }
}

std::vector<UnitView> Units(const Farm& farm, const PrivateState& priv) {
  std::vector<UnitView> units;
  units.reserve(1 + farm.hands.size());
  units.push_back(UnitView{0, {farm.farmer_x, farm.farmer_y},
                           priv.inventories.empty() ? nullptr
                                                    : &priv.inventories[0]});
  for (size_t index = 0; index < farm.hands.size(); ++index) {
    const int unit_index = static_cast<int>(index + 1);
    units.push_back(UnitView{
        unit_index, farm.hands[index],
        unit_index < static_cast<int>(priv.inventories.size())
            ? &priv.inventories[unit_index]
            : nullptr});
  }
  return units;
}

int64_t Carried(const std::vector<UnitView>& units, int item_index) {
  int64_t result = 0;
  for (const UnitView& unit : units) {
    if (unit.inventory != nullptr) result += unit.inventory->Get(item_index);
  }
  return result;
}

std::pair<int, int> NearestShed(std::pair<int, int> position,
                                int board_size) {
  const auto sheds = ShedAccessTiles(board_size);
  return *std::min_element(sheds.begin(), sheds.end(), [&](const auto& left,
                                                           const auto& right) {
    return std::tuple(Distance(position, left), left) <
           std::tuple(Distance(position, right), right);
  });
}

std::array<int64_t, kNumItems> ResourceDemand(
    const std::vector<Candidate>& candidates) {
  std::array<int64_t, kNumItems> result{};
  std::unordered_map<std::string, std::pair<int, int>> groups;
  for (const Candidate& candidate : candidates) {
    const Intent& intent = *candidate.intent;
    if (intent.required_item < 0 || !intent.allow_supply) continue;
    if (intent.resource_group.empty()) {
      ++result[intent.required_item];
    } else if (!groups.contains(intent.resource_group)) {
      groups[intent.resource_group] =
          {intent.required_item, std::max(1, intent.resource_limit)};
    }
  }
  for (const auto& [_, value] : groups) result[value.first] += value.second;
  return result;
}

bool RequiresItem(const Task& task, int item_index) {
  return std::any_of(task.intents.begin(), task.intents.end(),
                     [&](const Intent& intent) {
                       return Enabled(intent) &&
                              intent.required_item == item_index;
                     });
}

int ShedDistance(std::pair<int, int> position, int board_size) {
  const auto sheds = ShedAccessTiles(board_size);
  const auto closest =
      std::min_element(sheds.begin(), sheds.end(),
                       [&](const auto& left, const auto& right) {
                         return std::tuple(Distance(position, left), left) <
                                std::tuple(Distance(position, right), right);
                       });
  return closest == sheds.end() ? 0 : Distance(position, *closest);
}

std::vector<Candidate> OrderSupplyTargets(
    const std::vector<Candidate>& candidates, int item_index,
    int board_size, const std::set<Identity>& routed_nodes,
    const std::set<std::string>& bound_tasks) {
  std::vector<Candidate> remaining;
  for (const Candidate& candidate : candidates) {
    const Identity identity{candidate.task->key, candidate.node};
    if (candidate.intent->required_item == item_index &&
        candidate.intent->allow_supply && !routed_nodes.contains(identity) &&
        !bound_tasks.contains(candidate.task->key)) {
      remaining.push_back(candidate);
    }
  }

  std::vector<Candidate> result;
  std::optional<std::pair<int, int>> cursor;
  while (!remaining.empty()) {
    const auto selected = std::min_element(
        remaining.begin(), remaining.end(),
        [&](const Candidate& left, const Candidate& right) {
          const auto rank = [&](const Candidate& candidate) {
            const Task& task = *candidate.task;
            const Intent& intent = *candidate.intent;
            const int deadline = intent.deadline_step.value_or(
                task.deadline_step.value_or(std::numeric_limits<int>::max()));
            const int route_cost = cursor
                                       ? Distance(*cursor, task.position)
                                       : ShedDistance(task.position, board_size);
            return std::tuple(IsHard(task, intent) ? 0 : 1, deadline,
                              -std::max(task.priority, intent.priority),
                              route_cost, task.layout_cost, task.key,
                              candidate.node);
          };
          return rank(left) < rank(right);
        });
    cursor = selected->task->position;
    result.push_back(*selected);
    remaining.erase(selected);
  }
  return result;
}

}  // namespace

ScheduleResult Schedule(const PlannerStateView& state,
                        const std::vector<Task>& tasks,
                        SchedulerKind scheduler,
                        int supply_route_capacity,
                        SupplyRouteMode supply_route_mode,
                        TaskContinuationMode task_continuation_mode,
                        int continuation_travel_value,
                        std::unordered_map<int, Commitment>* commitments) {
  ScheduleResult result;
  const std::vector<UnitView> units = Units(state.farm, state.priv);
  std::vector<UnitAction> actions(units.size(),
                                  UnitAction{UnitOp::kPass, -1, 1});
  std::set<int> available;
  for (const UnitView& unit : units) available.insert(unit.index);
  std::unordered_map<std::string, std::set<std::string>> completed;
  std::set<Identity> assigned_nodes;
  std::set<Identity> routed_nodes;
  std::set<std::string> claimed_exclusive;
  std::unordered_map<std::string, int> claimed_resources;
  std::set<std::pair<std::string, UnitOp>> assigned_effects;
  std::array<int64_t, kNumItems> consumed{};
  const std::unordered_map<std::string, int> territories =
      scheduler == SchedulerKind::kTerritoryAware
          ? BuildTerritories(state, tasks, units)
          : std::unordered_map<std::string, int>{};

  std::set<std::string> valid_tasks;
  std::unordered_map<std::string, const Task*> task_by_key;
  for (const Task& task : tasks) {
    valid_tasks.insert(task.key);
    task_by_key[task.key] = &task;
  }
  const auto advance_route = [&](Commitment* commitment) {
    while (!commitment->route_tasks.empty()) {
      const auto task_it = task_by_key.find(commitment->route_tasks.front());
      if (task_it != task_by_key.end() &&
          RequiresItem(*task_it->second, commitment->item)) {
        commitment->task_key = task_it->first;
        commitment->target = task_it->second->position;
        return true;
      }
      commitment->route_tasks.erase(commitment->route_tasks.begin());
    }
    return false;
  };
  for (auto it = commitments->begin(); it != commitments->end();) {
    const bool valid_unit = it->first >= 0 && it->first < static_cast<int>(units.size());
    bool valid_task = true;
    if (valid_unit && !it->second.route_tasks.empty()) {
      valid_task = advance_route(&it->second);
      if (valid_task) {
        const Inventory* inventory = units[it->first].inventory;
        const bool has_item = inventory != nullptr &&
                              inventory->Get(it->second.item) > 0;
        it->second.kind = has_item ? CommitmentKind::kTask
                                   : CommitmentKind::kSupply;
      }
    } else if (valid_unit && it->second.kind == CommitmentKind::kTask) {
      valid_task = valid_tasks.contains(it->second.task_key);
    }
    if (!valid_unit || !valid_task) {
      it = commitments->erase(it);
    } else {
      ++it;
    }
  }

  const auto record = [&](const UnitView& unit, UnitAction action,
                          const std::string& task,
                          std::pair<int, int> target,
                          const std::string& reason, const std::string& node) {
    actions[unit.index] = action;
    available.erase(unit.index);
    result.assignments.push_back(
        Assignment{unit.index, task, target, action, reason, node});
  };

  const auto execute = [&](const UnitView& unit, const Candidate& candidate,
                           const std::string& reason) {
    const Task& task = *candidate.task;
    const Intent& intent = *candidate.intent;
    record(unit, intent.action, task.key, task.position, reason, candidate.node);
    completed[task.key].insert(candidate.node);
    assigned_nodes.emplace(task.key, candidate.node);
    assigned_effects.emplace(task.key, intent.action.op);
    Claim(intent, &claimed_exclusive, &claimed_resources);
    if (intent.required_item >= 0) ++consumed[intent.required_item];
    const auto commitment_it = commitments->find(unit.index);
    bool keep_route = false;
    if (commitment_it != commitments->end() &&
        !commitment_it->second.route_tasks.empty() &&
        commitment_it->second.task_key == task.key &&
        commitment_it->second.item == intent.required_item) {
      if (commitment_it->second.route_tasks.front() == task.key) {
        commitment_it->second.route_tasks.erase(
            commitment_it->second.route_tasks.begin());
      }
      keep_route = advance_route(&commitment_it->second);
      if (keep_route) commitment_it->second.kind = CommitmentKind::kTask;
    }
    if (!keep_route) {
      const bool has_remaining_intent = std::any_of(
          task.intents.begin(), task.intents.end(), [&](const Intent& pending) {
            return Enabled(pending) &&
                   !assigned_nodes.contains({task.key, pending.key});
          });
      if (task_continuation_mode != TaskContinuationMode::kRelease &&
          has_remaining_intent) {
        (*commitments)[unit.index] = Commitment{
            CommitmentKind::kTask, task.position, task.key, -1, {}};
      } else {
        commitments->erase(unit.index);
      }
    }
  };

  // Execute a legal same-tile prefix in actor order.  Later actors observe
  // predecessor effects selected for earlier actors in this same prefix.
  for (const UnitView& unit : units) {
    std::vector<Candidate> local;
    for (const Task& task : tasks) {
      if (task.position != unit.position) continue;
      for (const Intent& intent : task.intents) {
        if (!Enabled(intent) ||
            assigned_nodes.contains({task.key, intent.key}) ||
            !ConstraintsAllow(intent, claimed_exclusive, claimed_resources) ||
            assigned_effects.contains({task.key, intent.action.op}) ||
            !Ready(intent, completed[task.key]) || !HasItem(unit, intent)) {
          continue;
        }
        local.push_back(Candidate{&task, &intent, intent.key});
      }
    }
    if (local.empty()) continue;
    const Candidate* selected = &*std::min_element(
        local.begin(), local.end(), [&](const Candidate& left,
                                        const Candidate& right) {
          return std::tuple(CandidateRank(unit, left, state.step, *commitments,
                                          scheduler, territories),
                            SameTileOrder(left.intent->action.op)) <
                 std::tuple(CandidateRank(unit, right, state.step, *commitments,
                                          scheduler, territories),
                            SameTileOrder(right.intent->action.op));
        });

    // Do not spend a local actor on lower-value optional work while a remote
    // hard or materially higher-ranked root remains reachable.  Sticky mode
    // amortizes an already-paid trip unless this actor is the last one that
    // can prevent a hard deadline miss.
    auto local_rank = CandidateRank(unit, *selected, state.step, *commitments,
                                    scheduler, territories);
    bool defer = false;
    const auto commitment_it = commitments->find(unit.index);
    const bool retained_local =
        task_continuation_mode != TaskContinuationMode::kRelease &&
        commitment_it != commitments->end() &&
        commitment_it->second.kind == CommitmentKind::kTask &&
        commitment_it->second.task_key == selected->task->key;
    if (retained_local && !IsHard(*selected->task, *selected->intent)) {
      for (const Task& task : tasks) {
        if (task.position == unit.position) continue;
        for (const Intent& intent : task.intents) {
          if (!Enabled(intent) || !intent.predecessors.empty() ||
              !IsHard(task, intent) ||
              assigned_nodes.contains({task.key, intent.key}) ||
              assigned_effects.contains({task.key, intent.action.op}) ||
              !ConstraintsAllow(intent, claimed_exclusive,
                                claimed_resources) ||
              !HasItem(unit, intent)) {
            continue;
          }
          const int deadline = intent.deadline_step.value_or(
              task.deadline_step.value_or(
                  (state.step / state.config.turns_per_day + 1) *
                          state.config.turns_per_day -
                      1));
          const int arrival_now =
              state.step + Distance(unit.position, task.position);
          if (arrival_now > deadline || arrival_now + 1 <= deadline) continue;
          const bool other_actor_can_reach = std::any_of(
              available.begin(), available.end(), [&](int actor) {
                if (actor == unit.index || !HasItem(units[actor], intent)) {
                  return false;
                }
                return state.step +
                           Distance(units[actor].position, task.position) <=
                       deadline;
              });
          if (!other_actor_can_reach) {
            defer = true;
            break;
          }
        }
        if (defer) break;
      }
      if (!defer &&
          task_continuation_mode == TaskContinuationMode::kRegret) {
        const int local_priority =
            Priority(*selected->task, *selected->intent);
        for (const Task& task : tasks) {
          if (task.position == unit.position) continue;
          for (const Intent& intent : task.intents) {
            Candidate global{&task, &intent, intent.key};
            if (!Enabled(intent) || !intent.predecessors.empty() ||
                IsHard(task, intent) ||
                assigned_nodes.contains({task.key, intent.key}) ||
                assigned_effects.contains({task.key, intent.action.op}) ||
                !ConstraintsAllow(intent, claimed_exclusive,
                                  claimed_resources) ||
                !HasItem(unit, intent) ||
                !(CandidateRank(unit, global, state.step, *commitments,
                                scheduler, territories) < local_rank)) {
              continue;
            }
            const int distance = Distance(unit.position, task.position);
            const int remote_priority = Priority(task, intent);
            const int priority_gain = remote_priority - local_priority;
            const int deadline = intent.deadline_step.value_or(
                task.deadline_step.value_or(
                    (state.step / state.config.turns_per_day + 1) *
                            state.config.turns_per_day -
                        1));
            const int arrival_now = state.step + distance;
            const bool last_departure =
                arrival_now <= deadline && arrival_now + 1 > deadline;
            if ((last_departure && priority_gain > 0) ||
                priority_gain > continuation_travel_value * distance) {
              defer = true;
              break;
            }
          }
          if (defer) break;
        }
      }
    } else if (!retained_local) {
      for (const Task& task : tasks) {
        for (const Intent& intent : task.intents) {
          Candidate global{&task, &intent, intent.key};
          if (!Enabled(intent) || !intent.predecessors.empty() ||
              assigned_nodes.contains({task.key, intent.key}) ||
              !ConstraintsAllow(intent, claimed_exclusive,
                                claimed_resources) ||
              !HasItem(unit, intent)) {
            continue;
          }
          if (CandidateRank(unit, global, state.step, *commitments, scheduler,
                            territories) < local_rank) {
            defer = true;
            break;
          }
        }
        if (defer) break;
      }
    }
    if (!defer) execute(unit, *selected, selected->task->reason);
  }

  std::vector<Candidate> pending_required;
  std::vector<Candidate> pending_general;
  for (const Task& task : tasks) {
    for (const Intent& intent : task.intents) {
      if (!Enabled(intent) || !intent.predecessors.empty() ||
          assigned_nodes.contains({task.key, intent.key}) ||
          assigned_effects.contains({task.key, intent.action.op}) ||
          !ConstraintsAllow(intent, claimed_exclusive, claimed_resources)) {
        continue;
      }
      Candidate candidate{&task, &intent, intent.key};
      (intent.required_item >= 0 ? pending_required : pending_general)
          .push_back(candidate);
    }
  }

  const auto match_phase = [&](const std::vector<Candidate>& candidates,
                               bool require_item, bool hard_only,
                               const std::string& fixed_reason) {
    std::set<Identity> reserved;
    while (!available.empty()) {
      const UnitView* best_unit = nullptr;
      const Candidate* best_candidate = nullptr;
      using Rank = decltype(CandidateRank(units.front(), candidates.front(),
                                          state.step, *commitments, scheduler,
                                          territories));
      std::optional<Rank> best_rank;
      for (int index : available) {
        const UnitView& unit = units[index];
        for (const Candidate& candidate : candidates) {
          const Intent& intent = *candidate.intent;
          const Identity identity{candidate.task->key, candidate.node};
          if (reserved.contains(identity) || assigned_nodes.contains(identity) ||
              (hard_only && !IsHard(*candidate.task, intent)) ||
              (!hard_only && IsHard(*candidate.task, intent)) ||
              !ConstraintsAllow(intent, claimed_exclusive, claimed_resources) ||
              (require_item && !HasItem(unit, intent))) {
            continue;
          }
          const int deadline = intent.deadline_step.value_or(
              candidate.task->deadline_step.value_or(
                  (state.step / state.config.turns_per_day + 1) *
                          state.config.turns_per_day -
                      1));
          if (Distance(unit.position, candidate.task->position) + state.step >
              deadline) {
            continue;
          }
          const Rank rank = CandidateRank(unit, candidate, state.step,
                                          *commitments, scheduler, territories);
          if (!best_rank || rank < *best_rank) {
            best_rank = rank;
            best_unit = &unit;
            best_candidate = &candidate;
          }
        }
      }
      if (best_unit == nullptr || best_candidate == nullptr) break;
      const Intent& intent = *best_candidate->intent;
      const Task& task = *best_candidate->task;
      if (best_unit->position == task.position && HasItem(*best_unit, intent)) {
        execute(*best_unit, *best_candidate,
                fixed_reason.empty() ? task.reason : fixed_reason);
      } else {
        record(*best_unit, MoveToward(best_unit->position, task.position),
               task.key, task.position,
               fixed_reason.empty() ? task.reason : fixed_reason, "");
        (*commitments)[best_unit->index] = Commitment{
            CommitmentKind::kTask, task.position, task.key, -1, {}};
        Claim(intent, &claimed_exclusive, &claimed_resources);
      }
      reserved.emplace(task.key, best_candidate->node);
      routed_nodes.emplace(task.key, best_candidate->node);
    }
  };

  std::vector<Candidate> all_pending = pending_required;
  all_pending.insert(all_pending.end(), pending_general.begin(),
                     pending_general.end());
  match_phase(all_pending, true, true, "");
  match_phase(pending_required, true, false, "deliver_required_item");

  const auto required = ResourceDemand(pending_required);
  std::vector<Candidate> market_pending = pending_required;
  std::set<Identity> market_identities;
  for (const Candidate& candidate : market_pending) {
    market_identities.emplace(candidate.task->key, candidate.node);
  }
  for (const Task& task : tasks) {
    for (const Intent& intent : task.intents) {
      const Identity identity{task.key, intent.key};
      if (Enabled(intent) && intent.required_item >= 0 &&
          intent.reserve_before_ready && !assigned_nodes.contains(identity) &&
          !market_identities.contains(identity)) {
        market_pending.push_back(Candidate{&task, &intent, intent.key});
        market_identities.insert(identity);
      }
    }
  }
  result.supply_reservations = ResourceDemand(market_pending);

  // Split large demand into route-sized packets so multiple carriers can
  // service distant task clusters in parallel.  Zero preserves one unbounded
  // packet for controlled comparison with the original scheduler.
  std::set<std::string> bound_tasks;
  for (const auto& [_, commitment] : *commitments) {
    bound_tasks.insert(commitment.route_tasks.begin(),
                       commitment.route_tasks.end());
  }
  for (int item_index = 0; item_index < kNumItems; ++item_index) {
    const int64_t carried = std::max<int64_t>(0, Carried(units, item_index) -
                                                    consumed[item_index]);
    const int64_t pickup_need = std::max<int64_t>(0, required[item_index] - carried);
    int64_t remaining =
        std::min<int64_t>(pickup_need, state.priv.shed[item_index]);
    const int64_t route_capacity =
        supply_route_capacity > 0 ? supply_route_capacity : remaining;
    const bool bind_routes =
        supply_route_mode == SupplyRouteMode::kTaskBound &&
        (item_index == item::kWheat || item_index == item::kFertilizer);
    const std::vector<Candidate> ordered_targets =
        bind_routes ? OrderSupplyTargets(pending_required, item_index,
                                         state.config.board_size, routed_nodes,
                                         bound_tasks)
                    : std::vector<Candidate>{};
    size_t route_offset = 0;
    while (remaining > 0 && !available.empty()) {
      const UnitView* selected = nullptr;
      std::tuple<int, int, bool, int> selected_rank;
      for (int index : available) {
        const UnitView& unit = units[index];
        const auto target = NearestShed(unit.position, state.config.board_size);
        const auto commitment_it = commitments->find(index);
        const bool same_item = commitment_it != commitments->end() &&
                               commitment_it->second.item == item_index;
        const bool carries_anything =
            unit.inventory != nullptr && !unit.inventory->items.empty();
        const auto rank = std::tuple(same_item ? 0 : 1,
                                     Distance(unit.position, target),
                                     carries_anything, index);
        if (selected == nullptr || rank < selected_rank) {
          selected = &unit;
          selected_rank = rank;
        }
      }
      if (selected == nullptr) break;
      int64_t packet = std::min(remaining, route_capacity);
      std::vector<std::string> route_tasks;
      const auto existing = commitments->find(selected->index);
      if (bind_routes && existing != commitments->end() &&
          existing->second.item == item_index &&
          !existing->second.route_tasks.empty()) {
        route_tasks = existing->second.route_tasks;
        if (static_cast<int64_t>(route_tasks.size()) > packet) {
          route_tasks.resize(static_cast<size_t>(packet));
        }
        packet = std::min<int64_t>(packet, route_tasks.size());
      } else if (bind_routes) {
        while (route_offset < ordered_targets.size() &&
               static_cast<int64_t>(route_tasks.size()) < packet) {
          route_tasks.push_back(ordered_targets[route_offset].task->key);
          ++route_offset;
        }
        if (!route_tasks.empty()) {
          packet = static_cast<int64_t>(route_tasks.size());
        }
      }
      const auto shed_target =
          NearestShed(selected->position, state.config.board_size);
      const bool at_shed = IsShedAdjacent(selected->position.first,
                                          selected->position.second,
                                          state.config.board_size);
      const UnitAction action =
          at_shed ? UnitAction{UnitOp::kPickup, item_index, packet}
                  : MoveToward(selected->position, shed_target);
      record(*selected, action, "supply:" + std::to_string(item_index),
             shed_target,
             route_tasks.empty() ? "acquire_required_item"
                                 : "acquire_bound_required_item",
             "");
      Commitment commitment{CommitmentKind::kSupply, shed_target, "",
                            item_index, {}};
      commitment.route_tasks = std::move(route_tasks);
      if (!commitment.route_tasks.empty()) {
        const auto target_it = task_by_key.find(commitment.route_tasks.front());
        if (target_it != task_by_key.end()) {
          commitment.task_key = target_it->first;
          commitment.target = target_it->second->position;
        }
      }
      (*commitments)[selected->index] = std::move(commitment);
      remaining -= packet;
    }
  }

  match_phase(pending_general, false, false, "");

  std::set<int> required_items;
  for (int index = 0; index < kNumItems; ++index) {
    if (required[index] > 0) required_items.insert(index);
  }
  for (int index : std::vector<int>(available.begin(), available.end())) {
    const UnitView& unit = units[index];
    if (unit.inventory == nullptr || unit.inventory->items.empty()) {
      commitments->erase(index);
      continue;
    }
    bool carries_required = false;
    for (int item_index : required_items) {
      carries_required = carries_required || unit.inventory->Get(item_index) > 0;
    }
    if (carries_required) continue;
    const auto target = NearestShed(unit.position, state.config.board_size);
    const bool at_shed = IsShedAdjacent(unit.position.first, unit.position.second,
                                        state.config.board_size);
    const UnitAction action = at_shed ? UnitAction{UnitOp::kDrop, -1, 1}
                                     : MoveToward(unit.position, target);
    record(unit, action, "return_inventory", target,
           "make_inventory_sellable", "");
    if (at_shed) {
      commitments->erase(index);
    } else {
      (*commitments)[index] =
          Commitment{CommitmentKind::kReturn, target, "", -1, {}};
    }
  }

  for (const Task& task : tasks) {
    bool deferred = false;
    for (const Intent& intent : task.intents) {
      if (Enabled(intent) && !assigned_nodes.contains({task.key, intent.key})) {
        deferred = true;
        break;
      }
    }
    if (deferred) result.deferred_tasks.push_back(task.key);
  }
  result.unassigned_units.assign(available.begin(), available.end());
  for (int item_index = 0; item_index < kNumItems; ++item_index) {
    const int64_t carried = std::max<int64_t>(0, Carried(units, item_index) -
                                                    consumed[item_index]);
    result.supply_shortfalls[item_index] = std::max<int64_t>(
        0, result.supply_reservations[item_index] - carried -
               state.priv.shed[item_index]);
  }
  for (const auto& value : *commitments) result.commitments.push_back(value);
  std::sort(result.commitments.begin(), result.commitments.end(),
            [](const auto& left, const auto& right) {
              return left.first < right.first;
            });
  result.requested.farmer = actions.front();
  result.requested.hands.assign(actions.begin() + 1, actions.end());
  return result;
}

}  // namespace kagg::planner
