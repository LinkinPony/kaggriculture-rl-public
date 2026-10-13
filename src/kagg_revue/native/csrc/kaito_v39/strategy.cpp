#include "kaito_v39/strategy.hpp"

#include <algorithm>
#include <array>
#include <bit>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <numeric>
#include <utility>
#include <vector>

namespace kagg::kaito_v39 {
namespace {

constexpr uint8_t kBlank = 0;
constexpr uint8_t kPlant = 1;
constexpr uint8_t kWeed = 2;
constexpr uint8_t kCoop = 3;
constexpr uint8_t kPasture = 4;
constexpr uint8_t kWheat = 5;
constexpr uint8_t kGoose = 10;

// v38's feature order differs from the official product order around
// EGG/MILK/WOOL and intentionally uses replay-era normalization prices.
constexpr std::array<int, kNumProducts> kRouterProducts = {
    item::kWheat, item::kCarrot, item::kTomato, item::kStrawberry,
    item::kMelon, item::kMilk, item::kWool, item::kEgg,
    item::kFertilizer,
};
constexpr std::array<double, kNumProducts> kRouterBasePrice = {
    10.0, 16.0, 20.0, 28.0, 36.0, 24.0, 30.0, 18.0, 12.0,
};
constexpr std::array<double, 10> kLineageWeights = {
    8.0, 2.5, 2.0, 1.0, 1.5, 0.25, 1.0, 0.75, 0.5, 0.0,
};
// The frozen v38 router uses COW, SHEEP, GOOSE rather than engine order.
constexpr std::array<int, kNumAnimals> kRouterAnimalIndex = {2, 0, 1};

struct Estimate {
  double first = 0.0;
  double second = 0.0;
  double nearest = std::numeric_limits<double>::infinity();
};

uint8_t KindCode(const Tile& tile) {
  switch (tile.kind) {
    case TileKind::kPlant:
      return kPlant;
    case TileKind::kWeed:
      return kWeed;
    case TileKind::kStructure:
      return tile.structure == StructureKind::kCoop ? kCoop : kPasture;
    case TileKind::kEmpty:
    case TileKind::kLocked:
      return kBlank;
  }
  return kBlank;
}

uint8_t CropCode(const Tile& tile) {
  return tile.kind == TileKind::kPlant
             ? static_cast<uint8_t>(kWheat + tile.crop)
             : kBlank;
}

uint8_t AnimalCode(const Tile& tile) {
  return tile.kind == TileKind::kStructure && tile.has_animal
             ? static_cast<uint8_t>(kGoose + tile.animal)
             : kBlank;
}

uint8_t UnlockMask(const Farm& farm) {
  uint8_t mask = 1U;
  const int count = std::clamp(farm.extra_unlocked, 0,
                               static_cast<int>(kLandOrder.size()));
  for (int index = 0; index < count; ++index) {
    mask |= static_cast<uint8_t>(1U << kLandOrder[index]);
  }
  return mask;
}

void CountAssets(const Farm& farm, std::array<double, 5>* crops,
                 std::array<double, 3>* animals) {
  const size_t limit = std::min<size_t>(25, farm.tiles.size());
  for (size_t index = 0; index < limit; ++index) {
    const Tile& tile = farm.tiles[index];
    if (tile.kind == TileKind::kPlant && tile.crop >= 0 &&
        tile.crop < kNumCrops) {
      ++(*crops)[tile.crop];
    }
    if (tile.kind == TileKind::kStructure && tile.has_animal &&
        tile.animal >= 0 && tile.animal < kNumAnimals) {
      ++(*animals)[kRouterAnimalIndex[tile.animal]];
    }
  }
}

double ScaledL1(const double* left, int left_size, const double* right,
                int right_size, double scale) {
  const int size = std::max({left_size, right_size, 1});
  double total = 0.0;
  for (int index = 0; index < size; ++index) {
    const double left_value = index < left_size ? left[index] : 0.0;
    const double right_value = index < right_size ? right[index] : 0.0;
    total += std::min(4.0, std::abs(left_value - right_value) /
                               std::max(1e-9, scale));
  }
  return total / size;
}

double PartsDistance(const RouterPart& left, const RouterPart& right) {
  int layout_differences = 0;
  for (int index = 0; index < kLayoutWidth; ++index) {
    layout_differences +=
        left.opponent_layout[index] != right.opponent_layout[index];
  }
  const double opponent_layout =
      static_cast<double>(layout_differences) / kLayoutWidth;
  const double opponent_counts =
      ScaledL1(left.opponent_counts.data(), left.opponent_counts.size(),
               right.opponent_counts.data(), right.opponent_counts.size(), 5.0);
  const double opponent_actors = ScaledL1(
      left.opponent_actors.data(), left.opponent_actor_count,
      right.opponent_actors.data(), right.opponent_actor_count, 8.0);
  const double opponent_money = std::min(
      4.0, std::abs(std::log1p(std::max(0.0, left.opponent_money)) -
                         std::log1p(std::max(0.0, right.opponent_money))) /
               4.0);
  const double opponent_unlocks =
      static_cast<double>(std::popcount(static_cast<unsigned int>(
          left.opponent_unlocks ^ right.opponent_unlocks))) /
      4.0;
  double own_state = ScaledL1(left.own_state.data(), left.own_state.size(),
                             right.own_state.data(), right.own_state.size(),
                             10.0);
  own_state +=
      std::min(4.0, std::abs(left.own_state[0] - right.own_state[0]) / 1000.0);
  own_state /= 2.0;

  double prices = 0.0;
  for (int index = 0; index < kNumProducts; ++index) {
    prices += std::abs(left.prices[index] - right.prices[index]) /
              std::max(1.0, kRouterBasePrice[index]);
  }
  prices /= kNumProducts;
  const double market_inventory =
      ScaledL1(left.inventory.data(), left.inventory.size(),
               right.inventory.data(), right.inventory.size(), 100.0);

  int shop_union = 0;
  int shop_difference = 0;
  for (int shop = 0; shop < kNumShops; ++shop) {
    if (left.shops[shop] > 0 || right.shops[shop] > 0) ++shop_union;
    shop_difference += std::abs(static_cast<int>(left.shops[shop]) -
                                static_cast<int>(right.shops[shop]));
  }
  const double shops = static_cast<double>(shop_difference) /
                       std::max(2, shop_union * 2);
  const double seat = left.seat != right.seat ? 1.0 : 0.0;
  const std::array<double, 10> parts = {
      opponent_layout, opponent_counts, opponent_actors, opponent_money,
      opponent_unlocks, own_state, prices, market_inventory, shops, seat,
  };
  double total = 0.0;
  for (size_t index = 0; index < parts.size(); ++index) {
    total += kLineageWeights[index] * parts[index];
  }
  return total;
}

double Utility(double margin, double win_weight) {
  const double outcome = margin > 0.0 ? 1.0 : (margin == 0.0 ? 0.5 : 0.0);
  return outcome * win_weight + std::clamp(margin, -20000.0, 20000.0);
}

Estimate EstimatePopulation(const Portfolio& portfolio,
                            const std::vector<Prototype>& population,
                            const RouterPart& current, int neighbors,
                            double win_weight, double distance_floor) {
  struct Row {
    double distance;
    size_t index;
  };
  std::vector<Row> rows;
  rows.reserve(population.size());
  for (size_t index = 0; index < population.size(); ++index) {
    rows.push_back(Row{
        PartsDistance(current, portfolio.part(population[index].part_index)),
        index,
    });
  }
  std::stable_sort(rows.begin(), rows.end(),
                   [](const Row& left, const Row& right) {
                     return left.distance < right.distance;
                   });
  const int count = std::max(
      1, std::min(neighbors, static_cast<int>(rows.size())));
  Estimate result;
  result.nearest = rows.front().distance;
  double total_weight = 0.0;
  for (int rank = 0; rank < count; ++rank) {
    const Row& row = rows[rank];
    const Prototype& prototype = population[row.index];
    const double weight =
        1.0 / (std::max(1e-6, distance_floor) + row.distance);
    result.first += weight * Utility(prototype.margins[0], win_weight);
    result.second += weight * Utility(prototype.margins[1], win_weight);
    total_weight += weight;
  }
  result.first /= std::max(total_weight, 1e-9);
  result.second /= std::max(total_weight, 1e-9);
  return result;
}

Estimate EstimateHistory(
    const Portfolio& portfolio,
    const std::array<std::optional<RouterPart>, kHistoryCheckpoints>& history) {
  struct Row {
    double distance;
    size_t index;
  };
  std::vector<Row> rows;
  rows.reserve(portfolio.stage2().size());
  for (size_t index = 0; index < portfolio.stage2().size(); ++index) {
    const HistoryPrototype& prototype = portfolio.stage2()[index];
    double current = PartsDistance(
        *history[kHistoryCheckpoints - 1],
        portfolio.part(prototype.part_indices[kHistoryCheckpoints - 1]));
    double historical = 0.0;
    int historical_count = 0;
    for (int checkpoint = 0; checkpoint < kHistoryCheckpoints - 1;
         ++checkpoint) {
      if (!history[checkpoint].has_value() ||
          prototype.part_indices[checkpoint] < 0) {
        continue;
      }
      historical += PartsDistance(
          *history[checkpoint], portfolio.part(prototype.part_indices[checkpoint]));
      ++historical_count;
    }
    if (historical_count > 0) historical /= historical_count;
    rows.push_back(Row{current + 0.5 * historical, index});
  }
  std::stable_sort(rows.begin(), rows.end(),
                   [](const Row& left, const Row& right) {
                     return left.distance < right.distance;
                   });
  const Row& selected = rows.front();
  const HistoryPrototype& prototype = portfolio.stage2()[selected.index];
  const double weight = 1.0 / (0.05 + selected.distance);
  Estimate result;
  result.nearest = selected.distance;
  result.first = weight * Utility(prototype.margins[0], 50000.0) / weight;
  result.second = weight * Utility(prototype.margins[1], 50000.0) / weight;
  return result;
}

}  // namespace

RouterPart ExtractRouterPart(const Engine& engine, int player) {
  RouterPart result;
  const Farm& own = engine.farm(player);
  const Farm& opponent = engine.farm(1 - player);
  const size_t opponent_limit = std::min<size_t>(25, opponent.tiles.size());
  for (size_t index = 0; index < opponent_limit; ++index) {
    const Tile& tile = opponent.tiles[index];
    result.opponent_layout[index] = KindCode(tile);
    result.opponent_layout[25 + index] = CropCode(tile);
    result.opponent_layout[50 + index] = AnimalCode(tile);
  }
  std::array<double, 5> opponent_crops{};
  std::array<double, 3> opponent_animals{};
  CountAssets(opponent, &opponent_crops, &opponent_animals);
  std::copy(opponent_crops.begin(), opponent_crops.end(),
            result.opponent_counts.begin());
  std::copy(opponent_animals.begin(), opponent_animals.end(),
            result.opponent_counts.begin() + opponent_crops.size());

  result.opponent_actors[0] = opponent.hands.size();
  int actor_offset = 1;
  const auto add_position = [&result, &actor_offset](int x, int y) {
    result.opponent_actors[actor_offset++] = x;
    result.opponent_actors[actor_offset++] = y;
  };
  add_position(opponent.farmer_x, opponent.farmer_y);
  const int hand_limit =
      std::min<int>(8, static_cast<int>(opponent.hands.size()));
  for (int index = 0; index < hand_limit; ++index) {
    add_position(opponent.hands[index].first, opponent.hands[index].second);
  }
  result.opponent_actor_count = actor_offset;
  result.opponent_money = opponent.money;
  result.opponent_unlocks = UnlockMask(opponent);

  std::array<double, 5> own_crops{};
  std::array<double, 3> own_animals{};
  CountAssets(own, &own_crops, &own_animals);
  result.own_state[0] = own.money;
  result.own_state[1] = own.hands.size();
  std::copy(own_crops.begin(), own_crops.end(), result.own_state.begin() + 2);
  std::copy(own_animals.begin(), own_animals.end(),
            result.own_state.begin() + 2 + own_crops.size());

  for (int index = 0; index < kNumProducts; ++index) {
    const int product = kRouterProducts[index];
    result.prices[index] = engine.market().prices[product];
    result.inventory[index] = engine.market().inventory[product];
  }
  for (const int shop : engine.town_shops()) {
    if (shop >= 0 && shop < kNumShops && result.shops[shop] < UINT8_MAX) {
      ++result.shops[shop];
    }
  }
  result.seat = static_cast<uint8_t>(player);
  return result;
}

Route SelectNestedRoute(const Portfolio& portfolio,
                        const RouterPart& current) {
  const Estimate estimate = EstimatePopulation(
      portfolio, portfolio.nested(), current, 5, 20000.0, 0.05);
  if (estimate.nearest > 0.75) return Route::kV36;
  return estimate.first >= estimate.second + 10000.0 ? Route::kV36
                                                      : Route::kV37;
}

bool SelectStage1Wool(const Portfolio& portfolio,
                      const RouterPart& current) {
  const Estimate fallback = EstimatePopulation(
      portfolio, portfolio.fallback(), current, 9, 50000.0, 0.05);
  bool wool = fallback.nearest <= 0.1 && fallback.second >= fallback.first;
  const Estimate live = EstimatePopulation(
      portfolio, portfolio.stage1(), current, 9, 100000.0, 0.05);
  if (live.nearest <= 0.0) {
    wool = live.second >= live.first + 3000.0;
  }
  return wool;
}

bool SelectStage2Alt(
    const Portfolio& portfolio,
    const std::array<std::optional<RouterPart>, kHistoryCheckpoints>& history) {
  if (!history[kHistoryCheckpoints - 1].has_value()) return false;
  const Estimate estimate = EstimateHistory(portfolio, history);
  return estimate.nearest <= 0.0 &&
         estimate.second >= estimate.first + 3000.0;
}

}  // namespace kagg::kaito_v39
