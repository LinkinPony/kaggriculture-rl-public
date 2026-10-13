// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_3095b19fde1234023f0a(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"_", "actor", "command", "current", "delivery", "dist", "farm", "home", "hungry", "inv", "needed", "obs", "path", "pos", "private", "remaining", "ret", "step", "t", "target", "targets", "tasks", "travel", "work", "x", "y"};
s->PrepareSlots(s_names);
if (static_cast<bool>(([&]() -> Value { auto v26952 = ([&]() -> Value { auto fn26954 = s->Global("len"); Arguments args26955; args26955.Add(s->LocalAt(20), false); return Call(c, fn26954, std::move(args26955)); }()); Value v26953; v26953 = Value(int64_t{6}); if (!static_cast<bool>(Binary("NotEq", v26952, v26953))) return Value(false); v26952 = v26953; return Value(true); }()))) {
return ([&]() -> Value { auto fn26956 = s->Global("_SL_WORKER"); Arguments args26957; args26957.positional.reserve(3); args26957.Add(s->LocalAt(11), false); args26957.Add(s->LocalAt(1), false); args26957.Add(s->LocalAt(20), false); return Call(c, fn26956, std::move(args26957)); }());
}
auto v26958 = Get(Get(s->LocalAt(11), Value("farms")), Get(s->LocalAt(11), Value("player")));
s->SetAt(6, v26958);
auto v26959 = Get(s->LocalAt(11), Value("private"));
s->SetAt(14, v26959);
auto v26960 = ([&]() -> Value { auto fn26961 = s->Global("int"); Arguments args26962; args26962.Add(Get(s->LocalAt(11), Value("step")), false); return Call(c, fn26961, std::move(args26962)); }());
s->SetAt(17, v26960);
auto v26963 = ([&]() -> Value { auto fn26964 = s->Global("tuple"); Arguments args26965; args26965.Add(Get(Get(s->LocalAt(6), Value("hands")), ([&]() -> Value { auto v26966 = s->LocalAt(1); return Binary("Sub", v26966, Value(int64_t{1})); }())), false); return Call(c, fn26964, std::move(args26965)); }());
s->SetAt(13, v26963);
auto v26967 = Get(Get(s->LocalAt(14), Value("inventories")), s->LocalAt(1));
s->SetAt(9, v26967);
auto v26968 = List({});
s->SetAt(10, v26968);
auto v26969 = Value(int64_t{0});
s->SetAt(8, v26969);
for (const auto& item26970 : Iterate(s->LocalAt(20))) {
s->SetAt(19, item26970);
auto v26971 = s->LocalAt(19);
auto unpack26972 = Iterate(v26971);
ValidateUnpack(unpack26972, 2, false);
s->SetAt(24, unpack26972.at(0));
s->SetAt(25, unpack26972.at(1));
auto v26973 = Get(Get(Get(s->LocalAt(6), Value("tiles")), s->LocalAt(25)), s->LocalAt(24));
s->SetAt(18, v26973);
if (static_cast<bool>(([&]() -> Value { auto v26974 = Unary("Not", ([&]() -> Value { auto fn26975 = s->Global("isinstance"); Arguments args26976; args26976.positional.reserve(2); args26976.Add(s->LocalAt(18), false); args26976.Add(s->Global("dict"), false); return Call(c, fn26975, std::move(args26976)); }())); if (static_cast<bool>(v26974)) return v26974; v26974 = ([&]() -> Value { auto v26977 = ([&]() -> Value { auto fn26979 = PrepareDictionaryGet(s->LocalAt(18)); Arguments args26980; args26980.Add(Value("animal"), false); return CallDictionaryGet(c, fn26979, std::move(args26980)); }()); Value v26978; v26978 = Value("SHEEP"); if (!static_cast<bool>(Binary("NotEq", v26977, v26978))) return Value(false); v26977 = v26978; return Value(true); }()); return v26974; }()))) {
return ([&]() -> Value { auto fn26981 = s->Global("_SL_WORKER"); Arguments args26982; args26982.positional.reserve(3); args26982.Add(s->LocalAt(11), false); args26982.Add(s->LocalAt(1), false); args26982.Add(s->LocalAt(20), false); return Call(c, fn26981, std::move(args26982)); }());
}
if (static_cast<bool>(Unary("Not", Get(s->LocalAt(18), Value("fed_today"))))) {
auto v26983 = s->LocalAt(8);
s->SetAt(8, Inplace("Add", v26983, Value(int64_t{1})));
}
if (static_cast<bool>(([&]() -> Value { auto v26984 = Unary("Not", Get(s->LocalAt(18), Value("fed_today"))); if (static_cast<bool>(v26984)) return v26984; v26984 = Unary("Not", Get(s->LocalAt(18), Value("cared_today"))); return v26984; }()))) {
(void)([&]() -> Value { auto fn26985 = Attribute(s->LocalAt(10), "append"); Arguments args26986; args26986.Add(s->LocalAt(19), false); return Call(c, fn26985, std::move(args26986)); }());
}
}
auto v26987 = ([&]() -> Value { auto fn26988 = s->Global("_v219_home"); Arguments args26989; args26989.Add(s->LocalAt(13), false); return Call(c, fn26988, std::move(args26989)); }());
s->SetAt(7, v26987);
if (static_cast<bool>(([&]() -> Value { auto v26990 = s->LocalAt(8); Value v26991; v26991 = ([&]() -> Value { auto fn26992 = PrepareDictionaryGet(s->LocalAt(9)); Arguments args26993; args26993.positional.reserve(2); args26993.Add(Value("WHEAT"), false); args26993.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn26992, std::move(args26993)); }()); if (!static_cast<bool>(Binary("Gt", v26990, v26991))) return Value(false); v26990 = v26991; return Value(true); }()))) {
return ([&]() -> Value { auto v26994 = ([&]() -> Value { auto fn26995 = s->Global("_v219_walk"); Arguments args26996; args26996.positional.reserve(2); args26996.Add(s->LocalAt(13), false); args26996.Add(s->LocalAt(7), false); return Call(c, fn26995, std::move(args26996)); }()); if (static_cast<bool>(v26994)) return v26994; v26994 = List({Value("PICKUP"), Value("WHEAT"), ([&]() -> Value { auto fn26997 = s->Global("min"); Arguments args26998; args26998.positional.reserve(2); args26998.Add(s->LocalAt(8), false); args26998.Add(([&]() -> Value { auto fn26999 = PrepareDictionaryGet(Get(s->LocalAt(14), Value("shed"))); Arguments args27000; args27000.positional.reserve(2); args27000.Add(Value("WHEAT"), false); args27000.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn26999, std::move(args27000)); }()), false); return Call(c, fn26997, std::move(args26998)); }())}); return v26994; }());
}
if (static_cast<bool>(s->LocalAt(10))) {
auto v27001 = ([&]() -> Value { auto fn27002 = s->Global("_sl_path"); Arguments args27003; args27003.positional.reserve(2); args27003.Add(s->LocalAt(13), false); args27003.Add(s->LocalAt(10), false); return Call(c, fn27002, std::move(args27003)); }());
s->SetAt(12, v27001);
auto v27004 = Get(Get(Get(s->LocalAt(6), Value("tiles")), Get(s->LocalAt(13), Value(int64_t{1}))), Get(s->LocalAt(13), Value(int64_t{0})));
s->SetAt(3, v27004);
if (static_cast<bool>(([&]() -> Value { auto v27005 = ([&]() -> Value { auto v27006 = s->LocalAt(13); Value v27007; v27007 = s->LocalAt(20); if (!static_cast<bool>(Binary("In", v27006, v27007))) return Value(false); v27006 = v27007; return Value(true); }()); if (!static_cast<bool>(v27005)) return v27005; v27005 = ([&]() -> Value { auto fn27008 = s->Global("isinstance"); Arguments args27009; args27009.positional.reserve(2); args27009.Add(s->LocalAt(3), false); args27009.Add(s->Global("dict"), false); return Call(c, fn27008, std::move(args27009)); }()); if (!static_cast<bool>(v27005)) return v27005; v27005 = ([&]() -> Value { auto fn27010 = PrepareDictionaryGet(s->LocalAt(3)); Arguments args27011; args27011.Add(Value("fed_today"), false); return CallDictionaryGet(c, fn27010, std::move(args27011)); }()); if (!static_cast<bool>(v27005)) return v27005; v27005 = ([&]() -> Value { auto fn27012 = PrepareDictionaryGet(s->LocalAt(3)); Arguments args27013; args27013.Add(Value("cared_today"), false); return CallDictionaryGet(c, fn27012, std::move(args27013)); }()); if (!static_cast<bool>(v27005)) return v27005; v27005 = ([&]() -> Value { auto fn27014 = PrepareDictionaryGet(s->LocalAt(3)); Arguments args27015; args27015.Add(Value("fertilizer_available"), false); return CallDictionaryGet(c, fn27014, std::move(args27015)); }()); return v27005; }()))) {
auto v27016 = ([&]() -> Value { auto v27017 = ([&]() -> Value { auto fn27018 = s->Global("_sl_dist"); Arguments args27019; args27019.positional.reserve(2); args27019.Add(s->LocalAt(13), false); args27019.Add(Get(s->LocalAt(12), Value(int64_t{0})), false); return Call(c, fn27018, std::move(args27019)); }()); return Binary("Add", v27017, ([&]() -> Value { auto fn27020 = s->Global("sum"); Arguments args27021; args27021.Add(([&]() -> Value { auto comp27022 = std::make_shared<Scope>(); comp27022->globals = s->globals; comp27022->parent = s; static constexpr const char* comp27022_names[] = {"a", "b"}; comp27022->PrepareSlots(comp27022_names); auto result27023 = List(); for (const auto& item27024 : Iterate(([&]() -> Value { auto fn27025 = s->Global("zip"); Arguments args27026; args27026.positional.reserve(2); args27026.Add(s->LocalAt(12), false); args27026.Add(Slice(s->LocalAt(12), Value(int64_t{1}), Value{}, Value{}), false); return Call(c, fn27025, std::move(args27026)); }()))) { auto unpack27027 = Iterate(item27024); ValidateUnpack(unpack27027, 2, false); comp27022->SetAt(0, unpack27027.at(0)); comp27022->SetAt(1, unpack27027.at(1)); result27023.node()->sequence.push_back(([&]() -> Value { auto fn27028 = comp27022->Global("_sl_dist"); Arguments args27029; args27029.positional.reserve(2); args27029.Add(comp27022->LocalAt(0), false); args27029.Add(comp27022->LocalAt(1), false); return Call(c, fn27028, std::move(args27029)); }())); } return result27023; }()), false); return Call(c, fn27020, std::move(args27021)); }())); }());
s->SetAt(22, v27016);
auto v27030 = ([&]() -> Value { auto v27031 = ([&]() -> Value { auto fn27032 = s->Global("sum"); Arguments args27033; args27033.Add(([&]() -> Value { auto comp27034 = std::make_shared<Scope>(); comp27034->globals = s->globals; comp27034->parent = s; static constexpr const char* comp27034_names[] = {"x", "y"}; comp27034->PrepareSlots(comp27034_names); auto result27035 = List(); for (const auto& item27036 : Iterate(s->LocalAt(12))) { auto unpack27037 = Iterate(item27036); ValidateUnpack(unpack27037, 2, false); comp27034->SetAt(0, unpack27037.at(0)); comp27034->SetAt(1, unpack27037.at(1)); result27035.node()->sequence.push_back(Unary("Not", Get(Get(Get(Get(comp27034->Captured("farm"), Value("tiles")), comp27034->LocalAt(1)), comp27034->LocalAt(0)), Value("fed_today")))); } return result27035; }()), false); return Call(c, fn27032, std::move(args27033)); }()); return Binary("Add", v27031, ([&]() -> Value { auto fn27038 = s->Global("sum"); Arguments args27039; args27039.Add(([&]() -> Value { auto comp27040 = std::make_shared<Scope>(); comp27040->globals = s->globals; comp27040->parent = s; static constexpr const char* comp27040_names[] = {"x", "y"}; comp27040->PrepareSlots(comp27040_names); auto result27041 = List(); for (const auto& item27042 : Iterate(s->LocalAt(12))) { auto unpack27043 = Iterate(item27042); ValidateUnpack(unpack27043, 2, false); comp27040->SetAt(0, unpack27043.at(0)); comp27040->SetAt(1, unpack27043.at(1)); result27041.node()->sequence.push_back(Unary("Not", Get(Get(Get(Get(comp27040->Captured("farm"), Value("tiles")), comp27040->LocalAt(1)), comp27040->LocalAt(0)), Value("cared_today")))); } return result27041; }()), false); return Call(c, fn27038, std::move(args27039)); }())); }());
s->SetAt(23, v27030);
auto v27044 = (static_cast<bool>(([&]() -> Value { auto v27045 = ([&]() -> Value { auto v27047 = s->LocalAt(17); return Binary("FloorDiv", v27047, Value(int64_t{24})); }()); Value v27046; v27046 = Value(int64_t{29}); if (!static_cast<bool>(Binary("Eq", v27045, v27046))) return Value(false); v27045 = v27046; return Value(true); }())) ? ([&]() -> Value { auto v27048 = ([&]() -> Value { auto fn27049 = s->Global("_sl_dist"); Arguments args27050; args27050.positional.reserve(2); args27050.Add(Get(s->LocalAt(12), Unary("USub", Value(int64_t{1}))), false); args27050.Add(([&]() -> Value { auto fn27051 = s->Global("_v219_home"); Arguments args27052; args27052.Add(Get(s->LocalAt(12), Unary("USub", Value(int64_t{1}))), false); return Call(c, fn27051, std::move(args27052)); }()), false); return Call(c, fn27049, std::move(args27050)); }()); return Binary("Add", v27048, Value(int64_t{1})); }()) : Value(int64_t{0}));
s->SetAt(4, v27044);
auto v27053 = ([&]() -> Value { auto v27054 = ([&]() -> Value { auto fn27055 = s->Global("min"); Arguments args27056; args27056.positional.reserve(2); args27056.Add(([&]() -> Value { auto v27057 = ([&]() -> Value { auto v27058 = ([&]() -> Value { auto v27059 = s->LocalAt(17); return Binary("FloorDiv", v27059, Value(int64_t{24})); }()); return Binary("Add", v27058, Value(int64_t{1})); }()); return Binary("Mult", v27057, Value(int64_t{24})); }()), false); args27056.Add(Value(int64_t{719}), false); return Call(c, fn27055, std::move(args27056)); }()); return Binary("Sub", v27054, s->LocalAt(17)); }());
s->SetAt(15, v27053);
if (static_cast<bool>(([&]() -> Value { auto v27060 = ([&]() -> Value { auto v27062 = ([&]() -> Value { auto v27063 = ([&]() -> Value { auto v27064 = Value(int64_t{1}); return Binary("Add", v27064, s->LocalAt(22)); }()); return Binary("Add", v27063, s->LocalAt(23)); }()); return Binary("Add", v27062, s->LocalAt(4)); }()); Value v27061; v27061 = s->LocalAt(15); if (!static_cast<bool>(Binary("LtE", v27060, v27061))) return Value(false); v27060 = v27061; return Value(true); }()))) {
auto v27065 = s->Global("_SL_REPORT");
auto v27066 = Value("collect");
auto v27067 = Get(v27065, v27066);
Put(v27065, v27066, Inplace("Add", v27067, Value(int64_t{1})));
return List({Value("COLLECT_FERTILIZER")});
}
}
auto v27068 = Get(s->LocalAt(12), Value(int64_t{0}));
s->SetAt(19, v27068);
auto v27069 = Get(Get(Get(s->LocalAt(6), Value("tiles")), Get(s->LocalAt(19), Value(int64_t{1}))), Get(s->LocalAt(19), Value(int64_t{0})));
s->SetAt(18, v27069);
return ([&]() -> Value { auto v27070 = ([&]() -> Value { auto fn27071 = s->Global("_v219_walk"); Arguments args27072; args27072.positional.reserve(2); args27072.Add(s->LocalAt(13), false); args27072.Add(s->LocalAt(19), false); return Call(c, fn27071, std::move(args27072)); }()); if (static_cast<bool>(v27070)) return v27070; v27070 = (static_cast<bool>(Unary("Not", Get(s->LocalAt(18), Value("fed_today")))) ? List({Value("FEED")}) : List({Value("CARE")})); return v27070; }());
}
auto v27073 = (static_cast<bool>(([&]() -> Value { auto v27074 = ([&]() -> Value { auto v27076 = s->LocalAt(17); return Binary("FloorDiv", v27076, Value(int64_t{24})); }()); Value v27075; v27075 = Value(int64_t{29}); if (!static_cast<bool>(Binary("Eq", v27074, v27075))) return Value(false); v27074 = v27075; return Value(true); }())) ? ([&]() -> Value { auto v27077 = Value(int64_t{719}); return Binary("Sub", v27077, s->LocalAt(17)); }()) : ([&]() -> Value { auto v27078 = Value(int64_t{24}); return Binary("Sub", v27078, ([&]() -> Value { auto v27079 = s->LocalAt(17); return Binary("Mod", v27079, Value(int64_t{24})); }())); }()));
s->SetAt(15, v27073);
auto v27080 = List({});
s->SetAt(21, v27080);
for (const auto& item27081 : Iterate(s->LocalAt(20))) {
s->SetAt(19, item27081);
auto v27082 = Get(Get(Get(s->LocalAt(6), Value("tiles")), Get(s->LocalAt(19), Value(int64_t{1}))), Get(s->LocalAt(19), Value(int64_t{0})));
s->SetAt(18, v27082);
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto fn27083 = PrepareDictionaryGet(s->LocalAt(18)); Arguments args27084; args27084.Add(Value("fertilizer_available"), false); return CallDictionaryGet(c, fn27083, std::move(args27084)); }())))) {
continue;
}
auto v27085 = ([&]() -> Value { auto fn27086 = s->Global("_sl_dist"); Arguments args27087; args27087.positional.reserve(2); args27087.Add(s->LocalAt(13), false); args27087.Add(s->LocalAt(19), false); return Call(c, fn27086, std::move(args27087)); }());
s->SetAt(5, v27085);
auto v27088 = (static_cast<bool>(([&]() -> Value { auto v27089 = ([&]() -> Value { auto v27091 = s->LocalAt(17); return Binary("FloorDiv", v27091, Value(int64_t{24})); }()); Value v27090; v27090 = Value(int64_t{29}); if (!static_cast<bool>(Binary("Eq", v27089, v27090))) return Value(false); v27089 = v27090; return Value(true); }())) ? ([&]() -> Value { auto v27092 = ([&]() -> Value { auto fn27093 = s->Global("_sl_dist"); Arguments args27094; args27094.positional.reserve(2); args27094.Add(s->LocalAt(19), false); args27094.Add(([&]() -> Value { auto fn27095 = s->Global("_v219_home"); Arguments args27096; args27096.Add(s->LocalAt(19), false); return Call(c, fn27095, std::move(args27096)); }()), false); return Call(c, fn27093, std::move(args27094)); }()); return Binary("Add", v27092, Value(int64_t{1})); }()) : Value(int64_t{0}));
s->SetAt(16, v27088);
if (static_cast<bool>(([&]() -> Value { auto v27097 = ([&]() -> Value { auto v27099 = ([&]() -> Value { auto v27100 = s->LocalAt(5); return Binary("Add", v27100, Value(int64_t{1})); }()); return Binary("Add", v27099, s->LocalAt(16)); }()); Value v27098; v27098 = s->LocalAt(15); if (!static_cast<bool>(Binary("LtE", v27097, v27098))) return Value(false); v27097 = v27098; return Value(true); }()))) {
(void)([&]() -> Value { auto fn27101 = Attribute(s->LocalAt(21), "append"); Arguments args27102; args27102.Add(Tuple({s->LocalAt(5), ([&]() -> Value { auto fn27103 = s->Global("tuple"); Arguments args27104; args27104.Add(s->LocalAt(19), false); return Call(c, fn27103, std::move(args27104)); }())}), false); return Call(c, fn27101, std::move(args27102)); }());
}
}
if (static_cast<bool>(s->LocalAt(21))) {
auto v27105 = ([&]() -> Value { auto fn27106 = s->Global("min"); Arguments args27107; args27107.Add(s->LocalAt(21), false); return Call(c, fn27106, std::move(args27107)); }());
auto unpack27108 = Iterate(v27105);
ValidateUnpack(unpack27108, 2, false);
s->SetAt(0, unpack27108.at(0));
s->SetAt(19, unpack27108.at(1));
auto v27109 = ([&]() -> Value { auto v27110 = ([&]() -> Value { auto fn27111 = s->Global("_v219_walk"); Arguments args27112; args27112.positional.reserve(2); args27112.Add(s->LocalAt(13), false); args27112.Add(s->LocalAt(19), false); return Call(c, fn27111, std::move(args27112)); }()); if (static_cast<bool>(v27110)) return v27110; v27110 = List({Value("COLLECT_FERTILIZER")}); return v27110; }());
s->SetAt(2, v27109);
auto v27113 = s->Global("_SL_REPORT");
auto v27114 = Value("collect");
auto v27115 = Get(v27113, v27114);
Put(v27113, v27114, Inplace("Add", v27115, ([&]() -> Value { auto v27116 = s->LocalAt(2); Value v27117; v27117 = List({Value("COLLECT_FERTILIZER")}); if (!static_cast<bool>(Binary("Eq", v27116, v27117))) return Value(false); v27116 = v27117; return Value(true); }())));
return s->LocalAt(2);
}
if (static_cast<bool>(([&]() -> Value { auto fn27118 = PrepareDictionaryGet(s->LocalAt(9)); Arguments args27119; args27119.positional.reserve(2); args27119.Add(Value("FERTILIZER"), false); args27119.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn27118, std::move(args27119)); }()))) {
return ([&]() -> Value { auto v27120 = ([&]() -> Value { auto fn27121 = s->Global("_v219_walk"); Arguments args27122; args27122.positional.reserve(2); args27122.Add(s->LocalAt(13), false); args27122.Add(s->LocalAt(7), false); return Call(c, fn27121, std::move(args27122)); }()); if (static_cast<bool>(v27120)) return v27120; v27120 = List({Value("PLACE"), Value("FERTILIZER"), Get(s->LocalAt(9), Value("FERTILIZER"))}); return v27120; }());
}
return List({Value("PASS")});
return {};
}
}  // namespace kagg::opponents::compiled
