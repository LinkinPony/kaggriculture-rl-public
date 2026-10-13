// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_40bbeddbcf04560d6626(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"actor", "self"};
s->PrepareSlots(s_names);
return ([&]() -> Value { auto fn4339 = Attribute(s->LocalAt(1), "inv"); Arguments args4340; args4340.Add(s->LocalAt(0), false); return Call(c, fn4339, std::move(args4340)); }());
return {};
}
}  // namespace kagg::opponents::compiled
