// Handwritten equivalents of complete, hash-authenticated public policy functions.
#pragma once

#include <optional>

#include "opponents/compiled/runtime.hpp"

namespace kagg::opponents::compiled {
std::optional<Value> TypedView(Context&, const ScopePtr&);
std::optional<Value> TypedShed(Context&, const ScopePtr&);
std::optional<Value> TypedClone(Context&, const ScopePtr&);
std::optional<Value> TypedInputs(Context&, const ScopePtr&);
}  // namespace kagg::opponents::compiled
