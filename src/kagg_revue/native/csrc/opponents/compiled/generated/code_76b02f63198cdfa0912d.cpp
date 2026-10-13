// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_76b02f63198cdfa0912d(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"configuration", "observation", "pending", "player", "result", "standard", "state", "step"};
s->PrepareSlots(s_names);
auto v11394 = ([&]() -> Value { auto fn11395 = s->Global("_R127_PARENT"); Arguments args11396; args11396.positional.reserve(2); args11396.Add(s->LocalAt(1), false); args11396.Add(s->LocalAt(0), false); return Call(c, fn11395, std::move(args11396)); }());
s->SetAt(4, v11394);
try {
auto v11398 = ([&]() -> Value { auto fn11399 = s->Global("int"); Arguments args11400; args11400.Add(Get(s->LocalAt(1), Value("player")), false); return Call(c, fn11399, std::move(args11400)); }());
s->SetAt(3, v11398);
auto v11401 = ([&]() -> Value { auto fn11402 = s->Global("int"); Arguments args11403; args11403.Add(Get(s->LocalAt(1), Value("step")), false); return Call(c, fn11402, std::move(args11403)); }());
s->SetAt(7, v11401);
auto v11404 = ([&]() -> Value { auto fn11405 = PrepareDictionaryGet(s->Global("_R127_STATES")); Arguments args11406; args11406.Add(s->LocalAt(3), false); return CallDictionaryGet(c, fn11405, std::move(args11406)); }());
s->SetAt(6, v11404);
if (static_cast<bool>(([&]() -> Value { auto v11407 = ([&]() -> Value { auto v11408 = s->LocalAt(6); Value v11409; v11409 = Value{}; if (!static_cast<bool>(Binary("Is", v11408, v11409))) return Value(false); v11408 = v11409; return Value(true); }()); if (static_cast<bool>(v11407)) return v11407; v11407 = ([&]() -> Value { auto v11410 = s->LocalAt(7); Value v11411; v11411 = Get(s->LocalAt(6), Value("step")); if (!static_cast<bool>(Binary("LtE", v11410, v11411))) return Value(false); v11410 = v11411; return Value(true); }()); return v11407; }()))) {
auto v11412 = ([&]() -> Value { auto dict11413 = Dict(); auto key11414 = Value("step"); Put(dict11413, key11414, Unary("USub", Value(int64_t{1}))); return dict11413; }());
s->SetAt(6, v11412);
Put(s->Global("_R127_STATES"), s->LocalAt(3), v11412);
(void)([&]() -> Value { auto fn11415 = Attribute(s->Global("_R127_REPORT"), "update"); Arguments args11416; args11416.Keyword("last_hour_plants_dropped", Value(int64_t{0})); args11416.Keyword("priority_grain_orders", Value(int64_t{0})); args11416.Keyword("priority_grain_units", Value(int64_t{0})); args11416.Keyword("priority_grain_confirmed", Value(int64_t{0})); args11416.Keyword("priority_grain_shortfalls", Value(int64_t{0})); args11416.Keyword("priority_contract_errors", Value(int64_t{0})); return Call(c, fn11415, std::move(args11416)); }());
}
auto v11417 = ([&]() -> Value { auto fn11418 = Attribute(s->LocalAt(6), "pop"); Arguments args11419; args11419.positional.reserve(2); args11419.Add(Value("pending_grain"), false); args11419.Add(Value{}, false); return Call(c, fn11418, std::move(args11419)); }());
s->SetAt(2, v11417);
if (static_cast<bool>(([&]() -> Value { auto v11420 = s->LocalAt(2); if (!static_cast<bool>(v11420)) return v11420; v11420 = ([&]() -> Value { auto v11421 = s->LocalAt(7); Value v11422; v11422 = Get(s->LocalAt(2), Value(int64_t{0})); if (!static_cast<bool>(Binary("Eq", v11421, v11422))) return Value(false); v11421 = v11422; return Value(true); }()); return v11420; }()))) {
if (static_cast<bool>(([&]() -> Value { auto v11423 = ([&]() -> Value { auto fn11425 = PrepareDictionaryGet(Get(Get(s->LocalAt(1), Value("private")), Value("shed"))); Arguments args11426; args11426.positional.reserve(2); args11426.Add(Value("WHEAT"), false); args11426.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn11425, std::move(args11426)); }()); Value v11424; v11424 = Get(s->LocalAt(2), Value(int64_t{1})); if (!static_cast<bool>(Binary("GtE", v11423, v11424))) return Value(false); v11423 = v11424; return Value(true); }()))) {
auto v11427 = s->Global("_R127_REPORT");
auto v11428 = Value("priority_grain_confirmed");
auto v11429 = Get(v11427, v11428);
Put(v11427, v11428, Inplace("Add", v11429, Get(s->LocalAt(2), Value(int64_t{2}))));
}
else {
auto v11430 = s->Global("_R127_REPORT");
auto v11431 = Value("priority_grain_shortfalls");
auto v11432 = Get(v11430, v11431);
Put(v11430, v11431, Inplace("Add", v11432, Value(int64_t{1})));
}
}
auto v11433 = s->LocalAt(7);
Put(s->LocalAt(6), Value("step"), v11433);
auto v11434 = ([&]() -> Value { auto v11435 = ([&]() -> Value { auto v11436 = s->LocalAt(0); Value v11437; v11437 = Value{}; if (!static_cast<bool>(Binary("Is", v11436, v11437))) return Value(false); v11436 = v11437; return Value(true); }()); if (static_cast<bool>(v11435)) return v11435; v11435 = ([&]() -> Value { auto comp11438 = std::make_shared<Scope>(); comp11438->globals = s->globals; comp11438->parent = s; static constexpr const char* comp11438_names[] = {"k", "v"}; comp11438->PrepareSlots(comp11438_names); auto result11439 = List(); for (const auto& item11440 : Iterate(List({Tuple({Value("boardSize"), Value(int64_t{10})}), Tuple({Value("turnsPerDay"), Value(int64_t{24})}), Tuple({Value("shedCapacity"), Value(int64_t{100})}), Tuple({Value("maxMarketOrdersPerTurn"), Value(int64_t{10})}), Tuple({Value("farmHandCostMult"), Value(int64_t{1})})}))) { auto unpack11441 = Iterate(item11440); ValidateUnpack(unpack11441, 2, false); comp11438->SetAt(0, unpack11441.at(0)); comp11438->SetAt(1, unpack11441.at(1)); if (!static_cast<bool>(([&]() -> Value { auto v11442 = ([&]() -> Value { auto fn11444 = PrepareDictionaryGet(comp11438->Captured("configuration")); Arguments args11445; args11445.positional.reserve(2); args11445.Add(comp11438->LocalAt(0), false); args11445.Add(comp11438->LocalAt(1), false); return CallDictionaryGet(c, fn11444, std::move(args11445)); }()); Value v11443; v11443 = comp11438->LocalAt(1); if (!static_cast<bool>(Binary("Eq", v11442, v11443))) return Value(false); v11442 = v11443; return Value(true); }()))) return Value(false); } return Value(true); }()); return v11435; }());
s->SetAt(5, v11434);
if (static_cast<bool>(s->LocalAt(5))) {
auto v11446 = ([&]() -> Value { auto fn11447 = s->Global("_r127_priority"); Arguments args11448; args11448.positional.reserve(3); args11448.Add(s->LocalAt(1), false); args11448.Add(([&]() -> Value { auto fn11449 = s->Global("_r127_last_hour"); Arguments args11450; args11450.positional.reserve(2); args11450.Add(s->LocalAt(1), false); args11450.Add(s->LocalAt(4), false); return Call(c, fn11449, std::move(args11450)); }()), false); args11448.Add(s->LocalAt(6), false); return Call(c, fn11447, std::move(args11448)); }());
s->SetAt(4, v11446);
}
} catch (const Error& error11397) {
if (Matches(error11397, s->Global("Exception"))) {
auto v11451 = ([&]() -> Value { auto v11452 = ([&]() -> Value { auto fn11453 = PrepareDictionaryGet(s->Global("_R127_REPORT")); Arguments args11454; args11454.positional.reserve(2); args11454.Add(Value("priority_contract_errors"), false); args11454.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn11453, std::move(args11454)); }()); return Binary("Add", v11452, Value(int64_t{1})); }());
Put(s->Global("_R127_REPORT"), Value("priority_contract_errors"), v11451);
}
else { throw; }
}
(void)([&]() -> Value { auto fn11455 = Attribute(s->Global("_R127_REPORT"), "update"); Arguments args11456; args11456.Add(([&]() -> Value { auto fn11457 = s->Global("getattr"); Arguments args11458; args11458.positional.reserve(3); args11458.Add(s->Global("_R127_PARENT"), false); args11458.Add(Value("telemetry"), false); args11458.Add(([&]() -> Value { auto dict11459 = Dict(); return dict11459; }()), false); return Call(c, fn11457, std::move(args11458)); }()), false); return Call(c, fn11455, std::move(args11456)); }());
return s->LocalAt(4);
return {};
}
}  // namespace kagg::opponents::compiled
