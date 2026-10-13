// Native helpers for the source-authenticated Kaito v48 training runtime.
// The behavior is derived from kaitofukami/40-40-early-floor-39-46-top-10-v48-fast-routes
// (Apache-2.0); attribution and the frozen source hash live in
// kagg_revue/opponents/kaito/NOTICE.md and provenance.py.
#pragma once

#include <array>

#include "engine.hpp"
#include "types.hpp"

namespace kagg::kaito {

struct AssetCounts {
  int cow = 0;
  int sheep = 0;
  int goose = 0;
  int melon = 0;
  int wheat = 0;
  int strawberry = 0;
};

AssetCounts PublicAssetCounts(const Farm& farm);
double CloneDistance(const Engine& engine);

void AlignHands(const Engine& engine, int player, PlayerAction* action);
void ReorderSellSlots(const Engine& engine, PlayerAction* action,
                      double demand_alpha);

std::array<int64_t, kNumItems> ProjectedShed(const Engine& engine, int player,
                                             const PlayerAction& action);
void ReplaceTerminalMarket(const Engine& engine, int player,
                           PlayerAction* action);

}  // namespace kagg::kaito
