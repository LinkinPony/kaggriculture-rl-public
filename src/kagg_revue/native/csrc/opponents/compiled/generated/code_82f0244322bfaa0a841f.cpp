// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_82f0244322bfaa0a841f(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"access", "action", "actor", "available", "before", "c", "commands", "farm", "future", "intended", "item", "n", "obs", "order", "orders", "pos", "positions", "private", "proposed", "short", "step"};
s->PrepareSlots(s_names);
auto v12429 = ([&]() -> Value { auto fn12430 = s->Global("int"); Arguments args12431; args12431.Add(Get(s->LocalAt(12), Value("step")), false); return Call(c, fn12430, std::move(args12431)); }());
s->SetAt(20, v12429);
auto v12432 = ([&]() -> Value { auto v12433 = ([&]() -> Value { auto fn12434 = PrepareDictionaryGet(s->LocalAt(1)); Arguments args12435; args12435.Add(Value("market"), false); return CallDictionaryGet(c, fn12434, std::move(args12435)); }()); if (static_cast<bool>(v12433)) return v12433; v12433 = List({}); return v12433; }());
s->SetAt(14, v12432);
if (static_cast<bool>(([&]() -> Value { auto v12436 = ([&]() -> Value { auto v12437 = s->LocalAt(20); Value v12438; v12438 = Value(int64_t{24}); if (!static_cast<bool>(Binary("Lt", v12437, v12438))) return Value(false); v12437 = v12438; return Value(true); }()); if (static_cast<bool>(v12436)) return v12436; v12436 = ([&]() -> Value { auto v12439 = s->LocalAt(20); Value v12440; v12440 = Value(int64_t{695}); if (!static_cast<bool>(Binary("GtE", v12439, v12440))) return Value(false); v12439 = v12440; return Value(true); }()); if (static_cast<bool>(v12436)) return v12436; v12436 = ([&]() -> Value { auto v12441 = ([&]() -> Value { auto v12443 = s->LocalAt(20); return Binary("Mod", v12443, Value(int64_t{24})); }()); Value v12442; v12442 = Tuple({Value(int64_t{22}), Value(int64_t{23})}); if (!static_cast<bool>(Binary("In", v12441, v12442))) return Value(false); v12441 = v12442; return Value(true); }()); if (static_cast<bool>(v12436)) return v12436; v12436 = ([&]() -> Value { auto v12444 = ([&]() -> Value { auto fn12446 = s->Global("len"); Arguments args12447; args12447.Add(s->LocalAt(14), false); return Call(c, fn12446, std::move(args12447)); }()); Value v12445; v12445 = Value(int64_t{10}); if (!static_cast<bool>(Binary("GtE", v12444, v12445))) return Value(false); v12444 = v12445; return Value(true); }()); return v12436; }()))) {
return s->LocalAt(1);
}
auto v12448 = ([&]() -> Value { auto fn12449 = s->Global("_r128_future"); Arguments args12450; args12450.Add(s->LocalAt(12), false); return Call(c, fn12449, std::move(args12450)); }());
s->SetAt(8, v12448);
auto v12451 = ([&]() -> Value { Arguments args12452; args12452.Add(([&]() -> Value { auto v12453 = ([&]() -> Value { auto fn12454 = PrepareDictionaryGet(s->LocalAt(8)); Arguments args12455; args12455.Add(Value("farmer"), false); return CallDictionaryGet(c, fn12454, std::move(args12455)); }()); if (static_cast<bool>(v12453)) return v12453; v12453 = List({Value("PASS")}); return v12453; }()), false); args12452.Add(([&]() -> Value { auto v12456 = ([&]() -> Value { auto fn12457 = PrepareDictionaryGet(s->LocalAt(8)); Arguments args12458; args12458.Add(Value("hands"), false); return CallDictionaryGet(c, fn12457, std::move(args12458)); }()); if (static_cast<bool>(v12456)) return v12456; v12456 = List({}); return v12456; }()), true); return List(std::move(args12452.positional)); }());
s->SetAt(6, v12451);
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto comp12459 = std::make_shared<Scope>(); comp12459->globals = s->globals; comp12459->parent = s; static constexpr const char* comp12459_names[] = {"c"}; comp12459->PrepareSlots(comp12459_names); auto result12460 = List(); for (const auto& item12461 : Iterate(s->LocalAt(6))) { comp12459->SetAt(0, item12461); if (static_cast<bool>(([&]() -> Value { auto v12462 = comp12459->LocalAt(0); if (!static_cast<bool>(v12462)) return v12462; v12462 = ([&]() -> Value { auto v12463 = Get(comp12459->LocalAt(0), Value(int64_t{0})); Value v12464; v12464 = Value("PLANT"); if (!static_cast<bool>(Binary("Eq", v12463, v12464))) return Value(false); v12463 = v12464; return Value(true); }()); return v12462; }()))) return Value(true); } return Value(false); }())))) {
return s->LocalAt(1);
}
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto fn12465 = s->Global("_r97_budget"); Arguments args12466; args12466.positional.reserve(2); args12466.Add(s->LocalAt(12), false); args12466.Add(s->LocalAt(14), false); return Call(c, fn12465, std::move(args12466)); }())))) {
return s->LocalAt(1);
}
auto v12467 = ([&]() -> Value { auto fn12468 = s->Global("_r127_fields"); Arguments args12469; args12469.positional.reserve(2); args12469.Add(s->LocalAt(12), false); args12469.Add(s->LocalAt(1), false); return Call(c, fn12468, std::move(args12469)); }());
auto unpack12470 = Iterate(v12467);
ValidateUnpack(unpack12470, 2, false);
s->SetAt(7, unpack12470.at(0));
s->SetAt(17, unpack12470.at(1));
if (static_cast<bool>(([&]() -> Value { auto comp12471 = std::make_shared<Scope>(); comp12471->globals = s->globals; comp12471->parent = s; static constexpr const char* comp12471_names[] = {"o"}; comp12471->PrepareSlots(comp12471_names); auto result12472 = List(); for (const auto& item12473 : Iterate(s->LocalAt(14))) { comp12471->SetAt(0, item12473); if (static_cast<bool>(([&]() -> Value { auto v12474 = comp12471->LocalAt(0); if (!static_cast<bool>(v12474)) return v12474; v12474 = ([&]() -> Value { auto v12475 = Get(comp12471->LocalAt(0), Value(int64_t{0})); Value v12476; v12476 = Value("BUY_LAND"); if (!static_cast<bool>(Binary("Eq", v12475, v12476))) return Value(false); v12475 = v12476; return Value(true); }()); return v12474; }()))) return Value(true); } return Value(false); }()))) {
return s->LocalAt(1);
}
auto v12477 = Tuple({Tuple({Value(int64_t{4}), Value(int64_t{4})}), Tuple({Value(int64_t{5}), Value(int64_t{4})}), Tuple({Value(int64_t{4}), Value(int64_t{5})}), Tuple({Value(int64_t{5}), Value(int64_t{5})})});
s->SetAt(0, v12477);
auto v12478 = ([&]() -> Value { Arguments args12479; args12479.Add(([&]() -> Value { auto fn12480 = s->Global("tuple"); Arguments args12481; args12481.Add(Get(s->LocalAt(7), Value("farmer")), false); return Call(c, fn12480, std::move(args12481)); }()), false); args12479.Add(([&]() -> Value { auto fn12482 = s->Global("map"); Arguments args12483; args12483.positional.reserve(2); args12483.Add(s->Global("tuple"), false); args12483.Add(Get(s->LocalAt(7), Value("hands")), false); return Call(c, fn12482, std::move(args12483)); }()), true); return List(std::move(args12479.positional)); }());
s->SetAt(16, v12478);
for (const auto& item12484 : Iterate(s->LocalAt(14))) {
s->SetAt(13, item12484);
if (static_cast<bool>(([&]() -> Value { auto v12485 = s->LocalAt(13); if (!static_cast<bool>(v12485)) return v12485; v12485 = ([&]() -> Value { auto v12486 = Get(s->LocalAt(13), Value(int64_t{0})); Value v12487; v12487 = Value("HIRE"); if (!static_cast<bool>(Binary("Eq", v12486, v12487))) return Value(false); v12486 = v12487; return Value(true); }()); return v12485; }()))) {
auto v12488 = ([&]() -> Value { auto fn12489 = s->Global("min"); Arguments args12490; args12490.Add(s->LocalAt(0), false); args12490.Keyword("key", Define(&Code_6ba291e890a6ef569531, s, Signature{{"p"}, {}, {}, {}, "", "", ([]() -> std::span<const char* const> { static constexpr const char* names[] = {"p"}; return names; }())}, true, "<lambda>")); return Call(c, fn12489, std::move(args12490)); }());
s->SetAt(15, v12488);
(void)([&]() -> Value { auto fn12495 = Attribute(s->LocalAt(16), "append"); Arguments args12496; args12496.Add(s->LocalAt(15), false); return Call(c, fn12495, std::move(args12496)); }());
(void)([&]() -> Value { auto fn12497 = Attribute(Get(s->LocalAt(7), Value("hands")), "append"); Arguments args12498; args12498.Add(([&]() -> Value { auto fn12499 = s->Global("list"); Arguments args12500; args12500.Add(s->LocalAt(15), false); return Call(c, fn12499, std::move(args12500)); }()), false); return Call(c, fn12497, std::move(args12498)); }());
(void)([&]() -> Value { auto fn12501 = Attribute(Get(s->LocalAt(17), Value("inventories")), "append"); Arguments args12502; args12502.Add(([&]() -> Value { auto dict12503 = Dict(); return dict12503; }()), false); return Call(c, fn12501, std::move(args12502)); }());
}
else {
if (static_cast<bool>(([&]() -> Value { auto v12504 = ([&]() -> Value { auto v12505 = ([&]() -> Value { auto fn12507 = s->Global("len"); Arguments args12508; args12508.Add(s->LocalAt(13), false); return Call(c, fn12507, std::move(args12508)); }()); Value v12506; v12506 = Value(int64_t{2}); if (!static_cast<bool>(Binary("Gt", v12505, v12506))) return Value(false); v12505 = v12506; return Value(true); }()); if (!static_cast<bool>(v12504)) return v12504; v12504 = ([&]() -> Value { auto v12509 = Get(s->LocalAt(13), Value(int64_t{0})); Value v12510; v12510 = Value("BUY_SEED"); if (!static_cast<bool>(Binary("Eq", v12509, v12510))) return Value(false); v12509 = v12510; return Value(true); }()); return v12504; }()))) {
auto v12511 = ([&]() -> Value { auto v12512 = ([&]() -> Value { auto fn12513 = PrepareDictionaryGet(Get(s->LocalAt(17), Value("seeds"))); Arguments args12514; args12514.positional.reserve(2); args12514.Add(Get(s->LocalAt(13), Value(int64_t{1})), false); args12514.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn12513, std::move(args12514)); }()); return Binary("Add", v12512, ([&]() -> Value { auto fn12515 = s->Global("max"); Arguments args12516; args12516.positional.reserve(2); args12516.Add(Value(int64_t{0}), false); args12516.Add(([&]() -> Value { auto fn12517 = s->Global("int"); Arguments args12518; args12518.Add(Get(s->LocalAt(13), Value(int64_t{2})), false); return Call(c, fn12517, std::move(args12518)); }()), false); return Call(c, fn12515, std::move(args12516)); }())); }());
Put(Get(s->LocalAt(17), Value("seeds")), Get(s->LocalAt(13), Value(int64_t{1})), v12511);
}
}
}
auto v12519 = ([&]() -> Value { auto fn12520 = s->Global("dict"); Arguments args12521; args12521.Add(Get(s->LocalAt(17), Value("seeds")), false); return Call(c, fn12520, std::move(args12521)); }());
s->SetAt(3, v12519);
auto v12522 = ([&]() -> Value { auto dict12523 = Dict(); return dict12523; }());
s->SetAt(9, v12522);
for (const auto& item12524 : Iterate(s->LocalAt(6))) {
s->SetAt(5, item12524);
if (static_cast<bool>(([&]() -> Value { auto v12525 = ([&]() -> Value { auto v12526 = ([&]() -> Value { auto fn12528 = s->Global("len"); Arguments args12529; args12529.Add(s->LocalAt(5), false); return Call(c, fn12528, std::move(args12529)); }()); Value v12527; v12527 = Value(int64_t{1}); if (!static_cast<bool>(Binary("Gt", v12526, v12527))) return Value(false); v12526 = v12527; return Value(true); }()); if (!static_cast<bool>(v12525)) return v12525; v12525 = ([&]() -> Value { auto v12530 = Get(s->LocalAt(5), Value(int64_t{0})); Value v12531; v12531 = Value("PLANT"); if (!static_cast<bool>(Binary("Eq", v12530, v12531))) return Value(false); v12530 = v12531; return Value(true); }()); return v12525; }()))) {
auto v12532 = ([&]() -> Value { auto v12533 = ([&]() -> Value { auto fn12534 = PrepareDictionaryGet(s->LocalAt(9)); Arguments args12535; args12535.positional.reserve(2); args12535.Add(Get(s->LocalAt(5), Value(int64_t{1})), false); args12535.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn12534, std::move(args12535)); }()); return Binary("Add", v12533, Value(int64_t{1})); }());
Put(s->LocalAt(9), Get(s->LocalAt(5), Value(int64_t{1})), v12532);
}
}
for (const auto& item12536 : Iterate(([&]() -> Value { auto fn12537 = Attribute(s->LocalAt(9), "items"); Arguments args12538; return Call(c, fn12537, std::move(args12538)); }()))) {
auto unpack12539 = Iterate(item12536);
ValidateUnpack(unpack12539, 2, false);
s->SetAt(10, unpack12539.at(0));
s->SetAt(11, unpack12539.at(1));
auto v12540 = ([&]() -> Value { auto v12541 = ([&]() -> Value { auto fn12542 = PrepareDictionaryGet(s->LocalAt(3)); Arguments args12543; args12543.positional.reserve(2); args12543.Add(s->LocalAt(10), false); args12543.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn12542, std::move(args12543)); }()); return Binary("Add", v12541, s->LocalAt(11)); }());
Put(Get(s->LocalAt(17), Value("seeds")), s->LocalAt(10), v12540);
}
auto v12544 = ([&]() -> Value { auto fn12545 = s->Global("dict"); Arguments args12546; args12546.Add(Get(s->LocalAt(17), Value("seeds")), false); return Call(c, fn12545, std::move(args12546)); }());
s->SetAt(4, v12544);
for (const auto& item12547 : Iterate(([&]() -> Value { auto fn12548 = s->Global("enumerate"); Arguments args12549; args12549.Add(Slice(s->LocalAt(6), Value{}, ([&]() -> Value { auto fn12550 = s->Global("len"); Arguments args12551; args12551.Add(Get(s->LocalAt(17), Value("inventories")), false); return Call(c, fn12550, std::move(args12551)); }()), Value{}), false); return Call(c, fn12548, std::move(args12549)); }()))) {
auto unpack12552 = Iterate(item12547);
ValidateUnpack(unpack12552, 2, false);
s->SetAt(2, unpack12552.at(0));
s->SetAt(5, unpack12552.at(1));
(void)([&]() -> Value { auto fn12553 = Get(s->Global("_PLANNER_NS"), Value("_apply_unit_action")); Arguments args12554; args12554.positional.reserve(8); args12554.Add(s->LocalAt(7), false); args12554.Add(s->LocalAt(17), false); args12554.Add(s->LocalAt(2), false); args12554.Add(s->LocalAt(5), false); args12554.Add(Value(int64_t{10}), false); args12554.Add(([&]() -> Value { auto v12555 = s->LocalAt(20); return Binary("FloorDiv", v12555, Value(int64_t{24})); }()), false); args12554.Add(Value(int64_t{24}), false); args12554.Add(Value(int64_t{100}), false); return Call(c, fn12553, std::move(args12554)); }());
}
auto v12556 = ([&]() -> Value { auto comp12557 = std::make_shared<Scope>(); comp12557->globals = s->globals; comp12557->parent = s; static constexpr const char* comp12557_names[] = {"item"}; comp12557->PrepareSlots(comp12557_names); auto result12558 = Dict(); for (const auto& item12559 : Iterate(s->LocalAt(9))) { comp12557->SetAt(0, item12559); Put(result12558, comp12557->LocalAt(0), ([&]() -> Value { auto fn12560 = comp12557->Global("max"); Arguments args12561; args12561.positional.reserve(2); args12561.Add(Value(int64_t{0}), false); args12561.Add(([&]() -> Value { auto v12562 = ([&]() -> Value { auto v12563 = Get(comp12557->Captured("before"), comp12557->LocalAt(0)); return Binary("Sub", v12563, ([&]() -> Value { auto fn12564 = PrepareDictionaryGet(Get(comp12557->Captured("private"), Value("seeds"))); Arguments args12565; args12565.positional.reserve(2); args12565.Add(comp12557->LocalAt(0), false); args12565.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn12564, std::move(args12565)); }())); }()); return Binary("Sub", v12562, ([&]() -> Value { auto fn12566 = PrepareDictionaryGet(comp12557->Captured("available")); Arguments args12567; args12567.positional.reserve(2); args12567.Add(comp12557->LocalAt(0), false); args12567.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn12566, std::move(args12567)); }())); }()), false); return Call(c, fn12560, std::move(args12561)); }())); } return result12558; }());
s->SetAt(19, v12556);
auto v12568 = ([&]() -> Value { auto comp12569 = std::make_shared<Scope>(); comp12569->globals = s->globals; comp12569->parent = s; static constexpr const char* comp12569_names[] = {"item", "n"}; comp12569->PrepareSlots(comp12569_names); auto result12570 = Dict(); for (const auto& item12571 : Iterate(([&]() -> Value { auto fn12572 = Attribute(s->LocalAt(19), "items"); Arguments args12573; return Call(c, fn12572, std::move(args12573)); }()))) { auto unpack12574 = Iterate(item12571); ValidateUnpack(unpack12574, 2, false); comp12569->SetAt(0, unpack12574.at(0)); comp12569->SetAt(1, unpack12574.at(1)); if (!static_cast<bool>(([&]() -> Value { auto v12575 = comp12569->LocalAt(1); Value v12576; v12576 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v12575, v12576))) return Value(false); v12575 = v12576; return Value(true); }()))) continue; Put(result12570, comp12569->LocalAt(0), comp12569->LocalAt(1)); } return result12570; }());
s->SetAt(19, v12568);
if (static_cast<bool>(([&]() -> Value { auto v12577 = Unary("Not", s->LocalAt(19)); if (static_cast<bool>(v12577)) return v12577; v12577 = ([&]() -> Value { auto v12578 = ([&]() -> Value { auto v12580 = ([&]() -> Value { auto fn12581 = s->Global("len"); Arguments args12582; args12582.Add(s->LocalAt(14), false); return Call(c, fn12581, std::move(args12582)); }()); return Binary("Add", v12580, ([&]() -> Value { auto fn12583 = s->Global("len"); Arguments args12584; args12584.Add(s->LocalAt(19), false); return Call(c, fn12583, std::move(args12584)); }())); }()); Value v12579; v12579 = Value(int64_t{10}); if (!static_cast<bool>(Binary("Gt", v12578, v12579))) return Value(false); v12578 = v12579; return Value(true); }()); return v12577; }()))) {
return s->LocalAt(1);
}
auto v12585 = ([&]() -> Value { auto v12586 = ([&]() -> Value { auto fn12587 = s->Global("list"); Arguments args12588; args12588.Add(s->LocalAt(14), false); return Call(c, fn12587, std::move(args12588)); }()); return Binary("Add", v12586, ([&]() -> Value { auto comp12589 = std::make_shared<Scope>(); comp12589->globals = s->globals; comp12589->parent = s; static constexpr const char* comp12589_names[] = {"item", "n"}; comp12589->PrepareSlots(comp12589_names); auto result12590 = List(); for (const auto& item12591 : Iterate(([&]() -> Value { auto fn12592 = s->Global("sorted"); Arguments args12593; args12593.Add(([&]() -> Value { auto fn12594 = Attribute(s->LocalAt(19), "items"); Arguments args12595; return Call(c, fn12594, std::move(args12595)); }()), false); return Call(c, fn12592, std::move(args12593)); }()))) { auto unpack12596 = Iterate(item12591); ValidateUnpack(unpack12596, 2, false); comp12589->SetAt(0, unpack12596.at(0)); comp12589->SetAt(1, unpack12596.at(1)); result12590.node()->sequence.push_back(List({Value("BUY_SEED"), comp12589->LocalAt(0), comp12589->LocalAt(1)})); } return result12590; }())); }());
s->SetAt(18, v12585);
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto fn12597 = s->Global("_r97_budget"); Arguments args12598; args12598.positional.reserve(2); args12598.Add(s->LocalAt(12), false); args12598.Add(s->LocalAt(18), false); return Call(c, fn12597, std::move(args12598)); }())))) {
return s->LocalAt(1);
}
auto v12599 = s->Global("_R148_REPORT");
auto v12600 = Value("seed_prefund_turns");
auto v12601 = Get(v12599, v12600);
Put(v12599, v12600, Inplace("Add", v12601, Value(int64_t{1})));
auto v12602 = s->Global("_R148_REPORT");
auto v12603 = Value("seed_prefund_units");
auto v12604 = Get(v12602, v12603);
Put(v12602, v12603, Inplace("Add", v12604, ([&]() -> Value { auto fn12605 = s->Global("sum"); Arguments args12606; args12606.Add(([&]() -> Value { auto fn12607 = Attribute(s->LocalAt(19), "values"); Arguments args12608; return Call(c, fn12607, std::move(args12608)); }()), false); return Call(c, fn12605, std::move(args12606)); }())));
return ([&]() -> Value { auto fn12609 = s->Global("dict"); Arguments args12610; args12610.Add(s->LocalAt(1), false); args12610.Keyword("market", s->LocalAt(18)); return Call(c, fn12609, std::move(args12610)); }());
return {};
}
}  // namespace kagg::opponents::compiled
