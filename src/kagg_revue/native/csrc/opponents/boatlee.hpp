// Boatlee v29's route repair and adaptive market hysteresis.
#pragma once
#include "opponents/portfolio.hpp"

namespace kagg::opponents {
class Boatlee {
 public:
  explicit Boatlee(SharedPortfolio portfolio)
      : portfolio_(std::move(portfolio)) {}
  PlayerAction Act(const Engine& engine, int player);

 private:
  struct State {
    int last = -1;
    int mirror = -1;
    Products inventory{};
    Products sold{};
    Products added{};
    std::array<double, kNumProducts> pressure{};
    std::vector<int> shops;
  };
  SharedPortfolio portfolio_;
  std::array<State, 2> states_;
  std::array<RepairState, 2> repair_;
};
}  // namespace kagg::opponents
