// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_cc2c1dc6ccc1553dfcf1(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"_", "action", "after", "bag", "best", "final", "item", "loss", "n", "new_loss", "obs", "orders", "original", "private", "proposed", "released", "remaining", "stock", "tail", "take"};
s->PrepareSlots(s_names);
if (static_cast<bool>(([&]() -> Value { auto v12190 = ([&]() -> Value { auto v12192 = ([&]() -> Value { auto fn12193 = s->Global("int"); Arguments args12194; args12194.Add(Get(s->LocalAt(10), Value("step")), false); return Call(c, fn12193, std::move(args12194)); }()); return Binary("Mod", v12192, Value(int64_t{24})); }()); Value v12191; v12191 = Value(int64_t{23}); if (!static_cast<bool>(Binary("NotEq", v12190, v12191))) return Value(false); v12190 = v12191; return Value(true); }()))) {
return s->LocalAt(1);
}
auto v12195 = ([&]() -> Value { auto v12196 = ([&]() -> Value { auto fn12197 = PrepareDictionaryGet(s->LocalAt(1)); Arguments args12198; args12198.Add(Value("market"), false); return CallDictionaryGet(c, fn12197, std::move(args12198)); }()); if (static_cast<bool>(v12196)) return v12196; v12196 = List({}); return v12196; }());
s->SetAt(11, v12195);
if (static_cast<bool>(([&]() -> Value { auto v12199 = ([&]() -> Value { auto v12200 = ([&]() -> Value { auto fn12202 = s->Global("len"); Arguments args12203; args12203.Add(s->LocalAt(11), false); return Call(c, fn12202, std::move(args12203)); }()); Value v12201; v12201 = Value(int64_t{10}); if (!static_cast<bool>(Binary("GtE", v12200, v12201))) return Value(false); v12200 = v12201; return Value(true); }()); if (static_cast<bool>(v12199)) return v12199; v12199 = Unary("Not", ([&]() -> Value { auto fn12204 = s->Global("_r97_budget"); Arguments args12205; args12205.positional.reserve(2); args12205.Add(s->LocalAt(10), false); args12205.Add(s->LocalAt(11), false); return Call(c, fn12204, std::move(args12205)); }())); return v12199; }()))) {
return s->LocalAt(1);
}
auto v12206 = ([&]() -> Value { auto fn12207 = s->Global("_r127_fields"); Arguments args12208; args12208.positional.reserve(2); args12208.Add(s->LocalAt(10), false); args12208.Add(s->LocalAt(1), false); return Call(c, fn12207, std::move(args12208)); }());
auto unpack12209 = Iterate(v12206);
ValidateUnpack(unpack12209, 2, false);
s->SetAt(0, unpack12209.at(0));
s->SetAt(13, unpack12209.at(1));
auto v12210 = ([&]() -> Value { auto fn12211 = s->Global("_r97_market_stock"); Arguments args12212; args12212.positional.reserve(2); args12212.Add(Get(s->LocalAt(13), Value("shed")), false); args12212.Add(s->LocalAt(11), false); return Call(c, fn12211, std::move(args12212)); }());
auto unpack12213 = Iterate(v12210);
ValidateUnpack(unpack12213, 3, false);
s->SetAt(17, unpack12213.at(0));
s->SetAt(0, unpack12213.at(1));
s->SetAt(0, unpack12213.at(2));
auto v12214 = ([&]() -> Value { auto fn12215 = s->Global("_r97_delivery"); Arguments args12216; args12216.positional.reserve(3); args12216.Add(s->LocalAt(17), false); args12216.Add(s->LocalAt(13), false); args12216.Add(Value(true), false); return Call(c, fn12215, std::move(args12216)); }());
auto unpack12217 = Iterate(v12214);
ValidateUnpack(unpack12217, 2, false);
s->SetAt(12, unpack12217.at(0));
s->SetAt(7, unpack12217.at(1));
if (static_cast<bool>(Unary("Not", s->LocalAt(7)))) {
return s->LocalAt(1);
}
auto v12218 = ([&]() -> Value { auto fn12219 = s->Global("max"); Arguments args12220; args12220.positional.reserve(2); args12220.Add(Value(int64_t{0}), false); args12220.Add(([&]() -> Value { auto v12221 = Value(int64_t{100}); return Binary("Sub", v12221, ([&]() -> Value { auto fn12222 = s->Global("sum"); Arguments args12223; args12223.Add(([&]() -> Value { auto fn12224 = Attribute(s->LocalAt(17), "values"); Arguments args12225; return Call(c, fn12224, std::move(args12225)); }()), false); return Call(c, fn12222, std::move(args12223)); }())); }()), false); return Call(c, fn12219, std::move(args12220)); }());
s->SetAt(16, v12218);
auto v12226 = List({});
s->SetAt(18, v12226);
for (const auto& item12227 : Iterate(Get(s->LocalAt(13), Value("inventories")))) {
s->SetAt(3, item12227);
for (const auto& item12228 : Iterate(([&]() -> Value { auto fn12229 = Attribute(s->LocalAt(3), "items"); Arguments args12230; return Call(c, fn12229, std::move(args12230)); }()))) {
auto unpack12231 = Iterate(item12228);
ValidateUnpack(unpack12231, 2, false);
s->SetAt(6, unpack12231.at(0));
s->SetAt(8, unpack12231.at(1));
auto v12232 = ([&]() -> Value { auto fn12233 = s->Global("max"); Arguments args12234; args12234.positional.reserve(2); args12234.Add(Value(int64_t{0}), false); args12234.Add(([&]() -> Value { auto fn12235 = s->Global("int"); Arguments args12236; args12236.Add(s->LocalAt(8), false); return Call(c, fn12235, std::move(args12236)); }()), false); return Call(c, fn12233, std::move(args12234)); }());
s->SetAt(8, v12232);
auto v12237 = ([&]() -> Value { auto fn12238 = s->Global("min"); Arguments args12239; args12239.positional.reserve(2); args12239.Add(s->LocalAt(8), false); args12239.Add(s->LocalAt(16), false); return Call(c, fn12238, std::move(args12239)); }());
s->SetAt(19, v12237);
auto v12240 = s->LocalAt(16);
s->SetAt(16, Inplace("Sub", v12240, s->LocalAt(19)));
if (static_cast<bool>(([&]() -> Value { auto v12241 = s->LocalAt(8); Value v12242; v12242 = s->LocalAt(19); if (!static_cast<bool>(Binary("Gt", v12241, v12242))) return Value(false); v12241 = v12242; return Value(true); }()))) {
(void)([&]() -> Value { auto fn12243 = Attribute(s->LocalAt(18), "extend"); Arguments args12244; args12244.Add(([&]() -> Value { auto v12245 = List({s->LocalAt(6)}); return Binary("Mult", v12245, ([&]() -> Value { auto v12246 = s->LocalAt(8); return Binary("Sub", v12246, s->LocalAt(19)); }())); }()), false); return Call(c, fn12243, std::move(args12244)); }());
}
}
}
auto v12247 = ([&]() -> Value { auto dict12248 = Dict(); return dict12248; }());
s->SetAt(15, v12247);
auto v12249 = Value{};
s->SetAt(4, v12249);
for (const auto& item12250 : Iterate(s->LocalAt(18))) {
s->SetAt(6, item12250);
auto v12251 = ([&]() -> Value { auto v12252 = ([&]() -> Value { auto fn12253 = PrepareDictionaryGet(s->LocalAt(15)); Arguments args12254; args12254.positional.reserve(2); args12254.Add(s->LocalAt(6), false); args12254.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn12253, std::move(args12254)); }()); return Binary("Add", v12252, Value(int64_t{1})); }());
Put(s->LocalAt(15), s->LocalAt(6), v12251);
if (static_cast<bool>(([&]() -> Value { auto v12255 = ([&]() -> Value { auto v12256 = s->LocalAt(6); Value v12257; v12257 = Get(Get(s->LocalAt(10), Value("market")), Value("prices")); if (!static_cast<bool>(Binary("NotIn", v12256, v12257))) return Value(false); v12256 = v12257; return Value(true); }()); if (static_cast<bool>(v12255)) return v12255; v12255 = ([&]() -> Value { auto v12258 = Get(s->LocalAt(15), s->LocalAt(6)); Value v12259; v12259 = ([&]() -> Value { auto fn12260 = PrepareDictionaryGet(s->LocalAt(17)); Arguments args12261; args12261.positional.reserve(2); args12261.Add(s->LocalAt(6), false); args12261.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn12260, std::move(args12261)); }()); if (!static_cast<bool>(Binary("Gt", v12258, v12259))) return Value(false); v12258 = v12259; return Value(true); }()); return v12255; }()))) {
break;
}
if (static_cast<bool>(([&]() -> Value { auto v12262 = ([&]() -> Value { auto v12264 = ([&]() -> Value { auto fn12265 = s->Global("len"); Arguments args12266; args12266.Add(s->LocalAt(11), false); return Call(c, fn12265, std::move(args12266)); }()); return Binary("Add", v12264, ([&]() -> Value { auto fn12267 = s->Global("len"); Arguments args12268; args12268.Add(s->LocalAt(15), false); return Call(c, fn12267, std::move(args12268)); }())); }()); Value v12263; v12263 = Value(int64_t{10}); if (!static_cast<bool>(Binary("Gt", v12262, v12263))) return Value(false); v12262 = v12263; return Value(true); }()))) {
break;
}
auto v12269 = ([&]() -> Value { auto v12270 = ([&]() -> Value { auto fn12271 = s->Global("list"); Arguments args12272; args12272.Add(s->LocalAt(11), false); return Call(c, fn12271, std::move(args12272)); }()); return Binary("Add", v12270, ([&]() -> Value { auto comp12273 = std::make_shared<Scope>(); comp12273->globals = s->globals; comp12273->parent = s; static constexpr const char* comp12273_names[] = {"n", "p"}; comp12273->PrepareSlots(comp12273_names); auto result12274 = List(); for (const auto& item12275 : Iterate(([&]() -> Value { auto fn12276 = Attribute(s->LocalAt(15), "items"); Arguments args12277; return Call(c, fn12276, std::move(args12277)); }()))) { auto unpack12278 = Iterate(item12275); ValidateUnpack(unpack12278, 2, false); comp12273->SetAt(1, unpack12278.at(0)); comp12273->SetAt(0, unpack12278.at(1)); result12274.node()->sequence.push_back(List({Value("SELL"), comp12273->LocalAt(1), comp12273->LocalAt(0)})); } return result12274; }())); }());
s->SetAt(14, v12269);
auto v12279 = ([&]() -> Value { auto fn12280 = s->Global("_r97_market_stock"); Arguments args12281; args12281.positional.reserve(2); args12281.Add(Get(s->LocalAt(13), Value("shed")), false); args12281.Add(s->LocalAt(14), false); return Call(c, fn12280, std::move(args12281)); }());
auto unpack12282 = Iterate(v12279);
ValidateUnpack(unpack12282, 3, false);
s->SetAt(2, unpack12282.at(0));
s->SetAt(0, unpack12282.at(1));
s->SetAt(0, unpack12282.at(2));
auto v12283 = ([&]() -> Value { auto fn12284 = s->Global("_r97_delivery"); Arguments args12285; args12285.positional.reserve(3); args12285.Add(s->LocalAt(2), false); args12285.Add(s->LocalAt(13), false); args12285.Add(Value(true), false); return Call(c, fn12284, std::move(args12285)); }());
auto unpack12286 = Iterate(v12283);
ValidateUnpack(unpack12286, 2, false);
s->SetAt(5, unpack12286.at(0));
s->SetAt(9, unpack12286.at(1));
if (static_cast<bool>(([&]() -> Value { auto fn12287 = s->Global("_r148_same_stock"); Arguments args12288; args12288.positional.reserve(2); args12288.Add(s->LocalAt(12), false); args12288.Add(s->LocalAt(5), false); return Call(c, fn12287, std::move(args12288)); }()))) {
auto v12289 = Tuple({s->LocalAt(14), ([&]() -> Value { auto fn12290 = s->Global("dict"); Arguments args12291; args12291.Add(s->LocalAt(15), false); return Call(c, fn12290, std::move(args12291)); }()), s->LocalAt(5), s->LocalAt(9)});
s->SetAt(4, v12289);
}
}
if (static_cast<bool>(([&]() -> Value { auto v12292 = s->LocalAt(4); Value v12293; v12293 = Value{}; if (!static_cast<bool>(Binary("Is", v12292, v12293))) return Value(false); v12292 = v12293; return Value(true); }()))) {
return s->LocalAt(1);
}
auto v12294 = s->LocalAt(4);
auto unpack12295 = Iterate(v12294);
ValidateUnpack(unpack12295, 4, false);
s->SetAt(14, unpack12295.at(0));
s->SetAt(15, unpack12295.at(1));
s->SetAt(5, unpack12295.at(2));
s->SetAt(9, unpack12295.at(3));
auto v12296 = s->Global("_R148_REPORT");
auto v12297 = Value("overflow_turns");
auto v12298 = Get(v12296, v12297);
Put(v12296, v12297, Inplace("Add", v12298, Value(int64_t{1})));
auto v12299 = s->Global("_R148_REPORT");
auto v12300 = Value("overflow_units_reclaimed");
auto v12301 = Get(v12299, v12300);
Put(v12299, v12300, Inplace("Add", v12301, ([&]() -> Value { auto fn12302 = s->Global("sum"); Arguments args12303; args12303.Add(([&]() -> Value { auto fn12304 = Attribute(s->LocalAt(15), "values"); Arguments args12305; return Call(c, fn12304, std::move(args12305)); }()), false); return Call(c, fn12302, std::move(args12303)); }())));
auto v12306 = s->Global("_R148_REPORT");
auto v12307 = Value("overflow_quote_exposure");
auto v12308 = Get(v12306, v12307);
Put(v12306, v12307, Inplace("Add", v12308, ([&]() -> Value { auto fn12309 = s->Global("sum"); Arguments args12310; args12310.Add(([&]() -> Value { auto comp12311 = std::make_shared<Scope>(); comp12311->globals = s->globals; comp12311->parent = s; static constexpr const char* comp12311_names[] = {"n", "p"}; comp12311->PrepareSlots(comp12311_names); auto result12312 = List(); for (const auto& item12313 : Iterate(([&]() -> Value { auto fn12314 = Attribute(s->LocalAt(15), "items"); Arguments args12315; return Call(c, fn12314, std::move(args12315)); }()))) { auto unpack12316 = Iterate(item12313); ValidateUnpack(unpack12316, 2, false); comp12311->SetAt(1, unpack12316.at(0)); comp12311->SetAt(0, unpack12316.at(1)); result12312.node()->sequence.push_back(([&]() -> Value { auto v12317 = comp12311->LocalAt(0); return Binary("Mult", v12317, Get(Get(Get(comp12311->Captured("obs"), Value("market")), Value("prices")), comp12311->LocalAt(1))); }())); } return result12312; }()), false); return Call(c, fn12309, std::move(args12310)); }())));
auto v12318 = Tuple({([&]() -> Value { auto v12319 = ([&]() -> Value { auto fn12320 = s->Global("int"); Arguments args12321; args12321.Add(Get(s->LocalAt(10), Value("step")), false); return Call(c, fn12320, std::move(args12321)); }()); return Binary("Add", v12319, Value(int64_t{1})); }()), ([&]() -> Value { auto fn12322 = s->Global("dict"); Arguments args12323; args12323.Add(s->LocalAt(5), false); return Call(c, fn12322, std::move(args12323)); }())});
Put(s->Global("_R148_PENDING"), ([&]() -> Value { auto fn12324 = s->Global("int"); Arguments args12325; args12325.Add(Get(s->LocalAt(10), Value("player")), false); return Call(c, fn12324, std::move(args12325)); }()), v12318);
return ([&]() -> Value { auto fn12326 = s->Global("dict"); Arguments args12327; args12327.Add(s->LocalAt(1), false); args12327.Keyword("market", s->LocalAt(14)); return Call(c, fn12326, std::move(args12327)); }());
return {};
}
}  // namespace kagg::opponents::compiled
