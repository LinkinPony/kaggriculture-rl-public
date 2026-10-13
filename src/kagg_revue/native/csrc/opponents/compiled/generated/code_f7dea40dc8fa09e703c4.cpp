// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_f7dea40dc8fa09e703c4(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "already", "cfg", "future", "item", "next_sup", "nxt", "o", "planned", "projected", "qty", "route", "self", "step", "tape", "unlock_period", "view"};
s->PrepareSlots(s_names);
auto v955 = Attribute(s->LocalAt(12), "cfg");
s->SetAt(2, v955);
auto v956 = ([&]() -> Value { auto v957 = s->LocalAt(13); return Binary("Add", v957, Value(int64_t{1})); }());
s->SetAt(6, v956);
auto v958 = ([&]() -> Value { auto v959 = Value(int64_t{3}); return Binary("Mult", v959, Get(s->LocalAt(2), Value("turns_per_day"))); }());
s->SetAt(15, v958);
if (static_cast<bool>(([&]() -> Value { auto v960 = ([&]() -> Value { auto v961 = s->LocalAt(6); Value v962; v962 = s->Global("LAST_ACT_STEP"); if (!static_cast<bool>(Binary("Gt", v961, v962))) return Value(false); v961 = v962; return Value(true); }()); if (static_cast<bool>(v960)) return v960; v960 = ([&]() -> Value { auto v963 = ([&]() -> Value { auto v965 = s->LocalAt(6); return Binary("Mod", v965, s->LocalAt(15)); }()); Value v964; v964 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v963, v964))) return Value(false); v963 = v964; return Value(true); }()); if (static_cast<bool>(v960)) return v960; v960 = ([&]() -> Value { auto v966 = ([&]() -> Value { auto v968 = s->LocalAt(13); return Binary("Mod", v968, Value(int64_t{4})); }()); Value v967; v967 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v966, v967))) return Value(false); v966 = v967; return Value(true); }()); return v960; }()))) {
return Value{};
}
auto v969 = Get(Attribute(s->LocalAt(12), "routes"), s->LocalAt(11));
s->SetAt(14, v969);
auto v970 = (static_cast<bool>(([&]() -> Value { auto v971 = ([&]() -> Value { auto v972 = s->LocalAt(6); Value v973; v973 = ([&]() -> Value { auto fn974 = s->Global("len"); Arguments args975; args975.Add(s->LocalAt(14), false); return Call(c, fn974, std::move(args975)); }()); if (!static_cast<bool>(Binary("Lt", v972, v973))) return Value(false); v972 = v973; return Value(true); }()); if (!static_cast<bool>(v971)) return v971; v971 = ([&]() -> Value { auto fn976 = s->Global("isinstance"); Arguments args977; args977.positional.reserve(2); args977.Add(Get(s->LocalAt(14), s->LocalAt(6)), false); args977.Add(s->Global("dict"), false); return Call(c, fn976, std::move(args977)); }()); return v971; }())) ? Get(s->LocalAt(14), s->LocalAt(6)) : ([&]() -> Value { auto dict978 = Dict(); return dict978; }()));
s->SetAt(3, v970);
auto v979 = ([&]() -> Value { auto dict980 = Dict(); return dict980; }());
s->SetAt(8, v979);
for (const auto& item981 : Iterate(([&]() -> Value { auto v982 = ([&]() -> Value { auto fn983 = PrepareDictionaryGet(s->LocalAt(3)); Arguments args984; args984.Add(Value("market"), false); return CallDictionaryGet(c, fn983, std::move(args984)); }()); if (static_cast<bool>(v982)) return v982; v982 = List({}); return v982; }()))) {
s->SetAt(7, item981);
if (static_cast<bool>(([&]() -> Value { auto v985 = s->LocalAt(7); if (!static_cast<bool>(v985)) return v985; v985 = ([&]() -> Value { auto v986 = Get(s->LocalAt(7), Value(int64_t{0})); Value v987; v987 = Value("SELL"); if (!static_cast<bool>(Binary("Eq", v986, v987))) return Value(false); v986 = v987; return Value(true); }()); if (!static_cast<bool>(v985)) return v985; v985 = ([&]() -> Value { auto v988 = ([&]() -> Value { auto fn990 = s->Global("len"); Arguments args991; args991.Add(s->LocalAt(7), false); return Call(c, fn990, std::move(args991)); }()); Value v989; v989 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v988, v989))) return Value(false); v988 = v989; return Value(true); }()); if (!static_cast<bool>(v985)) return v985; v985 = ([&]() -> Value { auto v992 = Get(s->LocalAt(7), Value(int64_t{1})); Value v993; v993 = s->Global("PRODUCTS"); if (!static_cast<bool>(Binary("In", v992, v993))) return Value(false); v992 = v993; return Value(true); }()); return v985; }()))) {
auto v994 = ([&]() -> Value { auto v995 = ([&]() -> Value { auto fn996 = PrepareDictionaryGet(s->LocalAt(8)); Arguments args997; args997.positional.reserve(2); args997.Add(Get(s->LocalAt(7), Value(int64_t{1})), false); args997.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn996, std::move(args997)); }()); return Binary("Add", v995, ([&]() -> Value { auto fn998 = s->Global("max"); Arguments args999; args999.positional.reserve(2); args999.Add(Value(int64_t{0}), false); args999.Add(([&]() -> Value { auto fn1000 = s->Global("_int"); Arguments args1001; args1001.Add(Get(s->LocalAt(7), Value(int64_t{2})), false); return Call(c, fn1000, std::move(args1001)); }()), false); return Call(c, fn998, std::move(args999)); }())); }());
Put(s->LocalAt(8), Get(s->LocalAt(7), Value(int64_t{1})), v994);
}
}
auto v1002 = ([&]() -> Value { auto comp1003 = std::make_shared<Scope>(); comp1003->globals = s->globals; comp1003->parent = s; static constexpr const char* comp1003_names[] = {"o"}; comp1003->PrepareSlots(comp1003_names); auto result1004 = List(); for (const auto& item1005 : Iterate(([&]() -> Value { auto v1006 = ([&]() -> Value { auto fn1007 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args1008; args1008.Add(Value("market"), false); return CallDictionaryGet(c, fn1007, std::move(args1008)); }()); if (static_cast<bool>(v1006)) return v1006; v1006 = List({}); return v1006; }()))) { comp1003->SetAt(0, item1005); if (!static_cast<bool>(([&]() -> Value { auto v1009 = comp1003->LocalAt(0); if (!static_cast<bool>(v1009)) return v1009; v1009 = ([&]() -> Value { auto v1010 = Get(comp1003->LocalAt(0), Value(int64_t{0})); Value v1011; v1011 = Value("SELL"); if (!static_cast<bool>(Binary("Eq", v1010, v1011))) return Value(false); v1010 = v1011; return Value(true); }()); if (!static_cast<bool>(v1009)) return v1009; v1009 = ([&]() -> Value { auto v1012 = ([&]() -> Value { auto fn1014 = comp1003->Global("len"); Arguments args1015; args1015.Add(comp1003->LocalAt(0), false); return Call(c, fn1014, std::move(args1015)); }()); Value v1013; v1013 = Value(int64_t{1}); if (!static_cast<bool>(Binary("Gt", v1012, v1013))) return Value(false); v1012 = v1013; return Value(true); }()); return v1009; }()))) continue; result1004.node()->sequence.push_back(Get(comp1003->LocalAt(0), Value(int64_t{1}))); } return Set(result1004.node()->sequence); }());
s->SetAt(1, v1002);
for (const auto& item1016 : Iterate(s->Global("PRODUCTS"))) {
s->SetAt(4, item1016);
if (static_cast<bool>(([&]() -> Value { auto v1017 = ([&]() -> Value { auto v1018 = s->LocalAt(4); Value v1019; v1019 = Tuple({Value("WHEAT"), Value("FERTILIZER")}); if (!static_cast<bool>(Binary("In", v1018, v1019))) return Value(false); v1018 = v1019; return Value(true); }()); if (static_cast<bool>(v1017)) return v1017; v1017 = ([&]() -> Value { auto v1020 = ([&]() -> Value { auto fn1022 = PrepareDictionaryGet(s->LocalAt(8)); Arguments args1023; args1023.positional.reserve(2); args1023.Add(s->LocalAt(4), false); args1023.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn1022, std::move(args1023)); }()); Value v1021; v1021 = Value(int64_t{0}); if (!static_cast<bool>(Binary("LtE", v1020, v1021))) return Value(false); v1020 = v1021; return Value(true); }()); if (static_cast<bool>(v1017)) return v1017; v1017 = ([&]() -> Value { auto v1024 = s->LocalAt(4); Value v1025; v1025 = s->LocalAt(1); if (!static_cast<bool>(Binary("In", v1024, v1025))) return Value(false); v1024 = v1025; return Value(true); }()); return v1017; }()))) {
continue;
}
auto v1026 = ([&]() -> Value { auto fn1027 = s->Global("min"); Arguments args1028; args1028.positional.reserve(2); args1028.Add(([&]() -> Value { auto fn1029 = PrepareDictionaryGet(s->LocalAt(9)); Arguments args1030; args1030.positional.reserve(2); args1030.Add(s->LocalAt(4), false); args1030.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn1029, std::move(args1030)); }()), false); args1028.Add(Get(s->LocalAt(8), s->LocalAt(4)), false); return Call(c, fn1027, std::move(args1028)); }());
s->SetAt(10, v1026);
if (static_cast<bool>(([&]() -> Value { auto v1031 = ([&]() -> Value { auto v1032 = s->LocalAt(10); Value v1033; v1033 = Value(int64_t{0}); if (!static_cast<bool>(Binary("LtE", v1032, v1033))) return Value(false); v1032 = v1033; return Value(true); }()); if (static_cast<bool>(v1031)) return v1031; v1031 = ([&]() -> Value { auto v1034 = ([&]() -> Value { auto fn1036 = PrepareDictionaryGet(Attribute(s->LocalAt(16), "prices")); Arguments args1037; args1037.positional.reserve(2); args1037.Add(s->LocalAt(4), false); args1037.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn1036, std::move(args1037)); }()); Value v1035; v1035 = Get(s->LocalAt(2), Value("min_sell_price")); if (!static_cast<bool>(Binary("Lt", v1034, v1035))) return Value(false); v1034 = v1035; return Value(true); }()); return v1031; }()))) {
continue;
}
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto fn1038 = Attribute(s->LocalAt(12), "_add_sell"); Arguments args1039; args1039.positional.reserve(4); args1039.Add(s->LocalAt(0), false); args1039.Add(s->LocalAt(4), false); args1039.Add(s->LocalAt(10), false); args1039.Add(Get(s->LocalAt(2), Value("max_orders")), false); args1039.Keyword("merge", Value(false)); return Call(c, fn1038, std::move(args1039)); }())))) {
break;
}
auto v1040 = s->LocalAt(9);
auto v1041 = s->LocalAt(4);
auto v1042 = Get(v1040, v1041);
Put(v1040, v1041, Inplace("Sub", v1042, s->LocalAt(10)));
auto v1043 = ([&]() -> Value { auto v1044 = ([&]() -> Value { auto fn1045 = PrepareDictionaryGet(Get(s->LocalAt(5), Value("suppress"))); Arguments args1046; args1046.positional.reserve(2); args1046.Add(s->LocalAt(4), false); args1046.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn1045, std::move(args1046)); }()); return Binary("Add", v1044, s->LocalAt(10)); }());
Put(Get(s->LocalAt(5), Value("suppress")), s->LocalAt(4), v1043);
}
if (static_cast<bool>(Get(s->LocalAt(5), Value("suppress")))) {
auto v1047 = s->LocalAt(6);
Put(s->LocalAt(5), Value("due_step"), v1047);
}
return {};
}
}  // namespace kagg::opponents::compiled
