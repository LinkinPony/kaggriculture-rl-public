// Unit-tile geometry and resource reachability from public positions and own inventories.
#pragma once

#include <vector>

#include "types.hpp"

namespace kagg::production {

// Tile obligations visible on either farm; `plantable` marks empty unlocked land.
struct Due {
  bool water = false;
  bool feed = false;
  bool care = false;
  bool collect = false;
  bool harvest = false;
  bool plantable = false;
  bool any() const { return water || feed || care || collect || harvest; }
};

struct FarmGeometry {
  int board = 0;
  std::vector<int> unit_cells;        // present units in official order
  std::vector<Due> due;               // per cell
  std::vector<int> nearest_unit;      // per cell: Manhattan distance from the closest unit
  std::vector<int> units_within_two;  // per cell
  std::vector<int> shed_distance;     // per cell: distance to the closest shed access tile
};

int Distance(int cell, int other, int board);
Due DueTasks(const Tile& tile, int day);
FarmGeometry ComputeGeometry(const Config& config, const Farm& farm, int day);

// Writes the board::k* geometry fields for every unlocked cell into rows of
// kBoardFeatures doubles. `priv` enables own-seat resource reachability and
// must be null for the opponent, whose inventories are hidden.
void EncodeGeometry(const Config& config, const Farm& farm, const PrivateState* priv,
                    const FarmGeometry& geometry, int step, double* rows);

// Writes kUnitFeatures doubles for each present unit; absent slots stay zero.
void EncodeUnits(const FarmGeometry& geometry, int units, double* output);

}  // namespace kagg::production
