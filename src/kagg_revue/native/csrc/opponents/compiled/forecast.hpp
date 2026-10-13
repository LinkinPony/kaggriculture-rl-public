// Typed scoring for an exact authenticated public forecast function.
#pragma once

#include <optional>

#include "opponents/compiled/runtime.hpp"

namespace kagg::opponents::compiled {
std::optional<Value> Forecast(Context& context, const ScopePtr& scope);
}  // namespace kagg::opponents::compiled
