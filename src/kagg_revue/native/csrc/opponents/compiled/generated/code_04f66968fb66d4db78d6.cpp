// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_04f66968fb66d4db78d6(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "actor", "actual", "command", "crop", "day_end", "deadline", "farm", "future", "future_step", "intended", "native", "next_commands", "observation", "player", "positions", "private", "raw", "same_crop", "state", "step", "tape", "tile", "x", "y"};
s->PrepareSlots(s_names);
auto v15495 = ([&]() -> Value { auto fn15496 = s->Global("int"); Arguments args15497; args15497.Add(Get(s->LocalAt(13), Value("step")), false); return Call(c, fn15496, std::move(args15497)); }());
s->SetAt(20, v15495);
if (static_cast<bool>(([&]() -> Value { auto v15498 = ([&]() -> Value { auto v15499 = ([&]() -> Value { auto v15501 = s->LocalAt(20); return Binary("Mod", v15501, Value(int64_t{24})); }()); Value v15500; v15500 = Value(int64_t{20}); if (!static_cast<bool>(Binary("Gt", v15499, v15500))) return Value(false); v15499 = v15500; return Value(true); }()); if (static_cast<bool>(v15498)) return v15498; v15498 = ([&]() -> Value { auto fn15502 = PrepareDictionaryGet(s->LocalAt(19)); Arguments args15503; args15503.Add(Value("repair"), false); return CallDictionaryGet(c, fn15502, std::move(args15503)); }()); return v15498; }()))) {
return Value{};
}
auto v15504 = ([&]() -> Value { auto fn15505 = s->Global("int"); Arguments args15506; args15506.Add(Get(s->LocalAt(13), Value("player")), false); return Call(c, fn15505, std::move(args15506)); }());
s->SetAt(14, v15504);
auto v15507 = ([&]() -> Value { auto fn15508 = PrepareDictionaryGet(Attribute(Attribute(s->Global("_IMPL"), "chassis"), "players")); Arguments args15509; args15509.Add(s->LocalAt(14), false); return CallDictionaryGet(c, fn15508, std::move(args15509)); }());
s->SetAt(11, v15507);
if (static_cast<bool>(([&]() -> Value { auto v15510 = Unary("Not", s->LocalAt(11)); if (static_cast<bool>(v15510)) return v15510; v15510 = ([&]() -> Value { auto v15511 = ([&]() -> Value { auto fn15513 = PrepareDictionaryGet(s->LocalAt(11)); Arguments args15514; args15514.Add(Value("route"), false); return CallDictionaryGet(c, fn15513, std::move(args15514)); }()); Value v15512; v15512 = Attribute(Attribute(s->Global("_IMPL"), "chassis"), "routes"); if (!static_cast<bool>(Binary("NotIn", v15511, v15512))) return Value(false); v15511 = v15512; return Value(true); }()); return v15510; }()))) {
return Value{};
}
auto v15515 = Get(Attribute(Attribute(s->Global("_IMPL"), "chassis"), "routes"), Get(s->LocalAt(11), Value("route")));
s->SetAt(21, v15515);
if (static_cast<bool>(([&]() -> Value { auto v15516 = ([&]() -> Value { auto v15518 = s->LocalAt(20); return Binary("Add", v15518, Value(int64_t{2})); }()); Value v15517; v15517 = ([&]() -> Value { auto fn15519 = s->Global("len"); Arguments args15520; args15520.Add(s->LocalAt(21), false); return Call(c, fn15519, std::move(args15520)); }()); if (!static_cast<bool>(Binary("GtE", v15516, v15517))) return Value(false); v15516 = v15517; return Value(true); }()))) {
return Value{};
}
auto v15521 = ([&]() -> Value { auto fn15522 = s->Global("_r132_commands"); Arguments args15523; args15523.Add(Get(s->LocalAt(21), s->LocalAt(20)), false); return Call(c, fn15522, std::move(args15523)); }());
s->SetAt(17, v15521);
auto v15524 = ([&]() -> Value { auto fn15525 = s->Global("_r132_commands"); Arguments args15526; args15526.Add(s->LocalAt(0), false); return Call(c, fn15525, std::move(args15526)); }());
s->SetAt(2, v15524);
auto v15527 = Get(Get(s->LocalAt(13), Value("farms")), s->LocalAt(14));
s->SetAt(7, v15527);
auto v15528 = ([&]() -> Value { Arguments args15529; args15529.Add(Get(s->LocalAt(7), Value("farmer")), false); args15529.Add(Get(s->LocalAt(7), Value("hands")), true); return List(std::move(args15529.positional)); }());
s->SetAt(15, v15528);
auto v15530 = Get(s->LocalAt(13), Value("private"));
s->SetAt(16, v15530);
auto v15531 = ([&]() -> Value { auto fn15532 = s->Global("min"); Arguments args15533; args15533.positional.reserve(2); args15533.Add(([&]() -> Value { auto fn15534 = s->Global("len"); Arguments args15535; args15535.Add(s->LocalAt(21), false); return Call(c, fn15534, std::move(args15535)); }()), false); args15533.Add(([&]() -> Value { auto v15536 = ([&]() -> Value { auto v15537 = ([&]() -> Value { auto v15538 = s->LocalAt(20); return Binary("FloorDiv", v15538, Value(int64_t{24})); }()); return Binary("Add", v15537, Value(int64_t{1})); }()); return Binary("Mult", v15536, Value(int64_t{24})); }()), false); return Call(c, fn15532, std::move(args15533)); }());
s->SetAt(5, v15531);
for (const auto& item15539 : Iterate(([&]() -> Value { auto fn15540 = s->Global("enumerate"); Arguments args15541; args15541.Add(Slice(s->LocalAt(17), Value{}, ([&]() -> Value { auto fn15542 = s->Global("len"); Arguments args15543; args15543.Add(s->LocalAt(15), false); return Call(c, fn15542, std::move(args15543)); }()), Value{}), false); return Call(c, fn15540, std::move(args15541)); }()))) {
auto unpack15544 = Iterate(item15539);
ValidateUnpack(unpack15544, 2, false);
s->SetAt(1, unpack15544.at(0));
s->SetAt(10, unpack15544.at(1));
if (static_cast<bool>(([&]() -> Value { auto v15545 = ([&]() -> Value { auto v15546 = Slice(s->LocalAt(10), Value{}, Value(int64_t{1}), Value{}); Value v15547; v15547 = List({Value("PLANT")}); if (!static_cast<bool>(Binary("NotEq", v15546, v15547))) return Value(false); v15546 = v15547; return Value(true); }()); if (static_cast<bool>(v15545)) return v15545; v15545 = ([&]() -> Value { auto v15548 = s->LocalAt(1); Value v15549; v15549 = ([&]() -> Value { auto fn15550 = s->Global("len"); Arguments args15551; args15551.Add(s->LocalAt(2), false); return Call(c, fn15550, std::move(args15551)); }()); if (!static_cast<bool>(Binary("GtE", v15548, v15549))) return Value(false); v15548 = v15549; return Value(true); }()); if (static_cast<bool>(v15545)) return v15545; v15545 = ([&]() -> Value { auto v15552 = Get(s->LocalAt(2), s->LocalAt(1)); Value v15553; v15553 = List({Value("DIG")}); if (!static_cast<bool>(Binary("NotEq", v15552, v15553))) return Value(false); v15552 = v15553; return Value(true); }()); return v15545; }()))) {
continue;
}
auto v15554 = Get(s->LocalAt(15), s->LocalAt(1));
auto unpack15555 = Iterate(v15554);
ValidateUnpack(unpack15555, 2, false);
s->SetAt(23, unpack15555.at(0));
s->SetAt(24, unpack15555.at(1));
auto v15556 = Get(Get(Get(s->LocalAt(7), Value("tiles")), s->LocalAt(24)), s->LocalAt(23));
s->SetAt(22, v15556);
auto v15557 = Get(s->LocalAt(10), Value(int64_t{1}));
s->SetAt(4, v15557);
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto v15558 = ([&]() -> Value { auto fn15559 = s->Global("isinstance"); Arguments args15560; args15560.positional.reserve(2); args15560.Add(s->LocalAt(22), false); args15560.Add(s->Global("dict"), false); return Call(c, fn15559, std::move(args15560)); }()); if (!static_cast<bool>(v15558)) return v15558; v15558 = ([&]() -> Value { auto v15561 = ([&]() -> Value { auto fn15563 = PrepareDictionaryGet(s->LocalAt(22)); Arguments args15564; args15564.Add(Value("kind"), false); return CallDictionaryGet(c, fn15563, std::move(args15564)); }()); Value v15562; v15562 = Value("WEED"); if (!static_cast<bool>(Binary("Eq", v15561, v15562))) return Value(false); v15561 = v15562; return Value(true); }()); return v15558; }())))) {
continue;
}
auto v15565 = ([&]() -> Value { auto fn15566 = s->Global("sum"); Arguments args15567; args15567.Add(([&]() -> Value { auto comp15568 = std::make_shared<Scope>(); comp15568->globals = s->globals; comp15568->parent = s; static constexpr const char* comp15568_names[] = {"command"}; comp15568->PrepareSlots(comp15568_names); auto result15569 = List(); for (const auto& item15570 : Iterate(s->LocalAt(17))) { comp15568->SetAt(0, item15570); if (!static_cast<bool>(([&]() -> Value { auto v15571 = Slice(comp15568->LocalAt(0), Value{}, Value(int64_t{2}), Value{}); Value v15572; v15572 = List({Value("PLANT"), comp15568->Captured("crop")}); if (!static_cast<bool>(Binary("Eq", v15571, v15572))) return Value(false); v15571 = v15572; return Value(true); }()))) continue; result15569.node()->sequence.push_back(Value(int64_t{1})); } return result15569; }()), false); return Call(c, fn15566, std::move(args15567)); }());
s->SetAt(18, v15565);
if (static_cast<bool>(([&]() -> Value { auto v15573 = ([&]() -> Value { auto fn15575 = s->Global("int"); Arguments args15576; args15576.Add(([&]() -> Value { auto fn15577 = PrepareDictionaryGet(Get(s->LocalAt(16), Value("seeds"))); Arguments args15578; args15578.positional.reserve(2); args15578.Add(s->LocalAt(4), false); args15578.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn15577, std::move(args15578)); }()), false); return Call(c, fn15575, std::move(args15576)); }()); Value v15574; v15574 = s->LocalAt(18); if (!static_cast<bool>(Binary("Lt", v15573, v15574))) return Value(false); v15573 = v15574; return Value(true); }()))) {
continue;
}
auto v15579 = ([&]() -> Value { auto fn15580 = s->Global("_r132_commands"); Arguments args15581; args15581.Add(Get(s->LocalAt(21), ([&]() -> Value { auto v15582 = s->LocalAt(20); return Binary("Add", v15582, Value(int64_t{1})); }())), false); return Call(c, fn15580, std::move(args15581)); }());
s->SetAt(12, v15579);
if (static_cast<bool>(([&]() -> Value { auto v15583 = ([&]() -> Value { auto v15584 = s->LocalAt(1); Value v15585; v15585 = ([&]() -> Value { auto fn15586 = s->Global("len"); Arguments args15587; args15587.Add(s->LocalAt(12), false); return Call(c, fn15586, std::move(args15587)); }()); if (!static_cast<bool>(Binary("GtE", v15584, v15585))) return Value(false); v15584 = v15585; return Value(true); }()); if (static_cast<bool>(v15583)) return v15583; v15583 = ([&]() -> Value { auto v15588 = Get(s->LocalAt(12), s->LocalAt(1)); Value v15589; v15589 = List({Value("WATER")}); if (!static_cast<bool>(Binary("NotEq", v15588, v15589))) return Value(false); v15588 = v15589; return Value(true); }()); return v15583; }()))) {
continue;
}
auto v15590 = Value{};
s->SetAt(6, v15590);
for (const auto& item15591 : Iterate(([&]() -> Value { auto fn15592 = s->Global("range"); Arguments args15593; args15593.positional.reserve(2); args15593.Add(([&]() -> Value { auto v15594 = s->LocalAt(20); return Binary("Add", v15594, Value(int64_t{1})); }()), false); args15593.Add(s->LocalAt(5), false); return Call(c, fn15592, std::move(args15593)); }()))) {
s->SetAt(9, item15591);
auto v15595 = ([&]() -> Value { auto fn15596 = s->Global("_r132_commands"); Arguments args15597; args15597.Add(Get(s->LocalAt(21), s->LocalAt(9)), false); return Call(c, fn15596, std::move(args15597)); }());
s->SetAt(8, v15595);
auto v15598 = (static_cast<bool>(([&]() -> Value { auto v15599 = s->LocalAt(1); Value v15600; v15600 = ([&]() -> Value { auto fn15601 = s->Global("len"); Arguments args15602; args15602.Add(s->LocalAt(8), false); return Call(c, fn15601, std::move(args15602)); }()); if (!static_cast<bool>(Binary("Lt", v15599, v15600))) return Value(false); v15599 = v15600; return Value(true); }())) ? Get(s->LocalAt(8), s->LocalAt(1)) : List({Value("PASS")}));
s->SetAt(3, v15598);
if (static_cast<bool>(([&]() -> Value { auto v15603 = s->LocalAt(3); Value v15604; v15604 = List({Value("PASS")}); if (!static_cast<bool>(Binary("Eq", v15603, v15604))) return Value(false); v15603 = v15604; return Value(true); }()))) {
auto v15605 = s->LocalAt(9);
s->SetAt(6, v15605);
break;
}
}
if (static_cast<bool>(([&]() -> Value { auto v15606 = s->LocalAt(6); Value v15607; v15607 = Value{}; if (!static_cast<bool>(Binary("Is", v15606, v15607))) return Value(false); v15606 = v15607; return Value(true); }()))) {
continue;
}
auto v15608 = ([&]() -> Value { auto dict15609 = Dict(); auto key15610 = Value("actor"); Put(dict15609, key15610, s->LocalAt(1)); auto key15611 = Value("queue"); Put(dict15609, key15611, List({([&]() -> Value { auto fn15612 = s->Global("list"); Arguments args15613; args15613.Add(s->LocalAt(10), false); return Call(c, fn15612, std::move(args15613)); }())})); auto key15614 = Value("next_step"); Put(dict15609, key15614, ([&]() -> Value { auto v15615 = s->LocalAt(20); return Binary("Add", v15615, Value(int64_t{1})); }())); auto key15616 = Value("deadline"); Put(dict15609, key15616, s->LocalAt(6)); auto key15617 = Value("route"); Put(dict15609, key15617, Get(s->LocalAt(11), Value("route"))); return dict15609; }());
Put(s->LocalAt(19), Value("repair"), v15608);
auto v15618 = s->Global("_R132_REPORT");
auto v15619 = Value("weed_repair_started");
auto v15620 = Get(v15618, v15619);
Put(v15618, v15619, Inplace("Add", v15620, Value(int64_t{1})));
return Value{};
}
return {};
}
}  // namespace kagg::opponents::compiled
