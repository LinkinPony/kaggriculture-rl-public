// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_bd68a9e3bc7390e12434(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"_", "d", "ev", "last", "length", "lib", "m", "n", "names", "out", "pos", "raw", "shops", "start", "t"};
s->PrepareSlots(s_names);
auto v27251 = ([&]() -> Value { auto fn27252 = s->Global("_v92_p_lib"); Arguments args27253; return Call(c, fn27252, std::move(args27253)); }());
s->SetAt(5, v27251);
if (static_cast<bool>(([&]() -> Value { auto v27254 = s->LocalAt(12); Value v27255; v27255 = s->LocalAt(5); if (!static_cast<bool>(Binary("In", v27254, v27255))) return Value(false); v27254 = v27255; return Value(true); }()))) {
return Get(s->LocalAt(5), s->LocalAt(12));
}
auto v27256 = List({Value("BAKERY"), Value("BRUNCH_SPOT"), Value("FARMERS_MARKET"), Value("ICE_CREAM_SHOP"), Value("PET_CAFE"), Value("PIZZA_SHOP"), Value("SMOOTHIE_SHOP"), Value("YARN_STORE")});
s->SetAt(8, v27256);
auto v27257 = List({});
s->SetAt(9, v27257);
if (static_cast<bool>(([&]() -> Value { auto v27258 = ([&]() -> Value { auto v27259 = ([&]() -> Value { auto fn27261 = s->Global("len"); Arguments args27262; args27262.Add(s->LocalAt(12), false); return Call(c, fn27261, std::move(args27262)); }()); Value v27260; v27260 = Value(int64_t{2}); if (!static_cast<bool>(Binary("Eq", v27259, v27260))) return Value(false); v27259 = v27260; return Value(true); }()); if (!static_cast<bool>(v27258)) return v27258; v27258 = ([&]() -> Value { auto v27263 = Get(s->LocalAt(12), Value(int64_t{0})); Value v27264; v27264 = s->LocalAt(8); if (!static_cast<bool>(Binary("In", v27263, v27264))) return Value(false); v27263 = v27264; return Value(true); }()); if (!static_cast<bool>(v27258)) return v27258; v27258 = ([&]() -> Value { auto v27265 = Get(s->LocalAt(12), Value(int64_t{1})); Value v27266; v27266 = s->LocalAt(8); if (!static_cast<bool>(Binary("In", v27265, v27266))) return Value(false); v27265 = v27266; return Value(true); }()); return v27258; }()))) {
if (static_cast<bool>(([&]() -> Value { auto v27267 = s->Global("_V92_P_RAW"); Value v27268; v27268 = Value{}; if (!static_cast<bool>(Binary("Is", v27267, v27268))) return Value(false); v27267 = v27268; return Value(true); }()))) {
auto v27269 = c.constants.at(6);
Put(s->globals, "_V92_P_RAW", v27269);
}
auto v27270 = Get(s->Global("_V92_P_INDEX"), ([&]() -> Value { auto v27271 = ([&]() -> Value { auto v27272 = ([&]() -> Value { auto fn27273 = Attribute(s->LocalAt(8), "index"); Arguments args27274; args27274.Add(Get(s->LocalAt(12), Value(int64_t{0})), false); return Call(c, fn27273, std::move(args27274)); }()); return Binary("Mult", v27272, Value(int64_t{8})); }()); return Binary("Add", v27271, ([&]() -> Value { auto fn27275 = Attribute(s->LocalAt(8), "index"); Arguments args27276; args27276.Add(Get(s->LocalAt(12), Value(int64_t{1})), false); return Call(c, fn27275, std::move(args27276)); }())); }()));
auto unpack27277 = Iterate(v27270);
ValidateUnpack(unpack27277, 2, false);
s->SetAt(13, unpack27277.at(0));
s->SetAt(4, unpack27277.at(1));
auto v27278 = s->Global("_V92_P_RAW");
s->SetAt(11, v27278);
auto v27279 = s->LocalAt(13);
s->SetAt(10, v27279);
auto v27280 = ([&]() -> Value { auto v27281 = Get(s->LocalAt(11), s->LocalAt(10)); return Binary("BitOr", v27281, ([&]() -> Value { auto v27282 = Get(s->LocalAt(11), ([&]() -> Value { auto v27283 = s->LocalAt(10); return Binary("Add", v27283, Value(int64_t{1})); }())); return Binary("LShift", v27282, Value(int64_t{8})); }())); }());
s->SetAt(7, v27280);
auto v27284 = s->LocalAt(10);
s->SetAt(10, Inplace("Add", v27284, Value(int64_t{2})));
for (const auto& item27285 : Iterate(([&]() -> Value { auto fn27286 = s->Global("range"); Arguments args27287; args27287.Add(s->LocalAt(7), false); return Call(c, fn27286, std::move(args27287)); }()))) {
s->SetAt(0, item27285);
auto v27288 = ([&]() -> Value { auto v27289 = Get(s->LocalAt(11), s->LocalAt(10)); return Binary("BitOr", v27289, ([&]() -> Value { auto v27290 = Get(s->LocalAt(11), ([&]() -> Value { auto v27291 = s->LocalAt(10); return Binary("Add", v27291, Value(int64_t{1})); }())); return Binary("LShift", v27290, Value(int64_t{8})); }())); }());
s->SetAt(6, v27288);
auto v27292 = s->LocalAt(10);
s->SetAt(10, Inplace("Add", v27292, Value(int64_t{2})));
auto v27293 = ([&]() -> Value { auto dict27294 = Dict(); return dict27294; }());
s->SetAt(2, v27293);
auto v27295 = Value(int64_t{0});
s->SetAt(3, v27295);
for (const auto& item27296 : Iterate(([&]() -> Value { auto fn27297 = s->Global("range"); Arguments args27298; args27298.Add(s->LocalAt(6), false); return Call(c, fn27297, std::move(args27298)); }()))) {
s->SetAt(0, item27296);
auto v27299 = Get(s->LocalAt(11), s->LocalAt(10));
s->SetAt(1, v27299);
auto v27300 = s->LocalAt(10);
s->SetAt(10, Inplace("Add", v27300, Value(int64_t{1})));
if (static_cast<bool>(([&]() -> Value { auto v27301 = s->LocalAt(1); Value v27302; v27302 = Value(int64_t{255}); if (!static_cast<bool>(Binary("Eq", v27301, v27302))) return Value(false); v27301 = v27302; return Value(true); }()))) {
auto v27303 = ([&]() -> Value { auto v27304 = Get(s->LocalAt(11), s->LocalAt(10)); return Binary("BitOr", v27304, ([&]() -> Value { auto v27305 = Get(s->LocalAt(11), ([&]() -> Value { auto v27306 = s->LocalAt(10); return Binary("Add", v27306, Value(int64_t{1})); }())); return Binary("LShift", v27305, Value(int64_t{8})); }())); }());
s->SetAt(14, v27303);
auto v27307 = s->LocalAt(10);
s->SetAt(10, Inplace("Add", v27307, Value(int64_t{2})));
}
else {
auto v27308 = ([&]() -> Value { auto v27309 = s->LocalAt(3); return Binary("Add", v27309, s->LocalAt(1)); }());
s->SetAt(14, v27308);
}
auto v27310 = Get(s->LocalAt(11), ([&]() -> Value { auto v27311 = s->LocalAt(10); return Binary("Add", v27311, Value(int64_t{1})); }()));
Put(s->LocalAt(2), Tuple({s->LocalAt(14), Get(s->LocalAt(11), s->LocalAt(10))}), v27310);
auto v27312 = s->LocalAt(10);
s->SetAt(10, Inplace("Add", v27312, Value(int64_t{2})));
auto v27313 = s->LocalAt(14);
s->SetAt(3, v27313);
}
(void)([&]() -> Value { auto fn27314 = Attribute(s->LocalAt(9), "append"); Arguments args27315; args27315.Add(Tuple({Unary("USub", Value(int64_t{1})), s->LocalAt(2)}), false); return Call(c, fn27314, std::move(args27315)); }());
}
}
auto v27316 = s->LocalAt(9);
Put(s->LocalAt(5), s->LocalAt(12), v27316);
return s->LocalAt(9);
return {};
}
}  // namespace kagg::opponents::compiled
