#include "derived/features.hpp"

#include <algorithm>

#include "market_phase.hpp"

namespace kagg::derived {

double Sell(const Config& config, int product, int64_t inventory, int64_t amount) {
  double cash = 0;
  for (int64_t index = 0; index < amount; ++index) {
    const int64_t price = ComputeMarketPrice(config, product, inventory);
    if (price == 1) return cash + amount - index;
    cash += price;
    ++inventory;
  }
  return cash;
}

double Buy(const Config& config, int product, int64_t inventory, int64_t amount) {
  double cash = 0;
  for (int64_t index = 0; index < amount; ++index) {
    cash += ComputeMarketPrice(config, product, --inventory);
  }
  return cash;
}

Settlement Settle(const parallel::StateView& state, int seat, int product,
                  const std::array<Timeline, 2>& timelines, const Amounts& own_shed,
                  const Amounts& own_carried, const Timeline* addition) {
  const Config& config = state.config();
  const int step = state.step_index(), turns = config.episode_steps - 1;
  Settlement result;
  result.inventory.resize(turns, state.market().inventory[product]);
  for (auto& values : result.cash) values.assign(turns, 0.0);
  if (step >= turns) return result;
  std::array<int64_t, 2> held = {own_shed[product], 0};
  std::vector<int64_t> carried_arrivals(turns, 0);
  if (own_carried[product] > 0) {
    const auto& farm = state.farm(seat);
    const auto& bags = state.priv(seat).inventories;
    for (size_t unit = 0; unit < bags.size(); ++unit) {
      const auto position = unit == 0 ? std::pair{farm.farmer_x, farm.farmer_y} : farm.hands[unit - 1];
      int distance = 2 * config.board_size;
      for (const auto& access : ShedAccessTiles(config.board_size)) {
        distance = std::min(distance, std::abs(access.first - position.first) +
                            std::abs(access.second - position.second));
      }
      const int delivery = std::min(step + distance,
          (step / config.turns_per_day + 1) * config.turns_per_day);
      if (delivery < turns) carried_arrivals[delivery] += bags[unit].Get(product);
    }
  }
  std::array<std::vector<int64_t>, 2> future;
  for (int side = 0; side < 2; ++side) {
    future[side].assign(turns + 1, 0);
    for (int turn = 0; turn < turns; ++turn) {
      future[side][turn + 1] = future[side][turn] + timelines[side].input[turn][product] +
          (side == 0 && addition ? addition->input[turn][product] : 0);
    }
  }
  int64_t inventory = state.market().inventory[product];
  std::array<double, 2> cash{};
  for (int turn = step; turn < turns; ++turn) {
    std::array<int64_t, 2> signed_orders{};
    for (int side = 0; side < 2; ++side) {
      held[side] += timelines[side].delivered[turn][product];
      if (side == 0) {
        held[side] += carried_arrivals[turn];
        if (addition) held[side] += addition->delivered[turn][product];
      }
      const int64_t inputs = future[side][turn + 1] - future[side][turn];
      const int64_t consumed = std::min(inputs, held[side]);
      held[side] -= consumed;
      const int64_t purchase = inputs - consumed;
      const int end = std::min(turns, turn + config.turns_per_day + 1);
      const int64_t reserve = future[side][end] - future[side][turn + 1];
      const int64_t sell = std::max<int64_t>(0, held[side] - reserve);
      held[side] -= sell;
      signed_orders[side] = sell - purchase;
    }
    // Quote both players before committing either unit, as in ApplyMarketPhase.
    while (signed_orders[0] || signed_orders[1]) {
      std::array<int64_t, 2> prices{};
      for (int side = 0; side < 2; ++side) {
        if (signed_orders[side]) prices[side] = ComputeMarketPrice(
            config, product, inventory - (signed_orders[side] < 0));
      }
      for (int side = 0; side < 2; ++side) {
        if (signed_orders[side] > 0) {
          cash[side] += prices[side];
          if (prices[side] > 1) ++inventory;
          --signed_orders[side];
        } else if (signed_orders[side] < 0) {
          cash[side] -= prices[side];
          --inventory;
          ++signed_orders[side];
        }
      }
    }
    inventory -= Drain(config, state.town_shops(), product, turn, turn);
    result.inventory[turn] = inventory;
    for (int side = 0; side < 2; ++side) result.cash[side][turn] = cash[side];
  }
  return result;
}

}  // namespace kagg::derived
