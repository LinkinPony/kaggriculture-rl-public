// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_b465ca58eb6c1e8c9fde(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "actor", "c", "commands", "farm", "held", "i", "o", "obs", "orders", "private", "quantity", "removed", "reserve", "result", "retained", "step"};
s->PrepareSlots(s_names);
auto v10022 = ([&]() -> Value { auto fn10023 = s->Global("int"); Arguments args10024; args10024.Add(Get(s->LocalAt(8), Value("step")), false); return Call(c, fn10023, std::move(args10024)); }());
s->SetAt(16, v10022);
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto v10025 = Value(int64_t{10}); Value v10026; v10026 = ([&]() -> Value { auto v10027 = s->LocalAt(16); return Binary("FloorDiv", v10027, Value(int64_t{24})); }()); if (!static_cast<bool>(Binary("LtE", v10025, v10026))) return Value(false); v10025 = v10026; v10026 = Value(int64_t{11}); if (!static_cast<bool>(Binary("LtE", v10025, v10026))) return Value(false); v10025 = v10026; return Value(true); }())))) {
return s->LocalAt(0);
}
auto v10028 = ([&]() -> Value { auto v10029 = ([&]() -> Value { auto fn10030 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args10031; args10031.Add(Value("market"), false); return CallDictionaryGet(c, fn10030, std::move(args10031)); }()); if (static_cast<bool>(v10029)) return v10029; v10029 = List({}); return v10029; }());
s->SetAt(9, v10028);
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto comp10032 = std::make_shared<Scope>(); comp10032->globals = s->globals; comp10032->parent = s; static constexpr const char* comp10032_names[] = {"o"}; comp10032->PrepareSlots(comp10032_names); auto result10033 = List(); for (const auto& item10034 : Iterate(s->LocalAt(9))) { comp10032->SetAt(0, item10034); if (static_cast<bool>(([&]() -> Value { auto v10035 = ([&]() -> Value { auto v10036 = ([&]() -> Value { auto fn10038 = comp10032->Global("len"); Arguments args10039; args10039.Add(comp10032->LocalAt(0), false); return Call(c, fn10038, std::move(args10039)); }()); Value v10037; v10037 = Value(int64_t{2}); if (!static_cast<bool>(Binary("Gt", v10036, v10037))) return Value(false); v10036 = v10037; return Value(true); }()); if (!static_cast<bool>(v10035)) return v10035; v10035 = ([&]() -> Value { auto v10040 = Slice(comp10032->LocalAt(0), Value{}, Value(int64_t{2}), Value{}); Value v10041; v10041 = List({Value("BUY_PRODUCT"), Value("WHEAT")}); if (!static_cast<bool>(Binary("Eq", v10040, v10041))) return Value(false); v10040 = v10041; return Value(true); }()); if (!static_cast<bool>(v10035)) return v10035; v10035 = ([&]() -> Value { auto v10042 = ([&]() -> Value { auto fn10044 = comp10032->Global("int"); Arguments args10045; args10045.Add(Get(comp10032->LocalAt(0), Value(int64_t{2})), false); return Call(c, fn10044, std::move(args10045)); }()); Value v10043; v10043 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v10042, v10043))) return Value(false); v10042 = v10043; return Value(true); }()); return v10035; }()))) return Value(true); } return Value(false); }())))) {
return s->LocalAt(0);
}
if (static_cast<bool>(([&]() -> Value { auto comp10046 = std::make_shared<Scope>(); comp10046->globals = s->globals; comp10046->parent = s; static constexpr const char* comp10046_names[] = {"o"}; comp10046->PrepareSlots(comp10046_names); auto result10047 = List(); for (const auto& item10048 : Iterate(s->LocalAt(9))) { comp10046->SetAt(0, item10048); if (static_cast<bool>(([&]() -> Value { auto v10049 = Slice(comp10046->LocalAt(0), Value{}, Value(int64_t{2}), Value{}); Value v10050; v10050 = List({Value("SELL"), Value("WHEAT")}); if (!static_cast<bool>(Binary("Eq", v10049, v10050))) return Value(false); v10049 = v10050; return Value(true); }()))) return Value(true); } return Value(false); }()))) {
return s->LocalAt(0);
}
auto v10051 = ([&]() -> Value { auto fn10052 = Get(s->Global("_PLANNER_NS"), Value("_clone_state")); Arguments args10053; args10053.positional.reserve(2); args10053.Add(Get(Get(s->LocalAt(8), Value("farms")), Get(s->LocalAt(8), Value("player"))), false); args10053.Add(Get(s->LocalAt(8), Value("private")), false); return Call(c, fn10052, std::move(args10053)); }());
auto unpack10054 = Iterate(v10051);
ValidateUnpack(unpack10054, 2, false);
s->SetAt(4, unpack10054.at(0));
s->SetAt(10, unpack10054.at(1));
auto v10055 = ([&]() -> Value { Arguments args10056; args10056.Add(([&]() -> Value { auto v10057 = ([&]() -> Value { auto fn10058 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args10059; args10059.Add(Value("farmer"), false); return CallDictionaryGet(c, fn10058, std::move(args10059)); }()); if (static_cast<bool>(v10057)) return v10057; v10057 = List({Value("PASS")}); return v10057; }()), false); args10056.Add(([&]() -> Value { auto v10060 = ([&]() -> Value { auto fn10061 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args10062; args10062.Add(Value("hands"), false); return CallDictionaryGet(c, fn10061, std::move(args10062)); }()); if (static_cast<bool>(v10060)) return v10060; v10060 = List({}); return v10060; }()), true); return List(std::move(args10056.positional)); }());
s->SetAt(3, v10055);
for (const auto& item10063 : Iterate(([&]() -> Value { auto fn10064 = s->Global("enumerate"); Arguments args10065; args10065.Add(Slice(s->LocalAt(3), Value{}, ([&]() -> Value { auto fn10066 = s->Global("len"); Arguments args10067; args10067.Add(Get(s->LocalAt(10), Value("inventories")), false); return Call(c, fn10066, std::move(args10067)); }()), Value{}), false); return Call(c, fn10064, std::move(args10065)); }()))) {
auto unpack10068 = Iterate(item10063);
ValidateUnpack(unpack10068, 2, false);
s->SetAt(1, unpack10068.at(0));
s->SetAt(2, unpack10068.at(1));
(void)([&]() -> Value { auto fn10069 = Get(s->Global("_PLANNER_NS"), Value("_apply_unit_action")); Arguments args10070; args10070.positional.reserve(8); args10070.Add(s->LocalAt(4), false); args10070.Add(s->LocalAt(10), false); args10070.Add(s->LocalAt(1), false); args10070.Add(s->LocalAt(2), false); args10070.Add(Value(int64_t{10}), false); args10070.Add(([&]() -> Value { auto v10071 = s->LocalAt(16); return Binary("FloorDiv", v10071, Value(int64_t{24})); }()), false); args10070.Add(Value(int64_t{24}), false); args10070.Add(Value(int64_t{100}), false); return Call(c, fn10069, std::move(args10070)); }());
}
auto v10072 = ([&]() -> Value { auto fn10073 = s->Global("max"); Arguments args10074; args10074.positional.reserve(2); args10074.Add(Value(int64_t{0}), false); args10074.Add(([&]() -> Value { auto fn10075 = s->Global("int"); Arguments args10076; args10076.Add(([&]() -> Value { auto fn10077 = PrepareDictionaryGet(Get(s->LocalAt(10), Value("shed"))); Arguments args10078; args10078.positional.reserve(2); args10078.Add(Value("WHEAT"), false); args10078.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn10077, std::move(args10078)); }()), false); return Call(c, fn10075, std::move(args10076)); }()), false); return Call(c, fn10073, std::move(args10074)); }());
s->SetAt(5, v10072);
auto v10079 = ([&]() -> Value { auto fn10080 = s->Global("_r95_reserve"); Arguments args10081; args10081.Add(s->LocalAt(8), false); return Call(c, fn10080, std::move(args10081)); }());
s->SetAt(13, v10079);
auto v10082 = Value{};
s->SetAt(14, v10082);
auto v10083 = Value(int64_t{0});
s->SetAt(12, v10083);
for (const auto& item10084 : Iterate(([&]() -> Value { auto fn10085 = s->Global("enumerate"); Arguments args10086; args10086.Add(s->LocalAt(9), false); return Call(c, fn10085, std::move(args10086)); }()))) {
auto unpack10087 = Iterate(item10084);
ValidateUnpack(unpack10087, 2, false);
s->SetAt(6, unpack10087.at(0));
s->SetAt(7, unpack10087.at(1));
if (static_cast<bool>(([&]() -> Value { auto v10088 = ([&]() -> Value { auto v10089 = ([&]() -> Value { auto fn10091 = s->Global("len"); Arguments args10092; args10092.Add(s->LocalAt(7), false); return Call(c, fn10091, std::move(args10092)); }()); Value v10090; v10090 = Value(int64_t{3}); if (!static_cast<bool>(Binary("Lt", v10089, v10090))) return Value(false); v10089 = v10090; return Value(true); }()); if (static_cast<bool>(v10088)) return v10088; v10088 = ([&]() -> Value { auto v10093 = Slice(s->LocalAt(7), Value{}, Value(int64_t{2}), Value{}); Value v10094; v10094 = List({Value("BUY_PRODUCT"), Value("WHEAT")}); if (!static_cast<bool>(Binary("NotEq", v10093, v10094))) return Value(false); v10093 = v10094; return Value(true); }()); return v10088; }()))) {
continue;
}
auto v10095 = ([&]() -> Value { auto fn10096 = s->Global("max"); Arguments args10097; args10097.positional.reserve(2); args10097.Add(Value(int64_t{0}), false); args10097.Add(([&]() -> Value { auto fn10098 = s->Global("int"); Arguments args10099; args10099.Add(Get(s->LocalAt(7), Value(int64_t{2})), false); return Call(c, fn10098, std::move(args10099)); }()), false); return Call(c, fn10096, std::move(args10097)); }());
s->SetAt(11, v10095);
auto v10100 = ([&]() -> Value { auto fn10101 = s->Global("min"); Arguments args10102; args10102.positional.reserve(2); args10102.Add(s->LocalAt(11), false); args10102.Add(([&]() -> Value { auto fn10103 = s->Global("max"); Arguments args10104; args10104.positional.reserve(2); args10104.Add(Value(int64_t{0}), false); args10104.Add(([&]() -> Value { auto v10105 = s->LocalAt(13); return Binary("Sub", v10105, s->LocalAt(5)); }()), false); return Call(c, fn10103, std::move(args10104)); }()), false); return Call(c, fn10101, std::move(args10102)); }());
s->SetAt(15, v10100);
auto v10106 = s->LocalAt(5);
s->SetAt(5, Inplace("Add", v10106, s->LocalAt(15)));
if (static_cast<bool>(([&]() -> Value { auto v10107 = s->LocalAt(15); Value v10108; v10108 = s->LocalAt(11); if (!static_cast<bool>(Binary("Lt", v10107, v10108))) return Value(false); v10107 = v10108; return Value(true); }()))) {
if (static_cast<bool>(([&]() -> Value { auto v10109 = s->LocalAt(14); Value v10110; v10110 = Value{}; if (!static_cast<bool>(Binary("Is", v10109, v10110))) return Value(false); v10109 = v10110; return Value(true); }()))) {
auto v10111 = ([&]() -> Value { auto fn10112 = Attribute(s->Global("copy"), "deepcopy"); Arguments args10113; args10113.Add(s->LocalAt(0), false); return Call(c, fn10112, std::move(args10113)); }());
s->SetAt(14, v10111);
}
auto v10114 = s->LocalAt(15);
Put(Get(Get(s->LocalAt(14), Value("market")), s->LocalAt(6)), Value(int64_t{2}), v10114);
auto v10115 = s->LocalAt(12);
s->SetAt(12, Inplace("Add", v10115, ([&]() -> Value { auto v10116 = s->LocalAt(11); return Binary("Sub", v10116, s->LocalAt(15)); }())));
}
}
if (static_cast<bool>(([&]() -> Value { auto v10117 = s->LocalAt(14); Value v10118; v10118 = Value{}; if (!static_cast<bool>(Binary("Is", v10117, v10118))) return Value(false); v10117 = v10118; return Value(true); }()))) {
return s->LocalAt(0);
}
auto v10119 = s->Global("_R95_REPORT");
auto v10120 = Value("replenishment_trim_turns");
auto v10121 = Get(v10119, v10120);
Put(v10119, v10120, Inplace("Add", v10121, Value(int64_t{1})));
auto v10122 = s->Global("_R95_REPORT");
auto v10123 = Value("replenishment_trim_units");
auto v10124 = Get(v10122, v10123);
Put(v10122, v10123, Inplace("Add", v10124, s->LocalAt(12)));
return s->LocalAt(14);
return {};
}
}  // namespace kagg::opponents::compiled
