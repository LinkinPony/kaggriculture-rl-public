#include "capability_internal.hpp"

#include <algorithm>
#include <cmath>
#include <limits>
#include <numeric>
#include <stdexcept>
#include <string>
#include <vector>

namespace kagg::capability {
namespace {

float SafeRatio(double numerator, double denominator) {
  return static_cast<float>(numerator / std::max(1.0, denominator));
}

int64_t Fibonacci(int index) {
  if (index <= 0) return 0;
  int64_t previous = 0;
  int64_t current = 1;
  for (int cursor = 1; cursor < index; ++cursor) {
    if (current > std::numeric_limits<int64_t>::max() - previous) {
      return std::numeric_limits<int64_t>::max();
    }
    const int64_t next = previous + current;
    previous = current;
    current = next;
  }
  return current;
}

double EstimateCost(const Engine& engine, int player,
                    const GoalLedger& projected,
                    const internal::StateSummary& state) {
  const Config& config = engine.config();
  const Farm& farm = engine.farm(player);
  double cost = 0.0;
  int hires = farm.hires_today;
  for (int worker = state.farm.workers; worker < projected.workers.lower;
       ++worker) {
    cost += static_cast<double>(config.farm_hand_cost_mult) * Fibonacci(hires);
    ++hires;
  }
  for (int quadrant = state.farm.quadrants;
       quadrant < std::min(4, projected.land.lower); ++quadrant) {
    cost += static_cast<double>(kLandPrices[quadrant - 1]);
  }
  for (int crop = 0; crop < kNumCrops; ++crop) {
    cost += std::max(0, projected.crops[crop].lower -
                            state.farm.crop_counts[crop]) *
            static_cast<double>(kCrops[crop].seed_cost);
  }
  for (int animal = 0; animal < kNumAnimals; ++animal) {
    cost += std::max(0, projected.animals[animal].lower -
                            state.farm.animal_counts[animal]) *
            static_cast<double>(kAnimals[animal].cost);
  }
  for (int product = 0; product < kNumProducts; ++product) {
    cost += std::max<int64_t>(0, projected.products[product].lower -
                                    state.owned_items[product]) *
            static_cast<double>(engine.market().prices[product]);
  }
  return cost;
}

double EstimateReturn(const Engine& engine, const GoalLedger& projected,
                      const internal::StateSummary& state) {
  const Config& config = engine.config();
  const int remaining_steps =
      std::max(0, config.episode_steps - 1 - engine.step_index());
  const double remaining_days =
      static_cast<double>(remaining_steps) / std::max(1, config.turns_per_day);
  double value = 0.0;
  for (int crop = 0; crop < kNumCrops; ++crop) {
    const int delta = std::max(
        0, projected.crops[crop].lower - state.farm.crop_counts[crop]);
    if (delta == 0 || remaining_days < kCrops[crop].first_yield_day) continue;
    const double harvests = kCrops[crop].ongoing
                                ? 1.0 + (remaining_days -
                                         kCrops[crop].first_yield_day) /
                                            std::max(1, kCrops[crop].interval)
                                : 1.0;
    value += delta * harvests * kCrops[crop].max_yield *
             config.market_params[crop].base;
  }
  for (int animal = 0; animal < kNumAnimals; ++animal) {
    const int delta = std::max(
        0, projected.animals[animal].lower - state.farm.animal_counts[animal]);
    if (delta == 0 || remaining_days < kAnimals[animal].first_yield_day) {
      continue;
    }
    const double harvests =
        1.0 + (remaining_days - kAnimals[animal].first_yield_day) /
                  std::max(1, kAnimals[animal].interval);
    value += delta * harvests * kAnimals[animal].max_held *
             config.market_params[kAnimals[animal].product].base;
  }
  for (int product = 0; product < kNumProducts; ++product) {
    const int64_t sell = std::max<int64_t>(
        0, state.owned_items[product] - projected.products[product].lower);
    value += sell * engine.market().prices[product];
  }
  return value;
}

}  // namespace

namespace internal {

int64_t Carried(const PrivateState& priv, int item_index) {
  int64_t total = 0;
  for (const Inventory& inventory : priv.inventories) {
    total += inventory.Get(item_index);
  }
  return total;
}

FarmSummary SummarizeFarm(const Config& config, const Farm& farm, int day) {
  FarmSummary out;
  out.workers += static_cast<int>(farm.hands.size());
  out.quadrants += farm.extra_unlocked;
  for (const Tile& tile : farm.tiles) {
    if (tile.kind == TileKind::kLocked) continue;
    ++out.owned;
    if (tile.kind == TileKind::kEmpty) {
      ++out.empty;
      continue;
    }
    if (tile.kind == TileKind::kWeed) {
      ++out.weeds;
      continue;
    }
    if (tile.kind == TileKind::kPlant) {
      ++out.crops;
      ++out.crop_counts[tile.crop];
      if (!tile.watered_today) ++out.crops_needing_water;
      if (tile.yield_units > 0 &&
          day - tile.planted_day >= kCrops[tile.crop].first_yield_day) {
        ++out.crops_ready;
      }
      continue;
    }
    if (tile.kind == TileKind::kStructure && tile.has_animal) {
      ++out.animals;
      ++out.animal_counts[tile.animal];
      if (!tile.fed_today) ++out.animals_needing_feed;
      if (tile.yield_units > 0) ++out.animals_ready;
    }
  }
  (void)config;
  return out;
}

StateSummary Summarize(const Engine& engine, int player) {
  const Config& config = engine.config();
  const Farm& farm = engine.farm(player);
  const PrivateState& priv = engine.priv(player);
  const int day = engine.step_index() / std::max(1, config.turns_per_day);
  StateSummary out;
  out.farm = SummarizeFarm(config, farm, day);
  for (int item_index = 0; item_index < kNumItems; ++item_index) {
    const int64_t carried = Carried(priv, item_index);
    out.owned_items[item_index] = priv.shed[item_index] + carried;
    out.shed_total += priv.shed[item_index];
    out.carried_total += carried;
  }
  out.occupied = out.farm.owned - out.farm.empty;
  return out;
}

std::array<float, kCandidateFeatureCount> CandidateFeatures(
    const Engine& engine, int player, const StateSummary& state, Mode mode,
    const std::vector<Edit>& edits, const GoalLedger& projected,
    int max_edits) {
  std::array<float, kCandidateFeatureCount> out{};
  const Config& config = engine.config();
  const Farm& farm = engine.farm(player);
  const double cost = EstimateCost(engine, player, projected, state);
  const double expected_return = EstimateReturn(engine, projected, state);
  const int board_cells = std::max(1, config.board_size * config.board_size);
  const int remaining_steps =
      std::max(0, config.episode_steps - 1 - engine.step_index());
  const double scale = std::max<double>(1.0, config.starting_money);
  const int target_crops = std::accumulate(
      projected.crops.begin(), projected.crops.end(), 0,
      [](int total, const Goal& goal) { return total + goal.lower; });
  const int target_animals = std::accumulate(
      projected.animals.begin(), projected.animals.end(), 0,
      [](int total, const Goal& goal) { return total + goal.lower; });
  int64_t target_products = 0;
  int min_deadline = config.episode_steps - 1;
  int ensure_edits = 0;
  int reduce_edits = 0;
  int trade_edits = 0;
  int64_t buy_magnitude = 0;
  int64_t sell_magnitude = 0;
  float max_urgency = 0.0F;
  float max_price_guard = 0.0F;
  for (const Goal& goal : projected.products) target_products += goal.lower;
  for (const Edit& edit : edits) {
    min_deadline = std::min(min_deadline,
                            edit.deadline_step < 0 ? min_deadline
                                                   : static_cast<int>(edit.deadline_step));
    ensure_edits += edit.type == EditType::kEnsure;
    reduce_edits += edit.type == EditType::kReduce;
    trade_edits += edit.type == EditType::kTrade;
    max_urgency = std::max(max_urgency, edit.urgency);
    if (edit.object == ObjectKind::kProduct && edit.reference >= 0 &&
        edit.reference < kNumProducts) {
      const int product = static_cast<int>(edit.reference);
      const int64_t delta = edit.target - state.owned_items[product];
      buy_magnitude += std::max<int64_t>(0, delta);
      sell_magnitude += std::max<int64_t>(0, -delta);
      max_price_guard = std::max(
          max_price_guard,
          SafeRatio(edit.price_guard,
                    config.market_params[product].base));
    }
  }
  const double workload = target_crops + target_animals * 4.0 + 4.0;
  const double daily_capacity =
      std::max(1, projected.workers.lower) * std::max(1, config.turns_per_day);
  const double cash = farm.money;
  const bool feasible = cost <= std::max(0.0, cash) * 1.25 || cost == 0.0;

  const int mode_index = static_cast<int>(mode);
  if (mode_index >= 0 && mode_index < 4) out[mode_index] = 1.0F;
  out[4] = SafeRatio(edits.size(), std::max(1, max_edits));
  out[5] = projected.active ? 1.0F : 0.0F;
  out[6] = SafeRatio(projected.workers.lower, 16.0);
  out[7] = SafeRatio(projected.land.lower, 4.0);
  out[8] = SafeRatio(target_crops, board_cells);
  out[9] = SafeRatio(target_animals, board_cells);
  out[10] = SafeRatio(target_products, config.shed_capacity);
  out[11] = SafeRatio(cost, scale);
  out[12] = SafeRatio(cash, scale);
  out[13] = SafeRatio(remaining_steps, std::max(1, config.episode_steps - 1));
  out[14] = SafeRatio(std::max(0, min_deadline - engine.step_index()),
                      std::max(1, config.episode_steps - 1));
  out[15] = feasible ? 1.0F : 0.0F;
  out[16] = SafeRatio(workload, daily_capacity);
  out[17] = static_cast<float>(
      std::tanh((expected_return - cost) / std::max(1.0, scale)));
  out[18] = SafeRatio(state.farm.workers, 16.0);
  out[19] = SafeRatio(state.farm.quadrants, 4.0);
  out[20] = SafeRatio(state.farm.crops, board_cells);
  out[21] = SafeRatio(state.farm.animals, board_cells);
  out[22] = SafeRatio(state.occupied, std::max(1, state.farm.owned));
  out[23] = SafeRatio(state.shed_total, config.shed_capacity);
  out[24] = SafeRatio(buy_magnitude, config.shed_capacity);
  out[25] = SafeRatio(sell_magnitude, config.shed_capacity);
  out[26] = SafeRatio(ensure_edits, std::max<size_t>(1, edits.size()));
  out[27] = SafeRatio(reduce_edits, std::max<size_t>(1, edits.size()));
  out[28] = SafeRatio(trade_edits, std::max<size_t>(1, edits.size()));
  out[29] = SafeRatio(std::abs(target_crops - state.farm.crops) +
                          std::abs(target_animals - state.farm.animals),
                      board_cells);
  out[30] = max_price_guard;
  out[31] = max_urgency;
  return out;
}

}  // namespace internal

std::array<float, kRootFeatureCount> EncodeRootFeatures(
    const Engine& engine, int player, const Session& session) {
  if (player < 0 || player > 1) {
    throw std::invalid_argument("capability player must be 0 or 1");
  }
  const Config& config = engine.config();
  const int step = engine.step_index();
  const int turns_per_day = std::max(1, config.turns_per_day);
  const int day = step / turns_per_day;
  const Farm& own = engine.farm(player);
  const Farm& opponent = engine.farm(1 - player);
  const PrivateState& priv = engine.priv(player);
  const internal::FarmSummary own_summary =
      internal::SummarizeFarm(config, own, day);
  const internal::FarmSummary opponent_summary =
      internal::SummarizeFarm(config, opponent, day);
  const int board_cells = std::max(1, config.board_size * config.board_size);
  const double money_scale = std::max<double>(1.0, config.starting_money);
  std::array<float, kRootFeatureCount> out{};
  int index = 0;
  const auto push = [&](float value) { out[index++] = value; };
  push(SafeRatio(step, std::max(1, config.episode_steps - 1)));
  push(SafeRatio(day,
                 std::max(1, (config.episode_steps - 2) / turns_per_day)));
  push(SafeRatio(step % turns_per_day, turns_per_day - 1));
  push(SafeRatio(std::max(0, config.episode_steps - 1 - step),
                 std::max(1, config.episode_steps - 1)));
  push(SafeRatio(own.money, money_scale));
  push(SafeRatio(opponent.money, money_scale));
  push(SafeRatio(own.money - opponent.money, money_scale));
  push(SafeRatio(own_summary.workers, 16.0));
  push(SafeRatio(opponent_summary.workers, 16.0));
  push(SafeRatio(own_summary.quadrants, 4.0));
  push(SafeRatio(opponent_summary.quadrants, 4.0));
  push(SafeRatio(own_summary.owned, board_cells));
  push(SafeRatio(opponent_summary.owned, board_cells));
  push(SafeRatio(own_summary.empty, board_cells));
  push(SafeRatio(opponent_summary.empty, board_cells));
  push(SafeRatio(own_summary.weeds, board_cells));
  push(SafeRatio(opponent_summary.weeds, board_cells));
  push(SafeRatio(own_summary.crops, board_cells));
  push(SafeRatio(opponent_summary.crops, board_cells));
  push(SafeRatio(own_summary.animals, board_cells));
  push(SafeRatio(opponent_summary.animals, board_cells));
  push(SafeRatio(own_summary.crops_needing_water, board_cells));
  push(SafeRatio(opponent_summary.crops_needing_water, board_cells));
  push(SafeRatio(own_summary.animals_needing_feed, board_cells));
  push(SafeRatio(opponent_summary.animals_needing_feed, board_cells));
  push(SafeRatio(own_summary.crops_ready, board_cells));
  push(SafeRatio(opponent_summary.crops_ready, board_cells));
  push(SafeRatio(own_summary.animals_ready, board_cells));
  push(SafeRatio(opponent_summary.animals_ready, board_cells));
  push(SafeRatio(ShedTotal(priv), config.shed_capacity));
  int64_t carried_total = 0;
  for (int item_index = 0; item_index < kNumItems; ++item_index) {
    carried_total += internal::Carried(priv, item_index);
  }
  push(SafeRatio(carried_total, config.shed_capacity));
  push(SafeRatio(config.max_market_orders, 10.0));
  push(SafeRatio(engine.town_shops().size(), kNumShops));
  push(session.active() ? 1.0F : 0.0F);
  push(SafeRatio(static_cast<int>(session.selected_mode()), 3.0));
  for (int item_index = 0; item_index < kNumItems; ++item_index) {
    push(SafeRatio(priv.shed[item_index], config.shed_capacity));
  }
  for (int crop = 0; crop < kNumCrops; ++crop) {
    push(SafeRatio(priv.seeds[crop], config.shed_capacity));
  }
  for (int item_index = 0; item_index < kNumItems; ++item_index) {
    push(SafeRatio(internal::Carried(priv, item_index), config.shed_capacity));
  }
  for (int product = 0; product < kNumProducts; ++product) {
    push(SafeRatio(engine.market().inventory[product],
                   config.market_params[product].i0));
  }
  for (int product = 0; product < kNumProducts; ++product) {
    push(SafeRatio(engine.market().prices[product],
                   config.market_params[product].base));
  }
  std::array<bool, kNumShops> unlocked{};
  for (int shop : engine.town_shops()) {
    if (shop >= 0 && shop < kNumShops) unlocked[shop] = true;
  }
  for (bool value : unlocked) push(value ? 1.0F : 0.0F);
  if (index != kRootFeatureCount) {
    throw std::logic_error("capability root feature width is inconsistent");
  }
  return out;
}

std::vector<std::string> RootFeatureNames() {
  std::vector<std::string> names = {
      "step_fraction",          "day_fraction",
      "hour_fraction",          "remaining_fraction",
      "own_money",              "opponent_money",
      "money_difference",       "own_workers",
      "opponent_workers",       "own_land",
      "opponent_land",          "own_owned_tiles",
      "opponent_owned_tiles",   "own_empty_tiles",
      "opponent_empty_tiles",   "own_weeds",
      "opponent_weeds",         "own_crops",
      "opponent_crops",         "own_animals",
      "opponent_animals",       "own_crops_needing_water",
      "opponent_crops_needing_water",
      "own_animals_needing_feed",
      "opponent_animals_needing_feed",
      "own_crops_ready",        "opponent_crops_ready",
      "own_animals_ready",      "opponent_animals_ready",
      "own_shed_fill",          "own_carried_fill",
      "market_order_capacity",  "unlocked_shop_fraction",
      "capability_active",      "selected_mode",
  };
  for (const char* item_name : kItemNames) {
    names.push_back(std::string("shed:") + item_name);
  }
  for (int crop = 0; crop < kNumCrops; ++crop) {
    names.push_back(std::string("seed:") + kItemNames[crop]);
  }
  for (const char* item_name : kItemNames) {
    names.push_back(std::string("carried:") + item_name);
  }
  for (int product = 0; product < kNumProducts; ++product) {
    names.push_back(std::string("market_inventory:") + kItemNames[product]);
  }
  for (int product = 0; product < kNumProducts; ++product) {
    names.push_back(std::string("market_price:") + kItemNames[product]);
  }
  for (const ShopData& shop : kShops) {
    names.push_back(std::string("shop:") + shop.name);
  }
  if (static_cast<int>(names.size()) != kRootFeatureCount) {
    throw std::logic_error("capability root feature names have wrong width");
  }
  return names;
}

std::vector<std::string> CandidateFeatureNames() {
  return {
      "mode_direct",          "mode_continue",       "mode_cancel",
      "mode_patch",           "edit_fraction",       "projected_active",
      "target_workers",       "target_land",         "target_crops",
      "target_animals",       "target_products",     "estimated_cost",
      "cash",                 "remaining_fraction",  "deadline_fraction",
      "immediate_feasible",   "service_load",        "heuristic_return",
      "current_workers",      "current_land",        "current_crops",
      "current_animals",      "occupied_fraction",   "shed_fill",
      "buy_magnitude",        "sell_magnitude",      "ensure_fraction",
      "reduce_fraction",      "trade_fraction",      "goal_delta",
      "price_guard",          "urgency",
  };
}

}  // namespace kagg::capability
