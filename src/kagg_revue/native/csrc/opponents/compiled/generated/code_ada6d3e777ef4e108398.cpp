// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_ada6d3e777ef4e108398(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"_", "action", "avail", "carried", "extra", "farm", "item", "needed", "obs", "orders", "prices", "private", "qty", "step", "stock"};
s->PrepareSlots(s_names);
auto v19025 = ([&]() -> Value { auto fn19026 = s->Global("int"); Arguments args19027; args19027.Add(Get(s->LocalAt(8), Value("step")), false); return Call(c, fn19026, std::move(args19027)); }());
s->SetAt(13, v19025);
if (static_cast<bool>(([&]() -> Value { auto v19028 = ([&]() -> Value { auto v19029 = ([&]() -> Value { auto v19031 = s->LocalAt(13); return Binary("Mod", v19031, Value(int64_t{24})); }()); Value v19030; v19030 = s->Global("_Y_HOURS"); if (!static_cast<bool>(Binary("NotIn", v19029, v19030))) return Value(false); v19029 = v19030; return Value(true); }()); if (static_cast<bool>(v19028)) return v19028; v19028 = ([&]() -> Value { auto v19032 = ([&]() -> Value { auto v19034 = s->LocalAt(13); return Binary("FloorDiv", v19034, Value(int64_t{24})); }()); Value v19033; v19033 = s->Global("_Y_MIN_DAY"); if (!static_cast<bool>(Binary("Lt", v19032, v19033))) return Value(false); v19032 = v19033; return Value(true); }()); if (static_cast<bool>(v19028)) return v19028; v19028 = ([&]() -> Value { auto v19035 = s->LocalAt(13); Value v19036; v19036 = Value(int64_t{696}); if (!static_cast<bool>(Binary("GtE", v19035, v19036))) return Value(false); v19035 = v19036; return Value(true); }()); return v19028; }()))) {
return s->LocalAt(1);
}
auto v19037 = ([&]() -> Value { auto comp19038 = std::make_shared<Scope>(); comp19038->globals = s->globals; comp19038->parent = s; static constexpr const char* comp19038_names[] = {"o"}; comp19038->PrepareSlots(comp19038_names); auto result19039 = List(); for (const auto& item19040 : Iterate(([&]() -> Value { auto v19041 = ([&]() -> Value { auto fn19042 = PrepareDictionaryGet(s->LocalAt(1)); Arguments args19043; args19043.Add(Value("market"), false); return CallDictionaryGet(c, fn19042, std::move(args19043)); }()); if (static_cast<bool>(v19041)) return v19041; v19041 = List({}); return v19041; }()))) { comp19038->SetAt(0, item19040); result19039.node()->sequence.push_back(([&]() -> Value { auto fn19044 = comp19038->Global("list"); Arguments args19045; args19045.Add(comp19038->LocalAt(0), false); return Call(c, fn19044, std::move(args19045)); }())); } return result19039; }());
s->SetAt(9, v19037);
if (static_cast<bool>(([&]() -> Value { auto v19046 = ([&]() -> Value { auto fn19048 = s->Global("len"); Arguments args19049; args19049.Add(s->LocalAt(9), false); return Call(c, fn19048, std::move(args19049)); }()); Value v19047; v19047 = Value(int64_t{10}); if (!static_cast<bool>(Binary("GtE", v19046, v19047))) return Value(false); v19046 = v19047; return Value(true); }()))) {
return s->LocalAt(1);
}
auto v19050 = ([&]() -> Value { auto fn19051 = s->Global("_r127_fields"); Arguments args19052; args19052.positional.reserve(2); args19052.Add(s->LocalAt(8), false); args19052.Add(s->LocalAt(1), false); return Call(c, fn19051, std::move(args19052)); }());
auto unpack19053 = Iterate(v19050);
ValidateUnpack(unpack19053, 2, false);
s->SetAt(5, unpack19053.at(0));
s->SetAt(11, unpack19053.at(1));
auto v19054 = ([&]() -> Value { auto fn19055 = s->Global("_r97_market_stock"); Arguments args19056; args19056.positional.reserve(2); args19056.Add(Get(s->LocalAt(11), Value("shed")), false); args19056.Add(s->LocalAt(9), false); return Call(c, fn19055, std::move(args19056)); }());
auto unpack19057 = Iterate(v19054);
ValidateUnpack(unpack19057, 3, false);
s->SetAt(14, unpack19057.at(0));
s->SetAt(0, unpack19057.at(1));
s->SetAt(0, unpack19057.at(2));
auto v19058 = ([&]() -> Value { auto fn19059 = s->Global("sum"); Arguments args19060; args19060.Add(([&]() -> Value { auto comp19061 = std::make_shared<Scope>(); comp19061->globals = s->globals; comp19061->parent = s; static constexpr const char* comp19061_names[] = {"bag", "n"}; comp19061->PrepareSlots(comp19061_names); auto result19062 = List(); for (const auto& item19063 : Iterate(Get(s->LocalAt(11), Value("inventories")))) { comp19061->SetAt(0, item19063); for (const auto& item19064 : Iterate(([&]() -> Value { auto fn19065 = Attribute(comp19061->LocalAt(0), "values"); Arguments args19066; return Call(c, fn19065, std::move(args19066)); }()))) { comp19061->SetAt(1, item19064); result19062.node()->sequence.push_back(([&]() -> Value { auto fn19067 = comp19061->Global("max"); Arguments args19068; args19068.positional.reserve(2); args19068.Add(Value(int64_t{0}), false); args19068.Add(([&]() -> Value { auto fn19069 = comp19061->Global("int"); Arguments args19070; args19070.Add(comp19061->LocalAt(1), false); return Call(c, fn19069, std::move(args19070)); }()), false); return Call(c, fn19067, std::move(args19068)); }())); } } return result19062; }()), false); return Call(c, fn19059, std::move(args19060)); }());
s->SetAt(3, v19058);
auto v19071 = ([&]() -> Value { auto v19072 = ([&]() -> Value { auto v19073 = ([&]() -> Value { auto v19074 = ([&]() -> Value { auto fn19075 = s->Global("sum"); Arguments args19076; args19076.Add(([&]() -> Value { auto comp19077 = std::make_shared<Scope>(); comp19077->globals = s->globals; comp19077->parent = s; static constexpr const char* comp19077_names[] = {"v"}; comp19077->PrepareSlots(comp19077_names); auto result19078 = List(); for (const auto& item19079 : Iterate(([&]() -> Value { auto fn19080 = Attribute(s->LocalAt(14), "values"); Arguments args19081; return Call(c, fn19080, std::move(args19081)); }()))) { comp19077->SetAt(0, item19079); result19078.node()->sequence.push_back(([&]() -> Value { auto fn19082 = comp19077->Global("max"); Arguments args19083; args19083.positional.reserve(2); args19083.Add(Value(int64_t{0}), false); args19083.Add(([&]() -> Value { auto fn19084 = comp19077->Global("int"); Arguments args19085; args19085.Add(comp19077->LocalAt(0), false); return Call(c, fn19084, std::move(args19085)); }()), false); return Call(c, fn19082, std::move(args19083)); }())); } return result19078; }()), false); return Call(c, fn19075, std::move(args19076)); }()); return Binary("Add", v19074, s->LocalAt(3)); }()); return Binary("Sub", v19073, Value(int64_t{99})); }()); return Binary("Sub", v19072, s->Global("_Y_MARGIN")); }());
s->SetAt(7, v19071);
if (static_cast<bool>(([&]() -> Value { auto v19086 = s->LocalAt(7); Value v19087; v19087 = Value(int64_t{0}); if (!static_cast<bool>(Binary("LtE", v19086, v19087))) return Value(false); v19086 = v19087; return Value(true); }()))) {
return s->LocalAt(1);
}
auto v19088 = Get(Get(s->LocalAt(8), Value("market")), Value("prices"));
s->SetAt(10, v19088);
auto v19089 = List({});
s->SetAt(4, v19089);
for (const auto& item19090 : Iterate(([&]() -> Value { auto fn19091 = s->Global("sorted"); Arguments args19092; args19092.Add(s->Global("PRODUCTS"), false); args19092.Keyword("key", Define(&Code_609a2f72a1dcb06c7e5d, s, Signature{{"it"}, {}, {}, {}, "", "", ([]() -> std::span<const char* const> { static constexpr const char* names[] = {"it"}; return names; }())}, true, "<lambda>")); return Call(c, fn19091, std::move(args19092)); }()))) {
s->SetAt(6, item19090);
auto v19097 = ([&]() -> Value { auto fn19098 = s->Global("max"); Arguments args19099; args19099.positional.reserve(2); args19099.Add(Value(int64_t{0}), false); args19099.Add(([&]() -> Value { auto fn19100 = s->Global("int"); Arguments args19101; args19101.Add(([&]() -> Value { auto fn19102 = PrepareDictionaryGet(s->LocalAt(14)); Arguments args19103; args19103.positional.reserve(2); args19103.Add(s->LocalAt(6), false); args19103.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn19102, std::move(args19103)); }()), false); return Call(c, fn19100, std::move(args19101)); }()), false); return Call(c, fn19098, std::move(args19099)); }());
s->SetAt(2, v19097);
auto v19104 = ([&]() -> Value { auto fn19105 = s->Global("min"); Arguments args19106; args19106.positional.reserve(2); args19106.Add(s->LocalAt(7), false); args19106.Add(s->LocalAt(2), false); return Call(c, fn19105, std::move(args19106)); }());
s->SetAt(12, v19104);
if (static_cast<bool>(([&]() -> Value { auto v19107 = s->LocalAt(12); Value v19108; v19108 = Value(int64_t{0}); if (!static_cast<bool>(Binary("LtE", v19107, v19108))) return Value(false); v19107 = v19108; return Value(true); }()))) {
continue;
}
if (static_cast<bool>(([&]() -> Value { auto v19109 = ([&]() -> Value { auto v19110 = s->LocalAt(6); Value v19111; v19111 = s->Global("_Y_ITEMS"); if (!static_cast<bool>(Binary("In", v19110, v19111))) return Value(false); v19110 = v19111; return Value(true); }()); if (!static_cast<bool>(v19109)) return v19109; v19109 = ([&]() -> Value { auto v19112 = ([&]() -> Value { auto fn19114 = s->Global("int"); Arguments args19115; args19115.Add(([&]() -> Value { auto fn19116 = PrepareDictionaryGet(s->LocalAt(10)); Arguments args19117; args19117.positional.reserve(2); args19117.Add(s->LocalAt(6), false); args19117.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn19116, std::move(args19117)); }()), false); return Call(c, fn19114, std::move(args19115)); }()); Value v19113; v19113 = Value(int64_t{2}); if (!static_cast<bool>(Binary("GtE", v19112, v19113))) return Value(false); v19112 = v19113; return Value(true); }()); return v19109; }()))) {
(void)([&]() -> Value { auto fn19118 = Attribute(s->LocalAt(4), "append"); Arguments args19119; args19119.Add(List({Value("SELL"), s->LocalAt(6), s->LocalAt(12)}), false); return Call(c, fn19118, std::move(args19119)); }());
}
auto v19120 = s->LocalAt(7);
s->SetAt(7, Inplace("Sub", v19120, s->LocalAt(12)));
if (static_cast<bool>(([&]() -> Value { auto v19121 = s->LocalAt(7); Value v19122; v19122 = Value(int64_t{0}); if (!static_cast<bool>(Binary("LtE", v19121, v19122))) return Value(false); v19121 = v19122; return Value(true); }()))) {
break;
}
}
if (static_cast<bool>(([&]() -> Value { auto v19123 = Unary("Not", s->LocalAt(4)); if (static_cast<bool>(v19123)) return v19123; v19123 = ([&]() -> Value { auto v19124 = ([&]() -> Value { auto v19126 = ([&]() -> Value { auto fn19127 = s->Global("len"); Arguments args19128; args19128.Add(s->LocalAt(9), false); return Call(c, fn19127, std::move(args19128)); }()); return Binary("Add", v19126, ([&]() -> Value { auto fn19129 = s->Global("len"); Arguments args19130; args19130.Add(s->LocalAt(4), false); return Call(c, fn19129, std::move(args19130)); }())); }()); Value v19125; v19125 = Value(int64_t{10}); if (!static_cast<bool>(Binary("Gt", v19124, v19125))) return Value(false); v19124 = v19125; return Value(true); }()); return v19123; }()))) {
return s->LocalAt(1);
}
auto v19131 = s->Global("_PG_REPORT");
auto v19132 = Value("preguard_turns");
auto v19133 = Get(v19131, v19132);
Put(v19131, v19132, Inplace("Add", v19133, Value(int64_t{1})));
auto v19134 = s->Global("_PG_REPORT");
auto v19135 = Value("preguard_units");
auto v19136 = Get(v19134, v19135);
Put(v19134, v19135, Inplace("Add", v19136, ([&]() -> Value { auto fn19137 = s->Global("sum"); Arguments args19138; args19138.Add(([&]() -> Value { auto comp19139 = std::make_shared<Scope>(); comp19139->globals = s->globals; comp19139->parent = s; static constexpr const char* comp19139_names[] = {"o"}; comp19139->PrepareSlots(comp19139_names); auto result19140 = List(); for (const auto& item19141 : Iterate(s->LocalAt(4))) { comp19139->SetAt(0, item19141); result19140.node()->sequence.push_back(Get(comp19139->LocalAt(0), Value(int64_t{2}))); } return result19140; }()), false); return Call(c, fn19137, std::move(args19138)); }())));
return ([&]() -> Value { auto fn19142 = s->Global("dict"); Arguments args19143; args19143.Add(s->LocalAt(1), false); args19143.Keyword("market", ([&]() -> Value { auto v19144 = s->LocalAt(9); return Binary("Add", v19144, s->LocalAt(4)); }())); return Call(c, fn19142, std::move(args19143)); }());
return {};
}
}  // namespace kagg::opponents::compiled
