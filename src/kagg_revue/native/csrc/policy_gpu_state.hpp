// Compact, lossless PolicySession state shared with the GPU legality kernel.
#pragma once

namespace kagg::policy_gpu {

inline constexpr int kVersion = 3;

enum HeaderField {
  kDay = 0,
  kUnitCount,
  kUnitIndex,
  kMarketSlots,
  kPhase,
  kShedCapacity,
  kMaxMarketOrders,
  kBoardSize,
  kShedTotal,
  kMoney,
  kHiresToday,
  kExtraUnlocked,
  kFarmHandCostMultiplier,
  // Python-side economic replay sets this after an order whose realized
  // consequence depends on the opponent's simultaneous market orders.
  kMarketProjectionConditional,
  kHeaderFields,
};

enum TileField {
  kKind = 0,
  kCrop,
  kPlantedDay,
  kWateredToday,
  kFertilizedUntilDay,
  kYieldUnits,
  kStructure,
  kHasAnimal,
  kAnimal,
  kFedToday,
  kCaredToday,
  kFertilizerAvailable,
  kTileFields,
};

struct Layout {
  int positions;
  int inventories;
  int inventory_order;
  int shed;
  int seeds;
  int market_inventory;
  int market_prices;
  int market_base_milli;
  int market_i0;
  int market_t_milli;
  int market_below_function;
  int market_below_target_milli;
  int market_above_function;
  int market_above_target_milli;
  int seed_costs;
  int animal_costs;
  int land_costs;
  int tiles;
  int width;
};

inline Layout MakeLayout(int board_size, int unit_limit) {
  Layout layout;
  layout.positions = kHeaderFields;
  layout.inventories = layout.positions + unit_limit * 2;
  layout.inventory_order = layout.inventories + unit_limit * 12;
  layout.shed = layout.inventory_order + unit_limit * 12;
  layout.seeds = layout.shed + 12;
  layout.market_inventory = layout.seeds + 5;
  layout.market_prices = layout.market_inventory + 9;
  layout.market_base_milli = layout.market_prices + 9;
  layout.market_i0 = layout.market_base_milli + 9;
  layout.market_t_milli = layout.market_i0 + 9;
  layout.market_below_function = layout.market_t_milli + 9;
  layout.market_below_target_milli = layout.market_below_function + 9;
  layout.market_above_function = layout.market_below_target_milli + 9;
  layout.market_above_target_milli = layout.market_above_function + 9;
  layout.seed_costs = layout.market_above_target_milli + 9;
  layout.animal_costs = layout.seed_costs + 5;
  layout.land_costs = layout.animal_costs + 3;
  layout.tiles = layout.land_costs + 3;
  layout.width = layout.tiles + board_size * board_size * kTileFields;
  return layout;
}

}  // namespace kagg::policy_gpu
