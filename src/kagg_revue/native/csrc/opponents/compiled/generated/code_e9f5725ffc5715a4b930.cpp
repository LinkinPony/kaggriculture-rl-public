// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_e9f5725ffc5715a4b930(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "c", "commands", "extra", "market", "native", "o", "obs", "orders", "planned", "player", "product", "result", "rewritten", "selling", "species", "st", "step", "stock"};
s->PrepareSlots(s_names);
auto v21280 = ([&]() -> Value { auto fn21281 = s->Global("int"); Arguments args21282; args21282.Add(Get(s->LocalAt(7), Value("step")), false); return Call(c, fn21281, std::move(args21282)); }());
s->SetAt(17, v21280);
auto v21283 = ([&]() -> Value { auto v21284 = ([&]() -> Value { auto fn21285 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args21286; args21286.Add(Value("market"), false); return CallDictionaryGet(c, fn21285, std::move(args21286)); }()); if (static_cast<bool>(v21284)) return v21284; v21284 = List({}); return v21284; }());
s->SetAt(8, v21283);
if (static_cast<bool>(([&]() -> Value { auto v21287 = ([&]() -> Value { auto v21288 = ([&]() -> Value { auto fn21290 = PrepareDictionaryGet(s->LocalAt(16)); Arguments args21291; args21291.Add(Value("species"), false); return CallDictionaryGet(c, fn21290, std::move(args21291)); }()); Value v21289; v21289 = Value{}; if (!static_cast<bool>(Binary("Is", v21288, v21289))) return Value(false); v21288 = v21289; return Value(true); }()); if (!static_cast<bool>(v21287)) return v21287; v21287 = Unary("Not", ([&]() -> Value { auto fn21292 = PrepareDictionaryGet(s->LocalAt(16)); Arguments args21293; args21293.Add(Value("decided"), false); return CallDictionaryGet(c, fn21292, std::move(args21293)); }())); return v21287; }()))) {
if (static_cast<bool>(([&]() -> Value { auto v21294 = ([&]() -> Value { auto v21295 = s->LocalAt(17); Value v21296; v21296 = Value(int64_t{216}); if (!static_cast<bool>(Binary("GtE", v21295, v21296))) return Value(false); v21295 = v21296; return Value(true); }()); if (!static_cast<bool>(v21294)) return v21294; v21294 = ([&]() -> Value { auto comp21297 = std::make_shared<Scope>(); comp21297->globals = s->globals; comp21297->parent = s; static constexpr const char* comp21297_names[] = {"o"}; comp21297->PrepareSlots(comp21297_names); auto result21298 = List(); for (const auto& item21299 : Iterate(s->LocalAt(8))) { comp21297->SetAt(0, item21299); if (static_cast<bool>(([&]() -> Value { auto v21300 = ([&]() -> Value { auto v21301 = ([&]() -> Value { auto fn21303 = comp21297->Global("len"); Arguments args21304; args21304.Add(comp21297->LocalAt(0), false); return Call(c, fn21303, std::move(args21304)); }()); Value v21302; v21302 = Value(int64_t{2}); if (!static_cast<bool>(Binary("GtE", v21301, v21302))) return Value(false); v21301 = v21302; return Value(true); }()); if (!static_cast<bool>(v21300)) return v21300; v21300 = ([&]() -> Value { auto v21305 = Slice(comp21297->LocalAt(0), Value{}, Value(int64_t{2}), Value{}); Value v21306; v21306 = List({Value("BUY_ANIMAL"), Value("GOOSE")}); if (!static_cast<bool>(Binary("Eq", v21305, v21306))) return Value(false); v21305 = v21306; return Value(true); }()); return v21300; }()))) return Value(true); } return Value(false); }()); return v21294; }()))) {
auto v21307 = Value(true);
Put(s->LocalAt(16), Value("decided"), v21307);
auto v21308 = ([&]() -> Value { auto fn21309 = s->Global("_v9_herd_choose"); Arguments args21310; args21310.Add(s->LocalAt(7), false); return Call(c, fn21309, std::move(args21310)); }());
Put(s->LocalAt(16), Value("species"), v21308);
auto v21311 = ([&]() -> Value { auto v21312 = Get(s->LocalAt(16), Value("species")); if (static_cast<bool>(v21312)) return v21312; v21312 = Value(""); return v21312; }());
Put(s->Global("_V9_HERD_REPORT"), Value("herd_species"), v21311);
}
}
auto v21313 = ([&]() -> Value { auto fn21314 = PrepareDictionaryGet(s->LocalAt(16)); Arguments args21315; args21315.Add(Value("species"), false); return CallDictionaryGet(c, fn21314, std::move(args21315)); }());
s->SetAt(15, v21313);
if (static_cast<bool>(Unary("Not", s->LocalAt(15)))) {
return s->LocalAt(0);
}
auto v21316 = Get(s->Global("_V9_HERD_PRODUCT"), s->LocalAt(15));
s->SetAt(11, v21316);
auto v21317 = ([&]() -> Value { auto v21318 = List({([&]() -> Value { auto fn21319 = s->Global("list"); Arguments args21320; args21320.Add(([&]() -> Value { auto v21321 = ([&]() -> Value { auto fn21322 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args21323; args21323.Add(Value("farmer"), false); return CallDictionaryGet(c, fn21322, std::move(args21323)); }()); if (static_cast<bool>(v21321)) return v21321; v21321 = List({Value("PASS")}); return v21321; }()), false); return Call(c, fn21319, std::move(args21320)); }())}); return Binary("Add", v21318, ([&]() -> Value { auto comp21324 = std::make_shared<Scope>(); comp21324->globals = s->globals; comp21324->parent = s; static constexpr const char* comp21324_names[] = {"c"}; comp21324->PrepareSlots(comp21324_names); auto result21325 = List(); for (const auto& item21326 : Iterate(([&]() -> Value { auto v21327 = ([&]() -> Value { auto fn21328 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args21329; args21329.Add(Value("hands"), false); return CallDictionaryGet(c, fn21328, std::move(args21329)); }()); if (static_cast<bool>(v21327)) return v21327; v21327 = List({}); return v21327; }()))) { comp21324->SetAt(0, item21326); result21325.node()->sequence.push_back(([&]() -> Value { auto fn21330 = comp21324->Global("list"); Arguments args21331; args21331.Add(comp21324->LocalAt(0), false); return Call(c, fn21330, std::move(args21331)); }())); } return result21325; }())); }());
s->SetAt(2, v21317);
auto v21332 = ([&]() -> Value { auto comp21333 = std::make_shared<Scope>(); comp21333->globals = s->globals; comp21333->parent = s; static constexpr const char* comp21333_names[] = {"o"}; comp21333->PrepareSlots(comp21333_names); auto result21334 = List(); for (const auto& item21335 : Iterate(s->LocalAt(8))) { comp21333->SetAt(0, item21335); result21334.node()->sequence.push_back(([&]() -> Value { auto fn21336 = comp21333->Global("list"); Arguments args21337; args21337.Add(comp21333->LocalAt(0), false); return Call(c, fn21336, std::move(args21337)); }())); } return result21334; }());
s->SetAt(4, v21332);
for (const auto& item21338 : Iterate(s->LocalAt(2))) {
s->SetAt(1, item21338);
if (static_cast<bool>(([&]() -> Value { auto v21339 = s->LocalAt(1); if (!static_cast<bool>(v21339)) return v21339; v21339 = ([&]() -> Value { auto v21340 = Get(s->LocalAt(1), Value(int64_t{0})); Value v21341; v21341 = Value("BUILD_COOP"); if (!static_cast<bool>(Binary("Eq", v21340, v21341))) return Value(false); v21340 = v21341; return Value(true); }()); return v21339; }()))) {
auto v21342 = Value("BUILD_PASTURE");
Put(s->LocalAt(1), Value(int64_t{0}), v21342);
auto v21343 = s->Global("_V9_HERD_REPORT");
auto v21344 = Value("herd_rewrites");
auto v21345 = Get(v21343, v21344);
Put(v21343, v21344, Inplace("Add", v21345, Value(int64_t{1})));
}
else {
if (static_cast<bool>(([&]() -> Value { auto v21346 = ([&]() -> Value { auto v21347 = ([&]() -> Value { auto fn21349 = s->Global("len"); Arguments args21350; args21350.Add(s->LocalAt(1), false); return Call(c, fn21349, std::move(args21350)); }()); Value v21348; v21348 = Value(int64_t{2}); if (!static_cast<bool>(Binary("GtE", v21347, v21348))) return Value(false); v21347 = v21348; return Value(true); }()); if (!static_cast<bool>(v21346)) return v21346; v21346 = ([&]() -> Value { auto v21351 = Get(s->LocalAt(1), Value(int64_t{0})); Value v21352; v21352 = Tuple({Value("PICKUP"), Value("PLACE")}); if (!static_cast<bool>(Binary("In", v21351, v21352))) return Value(false); v21351 = v21352; return Value(true); }()); if (!static_cast<bool>(v21346)) return v21346; v21346 = ([&]() -> Value { auto v21353 = Get(s->LocalAt(1), Value(int64_t{1})); Value v21354; v21354 = Value("GOOSE"); if (!static_cast<bool>(Binary("Eq", v21353, v21354))) return Value(false); v21353 = v21354; return Value(true); }()); return v21346; }()))) {
auto v21355 = s->LocalAt(15);
Put(s->LocalAt(1), Value(int64_t{1}), v21355);
auto v21356 = s->Global("_V9_HERD_REPORT");
auto v21357 = Value("herd_rewrites");
auto v21358 = Get(v21356, v21357);
Put(v21356, v21357, Inplace("Add", v21358, Value(int64_t{1})));
}
}
}
auto v21359 = List({});
s->SetAt(13, v21359);
for (const auto& item21360 : Iterate(s->LocalAt(4))) {
s->SetAt(6, item21360);
if (static_cast<bool>(([&]() -> Value { auto v21361 = ([&]() -> Value { auto v21362 = ([&]() -> Value { auto fn21364 = s->Global("len"); Arguments args21365; args21365.Add(s->LocalAt(6), false); return Call(c, fn21364, std::move(args21365)); }()); Value v21363; v21363 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v21362, v21363))) return Value(false); v21362 = v21363; return Value(true); }()); if (!static_cast<bool>(v21361)) return v21361; v21361 = ([&]() -> Value { auto v21366 = Slice(s->LocalAt(6), Value{}, Value(int64_t{2}), Value{}); Value v21367; v21367 = List({Value("BUY_ANIMAL"), Value("GOOSE")}); if (!static_cast<bool>(Binary("Eq", v21366, v21367))) return Value(false); v21366 = v21367; return Value(true); }()); return v21361; }()))) {
(void)([&]() -> Value { auto fn21368 = Attribute(s->LocalAt(13), "append"); Arguments args21369; args21369.Add(List({Value("BUY_ANIMAL"), s->LocalAt(15), Get(s->LocalAt(6), Value(int64_t{2}))}), false); return Call(c, fn21368, std::move(args21369)); }());
}
else {
if (static_cast<bool>(([&]() -> Value { auto v21370 = ([&]() -> Value { auto v21371 = ([&]() -> Value { auto fn21373 = s->Global("len"); Arguments args21374; args21374.Add(s->LocalAt(6), false); return Call(c, fn21373, std::move(args21374)); }()); Value v21372; v21372 = Value(int64_t{2}); if (!static_cast<bool>(Binary("GtE", v21371, v21372))) return Value(false); v21371 = v21372; return Value(true); }()); if (!static_cast<bool>(v21370)) return v21370; v21370 = ([&]() -> Value { auto v21375 = Slice(s->LocalAt(6), Value{}, Value(int64_t{2}), Value{}); Value v21376; v21376 = List({Value("SELL"), Value("EGG")}); if (!static_cast<bool>(Binary("Eq", v21375, v21376))) return Value(false); v21375 = v21376; return Value(true); }()); if (!static_cast<bool>(v21370)) return v21370; v21370 = Unary("Not", ([&]() -> Value { auto comp21377 = std::make_shared<Scope>(); comp21377->globals = s->globals; comp21377->parent = s; static constexpr const char* comp21377_names[] = {"r_", "t_"}; comp21377->PrepareSlots(comp21377_names); auto result21378 = List(); for (const auto& item21379 : Iterate(Get(Get(Get(s->LocalAt(7), Value("farms")), ([&]() -> Value { auto fn21380 = s->Global("int"); Arguments args21381; args21381.Add(Get(s->LocalAt(7), Value("player")), false); return Call(c, fn21380, std::move(args21381)); }())), Value("tiles")))) { comp21377->SetAt(0, item21379); for (const auto& item21382 : Iterate(comp21377->LocalAt(0))) { comp21377->SetAt(1, item21382); if (static_cast<bool>(([&]() -> Value { auto v21383 = ([&]() -> Value { auto fn21384 = comp21377->Global("isinstance"); Arguments args21385; args21385.positional.reserve(2); args21385.Add(comp21377->LocalAt(1), false); args21385.Add(comp21377->Global("dict"), false); return Call(c, fn21384, std::move(args21385)); }()); if (!static_cast<bool>(v21383)) return v21383; v21383 = ([&]() -> Value { auto v21386 = ([&]() -> Value { auto fn21388 = PrepareDictionaryGet(comp21377->LocalAt(1)); Arguments args21389; args21389.Add(Value("animal"), false); return CallDictionaryGet(c, fn21388, std::move(args21389)); }()); Value v21387; v21387 = Value("GOOSE"); if (!static_cast<bool>(Binary("Eq", v21386, v21387))) return Value(false); v21386 = v21387; return Value(true); }()); return v21383; }()))) return Value(true); } } return Value(false); }())); return v21370; }()))) {
continue;
}
else {
(void)([&]() -> Value { auto fn21390 = Attribute(s->LocalAt(13), "append"); Arguments args21391; args21391.Add(s->LocalAt(6), false); return Call(c, fn21390, std::move(args21391)); }());
}
}
}
auto v21392 = ([&]() -> Value { auto fn21393 = s->Global("dict"); Arguments args21394; args21394.Add(s->LocalAt(0), false); return Call(c, fn21393, std::move(args21394)); }());
s->SetAt(12, v21392);
auto v21395 = Tuple({Get(s->LocalAt(2), Value(int64_t{0})), Slice(s->LocalAt(2), Value(int64_t{1}), Value{}, Value{}), s->LocalAt(13)});
auto unpack21396 = Iterate(v21395);
ValidateUnpack(unpack21396, 3, false);
Put(s->LocalAt(12), Value("farmer"), unpack21396.at(0));
Put(s->LocalAt(12), Value("hands"), unpack21396.at(1));
Put(s->LocalAt(12), Value("market"), unpack21396.at(2));
auto v21397 = ([&]() -> Value { auto fn21398 = s->Global("int"); Arguments args21399; args21399.Add(Get(s->LocalAt(7), Value("player")), false); return Call(c, fn21398, std::move(args21399)); }());
s->SetAt(10, v21397);
auto v21400 = ([&]() -> Value { auto fn21401 = PrepareDictionaryGet(Attribute(Attribute(s->Global("_IMPL"), "chassis"), "players")); Arguments args21402; args21402.Add(s->LocalAt(10), false); return CallDictionaryGet(c, fn21401, std::move(args21402)); }());
s->SetAt(5, v21400);
if (static_cast<bool>(([&]() -> Value { auto v21403 = s->LocalAt(5); if (!static_cast<bool>(v21403)) return v21403; v21403 = ([&]() -> Value { auto v21404 = ([&]() -> Value { auto fn21406 = PrepareDictionaryGet(s->LocalAt(5)); Arguments args21407; args21407.Add(Value("route"), false); return CallDictionaryGet(c, fn21406, std::move(args21407)); }()); Value v21405; v21405 = Attribute(Attribute(s->Global("_IMPL"), "chassis"), "routes"); if (!static_cast<bool>(Binary("In", v21404, v21405))) return Value(false); v21404 = v21405; return Value(true); }()); if (!static_cast<bool>(v21403)) return v21403; v21403 = ([&]() -> Value { auto v21408 = s->LocalAt(17); Value v21409; v21409 = Value(int64_t{718}); if (!static_cast<bool>(Binary("Lt", v21408, v21409))) return Value(false); v21408 = v21409; return Value(true); }()); return v21403; }()))) {
auto v21410 = ([&]() -> Value { auto fn21411 = PrepareDictionaryGet(([&]() -> Value { auto fn21413 = s->Global("projected_shed"); Arguments args21414; args21414.positional.reserve(2); args21414.Add(s->LocalAt(12), false); args21414.Add(([&]() -> Value { auto fn21415 = s->Global("FarmView"); Arguments args21416; args21416.Add(s->LocalAt(7), false); return Call(c, fn21415, std::move(args21416)); }()), false); return Call(c, fn21413, std::move(args21414)); }())); Arguments args21412; args21412.positional.reserve(2); args21412.Add(s->LocalAt(11), false); args21412.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn21411, std::move(args21412)); }());
s->SetAt(18, v21410);
auto v21417 = ([&]() -> Value { auto fn21418 = s->Global("sum"); Arguments args21419; args21419.Add(([&]() -> Value { auto comp21420 = std::make_shared<Scope>(); comp21420->globals = s->globals; comp21420->parent = s; static constexpr const char* comp21420_names[] = {"o"}; comp21420->PrepareSlots(comp21420_names); auto result21421 = List(); for (const auto& item21422 : Iterate(s->LocalAt(13))) { comp21420->SetAt(0, item21422); if (!static_cast<bool>(([&]() -> Value { auto v21423 = ([&]() -> Value { auto v21424 = ([&]() -> Value { auto fn21426 = comp21420->Global("len"); Arguments args21427; args21427.Add(comp21420->LocalAt(0), false); return Call(c, fn21426, std::move(args21427)); }()); Value v21425; v21425 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v21424, v21425))) return Value(false); v21424 = v21425; return Value(true); }()); if (!static_cast<bool>(v21423)) return v21423; v21423 = ([&]() -> Value { auto v21428 = Slice(comp21420->LocalAt(0), Value{}, Value(int64_t{2}), Value{}); Value v21429; v21429 = List({Value("SELL"), comp21420->Captured("product")}); if (!static_cast<bool>(Binary("Eq", v21428, v21429))) return Value(false); v21428 = v21429; return Value(true); }()); return v21423; }()))) continue; result21421.node()->sequence.push_back(([&]() -> Value { auto fn21430 = comp21420->Global("int"); Arguments args21431; args21431.Add(Get(comp21420->LocalAt(0), Value(int64_t{2})), false); return Call(c, fn21430, std::move(args21431)); }())); } return result21421; }()), false); return Call(c, fn21418, std::move(args21419)); }());
s->SetAt(14, v21417);
auto v21432 = ([&]() -> Value { auto fn21433 = Attribute(Attribute(s->Global("_IMPL"), "chassis"), "future_sells"); Arguments args21434; args21434.positional.reserve(3); args21434.Add(Get(s->LocalAt(5), Value("route")), false); args21434.Add(s->LocalAt(11), false); args21434.Add(([&]() -> Value { auto v21435 = s->LocalAt(17); return Binary("Add", v21435, Value(int64_t{1})); }()), false); return Call(c, fn21433, std::move(args21434)); }());
s->SetAt(9, v21432);
auto v21436 = ([&]() -> Value { auto v21437 = ([&]() -> Value { auto v21438 = s->LocalAt(18); return Binary("Sub", v21438, s->LocalAt(14)); }()); return Binary("Sub", v21437, s->LocalAt(9)); }());
s->SetAt(3, v21436);
if (static_cast<bool>(([&]() -> Value { auto v21439 = ([&]() -> Value { auto v21440 = s->LocalAt(3); Value v21441; v21441 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v21440, v21441))) return Value(false); v21440 = v21441; return Value(true); }()); if (!static_cast<bool>(v21439)) return v21439; v21439 = ([&]() -> Value { auto v21442 = ([&]() -> Value { auto fn21444 = s->Global("len"); Arguments args21445; args21445.Add(s->LocalAt(13), false); return Call(c, fn21444, std::move(args21445)); }()); Value v21443; v21443 = s->Global("MAX_ORDERS"); if (!static_cast<bool>(Binary("Lt", v21442, v21443))) return Value(false); v21442 = v21443; return Value(true); }()); if (!static_cast<bool>(v21439)) return v21439; v21439 = ([&]() -> Value { auto v21446 = ([&]() -> Value { auto fn21448 = s->Global("int"); Arguments args21449; args21449.Add(([&]() -> Value { auto fn21450 = PrepareDictionaryGet(Get(Get(s->LocalAt(7), Value("market")), Value("prices"))); Arguments args21451; args21451.positional.reserve(2); args21451.Add(s->LocalAt(11), false); args21451.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn21450, std::move(args21451)); }()), false); return Call(c, fn21448, std::move(args21449)); }()); Value v21447; v21447 = Value(int64_t{2}); if (!static_cast<bool>(Binary("GtE", v21446, v21447))) return Value(false); v21446 = v21447; return Value(true); }()); return v21439; }()))) {
(void)([&]() -> Value { auto fn21452 = Attribute(s->LocalAt(13), "insert"); Arguments args21453; args21453.positional.reserve(2); args21453.Add(Value(int64_t{0}), false); args21453.Add(List({Value("SELL"), s->LocalAt(11), s->LocalAt(3)}), false); return Call(c, fn21452, std::move(args21453)); }());
auto v21454 = s->Global("_V9_HERD_REPORT");
auto v21455 = Value("herd_extra_sold");
auto v21456 = Get(v21454, v21455);
Put(v21454, v21455, Inplace("Add", v21456, s->LocalAt(3)));
}
}
return s->LocalAt(12);
return {};
}
}  // namespace kagg::opponents::compiled
