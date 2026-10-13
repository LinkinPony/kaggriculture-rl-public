// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_aedcc5af9822fb0355cc(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "cap", "carried", "changed", "cmd", "configuration", "credit", "day", "farm", "fed", "first", "i", "interval", "k", "later", "market", "o", "observation", "overflow", "pos", "positions", "prices", "priv", "prod", "product", "q", "quote", "saved", "seat", "selling", "since", "st", "step", "stock", "tile", "units", "view_action", "visits", "y"};
s->PrepareSlots(s_names);
auto v23492 = ([&]() -> Value { auto fn23493 = s->Global("_CH_PARENT"); Arguments args23494; args23494.positional.reserve(2); args23494.Add(s->LocalAt(17), false); args23494.Add(s->LocalAt(5), false); return Call(c, fn23493, std::move(args23494)); }());
s->SetAt(0, v23492);
try {
auto v23496 = ([&]() -> Value { auto fn23497 = s->Global("int"); Arguments args23498; args23498.Add(Get(s->LocalAt(17), Value("step")), false); return Call(c, fn23497, std::move(args23498)); }());
s->SetAt(32, v23496);
auto v23499 = ([&]() -> Value { auto fn23500 = s->Global("int"); Arguments args23501; args23501.Add(Get(s->LocalAt(17), Value("player")), false); return Call(c, fn23500, std::move(args23501)); }());
s->SetAt(28, v23499);
auto v23502 = ([&]() -> Value { auto fn23503 = PrepareDictionaryGet(s->Global("_CH_STATE")); Arguments args23504; args23504.Add(s->LocalAt(28), false); return CallDictionaryGet(c, fn23503, std::move(args23504)); }());
s->SetAt(31, v23502);
if (static_cast<bool>(([&]() -> Value { auto v23505 = ([&]() -> Value { auto v23506 = s->LocalAt(32); Value v23507; v23507 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v23506, v23507))) return Value(false); v23506 = v23507; return Value(true); }()); if (static_cast<bool>(v23505)) return v23505; v23505 = ([&]() -> Value { auto v23508 = s->LocalAt(31); Value v23509; v23509 = Value{}; if (!static_cast<bool>(Binary("Is", v23508, v23509))) return Value(false); v23508 = v23509; return Value(true); }()); if (static_cast<bool>(v23505)) return v23505; v23505 = ([&]() -> Value { auto v23510 = s->LocalAt(32); Value v23511; v23511 = Get(s->LocalAt(31), Value("step")); if (!static_cast<bool>(Binary("LtE", v23510, v23511))) return Value(false); v23510 = v23511; return Value(true); }()); return v23505; }()))) {
auto v23512 = ([&]() -> Value { auto dict23513 = Dict(); auto key23514 = Value("step"); Put(dict23513, key23514, Unary("USub", Value(int64_t{1}))); auto key23515 = Value("credit"); Put(dict23513, key23515, ([&]() -> Value { auto dict23516 = Dict(); return dict23516; }())); return dict23513; }());
s->SetAt(31, v23512);
Put(s->Global("_CH_STATE"), s->LocalAt(28), v23512);
if (static_cast<bool>(([&]() -> Value { auto v23517 = s->LocalAt(32); Value v23518; v23518 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v23517, v23518))) return Value(false); v23517 = v23518; return Value(true); }()))) {
for (const auto& item23519 : Iterate(s->Global("_CH_REPORT"))) {
s->SetAt(13, item23519);
auto v23520 = Value(int64_t{0});
Put(s->Global("_CH_REPORT"), s->LocalAt(13), v23520);
}
}
}
auto v23521 = s->LocalAt(32);
Put(s->LocalAt(31), Value("step"), v23521);
if (static_cast<bool>(([&]() -> Value { auto v23522 = Unary("Not", ([&]() -> Value { auto fn23523 = s->Global("isinstance"); Arguments args23524; args23524.positional.reserve(2); args23524.Add(s->LocalAt(0), false); args23524.Add(s->Global("dict"), false); return Call(c, fn23523, std::move(args23524)); }())); if (static_cast<bool>(v23522)) return v23522; v23522 = ([&]() -> Value { auto v23525 = s->LocalAt(32); Value v23526; v23526 = Value(int64_t{717}); if (!static_cast<bool>(Binary("Gt", v23525, v23526))) return Value(false); v23525 = v23526; return Value(true); }()); return v23522; }()))) {
return s->LocalAt(0);
}
auto v23527 = ([&]() -> Value { auto v23528 = s->LocalAt(32); return Binary("FloorDiv", v23528, Value(int64_t{24})); }());
s->SetAt(7, v23527);
auto v23529 = Get(Get(s->LocalAt(17), Value("farms")), s->LocalAt(28));
s->SetAt(8, v23529);
auto v23530 = Get(s->LocalAt(17), Value("private"));
s->SetAt(22, v23530);
auto v23531 = Get(Get(s->LocalAt(17), Value("market")), Value("prices"));
s->SetAt(21, v23531);
auto v23532 = ([&]() -> Value { auto v23533 = List({([&]() -> Value { auto fn23534 = s->Global("tuple"); Arguments args23535; args23535.Add(Get(s->LocalAt(8), Value("farmer")), false); return Call(c, fn23534, std::move(args23535)); }())}); return Binary("Add", v23533, ([&]() -> Value { auto comp23536 = std::make_shared<Scope>(); comp23536->globals = s->globals; comp23536->parent = s; static constexpr const char* comp23536_names[] = {"h"}; comp23536->PrepareSlots(comp23536_names); auto result23537 = List(); for (const auto& item23538 : Iterate(Get(s->LocalAt(8), Value("hands")))) { comp23536->SetAt(0, item23538); result23537.node()->sequence.push_back(([&]() -> Value { auto fn23539 = comp23536->Global("tuple"); Arguments args23540; args23540.Add(comp23536->LocalAt(0), false); return Call(c, fn23539, std::move(args23540)); }())); } return result23537; }())); }());
s->SetAt(20, v23532);
auto v23541 = ([&]() -> Value { auto v23542 = List({([&]() -> Value { auto fn23543 = s->Global("list"); Arguments args23544; args23544.Add(([&]() -> Value { auto v23545 = ([&]() -> Value { auto fn23546 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args23547; args23547.Add(Value("farmer"), false); return CallDictionaryGet(c, fn23546, std::move(args23547)); }()); if (static_cast<bool>(v23545)) return v23545; v23545 = List({Value("PASS")}); return v23545; }()), false); return Call(c, fn23543, std::move(args23544)); }())}); return Binary("Add", v23542, ([&]() -> Value { auto comp23548 = std::make_shared<Scope>(); comp23548->globals = s->globals; comp23548->parent = s; static constexpr const char* comp23548_names[] = {"c"}; comp23548->PrepareSlots(comp23548_names); auto result23549 = List(); for (const auto& item23550 : Iterate(([&]() -> Value { auto v23551 = ([&]() -> Value { auto fn23552 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args23553; args23553.Add(Value("hands"), false); return CallDictionaryGet(c, fn23552, std::move(args23553)); }()); if (static_cast<bool>(v23551)) return v23551; v23551 = List({}); return v23551; }()))) { comp23548->SetAt(0, item23550); result23549.node()->sequence.push_back(([&]() -> Value { auto fn23554 = comp23548->Global("list"); Arguments args23555; args23555.Add(comp23548->LocalAt(0), false); return Call(c, fn23554, std::move(args23555)); }())); } return result23549; }())); }());
s->SetAt(35, v23541);
auto v23556 = ([&]() -> Value { auto comp23557 = std::make_shared<Scope>(); comp23557->globals = s->globals; comp23557->parent = s; static constexpr const char* comp23557_names[] = {"o"}; comp23557->PrepareSlots(comp23557_names); auto result23558 = List(); for (const auto& item23559 : Iterate(([&]() -> Value { auto v23560 = ([&]() -> Value { auto fn23561 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args23562; args23562.Add(Value("market"), false); return CallDictionaryGet(c, fn23561, std::move(args23562)); }()); if (static_cast<bool>(v23560)) return v23560; v23560 = List({}); return v23560; }()))) { comp23557->SetAt(0, item23559); result23558.node()->sequence.push_back(([&]() -> Value { auto fn23563 = comp23557->Global("list"); Arguments args23564; args23564.Add(comp23557->LocalAt(0), false); return Call(c, fn23563, std::move(args23564)); }())); } return result23558; }());
s->SetAt(15, v23556);
auto v23565 = Value(false);
s->SetAt(3, v23565);
auto v23566 = Value{};
s->SetAt(37, v23566);
for (const auto& item23567 : Iterate(([&]() -> Value { auto fn23568 = s->Global("enumerate"); Arguments args23569; args23569.Add(Slice(s->LocalAt(20), Value{}, ([&]() -> Value { auto fn23570 = s->Global("len"); Arguments args23571; args23571.Add(s->LocalAt(35), false); return Call(c, fn23570, std::move(args23571)); }()), Value{}), false); return Call(c, fn23568, std::move(args23569)); }()))) {
auto unpack23572 = Iterate(item23567);
ValidateUnpack(unpack23572, 2, false);
s->SetAt(11, unpack23572.at(0));
s->SetAt(19, unpack23572.at(1));
auto v23573 = Get(s->LocalAt(35), s->LocalAt(11));
s->SetAt(4, v23573);
if (static_cast<bool>(([&]() -> Value { auto v23574 = Unary("Not", s->LocalAt(4)); if (static_cast<bool>(v23574)) return v23574; v23574 = ([&]() -> Value { auto v23575 = Get(s->LocalAt(4), Value(int64_t{0})); Value v23576; v23576 = Tuple({Value("CARE"), Value("COLLECT_FERTILIZER")}); if (!static_cast<bool>(Binary("NotIn", v23575, v23576))) return Value(false); v23575 = v23576; return Value(true); }()); return v23574; }()))) {
continue;
}
auto v23577 = Get(Get(Get(s->LocalAt(8), Value("tiles")), Get(s->LocalAt(19), Value(int64_t{1}))), Get(s->LocalAt(19), Value(int64_t{0})));
s->SetAt(34, v23577);
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto v23578 = ([&]() -> Value { auto fn23579 = s->Global("isinstance"); Arguments args23580; args23580.positional.reserve(2); args23580.Add(s->LocalAt(34), false); args23580.Add(s->Global("dict"), false); return Call(c, fn23579, std::move(args23580)); }()); if (!static_cast<bool>(v23578)) return v23578; v23578 = ([&]() -> Value { auto v23581 = ([&]() -> Value { auto fn23583 = PrepareDictionaryGet(s->LocalAt(34)); Arguments args23584; args23584.Add(Value("animal"), false); return CallDictionaryGet(c, fn23583, std::move(args23584)); }()); Value v23582; v23582 = s->Global("_CH_ANIMALS"); if (!static_cast<bool>(Binary("In", v23581, v23582))) return Value(false); v23581 = v23582; return Value(true); }()); return v23578; }())))) {
continue;
}
auto v23585 = Get(s->Global("_CH_ANIMALS"), Get(s->LocalAt(34), Value("animal")));
auto unpack23586 = Iterate(v23585);
ValidateUnpack(unpack23586, 4, false);
s->SetAt(24, unpack23586.at(0));
s->SetAt(1, unpack23586.at(1));
s->SetAt(10, unpack23586.at(2));
s->SetAt(12, unpack23586.at(3));
auto v23587 = ([&]() -> Value { auto v23588 = ([&]() -> Value { auto v23589 = ([&]() -> Value { auto v23590 = s->LocalAt(7); return Binary("Add", v23590, Value(int64_t{1})); }()); return Binary("Sub", v23589, ([&]() -> Value { auto fn23591 = s->Global("int"); Arguments args23592; args23592.Add(([&]() -> Value { auto fn23593 = PrepareDictionaryGet(s->LocalAt(34)); Arguments args23594; args23594.positional.reserve(2); args23594.Add(Value("placed_day"), false); args23594.Add(Value(int64_t{99}), false); return CallDictionaryGet(c, fn23593, std::move(args23594)); }()), false); return Call(c, fn23591, std::move(args23592)); }())); }()); return Binary("Sub", v23588, s->LocalAt(10)); }());
s->SetAt(30, v23587);
if (static_cast<bool>(([&]() -> Value { auto v23595 = ([&]() -> Value { auto v23596 = s->LocalAt(30); Value v23597; v23597 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Lt", v23596, v23597))) return Value(false); v23596 = v23597; return Value(true); }()); if (static_cast<bool>(v23595)) return v23595; v23595 = ([&]() -> Value { auto v23598 = ([&]() -> Value { auto v23600 = s->LocalAt(30); return Binary("Mod", v23600, s->LocalAt(12)); }()); Value v23599; v23599 = Value(int64_t{0}); if (!static_cast<bool>(Binary("NotEq", v23598, v23599))) return Value(false); v23598 = v23599; return Value(true); }()); return v23595; }()))) {
continue;
}
auto v23601 = ([&]() -> Value { auto fn23602 = s->Global("int"); Arguments args23603; args23603.Add(([&]() -> Value { auto fn23604 = PrepareDictionaryGet(s->LocalAt(34)); Arguments args23605; args23605.positional.reserve(2); args23605.Add(Value("yield_units"), false); args23605.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn23604, std::move(args23605)); }()), false); return Call(c, fn23602, std::move(args23603)); }());
s->SetAt(38, v23601);
if (static_cast<bool>(([&]() -> Value { auto v23606 = s->LocalAt(37); Value v23607; v23607 = Value{}; if (!static_cast<bool>(Binary("Is", v23606, v23607))) return Value(false); v23606 = v23607; return Value(true); }()))) {
auto v23608 = ([&]() -> Value { auto fn23609 = s->Global("_ch_visits_today"); Arguments args23610; args23610.positional.reserve(2); args23610.Add(s->LocalAt(17), false); args23610.Add(s->LocalAt(0), false); return Call(c, fn23609, std::move(args23610)); }());
s->SetAt(37, v23608);
}
auto v23611 = ([&]() -> Value { auto fn23612 = PrepareDictionaryGet(s->LocalAt(37)); Arguments args23613; args23613.positional.reserve(2); args23613.Add(s->LocalAt(19), false); args23613.Add(List({}), false); return CallDictionaryGet(c, fn23612, std::move(args23613)); }());
s->SetAt(14, v23611);
if (static_cast<bool>(([&]() -> Value { auto comp23614 = std::make_shared<Scope>(); comp23614->globals = s->globals; comp23614->parent = s; static constexpr const char* comp23614_names[] = {"op", "t"}; comp23614->PrepareSlots(comp23614_names); auto result23615 = List(); for (const auto& item23616 : Iterate(s->LocalAt(14))) { auto unpack23617 = Iterate(item23616); ValidateUnpack(unpack23617, 2, false); comp23614->SetAt(1, unpack23617.at(0)); comp23614->SetAt(0, unpack23617.at(1)); if (static_cast<bool>(([&]() -> Value { auto v23618 = comp23614->LocalAt(0); Value v23619; v23619 = Value("HARVEST"); if (!static_cast<bool>(Binary("Eq", v23618, v23619))) return Value(false); v23618 = v23619; return Value(true); }()))) return Value(true); } return Value(false); }()))) {
continue;
}
auto v23620 = ([&]() -> Value { auto v23621 = ([&]() -> Value { auto fn23622 = s->Global("bool"); Arguments args23623; args23623.Add(([&]() -> Value { auto fn23624 = PrepareDictionaryGet(s->LocalAt(34)); Arguments args23625; args23625.Add(Value("fed_today"), false); return CallDictionaryGet(c, fn23624, std::move(args23625)); }()), false); return Call(c, fn23622, std::move(args23623)); }()); if (static_cast<bool>(v23621)) return v23621; v23621 = ([&]() -> Value { auto comp23626 = std::make_shared<Scope>(); comp23626->globals = s->globals; comp23626->parent = s; static constexpr const char* comp23626_names[] = {"op", "t"}; comp23626->PrepareSlots(comp23626_names); auto result23627 = List(); for (const auto& item23628 : Iterate(s->LocalAt(14))) { auto unpack23629 = Iterate(item23628); ValidateUnpack(unpack23629, 2, false); comp23626->SetAt(1, unpack23629.at(0)); comp23626->SetAt(0, unpack23629.at(1)); if (static_cast<bool>(([&]() -> Value { auto v23630 = comp23626->LocalAt(0); Value v23631; v23631 = Value("FEED"); if (!static_cast<bool>(Binary("Eq", v23630, v23631))) return Value(false); v23630 = v23631; return Value(true); }()))) return Value(true); } return Value(false); }()); return v23621; }());
s->SetAt(9, v23620);
auto v23632 = ([&]() -> Value { auto v23633 = Value(int64_t{1}); return Binary("Add", v23633, (static_cast<bool>(s->LocalAt(9)) ? ([&]() -> Value { auto fn23634 = s->Global("int"); Arguments args23635; args23635.Add(([&]() -> Value { auto fn23636 = PrepareDictionaryGet(s->LocalAt(34)); Arguments args23637; args23637.positional.reserve(2); args23637.Add(Value("pending_care_bonus"), false); args23637.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn23636, std::move(args23637)); }()), false); return Call(c, fn23634, std::move(args23635)); }()) : Value(int64_t{0}))); }());
s->SetAt(23, v23632);
auto v23638 = ([&]() -> Value { auto v23639 = ([&]() -> Value { auto v23640 = s->LocalAt(38); return Binary("Add", v23640, s->LocalAt(23)); }()); return Binary("Sub", v23639, s->LocalAt(1)); }());
s->SetAt(18, v23638);
if (static_cast<bool>(([&]() -> Value { auto v23641 = ([&]() -> Value { auto v23642 = s->LocalAt(18); Value v23643; v23643 = Value(int64_t{0}); if (!static_cast<bool>(Binary("LtE", v23642, v23643))) return Value(false); v23642 = v23643; return Value(true); }()); if (static_cast<bool>(v23641)) return v23641; v23641 = ([&]() -> Value { auto v23644 = s->LocalAt(38); Value v23645; v23645 = Value(int64_t{0}); if (!static_cast<bool>(Binary("LtE", v23644, v23645))) return Value(false); v23644 = v23645; return Value(true); }()); return v23641; }()))) {
continue;
}
auto v23646 = ([&]() -> Value { auto fn23647 = s->Global("int"); Arguments args23648; args23648.Add(([&]() -> Value { auto fn23649 = PrepareDictionaryGet(s->LocalAt(21)); Arguments args23650; args23650.positional.reserve(2); args23650.Add(s->LocalAt(24), false); args23650.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn23649, std::move(args23650)); }()), false); return Call(c, fn23647, std::move(args23648)); }());
s->SetAt(26, v23646);
if (static_cast<bool>(([&]() -> Value { auto v23651 = Get(s->LocalAt(4), Value(int64_t{0})); Value v23652; v23652 = Value("COLLECT_FERTILIZER"); if (!static_cast<bool>(Binary("Eq", v23651, v23652))) return Value(false); v23651 = v23652; return Value(true); }()))) {
if (static_cast<bool>(([&]() -> Value { auto v23653 = ([&]() -> Value { auto v23655 = s->LocalAt(18); return Binary("Mult", v23655, s->LocalAt(26)); }()); Value v23654; v23654 = ([&]() -> Value { auto fn23656 = s->Global("int"); Arguments args23657; args23657.Add(([&]() -> Value { auto fn23658 = PrepareDictionaryGet(s->LocalAt(21)); Arguments args23659; args23659.positional.reserve(2); args23659.Add(Value("FERTILIZER"), false); args23659.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn23658, std::move(args23659)); }()), false); return Call(c, fn23656, std::move(args23657)); }()); if (!static_cast<bool>(Binary("LtE", v23653, v23654))) return Value(false); v23653 = v23654; return Value(true); }()))) {
continue;
}
}
else {
if (static_cast<bool>(([&]() -> Value { auto v23660 = ([&]() -> Value { auto comp23661 = std::make_shared<Scope>(); comp23661->globals = s->globals; comp23661->parent = s; static constexpr const char* comp23661_names[] = {"op", "t"}; comp23661->PrepareSlots(comp23661_names); auto result23662 = List(); for (const auto& item23663 : Iterate(s->LocalAt(14))) { auto unpack23664 = Iterate(item23663); ValidateUnpack(unpack23664, 2, false); comp23661->SetAt(1, unpack23664.at(0)); comp23661->SetAt(0, unpack23664.at(1)); if (static_cast<bool>(([&]() -> Value { auto v23665 = comp23661->LocalAt(0); Value v23666; v23666 = Value("COLLECT_FERTILIZER"); if (!static_cast<bool>(Binary("Eq", v23665, v23666))) return Value(false); v23665 = v23666; return Value(true); }()))) return Value(true); } return Value(false); }()); if (static_cast<bool>(v23660)) return v23660; v23660 = ([&]() -> Value { auto v23667 = s->LocalAt(18); Value v23668; v23668 = Value(int64_t{1}); if (!static_cast<bool>(Binary("LtE", v23667, v23668))) return Value(false); v23667 = v23668; return Value(true); }()); return v23660; }()))) {
continue;
}
}
auto v23669 = ([&]() -> Value { auto fn23670 = s->Global("sum"); Arguments args23671; args23671.Add(([&]() -> Value { auto comp23672 = std::make_shared<Scope>(); comp23672->globals = s->globals; comp23672->parent = s; static constexpr const char* comp23672_names[] = {"inv", "v"}; comp23672->PrepareSlots(comp23672_names); auto result23673 = List(); for (const auto& item23674 : Iterate(Get(s->LocalAt(22), Value("inventories")))) { comp23672->SetAt(0, item23674); for (const auto& item23675 : Iterate(([&]() -> Value { auto fn23676 = Attribute(comp23672->LocalAt(0), "values"); Arguments args23677; return Call(c, fn23676, std::move(args23677)); }()))) { comp23672->SetAt(1, item23675); result23673.node()->sequence.push_back(([&]() -> Value { auto fn23678 = comp23672->Global("int"); Arguments args23679; args23679.Add(comp23672->LocalAt(1), false); return Call(c, fn23678, std::move(args23679)); }())); } } return result23673; }()), false); return Call(c, fn23670, std::move(args23671)); }());
s->SetAt(2, v23669);
if (static_cast<bool>(([&]() -> Value { auto v23680 = ([&]() -> Value { auto v23682 = ([&]() -> Value { auto v23683 = ([&]() -> Value { auto fn23684 = s->Global("sum"); Arguments args23685; args23685.Add(([&]() -> Value { auto comp23686 = std::make_shared<Scope>(); comp23686->globals = s->globals; comp23686->parent = s; static constexpr const char* comp23686_names[] = {"v"}; comp23686->PrepareSlots(comp23686_names); auto result23687 = List(); for (const auto& item23688 : Iterate(([&]() -> Value { auto fn23689 = Attribute(Get(s->LocalAt(22), Value("shed")), "values"); Arguments args23690; return Call(c, fn23689, std::move(args23690)); }()))) { comp23686->SetAt(0, item23688); result23687.node()->sequence.push_back(([&]() -> Value { auto fn23691 = comp23686->Global("int"); Arguments args23692; args23692.Add(comp23686->LocalAt(0), false); return Call(c, fn23691, std::move(args23692)); }())); } return result23687; }()), false); return Call(c, fn23684, std::move(args23685)); }()); return Binary("Add", v23683, s->LocalAt(2)); }()); return Binary("Add", v23682, s->LocalAt(38)); }()); Value v23681; v23681 = s->Global("_CH_SHED"); if (!static_cast<bool>(Binary("GtE", v23680, v23681))) return Value(false); v23680 = v23681; return Value(true); }()))) {
auto v23693 = s->Global("_CH_REPORT");
auto v23694 = Value("ch_shed_block");
auto v23695 = Get(v23693, v23694);
Put(v23693, v23694, Inplace("Add", v23695, Value(int64_t{1})));
continue;
}
auto v23696 = List({Value("HARVEST")});
Put(s->LocalAt(35), s->LocalAt(11), v23696);
auto v23697 = s->Global("_CH_REPORT");
auto v23698 = (static_cast<bool>(([&]() -> Value { auto v23700 = Get(s->LocalAt(4), Value(int64_t{0})); Value v23701; v23701 = Value("COLLECT_FERTILIZER"); if (!static_cast<bool>(Binary("Eq", v23700, v23701))) return Value(false); v23700 = v23701; return Value(true); }())) ? Value("ch_collect_swaps") : Value("ch_care_swaps"));
auto v23699 = Get(v23697, v23698);
Put(v23697, v23698, Inplace("Add", v23699, Value(int64_t{1})));
auto v23702 = (static_cast<bool>(([&]() -> Value { auto v23703 = Get(s->LocalAt(4), Value(int64_t{0})); Value v23704; v23704 = Value("COLLECT_FERTILIZER"); if (!static_cast<bool>(Binary("Eq", v23703, v23704))) return Value(false); v23703 = v23704; return Value(true); }())) ? s->LocalAt(18) : ([&]() -> Value { auto v23705 = s->LocalAt(18); return Binary("Sub", v23705, Value(int64_t{1})); }()));
s->SetAt(27, v23702);
auto v23706 = s->Global("_CH_REPORT");
auto v23707 = Value("ch_saved");
auto v23708 = Get(v23706, v23707);
Put(v23706, v23707, Inplace("Add", v23708, s->LocalAt(27)));
auto v23709 = ([&]() -> Value { auto v23710 = ([&]() -> Value { auto fn23711 = PrepareDictionaryGet(Get(s->LocalAt(31), Value("credit"))); Arguments args23712; args23712.positional.reserve(2); args23712.Add(s->LocalAt(24), false); args23712.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn23711, std::move(args23712)); }()); return Binary("Add", v23710, s->LocalAt(27)); }());
Put(Get(s->LocalAt(31), Value("credit")), s->LocalAt(24), v23709);
auto v23713 = Value(true);
s->SetAt(3, v23713);
}
if (static_cast<bool>(([&]() -> Value { auto v23714 = s->Global("_CH_SELL"); if (!static_cast<bool>(v23714)) return v23714; v23714 = ([&]() -> Value { auto comp23715 = std::make_shared<Scope>(); comp23715->globals = s->globals; comp23715->parent = s; static constexpr const char* comp23715_names[] = {"v"}; comp23715->PrepareSlots(comp23715_names); auto result23716 = List(); for (const auto& item23717 : Iterate(([&]() -> Value { auto fn23718 = Attribute(Get(s->LocalAt(31), Value("credit")), "values"); Arguments args23719; return Call(c, fn23718, std::move(args23719)); }()))) { comp23715->SetAt(0, item23717); if (static_cast<bool>(([&]() -> Value { auto v23720 = comp23715->LocalAt(0); Value v23721; v23721 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v23720, v23721))) return Value(false); v23720 = v23721; return Value(true); }()))) return Value(true); } return Value(false); }()); return v23714; }()))) {
auto v23722 = ([&]() -> Value { auto dict23723 = Dict(); auto key23724 = Value("farmer"); Put(dict23723, key23724, Get(s->LocalAt(35), Value(int64_t{0}))); auto key23725 = Value("hands"); Put(dict23723, key23725, Slice(s->LocalAt(35), Value(int64_t{1}), Value{}, Value{})); auto key23726 = Value("market"); Put(dict23723, key23726, s->LocalAt(15)); return dict23723; }());
s->SetAt(36, v23722);
auto v23727 = ([&]() -> Value { auto fn23728 = s->Global("dict"); Arguments args23729; args23729.Add(([&]() -> Value { auto fn23730 = s->Global("projected_shed"); Arguments args23731; args23731.positional.reserve(2); args23731.Add(s->LocalAt(36), false); args23731.Add(([&]() -> Value { auto fn23732 = s->Global("FarmView"); Arguments args23733; args23733.Add(s->LocalAt(17), false); return Call(c, fn23732, std::move(args23733)); }()), false); return Call(c, fn23730, std::move(args23731)); }()), false); return Call(c, fn23728, std::move(args23729)); }());
s->SetAt(33, v23727);
for (const auto& item23734 : Iterate(([&]() -> Value { auto fn23735 = s->Global("list"); Arguments args23736; args23736.Add(([&]() -> Value { auto fn23737 = Attribute(Get(s->LocalAt(31), Value("credit")), "items"); Arguments args23738; return Call(c, fn23737, std::move(args23738)); }()), false); return Call(c, fn23735, std::move(args23736)); }()))) {
auto unpack23739 = Iterate(item23734);
ValidateUnpack(unpack23739, 2, false);
s->SetAt(24, unpack23739.at(0));
s->SetAt(6, unpack23739.at(1));
if (static_cast<bool>(([&]() -> Value { auto v23740 = ([&]() -> Value { auto v23741 = s->LocalAt(6); Value v23742; v23742 = Value(int64_t{0}); if (!static_cast<bool>(Binary("LtE", v23741, v23742))) return Value(false); v23741 = v23742; return Value(true); }()); if (static_cast<bool>(v23740)) return v23740; v23740 = ([&]() -> Value { auto v23743 = ([&]() -> Value { auto fn23745 = s->Global("len"); Arguments args23746; args23746.Add(s->LocalAt(15), false); return Call(c, fn23745, std::move(args23746)); }()); Value v23744; v23744 = Value(int64_t{10}); if (!static_cast<bool>(Binary("GtE", v23743, v23744))) return Value(false); v23743 = v23744; return Value(true); }()); if (static_cast<bool>(v23740)) return v23740; v23740 = ([&]() -> Value { auto v23747 = ([&]() -> Value { auto fn23749 = s->Global("int"); Arguments args23750; args23750.Add(([&]() -> Value { auto fn23751 = PrepareDictionaryGet(s->LocalAt(21)); Arguments args23752; args23752.positional.reserve(2); args23752.Add(s->LocalAt(24), false); args23752.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn23751, std::move(args23752)); }()), false); return Call(c, fn23749, std::move(args23750)); }()); Value v23748; v23748 = Value(int64_t{2}); if (!static_cast<bool>(Binary("Lt", v23747, v23748))) return Value(false); v23747 = v23748; return Value(true); }()); return v23740; }()))) {
continue;
}
auto v23753 = ([&]() -> Value { auto fn23754 = s->Global("sum"); Arguments args23755; args23755.Add(([&]() -> Value { auto comp23756 = std::make_shared<Scope>(); comp23756->globals = s->globals; comp23756->parent = s; static constexpr const char* comp23756_names[] = {"o"}; comp23756->PrepareSlots(comp23756_names); auto result23757 = List(); for (const auto& item23758 : Iterate(s->LocalAt(15))) { comp23756->SetAt(0, item23758); if (!static_cast<bool>(([&]() -> Value { auto v23759 = ([&]() -> Value { auto v23760 = ([&]() -> Value { auto fn23762 = comp23756->Global("len"); Arguments args23763; args23763.Add(comp23756->LocalAt(0), false); return Call(c, fn23762, std::move(args23763)); }()); Value v23761; v23761 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v23760, v23761))) return Value(false); v23760 = v23761; return Value(true); }()); if (!static_cast<bool>(v23759)) return v23759; v23759 = ([&]() -> Value { auto v23764 = Slice(comp23756->LocalAt(0), Value{}, Value(int64_t{2}), Value{}); Value v23765; v23765 = List({Value("SELL"), comp23756->Captured("product")}); if (!static_cast<bool>(Binary("Eq", v23764, v23765))) return Value(false); v23764 = v23765; return Value(true); }()); return v23759; }()))) continue; result23757.node()->sequence.push_back(([&]() -> Value { auto fn23766 = comp23756->Global("int"); Arguments args23767; args23767.Add(Get(comp23756->LocalAt(0), Value(int64_t{2})), false); return Call(c, fn23766, std::move(args23767)); }())); } return result23757; }()), false); return Call(c, fn23754, std::move(args23755)); }());
s->SetAt(29, v23753);
auto v23768 = ([&]() -> Value { auto fn23769 = s->Global("min"); Arguments args23770; args23770.positional.reserve(2); args23770.Add(s->LocalAt(6), false); args23770.Add(([&]() -> Value { auto v23771 = ([&]() -> Value { auto fn23772 = s->Global("int"); Arguments args23773; args23773.Add(([&]() -> Value { auto fn23774 = PrepareDictionaryGet(s->LocalAt(33)); Arguments args23775; args23775.positional.reserve(2); args23775.Add(s->LocalAt(24), false); args23775.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn23774, std::move(args23775)); }()), false); return Call(c, fn23772, std::move(args23773)); }()); return Binary("Sub", v23771, s->LocalAt(29)); }()), false); return Call(c, fn23769, std::move(args23770)); }());
s->SetAt(25, v23768);
if (static_cast<bool>(([&]() -> Value { auto v23776 = s->LocalAt(25); Value v23777; v23777 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v23776, v23777))) return Value(false); v23776 = v23777; return Value(true); }()))) {
bool exhausted23778 = true;
for (const auto& item23779 : Iterate(s->LocalAt(15))) {
s->SetAt(16, item23779);
if (static_cast<bool>(([&]() -> Value { auto v23780 = ([&]() -> Value { auto v23781 = ([&]() -> Value { auto fn23783 = s->Global("len"); Arguments args23784; args23784.Add(s->LocalAt(16), false); return Call(c, fn23783, std::move(args23784)); }()); Value v23782; v23782 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v23781, v23782))) return Value(false); v23781 = v23782; return Value(true); }()); if (!static_cast<bool>(v23780)) return v23780; v23780 = ([&]() -> Value { auto v23785 = Slice(s->LocalAt(16), Value{}, Value(int64_t{2}), Value{}); Value v23786; v23786 = List({Value("SELL"), s->LocalAt(24)}); if (!static_cast<bool>(Binary("Eq", v23785, v23786))) return Value(false); v23785 = v23786; return Value(true); }()); return v23780; }()))) {
auto v23787 = ([&]() -> Value { auto v23788 = ([&]() -> Value { auto fn23789 = s->Global("int"); Arguments args23790; args23790.Add(Get(s->LocalAt(16), Value(int64_t{2})), false); return Call(c, fn23789, std::move(args23790)); }()); return Binary("Add", v23788, s->LocalAt(25)); }());
Put(s->LocalAt(16), Value(int64_t{2}), v23787);
exhausted23778 = false;
break;
}
}
if (exhausted23778) {
(void)([&]() -> Value { auto fn23791 = Attribute(s->LocalAt(15), "insert"); Arguments args23792; args23792.positional.reserve(2); args23792.Add(Value(int64_t{0}), false); args23792.Add(List({Value("SELL"), s->LocalAt(24), s->LocalAt(25)}), false); return Call(c, fn23791, std::move(args23792)); }());
}
auto v23793 = ([&]() -> Value { auto v23794 = s->LocalAt(6); return Binary("Sub", v23794, s->LocalAt(25)); }());
Put(Get(s->LocalAt(31), Value("credit")), s->LocalAt(24), v23793);
auto v23795 = s->Global("_CH_REPORT");
auto v23796 = Value("ch_sold");
auto v23797 = Get(v23795, v23796);
Put(v23795, v23796, Inplace("Add", v23797, s->LocalAt(25)));
auto v23798 = Value(true);
s->SetAt(3, v23798);
}
}
}
if (static_cast<bool>(s->LocalAt(3))) {
auto v23799 = ([&]() -> Value { auto fn23800 = s->Global("dict"); Arguments args23801; args23801.Add(s->LocalAt(0), false); return Call(c, fn23800, std::move(args23801)); }());
s->SetAt(0, v23799);
auto v23802 = Get(s->LocalAt(35), Value(int64_t{0}));
Put(s->LocalAt(0), Value("farmer"), v23802);
auto v23803 = Slice(s->LocalAt(35), Value(int64_t{1}), Value{}, Value{});
Put(s->LocalAt(0), Value("hands"), v23803);
auto v23804 = Slice(s->LocalAt(15), Value{}, Value(int64_t{10}), Value{});
Put(s->LocalAt(0), Value("market"), v23804);
}
} catch (const Error& error23495) {
if (Matches(error23495, s->Global("Exception"))) {
auto v23805 = s->Global("_CH_REPORT");
auto v23806 = Value("ch_errors");
auto v23807 = Get(v23805, v23806);
Put(v23805, v23806, Inplace("Add", v23807, Value(int64_t{1})));
}
else { throw; }
}
return s->LocalAt(0);
return {};
}
}  // namespace kagg::opponents::compiled
