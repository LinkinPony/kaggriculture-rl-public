#include "derived/features.hpp"

#include "production/features.hpp"

namespace kagg::derived {
namespace {

double Quote(const parallel::StateView& state, const TileForecast& forecast) {
  Amounts output{}, input{};
  for (const auto& event : forecast.events) {
    if (event.input) input[event.product] += event.amount;
    else if (event.delivery <= state.config().episode_steps - 2) output[event.product] += event.amount;
  }
  double result = 0;
  for (int product = 0; product < kNumProducts; ++product) {
    const int64_t inventory = state.market().inventory[product];
    result += Sell(state.config(), product, inventory, output[product]) -
        Buy(state.config(), product, inventory, input[product]);
  }
  return result;
}

int64_t Yield(const TileForecast& forecast, int product) {
  int64_t value = 0;
  for (const auto& event : forecast.events) {
    if (!event.input && event.product == product) value += event.amount;
  }
  return value;
}

}  // namespace

void Interventions(const parallel::StateView& state, const Tile& tile, int shed_distance,
                   double* row) {
  if (!production::Productive(tile)) return;
  const bool plant = tile.kind == TileKind::kPlant;
  const int day = state.step_index() / state.config().turns_per_day;
  const std::array<bool, 4> applicable = {
      plant && !tile.watered_today, !plant && !tile.fed_today,
      !plant && !tile.cared_today, plant && tile.fertilized_until_day < day + 2};
  for (int action = 0; action < 4; ++action) {
    if (!applicable[action]) continue;
    const auto without = Forecast(tile, state.config(), state.step_index(), shed_distance,
                                  false, false, action, false);
    const auto with = Forecast(tile, state.config(), state.step_index(), shed_distance,
                               false, false, action, true);
    row[action * 3] = 1;
    row[action * 3 + 1] = Count(Yield(with, production::Product(tile)) -
                                Yield(without, production::Product(tile)));
    row[action * 3 + 2] = Money(Quote(state, with) - Quote(state, without));
  }
}

}  // namespace kagg::derived
