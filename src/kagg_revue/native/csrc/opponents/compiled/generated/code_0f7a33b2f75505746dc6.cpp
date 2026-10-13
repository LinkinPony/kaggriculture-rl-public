// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_0f7a33b2f75505746dc6(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"a"};
s->PrepareSlots(s_names);
return Tuple({Get(s->Captured("occ"), s->LocalAt(0)), ([&]() -> Value { auto fn23489 = Attribute(s->Captured("access"), "index"); Arguments args23490; args23490.Add(s->LocalAt(0), false); return Call(c, fn23489, std::move(args23490)); }())});
return {};
}
}  // namespace kagg::opponents::compiled
