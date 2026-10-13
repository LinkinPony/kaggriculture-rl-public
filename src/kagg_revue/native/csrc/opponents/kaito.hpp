// Kaito v58: ten independent residual controllers and public-state routing.
#pragma once

#include <map>

#include "opponents/portfolio.hpp"

namespace kagg::opponents {

class Kaito {
 public:
  explicit Kaito(SharedPortfolio portfolio)
      : portfolio_(std::move(portfolio)) {}
  PlayerAction Act(const Engine& engine, int player);

 private:
  struct Controller {
    int last = -1;
    bool inventory_seen = false;
    Products inventory{};
    Products own_net{};
    std::array<double, kNumProducts> supply{};
    std::vector<int> shops;
    double confidence = 0.0;
    int evidence = 0;
    int near_streak = 0;
    bool near = false;
    std::map<int, Products> due;
    RepairState repair;
  };
  enum class Mode { kBase, kFarmers, kRecovery, kIce, kBakery, kPizza };
  struct Seat {
    int last = -1;
    Mode mode = Mode::kBase;
    int mirror_streak = 0;
    bool clone = false;
    bool yarn = false;
    std::array<Controller, 10> controllers;
  };

  PlayerAction Control(const Engine& engine, int player, int route,
                       Controller* state);
  void Flow(const Engine& engine, Controller* state);
  void Preempt(const Engine& engine, int player, int route,
               PlayerAction* action, Controller* state);
  static void Repay(int step, PlayerAction* action, Controller* state);
  static Products ExecutableNet(const Engine& engine, int player,
                                const PlayerAction& action);
  static Mode RecoveryMode(const Engine& engine, int player);
  static bool KnownYarn(const Engine& engine, int player);
  SharedPortfolio portfolio_;
  std::array<Seat, 2> seats_;
};

}  // namespace kagg::opponents
