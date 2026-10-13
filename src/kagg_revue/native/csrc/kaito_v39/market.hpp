// v39's frozen market-impact ordering and WHEAT round-trip expert.
#pragma once

#include "kaito_v39/policy.hpp"

namespace kagg::kaito_v39 {

void ReorderSellSlots(const Engine& engine, PlayerAction* action,
                      double demand_alpha);
PlayerAction ApplyMarketMaker(const Portfolio& portfolio,
                              const Engine& engine, int player, Route route,
                              PlayerAction action, MarketMakerState* state);

}  // namespace kagg::kaito_v39

