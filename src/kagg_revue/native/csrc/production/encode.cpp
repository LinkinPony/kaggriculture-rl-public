// Assembles the v4 agronomy block: tile forecasts, geometry, products, labor and units.
#include <algorithm>
#include <cmath>
#include <vector>

#include "half.hpp"
#include "production/features.hpp"
#include "production/geometry.hpp"
#include "production/ledger.hpp"
#include "production/products.hpp"

namespace kagg::production {
namespace {

double Log(double value) { return std::log1p(std::max(0.0, value)) / 5.0; }

// Per-farm labor demand versus the unit-turns left before the day (or season) ends.
struct Labor {
  int due = 0;
  int dying = 0;
  int units = 0;
  double travel = 0;
};

void WriteLabor(const Labor& labor, int area, int turns_left, double* output) {
  const int unit_turns = labor.units * turns_left;
  output[0] = labor.due / static_cast<double>(area);
  output[1] = labor.dying / static_cast<double>(area);
  output[2] = std::log1p(unit_turns) / 7.0;
  output[3] = std::min(labor.due / static_cast<double>(std::max(1, unit_turns)), 2.0) / 2.0;
  output[4] = std::log1p(labor.travel) / 8.0;
}

void Accumulate(const Tile& tile, const TileContext& context, int side, int day,
                std::array<double, kProductFeatures>& row) {
  namespace f = production::product;
  namespace t = production::tile;
  const bool plant = tile.kind == TileKind::kPlant;
  const int first = plant ? tile.planted_day + kCrops[tile.crop].first_yield_day
                          : tile.placed_day + kAnimals[tile.animal].first_yield_day;
  const bool exhausted = plant && kCrops[tile.crop].ongoing && day >= first &&
      context.next_production_step < 0;
  const int stock = Harvestable(tile, day) ? tile.yield_units : 0;
  if (side == 0) {
    row[f::kOwnImmatureTiles] += day < first;
    row[f::kOwnHarvestableTiles] += context.values[t::kHarvestable];
    row[f::kOwnExhaustedOngoingTiles] += exhausted;
    row[f::kOwnDayEndIdleLossTiles] += context.values[t::kDayEndIdleLoss];
    row[f::kOwnNeedsWater] += plant && !tile.watered_today;
    row[f::kOwnNeedsFeed] += !plant && !tile.fed_today;
    row[f::kOwnUsefulCareAvailable] +=
        !plant && !tile.cared_today && context.values[t::kNewCareCanPayBeforeEnd] > 0;
    row[f::kOwnFertilizerCollectable] += !plant && tile.fertilizer_available;
    row[f::kOwnHarvestableQuantity] += stock;
    row[f::kOwnRemainingProductionEvents] += context.values[t::kRemainingProductionEvents] * 30;
    for (int i = 0; i < 3; ++i) row[f::kOwnAdditionalHarvest1Day + i] += context.harvest[i];
    row[f::kOwnNextProductionOverflow] +=
        context.values[t::kNextProductionOverflowWithoutHarvest] * 6;
  } else {
    row[f::kOpponentImmatureTiles] += day < first;
    row[f::kOpponentHarvestableTiles] += context.values[t::kHarvestable];
    row[f::kOpponentExhaustedOngoingTiles] += exhausted;
    row[f::kOpponentHarvestableQuantity] += stock;
    for (int i = 0; i < 3; ++i) row[f::kOpponentAdditionalHarvest1Day + i] += context.harvest[i];
  }
}

}  // namespace

int FeatureCount(int board_size, int units) {
  return 2 * board_size * board_size * kBoardFeatures + kNumProducts * kProductFeatures +
      kGlobalFeatures + 2 * units * kUnitFeatures;
}

void Encode(const parallel::StateView& state, int seat, const Ledger& ledger, int units,
            uint16_t* output) {
  namespace g = production::global;
  const auto& config = state.config();
  const int board = config.board_size, area = board * board;
  const int step = state.step_index(), day = step / config.turns_per_day;
  const int last_step = config.episode_steps - 2;
  const int turns_left =
      std::min((day + 1) * config.turns_per_day, config.episode_steps - 1) - step;
  // Scratch belongs to an encoder thread, never to a game or a player. Reuse
  // capacity while resetting every feature on each call.
  thread_local std::vector<double> boards, unit_rows;
  boards.assign(2 * area * kBoardFeatures, 0.0);
  unit_rows.assign(2 * units * kUnitFeatures, 0.0);
  std::array<double, kGlobalFeatures> globals{};
  ProductRows products{};
  Holdings holdings;
  // Never inspect the other seat's private state, even in native self-play.
  const auto& priv = state.priv(seat);
  for (const auto& inventory : priv.inventories) {
    for (const auto& [item, count] : inventory.items) holdings.carried[item] += count;
  }
  std::array<Labor, 2> labor{};
  for (int side = 0; side < 2; ++side) {
    const auto& farm = state.farm(side == 0 ? seat : 1 - seat);
    const auto geometry = ComputeGeometry(config, farm, day);
    double* rows = boards.data() + static_cast<size_t>(side) * area * kBoardFeatures;
    EncodeGeometry(config, farm, side == 0 ? &priv : nullptr, geometry, step, rows);
    EncodeUnits(geometry, units, unit_rows.data() + static_cast<size_t>(side) * units * kUnitFeatures);
    labor[side].units = std::min<int>(units, geometry.unit_cells.size());
    for (int cell = 0; cell < area; ++cell) {
      const Tile& tile = farm.tiles[cell];
      if (geometry.due[cell].any()) {
        labor[side].due += 1;
        labor[side].travel += geometry.nearest_unit[cell];
      }
      if (side == 0) {
        holdings.feed_due += tile.has_animal && !tile.fed_today;
        holdings.empty += tile.kind == TileKind::kEmpty;
        if (tile.kind == TileKind::kStructure && !tile.has_animal) {
          ++holdings.structures[static_cast<int>(tile.structure)];
        }
      }
      if (!Productive(tile)) continue;
      const auto context = Describe(tile, config, step);
      double* row = rows + static_cast<size_t>(cell) * kBoardFeatures;
      std::copy(context.values.begin(), context.values.end(), row);
      labor[side].dying += context.values[tile::kDayEndIdleLoss] > 0;
      const bool harvestable = context.values[tile::kHarvestable] > 0;
      if (harvestable || context.next_production_step >= 0) {
        // Harvest on an earlier day is banked overnight; the final day needs the trip.
        const int ready = harvestable ? step : context.next_production_step;
        const int trip = geometry.nearest_unit[cell] + geometry.shed_distance[cell] + 2;
        row[board::kHarvestSellableBeforeEnd] =
            ready / config.turns_per_day < last_step / config.turns_per_day ||
            ready + trip <= last_step;
      }
      Accumulate(tile, context, side, day, products[Product(tile)]);
      auto& supply = side == 0 ? holdings.own_supply : holdings.opponent_supply;
      supply[Product(tile)] += Harvestable(tile, day) ? tile.yield_units : 0;
    }
  }
  for (int product = 0; product < kNumProducts; ++product) {
    holdings.own_supply[product] += priv.shed[product] + static_cast<int64_t>(holdings.carried[product]);
  }
  FinishProducts(state, seat, ledger, holdings, products);
  const double wheat_carried = holdings.carried[item::kWheat];
  globals[g::kFeedDueToday] = Log(holdings.feed_due);
  globals[g::kWheatTotal] = Log(priv.shed[item::kWheat] + wheat_carried);
  globals[g::kWheatStored] = Log(priv.shed[item::kWheat]);
  globals[g::kWheatCarried] = Log(wheat_carried);
  globals[g::kFeedShortfall] = Log(holdings.feed_due - priv.shed[item::kWheat] - wheat_carried);
  globals[g::kFertilizerStored] = Log(priv.shed[item::kFertilizer]);
  globals[g::kFertilizerCarried] = Log(holdings.carried[item::kFertilizer]);
  globals[g::kTurnsLeftToday] = turns_left / static_cast<double>(config.turns_per_day);
  globals[g::kFinalDay] = day == last_step / config.turns_per_day;
  const double capacity = std::max<int64_t>(1, config.shed_capacity);
  const double stored = ShedTotal(priv);
  double carried = 0;
  for (double count : holdings.carried) carried += count;
  globals[g::kShedRoom] = std::max(0.0, capacity - stored) / capacity;
  globals[g::kCarriedTotal] = carried / capacity;
  globals[g::kShedOverflowTonight] = std::max(0.0, stored + carried - capacity) / capacity;
  WriteLabor(labor[0], area, turns_left, globals.data() + g::kOwnDueTaskTiles);
  WriteLabor(labor[1], area, turns_left, globals.data() + g::kOpponentDueTaskTiles);
  size_t offset = 0;
  const auto emit = [&](const auto& row) {
    half::Pack(row.data(), row.size(), output + offset);
    offset += row.size();
  };
  emit(boards);
  for (const auto& row : products) emit(row);
  emit(globals);
  emit(unit_rows);
}

}  // namespace kagg::production
