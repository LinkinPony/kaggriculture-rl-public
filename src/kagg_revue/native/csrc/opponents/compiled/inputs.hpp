// Typed implementation of a hash-bound frozen input-tour search.
#pragma once

#include <optional>

#include "opponents/compiled/runtime.hpp"

namespace kagg::opponents::compiled {
std::optional<Value> InputPath(Context& context, const ScopePtr& scope);
}  // namespace kagg::opponents::compiled
