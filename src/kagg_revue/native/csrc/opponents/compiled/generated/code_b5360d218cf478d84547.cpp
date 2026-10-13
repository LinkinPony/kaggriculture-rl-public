// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_b5360d218cf478d84547(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"configuration", "observation"};
s->PrepareSlots(s_names);
return ([&]() -> Value { auto fn26781 = s->Global("_E343_LAST"); Arguments args26782; args26782.positional.reserve(2); args26782.Add(s->LocalAt(1), false); args26782.Add(s->LocalAt(0), false); return Call(c, fn26781, std::move(args26782)); }());
return {};
}
}  // namespace kagg::opponents::compiled
