// Turn processing: unit actions, town consumption, decay, end-of-day.
// Each block is a line-faithful translation of the official interpreter;
// comments cite the corresponding Python function.

#include "engine.hpp"

#include <algorithm>
#include <stdexcept>
#include <utility>

#include "market_phase.hpp"
#include "py_rng.hpp"
#include "production/rules.hpp"
#include "unit_phase.hpp"

namespace kagg {

Engine::Engine(const Config& config, int64_t seed) : config_(config) {
  if (config_.max_market_orders < 1) config_.max_market_orders = 1;
  if (config_.turns_per_day < 1) config_.turns_per_day = 1;
  if (config_.shop_unlock_interval < 1) config_.shop_unlock_interval = 1;
  if (config_.shop_sell_interval < 1) config_.shop_sell_interval = 1;
  if (config_.center_sell_interval < 1) config_.center_sell_interval = 1;
  Reset(seed);
}

void Engine::Reset(int64_t seed) {
  seed_ = seed;
  step_ = 0;
  done_ = false;
  const int bs = config_.board_size;
  for (int p = 0; p < 2; ++p) {
    Farm& farm = farms_[p];
    farm.money = static_cast<double>(config_.starting_money);
    farm.tiles.assign(static_cast<size_t>(bs) * bs, Tile{});
    for (int y = 0; y < bs; ++y) {
      for (int x = 0; x < bs; ++x) {
        if (QuadrantOf(x, y, bs) != 0) farm.tiles[y * bs + x] = MakeLocked();
      }
    }
    const auto spawn = DefaultSpawn(bs);
    farm.farmer_x = spawn.first;
    farm.farmer_y = spawn.second;
    farm.hands.clear();
    farm.extra_unlocked = 0;
    farm.hires_today = 0;
    privates_[p] = PrivateState{};
    privates_[p].inventories.assign(1, Inventory{});
  }
  for (int i = 0; i < kNumProducts; ++i) {
    market_.inventory[i] = config_.market_params[i].i0;
    // Official `_new_market` publishes `base` untouched as the initial price.
    market_.prices[i] = static_cast<int64_t>(config_.market_params[i].base);
  }
  town_shops_.clear();
}

// --- Town, decay, end-of-day ----------------------------------------------

// `_town_consume`
void Engine::TownConsume(int step) {
  if (step % config_.shop_sell_interval == 0) {
    for (const int shop_idx : town_shops_) {
      const ShopData& shop = kShops[shop_idx];
      const int64_t multiplier = (shop.n_products == 1) ? 2 : 1;
      for (int k = 0; k < shop.n_products; ++k) {
        market_.inventory[shop.products[k]] -= multiplier;
      }
    }
  }
  if (step % config_.center_sell_interval == 0) {
    for (int i = 0; i < kNumProducts; ++i) {
      if (i != item::kFertilizer) market_.inventory[i] -= 1;
    }
  }
  RefreshMarketPrices(config_, &market_);
}

// `_decay_plants`
void Engine::DecayPlants(Farm& farm, int step) {
  const int bs = config_.board_size;
  for (int y = 0; y < bs; ++y) {
    for (int x = 0; x < bs; ++x) {
      Tile& tile = farm.tiles[y * bs + x];
      if (tile.kind != TileKind::kPlant) continue;
      production::Decay(tile, step);
    }
  }
}

// `_daily_refresh_plants`
void Engine::DailyRefreshPlants(Farm& farm, int day) {
  const int bs = config_.board_size;
  for (int y = 0; y < bs; ++y) {
    for (int x = 0; x < bs; ++x) {
      Tile& tile = farm.tiles[y * bs + x];
      if (tile.kind != TileKind::kPlant) continue;
      production::RefreshPlant(tile, day, config_.turns_per_day);
    }
  }
}

// `_daily_refresh_animals`
void Engine::DailyRefreshAnimals(Farm& farm, int day) {
  const int bs = config_.board_size;
  for (int y = 0; y < bs; ++y) {
    for (int x = 0; x < bs; ++x) {
      Tile& tile = farm.tiles[y * bs + x];
      if (!(tile.kind == TileKind::kStructure && tile.has_animal)) continue;
      production::RefreshAnimal(tile, day);
    }
  }
}

// `_end_of_day`
void Engine::EndOfDay(int day) {
  // Stable RNG keyed off the resolved episode seed + day.
  PyRandom rng((static_cast<uint128>(seed_) * 1000003u) ^ static_cast<uint128>(day));

  const int bs = config_.board_size;
  for (int p = 0; p < 2; ++p) {
    Farm& farm = farms_[p];
    PrivateState& priv = privates_[p];
    DailyRefreshPlants(farm, day);
    DailyRefreshAnimals(farm, day);
    // `_spawn_weeds`: one draw per empty tile, row-major, player 0 first.
    for (int y = 0; y < bs; ++y) {
      for (int x = 0; x < bs; ++x) {
        Tile& tile = farm.tiles[y * bs + x];
        if (tile.kind == TileKind::kEmpty && rng.Random() < config_.weed_spawn_chance) {
          tile = MakeWeed();
        }
      }
    }
    // `_drop_inventories_to_shed`: dict insertion order; overflow discarded.
    for (Inventory& inv : priv.inventories) {
      for (const auto& [it, n] : inv.items) {
        const int64_t room = std::max<int64_t>(0, config_.shed_capacity - ShedTotal(priv));
        const int64_t take = std::min(n, room);
        if (take > 0) priv.shed[it] += take;
      }
      inv.items.clear();
    }
    const auto spawn = DefaultSpawn(bs);
    farm.farmer_x = spawn.first;
    farm.farmer_y = spawn.second;
    farm.hands.clear();
    farm.hires_today = 0;
    priv.inventories.assign(1, Inventory{});
  }

  const int next_day = day + 1;
  if (next_day > 0 && next_day % config_.shop_unlock_interval == 0 &&
      static_cast<int>(town_shops_.size()) < kMaxShopInstances) {
    // `rng.choice(sorted(SHOPS))`; kShops is already in sorted-name order.
    town_shops_.push_back(static_cast<int>(rng.RandBelow(kNumShops)));
  }
}

// --- Step (`interpreter`) ---------------------------------------------------

void Engine::Step(const PlayerAction& a0, const PlayerAction& a1,
                  std::vector<MarketSlotTrace>* market_trace) {
  if (done_) throw std::logic_error("episode is done");
  const int day = step_ / config_.turns_per_day;
  const std::array<const PlayerAction*, 2> actions = {&a0, &a1};

  for (int p = 0; p < 2; ++p) {
    const PlayerAction& pa = *actions[p];
    ApplyPlayerUnitPhase(config_, &farms_[p], &privates_[p], pa, day);
  }

  const std::array<Farm*, 2> farm_ptrs = {&farms_[0], &farms_[1]};
  const std::array<PrivateState*, 2> private_ptrs = {&privates_[0], &privates_[1]};
  ApplyMarketPhase(config_, farm_ptrs, private_ptrs, &market_, a0, a1, market_trace);
  TownConsume(step_);
  for (Farm& farm : farms_) DecayPlants(farm, step_);
  if ((step_ + 1) % config_.turns_per_day == 0) EndOfDay(day);

  if (step_ >= config_.episode_steps - 2) done_ = true;
  step_ += 1;
}

}  // namespace kagg
