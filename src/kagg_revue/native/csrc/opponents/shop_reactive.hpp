// Shop Router 0909: ordered-shop routing and worker-local daily queues.
#pragma once

#include <deque>

#include "opponents/portfolio.hpp"

namespace kagg::opponents {

class ReactiveShopRouter {
 public:
  explicit ReactiveShopRouter(SharedPortfolio portfolio)
      : portfolio_(std::move(portfolio)) {}
  PlayerAction Act(const Engine& engine, int player);

 private:
  struct State {
    int plan = 0;
    int last_step = -1;
    int day = -1;
    int sale_due_step = -1;
    Products advanced_sales{};
    std::vector<std::deque<UnitAction>> queues;
  };
  void Repair(const Engine& engine, int player, PlayerAction* action, State* state);
  void Sales(const Engine& engine, int player, PlayerAction* action, State* state);
  SharedPortfolio portfolio_;
  std::array<State, 2> states_;
};

}  // namespace kagg::opponents
