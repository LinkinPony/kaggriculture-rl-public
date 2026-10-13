// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_11687f747d60c958da20(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"a"};
s->PrepareSlots(s_names);
return Tuple({Get(s->Captured("occ"), s->LocalAt(0)), ([&]() -> Value { auto fn21761 = Attribute(s->Captured("access"), "index"); Arguments args21762; args21762.Add(s->LocalAt(0), false); return Call(c, fn21761, std::move(args21762)); }())});
return {};
}
}  // namespace kagg::opponents::compiled
