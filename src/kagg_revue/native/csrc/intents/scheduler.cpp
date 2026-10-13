#include "intents/session.hpp"

#include <algorithm>
#include <array>
#include <cstdint>
#include <limits>
#include <queue>
#include <tuple>
#include <utility>
#include <vector>

namespace kagg::intents {
namespace {

constexpr int kAnyUnit = -1;
constexpr int kFarmerOnly = 0;
constexpr int kHandOnly = 1;

struct Obligation {
  int64_t key = 0;
  int target = -1;
  UnitAction effect;
  int required_item = -1;
  Priority priority = Priority::kNormal;
  int deadline = std::numeric_limits<int>::max();
  int role = kAnyUnit;
  int work_index = -1;
  bool store = false;
  int64_t quantity = 1;
  bool safety = false;
  int required_unit = -1;
  bool fetch = false;
};

struct UnitState {
  int index = 0;
  int x = 0;
  int y = 0;
};

struct FlowEdge {
  int to = 0;
  int reverse = 0;
  int capacity = 0;
  int64_t cost = 0;
};

void AddFlowEdge(std::vector<std::vector<FlowEdge>>* graph, int from, int to,
                 int capacity, int64_t cost) {
  const int reverse_at_to = static_cast<int>((*graph)[to].size());
  const int reverse_at_from = static_cast<int>((*graph)[from].size());
  (*graph)[from].push_back({to, reverse_at_to, capacity, cost});
  (*graph)[to].push_back({from, reverse_at_from, 0, -cost});
}

int Distance(int x0, int y0, int x1, int y1) {
  return std::abs(x0 - x1) + std::abs(y0 - y1);
}

std::pair<int, int> TargetPosition(int target, int board_size) {
  return {target % board_size, target / board_size};
}

std::pair<int, int> NearestShed(int x, int y, int board_size) {
  auto result = ShedAccessTiles(board_size)[0];
  int best = Distance(x, y, result.first, result.second);
  for (const auto& candidate : ShedAccessTiles(board_size)) {
    const int distance = Distance(x, y, candidate.first, candidate.second);
    if (std::tie(distance, candidate.second, candidate.first) <
        std::tie(best, result.second, result.first)) {
      result = candidate;
      best = distance;
    }
  }
  return result;
}

UnitAction MoveToward(int x, int y, int target_x, int target_y) {
  if (x < target_x) return {UnitOp::kEast, -1, 1};
  if (x > target_x) return {UnitOp::kWest, -1, 1};
  if (y < target_y) return {UnitOp::kSouth, -1, 1};
  if (y > target_y) return {UnitOp::kNorth, -1, 1};
  return {UnitOp::kPass, -1, 1};
}

bool IsOfficialDirective(DirectiveOperation operation) {
  return operation >= DirectiveOperation::kPickup;
}

UnitOp DirectiveUnitOp(DirectiveOperation operation) {
  switch (operation) {
    case DirectiveOperation::kPickup:
      return UnitOp::kPickup;
    case DirectiveOperation::kDrop:
      return UnitOp::kDrop;
    case DirectiveOperation::kPlace:
      return UnitOp::kPlace;
    case DirectiveOperation::kPlant:
      return UnitOp::kPlant;
    case DirectiveOperation::kWater:
      return UnitOp::kWater;
    case DirectiveOperation::kHarvest:
      return UnitOp::kHarvest;
    case DirectiveOperation::kFertilize:
      return UnitOp::kFertilize;
    case DirectiveOperation::kDig:
      return UnitOp::kDig;
    case DirectiveOperation::kBuildCoop:
      return UnitOp::kBuildCoop;
    case DirectiveOperation::kBuildPasture:
      return UnitOp::kBuildPasture;
    case DirectiveOperation::kFeed:
      return UnitOp::kFeed;
    case DirectiveOperation::kCollectFertilizer:
      return UnitOp::kCollectFertilizer;
    case DirectiveOperation::kCare:
      return UnitOp::kCare;
    case DirectiveOperation::kPosition:
    case DirectiveOperation::kWait:
      return UnitOp::kPass;
  }
  return UnitOp::kPass;
}

UnitAction DirectiveAction(const UnitState& unit,
                           const UnitDirective& directive,
                           int board_size) {
  if (directive.operation == DirectiveOperation::kWait) {
    return {UnitOp::kPass, -1, 1};
  }
  const auto target = TargetPosition(directive.target, board_size);
  if (unit.x != target.first || unit.y != target.second) {
    return MoveToward(unit.x, unit.y, target.first, target.second);
  }
  if (!IsOfficialDirective(directive.operation)) {
    return {UnitOp::kPass, -1, 1};
  }
  const bool quantity =
      directive.operation == DirectiveOperation::kPickup ||
      directive.operation == DirectiveOperation::kPlace;
  return {DirectiveUnitOp(directive.operation), directive.item,
          quantity ? directive.quantity : 1};
}

bool UnitEligible(const UnitState& unit, const Obligation& obligation) {
  if (obligation.required_unit >= 0 &&
      unit.index != obligation.required_unit) {
    return false;
  }
  const int role = obligation.role;
  if (role == kFarmerOnly) return unit.index == 0;
  if (role == kHandOnly) return unit.index > 0;
  return true;
}

bool ProductionTomorrow(const Tile& tile, int day) {
  if (tile.kind == TileKind::kPlant && kCrops[tile.crop].ongoing) {
    const CropData& crop = kCrops[tile.crop];
    const int since_first = day + 1 - tile.planted_day - crop.first_yield_day;
    return since_first >= 0 && since_first % crop.interval == 0 &&
           since_first / crop.interval + 1 <= crop.max_yield;
  }
  if (tile.kind == TileKind::kStructure && tile.has_animal) {
    const AnimalData& animal = kAnimals[tile.animal];
    const int since_first = day + 1 - tile.placed_day - animal.first_yield_day;
    return since_first >= 0 && since_first % animal.interval == 0;
  }
  return false;
}

bool NeedsYieldWater(const Tile& tile, int day) {
  if (tile.kind != TileKind::kPlant || tile.watered_today) return false;
  const CropData& crop = kCrops[tile.crop];
  if (crop.ongoing) return ProductionTomorrow(tile, day);
  const int age = day - tile.planted_day;
  const int start = (crop.max_yield_day + 1) / 2;
  return age >= start && age <= crop.max_yield_day &&
         tile.yield_units < crop.max_yield;
}

UnitAction WorkEffect(WorkKind kind) {
  switch (kind) {
    case WorkKind::kHarvest:
    case WorkKind::kCollectProduct:
      return {UnitOp::kHarvest, -1, 1};
    case WorkKind::kFertilize:
      return {UnitOp::kFertilize, -1, 1};
    case WorkKind::kCareOnce:
      return {UnitOp::kCare, -1, 1};
    case WorkKind::kCollectFertilizer:
      return {UnitOp::kCollectFertilizer, -1, 1};
    case WorkKind::kClear:
      return {UnitOp::kDig, -1, 1};
    case WorkKind::kWaterOnce:
      return {UnitOp::kWater, -1, 1};
    case WorkKind::kFeedOnce:
      return {UnitOp::kFeed, -1, 1};
    case WorkKind::kStore:
      return {UnitOp::kPlace, -1, 1};
    case WorkKind::kFetch:
      return {UnitOp::kPickup, -1, 1};
    case WorkKind::kDirectivePosition:
    case WorkKind::kDirectiveWait:
    case WorkKind::kDirectivePickup:
    case WorkKind::kDirectiveDrop:
    case WorkKind::kDirectivePlace:
    case WorkKind::kDirectivePlant:
    case WorkKind::kDirectiveWater:
    case WorkKind::kDirectiveHarvest:
    case WorkKind::kDirectiveFertilize:
    case WorkKind::kDirectiveDig:
    case WorkKind::kDirectiveBuildCoop:
    case WorkKind::kDirectiveBuildPasture:
    case WorkKind::kDirectiveFeed:
    case WorkKind::kDirectiveCollectFertilizer:
    case WorkKind::kDirectiveCare:
      return {UnitOp::kPass, -1, 1};
  }
  return {UnitOp::kPass, -1, 1};
}

int RequiredItem(WorkKind kind) {
  if (kind == WorkKind::kFertilize) return item::kFertilizer;
  if (kind == WorkKind::kFeedOnce) return item::kWheat;
  return -1;
}

bool WorkReady(const WorkOrder& order, const Tile& tile, int day) {
  switch (order.kind) {
    case WorkKind::kHarvest:
      return tile.kind == TileKind::kPlant && tile.yield_units > 0 &&
             day - tile.planted_day >= kCrops[tile.crop].first_yield_day;
    case WorkKind::kCollectProduct:
      return tile.kind == TileKind::kStructure && tile.has_animal &&
             tile.yield_units > 0;
    case WorkKind::kFertilize:
      return tile.kind == TileKind::kPlant;
    case WorkKind::kCareOnce:
      return tile.kind == TileKind::kStructure && tile.has_animal &&
             !tile.cared_today;
    case WorkKind::kCollectFertilizer:
      return tile.kind == TileKind::kStructure && tile.has_animal &&
             tile.fertilizer_available;
    case WorkKind::kClear:
      return tile.kind != TileKind::kEmpty && tile.kind != TileKind::kLocked &&
             !(tile.kind == TileKind::kStructure && tile.has_animal);
    case WorkKind::kWaterOnce:
      return tile.kind == TileKind::kPlant && !tile.watered_today;
    case WorkKind::kFeedOnce:
      return tile.kind == TileKind::kStructure && tile.has_animal &&
             !tile.fed_today;
    case WorkKind::kStore:
    case WorkKind::kFetch:
    case WorkKind::kDirectivePosition:
    case WorkKind::kDirectiveWait:
    case WorkKind::kDirectivePickup:
    case WorkKind::kDirectiveDrop:
    case WorkKind::kDirectivePlace:
    case WorkKind::kDirectivePlant:
    case WorkKind::kDirectiveWater:
    case WorkKind::kDirectiveHarvest:
    case WorkKind::kDirectiveFertilize:
    case WorkKind::kDirectiveDig:
    case WorkKind::kDirectiveBuildCoop:
    case WorkKind::kDirectiveBuildPasture:
    case WorkKind::kDirectiveFeed:
    case WorkKind::kDirectiveCollectFertilizer:
    case WorkKind::kDirectiveCare:
      return true;
  }
  return false;
}

int PairCost(const UnitState& unit, const Obligation& obligation,
             const PrivateState& priv, int board_size, int current_step) {
  if (!UnitEligible(unit, obligation)) {
    return std::numeric_limits<int>::max();
  }
  if (obligation.fetch) {
    const int64_t carried =
        priv.inventories[unit.index].Get(obligation.required_item);
    if (carried >= obligation.quantity ||
        priv.shed[obligation.required_item] <= 0) {
      return std::numeric_limits<int>::max();
    }
    const auto shed = NearestShed(unit.x, unit.y, board_size);
    return Distance(unit.x, unit.y, shed.first, shed.second);
  }
  if (obligation.store) {
    if (priv.inventories[unit.index].Get(obligation.required_item) <= 0) {
      return std::numeric_limits<int>::max();
    }
    const auto shed = NearestShed(unit.x, unit.y, board_size);
    return Distance(unit.x, unit.y, shed.first, shed.second);
  }
  const auto target = TargetPosition(obligation.target, board_size);
  if (obligation.required_item < 0 ||
      priv.inventories[unit.index].Get(obligation.required_item) > 0) {
    const int distance = Distance(unit.x, unit.y, target.first, target.second);
    if (obligation.effect.op == UnitOp::kPlant &&
        current_step + distance > obligation.deadline) {
      return std::numeric_limits<int>::max();
    }
    return distance;
  }
  if (priv.shed[obligation.required_item] <= 0) {
    return std::numeric_limits<int>::max();
  }
  const auto shed = NearestShed(unit.x, unit.y, board_size);
  return Distance(unit.x, unit.y, shed.first, shed.second) + 1 +
         Distance(shed.first, shed.second, target.first, target.second);
}

std::vector<std::pair<int, int>> MinimumCostAssignments(
    const std::vector<Obligation>& obligations,
    const std::vector<int>& obligation_indices,
    const std::vector<UnitState>& units, const std::vector<bool>& unit_used,
    const PrivateState& priv, int board_size, int current_step) {
  std::vector<int> unit_indices;
  for (int unit = 0; unit < static_cast<int>(units.size()); ++unit) {
    if (!unit_used[unit]) unit_indices.push_back(unit);
  }
  if (obligation_indices.empty() || unit_indices.empty()) return {};

  const int source = 0;
  const int obligation_start = 1;
  const int unit_start = obligation_start + obligation_indices.size();
  const int sink = unit_start + unit_indices.size();
  const int node_count = sink + 1;
  std::vector<std::vector<FlowEdge>> graph(node_count);
  for (int row = 0; row < static_cast<int>(obligation_indices.size()); ++row) {
    const Obligation& obligation = obligations[obligation_indices[row]];
    const int64_t selection_cost =
        static_cast<int64_t>(obligation.deadline) * 1'000'000'000LL +
        static_cast<int64_t>(row) * 100;
    AddFlowEdge(&graph, source, obligation_start + row, 1, selection_cost);
    for (int column = 0; column < static_cast<int>(unit_indices.size());
         ++column) {
      const int unit = unit_indices[column];
      const int pair_cost =
          PairCost(units[unit], obligation, priv, board_size, current_step);
      if (pair_cost == std::numeric_limits<int>::max()) continue;
      AddFlowEdge(&graph, obligation_start + row, unit_start + column, 1,
                  static_cast<int64_t>(pair_cost) * 10'000 +
                      units[unit].index);
    }
  }
  for (int column = 0; column < static_cast<int>(unit_indices.size());
       ++column) {
    AddFlowEdge(&graph, unit_start + column, sink, 1, 0);
  }

  while (true) {
    const int64_t infinity = std::numeric_limits<int64_t>::max() / 4;
    std::vector<int64_t> distance(node_count, infinity);
    std::vector<int> previous_node(node_count, -1);
    std::vector<int> previous_edge(node_count, -1);
    std::vector<bool> queued(node_count, false);
    std::queue<int> queue;
    distance[source] = 0;
    queue.push(source);
    queued[source] = true;
    while (!queue.empty()) {
      const int from = queue.front();
      queue.pop();
      queued[from] = false;
      for (int edge_index = 0;
           edge_index < static_cast<int>(graph[from].size()); ++edge_index) {
        const FlowEdge& edge = graph[from][edge_index];
        if (edge.capacity <= 0 ||
            distance[edge.to] <= distance[from] + edge.cost) {
          continue;
        }
        distance[edge.to] = distance[from] + edge.cost;
        previous_node[edge.to] = from;
        previous_edge[edge.to] = edge_index;
        if (!queued[edge.to]) {
          queue.push(edge.to);
          queued[edge.to] = true;
        }
      }
    }
    if (previous_node[sink] < 0) break;
    for (int node = sink; node != source; node = previous_node[node]) {
      FlowEdge& edge = graph[previous_node[node]][previous_edge[node]];
      --edge.capacity;
      ++graph[node][edge.reverse].capacity;
    }
  }

  std::vector<std::pair<int, int>> result;
  for (int row = 0; row < static_cast<int>(obligation_indices.size()); ++row) {
    const int node = obligation_start + row;
    for (const FlowEdge& edge : graph[node]) {
      if (edge.to < unit_start || edge.to >= sink || edge.capacity != 0) {
        continue;
      }
      const int column = edge.to - unit_start;
      result.emplace_back(obligation_indices[row], unit_indices[column]);
      break;
    }
  }
  std::sort(result.begin(), result.end(), [&](const auto& left, const auto& right) {
    return std::tie(obligations[left.first].deadline,
                    obligations[left.first].key, units[left.second].index) <
           std::tie(obligations[right.first].deadline,
                    obligations[right.first].key, units[right.second].index);
  });
  return result;
}

UnitAction ImmediateAction(const UnitState& unit, const Obligation& obligation,
                           const PrivateState& priv, int board_size,
                           int64_t shed_room) {
  if (obligation.fetch) {
    const auto shed = NearestShed(unit.x, unit.y, board_size);
    if (unit.x != shed.first || unit.y != shed.second) {
      return MoveToward(unit.x, unit.y, shed.first, shed.second);
    }
    const int64_t carried =
        priv.inventories[unit.index].Get(obligation.required_item);
    return {UnitOp::kPickup, obligation.required_item,
            std::min(obligation.quantity - carried,
                     priv.shed[obligation.required_item])};
  }
  if (obligation.store) {
    const auto shed = NearestShed(unit.x, unit.y, board_size);
    if (unit.x != shed.first || unit.y != shed.second) {
      return MoveToward(unit.x, unit.y, shed.first, shed.second);
    }
    const int64_t carried =
        priv.inventories[unit.index].Get(obligation.required_item);
    return {UnitOp::kPlace, obligation.required_item,
            std::min({obligation.quantity, carried, shed_room})};
  }
  if (obligation.required_item >= 0 &&
      priv.inventories[unit.index].Get(obligation.required_item) <= 0) {
    const auto shed = NearestShed(unit.x, unit.y, board_size);
    if (unit.x != shed.first || unit.y != shed.second) {
      return MoveToward(unit.x, unit.y, shed.first, shed.second);
    }
    return {UnitOp::kPickup, obligation.required_item, 1};
  }
  const auto target = TargetPosition(obligation.target, board_size);
  if (unit.x != target.first || unit.y != target.second) {
    return MoveToward(unit.x, unit.y, target.first, target.second);
  }
  return obligation.effect;
}

}  // namespace

PlayerAction Session::CompileAction(const Engine& engine, int player) {
  const Farm& farm = engine.farm(player);
  const PrivateState& priv = engine.priv(player);
  const int step = engine.step_index();
  const int day = step / config_.turns_per_day;
  const int end_of_day = (day + 1) * config_.turns_per_day - 1;
  std::vector<Obligation> obligations;

  const auto add = [&](int64_t key, int target, UnitAction effect,
                       int required_item, Priority priority, int deadline,
                       int role = kAnyUnit, int work_index = -1,
                       bool store = false, int64_t quantity = 1,
                       bool safety = false, int required_unit = -1,
                       bool fetch = false) {
    if (!store) {
      for (Obligation& existing : obligations) {
        if (existing.target != target || existing.effect.op != effect.op ||
            existing.effect.arg != effect.arg ||
            existing.required_item != required_item || existing.role != role ||
            existing.store != store || existing.required_unit != required_unit ||
            existing.fetch != fetch) {
          continue;
        }
        existing.key = std::min(existing.key, key);
        existing.priority = std::max(existing.priority, priority);
        existing.deadline = std::min(existing.deadline, deadline);
        if (work_index >= 0) existing.work_index = work_index;
        existing.quantity = std::max(existing.quantity, quantity);
        existing.effect.n = std::max(existing.effect.n, effect.n);
        existing.safety = existing.safety || safety;
        return;
      }
    }
    obligations.push_back({key, target, effect, required_item, priority,
                           deadline, role, work_index, store, quantity,
                           safety, required_unit, fetch});
  };

  for (int target = 0; target < static_cast<int>(assets_.size()); ++target) {
    const AssetContract& contract = assets_[target];
    if (!contract.active) continue;
    const Tile& tile = farm.tiles[target];
    const int64_t base_key = AssetKey(target) * 16;
    if (!ContractMatches(contract, tile)) {
      if (tile.kind == TileKind::kLocked) continue;
      if (tile.kind == TileKind::kWeed) {
        add(base_key, target, {UnitOp::kDig, -1, 1}, -1,
            contract.priority, end_of_day);
      } else if (contract.kind == AssetKind::kCrop &&
                 tile.kind == TileKind::kEmpty && step < end_of_day &&
                 contract.item >= 0 && contract.item < kNumCrops &&
                 priv.seeds[contract.item] > 0) {
        add(base_key + 1, target, {UnitOp::kPlant, contract.item, 1}, -1,
            contract.priority, end_of_day - 1);
      } else if (contract.kind == AssetKind::kAnimal &&
                 tile.kind == TileKind::kEmpty) {
        const int animal = contract.item - item::kGoose;
        const UnitOp build = kAnimals[animal].structure == StructureKind::kCoop
                                 ? UnitOp::kBuildCoop
                                 : UnitOp::kBuildPasture;
        add(base_key + 1, target, {build, -1, 1}, -1, contract.priority,
            config_.episode_steps);
      } else if (contract.kind == AssetKind::kAnimal &&
                 tile.kind == TileKind::kStructure && !tile.has_animal &&
                 tile.structure ==
                     kAnimals[contract.item - item::kGoose].structure) {
        add(base_key + 2, target, {UnitOp::kPlace, contract.item, 1},
            contract.item, contract.priority, config_.episode_steps);
      }
      continue;
    }

    if (contract.kind == AssetKind::kCrop) {
      const bool establishing = !tile.watered_today && tile.planted_day == day;
      const bool survival = !tile.watered_today &&
                            tile.consecutive_unwatered >= 1 &&
                            contract.maintenance != Maintenance::kNone;
      const bool yield = contract.maintenance == Maintenance::kYield &&
                         NeedsYieldWater(tile, day);
      if (establishing || survival || yield) {
        add(base_key + 3, target, {UnitOp::kWater, -1, 1}, -1,
            establishing ? Priority::kHigh : contract.priority,
            (establishing || survival) ? end_of_day : config_.episode_steps,
            kAnyUnit, -1, false, 1, establishing);
      }
      continue;
    }

    const int animal = tile.animal;
    if (contract.maintenance != Maintenance::kNone && !tile.fed_today &&
        (tile.consecutive_unfed >= 1 ||
         contract.maintenance == Maintenance::kCared)) {
      add(base_key + 4, target, {UnitOp::kFeed, -1, 1}, item::kWheat,
          contract.priority, tile.consecutive_unfed >= 1
                                 ? end_of_day
                                 : config_.episode_steps);
    }
    if (contract.maintenance == Maintenance::kCared && !tile.cared_today) {
      add(base_key + 5, target, {UnitOp::kCare, -1, 1}, -1,
          contract.priority, end_of_day);
    }
    if (contract.product_collection == ProductCollection::kBeforeCap &&
        tile.yield_units > 0 && ProductionTomorrow(tile, day)) {
      const AnimalData& data = kAnimals[animal];
      const int production =
          1 + ((tile.fed_today || contract.maintenance == Maintenance::kCared)
                   ? tile.pending_care_bonus
                   : 0);
      if (tile.yield_units + production > data.max_held) {
        add(base_key + 6, target, {UnitOp::kHarvest, -1, 1}, -1,
            contract.priority, end_of_day);
      }
    }
    if (contract.fertilizer_collection == FertilizerCollection::kDaily &&
        tile.fertilizer_available) {
      add(base_key + 7, target, {UnitOp::kCollectFertilizer, -1, 1}, -1,
          contract.priority, end_of_day);
    }
  }

  for (int index = 0; index < static_cast<int>(work_.size()); ++index) {
    const WorkOrder& order = work_[index];
    if (order.dispatched_step >= 0) continue;
    if (order.kind == WorkKind::kStore) {
      add(StoreKey(order.item) * 16, -1,
          {UnitOp::kPlace, order.item, order.quantity}, order.item,
          order.priority, config_.episode_steps, kAnyUnit, index, true,
          order.quantity);
      continue;
    }
    if (order.target < 0 || order.target >= static_cast<int>(farm.tiles.size()) ||
        !WorkReady(order, farm.tiles[order.target], day)) {
      continue;
    }
    add(WorkKey(order.target, order.kind) * 16, order.target,
        WorkEffect(order.kind), RequiredItem(order.kind), order.priority,
        config_.episode_steps, kAnyUnit, index);
  }

  for (const FetchIntent& fetch : fetches_) {
    if (!fetch.active || fetch.unit < 0 ||
        fetch.unit >= static_cast<int>(priv.inventories.size()) ||
        fetch.item < 0 || fetch.item >= kNumItems ||
        priv.inventories[fetch.unit].Get(fetch.item) >= fetch.quantity) {
      continue;
    }
    add(FetchKey(fetch.unit) * 16, -1,
        {UnitOp::kPickup, fetch.item, fetch.quantity}, fetch.item,
        Priority::kHigh, step, kAnyUnit, -1, false, fetch.quantity, false,
        fetch.unit, true);
  }

  for (const PositionIntent& position : positions_) {
    if (!position.active) continue;
    add(PositionKey(position.role) * 16, position.target,
        {UnitOp::kPass, -1, 1}, -1, position.priority,
        config_.episode_steps,
        position.role == PositionRole::kFarmer ? kFarmerOnly : kHandOnly);
  }

  std::array<int64_t, kNumProducts> sell_need{};
  for (const std::optional<MarketOrder>& order : market_prefix_) {
    if (order && order->kind == OrderKind::kSell && order->item >= 0 &&
        order->item < kNumProducts) {
      sell_need[order->item] += order->remaining;
    }
  }
  for (int item_index = 0; item_index < kNumProducts; ++item_index) {
    int64_t remaining = std::max<int64_t>(0, sell_need[item_index] -
                                                priv.shed[item_index]);
    if (remaining <= 0) continue;
    for (int unit = 0; unit < static_cast<int>(priv.inventories.size()) &&
                       remaining > 0;
         ++unit) {
      const int64_t carried = priv.inventories[unit].Get(item_index);
      if (carried <= 0) continue;
      add(StoreKey(item_index) * 16 - 1, -1,
          {UnitOp::kPlace, item_index, std::min(carried, remaining)}, item_index,
          Priority::kHigh, step, kAnyUnit, -1, true,
          std::min(carried, remaining), false, unit);
      remaining -= carried;
    }
  }

  std::sort(obligations.begin(), obligations.end(),
            [](const Obligation& left, const Obligation& right) {
              return std::tuple{-static_cast<int>(left.priority), left.deadline,
                                left.key} <
                     std::tuple{-static_cast<int>(right.priority), right.deadline,
                                right.key};
            });

  std::vector<UnitState> units;
  units.push_back({0, farm.farmer_x, farm.farmer_y});
  for (int hand = 0; hand < static_cast<int>(farm.hands.size()); ++hand) {
    units.push_back({hand + 1, farm.hands[hand].first, farm.hands[hand].second});
  }
  PlayerAction requested;
  requested.hands.resize(farm.hands.size(), {UnitOp::kPass, -1, 1});
  std::vector<int> assigned_work(units.size(), -1);
  std::vector<int> assigned_obligation(units.size(), -1);
  std::vector<bool> unit_used(units.size(), false);
  std::vector<bool> submitted_directive(units.size(), false);
  for (const UnitDirective& directive : directives_) {
    if (!directive.active || directive.unit < 0 ||
        directive.unit >= static_cast<int>(units.size())) {
      continue;
    }
    const int unit = directive.unit;
    const UnitAction action =
        DirectiveAction(units[unit], directive, config_.board_size);
    if (unit == 0) {
      requested.farmer = action;
    } else {
      requested.hands[unit - 1] = action;
    }
    submitted_directive[unit] =
        IsOfficialDirective(directive.operation) &&
        action.op == DirectiveUnitOp(directive.operation);
    unit_used[unit] = true;
  }
  std::array<int64_t, kNumItems> reserved_shed{};
  const int64_t shed_room =
      std::max<int64_t>(0, config_.shed_capacity - ShedTotal(priv));

  const auto assign = [&](const std::vector<int>& obligation_indices) {
    const auto assignments = MinimumCostAssignments(
        obligations, obligation_indices, units, unit_used, priv,
        config_.board_size, step);
    for (const auto& [obligation_index, best_unit] : assignments) {
      const Obligation& obligation = obligations[obligation_index];
      UnitAction action = ImmediateAction(units[best_unit], obligation, priv,
                                          config_.board_size, shed_room);
      if (action.op == UnitOp::kPlace && action.n <= 0) continue;
      if (action.op == UnitOp::kPickup) {
        const int item = action.arg;
        const int64_t available =
            std::max<int64_t>(0, priv.shed[item] - reserved_shed[item]);
        action.n = std::min(action.n, available);
        if (action.n <= 0) continue;
        reserved_shed[item] += action.n;
      }
      if (best_unit == 0) {
        requested.farmer = action;
      } else {
        requested.hands[best_unit - 1] = action;
      }
      assigned_work[best_unit] = obligation.work_index;
      assigned_obligation[best_unit] = obligation_index;
      unit_used[best_unit] = true;
    }
  };

  std::vector<int> safety_indices;
  for (int index = 0; index < static_cast<int>(obligations.size()); ++index) {
    if (obligations[index].safety) safety_indices.push_back(index);
  }
  assign(safety_indices);
  for (int priority = static_cast<int>(Priority::kHigh);
       priority >= static_cast<int>(Priority::kLow); --priority) {
    std::vector<int> obligation_indices;
    for (int index = 0; index < static_cast<int>(obligations.size()); ++index) {
      if (!obligations[index].safety &&
          static_cast<int>(obligations[index].priority) == priority) {
        obligation_indices.push_back(index);
      }
    }
    assign(obligation_indices);
  }

  UnitPhaseResult compiled =
      CompileUnitPhase(config_, farm, priv, requested, day);
  compiled.actual.market = market_prefix_;
  for (int unit = 0; unit < static_cast<int>(submitted_directive.size());
       ++unit) {
    if (submitted_directive[unit] && unit < static_cast<int>(directives_.size())) {
      directives_[unit] = UnitDirective{};
    }
  }
  for (int unit = 0; unit < static_cast<int>(assigned_obligation.size());
       ++unit) {
    const int obligation_index = assigned_obligation[unit];
    if (obligation_index < 0 ||
        compiled.trace[unit].status != UnitActionStatus::kApplied ||
        compiled.trace[unit].actual.op != UnitOp::kHarvest) {
      continue;
    }
    const int target = obligations[obligation_index].target;
    if (target < 0 || target >= static_cast<int>(assets_.size()) ||
        !assets_[target].active ||
        farm.tiles[target].kind != TileKind::kPlant ||
        kCrops[farm.tiles[target].crop].ongoing) {
      continue;
    }
    assets_[target] = AssetContract{};
    terminal_asset_status_[target] = Status::kSatisfied;
    terminal_asset_reason_[target] = BlockReason::kNone;
    terminal_asset_step_[target] = step + 1;
  }
  for (int unit = 0; unit < static_cast<int>(assigned_work.size()); ++unit) {
    const int work_index = assigned_work[unit];
    if (work_index < 0 || compiled.trace[unit].status != UnitActionStatus::kApplied) {
      continue;
    }
    WorkOrder& order = work_[work_index];
    if (order.kind == WorkKind::kStore) {
      order.quantity -= compiled.trace[unit].actual.n;
      if (order.quantity <= 0) order.dispatched_step = step;
    } else if (compiled.trace[unit].actual.op == WorkEffect(order.kind).op) {
      order.dispatched_step = step;
    }
  }
  return compiled.actual;
}

}  // namespace kagg::intents
