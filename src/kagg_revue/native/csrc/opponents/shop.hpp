// Shop Router 0908: four immutable tapes, two public-state routing decisions.
#pragma once

#include "opponents/portfolio.hpp"

namespace kagg::opponents {

class ShopRouter {
 public:
  explicit ShopRouter(SharedPortfolio portfolio)
      : portfolio_(std::move(portfolio)) {}
  PlayerAction Act(const Engine& engine, int player);

 private:
  struct State {
    int route = 0;
    int last_decision = -1;
  };
  SharedPortfolio portfolio_;
  std::array<State, 2> states_;
};

}  // namespace kagg::opponents
