#include "production/geometry.hpp"

#include <algorithm>
#include <array>
#include <limits>

#include "production/features.hpp"

namespace kagg::production {
namespace {

constexpr int kFar = std::numeric_limits<int>::max() / 4;

// Board geometry never depends on a player or game. Keep division out of the
// unit/tile inner loops, with bounded storage for nonstandard large boards.
class DistanceTable {
 public:
  explicit DistanceTable(int board) : board_(board), area_(board * board) {
    if (board <= 0 || board > 32) return;
    values_.resize(area_ * area_);
    for (int a = 0; a < area_; ++a) {
      for (int b = 0; b < area_; ++b) {
        values_[a * area_ + b] = Distance(a, b, board);
      }
    }
  }
  int board() const { return board_; }
  int operator()(int a, int b) const {
    return values_.empty() ? Distance(a, b, board_) : values_[a * area_ + b];
  }

 private:
  int board_, area_;
  std::vector<int> values_;
};

const DistanceTable& Distances(int board) {
  thread_local DistanceTable table(0);
  if (table.board() != board) table = DistanceTable(board);
  return table;
}

int Cell(std::pair<int, int> position, int board) {
  return position.second * board + position.first;
}

// Cheapest unit -> shed -> tile trip for a unit that must first pick up supplies.
int ViaShed(const std::array<int, 4>& unit_to_shed,
            const std::array<int, 4>& shed_to_cell) {
  int best = kFar;
  for (int access = 0; access < 4; ++access) {
    best = std::min(best, unit_to_shed[access] + 1 + shed_to_cell[access]);
  }
  return best;
}

}  // namespace

int Distance(int cell, int other, int board) {
  return std::abs(cell % board - other % board) + std::abs(cell / board - other / board);
}

Due DueTasks(const Tile& tile, int day) {
  Due due;
  const bool animal = tile.kind == TileKind::kStructure && tile.has_animal;
  due.water = tile.kind == TileKind::kPlant && !tile.watered_today;
  due.feed = animal && !tile.fed_today;
  due.care = animal && !tile.cared_today;
  due.collect = animal && tile.fertilizer_available;
  due.harvest = Harvestable(tile, day);
  due.plantable = tile.kind == TileKind::kEmpty;
  return due;
}

FarmGeometry ComputeGeometry(const Config& config, const Farm& farm, int day) {
  FarmGeometry geometry;
  const int board = geometry.board = config.board_size;
  const int area = board * board;
  const auto& distance = Distances(board);
  geometry.unit_cells.reserve(farm.hands.size() + 1);
  geometry.unit_cells.push_back(farm.farmer_y * board + farm.farmer_x);
  for (const auto& hand : farm.hands) geometry.unit_cells.push_back(Cell(hand, board));
  geometry.due.resize(area);
  geometry.nearest_unit.assign(area, kFar);
  geometry.units_within_two.assign(area, 0);
  geometry.shed_distance.assign(area, kFar);
  const auto access = ShedAccessTiles(board);
  std::vector<int> counts(area, 0), occupied;
  for (int unit : geometry.unit_cells) {
    if (counts[unit]++ == 0) occupied.push_back(unit);
  }
  for (int cell = 0; cell < area; ++cell) {
    geometry.due[cell] = DueTasks(farm.tiles[cell], day);
    for (int unit : occupied) {
      const int gap = distance(cell, unit);
      geometry.nearest_unit[cell] = std::min(geometry.nearest_unit[cell], gap);
      geometry.units_within_two[cell] += gap <= 2 ? counts[unit] : 0;
    }
    for (const auto& tile : access) {
      geometry.shed_distance[cell] =
          std::min(geometry.shed_distance[cell], distance(cell, Cell(tile, board)));
    }
  }
  return geometry;
}

void EncodeGeometry(const Config& config, const Farm& farm, const PrivateState* priv,
                    const FarmGeometry& geometry, int step, double* rows) {
  const int board = geometry.board;
  const int area = board * board;
  const auto& distance = Distances(board);
  const int day = step / config.turns_per_day;
  const double reach = 2.0 * board;
  // Remaining actionable steps today, including this one, bounded by the season.
  const int turns_left = std::min((day + 1) * config.turns_per_day, config.episode_steps - 1) - step;
  const auto access = ShedAccessTiles(board);
  std::array<int, 4> nearest_shed;
  nearest_shed.fill(kFar);
  std::vector<int> wheat_carriers, fertilizer_carriers;
  if (priv != nullptr) {
    for (size_t unit = 0; unit < geometry.unit_cells.size(); ++unit) {
      for (int i = 0; i < 4; ++i) {
        nearest_shed[i] = std::min(nearest_shed[i],
                                  distance(geometry.unit_cells[unit], Cell(access[i], board)));
      }
      const bool known = unit < priv->inventories.size();
      if (known && priv->inventories[unit].Get(item::kWheat) > 0) {
        wheat_carriers.push_back(geometry.unit_cells[unit]);
      }
      if (known && priv->inventories[unit].Get(item::kFertilizer) > 0) {
        fertilizer_carriers.push_back(geometry.unit_cells[unit]);
      }
    }
  }
  for (int cell = 0; cell < area; ++cell) {
    const Tile& tile = farm.tiles[cell];
    if (tile.kind == TileKind::kLocked) continue;
    double* row = rows + static_cast<size_t>(cell) * kBoardFeatures;
    row[board::kNearestUnitDistance] = geometry.nearest_unit[cell] / reach;
    row[board::kUnitsWithinTwo] = std::min(geometry.units_within_two[cell], 8) / 8.0;
    row[board::kReachableBeforeDayEnd] = geometry.nearest_unit[cell] + 1 <= turns_left;
    row[board::kShedDistance] = geometry.shed_distance[cell] / reach;
    if (priv == nullptr) continue;
    std::array<int, 4> shed_to_cell{};
    for (int i = 0; i < 4; ++i) shed_to_cell[i] = distance(Cell(access[i], board), cell);
    const auto nearest = [&](const std::vector<int>& carriers) {
      int best = kFar;
      for (int carrier : carriers) best = std::min(best, distance(carrier, cell));
      return best;
    };
    if (geometry.due[cell].feed) {
      const int carrier = nearest(wheat_carriers);
      row[board::kHasFeedCarrier] = carrier < kFar;
      row[board::kFeedCarrierDistance] = carrier < kFar ? carrier / reach : 0;
      row[board::kShedHasWheat] = priv->shed[item::kWheat] > 0;
      row[board::kFeedViaShedDistance] =
          priv->shed[item::kWheat] > 0 ? ViaShed(nearest_shed, shed_to_cell) / (2 * reach) : 0;
    }
    if (tile.kind == TileKind::kPlant && tile.fertilized_until_day < day + 2) {
      const int carrier = nearest(fertilizer_carriers);
      row[board::kHasFertilizerCarrier] = carrier < kFar;
      row[board::kFertilizerCarrierDistance] = carrier < kFar ? carrier / reach : 0;
      row[board::kShedHasFertilizer] = priv->shed[item::kFertilizer] > 0;
      row[board::kFertilizerViaShedDistance] = priv->shed[item::kFertilizer] > 0
          ? ViaShed(nearest_shed, shed_to_cell) / (2 * reach) : 0;
    }
  }
}

void EncodeUnits(const FarmGeometry& geometry, int units, double* output) {
  const int board = geometry.board;
  const int area = board * board;
  const auto& distance = Distances(board);
  const double reach = 2.0 * board;
  const int count = std::min<int>(units, geometry.unit_cells.size());
  std::vector<int> first_unit(area, -1);
  for (int unit = 0; unit < count; ++unit) {
    double* row = output + static_cast<size_t>(unit) * kUnitFeatures;
    const int here = geometry.unit_cells[unit];
    if (first_unit[here] >= 0) {
      const auto* previous = output + static_cast<size_t>(first_unit[here]) * kUnitFeatures;
      std::copy(previous, previous + kUnitFeatures, row);
      continue;
    }
    first_unit[here] = unit;
    std::array<int, 6> nearest;
    nearest.fill(kFar);
    std::array<int, 4> pressure{};
    for (int cell = 0; cell < area; ++cell) {
      const Due& due = geometry.due[cell];
      const int gap = distance(cell, here);
      const std::array<bool, 6> kinds = {due.water, due.feed, due.care, due.collect,
                                         due.harvest, due.plantable};
      for (int kind = 0; kind < 6; ++kind) {
        if (kinds[kind]) nearest[kind] = std::min(nearest[kind], gap);
      }
      if (!due.any()) continue;
      pressure[0] += cell / board < here / board;
      pressure[1] += cell / board > here / board;
      pressure[2] += cell % board > here % board;
      pressure[3] += cell % board < here % board;
    }
    for (int kind = 0; kind < 6; ++kind) {
      row[unit::kNearestNeedsWater + kind] = nearest[kind] < kFar ? nearest[kind] / reach : 0;
      row[unit::kHasNeedsWater + kind] = nearest[kind] < kFar;
    }
    for (int direction = 0; direction < 4; ++direction) {
      row[unit::kDueTilesNorth + direction] = std::min(pressure[direction], 16) / 16.0;
    }
  }
}

}  // namespace kagg::production
