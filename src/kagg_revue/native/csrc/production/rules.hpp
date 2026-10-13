// Shared deterministic tile transitions used by the engine and visible features.
#pragma once

#include "types.hpp"

namespace kagg::production {

void Water(Tile& tile, int day);
void Fertilize(Tile& tile, int day);
void Decay(Tile& tile, int step);
void RefreshPlant(Tile& tile, int day, int turns_per_day);
void RefreshAnimal(Tile& tile, int day);

}  // namespace kagg::production
