// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_194b0ce5e12f1d1a7bd3(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"_", "action", "actor", "c", "changed", "commands", "drop", "farm", "obs", "original", "positions", "result", "tile", "x", "y"};
s->PrepareSlots(s_names);
if (static_cast<bool>(([&]() -> Value { auto v11113 = ([&]() -> Value { auto v11115 = ([&]() -> Value { auto fn11116 = s->Global("int"); Arguments args11117; args11117.Add(Get(s->LocalAt(8), Value("step")), false); return Call(c, fn11116, std::move(args11117)); }()); return Binary("Mod", v11115, Value(int64_t{24})); }()); Value v11114; v11114 = Value(int64_t{23}); if (!static_cast<bool>(Binary("NotEq", v11113, v11114))) return Value(false); v11113 = v11114; return Value(true); }()))) {
return s->LocalAt(1);
}
auto v11118 = ([&]() -> Value { Arguments args11119; args11119.Add(([&]() -> Value { auto v11120 = ([&]() -> Value { auto fn11121 = PrepareDictionaryGet(s->LocalAt(1)); Arguments args11122; args11122.Add(Value("farmer"), false); return CallDictionaryGet(c, fn11121, std::move(args11122)); }()); if (static_cast<bool>(v11120)) return v11120; v11120 = List({Value("PASS")}); return v11120; }()), false); args11119.Add(([&]() -> Value { auto v11123 = ([&]() -> Value { auto fn11124 = PrepareDictionaryGet(s->LocalAt(1)); Arguments args11125; args11125.Add(Value("hands"), false); return CallDictionaryGet(c, fn11124, std::move(args11125)); }()); if (static_cast<bool>(v11123)) return v11123; v11123 = List({}); return v11123; }()), true); return List(std::move(args11119.positional)); }());
s->SetAt(5, v11118);
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto comp11126 = std::make_shared<Scope>(); comp11126->globals = s->globals; comp11126->parent = s; static constexpr const char* comp11126_names[] = {"c"}; comp11126->PrepareSlots(comp11126_names); auto result11127 = List(); for (const auto& item11128 : Iterate(s->LocalAt(5))) { comp11126->SetAt(0, item11128); if (static_cast<bool>(([&]() -> Value { auto v11129 = comp11126->LocalAt(0); if (!static_cast<bool>(v11129)) return v11129; v11129 = ([&]() -> Value { auto v11130 = Get(comp11126->LocalAt(0), Value(int64_t{0})); Value v11131; v11131 = Value("PLANT"); if (!static_cast<bool>(Binary("Eq", v11130, v11131))) return Value(false); v11130 = v11131; return Value(true); }()); return v11129; }()))) return Value(true); } return Value(false); }())))) {
return s->LocalAt(1);
}
auto v11132 = ([&]() -> Value { auto fn11133 = Attribute(s->Global("copy"), "deepcopy"); Arguments args11134; args11134.Add(s->LocalAt(1), false); return Call(c, fn11133, std::move(args11134)); }());
s->SetAt(11, v11132);
auto v11135 = Value(false);
s->SetAt(4, v11135);
for (const auto& item11136 : Iterate(([&]() -> Value { auto fn11137 = s->Global("range"); Arguments args11138; args11138.Add(([&]() -> Value { auto v11139 = ([&]() -> Value { auto fn11140 = s->Global("len"); Arguments args11141; args11141.Add(s->LocalAt(5), false); return Call(c, fn11140, std::move(args11141)); }()); return Binary("Add", v11139, Value(int64_t{1})); }()), false); return Call(c, fn11137, std::move(args11138)); }()))) {
s->SetAt(0, item11136);
auto v11142 = ([&]() -> Value { auto fn11143 = s->Global("_r127_fields"); Arguments args11144; args11144.positional.reserve(2); args11144.Add(s->LocalAt(8), false); args11144.Add(s->LocalAt(11), false); return Call(c, fn11143, std::move(args11144)); }());
auto unpack11145 = Iterate(v11142);
ValidateUnpack(unpack11145, 2, false);
s->SetAt(7, unpack11145.at(0));
s->SetAt(0, unpack11145.at(1));
auto v11146 = Get(Get(s->LocalAt(8), Value("farms")), Get(s->LocalAt(8), Value("player")));
s->SetAt(9, v11146);
auto v11147 = ([&]() -> Value { Arguments args11148; args11148.Add(Get(s->LocalAt(9), Value("farmer")), false); args11148.Add(Get(s->LocalAt(9), Value("hands")), true); return List(std::move(args11148.positional)); }());
s->SetAt(10, v11147);
auto v11149 = List({});
s->SetAt(6, v11149);
for (const auto& item11150 : Iterate(([&]() -> Value { auto fn11151 = s->Global("enumerate"); Arguments args11152; args11152.Add(s->LocalAt(5), false); return Call(c, fn11151, std::move(args11152)); }()))) {
auto unpack11153 = Iterate(item11150);
ValidateUnpack(unpack11153, 2, false);
s->SetAt(2, unpack11153.at(0));
s->SetAt(3, unpack11153.at(1));
if (static_cast<bool>(([&]() -> Value { auto v11154 = Unary("Not", s->LocalAt(3)); if (static_cast<bool>(v11154)) return v11154; v11154 = ([&]() -> Value { auto v11155 = Get(s->LocalAt(3), Value(int64_t{0})); Value v11156; v11156 = Value("PLANT"); if (!static_cast<bool>(Binary("NotEq", v11155, v11156))) return Value(false); v11155 = v11156; return Value(true); }()); return v11154; }()))) {
continue;
}
auto v11157 = Value{};
s->SetAt(12, v11157);
if (static_cast<bool>(([&]() -> Value { auto v11158 = s->LocalAt(2); Value v11159; v11159 = ([&]() -> Value { auto fn11160 = s->Global("len"); Arguments args11161; args11161.Add(s->LocalAt(10), false); return Call(c, fn11160, std::move(args11161)); }()); if (!static_cast<bool>(Binary("Lt", v11158, v11159))) return Value(false); v11158 = v11159; return Value(true); }()))) {
auto v11162 = Get(s->LocalAt(10), s->LocalAt(2));
auto unpack11163 = Iterate(v11162);
ValidateUnpack(unpack11163, 2, false);
s->SetAt(13, unpack11163.at(0));
s->SetAt(14, unpack11163.at(1));
auto v11164 = Get(Get(Get(s->LocalAt(7), Value("tiles")), s->LocalAt(14)), s->LocalAt(13));
s->SetAt(12, v11164);
}
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto v11165 = ([&]() -> Value { auto fn11166 = s->Global("isinstance"); Arguments args11167; args11167.positional.reserve(2); args11167.Add(s->LocalAt(12), false); args11167.Add(s->Global("dict"), false); return Call(c, fn11166, std::move(args11167)); }()); if (!static_cast<bool>(v11165)) return v11165; v11165 = ([&]() -> Value { auto v11168 = ([&]() -> Value { auto fn11170 = PrepareDictionaryGet(s->LocalAt(12)); Arguments args11171; args11171.Add(Value("kind"), false); return CallDictionaryGet(c, fn11170, std::move(args11171)); }()); Value v11169; v11169 = Value("PLANT"); if (!static_cast<bool>(Binary("Eq", v11168, v11169))) return Value(false); v11168 = v11169; return Value(true); }()); if (!static_cast<bool>(v11165)) return v11165; v11165 = ([&]() -> Value { auto v11172 = ([&]() -> Value { auto fn11174 = PrepareDictionaryGet(s->LocalAt(12)); Arguments args11175; args11175.Add(Value("crop"), false); return CallDictionaryGet(c, fn11174, std::move(args11175)); }()); Value v11173; v11173 = Get(s->LocalAt(3), Value(int64_t{1})); if (!static_cast<bool>(Binary("Eq", v11172, v11173))) return Value(false); v11172 = v11173; return Value(true); }()); if (!static_cast<bool>(v11165)) return v11165; v11165 = ([&]() -> Value { auto v11176 = ([&]() -> Value { auto fn11178 = PrepareDictionaryGet(s->LocalAt(12)); Arguments args11179; args11179.Add(Value("planted_day"), false); return CallDictionaryGet(c, fn11178, std::move(args11179)); }()); Value v11177; v11177 = ([&]() -> Value { auto v11180 = ([&]() -> Value { auto fn11181 = s->Global("int"); Arguments args11182; args11182.Add(Get(s->LocalAt(8), Value("step")), false); return Call(c, fn11181, std::move(args11182)); }()); return Binary("FloorDiv", v11180, Value(int64_t{24})); }()); if (!static_cast<bool>(Binary("Eq", v11176, v11177))) return Value(false); v11176 = v11177; return Value(true); }()); if (!static_cast<bool>(v11165)) return v11165; v11165 = ([&]() -> Value { auto fn11183 = PrepareDictionaryGet(s->LocalAt(12)); Arguments args11184; args11184.Add(Value("watered_today"), false); return CallDictionaryGet(c, fn11183, std::move(args11184)); }()); return v11165; }())))) {
(void)([&]() -> Value { auto fn11185 = Attribute(s->LocalAt(6), "append"); Arguments args11186; args11186.Add(s->LocalAt(2), false); return Call(c, fn11185, std::move(args11186)); }());
}
}
if (static_cast<bool>(Unary("Not", s->LocalAt(6)))) {
break;
}
for (const auto& item11187 : Iterate(s->LocalAt(6))) {
s->SetAt(2, item11187);
auto v11188 = List({Value("PASS")});
Put(s->LocalAt(5), s->LocalAt(2), v11188);
}
auto v11189 = Get(s->LocalAt(5), Value(int64_t{0}));
Put(s->LocalAt(11), Value("farmer"), v11189);
auto v11190 = Slice(s->LocalAt(5), Value(int64_t{1}), Value{}, Value{});
Put(s->LocalAt(11), Value("hands"), v11190);
auto v11191 = Value(true);
s->SetAt(4, v11191);
auto v11192 = s->Global("_R127_REPORT");
auto v11193 = Value("last_hour_plants_dropped");
auto v11194 = Get(v11192, v11193);
Put(v11192, v11193, Inplace("Add", v11194, ([&]() -> Value { auto fn11195 = s->Global("len"); Arguments args11196; args11196.Add(s->LocalAt(6), false); return Call(c, fn11195, std::move(args11196)); }())));
}
return (static_cast<bool>(s->LocalAt(4)) ? s->LocalAt(11) : s->LocalAt(1));
return {};
}
}  // namespace kagg::opponents::compiled
