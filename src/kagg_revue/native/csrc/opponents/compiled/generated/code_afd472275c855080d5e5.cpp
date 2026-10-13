// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_afd472275c855080d5e5(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"p"};
s->PrepareSlots(s_names);
return Tuple({([&]() -> Value { auto fn11554 = Attribute(s->Captured("positions"), "count"); Arguments args11555; args11555.Add(s->LocalAt(0), false); return Call(c, fn11554, std::move(args11555)); }()), ([&]() -> Value { auto fn11556 = Attribute(s->Captured("access"), "index"); Arguments args11557; args11557.Add(s->LocalAt(0), false); return Call(c, fn11556, std::move(args11557)); }())});
return {};
}
}  // namespace kagg::opponents::compiled
