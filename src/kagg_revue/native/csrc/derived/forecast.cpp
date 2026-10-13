#include "derived/features.hpp"

#include <algorithm>
#include <cmath>

#include "production/features.hpp"
#include "production/pricing.hpp"
#include "production/rules.hpp"

namespace kagg::derived {

double Count(double value) {
  return std::copysign(std::log1p(std::abs(value)) / std::log(1025.0), value);
}

double Money(double value) {
  return std::copysign(std::log1p(std::abs(value) / 100.0) / std::log(1001.0), value);
}

double Time(double value, const Config& config) {
  return value / std::max(1, config.episode_steps - 1);
}

int FeatureCount(int board, int units) {
  return kGlobalFeatures + 2 * board * board * kBoardFeatures +
      2 * units * kUnitFeatures + kNumProducts * kProductFeatures;
}

std::array<int, kHorizons> Horizons(const Config& config, int step) {
  std::array<int, kHorizons> result{};
  constexpr std::array<int, 5> days = {1, 2, 4, 8, 12};
  for (int index = 0; index < 5; ++index) {
    result[index] = std::min(config.episode_steps - 2, step + days[index] * config.turns_per_day - 1);
  }
  result.back() = config.episode_steps - 2;
  return result;
}

int64_t Ticks(int first, int last, int interval) {
  if (last < first) return 0;
  return last / interval - (first == 0 ? -1 : (first - 1) / interval);
}

int64_t Drain(const Config& config, const std::vector<int>& shops, int product,
              int first, int last) {
  return production::ShopDemand(shops, product) * Ticks(first, last, config.shop_sell_interval) +
      (product != item::kFertilizer ? Ticks(first, last, config.center_sell_interval) : 0);
}

int Delivery(const Config& config, int harvest_step, int shed_distance) {
  // HARVEST then d moves then DROP; DROP and SELL share a turn. Night drop is
  // after the market and first becomes sellable on the following turn.
  const int walking = harvest_step + shed_distance + 1;
  const int night = (harvest_step / config.turns_per_day + 1) * config.turns_per_day;
  return std::min(walking, night);
}

TileForecast Forecast(Tile tile, const Config& config, int step, int distance_to_shed,
                      bool boosted, bool peak, int intervention, bool apply_intervention) {
  TileForecast result;
  result.events.reserve(128);
  const int last = config.episode_steps - 2;
  if (step > last || !production::Productive(tile)) return result;
  const int first_day = step / config.turns_per_day;
  const auto add = [&](int now, int product, int64_t amount, bool input) {
    if (amount > 0) result.events.push_back(
        {now, input ? now : Delivery(config, now, distance_to_shed), product, amount, input});
  };
  for (int day = first_day; day <= last / config.turns_per_day; ++day) {
    if (!production::Productive(tile)) break;
    const int now = std::max(step, day * config.turns_per_day);
    const bool plant = tile.kind == TileKind::kPlant;
    const auto selected = [&](int action, bool baseline) {
      return day == first_day && intervention == action ? apply_intervention : baseline;
    };
    if (plant) {
      const bool fertilize = selected(3, boosted && tile.fertilized_until_day < day);
      if (fertilize && tile.fertilized_until_day < day + 2) {
        production::Fertilize(tile, day);
        add(now, item::kFertilizer, 1, true);
        ++result.fertilizer;
        ++result.operations;
      }
      if (!tile.watered_today && selected(0, true)) {
        production::Water(tile, day);
        ++result.operations;
      }
    } else {
      if (!tile.fed_today && selected(1, true)) {
        tile.fed_today = true;
        add(now, item::kWheat, 1, true);
        ++result.feed;
        ++result.operations;
      }
      if (!tile.cared_today && selected(2, boosted)) {
        tile.cared_today = true;
        ++result.operations;
      }
      if (tile.fertilizer_available) {
        add(now, item::kFertilizer, 1, false);
        tile.fertilizer_available = false;
        ++result.operations;
      }
    }
    const bool oneoff = plant && !kCrops[tile.crop].ongoing;
    const bool final_delivery_day =
        Delivery(config, (day + 1) * config.turns_per_day, distance_to_shed) > last;
    const bool collect = !oneoff || !peak || tile.yield_units >= kCrops[tile.crop].max_yield ||
        day - tile.planted_day >= kCrops[tile.crop].max_yield_day || final_delivery_day;
    if (collect && production::Harvestable(tile, day)) {
      add(now, production::Product(tile), tile.yield_units, false);
      ++result.operations;
      tile.yield_units = 0;
      if (oneoff) break;
    }
    const int end = (day + 1) * config.turns_per_day - 1;
    if (plant && tile.max_lifespan_step >= 0) {
      int first_decay = std::max(now, tile.max_lifespan_step);
      first_decay += (first_decay - tile.max_lifespan_step) % 2;
      const int last_decay = std::min(end, last);
      if (first_decay <= last_decay) {
        tile.yield_units -= 1 + (last_decay - first_decay) / 2;
        if (tile.yield_units <= 0) break;
      }
    }
    if (end > last) break;
    if (plant) production::RefreshPlant(tile, day, config.turns_per_day);
    else production::RefreshAnimal(tile, day);
  }
  return result;
}

void Timeline::Add(const TileForecast& forecast) {
  operations += forecast.operations;
  for (const auto& event : forecast.events) {
    if (event.step >= 0 && event.step < static_cast<int>(harvest.size())) {
      (event.input ? input : harvest)[event.step][event.product] += event.amount;
    }
    if (!event.input && event.delivery >= 0 && event.delivery < static_cast<int>(delivered.size())) {
      delivered[event.delivery][event.product] += event.amount;
    }
  }
}

int64_t Timeline::Sum(int product, int first, int last, bool consumption) const {
  const auto& rows = consumption ? input : harvest;
  int64_t value = 0;
  for (int turn = std::max(0, first); turn <= last && turn < static_cast<int>(rows.size()); ++turn) {
    value += rows[turn][product];
  }
  return value;
}

Timeline FarmForecast(const Config& config, const Farm& farm,
                      const production::FarmGeometry& geometry, int step, bool boosted) {
  Timeline result(config.episode_steps - 1);
  const int day = step / config.turns_per_day;
  for (size_t cell = 0; cell < farm.tiles.size(); ++cell) {
    const Tile& tile = farm.tiles[cell];
    if (!production::Productive(tile)) continue;
    if (production::Harvestable(tile, day)) {
      result.initial_ready[production::Product(tile)] += tile.yield_units;
    }
    if (tile.has_animal && tile.fertilizer_available) ++result.initial_ready[item::kFertilizer];
    result.Add(Forecast(tile, config, step, geometry.shed_distance[cell], boosted));
  }
  return result;
}

}  // namespace kagg::derived
