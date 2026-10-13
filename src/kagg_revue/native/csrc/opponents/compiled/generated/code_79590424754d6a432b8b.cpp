// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_79590424754d6a432b8b(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"p"};
s->PrepareSlots(s_names);
return Tuple({([&]() -> Value { auto fn11280 = Attribute(s->Captured("positions"), "count"); Arguments args11281; args11281.Add(s->LocalAt(0), false); return Call(c, fn11280, std::move(args11281)); }()), ([&]() -> Value { auto fn11282 = Attribute(s->Captured("access"), "index"); Arguments args11283; args11283.Add(s->LocalAt(0), false); return Call(c, fn11282, std::move(args11283)); }())});
return {};
}
}  // namespace kagg::opponents::compiled
