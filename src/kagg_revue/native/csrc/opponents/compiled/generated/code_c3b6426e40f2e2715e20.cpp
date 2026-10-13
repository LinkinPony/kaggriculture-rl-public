// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_c3b6426e40f2e2715e20(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "next_sup", "projected", "route", "self", "step", "view"};
s->PrepareSlots(s_names);
if (static_cast<bool>(([&]() -> Value { auto v13560 = ([&]() -> Value { auto v13561 = s->LocalAt(5); Value v13562; v13562 = Value(int64_t{288}); if (!static_cast<bool>(Binary("Lt", v13561, v13562))) return Value(false); v13561 = v13562; return Value(true); }()); if (static_cast<bool>(v13560)) return v13560; v13560 = ([&]() -> Value { auto v13563 = s->LocalAt(5); Value v13564; v13564 = Value(int64_t{696}); if (!static_cast<bool>(Binary("GtE", v13563, v13564))) return Value(false); v13563 = v13564; return Value(true); }()); return v13560; }()))) {
return ([&]() -> Value { auto fn13565 = s->Global("_R36_NATIVE_LEAD"); Arguments args13566; args13566.positional.reserve(7); args13566.Add(s->LocalAt(4), false); args13566.Add(s->LocalAt(0), false); args13566.Add(s->LocalAt(6), false); args13566.Add(s->LocalAt(2), false); args13566.Add(s->LocalAt(3), false); args13566.Add(s->LocalAt(5), false); args13566.Add(s->LocalAt(1), false); return Call(c, fn13565, std::move(args13566)); }());
}
return {};
}
}  // namespace kagg::opponents::compiled
