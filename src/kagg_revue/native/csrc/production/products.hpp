// Per-product rows: own/opponent production lines, market impact and expansion.
#pragma once

#include <array>
#include <cstdint>

#include "production/features.hpp"
#include "production/ledger.hpp"

namespace kagg::production {

// Own-seat aggregates gathered while scanning both farms.
struct Holdings {
  std::array<double, kNumItems> carried{};
  int feed_due = 0;
  int empty = 0;
  std::array<int, 2> structures{};                    // bare coops and barns
  std::array<int64_t, kNumProducts> own_supply{};     // shed + carried + own harvestable
  std::array<int64_t, kNumProducts> opponent_supply{};  // harvestable on the other farm
};

using ProductRows = std::array<std::array<double, kProductFeatures>, kNumProducts>;

// Normalizes the accumulated tile counts and fills every non-tile product field.
void FinishProducts(const parallel::StateView& state, int seat, const Ledger& ledger,
                    const Holdings& holdings, ProductRows& rows);

}  // namespace kagg::production
