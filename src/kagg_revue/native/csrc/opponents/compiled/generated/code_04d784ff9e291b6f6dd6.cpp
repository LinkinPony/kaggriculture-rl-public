// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_04d784ff9e291b6f6dd6(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"draw", "i", "inv", "item", "obs", "player", "prev", "race", "sold", "st", "step"};
s->PrepareSlots(s_names);
auto v27317 = Tuple({([&]() -> Value { auto fn27318 = s->Global("int"); Arguments args27319; args27319.Add(Get(s->LocalAt(4), Value("player")), false); return Call(c, fn27318, std::move(args27319)); }()), ([&]() -> Value { auto fn27320 = s->Global("int"); Arguments args27321; args27321.Add(Get(s->LocalAt(4), Value("step")), false); return Call(c, fn27320, std::move(args27321)); }())});
auto unpack27322 = Iterate(v27317);
ValidateUnpack(unpack27322, 2, false);
s->SetAt(5, unpack27322.at(0));
s->SetAt(10, unpack27322.at(1));
auto v27323 = ([&]() -> Value { auto v27324 = ([&]() -> Value { auto fn27325 = PrepareDictionaryGet(s->Global("_V9_RACE")); Arguments args27326; args27326.Add(s->LocalAt(5), false); return CallDictionaryGet(c, fn27325, std::move(args27326)); }()); if (static_cast<bool>(v27324)) return v27324; v27324 = ([&]() -> Value { auto dict27327 = Dict(); return dict27327; }()); return v27324; }());
s->SetAt(7, v27323);
auto v27328 = ([&]() -> Value { auto fn27329 = PrepareDictionaryGet(s->LocalAt(7)); Arguments args27330; args27330.Add(Value("prev"), false); return CallDictionaryGet(c, fn27329, std::move(args27330)); }());
s->SetAt(6, v27328);
if (static_cast<bool>(([&]() -> Value { auto v27331 = Unary("Not", s->LocalAt(6)); if (static_cast<bool>(v27331)) return v27331; v27331 = ([&]() -> Value { auto v27332 = Get(s->LocalAt(6), Value("step")); Value v27333; v27333 = ([&]() -> Value { auto v27334 = s->LocalAt(10); return Binary("Sub", v27334, Value(int64_t{1})); }()); if (!static_cast<bool>(Binary("NotEq", v27332, v27333))) return Value(false); v27332 = v27333; return Value(true); }()); return v27331; }()))) {
return Value{};
}
auto v27335 = Get(Get(s->LocalAt(4), Value("market")), Value("inventory"));
s->SetAt(2, v27335);
auto v27336 = ([&]() -> Value { auto fn27337 = s->Global("_v9_town_draw"); Arguments args27338; args27338.positional.reserve(2); args27338.Add(Get(s->LocalAt(6), Value("shops")), false); args27338.Add(Get(s->LocalAt(6), Value("step")), false); return Call(c, fn27337, std::move(args27338)); }());
s->SetAt(0, v27336);
for (const auto& item27339 : Iterate(([&]() -> Value { auto fn27340 = s->Global("enumerate"); Arguments args27341; args27341.Add(s->Global("_V92_P_ITEMS"), false); return Call(c, fn27340, std::move(args27341)); }()))) {
auto unpack27342 = Iterate(item27339);
ValidateUnpack(unpack27342, 2, false);
s->SetAt(1, unpack27342.at(0));
s->SetAt(3, unpack27342.at(1));
if (static_cast<bool>(([&]() -> Value { auto v27343 = ([&]() -> Value { auto fn27345 = PrepareDictionaryGet(Get(s->LocalAt(6), Value("prices"))); Arguments args27346; args27346.positional.reserve(2); args27346.Add(s->LocalAt(3), false); args27346.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn27345, std::move(args27346)); }()); Value v27344; v27344 = Value(int64_t{3}); if (!static_cast<bool>(Binary("LtE", v27343, v27344))) return Value(false); v27343 = v27344; return Value(true); }()))) {
continue;
}
auto v27347 = ([&]() -> Value { auto v27348 = ([&]() -> Value { auto v27349 = ([&]() -> Value { auto v27350 = Get(s->LocalAt(2), s->LocalAt(3)); return Binary("Sub", v27350, Get(Get(s->LocalAt(6), Value("inventory")), s->LocalAt(3))); }()); return Binary("Add", v27349, ([&]() -> Value { auto fn27351 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args27352; args27352.positional.reserve(2); args27352.Add(s->LocalAt(3), false); args27352.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn27351, std::move(args27352)); }())); }()); return Binary("Sub", v27348, ([&]() -> Value { auto fn27353 = PrepareDictionaryGet(Get(s->LocalAt(6), Value("own"))); Arguments args27354; args27354.positional.reserve(2); args27354.Add(s->LocalAt(3), false); args27354.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn27353, std::move(args27354)); }())); }());
s->SetAt(8, v27347);
if (static_cast<bool>(([&]() -> Value { auto v27355 = s->LocalAt(8); Value v27356; v27356 = Value(int64_t{2}); if (!static_cast<bool>(Binary("GtE", v27355, v27356))) return Value(false); v27355 = v27356; return Value(true); }()))) {
auto v27357 = s->LocalAt(8);
Put(Get(s->LocalAt(9), Value("obs")), Tuple({([&]() -> Value { auto v27358 = s->LocalAt(10); return Binary("Sub", v27358, Value(int64_t{1})); }()), s->LocalAt(1)}), v27357);
}
}
return {};
}
}  // namespace kagg::opponents::compiled
