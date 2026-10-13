#include "mugundh/detail.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <limits>
#include <numeric>
#include <optional>
#include <utility>
#include <vector>

namespace kagg::mugundh::detail {
namespace {

constexpr int kMaximumOrders = 10;
constexpr int kPreemptStart = 120;
constexpr int kPreemptStop = 680;
constexpr int kPreemptMaximumBatch = 12;
constexpr int kPreemptMaximumCloneDistance = 6;
constexpr int kPreemptMinimumFutureQuantity = 4;
constexpr double kDemandAlpha = 0.25;

constexpr std::array<int, 4> kPremium = {
    item::kStrawberry, item::kMelon, item::kMilk, item::kWool};
constexpr std::array<int, 4> kCounterItems = {
    item::kMelon, item::kMilk, item::kStrawberry, item::kWool};
constexpr std::array<int, kNumProducts> kLiquidationOrder = {
    item::kCarrot, item::kEgg,        item::kFertilizer,
    item::kMelon,  item::kMilk,       item::kStrawberry,
    item::kTomato, item::kWheat,      item::kWool,
};

enum class FrozenShape : uint8_t { kLinear, kSq, kSqrt, kLog };

struct FrozenMarketParams {
  double base;
  int64_t equilibrium;
  double scale;
  FrozenShape below_shape;
  double below_target;
  FrozenShape above_shape;
  double above_target;
};

constexpr std::array<FrozenMarketParams, kNumProducts> kFrozenMarket = {{
    {25, 10000, 400, FrozenShape::kSqrt, 0.8, FrozenShape::kLog, 0.2},
    {35, 10000, 450, FrozenShape::kLog, 0.2, FrozenShape::kSqrt, 0.7},
    {60, 10000, 200, FrozenShape::kLinear, 0.4, FrozenShape::kSqrt, 0.6},
    {120, 10000, 100, FrozenShape::kSqrt, 0.7, FrozenShape::kLinear, 1.6},
    {250, 10000, 300, FrozenShape::kLog, 0.2, FrozenShape::kSq, 3.6},
    {50, 10000, 332, FrozenShape::kLinear, 0.4, FrozenShape::kLog, 0.2},
    {160, 10000, 122, FrozenShape::kSqrt, 0.6, FrozenShape::kLinear, 1.6},
    {200, 10000, 105, FrozenShape::kLog, 0.2, FrozenShape::kSq, 3.2},
    {100, 10000, 200, FrozenShape::kLinear, 0.4, FrozenShape::kLinear, 0.4},
}};

bool IsSell(const std::optional<MarketOrder>& slot, int product = -1) {
  return slot.has_value() && slot->kind == OrderKind::kSell &&
         slot->item >= 0 && slot->item < kNumProducts &&
         (product < 0 || slot->item == product);
}

std::optional<MarketOrder>* FirstSell(PlayerAction* action, int product) {
  for (auto& slot : action->market) {
    if (IsSell(slot, product)) return &slot;
  }
  return nullptr;
}

std::array<int64_t, kNumProducts> SellTotals(const PlayerAction& action) {
  std::array<int64_t, kNumProducts> totals{};
  for (const auto& slot : action.market) {
    if (IsSell(slot)) {
      totals[slot->item] += std::max<int64_t>(0, slot->remaining);
    }
  }
  return totals;
}

double Shape(FrozenShape shape, double value) {
  value = std::max(0.0, value);
  switch (shape) {
    case FrozenShape::kLinear:
      return value;
    case FrozenShape::kSq:
      return value * value;
    case FrozenShape::kSqrt:
      return std::sqrt(value);
    case FrozenShape::kLog:
      return std::log1p(value);
  }
  return value;
}

int64_t PyRound(double value) {
  double rounded = std::round(value);
  if (std::fabs(value - rounded) == 0.5) {
    rounded = 2.0 * std::round(value / 2.0);
  }
  return static_cast<int64_t>(rounded);
}

int64_t FrozenPrice(int product, int64_t inventory) {
  const FrozenMarketParams& params = kFrozenMarket[product];
  double price;
  if (inventory < params.equilibrium) {
    const double amplitude =
        params.below_target * params.base /
        Shape(params.below_shape, params.scale);
    price = params.base +
            amplitude * Shape(params.below_shape,
                              static_cast<double>(params.equilibrium - inventory));
  } else {
    const double amplitude =
        params.above_target * params.base /
        Shape(params.above_shape, params.scale);
    price = params.base -
            amplitude * Shape(params.above_shape,
                              static_cast<double>(inventory - params.equilibrium));
  }
  return std::max<int64_t>(1, PyRound(price));
}

double ImpactScore(const Engine& engine,
                   const std::optional<MarketOrder>& slot) {
  if (!IsSell(slot)) return -std::numeric_limits<double>::infinity();
  const int product = slot->item;
  const int64_t quantity = std::max<int64_t>(0, slot->remaining);
  const int64_t inventory = engine.market().inventory[product];
  const double current_quote = engine.market().prices[product];
  const double later_quote = FrozenPrice(product, inventory + quantity);
  return static_cast<double>(quantity) *
         std::max(0.0, current_quote - later_quote);
}

bool ShopSells(int shop, int product) {
  const ShopData& data = kShops[shop];
  return std::find(data.products.begin(),
                   data.products.begin() + data.n_products,
                   product) != data.products.begin() + data.n_products;
}

double DemandPerDay(const Engine& engine, int product) {
  double demand = 0.0;
  for (const int shop : engine.town_shops()) {
    if (!ShopSells(shop, product)) continue;
    demand += 6.0 * (kShops[shop].n_products == 1 ? 2.0 : 1.0);
  }
  if (product != item::kFertilizer) demand += 1.0;
  return demand;
}

double OrderScore(const Engine& engine,
                  const std::optional<MarketOrder>& slot) {
  const double score = ImpactScore(engine, slot);
  if (score <= 0.0 || !IsSell(slot)) return score;
  const int product = slot->item;
  const int64_t quantity = std::max<int64_t>(0, slot->remaining);
  const int64_t current_inventory = engine.market().inventory[product];
  const double demand = std::max(0.25, DemandPerDay(engine, product));
  const double excess = std::max<int64_t>(
      0, current_inventory + quantity - 10000);
  const double urgency = std::min(1.0, excess / demand / 10.0);
  return score * (1.0 + kDemandAlpha * urgency);
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
      const int animal_slot = tile.animal == 1 ? 5 :
                              (tile.animal == 2 ? 6 : 7);
      result.counts[animal_slot] += 1;
    } else if (tile.kind == TileKind::kStructure) {
      result.counts[tile.structure == StructureKind::kPasture ? 8 : 9] += 1;
    } else if (tile.kind == TileKind::kWeed) {
      result.counts[10] += 1;
    }
  }
  return result;
}

int CloneDistance(const Engine& engine) {
  const PublicSignature left = Signature(engine.farm(0));
  const PublicSignature right = Signature(engine.farm(1));
  int distance = std::abs(left.hands - right.hands) +
                 3 * std::abs(left.unlocked - right.unlocked);
  for (size_t index = 0; index < left.counts.size(); ++index) {
    distance += std::abs(left.counts[index] - right.counts[index]);
  }
  return distance;
}

bool HasDue(const ShiftState& state) {
  return std::any_of(state.due.begin(), state.due.end(),
                     [](int64_t value) { return value > 0; });
}

void ResetDue(ShiftState* state) {
  state->due_step = -1;
  state->due.fill(0);
}

int64_t PickupReserve(const PlayerAction& action, int product) {
  int64_t reserve = 0;
  const auto add = [&](const UnitAction& order) {
    if (order.op == UnitOp::kPickup && order.arg == product) {
      reserve += std::max<int64_t>(0, order.n);
    }
  };
  add(action.farmer);
  for (const UnitAction& order : action.hands) add(order);
  return reserve;
}

void AddSell(PlayerAction* action, int product, int64_t quantity) {
  if (auto* existing = FirstSell(action, product); existing != nullptr) {
    (*existing)->remaining =
        std::max<int64_t>(0, (*existing)->remaining) + quantity;
  } else if (static_cast<int>(action->market.size()) < kMaximumOrders) {
    action->market.push_back(
        MarketOrder{OrderKind::kSell, product, quantity});
  }
}

std::pair<int, int> OpponentAnimals(const Engine& engine, int player) {
  int cows = 0;
  int sheep = 0;
  for (const Tile& tile : engine.farm(1 - player).tiles) {
    if (tile.kind != TileKind::kStructure || !tile.has_animal) continue;
    if (tile.animal == 1) ++cows;
    if (tile.animal == 2) ++sheep;
  }
  return {cows, sheep};
}

bool TownDemandAt(const Engine& engine, int product, int step) {
  if (product != item::kFertilizer && step % 24 == 0) return true;
  if (step % 4 != 0) return false;
  for (const int shop : engine.town_shops()) {
    if (ShopSells(shop, product)) return true;
  }
  return false;
}

int64_t RoundHalfToEven(int64_t value) {
  int64_t result = value / 2;
  if (value % 2 != 0 && result % 2 != 0) ++result;
  return result;
}

}  // namespace

PlayerAction RepayShift(const Engine& engine, PlayerAction action,
                        ShiftState* state) {
  const int step = engine.step_index();
  if (state->due_step != step) {
    if (state->due_step < step) ResetDue(state);
    return action;
  }
  std::vector<std::optional<MarketOrder>> market;
  market.reserve(action.market.size());
  for (auto slot : action.market) {
    if (IsSell(slot) && state->due[slot->item] > 0) {
      int64_t requested = std::max<int64_t>(0, slot->remaining);
      const int64_t reduction =
          std::min(requested, state->due[slot->item]);
      requested -= reduction;
      state->due[slot->item] -= reduction;
      if (requested <= 0) continue;
      slot->remaining = requested;
    }
    market.push_back(std::move(slot));
  }
  action.market = std::move(market);
  ResetDue(state);
  return action;
}

PlayerAction RankSellSlots(const Engine& engine, PlayerAction action) {
  struct RankedSell {
    double score;
    size_t original_index;
    std::optional<MarketOrder> order;
  };
  std::vector<RankedSell> rows;
  for (size_t index = 0; index < action.market.size(); ++index) {
    if (!IsSell(action.market[index])) continue;
    rows.push_back(
        RankedSell{OrderScore(engine, action.market[index]), index,
                   action.market[index]});
  }
  if (rows.size() < 2) return action;
  std::sort(rows.begin(), rows.end(),
            [](const RankedSell& left, const RankedSell& right) {
              if (left.score != right.score) return left.score > right.score;
              return left.original_index < right.original_index;
            });
  size_t ranked = 0;
  for (auto& slot : action.market) {
    if (IsSell(slot)) slot = rows[ranked++].order;
  }
  return action;
}

PlayerAction ApplyPreemptShift(const Portfolio& portfolio,
                               const Engine& engine, int player, Tape tape,
                               PlayerAction action, ShiftState* state) {
  const int step = engine.step_index();
  if (step < kPreemptStart || step >= kPreemptStop || HasDue(*state) ||
      CloneDistance(engine) > kPreemptMaximumCloneDistance ||
      step + 1 >= kBaseTurns) {
    return action;
  }
  const auto future = portfolio.sell_totals(tape, step + 1);
  bool has_future = false;
  for (const int product : kPremium) {
    if (future[product] > 0) has_future = true;
  }
  if (!has_future || static_cast<int>(action.market.size()) >= kMaximumOrders) {
    return action;
  }
  auto remaining = ProjectedShed(engine, player, action);
  for (const auto& slot : action.market) {
    if (IsSell(slot)) {
      remaining[slot->item] = std::max<int64_t>(
          0, remaining[slot->item] -
                 std::max<int64_t>(0, slot->remaining));
    }
  }
  std::array<int64_t, kNumProducts> shifted{};
  for (const int product : kPremium) {
    const int64_t future_quantity = std::max<int64_t>(0, future[product]);
    if (future_quantity < kPreemptMinimumFutureQuantity) continue;
    const int64_t target = std::min(
        {std::max<int64_t>(0, remaining[product]), future_quantity,
         static_cast<int64_t>(kPreemptMaximumBatch)});
    if (target <= 0 ||
        static_cast<int>(action.market.size()) >= kMaximumOrders) {
      continue;
    }
    action.market.push_back(
        MarketOrder{OrderKind::kSell, product, target});
    remaining[product] = std::max<int64_t>(0, remaining[product] - target);
    shifted[product] = target;
  }
  if (std::any_of(shifted.begin(), shifted.end(),
                  [](int64_t value) { return value > 0; })) {
    state->due_step = step + 1;
    state->due = shifted;
  }
  return action;
}

PlayerAction ApplyR5Counter(const Portfolio& portfolio, const Engine& engine,
                            int player, PlayerAction action,
                            TargetState* state) {
  const int step = engine.step_index();
  if (!state->target && step >= 24) {
    const auto [cows, sheep] = OpponentAnimals(engine, player);
    if (sheep >= 4 && cows <= 3) state->target = true;
  }
  const int future_step = step + 3;
  if (!state->target || future_step >= kTapeTurns) return action;
  const auto targets = portfolio.sell_totals(Tape::kR5Market, future_step);
  const auto existing = SellTotals(action);
  const PrivateState& priv = engine.priv(player);
  for (const int product : kCounterItems) {
    const int64_t planned = std::max<int64_t>(0, targets[product]);
    if (planned <= 0 || TownDemandAt(engine, product, step) ||
        TownDemandAt(engine, product, step + 1)) {
      continue;
    }
    const int64_t available = std::max<int64_t>(
        0, priv.shed[product] - existing[product] -
               PickupReserve(action, product));
    const int64_t quantity = std::min(
        available, std::max<int64_t>(1, RoundHalfToEven(planned)));
    if (quantity <= 0) continue;
    AddSell(&action, product, quantity);
  }
  return action;
}

PlayerAction ApplyMdCounter(const Portfolio& portfolio, const Engine& engine,
                            int player, PlayerAction action,
                            TargetState* state) {
  const int step = engine.step_index();
  if (!state->target && step >= 160) {
    const auto [cows, sheep] = OpponentAnimals(engine, player);
    const int quadrants = engine.farm(1 - player).extra_unlocked + 1;
    if ((quadrants >= 2 && cows >= 4 && sheep <= 2) || cows >= 9) {
      state->target = true;
    }
  }
  if (!state->target || step + 1 >= kBaseTurns) return action;
  const auto targets = portfolio.sell_totals(Tape::kMdMarket, step + 1);
  const auto existing = SellTotals(action);
  const PrivateState& priv = engine.priv(player);
  for (const int product : kCounterItems) {
    const int64_t target = std::max<int64_t>(0, targets[product]);
    if (target <= 0) continue;
    const int64_t available = std::max<int64_t>(
        0, priv.shed[product] - existing[product] -
               PickupReserve(action, product));
    const int64_t quantity =
        std::min(available, std::max<int64_t>(1, target * 2));
    if (quantity <= 0) continue;
    AddSell(&action, product, quantity);
  }
  return action;
}

PlayerAction ApplyTerminalLiquidation(const Engine& engine, int player,
                                      PlayerAction action) {
  const int step = engine.step_index();
  if (step < 716) return action;
  const PrivateState& priv = engine.priv(player);
  const auto planned = SellTotals(action);
  for (const int product : kLiquidationOrder) {
    const int64_t available = std::max<int64_t>(0, priv.shed[product]);
    const int64_t extra =
        step >= 718 ? available
                    : std::max<int64_t>(0, available - planned[product]);
    if (extra > 0 &&
        static_cast<int>(action.market.size()) < kMaximumOrders) {
      action.market.push_back(
          MarketOrder{OrderKind::kSell, product, extra});
    }
  }
  return action;
}

PlayerAction ApplySellDivergenceGuard(const Engine& engine, int player,
                                      PlayerAction action) {
  if (action.market.empty()) return action;
  const auto available = ProjectedShed(engine, player, action);
  std::array<int64_t, kNumProducts> checked{};
  std::vector<std::optional<MarketOrder>> repaired;
  repaired.reserve(action.market.size());
  bool changed = false;
  for (auto slot : action.market) {
    if (!IsSell(slot)) {
      repaired.push_back(std::move(slot));
      continue;
    }
    const int product = slot->item;
    const int64_t requested = std::max<int64_t>(0, slot->remaining);
    const int64_t remaining =
        std::max<int64_t>(0, available[product] - checked[product]);
    const int64_t allowed = std::min(requested, remaining);
    if (allowed != requested) changed = true;
    if (allowed > 0) {
      slot->remaining = allowed;
      repaired.push_back(std::move(slot));
      checked[product] += allowed;
    } else {
      changed = true;
    }
  }
  if (changed) {
    if (repaired.size() > kMaximumOrders) repaired.resize(kMaximumOrders);
    action.market = std::move(repaired);
  }
  return action;
}

}  // namespace kagg::mugundh::detail
