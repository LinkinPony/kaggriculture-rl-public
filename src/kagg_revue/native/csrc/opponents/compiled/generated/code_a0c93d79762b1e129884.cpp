// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_a0c93d79762b1e129884(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"configuration", "observation"};
s->PrepareSlots(s_names);
return ([&]() -> Value { auto fn27773 = s->Global("_E352_INNER"); Arguments args27774; args27774.positional.reserve(2); args27774.Add(s->LocalAt(1), false); args27774.Add(s->LocalAt(0), false); return Call(c, fn27773, std::move(args27774)); }());
return {};
}
}  // namespace kagg::opponents::compiled
