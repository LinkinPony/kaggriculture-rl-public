// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_cec5c2d23ac38a766712(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "actor", "blocked", "c", "commands", "demand", "farm", "obs", "private"};
s->PrepareSlots(s_names);
auto v11056 = ([&]() -> Value { auto fn11057 = Get(s->Global("_PLANNER_NS"), Value("_clone_state")); Arguments args11058; args11058.positional.reserve(2); args11058.Add(Get(Get(s->LocalAt(7), Value("farms")), Get(s->LocalAt(7), Value("player"))), false); args11058.Add(Get(s->LocalAt(7), Value("private")), false); return Call(c, fn11057, std::move(args11058)); }());
auto unpack11059 = Iterate(v11056);
ValidateUnpack(unpack11059, 2, false);
s->SetAt(6, unpack11059.at(0));
s->SetAt(8, unpack11059.at(1));
auto v11060 = ([&]() -> Value { Arguments args11061; args11061.Add(([&]() -> Value { auto v11062 = ([&]() -> Value { auto fn11063 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args11064; args11064.Add(Value("farmer"), false); return CallDictionaryGet(c, fn11063, std::move(args11064)); }()); if (static_cast<bool>(v11062)) return v11062; v11062 = List({Value("PASS")}); return v11062; }()), false); args11061.Add(([&]() -> Value { auto v11065 = ([&]() -> Value { auto fn11066 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args11067; args11067.Add(Value("hands"), false); return CallDictionaryGet(c, fn11066, std::move(args11067)); }()); if (static_cast<bool>(v11065)) return v11065; v11065 = List({}); return v11065; }()), true); return List(std::move(args11061.positional)); }());
s->SetAt(4, v11060);
auto v11068 = ([&]() -> Value { auto dict11069 = Dict(); return dict11069; }());
s->SetAt(5, v11068);
for (const auto& item11070 : Iterate(s->LocalAt(4))) {
s->SetAt(3, item11070);
if (static_cast<bool>(([&]() -> Value { auto v11071 = ([&]() -> Value { auto v11072 = ([&]() -> Value { auto fn11074 = s->Global("len"); Arguments args11075; args11075.Add(s->LocalAt(3), false); return Call(c, fn11074, std::move(args11075)); }()); Value v11073; v11073 = Value(int64_t{1}); if (!static_cast<bool>(Binary("Gt", v11072, v11073))) return Value(false); v11072 = v11073; return Value(true); }()); if (!static_cast<bool>(v11071)) return v11071; v11071 = ([&]() -> Value { auto v11076 = Get(s->LocalAt(3), Value(int64_t{0})); Value v11077; v11077 = Value("PLANT"); if (!static_cast<bool>(Binary("Eq", v11076, v11077))) return Value(false); v11076 = v11077; return Value(true); }()); return v11071; }()))) {
auto v11078 = ([&]() -> Value { auto v11079 = ([&]() -> Value { auto fn11080 = PrepareDictionaryGet(s->LocalAt(5)); Arguments args11081; args11081.positional.reserve(2); args11081.Add(Get(s->LocalAt(3), Value(int64_t{1})), false); args11081.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn11080, std::move(args11081)); }()); return Binary("Add", v11079, Value(int64_t{1})); }());
Put(s->LocalAt(5), Get(s->LocalAt(3), Value(int64_t{1})), v11078);
}
}
auto v11082 = ([&]() -> Value { auto comp11083 = std::make_shared<Scope>(); comp11083->globals = s->globals; comp11083->parent = s; static constexpr const char* comp11083_names[] = {"n", "p"}; comp11083->PrepareSlots(comp11083_names); auto result11084 = List(); for (const auto& item11085 : Iterate(([&]() -> Value { auto fn11086 = Attribute(s->LocalAt(5), "items"); Arguments args11087; return Call(c, fn11086, std::move(args11087)); }()))) { auto unpack11088 = Iterate(item11085); ValidateUnpack(unpack11088, 2, false); comp11083->SetAt(1, unpack11088.at(0)); comp11083->SetAt(0, unpack11088.at(1)); if (!static_cast<bool>(([&]() -> Value { auto v11089 = comp11083->LocalAt(0); Value v11090; v11090 = ([&]() -> Value { auto fn11091 = PrepareDictionaryGet(Get(comp11083->Captured("private"), Value("seeds"))); Arguments args11092; args11092.positional.reserve(2); args11092.Add(comp11083->LocalAt(1), false); args11092.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn11091, std::move(args11092)); }()); if (!static_cast<bool>(Binary("Gt", v11089, v11090))) return Value(false); v11089 = v11090; return Value(true); }()))) continue; result11084.node()->sequence.push_back(comp11083->LocalAt(1)); } return Set(result11084.node()->sequence); }());
s->SetAt(2, v11082);
for (const auto& item11093 : Iterate(([&]() -> Value { auto fn11094 = s->Global("enumerate"); Arguments args11095; args11095.Add(Slice(s->LocalAt(4), Value{}, ([&]() -> Value { auto fn11096 = s->Global("len"); Arguments args11097; args11097.Add(Get(s->LocalAt(8), Value("inventories")), false); return Call(c, fn11096, std::move(args11097)); }()), Value{}), false); return Call(c, fn11094, std::move(args11095)); }()))) {
auto unpack11098 = Iterate(item11093);
ValidateUnpack(unpack11098, 2, false);
s->SetAt(1, unpack11098.at(0));
s->SetAt(3, unpack11098.at(1));
if (static_cast<bool>(([&]() -> Value { auto v11099 = ([&]() -> Value { auto v11100 = ([&]() -> Value { auto fn11102 = s->Global("len"); Arguments args11103; args11103.Add(s->LocalAt(3), false); return Call(c, fn11102, std::move(args11103)); }()); Value v11101; v11101 = Value(int64_t{1}); if (!static_cast<bool>(Binary("Gt", v11100, v11101))) return Value(false); v11100 = v11101; return Value(true); }()); if (!static_cast<bool>(v11099)) return v11099; v11099 = ([&]() -> Value { auto v11104 = Get(s->LocalAt(3), Value(int64_t{0})); Value v11105; v11105 = Value("PLANT"); if (!static_cast<bool>(Binary("Eq", v11104, v11105))) return Value(false); v11104 = v11105; return Value(true); }()); if (!static_cast<bool>(v11099)) return v11099; v11099 = ([&]() -> Value { auto v11106 = Get(s->LocalAt(3), Value(int64_t{1})); Value v11107; v11107 = s->LocalAt(2); if (!static_cast<bool>(Binary("In", v11106, v11107))) return Value(false); v11106 = v11107; return Value(true); }()); return v11099; }()))) {
continue;
}
(void)([&]() -> Value { auto fn11108 = Get(s->Global("_PLANNER_NS"), Value("_apply_unit_action")); Arguments args11109; args11109.positional.reserve(8); args11109.Add(s->LocalAt(6), false); args11109.Add(s->LocalAt(8), false); args11109.Add(s->LocalAt(1), false); args11109.Add(s->LocalAt(3), false); args11109.Add(Value(int64_t{10}), false); args11109.Add(([&]() -> Value { auto v11110 = ([&]() -> Value { auto fn11111 = s->Global("int"); Arguments args11112; args11112.Add(Get(s->LocalAt(7), Value("step")), false); return Call(c, fn11111, std::move(args11112)); }()); return Binary("FloorDiv", v11110, Value(int64_t{24})); }()), false); args11109.Add(Value(int64_t{24}), false); args11109.Add(Value(int64_t{100}), false); return Call(c, fn11108, std::move(args11109)); }());
}
return Tuple({s->LocalAt(6), s->LocalAt(8)});
return {};
}
}  // namespace kagg::opponents::compiled
