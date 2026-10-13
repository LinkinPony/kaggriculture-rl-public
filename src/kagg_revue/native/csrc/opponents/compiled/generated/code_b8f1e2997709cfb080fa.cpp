// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_b8f1e2997709cfb080fa(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"_", "access", "actor", "cargo", "command", "day", "distance", "farm", "home", "hungry", "inv", "obs", "pos", "private", "producing_tonight", "step", "target", "targets", "tasks", "tile", "x", "y"};
s->PrepareSlots(s_names);
auto v26396 = ([&]() -> Value { auto fn26397 = s->Global("int"); Arguments args26398; args26398.Add(Get(s->LocalAt(11), Value("step")), false); return Call(c, fn26397, std::move(args26398)); }());
s->SetAt(15, v26396);
auto v26399 = ([&]() -> Value { auto v26400 = s->LocalAt(15); return Binary("FloorDiv", v26400, Value(int64_t{24})); }());
s->SetAt(5, v26399);
if (static_cast<bool>(([&]() -> Value { auto v26401 = Unary("Not", s->Global("_E343_YX_END")); if (static_cast<bool>(v26401)) return v26401; v26401 = ([&]() -> Value { auto v26402 = s->LocalAt(5); Value v26403; v26403 = Value(int64_t{28}); if (!static_cast<bool>(Binary("Lt", v26402, v26403))) return Value(false); v26402 = v26403; return Value(true); }()); return v26401; }()))) {
return ([&]() -> Value { auto fn26404 = s->Global("_E343_YX_ORIG_WORKER"); Arguments args26405; args26405.positional.reserve(3); args26405.Add(s->LocalAt(11), false); args26405.Add(s->LocalAt(2), false); args26405.Add(s->LocalAt(17), false); return Call(c, fn26404, std::move(args26405)); }());
}
auto v26406 = Get(Get(s->LocalAt(11), Value("farms")), Get(s->LocalAt(11), Value("player")));
s->SetAt(7, v26406);
auto v26407 = Get(s->LocalAt(11), Value("private"));
s->SetAt(13, v26407);
auto v26408 = ([&]() -> Value { auto fn26409 = s->Global("tuple"); Arguments args26410; args26410.Add(Get(Get(s->LocalAt(7), Value("hands")), ([&]() -> Value { auto v26411 = s->LocalAt(2); return Binary("Sub", v26411, Value(int64_t{1})); }())), false); return Call(c, fn26409, std::move(args26410)); }());
s->SetAt(12, v26408);
auto v26412 = Get(Get(s->LocalAt(13), Value("inventories")), s->LocalAt(2));
s->SetAt(10, v26412);
auto v26413 = Tuple({Tuple({Value(int64_t{4}), Value(int64_t{4})}), Tuple({Value(int64_t{5}), Value(int64_t{4})}), Tuple({Value(int64_t{4}), Value(int64_t{5})}), Tuple({Value(int64_t{5}), Value(int64_t{5})})});
s->SetAt(1, v26413);
auto v26414 = ([&]() -> Value { auto fn26415 = s->Global("min"); Arguments args26416; args26416.Add(s->LocalAt(1), false); args26416.Keyword("key", Define(&Code_b722cb8fcb19df79be89, s, Signature{{"p"}, {}, {}, {}, "", "", ([]() -> std::span<const char* const> { static constexpr const char* names[] = {"p"}; return names; }())}, true, "<lambda>")); return Call(c, fn26415, std::move(args26416)); }());
s->SetAt(8, v26414);
auto v26424 = ([&]() -> Value { auto v26425 = ([&]() -> Value { auto fn26426 = s->Global("abs"); Arguments args26427; args26427.Add(([&]() -> Value { auto v26428 = Get(s->LocalAt(12), Value(int64_t{0})); return Binary("Sub", v26428, Get(s->LocalAt(8), Value(int64_t{0}))); }()), false); return Call(c, fn26426, std::move(args26427)); }()); return Binary("Add", v26425, ([&]() -> Value { auto fn26429 = s->Global("abs"); Arguments args26430; args26430.Add(([&]() -> Value { auto v26431 = Get(s->LocalAt(12), Value(int64_t{1})); return Binary("Sub", v26431, Get(s->LocalAt(8), Value(int64_t{1}))); }()), false); return Call(c, fn26429, std::move(args26430)); }())); }());
s->SetAt(6, v26424);
auto v26432 = ([&]() -> Value { auto comp26433 = std::make_shared<Scope>(); comp26433->globals = s->globals; comp26433->parent = s; static constexpr const char* comp26433_names[] = {"item"}; comp26433->PrepareSlots(comp26433_names); auto result26434 = List(); for (const auto& item26435 : Iterate(Tuple({Value("WOOL"), Value("FERTILIZER")}))) { comp26433->SetAt(0, item26435); if (!static_cast<bool>(([&]() -> Value { auto fn26436 = PrepareDictionaryGet(comp26433->Captured("inv")); Arguments args26437; args26437.positional.reserve(2); args26437.Add(comp26433->LocalAt(0), false); args26437.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn26436, std::move(args26437)); }()))) continue; result26434.node()->sequence.push_back(comp26433->LocalAt(0)); } return result26434; }());
s->SetAt(3, v26432);
if (static_cast<bool>(([&]() -> Value { auto v26438 = s->LocalAt(3); if (!static_cast<bool>(v26438)) return v26438; v26438 = ([&]() -> Value { auto v26439 = ([&]() -> Value { auto v26441 = s->LocalAt(15); return Binary("Mod", v26441, Value(int64_t{24})); }()); Value v26440; v26440 = ([&]() -> Value { auto v26442 = (static_cast<bool>(([&]() -> Value { auto v26443 = s->LocalAt(5); Value v26444; v26444 = Value(int64_t{29}); if (!static_cast<bool>(Binary("Eq", v26443, v26444))) return Value(false); v26443 = v26444; return Value(true); }())) ? Value(int64_t{22}) : Value(int64_t{23})); return Binary("Sub", v26442, s->LocalAt(6)); }()); if (!static_cast<bool>(Binary("GtE", v26439, v26440))) return Value(false); v26439 = v26440; return Value(true); }()); return v26438; }()))) {
return ([&]() -> Value { auto v26445 = ([&]() -> Value { auto fn26446 = s->Global("_v219_walk"); Arguments args26447; args26447.positional.reserve(2); args26447.Add(s->LocalAt(12), false); args26447.Add(s->LocalAt(8), false); return Call(c, fn26446, std::move(args26447)); }()); if (static_cast<bool>(v26445)) return v26445; v26445 = List({Value("PLACE"), Get(s->LocalAt(3), Value(int64_t{0})), Get(s->LocalAt(10), Get(s->LocalAt(3), Value(int64_t{0})))}); return v26445; }());
}
s->SetAt(14, Define(&Code_5167e6dcd8767b747dd5, s, Signature{{"t"}, {}, {}, {}, "", "", ([]() -> std::span<const char* const> { static constexpr const char* names[] = {"dsf", "t"}; return names; }())}, true, "producing_tonight"));
s->definitions.push_back("producing_tonight");
if (static_cast<bool>(([&]() -> Value { auto v26462 = s->LocalAt(5); Value v26463; v26463 = Value(int64_t{29}); if (!static_cast<bool>(Binary("Lt", v26462, v26463))) return Value(false); v26462 = v26463; return Value(true); }()))) {
auto v26464 = ([&]() -> Value { auto fn26465 = s->Global("sum"); Arguments args26466; args26466.Add(([&]() -> Value { auto comp26467 = std::make_shared<Scope>(); comp26467->globals = s->globals; comp26467->parent = s; static constexpr const char* comp26467_names[] = {"x", "y"}; comp26467->PrepareSlots(comp26467_names); auto result26468 = List(); for (const auto& item26469 : Iterate(s->LocalAt(17))) { auto unpack26470 = Iterate(item26469); ValidateUnpack(unpack26470, 2, false); comp26467->SetAt(0, unpack26470.at(0)); comp26467->SetAt(1, unpack26470.at(1)); result26468.node()->sequence.push_back(([&]() -> Value { auto v26471 = ([&]() -> Value { auto fn26472 = comp26467->Global("isinstance"); Arguments args26473; args26473.positional.reserve(2); args26473.Add(Get(Get(Get(comp26467->Captured("farm"), Value("tiles")), comp26467->LocalAt(1)), comp26467->LocalAt(0)), false); args26473.Add(comp26467->Global("dict"), false); return Call(c, fn26472, std::move(args26473)); }()); if (!static_cast<bool>(v26471)) return v26471; v26471 = ([&]() -> Value { auto v26474 = ([&]() -> Value { auto fn26476 = PrepareDictionaryGet(Get(Get(Get(comp26467->Captured("farm"), Value("tiles")), comp26467->LocalAt(1)), comp26467->LocalAt(0))); Arguments args26477; args26477.Add(Value("animal"), false); return CallDictionaryGet(c, fn26476, std::move(args26477)); }()); Value v26475; v26475 = Value("SHEEP"); if (!static_cast<bool>(Binary("Eq", v26474, v26475))) return Value(false); v26474 = v26475; return Value(true); }()); if (!static_cast<bool>(v26471)) return v26471; v26471 = Unary("Not", ([&]() -> Value { auto fn26478 = PrepareDictionaryGet(Get(Get(Get(comp26467->Captured("farm"), Value("tiles")), comp26467->LocalAt(1)), comp26467->LocalAt(0))); Arguments args26479; args26479.Add(Value("fed_today"), false); return CallDictionaryGet(c, fn26478, std::move(args26479)); }())); if (!static_cast<bool>(v26471)) return v26471; v26471 = ([&]() -> Value { auto v26480 = ([&]() -> Value { auto fn26481 = comp26467->Captured("producing_tonight"); Arguments args26482; args26482.Add(Get(Get(Get(comp26467->Captured("farm"), Value("tiles")), comp26467->LocalAt(1)), comp26467->LocalAt(0)), false); return Call(c, fn26481, std::move(args26482)); }()); if (static_cast<bool>(v26480)) return v26480; v26480 = ([&]() -> Value { auto v26483 = ([&]() -> Value { auto fn26485 = comp26467->Global("int"); Arguments args26486; args26486.Add(([&]() -> Value { auto fn26487 = PrepareDictionaryGet(Get(Get(Get(comp26467->Captured("farm"), Value("tiles")), comp26467->LocalAt(1)), comp26467->LocalAt(0))); Arguments args26488; args26488.positional.reserve(2); args26488.Add(Value("consecutive_unfed"), false); args26488.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn26487, std::move(args26488)); }()), false); return Call(c, fn26485, std::move(args26486)); }()); Value v26484; v26484 = Value(int64_t{1}); if (!static_cast<bool>(Binary("GtE", v26483, v26484))) return Value(false); v26483 = v26484; return Value(true); }()); return v26480; }()); return v26471; }())); } return result26468; }()), false); return Call(c, fn26465, std::move(args26466)); }());
s->SetAt(9, v26464);
if (static_cast<bool>(([&]() -> Value { auto v26489 = s->LocalAt(9); if (!static_cast<bool>(v26489)) return v26489; v26489 = Unary("Not", ([&]() -> Value { auto fn26490 = PrepareDictionaryGet(s->LocalAt(10)); Arguments args26491; args26491.positional.reserve(2); args26491.Add(Value("WHEAT"), false); args26491.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn26490, std::move(args26491)); }())); if (!static_cast<bool>(v26489)) return v26489; v26489 = ([&]() -> Value { auto fn26492 = PrepareDictionaryGet(Get(s->LocalAt(13), Value("shed"))); Arguments args26493; args26493.positional.reserve(2); args26493.Add(Value("WHEAT"), false); args26493.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn26492, std::move(args26493)); }()); return v26489; }()))) {
return ([&]() -> Value { auto v26494 = ([&]() -> Value { auto fn26495 = s->Global("_v219_walk"); Arguments args26496; args26496.positional.reserve(2); args26496.Add(s->LocalAt(12), false); args26496.Add(s->LocalAt(8), false); return Call(c, fn26495, std::move(args26496)); }()); if (static_cast<bool>(v26494)) return v26494; v26494 = List({Value("PICKUP"), Value("WHEAT"), ([&]() -> Value { auto fn26497 = s->Global("min"); Arguments args26498; args26498.positional.reserve(2); args26498.Add(s->LocalAt(9), false); args26498.Add(Get(Get(s->LocalAt(13), Value("shed")), Value("WHEAT")), false); return Call(c, fn26497, std::move(args26498)); }())}); return v26494; }());
}
}
auto v26499 = List({});
s->SetAt(18, v26499);
for (const auto& item26500 : Iterate(s->LocalAt(17))) {
s->SetAt(16, item26500);
auto v26501 = s->LocalAt(16);
auto unpack26502 = Iterate(v26501);
ValidateUnpack(unpack26502, 2, false);
s->SetAt(20, unpack26502.at(0));
s->SetAt(21, unpack26502.at(1));
auto v26503 = Get(Get(Get(s->LocalAt(7), Value("tiles")), s->LocalAt(21)), s->LocalAt(20));
s->SetAt(19, v26503);
auto v26504 = Value{};
s->SetAt(4, v26504);
if (static_cast<bool>(([&]() -> Value { auto v26505 = ([&]() -> Value { auto fn26506 = s->Global("isinstance"); Arguments args26507; args26507.positional.reserve(2); args26507.Add(s->LocalAt(19), false); args26507.Add(s->Global("dict"), false); return Call(c, fn26506, std::move(args26507)); }()); if (!static_cast<bool>(v26505)) return v26505; v26505 = ([&]() -> Value { auto v26508 = ([&]() -> Value { auto fn26510 = PrepareDictionaryGet(s->LocalAt(19)); Arguments args26511; args26511.Add(Value("animal"), false); return CallDictionaryGet(c, fn26510, std::move(args26511)); }()); Value v26509; v26509 = Value("SHEEP"); if (!static_cast<bool>(Binary("Eq", v26508, v26509))) return Value(false); v26508 = v26509; return Value(true); }()); return v26505; }()))) {
if (static_cast<bool>(([&]() -> Value { auto v26512 = ([&]() -> Value { auto v26513 = s->LocalAt(5); Value v26514; v26514 = Value(int64_t{29}); if (!static_cast<bool>(Binary("Lt", v26513, v26514))) return Value(false); v26513 = v26514; return Value(true); }()); if (!static_cast<bool>(v26512)) return v26512; v26512 = Unary("Not", Get(s->LocalAt(19), Value("fed_today"))); if (!static_cast<bool>(v26512)) return v26512; v26512 = ([&]() -> Value { auto v26515 = ([&]() -> Value { auto fn26516 = s->LocalAt(14); Arguments args26517; args26517.Add(s->LocalAt(19), false); return Call(c, fn26516, std::move(args26517)); }()); if (static_cast<bool>(v26515)) return v26515; v26515 = ([&]() -> Value { auto v26518 = ([&]() -> Value { auto fn26520 = s->Global("int"); Arguments args26521; args26521.Add(([&]() -> Value { auto fn26522 = PrepareDictionaryGet(s->LocalAt(19)); Arguments args26523; args26523.positional.reserve(2); args26523.Add(Value("consecutive_unfed"), false); args26523.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn26522, std::move(args26523)); }()), false); return Call(c, fn26520, std::move(args26521)); }()); Value v26519; v26519 = Value(int64_t{1}); if (!static_cast<bool>(Binary("GtE", v26518, v26519))) return Value(false); v26518 = v26519; return Value(true); }()); return v26515; }()); if (!static_cast<bool>(v26512)) return v26512; v26512 = ([&]() -> Value { auto fn26524 = PrepareDictionaryGet(s->LocalAt(10)); Arguments args26525; args26525.positional.reserve(2); args26525.Add(Value("WHEAT"), false); args26525.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn26524, std::move(args26525)); }()); return v26512; }()))) {
auto v26526 = List({Value("FEED")});
s->SetAt(4, v26526);
}
else {
if (static_cast<bool>(Get(s->LocalAt(19), Value("yield_units")))) {
auto v26527 = List({Value("HARVEST")});
s->SetAt(4, v26527);
}
else {
if (static_cast<bool>(Get(s->LocalAt(19), Value("fertilizer_available")))) {
auto v26528 = List({Value("COLLECT_FERTILIZER")});
s->SetAt(4, v26528);
}
else {
if (static_cast<bool>(([&]() -> Value { auto v26529 = Unary("Not", Get(s->LocalAt(19), Value("fed_today"))); if (!static_cast<bool>(v26529)) return v26529; v26529 = ([&]() -> Value { auto v26530 = s->LocalAt(5); Value v26531; v26531 = Value(int64_t{29}); if (!static_cast<bool>(Binary("Lt", v26530, v26531))) return Value(false); v26530 = v26531; return Value(true); }()); if (!static_cast<bool>(v26529)) return v26529; v26529 = Unary("Not", ([&]() -> Value { auto fn26532 = s->LocalAt(14); Arguments args26533; args26533.Add(s->LocalAt(19), false); return Call(c, fn26532, std::move(args26533)); }())); return v26529; }()))) {
auto v26534 = s->Global("_E343_YX_REPORT");
auto v26535 = Value("yx_feed_skips");
auto v26536 = Get(v26534, v26535);
Put(v26534, v26535, Inplace("Add", v26536, Value(int64_t{1})));
}
}
}
}
if (static_cast<bool>(([&]() -> Value { auto v26537 = Unary("Not", ([&]() -> Value { auto fn26538 = PrepareDictionaryGet(s->LocalAt(19)); Arguments args26539; args26539.Add(Value("cared_today"), false); return CallDictionaryGet(c, fn26538, std::move(args26539)); }())); if (!static_cast<bool>(v26537)) return v26537; v26537 = ([&]() -> Value { auto v26540 = s->LocalAt(4); Value v26541; v26541 = Value{}; if (!static_cast<bool>(Binary("Is", v26540, v26541))) return Value(false); v26540 = v26541; return Value(true); }()); return v26537; }()))) {
auto v26542 = s->Global("_E343_YX_REPORT");
auto v26543 = Value("yx_care_skips");
auto v26544 = Get(v26542, v26543);
Put(v26542, v26543, Inplace("Add", v26544, Value(int64_t{1})));
}
}
if (static_cast<bool>(s->LocalAt(4))) {
(void)([&]() -> Value { auto fn26545 = Attribute(s->LocalAt(18), "append"); Arguments args26546; args26546.Add(Tuple({([&]() -> Value { auto v26547 = ([&]() -> Value { auto fn26548 = s->Global("abs"); Arguments args26549; args26549.Add(([&]() -> Value { auto v26550 = Get(s->LocalAt(12), Value(int64_t{0})); return Binary("Sub", v26550, s->LocalAt(20)); }()), false); return Call(c, fn26548, std::move(args26549)); }()); return Binary("Add", v26547, ([&]() -> Value { auto fn26551 = s->Global("abs"); Arguments args26552; args26552.Add(([&]() -> Value { auto v26553 = Get(s->LocalAt(12), Value(int64_t{1})); return Binary("Sub", v26553, s->LocalAt(21)); }()), false); return Call(c, fn26551, std::move(args26552)); }())); }()), ([&]() -> Value { auto fn26554 = Attribute(s->LocalAt(17), "index"); Arguments args26555; args26555.Add(s->LocalAt(16), false); return Call(c, fn26554, std::move(args26555)); }()), s->LocalAt(16), s->LocalAt(4)}), false); return Call(c, fn26545, std::move(args26546)); }());
}
}
if (static_cast<bool>(s->LocalAt(18))) {
auto v26556 = ([&]() -> Value { auto fn26557 = s->Global("min"); Arguments args26558; args26558.Add(s->LocalAt(18), false); return Call(c, fn26557, std::move(args26558)); }());
auto unpack26559 = Iterate(v26556);
ValidateUnpack(unpack26559, 4, false);
s->SetAt(0, unpack26559.at(0));
s->SetAt(0, unpack26559.at(1));
s->SetAt(16, unpack26559.at(2));
s->SetAt(4, unpack26559.at(3));
return ([&]() -> Value { auto v26560 = ([&]() -> Value { auto fn26561 = s->Global("_v219_walk"); Arguments args26562; args26562.positional.reserve(2); args26562.Add(s->LocalAt(12), false); args26562.Add(s->LocalAt(16), false); return Call(c, fn26561, std::move(args26562)); }()); if (static_cast<bool>(v26560)) return v26560; v26560 = s->LocalAt(4); return v26560; }());
}
if (static_cast<bool>(s->LocalAt(3))) {
return ([&]() -> Value { auto v26563 = ([&]() -> Value { auto fn26564 = s->Global("_v219_walk"); Arguments args26565; args26565.positional.reserve(2); args26565.Add(s->LocalAt(12), false); args26565.Add(s->LocalAt(8), false); return Call(c, fn26564, std::move(args26565)); }()); if (static_cast<bool>(v26563)) return v26563; v26563 = List({Value("PLACE"), Get(s->LocalAt(3), Value(int64_t{0})), Get(s->LocalAt(10), Get(s->LocalAt(3), Value(int64_t{0})))}); return v26563; }());
}
return List({Value("PASS")});
return {};
}
}  // namespace kagg::opponents::compiled
