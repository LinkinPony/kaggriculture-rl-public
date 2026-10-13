// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_ae993816da07a6165a92(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "configuration", "observation", "player", "snapshot", "standard", "state", "step"};
s->PrepareSlots(s_names);
auto v13126 = Value{};
s->SetAt(6, v13126);
try {
auto v13128 = ([&]() -> Value { auto fn13129 = s->Global("int"); Arguments args13130; args13130.Add(Get(s->LocalAt(2), Value("player")), false); return Call(c, fn13129, std::move(args13130)); }());
s->SetAt(3, v13128);
auto v13131 = ([&]() -> Value { auto fn13132 = s->Global("int"); Arguments args13133; args13133.Add(Get(s->LocalAt(2), Value("step")), false); return Call(c, fn13132, std::move(args13133)); }());
s->SetAt(7, v13131);
auto v13134 = ([&]() -> Value { auto fn13135 = PrepareDictionaryGet(s->Global("_RACE_STATE")); Arguments args13136; args13136.Add(s->LocalAt(3), false); return CallDictionaryGet(c, fn13135, std::move(args13136)); }());
s->SetAt(6, v13134);
if (static_cast<bool>(([&]() -> Value { auto v13137 = ([&]() -> Value { auto v13138 = s->LocalAt(6); Value v13139; v13139 = Value{}; if (!static_cast<bool>(Binary("Is", v13138, v13139))) return Value(false); v13138 = v13139; return Value(true); }()); if (static_cast<bool>(v13137)) return v13137; v13137 = ([&]() -> Value { auto v13140 = s->LocalAt(7); Value v13141; v13141 = Get(s->LocalAt(6), Value("step")); if (!static_cast<bool>(Binary("LtE", v13140, v13141))) return Value(false); v13140 = v13141; return Value(true); }()); return v13137; }()))) {
auto v13142 = ([&]() -> Value { auto dict13143 = Dict(); auto key13144 = Value("step"); Put(dict13143, key13144, Unary("USub", Value(int64_t{1}))); auto key13145 = Value("hist"); Put(dict13143, key13145, List({})); auto key13146 = Value("horizon"); Put(dict13143, key13146, Value(int64_t{0})); auto key13147 = Value("level"); Put(dict13143, key13147, s->Global("_RACE_HORIZON_CLONE")); auto key13148 = Value("prev"); Put(dict13143, key13148, Value{}); auto key13149 = Value("prev_action"); Put(dict13143, key13149, Value{}); return dict13143; }());
s->SetAt(6, v13142);
Put(s->Global("_RACE_STATE"), s->LocalAt(3), v13142);
}
if (static_cast<bool>(([&]() -> Value { auto v13150 = s->LocalAt(7); Value v13151; v13151 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v13150, v13151))) return Value(false); v13150 = v13151; return Value(true); }()))) {
(void)([&]() -> Value { auto fn13152 = Attribute(s->Global("_RACE_REPORT"), "update"); Arguments args13153; args13153.Keyword("race_clone_turns", Value(int64_t{0})); args13153.Keyword("race_horizon_turns", Value(int64_t{0})); args13153.Keyword("race_lost_races", Value(int64_t{0})); args13153.Keyword("race_escalations", Value(int64_t{0})); args13153.Keyword("race_errors", Value(int64_t{0})); return Call(c, fn13152, std::move(args13153)); }());
}
auto v13154 = s->LocalAt(7);
Put(s->LocalAt(6), Value("step"), v13154);
auto v13155 = Value(int64_t{0});
Put(s->LocalAt(6), Value("horizon"), v13155);
auto v13156 = ([&]() -> Value { auto v13157 = ([&]() -> Value { auto v13158 = s->LocalAt(1); Value v13159; v13159 = Value{}; if (!static_cast<bool>(Binary("Is", v13158, v13159))) return Value(false); v13158 = v13159; return Value(true); }()); if (static_cast<bool>(v13157)) return v13157; v13157 = ([&]() -> Value { auto comp13160 = std::make_shared<Scope>(); comp13160->globals = s->globals; comp13160->parent = s; static constexpr const char* comp13160_names[] = {"k", "v"}; comp13160->PrepareSlots(comp13160_names); auto result13161 = List(); for (const auto& item13162 : Iterate(List({Tuple({Value("boardSize"), Value(int64_t{10})}), Tuple({Value("turnsPerDay"), Value(int64_t{24})}), Tuple({Value("shedCapacity"), Value(int64_t{100})}), Tuple({Value("maxMarketOrdersPerTurn"), Value(int64_t{10})})}))) { auto unpack13163 = Iterate(item13162); ValidateUnpack(unpack13163, 2, false); comp13160->SetAt(0, unpack13163.at(0)); comp13160->SetAt(1, unpack13163.at(1)); if (!static_cast<bool>(([&]() -> Value { auto v13164 = ([&]() -> Value { auto fn13166 = PrepareDictionaryGet(comp13160->Captured("configuration")); Arguments args13167; args13167.positional.reserve(2); args13167.Add(comp13160->LocalAt(0), false); args13167.Add(comp13160->LocalAt(1), false); return CallDictionaryGet(c, fn13166, std::move(args13167)); }()); Value v13165; v13165 = comp13160->LocalAt(1); if (!static_cast<bool>(Binary("Eq", v13164, v13165))) return Value(false); v13164 = v13165; return Value(true); }()))) return Value(false); } return Value(true); }()); return v13157; }());
s->SetAt(5, v13156);
if (static_cast<bool>(([&]() -> Value { auto v13168 = s->LocalAt(5); if (!static_cast<bool>(v13168)) return v13168; v13168 = ([&]() -> Value { auto v13169 = Value(int64_t{216}); Value v13170; v13170 = s->LocalAt(7); if (!static_cast<bool>(Binary("LtE", v13169, v13170))) return Value(false); v13169 = v13170; v13170 = Value(int64_t{696}); if (!static_cast<bool>(Binary("Lt", v13169, v13170))) return Value(false); v13169 = v13170; return Value(true); }()); if (!static_cast<bool>(v13168)) return v13168; v13168 = ([&]() -> Value { auto fn13171 = s->Global("_race_clone"); Arguments args13172; args13172.positional.reserve(2); args13172.Add(s->LocalAt(2), false); args13172.Add(s->LocalAt(6), false); return Call(c, fn13171, std::move(args13172)); }()); return v13168; }()))) {
auto v13173 = s->Global("_RACE_REPORT");
auto v13174 = Value("race_clone_turns");
auto v13175 = Get(v13173, v13174);
Put(v13173, v13174, Inplace("Add", v13175, Value(int64_t{1})));
if (static_cast<bool>(([&]() -> Value { auto v13176 = ([&]() -> Value { auto v13177 = Get(s->LocalAt(6), Value("level")); Value v13178; v13178 = s->Global("_RACE_HORIZON_ESCALATED"); if (!static_cast<bool>(Binary("Lt", v13177, v13178))) return Value(false); v13177 = v13178; return Value(true); }()); if (!static_cast<bool>(v13176)) return v13176; v13176 = ([&]() -> Value { auto fn13179 = s->Global("_race_lost"); Arguments args13180; args13180.positional.reserve(2); args13180.Add(s->LocalAt(2), false); args13180.Add(s->LocalAt(6), false); return Call(c, fn13179, std::move(args13180)); }()); return v13176; }()))) {
auto v13181 = s->Global("_RACE_REPORT");
auto v13182 = Value("race_lost_races");
auto v13183 = Get(v13181, v13182);
Put(v13181, v13182, Inplace("Add", v13183, Value(int64_t{1})));
auto v13184 = s->Global("_RACE_HORIZON_ESCALATED");
Put(s->LocalAt(6), Value("level"), v13184);
auto v13185 = s->Global("_RACE_REPORT");
auto v13186 = Value("race_escalations");
auto v13187 = Get(v13185, v13186);
Put(v13185, v13186, Inplace("Add", v13187, Value(int64_t{1})));
}
auto v13188 = Get(s->LocalAt(6), Value("level"));
Put(s->LocalAt(6), Value("horizon"), v13188);
auto v13189 = s->Global("_RACE_REPORT");
auto v13190 = Value("race_horizon_turns");
auto v13191 = Get(v13189, v13190);
Put(v13189, v13190, Inplace("Add", v13191, Value(int64_t{1})));
}
} catch (const Error& error13127) {
if (Matches(error13127, s->Global("Exception"))) {
auto v13192 = s->Global("_RACE_REPORT");
auto v13193 = Value("race_errors");
auto v13194 = Get(v13192, v13193);
Put(v13192, v13193, Inplace("Add", v13194, Value(int64_t{1})));
}
else { throw; }
}
auto v13195 = Value{};
s->SetAt(4, v13195);
try {
if (static_cast<bool>(([&]() -> Value { auto v13197 = ([&]() -> Value { auto v13198 = s->LocalAt(6); Value v13199; v13199 = Value{}; if (!static_cast<bool>(Binary("IsNot", v13198, v13199))) return Value(false); v13198 = v13199; return Value(true); }()); if (!static_cast<bool>(v13197)) return v13197; v13197 = ([&]() -> Value { auto v13200 = Value(int64_t{215}); Value v13201; v13201 = ([&]() -> Value { auto fn13202 = s->Global("int"); Arguments args13203; args13203.Add(Get(s->LocalAt(2), Value("step")), false); return Call(c, fn13202, std::move(args13203)); }()); if (!static_cast<bool>(Binary("LtE", v13200, v13201))) return Value(false); v13200 = v13201; v13201 = Value(int64_t{696}); if (!static_cast<bool>(Binary("Lt", v13200, v13201))) return Value(false); v13200 = v13201; return Value(true); }()); return v13197; }()))) {
auto v13204 = ([&]() -> Value { auto fn13205 = s->Global("_race_snapshot"); Arguments args13206; args13206.Add(s->LocalAt(2), false); return Call(c, fn13205, std::move(args13206)); }());
s->SetAt(4, v13204);
}
} catch (const Error& error13196) {
if (Matches(error13196, s->Global("Exception"))) {
auto v13207 = s->Global("_RACE_REPORT");
auto v13208 = Value("race_errors");
auto v13209 = Get(v13207, v13208);
Put(v13207, v13208, Inplace("Add", v13209, Value(int64_t{1})));
}
else { throw; }
}
auto v13210 = ([&]() -> Value { auto fn13211 = s->Global("_RACE_PARENT"); Arguments args13212; args13212.positional.reserve(2); args13212.Add(s->LocalAt(2), false); args13212.Add(s->LocalAt(1), false); return Call(c, fn13211, std::move(args13212)); }());
s->SetAt(0, v13210);
try {
if (static_cast<bool>(([&]() -> Value { auto v13214 = s->LocalAt(6); Value v13215; v13215 = Value{}; if (!static_cast<bool>(Binary("IsNot", v13214, v13215))) return Value(false); v13214 = v13215; return Value(true); }()))) {
auto v13216 = s->LocalAt(4);
Put(s->LocalAt(6), Value("prev"), v13216);
auto v13217 = (static_cast<bool>(([&]() -> Value { auto v13218 = s->LocalAt(4); Value v13219; v13219 = Value{}; if (!static_cast<bool>(Binary("IsNot", v13218, v13219))) return Value(false); v13218 = v13219; return Value(true); }())) ? s->LocalAt(0) : Value{});
Put(s->LocalAt(6), Value("prev_action"), v13217);
}
} catch (const Error& error13213) {
if (Matches(error13213, s->Global("Exception"))) {
auto v13220 = s->Global("_RACE_REPORT");
auto v13221 = Value("race_errors");
auto v13222 = Get(v13220, v13221);
Put(v13220, v13221, Inplace("Add", v13222, Value(int64_t{1})));
}
else { throw; }
}
(void)([&]() -> Value { auto fn13223 = Attribute(s->Global("_RACE_REPORT"), "update"); Arguments args13224; args13224.Add(([&]() -> Value { auto fn13225 = s->Global("getattr"); Arguments args13226; args13226.positional.reserve(3); args13226.Add(s->Global("_RACE_PARENT"), false); args13226.Add(Value("telemetry"), false); args13226.Add(([&]() -> Value { auto dict13227 = Dict(); return dict13227; }()), false); return Call(c, fn13225, std::move(args13226)); }()), false); return Call(c, fn13223, std::move(args13224)); }());
return s->LocalAt(0);
return {};
}
}  // namespace kagg::opponents::compiled
