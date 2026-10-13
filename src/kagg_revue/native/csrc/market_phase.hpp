// Exact ordered market settlement shared by Engine and the market compiler.
#pragma once

#include <array>
#include <optional>
#include <vector>

#include "types.hpp"

namespace kagg {

inline constexpr int kMarketCompilerSpecVersion = 1;
// Defensive bound inherited from the official settlement loop. Request control
// remains unbounded; only its diagnostic local projection is capped here.
inline constexpr int kMarketSettlementIterationGuard = 100000;
inline constexpr int64_t kMaxMarketUnitsPerSlot =
    kMarketSettlementIterationGuard - 1;

enum class MarketOrderStatus { kApplied, kPartial, kRejected, kMalformed };

struct MarketSlotTrace {
  int player = 0;
  int slot_index = 0;
  std::optional<MarketOrder> requested;
  std::optional<MarketOrder> actual;
  MarketOrderStatus status = MarketOrderStatus::kMalformed;
  int64_t committed = 0;
  double money_before = 0.0;
  double money_after = 0.0;
  int64_t shed_total_before = 0;
  int64_t shed_total_after = 0;
};

int64_t ComputeMarketPrice(const Config& config, int product, int64_t inventory);
double ComputeHirePrice(const Config& config, int hires_today);
void RefreshMarketPrices(const Config& config, MarketState* market);

// Settles both players' queues in official per-slot lockstep order. `trace`
// may be null when only state transition is required.
void ApplyMarketPhase(const Config& config, const std::array<Farm*, 2>& farms,
                      const std::array<PrivateState*, 2>& privates, MarketState* market,
                      const PlayerAction& action0, const PlayerAction& action1,
                      std::vector<MarketSlotTrace>* trace = nullptr);

const char* MarketOrderStatusName(MarketOrderStatus status);

}  // namespace kagg
