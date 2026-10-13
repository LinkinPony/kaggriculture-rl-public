#include "kaito_v39/market.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <limits>
#include <numeric>
#include <optional>
#include <utility>
#include <vector>

#include "market_phase.hpp"
#include "types.hpp"

namespace kagg::kaito_v39 {
namespace {

constexpr int kMaximumOrders = 10;
constexpr int kMaximumBatch = 10;
constexpr int kFixedShedCapacity = 100;
constexpr int kShedHeadroom = 10;
constexpr double kCashReserve = 500.0;
constexpr double kCostBuffer = 1.05;
constexpr std::array<int64_t, 3> kFrozenLandCosts = {1000, 2000, 4000};

const Config& FrozenMarketConfig() {
  static const Config config = [] {
    Config value;
    value.market_params = {{
        {25, 10000, 400, Shape::kSqrt, 0.80, Shape::kLog, 0.20},
        {35, 10000, 450, Shape::kLog, 0.20, Shape::kSqrt, 0.70},
        {60, 10000, 200, Shape::kLinear, 0.40, Shape::kSqrt, 0.60},
        {120, 10000, 100, Shape::kSqrt, 0.70, Shape::kLinear, 1.60},
        {250, 10000, 300, Shape::kLog, 0.20, Shape::kSq, 3.60},
        {50, 10000, 332, Shape::kLinear, 0.40, Shape::kLog, 0.20},
        {160, 10000, 122, Shape::kSqrt, 0.60, Shape::kLinear, 1.60},
        {200, 10000, 105, Shape::kLog, 0.20, Shape::kSq, 3.20},
        {100, 10000, 200, Shape::kLinear, 0.40, Shape::kLinear, 0.40},
    }};
    return value;
  }();
  return config;
}

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
  const double later_quote =
      ComputeMarketPrice(FrozenMarketConfig(), product, inventory + quantity);
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
  const double excess = std::max<int64_t>(
      0, engine.market().inventory[product] + quantity - 10000);
  const double recovery = excess / std::max(0.25, demand[product]);
  const double urgency = std::min(1.0, recovery / 10.0);
  return score * (1.0 + std::max(0.0, alpha) * urgency);
}

int64_t Take(Inventory* inventory, int item_index, int64_t requested) {
  requested = std::max<int64_t>(0, requested);
  for (auto iterator = inventory->items.begin();
       iterator != inventory->items.end(); ++iterator) {
    if (iterator->first != item_index) continue;
    const int64_t taken = std::min(requested, std::max<int64_t>(0, iterator->second));
    iterator->second -= taken;
    if (iterator->second == 0) inventory->items.erase(iterator);
    return taken;
  }
  return 0;
}

void Deposit(std::array<int64_t, kNumItems>* shed, int item_index,
             int64_t quantity, int64_t capacity) {
  const int64_t total =
      std::accumulate(shed->begin(), shed->end(), int64_t{0});
  const int64_t room = std::max<int64_t>(0, capacity - total);
  const int64_t deposited = std::min(std::max<int64_t>(0, quantity), room);
  if (item_index >= 0 && item_index < kNumItems && deposited > 0) {
    (*shed)[item_index] += deposited;
  }
}

struct PrivateProjection {
  std::array<int64_t, kNumItems> shed{};
  std::vector<Inventory> inventories;
};

PrivateProjection ProjectAfterActor(const Engine& engine, int player,
                                    const PlayerAction& action,
                                    int64_t shed_capacity) {
  PrivateProjection result;
  result.shed = engine.priv(player).shed;
  result.inventories = engine.priv(player).inventories;
  const Farm& farm = engine.farm(player);
  const auto access = ShedAccessTiles(engine.config().board_size);
  const int units = 1 + static_cast<int>(farm.hands.size());
  while (static_cast<int>(result.inventories.size()) < units) {
    result.inventories.emplace_back();
  }
  for (int unit = 0; unit < units; ++unit) {
    const int x = unit == 0 ? farm.farmer_x : farm.hands[unit - 1].first;
    const int y = unit == 0 ? farm.farmer_y : farm.hands[unit - 1].second;
    if (x < 0 || y < 0 || x >= engine.config().board_size ||
        y >= engine.config().board_size) {
      continue;
    }
    const Tile& tile =
        farm.tiles[static_cast<size_t>(y) * engine.config().board_size + x];
    if (tile.kind == TileKind::kLocked) continue;
    const bool at_shed =
        std::find(access.begin(), access.end(), std::pair{x, y}) != access.end();
    const UnitAction& request =
        unit == 0 ? action.farmer : action.hands[unit - 1];
    Inventory& inventory = result.inventories[unit];
    if (request.op == UnitOp::kDrop && at_shed) {
      for (const auto& [item_index, quantity] : inventory.items) {
        Deposit(&result.shed, item_index, quantity, shed_capacity);
      }
      inventory.items.clear();
      continue;
    }
    if (request.op == UnitOp::kPickup && at_shed && request.arg >= 0 &&
        request.arg < kNumItems) {
      const int64_t taken = std::min(
          std::max<int64_t>(0, request.n), result.shed[request.arg]);
      result.shed[request.arg] -= taken;
      if (taken > 0) inventory.Add(request.arg, taken);
      continue;
    }
    if (request.op == UnitOp::kPlace && request.arg >= 0 &&
        request.arg < kNumItems) {
      if (request.arg >= item::kGoose) {
        const int animal = request.arg - item::kGoose;
        if (tile.kind == TileKind::kStructure && !tile.has_animal &&
            tile.structure == kAnimals[animal].structure) {
          Take(&inventory, request.arg, 1);
          continue;
        }
      }
      if (!at_shed) continue;
      const int64_t total =
          std::accumulate(result.shed.begin(), result.shed.end(), int64_t{0});
      const int64_t room = std::max<int64_t>(0, shed_capacity - total);
      const int64_t deposited =
          Take(&inventory, request.arg,
               std::min(std::max<int64_t>(0, request.n), room));
      if (deposited > 0) result.shed[request.arg] += deposited;
      continue;
    }
    if (request.op == UnitOp::kFeed && tile.kind == TileKind::kStructure &&
        tile.has_animal && !tile.fed_today) {
      Take(&inventory, item::kWheat, 1);
    }
  }
  return result;
}

std::array<int64_t, kNumItems> ShedAfterMarket(
    std::array<int64_t, kNumItems> shed,
    const std::vector<std::optional<MarketOrder>>& market,
    int64_t shed_capacity) {
  for (const auto& slot : market) {
    if (!slot.has_value()) continue;
    const MarketOrder& order = *slot;
    const int64_t quantity = std::max<int64_t>(0, order.remaining);
    if (order.kind == OrderKind::kSell && order.item >= 0 &&
        order.item < kNumProducts) {
      shed[order.item] = std::max<int64_t>(0, shed[order.item] - quantity);
    } else if (order.kind == OrderKind::kBuyProduct && order.item >= 0 &&
               order.item < kNumProducts) {
      Deposit(&shed, order.item, quantity, shed_capacity);
    } else if (order.kind == OrderKind::kBuyAnimal && order.item >= 0 &&
               order.item < kNumAnimals) {
      Deposit(&shed, item::kGoose + order.item, quantity, shed_capacity);
    }
  }
  return shed;
}

int64_t WheatAfterMarket(
    int64_t quantity, const std::vector<std::optional<MarketOrder>>& market) {
  quantity = std::max<int64_t>(0, quantity);
  for (const auto& slot : market) {
    if (!slot.has_value() || slot->item != item::kWheat) continue;
    const int64_t units = std::max<int64_t>(0, slot->remaining);
    if (slot->kind == OrderKind::kSell) {
      quantity = std::max<int64_t>(0, quantity - units);
    } else if (slot->kind == OrderKind::kBuyProduct) {
      quantity += units;
    }
  }
  return quantity;
}

std::pair<int64_t, int64_t> ExecuteBuy(int64_t inventory,
                                       int64_t quantity) {
  int64_t cost = 0;
  for (int64_t unit = 0; unit < std::max<int64_t>(0, quantity); ++unit) {
    cost += ComputeMarketPrice(FrozenMarketConfig(), item::kWheat,
                               inventory - 1);
    --inventory;
  }
  return {cost, inventory};
}

std::pair<int64_t, int64_t> ExecuteSell(int64_t inventory,
                                        int64_t quantity) {
  int64_t revenue = 0;
  for (int64_t unit = 0; unit < std::max<int64_t>(0, quantity); ++unit) {
    const int64_t quote =
        ComputeMarketPrice(FrozenMarketConfig(), item::kWheat, inventory);
    revenue += quote;
    if (quote > 1) ++inventory;
  }
  return {revenue, inventory};
}

int64_t InventoryAfterWheatOrders(
    int64_t inventory,
    const std::vector<std::optional<MarketOrder>>& market) {
  for (const auto& slot : market) {
    if (!slot.has_value() || slot->item != item::kWheat) continue;
    const int64_t quantity = std::max<int64_t>(0, slot->remaining);
    if (slot->kind == OrderKind::kSell) {
      inventory = ExecuteSell(inventory, quantity).second;
    } else if (slot->kind == OrderKind::kBuyProduct) {
      inventory = ExecuteBuy(inventory, quantity).second;
    }
  }
  return inventory;
}

uint64_t Fib(int index) {
  uint64_t a = 1;
  uint64_t b = 1;
  for (int count = 0; count < std::max(0, index); ++count) {
    const uint64_t next = a + b;
    a = b;
    b = next;
  }
  return a;
}

double RouteInvestmentCost(const Portfolio& portfolio, const Engine& engine,
                           int player, Route route, double item_price) {
  const int start = engine.step_index();
  const int stop = std::min(kRouteTurns, start + 2);
  int hires_today = engine.farm(player).hires_today;
  int quadrants = engine.farm(player).extra_unlocked + 1;
  int last_day = start / std::max(1, engine.config().turns_per_day);
  double total = 0.0;
  for (int step = start; step < stop; ++step) {
    const int day = step / 24;
    if (day != last_day) {
      hires_today = 0;
      last_day = day;
    }
    for (const auto& slot : portfolio.action(route, step).market) {
      if (!slot.has_value()) continue;
      const MarketOrder& order = *slot;
      const int64_t quantity = std::max<int64_t>(0, order.remaining);
      switch (order.kind) {
        case OrderKind::kHire:
          total += static_cast<double>(engine.config().farm_hand_cost_mult) *
                   Fib(hires_today);
          ++hires_today;
          break;
        case OrderKind::kBuyLand: {
          const int extra = std::max(0, quadrants - 1);
          const int64_t cost =
              extra < static_cast<int>(kFrozenLandCosts.size())
                  ? kFrozenLandCosts[extra]
                  : 0;
          total += cost;
          quadrants += cost > 0;
          break;
        }
        case OrderKind::kBuySeed:
          if (order.item >= 0 && order.item < kNumCrops) {
            total += kCrops[order.item].seed_cost * quantity;
          }
          break;
        case OrderKind::kBuyAnimal:
          if (order.item >= 0 && order.item < kNumAnimals) {
            total += kAnimals[order.item].cost * quantity;
          }
          break;
        case OrderKind::kBuyProduct:
          total += std::max(1.0, item_price) * quantity;
          break;
        case OrderKind::kSell:
          break;
      }
    }
  }
  return total;
}

int AnimalCount(const Farm& farm) {
  return std::count_if(farm.tiles.begin(), farm.tiles.end(), [](const Tile& tile) {
    return tile.kind == TileKind::kStructure && tile.has_animal;
  });
}

double AvailableCash(const Portfolio& portfolio, const Engine& engine,
                     int player, Route route, const PlayerAction& action,
                     const PrivateProjection& projection) {
  int64_t protected_wheat = projection.shed[item::kWheat];
  for (const Inventory& inventory : projection.inventories) {
    protected_wheat += std::max<int64_t>(0, inventory.Get(item::kWheat));
  }
  for (const auto& slot : action.market) {
    if (slot.has_value() && slot->kind == OrderKind::kSell &&
        slot->item == item::kWheat) {
      protected_wheat =
          std::max<int64_t>(0, protected_wheat -
                                   std::max<int64_t>(0, slot->remaining));
    }
  }
  const int64_t required_feed =
      static_cast<int64_t>(std::ceil(AnimalCount(engine.farm(player)) * 2.0));
  const int64_t deficit = std::max<int64_t>(0, required_feed - protected_wheat);
  const int64_t inventory = engine.market().inventory[item::kWheat];
  const double feed = ExecuteBuy(inventory, deficit).first * kCostBuffer;
  const double quote =
      ComputeMarketPrice(FrozenMarketConfig(), item::kWheat, inventory);
  const double investment =
      RouteInvestmentCost(portfolio, engine, player, route, quote) * kCostBuffer;
  return std::max(0.0, engine.farm(player).money - kCashReserve - feed -
                           investment);
}

int DemandNow(const Engine& engine) {
  const Config& config = engine.config();
  const int step = engine.step_index();
  int demand = 0;
  if (step % std::max(1, config.shop_sell_interval) == 0) {
    for (const int shop : engine.town_shops()) {
      const ShopData& data = kShops[shop];
      if (std::find(data.products.begin(),
                    data.products.begin() + data.n_products,
                    item::kWheat) != data.products.begin() + data.n_products) {
        demand += data.n_products == 1 ? 2 : 1;
      }
    }
  }
  if (step % std::max(1, config.center_sell_interval) == 0) {
    if (config.center_sell_interval >= 24) {
      ++demand;
    } else {
      const int day = step / std::max(1, config.turns_per_day);
      demand += day >= 20 ? 4 : (day >= 10 ? 2 : 1);
    }
  }
  return demand;
}

struct RoundTrip {
  int quantity = 0;
  int64_t cost = 0;
  int64_t revenue = 0;
  double profit = 0.0;
};

std::optional<RoundTrip> BestRoundTrip(int64_t inventory, int demand,
                                       int maximum) {
  std::optional<RoundTrip> best;
  for (int quantity = 1; quantity <= std::max(0, maximum); ++quantity) {
    const auto [cost, after_buy] = ExecuteBuy(inventory, quantity);
    const auto [revenue, ignored] =
        ExecuteSell(after_buy - std::max(0, demand), quantity);
    (void)ignored;
    RoundTrip candidate{quantity, cost, revenue,
                        static_cast<double>(revenue - cost)};
    if (!best.has_value() || candidate.profit > best->profit ||
        (candidate.profit == best->profit &&
         candidate.quantity < best->quantity)) {
      best = candidate;
    }
  }
  if (!best.has_value() || best->profit < 1.0) return std::nullopt;
  return best;
}

}  // namespace

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

PlayerAction ApplyMarketMaker(const Portfolio& portfolio,
                              const Engine& engine, int player, Route route,
                              PlayerAction action, MarketMakerState* state) {
  const int step = engine.step_index();
  if (step == 0 || !state->initialized || step < state->last_step) {
    *state = MarketMakerState{};
    state->initialized = true;
    state->last_step = step;
  }
  state->last_step = step;
  const int maximum_orders =
      std::min(kMaximumOrders, std::max(1, engine.config().max_market_orders));
  const int64_t effective_capacity = std::min<int64_t>(
      kFixedShedCapacity, std::max<int64_t>(1, engine.config().shed_capacity));

  if (state->open_units > 0) {
    if (static_cast<int>(action.market.size()) >= maximum_orders) return action;
    const int64_t observed_wheat =
        std::max<int64_t>(0, engine.priv(player).shed[item::kWheat]);
    const PrivateProjection projection =
        ProjectAfterActor(engine, player, action, effective_capacity);
    const int64_t projected_wheat =
        std::max<int64_t>(0, projection.shed[item::kWheat]);
    const int64_t actor_delta = projected_wheat - observed_wheat;
    int64_t operational =
        std::max<int64_t>(0, state->baseline_wheat + actor_delta);
    operational = WheatAfterMarket(operational, action.market);
    const int64_t total = WheatAfterMarket(projected_wheat, action.market);
    const int64_t available_position = std::max<int64_t>(0, total - operational);
    const int64_t quantity =
        std::min<int64_t>(state->open_units, available_position);
    if (quantity <= 0) {
      state->open_units = 0;
      state->baseline_wheat = operational;
      return action;
    }
    action.market.push_back(
        MarketOrder{OrderKind::kSell, item::kWheat, quantity});
    state->open_units = 0;
    state->baseline_wheat = operational;
    return action;
  }

  if (step < 72 || step > 716) return action;
  const int demand = DemandNow(engine);
  if (demand <= 0) return action;
  if (static_cast<int>(action.market.size()) >= maximum_orders ||
      step + 1 >= kRouteTurns ||
      static_cast<int>(portfolio.action(route, step + 1).market.size()) >=
          maximum_orders) {
    return action;
  }
  const PrivateProjection projection =
      ProjectAfterActor(engine, player, action, effective_capacity);
  const auto after_base =
      ShedAfterMarket(projection.shed, action.market, effective_capacity);
  const int64_t total =
      std::accumulate(after_base.begin(), after_base.end(), int64_t{0});
  const int capacity = static_cast<int>(std::max<int64_t>(
      0, effective_capacity - kShedHeadroom - total));
  if (capacity <= 0) return action;
  const double available = AvailableCash(portfolio, engine, player, route,
                                         action, projection);
  if (available <= 0.0) return action;

  int64_t inventory = engine.market().inventory[item::kWheat];
  inventory = InventoryAfterWheatOrders(inventory, action.market);
  const int maximum = std::min(kMaximumBatch, capacity);
  int affordable = 0;
  for (int quantity = 1; quantity <= maximum; ++quantity) {
    const int64_t cost = ExecuteBuy(inventory, quantity).first;
    if (cost * kCostBuffer > available) break;
    affordable = quantity;
  }
  if (affordable <= 0) return action;
  const std::optional<RoundTrip> plan =
      BestRoundTrip(inventory, demand, affordable);
  if (!plan.has_value()) return action;

  action.market.push_back(MarketOrder{OrderKind::kBuyProduct, item::kWheat,
                                     plan->quantity});
  state->open_units = plan->quantity;
  state->entry_step = step;
  state->baseline_wheat =
      WheatAfterMarket(std::max<int64_t>(
                           0, projection.shed[item::kWheat]),
                       std::vector<std::optional<MarketOrder>>(
                           action.market.begin(), action.market.end() - 1));
  return action;
}

}  // namespace kagg::kaito_v39
