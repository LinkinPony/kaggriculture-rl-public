// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_395d0a2fa9584cb73fa1(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"p"};
s->PrepareSlots(s_names);
return Tuple({([&]() -> Value { auto fn9875 = Attribute(s->Captured("positions"), "count"); Arguments args9876; args9876.Add(s->LocalAt(0), false); return Call(c, fn9875, std::move(args9876)); }()), ([&]() -> Value { auto fn9877 = Attribute(s->Captured("access"), "index"); Arguments args9878; args9878.Add(s->LocalAt(0), false); return Call(c, fn9877, std::move(args9878)); }())});
return {};
}
}  // namespace kagg::opponents::compiled
