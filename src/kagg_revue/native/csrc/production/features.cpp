#include "production/features.hpp"

#include <algorithm>
#include <cmath>

#include "production/rules.hpp"

namespace kagg::production {
namespace {

struct Schedule {
  int first;
  int interval;
  int last;
  int capacity;
};

Schedule Timing(const Tile& tile, const Config& config) {
  const int last_day = (config.episode_steps - 2) / config.turns_per_day;
  if (tile.kind == TileKind::kPlant) {
    const auto& crop = kCrops[tile.crop];
    const int first = tile.planted_day + crop.first_yield_day;
    return {first, crop.interval,
            crop.ongoing ? std::min(last_day, first + (crop.max_yield - 1) * crop.interval)
                         : std::min(last_day, tile.planted_day + crop.max_yield_day),
            crop.max_yield};
  }
  const auto& animal = kAnimals[tile.animal];
  return {tile.placed_day + animal.first_yield_day, animal.interval, last_day, animal.max_held};
}

int Next(const Schedule& schedule, int earliest) {
  if (!schedule.interval) return -1;
  const int offset = std::max(0, earliest - schedule.first);
  const int day = schedule.first +
      ((offset + schedule.interval - 1) / schedule.interval) * schedule.interval;
  return day <= schedule.last ? day : -1;
}

void Maintain(Tile& tile, int day) {
  if (tile.kind == TileKind::kPlant && !tile.watered_today) Water(tile, day);
  if (tile.kind == TileKind::kStructure && tile.has_animal) tile.fed_today = true;
}

void FinishDay(Tile& tile, const Config& config, int first_step, int day) {
  const int end = (day + 1) * config.turns_per_day - 1;
  const int last = std::min(end, config.episode_steps - 2);
  if (tile.kind == TileKind::kPlant && tile.max_lifespan_step >= 0) {
    int first = std::max(first_step, tile.max_lifespan_step);
    first += (first - tile.max_lifespan_step) % 2;
    if (first <= last) {
      // No other rule runs within this forecast interval: Decay removes one
      // unit on alternating turns and replaces the plant at zero.
      tile.yield_units -= 1 + (last - first) / 2;
      if (tile.yield_units <= 0) tile = MakeWeed();
    }
  }
  if (end > config.episode_steps - 2) return;
  if (tile.kind == TileKind::kPlant) RefreshPlant(tile, day, config.turns_per_day);
  else if (tile.kind == TileKind::kStructure && tile.has_animal) RefreshAnimal(tile, day);
}

std::array<double, 3> HarvestForecast(Tile tile, const Config& config, int step) {
  const int day = step / config.turns_per_day;
  const bool oneoff = tile.kind == TileKind::kPlant && !kCrops[tile.crop].ongoing;
  // Existing harvestable stock is reported separately from additional harvest.
  if (Harvestable(tile, day)) {
    if (oneoff) return {};
    tile.yield_units = 0;
  }
  std::array<double, 3> result{};
  double total = 0;
  for (int offset = 0; offset < 4; ++offset) {
    const int current_day = day + offset;
    const int current_step = offset ? current_day * config.turns_per_day : step;
    if (Productive(tile) && current_step <= config.episode_steps - 2) {
      Maintain(tile, current_day);
      // A one-time crop can gain yield and be harvested on the same day.
      if (Harvestable(tile, current_day)) {
        total += tile.yield_units;
        tile.yield_units = 0;
        if (oneoff) tile = Tile{};
      }
      FinishDay(tile, config, current_step, current_day);
      if ((current_day + 1) * config.turns_per_day <= config.episode_steps - 2 &&
          Harvestable(tile, current_day + 1)) {
        total += tile.yield_units;
        tile.yield_units = 0;
        if (oneoff) tile = Tile{};
      }
    }
    if (offset == 0) result[0] = total;
    if (offset == 1) result[1] = total;
    if (offset == 3) result[2] = total;
  }
  return result;
}

}  // namespace

bool Productive(const Tile& tile) {
  return tile.kind == TileKind::kPlant ||
         (tile.kind == TileKind::kStructure && tile.has_animal);
}

bool Harvestable(const Tile& tile, int day) {
  return Productive(tile) && tile.yield_units > 0 &&
         (tile.kind != TileKind::kPlant ||
          day - tile.planted_day >= kCrops[tile.crop].first_yield_day);
}

int Product(const Tile& tile) {
  return tile.kind == TileKind::kPlant ? tile.crop : kAnimals[tile.animal].product;
}

TileContext Describe(const Tile& tile, const Config& config, int step) {
  TileContext context;
  if (!Productive(tile)) return context;
  auto& row = context.values;
  const int day = step / config.turns_per_day;
  const int last_step = config.episode_steps - 2;
  const double horizon = std::max(1, config.episode_steps - 1);
  const bool plant = tile.kind == TileKind::kPlant;
  const auto timing = Timing(tile, config);
  // `next` is always at least a day away, so a zero offset means "no event".
  const int next = Next(timing, day + 1);
  context.next_production_step = next < 0 ? -1 : next * config.turns_per_day;
  row[tile::kHarvestable] = Harvestable(tile, day);
  row[tile::kHarvestableQuantity] =
      row[tile::kHarvestable] ? std::log1p(tile.yield_units) / 5.0 : 0;
  row[tile::kAgeDays] = (day - (plant ? tile.planted_day : tile.placed_day)) / 30.0;
  row[tile::kCapacityRemaining] = std::max(0, timing.capacity - tile.yield_units) / 6.0;
  row[tile::kNextProductionTurns] =
      next < 0 ? 0 : (next * config.turns_per_day - step) / horizon;
  row[tile::kRemainingProductionEvents] =
      next < 0 ? 0 : (1 + (timing.last - next) / timing.interval) / 30.0;
  int decay = tile.max_lifespan_step;
  if (plant && kCrops[tile.crop].ongoing && decay < 0) {
    const auto& crop = kCrops[tile.crop];
    decay = (timing.first + (crop.max_yield - 1) * crop.interval + 1) * config.turns_per_day;
  }
  row[tile::kDecayStartTurns] = decay < 0 ? 0 : std::clamp((decay - step) / horizon, -1.0, 1.0);
  row[tile::kHasDecayDeadline] = decay >= 0;
  if (plant) {
    const auto& crop = kCrops[tile.crop];
    const int age = day - tile.planted_day;
    const int start = (crop.max_yield_day + 1) / 2;
    const bool window = !crop.ongoing && start <= age && age <= crop.max_yield_day;
    row[tile::kWateringBonusWindow] = window;
    if (!tile.watered_today) {
      Tile water = tile, fertilizer = tile;
      Water(water, day);
      Fertilize(fertilizer, day);
      Water(fertilizer, day);
      row[tile::kWaterImmediateYieldGain] = (water.yield_units - tile.yield_units) / 6.0;
      row[tile::kFertilizeThenWaterExtraGain] =
          (fertilizer.yield_units - water.yield_units) / 6.0;
    }
    const int end = std::min(crop.max_yield_day, last_step / config.turns_per_day - tile.planted_day);
    row[tile::kRemainingWateringBonusDays] = crop.ongoing ? 0 : std::max(0, end - std::max(start, age) + 1 -
        static_cast<int>(tile.watered_today && window)) / 30.0;
    // Potential incremental fertilizer-covered events, with daily watering.
    for (int d = day; d <= std::min(day + 2, last_step / config.turns_per_day); ++d) {
      if (tile.fertilized_until_day >= d) continue;
      const bool event = crop.ongoing
          ? Next(timing, d + 1) == d + 1
          : (d - tile.planted_day >= start && d - tile.planted_day <= crop.max_yield_day &&
             !(d == day && tile.watered_today));
      row[tile::kNewFertilizerCoveredEvents] += event / 3.0;
    }
  }
  if (next >= 0) {
    const int amount = plant
        ? 1 + static_cast<int>(tile.fertilized_until_day >= next - 1)
        : 1 + tile.pending_care_bonus + static_cast<int>(tile.cared_today && next > day + 1);
    row[tile::kNextMaintainedProduction] = std::min(amount, timing.capacity) / 6.0;
    row[tile::kNextProductionOverflowWithoutHarvest] =
        std::max(0, tile.yield_units + amount - timing.capacity) / 6.0;
  }
  const bool refresh = (day + 1) * config.turns_per_day - 1 <= last_step;
  if (refresh) {
    Tile idle = tile, maintained = tile;
    Maintain(maintained, day);
    FinishDay(idle, config, step, day);
    FinishDay(maintained, config, step, day);
    row[tile::kDayEndIdleYieldDelta] = (idle.yield_units - tile.yield_units) / 6.0;
    row[tile::kDayEndMaintainedYieldDelta] = (maintained.yield_units - tile.yield_units) / 6.0;
    row[tile::kDayEndIdleLoss] = !Productive(idle);
    row[tile::kMaintenancePreventsDayEndLoss] = !Productive(idle) && Productive(maintained);
    if (!plant && next == day + 1 && !tile.fed_today) {
      row[tile::kFeedingPreservesBankedBonus] = tile.pending_care_bonus / 6.0;
    }
  }
  if (!plant && !tile.cared_today) {
    // Today's care is banked AFTER tonight's production has consumed old bonuses.
    const int payout = Next(timing, day + 2);
    row[tile::kNewCarePayoutTurns] =
        payout < 0 ? 0 : (payout * config.turns_per_day - step) / horizon;
    row[tile::kNewCareCanPayBeforeEnd] = payout >= 0;
  }
  row[tile::kFirstHarvestTerminalSlack] = std::clamp(
      (last_step - std::max(step, timing.first * config.turns_per_day)) / horizon, -1.0, 1.0);
  context.harvest = HarvestForecast(tile, config, step);
  return context;
}

}  // namespace kagg::production
