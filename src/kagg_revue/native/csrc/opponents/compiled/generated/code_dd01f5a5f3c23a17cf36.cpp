// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_dd01f5a5f3c23a17cf36(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"_", "actor", "cargo", "command", "day", "distance", "farm", "home", "hungry", "inv", "last", "obs", "pos", "private", "sheep", "step", "target", "targets", "tasks", "tile", "x", "y"};
s->PrepareSlots(s_names);
auto v31056 = ([&]() -> Value { auto fn31057 = s->Global("int"); Arguments args31058; args31058.Add(Get(s->LocalAt(11), Value("step")), false); return Call(c, fn31057, std::move(args31058)); }());
s->SetAt(15, v31056);
auto v31059 = ([&]() -> Value { auto v31060 = s->LocalAt(15); return Binary("FloorDiv", v31060, Value(int64_t{24})); }());
s->SetAt(4, v31059);
if (static_cast<bool>(([&]() -> Value { auto v31061 = s->LocalAt(4); Value v31062; v31062 = Tuple({Value(int64_t{28}), Value(int64_t{29})}); if (!static_cast<bool>(Binary("NotIn", v31061, v31062))) return Value(false); v31061 = v31062; return Value(true); }()))) {
return ([&]() -> Value { auto fn31063 = s->Global("_VT_WORKER"); Arguments args31064; args31064.positional.reserve(3); args31064.Add(s->LocalAt(11), false); args31064.Add(s->LocalAt(1), false); args31064.Add(s->LocalAt(17), false); return Call(c, fn31063, std::move(args31064)); }());
}
auto v31065 = Get(Get(s->LocalAt(11), Value("farms")), Get(s->LocalAt(11), Value("player")));
s->SetAt(6, v31065);
auto v31066 = Get(s->LocalAt(11), Value("private"));
s->SetAt(13, v31066);
auto v31067 = ([&]() -> Value { auto fn31068 = s->Global("tuple"); Arguments args31069; args31069.Add(Get(Get(s->LocalAt(6), Value("hands")), ([&]() -> Value { auto v31070 = s->LocalAt(1); return Binary("Sub", v31070, Value(int64_t{1})); }())), false); return Call(c, fn31068, std::move(args31069)); }());
s->SetAt(12, v31067);
auto v31071 = Get(Get(s->LocalAt(13), Value("inventories")), s->LocalAt(1));
s->SetAt(9, v31071);
auto v31072 = ([&]() -> Value { auto fn31073 = s->Global("_v219_home"); Arguments args31074; args31074.Add(s->LocalAt(12), false); return Call(c, fn31073, std::move(args31074)); }());
s->SetAt(7, v31072);
auto v31075 = ([&]() -> Value { auto v31076 = ([&]() -> Value { auto fn31077 = s->Global("abs"); Arguments args31078; args31078.Add(([&]() -> Value { auto v31079 = Get(s->LocalAt(12), Value(int64_t{0})); return Binary("Sub", v31079, Get(s->LocalAt(7), Value(int64_t{0}))); }()), false); return Call(c, fn31077, std::move(args31078)); }()); return Binary("Add", v31076, ([&]() -> Value { auto fn31080 = s->Global("abs"); Arguments args31081; args31081.Add(([&]() -> Value { auto v31082 = Get(s->LocalAt(12), Value(int64_t{1})); return Binary("Sub", v31082, Get(s->LocalAt(7), Value(int64_t{1}))); }()), false); return Call(c, fn31080, std::move(args31081)); }())); }());
s->SetAt(5, v31075);
auto v31083 = ([&]() -> Value { auto comp31084 = std::make_shared<Scope>(); comp31084->globals = s->globals; comp31084->parent = s; static constexpr const char* comp31084_names[] = {"item"}; comp31084->PrepareSlots(comp31084_names); auto result31085 = List(); for (const auto& item31086 : Iterate(Tuple({Value("WOOL"), Value("FERTILIZER")}))) { comp31084->SetAt(0, item31086); if (!static_cast<bool>(([&]() -> Value { auto fn31087 = PrepareDictionaryGet(comp31084->Captured("inv")); Arguments args31088; args31088.positional.reserve(2); args31088.Add(comp31084->LocalAt(0), false); args31088.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn31087, std::move(args31088)); }()))) continue; result31085.node()->sequence.push_back(comp31084->LocalAt(0)); } return result31085; }());
s->SetAt(2, v31083);
auto v31089 = (static_cast<bool>(([&]() -> Value { auto v31090 = s->LocalAt(4); Value v31091; v31091 = Value(int64_t{29}); if (!static_cast<bool>(Binary("Eq", v31090, v31091))) return Value(false); v31090 = v31091; return Value(true); }())) ? Value(int64_t{717}) : ([&]() -> Value { auto v31092 = ([&]() -> Value { auto v31093 = s->LocalAt(4); return Binary("Mult", v31093, Value(int64_t{24})); }()); return Binary("Add", v31092, Value(int64_t{23})); }()));
s->SetAt(10, v31089);
if (static_cast<bool>(([&]() -> Value { auto v31094 = s->LocalAt(2); if (!static_cast<bool>(v31094)) return v31094; v31094 = ([&]() -> Value { auto v31095 = s->LocalAt(15); Value v31096; v31096 = ([&]() -> Value { auto v31097 = s->LocalAt(10); return Binary("Sub", v31097, s->LocalAt(5)); }()); if (!static_cast<bool>(Binary("GtE", v31095, v31096))) return Value(false); v31095 = v31096; return Value(true); }()); return v31094; }()))) {
return ([&]() -> Value { auto v31098 = ([&]() -> Value { auto fn31099 = s->Global("_v219_walk"); Arguments args31100; args31100.positional.reserve(2); args31100.Add(s->LocalAt(12), false); args31100.Add(s->LocalAt(7), false); return Call(c, fn31099, std::move(args31100)); }()); if (static_cast<bool>(v31098)) return v31098; v31098 = List({Value("PLACE"), Get(s->LocalAt(2), Value(int64_t{0})), Get(s->LocalAt(9), Get(s->LocalAt(2), Value(int64_t{0})))}); return v31098; }());
}
auto v31101 = ([&]() -> Value { auto comp31102 = std::make_shared<Scope>(); comp31102->globals = s->globals; comp31102->parent = s; static constexpr const char* comp31102_names[] = {"x", "y"}; comp31102->PrepareSlots(comp31102_names); auto result31103 = List(); for (const auto& item31104 : Iterate(s->LocalAt(17))) { auto unpack31105 = Iterate(item31104); ValidateUnpack(unpack31105, 2, false); comp31102->SetAt(0, unpack31105.at(0)); comp31102->SetAt(1, unpack31105.at(1)); if (!static_cast<bool>(([&]() -> Value { auto v31106 = ([&]() -> Value { auto fn31107 = comp31102->Global("isinstance"); Arguments args31108; args31108.positional.reserve(2); args31108.Add(Get(Get(Get(comp31102->Captured("farm"), Value("tiles")), comp31102->LocalAt(1)), comp31102->LocalAt(0)), false); args31108.Add(comp31102->Global("dict"), false); return Call(c, fn31107, std::move(args31108)); }()); if (!static_cast<bool>(v31106)) return v31106; v31106 = ([&]() -> Value { auto v31109 = ([&]() -> Value { auto fn31111 = PrepareDictionaryGet(Get(Get(Get(comp31102->Captured("farm"), Value("tiles")), comp31102->LocalAt(1)), comp31102->LocalAt(0))); Arguments args31112; args31112.Add(Value("animal"), false); return CallDictionaryGet(c, fn31111, std::move(args31112)); }()); Value v31110; v31110 = Value("SHEEP"); if (!static_cast<bool>(Binary("Eq", v31109, v31110))) return Value(false); v31109 = v31110; return Value(true); }()); return v31106; }()))) continue; result31103.node()->sequence.push_back(Tuple({comp31102->LocalAt(0), comp31102->LocalAt(1)})); } return result31103; }());
s->SetAt(14, v31101);
auto v31113 = List({});
s->SetAt(18, v31113);
if (static_cast<bool>(([&]() -> Value { auto v31114 = s->LocalAt(4); Value v31115; v31115 = Value(int64_t{28}); if (!static_cast<bool>(Binary("Eq", v31114, v31115))) return Value(false); v31114 = v31115; return Value(true); }()))) {
auto v31116 = ([&]() -> Value { auto fn31117 = s->Global("sum"); Arguments args31118; args31118.Add(([&]() -> Value { auto comp31119 = std::make_shared<Scope>(); comp31119->globals = s->globals; comp31119->parent = s; static constexpr const char* comp31119_names[] = {"x", "y"}; comp31119->PrepareSlots(comp31119_names); auto result31120 = List(); for (const auto& item31121 : Iterate(s->LocalAt(14))) { auto unpack31122 = Iterate(item31121); ValidateUnpack(unpack31122, 2, false); comp31119->SetAt(0, unpack31122.at(0)); comp31119->SetAt(1, unpack31122.at(1)); result31120.node()->sequence.push_back(Unary("Not", Get(Get(Get(Get(comp31119->Captured("farm"), Value("tiles")), comp31119->LocalAt(1)), comp31119->LocalAt(0)), Value("fed_today")))); } return result31120; }()), false); return Call(c, fn31117, std::move(args31118)); }());
s->SetAt(8, v31116);
if (static_cast<bool>(([&]() -> Value { auto v31123 = s->LocalAt(8); if (!static_cast<bool>(v31123)) return v31123; v31123 = Unary("Not", ([&]() -> Value { auto fn31124 = PrepareDictionaryGet(s->LocalAt(9)); Arguments args31125; args31125.positional.reserve(2); args31125.Add(Value("WHEAT"), false); args31125.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn31124, std::move(args31125)); }())); if (!static_cast<bool>(v31123)) return v31123; v31123 = ([&]() -> Value { auto fn31126 = PrepareDictionaryGet(Get(s->LocalAt(13), Value("shed"))); Arguments args31127; args31127.positional.reserve(2); args31127.Add(Value("WHEAT"), false); args31127.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn31126, std::move(args31127)); }()); return v31123; }()))) {
return ([&]() -> Value { auto v31128 = ([&]() -> Value { auto fn31129 = s->Global("_v219_walk"); Arguments args31130; args31130.positional.reserve(2); args31130.Add(s->LocalAt(12), false); args31130.Add(s->LocalAt(7), false); return Call(c, fn31129, std::move(args31130)); }()); if (static_cast<bool>(v31128)) return v31128; v31128 = List({Value("PICKUP"), Value("WHEAT"), ([&]() -> Value { auto fn31131 = s->Global("min"); Arguments args31132; args31132.positional.reserve(2); args31132.Add(s->LocalAt(8), false); args31132.Add(Get(Get(s->LocalAt(13), Value("shed")), Value("WHEAT")), false); return Call(c, fn31131, std::move(args31132)); }())}); return v31128; }());
}
}
for (const auto& item31133 : Iterate(s->LocalAt(14))) {
auto unpack31134 = Iterate(item31133);
ValidateUnpack(unpack31134, 2, false);
s->SetAt(20, unpack31134.at(0));
s->SetAt(21, unpack31134.at(1));
auto v31135 = Get(Get(Get(s->LocalAt(6), Value("tiles")), s->LocalAt(21)), s->LocalAt(20));
s->SetAt(19, v31135);
auto v31136 = Value{};
s->SetAt(3, v31136);
if (static_cast<bool>(([&]() -> Value { auto v31137 = ([&]() -> Value { auto v31138 = s->LocalAt(4); Value v31139; v31139 = Value(int64_t{28}); if (!static_cast<bool>(Binary("Eq", v31138, v31139))) return Value(false); v31138 = v31139; return Value(true); }()); if (!static_cast<bool>(v31137)) return v31137; v31137 = Unary("Not", Get(s->LocalAt(19), Value("fed_today"))); if (!static_cast<bool>(v31137)) return v31137; v31137 = ([&]() -> Value { auto fn31140 = PrepareDictionaryGet(s->LocalAt(9)); Arguments args31141; args31141.positional.reserve(2); args31141.Add(Value("WHEAT"), false); args31141.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn31140, std::move(args31141)); }()); return v31137; }()))) {
auto v31142 = List({Value("FEED")});
s->SetAt(3, v31142);
}
else {
if (static_cast<bool>(Get(s->LocalAt(19), Value("yield_units")))) {
auto v31143 = List({Value("HARVEST")});
s->SetAt(3, v31143);
}
else {
if (static_cast<bool>(([&]() -> Value { auto v31144 = ([&]() -> Value { auto v31145 = s->LocalAt(4); Value v31146; v31146 = Value(int64_t{28}); if (!static_cast<bool>(Binary("Eq", v31145, v31146))) return Value(false); v31145 = v31146; return Value(true); }()); if (!static_cast<bool>(v31144)) return v31144; v31144 = Get(s->LocalAt(19), Value("fertilizer_available")); return v31144; }()))) {
auto v31147 = List({Value("COLLECT_FERTILIZER")});
s->SetAt(3, v31147);
}
}
}
if (static_cast<bool>(([&]() -> Value { auto v31148 = ([&]() -> Value { auto v31149 = s->LocalAt(4); Value v31150; v31150 = Value(int64_t{28}); if (!static_cast<bool>(Binary("Eq", v31149, v31150))) return Value(false); v31149 = v31150; return Value(true); }()); if (!static_cast<bool>(v31148)) return v31148; v31148 = Unary("Not", Get(s->LocalAt(19), Value("cared_today"))); if (!static_cast<bool>(v31148)) return v31148; v31148 = ([&]() -> Value { auto v31151 = s->LocalAt(3); Value v31152; v31152 = Value{}; if (!static_cast<bool>(Binary("Is", v31151, v31152))) return Value(false); v31151 = v31152; return Value(true); }()); return v31148; }()))) {
auto v31153 = s->Global("_VT_REPORT");
auto v31154 = Value("vt_skipped_care");
auto v31155 = Get(v31153, v31154);
Put(v31153, v31154, Inplace("Add", v31155, Value(int64_t{1})));
}
if (static_cast<bool>(s->LocalAt(3))) {
(void)([&]() -> Value { auto fn31156 = Attribute(s->LocalAt(18), "append"); Arguments args31157; args31157.Add(Tuple({([&]() -> Value { auto v31158 = ([&]() -> Value { auto fn31159 = s->Global("abs"); Arguments args31160; args31160.Add(([&]() -> Value { auto v31161 = Get(s->LocalAt(12), Value(int64_t{0})); return Binary("Sub", v31161, s->LocalAt(20)); }()), false); return Call(c, fn31159, std::move(args31160)); }()); return Binary("Add", v31158, ([&]() -> Value { auto fn31162 = s->Global("abs"); Arguments args31163; args31163.Add(([&]() -> Value { auto v31164 = Get(s->LocalAt(12), Value(int64_t{1})); return Binary("Sub", v31164, s->LocalAt(21)); }()), false); return Call(c, fn31162, std::move(args31163)); }())); }()), Tuple({s->LocalAt(20), s->LocalAt(21)}), s->LocalAt(3)}), false); return Call(c, fn31156, std::move(args31157)); }());
}
}
if (static_cast<bool>(s->LocalAt(18))) {
auto v31165 = ([&]() -> Value { auto fn31166 = s->Global("min"); Arguments args31167; args31167.Add(s->LocalAt(18), false); return Call(c, fn31166, std::move(args31167)); }());
auto unpack31168 = Iterate(v31165);
ValidateUnpack(unpack31168, 3, false);
s->SetAt(0, unpack31168.at(0));
s->SetAt(16, unpack31168.at(1));
s->SetAt(3, unpack31168.at(2));
return ([&]() -> Value { auto v31169 = ([&]() -> Value { auto fn31170 = s->Global("_v219_walk"); Arguments args31171; args31171.positional.reserve(2); args31171.Add(s->LocalAt(12), false); args31171.Add(s->LocalAt(16), false); return Call(c, fn31170, std::move(args31171)); }()); if (static_cast<bool>(v31169)) return v31169; v31169 = s->LocalAt(3); return v31169; }());
}
if (static_cast<bool>(s->LocalAt(2))) {
return ([&]() -> Value { auto v31172 = ([&]() -> Value { auto fn31173 = s->Global("_v219_walk"); Arguments args31174; args31174.positional.reserve(2); args31174.Add(s->LocalAt(12), false); args31174.Add(s->LocalAt(7), false); return Call(c, fn31173, std::move(args31174)); }()); if (static_cast<bool>(v31172)) return v31172; v31172 = List({Value("PLACE"), Get(s->LocalAt(2), Value(int64_t{0})), Get(s->LocalAt(9), Get(s->LocalAt(2), Value(int64_t{0})))}); return v31172; }());
}
return List({Value("PASS")});
return {};
}
}  // namespace kagg::opponents::compiled
