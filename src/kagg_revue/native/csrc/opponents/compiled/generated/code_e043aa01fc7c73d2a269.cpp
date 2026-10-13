// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_e043aa01fc7c73d2a269(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"_rv", "observation", "shops", "state", "step", "use_new"};
s->PrepareSlots(s_names);
if (static_cast<bool>(([&]() -> Value { auto v28100 = s->LocalAt(4); Value v28101; v28101 = Value(int64_t{2}); if (!static_cast<bool>(Binary("Eq", v28100, v28101))) return Value(false); v28100 = v28101; return Value(true); }()))) {
try {
auto v28103 = Get(Get(s->LocalAt(1), Value("farms")), ([&]() -> Value { auto v28104 = Value(int64_t{1}); return Binary("Sub", v28104, ([&]() -> Value { auto fn28105 = s->Global("int"); Arguments args28106; args28106.Add(Get(s->LocalAt(1), Value("player")), false); return Call(c, fn28105, std::move(args28106)); }())); }()));
s->SetAt(0, v28103);
auto v28107 = Tuple({([&]() -> Value { auto fn28108 = s->Global("round"); Arguments args28109; args28109.positional.reserve(2); args28109.Add(([&]() -> Value { auto fn28110 = s->Global("float"); Arguments args28111; args28111.Add(Get(s->LocalAt(0), Value("money")), false); return Call(c, fn28110, std::move(args28111)); }()), false); args28109.Add(Value(int64_t{3}), false); return Call(c, fn28108, std::move(args28109)); }()), ([&]() -> Value { auto fn28112 = s->Global("int"); Arguments args28113; args28113.Add(Get(Get(Get(s->LocalAt(1), Value("market")), Value("inventory")), Value("WHEAT")), false); return Call(c, fn28112, std::move(args28113)); }())});
Put(s->LocalAt(3), Value("rkey"), v28107);
} catch (const Error& error28102) {
if (Matches(error28102, s->Global("Exception"))) {
auto v28114 = Value{};
Put(s->LocalAt(3), Value("rkey"), v28114);
}
else { throw; }
}
}
if (static_cast<bool>(([&]() -> Value { auto v28115 = ([&]() -> Value { auto v28116 = s->LocalAt(4); Value v28117; v28117 = Value(int64_t{144}); if (!static_cast<bool>(Binary("GtE", v28116, v28117))) return Value(false); v28116 = v28117; return Value(true); }()); if (!static_cast<bool>(v28115)) return v28115; v28115 = Unary("Not", ([&]() -> Value { auto fn28118 = PrepareDictionaryGet(s->LocalAt(3)); Arguments args28119; args28119.Add(Value("day6"), false); return CallDictionaryGet(c, fn28118, std::move(args28119)); }())); return v28115; }()))) {
auto v28120 = ([&]() -> Value { auto fn28121 = s->Global("tuple"); Arguments args28122; args28122.Add(Slice(([&]() -> Value { auto v28123 = ([&]() -> Value { auto fn28124 = s->Global("_get"); Arguments args28125; args28125.positional.reserve(3); args28125.Add(([&]() -> Value { auto fn28126 = s->Global("_get"); Arguments args28127; args28127.positional.reserve(3); args28127.Add(s->LocalAt(1), false); args28127.Add(Value("town"), false); args28127.Add(([&]() -> Value { auto dict28128 = Dict(); return dict28128; }()), false); return Call(c, fn28126, std::move(args28127)); }()), false); args28125.Add(Value("unlocked_shops"), false); args28125.Add(List({}), false); return Call(c, fn28124, std::move(args28125)); }()); if (static_cast<bool>(v28123)) return v28123; v28123 = List({}); return v28123; }()), Value{}, Value(int64_t{2}), Value{}), false); return Call(c, fn28121, std::move(args28122)); }());
s->SetAt(2, v28120);
auto v28129 = ([&]() -> Value { auto v28130 = ([&]() -> Value { auto fn28132 = Attribute(s->LocalAt(2), "count"); Arguments args28133; args28133.Add(Value("YARN_STORE"), false); return Call(c, fn28132, std::move(args28133)); }()); Value v28131; v28131 = Value(int64_t{0}); if (!static_cast<bool>(Binary("LtE", v28130, v28131))) return Value(false); v28130 = v28131; return Value(true); }());
s->SetAt(5, v28129);
auto v28134 = (static_cast<bool>(s->LocalAt(5)) ? Value("EXP240") : Value("V39"));
Put(s->LocalAt(3), Value("expert"), v28134);
auto v28135 = (static_cast<bool>(s->LocalAt(5)) ? ([&]() -> Value { auto fn28136 = PrepareDictionaryGet(s->Global("_R108_SHOP_ROUTES")); Arguments args28137; args28137.positional.reserve(2); args28137.Add(s->LocalAt(2), false); args28137.Add(Value(int64_t{100}), false); return CallDictionaryGet(c, fn28136, std::move(args28137)); }()) : ([&]() -> Value { auto fn28138 = PrepareDictionaryGet(s->Global("_R110_OLD_SHOPS")); Arguments args28139; args28139.positional.reserve(2); args28139.Add(s->LocalAt(2), false); args28139.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn28138, std::move(args28139)); }()));
Put(s->LocalAt(3), Value("route"), v28135);
auto v28140 = ([&]() -> Value { auto fn28141 = PrepareDictionaryGet(s->Global("_V92_TABLE")); Arguments args28142; args28142.positional.reserve(2); args28142.Add(s->LocalAt(2), false); args28142.Add(Get(s->LocalAt(3), Value("route")), false); return CallDictionaryGet(c, fn28141, std::move(args28142)); }());
Put(s->LocalAt(3), Value("route"), v28140);
if (static_cast<bool>(([&]() -> Value { auto v28143 = ([&]() -> Value { auto v28144 = Value("YARN_STORE"); Value v28145; v28145 = s->LocalAt(2); if (!static_cast<bool>(Binary("In", v28144, v28145))) return Value(false); v28144 = v28145; return Value(true); }()); if (!static_cast<bool>(v28143)) return v28143; v28143 = ([&]() -> Value { auto v28146 = ([&]() -> Value { auto fn28148 = PrepareDictionaryGet(s->LocalAt(3)); Arguments args28149; args28149.Add(Value("rkey"), false); return CallDictionaryGet(c, fn28148, std::move(args28149)); }()); Value v28147; v28147 = s->Global("_V93_ROUTE_BY_RIVAL"); if (!static_cast<bool>(Binary("In", v28146, v28147))) return Value(false); v28146 = v28147; return Value(true); }()); return v28143; }()))) {
auto v28150 = Get(s->Global("_V93_ROUTE_BY_RIVAL"), Get(s->LocalAt(3), Value("rkey")));
Put(s->LocalAt(3), Value("route"), v28150);
}
auto v28151 = Value(true);
Put(s->LocalAt(3), Value("day6"), v28151);
}
if (static_cast<bool>(([&]() -> Value { auto v28152 = ([&]() -> Value { auto v28153 = s->LocalAt(4); Value v28154; v28154 = Value(int64_t{648}); if (!static_cast<bool>(Binary("GtE", v28153, v28154))) return Value(false); v28153 = v28154; return Value(true); }()); if (!static_cast<bool>(v28152)) return v28152; v28152 = Unary("Not", ([&]() -> Value { auto fn28155 = PrepareDictionaryGet(s->LocalAt(3)); Arguments args28156; args28156.Add(Value("day27"), false); return CallDictionaryGet(c, fn28155, std::move(args28156)); }())); return v28152; }()))) {
auto v28157 = Value(int64_t{2});
Put(s->LocalAt(3), Value("route"), v28157);
auto v28158 = Value(true);
Put(s->LocalAt(3), Value("day27"), v28158);
}
return ([&]() -> Value { auto fn28159 = PrepareDictionaryGet(s->LocalAt(3)); Arguments args28160; args28160.positional.reserve(2); args28160.Add(Value("route"), false); args28160.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn28159, std::move(args28160)); }());
return {};
}
}  // namespace kagg::opponents::compiled
