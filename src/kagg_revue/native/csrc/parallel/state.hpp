// Non-owning visible-state interface shared by rollout and official observations.
#pragma once

#include "engine.hpp"

namespace kagg::parallel {

class StateView {
 public:
  StateView(const Engine& engine)
      : StateView(engine.config(), engine.step_index(), engine.farm(0), engine.farm(1),
                  engine.priv(0), engine.priv(1), engine.market(), engine.town_shops()) {}
  StateView(const Config& config, int step, const Farm& left, const Farm& right,
            const PrivateState& left_private, const PrivateState& right_private,
            const MarketState& market, const std::vector<int>& shops)
      : config_(config), step_(step), farms_{&left, &right},
        private_{&left_private, &right_private}, market_(market), shops_(shops) {}
  const Config& config() const { return config_; }
  int step_index() const { return step_; }
  const Farm& farm(int seat) const { return *farms_[seat]; }
  const PrivateState& priv(int seat) const { return *private_[seat]; }
  const MarketState& market() const { return market_; }
  const std::vector<int>& town_shops() const { return shops_; }

 private:
  const Config& config_;
  int step_;
  std::array<const Farm*, 2> farms_;
  std::array<const PrivateState*, 2> private_;
  const MarketState& market_;
  const std::vector<int>& shops_;
};

}  // namespace kagg::parallel
