// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_1cb39daec3b8092f276a(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "budget", "changed", "count", "crop_workers", "day", "expected", "extra", "farm", "fertilizer", "fertilizer_quantity", "labor", "native", "obs", "offset", "order", "parent_hires", "planned", "private", "remaining", "state", "step"};
s->PrepareSlots(s_names);
auto v14248 = ([&]() -> Value { auto fn14249 = s->Global("int"); Arguments args14250; args14250.Add(Get(s->LocalAt(13), Value("step")), false); return Call(c, fn14249, std::move(args14250)); }());
s->SetAt(21, v14248);
auto v14251 = ([&]() -> Value { auto v14252 = s->LocalAt(21); return Binary("FloorDiv", v14252, Value(int64_t{24})); }());
s->SetAt(5, v14251);
auto v14253 = ([&]() -> Value { auto v14254 = s->LocalAt(21); return Binary("Mod", v14254, Value(int64_t{24})); }());
s->SetAt(14, v14253);
auto v14255 = Get(Get(s->LocalAt(13), Value("farms")), Get(s->LocalAt(13), Value("player")));
s->SetAt(8, v14255);
auto v14256 = Get(s->LocalAt(13), Value("private"));
s->SetAt(18, v14256);
if (static_cast<bool>(([&]() -> Value { auto v14257 = Unary("Not", ([&]() -> Value { auto fn14258 = PrepareDictionaryGet(s->LocalAt(20)); Arguments args14259; args14259.Add(Value("committed"), false); return CallDictionaryGet(c, fn14258, std::move(args14259)); }())); if (!static_cast<bool>(v14257)) return v14257; v14257 = ([&]() -> Value { auto v14260 = s->LocalAt(5); Value v14261; v14261 = Value(int64_t{18}); if (!static_cast<bool>(Binary("NotEq", v14260, v14261))) return Value(false); v14260 = v14261; return Value(true); }()); return v14257; }()))) {
return s->LocalAt(0);
}
if (static_cast<bool>(([&]() -> Value { auto v14262 = ([&]() -> Value { auto v14263 = ([&]() -> Value { auto fn14265 = PrepareDictionaryGet(s->LocalAt(20)); Arguments args14266; args14266.Add(Value("requested_day"), false); return CallDictionaryGet(c, fn14265, std::move(args14266)); }()); Value v14264; v14264 = s->LocalAt(5); if (!static_cast<bool>(Binary("Eq", v14263, v14264))) return Value(false); v14263 = v14264; return Value(true); }()); if (static_cast<bool>(v14262)) return v14262; v14262 = ([&]() -> Value { auto v14267 = s->LocalAt(14); Value v14268; v14268 = Value(int64_t{3}); if (!static_cast<bool>(Binary("Gt", v14267, v14268))) return Value(false); v14267 = v14268; return Value(true); }()); return v14262; }()))) {
return s->LocalAt(0);
}
auto v14269 = ([&]() -> Value { auto fn14270 = s->Global("_v219_native_day"); Arguments args14271; args14271.positional.reserve(2); args14271.Add(s->LocalAt(12), false); args14271.Add(s->LocalAt(5), false); return Call(c, fn14270, std::move(args14271)); }());
s->SetAt(17, v14269);
auto v14272 = Slice(s->LocalAt(17), ([&]() -> Value { auto v14273 = s->LocalAt(14); return Binary("Add", v14273, Value(int64_t{1})); }()), Value{}, Value{});
s->SetAt(19, v14272);
if (static_cast<bool>(([&]() -> Value { auto comp14274 = std::make_shared<Scope>(); comp14274->globals = s->globals; comp14274->parent = s; static constexpr const char* comp14274_names[] = {"a", "o"}; comp14274->PrepareSlots(comp14274_names); auto result14275 = List(); for (const auto& item14276 : Iterate(s->LocalAt(19))) { comp14274->SetAt(0, item14276); for (const auto& item14277 : Iterate(([&]() -> Value { auto fn14278 = PrepareDictionaryGet(comp14274->LocalAt(0)); Arguments args14279; args14279.positional.reserve(2); args14279.Add(Value("market"), false); args14279.Add(List({}), false); return CallDictionaryGet(c, fn14278, std::move(args14279)); }()))) { comp14274->SetAt(1, item14277); if (static_cast<bool>(([&]() -> Value { auto v14280 = comp14274->LocalAt(1); if (!static_cast<bool>(v14280)) return v14280; v14280 = ([&]() -> Value { auto v14281 = Get(comp14274->LocalAt(1), Value(int64_t{0})); Value v14282; v14282 = Value("HIRE"); if (!static_cast<bool>(Binary("Eq", v14281, v14282))) return Value(false); v14281 = v14282; return Value(true); }()); return v14280; }()))) return Value(true); } } return Value(false); }()))) {
return s->LocalAt(0);
}
auto v14283 = ([&]() -> Value { auto fn14284 = s->Global("sum"); Arguments args14285; args14285.Add(([&]() -> Value { auto comp14286 = std::make_shared<Scope>(); comp14286->globals = s->globals; comp14286->parent = s; static constexpr const char* comp14286_names[] = {"o"}; comp14286->PrepareSlots(comp14286_names); auto result14287 = List(); for (const auto& item14288 : Iterate(Get(s->LocalAt(0), Value("market")))) { comp14286->SetAt(0, item14288); result14287.node()->sequence.push_back(([&]() -> Value { auto v14289 = ([&]() -> Value { auto fn14290 = comp14286->Global("bool"); Arguments args14291; args14291.Add(comp14286->LocalAt(0), false); return Call(c, fn14290, std::move(args14291)); }()); if (!static_cast<bool>(v14289)) return v14289; v14289 = ([&]() -> Value { auto v14292 = Get(comp14286->LocalAt(0), Value(int64_t{0})); Value v14293; v14293 = Value("HIRE"); if (!static_cast<bool>(Binary("Eq", v14292, v14293))) return Value(false); v14292 = v14293; return Value(true); }()); return v14289; }())); } return result14287; }()), false); return Call(c, fn14284, std::move(args14285)); }());
s->SetAt(16, v14283);
auto v14294 = ([&]() -> Value { auto fn14295 = s->Global("max"); Arguments args14296; args14296.Add(([&]() -> Value { auto comp14297 = std::make_shared<Scope>(); comp14297->globals = s->globals; comp14297->parent = s; static constexpr const char* comp14297_names[] = {"a"}; comp14297->PrepareSlots(comp14297_names); auto result14298 = List(); for (const auto& item14299 : Iterate(s->LocalAt(17))) { comp14297->SetAt(0, item14299); result14298.node()->sequence.push_back(([&]() -> Value { auto fn14300 = comp14297->Global("len"); Arguments args14301; args14301.Add(([&]() -> Value { auto fn14302 = PrepareDictionaryGet(comp14297->LocalAt(0)); Arguments args14303; args14303.positional.reserve(2); args14303.Add(Value("hands"), false); args14303.Add(List({}), false); return CallDictionaryGet(c, fn14302, std::move(args14303)); }()), false); return Call(c, fn14300, std::move(args14301)); }())); } return result14298; }()), false); return Call(c, fn14295, std::move(args14296)); }());
s->SetAt(6, v14294);
if (static_cast<bool>(([&]() -> Value { auto v14304 = ([&]() -> Value { auto v14306 = ([&]() -> Value { auto fn14307 = s->Global("len"); Arguments args14308; args14308.Add(Get(s->LocalAt(8), Value("hands")), false); return Call(c, fn14307, std::move(args14308)); }()); return Binary("Add", v14306, s->LocalAt(16)); }()); Value v14305; v14305 = s->LocalAt(6); if (!static_cast<bool>(Binary("NotEq", v14304, v14305))) return Value(false); v14304 = v14305; return Value(true); }()))) {
return s->LocalAt(0);
}
auto v14309 = ([&]() -> Value { auto fn14310 = s->Global("bool"); Arguments args14311; args14311.Add(([&]() -> Value { auto v14312 = s->Global("_V219_FERTILIZE"); if (!static_cast<bool>(v14312)) return v14312; v14312 = ([&]() -> Value { auto v14313 = s->LocalAt(5); Value v14314; v14314 = Tuple({Value(int64_t{24}), Value(int64_t{27})}); if (!static_cast<bool>(Binary("In", v14313, v14314))) return Value(false); v14313 = v14314; return Value(true); }()); if (!static_cast<bool>(v14312)) return v14312; v14312 = ([&]() -> Value { auto fn14315 = s->Global("_r79_tomato_fertilizer_worthwhile"); Arguments args14316; args14316.positional.reserve(2); args14316.Add(s->LocalAt(13), false); args14316.Add(s->LocalAt(0), false); return Call(c, fn14315, std::move(args14316)); }()); return v14312; }()), false); return Call(c, fn14310, std::move(args14311)); }());
s->SetAt(9, v14309);
auto v14317 = (static_cast<bool>(([&]() -> Value { auto v14318 = ([&]() -> Value { auto v14319 = s->LocalAt(5); Value v14320; v14320 = Tuple({Value(int64_t{19}), Value(int64_t{20}), Value(int64_t{21}), Value(int64_t{22}), Value(int64_t{23}), Value(int64_t{25})}); if (!static_cast<bool>(Binary("In", v14319, v14320))) return Value(false); v14319 = v14320; return Value(true); }()); if (!static_cast<bool>(v14318)) return v14318; v14318 = ([&]() -> Value { auto v14321 = s->LocalAt(14); Value v14322; v14322 = Value(int64_t{2}); if (!static_cast<bool>(Binary("LtE", v14321, v14322))) return Value(false); v14321 = v14322; return Value(true); }()); return v14318; }())) ? Value(int64_t{1}) : (static_cast<bool>(([&]() -> Value { auto v14323 = Value(int64_t{26}); Value v14324; v14324 = s->LocalAt(5); if (!static_cast<bool>(Binary("LtE", v14323, v14324))) return Value(false); v14323 = v14324; v14324 = Value(int64_t{28}); if (!static_cast<bool>(Binary("LtE", v14323, v14324))) return Value(false); v14323 = v14324; return Value(true); }())) ? Value(int64_t{3}) : Value(int64_t{2})));
s->SetAt(4, v14317);
auto v14325 = ([&]() -> Value { auto fn14326 = s->Global("_r53_labor_assignment"); Arguments args14327; args14327.positional.reserve(3); args14327.Add(s->LocalAt(13), false); args14327.Add(s->LocalAt(0), false); args14327.Add(s->LocalAt(9), false); return Call(c, fn14326, std::move(args14327)); }());
s->SetAt(11, v14325);
if (static_cast<bool>(([&]() -> Value { auto v14328 = s->LocalAt(11); Value v14329; v14329 = Value{}; if (!static_cast<bool>(Binary("IsNot", v14328, v14329))) return Value(false); v14328 = v14329; return Value(true); }()))) {
auto v14330 = Get(s->LocalAt(11), Value("workers"));
s->SetAt(4, v14330);
}
auto v14331 = ([&]() -> Value { auto v14332 = s->LocalAt(4); return Binary("Add", v14332, ([&]() -> Value { auto fn14333 = s->Global("int"); Arguments args14334; args14334.Add(([&]() -> Value { auto v14335 = s->LocalAt(9); if (!static_cast<bool>(v14335)) return v14335; v14335 = ([&]() -> Value { auto v14336 = s->LocalAt(5); Value v14337; v14337 = Value(int64_t{27}); if (!static_cast<bool>(Binary("Eq", v14336, v14337))) return Value(false); v14336 = v14337; return Value(true); }()); if (!static_cast<bool>(v14335)) return v14335; v14335 = ([&]() -> Value { auto v14338 = s->LocalAt(11); Value v14339; v14339 = Value{}; if (!static_cast<bool>(Binary("Is", v14338, v14339))) return Value(false); v14338 = v14339; return Value(true); }()); return v14335; }()), false); return Call(c, fn14333, std::move(args14334)); }())); }());
s->SetAt(3, v14331);
auto v14340 = List({});
s->SetAt(7, v14340);
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto fn14341 = PrepareDictionaryGet(s->LocalAt(20)); Arguments args14342; args14342.Add(Value("committed"), false); return CallDictionaryGet(c, fn14341, std::move(args14342)); }())))) {
auto v14343 = s->LocalAt(7);
s->SetAt(7, Inplace("Add", v14343, List({List({Value("BUY_LAND")}), List({Value("BUY_SEED"), Value("TOMATO"), Value(int64_t{10})})})));
}
auto v14344 = (static_cast<bool>(s->LocalAt(9)) ? ([&]() -> Value { auto fn14345 = s->Global("_r70_parent_fert_qty"); Arguments args14346; args14346.positional.reserve(4); args14346.Add(s->LocalAt(13), false); args14346.Add(s->LocalAt(0), false); args14346.Add(s->LocalAt(17), false); args14346.Add(s->LocalAt(14), false); return Call(c, fn14345, std::move(args14346)); }()) : Value(int64_t{0}));
s->SetAt(10, v14344);
if (static_cast<bool>(s->LocalAt(9))) {
(void)([&]() -> Value { auto fn14347 = Attribute(s->LocalAt(7), "append"); Arguments args14348; args14348.Add(List({Value("BUY_PRODUCT"), Value("FERTILIZER"), s->LocalAt(10)}), false); return Call(c, fn14347, std::move(args14348)); }());
}
auto v14349 = s->LocalAt(7);
s->SetAt(7, Inplace("Add", v14349, ([&]() -> Value { auto comp14350 = std::make_shared<Scope>(); comp14350->globals = s->globals; comp14350->parent = s; static constexpr const char* comp14350_names[] = {"_"}; comp14350->PrepareSlots(comp14350_names); auto result14351 = List(); for (const auto& item14352 : Iterate(([&]() -> Value { auto fn14353 = s->Global("range"); Arguments args14354; args14354.Add(s->LocalAt(3), false); return Call(c, fn14353, std::move(args14354)); }()))) { comp14350->SetAt(0, item14352); result14351.node()->sequence.push_back(List({Value("HIRE")})); } return result14351; }())));
if (static_cast<bool>(([&]() -> Value { auto v14355 = ([&]() -> Value { auto v14357 = ([&]() -> Value { auto fn14358 = s->Global("len"); Arguments args14359; args14359.Add(Get(s->LocalAt(0), Value("market")), false); return Call(c, fn14358, std::move(args14359)); }()); return Binary("Add", v14357, ([&]() -> Value { auto fn14360 = s->Global("len"); Arguments args14361; args14361.Add(s->LocalAt(7), false); return Call(c, fn14360, std::move(args14361)); }())); }()); Value v14356; v14356 = s->Global("MAX_ORDERS"); if (!static_cast<bool>(Binary("Gt", v14355, v14356))) return Value(false); v14355 = v14356; return Value(true); }()))) {
return s->LocalAt(0);
}
auto v14362 = ([&]() -> Value { auto fn14363 = s->Global("sum"); Arguments args14364; args14364.Add(([&]() -> Value { auto comp14365 = std::make_shared<Scope>(); comp14365->globals = s->globals; comp14365->parent = s; static constexpr const char* comp14365_names[] = {"n"}; comp14365->PrepareSlots(comp14365_names); auto result14366 = List(); for (const auto& item14367 : Iterate(([&]() -> Value { auto fn14368 = s->Global("range"); Arguments args14369; args14369.positional.reserve(2); args14369.Add(Get(s->LocalAt(8), Value("hires_today")), false); args14369.Add(([&]() -> Value { auto v14370 = ([&]() -> Value { auto v14371 = Get(s->LocalAt(8), Value("hires_today")); return Binary("Add", v14371, s->LocalAt(16)); }()); return Binary("Add", v14370, s->LocalAt(3)); }()), false); return Call(c, fn14368, std::move(args14369)); }()))) { comp14365->SetAt(0, item14367); result14366.node()->sequence.push_back(([&]() -> Value { auto fn14372 = comp14365->Global("_v219_fib"); Arguments args14373; args14373.Add(comp14365->LocalAt(0), false); return Call(c, fn14372, std::move(args14373)); }())); } return result14366; }()), false); return Call(c, fn14363, std::move(args14364)); }());
s->SetAt(1, v14362);
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto fn14374 = PrepareDictionaryGet(s->LocalAt(20)); Arguments args14375; args14375.Add(Value("committed"), false); return CallDictionaryGet(c, fn14374, std::move(args14375)); }())))) {
auto v14376 = s->LocalAt(1);
s->SetAt(1, Inplace("Add", v14376, Value(int64_t{4500})));
}
if (static_cast<bool>(s->LocalAt(9))) {
auto v14377 = s->LocalAt(1);
s->SetAt(1, Inplace("Add", v14377, ([&]() -> Value { auto v14378 = s->LocalAt(10); return Binary("Mult", v14378, ([&]() -> Value { auto v14379 = Get(Get(Get(s->LocalAt(13), Value("market")), Value("prices")), Value("FERTILIZER")); return Binary("Add", v14379, Value(int64_t{5})); }())); }())));
}
for (const auto& item14380 : Iterate(Get(s->LocalAt(0), Value("market")))) {
s->SetAt(15, item14380);
if (static_cast<bool>(Unary("Not", s->LocalAt(15)))) {
continue;
}
if (static_cast<bool>(([&]() -> Value { auto v14381 = Get(s->LocalAt(15), Value(int64_t{0})); Value v14382; v14382 = Value("BUY_PRODUCT"); if (!static_cast<bool>(Binary("Eq", v14381, v14382))) return Value(false); v14381 = v14382; return Value(true); }()))) {
auto v14383 = s->LocalAt(1);
s->SetAt(1, Inplace("Add", v14383, ([&]() -> Value { auto v14384 = ([&]() -> Value { auto fn14385 = s->Global("int"); Arguments args14386; args14386.Add(Get(s->LocalAt(15), Value(int64_t{2})), false); return Call(c, fn14385, std::move(args14386)); }()); return Binary("Mult", v14384, ([&]() -> Value { auto v14387 = ([&]() -> Value { auto fn14388 = s->Global("int"); Arguments args14389; args14389.Add(Get(Get(Get(s->LocalAt(13), Value("market")), Value("prices")), Get(s->LocalAt(15), Value(int64_t{1}))), false); return Call(c, fn14388, std::move(args14389)); }()); return Binary("Add", v14387, Value(int64_t{10})); }())); }())));
}
else {
if (static_cast<bool>(([&]() -> Value { auto v14390 = Get(s->LocalAt(15), Value(int64_t{0})); Value v14391; v14391 = Value("BUY_ANIMAL"); if (!static_cast<bool>(Binary("Eq", v14390, v14391))) return Value(false); v14390 = v14391; return Value(true); }()))) {
auto v14392 = s->LocalAt(1);
s->SetAt(1, Inplace("Add", v14392, ([&]() -> Value { auto v14393 = ([&]() -> Value { auto fn14394 = s->Global("int"); Arguments args14395; args14395.Add(Get(s->LocalAt(15), Value(int64_t{2})), false); return Call(c, fn14394, std::move(args14395)); }()); return Binary("Mult", v14393, Get(([&]() -> Value { auto dict14396 = Dict(); auto key14397 = Value("COW"); Put(dict14396, key14397, Value(int64_t{400})); auto key14398 = Value("SHEEP"); Put(dict14396, key14398, Value(int64_t{500})); auto key14399 = Value("GOOSE"); Put(dict14396, key14399, Value(int64_t{300})); return dict14396; }()), Get(s->LocalAt(15), Value(int64_t{1})))); }())));
}
else {
if (static_cast<bool>(([&]() -> Value { auto v14400 = Get(s->LocalAt(15), Value(int64_t{0})); Value v14401; v14401 = Value("BUY_SEED"); if (!static_cast<bool>(Binary("Eq", v14400, v14401))) return Value(false); v14400 = v14401; return Value(true); }()))) {
auto v14402 = s->LocalAt(1);
s->SetAt(1, Inplace("Add", v14402, ([&]() -> Value { auto v14403 = ([&]() -> Value { auto fn14404 = s->Global("int"); Arguments args14405; args14405.Add(Get(s->LocalAt(15), Value(int64_t{2})), false); return Call(c, fn14404, std::move(args14405)); }()); return Binary("Mult", v14403, Get(([&]() -> Value { auto dict14406 = Dict(); auto key14407 = Value("WHEAT"); Put(dict14406, key14407, Value(int64_t{10})); auto key14408 = Value("CARROT"); Put(dict14406, key14408, Value(int64_t{20})); auto key14409 = Value("TOMATO"); Put(dict14406, key14409, Value(int64_t{50})); auto key14410 = Value("STRAWBERRY"); Put(dict14406, key14410, Value(int64_t{100})); auto key14411 = Value("MELON"); Put(dict14406, key14411, Value(int64_t{80})); return dict14406; }()), Get(s->LocalAt(15), Value(int64_t{1})))); }())));
}
}
}
}
if (static_cast<bool>(([&]() -> Value { auto v14412 = Get(s->LocalAt(8), Value("money")); Value v14413; v14413 = ([&]() -> Value { auto v14414 = s->LocalAt(1); return Binary("Add", v14414, Value(int64_t{3000})); }()); if (!static_cast<bool>(Binary("Lt", v14412, v14413))) return Value(false); v14412 = v14413; return Value(true); }()))) {
auto v14415 = s->Global("_V219_REPORT");
auto v14416 = Value("budget_declines");
auto v14417 = Get(v14415, v14416);
Put(v14415, v14416, Inplace("Add", v14417, Value(int64_t{1})));
return s->LocalAt(0);
}
auto v14418 = ([&]() -> Value { auto dict14419 = Dict(); auto key14420 = Value("step"); Put(dict14419, key14420, s->LocalAt(21)); auto key14421 = Value("first_actor"); Put(dict14419, key14421, ([&]() -> Value { auto v14422 = s->LocalAt(6); return Binary("Add", v14422, Value(int64_t{1})); }())); auto key14423 = Value("count"); Put(dict14419, key14423, s->LocalAt(3)); auto key14424 = Value("crop_workers"); Put(dict14419, key14424, s->LocalAt(4)); auto key14425 = Value("fertilizer"); Put(dict14419, key14425, s->LocalAt(9)); auto key14426 = Value("labor"); Put(dict14419, key14426, s->LocalAt(11)); return dict14419; }());
Put(s->LocalAt(20), Value("pending"), v14418);
if (static_cast<bool>(([&]() -> Value { auto v14427 = s->LocalAt(11); Value v14428; v14428 = Value{}; if (!static_cast<bool>(Binary("IsNot", v14427, v14428))) return Value(false); v14427 = v14428; return Value(true); }()))) {
auto v14429 = s->Global("_R53_LABOR_REPORT");
auto v14430 = Value("labor_requests");
auto v14431 = Get(v14429, v14430);
Put(v14429, v14430, Inplace("Add", v14431, Value(int64_t{1})));
auto v14432 = s->Global("_R53_LABOR_REPORT");
auto v14433 = Value("labor_hires_avoided");
auto v14434 = Get(v14432, v14433);
Put(v14432, v14433, Inplace("Add", v14434, Value(int64_t{1})));
auto v14435 = s->Global("_R53_LABOR_REPORT");
auto v14436 = ([&]() -> Value { auto v14438 = Value("labor_day"); return Binary("Add", v14438, ([&]() -> Value { auto fn14439 = s->Global("str"); Arguments args14440; args14440.Add(s->LocalAt(5), false); return Call(c, fn14439, std::move(args14440)); }())); }());
auto v14437 = Get(v14435, v14436);
Put(v14435, v14436, Inplace("Add", v14437, Value(int64_t{1})));
}
auto v14441 = s->LocalAt(5);
Put(s->LocalAt(20), Value("requested_day"), v14441);
auto v14442 = s->Global("_V219_REPORT");
auto v14443 = Value("hire_requests");
auto v14444 = Get(v14442, v14443);
Put(v14442, v14443, Inplace("Add", v14444, s->LocalAt(3)));
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto fn14445 = PrepareDictionaryGet(s->LocalAt(20)); Arguments args14446; args14446.Add(Value("committed"), false); return CallDictionaryGet(c, fn14445, std::move(args14446)); }())))) {
auto v14447 = Value(true);
Put(s->LocalAt(20), Value("committed"), v14447);
auto v14448 = s->Global("_V219_REPORT");
auto v14449 = Value("commitments");
auto v14450 = Get(v14448, v14449);
Put(v14448, v14449, Inplace("Add", v14450, Value(int64_t{1})));
}
auto v14451 = ([&]() -> Value { auto fn14452 = Attribute(s->Global("copy"), "deepcopy"); Arguments args14453; args14453.Add(s->LocalAt(0), false); return Call(c, fn14452, std::move(args14453)); }());
s->SetAt(2, v14451);
auto v14454 = s->LocalAt(2);
auto v14455 = Value("market");
auto v14456 = Get(v14454, v14455);
Put(v14454, v14455, Inplace("Add", v14456, s->LocalAt(7)));
return s->LocalAt(2);
return {};
}
}  // namespace kagg::opponents::compiled
