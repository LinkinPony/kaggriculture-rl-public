// Thomas Tschinkel's frozen five-route public-state tree.
#pragma once
#include "opponents/portfolio.hpp"

namespace kagg::opponents {
class Router {
 public:
  explicit Router(SharedPortfolio portfolio)
      : portfolio_(std::move(portfolio)) {}
  PlayerAction Act(const Engine& engine, int player);

 private:
  struct State {
    int last = -1;
    int block = -1;
    int route = 0;
  };
  SharedPortfolio portfolio_;
  std::array<State, 2> states_;
};
}  // namespace kagg::opponents
