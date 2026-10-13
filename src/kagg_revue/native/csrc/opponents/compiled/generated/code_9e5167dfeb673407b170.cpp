// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_9e5167dfeb673407b170(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "already", "blocked", "future", "item", "next_sup", "nxt", "o", "planned", "prices", "projected", "qty", "route", "self", "step", "tape", "unlock_period", "view"};
s->PrepareSlots(s_names);
auto v30054 = Attribute(s->LocalAt(17), "prices");
s->SetAt(9, v30054);
auto v30055 = ([&]() -> Value { auto comp30056 = std::make_shared<Scope>(); comp30056->globals = s->globals; comp30056->parent = s; static constexpr const char* comp30056_names[] = {"i"}; comp30056->PrepareSlots(comp30056_names); auto result30057 = List(); for (const auto& item30058 : Iterate(s->Global("V9_RACEPX_BASE"))) { comp30056->SetAt(0, item30058); if (!static_cast<bool>(([&]() -> Value { auto v30059 = ([&]() -> Value { auto fn30061 = PrepareDictionaryGet(comp30056->Captured("prices")); Arguments args30062; args30062.positional.reserve(2); args30062.Add(comp30056->LocalAt(0), false); args30062.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn30061, std::move(args30062)); }()); Value v30060; v30060 = ([&]() -> Value { auto v30063 = Get(comp30056->Global("V9_RACEPX_BASE"), comp30056->LocalAt(0)); return Binary("Add", v30063, comp30056->Global("V9_RACEPX_MARGIN")); }()); if (!static_cast<bool>(Binary("LtE", v30059, v30060))) return Value(false); v30059 = v30060; return Value(true); }()))) continue; result30057.node()->sequence.push_back(comp30056->LocalAt(0)); } return Set(result30057.node()->sequence); }());
s->SetAt(2, v30055);
if (static_cast<bool>(Unary("Not", s->LocalAt(2)))) {
auto v30064 = s->Global("_v9_racepx_report");
auto v30065 = Value("racepx_sold");
auto v30066 = Get(v30064, v30065);
Put(v30064, v30065, Inplace("Add", v30066, Value(int64_t{1})));
return ([&]() -> Value { auto fn30067 = s->Global("_V9_RACEPX_LEAD"); Arguments args30068; args30068.positional.reserve(7); args30068.Add(s->LocalAt(13), false); args30068.Add(s->LocalAt(0), false); args30068.Add(s->LocalAt(17), false); args30068.Add(s->LocalAt(10), false); args30068.Add(s->LocalAt(12), false); args30068.Add(s->LocalAt(14), false); args30068.Add(s->LocalAt(5), false); return Call(c, fn30067, std::move(args30068)); }());
}
auto v30069 = ([&]() -> Value { auto v30070 = s->LocalAt(14); return Binary("Add", v30070, Value(int64_t{1})); }());
s->SetAt(6, v30069);
auto v30071 = ([&]() -> Value { auto v30072 = Value(int64_t{3}); return Binary("Mult", v30072, Get(Attribute(s->LocalAt(13), "cfg"), Value("turns_per_day"))); }());
s->SetAt(16, v30071);
if (static_cast<bool>(([&]() -> Value { auto v30073 = ([&]() -> Value { auto v30074 = s->LocalAt(6); Value v30075; v30075 = s->Global("LAST_ACT_STEP"); if (!static_cast<bool>(Binary("Gt", v30074, v30075))) return Value(false); v30074 = v30075; return Value(true); }()); if (static_cast<bool>(v30073)) return v30073; v30073 = ([&]() -> Value { auto v30076 = ([&]() -> Value { auto v30078 = s->LocalAt(6); return Binary("Mod", v30078, s->LocalAt(16)); }()); Value v30077; v30077 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v30076, v30077))) return Value(false); v30076 = v30077; return Value(true); }()); if (static_cast<bool>(v30073)) return v30073; v30073 = ([&]() -> Value { auto v30079 = ([&]() -> Value { auto v30081 = s->LocalAt(14); return Binary("Mod", v30081, Value(int64_t{4})); }()); Value v30080; v30080 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v30079, v30080))) return Value(false); v30079 = v30080; return Value(true); }()); return v30073; }()))) {
return Value{};
}
auto v30082 = Get(Attribute(s->LocalAt(13), "routes"), s->LocalAt(12));
s->SetAt(15, v30082);
auto v30083 = (static_cast<bool>(([&]() -> Value { auto v30084 = ([&]() -> Value { auto v30085 = s->LocalAt(6); Value v30086; v30086 = ([&]() -> Value { auto fn30087 = s->Global("len"); Arguments args30088; args30088.Add(s->LocalAt(15), false); return Call(c, fn30087, std::move(args30088)); }()); if (!static_cast<bool>(Binary("Lt", v30085, v30086))) return Value(false); v30085 = v30086; return Value(true); }()); if (!static_cast<bool>(v30084)) return v30084; v30084 = ([&]() -> Value { auto fn30089 = s->Global("isinstance"); Arguments args30090; args30090.positional.reserve(2); args30090.Add(Get(s->LocalAt(15), s->LocalAt(6)), false); args30090.Add(s->Global("dict"), false); return Call(c, fn30089, std::move(args30090)); }()); return v30084; }())) ? Get(s->LocalAt(15), s->LocalAt(6)) : ([&]() -> Value { auto dict30091 = Dict(); return dict30091; }()));
s->SetAt(3, v30083);
auto v30092 = ([&]() -> Value { auto dict30093 = Dict(); return dict30093; }());
s->SetAt(8, v30092);
for (const auto& item30094 : Iterate(([&]() -> Value { auto v30095 = ([&]() -> Value { auto fn30096 = PrepareDictionaryGet(s->LocalAt(3)); Arguments args30097; args30097.Add(Value("market"), false); return CallDictionaryGet(c, fn30096, std::move(args30097)); }()); if (static_cast<bool>(v30095)) return v30095; v30095 = List({}); return v30095; }()))) {
s->SetAt(7, item30094);
if (static_cast<bool>(([&]() -> Value { auto v30098 = s->LocalAt(7); if (!static_cast<bool>(v30098)) return v30098; v30098 = ([&]() -> Value { auto v30099 = Get(s->LocalAt(7), Value(int64_t{0})); Value v30100; v30100 = Value("SELL"); if (!static_cast<bool>(Binary("Eq", v30099, v30100))) return Value(false); v30099 = v30100; return Value(true); }()); if (!static_cast<bool>(v30098)) return v30098; v30098 = ([&]() -> Value { auto v30101 = ([&]() -> Value { auto fn30103 = s->Global("len"); Arguments args30104; args30104.Add(s->LocalAt(7), false); return Call(c, fn30103, std::move(args30104)); }()); Value v30102; v30102 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v30101, v30102))) return Value(false); v30101 = v30102; return Value(true); }()); if (!static_cast<bool>(v30098)) return v30098; v30098 = ([&]() -> Value { auto v30105 = Get(s->LocalAt(7), Value(int64_t{1})); Value v30106; v30106 = s->Global("PRODUCTS"); if (!static_cast<bool>(Binary("In", v30105, v30106))) return Value(false); v30105 = v30106; return Value(true); }()); return v30098; }()))) {
auto v30107 = ([&]() -> Value { auto v30108 = ([&]() -> Value { auto fn30109 = PrepareDictionaryGet(s->LocalAt(8)); Arguments args30110; args30110.positional.reserve(2); args30110.Add(Get(s->LocalAt(7), Value(int64_t{1})), false); args30110.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn30109, std::move(args30110)); }()); return Binary("Add", v30108, ([&]() -> Value { auto fn30111 = s->Global("max"); Arguments args30112; args30112.positional.reserve(2); args30112.Add(Value(int64_t{0}), false); args30112.Add(([&]() -> Value { auto fn30113 = s->Global("int"); Arguments args30114; args30114.Add(Get(s->LocalAt(7), Value(int64_t{2})), false); return Call(c, fn30113, std::move(args30114)); }()), false); return Call(c, fn30111, std::move(args30112)); }())); }());
Put(s->LocalAt(8), Get(s->LocalAt(7), Value(int64_t{1})), v30107);
}
}
auto v30115 = ([&]() -> Value { auto comp30116 = std::make_shared<Scope>(); comp30116->globals = s->globals; comp30116->parent = s; static constexpr const char* comp30116_names[] = {"o"}; comp30116->PrepareSlots(comp30116_names); auto result30117 = List(); for (const auto& item30118 : Iterate(([&]() -> Value { auto v30119 = ([&]() -> Value { auto fn30120 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args30121; args30121.Add(Value("market"), false); return CallDictionaryGet(c, fn30120, std::move(args30121)); }()); if (static_cast<bool>(v30119)) return v30119; v30119 = List({}); return v30119; }()))) { comp30116->SetAt(0, item30118); if (!static_cast<bool>(([&]() -> Value { auto v30122 = comp30116->LocalAt(0); if (!static_cast<bool>(v30122)) return v30122; v30122 = ([&]() -> Value { auto v30123 = Get(comp30116->LocalAt(0), Value(int64_t{0})); Value v30124; v30124 = Value("SELL"); if (!static_cast<bool>(Binary("Eq", v30123, v30124))) return Value(false); v30123 = v30124; return Value(true); }()); if (!static_cast<bool>(v30122)) return v30122; v30122 = ([&]() -> Value { auto v30125 = ([&]() -> Value { auto fn30127 = comp30116->Global("len"); Arguments args30128; args30128.Add(comp30116->LocalAt(0), false); return Call(c, fn30127, std::move(args30128)); }()); Value v30126; v30126 = Value(int64_t{1}); if (!static_cast<bool>(Binary("Gt", v30125, v30126))) return Value(false); v30125 = v30126; return Value(true); }()); return v30122; }()))) continue; result30117.node()->sequence.push_back(Get(comp30116->LocalAt(0), Value(int64_t{1}))); } return Set(result30117.node()->sequence); }());
s->SetAt(1, v30115);
for (const auto& item30129 : Iterate(s->Global("PRODUCTS"))) {
s->SetAt(4, item30129);
if (static_cast<bool>(([&]() -> Value { auto v30130 = ([&]() -> Value { auto v30131 = s->LocalAt(4); Value v30132; v30132 = s->LocalAt(2); if (!static_cast<bool>(Binary("In", v30131, v30132))) return Value(false); v30131 = v30132; return Value(true); }()); if (static_cast<bool>(v30130)) return v30130; v30130 = ([&]() -> Value { auto v30133 = s->LocalAt(4); Value v30134; v30134 = s->LocalAt(1); if (!static_cast<bool>(Binary("In", v30133, v30134))) return Value(false); v30133 = v30134; return Value(true); }()); if (static_cast<bool>(v30130)) return v30130; v30130 = ([&]() -> Value { auto v30135 = ([&]() -> Value { auto fn30137 = PrepareDictionaryGet(s->LocalAt(8)); Arguments args30138; args30138.positional.reserve(2); args30138.Add(s->LocalAt(4), false); args30138.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn30137, std::move(args30138)); }()); Value v30136; v30136 = Value(int64_t{0}); if (!static_cast<bool>(Binary("LtE", v30135, v30136))) return Value(false); v30135 = v30136; return Value(true); }()); return v30130; }()))) {
continue;
}
auto v30139 = ([&]() -> Value { auto fn30140 = s->Global("min"); Arguments args30141; args30141.positional.reserve(2); args30141.Add(([&]() -> Value { auto fn30142 = PrepareDictionaryGet(s->LocalAt(10)); Arguments args30143; args30143.positional.reserve(2); args30143.Add(s->LocalAt(4), false); args30143.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn30142, std::move(args30143)); }()), false); args30141.Add(Get(s->LocalAt(8), s->LocalAt(4)), false); return Call(c, fn30140, std::move(args30141)); }());
s->SetAt(11, v30139);
if (static_cast<bool>(([&]() -> Value { auto v30144 = ([&]() -> Value { auto v30145 = s->LocalAt(11); Value v30146; v30146 = Value(int64_t{0}); if (!static_cast<bool>(Binary("LtE", v30145, v30146))) return Value(false); v30145 = v30146; return Value(true); }()); if (static_cast<bool>(v30144)) return v30144; v30144 = ([&]() -> Value { auto v30147 = ([&]() -> Value { auto fn30149 = PrepareDictionaryGet(s->LocalAt(9)); Arguments args30150; args30150.positional.reserve(2); args30150.Add(s->LocalAt(4), false); args30150.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn30149, std::move(args30150)); }()); Value v30148; v30148 = Get(Attribute(s->LocalAt(13), "cfg"), Value("min_sell_price")); if (!static_cast<bool>(Binary("Lt", v30147, v30148))) return Value(false); v30147 = v30148; return Value(true); }()); return v30144; }()))) {
continue;
}
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto fn30151 = Attribute(s->LocalAt(13), "_add_sell"); Arguments args30152; args30152.positional.reserve(4); args30152.Add(s->LocalAt(0), false); args30152.Add(s->LocalAt(4), false); args30152.Add(s->LocalAt(11), false); args30152.Add(Get(Attribute(s->LocalAt(13), "cfg"), Value("max_orders")), false); args30152.Keyword("merge", Value(false)); return Call(c, fn30151, std::move(args30152)); }())))) {
break;
}
auto v30153 = s->LocalAt(10);
auto v30154 = s->LocalAt(4);
auto v30155 = Get(v30153, v30154);
Put(v30153, v30154, Inplace("Sub", v30155, s->LocalAt(11)));
auto v30156 = ([&]() -> Value { auto v30157 = ([&]() -> Value { auto fn30158 = PrepareDictionaryGet(Get(s->LocalAt(5), Value("suppress"))); Arguments args30159; args30159.positional.reserve(2); args30159.Add(s->LocalAt(4), false); args30159.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn30158, std::move(args30159)); }()); return Binary("Add", v30157, s->LocalAt(11)); }());
Put(Get(s->LocalAt(5), Value("suppress")), s->LocalAt(4), v30156);
auto v30160 = s->Global("_v9_racepx_report");
auto v30161 = Value("racepx_skipped");
auto v30162 = Get(v30160, v30161);
Put(v30160, v30161, Inplace("Add", v30162, Value(int64_t{1})));
}
if (static_cast<bool>(Get(s->LocalAt(5), Value("suppress")))) {
auto v30163 = s->LocalAt(6);
Put(s->LocalAt(5), Value("due_step"), v30163);
}
return {};
}
}  // namespace kagg::opponents::compiled
