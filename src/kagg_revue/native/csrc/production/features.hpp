// Versioned agronomic features derived exclusively from the observing seat.
#pragma once

#include <array>
#include <cstdint>

#include "parallel/state.hpp"

namespace kagg::production {

struct Ledger;

inline constexpr const char* kVersion = "grounded-production-context-v4";
inline constexpr int kTileFeatures = 23;    // rule forecasts, productive tiles only
inline constexpr int kBoardFeatures = 36;   // forecasts + geometry + resource reachability
inline constexpr int kProductFeatures = 49;
inline constexpr int kGlobalFeatures = 22;
inline constexpr int kUnitFeatures = 16;

// Field order is the checkpointed contract; `native/agronomy.py` mirrors the names.
namespace tile {
enum : int {
  kHarvestable = 0,
  kHarvestableQuantity,
  kAgeDays,
  kCapacityRemaining,
  kNextProductionTurns,
  kRemainingProductionEvents,
  kDecayStartTurns,
  kHasDecayDeadline,
  kWateringBonusWindow,
  kWaterImmediateYieldGain,
  kFertilizeThenWaterExtraGain,
  kRemainingWateringBonusDays,
  kNewFertilizerCoveredEvents,
  kNextMaintainedProduction,
  kNextProductionOverflowWithoutHarvest,
  kDayEndIdleYieldDelta,
  kDayEndMaintainedYieldDelta,
  kDayEndIdleLoss,
  kMaintenancePreventsDayEndLoss,
  kFeedingPreservesBankedBonus,
  kNewCarePayoutTurns,
  kNewCareCanPayBeforeEnd,
  kFirstHarvestTerminalSlack,
  kCount,
};
}  // namespace tile
static_assert(tile::kCount == kTileFeatures);

namespace board {
enum : int {
  kNearestUnitDistance = kTileFeatures,
  kUnitsWithinTwo,
  kReachableBeforeDayEnd,
  kShedDistance,
  kHarvestSellableBeforeEnd,
  kFeedCarrierDistance,
  kHasFeedCarrier,
  kFeedViaShedDistance,
  kShedHasWheat,
  kFertilizerCarrierDistance,
  kHasFertilizerCarrier,
  kFertilizerViaShedDistance,
  kShedHasFertilizer,
  kCount,
};
}  // namespace board
static_assert(board::kCount == kBoardFeatures);

namespace product {
enum : int {
  kOwnImmatureTiles = 0,
  kOwnHarvestableTiles,
  kOwnExhaustedOngoingTiles,
  kOwnDayEndIdleLossTiles,
  kOwnNeedsWater,
  kOwnNeedsFeed,
  kOwnUsefulCareAvailable,
  kOwnFertilizerCollectable,
  kOwnHarvestableQuantity,
  kOwnRemainingProductionEvents,
  kOwnAdditionalHarvest1Day,
  kOwnAdditionalHarvest2Days,
  kOwnAdditionalHarvest4Days,
  kOwnNextProductionOverflow,
  kOpponentImmatureTiles,
  kOpponentHarvestableTiles,
  kOpponentExhaustedOngoingTiles,
  kOpponentHarvestableQuantity,
  kOpponentAdditionalHarvest1Day,
  kOpponentAdditionalHarvest2Days,
  kOpponentAdditionalHarvest4Days,
  kUnplantedSeedsOrStoredAnimals,
  kCarriedAnimals,
  kEmptyCompatibleTiles,
  kTownConsumptionPerDay,
  kNextTownConsumptionTurns,
  kHasTownConsumptionBeforeEnd,
  kOwnAvailableTasks,
  kNewPlacementFirstHarvestTerminalSlack,
  kNewPlacementTotalYield,
  kNewPlacementTotalYieldBoosted,
  kSellAveragePrice2,
  kSellAveragePrice4,
  kSellAveragePrice8,
  kSellAveragePrice16,
  kSellAveragePrice32,
  kSellAveragePrice64,
  kSellAveragePriceAllStock,
  kUnitsUntilPriceBelow75,
  kUnitsUntilPriceBelow50,
  kUnitsUntilPriceFloor,
  kPriceAfterVisibleSupply,
  kMarketGlutted,
  kGlutRecoveryDays,
  kBuyAveragePrice10,
  kBuyAveragePrice50,
  kOwnHarvestedCumulative,
  kOpponentHarvestedCumulative,
  kPlayersNetMarketFlowCumulative,
  kCount,
};
}  // namespace product
static_assert(product::kCount == kProductFeatures);

namespace global {
enum : int {
  kFeedDueToday = 0,
  kWheatTotal,
  kWheatStored,
  kWheatCarried,
  kFeedShortfall,
  kFertilizerStored,
  kFertilizerCarried,
  kTurnsLeftToday,
  kFinalDay,
  kShedRoom,
  kCarriedTotal,
  kShedOverflowTonight,
  kOwnDueTaskTiles,
  kOwnDyingTonightTiles,
  kOwnUnitTurnsLeft,
  kOwnTaskPressure,
  kOwnTravelEstimate,
  kOpponentDueTaskTiles,
  kOpponentDyingTonightTiles,
  kOpponentUnitTurnsLeft,
  kOpponentTaskPressure,
  kOpponentTravelEstimate,
  kCount,
};
}  // namespace global
static_assert(global::kCount == kGlobalFeatures);

namespace unit {
enum : int {
  kNearestNeedsWater = 0,
  kNearestNeedsFeed,
  kNearestNeedsCare,
  kNearestFertilizerCollectable,
  kNearestHarvestable,
  kNearestPlantable,
  kHasNeedsWater,
  kHasNeedsFeed,
  kHasNeedsCare,
  kHasFertilizerCollectable,
  kHasHarvestable,
  kHasPlantable,
  kDueTilesNorth,
  kDueTilesSouth,
  kDueTilesEast,
  kDueTilesWest,
  kCount,
};
}  // namespace unit
static_assert(unit::kCount == kUnitFeatures);

struct TileContext {
  std::array<double, kTileFeatures> values{};
  // Additional harvest under daily maintenance, earliest harvest, no new care/fertilizer.
  std::array<double, 3> harvest{};
  int next_production_step = -1;  // first turn of the next production day, if any
};

bool Productive(const Tile& tile);
bool Harvestable(const Tile& tile, int day);
int Product(const Tile& tile);
TileContext Describe(const Tile& tile, const Config& config, int step);
// Layout: [2, area, kBoardFeatures] [kNumProducts, kProductFeatures] [kGlobalFeatures]
// [2, units, kUnitFeatures]; the second half of each pair is the opponent.
int FeatureCount(int board_size, int units);
void Encode(const parallel::StateView& state, int seat, const Ledger& ledger, int units,
            uint16_t* output);

}  // namespace kagg::production
