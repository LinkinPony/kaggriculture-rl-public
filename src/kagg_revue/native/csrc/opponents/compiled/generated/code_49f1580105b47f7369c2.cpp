// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_49f1580105b47f7369c2(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "birth", "bonus", "day", "extra_labor", "farm", "fertilizer", "inventory", "native_hires", "obs", "price", "tile", "until", "x", "y"};
s->PrepareSlots(s_names);
if (static_cast<bool>(([&]() -> Value { auto v9273 = Get(Get(Get(s->LocalAt(9), Value("market")), Value("prices")), Value("FERTILIZER")); Value v9274; v9274 = Value(int64_t{30}); if (!static_cast<bool>(Binary("LtE", v9273, v9274))) return Value(false); v9273 = v9274; return Value(true); }()))) {
return Value(true);
}
auto v9275 = Get(Get(s->LocalAt(9), Value("farms")), Get(s->LocalAt(9), Value("player")));
s->SetAt(5, v9275);
auto v9276 = ([&]() -> Value { auto v9277 = ([&]() -> Value { auto fn9278 = s->Global("int"); Arguments args9279; args9279.Add(Get(s->LocalAt(9), Value("step")), false); return Call(c, fn9278, std::move(args9279)); }()); return Binary("FloorDiv", v9277, Value(int64_t{24})); }());
s->SetAt(3, v9276);
auto v9280 = Value(int64_t{0});
s->SetAt(2, v9280);
for (const auto& item9281 : Iterate(Tuple({Value(int64_t{5}), Value(int64_t{6})}))) {
s->SetAt(14, item9281);
for (const auto& item9282 : Iterate(([&]() -> Value { auto fn9283 = s->Global("range"); Arguments args9284; args9284.positional.reserve(2); args9284.Add(Value(int64_t{5}), false); args9284.Add(Value(int64_t{10}), false); return Call(c, fn9283, std::move(args9284)); }()))) {
s->SetAt(13, item9282);
auto v9285 = Get(Get(Get(s->LocalAt(5), Value("tiles")), s->LocalAt(14)), s->LocalAt(13));
s->SetAt(11, v9285);
if (static_cast<bool>(([&]() -> Value { auto v9286 = Unary("Not", ([&]() -> Value { auto fn9287 = s->Global("isinstance"); Arguments args9288; args9288.positional.reserve(2); args9288.Add(s->LocalAt(11), false); args9288.Add(s->Global("dict"), false); return Call(c, fn9287, std::move(args9288)); }())); if (static_cast<bool>(v9286)) return v9286; v9286 = ([&]() -> Value { auto v9289 = ([&]() -> Value { auto fn9291 = PrepareDictionaryGet(s->LocalAt(11)); Arguments args9292; args9292.Add(Value("crop"), false); return CallDictionaryGet(c, fn9291, std::move(args9292)); }()); Value v9290; v9290 = Value("TOMATO"); if (!static_cast<bool>(Binary("NotEq", v9289, v9290))) return Value(false); v9289 = v9290; return Value(true); }()); return v9286; }()))) {
continue;
}
auto v9293 = Get(s->LocalAt(11), Value("planted_day"));
s->SetAt(1, v9293);
auto v9294 = ([&]() -> Value { auto fn9295 = PrepareDictionaryGet(s->LocalAt(11)); Arguments args9296; args9296.positional.reserve(2); args9296.Add(Value("fertilized_until_day"), false); args9296.Add(Unary("USub", Value(int64_t{1})), false); return CallDictionaryGet(c, fn9295, std::move(args9296)); }());
s->SetAt(12, v9294);
auto v9297 = s->LocalAt(2);
s->SetAt(2, Inplace("Add", v9297, ([&]() -> Value { auto fn9298 = s->Global("sum"); Arguments args9299; args9299.Add(([&]() -> Value { auto comp9300 = std::make_shared<Scope>(); comp9300->globals = s->globals; comp9300->parent = s; static constexpr const char* comp9300_names[] = {"d"}; comp9300->PrepareSlots(comp9300_names); auto result9301 = List(); for (const auto& item9302 : Iterate(([&]() -> Value { auto fn9303 = s->Global("range"); Arguments args9304; args9304.positional.reserve(2); args9304.Add(s->LocalAt(3), false); args9304.Add(([&]() -> Value { auto v9305 = s->LocalAt(3); return Binary("Add", v9305, Value(int64_t{3})); }()), false); return Call(c, fn9303, std::move(args9304)); }()))) { comp9300->SetAt(0, item9302); result9301.node()->sequence.push_back(([&]() -> Value { auto v9306 = ([&]() -> Value { auto v9307 = comp9300->Captured("until"); Value v9308; v9308 = comp9300->LocalAt(0); if (!static_cast<bool>(Binary("Lt", v9307, v9308))) return Value(false); v9307 = v9308; return Value(true); }()); if (!static_cast<bool>(v9306)) return v9306; v9306 = ([&]() -> Value { auto v9309 = Value(int64_t{8}); Value v9310; v9310 = ([&]() -> Value { auto v9311 = ([&]() -> Value { auto v9312 = comp9300->LocalAt(0); return Binary("Add", v9312, Value(int64_t{1})); }()); return Binary("Sub", v9311, comp9300->Captured("birth")); }()); if (!static_cast<bool>(Binary("LtE", v9309, v9310))) return Value(false); v9309 = v9310; v9310 = Value(int64_t{11}); if (!static_cast<bool>(Binary("LtE", v9309, v9310))) return Value(false); v9309 = v9310; return Value(true); }()); return v9306; }())); } return result9301; }()), false); return Call(c, fn9298, std::move(args9299)); }())));
}
}
if (static_cast<bool>(Unary("Not", s->LocalAt(2)))) {
return Value(false);
}
auto v9313 = Get(Get(s->LocalAt(9), Value("market")), Value("inventory"));
s->SetAt(7, v9313);
auto v9314 = ([&]() -> Value { auto fn9315 = s->Global("max"); Arguments args9316; args9316.positional.reserve(2); args9316.Add(Value(int64_t{1}), false); args9316.Add(([&]() -> Value { auto v9317 = ([&]() -> Value { auto fn9318 = s->Global("_r37_market_price"); Arguments args9319; args9319.positional.reserve(2); args9319.Add(Value("TOMATO"), false); args9319.Add(([&]() -> Value { auto v9320 = ([&]() -> Value { auto v9321 = Get(s->LocalAt(7), Value("TOMATO")); return Binary("Add", v9321, s->LocalAt(2)); }()); return Binary("Add", v9320, Value(int64_t{10})); }()), false); return Call(c, fn9318, std::move(args9319)); }()); return Binary("Sub", v9317, Value(int64_t{2})); }()), false); return Call(c, fn9315, std::move(args9316)); }());
s->SetAt(10, v9314);
auto v9322 = ([&]() -> Value { auto fn9323 = s->Global("max"); Arguments args9324; args9324.positional.reserve(2); args9324.Add(Value(int64_t{1}), false); args9324.Add(([&]() -> Value { auto v9325 = ([&]() -> Value { auto fn9326 = s->Global("_r37_market_price"); Arguments args9327; args9327.positional.reserve(2); args9327.Add(Value("FERTILIZER"), false); args9327.Add(([&]() -> Value { auto v9328 = Get(s->LocalAt(7), Value("FERTILIZER")); return Binary("Sub", v9328, Value(int64_t{10})); }()), false); return Call(c, fn9326, std::move(args9327)); }()); return Binary("Add", v9325, Value(int64_t{2})); }()), false); return Call(c, fn9323, std::move(args9324)); }());
s->SetAt(6, v9322);
auto v9329 = ([&]() -> Value { auto fn9330 = s->Global("sum"); Arguments args9331; args9331.Add(([&]() -> Value { auto comp9332 = std::make_shared<Scope>(); comp9332->globals = s->globals; comp9332->parent = s; static constexpr const char* comp9332_names[] = {"o"}; comp9332->PrepareSlots(comp9332_names); auto result9333 = List(); for (const auto& item9334 : Iterate(([&]() -> Value { auto fn9335 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args9336; args9336.positional.reserve(2); args9336.Add(Value("market"), false); args9336.Add(List({}), false); return CallDictionaryGet(c, fn9335, std::move(args9336)); }()))) { comp9332->SetAt(0, item9334); result9333.node()->sequence.push_back(([&]() -> Value { auto v9337 = ([&]() -> Value { auto fn9338 = comp9332->Global("bool"); Arguments args9339; args9339.Add(comp9332->LocalAt(0), false); return Call(c, fn9338, std::move(args9339)); }()); if (!static_cast<bool>(v9337)) return v9337; v9337 = ([&]() -> Value { auto v9340 = Get(comp9332->LocalAt(0), Value(int64_t{0})); Value v9341; v9341 = Value("HIRE"); if (!static_cast<bool>(Binary("Eq", v9340, v9341))) return Value(false); v9340 = v9341; return Value(true); }()); return v9337; }())); } return result9333; }()), false); return Call(c, fn9330, std::move(args9331)); }());
s->SetAt(8, v9329);
auto v9342 = ([&]() -> Value { auto fn9343 = s->Global("_v219_fib"); Arguments args9344; args9344.Add(([&]() -> Value { auto v9345 = ([&]() -> Value { auto v9346 = ([&]() -> Value { auto fn9347 = s->Global("int"); Arguments args9348; args9348.Add(Get(s->LocalAt(5), Value("hires_today")), false); return Call(c, fn9347, std::move(args9348)); }()); return Binary("Add", v9346, s->LocalAt(8)); }()); return Binary("Add", v9345, Value(int64_t{3})); }()), false); return Call(c, fn9343, std::move(args9344)); }());
s->SetAt(4, v9342);
return ([&]() -> Value { auto v9349 = ([&]() -> Value { auto v9351 = s->LocalAt(2); return Binary("Mult", v9351, s->LocalAt(10)); }()); Value v9350; v9350 = ([&]() -> Value { auto v9352 = ([&]() -> Value { auto v9353 = Value(int64_t{2}); return Binary("Mult", v9353, ([&]() -> Value { auto v9354 = ([&]() -> Value { auto v9355 = Value(int64_t{10}); return Binary("Mult", v9355, s->LocalAt(6)); }()); return Binary("Add", v9354, s->LocalAt(4)); }())); }()); return Binary("Add", v9352, Value(int64_t{100})); }()); if (!static_cast<bool>(Binary("GtE", v9349, v9350))) return Value(false); v9349 = v9350; return Value(true); }());
return {};
}
}  // namespace kagg::opponents::compiled
