// Fixed-width numeric action ABI shared by training, native rollout and submission.
#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

#include "types.hpp"

namespace kagg::policy {

inline constexpr const char* kActionCodecVersion = "turn-policy-actions-v2";
inline constexpr int kUnitActionTokens = 44;
inline constexpr int kMarketActionTokens = 23;
inline constexpr int kActionTokens = kUnitActionTokens + kMarketActionTokens;
inline constexpr int kMarketStopToken = kUnitActionTokens;
inline constexpr int kMarketHireToken = kUnitActionTokens + 21;

bool IsUnitToken(int token);
bool IsMarketToken(int token);
bool TokenHasQuantity(int token);

UnitAction DecodeUnitToken(int token, int64_t quantity);
std::optional<MarketOrder> DecodeMarketToken(int token, int64_t quantity);

// `tokens` contains the official unit prefix followed by ordered market tokens.
// Missing unit entries become PASS. MARKET:STOP terminates the market queue.
PlayerAction DecodePlayerAction(const int64_t* tokens, const int64_t* quantities,
                                int decision_count, int unit_count,
                                int max_market_orders);

// Inverse numeric boundary used by native capability/script executors.  The
// caller owns fixed-width buffers; returns the number of written decisions.
// Unsupported BUY_PRODUCT variants are encoded as an explicit skipped market
// slot, matching the deliberately compact policy vocabulary.
int EncodePlayerAction(const PlayerAction& action, int unit_count,
                       int64_t* tokens, int64_t* quantities, int capacity);

std::vector<std::string> ActionTokenKeys();

}  // namespace kagg::policy
