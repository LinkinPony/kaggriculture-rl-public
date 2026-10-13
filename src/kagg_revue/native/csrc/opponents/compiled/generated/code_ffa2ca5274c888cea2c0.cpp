// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_ffa2ca5274c888cea2c0(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "already", "cfg", "item", "next_sup", "nxt", "o", "own_next", "plan", "projected", "qty", "route", "self", "step", "view"};
s->PrepareSlots(s_names);
auto v1048 = Attribute(s->LocalAt(12), "cfg");
s->SetAt(2, v1048);
auto v1049 = ([&]() -> Value { auto v1050 = s->LocalAt(13); return Binary("Add", v1050, Value(int64_t{1})); }());
s->SetAt(5, v1049);
auto v1051 = Attribute(s->LocalAt(12), "opponent_plan");
s->SetAt(8, v1051);
if (static_cast<bool>(([&]() -> Value { auto v1052 = ([&]() -> Value { auto v1053 = s->LocalAt(5); Value v1054; v1054 = s->Global("LAST_ACT_STEP"); if (!static_cast<bool>(Binary("Gt", v1053, v1054))) return Value(false); v1053 = v1054; return Value(true); }()); if (static_cast<bool>(v1052)) return v1052; v1052 = ([&]() -> Value { auto v1055 = s->LocalAt(5); Value v1056; v1056 = ([&]() -> Value { auto fn1057 = s->Global("len"); Arguments args1058; args1058.Add(s->LocalAt(8), false); return Call(c, fn1057, std::move(args1058)); }()); if (!static_cast<bool>(Binary("GtE", v1055, v1056))) return Value(false); v1055 = v1056; return Value(true); }()); if (static_cast<bool>(v1052)) return v1052; v1052 = Unary("Not", ([&]() -> Value { auto fn1059 = s->Global("isinstance"); Arguments args1060; args1060.positional.reserve(2); args1060.Add(Get(s->LocalAt(8), s->LocalAt(5)), false); args1060.Add(s->Global("dict"), false); return Call(c, fn1059, std::move(args1060)); }())); return v1052; }()))) {
return Value{};
}
auto v1061 = ([&]() -> Value { auto comp1062 = std::make_shared<Scope>(); comp1062->globals = s->globals; comp1062->parent = s; static constexpr const char* comp1062_names[] = {"o"}; comp1062->PrepareSlots(comp1062_names); auto result1063 = List(); for (const auto& item1064 : Iterate(([&]() -> Value { auto v1065 = ([&]() -> Value { auto fn1066 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args1067; args1067.Add(Value("market"), false); return CallDictionaryGet(c, fn1066, std::move(args1067)); }()); if (static_cast<bool>(v1065)) return v1065; v1065 = List({}); return v1065; }()))) { comp1062->SetAt(0, item1064); if (!static_cast<bool>(([&]() -> Value { auto v1068 = comp1062->LocalAt(0); if (!static_cast<bool>(v1068)) return v1068; v1068 = ([&]() -> Value { auto v1069 = Get(comp1062->LocalAt(0), Value(int64_t{0})); Value v1070; v1070 = Value("SELL"); if (!static_cast<bool>(Binary("Eq", v1069, v1070))) return Value(false); v1069 = v1070; return Value(true); }()); if (!static_cast<bool>(v1068)) return v1068; v1068 = ([&]() -> Value { auto v1071 = ([&]() -> Value { auto fn1073 = comp1062->Global("len"); Arguments args1074; args1074.Add(comp1062->LocalAt(0), false); return Call(c, fn1073, std::move(args1074)); }()); Value v1072; v1072 = Value(int64_t{1}); if (!static_cast<bool>(Binary("Gt", v1071, v1072))) return Value(false); v1071 = v1072; return Value(true); }()); return v1068; }()))) continue; result1063.node()->sequence.push_back(Get(comp1062->LocalAt(0), Value(int64_t{1}))); } return Set(result1063.node()->sequence); }());
s->SetAt(1, v1061);
for (const auto& item1075 : Iterate(([&]() -> Value { auto v1076 = ([&]() -> Value { auto fn1077 = PrepareDictionaryGet(Get(s->LocalAt(8), s->LocalAt(5))); Arguments args1078; args1078.Add(Value("market"), false); return CallDictionaryGet(c, fn1077, std::move(args1078)); }()); if (static_cast<bool>(v1076)) return v1076; v1076 = List({}); return v1076; }()))) {
s->SetAt(6, item1075);
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto v1079 = s->LocalAt(6); if (!static_cast<bool>(v1079)) return v1079; v1079 = ([&]() -> Value { auto v1080 = Get(s->LocalAt(6), Value(int64_t{0})); Value v1081; v1081 = Value("SELL"); if (!static_cast<bool>(Binary("Eq", v1080, v1081))) return Value(false); v1080 = v1081; return Value(true); }()); if (!static_cast<bool>(v1079)) return v1079; v1079 = ([&]() -> Value { auto v1082 = ([&]() -> Value { auto fn1084 = s->Global("len"); Arguments args1085; args1085.Add(s->LocalAt(6), false); return Call(c, fn1084, std::move(args1085)); }()); Value v1083; v1083 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v1082, v1083))) return Value(false); v1082 = v1083; return Value(true); }()); if (!static_cast<bool>(v1079)) return v1079; v1079 = ([&]() -> Value { auto v1086 = Get(s->LocalAt(6), Value(int64_t{1})); Value v1087; v1087 = s->Global("FRONT_RUN_ITEMS"); if (!static_cast<bool>(Binary("In", v1086, v1087))) return Value(false); v1086 = v1087; return Value(true); }()); return v1079; }())))) {
continue;
}
auto v1088 = Get(s->LocalAt(6), Value(int64_t{1}));
s->SetAt(3, v1088);
if (static_cast<bool>(([&]() -> Value { auto v1089 = ([&]() -> Value { auto v1090 = s->LocalAt(3); Value v1091; v1091 = s->LocalAt(1); if (!static_cast<bool>(Binary("In", v1090, v1091))) return Value(false); v1090 = v1091; return Value(true); }()); if (static_cast<bool>(v1089)) return v1089; v1089 = ([&]() -> Value { auto v1092 = ([&]() -> Value { auto fn1094 = PrepareDictionaryGet(Attribute(s->LocalAt(14), "prices")); Arguments args1095; args1095.positional.reserve(2); args1095.Add(s->LocalAt(3), false); args1095.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn1094, std::move(args1095)); }()); Value v1093; v1093 = Get(s->LocalAt(2), Value("min_sell_price")); if (!static_cast<bool>(Binary("Lt", v1092, v1093))) return Value(false); v1092 = v1093; return Value(true); }()); return v1089; }()))) {
continue;
}
auto v1096 = ([&]() -> Value { auto fn1097 = s->Global("sum"); Arguments args1098; args1098.Add(([&]() -> Value { auto comp1099 = std::make_shared<Scope>(); comp1099->globals = s->globals; comp1099->parent = s; static constexpr const char* comp1099_names[] = {"x"}; comp1099->PrepareSlots(comp1099_names); auto result1100 = List(); for (const auto& item1101 : Iterate(([&]() -> Value { auto fn1102 = PrepareDictionaryGet(Get(Get(Attribute(s->LocalAt(12), "routes"), s->LocalAt(11)), s->LocalAt(5))); Arguments args1103; args1103.positional.reserve(2); args1103.Add(Value("market"), false); args1103.Add(List({}), false); return CallDictionaryGet(c, fn1102, std::move(args1103)); }()))) { comp1099->SetAt(0, item1101); if (!static_cast<bool>(([&]() -> Value { auto v1104 = ([&]() -> Value { auto v1105 = ([&]() -> Value { auto fn1107 = comp1099->Global("len"); Arguments args1108; args1108.Add(comp1099->LocalAt(0), false); return Call(c, fn1107, std::move(args1108)); }()); Value v1106; v1106 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v1105, v1106))) return Value(false); v1105 = v1106; return Value(true); }()); if (!static_cast<bool>(v1104)) return v1104; v1104 = ([&]() -> Value { auto v1109 = Get(comp1099->LocalAt(0), Value(int64_t{0})); Value v1110; v1110 = Value("SELL"); if (!static_cast<bool>(Binary("Eq", v1109, v1110))) return Value(false); v1109 = v1110; return Value(true); }()); if (!static_cast<bool>(v1104)) return v1104; v1104 = ([&]() -> Value { auto v1111 = Get(comp1099->LocalAt(0), Value(int64_t{1})); Value v1112; v1112 = comp1099->Captured("item"); if (!static_cast<bool>(Binary("Eq", v1111, v1112))) return Value(false); v1111 = v1112; return Value(true); }()); return v1104; }()))) continue; result1100.node()->sequence.push_back(([&]() -> Value { auto fn1113 = comp1099->Global("max"); Arguments args1114; args1114.positional.reserve(2); args1114.Add(Value(int64_t{0}), false); args1114.Add(([&]() -> Value { auto fn1115 = comp1099->Global("_int"); Arguments args1116; args1116.Add(Get(comp1099->LocalAt(0), Value(int64_t{2})), false); return Call(c, fn1115, std::move(args1116)); }()), false); return Call(c, fn1113, std::move(args1114)); }())); } return result1100; }()), false); return Call(c, fn1097, std::move(args1098)); }());
s->SetAt(7, v1096);
auto v1117 = ([&]() -> Value { auto fn1118 = s->Global("min"); Arguments args1119; args1119.positional.reserve(3); args1119.Add(([&]() -> Value { auto fn1120 = PrepareDictionaryGet(s->LocalAt(9)); Arguments args1121; args1121.positional.reserve(2); args1121.Add(s->LocalAt(3), false); args1121.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn1120, std::move(args1121)); }()), false); args1119.Add(([&]() -> Value { auto fn1122 = s->Global("max"); Arguments args1123; args1123.positional.reserve(2); args1123.Add(Value(int64_t{0}), false); args1123.Add(([&]() -> Value { auto fn1124 = s->Global("_int"); Arguments args1125; args1125.Add(Get(s->LocalAt(6), Value(int64_t{2})), false); return Call(c, fn1124, std::move(args1125)); }()), false); return Call(c, fn1122, std::move(args1123)); }()), false); args1119.Add(s->LocalAt(7), false); return Call(c, fn1118, std::move(args1119)); }());
s->SetAt(10, v1117);
if (static_cast<bool>(([&]() -> Value { auto v1126 = s->LocalAt(10); Value v1127; v1127 = Value(int64_t{0}); if (!static_cast<bool>(Binary("LtE", v1126, v1127))) return Value(false); v1126 = v1127; return Value(true); }()))) {
continue;
}
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto fn1128 = Attribute(s->LocalAt(12), "_add_sell"); Arguments args1129; args1129.positional.reserve(4); args1129.Add(s->LocalAt(0), false); args1129.Add(s->LocalAt(3), false); args1129.Add(s->LocalAt(10), false); args1129.Add(Get(s->LocalAt(2), Value("max_orders")), false); args1129.Keyword("merge", Value(false)); return Call(c, fn1128, std::move(args1129)); }())))) {
break;
}
auto v1130 = s->LocalAt(9);
auto v1131 = s->LocalAt(3);
auto v1132 = Get(v1130, v1131);
Put(v1130, v1131, Inplace("Sub", v1132, s->LocalAt(10)));
(void)([&]() -> Value { auto fn1133 = Attribute(s->LocalAt(1), "add"); Arguments args1134; args1134.Add(s->LocalAt(3), false); return Call(c, fn1133, std::move(args1134)); }());
auto v1135 = ([&]() -> Value { auto v1136 = ([&]() -> Value { auto fn1137 = PrepareDictionaryGet(Get(s->LocalAt(4), Value("suppress"))); Arguments args1138; args1138.positional.reserve(2); args1138.Add(s->LocalAt(3), false); args1138.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn1137, std::move(args1138)); }()); return Binary("Add", v1136, s->LocalAt(10)); }());
Put(Get(s->LocalAt(4), Value("suppress")), s->LocalAt(3), v1135);
}
if (static_cast<bool>(Get(s->LocalAt(4), Value("suppress")))) {
auto v1139 = s->LocalAt(5);
Put(s->LocalAt(4), Value("due_step"), v1139);
}
return {};
}
}  // namespace kagg::opponents::compiled
