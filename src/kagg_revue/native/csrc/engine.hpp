// Native official-rules engine targeting the official Python interpreter from
// kaggle-environments 1.32.7. Equivalence is established externally against
// identified official replay artifacts. One Engine instance is one episode;
// Step() advances one turn given both players' actions.
#pragma once

#include <cstdint>

#include "market_phase.hpp"
#include "types.hpp"

namespace kagg {

class Engine {
 public:
  // `seed` must be the resolved episode seed (env.info["seed"], >= 0).
  Engine(const Config& config, int64_t seed);

  void Reset(int64_t seed);

  // Processes one turn. Throws std::logic_error when already done. Matching
  // the official framework, the final processed step index is
  // episode_steps - 2 (episodeSteps=720 -> 719 transitions, steps 0..718).
  void Step(const PlayerAction& a0, const PlayerAction& a1,
            std::vector<MarketSlotTrace>* market_trace = nullptr);

  bool done() const { return done_; }
  int step_index() const { return step_; }
  const Config& config() const { return config_; }
  const Farm& farm(int player) const { return farms_[player]; }
  const PrivateState& priv(int player) const { return privates_[player]; }
  const MarketState& market() const { return market_; }
  const std::vector<int>& town_shops() const { return town_shops_; }

  // Official `market_price` (banker-rounded, floored at $1).
  int64_t MarketPrice(int product, int64_t inventory) const;

 private:
  void TownConsume(int step);
  void DecayPlants(Farm& farm, int step);
  void DailyRefreshPlants(Farm& farm, int day);
  void DailyRefreshAnimals(Farm& farm, int day);
  void EndOfDay(int day);

  Config config_;
  int64_t seed_ = 0;
  int step_ = 0;
  bool done_ = false;
  std::array<Farm, 2> farms_;
  std::array<PrivateState, 2> privates_;
  MarketState market_;
  std::vector<int> town_shops_;  // shop indices in unlock order
};

}  // namespace kagg
