// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_f028cb54291fdd3b1baa(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"_", "access", "action", "after", "after_buys", "after_loss", "before", "budget", "buys", "commands", "cost", "farm", "future", "loss", "native", "need", "night", "o", "obs", "orders", "player", "positions", "private", "proposed", "shortage", "state", "step", "stock"};
s->PrepareSlots(s_names);
auto v11213 = ([&]() -> Value { auto fn11214 = s->Global("int"); Arguments args11215; args11215.Add(Get(s->LocalAt(18), Value("step")), false); return Call(c, fn11214, std::move(args11215)); }());
s->SetAt(26, v11213);
auto v11216 = ([&]() -> Value { auto fn11217 = s->Global("int"); Arguments args11218; args11218.Add(Get(s->LocalAt(18), Value("player")), false); return Call(c, fn11217, std::move(args11218)); }());
s->SetAt(20, v11216);
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto v11219 = Value(int64_t{144}); Value v11220; v11220 = s->LocalAt(26); if (!static_cast<bool>(Binary("LtE", v11219, v11220))) return Value(false); v11219 = v11220; v11220 = Value(int64_t{695}); if (!static_cast<bool>(Binary("Lt", v11219, v11220))) return Value(false); v11219 = v11220; return Value(true); }())))) {
return s->LocalAt(2);
}
auto v11221 = ([&]() -> Value { auto v11222 = ([&]() -> Value { auto fn11223 = PrepareDictionaryGet(s->LocalAt(2)); Arguments args11224; args11224.Add(Value("market"), false); return CallDictionaryGet(c, fn11223, std::move(args11224)); }()); if (static_cast<bool>(v11222)) return v11222; v11222 = List({}); return v11222; }());
s->SetAt(19, v11221);
if (static_cast<bool>(([&]() -> Value { auto v11225 = ([&]() -> Value { auto v11226 = ([&]() -> Value { auto fn11228 = s->Global("len"); Arguments args11229; args11229.Add(s->LocalAt(19), false); return Call(c, fn11228, std::move(args11229)); }()); Value v11227; v11227 = Value(int64_t{9}); if (!static_cast<bool>(Binary("Gt", v11226, v11227))) return Value(false); v11226 = v11227; return Value(true); }()); if (static_cast<bool>(v11225)) return v11225; v11225 = ([&]() -> Value { auto comp11230 = std::make_shared<Scope>(); comp11230->globals = s->globals; comp11230->parent = s; static constexpr const char* comp11230_names[] = {"o"}; comp11230->PrepareSlots(comp11230_names); auto result11231 = List(); for (const auto& item11232 : Iterate(s->LocalAt(19))) { comp11230->SetAt(0, item11232); if (static_cast<bool>(([&]() -> Value { auto v11233 = Slice(comp11230->LocalAt(0), Value{}, Value(int64_t{2}), Value{}); Value v11234; v11234 = Tuple({List({Value("BUY_PRODUCT"), Value("WHEAT")}), List({Value("SELL"), Value("WHEAT")})}); if (!static_cast<bool>(Binary("In", v11233, v11234))) return Value(false); v11233 = v11234; return Value(true); }()))) return Value(true); } return Value(false); }()); return v11225; }()))) {
return s->LocalAt(2);
}
auto v11235 = Get(Attribute(Attribute(s->Global("_IMPL"), "chassis"), "players"), s->LocalAt(20));
s->SetAt(14, v11235);
auto v11236 = Get(Get(Attribute(Attribute(s->Global("_IMPL"), "chassis"), "routes"), (static_cast<bool>(([&]() -> Value { auto v11237 = ([&]() -> Value { auto v11239 = s->LocalAt(26); return Binary("Add", v11239, Value(int64_t{1})); }()); Value v11238; v11238 = Value(int64_t{648}); if (!static_cast<bool>(Binary("GtE", v11237, v11238))) return Value(false); v11237 = v11238; return Value(true); }())) ? Value(int64_t{2}) : Get(s->LocalAt(14), Value("route")))), ([&]() -> Value { auto v11240 = s->LocalAt(26); return Binary("Add", v11240, Value(int64_t{1})); }()));
s->SetAt(12, v11236);
auto v11241 = ([&]() -> Value { Arguments args11242; args11242.Add(([&]() -> Value { auto v11243 = ([&]() -> Value { auto fn11244 = PrepareDictionaryGet(s->LocalAt(12)); Arguments args11245; args11245.Add(Value("farmer"), false); return CallDictionaryGet(c, fn11244, std::move(args11245)); }()); if (static_cast<bool>(v11243)) return v11243; v11243 = List({Value("PASS")}); return v11243; }()), false); args11242.Add(([&]() -> Value { auto v11246 = ([&]() -> Value { auto fn11247 = PrepareDictionaryGet(s->LocalAt(12)); Arguments args11248; args11248.Add(Value("hands"), false); return CallDictionaryGet(c, fn11247, std::move(args11248)); }()); if (static_cast<bool>(v11246)) return v11246; v11246 = List({}); return v11246; }()), true); return List(std::move(args11242.positional)); }());
s->SetAt(9, v11241);
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto comp11249 = std::make_shared<Scope>(); comp11249->globals = s->globals; comp11249->parent = s; static constexpr const char* comp11249_names[] = {"c"}; comp11249->PrepareSlots(comp11249_names); auto result11250 = List(); for (const auto& item11251 : Iterate(s->LocalAt(9))) { comp11249->SetAt(0, item11251); if (static_cast<bool>(([&]() -> Value { auto v11252 = Slice(comp11249->LocalAt(0), Value{}, Value(int64_t{2}), Value{}); Value v11253; v11253 = List({Value("PICKUP"), Value("WHEAT")}); if (!static_cast<bool>(Binary("Eq", v11252, v11253))) return Value(false); v11252 = v11253; return Value(true); }()))) return Value(true); } return Value(false); }())))) {
return s->LocalAt(2);
}
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto fn11254 = s->Global("_r97_budget"); Arguments args11255; args11255.positional.reserve(2); args11255.Add(s->LocalAt(18), false); args11255.Add(s->LocalAt(19), false); return Call(c, fn11254, std::move(args11255)); }())))) {
return s->LocalAt(2);
}
auto v11256 = ([&]() -> Value { auto fn11257 = s->Global("_r127_fields"); Arguments args11258; args11258.positional.reserve(2); args11258.Add(s->LocalAt(18), false); args11258.Add(s->LocalAt(2), false); return Call(c, fn11257, std::move(args11258)); }());
auto unpack11259 = Iterate(v11256);
ValidateUnpack(unpack11259, 2, false);
s->SetAt(11, unpack11259.at(0));
s->SetAt(22, unpack11259.at(1));
auto v11260 = ([&]() -> Value { auto v11261 = ([&]() -> Value { auto v11263 = s->LocalAt(26); return Binary("Mod", v11263, Value(int64_t{24})); }()); Value v11262; v11262 = Value(int64_t{23}); if (!static_cast<bool>(Binary("Eq", v11261, v11262))) return Value(false); v11261 = v11262; return Value(true); }());
s->SetAt(16, v11260);
auto v11264 = Tuple({Tuple({Value(int64_t{4}), Value(int64_t{4})}), Tuple({Value(int64_t{5}), Value(int64_t{4})}), Tuple({Value(int64_t{4}), Value(int64_t{5})}), Tuple({Value(int64_t{5}), Value(int64_t{5})})});
s->SetAt(1, v11264);
auto v11265 = ([&]() -> Value { Arguments args11266; args11266.Add(([&]() -> Value { auto fn11267 = s->Global("tuple"); Arguments args11268; args11268.Add(Get(s->LocalAt(11), Value("farmer")), false); return Call(c, fn11267, std::move(args11268)); }()), false); args11266.Add(([&]() -> Value { auto fn11269 = s->Global("map"); Arguments args11270; args11270.positional.reserve(2); args11270.Add(s->Global("tuple"), false); args11270.Add(Get(s->LocalAt(11), Value("hands")), false); return Call(c, fn11269, std::move(args11270)); }()), true); return List(std::move(args11266.positional)); }());
s->SetAt(21, v11265);
if (static_cast<bool>(s->LocalAt(16))) {
auto v11271 = List({Tuple({Value(int64_t{4}), Value(int64_t{4})})});
s->SetAt(21, v11271);
}
else {
for (const auto& item11272 : Iterate(s->LocalAt(19))) {
s->SetAt(17, item11272);
if (static_cast<bool>(([&]() -> Value { auto v11273 = s->LocalAt(17); if (!static_cast<bool>(v11273)) return v11273; v11273 = ([&]() -> Value { auto v11274 = Get(s->LocalAt(17), Value(int64_t{0})); Value v11275; v11275 = Value("HIRE"); if (!static_cast<bool>(Binary("Eq", v11274, v11275))) return Value(false); v11274 = v11275; return Value(true); }()); return v11273; }()))) {
(void)([&]() -> Value { auto fn11276 = Attribute(s->LocalAt(21), "append"); Arguments args11277; args11277.Add(([&]() -> Value { auto fn11278 = s->Global("min"); Arguments args11279; args11279.Add(s->LocalAt(1), false); args11279.Keyword("key", Define(&Code_79590424754d6a432b8b, s, Signature{{"p"}, {}, {}, {}, "", "", ([]() -> std::span<const char* const> { static constexpr const char* names[] = {"p"}; return names; }())}, true, "<lambda>")); return Call(c, fn11278, std::move(args11279)); }()), false); return Call(c, fn11276, std::move(args11277)); }());
}
}
}
auto v11284 = ([&]() -> Value { auto fn11285 = s->Global("sum"); Arguments args11286; args11286.Add(([&]() -> Value { auto comp11287 = std::make_shared<Scope>(); comp11287->globals = s->globals; comp11287->parent = s; static constexpr const char* comp11287_names[] = {"c", "pos"}; comp11287->PrepareSlots(comp11287_names); auto result11288 = List(); for (const auto& item11289 : Iterate(([&]() -> Value { auto fn11290 = s->Global("zip"); Arguments args11291; args11291.positional.reserve(2); args11291.Add(s->LocalAt(21), false); args11291.Add(s->LocalAt(9), false); return Call(c, fn11290, std::move(args11291)); }()))) { auto unpack11292 = Iterate(item11289); ValidateUnpack(unpack11292, 2, false); comp11287->SetAt(1, unpack11292.at(0)); comp11287->SetAt(0, unpack11292.at(1)); if (!static_cast<bool>(([&]() -> Value { auto v11293 = ([&]() -> Value { auto v11294 = comp11287->LocalAt(1); Value v11295; v11295 = comp11287->Captured("access"); if (!static_cast<bool>(Binary("In", v11294, v11295))) return Value(false); v11294 = v11295; return Value(true); }()); if (!static_cast<bool>(v11293)) return v11293; v11293 = ([&]() -> Value { auto v11296 = Slice(comp11287->LocalAt(0), Value{}, Value(int64_t{2}), Value{}); Value v11297; v11297 = List({Value("PICKUP"), Value("WHEAT")}); if (!static_cast<bool>(Binary("Eq", v11296, v11297))) return Value(false); v11296 = v11297; return Value(true); }()); return v11293; }()))) continue; result11288.node()->sequence.push_back(([&]() -> Value { auto fn11298 = comp11287->Global("max"); Arguments args11299; args11299.positional.reserve(2); args11299.Add(Value(int64_t{0}), false); args11299.Add((static_cast<bool>(([&]() -> Value { auto v11300 = ([&]() -> Value { auto fn11302 = comp11287->Global("len"); Arguments args11303; args11303.Add(comp11287->LocalAt(0), false); return Call(c, fn11302, std::move(args11303)); }()); Value v11301; v11301 = Value(int64_t{2}); if (!static_cast<bool>(Binary("Gt", v11300, v11301))) return Value(false); v11300 = v11301; return Value(true); }())) ? ([&]() -> Value { auto fn11304 = comp11287->Global("int"); Arguments args11305; args11305.Add(Get(comp11287->LocalAt(0), Value(int64_t{2})), false); return Call(c, fn11304, std::move(args11305)); }()) : Value(int64_t{1})), false); return Call(c, fn11298, std::move(args11299)); }())); } return result11288; }()), false); return Call(c, fn11285, std::move(args11286)); }());
s->SetAt(15, v11284);
auto v11306 = ([&]() -> Value { auto fn11307 = s->Global("_r97_market_stock"); Arguments args11308; args11308.positional.reserve(2); args11308.Add(Get(s->LocalAt(22), Value("shed")), false); args11308.Add(s->LocalAt(19), false); return Call(c, fn11307, std::move(args11308)); }());
auto unpack11309 = Iterate(v11306);
ValidateUnpack(unpack11309, 3, false);
s->SetAt(27, unpack11309.at(0));
s->SetAt(8, unpack11309.at(1));
s->SetAt(0, unpack11309.at(2));
auto v11310 = ([&]() -> Value { auto fn11311 = s->Global("_r97_delivery"); Arguments args11312; args11312.positional.reserve(3); args11312.Add(s->LocalAt(27), false); args11312.Add(s->LocalAt(22), false); args11312.Add(s->LocalAt(16), false); return Call(c, fn11311, std::move(args11312)); }());
auto unpack11313 = Iterate(v11310);
ValidateUnpack(unpack11313, 2, false);
s->SetAt(6, unpack11313.at(0));
s->SetAt(13, unpack11313.at(1));
auto v11314 = ([&]() -> Value { auto fn11315 = s->Global("max"); Arguments args11316; args11316.positional.reserve(2); args11316.Add(Value(int64_t{0}), false); args11316.Add(([&]() -> Value { auto v11317 = s->LocalAt(15); return Binary("Sub", v11317, ([&]() -> Value { auto fn11318 = PrepareDictionaryGet(s->LocalAt(6)); Arguments args11319; args11319.positional.reserve(2); args11319.Add(Value("WHEAT"), false); args11319.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn11318, std::move(args11319)); }())); }()), false); return Call(c, fn11315, std::move(args11316)); }());
s->SetAt(24, v11314);
if (static_cast<bool>(([&]() -> Value { auto v11320 = Unary("Not", s->LocalAt(24)); if (static_cast<bool>(v11320)) return v11320; v11320 = ([&]() -> Value { auto v11321 = s->LocalAt(24); Value v11322; v11322 = ([&]() -> Value { auto v11323 = Value(int64_t{100}); return Binary("Sub", v11323, ([&]() -> Value { auto fn11324 = s->Global("sum"); Arguments args11325; args11325.Add(([&]() -> Value { auto fn11326 = Attribute(Get(s->LocalAt(22), Value("shed")), "values"); Arguments args11327; return Call(c, fn11326, std::move(args11327)); }()), false); return Call(c, fn11324, std::move(args11325)); }())); }()); if (!static_cast<bool>(Binary("Gt", v11321, v11322))) return Value(false); v11321 = v11322; return Value(true); }()); return v11320; }()))) {
return s->LocalAt(2);
}
auto v11328 = ([&]() -> Value { auto fn11329 = s->Global("_r127_prefix_bound"); Arguments args11330; args11330.positional.reserve(2); args11330.Add(s->LocalAt(18), false); args11330.Add(s->LocalAt(24), false); return Call(c, fn11329, std::move(args11330)); }());
s->SetAt(10, v11328);
auto v11331 = ([&]() -> Value { auto fn11332 = s->Global("dict"); Arguments args11333; args11333.Add(s->LocalAt(18), false); args11333.Keyword("farms", ([&]() -> Value { auto comp11334 = std::make_shared<Scope>(); comp11334->globals = s->globals; comp11334->parent = s; static constexpr const char* comp11334_names[] = {"f"}; comp11334->PrepareSlots(comp11334_names); auto result11335 = List(); for (const auto& item11336 : Iterate(Get(s->LocalAt(18), Value("farms")))) { comp11334->SetAt(0, item11336); result11335.node()->sequence.push_back(([&]() -> Value { auto fn11337 = comp11334->Global("dict"); Arguments args11338; args11338.Add(comp11334->LocalAt(0), false); return Call(c, fn11337, std::move(args11338)); }())); } return result11335; }())); return Call(c, fn11332, std::move(args11333)); }());
s->SetAt(7, v11331);
auto v11339 = Get(Get(s->LocalAt(7), Value("farms")), s->LocalAt(20));
auto v11340 = Value("money");
auto v11341 = Get(v11339, v11340);
Put(v11339, v11340, Inplace("Sub", v11341, s->LocalAt(10)));
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto fn11342 = s->Global("_r97_budget"); Arguments args11343; args11343.positional.reserve(2); args11343.Add(s->LocalAt(7), false); args11343.Add(s->LocalAt(19), false); return Call(c, fn11342, std::move(args11343)); }())))) {
return s->LocalAt(2);
}
auto v11344 = ([&]() -> Value { Arguments args11345; args11345.Add(List({Value("BUY_PRODUCT"), Value("WHEAT"), s->LocalAt(24)}), false); args11345.Add(([&]() -> Value { auto fn11346 = Attribute(s->Global("copy"), "deepcopy"); Arguments args11347; args11347.Add(s->LocalAt(19), false); return Call(c, fn11346, std::move(args11347)); }()), true); return List(std::move(args11345.positional)); }());
s->SetAt(23, v11344);
auto v11348 = ([&]() -> Value { auto fn11349 = s->Global("_r97_market_stock"); Arguments args11350; args11350.positional.reserve(2); args11350.Add(Get(s->LocalAt(22), Value("shed")), false); args11350.Add(s->LocalAt(23), false); return Call(c, fn11349, std::move(args11350)); }());
auto unpack11351 = Iterate(v11348);
ValidateUnpack(unpack11351, 3, false);
s->SetAt(27, unpack11351.at(0));
s->SetAt(4, unpack11351.at(1));
s->SetAt(0, unpack11351.at(2));
auto v11352 = ([&]() -> Value { auto fn11353 = s->Global("_r97_delivery"); Arguments args11354; args11354.positional.reserve(3); args11354.Add(s->LocalAt(27), false); args11354.Add(s->LocalAt(22), false); args11354.Add(s->LocalAt(16), false); return Call(c, fn11353, std::move(args11354)); }());
auto unpack11355 = Iterate(v11352);
ValidateUnpack(unpack11355, 2, false);
s->SetAt(3, unpack11355.at(0));
s->SetAt(5, unpack11355.at(1));
if (static_cast<bool>(([&]() -> Value { auto v11356 = ([&]() -> Value { auto v11357 = ([&]() -> Value { auto fn11359 = PrepareDictionaryGet(s->LocalAt(3)); Arguments args11360; args11360.positional.reserve(2); args11360.Add(Value("WHEAT"), false); args11360.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn11359, std::move(args11360)); }()); Value v11358; v11358 = s->LocalAt(15); if (!static_cast<bool>(Binary("Lt", v11357, v11358))) return Value(false); v11357 = v11358; return Value(true); }()); if (static_cast<bool>(v11356)) return v11356; v11356 = ([&]() -> Value { auto comp11361 = std::make_shared<Scope>(); comp11361->globals = s->globals; comp11361->parent = s; static constexpr const char* comp11361_names[] = {"i", "q"}; comp11361->PrepareSlots(comp11361_names); auto result11362 = List(); for (const auto& item11363 : Iterate(([&]() -> Value { auto fn11364 = Attribute(s->LocalAt(8), "items"); Arguments args11365; return Call(c, fn11364, std::move(args11365)); }()))) { auto unpack11366 = Iterate(item11363); ValidateUnpack(unpack11366, 2, false); comp11361->SetAt(0, unpack11366.at(0)); comp11361->SetAt(1, unpack11366.at(1)); if (static_cast<bool>(([&]() -> Value { auto v11367 = ([&]() -> Value { auto fn11369 = PrepareDictionaryGet(comp11361->Captured("after_buys")); Arguments args11370; args11370.positional.reserve(2); args11370.Add(([&]() -> Value { auto v11371 = comp11361->LocalAt(0); return Binary("Add", v11371, Value(int64_t{1})); }()), false); args11370.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn11369, std::move(args11370)); }()); Value v11368; v11368 = comp11361->LocalAt(1); if (!static_cast<bool>(Binary("Lt", v11367, v11368))) return Value(false); v11367 = v11368; return Value(true); }()))) return Value(true); } return Value(false); }()); if (static_cast<bool>(v11356)) return v11356; v11356 = ([&]() -> Value { auto comp11372 = std::make_shared<Scope>(); comp11372->globals = s->globals; comp11372->parent = s; static constexpr const char* comp11372_names[] = {"p", "q"}; comp11372->PrepareSlots(comp11372_names); auto result11373 = List(); for (const auto& item11374 : Iterate(([&]() -> Value { auto fn11375 = Attribute(s->LocalAt(5), "items"); Arguments args11376; return Call(c, fn11375, std::move(args11376)); }()))) { auto unpack11377 = Iterate(item11374); ValidateUnpack(unpack11377, 2, false); comp11372->SetAt(0, unpack11377.at(0)); comp11372->SetAt(1, unpack11377.at(1)); if (static_cast<bool>(([&]() -> Value { auto v11378 = comp11372->LocalAt(1); Value v11379; v11379 = ([&]() -> Value { auto fn11380 = PrepareDictionaryGet(comp11372->Captured("loss")); Arguments args11381; args11381.positional.reserve(2); args11381.Add(comp11372->LocalAt(0), false); args11381.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn11380, std::move(args11381)); }()); if (!static_cast<bool>(Binary("Gt", v11378, v11379))) return Value(false); v11378 = v11379; return Value(true); }()))) return Value(true); } return Value(false); }()); return v11356; }()))) {
return s->LocalAt(2);
}
auto v11382 = Tuple({([&]() -> Value { auto v11383 = s->LocalAt(26); return Binary("Add", v11383, Value(int64_t{1})); }()), ([&]() -> Value { auto fn11384 = PrepareDictionaryGet(s->LocalAt(3)); Arguments args11385; args11385.positional.reserve(2); args11385.Add(Value("WHEAT"), false); args11385.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn11384, std::move(args11385)); }()), s->LocalAt(24)});
Put(s->LocalAt(25), Value("pending_grain"), v11382);
auto v11386 = s->Global("_R127_REPORT");
auto v11387 = Value("priority_grain_orders");
auto v11388 = Get(v11386, v11387);
Put(v11386, v11387, Inplace("Add", v11388, Value(int64_t{1})));
auto v11389 = s->Global("_R127_REPORT");
auto v11390 = Value("priority_grain_units");
auto v11391 = Get(v11389, v11390);
Put(v11389, v11390, Inplace("Add", v11391, s->LocalAt(24)));
return ([&]() -> Value { auto fn11392 = s->Global("dict"); Arguments args11393; args11393.Add(s->LocalAt(2), false); args11393.Keyword("market", s->LocalAt(23)); return Call(c, fn11392, std::move(args11393)); }());
return {};
}
}  // namespace kagg::opponents::compiled
