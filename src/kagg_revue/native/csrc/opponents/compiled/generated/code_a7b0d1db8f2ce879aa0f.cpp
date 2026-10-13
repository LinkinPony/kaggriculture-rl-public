// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_a7b0d1db8f2ce879aa0f(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"_", "act", "action", "board", "builds", "buying_land", "carrier", "chosen", "cmd", "dx", "dy", "end", "farm", "half", "hires", "i", "ib", "ip", "k", "key", "locked_but_bought", "mode", "n", "next_quadrant", "nx", "ny", "obs", "pickups", "places", "plan", "pos", "positions", "prior", "q", "quadrant", "seat", "step", "t", "tb", "tile", "tiles", "tp", "units", "unlocked", "x", "y"};
s->PrepareSlots(s_names);
auto v25074 = ([&]() -> Value { auto fn25075 = s->Global("int"); Arguments args25076; args25076.Add(Get(s->LocalAt(26), Value("player")), false); return Call(c, fn25075, std::move(args25076)); }());
s->SetAt(35, v25074);
auto v25077 = ([&]() -> Value { auto fn25078 = s->Global("int"); Arguments args25079; args25079.Add(Get(s->LocalAt(26), Value("step")), false); return Call(c, fn25078, std::move(args25079)); }());
s->SetAt(36, v25077);
auto v25080 = Get(Get(s->LocalAt(26), Value("farms")), s->LocalAt(35));
s->SetAt(12, v25080);
auto v25081 = ([&]() -> Value { auto fn25082 = s->Global("len"); Arguments args25083; args25083.Add(Get(s->LocalAt(12), Value("tiles")), false); return Call(c, fn25082, std::move(args25083)); }());
s->SetAt(3, v25081);
auto v25084 = ([&]() -> Value { auto v25085 = List({([&]() -> Value { auto fn25086 = s->Global("list"); Arguments args25087; args25087.Add(Get(s->LocalAt(12), Value("farmer")), false); return Call(c, fn25086, std::move(args25087)); }())}); return Binary("Add", v25085, ([&]() -> Value { auto comp25088 = std::make_shared<Scope>(); comp25088->globals = s->globals; comp25088->parent = s; static constexpr const char* comp25088_names[] = {"h"}; comp25088->PrepareSlots(comp25088_names); auto result25089 = List(); for (const auto& item25090 : Iterate(Get(s->LocalAt(12), Value("hands")))) { comp25088->SetAt(0, item25090); result25089.node()->sequence.push_back(([&]() -> Value { auto fn25091 = comp25088->Global("list"); Arguments args25092; args25092.Add(comp25088->LocalAt(0), false); return Call(c, fn25091, std::move(args25092)); }())); } return result25089; }())); }());
s->SetAt(31, v25084);
auto v25093 = ([&]() -> Value { auto v25094 = ([&]() -> Value { auto v25095 = ([&]() -> Value { auto v25096 = ([&]() -> Value { auto v25097 = s->LocalAt(36); return Binary("FloorDiv", v25097, Value(int64_t{24})); }()); return Binary("Add", v25096, Value(int64_t{1})); }()); return Binary("Mult", v25095, Value(int64_t{24})); }()); return Binary("Sub", v25094, Value(int64_t{1})); }());
s->SetAt(11, v25093);
auto v25098 = Tuple({List({}), List({}), List({})});
auto unpack25099 = Iterate(v25098);
ValidateUnpack(unpack25099, 3, false);
s->SetAt(4, unpack25099.at(0));
s->SetAt(27, unpack25099.at(1));
s->SetAt(28, unpack25099.at(2));
for (const auto& item25100 : Iterate(([&]() -> Value { auto fn25101 = s->Global("range"); Arguments args25102; args25102.positional.reserve(2); args25102.Add(s->LocalAt(36), false); args25102.Add(([&]() -> Value { auto v25103 = s->LocalAt(11); return Binary("Add", v25103, Value(int64_t{1})); }()), false); return Call(c, fn25101, std::move(args25102)); }()))) {
s->SetAt(37, item25100);
auto v25104 = (static_cast<bool>(([&]() -> Value { auto v25105 = s->LocalAt(37); Value v25106; v25106 = s->LocalAt(36); if (!static_cast<bool>(Binary("Eq", v25105, v25106))) return Value(false); v25105 = v25106; return Value(true); }())) ? s->LocalAt(2) : ([&]() -> Value { auto fn25107 = s->Global("_cs_tape"); Arguments args25108; args25108.positional.reserve(2); args25108.Add(s->LocalAt(35), false); args25108.Add(s->LocalAt(37), false); return Call(c, fn25107, std::move(args25108)); }()));
s->SetAt(1, v25104);
auto v25109 = ([&]() -> Value { auto v25110 = List({([&]() -> Value { auto v25111 = ([&]() -> Value { auto fn25112 = PrepareDictionaryGet(s->LocalAt(1)); Arguments args25113; args25113.Add(Value("farmer"), false); return CallDictionaryGet(c, fn25112, std::move(args25113)); }()); if (static_cast<bool>(v25111)) return v25111; v25111 = List({Value("PASS")}); return v25111; }())}); return Binary("Add", v25110, ([&]() -> Value { auto fn25114 = s->Global("list"); Arguments args25115; args25115.Add(([&]() -> Value { auto v25116 = ([&]() -> Value { auto fn25117 = PrepareDictionaryGet(s->LocalAt(1)); Arguments args25118; args25118.Add(Value("hands"), false); return CallDictionaryGet(c, fn25117, std::move(args25118)); }()); if (static_cast<bool>(v25116)) return v25116; v25116 = List({}); return v25116; }()), false); return Call(c, fn25114, std::move(args25115)); }())); }());
s->SetAt(42, v25109);
for (const auto& item25119 : Iterate(([&]() -> Value { auto fn25120 = s->Global("range"); Arguments args25121; args25121.Add(([&]() -> Value { auto fn25122 = s->Global("len"); Arguments args25123; args25123.Add(s->LocalAt(31), false); return Call(c, fn25122, std::move(args25123)); }()), false); return Call(c, fn25120, std::move(args25121)); }()))) {
s->SetAt(15, item25119);
auto v25124 = (static_cast<bool>(([&]() -> Value { auto v25125 = ([&]() -> Value { auto v25126 = s->LocalAt(15); Value v25127; v25127 = ([&]() -> Value { auto fn25128 = s->Global("len"); Arguments args25129; args25129.Add(s->LocalAt(42), false); return Call(c, fn25128, std::move(args25129)); }()); if (!static_cast<bool>(Binary("Lt", v25126, v25127))) return Value(false); v25126 = v25127; return Value(true); }()); if (!static_cast<bool>(v25125)) return v25125; v25125 = Get(s->LocalAt(42), s->LocalAt(15)); return v25125; }())) ? Get(s->LocalAt(42), s->LocalAt(15)) : List({Value("PASS")}));
s->SetAt(8, v25124);
auto v25130 = ([&]() -> Value { auto fn25131 = s->Global("tuple"); Arguments args25132; args25132.Add(Get(s->LocalAt(31), s->LocalAt(15)), false); return Call(c, fn25131, std::move(args25132)); }());
s->SetAt(30, v25130);
if (static_cast<bool>(([&]() -> Value { auto v25133 = Get(s->LocalAt(8), Value(int64_t{0})); Value v25134; v25134 = s->Global("_CS_MOVES"); if (!static_cast<bool>(Binary("In", v25133, v25134))) return Value(false); v25133 = v25134; return Value(true); }()))) {
auto v25135 = Get(s->Global("_CS_MOVES"), Get(s->LocalAt(8), Value(int64_t{0})));
auto unpack25136 = Iterate(v25135);
ValidateUnpack(unpack25136, 2, false);
s->SetAt(9, unpack25136.at(0));
s->SetAt(10, unpack25136.at(1));
auto v25137 = Tuple({([&]() -> Value { auto v25138 = Get(s->LocalAt(30), Value(int64_t{0})); return Binary("Add", v25138, s->LocalAt(9)); }()), ([&]() -> Value { auto v25139 = Get(s->LocalAt(30), Value(int64_t{1})); return Binary("Add", v25139, s->LocalAt(10)); }())});
auto unpack25140 = Iterate(v25137);
ValidateUnpack(unpack25140, 2, false);
s->SetAt(24, unpack25140.at(0));
s->SetAt(25, unpack25140.at(1));
if (static_cast<bool>(([&]() -> Value { auto v25141 = ([&]() -> Value { auto v25142 = Value(int64_t{0}); Value v25143; v25143 = s->LocalAt(24); if (!static_cast<bool>(Binary("LtE", v25142, v25143))) return Value(false); v25142 = v25143; v25143 = s->LocalAt(3); if (!static_cast<bool>(Binary("Lt", v25142, v25143))) return Value(false); v25142 = v25143; return Value(true); }()); if (!static_cast<bool>(v25141)) return v25141; v25141 = ([&]() -> Value { auto v25144 = Value(int64_t{0}); Value v25145; v25145 = s->LocalAt(25); if (!static_cast<bool>(Binary("LtE", v25144, v25145))) return Value(false); v25144 = v25145; v25145 = s->LocalAt(3); if (!static_cast<bool>(Binary("Lt", v25144, v25145))) return Value(false); v25144 = v25145; return Value(true); }()); return v25141; }()))) {
auto v25146 = List({s->LocalAt(24), s->LocalAt(25)});
Put(s->LocalAt(31), s->LocalAt(15), v25146);
}
}
else {
if (static_cast<bool>(([&]() -> Value { auto v25147 = Get(s->LocalAt(8), Value(int64_t{0})); Value v25148; v25148 = Value("BUILD_PASTURE"); if (!static_cast<bool>(Binary("Eq", v25147, v25148))) return Value(false); v25147 = v25148; return Value(true); }()))) {
(void)([&]() -> Value { auto fn25149 = Attribute(s->LocalAt(4), "append"); Arguments args25150; args25150.Add(Tuple({s->LocalAt(37), s->LocalAt(15), s->LocalAt(30)}), false); return Call(c, fn25149, std::move(args25150)); }());
}
else {
if (static_cast<bool>(([&]() -> Value { auto v25151 = ([&]() -> Value { auto v25152 = ([&]() -> Value { auto fn25154 = s->Global("len"); Arguments args25155; args25155.Add(s->LocalAt(8), false); return Call(c, fn25154, std::move(args25155)); }()); Value v25153; v25153 = Value(int64_t{2}); if (!static_cast<bool>(Binary("GtE", v25152, v25153))) return Value(false); v25152 = v25153; return Value(true); }()); if (!static_cast<bool>(v25151)) return v25151; v25151 = ([&]() -> Value { auto v25156 = Get(s->LocalAt(8), Value(int64_t{0})); Value v25157; v25157 = Value("PICKUP"); if (!static_cast<bool>(Binary("Eq", v25156, v25157))) return Value(false); v25156 = v25157; return Value(true); }()); if (!static_cast<bool>(v25151)) return v25151; v25151 = ([&]() -> Value { auto v25158 = Get(s->LocalAt(8), Value(int64_t{1})); Value v25159; v25159 = Value("COW"); if (!static_cast<bool>(Binary("Eq", v25158, v25159))) return Value(false); v25158 = v25159; return Value(true); }()); return v25151; }()))) {
(void)([&]() -> Value { auto fn25160 = Attribute(s->LocalAt(27), "append"); Arguments args25161; args25161.Add(Tuple({s->LocalAt(37), s->LocalAt(15), ([&]() -> Value { auto fn25162 = s->Global("max"); Arguments args25163; args25163.positional.reserve(2); args25163.Add(Value(int64_t{1}), false); args25163.Add((static_cast<bool>(([&]() -> Value { auto v25164 = ([&]() -> Value { auto fn25166 = s->Global("len"); Arguments args25167; args25167.Add(s->LocalAt(8), false); return Call(c, fn25166, std::move(args25167)); }()); Value v25165; v25165 = Value(int64_t{2}); if (!static_cast<bool>(Binary("Gt", v25164, v25165))) return Value(false); v25164 = v25165; return Value(true); }())) ? ([&]() -> Value { auto fn25168 = s->Global("int"); Arguments args25169; args25169.Add(Get(s->LocalAt(8), Value(int64_t{2})), false); return Call(c, fn25168, std::move(args25169)); }()) : Value(int64_t{1})), false); return Call(c, fn25162, std::move(args25163)); }())}), false); return Call(c, fn25160, std::move(args25161)); }());
}
else {
if (static_cast<bool>(([&]() -> Value { auto v25170 = ([&]() -> Value { auto v25171 = ([&]() -> Value { auto fn25173 = s->Global("len"); Arguments args25174; args25174.Add(s->LocalAt(8), false); return Call(c, fn25173, std::move(args25174)); }()); Value v25172; v25172 = Value(int64_t{2}); if (!static_cast<bool>(Binary("GtE", v25171, v25172))) return Value(false); v25171 = v25172; return Value(true); }()); if (!static_cast<bool>(v25170)) return v25170; v25170 = ([&]() -> Value { auto v25175 = Get(s->LocalAt(8), Value(int64_t{0})); Value v25176; v25176 = Value("PLACE"); if (!static_cast<bool>(Binary("Eq", v25175, v25176))) return Value(false); v25175 = v25176; return Value(true); }()); if (!static_cast<bool>(v25170)) return v25170; v25170 = ([&]() -> Value { auto v25177 = Get(s->LocalAt(8), Value(int64_t{1})); Value v25178; v25178 = Value("COW"); if (!static_cast<bool>(Binary("Eq", v25177, v25178))) return Value(false); v25177 = v25178; return Value(true); }()); return v25170; }()))) {
(void)([&]() -> Value { auto fn25179 = Attribute(s->LocalAt(28), "append"); Arguments args25180; args25180.Add(Tuple({s->LocalAt(37), s->LocalAt(15), s->LocalAt(30)}), false); return Call(c, fn25179, std::move(args25180)); }());
}
}
}
}
}
auto v25181 = ([&]() -> Value { auto fn25182 = s->Global("sum"); Arguments args25183; args25183.Add(([&]() -> Value { auto comp25184 = std::make_shared<Scope>(); comp25184->globals = s->globals; comp25184->parent = s; static constexpr const char* comp25184_names[] = {"o"}; comp25184->PrepareSlots(comp25184_names); auto result25185 = List(); for (const auto& item25186 : Iterate(([&]() -> Value { auto v25187 = ([&]() -> Value { auto fn25188 = PrepareDictionaryGet(s->LocalAt(1)); Arguments args25189; args25189.Add(Value("market"), false); return CallDictionaryGet(c, fn25188, std::move(args25189)); }()); if (static_cast<bool>(v25187)) return v25187; v25187 = List({}); return v25187; }()))) { comp25184->SetAt(0, item25186); if (!static_cast<bool>(([&]() -> Value { auto v25190 = comp25184->LocalAt(0); if (!static_cast<bool>(v25190)) return v25190; v25190 = ([&]() -> Value { auto v25191 = Get(comp25184->LocalAt(0), Value(int64_t{0})); Value v25192; v25192 = Value("HIRE"); if (!static_cast<bool>(Binary("Eq", v25191, v25192))) return Value(false); v25191 = v25192; return Value(true); }()); return v25190; }()))) continue; result25185.node()->sequence.push_back(Value(int64_t{1})); } return result25185; }()), false); return Call(c, fn25182, std::move(args25183)); }());
s->SetAt(14, v25181);
for (const auto& item25193 : Iterate(([&]() -> Value { auto fn25194 = s->Global("range"); Arguments args25195; args25195.Add(s->LocalAt(14), false); return Call(c, fn25194, std::move(args25195)); }()))) {
s->SetAt(0, item25193);
(void)([&]() -> Value { auto fn25196 = Attribute(s->LocalAt(31), "append"); Arguments args25197; args25197.Add(([&]() -> Value { auto fn25198 = s->Global("_cs_spawn"); Arguments args25199; args25199.positional.reserve(2); args25199.Add(s->LocalAt(31), false); args25199.Add(s->LocalAt(3), false); return Call(c, fn25198, std::move(args25199)); }()), false); return Call(c, fn25196, std::move(args25197)); }());
}
}
auto v25200 = Tuple({List({}), ([&]() -> Value { auto fn25201 = s->Global("set"); Arguments args25202; return Call(c, fn25201, std::move(args25202)); }())});
auto unpack25203 = Iterate(v25200);
ValidateUnpack(unpack25203, 2, false);
s->SetAt(7, unpack25203.at(0));
s->SetAt(40, unpack25203.at(1));
for (const auto& item25204 : Iterate(s->LocalAt(28))) {
auto unpack25205 = Iterate(item25204);
ValidateUnpack(unpack25205, 3, false);
s->SetAt(37, unpack25205.at(0));
s->SetAt(15, unpack25205.at(1));
s->SetAt(30, unpack25205.at(2));
if (static_cast<bool>(([&]() -> Value { auto v25206 = s->LocalAt(30); Value v25207; v25207 = s->LocalAt(40); if (!static_cast<bool>(Binary("NotIn", v25206, v25207))) return Value(false); v25206 = v25207; return Value(true); }()))) {
(void)([&]() -> Value { auto fn25208 = Attribute(s->LocalAt(7), "append"); Arguments args25209; args25209.Add(Tuple({s->LocalAt(37), s->LocalAt(15), s->LocalAt(30)}), false); return Call(c, fn25208, std::move(args25209)); }());
(void)([&]() -> Value { auto fn25210 = Attribute(s->LocalAt(40), "add"); Arguments args25211; args25211.Add(s->LocalAt(30), false); return Call(c, fn25210, std::move(args25211)); }());
}
if (static_cast<bool>(([&]() -> Value { auto v25212 = ([&]() -> Value { auto fn25214 = s->Global("len"); Arguments args25215; args25215.Add(s->LocalAt(7), false); return Call(c, fn25214, std::move(args25215)); }()); Value v25213; v25213 = s->LocalAt(18); if (!static_cast<bool>(Binary("Eq", v25212, v25213))) return Value(false); v25212 = v25213; return Value(true); }()))) {
break;
}
}
if (static_cast<bool>(([&]() -> Value { auto v25216 = ([&]() -> Value { auto fn25218 = s->Global("len"); Arguments args25219; args25219.Add(s->LocalAt(7), false); return Call(c, fn25218, std::move(args25219)); }()); Value v25217; v25217 = s->LocalAt(18); if (!static_cast<bool>(Binary("Lt", v25216, v25217))) return Value(false); v25216 = v25217; return Value(true); }()))) {
return Value{};
}
auto v25220 = ([&]() -> Value { auto dict25221 = Dict(); auto key25222 = Value("builds"); Put(dict25221, key25222, ([&]() -> Value { auto dict25223 = Dict(); return dict25223; }())); auto key25224 = Value("pickups"); Put(dict25221, key25224, ([&]() -> Value { auto dict25225 = Dict(); return dict25225; }())); auto key25226 = Value("places"); Put(dict25221, key25226, ([&]() -> Value { auto dict25227 = Dict(); return dict25227; }())); return dict25221; }());
s->SetAt(29, v25220);
auto v25228 = ([&]() -> Value { auto comp25229 = std::make_shared<Scope>(); comp25229->globals = s->globals; comp25229->parent = s; static constexpr const char* comp25229_names[] = {"o"}; comp25229->PrepareSlots(comp25229_names); auto result25230 = List(); for (const auto& item25231 : Iterate(([&]() -> Value { auto v25232 = ([&]() -> Value { auto fn25233 = PrepareDictionaryGet(s->LocalAt(2)); Arguments args25234; args25234.Add(Value("market"), false); return CallDictionaryGet(c, fn25233, std::move(args25234)); }()); if (static_cast<bool>(v25232)) return v25232; v25232 = List({}); return v25232; }()))) { comp25229->SetAt(0, item25231); if (static_cast<bool>(([&]() -> Value { auto v25235 = comp25229->LocalAt(0); if (!static_cast<bool>(v25235)) return v25235; v25235 = ([&]() -> Value { auto v25236 = Get(comp25229->LocalAt(0), Value(int64_t{0})); Value v25237; v25237 = Value("BUY_LAND"); if (!static_cast<bool>(Binary("Eq", v25236, v25237))) return Value(false); v25236 = v25237; return Value(true); }()); return v25235; }()))) return Value(true); } return Value(false); }());
s->SetAt(5, v25228);
auto v25238 = ([&]() -> Value { auto fn25239 = s->Global("list"); Arguments args25240; args25240.Add(([&]() -> Value { auto v25241 = ([&]() -> Value { auto fn25242 = PrepareDictionaryGet(s->LocalAt(12)); Arguments args25243; args25243.Add(Value("unlocked_quadrants"), false); return CallDictionaryGet(c, fn25242, std::move(args25243)); }()); if (static_cast<bool>(v25241)) return v25241; v25241 = List({Value("NW")}); return v25241; }()), false); return Call(c, fn25239, std::move(args25240)); }());
s->SetAt(43, v25238);
auto v25244 = Slice(([&]() -> Value { auto comp25245 = std::make_shared<Scope>(); comp25245->globals = s->globals; comp25245->parent = s; static constexpr const char* comp25245_names[] = {"q"}; comp25245->PrepareSlots(comp25245_names); auto result25246 = List(); for (const auto& item25247 : Iterate(Tuple({Value("NE"), Value("SW"), Value("SE")}))) { comp25245->SetAt(0, item25247); if (!static_cast<bool>(([&]() -> Value { auto v25248 = comp25245->LocalAt(0); Value v25249; v25249 = comp25245->Captured("unlocked"); if (!static_cast<bool>(Binary("NotIn", v25248, v25249))) return Value(false); v25248 = v25249; return Value(true); }()))) continue; result25246.node()->sequence.push_back(comp25245->LocalAt(0)); } return result25246; }()), Value{}, Value(int64_t{1}), Value{});
s->SetAt(23, v25244);
auto v25250 = ([&]() -> Value { auto v25251 = s->LocalAt(3); return Binary("FloorDiv", v25251, Value(int64_t{2})); }());
s->SetAt(13, v25250);
for (const auto& item25252 : Iterate(s->LocalAt(7))) {
auto unpack25253 = Iterate(item25252);
ValidateUnpack(unpack25253, 3, false);
s->SetAt(37, unpack25253.at(0));
s->SetAt(15, unpack25253.at(1));
s->SetAt(30, unpack25253.at(2));
auto v25254 = s->LocalAt(30);
auto unpack25255 = Iterate(v25254);
ValidateUnpack(unpack25255, 2, false);
s->SetAt(44, unpack25255.at(0));
s->SetAt(45, unpack25255.at(1));
auto v25256 = Get(Get(Get(s->LocalAt(12), Value("tiles")), s->LocalAt(45)), s->LocalAt(44));
s->SetAt(39, v25256);
if (static_cast<bool>(([&]() -> Value { auto v25257 = s->LocalAt(21); Value v25258; v25258 = Value("GOOSE"); if (!static_cast<bool>(Binary("Eq", v25257, v25258))) return Value(false); v25257 = v25258; return Value(true); }()))) {
auto v25259 = ([&]() -> Value { auto v25260 = (static_cast<bool>(([&]() -> Value { auto v25261 = s->LocalAt(45); Value v25262; v25262 = s->LocalAt(13); if (!static_cast<bool>(Binary("Lt", v25261, v25262))) return Value(false); v25261 = v25262; return Value(true); }())) ? Value("N") : Value("S")); return Binary("Add", v25260, (static_cast<bool>(([&]() -> Value { auto v25263 = s->LocalAt(44); Value v25264; v25264 = s->LocalAt(13); if (!static_cast<bool>(Binary("Lt", v25263, v25264))) return Value(false); v25263 = v25264; return Value(true); }())) ? Value("W") : Value("E"))); }());
s->SetAt(34, v25259);
auto v25265 = ([&]() -> Value { auto v25266 = ([&]() -> Value { auto v25267 = s->LocalAt(39); Value v25268; v25268 = Value("LOCKED"); if (!static_cast<bool>(Binary("Eq", v25267, v25268))) return Value(false); v25267 = v25268; return Value(true); }()); if (!static_cast<bool>(v25266)) return v25266; v25266 = s->LocalAt(5); if (!static_cast<bool>(v25266)) return v25266; v25266 = ([&]() -> Value { auto v25269 = s->LocalAt(34); Value v25270; v25270 = s->LocalAt(23); if (!static_cast<bool>(Binary("In", v25269, v25270))) return Value(false); v25269 = v25270; return Value(true); }()); return v25266; }());
s->SetAt(20, v25265);
if (static_cast<bool>(([&]() -> Value { auto v25271 = ([&]() -> Value { auto v25272 = s->LocalAt(39); Value v25273; v25273 = Value{}; if (!static_cast<bool>(Binary("IsNot", v25272, v25273))) return Value(false); v25272 = v25273; return Value(true); }()); if (!static_cast<bool>(v25271)) return v25271; v25271 = Unary("Not", s->LocalAt(20)); return v25271; }()))) {
return Value{};
}
auto v25274 = ([&]() -> Value { auto comp25275 = std::make_shared<Scope>(); comp25275->globals = s->globals; comp25275->parent = s; static constexpr const char* comp25275_names[] = {"ib", "pb", "tb"}; comp25275->PrepareSlots(comp25275_names); auto result25276 = List(); for (const auto& item25277 : Iterate(s->LocalAt(4))) { auto unpack25278 = Iterate(item25277); ValidateUnpack(unpack25278, 3, false); comp25275->SetAt(2, unpack25278.at(0)); comp25275->SetAt(0, unpack25278.at(1)); comp25275->SetAt(1, unpack25278.at(2)); if (!static_cast<bool>(([&]() -> Value { auto v25279 = ([&]() -> Value { auto v25280 = comp25275->LocalAt(1); Value v25281; v25281 = comp25275->Captured("pos"); if (!static_cast<bool>(Binary("Eq", v25280, v25281))) return Value(false); v25280 = v25281; return Value(true); }()); if (!static_cast<bool>(v25279)) return v25279; v25279 = ([&]() -> Value { auto v25282 = comp25275->LocalAt(2); Value v25283; v25283 = comp25275->Captured("t"); if (!static_cast<bool>(Binary("Lt", v25282, v25283))) return Value(false); v25282 = v25283; return Value(true); }()); return v25279; }()))) continue; result25276.node()->sequence.push_back(Tuple({comp25275->LocalAt(2), comp25275->LocalAt(0)})); } return result25276; }());
s->SetAt(32, v25274);
if (static_cast<bool>(Unary("Not", s->LocalAt(32)))) {
return Value{};
}
auto v25284 = Get(s->LocalAt(32), Unary("USub", Value(int64_t{1})));
auto unpack25285 = Iterate(v25284);
ValidateUnpack(unpack25285, 2, false);
s->SetAt(38, unpack25285.at(0));
s->SetAt(16, unpack25285.at(1));
auto v25286 = s->LocalAt(30);
Put(Get(s->LocalAt(29), Value("builds")), Tuple({s->LocalAt(38), s->LocalAt(16)}), v25286);
}
auto v25287 = ([&]() -> Value { auto comp25288 = std::make_shared<Scope>(); comp25288->globals = s->globals; comp25288->parent = s; static constexpr const char* comp25288_names[] = {"ip", "q", "tp"}; comp25288->PrepareSlots(comp25288_names); auto result25289 = List(); for (const auto& item25290 : Iterate(s->LocalAt(27))) { auto unpack25291 = Iterate(item25290); ValidateUnpack(unpack25291, 3, false); comp25288->SetAt(2, unpack25291.at(0)); comp25288->SetAt(0, unpack25291.at(1)); comp25288->SetAt(1, unpack25291.at(2)); if (!static_cast<bool>(([&]() -> Value { auto v25292 = ([&]() -> Value { auto v25293 = comp25288->LocalAt(0); Value v25294; v25294 = comp25288->Captured("i"); if (!static_cast<bool>(Binary("Eq", v25293, v25294))) return Value(false); v25293 = v25294; return Value(true); }()); if (!static_cast<bool>(v25292)) return v25292; v25292 = ([&]() -> Value { auto v25295 = comp25288->LocalAt(2); Value v25296; v25296 = comp25288->Captured("t"); if (!static_cast<bool>(Binary("Lt", v25295, v25296))) return Value(false); v25295 = v25296; return Value(true); }()); return v25292; }()))) continue; result25289.node()->sequence.push_back(Tuple({comp25288->LocalAt(2), comp25288->LocalAt(0), comp25288->LocalAt(1)})); } return result25289; }());
s->SetAt(6, v25287);
if (static_cast<bool>(Unary("Not", s->LocalAt(6)))) {
return Value{};
}
auto v25297 = Get(s->LocalAt(6), Unary("USub", Value(int64_t{1})));
auto unpack25298 = Iterate(v25297);
ValidateUnpack(unpack25298, 3, false);
s->SetAt(41, unpack25298.at(0));
s->SetAt(17, unpack25298.at(1));
s->SetAt(33, unpack25298.at(2));
auto v25299 = ([&]() -> Value { auto v25300 = ([&]() -> Value { auto fn25301 = PrepareDictionaryGet(Get(s->LocalAt(29), Value("pickups"))); Arguments args25302; args25302.positional.reserve(2); args25302.Add(Tuple({s->LocalAt(41), s->LocalAt(17)}), false); args25302.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn25301, std::move(args25302)); }()); return Binary("Add", v25300, Value(int64_t{1})); }());
Put(Get(s->LocalAt(29), Value("pickups")), Tuple({s->LocalAt(41), s->LocalAt(17)}), v25299);
auto v25303 = s->LocalAt(30);
Put(Get(s->LocalAt(29), Value("places")), Tuple({s->LocalAt(37), s->LocalAt(15)}), v25303);
}
for (const auto& item25304 : Iterate(([&]() -> Value { auto fn25305 = Attribute(Get(s->LocalAt(29), Value("pickups")), "items"); Arguments args25306; return Call(c, fn25305, std::move(args25306)); }()))) {
auto unpack25307 = Iterate(item25304);
ValidateUnpack(unpack25307, 2, false);
s->SetAt(19, unpack25307.at(0));
s->SetAt(22, unpack25307.at(1));
auto v25308 = ([&]() -> Value { auto comp25309 = std::make_shared<Scope>(); comp25309->globals = s->globals; comp25309->parent = s; static constexpr const char* comp25309_names[] = {"ip", "q", "tp"}; comp25309->PrepareSlots(comp25309_names); auto result25310 = List(); for (const auto& item25311 : Iterate(s->LocalAt(27))) { auto unpack25312 = Iterate(item25311); ValidateUnpack(unpack25312, 3, false); comp25309->SetAt(2, unpack25312.at(0)); comp25309->SetAt(0, unpack25312.at(1)); comp25309->SetAt(1, unpack25312.at(2)); if (!static_cast<bool>(([&]() -> Value { auto v25313 = Tuple({comp25309->LocalAt(2), comp25309->LocalAt(0)}); Value v25314; v25314 = comp25309->Captured("key"); if (!static_cast<bool>(Binary("Eq", v25313, v25314))) return Value(false); v25313 = v25314; return Value(true); }()))) continue; return comp25309->LocalAt(1); } throw Error("StopIteration", "generator exhausted"); }());
s->SetAt(33, v25308);
if (static_cast<bool>(([&]() -> Value { auto v25315 = s->LocalAt(33); Value v25316; v25316 = s->LocalAt(22); if (!static_cast<bool>(Binary("NotEq", v25315, v25316))) return Value(false); v25315 = v25316; return Value(true); }()))) {
return Value{};
}
}
return s->LocalAt(29);
return {};
}
}  // namespace kagg::opponents::compiled
