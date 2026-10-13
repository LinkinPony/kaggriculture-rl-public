#include "kaito_v48_support.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <limits>
#include <numeric>
#include <utility>
#include <vector>

#include "market_phase.hpp"

namespace kagg::kaito {
namespace {

constexpr int kFixedShedCapacity = 100;
constexpr int kMaximumOrders = 10;
constexpr std::array<int, kNumProducts> kSellable = {
    item::kStrawberry, item::kMelon, item::kMilk,
    item::kWool,       item::kEgg,   item::kTomato,
    item::kCarrot,     item::kWheat, item::kFertilizer,
};
constexpr std::array<double, kNumProducts> kGlutWeight = {
    1.0, 1.0, 1.3, 2.0, 3.6, 1.5, 2.0, 3.2, 1.0,
};

UnitAction Pass() { return UnitAction{UnitOp::kPass, -1, 1}; }

bool IsSell(const std::optional<MarketOrder>& slot) {
  return slot.has_value() && slot->kind == OrderKind::kSell &&
         slot->item >= 0 && slot->item < kNumProducts;
}

double ImpactScore(const Engine& engine,
                   const std::optional<MarketOrder>& slot) {
  if (!IsSell(slot)) return -std::numeric_limits<double>::infinity();
  const int product = slot->item;
  const int64_t quantity = std::max<int64_t>(0, slot->remaining);
  const int64_t inventory = engine.market().inventory[product];
  const double current_quote = engine.market().prices[product];
  // The notebook froze the default market table instead of consulting the
  // resolved profile here. Config{} is that same table.
  static const Config kFrozenMarketConfig;
  const double later_quote =
      ComputeMarketPrice(kFrozenMarketConfig, product, inventory + quantity);
  return static_cast<double>(quantity) *
         std::max(0.0, current_quote - later_quote);
}

std::array<double, kNumProducts> DemandPerDay(const Engine& engine) {
  const Config& config = engine.config();
  std::array<double, kNumProducts> demand{};
  const double shop_ticks = static_cast<double>(config.turns_per_day) /
                            std::max(1, config.shop_sell_interval);
  for (const int shop : engine.town_shops()) {
    const ShopData& data = kShops[shop];
    const int multiplier = data.n_products == 1 ? 2 : 1;
    for (int index = 0; index < data.n_products; ++index) {
      demand[data.products[index]] += shop_ticks * multiplier;
    }
  }
  const bool rebalance = config.center_sell_interval >= 24;
  const int day = engine.step_index() / std::max(1, config.turns_per_day);
  const int center_multiplier =
      rebalance ? 1 : (day >= 20 ? 4 : (day >= 10 ? 2 : 1));
  const double center_ticks = static_cast<double>(config.turns_per_day) /
                              std::max(1, config.center_sell_interval);
  for (int product = 0; product < kNumProducts; ++product) {
    if (product != item::kFertilizer) {
      demand[product] += center_ticks * center_multiplier;
    }
  }
  return demand;
}

double DemandAdjustedScore(const Engine& engine,
                           const std::optional<MarketOrder>& slot,
                           double alpha,
                           const std::array<double, kNumProducts>& demand) {
  const double score = ImpactScore(engine, slot);
  if (score <= 0.0 || !IsSell(slot)) return score;
  const int product = slot->item;
  const int64_t quantity = std::max<int64_t>(0, slot->remaining);
  const double recovery =
      std::max<int64_t>(0, engine.market().inventory[product] + quantity - 10000) /
      std::max(0.25, demand[product]);
  const double urgency = std::min(1.0, recovery / 10.0);
  return score * (1.0 + std::max(0.0, alpha) * urgency);
}

struct PublicSignature {
  int hands = 0;
  int unlocked = 0;
  std::array<int, 11> counts{};
};

PublicSignature Signature(const Farm& farm) {
  PublicSignature result;
  result.hands = static_cast<int>(farm.hands.size());
  result.unlocked = farm.extra_unlocked + 1;
  for (const Tile& tile : farm.tiles) {
    if (tile.kind == TileKind::kPlant) {
      result.counts[tile.crop] += 1;
    } else if (tile.kind == TileKind::kStructure && tile.has_animal) {
      // WHEAT..MELON occupy 0..4; COW, SHEEP, GOOSE occupy 5..7.
      const int animal_slot = tile.animal == 1 ? 5 : (tile.animal == 2 ? 6 : 7);
      result.counts[animal_slot] += 1;
    } else if (tile.kind == TileKind::kStructure) {
      result.counts[tile.structure == StructureKind::kPasture ? 8 : 9] += 1;
    } else if (tile.kind == TileKind::kWeed) {
      result.counts[10] += 1;
    }
  }
  return result;
}

void Deposit(int item_index, int64_t quantity,
             std::array<int64_t, kNumItems>* shed) {
  const int64_t total =
      std::accumulate(shed->begin(), shed->end(), int64_t{0});
  const int64_t room = std::max<int64_t>(0, kFixedShedCapacity - total);
  const int64_t deposited = std::min(std::max<int64_t>(0, quantity), room);
  if (item_index >= 0 && item_index < kNumItems && deposited > 0) {
    (*shed)[item_index] += deposited;
  }
}

}  // namespace

AssetCounts PublicAssetCounts(const Farm& farm) {
  AssetCounts result;
  for (const Tile& tile : farm.tiles) {
    if (tile.kind == TileKind::kPlant) {
      if (tile.crop == item::kMelon) ++result.melon;
      if (tile.crop == item::kWheat) ++result.wheat;
      if (tile.crop == item::kStrawberry) ++result.strawberry;
    }
    if (tile.kind == TileKind::kStructure && tile.has_animal) {
      if (tile.animal == 0) ++result.goose;
      if (tile.animal == 1) ++result.cow;
      if (tile.animal == 2) ++result.sheep;
    }
  }
  return result;
}

double CloneDistance(const Engine& engine) {
  const PublicSignature left = Signature(engine.farm(0));
  const PublicSignature right = Signature(engine.farm(1));
  int distance = std::abs(left.hands - right.hands) +
                 3 * std::abs(left.unlocked - right.unlocked);
  for (size_t index = 0; index < left.counts.size(); ++index) {
    distance += std::abs(left.counts[index] - right.counts[index]);
  }
  return distance;
}

void AlignHands(const Engine& engine, int player, PlayerAction* action) {
  action->hands.resize(engine.farm(player).hands.size(), Pass());
}

void ReorderSellSlots(const Engine& engine, PlayerAction* action,
                      double demand_alpha) {
  struct RankedSell {
    double score;
    size_t original_index;
    std::optional<MarketOrder> order;
  };
  const auto demand = demand_alpha > 0.0
                          ? DemandPerDay(engine)
                          : std::array<double, kNumProducts>{};
  std::vector<RankedSell> sells;
  for (size_t index = 0; index < action->market.size(); ++index) {
    const auto& slot = action->market[index];
    if (!IsSell(slot)) continue;
    const double score =
        demand_alpha > 0.0
            ? DemandAdjustedScore(engine, slot, demand_alpha, demand)
            : ImpactScore(engine, slot);
    sells.push_back(RankedSell{score, index, slot});
  }
  if (sells.size() < 2) return;
  std::sort(sells.begin(), sells.end(), [](const RankedSell& left,
                                           const RankedSell& right) {
    if (left.score != right.score) return left.score > right.score;
    return left.original_index < right.original_index;
  });
  size_t ranked = 0;
  for (auto& slot : action->market) {
    if (IsSell(slot)) slot = sells[ranked++].order;
  }
}

std::array<int64_t, kNumItems> ProjectedShed(const Engine& engine, int player,
                                             const PlayerAction& action) {
  std::array<int64_t, kNumItems> projected = engine.priv(player).shed;
  const Farm& farm = engine.farm(player);
  const PrivateState& priv = engine.priv(player);
  const auto access = ShedAccessTiles(engine.config().board_size);
  const int unit_count = 1 + static_cast<int>(farm.hands.size());
  for (int unit = 0; unit < unit_count; ++unit) {
    if (unit >= static_cast<int>(priv.inventories.size())) continue;
    const int x = unit == 0 ? farm.farmer_x : farm.hands[unit - 1].first;
    const int y = unit == 0 ? farm.farmer_y : farm.hands[unit - 1].second;
    if (std::find(access.begin(), access.end(), std::pair{x, y}) == access.end()) {
      continue;
    }
    if (x < 0 || y < 0 || x >= engine.config().board_size ||
        y >= engine.config().board_size) {
      continue;
    }
    const UnitAction& request = unit == 0 ? action.farmer : action.hands[unit - 1];
    const Inventory& inventory = priv.inventories[unit];
    if (request.op == UnitOp::kDrop) {
      for (const auto& [item_index, quantity] : inventory.items) {
        Deposit(item_index, quantity, &projected);
      }
      continue;
    }
    if (request.op != UnitOp::kPlace || request.arg < 0 ||
        request.arg >= kNumItems) {
      continue;
    }
    const int item_index = request.arg;
    if (item_index >= item::kGoose) {
      const int animal = item_index - item::kGoose;
      const Tile& tile =
          farm.tiles[static_cast<size_t>(y) * engine.config().board_size + x];
      if (tile.kind == TileKind::kStructure && !tile.has_animal &&
          tile.structure == kAnimals[animal].structure) {
        continue;
      }
    }
    Deposit(item_index,
            std::min(std::max<int64_t>(0, request.n), inventory.Get(item_index)),
            &projected);
  }
  return projected;
}

void ReplaceTerminalMarket(const Engine& engine, int player,
                           PlayerAction* action) {
  AlignHands(engine, player, action);
  const auto shed = ProjectedShed(engine, player, *action);
  std::array<double, kNumProducts> exposure{};
  for (const Tile& tile : engine.farm(1 - player).tiles) {
    if (tile.kind == TileKind::kPlant && tile.crop < kNumProducts) {
      exposure[tile.crop] += std::max(1, tile.yield_units);
    }
    if (tile.kind == TileKind::kStructure && tile.has_animal) {
      const int product = kAnimals[tile.animal].product;
      exposure[product] += 1.0 + std::max(0, tile.yield_units);
    }
    if (tile.kind == TileKind::kStructure && tile.fertilizer_available) {
      exposure[item::kFertilizer] += 1.0;
    }
  }
  struct Liquidation {
    double score;
    int priority;
    int product;
    int64_t quantity;
  };
  std::vector<Liquidation> rows;
  for (size_t priority = 0; priority < kSellable.size(); ++priority) {
    const int product = kSellable[priority];
    const int64_t quantity = std::max<int64_t>(0, shed[product]);
    if (quantity <= 0) continue;
    const double price = std::max<int64_t>(1, engine.market().prices[product]);
    const double score = (1.0 + exposure[product]) * kGlutWeight[product] *
                         price * std::log1p(static_cast<double>(quantity));
    rows.push_back(
        Liquidation{score, -static_cast<int>(priority), product, quantity});
  }
  std::sort(rows.begin(), rows.end(), [](const Liquidation& left,
                                         const Liquidation& right) {
    if (left.score != right.score) return left.score > right.score;
    return left.priority > right.priority;
  });
  action->market.clear();
  const size_t limit = std::min<size_t>(kMaximumOrders, rows.size());
  action->market.reserve(limit);
  for (size_t index = 0; index < limit; ++index) {
    const Liquidation& row = rows[index];
    action->market.push_back(
        MarketOrder{OrderKind::kSell, row.product, row.quantity});
  }
}

}  // namespace kagg::kaito
