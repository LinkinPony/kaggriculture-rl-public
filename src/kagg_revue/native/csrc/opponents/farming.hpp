// Farming Score V4's prefix-compatible routes and execution guards.
#pragma once
#include "opponents/portfolio.hpp"

namespace kagg::opponents {
class Farming {
 public:
  explicit Farming(SharedPortfolio portfolio)
      : portfolio_(std::move(portfolio)) {}
  PlayerAction Act(const Engine& engine, int player);

 private:
  struct State {
    int route = 0;
    int last = -1;
  };
  void Budget(const Engine& engine, int player, int route,
              PlayerAction* action) const;
  void Capacity(const Engine& engine, int player, int route,
                PlayerAction* action) const;
  SharedPortfolio portfolio_;
  std::array<State, 2> states_;
};
}  // namespace kagg::opponents
