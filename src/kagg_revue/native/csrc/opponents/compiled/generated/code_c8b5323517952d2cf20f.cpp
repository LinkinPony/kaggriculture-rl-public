// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_c8b5323517952d2cf20f(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"_", "access", "actor", "cargo", "command", "distance", "farm", "home", "hungry", "inv", "missing", "obs", "pos", "private", "step", "target", "targets", "tasks", "tile", "x", "y"};
s->PrepareSlots(s_names);
auto v6951 = Get(Get(s->LocalAt(11), Value("farms")), Get(s->LocalAt(11), Value("player")));
s->SetAt(6, v6951);
auto v6952 = Get(s->LocalAt(11), Value("private"));
s->SetAt(13, v6952);
auto v6953 = ([&]() -> Value { auto fn6954 = s->Global("int"); Arguments args6955; args6955.Add(Get(s->LocalAt(11), Value("step")), false); return Call(c, fn6954, std::move(args6955)); }());
s->SetAt(14, v6953);
auto v6956 = ([&]() -> Value { auto fn6957 = s->Global("tuple"); Arguments args6958; args6958.Add(Get(Get(s->LocalAt(6), Value("hands")), ([&]() -> Value { auto v6959 = s->LocalAt(2); return Binary("Sub", v6959, Value(int64_t{1})); }())), false); return Call(c, fn6957, std::move(args6958)); }());
s->SetAt(12, v6956);
auto v6960 = Get(Get(s->LocalAt(13), Value("inventories")), s->LocalAt(2));
s->SetAt(9, v6960);
auto v6961 = Tuple({Tuple({Value(int64_t{4}), Value(int64_t{4})}), Tuple({Value(int64_t{5}), Value(int64_t{4})}), Tuple({Value(int64_t{4}), Value(int64_t{5})}), Tuple({Value(int64_t{5}), Value(int64_t{5})})});
s->SetAt(1, v6961);
auto v6962 = ([&]() -> Value { auto fn6963 = s->Global("min"); Arguments args6964; args6964.Add(s->LocalAt(1), false); args6964.Keyword("key", Define(&Code_a7ab56cf81de33acee35, s, Signature{{"p"}, {}, {}, {}, "", "", ([]() -> std::span<const char* const> { static constexpr const char* names[] = {"p"}; return names; }())}, true, "<lambda>")); return Call(c, fn6963, std::move(args6964)); }());
s->SetAt(7, v6962);
auto v6972 = ([&]() -> Value { auto v6973 = ([&]() -> Value { auto fn6974 = s->Global("abs"); Arguments args6975; args6975.Add(([&]() -> Value { auto v6976 = Get(s->LocalAt(12), Value(int64_t{0})); return Binary("Sub", v6976, Get(s->LocalAt(7), Value(int64_t{0}))); }()), false); return Call(c, fn6974, std::move(args6975)); }()); return Binary("Add", v6973, ([&]() -> Value { auto fn6977 = s->Global("abs"); Arguments args6978; args6978.Add(([&]() -> Value { auto v6979 = Get(s->LocalAt(12), Value(int64_t{1})); return Binary("Sub", v6979, Get(s->LocalAt(7), Value(int64_t{1}))); }()), false); return Call(c, fn6977, std::move(args6978)); }())); }());
s->SetAt(5, v6972);
auto v6980 = ([&]() -> Value { auto comp6981 = std::make_shared<Scope>(); comp6981->globals = s->globals; comp6981->parent = s; static constexpr const char* comp6981_names[] = {"item"}; comp6981->PrepareSlots(comp6981_names); auto result6982 = List(); for (const auto& item6983 : Iterate(Tuple({Value("WOOL"), Value("FERTILIZER")}))) { comp6981->SetAt(0, item6983); if (!static_cast<bool>(([&]() -> Value { auto fn6984 = PrepareDictionaryGet(comp6981->Captured("inv")); Arguments args6985; args6985.positional.reserve(2); args6985.Add(comp6981->LocalAt(0), false); args6985.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn6984, std::move(args6985)); }()))) continue; result6982.node()->sequence.push_back(comp6981->LocalAt(0)); } return result6982; }());
s->SetAt(3, v6980);
if (static_cast<bool>(([&]() -> Value { auto v6986 = s->LocalAt(3); if (!static_cast<bool>(v6986)) return v6986; v6986 = ([&]() -> Value { auto v6987 = ([&]() -> Value { auto v6989 = s->LocalAt(14); return Binary("Mod", v6989, Value(int64_t{24})); }()); Value v6988; v6988 = ([&]() -> Value { auto v6990 = (static_cast<bool>(([&]() -> Value { auto v6991 = ([&]() -> Value { auto v6993 = s->LocalAt(14); return Binary("FloorDiv", v6993, Value(int64_t{24})); }()); Value v6992; v6992 = Value(int64_t{29}); if (!static_cast<bool>(Binary("Eq", v6991, v6992))) return Value(false); v6991 = v6992; return Value(true); }())) ? Value(int64_t{22}) : Value(int64_t{23})); return Binary("Sub", v6990, s->LocalAt(5)); }()); if (!static_cast<bool>(Binary("GtE", v6987, v6988))) return Value(false); v6987 = v6988; return Value(true); }()); return v6986; }()))) {
return ([&]() -> Value { auto v6994 = ([&]() -> Value { auto fn6995 = s->Global("_v219_walk"); Arguments args6996; args6996.positional.reserve(2); args6996.Add(s->LocalAt(12), false); args6996.Add(s->LocalAt(7), false); return Call(c, fn6995, std::move(args6996)); }()); if (static_cast<bool>(v6994)) return v6994; v6994 = List({Value("PLACE"), Get(s->LocalAt(3), Value(int64_t{0})), Get(s->LocalAt(9), Get(s->LocalAt(3), Value(int64_t{0})))}); return v6994; }());
}
auto v6997 = ([&]() -> Value { auto fn6998 = s->Global("sum"); Arguments args6999; args6999.Add(([&]() -> Value { auto comp7000 = std::make_shared<Scope>(); comp7000->globals = s->globals; comp7000->parent = s; static constexpr const char* comp7000_names[] = {"x", "y"}; comp7000->PrepareSlots(comp7000_names); auto result7001 = List(); for (const auto& item7002 : Iterate(s->LocalAt(16))) { auto unpack7003 = Iterate(item7002); ValidateUnpack(unpack7003, 2, false); comp7000->SetAt(0, unpack7003.at(0)); comp7000->SetAt(1, unpack7003.at(1)); result7001.node()->sequence.push_back(Unary("Not", ([&]() -> Value { auto v7004 = ([&]() -> Value { auto fn7005 = comp7000->Global("isinstance"); Arguments args7006; args7006.positional.reserve(2); args7006.Add(Get(Get(Get(comp7000->Captured("farm"), Value("tiles")), comp7000->LocalAt(1)), comp7000->LocalAt(0)), false); args7006.Add(comp7000->Global("dict"), false); return Call(c, fn7005, std::move(args7006)); }()); if (!static_cast<bool>(v7004)) return v7004; v7004 = ([&]() -> Value { auto v7007 = ([&]() -> Value { auto fn7009 = PrepareDictionaryGet(Get(Get(Get(comp7000->Captured("farm"), Value("tiles")), comp7000->LocalAt(1)), comp7000->LocalAt(0))); Arguments args7010; args7010.Add(Value("animal"), false); return CallDictionaryGet(c, fn7009, std::move(args7010)); }()); Value v7008; v7008 = Value("SHEEP"); if (!static_cast<bool>(Binary("Eq", v7007, v7008))) return Value(false); v7007 = v7008; return Value(true); }()); return v7004; }()))); } return result7001; }()), false); return Call(c, fn6998, std::move(args6999)); }());
s->SetAt(10, v6997);
if (static_cast<bool>(([&]() -> Value { auto v7011 = s->LocalAt(10); if (!static_cast<bool>(v7011)) return v7011; v7011 = Unary("Not", ([&]() -> Value { auto fn7012 = PrepareDictionaryGet(s->LocalAt(9)); Arguments args7013; args7013.positional.reserve(2); args7013.Add(Value("SHEEP"), false); args7013.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn7012, std::move(args7013)); }())); if (!static_cast<bool>(v7011)) return v7011; v7011 = ([&]() -> Value { auto fn7014 = PrepareDictionaryGet(Get(s->LocalAt(13), Value("shed"))); Arguments args7015; args7015.positional.reserve(2); args7015.Add(Value("SHEEP"), false); args7015.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn7014, std::move(args7015)); }()); return v7011; }()))) {
return ([&]() -> Value { auto v7016 = ([&]() -> Value { auto fn7017 = s->Global("_v219_walk"); Arguments args7018; args7018.positional.reserve(2); args7018.Add(s->LocalAt(12), false); args7018.Add(s->LocalAt(7), false); return Call(c, fn7017, std::move(args7018)); }()); if (static_cast<bool>(v7016)) return v7016; v7016 = List({Value("PICKUP"), Value("SHEEP"), ([&]() -> Value { auto fn7019 = s->Global("min"); Arguments args7020; args7020.positional.reserve(2); args7020.Add(s->LocalAt(10), false); args7020.Add(Get(Get(s->LocalAt(13), Value("shed")), Value("SHEEP")), false); return Call(c, fn7019, std::move(args7020)); }())}); return v7016; }());
}
auto v7021 = ([&]() -> Value { auto fn7022 = s->Global("sum"); Arguments args7023; args7023.Add(([&]() -> Value { auto comp7024 = std::make_shared<Scope>(); comp7024->globals = s->globals; comp7024->parent = s; static constexpr const char* comp7024_names[] = {"x", "y"}; comp7024->PrepareSlots(comp7024_names); auto result7025 = List(); for (const auto& item7026 : Iterate(s->LocalAt(16))) { auto unpack7027 = Iterate(item7026); ValidateUnpack(unpack7027, 2, false); comp7024->SetAt(0, unpack7027.at(0)); comp7024->SetAt(1, unpack7027.at(1)); result7025.node()->sequence.push_back(Unary("Not", ([&]() -> Value { auto v7028 = ([&]() -> Value { auto fn7029 = comp7024->Global("isinstance"); Arguments args7030; args7030.positional.reserve(2); args7030.Add(Get(Get(Get(comp7024->Captured("farm"), Value("tiles")), comp7024->LocalAt(1)), comp7024->LocalAt(0)), false); args7030.Add(comp7024->Global("dict"), false); return Call(c, fn7029, std::move(args7030)); }()); if (!static_cast<bool>(v7028)) return v7028; v7028 = ([&]() -> Value { auto fn7031 = PrepareDictionaryGet(Get(Get(Get(comp7024->Captured("farm"), Value("tiles")), comp7024->LocalAt(1)), comp7024->LocalAt(0))); Arguments args7032; args7032.Add(Value("fed_today"), false); return CallDictionaryGet(c, fn7031, std::move(args7032)); }()); return v7028; }()))); } return result7025; }()), false); return Call(c, fn7022, std::move(args7023)); }());
s->SetAt(8, v7021);
if (static_cast<bool>(([&]() -> Value { auto v7033 = s->LocalAt(8); if (!static_cast<bool>(v7033)) return v7033; v7033 = Unary("Not", ([&]() -> Value { auto fn7034 = PrepareDictionaryGet(s->LocalAt(9)); Arguments args7035; args7035.positional.reserve(2); args7035.Add(Value("WHEAT"), false); args7035.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn7034, std::move(args7035)); }())); if (!static_cast<bool>(v7033)) return v7033; v7033 = ([&]() -> Value { auto fn7036 = PrepareDictionaryGet(Get(s->LocalAt(13), Value("shed"))); Arguments args7037; args7037.positional.reserve(2); args7037.Add(Value("WHEAT"), false); args7037.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn7036, std::move(args7037)); }()); return v7033; }()))) {
return ([&]() -> Value { auto v7038 = ([&]() -> Value { auto fn7039 = s->Global("_v219_walk"); Arguments args7040; args7040.positional.reserve(2); args7040.Add(s->LocalAt(12), false); args7040.Add(s->LocalAt(7), false); return Call(c, fn7039, std::move(args7040)); }()); if (static_cast<bool>(v7038)) return v7038; v7038 = List({Value("PICKUP"), Value("WHEAT"), ([&]() -> Value { auto fn7041 = s->Global("min"); Arguments args7042; args7042.positional.reserve(2); args7042.Add(s->LocalAt(8), false); args7042.Add(Get(Get(s->LocalAt(13), Value("shed")), Value("WHEAT")), false); return Call(c, fn7041, std::move(args7042)); }())}); return v7038; }());
}
auto v7043 = List({});
s->SetAt(17, v7043);
for (const auto& item7044 : Iterate(s->LocalAt(16))) {
s->SetAt(15, item7044);
auto v7045 = s->LocalAt(15);
auto unpack7046 = Iterate(v7045);
ValidateUnpack(unpack7046, 2, false);
s->SetAt(19, unpack7046.at(0));
s->SetAt(20, unpack7046.at(1));
auto v7047 = Get(Get(Get(s->LocalAt(6), Value("tiles")), s->LocalAt(20)), s->LocalAt(19));
s->SetAt(18, v7047);
auto v7048 = Value{};
s->SetAt(4, v7048);
if (static_cast<bool>(([&]() -> Value { auto v7049 = s->LocalAt(18); Value v7050; v7050 = Value{}; if (!static_cast<bool>(Binary("Is", v7049, v7050))) return Value(false); v7049 = v7050; return Value(true); }()))) {
auto v7051 = List({Value("BUILD_PASTURE")});
s->SetAt(4, v7051);
}
else {
if (static_cast<bool>(([&]() -> Value { auto v7052 = ([&]() -> Value { auto fn7053 = s->Global("isinstance"); Arguments args7054; args7054.positional.reserve(2); args7054.Add(s->LocalAt(18), false); args7054.Add(s->Global("dict"), false); return Call(c, fn7053, std::move(args7054)); }()); if (!static_cast<bool>(v7052)) return v7052; v7052 = ([&]() -> Value { auto v7055 = ([&]() -> Value { auto fn7057 = PrepareDictionaryGet(s->LocalAt(18)); Arguments args7058; args7058.Add(Value("kind"), false); return CallDictionaryGet(c, fn7057, std::move(args7058)); }()); Value v7056; v7056 = Value("WEED"); if (!static_cast<bool>(Binary("Eq", v7055, v7056))) return Value(false); v7055 = v7056; return Value(true); }()); return v7052; }()))) {
auto v7059 = List({Value("DIG")});
s->SetAt(4, v7059);
}
else {
if (static_cast<bool>(([&]() -> Value { auto v7060 = ([&]() -> Value { auto fn7061 = s->Global("isinstance"); Arguments args7062; args7062.positional.reserve(2); args7062.Add(s->LocalAt(18), false); args7062.Add(s->Global("dict"), false); return Call(c, fn7061, std::move(args7062)); }()); if (!static_cast<bool>(v7060)) return v7060; v7060 = ([&]() -> Value { auto v7063 = ([&]() -> Value { auto fn7065 = PrepareDictionaryGet(s->LocalAt(18)); Arguments args7066; args7066.Add(Value("kind"), false); return CallDictionaryGet(c, fn7065, std::move(args7066)); }()); Value v7064; v7064 = Value("PASTURE"); if (!static_cast<bool>(Binary("Eq", v7063, v7064))) return Value(false); v7063 = v7064; return Value(true); }()); if (!static_cast<bool>(v7060)) return v7060; v7060 = Unary("Not", ([&]() -> Value { auto fn7067 = PrepareDictionaryGet(s->LocalAt(18)); Arguments args7068; args7068.Add(Value("animal"), false); return CallDictionaryGet(c, fn7067, std::move(args7068)); }())); return v7060; }()))) {
if (static_cast<bool>(([&]() -> Value { auto fn7069 = PrepareDictionaryGet(s->LocalAt(9)); Arguments args7070; args7070.positional.reserve(2); args7070.Add(Value("SHEEP"), false); args7070.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn7069, std::move(args7070)); }()))) {
auto v7071 = List({Value("PLACE"), Value("SHEEP")});
s->SetAt(4, v7071);
}
}
else {
if (static_cast<bool>(([&]() -> Value { auto v7072 = ([&]() -> Value { auto fn7073 = s->Global("isinstance"); Arguments args7074; args7074.positional.reserve(2); args7074.Add(s->LocalAt(18), false); args7074.Add(s->Global("dict"), false); return Call(c, fn7073, std::move(args7074)); }()); if (!static_cast<bool>(v7072)) return v7072; v7072 = ([&]() -> Value { auto v7075 = ([&]() -> Value { auto fn7077 = PrepareDictionaryGet(s->LocalAt(18)); Arguments args7078; args7078.Add(Value("animal"), false); return CallDictionaryGet(c, fn7077, std::move(args7078)); }()); Value v7076; v7076 = Value("SHEEP"); if (!static_cast<bool>(Binary("Eq", v7075, v7076))) return Value(false); v7075 = v7076; return Value(true); }()); return v7072; }()))) {
if (static_cast<bool>(([&]() -> Value { auto v7079 = Unary("Not", Get(s->LocalAt(18), Value("fed_today"))); if (!static_cast<bool>(v7079)) return v7079; v7079 = ([&]() -> Value { auto fn7080 = PrepareDictionaryGet(s->LocalAt(9)); Arguments args7081; args7081.positional.reserve(2); args7081.Add(Value("WHEAT"), false); args7081.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn7080, std::move(args7081)); }()); return v7079; }()))) {
auto v7082 = List({Value("FEED")});
s->SetAt(4, v7082);
}
else {
if (static_cast<bool>(Unary("Not", Get(s->LocalAt(18), Value("cared_today"))))) {
auto v7083 = List({Value("CARE")});
s->SetAt(4, v7083);
}
else {
if (static_cast<bool>(Get(s->LocalAt(18), Value("yield_units")))) {
auto v7084 = List({Value("HARVEST")});
s->SetAt(4, v7084);
}
else {
if (static_cast<bool>(Get(s->LocalAt(18), Value("fertilizer_available")))) {
auto v7085 = List({Value("COLLECT_FERTILIZER")});
s->SetAt(4, v7085);
}
}
}
}
}
}
}
}
if (static_cast<bool>(s->LocalAt(4))) {
(void)([&]() -> Value { auto fn7086 = Attribute(s->LocalAt(17), "append"); Arguments args7087; args7087.Add(Tuple({([&]() -> Value { auto v7088 = ([&]() -> Value { auto fn7089 = s->Global("abs"); Arguments args7090; args7090.Add(([&]() -> Value { auto v7091 = Get(s->LocalAt(12), Value(int64_t{0})); return Binary("Sub", v7091, s->LocalAt(19)); }()), false); return Call(c, fn7089, std::move(args7090)); }()); return Binary("Add", v7088, ([&]() -> Value { auto fn7092 = s->Global("abs"); Arguments args7093; args7093.Add(([&]() -> Value { auto v7094 = Get(s->LocalAt(12), Value(int64_t{1})); return Binary("Sub", v7094, s->LocalAt(20)); }()), false); return Call(c, fn7092, std::move(args7093)); }())); }()), ([&]() -> Value { auto fn7095 = Attribute(s->LocalAt(16), "index"); Arguments args7096; args7096.Add(s->LocalAt(15), false); return Call(c, fn7095, std::move(args7096)); }()), s->LocalAt(15), s->LocalAt(4)}), false); return Call(c, fn7086, std::move(args7087)); }());
}
}
if (static_cast<bool>(s->LocalAt(17))) {
auto v7097 = ([&]() -> Value { auto fn7098 = s->Global("min"); Arguments args7099; args7099.Add(s->LocalAt(17), false); return Call(c, fn7098, std::move(args7099)); }());
auto unpack7100 = Iterate(v7097);
ValidateUnpack(unpack7100, 4, false);
s->SetAt(0, unpack7100.at(0));
s->SetAt(0, unpack7100.at(1));
s->SetAt(15, unpack7100.at(2));
s->SetAt(4, unpack7100.at(3));
return ([&]() -> Value { auto v7101 = ([&]() -> Value { auto fn7102 = s->Global("_v219_walk"); Arguments args7103; args7103.positional.reserve(2); args7103.Add(s->LocalAt(12), false); args7103.Add(s->LocalAt(15), false); return Call(c, fn7102, std::move(args7103)); }()); if (static_cast<bool>(v7101)) return v7101; v7101 = s->LocalAt(4); return v7101; }());
}
if (static_cast<bool>(s->LocalAt(3))) {
return ([&]() -> Value { auto v7104 = ([&]() -> Value { auto fn7105 = s->Global("_v219_walk"); Arguments args7106; args7106.positional.reserve(2); args7106.Add(s->LocalAt(12), false); args7106.Add(s->LocalAt(7), false); return Call(c, fn7105, std::move(args7106)); }()); if (static_cast<bool>(v7104)) return v7104; v7104 = List({Value("PLACE"), Get(s->LocalAt(3), Value(int64_t{0})), Get(s->LocalAt(9), Get(s->LocalAt(3), Value(int64_t{0})))}); return v7104; }());
}
return List({Value("PASS")});
return {};
}
}  // namespace kagg::opponents::compiled
