#include "parallel/observation.hpp"

#include <algorithm>
#include <cmath>
#include <stdexcept>

#include "actor_encoding.hpp"
#include "action_codec.hpp"
#include "unit_phase.hpp"
#include "half.hpp"
#include "market_phase.hpp"
#include "production/features.hpp"
#include "production/pricing.hpp"

namespace kagg::parallel {
namespace {

double Symlog(double value) {
  return std::copysign(std::log1p(std::abs(value)), value);
}

}  // namespace

void EncodeUnitSupport(const StateView& state, int seat, int units, uint16_t* output) {
  auto* values = reinterpret_cast<_Float16*>(output);
  std::fill(values, values + units * kUnitSupportFeatures, _Float16{0});
  const int count = 1 + state.farm(seat).hands.size();
  if (count > units) throw std::runtime_error("unit support capacity exceeded");
  const int day = state.step_index() / state.config().turns_per_day;
  for (int unit = 0; unit < count; ++unit) {
    for (int token = 0; token < kUnitSupportFeatures; ++token) {
      values[unit * kUnitSupportFeatures + token] = WouldApplyUnitAction(
          state.config(), state.farm(seat), state.priv(seat), unit,
          policy::DecodeUnitToken(token, 1), day) ? _Float16{1} : _Float16{0};
    }
  }
}

void PublicHistory::Record(const StateView& engine) {
  const int step = engine.step_index();
  if (step == recorded_step_) return;
  const bool contiguous = step == recorded_step_ + 1 && recorded_step_ >= 0;
  const PublicSnapshot previous = contiguous ?
      snapshots_[recorded_step_ % snapshots_.size()] : PublicSnapshot{};
  auto& snapshot = snapshots_[engine.step_index() % snapshots_.size()];
  snapshot = PublicSnapshot{};
  snapshot.last_unlock_step = previous.last_unlock_step;
  snapshot.unlock_delta = previous.unlock_delta;
  for (int product = 0; product < kNumProducts; ++product) {
    snapshot.prices[product] = engine.market().prices[product];
    snapshot.inventory[product] = engine.market().inventory[product];
    snapshot.shop_weight[product] = production::ShopDemand(engine.town_shops(), product);
    snapshot.floor_ticks[product] = previous.floor_ticks[product];
    snapshot.ambiguous_ticks[product] = previous.ambiguous_ticks[product];
    if (contiguous) {
      const auto& config = engine.config();
      const int processed = step - 1;
      const int town = (processed % config.shop_sell_interval == 0 ? previous.shop_weight[product] : 0) +
          (product != item::kFertilizer && processed % config.center_sell_interval == 0);
      snapshot.floor_ticks[product] += ComputeMarketPrice(
          config, product, engine.market().inventory[product] + town) == 1;
      // A production/refresh boundary can conceal a simultaneous visible harvest.
      snapshot.ambiguous_ticks[product] += step % config.turns_per_day == 0 &&
          previous.producers[0][product] + previous.producers[1][product] > 0;
    }
  }
  if (snapshot.shop_weight != previous.shop_weight) {
    snapshot.last_unlock_step = step;
    for (int product = 0; product < kNumProducts; ++product) {
      snapshot.unlock_delta[product] = snapshot.shop_weight[product] - previous.shop_weight[product];
    }
  }
  for (int seat = 0; seat < 2; ++seat) {
    snapshot.cash[seat] = engine.farm(seat).money;
    snapshot.hands[seat] = engine.farm(seat).hands.size();
    snapshot.land[seat] = engine.farm(seat).extra_unlocked;
    for (const auto& tile : engine.farm(seat).tiles) {
      if (!production::Productive(tile)) continue;
      const int product = production::Product(tile);
      snapshot.producers[seat][product] += 1;
      if (tile.max_lifespan_step >= 0 && step > tile.max_lifespan_step) {
        snapshot.ambiguous_ticks[product] += 1;
      }
    }
  }
  ledger_.Record(engine);
  snapshot.harvested = ledger_.harvested;
  snapshot.market_flow = ledger_.net_market_flow;
  recorded_step_ = step;
}

const PublicSnapshot& PublicHistory::Previous(const StateView& engine, int lookback) const {
  return snapshots_[std::max(0, engine.step_index() - lookback) % snapshots_.size()];
}

void EncodeObservation(const StateView& engine, int seat, int units, uint16_t* row) {
    const auto& config = engine.config();
    if (engine.farm(seat).hands.size() >= static_cast<size_t>(units)) {
      throw std::runtime_error("unit capacity exceeded; increase profile unit_limit");
    }
    const int board = actor::kBoardChannels * config.board_size * config.board_size;
    for (int player = 0; player < 2; ++player) {
      actor::EncodeBoardHalf(config, engine.farm(player == 0 ? seat : 1 - seat),
                             engine.step_index(), row + player * board);
    }
    actor::EncodeUnitsHalf(config, engine.farm(seat), &engine.priv(seat),
                           engine.step_index(), units, row + 2 * board, row);
    actor::SeatView view;
    view.config = &config;
    view.step = engine.step_index();
    view.own_farm = &engine.farm(seat);
    view.opponent_farm = &engine.farm(1 - seat);
    view.own_private = &engine.priv(seat);
    view.market_inventory = engine.market().inventory;
    view.market_prices = engine.market().prices;
    for (int shop : engine.town_shops()) ++view.shop_counts[shop];
    float global[actor::kGlobalFeat];
    actor::EncodeGlobal(view, global);
    auto* tail = reinterpret_cast<_Float16*>(row + 2 * board + units * actor::kUnitFeat);
    half::Pack(global, actor::kGlobalFeat, reinterpret_cast<uint16_t*>(tail));
    tail += actor::kGlobalFeat;
    std::fill(tail, tail + kMaxShopInstances * kNumShops, _Float16{0});
    for (size_t j = 0; j < engine.town_shops().size(); ++j) {
      tail[j * kNumShops + engine.town_shops()[j]] = 1;
    }
}

int EntityExtraFeatures(int units) {
  return units * actor::kUnitFeat + kNumProducts * kProductFeatures + kHistoryFeatures;
}

void EncodeEntityExtras(const StateView& engine, int seat, int units,
                        const PublicHistory& history, uint16_t* output,
                        const uint16_t* opponent_board) {
  const auto& config = engine.config();
  // Passing nullptr is the shared encoder's explicit hidden-inventory boundary.
  actor::EncodeUnitsHalf(config, engine.farm(1 - seat), nullptr,
                         engine.step_index(), units, output, opponent_board);
  auto* products = reinterpret_cast<_Float16*>(output + units * actor::kUnitFeat);
  std::fill(products, products + kNumProducts * kProductFeatures + kHistoryFeatures, _Float16{0});
  const auto& previous = history.Previous(engine, config.turns_per_day);
  const double area = config.board_size * config.board_size;
  std::array<std::array<double, kNumProducts>, 2> yields{}, producers{};
  for (int player = 0; player < 2; ++player) {
    for (const auto& tile : engine.farm(player).tiles) {
      int product = -1;
      if (tile.kind == TileKind::kPlant) product = tile.crop;
      if (tile.kind == TileKind::kStructure && tile.has_animal) {
        product = kAnimals[tile.animal].product;
      }
      if (product >= 0) {
        yields[player][product] += tile.yield_units;
        producers[player][product] += 1;
      }
    }
  }
  for (int product = 0; product < kNumProducts; ++product) {
    auto* row = products + product * kProductFeatures;
    const auto& parameters = config.market_params[product];
    const double base = std::max(1.0, parameters.base);
    const double scale = std::max(1.0, parameters.t);
    row[0] = Symlog((engine.market().inventory[product] - parameters.i0) / scale);
    row[1] = engine.market().prices[product] / base;
    row[2] = std::log1p(engine.priv(seat).shed[product]) / 5.0;
    row[3] = (engine.market().prices[product] - previous.prices[product]) / base;
    row[4] = Symlog((engine.market().inventory[product] - previous.inventory[product]) / scale);
    row[5] = Symlog(engine.market().inventory[product]) / 16.0;
    row[6] = base / 250.0;
    row[7] = scale / 500.0;
    row[8] = parameters.below_target;
    row[9] = parameters.above_target;
    row[10 + static_cast<int>(parameters.below_func)] = 1;
    row[16 + static_cast<int>(parameters.above_func)] = 1;
    if (product < kNumCrops) {
      const auto& crop = kCrops[product];
      row[22] = crop.seed_cost / 500.0;
      row[23] = crop.first_yield_day / 30.0;
      row[24] = crop.max_yield_day / 30.0;
      row[25] = crop.interval / 10.0;
      row[26] = crop.max_yield / 10.0;
      row[27] = crop.ongoing;
    } else {
      for (const auto& animal : kAnimals) {
        if (animal.product != product) continue;
        row[22] = animal.cost / 500.0;
        row[23] = animal.first_yield_day / 30.0;
        row[25] = animal.interval / 10.0;
        row[26] = animal.max_held / 10.0;
        row[27] = 1;
      }
    }
    row[28] = std::log1p(yields[seat][product]) / 5.0;
    row[29] = std::log1p(yields[1 - seat][product]) / 5.0;
    row[30] = producers[seat][product] / area;
    row[31] = producers[1 - seat][product] / area;
    for (int shop : engine.town_shops()) {
      const auto& data = kShops[shop];
      for (int index = 0; index < data.n_products; ++index) {
        if (data.products[index] == product) row[32] += _Float16{0.125};
      }
    }
    row[33] = std::min(1.0, static_cast<double>(engine.step_index()) / config.turns_per_day);
  }
  auto* changes = products + kNumProducts * kProductFeatures;
  for (int relative = 0; relative < 2; ++relative) {
    const int player = relative == 0 ? seat : 1 - seat;
    const auto& farm = engine.farm(player);
    changes[6 * relative] = Symlog((farm.money - previous.cash[player]) / 1000.0);
    changes[6 * relative + 1] = (farm.hands.size() - previous.hands[player]) / 32.0;
    changes[6 * relative + 2] = (farm.extra_unlocked - previous.land[player]) / 3.0;
    changes[6 * relative + 3] = farm.hires_today / 32.0;
    changes[6 * relative + 4] = farm.extra_unlocked / 3.0;
    changes[6 * relative + 5] = Symlog(previous.cash[player]) / 12.0;
  }
  changes[12] = std::min(1.0, static_cast<double>(engine.step_index()) / config.turns_per_day);
  changes[13] = static_cast<double>(engine.step_index() % config.shop_sell_interval) /
                config.shop_sell_interval;
  changes[14] = static_cast<double>(engine.step_index() % config.center_sell_interval) /
                config.center_sell_interval;
  changes[15] = config.weed_spawn_chance;
}

}  // namespace kagg::parallel
