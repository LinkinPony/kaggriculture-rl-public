// Actor-safe, policy-neutral facts derived exactly from visible rules and state.
#pragma once

#include <array>
#include <cstdint>
#include <string>
#include <vector>

#include "types.hpp"

namespace kagg::facts {

inline constexpr const char* kDerivedFactVersion = "derived-facts-v1";
inline constexpr int kTurnFactFeatures = 74;
inline constexpr int kPrefixFactFeatures = 32;
inline constexpr int kCandidateFactFeatures = 40;

struct View {
  const Config& config;
  const Farm& farm;
  const Farm& opponent_farm;
  const PrivateState& priv;
  const MarketState& market;
  const std::array<int, kNumShops>& shop_counts;
  int step = 0;
  int unit_limit = 1;
};

struct FlowSnapshot {
  int step = 0;
  std::array<int64_t, kNumProducts> market_inventory{};
  std::array<int64_t, kNumProducts> town_consumption{};
  std::array<int64_t, kNumProducts> opponent_unit_gain_upper{};
};

// Turn facts are row-major [token, kTurnFactFeatures]. `token_count` is set to
// the number of returned tokens. Bounds refer to total hidden opponent product
// holdings and must be computed only from actor-visible history.
std::vector<float> EncodeTurnFacts(
    const View& view,
    const std::array<int64_t, kNumProducts>& opponent_lower,
    const std::array<int64_t, kNumProducts>& opponent_upper,
    int* token_count);

std::array<float, kPrefixFactFeatures> EncodePrefixFacts(
    const View& view, const std::vector<int64_t>& tokens,
    const std::vector<int64_t>& quantities, int unit_count, int phase,
    int market_slots);

// Candidate facts are row-major [policy::kActionTokens,
// kCandidateFactFeatures]. Quantity-bearing candidates describe one unit plus
// an exact maximum feasible quantity under the stated projection semantics.
std::vector<float> EncodeCandidateFacts(
    const View& view, const std::vector<int64_t>& tokens,
    const std::vector<int64_t>& quantities, int unit_count, int phase,
    int unit_index, int market_slots);

FlowSnapshot MakeFlowSnapshot(const View& view);

// Conservative actor-visible bounds on the selected orders' contribution to
// public market inventory. Each product row is [minimum, maximum].
std::array<std::array<int64_t, 2>, kNumProducts> OwnMarketFlowBounds(
    const std::vector<int64_t>& tokens, const std::vector<int64_t>& quantities,
    int unit_count);

std::vector<std::string> TurnFactNames();
std::vector<std::string> PrefixFactNames();
std::vector<std::string> CandidateFactNames();

}  // namespace kagg::facts
