// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_98c3afa68764bf0c29c3(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "view"};
s->PrepareSlots(s_names);
return ([&]() -> Value { auto fn4341 = Attribute(Attribute(s->Global("_IMPL"), "chassis"), "_projected_shed"); Arguments args4342; args4342.positional.reserve(2); args4342.Add(s->LocalAt(0), false); args4342.Add(s->LocalAt(1), false); return Call(c, fn4341, std::move(args4342)); }());
return {};
}
}  // namespace kagg::opponents::compiled
