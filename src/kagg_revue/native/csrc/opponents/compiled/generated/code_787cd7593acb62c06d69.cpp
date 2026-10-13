// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_787cd7593acb62c06d69(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"_", "access", "action", "actor", "after", "blocked", "c", "commands", "day", "demand", "farm", "final", "following", "future", "index", "last_sale", "later", "native", "need", "next_orders", "night", "obs", "old", "order", "orders", "original_buys", "original_final", "original_loss", "original_stock", "player", "positions", "prefund", "private", "project", "proposed", "result", "safe", "sales", "shortage", "sold", "step"};
s->PrepareSlots(s_names);
auto v10313 = ([&]() -> Value { auto fn10314 = s->Global("int"); Arguments args10315; args10315.Add(Get(s->LocalAt(21), Value("step")), false); return Call(c, fn10314, std::move(args10315)); }());
s->SetAt(40, v10313);
auto v10316 = ([&]() -> Value { auto fn10317 = s->Global("int"); Arguments args10318; args10318.Add(Get(s->LocalAt(21), Value("player")), false); return Call(c, fn10317, std::move(args10318)); }());
s->SetAt(29, v10316);
auto v10319 = ([&]() -> Value { auto v10320 = s->LocalAt(40); return Binary("FloorDiv", v10320, Value(int64_t{24})); }());
s->SetAt(8, v10319);
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto v10321 = Value(int64_t{144}); Value v10322; v10322 = s->LocalAt(40); if (!static_cast<bool>(Binary("LtE", v10321, v10322))) return Value(false); v10321 = v10322; v10322 = Value(int64_t{695}); if (!static_cast<bool>(Binary("Lt", v10321, v10322))) return Value(false); v10321 = v10322; return Value(true); }())))) {
return s->LocalAt(2);
}
auto v10323 = Get(Attribute(Attribute(s->Global("_IMPL"), "chassis"), "players"), s->LocalAt(29));
s->SetAt(17, v10323);
auto v10324 = Get(Get(Attribute(Attribute(s->Global("_IMPL"), "chassis"), "routes"), (static_cast<bool>(([&]() -> Value { auto v10325 = ([&]() -> Value { auto v10327 = s->LocalAt(40); return Binary("Add", v10327, Value(int64_t{1})); }()); Value v10326; v10326 = Value(int64_t{648}); if (!static_cast<bool>(Binary("GtE", v10325, v10326))) return Value(false); v10325 = v10326; return Value(true); }())) ? Value(int64_t{2}) : Get(s->LocalAt(17), Value("route")))), ([&]() -> Value { auto v10328 = s->LocalAt(40); return Binary("Add", v10328, Value(int64_t{1})); }()));
s->SetAt(13, v10324);
auto v10329 = ([&]() -> Value { Arguments args10330; args10330.Add(([&]() -> Value { auto v10331 = ([&]() -> Value { auto fn10332 = PrepareDictionaryGet(s->LocalAt(13)); Arguments args10333; args10333.Add(Value("farmer"), false); return CallDictionaryGet(c, fn10332, std::move(args10333)); }()); if (static_cast<bool>(v10331)) return v10331; v10331 = List({Value("PASS")}); return v10331; }()), false); args10330.Add(([&]() -> Value { auto v10334 = ([&]() -> Value { auto fn10335 = PrepareDictionaryGet(s->LocalAt(13)); Arguments args10336; args10336.Add(Value("hands"), false); return CallDictionaryGet(c, fn10335, std::move(args10336)); }()); if (static_cast<bool>(v10334)) return v10334; v10334 = List({}); return v10334; }()), true); return List(std::move(args10330.positional)); }());
s->SetAt(7, v10329);
auto v10337 = Get(Get(Attribute(Attribute(s->Global("_IMPL"), "chassis"), "routes"), (static_cast<bool>(([&]() -> Value { auto v10338 = ([&]() -> Value { auto v10340 = s->LocalAt(40); return Binary("Add", v10340, Value(int64_t{2})); }()); Value v10339; v10339 = Value(int64_t{648}); if (!static_cast<bool>(Binary("GtE", v10338, v10339))) return Value(false); v10338 = v10339; return Value(true); }())) ? Value(int64_t{2}) : Get(s->LocalAt(17), Value("route")))), ([&]() -> Value { auto v10341 = s->LocalAt(40); return Binary("Add", v10341, Value(int64_t{2})); }()));
s->SetAt(12, v10337);
auto v10342 = ([&]() -> Value { auto v10343 = ([&]() -> Value { auto fn10344 = PrepareDictionaryGet(s->LocalAt(13)); Arguments args10345; args10345.Add(Value("market"), false); return CallDictionaryGet(c, fn10344, std::move(args10345)); }()); if (static_cast<bool>(v10343)) return v10343; v10343 = List({}); return v10343; }());
s->SetAt(19, v10342);
auto v10346 = Value(int64_t{0});
s->SetAt(31, v10346);
if (static_cast<bool>(([&]() -> Value { auto v10347 = ([&]() -> Value { auto v10348 = ([&]() -> Value { auto fn10350 = s->Global("len"); Arguments args10351; args10351.Add(s->LocalAt(19), false); return Call(c, fn10350, std::move(args10351)); }()); Value v10349; v10349 = Value(int64_t{10}); if (!static_cast<bool>(Binary("Eq", v10348, v10349))) return Value(false); v10348 = v10349; return Value(true); }()); if (!static_cast<bool>(v10347)) return v10347; v10347 = Unary("Not", ([&]() -> Value { auto comp10352 = std::make_shared<Scope>(); comp10352->globals = s->globals; comp10352->parent = s; static constexpr const char* comp10352_names[] = {"o"}; comp10352->PrepareSlots(comp10352_names); auto result10353 = List(); for (const auto& item10354 : Iterate(s->LocalAt(19))) { comp10352->SetAt(0, item10354); if (static_cast<bool>(([&]() -> Value { auto v10355 = Slice(comp10352->LocalAt(0), Value{}, Value(int64_t{2}), Value{}); Value v10356; v10356 = Tuple({List({Value("BUY_PRODUCT"), Value("WHEAT")}), List({Value("SELL"), Value("WHEAT")})}); if (!static_cast<bool>(Binary("In", v10355, v10356))) return Value(false); v10355 = v10356; return Value(true); }()))) return Value(true); } return Value(false); }())); return v10347; }()))) {
auto v10357 = ([&]() -> Value { Arguments args10358; args10358.Add(([&]() -> Value { auto v10359 = ([&]() -> Value { auto fn10360 = PrepareDictionaryGet(s->LocalAt(12)); Arguments args10361; args10361.Add(Value("farmer"), false); return CallDictionaryGet(c, fn10360, std::move(args10361)); }()); if (static_cast<bool>(v10359)) return v10359; v10359 = List({Value("PASS")}); return v10359; }()), false); args10358.Add(([&]() -> Value { auto v10362 = ([&]() -> Value { auto fn10363 = PrepareDictionaryGet(s->LocalAt(12)); Arguments args10364; args10364.Add(Value("hands"), false); return CallDictionaryGet(c, fn10363, std::move(args10364)); }()); if (static_cast<bool>(v10362)) return v10362; v10362 = List({}); return v10362; }()), true); return List(std::move(args10358.positional)); }());
s->SetAt(16, v10357);
auto v10365 = Define(&Code_d8543b169df87a974842, s, Signature{{"cs"}, {}, {}, {}, "", "", ([]() -> std::span<const char* const> { static constexpr const char* names[] = {"cs"}; return names; }())}, true, "<lambda>");
s->SetAt(9, v10365);
if (static_cast<bool>(([&]() -> Value { auto fn10381 = s->LocalAt(9); Arguments args10382; args10382.Add(s->LocalAt(16), false); return Call(c, fn10381, std::move(args10382)); }()))) {
auto v10383 = ([&]() -> Value { auto v10384 = ([&]() -> Value { auto fn10385 = s->LocalAt(9); Arguments args10386; args10386.Add(s->LocalAt(7), false); return Call(c, fn10385, std::move(args10386)); }()); return Binary("Add", v10384, ([&]() -> Value { auto fn10387 = s->LocalAt(9); Arguments args10388; args10388.Add(s->LocalAt(16), false); return Call(c, fn10387, std::move(args10388)); }())); }());
s->SetAt(31, v10383);
}
}
if (static_cast<bool>(([&]() -> Value { auto v10389 = Unary("Not", s->LocalAt(31)); if (!static_cast<bool>(v10389)) return v10389; v10389 = Unary("Not", ([&]() -> Value { auto comp10390 = std::make_shared<Scope>(); comp10390->globals = s->globals; comp10390->parent = s; static constexpr const char* comp10390_names[] = {"c"}; comp10390->PrepareSlots(comp10390_names); auto result10391 = List(); for (const auto& item10392 : Iterate(s->LocalAt(7))) { comp10390->SetAt(0, item10392); if (static_cast<bool>(([&]() -> Value { auto v10393 = Slice(comp10390->LocalAt(0), Value{}, Value(int64_t{2}), Value{}); Value v10394; v10394 = List({Value("PICKUP"), Value("WHEAT")}); if (!static_cast<bool>(Binary("Eq", v10393, v10394))) return Value(false); v10393 = v10394; return Value(true); }()))) return Value(true); } return Value(false); }())); return v10389; }()))) {
return s->LocalAt(2);
}
auto v10395 = ([&]() -> Value { auto v10396 = ([&]() -> Value { auto fn10397 = PrepareDictionaryGet(s->LocalAt(2)); Arguments args10398; args10398.Add(Value("market"), false); return CallDictionaryGet(c, fn10397, std::move(args10398)); }()); if (static_cast<bool>(v10396)) return v10396; v10396 = List({}); return v10396; }());
s->SetAt(24, v10395);
if (static_cast<bool>(([&]() -> Value { auto v10399 = ([&]() -> Value { auto v10400 = ([&]() -> Value { auto fn10402 = s->Global("len"); Arguments args10403; args10403.Add(s->LocalAt(24), false); return Call(c, fn10402, std::move(args10403)); }()); Value v10401; v10401 = Value(int64_t{10}); if (!static_cast<bool>(Binary("Gt", v10400, v10401))) return Value(false); v10400 = v10401; return Value(true); }()); if (static_cast<bool>(v10399)) return v10399; v10399 = Unary("Not", ([&]() -> Value { auto fn10404 = s->Global("_r97_budget"); Arguments args10405; args10405.positional.reserve(2); args10405.Add(s->LocalAt(21), false); args10405.Add(s->LocalAt(24), false); return Call(c, fn10404, std::move(args10405)); }())); return v10399; }()))) {
auto v10406 = s->Global("_R97_REPORT");
auto v10407 = Value("supply_budget_declines");
auto v10408 = Get(v10406, v10407);
Put(v10406, v10407, Inplace("Add", v10408, Value(int64_t{1})));
return s->LocalAt(2);
}
auto v10409 = ([&]() -> Value { auto fn10410 = Get(s->Global("_PLANNER_NS"), Value("_clone_state")); Arguments args10411; args10411.positional.reserve(2); args10411.Add(Get(Get(s->LocalAt(21), Value("farms")), s->LocalAt(29)), false); args10411.Add(Get(s->LocalAt(21), Value("private")), false); return Call(c, fn10410, std::move(args10411)); }());
auto unpack10412 = Iterate(v10409);
ValidateUnpack(unpack10412, 2, false);
s->SetAt(10, unpack10412.at(0));
s->SetAt(32, unpack10412.at(1));
for (const auto& item10413 : Iterate(([&]() -> Value { auto fn10414 = s->Global("enumerate"); Arguments args10415; args10415.Add(Slice(([&]() -> Value { Arguments args10418; args10418.Add(([&]() -> Value { auto v10419 = ([&]() -> Value { auto fn10420 = PrepareDictionaryGet(s->LocalAt(2)); Arguments args10421; args10421.Add(Value("farmer"), false); return CallDictionaryGet(c, fn10420, std::move(args10421)); }()); if (static_cast<bool>(v10419)) return v10419; v10419 = List({Value("PASS")}); return v10419; }()), false); args10418.Add(([&]() -> Value { auto v10422 = ([&]() -> Value { auto fn10423 = PrepareDictionaryGet(s->LocalAt(2)); Arguments args10424; args10424.Add(Value("hands"), false); return CallDictionaryGet(c, fn10423, std::move(args10424)); }()); if (static_cast<bool>(v10422)) return v10422; v10422 = List({}); return v10422; }()), true); return List(std::move(args10418.positional)); }()), Value{}, ([&]() -> Value { auto fn10416 = s->Global("len"); Arguments args10417; args10417.Add(Get(s->LocalAt(32), Value("inventories")), false); return Call(c, fn10416, std::move(args10417)); }()), Value{}), false); return Call(c, fn10414, std::move(args10415)); }()))) {
auto unpack10425 = Iterate(item10413);
ValidateUnpack(unpack10425, 2, false);
s->SetAt(3, unpack10425.at(0));
s->SetAt(6, unpack10425.at(1));
(void)([&]() -> Value { auto fn10426 = Get(s->Global("_PLANNER_NS"), Value("_apply_unit_action")); Arguments args10427; args10427.positional.reserve(8); args10427.Add(s->LocalAt(10), false); args10427.Add(s->LocalAt(32), false); args10427.Add(s->LocalAt(3), false); args10427.Add(s->LocalAt(6), false); args10427.Add(Value(int64_t{10}), false); args10427.Add(s->LocalAt(8), false); args10427.Add(Value(int64_t{24}), false); args10427.Add(Value(int64_t{100}), false); return Call(c, fn10426, std::move(args10427)); }());
}
auto v10428 = ([&]() -> Value { Arguments args10429; args10429.Add(([&]() -> Value { auto fn10430 = s->Global("tuple"); Arguments args10431; args10431.Add(Get(s->LocalAt(10), Value("farmer")), false); return Call(c, fn10430, std::move(args10431)); }()), false); args10429.Add(([&]() -> Value { auto fn10432 = s->Global("map"); Arguments args10433; args10433.positional.reserve(2); args10433.Add(s->Global("tuple"), false); args10433.Add(Get(s->LocalAt(10), Value("hands")), false); return Call(c, fn10432, std::move(args10433)); }()), true); return List(std::move(args10429.positional)); }());
s->SetAt(30, v10428);
auto v10434 = ([&]() -> Value { auto v10435 = ([&]() -> Value { auto v10437 = s->LocalAt(40); return Binary("Mod", v10437, Value(int64_t{24})); }()); Value v10436; v10436 = Value(int64_t{23}); if (!static_cast<bool>(Binary("Eq", v10435, v10436))) return Value(false); v10435 = v10436; return Value(true); }());
s->SetAt(20, v10434);
auto v10438 = Tuple({Tuple({Value(int64_t{4}), Value(int64_t{4})}), Tuple({Value(int64_t{5}), Value(int64_t{4})}), Tuple({Value(int64_t{4}), Value(int64_t{5})}), Tuple({Value(int64_t{5}), Value(int64_t{5})})});
s->SetAt(1, v10438);
if (static_cast<bool>(s->LocalAt(20))) {
auto v10439 = List({Tuple({Value(int64_t{4}), Value(int64_t{4})})});
s->SetAt(30, v10439);
}
else {
for (const auto& item10440 : Iterate(s->LocalAt(24))) {
s->SetAt(23, item10440);
if (static_cast<bool>(([&]() -> Value { auto v10441 = s->LocalAt(23); if (!static_cast<bool>(v10441)) return v10441; v10441 = ([&]() -> Value { auto v10442 = Get(s->LocalAt(23), Value(int64_t{0})); Value v10443; v10443 = Value("HIRE"); if (!static_cast<bool>(Binary("Eq", v10442, v10443))) return Value(false); v10442 = v10443; return Value(true); }()); return v10441; }()))) {
(void)([&]() -> Value { auto fn10444 = Attribute(s->LocalAt(30), "append"); Arguments args10445; args10445.Add(([&]() -> Value { auto fn10446 = s->Global("min"); Arguments args10447; args10447.Add(s->LocalAt(1), false); args10447.Keyword("key", Define(&Code_8cc070ad117dc4ed9794, s, Signature{{"p"}, {}, {}, {}, "", "", ([]() -> std::span<const char* const> { static constexpr const char* names[] = {"p"}; return names; }())}, true, "<lambda>")); return Call(c, fn10446, std::move(args10447)); }()), false); return Call(c, fn10444, std::move(args10445)); }());
}
}
}
auto v10452 = ([&]() -> Value { auto fn10453 = s->Global("sum"); Arguments args10454; args10454.Add(([&]() -> Value { auto comp10455 = std::make_shared<Scope>(); comp10455->globals = s->globals; comp10455->parent = s; static constexpr const char* comp10455_names[] = {"c", "pos"}; comp10455->PrepareSlots(comp10455_names); auto result10456 = List(); for (const auto& item10457 : Iterate(([&]() -> Value { auto fn10458 = s->Global("zip"); Arguments args10459; args10459.positional.reserve(2); args10459.Add(s->LocalAt(30), false); args10459.Add(s->LocalAt(7), false); return Call(c, fn10458, std::move(args10459)); }()))) { auto unpack10460 = Iterate(item10457); ValidateUnpack(unpack10460, 2, false); comp10455->SetAt(1, unpack10460.at(0)); comp10455->SetAt(0, unpack10460.at(1)); if (!static_cast<bool>(([&]() -> Value { auto v10461 = ([&]() -> Value { auto v10462 = comp10455->LocalAt(1); Value v10463; v10463 = comp10455->Captured("access"); if (!static_cast<bool>(Binary("In", v10462, v10463))) return Value(false); v10462 = v10463; return Value(true); }()); if (!static_cast<bool>(v10461)) return v10461; v10461 = ([&]() -> Value { auto v10464 = Slice(comp10455->LocalAt(0), Value{}, Value(int64_t{2}), Value{}); Value v10465; v10465 = List({Value("PICKUP"), Value("WHEAT")}); if (!static_cast<bool>(Binary("Eq", v10464, v10465))) return Value(false); v10464 = v10465; return Value(true); }()); return v10461; }()))) continue; result10456.node()->sequence.push_back(([&]() -> Value { auto fn10466 = comp10455->Global("max"); Arguments args10467; args10467.positional.reserve(2); args10467.Add(Value(int64_t{0}), false); args10467.Add((static_cast<bool>(([&]() -> Value { auto v10468 = ([&]() -> Value { auto fn10470 = comp10455->Global("len"); Arguments args10471; args10471.Add(comp10455->LocalAt(0), false); return Call(c, fn10470, std::move(args10471)); }()); Value v10469; v10469 = Value(int64_t{2}); if (!static_cast<bool>(Binary("Gt", v10468, v10469))) return Value(false); v10468 = v10469; return Value(true); }())) ? ([&]() -> Value { auto fn10472 = comp10455->Global("int"); Arguments args10473; args10473.Add(Get(comp10455->LocalAt(0), Value(int64_t{2})), false); return Call(c, fn10472, std::move(args10473)); }()) : Value(int64_t{1})), false); return Call(c, fn10466, std::move(args10467)); }())); } return result10456; }()), false); return Call(c, fn10453, std::move(args10454)); }());
s->SetAt(18, v10452);
auto v10474 = ([&]() -> Value { auto fn10475 = s->Global("max"); Arguments args10476; args10476.positional.reserve(2); args10476.Add(s->LocalAt(18), false); args10476.Add(s->LocalAt(31), false); return Call(c, fn10475, std::move(args10476)); }());
s->SetAt(18, v10474);
if (static_cast<bool>(Unary("Not", s->LocalAt(18)))) {
return s->LocalAt(2);
}
auto v10477 = ([&]() -> Value { auto fn10478 = s->Global("_r97_market_stock"); Arguments args10479; args10479.positional.reserve(2); args10479.Add(Get(s->LocalAt(32), Value("shed")), false); args10479.Add(s->LocalAt(24), false); return Call(c, fn10478, std::move(args10479)); }());
auto unpack10480 = Iterate(v10477);
ValidateUnpack(unpack10480, 3, false);
s->SetAt(28, unpack10480.at(0));
s->SetAt(25, unpack10480.at(1));
s->SetAt(0, unpack10480.at(2));
auto v10481 = ([&]() -> Value { auto fn10482 = s->Global("_r97_delivery"); Arguments args10483; args10483.positional.reserve(3); args10483.Add(s->LocalAt(28), false); args10483.Add(s->LocalAt(32), false); args10483.Add(s->LocalAt(20), false); return Call(c, fn10482, std::move(args10483)); }());
auto unpack10484 = Iterate(v10481);
ValidateUnpack(unpack10484, 2, false);
s->SetAt(26, unpack10484.at(0));
s->SetAt(27, unpack10484.at(1));
if (static_cast<bool>(([&]() -> Value { auto v10485 = ([&]() -> Value { auto fn10487 = PrepareDictionaryGet(s->LocalAt(26)); Arguments args10488; args10488.positional.reserve(2); args10488.Add(Value("WHEAT"), false); args10488.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn10487, std::move(args10488)); }()); Value v10486; v10486 = s->LocalAt(18); if (!static_cast<bool>(Binary("GtE", v10485, v10486))) return Value(false); v10485 = v10486; return Value(true); }()))) {
return s->LocalAt(2);
}
auto v10489 = ([&]() -> Value { auto fn10490 = Attribute(s->Global("copy"), "deepcopy"); Arguments args10491; args10491.Add(s->LocalAt(2), false); return Call(c, fn10490, std::move(args10491)); }());
s->SetAt(35, v10489);
auto v10492 = Get(s->LocalAt(35), Value("market"));
s->SetAt(34, v10492);
auto v10493 = Value(false);
s->SetAt(5, v10493);
s->SetAt(33, Define(&Code_3327c37e5ec98da713bb, s, Signature{{"candidate"}, {}, {}, {}, "", "", ([]() -> std::span<const char* const> { static constexpr const char* names[] = {"buys", "candidate", "final", "loss", "safe", "sales", "stock"}; return names; }())}, true, "project"));
s->definitions.push_back("project");
for (const auto& item10524 : Iterate(([&]() -> Value { auto fn10525 = s->Global("range"); Arguments args10526; args10526.positional.reserve(3); args10526.Add(([&]() -> Value { auto v10527 = ([&]() -> Value { auto fn10528 = s->Global("len"); Arguments args10529; args10529.Add(s->LocalAt(34), false); return Call(c, fn10528, std::move(args10529)); }()); return Binary("Sub", v10527, Value(int64_t{1})); }()), false); args10526.Add(Unary("USub", Value(int64_t{1})), false); args10526.Add(Unary("USub", Value(int64_t{1})), false); return Call(c, fn10525, std::move(args10526)); }()))) {
s->SetAt(14, item10524);
if (static_cast<bool>(([&]() -> Value { auto v10530 = Slice(Get(s->LocalAt(34), s->LocalAt(14)), Value{}, Value(int64_t{2}), Value{}); Value v10531; v10531 = List({Value("SELL"), Value("WHEAT")}); if (!static_cast<bool>(Binary("NotEq", v10530, v10531))) return Value(false); v10530 = v10531; return Value(true); }()))) {
continue;
}
auto v10532 = ([&]() -> Value { auto fn10533 = s->LocalAt(33); Arguments args10534; args10534.Add(s->LocalAt(34), false); return Call(c, fn10533, std::move(args10534)); }());
auto unpack10535 = Iterate(v10532);
ValidateUnpack(unpack10535, 3, false);
s->SetAt(11, unpack10535.at(0));
s->SetAt(37, unpack10535.at(1));
s->SetAt(36, unpack10535.at(2));
auto v10536 = ([&]() -> Value { auto fn10537 = s->Global("max"); Arguments args10538; args10538.positional.reserve(2); args10538.Add(Value(int64_t{0}), false); args10538.Add(([&]() -> Value { auto v10539 = s->LocalAt(18); return Binary("Sub", v10539, ([&]() -> Value { auto fn10540 = PrepareDictionaryGet(s->LocalAt(11)); Arguments args10541; args10541.positional.reserve(2); args10541.Add(Value("WHEAT"), false); args10541.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn10540, std::move(args10541)); }())); }()), false); return Call(c, fn10537, std::move(args10538)); }());
s->SetAt(38, v10536);
if (static_cast<bool>(Unary("Not", s->LocalAt(38)))) {
break;
}
auto v10542 = ([&]() -> Value { auto fn10543 = PrepareDictionaryGet(s->LocalAt(37)); Arguments args10544; args10544.positional.reserve(2); args10544.Add(s->LocalAt(14), false); args10544.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn10543, std::move(args10544)); }());
s->SetAt(39, v10542);
if (static_cast<bool>(Unary("Not", s->LocalAt(39)))) {
continue;
}
auto v10545 = Get(Get(s->LocalAt(34), s->LocalAt(14)), Value(int64_t{2}));
s->SetAt(22, v10545);
auto v10546 = ([&]() -> Value { auto fn10547 = s->Global("max"); Arguments args10548; args10548.positional.reserve(2); args10548.Add(Value(int64_t{0}), false); args10548.Add(([&]() -> Value { auto v10549 = s->LocalAt(39); return Binary("Sub", v10549, s->LocalAt(38)); }()), false); return Call(c, fn10547, std::move(args10548)); }());
Put(Get(s->LocalAt(34), s->LocalAt(14)), Value(int64_t{2}), v10546);
auto v10550 = ([&]() -> Value { auto fn10551 = s->LocalAt(33); Arguments args10552; args10552.Add(s->LocalAt(34), false); return Call(c, fn10551, std::move(args10552)); }());
auto unpack10553 = Iterate(v10550);
ValidateUnpack(unpack10553, 3, false);
s->SetAt(4, unpack10553.at(0));
s->SetAt(0, unpack10553.at(1));
s->SetAt(36, unpack10553.at(2));
if (static_cast<bool>(([&]() -> Value { auto v10554 = Unary("Not", s->LocalAt(36)); if (static_cast<bool>(v10554)) return v10554; v10554 = ([&]() -> Value { auto v10555 = ([&]() -> Value { auto fn10557 = PrepareDictionaryGet(s->LocalAt(4)); Arguments args10558; args10558.positional.reserve(2); args10558.Add(Value("WHEAT"), false); args10558.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn10557, std::move(args10558)); }()); Value v10556; v10556 = ([&]() -> Value { auto fn10559 = PrepareDictionaryGet(s->LocalAt(11)); Arguments args10560; args10560.positional.reserve(2); args10560.Add(Value("WHEAT"), false); args10560.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn10559, std::move(args10560)); }()); if (!static_cast<bool>(Binary("LtE", v10555, v10556))) return Value(false); v10555 = v10556; return Value(true); }()); return v10554; }()))) {
auto v10561 = s->LocalAt(22);
Put(Get(s->LocalAt(34), s->LocalAt(14)), Value(int64_t{2}), v10561);
}
}
auto v10562 = ([&]() -> Value { auto fn10563 = s->LocalAt(33); Arguments args10564; args10564.Add(s->LocalAt(34), false); return Call(c, fn10563, std::move(args10564)); }());
auto unpack10565 = Iterate(v10562);
ValidateUnpack(unpack10565, 3, false);
s->SetAt(11, unpack10565.at(0));
s->SetAt(0, unpack10565.at(1));
s->SetAt(36, unpack10565.at(2));
auto v10566 = ([&]() -> Value { auto fn10567 = s->Global("max"); Arguments args10568; args10568.positional.reserve(2); args10568.Add(Value(int64_t{0}), false); args10568.Add(([&]() -> Value { auto v10569 = s->LocalAt(18); return Binary("Sub", v10569, ([&]() -> Value { auto fn10570 = PrepareDictionaryGet(s->LocalAt(11)); Arguments args10571; args10571.positional.reserve(2); args10571.Add(Value("WHEAT"), false); args10571.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn10570, std::move(args10571)); }())); }()), false); return Call(c, fn10567, std::move(args10568)); }());
s->SetAt(38, v10566);
if (static_cast<bool>(s->LocalAt(38))) {
auto v10572 = ([&]() -> Value { auto fn10573 = s->Global("max"); Arguments args10574; args10574.Add(([&]() -> Value { auto comp10575 = std::make_shared<Scope>(); comp10575->globals = s->globals; comp10575->parent = s; static constexpr const char* comp10575_names[] = {"i", "o"}; comp10575->PrepareSlots(comp10575_names); auto result10576 = List(); for (const auto& item10577 : Iterate(([&]() -> Value { auto fn10578 = s->Global("enumerate"); Arguments args10579; args10579.Add(s->LocalAt(34), false); return Call(c, fn10578, std::move(args10579)); }()))) { auto unpack10580 = Iterate(item10577); ValidateUnpack(unpack10580, 2, false); comp10575->SetAt(0, unpack10580.at(0)); comp10575->SetAt(1, unpack10580.at(1)); if (!static_cast<bool>(([&]() -> Value { auto v10581 = Slice(comp10575->LocalAt(1), Value{}, Value(int64_t{2}), Value{}); Value v10582; v10582 = List({Value("SELL"), Value("WHEAT")}); if (!static_cast<bool>(Binary("Eq", v10581, v10582))) return Value(false); v10581 = v10582; return Value(true); }()))) continue; result10576.node()->sequence.push_back(comp10575->LocalAt(0)); } return result10576; }()), false); args10574.Keyword("default", Unary("USub", Value(int64_t{1}))); return Call(c, fn10573, std::move(args10574)); }());
s->SetAt(15, v10572);
auto v10583 = ([&]() -> Value { auto comp10584 = std::make_shared<Scope>(); comp10584->globals = s->globals; comp10584->parent = s; static constexpr const char* comp10584_names[] = {"i"}; comp10584->PrepareSlots(comp10584_names); auto result10585 = List(); auto fallback = Value{}; for (const auto& item10586 : Iterate(([&]() -> Value { auto fn10587 = s->Global("range"); Arguments args10588; args10588.positional.reserve(3); args10588.Add(([&]() -> Value { auto v10589 = ([&]() -> Value { auto fn10590 = s->Global("len"); Arguments args10591; args10591.Add(s->LocalAt(34), false); return Call(c, fn10590, std::move(args10591)); }()); return Binary("Sub", v10589, Value(int64_t{1})); }()), false); args10588.Add(s->LocalAt(15), false); args10588.Add(Unary("USub", Value(int64_t{1})), false); return Call(c, fn10587, std::move(args10588)); }()))) { comp10584->SetAt(0, item10586); if (!static_cast<bool>(([&]() -> Value { auto v10592 = Slice(Get(comp10584->Captured("proposed"), comp10584->LocalAt(0)), Value{}, Value(int64_t{2}), Value{}); Value v10593; v10593 = List({Value("BUY_PRODUCT"), Value("WHEAT")}); if (!static_cast<bool>(Binary("Eq", v10592, v10593))) return Value(false); v10592 = v10593; return Value(true); }()))) continue; return comp10584->LocalAt(0); } return fallback; }());
s->SetAt(14, v10583);
if (static_cast<bool>(([&]() -> Value { auto v10594 = s->LocalAt(14); Value v10595; v10595 = Value{}; if (!static_cast<bool>(Binary("IsNot", v10594, v10595))) return Value(false); v10594 = v10595; return Value(true); }()))) {
auto v10596 = ([&]() -> Value { auto v10597 = ([&]() -> Value { auto fn10598 = s->Global("max"); Arguments args10599; args10599.positional.reserve(2); args10599.Add(Value(int64_t{0}), false); args10599.Add(([&]() -> Value { auto fn10600 = s->Global("int"); Arguments args10601; args10601.Add(Get(Get(s->LocalAt(34), s->LocalAt(14)), Value(int64_t{2})), false); return Call(c, fn10600, std::move(args10601)); }()), false); return Call(c, fn10598, std::move(args10599)); }()); return Binary("Add", v10597, s->LocalAt(38)); }());
Put(Get(s->LocalAt(34), s->LocalAt(14)), Value(int64_t{2}), v10596);
}
else {
if (static_cast<bool>(([&]() -> Value { auto v10602 = ([&]() -> Value { auto fn10604 = s->Global("len"); Arguments args10605; args10605.Add(s->LocalAt(34), false); return Call(c, fn10604, std::move(args10605)); }()); Value v10603; v10603 = Value(int64_t{10}); if (!static_cast<bool>(Binary("Lt", v10602, v10603))) return Value(false); v10602 = v10603; return Value(true); }()))) {
(void)([&]() -> Value { auto fn10606 = Attribute(s->LocalAt(34), "append"); Arguments args10607; args10607.Add(List({Value("BUY_PRODUCT"), Value("WHEAT"), s->LocalAt(38)}), false); return Call(c, fn10606, std::move(args10607)); }());
}
else {
auto v10608 = s->Global("_R97_REPORT");
auto v10609 = Value("supply_slot_declines");
auto v10610 = Get(v10608, v10609);
Put(v10608, v10609, Inplace("Add", v10610, Value(int64_t{1})));
return s->LocalAt(2);
}
}
}
auto v10611 = ([&]() -> Value { auto fn10612 = s->LocalAt(33); Arguments args10613; args10613.Add(s->LocalAt(34), false); return Call(c, fn10612, std::move(args10613)); }());
auto unpack10614 = Iterate(v10611);
ValidateUnpack(unpack10614, 3, false);
s->SetAt(11, unpack10614.at(0));
s->SetAt(0, unpack10614.at(1));
s->SetAt(36, unpack10614.at(2));
if (static_cast<bool>(([&]() -> Value { auto v10615 = Unary("Not", s->LocalAt(36)); if (static_cast<bool>(v10615)) return v10615; v10615 = ([&]() -> Value { auto v10616 = ([&]() -> Value { auto fn10618 = PrepareDictionaryGet(s->LocalAt(11)); Arguments args10619; args10619.positional.reserve(2); args10619.Add(Value("WHEAT"), false); args10619.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn10618, std::move(args10619)); }()); Value v10617; v10617 = s->LocalAt(18); if (!static_cast<bool>(Binary("Lt", v10616, v10617))) return Value(false); v10616 = v10617; return Value(true); }()); return v10615; }()))) {
auto v10620 = s->Global("_R97_REPORT");
auto v10621 = Value("supply_capacity_declines");
auto v10622 = Get(v10620, v10621);
Put(v10620, v10621, Inplace("Add", v10622, Value(int64_t{1})));
return s->LocalAt(2);
}
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto fn10623 = s->Global("_r97_budget"); Arguments args10624; args10624.positional.reserve(2); args10624.Add(s->LocalAt(21), false); args10624.Add(s->LocalAt(34), false); return Call(c, fn10623, std::move(args10624)); }())))) {
auto v10625 = s->Global("_R97_REPORT");
auto v10626 = Value("supply_budget_declines");
auto v10627 = Get(v10625, v10626);
Put(v10625, v10626, Inplace("Add", v10627, Value(int64_t{1})));
return s->LocalAt(2);
}
if (static_cast<bool>(s->LocalAt(31))) {
auto v10628 = s->Global("_R97_REPORT");
auto v10629 = Value("supply_prefund_changes");
auto v10630 = Get(v10628, v10629);
Put(v10628, v10629, Inplace("Add", v10630, Value(int64_t{1})));
auto v10631 = s->Global("_R97_REPORT");
auto v10632 = Value("supply_prefund_units");
auto v10633 = Get(v10631, v10632);
Put(v10631, v10632, Inplace("Add", v10633, ([&]() -> Value { auto fn10634 = s->Global("max"); Arguments args10635; args10635.positional.reserve(2); args10635.Add(Value(int64_t{0}), false); args10635.Add(([&]() -> Value { auto v10636 = ([&]() -> Value { auto fn10637 = PrepareDictionaryGet(s->LocalAt(11)); Arguments args10638; args10638.positional.reserve(2); args10638.Add(Value("WHEAT"), false); args10638.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn10637, std::move(args10638)); }()); return Binary("Sub", v10636, ([&]() -> Value { auto fn10639 = PrepareDictionaryGet(s->LocalAt(26)); Arguments args10640; args10640.positional.reserve(2); args10640.Add(Value("WHEAT"), false); args10640.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn10639, std::move(args10640)); }())); }()), false); return Call(c, fn10634, std::move(args10635)); }())));
}
if (static_cast<bool>(([&]() -> Value { auto v10641 = s->LocalAt(40); Value v10642; v10642 = Value(int64_t{288}); if (!static_cast<bool>(Binary("Lt", v10641, v10642))) return Value(false); v10641 = v10642; return Value(true); }()))) {
auto v10643 = s->Global("_R97_REPORT");
auto v10644 = Value("supply_early_changes");
auto v10645 = Get(v10643, v10644);
Put(v10643, v10644, Inplace("Add", v10645, Value(int64_t{1})));
auto v10646 = s->Global("_R97_REPORT");
auto v10647 = Value("supply_early_units");
auto v10648 = Get(v10646, v10647);
Put(v10646, v10647, Inplace("Add", v10648, ([&]() -> Value { auto fn10649 = s->Global("max"); Arguments args10650; args10650.positional.reserve(2); args10650.Add(Value(int64_t{0}), false); args10650.Add(([&]() -> Value { auto v10651 = ([&]() -> Value { auto fn10652 = PrepareDictionaryGet(s->LocalAt(11)); Arguments args10653; args10653.positional.reserve(2); args10653.Add(Value("WHEAT"), false); args10653.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn10652, std::move(args10653)); }()); return Binary("Sub", v10651, ([&]() -> Value { auto fn10654 = PrepareDictionaryGet(s->LocalAt(26)); Arguments args10655; args10655.positional.reserve(2); args10655.Add(Value("WHEAT"), false); args10655.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn10654, std::move(args10655)); }())); }()), false); return Call(c, fn10649, std::move(args10650)); }())));
}
auto v10656 = s->Global("_R97_REPORT");
auto v10657 = Value("supply_guard_changes");
auto v10658 = Get(v10656, v10657);
Put(v10656, v10657, Inplace("Add", v10658, Value(int64_t{1})));
auto v10659 = s->Global("_R97_REPORT");
auto v10660 = Value("supply_grain_protected");
auto v10661 = Get(v10659, v10660);
Put(v10659, v10660, Inplace("Add", v10661, ([&]() -> Value { auto v10662 = ([&]() -> Value { auto fn10663 = PrepareDictionaryGet(s->LocalAt(11)); Arguments args10664; args10664.positional.reserve(2); args10664.Add(Value("WHEAT"), false); args10664.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn10663, std::move(args10664)); }()); return Binary("Sub", v10662, ([&]() -> Value { auto fn10665 = PrepareDictionaryGet(s->LocalAt(26)); Arguments args10666; args10666.positional.reserve(2); args10666.Add(Value("WHEAT"), false); args10666.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn10665, std::move(args10666)); }())); }())));
auto v10667 = s->Global("_R97_REPORT");
auto v10668 = Value("supply_buy_units");
auto v10669 = Get(v10667, v10668);
Put(v10667, v10668, Inplace("Add", v10669, ([&]() -> Value { auto v10670 = ([&]() -> Value { auto fn10671 = s->Global("sum"); Arguments args10672; args10672.Add(([&]() -> Value { auto comp10673 = std::make_shared<Scope>(); comp10673->globals = s->globals; comp10673->parent = s; static constexpr const char* comp10673_names[] = {"o"}; comp10673->PrepareSlots(comp10673_names); auto result10674 = List(); for (const auto& item10675 : Iterate(s->LocalAt(34))) { comp10673->SetAt(0, item10675); if (!static_cast<bool>(([&]() -> Value { auto v10676 = Slice(comp10673->LocalAt(0), Value{}, Value(int64_t{2}), Value{}); Value v10677; v10677 = List({Value("BUY_PRODUCT"), Value("WHEAT")}); if (!static_cast<bool>(Binary("Eq", v10676, v10677))) return Value(false); v10676 = v10677; return Value(true); }()))) continue; result10674.node()->sequence.push_back(([&]() -> Value { auto fn10678 = comp10673->Global("max"); Arguments args10679; args10679.positional.reserve(2); args10679.Add(Value(int64_t{0}), false); args10679.Add(([&]() -> Value { auto fn10680 = comp10673->Global("int"); Arguments args10681; args10681.Add(Get(comp10673->LocalAt(0), Value(int64_t{2})), false); return Call(c, fn10680, std::move(args10681)); }()), false); return Call(c, fn10678, std::move(args10679)); }())); } return result10674; }()), false); return Call(c, fn10671, std::move(args10672)); }()); return Binary("Sub", v10670, ([&]() -> Value { auto fn10682 = s->Global("sum"); Arguments args10683; args10683.Add(([&]() -> Value { auto comp10684 = std::make_shared<Scope>(); comp10684->globals = s->globals; comp10684->parent = s; static constexpr const char* comp10684_names[] = {"o"}; comp10684->PrepareSlots(comp10684_names); auto result10685 = List(); for (const auto& item10686 : Iterate(s->LocalAt(24))) { comp10684->SetAt(0, item10686); if (!static_cast<bool>(([&]() -> Value { auto v10687 = Slice(comp10684->LocalAt(0), Value{}, Value(int64_t{2}), Value{}); Value v10688; v10688 = List({Value("BUY_PRODUCT"), Value("WHEAT")}); if (!static_cast<bool>(Binary("Eq", v10687, v10688))) return Value(false); v10687 = v10688; return Value(true); }()))) continue; result10685.node()->sequence.push_back(([&]() -> Value { auto fn10689 = comp10684->Global("max"); Arguments args10690; args10690.positional.reserve(2); args10690.Add(Value(int64_t{0}), false); args10690.Add(([&]() -> Value { auto fn10691 = comp10684->Global("int"); Arguments args10692; args10692.Add(Get(comp10684->LocalAt(0), Value(int64_t{2})), false); return Call(c, fn10691, std::move(args10692)); }()), false); return Call(c, fn10689, std::move(args10690)); }())); } return result10685; }()), false); return Call(c, fn10682, std::move(args10683)); }())); }())));
return s->LocalAt(35);
return {};
}
}  // namespace kagg::opponents::compiled
