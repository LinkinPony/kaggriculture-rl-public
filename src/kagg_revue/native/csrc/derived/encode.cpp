#include "derived/features.hpp"

#include <algorithm>
#include <cmath>
#include <stdexcept>

namespace kagg::derived {

void Encode(const parallel::StateView& state, int seat, const parallel::PublicHistory& history,
            int units, uint16_t* output) {
  const auto execution = ExecutionFeatures(state, seat, units);
  std::array<std::array<Timeline, 2>, 2> scenarios;
  std::array<std::array<Settlement, kNumProducts>, 2> settlement;
  Amounts shed{};
  std::copy_n(state.priv(seat).shed.begin(), kNumProducts, shed.begin());
  for (int boost = 0; boost < 2; ++boost) {
    for (int side = 0; side < 2; ++side) {
      scenarios[boost][side] = FarmForecast(state.config(), state.farm(side == 0 ? seat : 1 - seat),
          execution.geometry[side], state.step_index(), boost != 0);
    }
    for (int product = 0; product < kNumProducts; ++product) {
      settlement[boost][product] = Settle(state, seat, product, scenarios[boost], shed, execution.carried);
    }
  }
  ProductRows products{};
  InvestmentFeatures(state, seat, execution, scenarios, settlement, products);
  ProductFeatures(state, seat, history, execution, scenarios, settlement, products);
  const auto globals = GlobalFeatures(state, seat, execution, scenarios[0]);
  auto* packed = reinterpret_cast<_Float16*>(output);
  const auto append = [&](const auto& values) {
    for (double value : values) {
      if (!std::isfinite(value) || std::abs(value) > 65504) {
        throw std::runtime_error("nonfinite or overflowing v5b derived feature");
      }
      *packed++ = static_cast<_Float16>(value);
    }
  };
  append(globals);
  append(execution.boards);
  append(execution.units);
  for (const auto& row : products) append(row);
}

}  // namespace kagg::derived
