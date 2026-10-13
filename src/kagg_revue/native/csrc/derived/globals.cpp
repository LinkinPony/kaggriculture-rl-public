#include "derived/features.hpp"

#include <algorithm>

#include "market_phase.hpp"

namespace kagg::derived {
namespace {

int NewHandCell(const Config& config, const production::FarmGeometry& geometry) {
  const auto access = ShedAccessTiles(config.board_size);
  int best = -1, occupied = 1000000;
  for (const auto& [x, y] : access) {
    const int cell = y * config.board_size + x;
    const int count = std::count(geometry.unit_cells.begin(), geometry.unit_cells.end(), cell);
    if (count < occupied) { best = cell; occupied = count; }
  }
  return best;
}

}  // namespace

std::array<double, kGlobalFeatures> GlobalFeatures(
    const parallel::StateView& state, int seat, const Execution& execution,
    const std::array<Timeline, 2>& baseline) {
  std::array<double, kGlobalFeatures> row{};
  const auto& config = state.config();
  const auto& farm = state.farm(seat);
  const auto& priv = state.priv(seat);
  const auto& geometry = execution.geometry[0];
  const int step = state.step_index(), last = config.episode_steps - 2;
  const int end = std::min(last, (step / config.turns_per_day + 1) * config.turns_per_day - 1);
  const int left = std::max(0, end - step + 1), workers = geometry.unit_cells.size();
  const auto horizons = Horizons(config, step);
  for (int i = 0; i < kHorizons; ++i) row[i] = Time(std::max(0, horizons[i] - step + 1), config);
  const int critical = execution.critical[0] + execution.travel[0];
  row[6] = Count(critical);
  row[7] = critical / static_cast<double>(std::max(1, left * workers));
  const int64_t reserve = baseline[0].Sum(item::kWheat, step,
      std::min(last, step + 2 * config.turns_per_day - 1), true);
  const int64_t shortage = std::max<int64_t>(0, reserve - priv.shed[item::kWheat] -
      execution.carried[item::kWheat]);
  const double feed_cash = Buy(config, item::kWheat, state.market().inventory[item::kWheat], shortage);
  row[8] = Money(feed_cash);
  row[9] = Money(farm.money - feed_cash);
  double liquidation = 0, overflow = 0;
  for (int product = 0; product < kNumProducts; ++product) {
    const int64_t held = priv.shed[product] + execution.carried[product];
    const int64_t inventory = state.market().inventory[product];
    liquidation += Sell(config, product, inventory, held + baseline[0].initial_ready[product]);
    overflow += Sell(config, product, inventory, held) -
        Sell(config, product, inventory, held - execution.overflow[product]);
  }
  row[10] = Money(liquidation);
  row[11] = Money(overflow);
  row[12] = Count(execution.unreachable[0]);
  row[13] = Count(execution.critical[1] + execution.travel[1]);
  int reusable = 0;
  for (const auto& tile : farm.tiles) reusable += tile.kind == TileKind::kStructure && !tile.has_animal;
  row[16] = Count(reusable);
  if (farm.extra_unlocked < static_cast<int>(kLandOrder.size())) {
    row[14] = 1;
    const int quadrant = kLandOrder[farm.extra_unlocked];
    int cells = 0, delay = 2 * config.board_size;
    for (int cell = 0; cell < config.board_size * config.board_size; ++cell) {
      if (farm.tiles[cell].kind != TileKind::kLocked ||
          QuadrantOf(cell % config.board_size, cell / config.board_size, config.board_size) != quadrant) continue;
      ++cells;
      delay = std::min(delay, std::max(1, geometry.nearest_unit[cell]));
    }
    const double cost = kLandPrices[farm.extra_unlocked];
    row[15] = Count(cells);
    row[17] = Money(cost / std::max(1, cells));
    row[18] = Money(std::max(0.0, cost - (farm.money - feed_cash)));
    row[19] = Time(delay, config);
    row[20] = Count(std::min(cells, workers * std::max(0, left - 1) / 2));
  }
  const int remaining = std::max(0, last - step);
  row[21] = Money(ComputeHirePrice(config, farm.hires_today) / std::max(1, remaining));
  const int spawn = NewHandCell(config, geometry);
  int exclusive = 0;
  for (size_t cell = 0; cell < farm.tiles.size(); ++cell) {
    if (!CriticalTasks(farm.tiles[cell], step, config)) continue;
    const int deadline = TaskDeadline(farm.tiles[cell], step, config);
    const int distance = production::Distance(spawn, cell, config.board_size);
    exclusive += step + 1 + distance <= deadline && step + geometry.nearest_unit[cell] > deadline;
  }
  row[22] = Count(exclusive);
  row[23] = std::max(0, left - 1) / static_cast<double>(config.turns_per_day);
  return row;
}

}  // namespace kagg::derived
