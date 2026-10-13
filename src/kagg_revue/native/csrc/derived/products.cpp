#include "derived/features.hpp"

#include <algorithm>
#include <cmath>

#include "market_phase.hpp"
#include "parallel/observation.hpp"
#include "production/features.hpp"

namespace kagg::derived {
namespace {

// Unknown shop identities are independent uniform draws with replacement.
// Only the published schedule and distribution enter these moments.
std::array<double, 2> FutureDrain(const parallel::StateView& state, int product, int last) {
  const auto& config = state.config();
  double mean = 0, square = 0;
  for (const auto& shop : kShops) {
    int weight = 0;
    for (int i = 0; i < shop.n_products; ++i) {
      if (shop.products[i] == product) weight += shop.n_products == 1 ? 2 : 1;
    }
    mean += weight / static_cast<double>(kNumShops);
    square += weight * weight / static_cast<double>(kNumShops);
  }
  const int interval = config.shop_unlock_interval * config.turns_per_day;
  const int next = (state.step_index() / interval + 1) * interval;
  double total = 0, variance = 0;
  for (int index = state.town_shops().size(), turn = next;
       index < kMaxShopInstances && turn <= last; ++index, turn += interval) {
    const double ticks = Ticks(turn, last, config.shop_sell_interval);
    total += ticks * mean;
    variance += ticks * ticks * (square - mean * mean);
  }
  return {total, std::sqrt(std::max(0.0, variance))};
}

void Liquidity(const parallel::StateView& state, int seat, int product,
               const Execution& execution, const Timeline& baseline, double* row) {
  const auto& config = state.config();
  const auto& priv = state.priv(seat);
  const auto& farm = state.farm(seat);
  const auto& geometry = execution.geometry[0];
  const int step = state.step_index();
  const int64_t inventory = state.market().inventory[product];
  const int64_t shed = priv.shed[product], carried = execution.carried[product];
  row[72] = Money(Sell(config, product, inventory, shed));
  row[73] = Money(Sell(config, product, inventory, shed + carried) -
                  Sell(config, product, inventory, shed));
  if (carried > 0) {
    int arrival = (step / config.turns_per_day + 1) * config.turns_per_day;
    for (size_t unit = 0; unit < geometry.unit_cells.size(); ++unit) {
      if (priv.inventories[unit].Get(product) > 0) {
        arrival = std::min(arrival, step + geometry.shed_distance[geometry.unit_cells[unit]]);
      }
    }
    row[74] = Time(arrival - step, config);
  }
  if (product < kNumCrops) {
    int planters = 0;
    for (int cell : geometry.unit_cells) planters += farm.tiles[cell].kind == TileKind::kEmpty;
    row[75] = Count(std::max<int64_t>(0, planters - priv.seeds[product]));
  }
  row[76] = Count(execution.overflow[product]);
  const int64_t reserve = product == item::kWheat ? baseline.Sum(
      product, step, std::min(config.episode_steps - 2, step + 2 * config.turns_per_day - 1), true) : 0;
  row[77] = Count(reserve);
  row[78] = Count(shed + carried - reserve);
  int harvests = 0;
  for (const auto& tile : farm.tiles) {
    if (product == item::kFertilizer) harvests += tile.has_animal && tile.fertilizer_available;
    else harvests += production::Harvestable(tile, step / config.turns_per_day) &&
        production::Product(tile) == product;
  }
  row[79] = Count(harvests);
}

}  // namespace

void ProductFeatures(const parallel::StateView& state, int seat,
                     const parallel::PublicHistory& history, const Execution& execution,
                     const std::array<std::array<Timeline, 2>, 2>& scenarios,
                     const std::array<std::array<Settlement, kNumProducts>, 2>& settlement,
                     ProductRows& rows) {
  const auto& config = state.config();
  const int step = state.step_index(), last = config.episode_steps - 2;
  const auto horizons = Horizons(config, step);
  const auto& current = history.Previous(state, 0);
  for (int product = 0; product < kNumProducts; ++product) {
    auto& row = rows[product];
    const double base = config.market_params[product].base;
    for (int index = 0; index < kHorizons; ++index) {
      const int end = horizons[index], start = index * 8;
      const int64_t drain = Drain(config, state.town_shops(), product, step, end);
      row[start] = Count(drain);
      std::array<std::array<int64_t, 2>, 2> net{};
      for (int boost = 0; boost < 2; ++boost) {
        for (int side = 0; side < 2; ++side) {
          const auto& forecast = scenarios[boost][side];
          net[boost][side] = std::max<int64_t>(0, forecast.Sum(product, step, end) -
              forecast.initial_ready[product]) - forecast.Sum(product, step, end, true);
          row[start + 1 + boost * 2 + side] = Count(net[boost][side]);
        }
        row[start + 6 + boost] = ComputeMarketPrice(
            config, product, settlement[boost][product].inventory[end]) / base;
      }
      const int64_t visible = state.priv(seat).shed[product] + execution.carried[product] +
          scenarios[0][0].initial_ready[product] + scenarios[0][1].initial_ready[product];
      row[start + 5] = Count(drain - visible - net[0][0] - net[0][1]);
    }
    row[64] = Count(current.unlock_delta[product] *
        static_cast<double>(config.turns_per_day) / config.shop_sell_interval);
    if (current.last_unlock_step >= 0) row[65] = Time(step - current.last_unlock_step, config);
    const auto eight = FutureDrain(state, product, std::min(last, step + 8 * config.turns_per_day - 1));
    const auto remaining = FutureDrain(state, product, last);
    row[66] = Count(eight[0]);
    row[67] = Count(eight[1]);
    row[68] = Count(remaining[0]);
    row[69] = Count(remaining[1]);
    const int interval = config.shop_unlock_interval * config.turns_per_day;
    const int next = (step / interval + 1) * interval;
    const double first_sale = last - row[50] * std::max(1, config.episode_steps - 1);
    row[70] = row[48] && state.town_shops().size() < kMaxShopInstances &&
        next <= last && next <= first_sale;
    for (const auto& shop : kShops) {
      for (int i = 0; i < shop.n_products; ++i) {
        if (shop.products[i] == product) row[71] += 1.0 / kNumShops;
      }
    }
    Liquidity(state, seat, product, execution, scenarios[0][0], row.data());
    for (int window = 0; window < 2; ++window) {
      const int lookback = (window == 0 ? 2 : 4) * config.turns_per_day;
      const auto& old = history.Previous(state, lookback);
      const int at = 80 + window * 8;
      row[at] = Count(current.harvested[seat][product] - old.harvested[seat][product]);
      row[at + 1] = Count(current.harvested[1 - seat][product] - old.harvested[1 - seat][product]);
      row[at + 2] = Count(current.market_flow[product] - old.market_flow[product]);
      row[at + 3] = (current.prices[product] - old.prices[product]) / base;
      row[at + 4] = std::min(step, lookback) / static_cast<double>(lookback);
      row[at + 5] = current.floor_ticks[product] > old.floor_ticks[product];
      row[at + 6] = current.ambiguous_ticks[product] > old.ambiguous_ticks[product];
      row[at + 7] = Count(current.producers[seat][product] - current.producers[1 - seat][product] -
          old.producers[seat][product] + old.producers[1 - seat][product]);
    }
  }
}

}  // namespace kagg::derived
