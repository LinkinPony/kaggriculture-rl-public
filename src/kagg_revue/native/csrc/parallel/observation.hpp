// Actor-visible entities and a bounded history of public observations.
#pragma once

#include <algorithm>
#include <array>
#include <vector>

#include "parallel/state.hpp"
#include "production/ledger.hpp"

namespace kagg::parallel {

inline constexpr int kProductFeatures = 34;
inline constexpr int kHistoryFeatures = 16;
inline constexpr const char* kEntityObservationVersion = "production-entities-v2";
inline constexpr int kUnitSupportFeatures = 44;
inline constexpr const char* kGroundedObservationVersion = "grounded-unit-support-v1";

struct PublicSnapshot {
  std::array<double, kNumProducts> prices{}, inventory{};
  std::array<double, 2> cash{}, hands{}, land{};
  std::array<std::array<double, kNumProducts>, 2> harvested{}, producers{};
  std::array<double, kNumProducts> market_flow{}, floor_ticks{}, ambiguous_ticks{};
  std::array<int, kNumProducts> shop_weight{}, unlock_delta{};
  int last_unlock_step = -1;
};

class PublicHistory {
 public:
  explicit PublicHistory(int turns_per_day) : snapshots_(std::max(24, 4 * turns_per_day) + 1) {}
  void Record(const StateView& engine);
  const PublicSnapshot& Previous(const StateView& engine, int lookback) const;
  const production::Ledger& ledger() const { return ledger_; }

 private:
  std::vector<PublicSnapshot> snapshots_;
  production::Ledger ledger_;
  int recorded_step_ = -1;
};

void EncodeObservation(const StateView& state, int seat, int units, uint16_t* output);
void EncodeUnitSupport(const StateView& state, int seat, int units, uint16_t* output);
int EntityExtraFeatures(int units);
void EncodeEntityExtras(const StateView& engine, int seat, int units,
                        const PublicHistory& history, uint16_t* output,
                        const uint16_t* opponent_board = nullptr);

}  // namespace kagg::parallel
