#include <algorithm>
#include <cmath>
#include <cstring>

#include "market_phase.hpp"
#include "opponents/kaito.hpp"

namespace kagg::opponents {
namespace {

double Revenue(int item, int64_t inventory, int64_t quantity) {
  static const Config kFrozenMarket;
  int64_t value = 0;
  for (int64_t i = 0; i < quantity; ++i) {
    const int64_t price = ComputeMarketPrice(kFrozenMarket, item, inventory);
    value += price;
    if (price > 1) ++inventory;
  }
  return value;
}

std::array<double, kNumProducts> Exposure(const Farm& farm) {
  std::array<double, kNumProducts> result{};
  for (const auto& tile : farm.tiles) {
    if (tile.kind == TileKind::kPlant)
      result[tile.crop] += std::max(1, tile.yield_units);
    if (tile.kind == TileKind::kStructure && tile.has_animal) {
      result[kAnimals[tile.animal].product] += std::max(1, tile.yield_units);
      if (tile.fertilizer_available) result[item::kFertilizer] += 1.0;
    }
  }
  return result;
}

struct Candidate {
  double delta;
  double gross;
  int item;
  int64_t scheduled;
  std::array<int64_t, 2> allocations;
};

}  // namespace

void Kaito::Preempt(const Engine& engine, int player, int route,
                    PlayerAction* action, Controller* state) {
  const int step = engine.step_index();
  if (step < 72 || step >= 700 || action->market.size() >= 10) return;
  const double deficit =
      engine.farm(1 - player).money - engine.farm(player).money;
  if (!state->near && deficit < 4000.0 &&
      *std::max_element(state->supply.begin(), state->supply.end()) < 3.0)
    return;
  const auto exposure = Exposure(engine.farm(1 - player));
  const auto projected = ProjectShed(engine, player, *action, true, true,
                                     engine.config().shed_capacity, 0);
  const auto existing = SellTotals(*action);
  std::vector<Candidate> candidates;
  for (int item = item::kCarrot; item <= item::kWool; ++item) {
    int64_t available = std::min<int64_t>(
        8, std::max<int64_t>(0, projected[item] - existing[item]));
    if (available <= 0) continue;
    std::array<int64_t, 2> allocations{};
    int64_t scheduled = 0;
    for (int offset = 1; offset <= 2 && step + offset < 719; ++offset) {
      const auto found = state->due.find(step + offset);
      const int64_t debt = found == state->due.end() ? 0 : found->second[item];
      const auto sold = SellTotals(portfolio_->Action(route, step + offset));
      const int64_t quantity =
          std::min(available, std::max<int64_t>(0, sold[item] - debt));
      allocations[offset - 1] = quantity;
      scheduled += quantity;
      available -= quantity;
    }
    if (scheduled <= 0 ||
        engine.market().prices[item] / kDefaultMarketParams[item].base < 0.45)
      continue;
    double forecast = 2 * (state->supply[item] + 0.08 * exposure[item]);
    if (state->near && state->evidence >= 2 && state->confidence >= 0.3)
      forecast += state->confidence * scheduled;
    int demand = 0;
    for (int offset = 0; offset < 2; ++offset) {
      demand += Demand(engine.town_shops(), item, step + offset,
                       engine.config().shop_sell_interval,
                       engine.config().center_sell_interval);
    }
    const int64_t inventory = engine.market().inventory[item] == 0
                                  ? 10000
                                  : engine.market().inventory[item];
    // nearbyint preserves Python's ties-to-even rounding under the default FP
    // mode.
    const int64_t future =
        static_cast<int64_t>(std::nearbyint(inventory + forecast - demand));
    const double now = Revenue(item, inventory, scheduled);
    const double delta = now - Revenue(item, future, scheduled);
    if (delta >= 8.0)
      candidates.push_back({delta, now, item, scheduled, allocations});
  }
  std::sort(candidates.begin(), candidates.end(),
            [](const auto& a, const auto& b) {
              if (a.delta != b.delta) return a.delta > b.delta;
              if (a.gross != b.gross) return a.gross > b.gross;
              return std::strcmp(kItemNames[a.item], kItemNames[b.item]) > 0;
            });
  int64_t remaining = 8;
  std::vector<std::optional<MarketOrder>> additions;
  for (const auto& candidate : candidates) {
    if (action->market.size() + additions.size() >= 10 || remaining <= 0) break;
    const int64_t quantity = std::min(candidate.scheduled, remaining);
    additions.push_back(
        MarketOrder{OrderKind::kSell, candidate.item, quantity});
    int64_t left = quantity;
    for (int offset = 1; offset <= 2; ++offset) {
      const int64_t allocated =
          std::min(left, candidate.allocations[offset - 1]);
      if (allocated > 0) state->due[step + offset][candidate.item] += allocated;
      left -= allocated;
    }
    remaining -= quantity;
  }
  action->market.insert(action->market.begin(), additions.begin(),
                        additions.end());
}

}  // namespace kagg::opponents
