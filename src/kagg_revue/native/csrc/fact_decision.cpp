#include "derived_facts.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <limits>
#include <optional>
#include <vector>

#include "action_codec.hpp"
#include "fact_common.hpp"
#include "market_phase.hpp"
#include "unit_phase.hpp"

namespace kagg::facts {
namespace {

using CandidateFact = std::array<float, kCandidateFactFeatures>;
using internal::ProjectedState;

enum PrefixFeature : int {
  kPrefixPresent = 0,
  kPrefixUnitPhase = 1,
  kPrefixMarketPhase = 2,
  kPrefixUnitIndex = 3,
  kPrefixUnitsRemaining = 4,
  kPrefixMarketSlotsUsed = 5,
  kPrefixMarketSlotsRemaining = 6,
  kPrefixMoney = 7,
  kPrefixShedTotal = 8,
  kPrefixShedFree = 9,
  kPrefixShedFirst = 10,
  kPrefixSeedFirst = 22,
  kPrefixUnitInventory = 27,
  kPrefixUnitShedDistance = 28,
  kPrefixDecisionCount = 29,
  kPrefixExact = 30,
  kPrefixConditional = 31,
};

enum CandidateFeature : int {
  kCandidatePresent = 0,
  kCandidatePhaseValid = 1,
  kCandidateExecutable = 2,
  kCandidateExact = 3,
  kCandidateConditional = 4,
  kCandidateQuantityDependent = 5,
  kCandidateDeltaX = 6,
  kCandidateDeltaY = 7,
  kCandidateShedDistanceDelta = 8,
  kCandidateCarriedTotalDelta = 9,
  kCandidateCarriedItemDelta = 10,
  kCandidateShedTotalDelta = 11,
  kCandidateShedItemDelta = 12,
  kCandidateSeedDelta = 13,
  kCandidateCashDelta = 14,
  kCandidateMarketInventoryDelta = 15,
  kCandidateTileChanged = 16,
  kCandidateTileRemoved = 17,
  kCandidateTileCreated = 18,
  kCandidateYieldDelta = 19,
  kCandidateWateredDelta = 20,
  kCandidateFedDelta = 21,
  kCandidateCaredDelta = 22,
  kCandidateFertilizerDelta = 23,
  kCandidatePendingBonusDelta = 24,
  kCandidateMaximumQuantity = 25,
  kCandidateOneCommitted = 26,
  kCandidateUnitPrice = 27,
  kCandidateNextUnitPrice = 28,
  kCandidateMaximumCashDelta = 29,
  kCandidateResultingShedFree = 30,
  kCandidateMinimumSlackBefore = 31,
  kCandidateMinimumSlackAfter = 32,
  kCandidateMinimumSlackDelta = 33,
  kCandidateReachableBefore = 34,
  kCandidateReachableAfter = 35,
  kCandidateReachableDelta = 36,
  kCandidateResourceAvailable = 37,
  kCandidateUnitPhase = 38,
  kCandidateMarketPhase = 39,
};

int64_t InventoryTotal(const Inventory* inventory) {
  if (inventory == nullptr) return 0;
  int64_t result = 0;
  for (const auto& [_, count] : inventory->items) result += count;
  return result;
}

bool SameTile(const Tile& left, const Tile& right) {
  return left.kind == right.kind && left.crop == right.crop &&
         left.planted_day == right.planted_day &&
         left.watered_today == right.watered_today &&
         left.consecutive_unwatered == right.consecutive_unwatered &&
         left.max_lifespan_step == right.max_lifespan_step &&
         left.fertilized_until_day == right.fertilized_until_day &&
         left.yield_units == right.yield_units &&
         left.structure == right.structure && left.has_animal == right.has_animal &&
         left.animal == right.animal && left.placed_day == right.placed_day &&
         left.fed_today == right.fed_today &&
         left.consecutive_unfed == right.consecutive_unfed &&
         left.cared_today == right.cared_today &&
         left.fertilizer_available == right.fertilizer_available &&
         left.pending_care_bonus == right.pending_care_bonus;
}

int TileDifferenceCount(const Farm& before, const Farm& after) {
  int result = 0;
  const size_t count = std::min(before.tiles.size(), after.tiles.size());
  for (size_t index = 0; index < count; ++index) {
    if (!SameTile(before.tiles[index], after.tiles[index])) ++result;
  }
  return result;
}

const Tile& TileAt(const Farm& farm, std::pair<int, int> position,
                   int board_size) {
  return farm.tiles[position.second * board_size + position.first];
}

int64_t MaximumUnitQuantity(const ProjectedState& state, int unit_index,
                            const UnitAction& action, const Config& config) {
  const Inventory* inventory = internal::UnitInventory(state.priv, unit_index);
  if (action.op == UnitOp::kPickup && action.arg >= 0 && action.arg < kNumItems) {
    return std::max<int64_t>(0, state.priv.shed[action.arg]);
  }
  if (action.op == UnitOp::kPlace && action.arg >= 0 && action.arg < kNumItems) {
    const auto position = internal::UnitPosition(state.farm, unit_index);
    const Tile& tile = TileAt(state.farm, position, config.board_size);
    if (action.arg >= item::kGoose && tile.kind == TileKind::kStructure &&
        !tile.has_animal &&
        tile.structure == kAnimals[action.arg - item::kGoose].structure) {
      return inventory == nullptr ? 0 : std::min<int64_t>(1, inventory->Get(action.arg));
    }
    const int64_t carried = inventory == nullptr ? 0 : inventory->Get(action.arg);
    const int64_t room =
        std::max<int64_t>(0, config.shed_capacity - ShedTotal(state.priv));
    return std::min(carried, room);
  }
  return 1;
}

uint64_t Fibonacci(int n) {
  uint64_t left = 1;
  uint64_t right = 1;
  for (int index = 0; index < n; ++index) {
    const uint64_t next = left + right;
    if (next < right) return UINT64_MAX;
    left = right;
    right = next;
  }
  return left;
}

int64_t AffordableUnits(double money, int64_t unit_cost) {
  if (!(money >= static_cast<double>(unit_cost)) || unit_cost <= 0) return 0;
  const double affordable = std::floor(money / static_cast<double>(unit_cost));
  if (affordable >= static_cast<double>(kMaxMarketUnitsPerSlot)) {
    return kMaxMarketUnitsPerSlot;
  }
  return static_cast<int64_t>(affordable);
}

int64_t MaximumMarketQuantity(const View& view, const ProjectedState& state,
                              const MarketOrder& order) {
  const int64_t free =
      std::max<int64_t>(0, view.config.shed_capacity - ShedTotal(state.priv));
  if (order.kind == OrderKind::kSell) {
    return std::min<int64_t>(
        kMaxMarketUnitsPerSlot,
        std::max<int64_t>(0, state.priv.shed[order.item]));
  }
  if (order.kind == OrderKind::kBuySeed) {
    const int64_t cost = kCrops[order.item].seed_cost;
    return AffordableUnits(state.farm.money, cost);
  }
  if (order.kind == OrderKind::kBuyAnimal) {
    const int64_t cost = kAnimals[order.item].cost;
    return std::min<int64_t>(free, AffordableUnits(state.farm.money, cost));
  }
  if (order.kind == OrderKind::kBuyProduct) {
    int64_t inventory = state.market.inventory[order.item];
    double money = state.farm.money;
    int64_t result = 0;
    while (result < free && result < kMaxMarketUnitsPerSlot) {
      const int64_t price =
          ComputeMarketPrice(view.config, order.item, inventory - 1);
      if (money < static_cast<double>(price)) break;
      money -= static_cast<double>(price);
      --inventory;
      ++result;
    }
    return result;
  }
  if (order.kind == OrderKind::kHire) {
    const uint64_t raw = Fibonacci(state.farm.hires_today);
    const double cost = static_cast<double>(view.config.farm_hand_cost_mult) * raw;
    return state.farm.money >= cost ? 1 : 0;
  }
  if (order.kind == OrderKind::kBuyLand) {
    if (state.farm.extra_unlocked >= static_cast<int>(kLandPrices.size())) return 0;
    return state.farm.money >= kLandPrices[state.farm.extra_unlocked] ? 1 : 0;
  }
  return 0;
}

double UnitPrice(const View& view, const ProjectedState& state,
                 const MarketOrder& order, bool next) {
  if (order.kind == OrderKind::kSell) {
    int64_t inventory = state.market.inventory[order.item];
    const int64_t current =
        ComputeMarketPrice(view.config, order.item, inventory);
    if (next && current > kPriceFloor) ++inventory;
    return ComputeMarketPrice(view.config, order.item, inventory);
  }
  if (order.kind == OrderKind::kBuyProduct) {
    return ComputeMarketPrice(view.config, order.item,
                              state.market.inventory[order.item] -
                                  (next ? 2 : 1));
  }
  if (order.kind == OrderKind::kBuySeed) return kCrops[order.item].seed_cost;
  if (order.kind == OrderKind::kBuyAnimal) return kAnimals[order.item].cost;
  if (order.kind == OrderKind::kHire) {
    return static_cast<double>(view.config.farm_hand_cost_mult) *
           Fibonacci(state.farm.hires_today + (next ? 1 : 0));
  }
  if (order.kind == OrderKind::kBuyLand &&
      state.farm.extra_unlocked + (next ? 1 : 0) <
          static_cast<int>(kLandPrices.size())) {
    return kLandPrices[state.farm.extra_unlocked + (next ? 1 : 0)];
  }
  return 0.0;
}

double MaximumCashDelta(const View& view, const ProjectedState& state,
                        const MarketOrder& order, int64_t quantity) {
  if (quantity <= 0) return 0.0;
  if (order.kind == OrderKind::kSell) {
    int64_t inventory = state.market.inventory[order.item];
    double revenue = 0.0;
    for (int64_t unit = 0; unit < quantity; ++unit) {
      const int64_t price =
          ComputeMarketPrice(view.config, order.item, inventory);
      revenue += static_cast<double>(price);
      if (price > kPriceFloor) ++inventory;
    }
    return revenue;
  }
  if (order.kind == OrderKind::kBuyProduct) {
    int64_t inventory = state.market.inventory[order.item];
    double cost = 0.0;
    for (int64_t unit = 0; unit < quantity; ++unit) {
      cost += static_cast<double>(
          ComputeMarketPrice(view.config, order.item, inventory - 1));
      --inventory;
    }
    return -cost;
  }
  if (order.kind == OrderKind::kBuySeed) {
    return -static_cast<double>(quantity) * kCrops[order.item].seed_cost;
  }
  if (order.kind == OrderKind::kBuyAnimal) {
    return -static_cast<double>(quantity) * kAnimals[order.item].cost;
  }
  if (order.kind == OrderKind::kHire || order.kind == OrderKind::kBuyLand) {
    return -UnitPrice(view, state, order, false);
  }
  return 0.0;
}

double PriceScale(const View& view, const MarketOrder& order) {
  const int item_index = internal::RelevantItem(order);
  if (item_index >= 0 && item_index < kNumProducts) {
    return std::max(1.0, 5.0 * view.config.market_params[item_index].base);
  }
  return std::max(1.0, UnitPrice(view, internal::ProjectedState{
                                          view.farm, view.priv, view.market, false},
                                      order, false) *
                           5.0);
}

void AppendCandidate(std::vector<int64_t>* tokens,
                     std::vector<int64_t>* quantities, int token,
                     int64_t quantity) {
  tokens->push_back(token);
  quantities->push_back(quantity);
}

int64_t SaturatingAdd(int64_t value, int64_t update) {
  if (update > 0 && value > std::numeric_limits<int64_t>::max() - update) {
    return std::numeric_limits<int64_t>::max();
  }
  if (update < 0 && value < std::numeric_limits<int64_t>::min() - update) {
    return std::numeric_limits<int64_t>::min();
  }
  return value + update;
}

}  // namespace

std::array<float, kPrefixFactFeatures> EncodePrefixFacts(
    const View& view, const std::vector<int64_t>& tokens,
    const std::vector<int64_t>& quantities, int unit_count, int phase,
    int market_slots) {
  std::array<float, kPrefixFactFeatures> result{};
  const ProjectedState projected =
      internal::ProjectPrefix(view, tokens, quantities, unit_count);
  result[kPrefixPresent] = 1.0F;
  result[kPrefixUnitPhase] = phase == 0 ? 1.0F : 0.0F;
  result[kPrefixMarketPhase] = phase == 1 ? 1.0F : 0.0F;
  const int unit_index = std::min<int>(tokens.size(), unit_count);
  result[kPrefixUnitIndex] =
      internal::ClampRatio(unit_index, std::max(1, unit_count - 1));
  result[kPrefixUnitsRemaining] = internal::ClampRatio(
      std::max(0, unit_count - unit_index), std::max(1, unit_count));
  result[kPrefixMarketSlotsUsed] = internal::ClampRatio(
      market_slots, view.config.max_market_orders);
  result[kPrefixMarketSlotsRemaining] = internal::ClampRatio(
      std::max(0, view.config.max_market_orders - market_slots),
      view.config.max_market_orders);
  result[kPrefixMoney] = internal::SignedLog(projected.farm.money);
  const int64_t shed_total = ShedTotal(projected.priv);
  result[kPrefixShedTotal] = internal::ClampRatio(
      shed_total, view.config.shed_capacity);
  result[kPrefixShedFree] = internal::ClampRatio(
      std::max<int64_t>(0, view.config.shed_capacity - shed_total),
      view.config.shed_capacity);
  for (int item_index = 0; item_index < kNumItems; ++item_index) {
    result[kPrefixShedFirst + item_index] =
        internal::SignedLog(projected.priv.shed[item_index]);
  }
  for (int crop = 0; crop < kNumCrops; ++crop) {
    result[kPrefixSeedFirst + crop] =
        internal::SignedLog(projected.priv.seeds[crop]);
  }
  if (phase == 0 && unit_index < unit_count) {
    const Inventory* inventory = internal::UnitInventory(projected.priv, unit_index);
    result[kPrefixUnitInventory] = internal::SignedLog(InventoryTotal(inventory));
    result[kPrefixUnitShedDistance] = internal::ClampRatio(
        internal::DistanceToShed(
            internal::UnitPosition(projected.farm, unit_index),
            view.config.board_size),
        view.config.board_size);
  }
  result[kPrefixDecisionCount] = internal::ClampRatio(
      tokens.size(), unit_count + view.config.max_market_orders);
  result[kPrefixExact] = projected.market_conditional ? 0.0F : 1.0F;
  result[kPrefixConditional] = projected.market_conditional ? 1.0F : 0.0F;
  return result;
}

std::vector<float> EncodeCandidateFacts(
    const View& view, const std::vector<int64_t>& tokens,
    const std::vector<int64_t>& quantities, int unit_count, int phase,
    int unit_index, int market_slots) {
  std::array<CandidateFact, policy::kActionTokens> facts{};
  const ProjectedState before =
      internal::ProjectPrefix(view, tokens, quantities, unit_count);
  const int64_t before_shed_total = ShedTotal(before.priv);

  if (phase == 0 && unit_index < unit_count) {
    const auto before_position = internal::UnitPosition(before.farm, unit_index);
    const Inventory* before_inventory =
        internal::UnitInventory(before.priv, unit_index);
    const internal::SlackSummary before_slack =
        internal::UnitSlack(view, before.farm, before.priv, unit_index);
    for (int token = 0; token < policy::kUnitActionTokens; ++token) {
      CandidateFact& fact = facts[token];
      fact[kCandidatePresent] = 1.0F;
      fact[kCandidatePhaseValid] = 1.0F;
      fact[kCandidateExact] = 1.0F;
      fact[kCandidateUnitPhase] = 1.0F;
      fact[kCandidateQuantityDependent] =
          policy::TokenHasQuantity(token) ? 1.0F : 0.0F;
      const UnitAction action = policy::DecodeUnitToken(token, 1);
      std::vector<int64_t> candidate_tokens = tokens;
      std::vector<int64_t> candidate_quantities = quantities;
      AppendCandidate(&candidate_tokens, &candidate_quantities, token, 1);
      const ProjectedState after = internal::ProjectPrefix(
          view, candidate_tokens, candidate_quantities, unit_count);
      const PlayerAction decoded = policy::DecodePlayerAction(
          candidate_tokens.data(), candidate_quantities.data(),
          candidate_tokens.size(), unit_count, view.config.max_market_orders);
      const UnitPhaseResult compiled = CompileUnitPhase(
          view.config, view.farm, view.priv, decoded,
          view.step / view.config.turns_per_day);
      const bool executable =
          unit_index < static_cast<int>(compiled.trace.size()) &&
          (compiled.trace[unit_index].status == UnitActionStatus::kApplied ||
           compiled.trace[unit_index].status == UnitActionStatus::kPass);
      fact[kCandidateExecutable] = executable ? 1.0F : 0.0F;
      fact[kCandidateOneCommitted] = executable ? 1.0F : 0.0F;
      const auto after_position = internal::UnitPosition(after.farm, unit_index);
      fact[kCandidateDeltaX] = internal::ClampRatio(
          after_position.first - before_position.first,
          view.config.board_size - 1);
      fact[kCandidateDeltaY] = internal::ClampRatio(
          after_position.second - before_position.second,
          view.config.board_size - 1);
      fact[kCandidateShedDistanceDelta] = internal::ClampRatio(
          internal::DistanceToShed(after_position, view.config.board_size) -
              internal::DistanceToShed(before_position, view.config.board_size),
          view.config.board_size);
      const Inventory* after_inventory =
          internal::UnitInventory(after.priv, unit_index);
      fact[kCandidateCarriedTotalDelta] = internal::SignedLog(
          InventoryTotal(after_inventory) - InventoryTotal(before_inventory));
      const int item_index = internal::RelevantItem(action);
      if (item_index >= 0 && item_index < kNumItems) {
        const int64_t before_item = before_inventory == nullptr
                                        ? 0
                                        : before_inventory->Get(item_index);
        const int64_t after_item = after_inventory == nullptr
                                       ? 0
                                       : after_inventory->Get(item_index);
        fact[kCandidateCarriedItemDelta] =
            internal::SignedLog(after_item - before_item);
        fact[kCandidateShedItemDelta] = internal::SignedLog(
            after.priv.shed[item_index] - before.priv.shed[item_index]);
        if (item_index < kNumCrops) {
          fact[kCandidateSeedDelta] = internal::SignedLog(
              after.priv.seeds[item_index] - before.priv.seeds[item_index]);
        }
      }
      fact[kCandidateShedTotalDelta] = internal::SignedLog(
          ShedTotal(after.priv) - before_shed_total);
      fact[kCandidateTileChanged] =
          internal::ClampRatio(TileDifferenceCount(before.farm, after.farm),
                               view.config.board_size * view.config.board_size);
      const Tile& tile_before =
          TileAt(before.farm, before_position, view.config.board_size);
      const Tile& tile_after =
          TileAt(after.farm, before_position, view.config.board_size);
      fact[kCandidateTileRemoved] =
          tile_before.kind != TileKind::kEmpty &&
                  tile_after.kind == TileKind::kEmpty
              ? 1.0F
              : 0.0F;
      fact[kCandidateTileCreated] =
          tile_before.kind == TileKind::kEmpty &&
                  tile_after.kind != TileKind::kEmpty
              ? 1.0F
              : 0.0F;
      fact[kCandidateYieldDelta] = internal::SignedLog(
          tile_after.yield_units - tile_before.yield_units);
      fact[kCandidateWateredDelta] =
          static_cast<float>(tile_after.watered_today) -
          static_cast<float>(tile_before.watered_today);
      fact[kCandidateFedDelta] = static_cast<float>(tile_after.fed_today) -
                                 static_cast<float>(tile_before.fed_today);
      fact[kCandidateCaredDelta] = static_cast<float>(tile_after.cared_today) -
                                   static_cast<float>(tile_before.cared_today);
      fact[kCandidateFertilizerDelta] =
          static_cast<float>(tile_after.fertilizer_available) -
          static_cast<float>(tile_before.fertilizer_available);
      fact[kCandidatePendingBonusDelta] = internal::SignedLog(
          tile_after.pending_care_bonus - tile_before.pending_care_bonus);
      const int64_t maximum =
          executable
              ? (policy::TokenHasQuantity(token)
                     ? MaximumUnitQuantity(before, unit_index, action,
                                           view.config)
                     : 1)
              : 0;
      fact[kCandidateMaximumQuantity] = internal::SignedLog(maximum);
      fact[kCandidateResourceAvailable] =
          executable && maximum > 0 ? 1.0F : 0.0F;
      fact[kCandidateResultingShedFree] = internal::ClampRatio(
          std::max<int64_t>(0, view.config.shed_capacity - ShedTotal(after.priv)),
          view.config.shed_capacity);
      const internal::SlackSummary after_slack =
          internal::UnitSlack(view, after.farm, after.priv, unit_index);
      if (before_slack.present) {
        fact[kCandidateMinimumSlackBefore] = internal::ClampRatio(
            before_slack.minimum, view.config.episode_steps);
      }
      if (after_slack.present) {
        fact[kCandidateMinimumSlackAfter] = internal::ClampRatio(
            after_slack.minimum, view.config.episode_steps);
      }
      if (before_slack.present && after_slack.present) {
        fact[kCandidateMinimumSlackDelta] = internal::ClampRatio(
            after_slack.minimum - before_slack.minimum,
            view.config.episode_steps);
      }
      fact[kCandidateReachableBefore] = internal::ClampRatio(
          before_slack.reachable,
          std::max(1, view.config.board_size * view.config.board_size));
      fact[kCandidateReachableAfter] = internal::ClampRatio(
          after_slack.reachable,
          std::max(1, view.config.board_size * view.config.board_size));
      fact[kCandidateReachableDelta] = internal::ClampRatio(
          after_slack.reachable - before_slack.reachable,
          view.config.board_size * view.config.board_size);
    }
  } else if (phase == 1 && market_slots < view.config.max_market_orders) {
    for (int token = policy::kUnitActionTokens; token < policy::kActionTokens;
         ++token) {
      CandidateFact& fact = facts[token];
      fact[kCandidatePresent] = 1.0F;
      fact[kCandidatePhaseValid] = 1.0F;
      fact[kCandidateMarketPhase] = 1.0F;
      fact[kCandidateQuantityDependent] =
          policy::TokenHasQuantity(token) ? 1.0F : 0.0F;
      const std::optional<MarketOrder> order =
          policy::DecodeMarketToken(token, 1);
      const bool special = token == policy::kMarketStopToken || !order;
      const int64_t maximum = order ? MaximumMarketQuantity(view, before, *order) : 1;
      fact[kCandidateMaximumQuantity] = internal::SignedLog(maximum);
      fact[kCandidateExecutable] = special || maximum > 0 ? 1.0F : 0.0F;
      fact[kCandidateResourceAvailable] = special || maximum > 0 ? 1.0F : 0.0F;
      std::vector<int64_t> candidate_tokens = tokens;
      std::vector<int64_t> candidate_quantities = quantities;
      AppendCandidate(&candidate_tokens, &candidate_quantities, token, 1);
      const ProjectedState after = internal::ProjectPrefix(
          view, candidate_tokens, candidate_quantities, unit_count);
      const bool candidate_conditional =
          order && (order->kind == OrderKind::kSell ||
                    order->kind == OrderKind::kBuyProduct);
      const bool conditional = before.market_conditional || candidate_conditional;
      fact[kCandidateExact] = conditional ? 0.0F : 1.0F;
      fact[kCandidateConditional] = conditional ? 1.0F : 0.0F;
      fact[kCandidateOneCommitted] =
          special || std::abs(after.farm.money - before.farm.money) > 0.0 ||
                  ShedTotal(after.priv) != before_shed_total
              ? 1.0F
              : 0.0F;
      fact[kCandidateCashDelta] =
          internal::SignedLog(after.farm.money - before.farm.money);
      fact[kCandidateShedTotalDelta] = internal::SignedLog(
          ShedTotal(after.priv) - before_shed_total);
      if (order) {
        const int item_index = internal::RelevantItem(*order);
        if (item_index >= 0 && item_index < kNumItems) {
          fact[kCandidateShedItemDelta] = internal::SignedLog(
              after.priv.shed[item_index] - before.priv.shed[item_index]);
          if (order->kind == OrderKind::kBuySeed) {
            fact[kCandidateSeedDelta] = internal::SignedLog(
                after.priv.seeds[order->item] -
                before.priv.seeds[order->item]);
          }
        }
        if (order->item >= 0 && order->item < kNumProducts &&
            (order->kind == OrderKind::kSell ||
             order->kind == OrderKind::kBuyProduct)) {
          fact[kCandidateMarketInventoryDelta] = internal::SignedLog(
              after.market.inventory[order->item] -
              before.market.inventory[order->item]);
        }
        const double scale = PriceScale(view, *order);
        fact[kCandidateUnitPrice] = internal::ClampRatio(
            UnitPrice(view, before, *order, false), scale);
        fact[kCandidateNextUnitPrice] = internal::ClampRatio(
            UnitPrice(view, before, *order, true), scale);
        if (maximum > 0) {
          fact[kCandidateMaximumCashDelta] = internal::SignedLog(
              MaximumCashDelta(view, before, *order, maximum));
        }
      }
      fact[kCandidateResultingShedFree] = internal::ClampRatio(
          std::max<int64_t>(0, view.config.shed_capacity - ShedTotal(after.priv)),
          view.config.shed_capacity);
    }
  }

  std::vector<float> result;
  result.reserve(policy::kActionTokens * kCandidateFactFeatures);
  for (const CandidateFact& fact : facts) {
    result.insert(result.end(), fact.begin(), fact.end());
  }
  return result;
}

std::array<std::array<int64_t, 2>, kNumProducts> OwnMarketFlowBounds(
    const std::vector<int64_t>& tokens, const std::vector<int64_t>& quantities,
    int unit_count) {
  std::array<std::array<int64_t, 2>, kNumProducts> result{};
  const int decisions = std::min(tokens.size(), quantities.size());
  for (int index = unit_count; index < decisions; ++index) {
    const int token = static_cast<int>(tokens[index]);
    if (token == policy::kMarketStopToken) break;
    const std::optional<MarketOrder> order =
        policy::DecodeMarketToken(token, quantities[index]);
    if (!order) continue;
    const int64_t quantity = std::max<int64_t>(0, order->remaining);
    if (order->kind == OrderKind::kSell && order->item < kNumProducts) {
      result[order->item][1] =
          SaturatingAdd(result[order->item][1], quantity);
    } else if (order->kind == OrderKind::kBuyProduct &&
               order->item < kNumProducts) {
      result[order->item][0] =
          SaturatingAdd(result[order->item][0], -quantity);
    }
  }
  return result;
}

std::vector<std::string> PrefixFactNames() {
  return {
      "present", "phase_unit", "phase_market", "unit_index",
      "units_remaining", "market_slots_used", "market_slots_remaining",
      "projected_money", "projected_shed_total", "projected_shed_free",
      "shed_wheat", "shed_carrot", "shed_tomato", "shed_strawberry",
      "shed_melon", "shed_egg", "shed_milk", "shed_wool",
      "shed_fertilizer", "shed_goose", "shed_cow", "shed_sheep",
      "seed_wheat", "seed_carrot", "seed_tomato", "seed_strawberry",
      "seed_melon", "current_unit_inventory", "current_unit_shed_distance",
      "selected_decisions", "projection_exact",
      "projection_conditional_no_opponent"};
}

std::vector<std::string> CandidateFactNames() {
  return {
      "present", "phase_valid", "executable", "exact",
      "conditional_no_opponent", "quantity_dependent", "delta_x", "delta_y",
      "distance_to_shed_delta", "carried_total_delta",
      "carried_relevant_item_delta", "shed_total_delta",
      "shed_relevant_item_delta", "seed_delta", "cash_delta",
      "market_inventory_delta", "changed_tile_fraction", "tile_removed",
      "tile_created", "yield_delta", "watered_delta", "fed_delta",
      "cared_delta", "fertilizer_available_delta", "pending_bonus_delta",
      "maximum_feasible_quantity", "one_unit_committed", "unit_price",
      "next_unit_price", "maximum_quantity_cash_delta", "resulting_shed_free",
      "minimum_slack_before", "minimum_slack_after", "minimum_slack_delta",
      "reachable_services_before", "reachable_services_after",
      "reachable_services_delta", "resource_available", "phase_unit",
      "phase_market"};
}

}  // namespace kagg::facts
