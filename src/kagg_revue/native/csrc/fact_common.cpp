#include "fact_common.hpp"

#include <algorithm>
#include <cmath>
#include <limits>

#include "action_codec.hpp"
#include "market_phase.hpp"

namespace kagg::facts::internal {
namespace {

constexpr int kUnreachable = std::numeric_limits<int>::max() / 4;

bool IsMarketConditional(const std::optional<MarketOrder>& order) {
  return order && (order->kind == OrderKind::kSell ||
                   order->kind == OrderKind::kBuyProduct);
}

}  // namespace

float ClampRatio(double value, double scale) {
  if (!(scale > 0.0)) return 0.0F;
  return static_cast<float>(std::clamp(value / scale, -1.0, 1.0));
}

float SignedLog(double value) {
  if (value == 0.0) return 0.0F;
  return static_cast<float>(std::copysign(std::log1p(std::abs(value)) / 12.0,
                                         value));
}

int Manhattan(std::pair<int, int> left, std::pair<int, int> right) {
  return std::abs(left.first - right.first) +
         std::abs(left.second - right.second);
}

std::pair<int, int> UnitPosition(const Farm& farm, int unit_index) {
  if (unit_index <= 0) return {farm.farmer_x, farm.farmer_y};
  const int hand = unit_index - 1;
  if (hand >= static_cast<int>(farm.hands.size())) return {-1, -1};
  return farm.hands[hand];
}

const Inventory* UnitInventory(const PrivateState& priv, int unit_index) {
  if (unit_index < 0 || unit_index >= static_cast<int>(priv.inventories.size())) {
    return nullptr;
  }
  return &priv.inventories[unit_index];
}

int DistanceToShed(std::pair<int, int> position, int board_size) {
  int result = kUnreachable;
  for (const auto& target : ShedAccessTiles(board_size)) {
    result = std::min(result, Manhattan(position, target));
  }
  return result;
}

int EndOfDay(const Config& config, int step) {
  return (step / config.turns_per_day + 1) * config.turns_per_day - 1;
}

int NextProductionStep(const Config& config, const Tile& tile, int step) {
  int start_day;
  int first_day;
  int interval;
  int maximum = std::numeric_limits<int>::max();
  if (tile.kind == TileKind::kPlant && kCrops[tile.crop].ongoing) {
    const CropData& crop = kCrops[tile.crop];
    start_day = tile.planted_day;
    first_day = crop.first_yield_day;
    interval = crop.interval;
    maximum = crop.max_yield;
  } else if (tile.kind == TileKind::kStructure && tile.has_animal) {
    const AnimalData& animal = kAnimals[tile.animal];
    start_day = tile.placed_day;
    first_day = animal.first_yield_day;
    interval = animal.interval;
  } else {
    return -1;
  }
  const int last_day =
      (config.episode_steps + config.turns_per_day - 1) / config.turns_per_day;
  const int current_day = step / config.turns_per_day;
  for (int production_day = current_day; production_day <= last_day;
       ++production_day) {
    const int since_first = production_day - start_day - first_day;
    if (since_first < 0 || since_first % interval != 0) continue;
    const int count = since_first / interval + 1;
    if (count > maximum) return -1;
    const int production_step = production_day * config.turns_per_day - 1;
    if (production_step >= step) return production_step;
  }
  return -1;
}

std::vector<Service> BuildServices(const View& view, const Farm& farm) {
  std::vector<Service> result;
  const int end_of_day = EndOfDay(view.config, view.step);
  const int season_end = std::max(view.step, view.config.episode_steps - 2);
  for (int y = 0; y < view.config.board_size; ++y) {
    for (int x = 0; x < view.config.board_size; ++x) {
      const int tile_index = y * view.config.board_size + x;
      const Tile& tile = farm.tiles[tile_index];
      const auto add = [&](ServiceKind kind, int item, int required_item,
                           std::optional<int> opportunity,
                           std::optional<int> terminal) {
        Service service;
        service.x = x;
        service.y = y;
        service.tile_index = tile_index;
        service.kind = kind;
        service.item = item;
        service.required_item = required_item;
        service.opportunity_deadline = opportunity;
        service.terminal_deadline = terminal;
        if (tile.kind == TileKind::kPlant) {
          const CropData& crop = kCrops[tile.crop];
          service.maturity_step =
              (tile.planted_day + crop.first_yield_day) *
              view.config.turns_per_day;
          service.first_decay_step = tile.max_lifespan_step;
          if (tile.max_lifespan_step >= 0 && tile.yield_units > 0) {
            service.last_positive_step =
                tile.max_lifespan_step + 2 * (tile.yield_units - 1);
          }
        }
        service.production_step = NextProductionStep(view.config, tile, view.step);
        result.push_back(service);
      };

      if (tile.kind == TileKind::kPlant) {
        const CropData& crop = kCrops[tile.crop];
        const int maturity =
            (tile.planted_day + crop.first_yield_day) * view.config.turns_per_day;
        if (!tile.watered_today) {
          const int survival =
              end_of_day + (tile.consecutive_unwatered == 0
                                ? view.config.turns_per_day
                                : 0);
          add(ServiceKind::kWater, tile.crop, -1, end_of_day, survival);
        }
        if (tile.yield_units > 0 && view.step >= maturity) {
          const std::optional<int> first_decay =
              tile.max_lifespan_step >= 0
                  ? std::optional<int>(tile.max_lifespan_step)
                  : std::optional<int>(season_end);
          const std::optional<int> last_positive =
              tile.max_lifespan_step >= 0
                  ? std::optional<int>(tile.max_lifespan_step +
                                       2 * (tile.yield_units - 1))
                  : std::optional<int>(season_end);
          add(ServiceKind::kHarvest, tile.crop, -1,
              first_decay, last_positive);
        }
        add(ServiceKind::kFertilize, item::kFertilizer, item::kFertilizer,
            std::nullopt, std::nullopt);
      } else if (tile.kind == TileKind::kStructure && tile.has_animal) {
        const AnimalData& animal = kAnimals[tile.animal];
        if (!tile.fed_today) {
          const int survival = end_of_day +
                               (tile.consecutive_unfed == 0
                                    ? view.config.turns_per_day
                                    : 0);
          add(ServiceKind::kFeed, animal.product, item::kWheat, end_of_day,
              survival);
        }
        if (tile.yield_units > 0) {
          const int production = NextProductionStep(view.config, tile, view.step);
          const std::optional<int> opportunity =
              production >= 0 && tile.yield_units >= animal.max_held
                  ? std::optional<int>(production)
                  : std::optional<int>(season_end);
          add(ServiceKind::kHarvest, animal.product, -1, opportunity,
              season_end);
        }
        if (!tile.cared_today) {
          add(ServiceKind::kCare, animal.product, -1, end_of_day,
              std::nullopt);
        }
        if (tile.fertilizer_available) {
          add(ServiceKind::kCollect, item::kFertilizer, -1, std::nullopt,
              std::nullopt);
        }
      } else if (tile.kind == TileKind::kWeed) {
        add(ServiceKind::kDig, -1, -1, std::nullopt, std::nullopt);
      } else if (tile.kind == TileKind::kStructure && !tile.has_animal) {
        for (int animal = 0; animal < kNumAnimals; ++animal) {
          if (kAnimals[animal].structure == tile.structure) {
            add(ServiceKind::kPlace, item::kGoose + animal,
                item::kGoose + animal, std::nullopt, std::nullopt);
          }
        }
      }
    }
  }
  for (const auto& [x, y] : ShedAccessTiles(view.config.board_size)) {
    Service service;
    service.x = x;
    service.y = y;
    service.tile_index = y * view.config.board_size + x;
    service.kind = ServiceKind::kShed;
    result.push_back(service);
  }
  return result;
}

int CompletionStep(const View& view, const Farm& farm,
                   const PrivateState& priv, int unit_index,
                   const Service& service) {
  const auto position = UnitPosition(farm, unit_index);
  if (position.first < 0) return kUnreachable;
  const auto target = std::pair(service.x, service.y);
  const Inventory* inventory = UnitInventory(priv, unit_index);
  const bool has_item =
      service.required_item < 0 ||
      (inventory != nullptr && inventory->Get(service.required_item) > 0);
  if (has_item) return view.step + Manhattan(position, target);
  if (service.required_item < 0 || priv.shed[service.required_item] <= 0) {
    return kUnreachable;
  }
  int route = kUnreachable;
  for (const auto& shed : ShedAccessTiles(view.config.board_size)) {
    route = std::min(route, Manhattan(position, shed) +
                                Manhattan(shed, target));
  }
  // Movement to shed, PICKUP, movement to target, interaction.
  return view.step + route + 1;
}

SlackSummary UnitSlack(const View& view, const Farm& farm,
                       const PrivateState& priv, int unit_index) {
  SlackSummary result;
  for (const Service& service : BuildServices(view, farm)) {
    if (!service.terminal_deadline) continue;
    const int completion = CompletionStep(view, farm, priv, unit_index, service);
    if (completion >= kUnreachable) continue;
    const int slack = *service.terminal_deadline - completion;
    if (!result.present || slack < result.minimum) result.minimum = slack;
    result.present = true;
    if (slack >= 0) ++result.reachable;
  }
  return result;
}

ProjectedState ProjectPrefix(const View& view,
                             const std::vector<int64_t>& tokens,
                             const std::vector<int64_t>& quantities,
                             int unit_count) {
  const int decisions = std::min(tokens.size(), quantities.size());
  const PlayerAction decoded = policy::DecodePlayerAction(
      tokens.data(), quantities.data(), decisions, unit_count,
      view.config.max_market_orders);
  const UnitPhaseResult unit = CompileUnitPhase(
      view.config, view.farm, view.priv, decoded,
      view.step / view.config.turns_per_day);
  ProjectedState result{unit.farm, unit.priv, view.market, false};
  if (decoded.market.empty()) return result;

  PlayerAction own;
  own.market = decoded.market;
  PlayerAction opponent;
  Farm other_farm = view.opponent_farm;
  PrivateState other_private;
  std::array<Farm*, 2> farms = {&result.farm, &other_farm};
  std::array<PrivateState*, 2> privates = {&result.priv, &other_private};
  ApplyMarketPhase(view.config, farms, privates, &result.market, own, opponent);
  result.market_conditional =
      std::any_of(decoded.market.begin(), decoded.market.end(),
                  IsMarketConditional);
  return result;
}

int RelevantItem(const UnitAction& action) {
  if (action.op == UnitOp::kPlant) return action.arg;
  if (action.op == UnitOp::kPickup || action.op == UnitOp::kPlace) {
    return action.arg;
  }
  if (action.op == UnitOp::kFeed) return item::kWheat;
  if (action.op == UnitOp::kFertilize ||
      action.op == UnitOp::kCollectFertilizer) {
    return item::kFertilizer;
  }
  return -1;
}

int RelevantItem(const MarketOrder& order) {
  if (order.kind == OrderKind::kBuyAnimal) return item::kGoose + order.item;
  return order.item;
}

std::array<int64_t, kNumProducts> TownConsumption(const View& view) {
  std::array<int64_t, kNumProducts> result{};
  if (view.step % view.config.shop_sell_interval == 0) {
    for (int shop = 0; shop < kNumShops; ++shop) {
      const int64_t instances = view.shop_counts[shop];
      const int64_t multiplier = kShops[shop].n_products == 1 ? 2 : 1;
      for (int product = 0; product < kShops[shop].n_products; ++product) {
        result[kShops[shop].products[product]] += instances * multiplier;
      }
    }
  }
  if (view.step % view.config.center_sell_interval == 0) {
    for (int product = 0; product < kNumProducts; ++product) {
      if (product != item::kFertilizer) ++result[product];
    }
  }
  return result;
}

}  // namespace kagg::facts::internal
