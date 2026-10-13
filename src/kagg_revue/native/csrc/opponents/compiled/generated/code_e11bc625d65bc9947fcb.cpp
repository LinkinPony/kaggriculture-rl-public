// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_e11bc625d65bc9947fcb(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"e", "native", "player", "t"};
s->PrepareSlots(s_names);
auto v25742 = Get(Attribute(Attribute(s->Global("_IMPL"), "chassis"), "players"), s->LocalAt(2));
s->SetAt(1, v25742);
if (static_cast<bool>(([&]() -> Value { auto v25743 = ([&]() -> Value { auto v25744 = s->LocalAt(3); Value v25745; v25745 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Lt", v25744, v25745))) return Value(false); v25744 = v25745; return Value(true); }()); if (static_cast<bool>(v25743)) return v25743; v25743 = ([&]() -> Value { auto v25746 = s->LocalAt(3); Value v25747; v25747 = Value(int64_t{718}); if (!static_cast<bool>(Binary("Gt", v25746, v25747))) return Value(false); v25746 = v25747; return Value(true); }()); return v25743; }()))) {
return List({});
}
auto v25748 = Get(Get(Attribute(Attribute(s->Global("_IMPL"), "chassis"), "routes"), (static_cast<bool>(([&]() -> Value { auto v25749 = s->LocalAt(3); Value v25750; v25750 = Value(int64_t{648}); if (!static_cast<bool>(Binary("GtE", v25749, v25750))) return Value(false); v25749 = v25750; return Value(true); }())) ? Value(int64_t{2}) : Get(s->LocalAt(1), Value("route")))), s->LocalAt(3));
s->SetAt(0, v25748);
return ([&]() -> Value { Arguments args25751; args25751.Add(([&]() -> Value { auto v25752 = ([&]() -> Value { auto fn25753 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args25754; args25754.Add(Value("farmer"), false); return CallDictionaryGet(c, fn25753, std::move(args25754)); }()); if (static_cast<bool>(v25752)) return v25752; v25752 = List({Value("PASS")}); return v25752; }()), false); args25751.Add(([&]() -> Value { auto v25755 = ([&]() -> Value { auto fn25756 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args25757; args25757.Add(Value("hands"), false); return CallDictionaryGet(c, fn25756, std::move(args25757)); }()); if (static_cast<bool>(v25755)) return v25755; v25755 = List({}); return v25755; }()), true); return List(std::move(args25751.positional)); }());
return {};
}
}  // namespace kagg::opponents::compiled
