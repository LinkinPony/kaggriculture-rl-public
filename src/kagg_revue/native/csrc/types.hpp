// Data tables, configuration and state types for the native official-rules
// engine. Semantics authority: the audited interpreter from environment package 1.32.7.
#pragma once

#include <array>
#include <cstdint>
#include <optional>
#include <utility>
#include <vector>

namespace kagg {

inline constexpr int kNumProducts = 9;
inline constexpr int kNumItems = 12;  // products + animals, in shed key order
inline constexpr int kNumCrops = 5;
inline constexpr int kNumAnimals = 3;
inline constexpr int kNumShops = 8;
inline constexpr int kMaxShopInstances = 8;
inline constexpr int64_t kPriceFloor = 1;
inline constexpr double kHingeGain = 8.0;

// Item indices. 0..8 are products (official PRODUCTS order), 9..11 animals.
// Crop index == item index for 0..4; animal index a maps to item kGoose + a.
namespace item {
enum : int {
  kWheat = 0,
  kCarrot,
  kTomato,
  kStrawberry,
  kMelon,
  kEgg,
  kMilk,
  kWool,
  kFertilizer,
  kGoose,
  kCow,
  kSheep,
};
}  // namespace item

inline constexpr std::array<const char*, kNumItems> kItemNames = {
    "WHEAT", "CARROT", "TOMATO",     "STRAWBERRY", "MELON", "EGG",
    "MILK",  "WOOL",   "FERTILIZER", "GOOSE",      "COW",   "SHEEP",
};

struct CropData {
  int64_t seed_cost;
  int first_yield_day;
  int max_yield_day;
  int interval;
  int max_yield;
  bool ongoing;
};

inline constexpr std::array<CropData, kNumCrops> kCrops = {{
    {10, 2, 4, 0, 6, false},     // WHEAT
    {20, 2, 3, 0, 4, false},     // CARROT
    {50, 8, 8, 1, 4, true},      // TOMATO
    {100, 10, 10, 2, 4, true},   // STRAWBERRY
    {80, 10, 12, 0, 6, false},   // MELON
}};

enum class StructureKind : uint8_t { kCoop, kPasture };

struct AnimalData {
  int64_t cost;
  StructureKind structure;
  int first_yield_day;
  int interval;
  int max_held;
  int product;  // item index of the produced good
};

inline constexpr std::array<AnimalData, kNumAnimals> kAnimals = {{
    {300, StructureKind::kCoop, 4, 1, 4, item::kEgg},       // GOOSE
    {400, StructureKind::kPasture, 8, 2, 6, item::kMilk},   // COW
    {500, StructureKind::kPasture, 6, 3, 6, item::kWool},   // SHEEP
}};

// Shops in sorted-name order (the order `rng.choice(sorted(SHOPS))` samples).
struct ShopData {
  const char* name;
  std::array<int, 4> products;
  int n_products;
};

inline constexpr std::array<ShopData, kNumShops> kShops = {{
    {"BAKERY", {item::kEgg, item::kWheat, 0, 0}, 2},
    {"BRUNCH_SPOT", {item::kEgg, item::kWheat, item::kStrawberry, 0}, 3},
    {"FARMERS_MARKET", {item::kWheat, item::kCarrot, item::kTomato, item::kStrawberry}, 4},
    {"ICE_CREAM_SHOP", {item::kStrawberry, item::kMilk, item::kWheat, 0}, 3},
    {"PET_CAFE", {item::kCarrot, 0, 0, 0}, 1},
    {"PIZZA_SHOP", {item::kMilk, item::kTomato, item::kWheat, 0}, 3},
    {"SMOOTHIE_SHOP", {item::kStrawberry, item::kMilk, 0, 0}, 2},
    {"YARN_STORE", {item::kWool, 0, 0, 0}, 1},
}};

// BUY_LAND unlock order (quadrant indices: NW=0, NE=1, SW=2, SE=3) and prices.
inline constexpr std::array<int, 3> kLandOrder = {1, 2, 3};
inline constexpr std::array<int64_t, 3> kLandPrices = {1000, 2000, 4000};
inline constexpr std::array<const char*, 4> kQuadrantNames = {"NW", "NE", "SW", "SE"};

enum class Shape : uint8_t { kLinear, kSq, kSqrt, kLog, kLog10, kHinge };

struct MarketParams {
  double base;
  int64_t i0;
  double t;
  Shape below_func;
  double below_target;
  Shape above_func;
  double above_target;
};

inline constexpr std::array<MarketParams, kNumProducts> kDefaultMarketParams = {{
    {25, 10000, 400, Shape::kSqrt, 0.80, Shape::kLog, 0.20},      // WHEAT
    {35, 10000, 450, Shape::kHinge, 1.00, Shape::kSqrt, 0.70},    // CARROT
    {60, 10000, 200, Shape::kHinge, 0.40, Shape::kSqrt, 0.60},    // TOMATO
    {120, 10000, 100, Shape::kSqrt, 0.70, Shape::kLinear, 1.60},  // STRAWBERRY
    {250, 10000, 300, Shape::kLog, 0.20, Shape::kSq, 3.60},       // MELON
    {50, 10000, 332, Shape::kHinge, 0.40, Shape::kLog, 0.20},     // EGG
    {160, 10000, 122, Shape::kSqrt, 0.60, Shape::kLinear, 1.60},  // MILK
    {200, 10000, 105, Shape::kLog, 0.20, Shape::kSq, 3.20},       // WOOL
    {100, 10000, 200, Shape::kLinear, 0.40, Shape::kLinear, 0.40},  // FERTILIZER
}};

struct Config {
  int episode_steps = 720;
  int board_size = 10;
  int64_t starting_money = 3000;
  int max_market_orders = 10;   // clamped to >= 1 like the official engine
  int turns_per_day = 24;       // clamped to >= 1
  int64_t shed_capacity = 100;
  double weed_spawn_chance = 0.005;
  int shop_unlock_interval = 3;   // clamped to >= 1
  int shop_sell_interval = 4;     // clamped to >= 1
  int center_sell_interval = 24;  // clamped to >= 1
  int64_t farm_hand_cost_mult = 1;
  std::array<MarketParams, kNumProducts> market_params = kDefaultMarketParams;
};

// --- Tiles -------------------------------------------------------------

enum class TileKind : uint8_t { kEmpty, kLocked, kWeed, kPlant, kStructure };

// Flat tagged record; only the fields of the active kind are meaningful.
// Factories below always start from a default Tile so stale fields are reset,
// mirroring the official engine's dict replacement.
struct Tile {
  TileKind kind = TileKind::kEmpty;
  // PLANT
  int crop = 0;
  int planted_day = 0;
  bool watered_today = false;
  int consecutive_unwatered = 0;
  int max_lifespan_step = -1;
  int fertilized_until_day = -1;
  // PLANT and occupied STRUCTURE
  int yield_units = 0;
  // STRUCTURE
  StructureKind structure = StructureKind::kCoop;
  bool has_animal = false;
  int animal = 0;  // animal index 0..2
  int placed_day = 0;
  bool fed_today = false;
  int consecutive_unfed = 0;
  bool cared_today = false;
  bool fertilizer_available = false;
  int pending_care_bonus = 0;
};

inline Tile MakeLocked() {
  Tile t;
  t.kind = TileKind::kLocked;
  return t;
}

inline Tile MakeWeed() {
  Tile t;
  t.kind = TileKind::kWeed;
  return t;
}

inline Tile MakeBareStructure(StructureKind s) {
  Tile t;
  t.kind = TileKind::kStructure;
  t.structure = s;
  return t;
}

inline Tile MakePlant(int crop, int day, int turns_per_day) {
  const CropData& cd = kCrops[crop];
  Tile t;
  t.kind = TileKind::kPlant;
  t.crop = crop;
  t.planted_day = day;
  t.watered_today = false;
  t.consecutive_unwatered = 1;  // planting day counts as unwatered
  t.yield_units = cd.ongoing ? 0 : 1;
  t.max_lifespan_step = cd.ongoing ? -1 : (day + cd.max_yield_day + 1) * turns_per_day;
  t.fertilized_until_day = -1;
  return t;
}

inline Tile MakeAnimal(int animal, int day) {
  Tile t;
  t.kind = TileKind::kStructure;
  t.structure = kAnimals[animal].structure;
  t.has_animal = true;
  t.animal = animal;
  t.placed_day = day;
  t.yield_units = 0;
  return t;
}

// --- Player / market state ----------------------------------------------

// Per-unit inventory preserving CPython dict insertion order (the order
// matters for shed overflow during DROP / end-of-day drop). Deleting a key
// and re-adding it moves it to the back, exactly like a Python dict.
struct Inventory {
  std::vector<std::pair<int, int64_t>> items;

  int64_t Get(int it) const {
    for (const auto& kv : items) {
      if (kv.first == it) return kv.second;
    }
    return 0;
  }

  void Add(int it, int64_t n) {
    for (auto& kv : items) {
      if (kv.first == it) {
        kv.second += n;
        return;
      }
    }
    items.emplace_back(it, n);
  }

  // `_inv_take`: false when fewer than n held; erases the key at zero.
  bool Take(int it, int64_t n) {
    for (auto iter = items.begin(); iter != items.end(); ++iter) {
      if (iter->first == it) {
        if (iter->second < n) return false;
        iter->second -= n;
        if (iter->second == 0) items.erase(iter);
        return true;
      }
    }
    return false;
  }
};

struct Farm {
  double money = 0.0;
  std::vector<Tile> tiles;  // row-major, tiles[y * board_size + x]
  int farmer_x = 0;
  int farmer_y = 0;
  std::vector<std::pair<int, int>> hands;
  int extra_unlocked = 0;  // count of kLandOrder quadrants bought (NW is free)
  int hires_today = 0;
};

struct PrivateState {
  std::array<int64_t, kNumItems> shed{};
  std::array<int64_t, kNumCrops> seeds{};
  std::vector<Inventory> inventories;  // [0] = main farmer, then hands
};

inline int64_t ShedTotal(const PrivateState& p) {
  int64_t total = 0;
  for (int64_t v : p.shed) total += v;
  return total;
}

struct MarketState {
  std::array<int64_t, kNumProducts> inventory{};
  std::array<int64_t, kNumProducts> prices{};
};

// --- Actions --------------------------------------------------------------

enum class UnitOp : uint8_t {
  kInvalid,  // malformed / unknown: silent no-op
  kNorth,
  kSouth,
  kEast,
  kWest,
  kPass,
  kPickup,
  kDrop,
  kPlace,
  kPlant,
  kWater,
  kHarvest,
  kFertilize,
  kDig,
  kBuildCoop,
  kBuildPasture,
  kFeed,
  kCollectFertilizer,
  kCare,
};

struct UnitAction {
  UnitOp op = UnitOp::kPass;
  // PICKUP/PLACE: item index (0..11); PLANT: crop index (0..4).
  int arg = -1;
  int64_t n = 1;  // count for PICKUP/PLACE (defaults to 1 when absent)
};

enum class OrderKind : uint8_t { kBuySeed, kBuyProduct, kBuyAnimal, kSell, kHire, kBuyLand };

struct MarketOrder {
  OrderKind kind = OrderKind::kHire;
  // kBuySeed: crop index; kSell/kBuyProduct: product index; kBuyAnimal:
  // animal index. Unused for kHire/kBuyLand.
  int item = 0;
  int64_t remaining = 0;
};

struct PlayerAction {
  UnitAction farmer{UnitOp::kPass, -1, 1};
  std::vector<UnitAction> hands;
  // Order slots, already truncated to maxMarketOrdersPerTurn. An empty slot
  // is a malformed order that keeps its queue index but does nothing.
  std::vector<std::optional<MarketOrder>> market;
};

// --- Board geometry -------------------------------------------------------

// Quadrant index: NW=0, NE=1, SW=2, SE=3.
inline int QuadrantOf(int x, int y, int board_size) {
  const int half = board_size / 2;
  return (y < half ? 0 : 2) + (x < half ? 0 : 1);
}

// Four inner-corner tiles around the shed, in NWSE order.
inline std::array<std::pair<int, int>, 4> ShedAccessTiles(int board_size) {
  const int half = board_size / 2;
  return {{{half - 1, half - 1}, {half, half - 1}, {half - 1, half}, {half, half}}};
}

inline bool IsShedAdjacent(int x, int y, int board_size) {
  for (const auto& [tx, ty] : ShedAccessTiles(board_size)) {
    if (tx == x && ty == y) return true;
  }
  return false;
}

// First shed-access tile inside NW; falls back to (0, 0).
inline std::pair<int, int> DefaultSpawn(int board_size) {
  for (const auto& tile : ShedAccessTiles(board_size)) {
    if (QuadrantOf(tile.first, tile.second, board_size) == 0) return tile;
  }
  return {0, 0};
}

}  // namespace kagg
