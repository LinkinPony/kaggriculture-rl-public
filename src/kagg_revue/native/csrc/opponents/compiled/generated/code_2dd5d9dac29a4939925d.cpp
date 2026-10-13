// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_2dd5d9dac29a4939925d(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"a", "action", "c", "carried", "changed", "command", "commands", "day", "farm", "have", "inventories", "native", "obs", "planned", "player", "positions", "result", "step", "t", "tape", "targeted", "tile", "u", "unit", "x", "y"};
s->PrepareSlots(s_names);
auto v21499 = ([&]() -> Value { auto fn21500 = s->Global("int"); Arguments args21501; args21501.Add(Get(s->LocalAt(12), Value("step")), false); return Call(c, fn21500, std::move(args21501)); }());
s->SetAt(17, v21499);
auto v21502 = ([&]() -> Value { auto v21503 = s->LocalAt(17); return Binary("FloorDiv", v21503, Value(int64_t{24})); }());
s->SetAt(7, v21502);
if (static_cast<bool>(([&]() -> Value { auto v21504 = ([&]() -> Value { auto v21505 = s->LocalAt(7); Value v21506; v21506 = s->Global("V9_FERT_FIRST_DAY"); if (!static_cast<bool>(Binary("Lt", v21505, v21506))) return Value(false); v21505 = v21506; return Value(true); }()); if (static_cast<bool>(v21504)) return v21504; v21504 = ([&]() -> Value { auto v21507 = s->LocalAt(17); Value v21508; v21508 = Value(int64_t{700}); if (!static_cast<bool>(Binary("GtE", v21507, v21508))) return Value(false); v21507 = v21508; return Value(true); }()); return v21504; }()))) {
return s->LocalAt(1);
}
auto v21509 = ([&]() -> Value { auto fn21510 = s->Global("int"); Arguments args21511; args21511.Add(Get(s->LocalAt(12), Value("player")), false); return Call(c, fn21510, std::move(args21511)); }());
s->SetAt(14, v21509);
auto v21512 = Get(Get(s->LocalAt(12), Value("farms")), s->LocalAt(14));
s->SetAt(8, v21512);
auto v21513 = ([&]() -> Value { auto v21514 = List({([&]() -> Value { auto fn21515 = s->Global("tuple"); Arguments args21516; args21516.Add(Get(s->LocalAt(8), Value("farmer")), false); return Call(c, fn21515, std::move(args21516)); }())}); return Binary("Add", v21514, ([&]() -> Value { auto comp21517 = std::make_shared<Scope>(); comp21517->globals = s->globals; comp21517->parent = s; static constexpr const char* comp21517_names[] = {"p"}; comp21517->PrepareSlots(comp21517_names); auto result21518 = List(); for (const auto& item21519 : Iterate(Get(s->LocalAt(8), Value("hands")))) { comp21517->SetAt(0, item21519); result21518.node()->sequence.push_back(([&]() -> Value { auto fn21520 = comp21517->Global("tuple"); Arguments args21521; args21521.Add(comp21517->LocalAt(0), false); return Call(c, fn21520, std::move(args21521)); }())); } return result21518; }())); }());
s->SetAt(15, v21513);
auto v21522 = Get(Get(s->LocalAt(12), Value("private")), Value("inventories"));
s->SetAt(10, v21522);
auto v21523 = ([&]() -> Value { auto v21524 = List({([&]() -> Value { auto fn21525 = s->Global("list"); Arguments args21526; args21526.Add(([&]() -> Value { auto v21527 = ([&]() -> Value { auto fn21528 = PrepareDictionaryGet(s->LocalAt(1)); Arguments args21529; args21529.Add(Value("farmer"), false); return CallDictionaryGet(c, fn21528, std::move(args21529)); }()); if (static_cast<bool>(v21527)) return v21527; v21527 = List({Value("PASS")}); return v21527; }()), false); return Call(c, fn21525, std::move(args21526)); }())}); return Binary("Add", v21524, ([&]() -> Value { auto comp21530 = std::make_shared<Scope>(); comp21530->globals = s->globals; comp21530->parent = s; static constexpr const char* comp21530_names[] = {"c"}; comp21530->PrepareSlots(comp21530_names); auto result21531 = List(); for (const auto& item21532 : Iterate(([&]() -> Value { auto v21533 = ([&]() -> Value { auto fn21534 = PrepareDictionaryGet(s->LocalAt(1)); Arguments args21535; args21535.Add(Value("hands"), false); return CallDictionaryGet(c, fn21534, std::move(args21535)); }()); if (static_cast<bool>(v21533)) return v21533; v21533 = List({}); return v21533; }()))) { comp21530->SetAt(0, item21532); result21531.node()->sequence.push_back(([&]() -> Value { auto fn21536 = comp21530->Global("list"); Arguments args21537; args21537.Add(comp21530->LocalAt(0), false); return Call(c, fn21536, std::move(args21537)); }())); } return result21531; }())); }());
s->SetAt(6, v21523);
auto v21538 = Value(false);
s->SetAt(4, v21538);
auto v21539 = ([&]() -> Value { auto fn21540 = PrepareDictionaryGet(Attribute(Attribute(s->Global("_IMPL"), "chassis"), "players")); Arguments args21541; args21541.Add(s->LocalAt(14), false); return CallDictionaryGet(c, fn21540, std::move(args21541)); }());
s->SetAt(11, v21539);
auto v21542 = (static_cast<bool>(s->LocalAt(11)) ? ([&]() -> Value { auto fn21543 = PrepareDictionaryGet(Attribute(Attribute(s->Global("_IMPL"), "chassis"), "routes")); Arguments args21544; args21544.Add(([&]() -> Value { auto fn21545 = PrepareDictionaryGet(s->LocalAt(11)); Arguments args21546; args21546.Add(Value("route"), false); return CallDictionaryGet(c, fn21545, std::move(args21546)); }()), false); return CallDictionaryGet(c, fn21543, std::move(args21544)); }()) : Value{});
s->SetAt(19, v21542);
auto v21547 = ([&]() -> Value { auto dict21548 = Dict(); return dict21548; }());
s->SetAt(13, v21547);
if (static_cast<bool>(([&]() -> Value { auto v21549 = s->LocalAt(19); Value v21550; v21550 = Value{}; if (!static_cast<bool>(Binary("IsNot", v21549, v21550))) return Value(false); v21549 = v21550; return Value(true); }()))) {
for (const auto& item21551 : Iterate(([&]() -> Value { auto fn21552 = s->Global("range"); Arguments args21553; args21553.positional.reserve(2); args21553.Add(s->LocalAt(17), false); args21553.Add(([&]() -> Value { auto fn21554 = s->Global("min"); Arguments args21555; args21555.positional.reserve(2); args21555.Add(([&]() -> Value { auto fn21556 = s->Global("len"); Arguments args21557; args21557.Add(s->LocalAt(19), false); return Call(c, fn21556, std::move(args21557)); }()), false); args21555.Add(([&]() -> Value { auto v21558 = ([&]() -> Value { auto v21559 = s->LocalAt(7); return Binary("Mult", v21559, Value(int64_t{24})); }()); return Binary("Add", v21558, Value(int64_t{24})); }()), false); return Call(c, fn21554, std::move(args21555)); }()), false); return Call(c, fn21552, std::move(args21553)); }()))) {
s->SetAt(18, item21551);
auto v21560 = ([&]() -> Value { auto v21561 = Get(s->LocalAt(19), s->LocalAt(18)); if (static_cast<bool>(v21561)) return v21561; v21561 = ([&]() -> Value { auto dict21562 = Dict(); return dict21562; }()); return v21561; }());
s->SetAt(0, v21560);
for (const auto& item21563 : Iterate(([&]() -> Value { auto fn21564 = s->Global("enumerate"); Arguments args21565; args21565.Add(([&]() -> Value { auto v21566 = List({([&]() -> Value { auto v21567 = ([&]() -> Value { auto fn21568 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args21569; args21569.Add(Value("farmer"), false); return CallDictionaryGet(c, fn21568, std::move(args21569)); }()); if (static_cast<bool>(v21567)) return v21567; v21567 = List({Value("PASS")}); return v21567; }())}); return Binary("Add", v21566, ([&]() -> Value { auto fn21570 = s->Global("list"); Arguments args21571; args21571.Add(([&]() -> Value { auto v21572 = ([&]() -> Value { auto fn21573 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args21574; args21574.Add(Value("hands"), false); return CallDictionaryGet(c, fn21573, std::move(args21574)); }()); if (static_cast<bool>(v21572)) return v21572; v21572 = List({}); return v21572; }()), false); return Call(c, fn21570, std::move(args21571)); }())); }()), false); return Call(c, fn21564, std::move(args21565)); }()))) {
auto unpack21575 = Iterate(item21563);
ValidateUnpack(unpack21575, 2, false);
s->SetAt(22, unpack21575.at(0));
s->SetAt(2, unpack21575.at(1));
if (static_cast<bool>(([&]() -> Value { auto v21576 = s->LocalAt(2); if (!static_cast<bool>(v21576)) return v21576; v21576 = ([&]() -> Value { auto v21577 = Get(s->LocalAt(2), Value(int64_t{0})); Value v21578; v21578 = Value("FERTILIZE"); if (!static_cast<bool>(Binary("Eq", v21577, v21578))) return Value(false); v21577 = v21578; return Value(true); }()); return v21576; }()))) {
auto v21579 = ([&]() -> Value { auto v21580 = ([&]() -> Value { auto fn21581 = PrepareDictionaryGet(s->LocalAt(13)); Arguments args21582; args21582.positional.reserve(2); args21582.Add(s->LocalAt(22), false); args21582.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn21581, std::move(args21582)); }()); return Binary("Add", v21580, Value(int64_t{1})); }());
Put(s->LocalAt(13), s->LocalAt(22), v21579);
}
}
}
}
auto v21583 = ([&]() -> Value { auto dict21584 = Dict(); return dict21584; }());
s->SetAt(3, v21583);
auto v21585 = ([&]() -> Value { auto fn21586 = s->Global("set"); Arguments args21587; return Call(c, fn21586, std::move(args21587)); }());
s->SetAt(20, v21585);
for (const auto& item21588 : Iterate(([&]() -> Value { auto fn21589 = s->Global("enumerate"); Arguments args21590; args21590.Add(Slice(s->LocalAt(6), Value{}, ([&]() -> Value { auto fn21591 = s->Global("len"); Arguments args21592; args21592.Add(s->LocalAt(15), false); return Call(c, fn21591, std::move(args21592)); }()), Value{}), false); return Call(c, fn21589, std::move(args21590)); }()))) {
auto unpack21593 = Iterate(item21588);
ValidateUnpack(unpack21593, 2, false);
s->SetAt(23, unpack21593.at(0));
s->SetAt(5, unpack21593.at(1));
if (static_cast<bool>(([&]() -> Value { auto v21594 = Unary("Not", s->LocalAt(5)); if (static_cast<bool>(v21594)) return v21594; v21594 = ([&]() -> Value { auto v21595 = Get(s->LocalAt(5), Value(int64_t{0})); Value v21596; v21596 = Value("WATER"); if (!static_cast<bool>(Binary("NotEq", v21595, v21596))) return Value(false); v21595 = v21596; return Value(true); }()); return v21594; }()))) {
continue;
}
auto v21597 = Get(s->LocalAt(15), s->LocalAt(23));
auto unpack21598 = Iterate(v21597);
ValidateUnpack(unpack21598, 2, false);
s->SetAt(24, unpack21598.at(0));
s->SetAt(25, unpack21598.at(1));
auto v21599 = Get(Get(Get(s->LocalAt(8), Value("tiles")), s->LocalAt(25)), s->LocalAt(24));
s->SetAt(21, v21599);
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto v21600 = ([&]() -> Value { auto fn21601 = s->Global("isinstance"); Arguments args21602; args21602.positional.reserve(2); args21602.Add(s->LocalAt(21), false); args21602.Add(s->Global("dict"), false); return Call(c, fn21601, std::move(args21602)); }()); if (!static_cast<bool>(v21600)) return v21600; v21600 = ([&]() -> Value { auto v21603 = ([&]() -> Value { auto fn21605 = PrepareDictionaryGet(s->LocalAt(21)); Arguments args21606; args21606.Add(Value("kind"), false); return CallDictionaryGet(c, fn21605, std::move(args21606)); }()); Value v21604; v21604 = Value("PLANT"); if (!static_cast<bool>(Binary("Eq", v21603, v21604))) return Value(false); v21603 = v21604; return Value(true); }()); if (!static_cast<bool>(v21600)) return v21600; v21600 = ([&]() -> Value { auto v21607 = ([&]() -> Value { auto fn21609 = PrepareDictionaryGet(s->LocalAt(21)); Arguments args21610; args21610.Add(Value("crop"), false); return CallDictionaryGet(c, fn21609, std::move(args21610)); }()); Value v21608; v21608 = s->Global("V9_FERT_CROPS"); if (!static_cast<bool>(Binary("In", v21607, v21608))) return Value(false); v21607 = v21608; return Value(true); }()); return v21600; }())))) {
continue;
}
if (static_cast<bool>(([&]() -> Value { auto v21611 = ([&]() -> Value { auto v21612 = ([&]() -> Value { auto v21614 = s->LocalAt(7); return Binary("Sub", v21614, ([&]() -> Value { auto fn21615 = s->Global("int"); Arguments args21616; args21616.Add(Get(s->LocalAt(21), Value("planted_day")), false); return Call(c, fn21615, std::move(args21616)); }())); }()); Value v21613; v21613 = s->Global("V9_FERT_AGES"); if (!static_cast<bool>(Binary("NotIn", v21612, v21613))) return Value(false); v21612 = v21613; return Value(true); }()); if (static_cast<bool>(v21611)) return v21611; v21611 = ([&]() -> Value { auto fn21617 = PrepareDictionaryGet(s->LocalAt(21)); Arguments args21618; args21618.Add(Value("watered_today"), false); return CallDictionaryGet(c, fn21617, std::move(args21618)); }()); return v21611; }()))) {
continue;
}
if (static_cast<bool>(([&]() -> Value { auto v21619 = ([&]() -> Value { auto v21620 = ([&]() -> Value { auto fn21622 = s->Global("int"); Arguments args21623; args21623.Add(([&]() -> Value { auto fn21624 = PrepareDictionaryGet(s->LocalAt(21)); Arguments args21625; args21625.positional.reserve(2); args21625.Add(Value("consecutive_unwatered"), false); args21625.Add(Value(int64_t{1}), false); return CallDictionaryGet(c, fn21624, std::move(args21625)); }()), false); return Call(c, fn21622, std::move(args21623)); }()); Value v21621; v21621 = Value(int64_t{0}); if (!static_cast<bool>(Binary("NotEq", v21620, v21621))) return Value(false); v21620 = v21621; return Value(true); }()); if (static_cast<bool>(v21619)) return v21619; v21619 = ([&]() -> Value { auto v21626 = ([&]() -> Value { auto fn21628 = s->Global("int"); Arguments args21629; args21629.Add(([&]() -> Value { auto fn21630 = PrepareDictionaryGet(s->LocalAt(21)); Arguments args21631; args21631.positional.reserve(2); args21631.Add(Value("fertilized_until_day"), false); args21631.Add(Unary("USub", Value(int64_t{1})), false); return CallDictionaryGet(c, fn21630, std::move(args21631)); }()), false); return Call(c, fn21628, std::move(args21629)); }()); Value v21627; v21627 = s->LocalAt(7); if (!static_cast<bool>(Binary("GtE", v21626, v21627))) return Value(false); v21626 = v21627; return Value(true); }()); return v21619; }()))) {
continue;
}
auto v21632 = ([&]() -> Value { auto fn21633 = Attribute(s->LocalAt(3), "setdefault"); Arguments args21634; args21634.positional.reserve(2); args21634.Add(s->LocalAt(23), false); args21634.Add(([&]() -> Value { auto v21635 = ([&]() -> Value { auto fn21636 = s->Global("int"); Arguments args21637; args21637.Add(([&]() -> Value { auto fn21638 = PrepareDictionaryGet((static_cast<bool>(([&]() -> Value { auto v21640 = s->LocalAt(23); Value v21641; v21641 = ([&]() -> Value { auto fn21642 = s->Global("len"); Arguments args21643; args21643.Add(s->LocalAt(10), false); return Call(c, fn21642, std::move(args21643)); }()); if (!static_cast<bool>(Binary("Lt", v21640, v21641))) return Value(false); v21640 = v21641; return Value(true); }())) ? Get(s->LocalAt(10), s->LocalAt(23)) : ([&]() -> Value { auto dict21644 = Dict(); return dict21644; }()))); Arguments args21639; args21639.positional.reserve(2); args21639.Add(Value("FERTILIZER"), false); args21639.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn21638, std::move(args21639)); }()), false); return Call(c, fn21636, std::move(args21637)); }()); return Binary("Sub", v21635, ([&]() -> Value { auto fn21645 = PrepareDictionaryGet(s->LocalAt(13)); Arguments args21646; args21646.positional.reserve(2); args21646.Add(s->LocalAt(23), false); args21646.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn21645, std::move(args21646)); }())); }()), false); return Call(c, fn21633, std::move(args21634)); }());
s->SetAt(9, v21632);
if (static_cast<bool>(([&]() -> Value { auto v21647 = ([&]() -> Value { auto v21648 = s->LocalAt(9); Value v21649; v21649 = Value(int64_t{0}); if (!static_cast<bool>(Binary("LtE", v21648, v21649))) return Value(false); v21648 = v21649; return Value(true); }()); if (static_cast<bool>(v21647)) return v21647; v21647 = ([&]() -> Value { auto v21650 = Tuple({s->LocalAt(24), s->LocalAt(25)}); Value v21651; v21651 = s->LocalAt(20); if (!static_cast<bool>(Binary("In", v21650, v21651))) return Value(false); v21650 = v21651; return Value(true); }()); return v21647; }()))) {
continue;
}
auto v21652 = List({Value("FERTILIZE")});
Put(s->LocalAt(6), s->LocalAt(23), v21652);
auto v21653 = ([&]() -> Value { auto v21654 = s->LocalAt(9); return Binary("Sub", v21654, Value(int64_t{1})); }());
Put(s->LocalAt(3), s->LocalAt(23), v21653);
(void)([&]() -> Value { auto fn21655 = Attribute(s->LocalAt(20), "add"); Arguments args21656; args21656.Add(Tuple({s->LocalAt(24), s->LocalAt(25)}), false); return Call(c, fn21655, std::move(args21656)); }());
auto v21657 = Value(true);
s->SetAt(4, v21657);
auto v21658 = s->Global("_V9_FERT_REPORT");
auto v21659 = Value("fert_applied");
auto v21660 = Get(v21658, v21659);
Put(v21658, v21659, Inplace("Add", v21660, Value(int64_t{1})));
}
if (static_cast<bool>(Unary("Not", s->LocalAt(4)))) {
return s->LocalAt(1);
}
auto v21661 = ([&]() -> Value { auto fn21662 = s->Global("dict"); Arguments args21663; args21663.Add(s->LocalAt(1), false); return Call(c, fn21662, std::move(args21663)); }());
s->SetAt(16, v21661);
auto v21664 = Tuple({Get(s->LocalAt(6), Value(int64_t{0})), Slice(s->LocalAt(6), Value(int64_t{1}), Value{}, Value{})});
auto unpack21665 = Iterate(v21664);
ValidateUnpack(unpack21665, 2, false);
Put(s->LocalAt(16), Value("farmer"), unpack21665.at(0));
Put(s->LocalAt(16), Value("hands"), unpack21665.at(1));
return s->LocalAt(16);
return {};
}
}  // namespace kagg::opponents::compiled
