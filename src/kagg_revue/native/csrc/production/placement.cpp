#include "production/placement.hpp"

#include "production/rules.hpp"

namespace kagg::production {
namespace {

double CropTotal(int crop, const Config& config, int day, int last_day, bool boosted) {
  const auto& rule = kCrops[crop];
  Tile tile = MakePlant(crop, day, config.turns_per_day);
  double total = 0;
  for (int d = day; d <= last_day; ++d) {
    if (boosted && tile.fertilized_until_day < d) Fertilize(tile, d);
    Water(tile, d);
    const int age = d - tile.planted_day;
    if (age >= rule.first_yield_day && tile.yield_units > 0) {
      // Single-harvest crops wait for the bonus window unless the season ends first.
      if (rule.ongoing || tile.yield_units >= rule.max_yield || age >= rule.max_yield_day ||
          d == last_day) {
        total += tile.yield_units;
        if (!rule.ongoing) break;
        tile.yield_units = 0;
      }
    }
    if (d == last_day) break;
    RefreshPlant(tile, d, config.turns_per_day);
    if (tile.kind != TileKind::kPlant) break;
  }
  return total;
}

double AnimalTotal(int animal, int day, int last_day, bool boosted) {
  Tile tile = MakeAnimal(animal, day);
  double total = 0;
  for (int d = day; d <= last_day; ++d) {
    total += tile.yield_units;  // collected each morning it appears
    tile.yield_units = 0;
    if (d == last_day) break;
    tile.fed_today = true;
    tile.cared_today = boosted;
    RefreshAnimal(tile, d);
  }
  return total;
}

}  // namespace

double PlacementTotal(int product, const Config& config, int step, bool boosted) {
  const int day = step / config.turns_per_day;
  const int last_day = (config.episode_steps - 2) / config.turns_per_day;
  struct Cache {
    int day = -1, last_day = -1, turns = -1;
    std::array<std::array<double, 2>, kNumProducts> totals;
  };
  thread_local Cache cache;
  if (cache.day != day || cache.last_day != last_day || cache.turns != config.turns_per_day) {
    cache.day = day;
    cache.last_day = last_day;
    cache.turns = config.turns_per_day;
    for (auto& row : cache.totals) row.fill(-1);
  }
  double& total = cache.totals[product][boosted];
  if (total >= 0) return total;
  if (product < kNumCrops) {
    return total = CropTotal(product, config, day, last_day, boosted);
  }
  for (int animal = 0; animal < kNumAnimals; ++animal) {
    if (kAnimals[animal].product == product) {
      return total = AnimalTotal(animal, day, last_day, boosted);
    }
  }
  return total = 0;
}

}  // namespace kagg::production
