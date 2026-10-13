// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_1dc425f0d5cfa1deb13e(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "actor", "command", "commands", "configuration", "count", "day", "farm", "funded", "gained", "i", "item", "observation", "pending", "player", "previous", "private", "result", "scheduled", "state", "step", "stock", "targets"};
s->PrepareSlots(s_names);
auto v28826 = ([&]() -> Value { auto fn28827 = s->Global("_V233_PARENT"); Arguments args28828; args28828.positional.reserve(2); args28828.Add(s->LocalAt(12), false); args28828.Add(s->LocalAt(4), false); return Call(c, fn28827, std::move(args28828)); }());
s->SetAt(0, v28826);
auto v28829 = ([&]() -> Value { auto fn28830 = s->Global("int"); Arguments args28831; args28831.Add(Get(s->LocalAt(12), Value("step")), false); return Call(c, fn28830, std::move(args28831)); }());
s->SetAt(20, v28829);
auto v28832 = ([&]() -> Value { auto fn28833 = s->Global("int"); Arguments args28834; args28834.Add(Get(s->LocalAt(12), Value("player")), false); return Call(c, fn28833, std::move(args28834)); }());
s->SetAt(14, v28832);
auto v28835 = ([&]() -> Value { auto v28836 = s->LocalAt(20); return Binary("FloorDiv", v28836, Value(int64_t{24})); }());
s->SetAt(6, v28835);
auto v28837 = ([&]() -> Value { auto fn28838 = PrepareDictionaryGet(s->Global("_V233_STATES")); Arguments args28839; args28839.Add(s->LocalAt(14), false); return CallDictionaryGet(c, fn28838, std::move(args28839)); }());
s->SetAt(19, v28837);
if (static_cast<bool>(([&]() -> Value { auto v28840 = ([&]() -> Value { auto v28841 = s->LocalAt(19); Value v28842; v28842 = Value{}; if (!static_cast<bool>(Binary("Is", v28841, v28842))) return Value(false); v28841 = v28842; return Value(true); }()); if (static_cast<bool>(v28840)) return v28840; v28840 = ([&]() -> Value { auto v28843 = s->LocalAt(20); Value v28844; v28844 = Get(s->LocalAt(19), Value("last_step")); if (!static_cast<bool>(Binary("LtE", v28843, v28844))) return Value(false); v28843 = v28844; return Value(true); }()); return v28840; }()))) {
auto v28845 = ([&]() -> Value { auto dict28846 = Dict(); auto key28847 = Value("last_step"); Put(dict28846, key28847, s->LocalAt(20)); auto key28848 = Value("day"); Put(dict28846, key28848, Unary("USub", Value(int64_t{1}))); auto key28849 = Value("workers"); Put(dict28846, key28849, ([&]() -> Value { auto dict28850 = Dict(); return dict28850; }())); auto key28851 = Value("work"); Put(dict28846, key28851, ([&]() -> Value { auto dict28852 = Dict(); return dict28852; }())); auto key28853 = Value("credit"); Put(dict28846, key28853, ([&]() -> Value { auto dict28854 = Dict(); auto key28855 = Value("WOOL"); Put(dict28854, key28855, Value(int64_t{0})); auto key28856 = Value("FERTILIZER"); Put(dict28854, key28856, Value(int64_t{0})); return dict28854; }())); return dict28846; }());
s->SetAt(19, v28845);
auto v28857 = s->LocalAt(19);
Put(s->Global("_V233_STATES"), s->LocalAt(14), v28857);
}
auto v28858 = s->LocalAt(20);
Put(s->LocalAt(19), Value("last_step"), v28858);
if (static_cast<bool>(([&]() -> Value { auto v28859 = ([&]() -> Value { auto v28860 = s->LocalAt(4); Value v28861; v28861 = Value{}; if (!static_cast<bool>(Binary("IsNot", v28860, v28861))) return Value(false); v28860 = v28861; return Value(true); }()); if (!static_cast<bool>(v28859)) return v28859; v28859 = ([&]() -> Value { auto comp28862 = std::make_shared<Scope>(); comp28862->globals = s->globals; comp28862->parent = s; static constexpr const char* comp28862_names[] = {"k", "v"}; comp28862->PrepareSlots(comp28862_names); auto result28863 = List(); for (const auto& item28864 : Iterate(Tuple({Tuple({Value("boardSize"), Value(int64_t{10})}), Tuple({Value("turnsPerDay"), Value(int64_t{24})}), Tuple({Value("shedCapacity"), Value(int64_t{100})}), Tuple({Value("maxMarketOrdersPerTurn"), Value(int64_t{10})})}))) { auto unpack28865 = Iterate(item28864); ValidateUnpack(unpack28865, 2, false); comp28862->SetAt(0, unpack28865.at(0)); comp28862->SetAt(1, unpack28865.at(1)); if (static_cast<bool>(([&]() -> Value { auto v28866 = ([&]() -> Value { auto fn28868 = PrepareDictionaryGet(comp28862->Captured("configuration")); Arguments args28869; args28869.positional.reserve(2); args28869.Add(comp28862->LocalAt(0), false); args28869.Add(comp28862->LocalAt(1), false); return CallDictionaryGet(c, fn28868, std::move(args28869)); }()); Value v28867; v28867 = comp28862->LocalAt(1); if (!static_cast<bool>(Binary("NotEq", v28866, v28867))) return Value(false); v28866 = v28867; return Value(true); }()))) return Value(true); } return Value(false); }()); return v28859; }()))) {
return s->LocalAt(0);
}
if (static_cast<bool>(([&]() -> Value { auto v28870 = s->LocalAt(6); Value v28871; v28871 = Value(int64_t{11}); if (!static_cast<bool>(Binary("Lt", v28870, v28871))) return Value(false); v28870 = v28871; return Value(true); }()))) {
return s->LocalAt(0);
}
auto v28872 = Get(Get(s->LocalAt(12), Value("farms")), s->LocalAt(14));
s->SetAt(7, v28872);
auto v28873 = Get(s->LocalAt(12), Value("private"));
s->SetAt(16, v28873);
if (static_cast<bool>(([&]() -> Value { auto v28874 = Get(s->LocalAt(19), Value("day")); Value v28875; v28875 = s->LocalAt(6); if (!static_cast<bool>(Binary("NotEq", v28874, v28875))) return Value(false); v28874 = v28875; return Value(true); }()))) {
auto v28876 = s->LocalAt(6);
Put(s->LocalAt(19), Value("day"), v28876);
auto v28877 = ([&]() -> Value { auto dict28878 = Dict(); return dict28878; }());
Put(s->LocalAt(19), Value("workers"), v28877);
auto v28879 = ([&]() -> Value { auto dict28880 = Dict(); return dict28880; }());
Put(s->LocalAt(19), Value("work"), v28879);
auto v28881 = Value(int64_t{0});
Put(s->LocalAt(19), Value("rescue_today"), v28881);
}
for (const auto& item28882 : Iterate(([&]() -> Value { auto fn28883 = Attribute(Get(s->LocalAt(19), Value("work")), "items"); Arguments args28884; return Call(c, fn28883, std::move(args28884)); }()))) {
auto unpack28885 = Iterate(item28882);
ValidateUnpack(unpack28885, 2, false);
s->SetAt(1, unpack28885.at(0));
s->SetAt(15, unpack28885.at(1));
if (static_cast<bool>(([&]() -> Value { auto v28886 = ([&]() -> Value { auto v28887 = Get(s->LocalAt(15), Value("step")); Value v28888; v28888 = ([&]() -> Value { auto v28889 = s->LocalAt(20); return Binary("Sub", v28889, Value(int64_t{1})); }()); if (!static_cast<bool>(Binary("NotEq", v28887, v28888))) return Value(false); v28887 = v28888; return Value(true); }()); if (static_cast<bool>(v28886)) return v28886; v28886 = ([&]() -> Value { auto v28890 = s->LocalAt(1); Value v28891; v28891 = ([&]() -> Value { auto fn28892 = s->Global("len"); Arguments args28893; args28893.Add(Get(s->LocalAt(16), Value("inventories")), false); return Call(c, fn28892, std::move(args28893)); }()); if (!static_cast<bool>(Binary("GtE", v28890, v28891))) return Value(false); v28890 = v28891; return Value(true); }()); return v28886; }()))) {
continue;
}
auto v28894 = ([&]() -> Value { auto fn28895 = PrepareDictionaryGet(([&]() -> Value { auto dict28897 = Dict(); auto key28898 = Value("HARVEST"); Put(dict28897, key28898, Value("WOOL")); auto key28899 = Value("COLLECT_FERTILIZER"); Put(dict28897, key28899, Value("FERTILIZER")); return dict28897; }())); Arguments args28896; args28896.Add(Get(Get(s->LocalAt(15), Value("command")), Value(int64_t{0})), false); return CallDictionaryGet(c, fn28895, std::move(args28896)); }());
s->SetAt(11, v28894);
if (static_cast<bool>(s->LocalAt(11))) {
auto v28900 = ([&]() -> Value { auto fn28901 = s->Global("max"); Arguments args28902; args28902.positional.reserve(2); args28902.Add(Value(int64_t{0}), false); args28902.Add(([&]() -> Value { auto v28903 = ([&]() -> Value { auto fn28904 = PrepareDictionaryGet(Get(Get(s->LocalAt(16), Value("inventories")), s->LocalAt(1))); Arguments args28905; args28905.positional.reserve(2); args28905.Add(s->LocalAt(11), false); args28905.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn28904, std::move(args28905)); }()); return Binary("Sub", v28903, ([&]() -> Value { auto fn28906 = PrepareDictionaryGet(Get(s->LocalAt(15), Value("inventory"))); Arguments args28907; args28907.positional.reserve(2); args28907.Add(s->LocalAt(11), false); args28907.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn28906, std::move(args28907)); }())); }()), false); return Call(c, fn28901, std::move(args28902)); }());
s->SetAt(9, v28900);
auto v28908 = Get(s->LocalAt(19), Value("credit"));
auto v28909 = s->LocalAt(11);
auto v28910 = Get(v28908, v28909);
Put(v28908, v28909, Inplace("Add", v28910, s->LocalAt(9)));
auto v28911 = s->Global("_V233_REPORT");
auto v28912 = (static_cast<bool>(([&]() -> Value { auto v28914 = s->LocalAt(11); Value v28915; v28915 = Value("WOOL"); if (!static_cast<bool>(Binary("Eq", v28914, v28915))) return Value(false); v28914 = v28915; return Value(true); }())) ? Value("sheep_wool_harvested") : Value("sheep_fert_collected"));
auto v28913 = Get(v28911, v28912);
Put(v28911, v28912, Inplace("Add", v28913, s->LocalAt(9)));
}
}
auto v28916 = ([&]() -> Value { auto fn28917 = Attribute(s->LocalAt(19), "pop"); Arguments args28918; args28918.positional.reserve(2); args28918.Add(Value("pending"), false); args28918.Add(Value{}, false); return Call(c, fn28917, std::move(args28918)); }());
s->SetAt(13, v28916);
if (static_cast<bool>(s->LocalAt(13))) {
auto v28919 = ([&]() -> Value { auto v28920 = ([&]() -> Value { auto v28921 = Value("SE"); Value v28922; v28922 = Get(s->LocalAt(7), Value("unlocked_quadrants")); if (!static_cast<bool>(Binary("In", v28921, v28922))) return Value(false); v28921 = v28922; return Value(true); }()); if (!static_cast<bool>(v28920)) return v28920; v28920 = ([&]() -> Value { auto v28923 = Unary("Not", Get(s->LocalAt(13), Value("initial"))); if (static_cast<bool>(v28923)) return v28923; v28923 = ([&]() -> Value { auto v28924 = ([&]() -> Value { auto fn28926 = PrepareDictionaryGet(Get(s->LocalAt(16), Value("shed"))); Arguments args28927; args28927.positional.reserve(2); args28927.Add(Value("SHEEP"), false); args28927.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn28926, std::move(args28927)); }()); Value v28925; v28925 = Value(int64_t{6}); if (!static_cast<bool>(Binary("GtE", v28924, v28925))) return Value(false); v28924 = v28925; return Value(true); }()); return v28923; }()); return v28920; }());
s->SetAt(8, v28919);
if (static_cast<bool>(Unary("Not", s->LocalAt(8)))) {
auto v28928 = s->Global("_V233_REPORT");
auto v28929 = Value("sheep_purchase_shortfalls");
auto v28930 = Get(v28928, v28929);
Put(v28928, v28929, Inplace("Add", v28930, Value(int64_t{1})));
}
else {
if (static_cast<bool>(([&]() -> Value { auto v28931 = ([&]() -> Value { auto fn28933 = s->Global("len"); Arguments args28934; args28934.Add(Get(s->LocalAt(7), Value("hands")), false); return Call(c, fn28933, std::move(args28934)); }()); Value v28932; v28932 = ([&]() -> Value { auto v28935 = ([&]() -> Value { auto v28936 = Get(s->LocalAt(13), Value("first")); return Binary("Add", v28936, ([&]() -> Value { auto fn28937 = PrepareDictionaryGet(s->LocalAt(13)); Arguments args28938; args28938.positional.reserve(2); args28938.Add(Value("count"), false); args28938.Add(Value(int64_t{2}), false); return CallDictionaryGet(c, fn28937, std::move(args28938)); }())); }()); return Binary("Sub", v28935, Value(int64_t{1})); }()); if (!static_cast<bool>(Binary("Lt", v28931, v28932))) return Value(false); v28931 = v28932; return Value(true); }()))) {
auto v28939 = s->Global("_V233_REPORT");
auto v28940 = Value("sheep_hire_shortfalls");
auto v28941 = Get(v28939, v28940);
Put(v28939, v28940, Inplace("Add", v28941, Value(int64_t{1})));
}
else {
if (static_cast<bool>(([&]() -> Value { auto v28942 = ([&]() -> Value { auto fn28944 = PrepareDictionaryGet(s->LocalAt(13)); Arguments args28945; args28945.positional.reserve(2); args28945.Add(Value("count"), false); args28945.Add(Value(int64_t{2}), false); return CallDictionaryGet(c, fn28944, std::move(args28945)); }()); Value v28943; v28943 = Value(int64_t{1}); if (!static_cast<bool>(Binary("Eq", v28942, v28943))) return Value(false); v28942 = v28943; return Value(true); }()))) {
auto v28946 = ([&]() -> Value { auto fn28947 = s->Global("list"); Arguments args28948; args28948.Add(Get(s->LocalAt(13), Value("targets")), false); return Call(c, fn28947, std::move(args28948)); }());
Put(Get(s->LocalAt(19), Value("workers")), Get(s->LocalAt(13), Value("first")), v28946);
auto v28949 = s->Global("_SL_REPORT");
auto v28950 = Value("confirmed");
auto v28951 = Get(v28949, v28950);
Put(v28949, v28950, Inplace("Add", v28951, Value(int64_t{1})));
}
else {
for (const auto& item28952 : Iterate(([&]() -> Value { auto fn28953 = s->Global("range"); Arguments args28954; args28954.Add(Value(int64_t{2}), false); return Call(c, fn28953, std::move(args28954)); }()))) {
s->SetAt(10, item28952);
auto v28955 = ([&]() -> Value { auto comp28956 = std::make_shared<Scope>(); comp28956->globals = s->globals; comp28956->parent = s; static constexpr const char* comp28956_names[] = {"x"}; comp28956->PrepareSlots(comp28956_names); auto result28957 = List(); for (const auto& item28958 : Iterate(([&]() -> Value { auto fn28959 = s->Global("range"); Arguments args28960; args28960.positional.reserve(2); args28960.Add(Value(int64_t{5}), false); args28960.Add(Value(int64_t{8}), false); return Call(c, fn28959, std::move(args28960)); }()))) { comp28956->SetAt(0, item28958); result28957.node()->sequence.push_back(Tuple({comp28956->LocalAt(0), ([&]() -> Value { auto v28961 = Value(int64_t{5}); return Binary("Add", v28961, comp28956->Captured("i")); }())})); } return result28957; }());
Put(Get(s->LocalAt(19), Value("workers")), ([&]() -> Value { auto v28962 = Get(s->LocalAt(13), Value("first")); return Binary("Add", v28962, s->LocalAt(10)); }()), v28955);
}
}
auto v28963 = s->Global("_V233_REPORT");
auto v28964 = Value("sheep_workers_confirmed");
auto v28965 = Get(v28963, v28964);
Put(v28963, v28964, Inplace("Add", v28965, ([&]() -> Value { auto fn28966 = PrepareDictionaryGet(s->LocalAt(13)); Arguments args28967; args28967.positional.reserve(2); args28967.Add(Value("count"), false); args28967.Add(Value(int64_t{2}), false); return CallDictionaryGet(c, fn28966, std::move(args28967)); }())));
if (static_cast<bool>(Get(s->LocalAt(13), Value("initial")))) {
auto v28968 = Value(true);
Put(s->LocalAt(19), Value("committed"), v28968);
auto v28969 = s->Global("_V233_REPORT");
auto v28970 = Value("sheep_committed");
auto v28971 = Get(v28969, v28970);
Put(v28969, v28970, Inplace("Add", v28971, Value(int64_t{1})));
}
}
}
}
auto v28972 = ([&]() -> Value { auto fn28973 = s->Global("_v233_request"); Arguments args28974; args28974.positional.reserve(4); args28974.Add(s->LocalAt(12), false); args28974.Add(s->LocalAt(0), false); args28974.Add(s->LocalAt(19), false); args28974.Add(Get(Attribute(Attribute(s->Global("_IMPL"), "chassis"), "players"), s->LocalAt(14)), false); return Call(c, fn28973, std::move(args28974)); }());
s->SetAt(0, v28972);
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto fn28975 = PrepareDictionaryGet(s->LocalAt(19)); Arguments args28976; args28976.Add(Value("committed"), false); return CallDictionaryGet(c, fn28975, std::move(args28976)); }())))) {
return s->LocalAt(0);
}
auto v28977 = ([&]() -> Value { auto fn28978 = Attribute(s->Global("copy"), "deepcopy"); Arguments args28979; args28979.Add(s->LocalAt(0), false); return Call(c, fn28978, std::move(args28979)); }());
s->SetAt(17, v28977);
auto v28980 = ([&]() -> Value { auto v28981 = List({([&]() -> Value { auto v28982 = ([&]() -> Value { auto fn28983 = PrepareDictionaryGet(s->LocalAt(17)); Arguments args28984; args28984.Add(Value("farmer"), false); return CallDictionaryGet(c, fn28983, std::move(args28984)); }()); if (static_cast<bool>(v28982)) return v28982; v28982 = List({Value("PASS")}); return v28982; }())}); return Binary("Add", v28981, ([&]() -> Value { auto fn28985 = s->Global("list"); Arguments args28986; args28986.Add(([&]() -> Value { auto v28987 = ([&]() -> Value { auto fn28988 = PrepareDictionaryGet(s->LocalAt(17)); Arguments args28989; args28989.Add(Value("hands"), false); return CallDictionaryGet(c, fn28988, std::move(args28989)); }()); if (static_cast<bool>(v28987)) return v28987; v28987 = List({}); return v28987; }()), false); return Call(c, fn28985, std::move(args28986)); }())); }());
s->SetAt(3, v28980);
auto v28990 = s->LocalAt(3);
s->SetAt(3, Inplace("Add", v28990, ([&]() -> Value { auto comp28991 = std::make_shared<Scope>(); comp28991->globals = s->globals; comp28991->parent = s; static constexpr const char* comp28991_names[] = {"_"}; comp28991->PrepareSlots(comp28991_names); auto result28992 = List(); for (const auto& item28993 : Iterate(([&]() -> Value { auto fn28994 = s->Global("range"); Arguments args28995; args28995.Add(([&]() -> Value { auto v28996 = ([&]() -> Value { auto v28997 = ([&]() -> Value { auto fn28998 = s->Global("len"); Arguments args28999; args28999.Add(Get(s->LocalAt(7), Value("hands")), false); return Call(c, fn28998, std::move(args28999)); }()); return Binary("Add", v28997, Value(int64_t{1})); }()); return Binary("Sub", v28996, ([&]() -> Value { auto fn29000 = s->Global("len"); Arguments args29001; args29001.Add(s->LocalAt(3), false); return Call(c, fn29000, std::move(args29001)); }())); }()), false); return Call(c, fn28994, std::move(args28995)); }()))) { comp28991->SetAt(0, item28993); result28992.node()->sequence.push_back(List({Value("PASS")})); } return result28992; }())));
auto v29002 = ([&]() -> Value { auto dict29003 = Dict(); return dict29003; }());
Put(s->LocalAt(19), Value("work"), v29002);
for (const auto& item29004 : Iterate(([&]() -> Value { auto fn29005 = Attribute(Get(s->LocalAt(19), Value("workers")), "items"); Arguments args29006; return Call(c, fn29005, std::move(args29006)); }()))) {
auto unpack29007 = Iterate(item29004);
ValidateUnpack(unpack29007, 2, false);
s->SetAt(1, unpack29007.at(0));
s->SetAt(22, unpack29007.at(1));
auto v29008 = ([&]() -> Value { auto fn29009 = s->Global("_v233_worker"); Arguments args29010; args29010.positional.reserve(3); args29010.Add(s->LocalAt(12), false); args29010.Add(s->LocalAt(1), false); args29010.Add(s->LocalAt(22), false); return Call(c, fn29009, std::move(args29010)); }());
s->SetAt(2, v29008);
auto v29011 = s->LocalAt(2);
Put(s->LocalAt(3), s->LocalAt(1), v29011);
auto v29012 = ([&]() -> Value { auto dict29013 = Dict(); auto key29014 = Value("step"); Put(dict29013, key29014, s->LocalAt(20)); auto key29015 = Value("command"); Put(dict29013, key29015, s->LocalAt(2)); auto key29016 = Value("inventory"); Put(dict29013, key29016, ([&]() -> Value { auto fn29017 = s->Global("dict"); Arguments args29018; args29018.Add(Get(Get(s->LocalAt(16), Value("inventories")), s->LocalAt(1)), false); return Call(c, fn29017, std::move(args29018)); }())); return dict29013; }());
Put(Get(s->LocalAt(19), Value("work")), s->LocalAt(1), v29012);
}
auto v29019 = Tuple({Get(s->LocalAt(3), Value(int64_t{0})), Slice(s->LocalAt(3), Value(int64_t{1}), Value{}, Value{})});
auto unpack29020 = Iterate(v29019);
ValidateUnpack(unpack29020, 2, false);
Put(s->LocalAt(17), Value("farmer"), unpack29020.at(0));
Put(s->LocalAt(17), Value("hands"), unpack29020.at(1));
auto v29021 = ([&]() -> Value { auto fn29022 = s->Global("_v234_rescue"); Arguments args29023; args29023.positional.reserve(3); args29023.Add(s->LocalAt(12), false); args29023.Add(s->LocalAt(17), false); args29023.Add(s->LocalAt(19), false); return Call(c, fn29022, std::move(args29023)); }());
s->SetAt(17, v29021);
auto v29024 = ([&]() -> Value { auto fn29025 = s->Global("projected_shed"); Arguments args29026; args29026.positional.reserve(2); args29026.Add(s->LocalAt(17), false); args29026.Add(([&]() -> Value { auto fn29027 = s->Global("FarmView"); Arguments args29028; args29028.Add(s->LocalAt(12), false); return Call(c, fn29027, std::move(args29028)); }()), false); return Call(c, fn29025, std::move(args29026)); }());
s->SetAt(21, v29024);
for (const auto& item29029 : Iterate(Tuple({Value("WOOL"), Value("FERTILIZER")}))) {
s->SetAt(11, item29029);
auto v29030 = ([&]() -> Value { auto fn29031 = s->Global("sum"); Arguments args29032; args29032.Add(([&]() -> Value { auto comp29033 = std::make_shared<Scope>(); comp29033->globals = s->globals; comp29033->parent = s; static constexpr const char* comp29033_names[] = {"o"}; comp29033->PrepareSlots(comp29033_names); auto result29034 = List(); for (const auto& item29035 : Iterate(Get(s->LocalAt(17), Value("market")))) { comp29033->SetAt(0, item29035); if (!static_cast<bool>(([&]() -> Value { auto v29036 = Slice(comp29033->LocalAt(0), Value{}, Value(int64_t{2}), Value{}); Value v29037; v29037 = List({Value("SELL"), comp29033->Captured("item")}); if (!static_cast<bool>(Binary("Eq", v29036, v29037))) return Value(false); v29036 = v29037; return Value(true); }()))) continue; result29034.node()->sequence.push_back(([&]() -> Value { auto fn29038 = comp29033->Global("int"); Arguments args29039; args29039.Add(Get(comp29033->LocalAt(0), Value(int64_t{2})), false); return Call(c, fn29038, std::move(args29039)); }())); } return result29034; }()), false); return Call(c, fn29031, std::move(args29032)); }());
s->SetAt(18, v29030);
auto v29040 = ([&]() -> Value { auto fn29041 = s->Global("min"); Arguments args29042; args29042.positional.reserve(2); args29042.Add(Get(Get(s->LocalAt(19), Value("credit")), s->LocalAt(11)), false); args29042.Add(([&]() -> Value { auto fn29043 = s->Global("max"); Arguments args29044; args29044.positional.reserve(2); args29044.Add(Value(int64_t{0}), false); args29044.Add(([&]() -> Value { auto v29045 = ([&]() -> Value { auto fn29046 = PrepareDictionaryGet(s->LocalAt(21)); Arguments args29047; args29047.positional.reserve(2); args29047.Add(s->LocalAt(11), false); args29047.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn29046, std::move(args29047)); }()); return Binary("Sub", v29045, s->LocalAt(18)); }()), false); return Call(c, fn29043, std::move(args29044)); }()), false); return Call(c, fn29041, std::move(args29042)); }());
s->SetAt(5, v29040);
if (static_cast<bool>(([&]() -> Value { auto v29048 = s->LocalAt(5); if (!static_cast<bool>(v29048)) return v29048; v29048 = ([&]() -> Value { auto v29049 = ([&]() -> Value { auto fn29051 = s->Global("len"); Arguments args29052; args29052.Add(Get(s->LocalAt(17), Value("market")), false); return Call(c, fn29051, std::move(args29052)); }()); Value v29050; v29050 = s->Global("MAX_ORDERS"); if (!static_cast<bool>(Binary("Lt", v29049, v29050))) return Value(false); v29049 = v29050; return Value(true); }()); return v29048; }()))) {
(void)([&]() -> Value { auto fn29053 = Attribute(Get(s->LocalAt(17), Value("market")), "append"); Arguments args29054; args29054.Add(List({Value("SELL"), s->LocalAt(11), s->LocalAt(5)}), false); return Call(c, fn29053, std::move(args29054)); }());
auto v29055 = Get(s->LocalAt(19), Value("credit"));
auto v29056 = s->LocalAt(11);
auto v29057 = Get(v29055, v29056);
Put(v29055, v29056, Inplace("Sub", v29057, s->LocalAt(5)));
auto v29058 = s->Global("_V233_REPORT");
auto v29059 = (static_cast<bool>(([&]() -> Value { auto v29061 = s->LocalAt(11); Value v29062; v29062 = Value("WOOL"); if (!static_cast<bool>(Binary("Eq", v29061, v29062))) return Value(false); v29061 = v29062; return Value(true); }())) ? Value("sheep_extra_wool_sales") : Value("sheep_extra_fert_sales"));
auto v29060 = Get(v29058, v29059);
Put(v29058, v29059, Inplace("Add", v29060, s->LocalAt(5)));
}
}
return s->LocalAt(17);
return {};
}
}  // namespace kagg::opponents::compiled
