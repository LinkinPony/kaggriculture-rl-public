// Episode-local sparse feedback state for one v39 route.
#pragma once

#include <array>
#include <map>
#include <vector>

#include "kaito_v39/portfolio.hpp"

namespace kagg::kaito_v39 {

struct RepairTransaction {
  bool active = false;
  int start = 0;
  UnitAction intended;
};

struct RepairState {
  bool initialized = false;
  int last_step = -1;
  std::vector<RepairTransaction> active;
};

struct PreemptionState {
  bool initialized = false;
  int last_step = -1;
  int near_streak = 0;
  bool latched = false;
  std::map<int, std::array<int64_t, kNumProducts>> due;
};

struct MarketMakerState {
  bool initialized = false;
  int last_step = -1;
  int open_units = 0;
  int entry_step = -1;
  int64_t baseline_wheat = 0;
};

struct RouteState {
  RepairState repair;
  PreemptionState preemption;
  MarketMakerState market_maker;
};

PlayerAction ApplyRoute(const Portfolio& portfolio, const Engine& engine,
                        int player, Route route, RouteState* state);
bool ActionsEqual(const PlayerAction& left, const PlayerAction& right);

}  // namespace kagg::kaito_v39

