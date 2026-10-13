// Public-information accumulators kept alongside the observation history.
#pragma once

#include <array>
#include <cstdint>
#include <vector>

#include "parallel/state.hpp"

namespace kagg::production {

// Visible harvests on both farms and the players' combined net market flow
// after removing deterministic town consumption. Everything here is derived
// from consecutive public states only; a non-consecutive record resets it.
struct Ledger {
  std::array<std::array<double, kNumProducts>, 2> harvested{};  // by absolute player
  std::array<double, kNumProducts> net_market_flow{};           // units sold minus bought

  void Record(const parallel::StateView& state);

 private:
  int step_ = -1;
  std::vector<Tile> tiles_;  // both farms as of the previous record
  std::array<int64_t, kNumProducts> inventory_{};
  std::vector<int> shops_;
};

}  // namespace kagg::production
