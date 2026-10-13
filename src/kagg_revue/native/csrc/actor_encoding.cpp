#include "actor_encoding.hpp"

#include <algorithm>
#include <cmath>
#include <cstring>
#include <vector>

#include "engine.hpp"
#include "half.hpp"

namespace kagg::actor {
namespace {

constexpr double kInvLog101 = 0.21714724095162588;

float Log1pScale(double value) {
  return static_cast<float>(std::log1p(std::max(0.0, value)) * kInvLog101);
}

int DistanceToShed(int x, int y, int board_size) {
  int best = 1 << 20;
  for (const auto& [target_x, target_y] : ShedAccessTiles(board_size)) {
    best = std::min(best, std::abs(target_x - x) + std::abs(target_y - y));
  }
  return best;
}

int NextProductionIn(int day, int start_day, int first_yield_day, int interval) {
  if (interval <= 0) return -1;
  const int since = day + 1 - start_day - first_yield_day;
  if (since <= 0) return -since;
  const int remainder = since % interval;
  return remainder == 0 ? 0 : interval - remainder;
}

uint64_t Fibonacci(int n) {
  uint64_t left = 1;
  uint64_t right = 1;
  for (int index = 0; index < n; ++index) {
    const uint64_t next = left + right;
    left = right;
    right = next;
  }
  return left;
}

int64_t NextHireCost(const Config& config, const Farm& farm) {
  return config.farm_hand_cost_mult * static_cast<int64_t>(Fibonacci(farm.hires_today));
}

struct UnitRef {
  int x;
  int y;
  const Inventory* inventory;
};

int CollectUnits(const Farm& farm, const PrivateState* private_state, int unit_limit,
                 UnitRef* output) {
  const int count = std::min<int>(1 + static_cast<int>(farm.hands.size()), unit_limit);
  for (int index = 0; index < count; ++index) {
    const int x = index == 0 ? farm.farmer_x : farm.hands[index - 1].first;
    const int y = index == 0 ? farm.farmer_y : farm.hands[index - 1].second;
    const Inventory* inventory = nullptr;
    if (private_state != nullptr &&
        index < static_cast<int>(private_state->inventories.size())) {
      inventory = &private_state->inventories[index];
    }
    output[index] = UnitRef{x, y, inventory};
  }
  return count;
}

}  // namespace

template <typename Output>
void EncodeBoardImpl(const Config& config, const Farm& farm, int step,
                     Output* output) {
  const int board_size = config.board_size;
  const int board_area = board_size * board_size;
  std::memset(output, 0, sizeof(Output) * kBoardChannels * board_area);
  const int day = step / config.turns_per_day;
  const auto at = [&](int plane_index, int y, int x) -> Output& {
    return output[plane_index * board_area + y * board_size + x];
  };
  for (int y = 0; y < board_size; ++y) {
    for (int x = 0; x < board_size; ++x) {
      const Tile& tile = farm.tiles[y * board_size + x];
      switch (tile.kind) {
        case TileKind::kEmpty:
          at(plane::kEmpty, y, x) = 1.0F;
          break;
        case TileKind::kLocked:
          at(plane::kLocked, y, x) = 1.0F;
          break;
        case TileKind::kWeed:
          at(plane::kWeed, y, x) = 1.0F;
          break;
        case TileKind::kPlant: {
          at(plane::kPlant, y, x) = 1.0F;
          at(plane::kCrop0 + tile.crop, y, x) = 1.0F;
          at(plane::kPlantAge, y, x) = static_cast<float>(day - tile.planted_day) / 30.0F;
          at(plane::kYield, y, x) = static_cast<float>(tile.yield_units) / 6.0F;
          at(plane::kWatered, y, x) = tile.watered_today ? 1.0F : 0.0F;
          at(plane::kUnwatered, y, x) =
              static_cast<float>(tile.consecutive_unwatered) / 2.0F;
          at(plane::kFertDays, y, x) =
              static_cast<float>(std::max(0, tile.fertilized_until_day - day + 1)) / 3.0F;
          if (tile.max_lifespan_step >= 0) {
            const float fraction = static_cast<float>(tile.max_lifespan_step - step) /
                                   static_cast<float>(config.episode_steps);
            at(plane::kLifespan, y, x) = std::clamp(fraction, 0.0F, 1.0F);
          } else {
            at(plane::kLifespan, y, x) = 1.0F;
          }
          const CropData& crop = kCrops[tile.crop];
          if (crop.ongoing) {
            const int remaining = NextProductionIn(
                day, tile.planted_day, crop.first_yield_day, crop.interval);
            if (remaining >= 0) {
              at(plane::kNextProd, y, x) = static_cast<float>(remaining + 1) / 8.0F;
            }
          }
          break;
        }
        case TileKind::kStructure: {
          at(tile.structure == StructureKind::kCoop ? plane::kCoop : plane::kPasture,
             y, x) = 1.0F;
          if (tile.has_animal) {
            const AnimalData& animal = kAnimals[tile.animal];
            at(plane::kHasAnimal, y, x) = 1.0F;
            at(plane::kAnimal0 + tile.animal, y, x) = 1.0F;
            at(plane::kYield, y, x) = static_cast<float>(tile.yield_units) / 6.0F;
            at(plane::kFed, y, x) = tile.fed_today ? 1.0F : 0.0F;
            at(plane::kUnfed, y, x) = static_cast<float>(tile.consecutive_unfed) / 2.0F;
            at(plane::kCared, y, x) = tile.cared_today ? 1.0F : 0.0F;
            at(plane::kFertAvail, y, x) = tile.fertilizer_available ? 1.0F : 0.0F;
            at(plane::kPendingBonus, y, x) =
                static_cast<float>(tile.pending_care_bonus) / 6.0F;
            const int remaining = NextProductionIn(
                day, tile.placed_day, animal.first_yield_day, animal.interval);
            if (remaining >= 0) {
              at(plane::kNextProd, y, x) = static_cast<float>(remaining + 1) / 8.0F;
            }
          }
          break;
        }
      }
    }
  }
  const auto add_unit = [&](int x, int y) { at(plane::kUnitsHere, y, x) += 0.25F; };
  add_unit(farm.farmer_x, farm.farmer_y);
  for (const auto& [x, y] : farm.hands) add_unit(x, y);
  for (const auto& [x, y] : ShedAccessTiles(board_size)) {
    at(plane::kShedAccess, y, x) = 1.0F;
  }
}

template <typename Output>
void EncodeUnitsImpl(const Config& config, const Farm& farm,
                     const PrivateState* private_state, int step,
                     int unit_limit, Output* output, const Output* encoded_board = nullptr) {
  const int board_size = config.board_size;
  std::memset(output, 0, sizeof(Output) * unit_limit * kUnitFeat);
  thread_local std::vector<UnitRef> units;
  units.resize(unit_limit);
  const int count = CollectUnits(farm, private_state, unit_limit, units.data());
  thread_local std::vector<Output> scratch_board;
  if (encoded_board == nullptr) {
    scratch_board.resize(static_cast<size_t>(kBoardChannels) * board_size * board_size);
    EncodeBoardImpl(config, farm, step, scratch_board.data());
    encoded_board = scratch_board.data();
  }
  const int board_area = board_size * board_size;
  for (int index = 0; index < count; ++index) {
    Output* features = output + static_cast<size_t>(index) * kUnitFeat;
    const UnitRef& unit = units[index];
    features[0] = 1.0F;
    features[1] = index == 0 ? 1.0F : 0.0F;
    features[2] = static_cast<float>(unit.x) / static_cast<float>(board_size - 1);
    features[3] = static_cast<float>(unit.y) / static_cast<float>(board_size - 1);
    features[4] = IsShedAdjacent(unit.x, unit.y, board_size) ? 1.0F : 0.0F;
    features[5] = static_cast<float>(DistanceToShed(unit.x, unit.y, board_size)) /
                  static_cast<float>(board_size);
    if (unit.inventory != nullptr) {
      int64_t total = 0;
      for (size_t order = 0; order < unit.inventory->items.size(); ++order) {
        const auto [item_index, count] = unit.inventory->items[order];
        features[6 + item_index] = Log1pScale(static_cast<double>(count));
        features[kUnitOrderFirst + item_index] =
            static_cast<float>(order + 1) / static_cast<float>(kNumItems);
        total += count;
      }
      features[6 + kNumItems] = static_cast<float>(total) / 20.0F;
    }
    for (int channel = 0; channel < kBoardChannels; ++channel) {
      features[kUnitBaseFeat + channel] =
          encoded_board[static_cast<size_t>(channel) * board_area + unit.y * board_size + unit.x];
    }
  }
}

template <typename Output>
void EncodeGlobalImpl(const SeatView& view, Output* output) {
  const Config& config = *view.config;
  std::memset(output, 0, sizeof(Output) * kGlobalFeat);
  int index = 0;
  const int day = view.day();
  output[index++] = static_cast<float>(day) / 30.0F;
  output[index++] = static_cast<float>(view.hour()) /
                    static_cast<float>(config.turns_per_day);
  output[index++] = static_cast<float>(view.step) /
                    static_cast<float>(config.episode_steps);
  output[index++] = static_cast<float>(config.episode_steps - view.step) /
                    static_cast<float>(config.episode_steps);
  output[index++] = static_cast<float>(config.episode_steps / config.turns_per_day - day) /
                    30.0F;

  const double own_money = view.own_farm->money;
  const double opponent_money = view.opponent_farm->money;
  output[index++] = static_cast<float>(own_money / 1e5);
  output[index++] = static_cast<float>(std::log1p(std::max(0.0, own_money)) / 12.0);
  output[index++] = static_cast<float>(opponent_money / 1e5);
  output[index++] = static_cast<float>(std::log1p(std::max(0.0, opponent_money)) / 12.0);
  output[index++] = static_cast<float>((own_money - opponent_money) / 1e5);

  for (int product = 0; product < kNumProducts; ++product) {
    const MarketParams& parameters = config.market_params[product];
    const double delta =
        static_cast<double>(view.market_inventory[product] - parameters.i0) /
        std::max(1.0, parameters.t);
    output[index++] = static_cast<float>(std::clamp(delta, -8.0, 8.0) / 8.0);
  }
  for (int product = 0; product < kNumProducts; ++product) {
    output[index++] = static_cast<float>(
        static_cast<double>(view.market_prices[product]) /
        std::max(1.0, config.market_params[product].base) / 5.0);
  }

  int64_t shed_total = 0;
  for (int item_index = 0; item_index < kNumItems; ++item_index) {
    output[index++] = Log1pScale(static_cast<double>(view.own_private->shed[item_index]));
    shed_total += view.own_private->shed[item_index];
  }
  output[index++] = static_cast<float>(shed_total) /
                    static_cast<float>(config.shed_capacity);
  for (int crop = 0; crop < kNumCrops; ++crop) {
    output[index++] = Log1pScale(static_cast<double>(view.own_private->seeds[crop]));
  }
  for (int item_index = 0; item_index < kNumItems; ++item_index) {
    output[index++] = Log1pScale(view.opponent_shed_estimate[item_index]);
  }

  int shop_total = 0;
  for (int shop = 0; shop < kNumShops; ++shop) {
    output[index++] = static_cast<float>(view.shop_counts[shop]) / 2.0F;
    shop_total += view.shop_counts[shop];
  }
  output[index++] = static_cast<float>(shop_total) /
                    static_cast<float>(kMaxShopInstances);
  const int interval = config.shop_unlock_interval;
  output[index++] = static_cast<float>((interval - 1 - (day % interval) + interval) % interval) /
                    static_cast<float>(interval);
  output[index++] = static_cast<float>(kMaxShopInstances - shop_total) /
                    static_cast<float>(kMaxShopInstances);

  const auto encode_quadrants = [&](const Farm& farm, Output* destination) {
    destination[0] = 1.0F;
    for (int quadrant = 0; quadrant < static_cast<int>(kLandOrder.size()); ++quadrant) {
      destination[kLandOrder[quadrant]] =
          quadrant < farm.extra_unlocked ? 1.0F : 0.0F;
    }
  };
  encode_quadrants(*view.own_farm, output + index);
  index += 4;
  encode_quadrants(*view.opponent_farm, output + index);
  index += 4;

  output[index++] = static_cast<float>(view.own_farm->hands.size()) / 15.0F;
  output[index++] = static_cast<float>(view.opponent_farm->hands.size()) / 15.0F;
  output[index++] = static_cast<float>(view.own_farm->hires_today) / 8.0F;
  output[index++] = static_cast<float>(view.opponent_farm->hires_today) / 8.0F;
  output[index++] = static_cast<float>(
      std::log1p(static_cast<double>(NextHireCost(config, *view.own_farm))) / 10.0);
}

void EncodeBoard(const Config& config, const Farm& farm, int step,
                 float* output) {
  EncodeBoardImpl(config, farm, step, output);
}

void EncodeUnits(const Config& config, const Farm& farm,
                 const PrivateState* private_state, int step, int unit_limit,
                 float* output) {
  EncodeUnitsImpl(config, farm, private_state, step, unit_limit, output);
}

void EncodeGlobal(const SeatView& view, float* output) {
  EncodeGlobalImpl(view, output);
}

using Float16 = _Float16;
static_assert(sizeof(Float16) == sizeof(std::uint16_t));

void EncodeBoardHalf(const Config& config, const Farm& farm, int step,
                     std::uint16_t* output) {
  if (farm.hands.size() >= 2048) {
    // Preserve sequential half rounding even outside supported policy unit limits.
    EncodeBoardImpl(config, farm, step, reinterpret_cast<Float16*>(output));
    return;
  }
  thread_local std::vector<float> board;
  board.resize(static_cast<size_t>(kBoardChannels) * config.board_size * config.board_size);
  EncodeBoardImpl(config, farm, step, board.data());
  half::Pack(board.data(), board.size(), output);
}

void EncodeUnitsHalf(const Config& config, const Farm& farm,
                     const PrivateState* private_state, int step,
                     int unit_limit, std::uint16_t* output, const std::uint16_t* board) {
  EncodeUnitsImpl(config, farm, private_state, step, unit_limit,
                  reinterpret_cast<Float16*>(output), reinterpret_cast<const Float16*>(board));
}

template <typename Output>
void EncodeEngineSeatImpl(const Engine& engine, int player, int unit_limit,
                          Output* board_output, Output* unit_output,
                          Output* global_output) {
  if (player < 0 || player > 1) return;
  const Config& config = engine.config();
  const int opponent = 1 - player;
  const size_t board_size = static_cast<size_t>(kBoardChannels) *
                            config.board_size * config.board_size;
  const size_t unit_size = static_cast<size_t>(unit_limit) * kUnitFeat;
  EncodeBoardImpl(config, engine.farm(player), engine.step_index(),
                  board_output);
  EncodeBoardImpl(config, engine.farm(opponent), engine.step_index(),
                  board_output + board_size);
  EncodeUnitsImpl(config, engine.farm(player), &engine.priv(player),
                  engine.step_index(), unit_limit, unit_output);
  EncodeUnitsImpl(config, engine.farm(opponent), nullptr, engine.step_index(),
                  unit_limit, unit_output + unit_size);

  SeatView view;
  view.config = &config;
  view.step = engine.step_index();
  view.own_farm = &engine.farm(player);
  view.opponent_farm = &engine.farm(opponent);
  view.own_private = &engine.priv(player);
  view.market_inventory = engine.market().inventory;
  view.market_prices = engine.market().prices;
  view.shop_counts.fill(0);
  for (const int shop : engine.town_shops()) ++view.shop_counts[shop];
  EncodeGlobalImpl(view, global_output);
}

void EncodeEngineSeat(const Engine& engine, int player, int unit_limit,
                      float* board_output, float* unit_output,
                      float* global_output) {
  EncodeEngineSeatImpl(engine, player, unit_limit, board_output, unit_output,
                       global_output);
}

}  // namespace kagg::actor
