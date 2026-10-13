// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_c84b15e4d6dc326f19a7(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"p"};
s->PrepareSlots(s_names);
return Tuple({Get(s->Captured("counts"), s->LocalAt(0)), ([&]() -> Value { auto fn7657 = Attribute(s->Captured("access"), "index"); Arguments args7658; args7658.Add(s->LocalAt(0), false); return Call(c, fn7657, std::move(args7658)); }())});
return {};
}
}  // namespace kagg::opponents::compiled
