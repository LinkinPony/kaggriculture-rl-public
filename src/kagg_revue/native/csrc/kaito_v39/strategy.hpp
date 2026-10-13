// Exact public-state feature extraction and v39 hierarchy decisions.
#pragma once

#include <array>
#include <optional>

#include "kaito_v39/portfolio.hpp"

namespace kagg::kaito_v39 {

RouterPart ExtractRouterPart(const Engine& engine, int player);
Route SelectNestedRoute(const Portfolio& portfolio,
                        const RouterPart& current);
bool SelectStage1Wool(const Portfolio& portfolio,
                      const RouterPart& current);
bool SelectStage2Alt(
    const Portfolio& portfolio,
    const std::array<std::optional<RouterPart>, kHistoryCheckpoints>& history);

}  // namespace kagg::kaito_v39

