#include "opponents/compiled/forecast.hpp"
// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_dc5e8d9393a863e63342(Context& c, const ScopePtr& s) {
if (auto result = Forecast(c, s)) return *result;
static constexpr const char* s_names[] = {"cands", "ep", "ev", "f", "i", "lo", "m", "miss", "obs", "q", "recent", "scored", "seen", "shops", "st", "step", "tt"};
s->PrepareSlots(s_names);
auto v27359 = ([&]() -> Value { auto fn27360 = s->Global("int"); Arguments args27361; args27361.Add(Get(s->LocalAt(8), Value("step")), false); return Call(c, fn27360, std::move(args27361)); }());
s->SetAt(15, v27359);
auto v27362 = ([&]() -> Value { auto fn27363 = s->Global("tuple"); Arguments args27364; args27364.Add(Slice(Get(Get(s->LocalAt(8), Value("town")), Value("unlocked_shops")), Value{}, Value(int64_t{2}), Value{}), false); return Call(c, fn27363, std::move(args27364)); }());
s->SetAt(13, v27362);
auto v27365 = ([&]() -> Value { auto fn27366 = s->Global("_v92_p_pair"); Arguments args27367; args27367.Add(s->LocalAt(13), false); return Call(c, fn27366, std::move(args27367)); }());
s->SetAt(0, v27365);
if (static_cast<bool>(([&]() -> Value { auto v27368 = s->Global("_V92_EP"); Value v27369; v27369 = Value{}; if (!static_cast<bool>(Binary("IsNot", v27368, v27369))) return Value(false); v27368 = v27369; return Value(true); }()))) {
auto v27370 = ([&]() -> Value { auto comp27371 = std::make_shared<Scope>(); comp27371->globals = s->globals; comp27371->parent = s; static constexpr const char* comp27371_names[] = {"c"}; comp27371->PrepareSlots(comp27371_names); auto result27372 = List(); for (const auto& item27373 : Iterate(s->LocalAt(0))) { comp27371->SetAt(0, item27373); if (!static_cast<bool>(([&]() -> Value { auto v27374 = ([&]() -> Value { auto v27376 = Get(comp27371->LocalAt(0), Value(int64_t{0})); return Binary("Mod", v27376, Value(int64_t{2})); }()); Value v27375; v27375 = ([&]() -> Value { auto v27377 = comp27371->Global("_V92_EP"); return Binary("Mod", v27377, Value(int64_t{2})); }()); if (!static_cast<bool>(Binary("NotEq", v27374, v27375))) return Value(false); v27374 = v27375; return Value(true); }()))) continue; result27372.node()->sequence.push_back(comp27371->LocalAt(0)); } return result27372; }());
s->SetAt(0, v27370);
}
auto v27378 = Get(s->LocalAt(14), Value("obs"));
s->SetAt(12, v27378);
auto v27379 = ([&]() -> Value { auto v27380 = s->LocalAt(15); return Binary("Sub", v27380, Value(int64_t{240})); }());
s->SetAt(5, v27379);
auto v27381 = List({});
s->SetAt(11, v27381);
auto v27382 = ([&]() -> Value { auto comp27383 = std::make_shared<Scope>(); comp27383->globals = s->globals; comp27383->parent = s; static constexpr const char* comp27383_names[] = {"i", "tt"}; comp27383->PrepareSlots(comp27383_names); auto result27384 = List(); for (const auto& item27385 : Iterate(s->LocalAt(12))) { auto unpack27386 = Iterate(item27385); ValidateUnpack(unpack27386, 2, false); comp27383->SetAt(1, unpack27386.at(0)); comp27383->SetAt(0, unpack27386.at(1)); if (!static_cast<bool>(([&]() -> Value { auto v27387 = comp27383->LocalAt(1); Value v27388; v27388 = comp27383->Captured("lo"); if (!static_cast<bool>(Binary("GtE", v27387, v27388))) return Value(false); v27387 = v27388; return Value(true); }()))) continue; result27384.node()->sequence.push_back(Tuple({comp27383->LocalAt(1), comp27383->LocalAt(0)})); } return result27384; }());
s->SetAt(10, v27382);
for (const auto& item27389 : Iterate(s->LocalAt(0))) {
auto unpack27390 = Iterate(item27389);
ValidateUnpack(unpack27390, 2, false);
s->SetAt(1, unpack27390.at(0));
s->SetAt(2, unpack27390.at(1));
auto v27391 = Value(int64_t{0});
s->SetAt(6, v27391);
s->SetAt(3, v27391);
for (const auto& item27392 : Iterate(([&]() -> Value { auto fn27393 = Attribute(s->LocalAt(2), "items"); Arguments args27394; return Call(c, fn27393, std::move(args27394)); }()))) {
auto unpack27395 = Iterate(item27392);
ValidateUnpack(unpack27395, 2, false);
auto unpack27396 = Iterate(unpack27395.at(0));
ValidateUnpack(unpack27396, 2, false);
s->SetAt(16, unpack27396.at(0));
s->SetAt(4, unpack27396.at(1));
s->SetAt(9, unpack27395.at(1));
if (static_cast<bool>(([&]() -> Value { auto v27397 = s->LocalAt(5); Value v27398; v27398 = s->LocalAt(16); if (!static_cast<bool>(Binary("LtE", v27397, v27398))) return Value(false); v27397 = v27398; v27398 = ([&]() -> Value { auto v27399 = s->LocalAt(15); return Binary("Sub", v27399, Value(int64_t{1})); }()); if (!static_cast<bool>(Binary("Lt", v27397, v27398))) return Value(false); v27397 = v27398; return Value(true); }()))) {
if (static_cast<bool>(([&]() -> Value { auto v27400 = ([&]() -> Value { auto v27401 = Tuple({s->LocalAt(16), s->LocalAt(4)}); Value v27402; v27402 = s->LocalAt(12); if (!static_cast<bool>(Binary("In", v27401, v27402))) return Value(false); v27401 = v27402; return Value(true); }()); if (static_cast<bool>(v27400)) return v27400; v27400 = ([&]() -> Value { auto v27403 = Tuple({([&]() -> Value { auto v27405 = s->LocalAt(16); return Binary("Sub", v27405, Value(int64_t{1})); }()), s->LocalAt(4)}); Value v27404; v27404 = s->LocalAt(12); if (!static_cast<bool>(Binary("In", v27403, v27404))) return Value(false); v27403 = v27404; return Value(true); }()); if (static_cast<bool>(v27400)) return v27400; v27400 = ([&]() -> Value { auto v27406 = Tuple({([&]() -> Value { auto v27408 = s->LocalAt(16); return Binary("Add", v27408, Value(int64_t{1})); }()), s->LocalAt(4)}); Value v27407; v27407 = s->LocalAt(12); if (!static_cast<bool>(Binary("In", v27406, v27407))) return Value(false); v27406 = v27407; return Value(true); }()); return v27400; }()))) {
auto v27409 = s->LocalAt(6);
s->SetAt(6, Inplace("Add", v27409, Value(int64_t{1})));
}
else {
auto v27410 = s->LocalAt(3);
s->SetAt(3, Inplace("Add", v27410, Value(int64_t{1})));
}
}
}
auto v27411 = ([&]() -> Value { auto fn27412 = s->Global("sum"); Arguments args27413; args27413.Add(([&]() -> Value { auto comp27414 = std::make_shared<Scope>(); comp27414->globals = s->globals; comp27414->parent = s; static constexpr const char* comp27414_names[] = {"i", "tt"}; comp27414->PrepareSlots(comp27414_names); auto result27415 = List(); for (const auto& item27416 : Iterate(s->LocalAt(10))) { auto unpack27417 = Iterate(item27416); ValidateUnpack(unpack27417, 2, false); comp27414->SetAt(1, unpack27417.at(0)); comp27414->SetAt(0, unpack27417.at(1)); if (!static_cast<bool>(([&]() -> Value { auto v27418 = ([&]() -> Value { auto v27419 = Tuple({comp27414->LocalAt(1), comp27414->LocalAt(0)}); Value v27420; v27420 = comp27414->Captured("ev"); if (!static_cast<bool>(Binary("NotIn", v27419, v27420))) return Value(false); v27419 = v27420; return Value(true); }()); if (!static_cast<bool>(v27418)) return v27418; v27418 = ([&]() -> Value { auto v27421 = Tuple({([&]() -> Value { auto v27423 = comp27414->LocalAt(1); return Binary("Sub", v27423, Value(int64_t{1})); }()), comp27414->LocalAt(0)}); Value v27422; v27422 = comp27414->Captured("ev"); if (!static_cast<bool>(Binary("NotIn", v27421, v27422))) return Value(false); v27421 = v27422; return Value(true); }()); if (!static_cast<bool>(v27418)) return v27418; v27418 = ([&]() -> Value { auto v27424 = Tuple({([&]() -> Value { auto v27426 = comp27414->LocalAt(1); return Binary("Add", v27426, Value(int64_t{1})); }()), comp27414->LocalAt(0)}); Value v27425; v27425 = comp27414->Captured("ev"); if (!static_cast<bool>(Binary("NotIn", v27424, v27425))) return Value(false); v27424 = v27425; return Value(true); }()); return v27418; }()))) continue; result27415.node()->sequence.push_back(Value(int64_t{1})); } return result27415; }()), false); return Call(c, fn27412, std::move(args27413)); }());
s->SetAt(7, v27411);
(void)([&]() -> Value { auto fn27427 = Attribute(s->LocalAt(11), "append"); Arguments args27428; args27428.Add(Tuple({([&]() -> Value { auto v27429 = ([&]() -> Value { auto v27430 = s->LocalAt(6); return Binary("Sub", v27430, ([&]() -> Value { auto v27431 = Value(0.5); return Binary("Mult", v27431, s->LocalAt(3)); }())); }()); return Binary("Sub", v27429, ([&]() -> Value { auto v27432 = Value(0.5); return Binary("Mult", v27432, s->LocalAt(7)); }())); }()), s->LocalAt(2)}), false); return Call(c, fn27427, std::move(args27428)); }());
}
(void)([&]() -> Value { auto fn27433 = Attribute(s->LocalAt(11), "sort"); Arguments args27434; args27434.Keyword("key", Define(&Code_f119e35edfa3b8db337f, s, Signature{{"x"}, {}, {}, {}, "", "", ([]() -> std::span<const char* const> { static constexpr const char* names[] = {"x"}; return names; }())}, true, "<lambda>")); return Call(c, fn27433, std::move(args27434)); }());
return ([&]() -> Value { auto comp27435 = std::make_shared<Scope>(); comp27435->globals = s->globals; comp27435->parent = s; static constexpr const char* comp27435_names[] = {"_", "ev"}; comp27435->PrepareSlots(comp27435_names); auto result27436 = List(); for (const auto& item27437 : Iterate(Slice(s->LocalAt(11), Value{}, s->Global("_V92_P_TOP"), Value{}))) { auto unpack27438 = Iterate(item27437); ValidateUnpack(unpack27438, 2, false); comp27435->SetAt(0, unpack27438.at(0)); comp27435->SetAt(1, unpack27438.at(1)); result27436.node()->sequence.push_back(comp27435->LocalAt(1)); } return result27436; }());
return {};
}
}  // namespace kagg::opponents::compiled
