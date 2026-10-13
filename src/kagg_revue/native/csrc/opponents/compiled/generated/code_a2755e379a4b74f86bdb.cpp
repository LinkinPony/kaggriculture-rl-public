// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_a2755e379a4b74f86bdb(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"_", "action", "buying", "ch", "changed", "cmd", "configuration", "cr", "cu", "cut", "day", "farm", "harvest", "have", "here", "i", "key", "later", "market", "new_market", "o", "observation", "p_c", "p_w", "pays_now", "planted", "pos", "positions", "prices", "priv", "q", "seat", "seeds_c", "selling", "st", "step", "stock", "tile", "tiles", "units", "view_action", "visits", "wheat_ok", "wu", "yu"};
s->PrepareSlots(s_names);
auto v21990 = ([&]() -> Value { auto fn21991 = s->Global("_CA_PARENT"); Arguments args21992; args21992.positional.reserve(2); args21992.Add(s->LocalAt(21), false); args21992.Add(s->LocalAt(6), false); return Call(c, fn21991, std::move(args21992)); }());
s->SetAt(1, v21990);
try {
auto v21994 = ([&]() -> Value { auto fn21995 = s->Global("int"); Arguments args21996; args21996.Add(Get(s->LocalAt(21), Value("step")), false); return Call(c, fn21995, std::move(args21996)); }());
s->SetAt(35, v21994);
auto v21997 = ([&]() -> Value { auto fn21998 = s->Global("int"); Arguments args21999; args21999.Add(Get(s->LocalAt(21), Value("player")), false); return Call(c, fn21998, std::move(args21999)); }());
s->SetAt(31, v21997);
auto v22000 = ([&]() -> Value { auto fn22001 = PrepareDictionaryGet(s->Global("_CA_STATE")); Arguments args22002; args22002.Add(s->LocalAt(31), false); return CallDictionaryGet(c, fn22001, std::move(args22002)); }());
s->SetAt(34, v22000);
if (static_cast<bool>(([&]() -> Value { auto v22003 = ([&]() -> Value { auto v22004 = s->LocalAt(35); Value v22005; v22005 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v22004, v22005))) return Value(false); v22004 = v22005; return Value(true); }()); if (static_cast<bool>(v22003)) return v22003; v22003 = ([&]() -> Value { auto v22006 = s->LocalAt(34); Value v22007; v22007 = Value{}; if (!static_cast<bool>(Binary("Is", v22006, v22007))) return Value(false); v22006 = v22007; return Value(true); }()); if (static_cast<bool>(v22003)) return v22003; v22003 = ([&]() -> Value { auto v22008 = s->LocalAt(35); Value v22009; v22009 = Get(s->LocalAt(34), Value("step")); if (!static_cast<bool>(Binary("LtE", v22008, v22009))) return Value(false); v22008 = v22009; return Value(true); }()); return v22003; }()))) {
auto v22010 = ([&]() -> Value { auto dict22011 = Dict(); auto key22012 = Value("step"); Put(dict22011, key22012, Unary("USub", Value(int64_t{1}))); auto key22013 = Value("tiles"); Put(dict22011, key22013, ([&]() -> Value { auto dict22014 = Dict(); return dict22014; }())); auto key22015 = Value("spare_wheat"); Put(dict22011, key22015, Value(int64_t{0})); auto key22016 = Value("spare_carrot"); Put(dict22011, key22016, Value(int64_t{0})); auto key22017 = Value("credit"); Put(dict22011, key22017, Value(int64_t{0})); return dict22011; }());
s->SetAt(34, v22010);
Put(s->Global("_CA_STATE"), s->LocalAt(31), v22010);
if (static_cast<bool>(([&]() -> Value { auto v22018 = s->LocalAt(35); Value v22019; v22019 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v22018, v22019))) return Value(false); v22018 = v22019; return Value(true); }()))) {
(void)([&]() -> Value { auto fn22020 = Attribute(s->Global("_CA_REPORT"), "update"); Arguments args22021; args22021.Keyword("ca_swaps", Value(int64_t{0})); args22021.Keyword("ca_rescues", Value(int64_t{0})); args22021.Keyword("ca_harvested", Value(int64_t{0})); args22021.Keyword("ca_sold", Value(int64_t{0})); args22021.Keyword("ca_seed_bought", Value(int64_t{0})); args22021.Keyword("ca_wheat_seed_saved", Value(int64_t{0})); args22021.Keyword("ca_carrot_seed_saved", Value(int64_t{0})); args22021.Keyword("ca_feed_block", Value(int64_t{0})); args22021.Keyword("ca_errors", Value(int64_t{0})); args22021.Keyword("ca_min_wheat", Value(int64_t{999})); return Call(c, fn22020, std::move(args22021)); }());
}
}
auto v22022 = s->LocalAt(35);
Put(s->LocalAt(34), Value("step"), v22022);
if (static_cast<bool>(([&]() -> Value { auto v22023 = Unary("Not", ([&]() -> Value { auto fn22024 = s->Global("isinstance"); Arguments args22025; args22025.positional.reserve(2); args22025.Add(s->LocalAt(1), false); args22025.Add(s->Global("dict"), false); return Call(c, fn22024, std::move(args22025)); }())); if (static_cast<bool>(v22023)) return v22023; v22023 = ([&]() -> Value { auto v22026 = s->LocalAt(35); Value v22027; v22027 = Value(int64_t{717}); if (!static_cast<bool>(Binary("Gt", v22026, v22027))) return Value(false); v22026 = v22027; return Value(true); }()); return v22023; }()))) {
return s->LocalAt(1);
}
auto v22028 = ([&]() -> Value { auto v22029 = s->LocalAt(35); return Binary("FloorDiv", v22029, Value(int64_t{24})); }());
s->SetAt(10, v22028);
auto v22030 = Get(Get(s->LocalAt(21), Value("farms")), s->LocalAt(31));
s->SetAt(11, v22030);
auto v22031 = Get(s->LocalAt(11), Value("tiles"));
s->SetAt(38, v22031);
auto v22032 = Get(s->LocalAt(21), Value("private"));
s->SetAt(29, v22032);
auto v22033 = Get(Get(s->LocalAt(21), Value("market")), Value("prices"));
s->SetAt(28, v22033);
auto v22034 = Tuple({([&]() -> Value { auto fn22035 = s->Global("int"); Arguments args22036; args22036.Add(([&]() -> Value { auto fn22037 = PrepareDictionaryGet(s->LocalAt(28)); Arguments args22038; args22038.positional.reserve(2); args22038.Add(Value("CARROT"), false); args22038.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn22037, std::move(args22038)); }()), false); return Call(c, fn22035, std::move(args22036)); }()), ([&]() -> Value { auto fn22039 = s->Global("int"); Arguments args22040; args22040.Add(([&]() -> Value { auto fn22041 = PrepareDictionaryGet(s->LocalAt(28)); Arguments args22042; args22042.positional.reserve(2); args22042.Add(Value("WHEAT"), false); args22042.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn22041, std::move(args22042)); }()), false); return Call(c, fn22039, std::move(args22040)); }())});
auto unpack22043 = Iterate(v22034);
ValidateUnpack(unpack22043, 2, false);
s->SetAt(22, unpack22043.at(0));
s->SetAt(23, unpack22043.at(1));
auto v22044 = ([&]() -> Value { auto v22045 = List({([&]() -> Value { auto fn22046 = s->Global("tuple"); Arguments args22047; args22047.Add(Get(s->LocalAt(11), Value("farmer")), false); return Call(c, fn22046, std::move(args22047)); }())}); return Binary("Add", v22045, ([&]() -> Value { auto comp22048 = std::make_shared<Scope>(); comp22048->globals = s->globals; comp22048->parent = s; static constexpr const char* comp22048_names[] = {"h"}; comp22048->PrepareSlots(comp22048_names); auto result22049 = List(); for (const auto& item22050 : Iterate(Get(s->LocalAt(11), Value("hands")))) { comp22048->SetAt(0, item22050); result22049.node()->sequence.push_back(([&]() -> Value { auto fn22051 = comp22048->Global("tuple"); Arguments args22052; args22052.Add(comp22048->LocalAt(0), false); return Call(c, fn22051, std::move(args22052)); }())); } return result22049; }())); }());
s->SetAt(27, v22044);
auto v22053 = ([&]() -> Value { auto v22054 = List({([&]() -> Value { auto fn22055 = s->Global("list"); Arguments args22056; args22056.Add(([&]() -> Value { auto v22057 = ([&]() -> Value { auto fn22058 = PrepareDictionaryGet(s->LocalAt(1)); Arguments args22059; args22059.Add(Value("farmer"), false); return CallDictionaryGet(c, fn22058, std::move(args22059)); }()); if (static_cast<bool>(v22057)) return v22057; v22057 = List({Value("PASS")}); return v22057; }()), false); return Call(c, fn22055, std::move(args22056)); }())}); return Binary("Add", v22054, ([&]() -> Value { auto comp22060 = std::make_shared<Scope>(); comp22060->globals = s->globals; comp22060->parent = s; static constexpr const char* comp22060_names[] = {"c"}; comp22060->PrepareSlots(comp22060_names); auto result22061 = List(); for (const auto& item22062 : Iterate(([&]() -> Value { auto v22063 = ([&]() -> Value { auto fn22064 = PrepareDictionaryGet(s->LocalAt(1)); Arguments args22065; args22065.Add(Value("hands"), false); return CallDictionaryGet(c, fn22064, std::move(args22065)); }()); if (static_cast<bool>(v22063)) return v22063; v22063 = List({}); return v22063; }()))) { comp22060->SetAt(0, item22062); result22061.node()->sequence.push_back(([&]() -> Value { auto fn22066 = comp22060->Global("list"); Arguments args22067; args22067.Add(comp22060->LocalAt(0), false); return Call(c, fn22066, std::move(args22067)); }())); } return result22061; }())); }());
s->SetAt(39, v22053);
auto v22068 = ([&]() -> Value { auto comp22069 = std::make_shared<Scope>(); comp22069->globals = s->globals; comp22069->parent = s; static constexpr const char* comp22069_names[] = {"o"}; comp22069->PrepareSlots(comp22069_names); auto result22070 = List(); for (const auto& item22071 : Iterate(([&]() -> Value { auto v22072 = ([&]() -> Value { auto fn22073 = PrepareDictionaryGet(s->LocalAt(1)); Arguments args22074; args22074.Add(Value("market"), false); return CallDictionaryGet(c, fn22073, std::move(args22074)); }()); if (static_cast<bool>(v22072)) return v22072; v22072 = List({}); return v22072; }()))) { comp22069->SetAt(0, item22071); result22070.node()->sequence.push_back(([&]() -> Value { auto fn22075 = comp22069->Global("list"); Arguments args22076; args22076.Add(comp22069->LocalAt(0), false); return Call(c, fn22075, std::move(args22076)); }())); } return result22070; }());
s->SetAt(18, v22068);
auto v22077 = Value(false);
s->SetAt(4, v22077);
if (static_cast<bool>(([&]() -> Value { auto v22078 = s->Global("_CA_FROM"); Value v22079; v22079 = s->LocalAt(10); if (!static_cast<bool>(Binary("LtE", v22078, v22079))) return Value(false); v22078 = v22079; v22079 = ([&]() -> Value { auto v22080 = s->Global("_CA_TO"); return Binary("Add", v22080, Value(int64_t{4})); }()); if (!static_cast<bool>(Binary("LtE", v22078, v22079))) return Value(false); v22078 = v22079; return Value(true); }()))) {
auto v22081 = ([&]() -> Value { auto fn22082 = s->Global("min"); Arguments args22083; args22083.positional.reserve(2); args22083.Add(Get(s->Global("_CA_REPORT"), Value("ca_min_wheat")), false); args22083.Add(([&]() -> Value { auto fn22084 = s->Global("_ca_wheat_total"); Arguments args22085; args22085.Add(s->LocalAt(21), false); return Call(c, fn22084, std::move(args22085)); }()), false); return Call(c, fn22082, std::move(args22083)); }());
Put(s->Global("_CA_REPORT"), Value("ca_min_wheat"), v22081);
}
for (const auto& item22086 : Iterate(([&]() -> Value { auto fn22087 = s->Global("list"); Arguments args22088; args22088.Add(([&]() -> Value { auto fn22089 = Attribute(Get(s->LocalAt(34), Value("tiles")), "items"); Arguments args22090; return Call(c, fn22089, std::move(args22090)); }()), false); return Call(c, fn22087, std::move(args22088)); }()))) {
auto unpack22091 = Iterate(item22086);
ValidateUnpack(unpack22091, 2, false);
s->SetAt(26, unpack22091.at(0));
s->SetAt(25, unpack22091.at(1));
auto v22092 = Get(Get(s->LocalAt(38), Get(s->LocalAt(26), Value(int64_t{1}))), Get(s->LocalAt(26), Value(int64_t{0})));
s->SetAt(37, v22092);
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto v22093 = ([&]() -> Value { auto fn22094 = s->Global("isinstance"); Arguments args22095; args22095.positional.reserve(2); args22095.Add(s->LocalAt(37), false); args22095.Add(s->Global("dict"), false); return Call(c, fn22094, std::move(args22095)); }()); if (!static_cast<bool>(v22093)) return v22093; v22093 = ([&]() -> Value { auto v22096 = ([&]() -> Value { auto fn22098 = PrepareDictionaryGet(s->LocalAt(37)); Arguments args22099; args22099.Add(Value("crop"), false); return CallDictionaryGet(c, fn22098, std::move(args22099)); }()); Value v22097; v22097 = Value("CARROT"); if (!static_cast<bool>(Binary("Eq", v22096, v22097))) return Value(false); v22096 = v22097; return Value(true); }()); if (!static_cast<bool>(v22093)) return v22093; v22093 = ([&]() -> Value { auto v22100 = ([&]() -> Value { auto fn22102 = s->Global("int"); Arguments args22103; args22103.Add(([&]() -> Value { auto fn22104 = PrepareDictionaryGet(s->LocalAt(37)); Arguments args22105; args22105.positional.reserve(2); args22105.Add(Value("planted_day"), false); args22105.Add(Unary("USub", Value(int64_t{9})), false); return CallDictionaryGet(c, fn22104, std::move(args22105)); }()), false); return Call(c, fn22102, std::move(args22103)); }()); Value v22101; v22101 = s->LocalAt(25); if (!static_cast<bool>(Binary("Eq", v22100, v22101))) return Value(false); v22100 = v22101; return Value(true); }()); return v22093; }())))) {
(void)([&]() -> Value { auto fn22106 = Attribute(Get(s->LocalAt(34), Value("tiles")), "pop"); Arguments args22107; args22107.positional.reserve(2); args22107.Add(s->LocalAt(26), false); args22107.Add(Value{}, false); return Call(c, fn22106, std::move(args22107)); }());
continue;
}
auto v22108 = ([&]() -> Value { auto comp22109 = std::make_shared<Scope>(); comp22109->globals = s->globals; comp22109->parent = s; static constexpr const char* comp22109_names[] = {"i", "p"}; comp22109->PrepareSlots(comp22109_names); auto result22110 = List(); for (const auto& item22111 : Iterate(([&]() -> Value { auto fn22112 = s->Global("enumerate"); Arguments args22113; args22113.Add(s->LocalAt(27), false); return Call(c, fn22112, std::move(args22113)); }()))) { auto unpack22114 = Iterate(item22111); ValidateUnpack(unpack22114, 2, false); comp22109->SetAt(0, unpack22114.at(0)); comp22109->SetAt(1, unpack22114.at(1)); if (!static_cast<bool>(([&]() -> Value { auto v22115 = ([&]() -> Value { auto v22116 = comp22109->LocalAt(1); Value v22117; v22117 = comp22109->Captured("pos"); if (!static_cast<bool>(Binary("Eq", v22116, v22117))) return Value(false); v22116 = v22117; return Value(true); }()); if (!static_cast<bool>(v22115)) return v22115; v22115 = ([&]() -> Value { auto v22118 = comp22109->LocalAt(0); Value v22119; v22119 = ([&]() -> Value { auto fn22120 = comp22109->Global("len"); Arguments args22121; args22121.Add(comp22109->Captured("units"), false); return Call(c, fn22120, std::move(args22121)); }()); if (!static_cast<bool>(Binary("Lt", v22118, v22119))) return Value(false); v22118 = v22119; return Value(true); }()); return v22115; }()))) continue; result22110.node()->sequence.push_back(comp22109->LocalAt(0)); } return result22110; }());
s->SetAt(14, v22108);
if (static_cast<bool>(Unary("Not", s->LocalAt(14)))) {
continue;
}
auto v22122 = Get(s->LocalAt(14), Value(int64_t{0}));
s->SetAt(15, v22122);
auto v22123 = Get(s->LocalAt(39), s->LocalAt(15));
s->SetAt(5, v22123);
auto v22124 = ([&]() -> Value { auto fn22125 = s->Global("int"); Arguments args22126; args22126.Add(([&]() -> Value { auto fn22127 = PrepareDictionaryGet(s->LocalAt(37)); Arguments args22128; args22128.positional.reserve(2); args22128.Add(Value("yield_units"), false); args22128.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn22127, std::move(args22128)); }()), false); return Call(c, fn22125, std::move(args22126)); }());
s->SetAt(44, v22124);
if (static_cast<bool>(([&]() -> Value { auto v22129 = s->LocalAt(5); if (!static_cast<bool>(v22129)) return v22129; v22129 = ([&]() -> Value { auto v22130 = Get(s->LocalAt(5), Value(int64_t{0})); Value v22131; v22131 = Value("HARVEST"); if (!static_cast<bool>(Binary("Eq", v22130, v22131))) return Value(false); v22130 = v22131; return Value(true); }()); return v22129; }()))) {
if (static_cast<bool>(([&]() -> Value { auto v22132 = ([&]() -> Value { auto v22133 = ([&]() -> Value { auto v22135 = s->LocalAt(10); return Binary("Sub", v22135, s->LocalAt(25)); }()); Value v22134; v22134 = Value(int64_t{2}); if (!static_cast<bool>(Binary("GtE", v22133, v22134))) return Value(false); v22133 = v22134; return Value(true); }()); if (!static_cast<bool>(v22132)) return v22132; v22132 = ([&]() -> Value { auto v22136 = s->LocalAt(44); Value v22137; v22137 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v22136, v22137))) return Value(false); v22136 = v22137; return Value(true); }()); return v22132; }()))) {
auto v22138 = s->LocalAt(34);
auto v22139 = Value("credit");
auto v22140 = Get(v22138, v22139);
Put(v22138, v22139, Inplace("Add", v22140, s->LocalAt(44)));
auto v22141 = s->Global("_CA_REPORT");
auto v22142 = Value("ca_harvested");
auto v22143 = Get(v22141, v22142);
Put(v22141, v22142, Inplace("Add", v22143, s->LocalAt(44)));
(void)([&]() -> Value { auto fn22144 = Attribute(Get(s->LocalAt(34), Value("tiles")), "pop"); Arguments args22145; args22145.positional.reserve(2); args22145.Add(s->LocalAt(26), false); args22145.Add(Value{}, false); return Call(c, fn22144, std::move(args22145)); }());
}
continue;
}
if (static_cast<bool>(([&]() -> Value { auto v22146 = Unary("Not", s->Global("_CA_RESCUE")); if (static_cast<bool>(v22146)) return v22146; v22146 = ([&]() -> Value { auto v22147 = s->LocalAt(5); if (!static_cast<bool>(v22147)) return v22147; v22147 = ([&]() -> Value { auto v22148 = Get(s->LocalAt(5), Value(int64_t{0})); Value v22149; v22149 = s->Global("_CA_MOVES"); if (!static_cast<bool>(Binary("In", v22148, v22149))) return Value(false); v22148 = v22149; return Value(true); }()); return v22147; }()); if (static_cast<bool>(v22146)) return v22146; v22146 = ([&]() -> Value { auto v22150 = ([&]() -> Value { auto v22152 = s->LocalAt(10); return Binary("Sub", v22152, s->LocalAt(25)); }()); Value v22151; v22151 = Value(int64_t{2}); if (!static_cast<bool>(Binary("Lt", v22150, v22151))) return Value(false); v22150 = v22151; return Value(true); }()); if (static_cast<bool>(v22146)) return v22146; v22146 = ([&]() -> Value { auto v22153 = s->LocalAt(44); Value v22154; v22154 = Value(int64_t{0}); if (!static_cast<bool>(Binary("LtE", v22153, v22154))) return Value(false); v22153 = v22154; return Value(true); }()); return v22146; }()))) {
continue;
}
auto v22155 = ([&]() -> Value { auto fn22156 = s->Global("_ca_visits"); Arguments args22157; args22157.positional.reserve(4); args22157.Add(s->LocalAt(21), false); args22157.Add(s->LocalAt(1), false); args22157.Add(s->LocalAt(26), false); args22157.Add(([&]() -> Value { auto v22158 = ([&]() -> Value { auto v22159 = s->LocalAt(25); return Binary("Add", v22159, Value(int64_t{5})); }()); return Binary("Mult", v22158, Value(int64_t{24})); }()), false); return Call(c, fn22156, std::move(args22157)); }());
s->SetAt(41, v22155);
auto v22160 = ([&]() -> Value { auto fn22161 = s->Global("_ca_yield_path"); Arguments args22162; args22162.positional.reserve(3); args22162.Add(Value("CARROT"), false); args22162.Add(s->LocalAt(25), false); args22162.Add(s->LocalAt(41), false); args22162.Keyword("y0", s->LocalAt(44)); args22162.Keyword("fert_until", ([&]() -> Value { auto fn22163 = s->Global("int"); Arguments args22164; args22164.Add(([&]() -> Value { auto fn22165 = PrepareDictionaryGet(s->LocalAt(37)); Arguments args22166; args22166.positional.reserve(2); args22166.Add(Value("fertilized_until_day"), false); args22166.Add(Unary("USub", Value(int64_t{1})), false); return CallDictionaryGet(c, fn22165, std::move(args22166)); }()), false); return Call(c, fn22163, std::move(args22164)); }())); args22162.Keyword("watered_day", (static_cast<bool>(([&]() -> Value { auto fn22167 = PrepareDictionaryGet(s->LocalAt(37)); Arguments args22168; args22168.Add(Value("watered_today"), false); return CallDictionaryGet(c, fn22167, std::move(args22168)); }())) ? s->LocalAt(10) : Unary("USub", Value(int64_t{1})))); args22162.Keyword("now_step", s->LocalAt(35)); return Call(c, fn22161, std::move(args22162)); }());
auto unpack22169 = Iterate(v22160);
ValidateUnpack(unpack22169, 3, false);
s->SetAt(12, unpack22169.at(0));
s->SetAt(17, unpack22169.at(1));
s->SetAt(0, unpack22169.at(2));
if (static_cast<bool>(([&]() -> Value { auto v22170 = s->LocalAt(44); Value v22171; v22171 = ([&]() -> Value { auto fn22172 = s->Global("max"); Arguments args22173; args22173.positional.reserve(2); args22173.Add(s->LocalAt(12), false); args22173.Add(s->LocalAt(17), false); return Call(c, fn22172, std::move(args22173)); }()); if (!static_cast<bool>(Binary("Gt", v22170, v22171))) return Value(false); v22170 = v22171; return Value(true); }()))) {
auto v22174 = List({Value("HARVEST")});
Put(s->LocalAt(39), s->LocalAt(15), v22174);
auto v22175 = s->LocalAt(34);
auto v22176 = Value("credit");
auto v22177 = Get(v22175, v22176);
Put(v22175, v22176, Inplace("Add", v22177, s->LocalAt(44)));
auto v22178 = s->Global("_CA_REPORT");
auto v22179 = Value("ca_harvested");
auto v22180 = Get(v22178, v22179);
Put(v22178, v22179, Inplace("Add", v22180, s->LocalAt(44)));
auto v22181 = s->Global("_CA_REPORT");
auto v22182 = Value("ca_rescues");
auto v22183 = Get(v22181, v22182);
Put(v22181, v22182, Inplace("Add", v22183, Value(int64_t{1})));
(void)([&]() -> Value { auto fn22184 = Attribute(Get(s->LocalAt(34), Value("tiles")), "pop"); Arguments args22185; args22185.positional.reserve(2); args22185.Add(s->LocalAt(26), false); args22185.Add(Value{}, false); return Call(c, fn22184, std::move(args22185)); }());
auto v22186 = Value(true);
s->SetAt(4, v22186);
}
}
auto v22187 = ([&]() -> Value { auto v22188 = ([&]() -> Value { auto v22190 = ([&]() -> Value { auto v22191 = Value(int64_t{3}); return Binary("Mult", v22191, ([&]() -> Value { auto v22192 = s->LocalAt(22); return Binary("Sub", v22192, s->Global("_CA_DROP")); }())); }()); return Binary("Sub", v22190, Value(int64_t{20})); }()); Value v22189; v22189 = ([&]() -> Value { auto v22193 = ([&]() -> Value { auto v22194 = ([&]() -> Value { auto v22195 = Value(int64_t{4}); return Binary("Mult", v22195, s->LocalAt(23)); }()); return Binary("Sub", v22194, Value(int64_t{10})); }()); return Binary("Add", v22193, s->Global("_CA_MARGIN")); }()); if (!static_cast<bool>(Binary("Gt", v22188, v22189))) return Value(false); v22188 = v22189; return Value(true); }());
s->SetAt(24, v22187);
if (static_cast<bool>(([&]() -> Value { auto v22196 = ([&]() -> Value { auto v22197 = s->Global("_CA_FROM"); Value v22198; v22198 = s->LocalAt(10); if (!static_cast<bool>(Binary("LtE", v22197, v22198))) return Value(false); v22197 = v22198; v22198 = s->Global("_CA_TO"); if (!static_cast<bool>(Binary("LtE", v22197, v22198))) return Value(false); v22197 = v22198; return Value(true); }()); if (!static_cast<bool>(v22196)) return v22196; v22196 = s->LocalAt(24); return v22196; }()))) {
auto v22199 = ([&]() -> Value { auto fn22200 = s->Global("min"); Arguments args22201; args22201.positional.reserve(2); args22201.Add(Get(s->LocalAt(34), Value("spare_carrot")), false); args22201.Add(([&]() -> Value { auto v22202 = ([&]() -> Value { auto fn22203 = s->Global("int"); Arguments args22204; args22204.Add(([&]() -> Value { auto fn22205 = PrepareDictionaryGet(Get(s->LocalAt(29), Value("seeds"))); Arguments args22206; args22206.positional.reserve(2); args22206.Add(Value("CARROT"), false); args22206.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn22205, std::move(args22206)); }()), false); return Call(c, fn22203, std::move(args22204)); }()); return Binary("Sub", v22202, ([&]() -> Value { auto fn22207 = s->Global("sum"); Arguments args22208; args22208.Add(([&]() -> Value { auto comp22209 = std::make_shared<Scope>(); comp22209->globals = s->globals; comp22209->parent = s; static constexpr const char* comp22209_names[] = {"c"}; comp22209->PrepareSlots(comp22209_names); auto result22210 = List(); for (const auto& item22211 : Iterate(s->LocalAt(39))) { comp22209->SetAt(0, item22211); if (!static_cast<bool>(([&]() -> Value { auto v22212 = Slice(comp22209->LocalAt(0), Value{}, Value(int64_t{2}), Value{}); Value v22213; v22213 = List({Value("PLANT"), Value("CARROT")}); if (!static_cast<bool>(Binary("Eq", v22212, v22213))) return Value(false); v22212 = v22213; return Value(true); }()))) continue; result22210.node()->sequence.push_back(Value(int64_t{1})); } return result22210; }()), false); return Call(c, fn22207, std::move(args22208)); }())); }()), false); return Call(c, fn22200, std::move(args22201)); }());
s->SetAt(32, v22199);
auto v22214 = Value{};
s->SetAt(42, v22214);
for (const auto& item22215 : Iterate(([&]() -> Value { auto fn22216 = s->Global("enumerate"); Arguments args22217; args22217.Add(s->LocalAt(39), false); return Call(c, fn22216, std::move(args22217)); }()))) {
auto unpack22218 = Iterate(item22215);
ValidateUnpack(unpack22218, 2, false);
s->SetAt(15, unpack22218.at(0));
s->SetAt(5, unpack22218.at(1));
if (static_cast<bool>(([&]() -> Value { auto v22219 = ([&]() -> Value { auto v22220 = Slice(s->LocalAt(5), Value{}, Value(int64_t{2}), Value{}); Value v22221; v22221 = List({Value("PLANT"), Value("WHEAT")}); if (!static_cast<bool>(Binary("NotEq", v22220, v22221))) return Value(false); v22220 = v22221; return Value(true); }()); if (static_cast<bool>(v22219)) return v22219; v22219 = ([&]() -> Value { auto v22222 = s->LocalAt(15); Value v22223; v22223 = ([&]() -> Value { auto fn22224 = s->Global("len"); Arguments args22225; args22225.Add(s->LocalAt(27), false); return Call(c, fn22224, std::move(args22225)); }()); if (!static_cast<bool>(Binary("GtE", v22222, v22223))) return Value(false); v22222 = v22223; return Value(true); }()); if (static_cast<bool>(v22219)) return v22219; v22219 = ([&]() -> Value { auto v22226 = s->LocalAt(32); Value v22227; v22227 = Value(int64_t{0}); if (!static_cast<bool>(Binary("LtE", v22226, v22227))) return Value(false); v22226 = v22227; return Value(true); }()); return v22219; }()))) {
continue;
}
auto v22228 = Get(s->LocalAt(27), s->LocalAt(15));
s->SetAt(26, v22228);
if (static_cast<bool>(([&]() -> Value { auto v22229 = Get(Get(s->LocalAt(38), Get(s->LocalAt(26), Value(int64_t{1}))), Get(s->LocalAt(26), Value(int64_t{0}))); Value v22230; v22230 = Value{}; if (!static_cast<bool>(Binary("IsNot", v22229, v22230))) return Value(false); v22229 = v22230; return Value(true); }()))) {
continue;
}
if (static_cast<bool>(([&]() -> Value { auto v22231 = s->LocalAt(42); Value v22232; v22232 = Value{}; if (!static_cast<bool>(Binary("Is", v22231, v22232))) return Value(false); v22231 = v22232; return Value(true); }()))) {
auto v22233 = ([&]() -> Value { auto v22234 = ([&]() -> Value { auto fn22236 = s->Global("_ca_wheat_total"); Arguments args22237; args22237.Add(s->LocalAt(21), false); return Call(c, fn22236, std::move(args22237)); }()); Value v22235; v22235 = ([&]() -> Value { auto fn22238 = s->Global("_ca_feed_need"); Arguments args22239; args22239.positional.reserve(3); args22239.Add(s->LocalAt(31), false); args22239.Add(s->LocalAt(35), false); args22239.Add(s->Global("_CA_FEED_DAYS"), false); return Call(c, fn22238, std::move(args22239)); }()); if (!static_cast<bool>(Binary("GtE", v22234, v22235))) return Value(false); v22234 = v22235; return Value(true); }());
s->SetAt(42, v22233);
}
if (static_cast<bool>(Unary("Not", s->LocalAt(42)))) {
auto v22240 = s->Global("_CA_REPORT");
auto v22241 = Value("ca_feed_block");
auto v22242 = Get(v22240, v22241);
Put(v22240, v22241, Inplace("Add", v22242, Value(int64_t{1})));
break;
}
auto v22243 = ([&]() -> Value { auto fn22244 = s->Global("_ca_visits"); Arguments args22245; args22245.positional.reserve(4); args22245.Add(s->LocalAt(21), false); args22245.Add(s->LocalAt(1), false); args22245.Add(s->LocalAt(26), false); args22245.Add(([&]() -> Value { auto v22246 = ([&]() -> Value { auto v22247 = s->LocalAt(10); return Binary("Add", v22247, Value(int64_t{6})); }()); return Binary("Mult", v22246, Value(int64_t{24})); }()), false); args22245.Keyword("start", ([&]() -> Value { auto v22248 = s->LocalAt(35); return Binary("Add", v22248, Value(int64_t{1})); }())); return Call(c, fn22244, std::move(args22245)); }());
s->SetAt(41, v22243);
auto v22249 = ([&]() -> Value { auto fn22250 = s->Global("_ca_yield_path"); Arguments args22251; args22251.positional.reserve(3); args22251.Add(Value("WHEAT"), false); args22251.Add(s->LocalAt(10), false); args22251.Add(s->LocalAt(41), false); return Call(c, fn22250, std::move(args22251)); }());
auto unpack22252 = Iterate(v22249);
ValidateUnpack(unpack22252, 3, false);
s->SetAt(43, unpack22252.at(0));
s->SetAt(0, unpack22252.at(1));
s->SetAt(0, unpack22252.at(2));
auto v22253 = ([&]() -> Value { auto fn22254 = s->Global("_ca_yield_path"); Arguments args22255; args22255.positional.reserve(3); args22255.Add(Value("CARROT"), false); args22255.Add(s->LocalAt(10), false); args22255.Add(s->LocalAt(41), false); return Call(c, fn22254, std::move(args22255)); }());
auto unpack22256 = Iterate(v22253);
ValidateUnpack(unpack22256, 3, false);
s->SetAt(3, unpack22256.at(0));
s->SetAt(7, unpack22256.at(1));
s->SetAt(0, unpack22256.at(2));
auto v22257 = ([&]() -> Value { auto fn22258 = s->Global("max"); Arguments args22259; args22259.positional.reserve(2); args22259.Add(s->LocalAt(3), false); args22259.Add((static_cast<bool>(s->Global("_CA_RESCUE")) ? s->LocalAt(7) : Value(int64_t{0})), false); return Call(c, fn22258, std::move(args22259)); }());
s->SetAt(8, v22257);
if (static_cast<bool>(([&]() -> Value { auto v22260 = ([&]() -> Value { auto v22262 = ([&]() -> Value { auto v22263 = s->LocalAt(8); return Binary("Mult", v22263, ([&]() -> Value { auto v22264 = s->LocalAt(22); return Binary("Sub", v22264, s->Global("_CA_DROP")); }())); }()); return Binary("Sub", v22262, Value(int64_t{20})); }()); Value v22261; v22261 = ([&]() -> Value { auto v22265 = ([&]() -> Value { auto v22266 = ([&]() -> Value { auto v22267 = s->LocalAt(43); return Binary("Mult", v22267, s->LocalAt(23)); }()); return Binary("Sub", v22266, Value(int64_t{10})); }()); return Binary("Add", v22265, s->Global("_CA_MARGIN")); }()); if (!static_cast<bool>(Binary("Gt", v22260, v22261))) return Value(false); v22260 = v22261; return Value(true); }()))) {
auto v22268 = List({Value("PLANT"), Value("CARROT")});
Put(s->LocalAt(39), s->LocalAt(15), v22268);
auto v22269 = s->LocalAt(32);
s->SetAt(32, Inplace("Sub", v22269, Value(int64_t{1})));
auto v22270 = s->LocalAt(34);
auto v22271 = Value("spare_carrot");
auto v22272 = Get(v22270, v22271);
Put(v22270, v22271, Inplace("Sub", v22272, Value(int64_t{1})));
auto v22273 = s->LocalAt(10);
Put(Get(s->LocalAt(34), Value("tiles")), s->LocalAt(26), v22273);
auto v22274 = s->LocalAt(34);
auto v22275 = Value("spare_wheat");
auto v22276 = Get(v22274, v22275);
Put(v22274, v22275, Inplace("Add", v22276, Value(int64_t{1})));
auto v22277 = s->Global("_CA_REPORT");
auto v22278 = Value("ca_swaps");
auto v22279 = Get(v22277, v22278);
Put(v22277, v22278, Inplace("Add", v22279, Value(int64_t{1})));
auto v22280 = Value(true);
s->SetAt(4, v22280);
}
}
}
auto v22281 = List({});
s->SetAt(19, v22281);
for (const auto& item22282 : Iterate(s->LocalAt(18))) {
s->SetAt(20, item22282);
if (static_cast<bool>(([&]() -> Value { auto v22283 = ([&]() -> Value { auto v22284 = ([&]() -> Value { auto fn22286 = s->Global("len"); Arguments args22287; args22287.Add(s->LocalAt(20), false); return Call(c, fn22286, std::move(args22287)); }()); Value v22285; v22285 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v22284, v22285))) return Value(false); v22284 = v22285; return Value(true); }()); if (!static_cast<bool>(v22283)) return v22283; v22283 = ([&]() -> Value { auto v22288 = Get(s->LocalAt(20), Value(int64_t{0})); Value v22289; v22289 = Value("BUY_SEED"); if (!static_cast<bool>(Binary("Eq", v22288, v22289))) return Value(false); v22288 = v22289; return Value(true); }()); if (!static_cast<bool>(v22283)) return v22283; v22283 = ([&]() -> Value { auto v22290 = Get(s->LocalAt(20), Value(int64_t{1})); Value v22291; v22291 = Tuple({Value("WHEAT"), Value("CARROT")}); if (!static_cast<bool>(Binary("In", v22290, v22291))) return Value(false); v22290 = v22291; return Value(true); }()); return v22283; }()))) {
auto v22292 = (static_cast<bool>(([&]() -> Value { auto v22293 = Get(s->LocalAt(20), Value(int64_t{1})); Value v22294; v22294 = Value("WHEAT"); if (!static_cast<bool>(Binary("Eq", v22293, v22294))) return Value(false); v22293 = v22294; return Value(true); }())) ? Value("spare_wheat") : Value("spare_carrot"));
s->SetAt(16, v22292);
auto v22295 = ([&]() -> Value { auto fn22296 = s->Global("min"); Arguments args22297; args22297.positional.reserve(2); args22297.Add(([&]() -> Value { auto fn22298 = s->Global("int"); Arguments args22299; args22299.Add(Get(s->LocalAt(20), Value(int64_t{2})), false); return Call(c, fn22298, std::move(args22299)); }()), false); args22297.Add(Get(s->LocalAt(34), s->LocalAt(16)), false); return Call(c, fn22296, std::move(args22297)); }());
s->SetAt(9, v22295);
if (static_cast<bool>(([&]() -> Value { auto v22300 = s->LocalAt(9); Value v22301; v22301 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v22300, v22301))) return Value(false); v22300 = v22301; return Value(true); }()))) {
auto v22302 = s->LocalAt(34);
auto v22303 = s->LocalAt(16);
auto v22304 = Get(v22302, v22303);
Put(v22302, v22303, Inplace("Sub", v22304, s->LocalAt(9)));
auto v22305 = s->Global("_CA_REPORT");
auto v22306 = (static_cast<bool>(([&]() -> Value { auto v22308 = Get(s->LocalAt(20), Value(int64_t{1})); Value v22309; v22309 = Value("WHEAT"); if (!static_cast<bool>(Binary("Eq", v22308, v22309))) return Value(false); v22308 = v22309; return Value(true); }())) ? Value("ca_wheat_seed_saved") : Value("ca_carrot_seed_saved"));
auto v22307 = Get(v22305, v22306);
Put(v22305, v22306, Inplace("Add", v22307, s->LocalAt(9)));
auto v22310 = Value(true);
s->SetAt(4, v22310);
if (static_cast<bool>(([&]() -> Value { auto v22311 = ([&]() -> Value { auto v22313 = ([&]() -> Value { auto fn22314 = s->Global("int"); Arguments args22315; args22315.Add(Get(s->LocalAt(20), Value(int64_t{2})), false); return Call(c, fn22314, std::move(args22315)); }()); return Binary("Sub", v22313, s->LocalAt(9)); }()); Value v22312; v22312 = Value(int64_t{0}); if (!static_cast<bool>(Binary("LtE", v22311, v22312))) return Value(false); v22311 = v22312; return Value(true); }()))) {
continue;
}
auto v22316 = List({Get(s->LocalAt(20), Value(int64_t{0})), Get(s->LocalAt(20), Value(int64_t{1})), ([&]() -> Value { auto v22317 = ([&]() -> Value { auto fn22318 = s->Global("int"); Arguments args22319; args22319.Add(Get(s->LocalAt(20), Value(int64_t{2})), false); return Call(c, fn22318, std::move(args22319)); }()); return Binary("Sub", v22317, s->LocalAt(9)); }())});
s->SetAt(20, v22316);
}
}
(void)([&]() -> Value { auto fn22320 = Attribute(s->LocalAt(19), "append"); Arguments args22321; args22321.Add(s->LocalAt(20), false); return Call(c, fn22320, std::move(args22321)); }());
}
auto v22322 = s->LocalAt(19);
s->SetAt(18, v22322);
if (static_cast<bool>(([&]() -> Value { auto v22323 = ([&]() -> Value { auto v22324 = s->Global("_CA_FROM"); Value v22325; v22325 = s->LocalAt(10); if (!static_cast<bool>(Binary("LtE", v22324, v22325))) return Value(false); v22324 = v22325; v22325 = ([&]() -> Value { auto v22326 = s->Global("_CA_TO"); return Binary("Sub", v22326, Value(int64_t{1})); }()); if (!static_cast<bool>(Binary("LtE", v22324, v22325))) return Value(false); v22324 = v22325; return Value(true); }()); if (!static_cast<bool>(v22323)) return v22323; v22323 = s->LocalAt(24); if (!static_cast<bool>(v22323)) return v22323; v22323 = ([&]() -> Value { auto v22327 = ([&]() -> Value { auto fn22329 = s->Global("len"); Arguments args22330; args22330.Add(s->LocalAt(18), false); return Call(c, fn22329, std::move(args22330)); }()); Value v22328; v22328 = Value(int64_t{10}); if (!static_cast<bool>(Binary("Lt", v22327, v22328))) return Value(false); v22327 = v22328; return Value(true); }()); return v22323; }()))) {
auto v22331 = ([&]() -> Value { auto v22332 = ([&]() -> Value { auto fn22333 = s->Global("int"); Arguments args22334; args22334.Add(([&]() -> Value { auto fn22335 = PrepareDictionaryGet(Get(s->LocalAt(29), Value("seeds"))); Arguments args22336; args22336.positional.reserve(2); args22336.Add(Value("CARROT"), false); args22336.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn22335, std::move(args22336)); }()), false); return Call(c, fn22333, std::move(args22334)); }()); return Binary("Sub", v22332, ([&]() -> Value { auto fn22337 = s->Global("sum"); Arguments args22338; args22338.Add(([&]() -> Value { auto comp22339 = std::make_shared<Scope>(); comp22339->globals = s->globals; comp22339->parent = s; static constexpr const char* comp22339_names[] = {"c"}; comp22339->PrepareSlots(comp22339_names); auto result22340 = List(); for (const auto& item22341 : Iterate(s->LocalAt(39))) { comp22339->SetAt(0, item22341); if (!static_cast<bool>(([&]() -> Value { auto v22342 = Slice(comp22339->LocalAt(0), Value{}, Value(int64_t{2}), Value{}); Value v22343; v22343 = List({Value("PLANT"), Value("CARROT")}); if (!static_cast<bool>(Binary("Eq", v22342, v22343))) return Value(false); v22342 = v22343; return Value(true); }()))) continue; result22340.node()->sequence.push_back(Value(int64_t{1})); } return result22340; }()), false); return Call(c, fn22337, std::move(args22338)); }())); }());
s->SetAt(13, v22331);
auto v22344 = ([&]() -> Value { auto fn22345 = s->Global("sum"); Arguments args22346; args22346.Add(([&]() -> Value { auto comp22347 = std::make_shared<Scope>(); comp22347->globals = s->globals; comp22347->parent = s; static constexpr const char* comp22347_names[] = {"o"}; comp22347->PrepareSlots(comp22347_names); auto result22348 = List(); for (const auto& item22349 : Iterate(s->LocalAt(18))) { comp22347->SetAt(0, item22349); if (!static_cast<bool>(([&]() -> Value { auto v22350 = ([&]() -> Value { auto v22351 = ([&]() -> Value { auto fn22353 = comp22347->Global("len"); Arguments args22354; args22354.Add(comp22347->LocalAt(0), false); return Call(c, fn22353, std::move(args22354)); }()); Value v22352; v22352 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v22351, v22352))) return Value(false); v22351 = v22352; return Value(true); }()); if (!static_cast<bool>(v22350)) return v22350; v22350 = ([&]() -> Value { auto v22355 = Slice(comp22347->LocalAt(0), Value{}, Value(int64_t{2}), Value{}); Value v22356; v22356 = List({Value("BUY_SEED"), Value("CARROT")}); if (!static_cast<bool>(Binary("Eq", v22355, v22356))) return Value(false); v22355 = v22356; return Value(true); }()); return v22350; }()))) continue; result22348.node()->sequence.push_back(([&]() -> Value { auto fn22357 = comp22347->Global("int"); Arguments args22358; args22358.Add(Get(comp22347->LocalAt(0), Value(int64_t{2})), false); return Call(c, fn22357, std::move(args22358)); }())); } return result22348; }()), false); return Call(c, fn22345, std::move(args22346)); }());
s->SetAt(2, v22344);
auto v22359 = ([&]() -> Value { auto v22360 = ([&]() -> Value { auto v22361 = s->Global("_CA_BUFFER"); return Binary("Sub", v22361, s->LocalAt(13)); }()); return Binary("Sub", v22360, s->LocalAt(2)); }());
s->SetAt(30, v22359);
if (static_cast<bool>(([&]() -> Value { auto v22362 = ([&]() -> Value { auto v22363 = s->LocalAt(30); Value v22364; v22364 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v22363, v22364))) return Value(false); v22363 = v22364; return Value(true); }()); if (!static_cast<bool>(v22362)) return v22362; v22362 = ([&]() -> Value { auto v22365 = ([&]() -> Value { auto fn22367 = s->Global("int"); Arguments args22368; args22368.Add(([&]() -> Value { auto fn22369 = PrepareDictionaryGet(s->LocalAt(11)); Arguments args22370; args22370.positional.reserve(2); args22370.Add(Value("money"), false); args22370.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn22369, std::move(args22370)); }()), false); return Call(c, fn22367, std::move(args22368)); }()); Value v22366; v22366 = ([&]() -> Value { auto v22371 = s->Global("_CA_CASH"); return Binary("Add", v22371, ([&]() -> Value { auto v22372 = Value(int64_t{20}); return Binary("Mult", v22372, s->LocalAt(30)); }())); }()); if (!static_cast<bool>(Binary("GtE", v22365, v22366))) return Value(false); v22365 = v22366; return Value(true); }()); return v22362; }()))) {
(void)([&]() -> Value { auto fn22373 = Attribute(s->LocalAt(18), "append"); Arguments args22374; args22374.Add(List({Value("BUY_SEED"), Value("CARROT"), s->LocalAt(30)}), false); return Call(c, fn22373, std::move(args22374)); }());
auto v22375 = s->LocalAt(34);
auto v22376 = Value("spare_carrot");
auto v22377 = Get(v22375, v22376);
Put(v22375, v22376, Inplace("Add", v22377, s->LocalAt(30)));
auto v22378 = s->Global("_CA_REPORT");
auto v22379 = Value("ca_seed_bought");
auto v22380 = Get(v22378, v22379);
Put(v22378, v22379, Inplace("Add", v22380, s->LocalAt(30)));
auto v22381 = Value(true);
s->SetAt(4, v22381);
}
}
if (static_cast<bool>(([&]() -> Value { auto v22382 = ([&]() -> Value { auto v22383 = Get(s->LocalAt(34), Value("credit")); Value v22384; v22384 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v22383, v22384))) return Value(false); v22383 = v22384; return Value(true); }()); if (!static_cast<bool>(v22382)) return v22382; v22382 = ([&]() -> Value { auto v22385 = s->LocalAt(22); Value v22386; v22386 = Value(int64_t{2}); if (!static_cast<bool>(Binary("GtE", v22385, v22386))) return Value(false); v22385 = v22386; return Value(true); }()); if (!static_cast<bool>(v22382)) return v22382; v22382 = ([&]() -> Value { auto v22387 = ([&]() -> Value { auto fn22389 = s->Global("len"); Arguments args22390; args22390.Add(s->LocalAt(18), false); return Call(c, fn22389, std::move(args22390)); }()); Value v22388; v22388 = Value(int64_t{10}); if (!static_cast<bool>(Binary("Lt", v22387, v22388))) return Value(false); v22387 = v22388; return Value(true); }()); return v22382; }()))) {
auto v22391 = ([&]() -> Value { auto dict22392 = Dict(); auto key22393 = Value("farmer"); Put(dict22392, key22393, Get(s->LocalAt(39), Value(int64_t{0}))); auto key22394 = Value("hands"); Put(dict22392, key22394, Slice(s->LocalAt(39), Value(int64_t{1}), Value{}, Value{})); auto key22395 = Value("market"); Put(dict22392, key22395, s->LocalAt(18)); return dict22392; }());
s->SetAt(40, v22391);
auto v22396 = ([&]() -> Value { auto fn22397 = s->Global("int"); Arguments args22398; args22398.Add(([&]() -> Value { auto fn22399 = PrepareDictionaryGet(([&]() -> Value { auto fn22401 = s->Global("projected_shed"); Arguments args22402; args22402.positional.reserve(2); args22402.Add(s->LocalAt(40), false); args22402.Add(([&]() -> Value { auto fn22403 = s->Global("FarmView"); Arguments args22404; args22404.Add(s->LocalAt(21), false); return Call(c, fn22403, std::move(args22404)); }()), false); return Call(c, fn22401, std::move(args22402)); }())); Arguments args22400; args22400.positional.reserve(2); args22400.Add(Value("CARROT"), false); args22400.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn22399, std::move(args22400)); }()), false); return Call(c, fn22397, std::move(args22398)); }());
s->SetAt(36, v22396);
auto v22405 = ([&]() -> Value { auto fn22406 = s->Global("sum"); Arguments args22407; args22407.Add(([&]() -> Value { auto comp22408 = std::make_shared<Scope>(); comp22408->globals = s->globals; comp22408->parent = s; static constexpr const char* comp22408_names[] = {"o"}; comp22408->PrepareSlots(comp22408_names); auto result22409 = List(); for (const auto& item22410 : Iterate(s->LocalAt(18))) { comp22408->SetAt(0, item22410); if (!static_cast<bool>(([&]() -> Value { auto v22411 = ([&]() -> Value { auto v22412 = ([&]() -> Value { auto fn22414 = comp22408->Global("len"); Arguments args22415; args22415.Add(comp22408->LocalAt(0), false); return Call(c, fn22414, std::move(args22415)); }()); Value v22413; v22413 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v22412, v22413))) return Value(false); v22412 = v22413; return Value(true); }()); if (!static_cast<bool>(v22411)) return v22411; v22411 = ([&]() -> Value { auto v22416 = Slice(comp22408->LocalAt(0), Value{}, Value(int64_t{2}), Value{}); Value v22417; v22417 = List({Value("SELL"), Value("CARROT")}); if (!static_cast<bool>(Binary("Eq", v22416, v22417))) return Value(false); v22416 = v22417; return Value(true); }()); return v22411; }()))) continue; result22409.node()->sequence.push_back(([&]() -> Value { auto fn22418 = comp22408->Global("int"); Arguments args22419; args22419.Add(Get(comp22408->LocalAt(0), Value(int64_t{2})), false); return Call(c, fn22418, std::move(args22419)); }())); } return result22409; }()), false); return Call(c, fn22406, std::move(args22407)); }());
s->SetAt(33, v22405);
auto v22420 = ([&]() -> Value { auto fn22421 = s->Global("min"); Arguments args22422; args22422.positional.reserve(2); args22422.Add(Get(s->LocalAt(34), Value("credit")), false); args22422.Add(([&]() -> Value { auto v22423 = s->LocalAt(36); return Binary("Sub", v22423, s->LocalAt(33)); }()), false); return Call(c, fn22421, std::move(args22422)); }());
s->SetAt(30, v22420);
if (static_cast<bool>(([&]() -> Value { auto v22424 = s->LocalAt(30); Value v22425; v22425 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v22424, v22425))) return Value(false); v22424 = v22425; return Value(true); }()))) {
(void)([&]() -> Value { auto fn22426 = Attribute(s->LocalAt(18), "insert"); Arguments args22427; args22427.positional.reserve(2); args22427.Add(Value(int64_t{0}), false); args22427.Add(List({Value("SELL"), Value("CARROT"), s->LocalAt(30)}), false); return Call(c, fn22426, std::move(args22427)); }());
auto v22428 = s->LocalAt(34);
auto v22429 = Value("credit");
auto v22430 = Get(v22428, v22429);
Put(v22428, v22429, Inplace("Sub", v22430, s->LocalAt(30)));
auto v22431 = s->Global("_CA_REPORT");
auto v22432 = Value("ca_sold");
auto v22433 = Get(v22431, v22432);
Put(v22431, v22432, Inplace("Add", v22433, s->LocalAt(30)));
auto v22434 = Value(true);
s->SetAt(4, v22434);
}
}
if (static_cast<bool>(s->LocalAt(4))) {
auto v22435 = ([&]() -> Value { auto fn22436 = s->Global("dict"); Arguments args22437; args22437.Add(s->LocalAt(1), false); return Call(c, fn22436, std::move(args22437)); }());
s->SetAt(1, v22435);
auto v22438 = Get(s->LocalAt(39), Value(int64_t{0}));
Put(s->LocalAt(1), Value("farmer"), v22438);
auto v22439 = Slice(s->LocalAt(39), Value(int64_t{1}), Value{}, Value{});
Put(s->LocalAt(1), Value("hands"), v22439);
auto v22440 = Slice(s->LocalAt(18), Value{}, Value(int64_t{10}), Value{});
Put(s->LocalAt(1), Value("market"), v22440);
}
} catch (const Error& error21993) {
if (Matches(error21993, s->Global("Exception"))) {
auto v22441 = s->Global("_CA_REPORT");
auto v22442 = Value("ca_errors");
auto v22443 = Get(v22441, v22442);
Put(v22441, v22442, Inplace("Add", v22443, Value(int64_t{1})));
}
else { throw; }
}
return s->LocalAt(1);
return {};
}
}  // namespace kagg::opponents::compiled
