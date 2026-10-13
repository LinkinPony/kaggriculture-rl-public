// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_efe26f3dbdac8b874cd6(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"actual", "configuration", "farm", "hires", "native", "observation", "p", "player", "reserve", "result", "standard", "state", "step", "t", "x", "y"};
s->PrepareSlots(s_names);
auto v10934 = ([&]() -> Value { auto fn10935 = s->Global("_R124_PARENT"); Arguments args10936; args10936.positional.reserve(2); args10936.Add(s->LocalAt(5), false); args10936.Add(s->LocalAt(1), false); return Call(c, fn10935, std::move(args10936)); }());
s->SetAt(9, v10934);
try {
auto v10938 = ([&]() -> Value { auto fn10939 = s->Global("int"); Arguments args10940; args10940.Add(Get(s->LocalAt(5), Value("player")), false); return Call(c, fn10939, std::move(args10940)); }());
s->SetAt(7, v10938);
auto v10941 = ([&]() -> Value { auto fn10942 = s->Global("int"); Arguments args10943; args10943.Add(Get(s->LocalAt(5), Value("step")), false); return Call(c, fn10942, std::move(args10943)); }());
s->SetAt(12, v10941);
auto v10944 = ([&]() -> Value { auto fn10945 = PrepareDictionaryGet(s->Global("_R124_STATES")); Arguments args10946; args10946.Add(s->LocalAt(7), false); return CallDictionaryGet(c, fn10945, std::move(args10946)); }());
s->SetAt(11, v10944);
if (static_cast<bool>(([&]() -> Value { auto v10947 = ([&]() -> Value { auto v10948 = s->LocalAt(11); Value v10949; v10949 = Value{}; if (!static_cast<bool>(Binary("Is", v10948, v10949))) return Value(false); v10948 = v10949; return Value(true); }()); if (static_cast<bool>(v10947)) return v10947; v10947 = ([&]() -> Value { auto v10950 = s->LocalAt(12); Value v10951; v10951 = Get(s->LocalAt(11), Value("step")); if (!static_cast<bool>(Binary("LtE", v10950, v10951))) return Value(false); v10950 = v10951; return Value(true); }()); return v10947; }()))) {
auto v10952 = ([&]() -> Value { auto dict10953 = Dict(); auto key10954 = Value("step"); Put(dict10953, key10954, Unary("USub", Value(int64_t{1}))); auto key10955 = Value("pending_plants"); Put(dict10953, key10955, List({})); return dict10953; }());
s->SetAt(11, v10952);
Put(s->Global("_R124_STATES"), s->LocalAt(7), v10952);
(void)([&]() -> Value { auto fn10956 = Attribute(s->Global("_R124_REPORT"), "update"); Arguments args10957; args10957.Keyword("opening_seed_budget_units", Value(int64_t{0})); args10957.Keyword("opening_seed_budget_cost", Value(int64_t{0})); args10957.Keyword("opening_atomic_dropped", Value(int64_t{0})); args10957.Keyword("opening_atomic_rescued_requests", Value(int64_t{0})); args10957.Keyword("opening_atomic_rescued_confirmed", Value(int64_t{0})); args10957.Keyword("opening_atomic_plant_errors", Value(int64_t{0})); args10957.Keyword("opening_day1_cash", Value(int64_t{0})); args10957.Keyword("opening_day1_hires_requested", Value(int64_t{0})); args10957.Keyword("opening_day1_hires_confirmed", Value(int64_t{0})); args10957.Keyword("opening_day1_hire_shortfalls", Value(int64_t{0})); args10957.Keyword("opening_contract_errors", Value(int64_t{0})); return Call(c, fn10956, std::move(args10957)); }());
}
auto v10958 = s->LocalAt(12);
Put(s->LocalAt(11), Value("step"), v10958);
auto v10959 = Get(Get(s->LocalAt(5), Value("farms")), s->LocalAt(7));
s->SetAt(2, v10959);
for (const auto& item10960 : Iterate(([&]() -> Value { auto fn10961 = Attribute(s->LocalAt(11), "pop"); Arguments args10962; args10962.positional.reserve(2); args10962.Add(Value("pending_plants"), false); args10962.Add(List({}), false); return Call(c, fn10961, std::move(args10962)); }()))) {
s->SetAt(6, item10960);
auto v10963 = Get(s->LocalAt(6), Value("xy"));
auto unpack10964 = Iterate(v10963);
ValidateUnpack(unpack10964, 2, false);
s->SetAt(14, unpack10964.at(0));
s->SetAt(15, unpack10964.at(1));
auto v10965 = Get(Get(Get(s->LocalAt(2), Value("tiles")), s->LocalAt(15)), s->LocalAt(14));
s->SetAt(13, v10965);
if (static_cast<bool>(([&]() -> Value { auto v10966 = ([&]() -> Value { auto fn10967 = s->Global("isinstance"); Arguments args10968; args10968.positional.reserve(2); args10968.Add(s->LocalAt(13), false); args10968.Add(s->Global("dict"), false); return Call(c, fn10967, std::move(args10968)); }()); if (!static_cast<bool>(v10966)) return v10966; v10966 = ([&]() -> Value { auto v10969 = ([&]() -> Value { auto fn10971 = PrepareDictionaryGet(s->LocalAt(13)); Arguments args10972; args10972.Add(Value("crop"), false); return CallDictionaryGet(c, fn10971, std::move(args10972)); }()); Value v10970; v10970 = Get(s->LocalAt(6), Value("crop")); if (!static_cast<bool>(Binary("Eq", v10969, v10970))) return Value(false); v10969 = v10970; return Value(true); }()); if (!static_cast<bool>(v10966)) return v10966; v10966 = ([&]() -> Value { auto v10973 = ([&]() -> Value { auto fn10975 = PrepareDictionaryGet(s->LocalAt(13)); Arguments args10976; args10976.Add(Value("planted_day"), false); return CallDictionaryGet(c, fn10975, std::move(args10976)); }()); Value v10974; v10974 = Get(s->LocalAt(6), Value("birth")); if (!static_cast<bool>(Binary("Eq", v10973, v10974))) return Value(false); v10973 = v10974; return Value(true); }()); return v10966; }()))) {
auto v10977 = s->Global("_R124_REPORT");
auto v10978 = Value("opening_atomic_rescued_confirmed");
auto v10979 = Get(v10977, v10978);
Put(v10977, v10978, Inplace("Add", v10979, Value(int64_t{1})));
}
else {
auto v10980 = s->Global("_R124_REPORT");
auto v10981 = Value("opening_atomic_plant_errors");
auto v10982 = Get(v10980, v10981);
Put(v10980, v10981, Inplace("Add", v10982, Value(int64_t{1})));
}
}
auto v10983 = ([&]() -> Value { auto v10984 = ([&]() -> Value { auto v10985 = s->LocalAt(1); Value v10986; v10986 = Value{}; if (!static_cast<bool>(Binary("Is", v10985, v10986))) return Value(false); v10985 = v10986; return Value(true); }()); if (static_cast<bool>(v10984)) return v10984; v10984 = ([&]() -> Value { auto comp10987 = std::make_shared<Scope>(); comp10987->globals = s->globals; comp10987->parent = s; static constexpr const char* comp10987_names[] = {"k", "v"}; comp10987->PrepareSlots(comp10987_names); auto result10988 = List(); for (const auto& item10989 : Iterate(List({Tuple({Value("boardSize"), Value(int64_t{10})}), Tuple({Value("turnsPerDay"), Value(int64_t{24})}), Tuple({Value("shedCapacity"), Value(int64_t{100})}), Tuple({Value("maxMarketOrdersPerTurn"), Value(int64_t{10})}), Tuple({Value("farmHandCostMult"), Value(int64_t{1})})}))) { auto unpack10990 = Iterate(item10989); ValidateUnpack(unpack10990, 2, false); comp10987->SetAt(0, unpack10990.at(0)); comp10987->SetAt(1, unpack10990.at(1)); if (!static_cast<bool>(([&]() -> Value { auto v10991 = ([&]() -> Value { auto fn10993 = PrepareDictionaryGet(comp10987->Captured("configuration")); Arguments args10994; args10994.positional.reserve(2); args10994.Add(comp10987->LocalAt(0), false); args10994.Add(comp10987->LocalAt(1), false); return CallDictionaryGet(c, fn10993, std::move(args10994)); }()); Value v10992; v10992 = comp10987->LocalAt(1); if (!static_cast<bool>(Binary("Eq", v10991, v10992))) return Value(false); v10991 = v10992; return Value(true); }()))) return Value(false); } return Value(true); }()); return v10984; }());
s->SetAt(10, v10983);
if (static_cast<bool>(([&]() -> Value { auto v10995 = s->LocalAt(10); if (!static_cast<bool>(v10995)) return v10995; v10995 = ([&]() -> Value { auto v10996 = Value(int64_t{0}); Value v10997; v10997 = s->LocalAt(12); if (!static_cast<bool>(Binary("LtE", v10996, v10997))) return Value(false); v10996 = v10997; v10997 = Value(int64_t{24}); if (!static_cast<bool>(Binary("Lt", v10996, v10997))) return Value(false); v10996 = v10997; return Value(true); }()); return v10995; }()))) {
auto v10998 = Get(s->Global("_ROUTES"), Get(Get(Attribute(Attribute(s->Global("_IMPL"), "chassis"), "players"), s->LocalAt(7)), Value("route")));
s->SetAt(4, v10998);
auto v10999 = ([&]() -> Value { auto fn11000 = s->Global("_r124_labor_reserve"); Arguments args11001; args11001.Add(s->LocalAt(4), false); return Call(c, fn11000, std::move(args11001)); }());
auto unpack11002 = Iterate(v10999);
ValidateUnpack(unpack11002, 2, false);
s->SetAt(8, unpack11002.at(0));
s->SetAt(3, unpack11002.at(1));
auto v11003 = ([&]() -> Value { auto fn11004 = s->Global("_r124_seed_budget"); Arguments args11005; args11005.positional.reserve(3); args11005.Add(s->LocalAt(5), false); args11005.Add(s->LocalAt(9), false); args11005.Add(s->LocalAt(8), false); return Call(c, fn11004, std::move(args11005)); }());
s->SetAt(9, v11003);
auto v11006 = ([&]() -> Value { auto fn11007 = s->Global("_r124_atomic"); Arguments args11008; args11008.positional.reserve(3); args11008.Add(s->LocalAt(5), false); args11008.Add(s->LocalAt(9), false); args11008.Add(s->LocalAt(11), false); return Call(c, fn11007, std::move(args11008)); }());
s->SetAt(9, v11006);
}
if (static_cast<bool>(([&]() -> Value { auto v11009 = s->LocalAt(12); Value v11010; v11010 = Value(int64_t{24}); if (!static_cast<bool>(Binary("Eq", v11009, v11010))) return Value(false); v11009 = v11010; return Value(true); }()))) {
auto v11011 = Get(s->LocalAt(2), Value("money"));
Put(s->Global("_R124_REPORT"), Value("opening_day1_cash"), v11011);
auto v11012 = ([&]() -> Value { auto fn11013 = s->Global("sum"); Arguments args11014; args11014.Add(([&]() -> Value { auto comp11015 = std::make_shared<Scope>(); comp11015->globals = s->globals; comp11015->parent = s; static constexpr const char* comp11015_names[] = {"o"}; comp11015->PrepareSlots(comp11015_names); auto result11016 = List(); for (const auto& item11017 : Iterate(([&]() -> Value { auto fn11018 = PrepareDictionaryGet(s->LocalAt(9)); Arguments args11019; args11019.positional.reserve(2); args11019.Add(Value("market"), false); args11019.Add(List({}), false); return CallDictionaryGet(c, fn11018, std::move(args11019)); }()))) { comp11015->SetAt(0, item11017); result11016.node()->sequence.push_back(([&]() -> Value { auto v11020 = ([&]() -> Value { auto fn11021 = comp11015->Global("bool"); Arguments args11022; args11022.Add(comp11015->LocalAt(0), false); return Call(c, fn11021, std::move(args11022)); }()); if (!static_cast<bool>(v11020)) return v11020; v11020 = ([&]() -> Value { auto v11023 = Get(comp11015->LocalAt(0), Value(int64_t{0})); Value v11024; v11024 = Value("HIRE"); if (!static_cast<bool>(Binary("Eq", v11023, v11024))) return Value(false); v11023 = v11024; return Value(true); }()); return v11020; }())); } return result11016; }()), false); return Call(c, fn11013, std::move(args11014)); }());
Put(s->LocalAt(11), Value("hires"), v11012);
auto v11025 = Get(s->LocalAt(11), Value("hires"));
Put(s->Global("_R124_REPORT"), Value("opening_day1_hires_requested"), v11025);
}
if (static_cast<bool>(([&]() -> Value { auto v11026 = s->LocalAt(12); Value v11027; v11027 = Value(int64_t{25}); if (!static_cast<bool>(Binary("Eq", v11026, v11027))) return Value(false); v11026 = v11027; return Value(true); }()))) {
auto v11028 = ([&]() -> Value { auto fn11029 = s->Global("len"); Arguments args11030; args11030.Add(Get(s->LocalAt(2), Value("hands")), false); return Call(c, fn11029, std::move(args11030)); }());
s->SetAt(0, v11028);
auto v11031 = s->LocalAt(0);
Put(s->Global("_R124_REPORT"), Value("opening_day1_hires_confirmed"), v11031);
auto v11032 = ([&]() -> Value { auto fn11033 = s->Global("max"); Arguments args11034; args11034.positional.reserve(2); args11034.Add(Value(int64_t{0}), false); args11034.Add(([&]() -> Value { auto v11035 = ([&]() -> Value { auto fn11036 = PrepareDictionaryGet(s->LocalAt(11)); Arguments args11037; args11037.positional.reserve(2); args11037.Add(Value("hires"), false); args11037.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn11036, std::move(args11037)); }()); return Binary("Sub", v11035, s->LocalAt(0)); }()), false); return Call(c, fn11033, std::move(args11034)); }());
Put(s->Global("_R124_REPORT"), Value("opening_day1_hire_shortfalls"), v11032);
}
} catch (const Error& error10937) {
if (Matches(error10937, s->Global("Exception"))) {
auto v11038 = ([&]() -> Value { auto v11039 = ([&]() -> Value { auto fn11040 = PrepareDictionaryGet(s->Global("_R124_REPORT")); Arguments args11041; args11041.positional.reserve(2); args11041.Add(Value("opening_contract_errors"), false); args11041.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn11040, std::move(args11041)); }()); return Binary("Add", v11039, Value(int64_t{1})); }());
Put(s->Global("_R124_REPORT"), Value("opening_contract_errors"), v11038);
}
else { throw; }
}
(void)([&]() -> Value { auto fn11042 = Attribute(s->Global("_R124_REPORT"), "update"); Arguments args11043; args11043.Add(([&]() -> Value { auto fn11044 = s->Global("getattr"); Arguments args11045; args11045.positional.reserve(3); args11045.Add(s->Global("_R124_PARENT"), false); args11045.Add(Value("telemetry"), false); args11045.Add(([&]() -> Value { auto dict11046 = Dict(); return dict11046; }()), false); return Call(c, fn11044, std::move(args11045)); }()), false); return Call(c, fn11042, std::move(args11043)); }());
return s->LocalAt(9);
return {};
}
}  // namespace kagg::opponents::compiled
