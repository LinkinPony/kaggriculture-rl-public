// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_07b72a273de4fe219166(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"act", "action", "c", "cands", "cap", "carried", "cmd", "configuration", "farm", "got", "held", "i", "inv", "item", "k", "left", "market", "need", "night_shed", "o", "observation", "op", "overflow", "pos", "price", "prices", "priv", "proj", "q", "seat", "sold_now", "spare", "step", "t", "tile", "units", "view"};
s->PrepareSlots(s_names);
auto v23839 = ([&]() -> Value { auto fn23840 = s->Global("_SR_PARENT"); Arguments args23841; args23841.positional.reserve(2); args23841.Add(s->LocalAt(20), false); args23841.Add(s->LocalAt(7), false); return Call(c, fn23840, std::move(args23841)); }());
s->SetAt(1, v23839);
try {
auto v23843 = ([&]() -> Value { auto fn23844 = s->Global("int"); Arguments args23845; args23845.Add(Get(s->LocalAt(20), Value("step")), false); return Call(c, fn23844, std::move(args23845)); }());
s->SetAt(32, v23843);
if (static_cast<bool>(([&]() -> Value { auto v23846 = s->LocalAt(32); Value v23847; v23847 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v23846, v23847))) return Value(false); v23846 = v23847; return Value(true); }()))) {
for (const auto& item23848 : Iterate(s->Global("_SR_REPORT"))) {
s->SetAt(14, item23848);
auto v23849 = Value(int64_t{0});
Put(s->Global("_SR_REPORT"), s->LocalAt(14), v23849);
}
}
if (static_cast<bool>(([&]() -> Value { auto v23850 = ([&]() -> Value { auto v23851 = ([&]() -> Value { auto v23853 = s->LocalAt(32); return Binary("Mod", v23853, Value(int64_t{24})); }()); Value v23852; v23852 = s->Global("_SR_HOURS"); if (!static_cast<bool>(Binary("NotIn", v23851, v23852))) return Value(false); v23851 = v23852; return Value(true); }()); if (static_cast<bool>(v23850)) return v23850; v23850 = ([&]() -> Value { auto v23854 = s->LocalAt(32); Value v23855; v23855 = Value(int64_t{717}); if (!static_cast<bool>(Binary("GtE", v23854, v23855))) return Value(false); v23854 = v23855; return Value(true); }()); if (static_cast<bool>(v23850)) return v23850; v23850 = Unary("Not", ([&]() -> Value { auto fn23856 = s->Global("isinstance"); Arguments args23857; args23857.positional.reserve(2); args23857.Add(s->LocalAt(1), false); args23857.Add(s->Global("dict"), false); return Call(c, fn23856, std::move(args23857)); }())); return v23850; }()))) {
return s->LocalAt(1);
}
auto v23858 = ([&]() -> Value { auto fn23859 = s->Global("int"); Arguments args23860; args23860.Add(Get(s->LocalAt(20), Value("player")), false); return Call(c, fn23859, std::move(args23860)); }());
s->SetAt(29, v23858);
auto v23861 = Get(Get(s->LocalAt(20), Value("farms")), s->LocalAt(29));
s->SetAt(8, v23861);
auto v23862 = Get(s->LocalAt(20), Value("private"));
s->SetAt(26, v23862);
auto v23863 = ([&]() -> Value { auto fn23864 = s->Global("FarmView"); Arguments args23865; args23865.Add(s->LocalAt(20), false); return Call(c, fn23864, std::move(args23865)); }());
s->SetAt(36, v23863);
auto v23866 = ([&]() -> Value { auto fn23867 = s->Global("dict"); Arguments args23868; args23868.Add(([&]() -> Value { auto fn23869 = s->Global("projected_shed"); Arguments args23870; args23870.positional.reserve(2); args23870.Add(s->LocalAt(1), false); args23870.Add(s->LocalAt(36), false); return Call(c, fn23869, std::move(args23870)); }()), false); return Call(c, fn23867, std::move(args23868)); }());
s->SetAt(27, v23866);
auto v23871 = ([&]() -> Value { auto comp23872 = std::make_shared<Scope>(); comp23872->globals = s->globals; comp23872->parent = s; static constexpr const char* comp23872_names[] = {"o"}; comp23872->PrepareSlots(comp23872_names); auto result23873 = List(); for (const auto& item23874 : Iterate(([&]() -> Value { auto v23875 = ([&]() -> Value { auto fn23876 = PrepareDictionaryGet(s->LocalAt(1)); Arguments args23877; args23877.Add(Value("market"), false); return CallDictionaryGet(c, fn23876, std::move(args23877)); }()); if (static_cast<bool>(v23875)) return v23875; v23875 = List({}); return v23875; }()))) { comp23872->SetAt(0, item23874); result23873.node()->sequence.push_back(([&]() -> Value { auto fn23878 = comp23872->Global("list"); Arguments args23879; args23879.Add(comp23872->LocalAt(0), false); return Call(c, fn23878, std::move(args23879)); }())); } return result23873; }());
s->SetAt(16, v23871);
auto v23880 = ([&]() -> Value { auto fn23881 = s->Global("dict"); Arguments args23882; args23882.Add(s->LocalAt(27), false); return Call(c, fn23881, std::move(args23882)); }());
s->SetAt(15, v23880);
auto v23883 = ([&]() -> Value { auto fn23884 = s->Global("sum"); Arguments args23885; args23885.Add(([&]() -> Value { auto comp23886 = std::make_shared<Scope>(); comp23886->globals = s->globals; comp23886->parent = s; static constexpr const char* comp23886_names[] = {"v"}; comp23886->PrepareSlots(comp23886_names); auto result23887 = List(); for (const auto& item23888 : Iterate(([&]() -> Value { auto fn23889 = Attribute(s->LocalAt(27), "values"); Arguments args23890; return Call(c, fn23889, std::move(args23890)); }()))) { comp23886->SetAt(0, item23888); result23887.node()->sequence.push_back(([&]() -> Value { auto fn23891 = comp23886->Global("max"); Arguments args23892; args23892.positional.reserve(2); args23892.Add(Value(int64_t{0}), false); args23892.Add(([&]() -> Value { auto fn23893 = comp23886->Global("int"); Arguments args23894; args23894.Add(comp23886->LocalAt(0), false); return Call(c, fn23893, std::move(args23894)); }()), false); return Call(c, fn23891, std::move(args23892)); }())); } return result23887; }()), false); return Call(c, fn23884, std::move(args23885)); }());
s->SetAt(18, v23883);
for (const auto& item23895 : Iterate(s->LocalAt(16))) {
s->SetAt(19, item23895);
if (static_cast<bool>(([&]() -> Value { auto v23896 = ([&]() -> Value { auto v23897 = ([&]() -> Value { auto fn23899 = s->Global("len"); Arguments args23900; args23900.Add(s->LocalAt(19), false); return Call(c, fn23899, std::move(args23900)); }()); Value v23898; v23898 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v23897, v23898))) return Value(false); v23897 = v23898; return Value(true); }()); if (!static_cast<bool>(v23896)) return v23896; v23896 = ([&]() -> Value { auto v23901 = Get(s->LocalAt(19), Value(int64_t{0})); Value v23902; v23902 = Value("SELL"); if (!static_cast<bool>(Binary("Eq", v23901, v23902))) return Value(false); v23901 = v23902; return Value(true); }()); return v23896; }()))) {
auto v23903 = ([&]() -> Value { auto fn23904 = s->Global("min"); Arguments args23905; args23905.positional.reserve(2); args23905.Add(([&]() -> Value { auto fn23906 = s->Global("max"); Arguments args23907; args23907.positional.reserve(2); args23907.Add(Value(int64_t{0}), false); args23907.Add(([&]() -> Value { auto fn23908 = s->Global("int"); Arguments args23909; args23909.Add(Get(s->LocalAt(19), Value(int64_t{2})), false); return Call(c, fn23908, std::move(args23909)); }()), false); return Call(c, fn23906, std::move(args23907)); }()), false); args23905.Add(([&]() -> Value { auto fn23910 = s->Global("max"); Arguments args23911; args23911.positional.reserve(2); args23911.Add(Value(int64_t{0}), false); args23911.Add(([&]() -> Value { auto fn23912 = s->Global("int"); Arguments args23913; args23913.Add(([&]() -> Value { auto fn23914 = PrepareDictionaryGet(s->LocalAt(15)); Arguments args23915; args23915.positional.reserve(2); args23915.Add(Get(s->LocalAt(19), Value(int64_t{1})), false); args23915.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn23914, std::move(args23915)); }()), false); return Call(c, fn23912, std::move(args23913)); }()), false); return Call(c, fn23910, std::move(args23911)); }()), false); return Call(c, fn23904, std::move(args23905)); }());
s->SetAt(9, v23903);
auto v23916 = ([&]() -> Value { auto v23917 = ([&]() -> Value { auto fn23918 = PrepareDictionaryGet(s->LocalAt(15)); Arguments args23919; args23919.positional.reserve(2); args23919.Add(Get(s->LocalAt(19), Value(int64_t{1})), false); args23919.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn23918, std::move(args23919)); }()); return Binary("Sub", v23917, s->LocalAt(9)); }());
Put(s->LocalAt(15), Get(s->LocalAt(19), Value(int64_t{1})), v23916);
auto v23920 = s->LocalAt(18);
s->SetAt(18, Inplace("Sub", v23920, s->LocalAt(9)));
}
else {
if (static_cast<bool>(([&]() -> Value { auto v23921 = ([&]() -> Value { auto v23922 = ([&]() -> Value { auto fn23924 = s->Global("len"); Arguments args23925; args23925.Add(s->LocalAt(19), false); return Call(c, fn23924, std::move(args23925)); }()); Value v23923; v23923 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v23922, v23923))) return Value(false); v23922 = v23923; return Value(true); }()); if (!static_cast<bool>(v23921)) return v23921; v23921 = ([&]() -> Value { auto v23926 = Get(s->LocalAt(19), Value(int64_t{0})); Value v23927; v23927 = Tuple({Value("BUY_PRODUCT"), Value("BUY_ANIMAL")}); if (!static_cast<bool>(Binary("In", v23926, v23927))) return Value(false); v23926 = v23927; return Value(true); }()); return v23921; }()))) {
auto v23928 = s->LocalAt(18);
s->SetAt(18, Inplace("Add", v23928, ([&]() -> Value { auto fn23929 = s->Global("max"); Arguments args23930; args23930.positional.reserve(2); args23930.Add(Value(int64_t{0}), false); args23930.Add(([&]() -> Value { auto fn23931 = s->Global("int"); Arguments args23932; args23932.Add(Get(s->LocalAt(19), Value(int64_t{2})), false); return Call(c, fn23931, std::move(args23932)); }()), false); return Call(c, fn23929, std::move(args23930)); }())));
}
}
}
auto v23933 = ([&]() -> Value { auto v23934 = List({([&]() -> Value { auto v23935 = ([&]() -> Value { auto fn23936 = PrepareDictionaryGet(s->LocalAt(1)); Arguments args23937; args23937.Add(Value("farmer"), false); return CallDictionaryGet(c, fn23936, std::move(args23937)); }()); if (static_cast<bool>(v23935)) return v23935; v23935 = List({Value("PASS")}); return v23935; }())}); return Binary("Add", v23934, ([&]() -> Value { auto fn23938 = s->Global("list"); Arguments args23939; args23939.Add(([&]() -> Value { auto v23940 = ([&]() -> Value { auto fn23941 = PrepareDictionaryGet(s->LocalAt(1)); Arguments args23942; args23942.Add(Value("hands"), false); return CallDictionaryGet(c, fn23941, std::move(args23942)); }()); if (static_cast<bool>(v23940)) return v23940; v23940 = List({}); return v23940; }()), false); return Call(c, fn23938, std::move(args23939)); }())); }());
s->SetAt(35, v23933);
auto v23943 = Value(int64_t{0});
s->SetAt(5, v23943);
for (const auto& item23944 : Iterate(([&]() -> Value { auto fn23945 = s->Global("enumerate"); Arguments args23946; args23946.Add(Attribute(s->LocalAt(36), "positions"), false); return Call(c, fn23945, std::move(args23946)); }()))) {
auto unpack23947 = Iterate(item23944);
ValidateUnpack(unpack23947, 2, false);
s->SetAt(11, unpack23947.at(0));
s->SetAt(23, unpack23947.at(1));
auto v23948 = (static_cast<bool>(([&]() -> Value { auto v23949 = s->LocalAt(11); Value v23950; v23950 = ([&]() -> Value { auto fn23951 = s->Global("len"); Arguments args23952; args23952.Add(Get(s->LocalAt(26), Value("inventories")), false); return Call(c, fn23951, std::move(args23952)); }()); if (!static_cast<bool>(Binary("Lt", v23949, v23950))) return Value(false); v23949 = v23950; return Value(true); }())) ? Get(Get(s->LocalAt(26), Value("inventories")), s->LocalAt(11)) : ([&]() -> Value { auto dict23953 = Dict(); return dict23953; }()));
s->SetAt(12, v23948);
auto v23954 = ([&]() -> Value { auto fn23955 = s->Global("sum"); Arguments args23956; args23956.Add(([&]() -> Value { auto comp23957 = std::make_shared<Scope>(); comp23957->globals = s->globals; comp23957->parent = s; static constexpr const char* comp23957_names[] = {"v"}; comp23957->PrepareSlots(comp23957_names); auto result23958 = List(); for (const auto& item23959 : Iterate(([&]() -> Value { auto fn23960 = Attribute(s->LocalAt(12), "values"); Arguments args23961; return Call(c, fn23960, std::move(args23961)); }()))) { comp23957->SetAt(0, item23959); result23958.node()->sequence.push_back(([&]() -> Value { auto fn23962 = comp23957->Global("max"); Arguments args23963; args23963.positional.reserve(2); args23963.Add(Value(int64_t{0}), false); args23963.Add(([&]() -> Value { auto fn23964 = comp23957->Global("int"); Arguments args23965; args23965.Add(comp23957->LocalAt(0), false); return Call(c, fn23964, std::move(args23965)); }()), false); return Call(c, fn23962, std::move(args23963)); }())); } return result23958; }()), false); return Call(c, fn23955, std::move(args23956)); }());
s->SetAt(10, v23954);
auto v23966 = (static_cast<bool>(([&]() -> Value { auto v23967 = ([&]() -> Value { auto v23968 = s->LocalAt(11); Value v23969; v23969 = ([&]() -> Value { auto fn23970 = s->Global("len"); Arguments args23971; args23971.Add(s->LocalAt(35), false); return Call(c, fn23970, std::move(args23971)); }()); if (!static_cast<bool>(Binary("Lt", v23968, v23969))) return Value(false); v23968 = v23969; return Value(true); }()); if (!static_cast<bool>(v23967)) return v23967; v23967 = Get(s->LocalAt(35), s->LocalAt(11)); return v23967; }())) ? Get(s->LocalAt(35), s->LocalAt(11)) : List({Value("PASS")}));
s->SetAt(6, v23966);
auto v23972 = (static_cast<bool>(([&]() -> Value { auto fn23973 = s->Global("isinstance"); Arguments args23974; args23974.positional.reserve(2); args23974.Add(s->LocalAt(23), false); args23974.Add(Tuple({s->Global("list"), s->Global("tuple")}), false); return Call(c, fn23973, std::move(args23974)); }())) ? Get(Get(Get(s->LocalAt(8), Value("tiles")), Get(s->LocalAt(23), Value(int64_t{1}))), Get(s->LocalAt(23), Value(int64_t{0}))) : Value{});
s->SetAt(34, v23972);
auto v23975 = Get(s->LocalAt(6), Value(int64_t{0}));
s->SetAt(21, v23975);
if (static_cast<bool>(([&]() -> Value { auto v23976 = ([&]() -> Value { auto v23977 = s->LocalAt(21); Value v23978; v23978 = Value("DROP"); if (!static_cast<bool>(Binary("Eq", v23977, v23978))) return Value(false); v23977 = v23978; return Value(true); }()); if (!static_cast<bool>(v23976)) return v23976; v23976 = ([&]() -> Value { auto fn23979 = s->Global("_shed_adjacent"); Arguments args23980; args23980.positional.reserve(2); args23980.Add(s->LocalAt(23), false); args23980.Add(Attribute(s->LocalAt(36), "board"), false); return Call(c, fn23979, std::move(args23980)); }()); return v23976; }()))) {
auto v23981 = Value(int64_t{0});
s->SetAt(10, v23981);
}
else {
if (static_cast<bool>(([&]() -> Value { auto v23982 = ([&]() -> Value { auto v23983 = s->LocalAt(21); Value v23984; v23984 = Value("HARVEST"); if (!static_cast<bool>(Binary("Eq", v23983, v23984))) return Value(false); v23983 = v23984; return Value(true); }()); if (!static_cast<bool>(v23982)) return v23982; v23982 = ([&]() -> Value { auto fn23985 = s->Global("isinstance"); Arguments args23986; args23986.positional.reserve(2); args23986.Add(s->LocalAt(34), false); args23986.Add(s->Global("dict"), false); return Call(c, fn23985, std::move(args23986)); }()); return v23982; }()))) {
auto v23987 = s->LocalAt(10);
s->SetAt(10, Inplace("Add", v23987, ([&]() -> Value { auto fn23988 = s->Global("max"); Arguments args23989; args23989.positional.reserve(2); args23989.Add(Value(int64_t{0}), false); args23989.Add(([&]() -> Value { auto fn23990 = s->Global("int"); Arguments args23991; args23991.Add(([&]() -> Value { auto fn23992 = PrepareDictionaryGet(s->LocalAt(34)); Arguments args23993; args23993.positional.reserve(2); args23993.Add(Value("yield_units"), false); args23993.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn23992, std::move(args23993)); }()), false); return Call(c, fn23990, std::move(args23991)); }()), false); return Call(c, fn23988, std::move(args23989)); }())));
}
else {
if (static_cast<bool>(([&]() -> Value { auto v23994 = ([&]() -> Value { auto v23995 = s->LocalAt(21); Value v23996; v23996 = Value("COLLECT_FERTILIZER"); if (!static_cast<bool>(Binary("Eq", v23995, v23996))) return Value(false); v23995 = v23996; return Value(true); }()); if (!static_cast<bool>(v23994)) return v23994; v23994 = ([&]() -> Value { auto fn23997 = s->Global("isinstance"); Arguments args23998; args23998.positional.reserve(2); args23998.Add(s->LocalAt(34), false); args23998.Add(s->Global("dict"), false); return Call(c, fn23997, std::move(args23998)); }()); if (!static_cast<bool>(v23994)) return v23994; v23994 = ([&]() -> Value { auto fn23999 = PrepareDictionaryGet(s->LocalAt(34)); Arguments args24000; args24000.Add(Value("fertilizer_available"), false); return CallDictionaryGet(c, fn23999, std::move(args24000)); }()); return v23994; }()))) {
auto v24001 = s->LocalAt(10);
s->SetAt(10, Inplace("Add", v24001, Value(int64_t{1})));
}
else {
if (static_cast<bool>(([&]() -> Value { auto v24002 = ([&]() -> Value { auto v24003 = s->LocalAt(21); Value v24004; v24004 = Tuple({Value("FEED"), Value("FERTILIZE")}); if (!static_cast<bool>(Binary("In", v24003, v24004))) return Value(false); v24003 = v24004; return Value(true); }()); if (!static_cast<bool>(v24002)) return v24002; v24002 = ([&]() -> Value { auto v24005 = s->LocalAt(10); Value v24006; v24006 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v24005, v24006))) return Value(false); v24005 = v24006; return Value(true); }()); return v24002; }()))) {
auto v24007 = s->LocalAt(10);
s->SetAt(10, Inplace("Sub", v24007, Value(int64_t{1})));
}
else {
if (static_cast<bool>(([&]() -> Value { auto v24008 = ([&]() -> Value { auto v24009 = s->LocalAt(21); Value v24010; v24010 = Value("PICKUP"); if (!static_cast<bool>(Binary("Eq", v24009, v24010))) return Value(false); v24009 = v24010; return Value(true); }()); if (!static_cast<bool>(v24008)) return v24008; v24008 = ([&]() -> Value { auto v24011 = ([&]() -> Value { auto fn24013 = s->Global("len"); Arguments args24014; args24014.Add(s->LocalAt(6), false); return Call(c, fn24013, std::move(args24014)); }()); Value v24012; v24012 = Value(int64_t{2}); if (!static_cast<bool>(Binary("GtE", v24011, v24012))) return Value(false); v24011 = v24012; return Value(true); }()); if (!static_cast<bool>(v24008)) return v24008; v24008 = ([&]() -> Value { auto fn24015 = s->Global("_shed_adjacent"); Arguments args24016; args24016.positional.reserve(2); args24016.Add(s->LocalAt(23), false); args24016.Add(Attribute(s->LocalAt(36), "board"), false); return Call(c, fn24015, std::move(args24016)); }()); return v24008; }()))) {
auto v24017 = s->LocalAt(10);
s->SetAt(10, Inplace("Add", v24017, ([&]() -> Value { auto fn24018 = s->Global("max"); Arguments args24019; args24019.positional.reserve(2); args24019.Add(Value(int64_t{1}), false); args24019.Add((static_cast<bool>(([&]() -> Value { auto v24020 = ([&]() -> Value { auto fn24022 = s->Global("len"); Arguments args24023; args24023.Add(s->LocalAt(6), false); return Call(c, fn24022, std::move(args24023)); }()); Value v24021; v24021 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v24020, v24021))) return Value(false); v24020 = v24021; return Value(true); }())) ? ([&]() -> Value { auto fn24024 = s->Global("int"); Arguments args24025; args24025.Add(Get(s->LocalAt(6), Value(int64_t{2})), false); return Call(c, fn24024, std::move(args24025)); }()) : Value(int64_t{1})), false); return Call(c, fn24018, std::move(args24019)); }())));
}
}
}
}
}
auto v24026 = s->LocalAt(5);
s->SetAt(5, Inplace("Add", v24026, s->LocalAt(10)));
}
auto v24027 = (static_cast<bool>(([&]() -> Value { auto fn24028 = s->Global("isinstance"); Arguments args24029; args24029.positional.reserve(2); args24029.Add(s->LocalAt(7), false); args24029.Add(s->Global("dict"), false); return Call(c, fn24028, std::move(args24029)); }())) ? ([&]() -> Value { auto fn24030 = s->Global("int"); Arguments args24031; args24031.Add(([&]() -> Value { auto fn24032 = PrepareDictionaryGet(([&]() -> Value { auto v24034 = s->LocalAt(7); if (static_cast<bool>(v24034)) return v24034; v24034 = ([&]() -> Value { auto dict24035 = Dict(); return dict24035; }()); return v24034; }())); Arguments args24033; args24033.positional.reserve(2); args24033.Add(Value("shedCapacity"), false); args24033.Add(Value(int64_t{100}), false); return CallDictionaryGet(c, fn24032, std::move(args24033)); }()), false); return Call(c, fn24030, std::move(args24031)); }()) : Value(int64_t{100}));
s->SetAt(4, v24027);
auto v24036 = ([&]() -> Value { auto v24037 = ([&]() -> Value { auto v24038 = ([&]() -> Value { auto v24039 = s->LocalAt(18); return Binary("Add", v24039, s->LocalAt(5)); }()); return Binary("Sub", v24038, s->LocalAt(4)); }()); return Binary("Add", v24037, s->Global("_SR_MARGIN")); }());
s->SetAt(22, v24036);
if (static_cast<bool>(([&]() -> Value { auto v24040 = s->LocalAt(22); Value v24041; v24041 = Value(int64_t{0}); if (!static_cast<bool>(Binary("LtE", v24040, v24041))) return Value(false); v24040 = v24041; return Value(true); }()))) {
return s->LocalAt(1);
}
auto v24042 = ([&]() -> Value { auto dict24043 = Dict(); auto key24044 = Value("WHEAT"); Put(dict24043, key24044, Value(int64_t{0})); auto key24045 = Value("FERTILIZER"); Put(dict24043, key24045, Value(int64_t{0})); return dict24043; }());
s->SetAt(17, v24042);
for (const auto& item24046 : Iterate(([&]() -> Value { auto fn24047 = s->Global("range"); Arguments args24048; args24048.positional.reserve(2); args24048.Add(([&]() -> Value { auto v24049 = s->LocalAt(32); return Binary("Add", v24049, Value(int64_t{1})); }()), false); args24048.Add(([&]() -> Value { auto fn24050 = s->Global("min"); Arguments args24051; args24051.positional.reserve(2); args24051.Add(Value(int64_t{719}), false); args24051.Add(([&]() -> Value { auto v24052 = s->LocalAt(32); return Binary("Add", v24052, Value(int64_t{25})); }()), false); return Call(c, fn24050, std::move(args24051)); }()), false); return Call(c, fn24047, std::move(args24048)); }()))) {
s->SetAt(33, item24046);
auto v24053 = ([&]() -> Value { auto fn24054 = s->Global("_sr_tape"); Arguments args24055; args24055.positional.reserve(2); args24055.Add(s->LocalAt(29), false); args24055.Add(s->LocalAt(33), false); return Call(c, fn24054, std::move(args24055)); }());
s->SetAt(0, v24053);
for (const auto& item24056 : Iterate(([&]() -> Value { auto v24057 = List({([&]() -> Value { auto v24058 = ([&]() -> Value { auto fn24059 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args24060; args24060.Add(Value("farmer"), false); return CallDictionaryGet(c, fn24059, std::move(args24060)); }()); if (static_cast<bool>(v24058)) return v24058; v24058 = List({Value("PASS")}); return v24058; }())}); return Binary("Add", v24057, ([&]() -> Value { auto fn24061 = s->Global("list"); Arguments args24062; args24062.Add(([&]() -> Value { auto v24063 = ([&]() -> Value { auto fn24064 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args24065; args24065.Add(Value("hands"), false); return CallDictionaryGet(c, fn24064, std::move(args24065)); }()); if (static_cast<bool>(v24063)) return v24063; v24063 = List({}); return v24063; }()), false); return Call(c, fn24061, std::move(args24062)); }())); }()))) {
s->SetAt(2, item24056);
if (static_cast<bool>(Unary("Not", s->LocalAt(2)))) {
continue;
}
if (static_cast<bool>(([&]() -> Value { auto v24066 = Get(s->LocalAt(2), Value(int64_t{0})); Value v24067; v24067 = Value("FEED"); if (!static_cast<bool>(Binary("Eq", v24066, v24067))) return Value(false); v24066 = v24067; return Value(true); }()))) {
auto v24068 = s->LocalAt(17);
auto v24069 = Value("WHEAT");
auto v24070 = Get(v24068, v24069);
Put(v24068, v24069, Inplace("Add", v24070, Value(int64_t{1})));
}
else {
if (static_cast<bool>(([&]() -> Value { auto v24071 = Get(s->LocalAt(2), Value(int64_t{0})); Value v24072; v24072 = Value("FERTILIZE"); if (!static_cast<bool>(Binary("Eq", v24071, v24072))) return Value(false); v24071 = v24072; return Value(true); }()))) {
auto v24073 = s->LocalAt(17);
auto v24074 = Value("FERTILIZER");
auto v24075 = Get(v24073, v24074);
Put(v24073, v24074, Inplace("Add", v24075, Value(int64_t{1})));
}
}
}
}
auto v24076 = Get(Get(s->LocalAt(20), Value("market")), Value("prices"));
s->SetAt(25, v24076);
auto v24077 = List({});
s->SetAt(3, v24077);
for (const auto& item24078 : Iterate(s->Global("_SR_PRODUCTS"))) {
s->SetAt(13, item24078);
auto v24079 = ([&]() -> Value { auto v24080 = ([&]() -> Value { auto fn24081 = s->Global("int"); Arguments args24082; args24082.Add(([&]() -> Value { auto fn24083 = PrepareDictionaryGet(s->LocalAt(15)); Arguments args24084; args24084.positional.reserve(2); args24084.Add(s->LocalAt(13), false); args24084.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn24083, std::move(args24084)); }()), false); return Call(c, fn24081, std::move(args24082)); }()); return Binary("Sub", v24080, ([&]() -> Value { auto fn24085 = PrepareDictionaryGet(s->LocalAt(17)); Arguments args24086; args24086.positional.reserve(2); args24086.Add(s->LocalAt(13), false); args24086.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn24085, std::move(args24086)); }())); }());
s->SetAt(31, v24079);
if (static_cast<bool>(([&]() -> Value { auto v24087 = ([&]() -> Value { auto v24088 = s->LocalAt(31); Value v24089; v24089 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v24088, v24089))) return Value(false); v24088 = v24089; return Value(true); }()); if (!static_cast<bool>(v24087)) return v24087; v24087 = ([&]() -> Value { auto v24090 = ([&]() -> Value { auto fn24092 = s->Global("int"); Arguments args24093; args24093.Add(([&]() -> Value { auto fn24094 = PrepareDictionaryGet(s->LocalAt(25)); Arguments args24095; args24095.positional.reserve(2); args24095.Add(s->LocalAt(13), false); args24095.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn24094, std::move(args24095)); }()), false); return Call(c, fn24092, std::move(args24093)); }()); Value v24091; v24091 = Value(int64_t{2}); if (!static_cast<bool>(Binary("GtE", v24090, v24091))) return Value(false); v24090 = v24091; return Value(true); }()); return v24087; }()))) {
(void)([&]() -> Value { auto fn24096 = Attribute(s->LocalAt(3), "append"); Arguments args24097; args24097.Add(Tuple({([&]() -> Value { auto fn24098 = s->Global("int"); Arguments args24099; args24099.Add(([&]() -> Value { auto fn24100 = PrepareDictionaryGet(s->LocalAt(25)); Arguments args24101; args24101.positional.reserve(2); args24101.Add(s->LocalAt(13), false); args24101.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn24100, std::move(args24101)); }()), false); return Call(c, fn24098, std::move(args24099)); }()), s->LocalAt(13), s->LocalAt(31)}), false); return Call(c, fn24096, std::move(args24097)); }());
}
}
(void)([&]() -> Value { auto fn24102 = Attribute(s->LocalAt(3), "sort"); Arguments args24103; return Call(c, fn24102, std::move(args24103)); }());
auto v24104 = Value(int64_t{0});
s->SetAt(30, v24104);
for (const auto& item24105 : Iterate(s->LocalAt(3))) {
auto unpack24106 = Iterate(item24105);
ValidateUnpack(unpack24106, 3, false);
s->SetAt(24, unpack24106.at(0));
s->SetAt(13, unpack24106.at(1));
s->SetAt(31, unpack24106.at(2));
if (static_cast<bool>(([&]() -> Value { auto v24107 = s->LocalAt(22); Value v24108; v24108 = Value(int64_t{0}); if (!static_cast<bool>(Binary("LtE", v24107, v24108))) return Value(false); v24107 = v24108; return Value(true); }()))) {
break;
}
auto v24109 = ([&]() -> Value { auto fn24110 = s->Global("min"); Arguments args24111; args24111.positional.reserve(2); args24111.Add(s->LocalAt(31), false); args24111.Add(s->LocalAt(22), false); return Call(c, fn24110, std::move(args24111)); }());
s->SetAt(28, v24109);
bool exhausted24112 = true;
for (const auto& item24113 : Iterate(s->LocalAt(16))) {
s->SetAt(19, item24113);
if (static_cast<bool>(([&]() -> Value { auto v24114 = ([&]() -> Value { auto v24115 = ([&]() -> Value { auto fn24117 = s->Global("len"); Arguments args24118; args24118.Add(s->LocalAt(19), false); return Call(c, fn24117, std::move(args24118)); }()); Value v24116; v24116 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v24115, v24116))) return Value(false); v24115 = v24116; return Value(true); }()); if (!static_cast<bool>(v24114)) return v24114; v24114 = ([&]() -> Value { auto v24119 = Slice(s->LocalAt(19), Value{}, Value(int64_t{2}), Value{}); Value v24120; v24120 = List({Value("SELL"), s->LocalAt(13)}); if (!static_cast<bool>(Binary("Eq", v24119, v24120))) return Value(false); v24119 = v24120; return Value(true); }()); return v24114; }()))) {
auto v24121 = ([&]() -> Value { auto v24122 = ([&]() -> Value { auto fn24123 = s->Global("int"); Arguments args24124; args24124.Add(Get(s->LocalAt(19), Value(int64_t{2})), false); return Call(c, fn24123, std::move(args24124)); }()); return Binary("Add", v24122, s->LocalAt(28)); }());
Put(s->LocalAt(19), Value(int64_t{2}), v24121);
exhausted24112 = false;
break;
}
}
if (exhausted24112) {
if (static_cast<bool>(([&]() -> Value { auto v24125 = ([&]() -> Value { auto fn24127 = s->Global("len"); Arguments args24128; args24128.Add(s->LocalAt(16), false); return Call(c, fn24127, std::move(args24128)); }()); Value v24126; v24126 = Value(int64_t{10}); if (!static_cast<bool>(Binary("GtE", v24125, v24126))) return Value(false); v24125 = v24126; return Value(true); }()))) {
continue;
}
(void)([&]() -> Value { auto fn24129 = Attribute(s->LocalAt(16), "append"); Arguments args24130; args24130.Add(List({Value("SELL"), s->LocalAt(13), s->LocalAt(28)}), false); return Call(c, fn24129, std::move(args24130)); }());
}
auto v24131 = s->LocalAt(22);
s->SetAt(22, Inplace("Sub", v24131, s->LocalAt(28)));
auto v24132 = s->LocalAt(30);
s->SetAt(30, Inplace("Add", v24132, s->LocalAt(28)));
}
if (static_cast<bool>(s->LocalAt(30))) {
auto v24133 = s->Global("_SR_REPORT");
auto v24134 = Value("sr_turns");
auto v24135 = Get(v24133, v24134);
Put(v24133, v24134, Inplace("Add", v24135, Value(int64_t{1})));
auto v24136 = s->Global("_SR_REPORT");
auto v24137 = Value("sr_units");
auto v24138 = Get(v24136, v24137);
Put(v24136, v24137, Inplace("Add", v24138, s->LocalAt(30)));
auto v24139 = ([&]() -> Value { auto fn24140 = s->Global("dict"); Arguments args24141; args24141.Add(s->LocalAt(1), false); return Call(c, fn24140, std::move(args24141)); }());
s->SetAt(1, v24139);
auto v24142 = s->LocalAt(16);
Put(s->LocalAt(1), Value("market"), v24142);
}
} catch (const Error& error23842) {
if (Matches(error23842, s->Global("Exception"))) {
auto v24143 = s->Global("_SR_REPORT");
auto v24144 = Value("sr_errors");
auto v24145 = Get(v24143, v24144);
Put(v24143, v24144, Inplace("Add", v24145, Value(int64_t{1})));
}
else { throw; }
}
return s->LocalAt(1);
return {};
}
}  // namespace kagg::opponents::compiled
