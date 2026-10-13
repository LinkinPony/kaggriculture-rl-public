// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_8b201a271426d5305cfe(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"configuration", "observation"};
s->PrepareSlots(s_names);
return ([&]() -> Value { auto fn31523 = s->Global("_V11_ENTRY"); Arguments args31524; args31524.positional.reserve(2); args31524.Add(s->LocalAt(1), false); args31524.Add(s->LocalAt(0), false); return Call(c, fn31523, std::move(args31524)); }());
return {};
}
}  // namespace kagg::opponents::compiled
