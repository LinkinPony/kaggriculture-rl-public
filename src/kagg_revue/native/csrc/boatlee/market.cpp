#include "boatlee/detail.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <limits>
#include <optional>
#include <utility>
#include <vector>

namespace kagg::boatlee::detail {
namespace {

constexpr int kPreemptStart = 120;
constexpr int kPreemptStop = 680;
constexpr int kPreemptMaximumBatch = 12;
constexpr int kPreemptMaximumCloneDistance = 6;
constexpr int kPreemptMinimumFutureQuantity = 4;
constexpr int kMaximumOpponentHorizon = 6;
constexpr double kAdaptMinimumEvidence = 1.5;
constexpr double kAdaptDecay = 0.999;
constexpr double kDemandAlpha = 0.25;

constexpr std::array<int, 4> kPremium = {
    item::kStrawberry, item::kMelon, item::kMilk, item::kWool};
constexpr std::array<int, 4> kCounterItems = {
    item::kMelon, item::kMilk, item::kStrawberry, item::kWool};

enum class FrozenShape : uint8_t { kLinear, kSq, kSqrt, kLog, kHinge };

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
    {35, 10000, 450, FrozenShape::kHinge, 1.0, FrozenShape::kSqrt, 0.7},
    {60, 10000, 200, FrozenShape::kHinge, 0.4, FrozenShape::kSqrt, 0.6},
    {120, 10000, 100, FrozenShape::kSqrt, 0.7, FrozenShape::kLinear, 1.6},
    {250, 10000, 300, FrozenShape::kLog, 0.2, FrozenShape::kSq, 3.6},
    {50, 10000, 332, FrozenShape::kHinge, 0.4, FrozenShape::kLog, 0.2},
    {160, 10000, 122, FrozenShape::kSqrt, 0.6, FrozenShape::kLinear, 1.6},
    {200, 10000, 105, FrozenShape::kLog, 0.2, FrozenShape::kSq, 3.2},
    {100, 10000, 200, FrozenShape::kLinear, 0.4, FrozenShape::kLinear, 0.4},
}};

int PremiumIndex(int product) {
  const auto found = std::find(kPremium.begin(), kPremium.end(), product);
  return found == kPremium.end()
             ? -1
             : static_cast<int>(std::distance(kPremium.begin(), found));
}

double Shape(FrozenShape shape, double value, double scale) {
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
    case FrozenShape::kHinge: {
      const double normalized = value / scale;
      const double excess = std::max(0.0, normalized - 1.0);
      return normalized + 8.0 * excess * excess;
    }
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
        Shape(params.below_shape, params.scale, params.scale);
    price = params.base +
            amplitude * Shape(params.below_shape,
                              static_cast<double>(params.equilibrium - inventory),
                              params.scale);
  } else {
    const double amplitude =
        params.above_target * params.base /
        Shape(params.above_shape, params.scale, params.scale);
    price = params.base -
            amplitude * Shape(params.above_shape,
                              static_cast<double>(inventory - params.equilibrium),
                              params.scale);
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
    if (ShopSells(shop, product)) {
      demand += 6.0 * (kShops[shop].n_products == 1 ? 2.0 : 1.0);
    }
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
  const int64_t inventory = engine.market().inventory[product];
  const double demand = std::max(0.25, DemandPerDay(engine, product));
  const double excess =
      std::max<double>(0.0, inventory + quantity - 10000);
  const double urgency = std::min(1.0, excess / demand / 10.0);
  return score * (1.0 + kDemandAlpha * urgency);
}

struct PublicSignature {
  int hands = 0;
  int quadrants = 0;
  // Python sorts the names alphabetically: CARROT, COOP, COW, GOOSE, MELON,
  // PASTURE, SHEEP, STRAWBERRY, TOMATO, WEED, WHEAT.
  std::array<int, 11> counts{};
};

PublicSignature Signature(const Farm& farm) {
  PublicSignature result;
  result.hands = static_cast<int>(farm.hands.size());
  result.quadrants = farm.extra_unlocked + 1;
  for (const Tile& tile : farm.tiles) {
    if (tile.kind == TileKind::kPlant) {
      constexpr std::array<int, kNumCrops> kCropSlots = {10, 0, 8, 7, 4};
      result.counts[kCropSlots[tile.crop]] += 1;
    } else if (tile.kind == TileKind::kStructure && tile.has_animal) {
      constexpr std::array<int, kNumAnimals> kAnimalSlots = {3, 2, 6};
      result.counts[kAnimalSlots[tile.animal]] += 1;
    } else if (tile.kind == TileKind::kStructure) {
      result.counts[tile.structure == StructureKind::kPasture ? 5 : 1] += 1;
    } else if (tile.kind == TileKind::kWeed) {
      result.counts[9] += 1;
    }
  }
  return result;
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

int TownDrain(int step, const std::vector<int>& shops, int product) {
  int drain = 0;
  if (step % 4 == 0) {
    for (const int shop : shops) {
      if (ShopSells(shop, product)) {
        drain += kShops[shop].n_products == 1 ? 2 : 1;
      }
    }
  }
  if (step % 24 == 0) ++drain;
  return drain;
}

bool TownDemandAt(const Engine& engine, int product, int step) {
  if (product != item::kFertilizer && step % 24 == 0) return true;
  if (step % 4 != 0) return false;
  for (const int shop : engine.town_shops()) {
    if (ShopSells(shop, product)) return true;
  }
  return false;
}

int64_t PlannedPremium(const Portfolio& portfolio, const Engine& engine,
                       int player, MoonState* state, int step, int product) {
  if (step < 0 || step >= kMoonTurns) return 0;
  return portfolio.sell_totals(SelectMoonTape(engine, player, state), step)
      [product];
}

int64_t RoundHalfToEven(int64_t value) {
  int64_t result = value / 2;
  if (value % 2 != 0 && result % 2 != 0) ++result;
  return result;
}

}  // namespace

int CloneDistance(const Engine& engine) {
  const PublicSignature left = Signature(engine.farm(0));
  const PublicSignature right = Signature(engine.farm(1));
  int distance = std::abs(left.hands - right.hands) +
                 3 * std::abs(left.quadrants - right.quadrants);
  for (size_t index = 0; index < left.counts.size(); ++index) {
    distance += std::abs(left.counts[index] - right.counts[index]);
  }
  return distance;
}

void ObserveOpponentMarket(const Portfolio& portfolio, const Engine& engine,
                           int player, MoonState* state) {
  const int step = engine.step_index();
  RaceState& race = state->race;
  if (step == 0 || step < race.last_step) race = RaceState{};
  race.policy_evidence *= kAdaptDecay;
  for (double& score : race.policy_scores) score *= kAdaptDecay;
  for (int item_index = 0; item_index < static_cast<int>(kPremium.size());
       ++item_index) {
    race.evidence[item_index] *= kAdaptDecay;
    for (double& score : race.scores[item_index]) score *= kAdaptDecay;
  }
  if (race.initialized && race.last_step == step - 1 &&
      CloneDistance(engine) <= kPreemptMaximumCloneDistance) {
    for (int item_index = 0; item_index < static_cast<int>(kPremium.size());
         ++item_index) {
      const int product = kPremium[item_index];
      if (race.prices[product] <= 1 ||
          engine.market().prices[product] <= 1) {
        continue;
      }
      const int64_t delta = engine.market().inventory[product] -
                            race.inventory[product];
      const int64_t opponent_supply =
          delta + TownDrain(race.last_step, race.shops, product) -
          race.own_sells[product];
      const int64_t extra_supply =
          opponent_supply - PlannedPremium(portfolio, engine, player, state,
                                            race.last_step, product);
      if (extra_supply < kPreemptMinimumFutureQuantity) continue;
      race.evidence[item_index] += 1.0;
      race.policy_evidence += 1.0;
      for (int horizon = 1; horizon <= kMaximumOpponentHorizon; ++horizon) {
        const int64_t expected = PlannedPremium(
            portfolio, engine, player, state, race.last_step + horizon,
            product);
        double update = -0.15;
        if (expected > 0) {
          const double similarity =
              static_cast<double>(std::min(extra_supply, expected)) /
              static_cast<double>(std::max(extra_supply, expected));
          update = 1.0 + similarity;
        }
        race.scores[item_index][horizon - 1] += update;
        race.policy_scores[horizon - 1] += update;
      }
      if (race.evidence[item_index] >= kAdaptMinimumEvidence) {
        std::array<int, kMaximumOpponentHorizon> ranked = {0, 1, 2, 3, 4, 5};
        std::sort(ranked.begin(), ranked.end(), [&](int left, int right) {
          if (race.scores[item_index][left] !=
              race.scores[item_index][right]) {
            return race.scores[item_index][left] >
                   race.scores[item_index][right];
          }
          return left < right;
        });
        if (race.scores[item_index][ranked[0]] >=
            race.scores[item_index][ranked[1]] + 0.25) {
          race.horizon[item_index] =
              std::min(kMaximumOpponentHorizon, ranked[0] + 2);
        }
      }
    }
  }
  if (race.policy_evidence >= kAdaptMinimumEvidence) {
    std::array<int, kMaximumOpponentHorizon> ranked = {0, 1, 2, 3, 4, 5};
    std::sort(ranked.begin(), ranked.end(), [&](int left, int right) {
      if (race.policy_scores[left] != race.policy_scores[right]) {
        return race.policy_scores[left] > race.policy_scores[right];
      }
      return left < right;
    });
    if (race.policy_scores[ranked[0]] >=
        race.policy_scores[ranked[1]] + 0.25) {
      race.policy_horizon =
          std::min(kMaximumOpponentHorizon, ranked[0] + 2);
      for (int& horizon : race.horizon) {
        if (horizon == 1) horizon = race.policy_horizon;
      }
    }
  }
  race.last_step = step;
  race.initialized = true;
  race.inventory = engine.market().inventory;
  race.prices = engine.market().prices;
  race.shops = engine.town_shops();
}

void RecordOwnSells(const Engine& engine, int player,
                    const PlayerAction& action, RaceState* state) {
  state->own_sells.fill(0);
  auto remaining = ProjectedShed(engine, player, action);
  for (const auto& slot : action.market) {
    if (!IsSell(slot) || PremiumIndex(slot->item) < 0) continue;
    const int product = slot->item;
    const int64_t quantity = std::min(
        std::max<int64_t>(0, slot->remaining),
        std::max<int64_t>(0, remaining[product]));
    if (quantity <= 0) continue;
    state->own_sells[product] += quantity;
    remaining[product] = std::max<int64_t>(0, remaining[product] - quantity);
  }
}

PlayerAction RepayShift(const Engine& engine, PlayerAction action,
                        ShiftState* state) {
  const int step = engine.step_index();
  auto found = state->debts.find(step);
  if (found == state->debts.end()) return action;
  auto due = found->second;
  state->debts.erase(found);
  std::vector<std::optional<MarketOrder>> market;
  market.reserve(action.market.size());
  for (auto slot : action.market) {
    if (IsSell(slot) && due[slot->item] > 0) {
      int64_t requested = std::max<int64_t>(0, slot->remaining);
      const int64_t reduction = std::min(requested, due[slot->item]);
      requested -= reduction;
      due[slot->item] -= reduction;
      if (requested <= 0) continue;
      slot->remaining = requested;
    }
    market.push_back(std::move(slot));
  }
  action.market = std::move(market);
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
    if (IsSell(action.market[index])) {
      rows.push_back(RankedSell{OrderScore(engine, action.market[index]),
                                index, action.market[index]});
    }
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
                               PlayerAction action, MoonState* state) {
  const int step = engine.step_index();
  if (step < kPreemptStart || step >= kPreemptStop ||
      CloneDistance(engine) > kPreemptMaximumCloneDistance ||
      static_cast<int>(action.market.size()) >= kMaximumOrders) {
    return action;
  }
  auto remaining = ProjectedShed(engine, player, action);
  for (const auto& slot : action.market) {
    if (IsSell(slot)) {
      remaining[slot->item] = std::max<int64_t>(
          0, remaining[slot->item] - std::max<int64_t>(0, slot->remaining));
    }
  }
  struct Choice {
    double value;
    int product;
    int64_t target;
    int horizon;
  };
  std::vector<Choice> choices;
  const int clone_distance = CloneDistance(engine);
  for (int premium_index = 0;
       premium_index < static_cast<int>(kPremium.size()); ++premium_index) {
    const int product = kPremium[premium_index];
    int preferred = state->race.horizon[premium_index];
    if (clone_distance <= 2) preferred = std::max(3, preferred);
    for (int horizon = preferred; horizon > 0; --horizon) {
      const int64_t future = portfolio.sell_totals(tape, step + horizon)
                                 [product];
      if (future < kPreemptMinimumFutureQuantity) continue;
      const int64_t target = std::min(
          {std::max<int64_t>(0, remaining[product]), future,
           static_cast<int64_t>(kPreemptMaximumBatch)});
      if (target > 0) {
        choices.push_back(Choice{
            static_cast<double>(engine.market().prices[product]) * target,
            product, target, horizon});
      }
      break;
    }
  }
  std::vector<Choice> selected;
  for (const Choice& choice : choices) {
    if (choice.horizon > 1) selected.push_back(choice);
  }
  if (!selected.empty()) {
    const auto best = std::max_element(
        selected.begin(), selected.end(),
        [](const Choice& left, const Choice& right) {
          if (left.value != right.value) return left.value < right.value;
          const int names = std::strcmp(kItemNames[left.product],
                                        kItemNames[right.product]);
          if (names != 0) return names < 0;
          if (left.target != right.target) return left.target < right.target;
          return left.horizon < right.horizon;
        });
    selected = {*best};
  } else {
    selected = choices;
  }
  for (const Choice& choice : selected) {
    if (static_cast<int>(action.market.size()) >= kMaximumOrders) break;
    action.market.push_back(MarketOrder{OrderKind::kSell, choice.product,
                                        choice.target});
    remaining[choice.product] =
        std::max<int64_t>(0, remaining[choice.product] - choice.target);
    state->shift.debts[step + choice.horizon][choice.product] +=
        choice.target;
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
  const auto targets = portfolio.sell_totals(Tape::kMoonR5Market,
                                              future_step);
  const PrivateState& priv = engine.priv(player);
  for (const int product : kCounterItems) {
    const int64_t planned = std::max<int64_t>(0, targets[product]);
    if (planned <= 0 || TownDemandAt(engine, product, step) ||
        TownDemandAt(engine, product, step + 1)) {
      continue;
    }
    const int64_t existing = SellTotals(action)[product];
    const int64_t available = std::max<int64_t>(
        0, priv.shed[product] - existing - PickupReserve(action, product));
    const int64_t quantity =
        std::min(available, std::max<int64_t>(1, RoundHalfToEven(planned)));
    if (quantity > 0) AddSell(&action, product, quantity);
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
  if (!state->target || step + 1 >= kMoonTurns) return action;
  const auto targets =
      portfolio.sell_totals(Tape::kMoonMdMarket, step + 1);
  const PrivateState& priv = engine.priv(player);
  for (const int product : kCounterItems) {
    const int64_t target = std::max<int64_t>(0, targets[product]);
    if (target <= 0) continue;
    const int64_t existing = SellTotals(action)[product];
    const int64_t available = std::max<int64_t>(
        0, priv.shed[product] - existing - PickupReserve(action, product));
    const int64_t quantity = std::min(available, target * 2);
    if (quantity > 0) AddSell(&action, product, quantity);
  }
  return action;
}

}  // namespace kagg::boatlee::detail
