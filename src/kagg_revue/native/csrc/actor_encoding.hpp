// Deploy-visible observation encoding shared by training and submission.
#pragma once

#include <array>
#include <cstdint>

#include "types.hpp"

namespace kagg {
class Engine;
}

namespace kagg::actor {

// Bump whenever an encoded field, shape, or normalization changes.
inline constexpr const char* kEncoderSpecVersion = "actor-observation-v2";

namespace plane {
enum : int {
  kEmpty = 0,
  kLocked,
  kWeed,
  kPlant,
  kCoop,
  kPasture,
  kCrop0,
  kPlantAge = kCrop0 + kNumCrops,
  kYield,
  kWatered,
  kUnwatered,
  kFertDays,
  kLifespan,
  kHasAnimal,
  kAnimal0,
  kFed = kAnimal0 + kNumAnimals,
  kUnfed,
  kCared,
  kFertAvail,
  kPendingBonus,
  kNextProd,
  kUnitsHere,
  kShedAccess,
  kCount,
};
}  // namespace plane

inline constexpr int kBoardChannels = plane::kCount;
inline constexpr int kUnitBaseFeat = 6 + kNumItems + 1;
inline constexpr int kUnitLegacyFeat = kUnitBaseFeat + kBoardChannels;
inline constexpr int kUnitOrderFirst = kUnitLegacyFeat;
inline constexpr int kUnitFeat = kUnitLegacyFeat + kNumItems;
inline constexpr int kUnitPrivFirst = 6;
inline constexpr int kUnitPrivLast = 6 + kNumItems + 1;
inline constexpr int kGlobalFeat = 82;

struct SeatView {
  const Config* config = nullptr;
  int step = 0;
  const Farm* own_farm = nullptr;
  const Farm* opponent_farm = nullptr;
  const PrivateState* own_private = nullptr;
  std::array<double, kNumItems> opponent_shed_estimate{};
  std::array<int64_t, kNumProducts> market_inventory{};
  std::array<int64_t, kNumProducts> market_prices{};
  std::array<int, kNumShops> shop_counts{};

  int day() const { return step / config->turns_per_day; }
  int hour() const { return step % config->turns_per_day; }
};

void EncodeBoard(const Config& config, const Farm& farm, int step, float* output);
void EncodeUnits(const Config& config, const Farm& farm, const PrivateState* private_state,
                 int step, int unit_limit, float* output);
void EncodeGlobal(const SeatView& view, float* output);

// Compact encoders preserve IEEE float16 observations. An already encoded
// farm board can be reused when gathering local unit features.
void EncodeBoardHalf(const Config& config, const Farm& farm, int step,
                     std::uint16_t* output);
void EncodeUnitsHalf(const Config& config, const Farm& farm,
                     const PrivateState* private_state, int step,
                     int unit_limit, std::uint16_t* output,
                     const std::uint16_t* board = nullptr);

// Encode directly from the native engine without constructing an official
// Python observation. Buffers use board [2,C,H,W], units [2,U,F], global [G].
void EncodeEngineSeat(const Engine& engine, int player, int unit_limit,
                      float* board_output, float* unit_output,
                      float* global_output);

}  // namespace kagg::actor
