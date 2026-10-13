// Season-end yield of a placement made now under idealized daily maintenance.
#pragma once

#include "types.hpp"

namespace kagg::production {

// Units a fresh plant or animal of `product` returns by the last actionable day
// when watered or fed every day; `boosted` adds continuous fertilizer or care.
double PlacementTotal(int product, const Config& config, int step, bool boosted);

}  // namespace kagg::production
