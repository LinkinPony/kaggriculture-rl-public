#include "derived/features.hpp"

#include <algorithm>
#include <limits>

#include "production/features.hpp"

namespace kagg::derived {
namespace {

constexpr int kFar = 1000000;

int ServiceDelay(const Config& config, const production::FarmGeometry& geometry,
                 const PrivateState* priv, int unit, int cell, bool feed) {
  const int from = geometry.unit_cells[unit];
  const int direct = production::Distance(from, cell, config.board_size);
  if (!feed || priv == nullptr) return direct;
  if (unit < static_cast<int>(priv->inventories.size()) &&
      priv->inventories[unit].Get(item::kWheat) > 0) return direct;
  int best = kFar;
  for (const auto& [x, y] : ShedAccessTiles(config.board_size)) {
    const int access = y * config.board_size + x;
    const int approach = production::Distance(from, access, config.board_size);
    const int purchase_delay = priv->shed[item::kWheat] > 0 ? 0 : 1;
    best = std::min(best, std::max(approach, purchase_delay) + 1 +
        production::Distance(access, cell, config.board_size));
  }
  return best;
}

}  // namespace

int CriticalTasks(const Tile& tile, int step, const Config& config) {
  const bool plant = tile.kind == TileKind::kPlant;
  const bool animal = tile.kind == TileKind::kStructure && tile.has_animal;
  const bool maintenance = (plant && !tile.watered_today && tile.consecutive_unwatered >= 1) ||
      (animal && !tile.fed_today && tile.consecutive_unfed >= 1);
  const int end = std::min(config.episode_steps - 2,
                          (step / config.turns_per_day + 1) * config.turns_per_day - 1);
  const bool decay = plant && production::Harvestable(tile, step / config.turns_per_day) &&
      tile.max_lifespan_step >= 0 && tile.max_lifespan_step <= end;
  return static_cast<int>(maintenance) + static_cast<int>(decay);
}

int TaskDeadline(const Tile& tile, int step, const Config& config) {
  int end = std::min(config.episode_steps - 2,
                     (step / config.turns_per_day + 1) * config.turns_per_day - 1);
  if (tile.max_lifespan_step >= 0 && production::Harvestable(tile, step / config.turns_per_day)) {
    end = std::min(end, std::max(step, tile.max_lifespan_step));
  }
  return end;
}

namespace {

double BagQuote(const parallel::StateView& state, const Inventory& bag) {
  double value = 0;
  for (const auto& [item, count] : bag.items) {
    if (item < kNumProducts) value += Sell(state.config(), item, state.market().inventory[item], count);
  }
  return value;
}

}  // namespace

Execution ExecutionFeatures(const parallel::StateView& state, int seat, int units) {
  Execution result;
  const Config& config = state.config();
  const int board = config.board_size, area = board * board, step = state.step_index();
  const int day = step / config.turns_per_day, last = config.episode_steps - 2;
  const int end = std::min(last, (day + 1) * config.turns_per_day - 1);
  const int left = std::max(0, end - step + 1);
  const double clock = config.turns_per_day;
  result.boards.assign(2 * area * kBoardFeatures, 0);
  result.units.assign(2 * units * kUnitFeatures, 0);
  const auto& own = state.priv(seat);
  std::vector<int64_t> lost(own.inventories.size(), 0);
  int64_t room = std::max<int64_t>(0, config.shed_capacity - ShedTotal(own));
  for (size_t unit = 0; unit < own.inventories.size(); ++unit) {
    for (const auto& [item, count] : own.inventories[unit].items) {
      const int64_t accepted = std::min(room, count);
      room -= accepted;
      if (item < kNumProducts) {
        result.carried[item] += count;
        if ((day + 1) * config.turns_per_day - 1 <= last) result.overflow[item] += count - accepted;
      }
      if ((day + 1) * config.turns_per_day - 1 <= last) lost[unit] += count - accepted;
    }
  }
  for (int side = 0; side < 2; ++side) {
    const Farm& farm = state.farm(side == 0 ? seat : 1 - seat);
    const PrivateState* priv = side == 0 ? &own : nullptr;
    auto& geometry = result.geometry[side] = production::ComputeGeometry(config, farm, day);
    const int count = std::min<int>(units, geometry.unit_cells.size());
    std::vector<int> assigned(count, 0), radius(count, 0), owners(area, 0), critical(area, 0);
    for (int cell = 0; cell < area; ++cell) {
      const Tile& tile = farm.tiles[cell];
      critical[cell] = CriticalTasks(tile, step, config);
      int nearest = kFar;
      for (int unit = 0; unit < count; ++unit) {
        const int distance = production::Distance(geometry.unit_cells[unit], cell, board);
        if (distance < nearest) { nearest = distance; owners[cell] = unit; }
      }
      if (critical[cell]) {
        assigned[owners[cell]] += critical[cell];
        radius[owners[cell]] = std::max(radius[owners[cell]], nearest);
        result.critical[side] += critical[cell];
        result.travel[side] = std::max(result.travel[side], nearest);
      }
    }
    for (int cell = 0; cell < area; ++cell) {
      const Tile& tile = farm.tiles[cell];
      double* row = result.boards.data() + (side * area + cell) * kBoardFeatures;
      row[19] = priv != nullptr;
      if (!production::Productive(tile)) continue;
      Interventions(state, tile, geometry.shed_distance[cell], row);
      const bool feed = tile.has_animal && !tile.fed_today;
      int delay = kFar, reachable = 0;
      for (int unit = 0; unit < count; ++unit) {
        const int distance = ServiceDelay(config, geometry, priv, unit, cell, feed);
        delay = std::min(delay, distance);
        reachable += step + distance <= TaskDeadline(tile, step, config);
      }
      row[12] = delay / clock;
      row[13] = (TaskDeadline(tile, step, config) - step - delay) / clock;
      int ready = production::Harvestable(tile, day) ? step :
          production::Describe(tile, config, step).next_production_step;
      if (tile.kind == TileKind::kPlant && !kCrops[tile.crop].ongoing && tile.yield_units > 0) {
        ready = std::max(step, (tile.planted_day + kCrops[tile.crop].first_yield_day) * config.turns_per_day);
      }
      if (ready >= 0) {
        const int harvest = std::max(ready, step + geometry.nearest_unit[cell]);
        const int sell = Delivery(config, harvest, geometry.shed_distance[cell]);
        row[14] = Time(sell - step, config);
        row[15] = Time(last - sell, config);
      }
      row[16] = Count(reachable);
      row[17] = Count(assigned[owners[cell]]);
      if (priv && feed) {
        row[18] = own.shed[item::kWheat] + result.carried[item::kWheat] < 1;
      }
      if (critical[cell] && !reachable) ++result.unreachable[side];
    }
    for (int unit = 0; unit < count; ++unit) {
      double* row = result.units.data() + (side * units + unit) * kUnitFeatures;
      const int from = geometry.unit_cells[unit];
      for (int cell = 0; cell < area; ++cell) {
        const auto& due = geometry.due[cell];
        const int distance = production::Distance(from, cell, board);
        const int feed_delay = ServiceDelay(config, geometry, priv, unit, cell, true);
        const bool reached = step + distance <= TaskDeadline(farm.tiles[cell], step, config);
        const std::array<bool, 6> tasks = {due.water && reached,
            due.feed && step + feed_delay <= TaskDeadline(farm.tiles[cell], step, config),
            due.care && reached, due.collect && reached, due.harvest && reached,
            due.plantable && distance + 2 <= left};
        for (int task = 0; task < 6; ++task) row[task] += tasks[task];
        if (critical[cell] && reached) {
          for (int other = 0; other < count; ++other) {
            if (other != unit && step + production::Distance(geometry.unit_cells[other], cell, board) <=
                TaskDeadline(farm.tiles[cell], step, config)) { row[15] += 1; break; }
          }
        }
      }
      row[6] = Count(assigned[unit]);
      row[7] = (assigned[unit] + radius[unit]) / clock;
      int shed = 2 * board;
      for (const auto& [x, y] : ShedAccessTiles(board)) {
        shed = std::min(shed, production::Distance(from, y * board + x, board));
      }
      if (priv && unit < static_cast<int>(priv->inventories.size())) {
        const auto& bag = priv->inventories[unit];
        row[8] = Money(BagQuote(state, bag));
        const int delivery = std::min(step + shed, (day + 1) * config.turns_per_day);
        row[9] = (delivery - step) / clock;
        row[10] = Time(last - delivery, config);
        row[11] = Count(lost[unit]);
        row[12] = Count(std::min<double>(bag.Get(item::kWheat), row[1]));
        int fertilizable = 0;
        for (int cell = 0; cell < area; ++cell) {
          fertilizable += farm.tiles[cell].kind == TileKind::kPlant &&
              farm.tiles[cell].fertilized_until_day < day + 2 &&
              production::Distance(from, cell, board) < left;
        }
        row[13] = Count(std::min<int64_t>(bag.Get(item::kFertilizer), fertilizable));
        row[14] = 1;
      }
      for (int task = 0; task < 6; ++task) row[task] = Count(row[task]);
      row[15] = Count(row[15]);
    }
  }
  return result;
}

}  // namespace kagg::derived
