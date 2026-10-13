// Construct policy-native C++ values directly from Engine; no Python objects.
#include "opponents/compiled/policy.hpp"

namespace kagg::opponents::compiled {
namespace {
Value TileValue(const Tile& tile) {
  if (tile.kind == TileKind::kEmpty) return {};
  if (tile.kind == TileKind::kLocked) return "LOCKED";
  if (tile.kind == TileKind::kWeed) return Dict({{"kind", "WEED"}});
  if (tile.kind == TileKind::kPlant)
    return Dict({{"kind", "PLANT"},
                 {"crop", kItemNames[tile.crop]},
                 {"planted_day", tile.planted_day},
                 {"watered_today", tile.watered_today},
                 {"consecutive_unwatered", tile.consecutive_unwatered},
                 {"yield_units", tile.yield_units},
                 {"max_lifespan_step", tile.max_lifespan_step},
                 {"fertilized_until_day", tile.fertilized_until_day}});
  auto value = Dict(
      {{"kind", tile.structure == StructureKind::kCoop ? "COOP" : "PASTURE"}});
  if (tile.has_animal) {
    Put(value, "animal", kItemNames[item::kGoose + tile.animal]);
    Put(value, "placed_day", tile.placed_day);
    Put(value, "yield_units", tile.yield_units);
    Put(value, "consecutive_unfed", tile.consecutive_unfed);
    Put(value, "fed_today", tile.fed_today);
    Put(value, "cared_today", tile.cared_today);
    Put(value, "fertilizer_available", tile.fertilizer_available);
    Put(value, "pending_care_bonus", tile.pending_care_bonus);
  }
  return value;
}
Value FarmValue(const Farm& farm, int size) {
  Values rows, hands, quadrants{"NW"};
  for (int y = 0; y < size; ++y) {
    Values row;
    for (int x = 0; x < size; ++x)
      row.push_back(TileValue(farm.tiles[y * size + x]));
    rows.push_back(List(std::move(row)));
  }
  for (const auto& [x, y] : farm.hands) hands.push_back(List({x, y}));
  for (int i = 0; i < farm.extra_unlocked; ++i)
    quadrants.emplace_back(kQuadrantNames[kLandOrder[i]]);
  return Dict({{"money", farm.money},
               {"tiles", List(std::move(rows))},
               {"farmer", List({farm.farmer_x, farm.farmer_y})},
               {"hands", List(std::move(hands))},
               {"unlocked_quadrants", List(std::move(quadrants))},
               {"hires_today", farm.hires_today}});
}
Value PrivateValue(const PrivateState& state) {
  auto shed = Dict(), seeds = Dict();
  Values inventories;
  for (int i = 0; i < kNumItems; ++i) Put(shed, kItemNames[i], state.shed[i]);
  for (int i = 0; i < kNumCrops; ++i) Put(seeds, kItemNames[i], state.seeds[i]);
  for (const auto& source : state.inventories) {
    auto inventory = Dict();
    for (const auto& [item, n] : source.items)
      Put(inventory, kItemNames[item], n);
    inventories.push_back(inventory);
  }
  return Dict({{"shed", shed},
               {"seeds", seeds},
               {"inventories", List(std::move(inventories))}});
}
}  // namespace
Value Observation(const Engine& engine, int player) {
  auto inventory = Dict(), prices = Dict();
  Values shops;
  for (int i = 0; i < kNumProducts; ++i) {
    Put(inventory, kItemNames[i], engine.market().inventory[i]);
    Put(prices, kItemNames[i], engine.market().prices[i]);
  }
  for (int shop : engine.town_shops()) shops.emplace_back(kShops[shop].name);
  return Dict(
      {{"player", player},
       {"step", engine.step_index()},
       {"day", engine.step_index() / engine.config().turns_per_day},
       {"hour", engine.step_index() % engine.config().turns_per_day},
       {"farms", List({FarmValue(engine.farm(0), engine.config().board_size),
                       FarmValue(engine.farm(1), engine.config().board_size)})},
       {"private", PrivateValue(engine.priv(player))},
       {"market", Dict({{"inventory", inventory}, {"prices", prices}})},
       {"town", Dict({{"unlocked_shops", List(std::move(shops))}})}});
}
Value Configuration(const Config& cfg) {
  return Dict({{"episodeSteps", cfg.episode_steps},
               {"boardSize", cfg.board_size},
               {"startingMoney", cfg.starting_money},
               {"maxMarketOrdersPerTurn", cfg.max_market_orders},
               {"turnsPerDay", cfg.turns_per_day},
               {"shedCapacity", cfg.shed_capacity},
               {"weedSpawnChance", cfg.weed_spawn_chance},
               {"townShopUnlockInterval", cfg.shop_unlock_interval},
               {"townShopSellInterval", cfg.shop_sell_interval},
               {"townCenterSellInterval", cfg.center_sell_interval},
               {"farmHandCostMult", cfg.farm_hand_cost_mult}});
}
}  // namespace kagg::opponents::compiled
