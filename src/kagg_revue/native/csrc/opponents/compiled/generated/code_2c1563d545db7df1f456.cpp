// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_2c1563d545db7df1f456(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"_", "d", "ev", "last", "length", "lib", "m", "n", "names", "out", "pos", "raw", "shops", "start", "t"};
s->PrepareSlots(s_names);
auto v29318 = ([&]() -> Value { auto fn29319 = s->Global("_v92_p_lib"); Arguments args29320; return Call(c, fn29319, std::move(args29320)); }());
s->SetAt(5, v29318);
if (static_cast<bool>(([&]() -> Value { auto v29321 = s->LocalAt(12); Value v29322; v29322 = s->LocalAt(5); if (!static_cast<bool>(Binary("In", v29321, v29322))) return Value(false); v29321 = v29322; return Value(true); }()))) {
return Get(s->LocalAt(5), s->LocalAt(12));
}
auto v29323 = List({Value("BAKERY"), Value("BRUNCH_SPOT"), Value("FARMERS_MARKET"), Value("ICE_CREAM_SHOP"), Value("PET_CAFE"), Value("PIZZA_SHOP"), Value("SMOOTHIE_SHOP"), Value("YARN_STORE")});
s->SetAt(8, v29323);
auto v29324 = List({});
s->SetAt(9, v29324);
if (static_cast<bool>(([&]() -> Value { auto v29325 = ([&]() -> Value { auto v29326 = ([&]() -> Value { auto fn29328 = s->Global("len"); Arguments args29329; args29329.Add(s->LocalAt(12), false); return Call(c, fn29328, std::move(args29329)); }()); Value v29327; v29327 = Value(int64_t{2}); if (!static_cast<bool>(Binary("Eq", v29326, v29327))) return Value(false); v29326 = v29327; return Value(true); }()); if (!static_cast<bool>(v29325)) return v29325; v29325 = ([&]() -> Value { auto v29330 = Get(s->LocalAt(12), Value(int64_t{0})); Value v29331; v29331 = s->LocalAt(8); if (!static_cast<bool>(Binary("In", v29330, v29331))) return Value(false); v29330 = v29331; return Value(true); }()); if (!static_cast<bool>(v29325)) return v29325; v29325 = ([&]() -> Value { auto v29332 = Get(s->LocalAt(12), Value(int64_t{1})); Value v29333; v29333 = s->LocalAt(8); if (!static_cast<bool>(Binary("In", v29332, v29333))) return Value(false); v29332 = v29333; return Value(true); }()); return v29325; }()))) {
if (static_cast<bool>(([&]() -> Value { auto v29334 = s->Global("_V92_P_RAW"); Value v29335; v29335 = Value{}; if (!static_cast<bool>(Binary("Is", v29334, v29335))) return Value(false); v29334 = v29335; return Value(true); }()))) {
auto v29336 = c.constants.at(12);
Put(s->globals, "_V92_P_RAW", v29336);
}
auto v29337 = Get(s->Global("_V92_P_INDEX"), ([&]() -> Value { auto v29338 = ([&]() -> Value { auto v29339 = ([&]() -> Value { auto fn29340 = Attribute(s->LocalAt(8), "index"); Arguments args29341; args29341.Add(Get(s->LocalAt(12), Value(int64_t{0})), false); return Call(c, fn29340, std::move(args29341)); }()); return Binary("Mult", v29339, Value(int64_t{8})); }()); return Binary("Add", v29338, ([&]() -> Value { auto fn29342 = Attribute(s->LocalAt(8), "index"); Arguments args29343; args29343.Add(Get(s->LocalAt(12), Value(int64_t{1})), false); return Call(c, fn29342, std::move(args29343)); }())); }()));
auto unpack29344 = Iterate(v29337);
ValidateUnpack(unpack29344, 2, false);
s->SetAt(13, unpack29344.at(0));
s->SetAt(4, unpack29344.at(1));
auto v29345 = s->Global("_V92_P_RAW");
s->SetAt(11, v29345);
auto v29346 = s->LocalAt(13);
s->SetAt(10, v29346);
auto v29347 = ([&]() -> Value { auto v29348 = Get(s->LocalAt(11), s->LocalAt(10)); return Binary("BitOr", v29348, ([&]() -> Value { auto v29349 = Get(s->LocalAt(11), ([&]() -> Value { auto v29350 = s->LocalAt(10); return Binary("Add", v29350, Value(int64_t{1})); }())); return Binary("LShift", v29349, Value(int64_t{8})); }())); }());
s->SetAt(7, v29347);
auto v29351 = s->LocalAt(10);
s->SetAt(10, Inplace("Add", v29351, Value(int64_t{2})));
for (const auto& item29352 : Iterate(([&]() -> Value { auto fn29353 = s->Global("range"); Arguments args29354; args29354.Add(s->LocalAt(7), false); return Call(c, fn29353, std::move(args29354)); }()))) {
s->SetAt(0, item29352);
auto v29355 = ([&]() -> Value { auto v29356 = Get(s->LocalAt(11), s->LocalAt(10)); return Binary("BitOr", v29356, ([&]() -> Value { auto v29357 = Get(s->LocalAt(11), ([&]() -> Value { auto v29358 = s->LocalAt(10); return Binary("Add", v29358, Value(int64_t{1})); }())); return Binary("LShift", v29357, Value(int64_t{8})); }())); }());
s->SetAt(6, v29355);
auto v29359 = s->LocalAt(10);
s->SetAt(10, Inplace("Add", v29359, Value(int64_t{2})));
auto v29360 = ([&]() -> Value { auto dict29361 = Dict(); return dict29361; }());
s->SetAt(2, v29360);
auto v29362 = Value(int64_t{0});
s->SetAt(3, v29362);
for (const auto& item29363 : Iterate(([&]() -> Value { auto fn29364 = s->Global("range"); Arguments args29365; args29365.Add(s->LocalAt(6), false); return Call(c, fn29364, std::move(args29365)); }()))) {
s->SetAt(0, item29363);
auto v29366 = Get(s->LocalAt(11), s->LocalAt(10));
s->SetAt(1, v29366);
auto v29367 = s->LocalAt(10);
s->SetAt(10, Inplace("Add", v29367, Value(int64_t{1})));
if (static_cast<bool>(([&]() -> Value { auto v29368 = s->LocalAt(1); Value v29369; v29369 = Value(int64_t{255}); if (!static_cast<bool>(Binary("Eq", v29368, v29369))) return Value(false); v29368 = v29369; return Value(true); }()))) {
auto v29370 = ([&]() -> Value { auto v29371 = Get(s->LocalAt(11), s->LocalAt(10)); return Binary("BitOr", v29371, ([&]() -> Value { auto v29372 = Get(s->LocalAt(11), ([&]() -> Value { auto v29373 = s->LocalAt(10); return Binary("Add", v29373, Value(int64_t{1})); }())); return Binary("LShift", v29372, Value(int64_t{8})); }())); }());
s->SetAt(14, v29370);
auto v29374 = s->LocalAt(10);
s->SetAt(10, Inplace("Add", v29374, Value(int64_t{2})));
}
else {
auto v29375 = ([&]() -> Value { auto v29376 = s->LocalAt(3); return Binary("Add", v29376, s->LocalAt(1)); }());
s->SetAt(14, v29375);
}
auto v29377 = Get(s->LocalAt(11), ([&]() -> Value { auto v29378 = s->LocalAt(10); return Binary("Add", v29378, Value(int64_t{1})); }()));
Put(s->LocalAt(2), Tuple({s->LocalAt(14), Get(s->LocalAt(11), s->LocalAt(10))}), v29377);
auto v29379 = s->LocalAt(10);
s->SetAt(10, Inplace("Add", v29379, Value(int64_t{2})));
auto v29380 = s->LocalAt(14);
s->SetAt(3, v29380);
}
(void)([&]() -> Value { auto fn29381 = Attribute(s->LocalAt(9), "append"); Arguments args29382; args29382.Add(Tuple({Unary("USub", Value(int64_t{1})), s->LocalAt(2)}), false); return Call(c, fn29381, std::move(args29382)); }());
}
}
auto v29383 = s->LocalAt(9);
Put(s->LocalAt(5), s->LocalAt(12), v29383);
return s->LocalAt(9);
return {};
}
}  // namespace kagg::opponents::compiled
