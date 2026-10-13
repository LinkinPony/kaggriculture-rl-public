// Versioned causal production context for the deeper grounded policy.
#pragma once

#include "parallel/observation.hpp"

namespace kagg::parallel {

inline constexpr const char* kContextObservationVersion = "grounded-production-context-v2";
inline constexpr int kContextBoardChannels = 8;
inline constexpr int kContextProductFeatures = 8;
inline constexpr int kContextGlobalFeatures = 16;
inline constexpr int kContextHistoryTokens = 4;
inline constexpr int kContextHistoryFeatures = 28;

// `units` is the actor unit capacity; it only sizes the agronomy unit block.
int ContextFeatures(int board_size, bool agronomy = false, int units = 0, bool derived = false);
void EncodeContext(const StateView& state, int seat, const PublicHistory& history,
                   uint16_t* output, bool agronomy = false, int units = 0, bool derived = false);

}  // namespace kagg::parallel
