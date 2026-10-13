// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_9f396fbdcf68ec3113d4(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "actor", "avail", "c", "center", "cfg", "credit", "day", "extra", "farm", "frm", "gained", "got", "inv", "inventories", "key", "kind", "market", "n", "o", "obs", "occupied", "op", "p", "planned", "positions", "private", "prod", "qty", "result", "seat", "seen", "shed", "shops", "site", "state", "step", "t", "tile", "tiles", "to", "trial", "units", "work", "workers", "x", "y"};
s->PrepareSlots(s_names);
auto v19842 = ([&]() -> Value { auto fn19843 = s->Global("int"); Arguments args19844; args19844.Add(Get(s->LocalAt(20), Value("step")), false); return Call(c, fn19843, std::move(args19844)); }());
s->SetAt(36, v19842);
auto v19845 = ([&]() -> Value { auto v19846 = s->LocalAt(36); return Binary("FloorDiv", v19846, Value(int64_t{24})); }());
s->SetAt(7, v19845);
auto v19847 = ([&]() -> Value { auto fn19848 = s->Global("int"); Arguments args19849; args19849.Add(Get(s->LocalAt(20), Value("player")), false); return Call(c, fn19848, std::move(args19849)); }());
s->SetAt(30, v19847);
auto v19850 = Get(Get(s->LocalAt(20), Value("farms")), s->LocalAt(30));
s->SetAt(9, v19850);
auto v19851 = Get(s->LocalAt(20), Value("private"));
s->SetAt(26, v19851);
auto v19852 = Get(s->LocalAt(26), Value("shed"));
s->SetAt(32, v19852);
auto v19853 = ([&]() -> Value { auto fn19854 = PrepareDictionaryGet(s->LocalAt(26)); Arguments args19855; args19855.positional.reserve(2); args19855.Add(Value("inventories"), false); args19855.Add(List({}), false); return CallDictionaryGet(c, fn19854, std::move(args19855)); }());
s->SetAt(14, v19853);
auto v19856 = ([&]() -> Value { auto fn19857 = s->Global("list"); Arguments args19858; args19858.Add(([&]() -> Value { auto v19859 = ([&]() -> Value { auto fn19860 = PrepareDictionaryGet(([&]() -> Value { auto v19862 = ([&]() -> Value { auto fn19863 = PrepareDictionaryGet(s->LocalAt(20)); Arguments args19864; args19864.Add(Value("town"), false); return CallDictionaryGet(c, fn19863, std::move(args19864)); }()); if (static_cast<bool>(v19862)) return v19862; v19862 = ([&]() -> Value { auto dict19865 = Dict(); return dict19865; }()); return v19862; }())); Arguments args19861; args19861.positional.reserve(2); args19861.Add(Value("unlocked_shops"), false); args19861.Add(List({}), false); return CallDictionaryGet(c, fn19860, std::move(args19861)); }()); if (static_cast<bool>(v19859)) return v19859; v19859 = List({}); return v19859; }()), false); return Call(c, fn19857, std::move(args19858)); }());
s->SetAt(33, v19856);
auto v19866 = Get(s->LocalAt(9), Value("tiles"));
s->SetAt(39, v19866);
auto v19867 = ([&]() -> Value { auto fn19868 = s->Global("len"); Arguments args19869; args19869.Add(s->LocalAt(39), false); return Call(c, fn19868, std::move(args19869)); }());
s->SetAt(18, v19867);
auto v19870 = ([&]() -> Value { auto v19871 = s->LocalAt(18); return Binary("FloorDiv", v19871, Value(int64_t{2})); }());
s->SetAt(4, v19870);
auto v19872 = ([&]() -> Value { auto dict19873 = Dict(); return dict19873; }());
s->SetAt(11, v19872);
for (const auto& item19874 : Iterate(Get(s->LocalAt(35), Value("pending")))) {
s->SetAt(23, item19874);
auto v19875 = Get(s->LocalAt(23), Value("to"));
s->SetAt(40, v19875);
if (static_cast<bool>(([&]() -> Value { auto v19876 = s->LocalAt(40); Value v19877; v19877 = s->LocalAt(11); if (!static_cast<bool>(Binary("NotIn", v19876, v19877))) return Value(false); v19876 = v19877; return Value(true); }()))) {
auto v19878 = ([&]() -> Value { auto fn19879 = s->Global("max"); Arguments args19880; args19880.positional.reserve(2); args19880.Add(Value(int64_t{0}), false); args19880.Add(([&]() -> Value { auto v19881 = ([&]() -> Value { auto fn19882 = s->Global("int"); Arguments args19883; args19883.Add(([&]() -> Value { auto fn19884 = PrepareDictionaryGet(s->LocalAt(32)); Arguments args19885; args19885.positional.reserve(2); args19885.Add(s->LocalAt(40), false); args19885.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn19884, std::move(args19885)); }()), false); return Call(c, fn19882, std::move(args19883)); }()); return Binary("Sub", v19881, Get(s->LocalAt(23), Value("before"))); }()), false); return Call(c, fn19879, std::move(args19880)); }());
Put(s->LocalAt(11), s->LocalAt(40), v19878);
}
auto v19886 = ([&]() -> Value { auto fn19887 = s->Global("min"); Arguments args19888; args19888.positional.reserve(2); args19888.Add(Get(s->LocalAt(23), Value("qty")), false); args19888.Add(Get(s->LocalAt(11), s->LocalAt(40)), false); return Call(c, fn19887, std::move(args19888)); }());
s->SetAt(12, v19886);
auto v19889 = s->LocalAt(11);
auto v19890 = s->LocalAt(40);
auto v19891 = Get(v19889, v19890);
Put(v19889, v19890, Inplace("Sub", v19891, s->LocalAt(12)));
if (static_cast<bool>(([&]() -> Value { auto v19892 = s->LocalAt(12); Value v19893; v19893 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v19892, v19893))) return Value(false); v19892 = v19893; return Value(true); }()))) {
auto v19894 = Tuple({Get(s->LocalAt(23), Value("from")), s->LocalAt(40)});
s->SetAt(15, v19894);
auto v19895 = ([&]() -> Value { auto v19896 = ([&]() -> Value { auto fn19897 = PrepareDictionaryGet(Get(s->LocalAt(35), Value("credit"))); Arguments args19898; args19898.positional.reserve(2); args19898.Add(s->LocalAt(15), false); args19898.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn19897, std::move(args19898)); }()); return Binary("Add", v19896, s->LocalAt(12)); }());
Put(Get(s->LocalAt(35), Value("credit")), s->LocalAt(15), v19895);
if (static_cast<bool>(([&]() -> Value { auto v19899 = Get(s->Global("_Y_STRUCT"), Get(s->LocalAt(23), Value("from"))); Value v19900; v19900 = Get(s->Global("_Y_STRUCT"), s->LocalAt(40)); if (!static_cast<bool>(Binary("NotEq", v19899, v19900))) return Value(false); v19899 = v19900; return Value(true); }()))) {
auto v19901 = s->LocalAt(35);
auto v19902 = Value("coop_swap");
auto v19903 = Get(v19901, v19902);
Put(v19901, v19902, Inplace("Add", v19903, s->LocalAt(12)));
}
}
}
auto v19904 = List({});
Put(s->LocalAt(35), Value("pending"), v19904);
auto v19905 = ([&]() -> Value { auto fn19906 = Attribute(s->Global("_y_copy"), "deepcopy"); Arguments args19907; args19907.Add(s->LocalAt(0), false); return Call(c, fn19906, std::move(args19907)); }());
s->SetAt(29, v19905);
auto v19908 = ([&]() -> Value { auto v19909 = ([&]() -> Value { auto fn19910 = PrepareDictionaryGet(s->LocalAt(29)); Arguments args19911; args19911.Add(Value("market"), false); return CallDictionaryGet(c, fn19910, std::move(args19911)); }()); if (static_cast<bool>(v19909)) return v19909; v19909 = List({}); return v19909; }());
s->SetAt(17, v19908);
auto v19912 = s->LocalAt(17);
Put(s->LocalAt(29), Value("market"), v19912);
if (static_cast<bool>(([&]() -> Value { auto v19913 = Get(Get(s->LocalAt(5), Value("days")), Value(int64_t{0})); Value v19914; v19914 = s->LocalAt(7); if (!static_cast<bool>(Binary("LtE", v19913, v19914))) return Value(false); v19913 = v19914; v19914 = Get(Get(s->LocalAt(5), Value("days")), Value(int64_t{1})); if (!static_cast<bool>(Binary("LtE", v19913, v19914))) return Value(false); v19913 = v19914; return Value(true); }()))) {
for (const auto& item19915 : Iterate(s->LocalAt(17))) {
s->SetAt(19, item19915);
if (static_cast<bool>(([&]() -> Value { auto v19916 = ([&]() -> Value { auto v19917 = ([&]() -> Value { auto fn19919 = s->Global("len"); Arguments args19920; args19920.Add(s->LocalAt(19), false); return Call(c, fn19919, std::move(args19920)); }()); Value v19918; v19918 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v19917, v19918))) return Value(false); v19917 = v19918; return Value(true); }()); if (!static_cast<bool>(v19916)) return v19916; v19916 = ([&]() -> Value { auto v19921 = Get(s->LocalAt(19), Value(int64_t{0})); Value v19922; v19922 = Value("BUY_ANIMAL"); if (!static_cast<bool>(Binary("Eq", v19921, v19922))) return Value(false); v19921 = v19922; return Value(true); }()); if (!static_cast<bool>(v19916)) return v19916; v19916 = ([&]() -> Value { auto v19923 = Get(s->LocalAt(19), Value(int64_t{1})); Value v19924; v19924 = s->Global("_Y_COST"); if (!static_cast<bool>(Binary("In", v19923, v19924))) return Value(false); v19923 = v19924; return Value(true); }()); if (!static_cast<bool>(v19916)) return v19916; v19916 = ([&]() -> Value { auto v19925 = Value(int64_t{1}); Value v19926; v19926 = ([&]() -> Value { auto fn19927 = s->Global("int"); Arguments args19928; args19928.Add(Get(s->LocalAt(19), Value(int64_t{2})), false); return Call(c, fn19927, std::move(args19928)); }()); if (!static_cast<bool>(Binary("LtE", v19925, v19926))) return Value(false); v19925 = v19926; v19926 = ([&]() -> Value { auto fn19929 = PrepareDictionaryGet(s->LocalAt(5)); Arguments args19930; args19930.positional.reserve(2); args19930.Add(Value("maxq"), false); args19930.Add(Value(int64_t{2}), false); return CallDictionaryGet(c, fn19929, std::move(args19930)); }()); if (!static_cast<bool>(Binary("LtE", v19925, v19926))) return Value(false); v19925 = v19926; return Value(true); }()); return v19916; }()))) {
auto v19931 = ([&]() -> Value { auto fn19932 = s->Global("_y_target"); Arguments args19933; args19933.positional.reserve(3); args19933.Add(Get(s->LocalAt(19), Value(int64_t{1})), false); args19933.Add(s->LocalAt(33), false); args19933.Add(s->LocalAt(5), false); return Call(c, fn19932, std::move(args19933)); }());
s->SetAt(40, v19931);
if (static_cast<bool>(([&]() -> Value { auto v19934 = ([&]() -> Value { auto v19935 = s->LocalAt(40); Value v19936; v19936 = Value{}; if (!static_cast<bool>(Binary("Is", v19935, v19936))) return Value(false); v19935 = v19936; return Value(true); }()); if (static_cast<bool>(v19934)) return v19934; v19934 = ([&]() -> Value { auto v19937 = s->LocalAt(40); Value v19938; v19938 = Get(s->LocalAt(19), Value(int64_t{1})); if (!static_cast<bool>(Binary("Eq", v19937, v19938))) return Value(false); v19937 = v19938; return Value(true); }()); return v19934; }()))) {
continue;
}
auto v19939 = ([&]() -> Value { auto comp19940 = std::make_shared<Scope>(); comp19940->globals = s->globals; comp19940->parent = s; static constexpr const char* comp19940_names[] = {"x"}; comp19940->PrepareSlots(comp19940_names); auto result19941 = List(); for (const auto& item19942 : Iterate(s->LocalAt(17))) { comp19940->SetAt(0, item19942); result19941.node()->sequence.push_back((static_cast<bool>(([&]() -> Value { auto fn19943 = comp19940->Global("isinstance"); Arguments args19944; args19944.positional.reserve(2); args19944.Add(comp19940->LocalAt(0), false); args19944.Add(comp19940->Global("list"), false); return Call(c, fn19943, std::move(args19944)); }())) ? ([&]() -> Value { auto fn19945 = comp19940->Global("list"); Arguments args19946; args19946.Add(comp19940->LocalAt(0), false); return Call(c, fn19945, std::move(args19946)); }()) : comp19940->LocalAt(0))); } return result19941; }());
s->SetAt(41, v19939);
for (const auto& item19947 : Iterate(s->LocalAt(41))) {
s->SetAt(37, item19947);
if (static_cast<bool>(([&]() -> Value { auto v19948 = ([&]() -> Value { auto fn19949 = s->Global("isinstance"); Arguments args19950; args19950.positional.reserve(2); args19950.Add(s->LocalAt(37), false); args19950.Add(s->Global("list"), false); return Call(c, fn19949, std::move(args19950)); }()); if (!static_cast<bool>(v19948)) return v19948; v19948 = ([&]() -> Value { auto v19951 = s->LocalAt(37); Value v19952; v19952 = s->LocalAt(19); if (!static_cast<bool>(Binary("Eq", v19951, v19952))) return Value(false); v19951 = v19952; return Value(true); }()); return v19948; }()))) {
auto v19953 = s->LocalAt(40);
Put(s->LocalAt(37), Value(int64_t{1}), v19953);
}
}
if (static_cast<bool>(([&]() -> Value { auto v19954 = ([&]() -> Value { auto fn19956 = s->Global("_y_cash"); Arguments args19957; args19957.positional.reserve(3); args19957.Add(s->LocalAt(20), false); args19957.Add(s->LocalAt(29), false); args19957.Add(s->LocalAt(41), false); return Call(c, fn19956, std::move(args19957)); }()); Value v19955; v19955 = ([&]() -> Value { auto fn19958 = PrepareDictionaryGet(s->LocalAt(5)); Arguments args19959; args19959.positional.reserve(2); args19959.Add(Value("margin"), false); args19959.Add(Value(int64_t{100}), false); return CallDictionaryGet(c, fn19958, std::move(args19959)); }()); if (!static_cast<bool>(Binary("Lt", v19954, v19955))) return Value(false); v19954 = v19955; return Value(true); }()))) {
auto v19960 = s->Global("_Y_REPORT");
auto v19961 = Value("declined");
auto v19962 = Get(v19960, v19961);
Put(v19960, v19961, Inplace("Add", v19962, Value(int64_t{1})));
continue;
}
(void)([&]() -> Value { auto fn19963 = Attribute(Get(s->LocalAt(35), Value("pending")), "append"); Arguments args19964; args19964.Add(([&]() -> Value { auto dict19965 = Dict(); auto key19966 = Value("from"); Put(dict19965, key19966, Get(s->LocalAt(19), Value(int64_t{1}))); auto key19967 = Value("to"); Put(dict19965, key19967, s->LocalAt(40)); auto key19968 = Value("qty"); Put(dict19965, key19968, ([&]() -> Value { auto fn19969 = s->Global("int"); Arguments args19970; args19970.Add(Get(s->LocalAt(19), Value(int64_t{2})), false); return Call(c, fn19969, std::move(args19970)); }())); auto key19971 = Value("before"); Put(dict19965, key19971, ([&]() -> Value { auto fn19972 = s->Global("int"); Arguments args19973; args19973.Add(([&]() -> Value { auto fn19974 = PrepareDictionaryGet(s->LocalAt(32)); Arguments args19975; args19975.positional.reserve(2); args19975.Add(s->LocalAt(40), false); args19975.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn19974, std::move(args19975)); }()), false); return Call(c, fn19972, std::move(args19973)); }())); return dict19965; }()), false); return Call(c, fn19963, std::move(args19964)); }());
auto v19976 = s->Global("_Y_REPORT");
auto v19977 = Value("swaps");
auto v19978 = Get(v19976, v19977);
Put(v19976, v19977, Inplace("Add", v19978, ([&]() -> Value { auto fn19979 = s->Global("int"); Arguments args19980; args19980.Add(Get(s->LocalAt(19), Value(int64_t{2})), false); return Call(c, fn19979, std::move(args19980)); }())));
auto v19981 = s->LocalAt(40);
Put(s->LocalAt(19), Value(int64_t{1}), v19981);
}
}
}
auto v19982 = ([&]() -> Value { Arguments args19983; args19983.Add(([&]() -> Value { auto v19984 = ([&]() -> Value { auto fn19985 = PrepareDictionaryGet(s->LocalAt(29)); Arguments args19986; args19986.Add(Value("farmer"), false); return CallDictionaryGet(c, fn19985, std::move(args19986)); }()); if (static_cast<bool>(v19984)) return v19984; v19984 = List({Value("PASS")}); return v19984; }()), false); args19983.Add(([&]() -> Value { auto v19987 = ([&]() -> Value { auto fn19988 = PrepareDictionaryGet(s->LocalAt(29)); Arguments args19989; args19989.Add(Value("hands"), false); return CallDictionaryGet(c, fn19988, std::move(args19989)); }()); if (static_cast<bool>(v19987)) return v19987; v19987 = List({}); return v19987; }()), true); return List(std::move(args19983.positional)); }());
s->SetAt(44, v19982);
auto v19990 = ([&]() -> Value { Arguments args19991; args19991.Add(Get(s->LocalAt(9), Value("farmer")), false); args19991.Add(Get(s->LocalAt(9), Value("hands")), true); return List(std::move(args19991.positional)); }());
s->SetAt(25, v19990);
auto v19992 = ([&]() -> Value { auto comp19993 = std::make_shared<Scope>(); comp19993->globals = s->globals; comp19993->parent = s; static constexpr const char* comp19993_names[] = {"k"}; comp19993->PrepareSlots(comp19993_names); auto result19994 = Dict(); for (const auto& item19995 : Iterate(s->Global("_Y_COST"))) { comp19993->SetAt(0, item19995); Put(result19994, comp19993->LocalAt(0), ([&]() -> Value { auto fn19996 = comp19993->Global("int"); Arguments args19997; args19997.Add(([&]() -> Value { auto fn19998 = PrepareDictionaryGet(comp19993->Captured("shed")); Arguments args19999; args19999.positional.reserve(2); args19999.Add(comp19993->LocalAt(0), false); args19999.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn19998, std::move(args19999)); }()), false); return Call(c, fn19996, std::move(args19997)); }())); } return result19994; }());
s->SetAt(2, v19992);
auto v20000 = ([&]() -> Value { auto fn20001 = s->Global("set"); Arguments args20002; return Call(c, fn20001, std::move(args20002)); }());
s->SetAt(31, v20000);
auto v20003 = ([&]() -> Value { auto fn20004 = s->Global("set"); Arguments args20005; return Call(c, fn20004, std::move(args20005)); }());
s->SetAt(21, v20003);
for (const auto& item20006 : Iterate(([&]() -> Value { auto fn20007 = s->Global("enumerate"); Arguments args20008; args20008.Add(Slice(s->LocalAt(44), Value{}, ([&]() -> Value { auto fn20009 = s->Global("len"); Arguments args20010; args20010.Add(s->LocalAt(25), false); return Call(c, fn20009, std::move(args20010)); }()), Value{}), false); return Call(c, fn20007, std::move(args20008)); }()))) {
auto unpack20011 = Iterate(item20006);
ValidateUnpack(unpack20011, 2, false);
s->SetAt(1, unpack20011.at(0));
s->SetAt(43, unpack20011.at(1));
if (static_cast<bool>(([&]() -> Value { auto v20012 = Unary("Not", s->LocalAt(43)); if (static_cast<bool>(v20012)) return v20012; v20012 = Unary("Not", ([&]() -> Value { auto fn20013 = s->Global("isinstance"); Arguments args20014; args20014.positional.reserve(2); args20014.Add(s->LocalAt(43), false); args20014.Add(s->Global("list"), false); return Call(c, fn20013, std::move(args20014)); }())); return v20012; }()))) {
continue;
}
auto v20015 = (static_cast<bool>(([&]() -> Value { auto v20016 = s->LocalAt(1); Value v20017; v20017 = ([&]() -> Value { auto fn20018 = s->Global("len"); Arguments args20019; args20019.Add(s->LocalAt(14), false); return Call(c, fn20018, std::move(args20019)); }()); if (!static_cast<bool>(Binary("Lt", v20016, v20017))) return Value(false); v20016 = v20017; return Value(true); }())) ? Get(s->LocalAt(14), s->LocalAt(1)) : ([&]() -> Value { auto dict20020 = Dict(); return dict20020; }()));
s->SetAt(13, v20015);
auto v20021 = Get(s->LocalAt(25), s->LocalAt(1));
auto unpack20022 = Iterate(v20021);
ValidateUnpack(unpack20022, 2, false);
s->SetAt(45, unpack20022.at(0));
s->SetAt(46, unpack20022.at(1));
auto v20023 = Get(Get(s->LocalAt(39), s->LocalAt(46)), s->LocalAt(45));
s->SetAt(38, v20023);
auto v20024 = Tuple({s->LocalAt(45), s->LocalAt(46)});
s->SetAt(34, v20024);
auto v20025 = Get(s->LocalAt(43), Value(int64_t{0}));
s->SetAt(22, v20025);
if (static_cast<bool>(([&]() -> Value { auto v20026 = ([&]() -> Value { auto v20027 = s->LocalAt(22); Value v20028; v20028 = Value("PICKUP"); if (!static_cast<bool>(Binary("Eq", v20027, v20028))) return Value(false); v20027 = v20028; return Value(true); }()); if (!static_cast<bool>(v20026)) return v20026; v20026 = ([&]() -> Value { auto v20029 = ([&]() -> Value { auto fn20031 = s->Global("len"); Arguments args20032; args20032.Add(s->LocalAt(43), false); return Call(c, fn20031, std::move(args20032)); }()); Value v20030; v20030 = Value(int64_t{2}); if (!static_cast<bool>(Binary("GtE", v20029, v20030))) return Value(false); v20029 = v20030; return Value(true); }()); if (!static_cast<bool>(v20026)) return v20026; v20026 = ([&]() -> Value { auto v20033 = Get(s->LocalAt(43), Value(int64_t{1})); Value v20034; v20034 = s->Global("_Y_COST"); if (!static_cast<bool>(Binary("In", v20033, v20034))) return Value(false); v20033 = v20034; return Value(true); }()); return v20026; }()))) {
auto v20035 = Get(s->LocalAt(43), Value(int64_t{1}));
s->SetAt(16, v20035);
auto v20036 = (static_cast<bool>(([&]() -> Value { auto v20037 = ([&]() -> Value { auto fn20039 = s->Global("len"); Arguments args20040; args20040.Add(s->LocalAt(43), false); return Call(c, fn20039, std::move(args20040)); }()); Value v20038; v20038 = Value(int64_t{2}); if (!static_cast<bool>(Binary("Gt", v20037, v20038))) return Value(false); v20037 = v20038; return Value(true); }())) ? ([&]() -> Value { auto fn20041 = s->Global("max"); Arguments args20042; args20042.positional.reserve(2); args20042.Add(Value(int64_t{1}), false); args20042.Add(([&]() -> Value { auto fn20043 = s->Global("int"); Arguments args20044; args20044.Add(Get(s->LocalAt(43), Value(int64_t{2})), false); return Call(c, fn20043, std::move(args20044)); }()), false); return Call(c, fn20041, std::move(args20042)); }()) : Value(int64_t{1}));
s->SetAt(28, v20036);
if (static_cast<bool>(([&]() -> Value { auto v20045 = ([&]() -> Value { auto fn20047 = PrepareDictionaryGet(s->LocalAt(2)); Arguments args20048; args20048.positional.reserve(2); args20048.Add(s->LocalAt(16), false); args20048.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn20047, std::move(args20048)); }()); Value v20046; v20046 = s->LocalAt(28); if (!static_cast<bool>(Binary("GtE", v20045, v20046))) return Value(false); v20045 = v20046; return Value(true); }()))) {
auto v20049 = s->LocalAt(2);
auto v20050 = s->LocalAt(16);
auto v20051 = Get(v20049, v20050);
Put(v20049, v20050, Inplace("Sub", v20051, s->LocalAt(28)));
continue;
}
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto v20052 = ([&]() -> Value { auto v20053 = s->LocalAt(45); Value v20054; v20054 = Tuple({([&]() -> Value { auto v20055 = s->LocalAt(4); return Binary("Sub", v20055, Value(int64_t{1})); }()), s->LocalAt(4)}); if (!static_cast<bool>(Binary("In", v20053, v20054))) return Value(false); v20053 = v20054; return Value(true); }()); if (!static_cast<bool>(v20052)) return v20052; v20052 = ([&]() -> Value { auto v20056 = s->LocalAt(46); Value v20057; v20057 = Tuple({([&]() -> Value { auto v20058 = s->LocalAt(4); return Binary("Sub", v20058, Value(int64_t{1})); }()), s->LocalAt(4)}); if (!static_cast<bool>(Binary("In", v20056, v20057))) return Value(false); v20056 = v20057; return Value(true); }()); return v20052; }())))) {
continue;
}
if (static_cast<bool>(([&]() -> Value { auto comp20059 = std::make_shared<Scope>(); comp20059->globals = s->globals; comp20059->parent = s; static constexpr const char* comp20059_names[] = {"a"}; comp20059->PrepareSlots(comp20059_names); auto result20060 = List(); for (const auto& item20061 : Iterate(s->Global("_Y_COST"))) { comp20059->SetAt(0, item20061); if (static_cast<bool>(([&]() -> Value { auto fn20062 = PrepareDictionaryGet(comp20059->Captured("inv")); Arguments args20063; args20063.positional.reserve(2); args20063.Add(comp20059->LocalAt(0), false); args20063.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn20062, std::move(args20063)); }()))) return Value(true); } return Value(false); }()))) {
continue;
}
for (const auto& item20064 : Iterate(([&]() -> Value { auto fn20065 = s->Global("list"); Arguments args20066; args20066.Add(([&]() -> Value { auto fn20067 = Attribute(Get(s->LocalAt(35), Value("credit")), "items"); Arguments args20068; return Call(c, fn20067, std::move(args20068)); }()), false); return Call(c, fn20065, std::move(args20066)); }()))) {
auto unpack20069 = Iterate(item20064);
ValidateUnpack(unpack20069, 2, false);
auto unpack20070 = Iterate(unpack20069.at(0));
ValidateUnpack(unpack20070, 2, false);
s->SetAt(10, unpack20070.at(0));
s->SetAt(40, unpack20070.at(1));
s->SetAt(3, unpack20069.at(1));
if (static_cast<bool>(([&]() -> Value { auto v20071 = ([&]() -> Value { auto v20072 = s->LocalAt(10); Value v20073; v20073 = s->LocalAt(16); if (!static_cast<bool>(Binary("Eq", v20072, v20073))) return Value(false); v20072 = v20073; return Value(true); }()); if (!static_cast<bool>(v20071)) return v20071; v20071 = ([&]() -> Value { auto v20074 = s->LocalAt(3); Value v20075; v20075 = s->LocalAt(28); if (!static_cast<bool>(Binary("GtE", v20074, v20075))) return Value(false); v20074 = v20075; return Value(true); }()); if (!static_cast<bool>(v20071)) return v20071; v20071 = ([&]() -> Value { auto v20076 = ([&]() -> Value { auto fn20078 = PrepareDictionaryGet(s->LocalAt(2)); Arguments args20079; args20079.positional.reserve(2); args20079.Add(s->LocalAt(40), false); args20079.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn20078, std::move(args20079)); }()); Value v20077; v20077 = s->LocalAt(28); if (!static_cast<bool>(Binary("GtE", v20076, v20077))) return Value(false); v20076 = v20077; return Value(true); }()); return v20071; }()))) {
auto v20080 = s->LocalAt(40);
Put(s->LocalAt(43), Value(int64_t{1}), v20080);
auto v20081 = ([&]() -> Value { auto v20082 = s->LocalAt(3); return Binary("Sub", v20082, s->LocalAt(28)); }());
Put(Get(s->LocalAt(35), Value("credit")), Tuple({s->LocalAt(10), s->LocalAt(40)}), v20081);
auto v20083 = s->LocalAt(2);
auto v20084 = s->LocalAt(40);
auto v20085 = Get(v20083, v20084);
Put(v20083, v20084, Inplace("Sub", v20085, s->LocalAt(28)));
auto v20086 = s->Global("_Y_REPORT");
auto v20087 = Value("pick");
auto v20088 = Get(v20086, v20087);
Put(v20086, v20087, Inplace("Add", v20088, s->LocalAt(28)));
break;
}
}
}
else {
if (static_cast<bool>(([&]() -> Value { auto v20089 = ([&]() -> Value { auto v20090 = s->LocalAt(22); Value v20091; v20091 = Value("PLACE"); if (!static_cast<bool>(Binary("Eq", v20090, v20091))) return Value(false); v20090 = v20091; return Value(true); }()); if (!static_cast<bool>(v20089)) return v20089; v20089 = ([&]() -> Value { auto v20092 = ([&]() -> Value { auto fn20094 = s->Global("len"); Arguments args20095; args20095.Add(s->LocalAt(43), false); return Call(c, fn20094, std::move(args20095)); }()); Value v20093; v20093 = Value(int64_t{2}); if (!static_cast<bool>(Binary("GtE", v20092, v20093))) return Value(false); v20092 = v20093; return Value(true); }()); if (!static_cast<bool>(v20089)) return v20089; v20089 = ([&]() -> Value { auto v20096 = Get(s->LocalAt(43), Value(int64_t{1})); Value v20097; v20097 = s->Global("_Y_COST"); if (!static_cast<bool>(Binary("In", v20096, v20097))) return Value(false); v20096 = v20097; return Value(true); }()); return v20089; }()))) {
auto v20098 = Get(s->LocalAt(43), Value(int64_t{1}));
s->SetAt(16, v20098);
if (static_cast<bool>(([&]() -> Value { auto v20099 = ([&]() -> Value { auto fn20101 = PrepareDictionaryGet(s->LocalAt(13)); Arguments args20102; args20102.positional.reserve(2); args20102.Add(s->LocalAt(16), false); args20102.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn20101, std::move(args20102)); }()); Value v20100; v20100 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v20099, v20100))) return Value(false); v20099 = v20100; return Value(true); }()))) {
continue;
}
for (const auto& item20103 : Iterate(Tuple({Value("COW"), Value("SHEEP"), Value("GOOSE")}))) {
s->SetAt(40, item20103);
if (static_cast<bool>(([&]() -> Value { auto v20104 = ([&]() -> Value { auto v20105 = s->LocalAt(40); Value v20106; v20106 = s->LocalAt(16); if (!static_cast<bool>(Binary("NotEq", v20105, v20106))) return Value(false); v20105 = v20106; return Value(true); }()); if (!static_cast<bool>(v20104)) return v20104; v20104 = ([&]() -> Value { auto v20107 = ([&]() -> Value { auto fn20109 = PrepareDictionaryGet(s->LocalAt(13)); Arguments args20110; args20110.positional.reserve(2); args20110.Add(s->LocalAt(40), false); args20110.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn20109, std::move(args20110)); }()); Value v20108; v20108 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v20107, v20108))) return Value(false); v20107 = v20108; return Value(true); }()); if (!static_cast<bool>(v20104)) return v20104; v20104 = ([&]() -> Value { auto fn20111 = s->Global("isinstance"); Arguments args20112; args20112.positional.reserve(2); args20112.Add(s->LocalAt(38), false); args20112.Add(s->Global("dict"), false); return Call(c, fn20111, std::move(args20112)); }()); if (!static_cast<bool>(v20104)) return v20104; v20104 = ([&]() -> Value { auto v20113 = ([&]() -> Value { auto fn20115 = PrepareDictionaryGet(s->LocalAt(38)); Arguments args20116; args20116.Add(Value("kind"), false); return CallDictionaryGet(c, fn20115, std::move(args20116)); }()); Value v20114; v20114 = Get(s->Global("_Y_STRUCT"), s->LocalAt(40)); if (!static_cast<bool>(Binary("Eq", v20113, v20114))) return Value(false); v20113 = v20114; return Value(true); }()); if (!static_cast<bool>(v20104)) return v20104; v20104 = Unary("Not", ([&]() -> Value { auto fn20117 = PrepareDictionaryGet(s->LocalAt(38)); Arguments args20118; args20118.Add(Value("animal"), false); return CallDictionaryGet(c, fn20117, std::move(args20118)); }())); if (!static_cast<bool>(v20104)) return v20104; v20104 = ([&]() -> Value { auto v20119 = s->LocalAt(34); Value v20120; v20120 = s->LocalAt(21); if (!static_cast<bool>(Binary("NotIn", v20119, v20120))) return Value(false); v20119 = v20120; return Value(true); }()); return v20104; }()))) {
auto v20121 = s->LocalAt(40);
Put(s->LocalAt(43), Value(int64_t{1}), v20121);
auto v20122 = s->LocalAt(40);
Put(Get(s->LocalAt(35), Value("sites")), s->LocalAt(34), v20122);
(void)([&]() -> Value { auto fn20123 = Attribute(s->LocalAt(21), "add"); Arguments args20124; args20124.Add(s->LocalAt(34), false); return Call(c, fn20123, std::move(args20124)); }());
auto v20125 = s->Global("_Y_REPORT");
auto v20126 = Value("place");
auto v20127 = Get(v20125, v20126);
Put(v20125, v20126, Inplace("Add", v20127, Value(int64_t{1})));
break;
}
}
}
else {
if (static_cast<bool>(([&]() -> Value { auto v20128 = ([&]() -> Value { auto v20129 = s->LocalAt(22); Value v20130; v20130 = Value("BUILD_COOP"); if (!static_cast<bool>(Binary("Eq", v20129, v20130))) return Value(false); v20129 = v20130; return Value(true); }()); if (!static_cast<bool>(v20128)) return v20128; v20128 = ([&]() -> Value { auto v20131 = Get(s->LocalAt(35), Value("coop_swap")); Value v20132; v20132 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v20131, v20132))) return Value(false); v20131 = v20132; return Value(true); }()); return v20128; }()))) {
auto v20133 = Value("BUILD_PASTURE");
Put(s->LocalAt(43), Value(int64_t{0}), v20133);
auto v20134 = s->Global("_Y_REPORT");
auto v20135 = Value("coop");
auto v20136 = Get(v20134, v20135);
Put(v20134, v20135, Inplace("Add", v20136, Value(int64_t{1})));
}
else {
if (static_cast<bool>(([&]() -> Value { auto v20137 = ([&]() -> Value { auto v20138 = s->LocalAt(22); Value v20139; v20139 = Value("HARVEST"); if (!static_cast<bool>(Binary("Eq", v20138, v20139))) return Value(false); v20138 = v20139; return Value(true); }()); if (!static_cast<bool>(v20137)) return v20137; v20137 = ([&]() -> Value { auto v20140 = s->LocalAt(34); Value v20141; v20141 = Get(s->LocalAt(35), Value("sites")); if (!static_cast<bool>(Binary("In", v20140, v20141))) return Value(false); v20140 = v20141; return Value(true); }()); if (!static_cast<bool>(v20137)) return v20137; v20137 = ([&]() -> Value { auto v20142 = s->LocalAt(34); Value v20143; v20143 = s->LocalAt(31); if (!static_cast<bool>(Binary("NotIn", v20142, v20143))) return Value(false); v20142 = v20143; return Value(true); }()); return v20137; }()))) {
if (static_cast<bool>(([&]() -> Value { auto v20144 = ([&]() -> Value { auto fn20145 = s->Global("isinstance"); Arguments args20146; args20146.positional.reserve(2); args20146.Add(s->LocalAt(38), false); args20146.Add(s->Global("dict"), false); return Call(c, fn20145, std::move(args20146)); }()); if (!static_cast<bool>(v20144)) return v20144; v20144 = ([&]() -> Value { auto v20147 = ([&]() -> Value { auto fn20149 = PrepareDictionaryGet(s->LocalAt(38)); Arguments args20150; args20150.Add(Value("animal"), false); return CallDictionaryGet(c, fn20149, std::move(args20150)); }()); Value v20148; v20148 = Get(Get(s->LocalAt(35), Value("sites")), s->LocalAt(34)); if (!static_cast<bool>(Binary("Eq", v20147, v20148))) return Value(false); v20147 = v20148; return Value(true); }()); return v20144; }()))) {
auto v20151 = ([&]() -> Value { auto fn20152 = s->Global("max"); Arguments args20153; args20153.positional.reserve(2); args20153.Add(Value(int64_t{0}), false); args20153.Add(([&]() -> Value { auto fn20154 = s->Global("int"); Arguments args20155; args20155.Add(([&]() -> Value { auto v20156 = ([&]() -> Value { auto fn20157 = PrepareDictionaryGet(s->LocalAt(38)); Arguments args20158; args20158.positional.reserve(2); args20158.Add(Value("yield_units"), false); args20158.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn20157, std::move(args20158)); }()); if (static_cast<bool>(v20156)) return v20156; v20156 = Value(int64_t{0}); return v20156; }()), false); return Call(c, fn20154, std::move(args20155)); }()), false); return Call(c, fn20152, std::move(args20153)); }());
s->SetAt(42, v20151);
if (static_cast<bool>(s->LocalAt(42))) {
auto v20159 = Get(s->Global("_Y_PRODUCT"), Get(s->LocalAt(38), Value("animal")));
s->SetAt(27, v20159);
auto v20160 = ([&]() -> Value { auto v20161 = ([&]() -> Value { auto fn20162 = PrepareDictionaryGet(Get(s->LocalAt(35), Value("sale"))); Arguments args20163; args20163.positional.reserve(2); args20163.Add(s->LocalAt(27), false); args20163.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn20162, std::move(args20163)); }()); return Binary("Add", v20161, s->LocalAt(42)); }());
Put(Get(s->LocalAt(35), Value("sale")), s->LocalAt(27), v20160);
auto v20164 = s->Global("_Y_REPORT");
auto v20165 = Value("harvest");
auto v20166 = Get(v20164, v20165);
Put(v20164, v20165, Inplace("Add", v20166, s->LocalAt(42)));
}
}
(void)([&]() -> Value { auto fn20167 = Attribute(s->LocalAt(31), "add"); Arguments args20168; args20168.Add(s->LocalAt(34), false); return Call(c, fn20167, std::move(args20168)); }());
}
}
}
}
}
auto v20169 = Tuple({Get(s->LocalAt(44), Value(int64_t{0})), Slice(s->LocalAt(44), Value(int64_t{1}), Value{}, Value{})});
auto unpack20170 = Iterate(v20169);
ValidateUnpack(unpack20170, 2, false);
Put(s->LocalAt(29), Value("farmer"), unpack20170.at(0));
Put(s->LocalAt(29), Value("hands"), unpack20170.at(1));
if (static_cast<bool>(([&]() -> Value { auto fn20171 = PrepareDictionaryGet(s->LocalAt(5)); Arguments args20172; args20172.positional.reserve(2); args20172.Add(Value("boost"), false); args20172.Add(Value(true), false); return CallDictionaryGet(c, fn20171, std::move(args20172)); }()))) {
for (const auto& item20173 : Iterate(([&]() -> Value { auto fn20174 = s->Global("list"); Arguments args20175; args20175.Add(([&]() -> Value { auto fn20176 = Attribute(Get(s->LocalAt(35), Value("sale")), "items"); Arguments args20177; return Call(c, fn20176, std::move(args20177)); }()), false); return Call(c, fn20174, std::move(args20175)); }()))) {
auto unpack20178 = Iterate(item20173);
ValidateUnpack(unpack20178, 2, false);
s->SetAt(27, unpack20178.at(0));
s->SetAt(6, unpack20178.at(1));
auto v20179 = ([&]() -> Value { auto fn20180 = s->Global("min"); Arguments args20181; args20181.positional.reserve(2); args20181.Add(s->LocalAt(6), false); args20181.Add(([&]() -> Value { auto fn20182 = s->Global("int"); Arguments args20183; args20183.Add(([&]() -> Value { auto fn20184 = PrepareDictionaryGet(s->LocalAt(32)); Arguments args20185; args20185.positional.reserve(2); args20185.Add(s->LocalAt(27), false); args20185.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn20184, std::move(args20185)); }()), false); return Call(c, fn20182, std::move(args20183)); }()), false); return Call(c, fn20180, std::move(args20181)); }());
s->SetAt(6, v20179);
auto v20186 = s->LocalAt(6);
Put(Get(s->LocalAt(35), Value("sale")), s->LocalAt(27), v20186);
if (static_cast<bool>(([&]() -> Value { auto v20187 = s->LocalAt(6); Value v20188; v20188 = Value(int64_t{0}); if (!static_cast<bool>(Binary("LtE", v20187, v20188))) return Value(false); v20187 = v20188; return Value(true); }()))) {
continue;
}
auto v20189 = ([&]() -> Value { auto fn20190 = s->Global("sum"); Arguments args20191; args20191.Add(([&]() -> Value { auto comp20192 = std::make_shared<Scope>(); comp20192->globals = s->globals; comp20192->parent = s; static constexpr const char* comp20192_names[] = {"o"}; comp20192->PrepareSlots(comp20192_names); auto result20193 = List(); for (const auto& item20194 : Iterate(s->LocalAt(17))) { comp20192->SetAt(0, item20194); if (!static_cast<bool>(([&]() -> Value { auto v20195 = ([&]() -> Value { auto v20196 = ([&]() -> Value { auto fn20198 = comp20192->Global("len"); Arguments args20199; args20199.Add(comp20192->LocalAt(0), false); return Call(c, fn20198, std::move(args20199)); }()); Value v20197; v20197 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v20196, v20197))) return Value(false); v20196 = v20197; return Value(true); }()); if (!static_cast<bool>(v20195)) return v20195; v20195 = ([&]() -> Value { auto v20200 = Get(comp20192->LocalAt(0), Value(int64_t{0})); Value v20201; v20201 = Value("SELL"); if (!static_cast<bool>(Binary("Eq", v20200, v20201))) return Value(false); v20200 = v20201; return Value(true); }()); if (!static_cast<bool>(v20195)) return v20195; v20195 = ([&]() -> Value { auto v20202 = Get(comp20192->LocalAt(0), Value(int64_t{1})); Value v20203; v20203 = comp20192->Captured("prod"); if (!static_cast<bool>(Binary("Eq", v20202, v20203))) return Value(false); v20202 = v20203; return Value(true); }()); return v20195; }()))) continue; result20193.node()->sequence.push_back(([&]() -> Value { auto fn20204 = comp20192->Global("max"); Arguments args20205; args20205.positional.reserve(2); args20205.Add(Value(int64_t{0}), false); args20205.Add(([&]() -> Value { auto fn20206 = comp20192->Global("int"); Arguments args20207; args20207.Add(Get(comp20192->LocalAt(0), Value(int64_t{2})), false); return Call(c, fn20206, std::move(args20207)); }()), false); return Call(c, fn20204, std::move(args20205)); }())); } return result20193; }()), false); return Call(c, fn20190, std::move(args20191)); }());
s->SetAt(24, v20189);
if (static_cast<bool>(([&]() -> Value { auto v20208 = s->LocalAt(24); Value v20209; v20209 = Value(int64_t{0}); if (!static_cast<bool>(Binary("LtE", v20208, v20209))) return Value(false); v20208 = v20209; return Value(true); }()))) {
continue;
}
auto v20210 = ([&]() -> Value { auto fn20211 = s->Global("min"); Arguments args20212; args20212.positional.reserve(2); args20212.Add(s->LocalAt(6), false); args20212.Add(([&]() -> Value { auto v20213 = ([&]() -> Value { auto fn20214 = s->Global("int"); Arguments args20215; args20215.Add(([&]() -> Value { auto fn20216 = PrepareDictionaryGet(s->LocalAt(32)); Arguments args20217; args20217.positional.reserve(2); args20217.Add(s->LocalAt(27), false); args20217.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn20216, std::move(args20217)); }()), false); return Call(c, fn20214, std::move(args20215)); }()); return Binary("Sub", v20213, s->LocalAt(24)); }()), false); return Call(c, fn20211, std::move(args20212)); }());
s->SetAt(8, v20210);
if (static_cast<bool>(([&]() -> Value { auto v20218 = s->LocalAt(8); Value v20219; v20219 = Value(int64_t{0}); if (!static_cast<bool>(Binary("LtE", v20218, v20219))) return Value(false); v20218 = v20219; return Value(true); }()))) {
continue;
}
for (const auto& item20220 : Iterate(s->LocalAt(17))) {
s->SetAt(19, item20220);
if (static_cast<bool>(([&]() -> Value { auto v20221 = ([&]() -> Value { auto v20222 = ([&]() -> Value { auto fn20224 = s->Global("len"); Arguments args20225; args20225.Add(s->LocalAt(19), false); return Call(c, fn20224, std::move(args20225)); }()); Value v20223; v20223 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v20222, v20223))) return Value(false); v20222 = v20223; return Value(true); }()); if (!static_cast<bool>(v20221)) return v20221; v20221 = ([&]() -> Value { auto v20226 = Get(s->LocalAt(19), Value(int64_t{0})); Value v20227; v20227 = Value("SELL"); if (!static_cast<bool>(Binary("Eq", v20226, v20227))) return Value(false); v20226 = v20227; return Value(true); }()); if (!static_cast<bool>(v20221)) return v20221; v20221 = ([&]() -> Value { auto v20228 = Get(s->LocalAt(19), Value(int64_t{1})); Value v20229; v20229 = s->LocalAt(27); if (!static_cast<bool>(Binary("Eq", v20228, v20229))) return Value(false); v20228 = v20229; return Value(true); }()); if (!static_cast<bool>(v20221)) return v20221; v20221 = ([&]() -> Value { auto v20230 = ([&]() -> Value { auto fn20232 = s->Global("int"); Arguments args20233; args20233.Add(Get(s->LocalAt(19), Value(int64_t{2})), false); return Call(c, fn20232, std::move(args20233)); }()); Value v20231; v20231 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v20230, v20231))) return Value(false); v20230 = v20231; return Value(true); }()); return v20221; }()))) {
auto v20234 = ([&]() -> Value { auto v20235 = ([&]() -> Value { auto fn20236 = s->Global("int"); Arguments args20237; args20237.Add(Get(s->LocalAt(19), Value(int64_t{2})), false); return Call(c, fn20236, std::move(args20237)); }()); return Binary("Add", v20235, s->LocalAt(8)); }());
Put(s->LocalAt(19), Value(int64_t{2}), v20234);
auto v20238 = ([&]() -> Value { auto v20239 = s->LocalAt(6); return Binary("Sub", v20239, s->LocalAt(8)); }());
Put(Get(s->LocalAt(35), Value("sale")), s->LocalAt(27), v20238);
auto v20240 = s->Global("_Y_REPORT");
auto v20241 = Value("boost");
auto v20242 = Get(v20240, v20241);
Put(v20240, v20241, Inplace("Add", v20242, s->LocalAt(8)));
break;
}
}
}
}
return s->LocalAt(29);
return {};
}
}  // namespace kagg::opponents::compiled
