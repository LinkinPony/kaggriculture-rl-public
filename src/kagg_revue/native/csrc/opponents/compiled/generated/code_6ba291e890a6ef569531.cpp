// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_6ba291e890a6ef569531(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"p"};
s->PrepareSlots(s_names);
return Tuple({([&]() -> Value { auto fn12491 = Attribute(s->Captured("positions"), "count"); Arguments args12492; args12492.Add(s->LocalAt(0), false); return Call(c, fn12491, std::move(args12492)); }()), ([&]() -> Value { auto fn12493 = Attribute(s->Captured("access"), "index"); Arguments args12494; args12494.Add(s->LocalAt(0), false); return Call(c, fn12493, std::move(args12494)); }())});
return {};
}
}  // namespace kagg::opponents::compiled
