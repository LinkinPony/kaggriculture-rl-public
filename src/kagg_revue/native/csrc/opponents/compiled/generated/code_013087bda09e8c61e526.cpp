// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_013087bda09e8c61e526(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"configuration", "observation"};
s->PrepareSlots(s_names);
return ([&]() -> Value { auto fn20550 = s->Global("_e334_agent"); Arguments args20551; args20551.positional.reserve(2); args20551.Add(s->LocalAt(1), false); args20551.Add(s->LocalAt(0), false); return Call(c, fn20550, std::move(args20551)); }());
return {};
}
}  // namespace kagg::opponents::compiled
