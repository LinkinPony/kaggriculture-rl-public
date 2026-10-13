#include "derived/features.hpp"

#include <algorithm>
#include <limits>

namespace kagg::derived {
namespace {

struct Candidate {
  int cell = -1;
  int delay = std::numeric_limits<int>::max() / 4;
  int operations = 0;
  int64_t purchase = 0;
};

Candidate Placement(const parallel::StateView& state, int seat, int product,
                    const production::FarmGeometry& geometry) {
  Candidate best;
  const Config& config = state.config();
  const Farm& farm = state.farm(seat);
  const auto& priv = state.priv(seat);
  const bool crop = product < kNumCrops;
  const int animal = product - kNumCrops;
  if (product == item::kFertilizer) return best;
  for (size_t cell = 0; cell < farm.tiles.size(); ++cell) {
    const auto& tile = farm.tiles[cell];
    const bool build = tile.kind == TileKind::kEmpty && !crop;
    if (tile.kind != TileKind::kEmpty && !( !crop && tile.kind == TileKind::kStructure &&
        !tile.has_animal && tile.structure == kAnimals[animal].structure)) continue;
    for (size_t unit = 0; unit < geometry.unit_cells.size(); ++unit) {
      const int from = geometry.unit_cells[unit];
      const int direct = production::Distance(from, cell, config.board_size);
      int delay = direct, operations = 1;
      int64_t purchase = 0;
      if (crop) {
        purchase = priv.seeds[product] ? 0 : kCrops[product].seed_cost;
        delay = std::max(delay, purchase > 0 ? 1 : 0);
      } else {
        const int item = item::kGoose + animal;
        const bool carrying = unit < priv.inventories.size() && priv.inventories[unit].Get(item) > 0;
        if (!carrying) {
          purchase = priv.shed[item] > 0 ? 0 : kAnimals[animal].cost;
          delay = std::numeric_limits<int>::max() / 4;
          for (const auto& [x, y] : ShedAccessTiles(config.board_size)) {
            const int access = y * config.board_size + x;
            const int approach = production::Distance(from, access, config.board_size);
            delay = std::min(delay, std::max(approach, purchase > 0 ? 1 : 0) + 1 +
                production::Distance(access, cell, config.board_size));
          }
          ++operations;
        }
        if (build) {
          // A different worker may build while the carrier approaches.
          delay = std::max(delay, geometry.nearest_unit[cell] + 1);
          ++operations;
        }
      }
      if (delay < best.delay) best = {static_cast<int>(cell), delay, operations, purchase};
    }
  }
  return best;
}

}  // namespace

void InvestmentFeatures(const parallel::StateView& state, int seat,
                        const Execution& execution,
                        const std::array<std::array<Timeline, 2>, 2>& scenarios,
                        const std::array<std::array<Settlement, kNumProducts>, 2>& settlement,
                        ProductRows& rows) {
  const Config& config = state.config();
  const int step = state.step_index(), last = config.episode_steps - 2;
  Amounts shed{};
  std::copy_n(state.priv(seat).shed.begin(), kNumProducts, shed.begin());
  for (int product = 0; product < kNumProducts - 1; ++product) {
    const auto candidate = Placement(state, seat, product, execution.geometry[0]);
    if (candidate.cell < 0 || step + candidate.delay > last) continue;
    auto& row = rows[product];
    const int placed = step + candidate.delay;
    const int day = placed / config.turns_per_day;
    const int shed_distance = execution.geometry[0].shed_distance[candidate.cell];
    const bool crop = product < kNumCrops;
    const int animal = product - kNumCrops;
    const int first_day = day + (crop ? kCrops[product].first_yield_day : kAnimals[animal].first_yield_day);
    const int first_sale = Delivery(config, first_day * config.turns_per_day, shed_distance);
    row[48] = 1;
    row[49] = Time(candidate.delay, config);
    row[50] = Time(last - first_sale, config);
    row[51] = Money(candidate.purchase);
    std::array<int, 2> operations{};
    for (int boost = 0; boost < 2; ++boost) {
      const Tile tile = crop ? MakePlant(product, day, config.turns_per_day) : MakeAnimal(animal, day);
      const auto forecast = Forecast(tile, config, placed, shed_distance, boost != 0, true);
      Timeline addition(config.episode_steps - 1);
      addition.Add(forecast);
      operations[boost] = candidate.operations + forecast.operations;
      if (boost == 0) {
        row[53] = Count(forecast.feed);
        row[55] = Count(operations[boost]);
      } else {
        row[54] = Count(forecast.fertilizer);
        row[56] = Count(operations[1] - operations[0]);
      }
      std::vector<double> own(last + 1, -static_cast<double>(candidate.purchase));
      std::vector<double> other(last + 1, 0);
      int first_income = last + 1;
      for (const auto& event : forecast.events) {
        if (!event.input) first_income = std::min(first_income, event.delivery);
      }
      // Only the asset's product, wheat, and fertilizer can differ. Quote each
      // against the same whole-farm baseline, retaining price cannibalization.
      for (int affected = 0; affected < kNumProducts; ++affected) {
        if (affected != product && affected != item::kWheat && affected != item::kFertilizer) continue;
        const auto changed = Settle(state, seat, affected, scenarios[boost], shed,
                                    execution.carried, &addition);
        const auto& base = settlement[boost][affected];
        for (int turn = step; turn <= last; ++turn) {
          own[turn] += changed.cash[0][turn] - base.cash[0][turn];
          other[turn] += changed.cash[1][turn] - base.cash[1][turn];
        }
      }
      row[57 + boost] = Money(own[last]);
      row[boost == 0 ? 52 : 63] = Money(own[last] - other[last]);
      for (int turn = std::max(step, first_income); turn <= last; ++turn) {
        if (own[turn] >= 0) {
          row[59 + boost] = Time(turn - step, config);
          row[61 + boost] = 1;
          break;
        }
      }
    }
  }
}

}  // namespace kagg::derived
