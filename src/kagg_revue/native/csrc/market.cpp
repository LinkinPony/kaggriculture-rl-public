// Market pricing and per-unit lockstep settlement (`market_price`,
// `_process_market`, `_commit_unit`, `_do_hire`, `_do_buy_land`).
//
// Floating point discipline: identical operations in identical order as the
// Python source, using the same libm as CPython. Compiled with
// -ffp-contract=off so no FMA fusing changes double results.

#include "market_phase.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <optional>
#include <utility>

#include "engine.hpp"

namespace kagg {
namespace {

double ShapeFn(Shape function, double x, double threshold) {
  x = std::max(0.0, x);
  switch (function) {
    case Shape::kLinear:
      return x;
    case Shape::kSq:
      return x * x;
    case Shape::kSqrt:
      return std::sqrt(x);
    case Shape::kLog:
      return std::log(1.0 + x);
    case Shape::kLog10:
      return std::log10(1.0 + x);
    case Shape::kHinge: {
      if (!(threshold > 0.0)) return x;
      const double scaled = x / threshold;
      return scaled + kHingeGain * std::pow(std::max(0.0, scaled - 1.0), 2.0);
    }
  }
  return x;
}

int64_t PyRound(double x) {
  double rounded = std::round(x);
  if (std::fabs(x - rounded) == 0.5) rounded = 2.0 * std::round(x / 2.0);
  return static_cast<int64_t>(rounded);
}

uint64_t Fib(int n) {
  uint64_t a = 1;
  uint64_t b = 1;
  for (int i = 0; i < n; ++i) {
    const uint64_t next = a + b;
    if (next < b) return UINT64_MAX;
    a = b;
    b = next;
  }
  return a;
}

bool CommitUnit(const Config& config, Farm* farm, PrivateState* priv,
                MarketState* market, OrderKind kind, int item_index, int64_t price) {
  switch (kind) {
    case OrderKind::kSell:
      if (priv->shed[item_index] <= 0) return false;
      priv->shed[item_index] -= 1;
      farm->money += static_cast<double>(price);
      if (price > kPriceFloor) market->inventory[item_index] += 1;
      return true;
    case OrderKind::kBuyProduct:
      if (farm->money < static_cast<double>(price) ||
          ShedTotal(*priv) >= config.shed_capacity) {
        return false;
      }
      farm->money -= static_cast<double>(price);
      priv->shed[item_index] += 1;
      market->inventory[item_index] -= 1;
      return true;
    case OrderKind::kBuySeed:
      if (farm->money < static_cast<double>(price)) return false;
      farm->money -= static_cast<double>(price);
      priv->seeds[item_index] += 1;
      return true;
    case OrderKind::kBuyAnimal:
      if (farm->money < static_cast<double>(price) ||
          ShedTotal(*priv) >= config.shed_capacity) {
        return false;
      }
      farm->money -= static_cast<double>(price);
      priv->shed[item::kGoose + item_index] += 1;
      return true;
    default:
      return false;
  }
}

std::pair<int, int> SpawnHand(const Config& config, const Farm& farm) {
  const auto tiles = ShedAccessTiles(config.board_size);
  std::array<int, 4> occupants{};
  const auto count_position = [&](int x, int y) {
    for (int index = 0; index < 4; ++index) {
      if (tiles[index].first == x && tiles[index].second == y) occupants[index] += 1;
    }
  };
  count_position(farm.farmer_x, farm.farmer_y);
  for (const auto& [x, y] : farm.hands) count_position(x, y);
  int best = 0;
  for (int index = 1; index < 4; ++index) {
    if (occupants[index] < occupants[best]) best = index;
  }
  return tiles[best];
}

bool DoHire(const Config& config, Farm* farm, PrivateState* priv) {
  const double cost = ComputeHirePrice(config, farm->hires_today);
  if (farm->money < cost) return false;
  farm->money -= cost;
  farm->hires_today += 1;
  farm->hands.push_back(SpawnHand(config, *farm));
  priv->inventories.emplace_back();
  return true;
}

bool DoBuyLand(const Config& config, Farm* farm) {
  if (farm->extra_unlocked >= static_cast<int>(kLandOrder.size())) return false;
  const double cost = static_cast<double>(kLandPrices[farm->extra_unlocked]);
  if (farm->money < cost) return false;
  farm->money -= cost;
  const int quadrant = kLandOrder[farm->extra_unlocked];
  farm->extra_unlocked += 1;
  for (int y = 0; y < config.board_size; ++y) {
    for (int x = 0; x < config.board_size; ++x) {
      Tile& tile = farm->tiles[y * config.board_size + x];
      if (QuadrantOf(x, y, config.board_size) == quadrant &&
          tile.kind == TileKind::kLocked) {
        tile = Tile{};
      }
    }
  }
  return true;
}

bool IsAtomic(OrderKind kind) {
  return kind == OrderKind::kHire || kind == OrderKind::kBuyLand;
}

}  // namespace

double ComputeHirePrice(const Config& config, int hires_today) {
  return static_cast<double>(config.farm_hand_cost_mult) * static_cast<double>(Fib(hires_today));
}

int64_t ComputeMarketPrice(const Config& config, int product, int64_t inventory) {
  const MarketParams& params = config.market_params[product];
  double price;
  if (inventory < params.i0) {
    const double amplitude =
        params.below_target * params.base / ShapeFn(params.below_func, params.t, params.t);
    price = params.base +
            amplitude * ShapeFn(params.below_func,
                                static_cast<double>(params.i0 - inventory), params.t);
  } else {
    const double amplitude =
        params.above_target * params.base / ShapeFn(params.above_func, params.t, params.t);
    price = params.base -
            amplitude * ShapeFn(params.above_func,
                                static_cast<double>(inventory - params.i0), params.t);
  }
  return std::max(kPriceFloor, PyRound(price));
}

void RefreshMarketPrices(const Config& config, MarketState* market) {
  for (int item_index = 0; item_index < kNumProducts; ++item_index) {
    market->prices[item_index] =
        ComputeMarketPrice(config, item_index, market->inventory[item_index]);
  }
}

const char* MarketOrderStatusName(MarketOrderStatus status) {
  switch (status) {
    case MarketOrderStatus::kApplied:
      return "applied";
    case MarketOrderStatus::kPartial:
      return "partial";
    case MarketOrderStatus::kRejected:
      return "rejected";
    case MarketOrderStatus::kMalformed:
      return "malformed";
  }
  return "rejected";
}

void ApplyMarketPhase(const Config& config, const std::array<Farm*, 2>& farms,
                      const std::array<PrivateState*, 2>& privates, MarketState* market,
                      const PlayerAction& action0, const PlayerAction& action1,
                      std::vector<MarketSlotTrace>* trace) {
  const std::array<const std::vector<std::optional<MarketOrder>>*, 2> queues = {
      &action0.market, &action1.market};
  const size_t max_length = std::max(queues[0]->size(), queues[1]->size());
  for (size_t slot = 0; slot < max_length; ++slot) {
    std::array<std::optional<MarketOrder>, 2> order_state;
    std::array<int64_t, 2> committed{};
    std::array<std::optional<size_t>, 2> trace_index;
    for (int player = 0; player < 2; ++player) {
      if (slot >= queues[player]->size()) continue;
      order_state[player] = (*queues[player])[slot];
      if (trace != nullptr) {
        trace_index[player] = trace->size();
        MarketSlotTrace entry;
        entry.player = player;
        entry.slot_index = static_cast<int>(slot);
        entry.requested = order_state[player];
        entry.money_before = farms[player]->money;
        entry.shed_total_before = ShedTotal(*privates[player]);
        trace->push_back(entry);
      }
    }

    for (int player = 0; player < 2; ++player) {
      if (!order_state[player]) continue;
      bool success = false;
      if (order_state[player]->kind == OrderKind::kHire) {
        success = DoHire(config, farms[player], privates[player]);
      } else if (order_state[player]->kind == OrderKind::kBuyLand) {
        success = DoBuyLand(config, farms[player]);
      } else {
        continue;
      }
      if (success) committed[player] = 1;
      order_state[player].reset();
    }

    struct Quote {
      OrderKind kind;
      int item;
      int64_t price;
    };
    int iteration_guard = 0;
    while (true) {
      if (++iteration_guard >= kMarketSettlementIterationGuard) break;
      std::array<std::optional<Quote>, 2> quoted;
      for (int player = 0; player < 2; ++player) {
        if (!order_state[player] || order_state[player]->remaining <= 0) continue;
        const OrderKind kind = order_state[player]->kind;
        const int item_index = order_state[player]->item;
        switch (kind) {
          case OrderKind::kSell:
            quoted[player] = Quote{
                kind, item_index,
                ComputeMarketPrice(config, item_index, market->inventory[item_index])};
            break;
          case OrderKind::kBuyProduct:
            if (item_index == item::kWheat || item_index == item::kFertilizer) {
              quoted[player] = Quote{
                  kind, item_index,
                  ComputeMarketPrice(config, item_index,
                                     market->inventory[item_index] - 1)};
            } else {
              order_state[player].reset();
            }
            break;
          case OrderKind::kBuySeed:
            quoted[player] = Quote{kind, item_index, kCrops[item_index].seed_cost};
            break;
          case OrderKind::kBuyAnimal:
            quoted[player] = Quote{kind, item_index, kAnimals[item_index].cost};
            break;
          default:
            order_state[player].reset();
        }
      }
      if (!quoted[0] && !quoted[1]) break;

      bool committed_any = false;
      for (int player = 0; player < 2; ++player) {
        if (!quoted[player]) continue;
        if (CommitUnit(config, farms[player], privates[player], market,
                       quoted[player]->kind, quoted[player]->item,
                       quoted[player]->price)) {
          order_state[player]->remaining -= 1;
          committed[player] += 1;
          committed_any = true;
        } else {
          order_state[player].reset();
        }
      }
      if (!committed_any) break;
    }

    RefreshMarketPrices(config, market);
    if (trace == nullptr) continue;
    for (int player = 0; player < 2; ++player) {
      if (!trace_index[player]) continue;
      MarketSlotTrace& entry = (*trace)[*trace_index[player]];
      entry.committed = committed[player];
      entry.money_after = farms[player]->money;
      entry.shed_total_after = ShedTotal(*privates[player]);
      if (!entry.requested) {
        entry.status = MarketOrderStatus::kMalformed;
      } else if (committed[player] <= 0) {
        entry.status = MarketOrderStatus::kRejected;
      } else {
        entry.actual = entry.requested;
        if (!IsAtomic(entry.requested->kind)) entry.actual->remaining = committed[player];
        entry.status = IsAtomic(entry.requested->kind) ||
                               committed[player] == entry.requested->remaining
                           ? MarketOrderStatus::kApplied
                           : MarketOrderStatus::kPartial;
      }
    }
  }
}

int64_t Engine::MarketPrice(int product, int64_t inventory) const {
  return ComputeMarketPrice(config_, product, inventory);
}

}  // namespace kagg
