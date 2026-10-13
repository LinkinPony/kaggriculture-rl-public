#include "production/ledger.hpp"

#include <algorithm>

#include "production/features.hpp"

namespace kagg::production {
namespace {

// Units a visible yield drop attributes to harvesting after the processed step.
int HarvestedUnits(const Tile& before, const Tile& after, int processed, int turns_per_day) {
  if (!Productive(before) || before.yield_units <= 0 ||
      !Harvestable(before, processed / turns_per_day)) {
    return 0;
  }
  int drop = 0;
  if (Productive(after) && after.kind == before.kind && Product(after) == Product(before)) {
    drop = before.yield_units - after.yield_units;
  } else if (after.kind == TileKind::kEmpty && before.kind == TileKind::kPlant &&
             !kCrops[before.crop].ongoing) {
    drop = before.yield_units;  // single-harvest crops leave the tile
  }
  // Weeds and empty animal structures lose their yield without a harvest.
  if (before.kind == TileKind::kPlant && before.max_lifespan_step >= 0 &&
      processed >= before.max_lifespan_step && (processed - before.max_lifespan_step) % 2 == 0) {
    drop -= 1;  // decay tick of the processed step
  }
  return std::max(0, drop);
}

int64_t TownConsumption(const Config& config, const std::vector<int>& shops, int product,
                        int processed) {
  int64_t units = 0;
  if (processed % config.shop_sell_interval == 0) {
    for (int shop : shops) {
      const auto& rule = kShops[shop];
      for (int i = 0; i < rule.n_products; ++i) {
        if (rule.products[i] == product) units += rule.n_products == 1 ? 2 : 1;
      }
    }
  }
  if (product != item::kFertilizer && processed % config.center_sell_interval == 0) units += 1;
  return units;
}

}  // namespace

void Ledger::Record(const parallel::StateView& state) {
  const auto& config = state.config();
  const int area = config.board_size * config.board_size;
  const int step = state.step_index();
  if (step == step_) return;  // re-observing the same turn changes nothing
  if (step != step_ + 1 || tiles_.size() != static_cast<size_t>(2 * area)) {
    harvested = {};
    net_market_flow = {};
  } else {
    for (int player = 0; player < 2; ++player) {
      const auto& farm = state.farm(player);
      for (int cell = 0; cell < area; ++cell) {
        const Tile& before = tiles_[player * area + cell];
        const int units = HarvestedUnits(before, farm.tiles[cell], step_, config.turns_per_day);
        if (units > 0) harvested[player][Product(before)] += units;
      }
    }
    for (int product = 0; product < kNumProducts; ++product) {
      // The town always removes its full demand, so the residual is player flow.
      const int64_t town = TownConsumption(config, shops_, product, step_);
      net_market_flow[product] += state.market().inventory[product] - inventory_[product] + town;
    }
  }
  step_ = step;
  tiles_.resize(2 * area);
  for (int player = 0; player < 2; ++player) {
    std::copy_n(state.farm(player).tiles.begin(), area, tiles_.begin() + player * area);
  }
  inventory_ = state.market().inventory;
  shops_ = state.town_shops();
}

}  // namespace kagg::production
