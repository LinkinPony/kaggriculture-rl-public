// Opt-in native function timings; disabled in every training process.
#pragma once

#include "opponents/compiled/runtime.hpp"

namespace kagg::opponents::compiled {
extern const bool kProfileFunctions;
Value ProfileCall(Context& context, const Function& function,
                  const std::string& name, const ScopePtr& scope);
Value FunctionProfile();
}  // namespace kagg::opponents::compiled
