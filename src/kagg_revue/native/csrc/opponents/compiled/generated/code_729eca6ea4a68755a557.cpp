// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_729eca6ea4a68755a557(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"native", "player", "t"};
s->PrepareSlots(s_names);
auto v18620 = Get(Attribute(Attribute(s->Global("_IMPL"), "chassis"), "players"), s->LocalAt(1));
s->SetAt(0, v18620);
return ([&]() -> Value { auto v18621 = ([&]() -> Value { auto fn18622 = PrepareDictionaryGet(Get(Get(Attribute(Attribute(s->Global("_IMPL"), "chassis"), "routes"), (static_cast<bool>(([&]() -> Value { auto v18624 = s->LocalAt(2); Value v18625; v18625 = Value(int64_t{648}); if (!static_cast<bool>(Binary("GtE", v18624, v18625))) return Value(false); v18624 = v18625; return Value(true); }())) ? Value(int64_t{2}) : Get(s->LocalAt(0), Value("route")))), s->LocalAt(2))); Arguments args18623; args18623.positional.reserve(2); args18623.Add(Value("market"), false); args18623.Add(List({}), false); return CallDictionaryGet(c, fn18622, std::move(args18623)); }()); if (static_cast<bool>(v18621)) return v18621; v18621 = List({}); return v18621; }());
return {};
}
}  // namespace kagg::opponents::compiled
