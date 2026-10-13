#include "parallel/context.hpp"

#include <algorithm>
#include <cmath>

#include "production/features.hpp"
#include "derived/features.hpp"

namespace kagg::parallel {
namespace {

double Log(double value) { return std::log1p(std::max(0.0, value)) / 5.0; }
double Symlog(double value) {
  return std::copysign(std::log1p(std::abs(value)), value);
}

}  // namespace

int ContextFeatures(int board_size, bool agronomy, int units, bool derived) {
  return 2 * board_size * board_size * kContextBoardChannels +
         kNumProducts * kContextProductFeatures + kContextGlobalFeatures +
         kContextHistoryTokens * kContextHistoryFeatures +
         (agronomy ? production::FeatureCount(board_size, units) : 0) +
         (derived ? derived::FeatureCount(board_size, units) : 0);
}

void EncodeContext(const StateView& state, int seat, const PublicHistory& history,
                   uint16_t* output, bool agronomy, int units, bool derived) {
  const auto& config = state.config();
  const int area = config.board_size * config.board_size;
  const int step = state.step_index();
  const int day = step / config.turns_per_day;
  auto* board = reinterpret_cast<_Float16*>(output);
  std::fill(board, board + ContextFeatures(config.board_size), _Float16{0});
  auto* products = board + 2 * area * kContextBoardChannels;
  auto* global = products + kNumProducts * kContextProductFeatures;
  auto* changes = global + kContextGlobalFeatures;
  std::array<double, kNumProducts> harvest{}, ready{};
  for (int side = 0; side < 2; ++side) {
    const auto& farm = state.farm(side == 0 ? seat : 1 - seat);
    auto* summary = global + side * 8;
    for (int cell = 0; cell < area; ++cell) {
      const auto& tile = farm.tiles[cell];
      auto* row = board + (side * area + cell) * kContextBoardChannels;
      const bool plant = tile.kind == TileKind::kPlant;
      const bool animal = tile.kind == TileKind::kStructure && tile.has_animal;
      if (!plant && !animal) continue;
      const int product = plant ? tile.crop : kAnimals[tile.animal].product;
      const int start = plant ? tile.planted_day : tile.placed_day;
      const int first = plant ? kCrops[tile.crop].first_yield_day
                              : kAnimals[tile.animal].first_yield_day;
      const bool needs = plant ? !tile.watered_today : !tile.fed_today;
      const bool risk = needs && (plant ? tile.consecutive_unwatered : tile.consecutive_unfed) >= 1;
      row[0] = tile.yield_units > 0;
      row[1] = std::max(0, start + first - day) / 30.0;
      if (plant) row[2] = std::max(0, start + kCrops[tile.crop].max_yield_day - day) / 30.0;
      row[3] = tile.max_lifespan_step >= 0
                   ? std::clamp((tile.max_lifespan_step - step) / static_cast<double>(config.turns_per_day), 0.0, 30.0) / 30.0
                   : 1.0;
      row[4] = needs;
      row[5] = risk;
      row[6] = animal && (!tile.cared_today || tile.fertilizer_available);
      row[7] = Log(tile.yield_units * state.market().prices[product]);
      summary[0] += 1.0 / area;
      summary[1] += (tile.yield_units > 0) / static_cast<double>(area);
      summary[2] += (plant && needs) / static_cast<double>(area);
      summary[3] += (animal && needs) / static_cast<double>(area);
      summary[4] += risk / static_cast<double>(area);
      summary[5] += (animal && !tile.cared_today) / static_cast<double>(area);
      summary[6] += (tile.max_lifespan_step >= 0 && tile.max_lifespan_step - step <= config.turns_per_day)
                        / static_cast<double>(area);
      summary[7] += (start + first > day) / static_cast<double>(area);
      if (side == 0) {
        harvest[product] += tile.yield_units;
        ready[product] += tile.yield_units > 0;
      }
    }
  }
  for (int product = 0; product < kNumProducts; ++product) {
    double carried = 0;
    for (const auto& inventory : state.priv(seat).inventories) carried += inventory.Get(product);
    const double stored = state.priv(seat).shed[product];
    auto* row = products + product * kContextProductFeatures;
    row[0] = Log(carried);
    row[1] = Log(stored);
    row[2] = Log(carried + stored);
    row[3] = Log(harvest[product]);
    row[4] = Log((carried + stored + harvest[product]) * state.market().prices[product]);
    row[5] = ready[product] / area;
    row[6] = carried / std::max(1.0, carried + stored);
    row[7] = product < kNumCrops ? Log(state.priv(seat).seeds[product]) : 0;
  }
  if (agronomy) {
    production::Encode(state, seat, history.ledger(), units,
                       output + ContextFeatures(config.board_size));
  }
  if (derived) {
    derived::Encode(state, seat, history, units,
                    output + ContextFeatures(config.board_size, true, units));
  }
  constexpr std::array<int, kContextHistoryTokens> lookbacks = {1, 4, 12, 24};
  for (int token = 0; token < kContextHistoryTokens; ++token) {
    const int lookback = lookbacks[token];
    const auto& previous = history.Previous(state, lookback);
    auto* row = changes + token * kContextHistoryFeatures;
    for (int product = 0; product < kNumProducts; ++product) {
      const auto& parameters = config.market_params[product];
      row[product] = (state.market().prices[product] - previous.prices[product]) /
                     std::max(1.0, parameters.base);
      row[9 + product] = Symlog((state.market().inventory[product] - previous.inventory[product]) /
                                std::max(1.0, parameters.t));
    }
    for (int relative = 0; relative < 2; ++relative) {
      const int player = relative == 0 ? seat : 1 - seat;
      row[18 + 3 * relative] = Symlog((state.farm(player).money - previous.cash[player]) / 1000.0);
      row[19 + 3 * relative] = (state.farm(player).hands.size() - previous.hands[player]) / 32.0;
      row[20 + 3 * relative] = (state.farm(player).extra_unlocked - previous.land[player]) / 3.0;
    }
    row[24] = std::min(step, lookback) / static_cast<double>(lookback);
    row[25] = lookback / 24.0;
    row[26] = (step % config.turns_per_day) / static_cast<double>(config.turns_per_day);
    row[27] = step / static_cast<double>(config.episode_steps - 1);
  }
}

}  // namespace kagg::parallel
