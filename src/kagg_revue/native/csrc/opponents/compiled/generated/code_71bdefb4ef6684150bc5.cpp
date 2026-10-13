// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_71bdefb4ef6684150bc5(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "configuration", "observation"};
s->PrepareSlots(s_names);
auto v29293 = ([&]() -> Value { auto fn29294 = s->Global("_V9_OPENING_PARENT"); Arguments args29295; args29295.positional.reserve(2); args29295.Add(s->LocalAt(2), false); args29295.Add(s->LocalAt(1), false); return Call(c, fn29294, std::move(args29295)); }());
s->SetAt(0, v29293);
try {
return ([&]() -> Value { auto fn29297 = s->Global("_v9_opening"); Arguments args29298; args29298.positional.reserve(2); args29298.Add(s->LocalAt(2), false); args29298.Add(s->LocalAt(0), false); return Call(c, fn29297, std::move(args29298)); }());
} catch (const Error& error29296) {
if (Matches(error29296, s->Global("Exception"))) {
return s->LocalAt(0);
}
else { throw; }
}
return {};
}
}  // namespace kagg::opponents::compiled
