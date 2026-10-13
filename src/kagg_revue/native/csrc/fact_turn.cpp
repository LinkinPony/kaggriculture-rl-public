#include "derived_facts.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <limits>
#include <set>
#include <utility>
#include <vector>

#include "fact_common.hpp"
#include "market_phase.hpp"

namespace kagg::facts {
namespace {

using Fact = std::array<float, kTurnFactFeatures>;
using internal::Service;

enum Feature : int {
  kPresent = 0,
  kAssetType = 1,
  kUnitServiceType = 2,
  kMarketType = 3,
  kFeasibilityType = 4,
  kItemFirst = 5,
  kServiceFirst = 17,
  kUnitSlot = 26,
  kX = 27,
  kY = 28,
  kDx = 29,
  kDy = 30,
  kDistance = 31,
  kShedDistance = 32,
  kOpportunity = 33,
  kResourceRequired = 34,
  kResourceAvailable = 35,
  kOpportunityDeadline = 36,
  kOpportunityTurns = 37,
  kTerminalDeadline = 38,
  kTerminalTurns = 39,
  kArrivalSlack = 40,
  kReachable = 41,
  kMaturityTurns = 42,
  kProductionTurns = 43,
  kFirstDecayTurns = 44,
  kLastPositiveTurns = 45,
  kYield = 46,
  kWatered = 47,
  kFed = 48,
  kCared = 49,
  kFertilizerAvailable = 50,
  kPendingBonus = 51,
  kMinimumUnitDistance = 52,
  kSecondUnitDistance = 53,
  kCoverageCount = 54,
  kMatchingCritical = 55,
  kMatchingSelected = 56,
  kMarketInventory = 57,
  kCurrentPrice = 58,
  kOwnStock = 59,
  kNextShopTurns = 60,
  kShopAmount = 61,
  kNextCenterTurns = 62,
  kCenterAmount = 63,
  kMarginalOne = 64,
  kAverageTwo = 65,
  kAverageFour = 66,
  kAverageEight = 67,
  kAverageSixteen = 68,
  kAverageAvailable = 69,
  kUnitsToFloorOrCap = 70,
  kFloorReached = 71,
  kOpponentLower = 72,
  kOpponentUpper = 73,
};

struct FloorDistance {
  int64_t units = 0;
  bool reached = false;
};

void SetItem(int item_index, Fact* fact) {
  if (item_index >= 0 && item_index < kNumItems) {
    (*fact)[kItemFirst + item_index] = 1.0F;
  }
}

void FillTile(const View& view, const Tile& tile, Fact* fact) {
  if (tile.kind == TileKind::kPlant) {
    const CropData& crop = kCrops[tile.crop];
    SetItem(tile.crop, fact);
    (*fact)[kMaturityTurns] = internal::ClampRatio(
        (tile.planted_day + crop.first_yield_day) * view.config.turns_per_day -
            view.step,
        view.config.episode_steps);
    (*fact)[kWatered] = tile.watered_today ? 1.0F : 0.0F;
  } else if (tile.kind == TileKind::kStructure && tile.has_animal) {
    SetItem(kAnimals[tile.animal].product, fact);
    (*fact)[kFed] = tile.fed_today ? 1.0F : 0.0F;
    (*fact)[kCared] = tile.cared_today ? 1.0F : 0.0F;
    (*fact)[kFertilizerAvailable] =
        tile.fertilizer_available ? 1.0F : 0.0F;
    (*fact)[kPendingBonus] =
        internal::ClampRatio(tile.pending_care_bonus, 8.0);
  }
  (*fact)[kYield] = internal::ClampRatio(tile.yield_units, 8.0);
  const int production =
      internal::NextProductionStep(view.config, tile, view.step);
  if (production >= 0) {
    (*fact)[kProductionTurns] = internal::ClampRatio(
        production - view.step, view.config.episode_steps);
  }
  if (tile.kind == TileKind::kPlant && tile.max_lifespan_step >= 0) {
    (*fact)[kFirstDecayTurns] = internal::ClampRatio(
        tile.max_lifespan_step - view.step, view.config.episode_steps);
    if (tile.yield_units > 0) {
      (*fact)[kLastPositiveTurns] = internal::ClampRatio(
          tile.max_lifespan_step + 2 * (tile.yield_units - 1) - view.step,
          view.config.episode_steps);
    }
  }
}

int UnitCount(const View& view, const Farm& farm) {
  return std::min(view.unit_limit, 1 + static_cast<int>(farm.hands.size()));
}

bool MatchTask(const View& view, const std::vector<Service>& services,
               int task, int excluded, std::vector<int>* unit_match,
               std::vector<uint8_t>* seen) {
  const Service& service = services[task];
  if (!service.terminal_deadline || task == excluded) return false;
  const int units = UnitCount(view, view.farm);
  for (int unit = 0; unit < units; ++unit) {
    if ((*seen)[unit]) continue;
    const int completion = internal::CompletionStep(
        view, view.farm, view.priv, unit, service);
    if (completion > *service.terminal_deadline) continue;
    (*seen)[unit] = 1;
    if ((*unit_match)[unit] < 0 ||
        MatchTask(view, services, (*unit_match)[unit], excluded, unit_match,
                  seen)) {
      (*unit_match)[unit] = task;
      return true;
    }
  }
  return false;
}

int MaximumRelaxedMatching(const View& view,
                           const std::vector<Service>& services, int excluded,
                           std::vector<uint8_t>* selected) {
  const int units = UnitCount(view, view.farm);
  std::vector<int> unit_match(units, -1);
  int result = 0;
  for (int task = 0; task < static_cast<int>(services.size()); ++task) {
    std::vector<uint8_t> seen(units, 0);
    if (MatchTask(view, services, task, excluded, &unit_match, &seen)) ++result;
  }
  if (selected != nullptr) {
    selected->assign(services.size(), 0);
    for (int task : unit_match) {
      if (task >= 0) (*selected)[task] = 1;
    }
  }
  return result;
}

std::vector<int> CoverageCounts(const View& view,
                                const std::vector<Service>& services) {
  std::vector<int> result(services.size(), 0);
  const int units = UnitCount(view, view.farm);
  for (int task = 0; task < static_cast<int>(services.size()); ++task) {
    if (!services[task].terminal_deadline) continue;
    for (int unit = 0; unit < units; ++unit) {
      if (internal::CompletionStep(view, view.farm, view.priv, unit,
                                   services[task]) <=
          *services[task].terminal_deadline) {
        ++result[task];
      }
    }
  }
  return result;
}

double SellRevenue(const Config& config, int product, int64_t inventory,
                   int64_t quantity) {
  double result = 0.0;
  for (int64_t unit = 0; unit < quantity; ++unit) {
    const int64_t price = ComputeMarketPrice(config, product, inventory);
    result += static_cast<double>(price);
    if (price > kPriceFloor) ++inventory;
  }
  return result;
}

FloorDistance UnitsToFloor(const Config& config, int product,
                           int64_t inventory) {
  if (ComputeMarketPrice(config, product, inventory) <= kPriceFloor) {
    return FloorDistance{0, true};
  }
  if (ComputeMarketPrice(config, product,
                         inventory + kMaxMarketUnitsPerSlot) > kPriceFloor) {
    return FloorDistance{kMaxMarketUnitsPerSlot, false};
  }
  int64_t lower = 0;
  int64_t upper = kMaxMarketUnitsPerSlot;
  while (lower + 1 < upper) {
    const int64_t middle = lower + (upper - lower) / 2;
    if (ComputeMarketPrice(config, product, inventory + middle) >
        kPriceFloor) {
      lower = middle;
    } else {
      upper = middle;
    }
  }
  return FloorDistance{upper, true};
}

int StepsUntil(int step, int interval) {
  return (interval - step % interval) % interval;
}

std::array<int64_t, kNumProducts> ShopAmounts(const View& view) {
  std::array<int64_t, kNumProducts> result{};
  for (int shop = 0; shop < kNumShops; ++shop) {
    const int64_t instances = view.shop_counts[shop];
    const int64_t multiplier = kShops[shop].n_products == 1 ? 2 : 1;
    for (int index = 0; index < kShops[shop].n_products; ++index) {
      result[kShops[shop].products[index]] += instances * multiplier;
    }
  }
  return result;
}

}  // namespace

std::vector<float> EncodeTurnFacts(
    const View& view,
    const std::array<int64_t, kNumProducts>& opponent_lower,
    const std::array<int64_t, kNumProducts>& opponent_upper,
    int* token_count) {
  const std::vector<internal::Service> services =
      internal::BuildServices(view, view.farm);
  const std::vector<int> coverage = CoverageCounts(view, services);
  std::vector<uint8_t> selected;
  const int maximum = MaximumRelaxedMatching(view, services, -1, &selected);
  std::vector<uint8_t> critical(services.size(), 0);
  for (int task = 0; task < static_cast<int>(services.size()); ++task) {
    if (services[task].terminal_deadline &&
        MaximumRelaxedMatching(view, services, task, nullptr) < maximum) {
      critical[task] = 1;
    }
  }

  std::vector<Fact> facts;
  for (int y = 0; y < view.config.board_size; ++y) {
    for (int x = 0; x < view.config.board_size; ++x) {
      const Tile& tile = view.farm.tiles[y * view.config.board_size + x];
      if (tile.kind == TileKind::kEmpty || tile.kind == TileKind::kLocked) {
        continue;
      }
      Fact fact{};
      fact[kPresent] = 1.0F;
      fact[kAssetType] = 1.0F;
      fact[kX] = internal::ClampRatio(x, view.config.board_size - 1);
      fact[kY] = internal::ClampRatio(y, view.config.board_size - 1);
      FillTile(view, tile, &fact);
      int first = std::numeric_limits<int>::max();
      int second = std::numeric_limits<int>::max();
      for (int unit = 0; unit < UnitCount(view, view.farm); ++unit) {
        const int distance = internal::Manhattan(
            internal::UnitPosition(view.farm, unit), {x, y});
        if (distance < first) {
          second = first;
          first = distance;
        } else if (distance < second) {
          second = distance;
        }
      }
      if (first != std::numeric_limits<int>::max()) {
        fact[kMinimumUnitDistance] = internal::ClampRatio(
            first, 2 * (view.config.board_size - 1));
      }
      if (second != std::numeric_limits<int>::max()) {
        fact[kSecondUnitDistance] = internal::ClampRatio(
            second, 2 * (view.config.board_size - 1));
      }
      facts.push_back(fact);
    }
  }

  for (int task = 0; task < static_cast<int>(services.size()); ++task) {
    const Service& service = services[task];
    const Tile& tile = view.farm.tiles[service.tile_index];
    for (int unit = 0; unit < UnitCount(view, view.farm); ++unit) {
      Fact fact{};
      fact[kPresent] = 1.0F;
      fact[kUnitServiceType] = 1.0F;
      SetItem(service.item, &fact);
      fact[kServiceFirst + static_cast<int>(service.kind)] = 1.0F;
      fact[kUnitSlot] = internal::ClampRatio(unit, std::max(1, view.unit_limit - 1));
      fact[kX] = internal::ClampRatio(service.x, view.config.board_size - 1);
      fact[kY] = internal::ClampRatio(service.y, view.config.board_size - 1);
      const auto position = internal::UnitPosition(view.farm, unit);
      fact[kDx] = internal::ClampRatio(
          service.x - position.first, view.config.board_size - 1);
      fact[kDy] = internal::ClampRatio(
          service.y - position.second, view.config.board_size - 1);
      fact[kDistance] = internal::ClampRatio(
          internal::Manhattan(position, {service.x, service.y}),
          2 * (view.config.board_size - 1));
      fact[kShedDistance] = internal::ClampRatio(
          internal::DistanceToShed(position, view.config.board_size),
          view.config.board_size);
      fact[kOpportunity] = 1.0F;
      fact[kResourceRequired] = service.required_item >= 0 ? 1.0F : 0.0F;
      const Inventory* inventory = internal::UnitInventory(view.priv, unit);
      fact[kResourceAvailable] =
          service.required_item < 0 ||
                  (inventory != nullptr &&
                   inventory->Get(service.required_item) > 0) ||
                  view.priv.shed[service.required_item] > 0
              ? 1.0F
              : 0.0F;
      if (service.opportunity_deadline) {
        fact[kOpportunityDeadline] = 1.0F;
        fact[kOpportunityTurns] = internal::ClampRatio(
            *service.opportunity_deadline - view.step,
            view.config.episode_steps);
      }
      if (service.terminal_deadline) {
        fact[kTerminalDeadline] = 1.0F;
        fact[kTerminalTurns] = internal::ClampRatio(
            *service.terminal_deadline - view.step,
            view.config.episode_steps);
        const int completion = internal::CompletionStep(
            view, view.farm, view.priv, unit, service);
        if (completion < std::numeric_limits<int>::max() / 4) {
          const int slack = *service.terminal_deadline - completion;
          fact[kArrivalSlack] = internal::ClampRatio(
              slack, view.config.episode_steps);
          fact[kReachable] = slack >= 0 ? 1.0F : 0.0F;
        }
      }
      if (service.kind != internal::ServiceKind::kShed) {
        FillTile(view, tile, &fact);
      }
      fact[kCoverageCount] = internal::ClampRatio(
          coverage[task], std::max(1, UnitCount(view, view.farm)));
      fact[kMatchingCritical] = critical[task] ? 1.0F : 0.0F;
      fact[kMatchingSelected] = selected[task] ? 1.0F : 0.0F;
      facts.push_back(fact);
    }
  }

  const auto shop_amounts = ShopAmounts(view);
  for (int product = 0; product < kNumProducts; ++product) {
    Fact fact{};
    fact[kPresent] = 1.0F;
    fact[kMarketType] = 1.0F;
    SetItem(product, &fact);
    const MarketParams& params = view.config.market_params[product];
    const int64_t inventory = view.market.inventory[product];
    const double base = std::max(1.0, params.base);
    fact[kMarketInventory] = internal::ClampRatio(
        static_cast<double>(inventory - params.i0), 8.0 * params.t);
    fact[kCurrentPrice] = internal::ClampRatio(
        view.market.prices[product], 5.0 * base);
    const int64_t stock = std::max<int64_t>(0, view.priv.shed[product]);
    fact[kOwnStock] = internal::SignedLog(stock);
    fact[kNextShopTurns] = internal::ClampRatio(
        StepsUntil(view.step, view.config.shop_sell_interval),
        view.config.shop_sell_interval);
    fact[kShopAmount] = internal::SignedLog(shop_amounts[product]);
    fact[kNextCenterTurns] = internal::ClampRatio(
        StepsUntil(view.step, view.config.center_sell_interval),
        view.config.center_sell_interval);
    fact[kCenterAmount] = product == item::kFertilizer ? 0.0F : 1.0F;
    const auto normalized_average = [&](int64_t quantity) {
      if (quantity <= 0) return 0.0F;
      return internal::ClampRatio(
          SellRevenue(view.config, product, inventory, quantity) / quantity,
          5.0 * base);
    };
    fact[kMarginalOne] = normalized_average(1);
    fact[kAverageTwo] = normalized_average(2);
    fact[kAverageFour] = normalized_average(4);
    fact[kAverageEight] = normalized_average(8);
    fact[kAverageSixteen] = normalized_average(16);
    fact[kAverageAvailable] = normalized_average(
        std::min<int64_t>(stock, kMaxMarketUnitsPerSlot));
    const FloorDistance floor =
        UnitsToFloor(view.config, product, inventory);
    fact[kUnitsToFloorOrCap] = internal::SignedLog(floor.units);
    fact[kFloorReached] = floor.reached ? 1.0F : 0.0F;
    fact[kOpponentLower] =
        internal::SignedLog(std::max<int64_t>(0, opponent_lower[product]));
    fact[kOpponentUpper] = internal::SignedLog(
        std::max(opponent_lower[product], opponent_upper[product]));
    facts.push_back(fact);
  }

  Fact feasibility{};
  feasibility[kPresent] = 1.0F;
  feasibility[kFeasibilityType] = 1.0F;
  const int finite_tasks = static_cast<int>(std::count_if(
      services.begin(), services.end(),
      [](const Service& service) { return service.terminal_deadline.has_value(); }));
  feasibility[kCoverageCount] = internal::ClampRatio(
      finite_tasks, std::max(1, view.config.board_size * view.config.board_size));
  feasibility[kMatchingSelected] = internal::ClampRatio(
      maximum, std::max(1, finite_tasks));
  facts.push_back(feasibility);

  std::vector<float> result;
  result.reserve(facts.size() * kTurnFactFeatures);
  for (const Fact& fact : facts) result.insert(result.end(), fact.begin(), fact.end());
  *token_count = static_cast<int>(facts.size());
  return result;
}

FlowSnapshot MakeFlowSnapshot(const View& view) {
  FlowSnapshot result;
  result.step = view.step;
  result.market_inventory = view.market.inventory;
  result.town_consumption = internal::TownConsumption(view);
  std::set<int> occupied_tiles;
  const int day = view.step / view.config.turns_per_day;
  const int opponent_units = 1 + static_cast<int>(view.opponent_farm.hands.size());
  for (int unit = 0; unit < opponent_units; ++unit) {
    const auto [x, y] = internal::UnitPosition(view.opponent_farm, unit);
    if (x < 0 || y < 0) continue;
    const int tile_index = y * view.config.board_size + x;
    if (!occupied_tiles.insert(tile_index).second) continue;
    const Tile& tile = view.opponent_farm.tiles[tile_index];
    if (tile.kind == TileKind::kPlant && tile.yield_units > 0 &&
        day - tile.planted_day >= kCrops[tile.crop].first_yield_day) {
      result.opponent_unit_gain_upper[tile.crop] += tile.yield_units;
    } else if (tile.kind == TileKind::kStructure && tile.has_animal) {
      if (tile.yield_units > 0) {
        result.opponent_unit_gain_upper[kAnimals[tile.animal].product] +=
            tile.yield_units;
      }
      if (tile.fertilizer_available) {
        ++result.opponent_unit_gain_upper[item::kFertilizer];
      }
    }
  }
  return result;
}

std::vector<std::string> TurnFactNames() {
  return {
      "present", "type_asset", "type_unit_service", "type_market",
      "type_relaxed_feasibility", "item_wheat", "item_carrot",
      "item_tomato", "item_strawberry", "item_melon", "item_egg",
      "item_milk", "item_wool", "item_fertilizer", "item_goose",
      "item_cow", "item_sheep", "service_water", "service_harvest",
      "service_fertilize", "service_feed", "service_care",
      "service_collect_fertilizer", "service_dig", "service_place",
      "service_shed", "unit_slot", "x", "y", "relative_x",
      "relative_y", "manhattan_distance", "distance_to_shed",
      "opportunity_available", "resource_required", "resource_available",
      "opportunity_deadline_present", "turns_to_opportunity_deadline",
      "terminal_deadline_present", "turns_to_terminal_deadline",
      "arrival_slack", "reachable", "turns_to_maturity",
      "turns_to_next_production", "turns_to_first_decay",
      "turns_to_last_positive_yield", "yield_units", "watered", "fed",
      "cared", "fertilizer_available", "pending_care_bonus",
      "minimum_unit_distance", "second_unit_distance",
      "relaxed_coverage_count", "relaxed_matching_critical",
      "relaxed_matching_selected", "market_inventory", "current_price",
      "own_sellable_stock", "turns_to_shop_consumption",
      "shop_consumption_amount", "turns_to_center_consumption",
      "center_consumption_amount", "sell_marginal_one", "sell_average_two",
      "sell_average_four", "sell_average_eight", "sell_average_sixteen",
      "sell_average_available_in_slot", "sell_units_to_floor_or_slot_cap",
      "sell_floor_reached_within_slot", "opponent_product_lower_bound",
      "opponent_product_upper_bound"};
}

}  // namespace kagg::facts
