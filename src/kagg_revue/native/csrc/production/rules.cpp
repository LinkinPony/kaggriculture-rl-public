#include "production/rules.hpp"

#include <algorithm>

namespace kagg::production {

void Water(Tile& tile, int day) {
  tile.watered_today = true;
  const CropData& crop = kCrops[tile.crop];
  if (!crop.ongoing) {
    const int age_days = day - tile.planted_day;
    const int window_start = (crop.max_yield_day + 1) / 2;
    if (window_start <= age_days && age_days <= crop.max_yield_day) {
      const int bonus = tile.fertilized_until_day >= day ? 2 : 1;
      tile.yield_units = std::min(crop.max_yield, tile.yield_units + bonus);
    }
  }
}

void Fertilize(Tile& tile, int day) {
  tile.fertilized_until_day = std::max(tile.fertilized_until_day, day + 2);
}

void Decay(Tile& tile, int step) {
  const int mls = tile.max_lifespan_step;
  if (mls < 0 || step < mls) return;
  if ((step - mls) % 2 != 0) return;
  tile.yield_units -= 1;
  if (tile.yield_units <= 0) tile = MakeWeed();
}

void RefreshPlant(Tile& tile, int day, int turns_per_day) {
  const int next_day = day + 1;
  const bool was_watered = tile.watered_today;
  if (was_watered) {
    tile.consecutive_unwatered = 0;
  } else {
    tile.consecutive_unwatered += 1;
  }
  tile.watered_today = false;
  if (tile.consecutive_unwatered >= 2) {
    tile = MakeWeed();
    return;
  }
  const CropData& cd = kCrops[tile.crop];
  if (!cd.ongoing) return;
  const int days_since_first = next_day - tile.planted_day - cd.first_yield_day;
  if (days_since_first < 0) return;
  if (days_since_first % cd.interval != 0) return;
  const int production_count = days_since_first / cd.interval + 1;
  if (production_count > cd.max_yield) return;
  // Fertilizer bonus only applies on watered days (basic needs first).
  const bool fertilized = was_watered && tile.fertilized_until_day >= day;
  tile.yield_units = std::min(cd.max_yield, tile.yield_units + (fertilized ? 2 : 1));
  if (production_count == cd.max_yield) {
    tile.max_lifespan_step = (next_day + 1) * turns_per_day;
  }
}

void RefreshAnimal(Tile& tile, int day) {
  const int next_day = day + 1;
  if (tile.fed_today) {
    tile.consecutive_unfed = 0;
  } else {
    tile.consecutive_unfed += 1;
  }
  if (tile.consecutive_unfed >= 2) {
    // Animal escapes; the bare structure remains.
    tile = MakeBareStructure(kAnimals[tile.animal].structure);
    return;
  }
  const AnimalData& ad = kAnimals[tile.animal];
  const int days_since_first = next_day - tile.placed_day - ad.first_yield_day;
  if (days_since_first >= 0 && days_since_first % ad.interval == 0) {
    // Care bonus only consumed on a fed production day; the bank resets
    // on every production day either way.
    const int bonus = tile.fed_today ? tile.pending_care_bonus : 0;
    tile.yield_units = std::min(ad.max_held, tile.yield_units + 1 + bonus);
    tile.pending_care_bonus = 0;
  }
  if (tile.cared_today && tile.fed_today) tile.pending_care_bonus += 1;
  tile.fertilizer_available = true;
  tile.fed_today = false;
  tile.cared_today = false;
}

}  // namespace kagg::production
