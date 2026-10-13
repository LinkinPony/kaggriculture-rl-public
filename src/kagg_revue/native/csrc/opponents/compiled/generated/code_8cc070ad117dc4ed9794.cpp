// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_8cc070ad117dc4ed9794(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"p"};
s->PrepareSlots(s_names);
return Tuple({([&]() -> Value { auto fn10448 = Attribute(s->Captured("positions"), "count"); Arguments args10449; args10449.Add(s->LocalAt(0), false); return Call(c, fn10448, std::move(args10449)); }()), ([&]() -> Value { auto fn10450 = Attribute(s->Captured("access"), "index"); Arguments args10451; args10451.Add(s->LocalAt(0), false); return Call(c, fn10450, std::move(args10451)); }())});
return {};
}
}  // namespace kagg::opponents::compiled
