#include "plans/session.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <limits>
#include <numeric>
#include <tuple>
#include <utility>
#include <vector>

#include "unit_phase.hpp"

namespace kagg::plans {
namespace {

enum class TaskClass : int {
  kPreventLoss = 0,
  kHarvest = 1,
  kSupply = 2,
  kExpand = 3,
  kOptionalYield = 4,
  kReturnInventory = 5,
};

enum class TraceReason : int64_t {
  kPass = 0,
  kMove = 1,
  kExecute = 2,
  kPickup = 3,
  kDrop = 4,
};

struct Task {
  uint64_t id = 0;
  int source = -1;
  TaskClass task_class = TaskClass::kExpand;
  int rank = -1;
  int line_priority = 0;
  int deadline = std::numeric_limits<int>::max();
  int x = 0;
  int y = 0;
  UnitAction operation;
  int required_item = -1;
  int preferred_unit = -1;
};

struct MarketRequest {
  MarketOrder order;
  int source = -1;
  int task_priority = 0;
  int line_priority = 0;
  int stable_id = 0;
  int64_t requested = 0;
  int64_t unit_cost = 0;
  bool uses_shed = false;
};

uint64_t HashTask(int source, TaskClass task_class, int x, int y,
                  const UnitAction& operation, int preferred_unit) {
  uint64_t value = 1469598103934665603ULL;
  for (const int item : {source, static_cast<int>(task_class), x, y,
                         static_cast<int>(operation.op), operation.arg,
                         preferred_unit}) {
    value ^= static_cast<uint64_t>(static_cast<uint32_t>(item));
    value *= 1099511628211ULL;
  }
  return value == 0 ? 1 : value;
}

int64_t Fibonacci(int index) {
  int64_t first = 1;
  int64_t second = 1;
  for (int cursor = 0; cursor < index; ++cursor) {
    if (second > std::numeric_limits<int64_t>::max() - first) {
      return std::numeric_limits<int64_t>::max();
    }
    const int64_t next = first + second;
    first = second;
    second = next;
  }
  return first;
}

int64_t SaturatingMultiply(int64_t first, int64_t second) {
  if (first <= 0 || second <= 0) return 0;
  if (first > std::numeric_limits<int64_t>::max() / second) {
    return std::numeric_limits<int64_t>::max();
  }
  return first * second;
}

std::pair<int, int> UnitPosition(const Farm& farm, int unit) {
  return unit == 0 ? std::pair{farm.farmer_x, farm.farmer_y}
                   : farm.hands[unit - 1];
}

const Inventory* UnitInventory(const PrivateState& priv, int unit) {
  return unit >= 0 && unit < static_cast<int>(priv.inventories.size())
             ? &priv.inventories[unit]
             : nullptr;
}

int64_t UnitItem(const PrivateState& priv, int unit, int item_index) {
  const Inventory* inventory = UnitInventory(priv, unit);
  return inventory == nullptr ? 0 : inventory->Get(item_index);
}

bool HasInventory(const PrivateState& priv, int unit) {
  const Inventory* inventory = UnitInventory(priv, unit);
  return inventory != nullptr && !inventory->items.empty();
}

int64_t Carried(const PrivateState& priv, int item_index) {
  int64_t count = 0;
  for (const Inventory& inventory : priv.inventories) {
    count += inventory.Get(item_index);
  }
  return count;
}

int64_t OwnedItem(const PrivateState& priv, int item_index) {
  return priv.shed[item_index] + Carried(priv, item_index);
}

int CountPlants(const Farm& farm, int crop) {
  return static_cast<int>(std::count_if(
      farm.tiles.begin(), farm.tiles.end(), [crop](const Tile& tile) {
        return tile.kind == TileKind::kPlant && tile.crop == crop;
      }));
}

int CountAnimals(const Farm& farm, int animal) {
  return static_cast<int>(std::count_if(
      farm.tiles.begin(), farm.tiles.end(), [animal](const Tile& tile) {
        return tile.kind == TileKind::kStructure && tile.has_animal &&
               tile.animal == animal;
      }));
}

int Distance(std::pair<int, int> first, std::pair<int, int> second) {
  return std::abs(first.first - second.first) +
         std::abs(first.second - second.second);
}

UnitAction MoveToward(std::pair<int, int> origin,
                      std::pair<int, int> target) {
  if (origin.first < target.first) {
    return UnitAction{UnitOp::kEast, -1, 1};
  }
  if (origin.first > target.first) {
    return UnitAction{UnitOp::kWest, -1, 1};
  }
  if (origin.second < target.second) {
    return UnitAction{UnitOp::kSouth, -1, 1};
  }
  if (origin.second > target.second) {
    return UnitAction{UnitOp::kNorth, -1, 1};
  }
  return UnitAction{UnitOp::kPass, -1, 1};
}

std::pair<int, int> NearestShed(std::pair<int, int> origin,
                                int board_size) {
  std::pair<int, int> selected = ShedAccessTiles(board_size)[0];
  int best = Distance(origin, selected);
  for (const auto& candidate : ShedAccessTiles(board_size)) {
    const int distance = Distance(origin, candidate);
    if (std::tie(distance, candidate.second, candidate.first) <
        std::tie(best, selected.second, selected.first)) {
      selected = candidate;
      best = distance;
    }
  }
  return selected;
}

void AddTask(std::vector<Task>* tasks, int source, TaskClass task_class,
             int rank, int line_priority, int deadline, int x, int y,
             UnitAction operation, int required_item = -1,
             int preferred_unit = -1) {
  Task task;
  task.source = source;
  task.task_class = task_class;
  task.rank = rank;
  task.line_priority = line_priority;
  task.deadline = deadline;
  task.x = x;
  task.y = y;
  task.operation = operation;
  task.required_item = required_item;
  task.preferred_unit = preferred_unit;
  task.id = HashTask(source, task_class, x, y, operation, preferred_unit);
  tasks->push_back(task);
}

std::array<int, 6> TaskRanks(
    const std::array<int64_t, kGlobalFieldCount>& global_plan) {
  std::array<int, 6> classes{};
  std::iota(classes.begin(), classes.end(), 0);
  std::stable_sort(classes.begin(), classes.end(), [&](int left, int right) {
    return std::tuple(-global_plan[kTaskPriorityFirst + left], left) <
           std::tuple(-global_plan[kTaskPriorityFirst + right], right);
  });
  std::array<int, 6> ranks{};
  for (int rank = 0; rank < static_cast<int>(classes.size()); ++rank) {
    ranks[classes[rank]] = rank;
  }
  return ranks;
}

std::vector<int> ActiveLineOrder(
    const std::array<ProductionLine, kProductionLineCount>& lines) {
  std::vector<int> result;
  for (int line = 0; line < kProductionLineCount; ++line) {
    if (lines[line].active) result.push_back(line);
  }
  std::stable_sort(result.begin(), result.end(), [&](int left, int right) {
    return std::tuple(-lines[left].values[kLinePriority], left) <
           std::tuple(-lines[right].values[kLinePriority], right);
  });
  return result;
}

bool PriceCondition(const ProductionLine& line, int64_t visible_price) {
  switch (line.values[kPricePolicy]) {
    case 0:
      return true;
    case 1:
      return visible_price >= line.price_anchor;
    case 2:
      return 10 * visible_price >= 11 * line.price_anchor;
    case 3:
      return visible_price <= line.price_anchor;
    case 4:
      return 10 * visible_price <= 9 * line.price_anchor;
    default:
      return false;
  }
}

int ProductForLine(int line) {
  return line < kNumCrops ? line : kAnimals[line - kNumCrops].product;
}

void AddMarketRequest(std::vector<MarketRequest>* requests, MarketOrder order,
                      int source, int task_priority, int line_priority,
                      int stable_id, int64_t requested, int64_t unit_cost,
                      bool uses_shed) {
  if (requested <= 0) return;
  order.remaining = requested;
  requests->push_back(MarketRequest{order, source, task_priority,
                                    line_priority, stable_id, requested,
                                    unit_cost, uses_shed});
}

}  // namespace

NumericAction Session::Action(const Engine& engine, int player) {
  Refresh(engine, player);
  const Farm& farm = engine.farm(player);
  const PrivateState& priv = engine.priv(player);
  const int unit_count = 1 + static_cast<int>(farm.hands.size());
  NumericAction output;
  output.unit_count = unit_count;
  output.requires_decision = pending_events_ != 0;
  output.tokens.assign(static_cast<size_t>(unit_count), 0);
  output.quantities.assign(static_cast<size_t>(unit_count), 0);
  output.unit_sources.assign(static_cast<size_t>(unit_count), -1);
  output.unit_reasons.assign(
      static_cast<size_t>(unit_count),
      static_cast<int64_t>(TraceReason::kPass));
  output.decision_count = unit_count;
  if (output.requires_decision || !active()) return output;

  const std::array<int, 6> ranks = TaskRanks(global_plan_);
  const std::vector<int> line_order = ActiveLineOrder(lines_);
  const int day =
      engine.step_index() / std::max(1, config_.turns_per_day);
  const int end_of_day = (day + 1) * config_.turns_per_day - 1;
  std::vector<Task> tasks;
  std::vector<bool> claimed(farm.tiles.size(), false);
  std::array<int, kNumCrops> crops_seen{};
  std::array<int, kNumAnimals> animals_seen{};

  for (int index = 0; index < static_cast<int>(farm.tiles.size()); ++index) {
    const Tile& tile = farm.tiles[index];
    const int x = index % config_.board_size;
    const int y = index / config_.board_size;
    if (tile.kind == TileKind::kPlant && tile.crop >= 0 &&
        tile.crop < kNumCrops && lines_[tile.crop].active) {
      const int line_id = tile.crop;
      const ProductionLine& line = lines_[line_id];
      const int priority = static_cast<int>(line.values[kLinePriority]);
      const int target =
          static_cast<int>(kCountBuckets[line.values[kTarget]]);
      const bool extra = !paused_ && line.values[kScaleMode] == 1 &&
                         crops_seen[tile.crop] >= target;
      ++crops_seen[tile.crop];
      const bool ready =
          tile.yield_units > 0 &&
          day - tile.planted_day >= kCrops[tile.crop].first_yield_day;
      if (extra) {
        if (ready) {
          const int deadline =
              tile.max_lifespan_step >= 0
                  ? tile.max_lifespan_step
                  : std::numeric_limits<int>::max();
          AddTask(&tasks, line_id, TaskClass::kHarvest,
                  ranks[static_cast<int>(TaskClass::kHarvest)], priority,
                  deadline, x, y,
                  UnitAction{UnitOp::kHarvest, -1, 1});
        } else {
          AddTask(&tasks, line_id, TaskClass::kExpand,
                  ranks[static_cast<int>(TaskClass::kExpand)], priority,
                  std::numeric_limits<int>::max(), x, y,
                  UnitAction{UnitOp::kDig, -1, 1});
        }
        continue;
      }
      if (!tile.watered_today) {
        AddTask(&tasks, line_id, TaskClass::kPreventLoss,
                ranks[static_cast<int>(TaskClass::kPreventLoss)], priority,
                end_of_day, x, y,
                UnitAction{UnitOp::kWater, -1, 1});
      }
      if (ready) {
        const int deadline =
            tile.max_lifespan_step >= 0
                ? tile.max_lifespan_step
                : std::numeric_limits<int>::max();
        AddTask(&tasks, line_id, TaskClass::kHarvest,
                ranks[static_cast<int>(TaskClass::kHarvest)], priority,
                deadline, x, y,
                UnitAction{UnitOp::kHarvest, -1, 1});
      }
      if (!paused_ && line.values[kOptionalYield] != 0 &&
          tile.fertilized_until_day < day) {
        AddTask(&tasks, line_id, TaskClass::kOptionalYield,
                ranks[static_cast<int>(TaskClass::kOptionalYield)],
                priority, std::numeric_limits<int>::max(), x, y,
                UnitAction{UnitOp::kFertilize, -1, 1},
                item::kFertilizer);
      }
      continue;
    }
    if (tile.kind == TileKind::kStructure && tile.has_animal &&
        tile.animal >= 0 && tile.animal < kNumAnimals) {
      const int line_id = kNumCrops + tile.animal;
      if (!lines_[line_id].active) continue;
      const ProductionLine& line = lines_[line_id];
      const int priority = static_cast<int>(line.values[kLinePriority]);
      const int target =
          static_cast<int>(kCountBuckets[line.values[kTarget]]);
      const bool extra = !paused_ && line.values[kScaleMode] == 1 &&
                         animals_seen[tile.animal] >= target;
      ++animals_seen[tile.animal];
      if (tile.yield_units > 0) {
        AddTask(&tasks, line_id, TaskClass::kHarvest,
                ranks[static_cast<int>(TaskClass::kHarvest)], priority,
                std::numeric_limits<int>::max(), x, y,
                UnitAction{UnitOp::kHarvest, -1, 1});
      }
      if (extra) continue;
      if (!tile.fed_today) {
        AddTask(&tasks, line_id, TaskClass::kPreventLoss,
                ranks[static_cast<int>(TaskClass::kPreventLoss)], priority,
                end_of_day, x, y, UnitAction{UnitOp::kFeed, -1, 1},
                item::kWheat);
      }
      if (!tile.cared_today) {
        AddTask(&tasks, line_id, TaskClass::kOptionalYield,
                ranks[static_cast<int>(TaskClass::kOptionalYield)],
                priority, end_of_day, x, y,
                UnitAction{UnitOp::kCare, -1, 1});
      }
      if (line.values[kOptionalYield] != 0 &&
          tile.fertilizer_available) {
        AddTask(&tasks, line_id, TaskClass::kHarvest,
                ranks[static_cast<int>(TaskClass::kHarvest)], priority,
                std::numeric_limits<int>::max(), x, y,
                UnitAction{UnitOp::kCollectFertilizer, -1, 1});
      }
    }
  }

  if (!paused_) {
    for (int line_id : line_order) {
      const ProductionLine& line = lines_[line_id];
      const int priority = static_cast<int>(line.values[kLinePriority]);
      const int target =
          static_cast<int>(kCountBuckets[line.values[kTarget]]);
      if (line_id < kNumCrops) {
        int remaining = std::min<int64_t>(
            std::max(0, target - CountPlants(farm, line_id)),
            priv.seeds[line_id]);
        for (int index = 0;
             index < static_cast<int>(farm.tiles.size()) && remaining > 0;
             ++index) {
          if (claimed[index] ||
              farm.tiles[index].kind != TileKind::kEmpty) {
            continue;
          }
          claimed[index] = true;
          AddTask(&tasks, line_id, TaskClass::kExpand,
                  ranks[static_cast<int>(TaskClass::kExpand)], priority,
                  std::numeric_limits<int>::max(),
                  index % config_.board_size,
                  index / config_.board_size,
                  UnitAction{UnitOp::kPlant, line_id, 1});
          --remaining;
        }
        continue;
      }

      const int animal = line_id - kNumCrops;
      int remaining = std::max(0, target - CountAnimals(farm, animal));
      for (int index = 0;
           index < static_cast<int>(farm.tiles.size()) && remaining > 0;
           ++index) {
        const Tile& tile = farm.tiles[index];
        if (claimed[index] || tile.kind != TileKind::kStructure ||
            tile.has_animal ||
            tile.structure != kAnimals[animal].structure) {
          continue;
        }
        claimed[index] = true;
        AddTask(&tasks, line_id, TaskClass::kExpand,
                ranks[static_cast<int>(TaskClass::kExpand)], priority,
                std::numeric_limits<int>::max(),
                index % config_.board_size,
                index / config_.board_size,
                UnitAction{UnitOp::kPlace, item::kGoose + animal, 1},
                item::kGoose + animal);
        --remaining;
      }
      for (int index = 0;
           index < static_cast<int>(farm.tiles.size()) && remaining > 0;
           ++index) {
        if (claimed[index] ||
            farm.tiles[index].kind != TileKind::kEmpty) {
          continue;
        }
        claimed[index] = true;
        const UnitOp operation =
            kAnimals[animal].structure == StructureKind::kCoop
                ? UnitOp::kBuildCoop
                : UnitOp::kBuildPasture;
        AddTask(&tasks, line_id, TaskClass::kExpand,
                ranks[static_cast<int>(TaskClass::kExpand)], priority,
                std::numeric_limits<int>::max(),
                index % config_.board_size,
                index / config_.board_size,
                UnitAction{operation, -1, 1});
        --remaining;
      }
    }
  }

  const int return_class =
      static_cast<int>(TaskClass::kReturnInventory);
  const int return_source =
      kProductionLineCount + kTaskPriorityFirst + return_class;
  for (int unit = 0; unit < unit_count; ++unit) {
    if (!HasInventory(priv, unit)) continue;
    const auto position = UnitPosition(farm, unit);
    const auto target = NearestShed(position, config_.board_size);
    AddTask(&tasks, return_source, TaskClass::kReturnInventory,
            ranks[return_class], 0, std::numeric_limits<int>::max(),
            target.first, target.second,
            UnitAction{UnitOp::kDrop, -1, 1}, -1, unit);
  }

  const int supply_rank = ranks[static_cast<int>(TaskClass::kSupply)];
  for (Task& task : tasks) {
    if (task.required_item >= 0) {
      task.rank = std::max(task.rank, supply_rank);
    }
  }
  std::stable_sort(tasks.begin(), tasks.end(),
                   [](const Task& left, const Task& right) {
    const bool left_deadline =
        left.deadline != std::numeric_limits<int>::max();
    const bool right_deadline =
        right.deadline != std::numeric_limits<int>::max();
    return std::tuple(!left_deadline, left.deadline, left.rank,
                      -left.line_priority, left.id) <
           std::tuple(!right_deadline, right.deadline, right.rank,
                      -right.line_priority, right.id);
  });

  commitments_.resize(static_cast<size_t>(unit_count), 0);
  std::vector<bool> used(static_cast<size_t>(unit_count), false);
  std::vector<UnitAction> requested(
      static_cast<size_t>(unit_count),
      UnitAction{UnitOp::kPass, -1, 1});
  std::vector<int64_t> sources(static_cast<size_t>(unit_count), -1);
  std::vector<int64_t> reasons(
      static_cast<size_t>(unit_count),
      static_cast<int64_t>(TraceReason::kPass));
  std::array<int64_t, kNumItems> supply_remaining = priv.shed;
  for (const Task& task : tasks) {
    int selected = -1;
    std::tuple<int, int, int> best{2, std::numeric_limits<int>::max(),
                                   std::numeric_limits<int>::max()};
    for (int unit = 0; unit < unit_count; ++unit) {
      if (used[unit] ||
          (task.preferred_unit >= 0 && task.preferred_unit != unit)) {
        continue;
      }
      const bool has_item =
          task.required_item < 0 ||
          UnitItem(priv, unit, task.required_item) > 0;
      if (!has_item &&
          (task.required_item < 0 ||
           supply_remaining[task.required_item] <= 0)) {
        continue;
      }
      const auto origin = UnitPosition(farm, unit);
      const auto target = has_item || task.required_item < 0
                              ? std::pair{task.x, task.y}
                              : NearestShed(origin, config_.board_size);
      const std::tuple<int, int, int> score{
          commitments_[unit] == task.id ? 0 : 1,
          Distance(origin, target), unit};
      if (score < best) {
        best = score;
        selected = unit;
      }
    }
    if (selected < 0) continue;
    const auto origin = UnitPosition(farm, selected);
    const bool has_item =
        task.required_item < 0 ||
        UnitItem(priv, selected, task.required_item) > 0;
    const auto target = has_item || task.required_item < 0
                            ? std::pair{task.x, task.y}
                            : NearestShed(origin, config_.board_size);
    UnitAction action;
    TraceReason reason;
    if (origin != target) {
      action = MoveToward(origin, target);
      reason = TraceReason::kMove;
      commitments_[selected] = task.id;
    } else if (!has_item) {
      action = UnitAction{UnitOp::kPickup, task.required_item, 1};
      reason = TraceReason::kPickup;
      --supply_remaining[task.required_item];
      commitments_[selected] = task.id;
    } else {
      action = task.operation;
      reason = task.operation.op == UnitOp::kDrop ? TraceReason::kDrop
                                                  : TraceReason::kExecute;
      commitments_[selected] = 0;
    }
    requested[selected] = action;
    sources[selected] = task.source;
    reasons[selected] = static_cast<int64_t>(reason);
    used[selected] = true;
  }

  PlayerAction player_action;
  player_action.farmer = requested[0];
  player_action.hands.assign(requested.begin() + 1, requested.end());
  const UnitPhaseResult compiled =
      CompileUnitPhase(config_, farm, priv, player_action, day);
  player_action = compiled.actual;
  for (int unit = 0; unit < unit_count; ++unit) {
    const UnitActionTrace& trace = compiled.trace[unit];
    if (requested[unit].op != UnitOp::kPass &&
        trace.status != UnitActionStatus::kApplied) {
      compiler_failed_ = true;
      ++task_failures_;
      commitments_[unit] = 0;
      sources[unit] = -1;
      reasons[unit] = static_cast<int64_t>(TraceReason::kPass);
    } else if (reasons[unit] ==
                   static_cast<int64_t>(TraceReason::kExecute) ||
               reasons[unit] ==
                   static_cast<int64_t>(TraceReason::kDrop)) {
      ++task_successes_;
    }
  }

  std::vector<MarketRequest> market_requests;
  int feed_source = -1;
  int feed_line_priority = -1;
  int optional_source = -1;
  int optional_line_priority = -1;
  int64_t desired_feed = 0;
  int64_t desired_fertilizer = 0;
  for (int line_id : line_order) {
    const ProductionLine& line = lines_[line_id];
    const int priority = static_cast<int>(line.values[kLinePriority]);
    const int product = ProductForLine(line_id);
    const int64_t reserve =
        kCountBuckets[line.values[kOutputReserve]];
    if (PriceCondition(line, engine.market().prices[product])) {
      const int64_t sell =
          std::max<int64_t>(0, priv.shed[product] - reserve);
      AddMarketRequest(
          &market_requests, MarketOrder{OrderKind::kSell, product, sell},
          line_id,
          static_cast<int>(global_plan_[
              kTaskPriorityFirst + static_cast<int>(TaskClass::kHarvest)]),
          priority, line_id * 10, sell, 0, false);
    }
    const int target =
        static_cast<int>(kCountBuckets[line.values[kTarget]]);
    if (line_id < kNumCrops) {
      if (paused_) continue;
      const int64_t deficit = std::max<int64_t>(
          0, target - CountPlants(farm, line_id) - priv.seeds[line_id]);
      AddMarketRequest(
          &market_requests,
          MarketOrder{OrderKind::kBuySeed, line_id, deficit}, line_id,
          static_cast<int>(global_plan_[
              kTaskPriorityFirst + static_cast<int>(TaskClass::kExpand)]),
          priority, line_id * 10 + 1, deficit,
          kCrops[line_id].seed_cost, false);
      if (line.values[kOptionalYield] != 0) {
        desired_fertilizer += std::max(target, CountPlants(farm, line_id));
        if (priority > optional_line_priority) {
          optional_line_priority = priority;
          optional_source = line_id;
        }
      }
      continue;
    }
    const int animal = line_id - kNumCrops;
    const int current = CountAnimals(farm, animal);
    const int maintained = line.values[kScaleMode] == 1
                               ? std::min(current, target)
                               : current;
    const int feed_demand =
        paused_ ? maintained : std::max(maintained, target);
    desired_feed += feed_demand;
    if (feed_demand > 0 && priority > feed_line_priority) {
      feed_line_priority = priority;
      feed_source = line_id;
    }
    if (paused_) continue;
    const int item_index = item::kGoose + animal;
    const int64_t deficit = std::max<int64_t>(
        0, target - current - OwnedItem(priv, item_index));
    AddMarketRequest(
        &market_requests,
        MarketOrder{OrderKind::kBuyAnimal, animal, deficit}, line_id,
        static_cast<int>(global_plan_[
            kTaskPriorityFirst + static_cast<int>(TaskClass::kExpand)]),
        priority, line_id * 10 + 1, deficit,
        kAnimals[animal].cost, true);
  }

  if (feed_source >= 0) {
    const int64_t deficit =
        std::max<int64_t>(0, desired_feed - OwnedItem(priv, item::kWheat));
    AddMarketRequest(
        &market_requests,
        MarketOrder{OrderKind::kBuyProduct, item::kWheat, deficit},
        feed_source,
        static_cast<int>(global_plan_[
            kTaskPriorityFirst + static_cast<int>(TaskClass::kPreventLoss)]),
        feed_line_priority, 100, deficit,
        engine.market().prices[item::kWheat], true);
  }
  if (!paused_ && optional_source >= 0) {
    const int64_t deficit = std::max<int64_t>(
        0, desired_fertilizer - OwnedItem(priv, item::kFertilizer));
    AddMarketRequest(
        &market_requests,
        MarketOrder{OrderKind::kBuyProduct, item::kFertilizer, deficit},
        optional_source,
        static_cast<int>(global_plan_[
            kTaskPriorityFirst + static_cast<int>(TaskClass::kOptionalYield)]),
        optional_line_priority, 101, deficit,
        engine.market().prices[item::kFertilizer], true);
  }
  if (!paused_ && global_initialized_) {
    const int worker_target =
        static_cast<int>(kCountBuckets[global_plan_[kWorkerCeiling]]);
    if (static_cast<int>(farm.hands.size()) < worker_target) {
      const int64_t cost = SaturatingMultiply(
          config_.farm_hand_cost_mult, Fibonacci(farm.hires_today));
      AddMarketRequest(
          &market_requests, MarketOrder{OrderKind::kHire, 0, 0},
          kProductionLineCount + kWorkerCeiling,
          static_cast<int>(global_plan_[
              kTaskPriorityFirst + static_cast<int>(TaskClass::kExpand)]),
          0, 200, 1, cost, false);
    }
    const int land_target =
        static_cast<int>(global_plan_[kLandCeiling]) + 1;
    if (farm.extra_unlocked + 1 < land_target &&
        farm.extra_unlocked < 3) {
      AddMarketRequest(
          &market_requests, MarketOrder{OrderKind::kBuyLand, 0, 0},
          kProductionLineCount + kLandCeiling,
          static_cast<int>(global_plan_[
              kTaskPriorityFirst + static_cast<int>(TaskClass::kExpand)]),
          0, 201, 1, kLandPrices[farm.extra_unlocked], false);
    }
  }

  std::stable_sort(
      market_requests.begin(), market_requests.end(),
      [](const MarketRequest& left, const MarketRequest& right) {
        return std::tuple(-left.task_priority, -left.line_priority,
                          left.stable_id) <
               std::tuple(-right.task_priority, -right.line_priority,
                          right.stable_id);
      });
  submitted_market_sources_.clear();
  const double reserve =
      kMoneyFractions[global_plan_[kCashReserve]] * config_.starting_money;
  const double spend_cap =
      kMoneyFractions[global_plan_[kSpendCap]] * config_.starting_money;
  double committed_spend = 0.0;
  int64_t projected_shed = ShedTotal(priv);
  bool market_slots_truncated = false;
  bool budget_truncated = false;
  for (const MarketRequest& request : market_requests) {
    if (static_cast<int>(player_action.market.size()) >=
        config_.max_market_orders) {
      market_slots_truncated = true;
      break;
    }
    int64_t quantity = request.requested;
    if (request.order.kind == OrderKind::kSell) {
      quantity = std::min<int64_t>(quantity, priv.shed[request.order.item]);
    } else if (request.unit_cost > 0) {
      const double cash_available = std::max(
          0.0, farm.money - reserve - committed_spend);
      const double cap_available = std::max(
          0.0, spend_cap - phase_spend_ - committed_spend);
      const double available = std::min(cash_available, cap_available);
      quantity = std::min<int64_t>(
          quantity,
          static_cast<int64_t>(available / request.unit_cost));
    }
    if (request.uses_shed) {
      quantity = std::min<int64_t>(
          quantity, std::max<int64_t>(0, config_.shed_capacity -
                                             projected_shed));
    }
    if (request.order.kind == OrderKind::kBuyProduct) {
      quantity = std::min<int64_t>(
          quantity, engine.market().inventory[request.order.item]);
    }
    if (quantity < request.requested) {
      budget_truncated = true;
    }
    if (quantity <= 0) continue;
    MarketOrder order = request.order;
    order.remaining =
        order.kind == OrderKind::kHire || order.kind == OrderKind::kBuyLand
            ? 0
            : quantity;
    player_action.market.push_back(order);
    submitted_market_sources_.push_back(request.source);
    const double cost =
        static_cast<double>(request.unit_cost) * quantity;
    committed_spend += cost;
    if (request.uses_shed) projected_shed += quantity;
    if (order.kind == OrderKind::kSell) {
      projected_shed = std::max<int64_t>(0, projected_shed - quantity);
    }
  }
  if (market_slots_truncated && !market_slots_truncated_) {
    pending_events_ |=
        uint64_t{1} << static_cast<int>(Event::kMarketSlotsTruncated);
  }
  if (budget_truncated && !budget_truncated_) {
    pending_events_ |=
        uint64_t{1} << static_cast<int>(Event::kBudgetTruncated);
  }
  market_slots_truncated_ = market_slots_truncated;
  budget_truncated_ = budget_truncated;
  phase_spend_ += committed_spend;

  const int capacity =
      unit_count + static_cast<int>(player_action.market.size());
  output.tokens.assign(static_cast<size_t>(capacity), 0);
  output.quantities.assign(static_cast<size_t>(capacity), 0);
  output.decision_count = policy::EncodePlayerAction(
      player_action, unit_count, output.tokens.data(),
      output.quantities.data(), capacity);
  output.unit_sources = std::move(sources);
  output.unit_reasons = std::move(reasons);
  output.market_sources = submitted_market_sources_;
  output.requires_decision = false;
  return output;
}

}  // namespace kagg::plans
