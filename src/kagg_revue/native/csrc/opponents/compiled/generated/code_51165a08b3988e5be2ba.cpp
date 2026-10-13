// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_51165a08b3988e5be2ba(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "next_sup", "projected", "route", "self", "step", "view"};
s->PrepareSlots(s_names);
if (static_cast<bool>(([&]() -> Value { auto v5753 = ([&]() -> Value { auto v5754 = s->LocalAt(5); Value v5755; v5755 = Value(int64_t{216}); if (!static_cast<bool>(Binary("Lt", v5754, v5755))) return Value(false); v5754 = v5755; return Value(true); }()); if (static_cast<bool>(v5753)) return v5753; v5753 = ([&]() -> Value { auto v5756 = s->LocalAt(5); Value v5757; v5757 = Value(int64_t{696}); if (!static_cast<bool>(Binary("GtE", v5756, v5757))) return Value(false); v5756 = v5757; return Value(true); }()); return v5753; }()))) {
return ([&]() -> Value { auto fn5758 = s->Global("_R36_NATIVE_LEAD"); Arguments args5759; args5759.positional.reserve(7); args5759.Add(s->LocalAt(4), false); args5759.Add(s->LocalAt(0), false); args5759.Add(s->LocalAt(6), false); args5759.Add(s->LocalAt(2), false); args5759.Add(s->LocalAt(3), false); args5759.Add(s->LocalAt(5), false); args5759.Add(s->LocalAt(1), false); return Call(c, fn5758, std::move(args5759)); }());
}
return {};
}
}  // namespace kagg::opponents::compiled
