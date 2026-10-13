// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_f033ae53b9e653bf8fd7(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"native", "seat", "t", "tape"};
s->PrepareSlots(s_names);
auto v25031 = ([&]() -> Value { auto fn25032 = PrepareDictionaryGet(Attribute(Attribute(s->Global("_IMPL"), "chassis"), "players")); Arguments args25033; args25033.Add(s->LocalAt(1), false); return CallDictionaryGet(c, fn25032, std::move(args25033)); }());
s->SetAt(0, v25031);
if (static_cast<bool>(([&]() -> Value { auto v25034 = Unary("Not", s->LocalAt(0)); if (static_cast<bool>(v25034)) return v25034; v25034 = ([&]() -> Value { auto v25035 = s->LocalAt(2); Value v25036; v25036 = Value(int64_t{719}); if (!static_cast<bool>(Binary("Gt", v25035, v25036))) return Value(false); v25035 = v25036; return Value(true); }()); return v25034; }()))) {
return ([&]() -> Value { auto dict25037 = Dict(); return dict25037; }());
}
auto v25038 = Get(Attribute(Attribute(s->Global("_IMPL"), "chassis"), "routes"), (static_cast<bool>(([&]() -> Value { auto v25039 = s->LocalAt(2); Value v25040; v25040 = Value(int64_t{648}); if (!static_cast<bool>(Binary("GtE", v25039, v25040))) return Value(false); v25039 = v25040; return Value(true); }())) ? Value(int64_t{2}) : Get(s->LocalAt(0), Value("route"))));
s->SetAt(3, v25038);
return (static_cast<bool>(([&]() -> Value { auto v25041 = ([&]() -> Value { auto v25042 = s->LocalAt(2); Value v25043; v25043 = ([&]() -> Value { auto fn25044 = s->Global("len"); Arguments args25045; args25045.Add(s->LocalAt(3), false); return Call(c, fn25044, std::move(args25045)); }()); if (!static_cast<bool>(Binary("Lt", v25042, v25043))) return Value(false); v25042 = v25043; return Value(true); }()); if (!static_cast<bool>(v25041)) return v25041; v25041 = ([&]() -> Value { auto fn25046 = s->Global("isinstance"); Arguments args25047; args25047.positional.reserve(2); args25047.Add(Get(s->LocalAt(3), s->LocalAt(2)), false); args25047.Add(s->Global("dict"), false); return Call(c, fn25046, std::move(args25047)); }()); return v25041; }())) ? Get(s->LocalAt(3), s->LocalAt(2)) : ([&]() -> Value { auto dict25048 = Dict(); return dict25048; }()));
return {};
}
}  // namespace kagg::opponents::compiled
