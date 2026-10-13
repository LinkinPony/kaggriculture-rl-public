// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_2d4fea6e6f05d7011b47(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"best", "c", "draw", "evs", "f", "hit", "i", "index", "inv", "item", "m", "near", "obs", "player", "prev", "race", "rescan", "score", "seen", "sold", "st", "step", "tau", "touched"};
s->PrepareSlots(s_names);
auto v29506 = Tuple({([&]() -> Value { auto fn29507 = s->Global("int"); Arguments args29508; args29508.Add(Get(s->LocalAt(12), Value("player")), false); return Call(c, fn29507, std::move(args29508)); }()), ([&]() -> Value { auto fn29509 = s->Global("int"); Arguments args29510; args29510.Add(Get(s->LocalAt(12), Value("step")), false); return Call(c, fn29509, std::move(args29510)); }())});
auto unpack29511 = Iterate(v29506);
ValidateUnpack(unpack29511, 2, false);
s->SetAt(13, unpack29511.at(0));
s->SetAt(21, unpack29511.at(1));
auto v29512 = ([&]() -> Value { auto v29513 = ([&]() -> Value { auto fn29514 = PrepareDictionaryGet(s->Global("_V9_RACE")); Arguments args29515; args29515.Add(s->LocalAt(13), false); return CallDictionaryGet(c, fn29514, std::move(args29515)); }()); if (static_cast<bool>(v29513)) return v29513; v29513 = ([&]() -> Value { auto dict29516 = Dict(); return dict29516; }()); return v29513; }());
s->SetAt(15, v29512);
auto v29517 = ([&]() -> Value { auto fn29518 = PrepareDictionaryGet(s->LocalAt(15)); Arguments args29519; args29519.Add(Value("prev"), false); return CallDictionaryGet(c, fn29518, std::move(args29519)); }());
s->SetAt(14, v29517);
auto v29520 = Get(s->LocalAt(20), Value("obs"));
s->SetAt(18, v29520);
if (static_cast<bool>(([&]() -> Value { auto v29521 = s->LocalAt(14); if (!static_cast<bool>(v29521)) return v29521; v29521 = ([&]() -> Value { auto v29522 = Get(s->LocalAt(14), Value("step")); Value v29523; v29523 = ([&]() -> Value { auto v29524 = s->LocalAt(21); return Binary("Sub", v29524, Value(int64_t{1})); }()); if (!static_cast<bool>(Binary("Eq", v29522, v29523))) return Value(false); v29522 = v29523; return Value(true); }()); return v29521; }()))) {
auto v29525 = Get(Get(s->LocalAt(12), Value("market")), Value("inventory"));
s->SetAt(8, v29525);
auto v29526 = ([&]() -> Value { auto fn29527 = s->Global("_v9_town_draw"); Arguments args29528; args29528.positional.reserve(2); args29528.Add(Get(s->LocalAt(14), Value("shops")), false); args29528.Add(Get(s->LocalAt(14), Value("step")), false); return Call(c, fn29527, std::move(args29528)); }());
s->SetAt(2, v29526);
for (const auto& item29529 : Iterate(([&]() -> Value { auto fn29530 = s->Global("enumerate"); Arguments args29531; args29531.Add(s->Global("_V92_Q_ITEMS"), false); return Call(c, fn29530, std::move(args29531)); }()))) {
auto unpack29532 = Iterate(item29529);
ValidateUnpack(unpack29532, 2, false);
s->SetAt(6, unpack29532.at(0));
s->SetAt(9, unpack29532.at(1));
if (static_cast<bool>(([&]() -> Value { auto v29533 = ([&]() -> Value { auto fn29535 = PrepareDictionaryGet(Get(s->LocalAt(14), Value("prices"))); Arguments args29536; args29536.positional.reserve(2); args29536.Add(s->LocalAt(9), false); args29536.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn29535, std::move(args29536)); }()); Value v29534; v29534 = Value(int64_t{3}); if (!static_cast<bool>(Binary("LtE", v29533, v29534))) return Value(false); v29533 = v29534; return Value(true); }()))) {
continue;
}
auto v29537 = ([&]() -> Value { auto v29538 = ([&]() -> Value { auto v29539 = ([&]() -> Value { auto v29540 = Get(s->LocalAt(8), s->LocalAt(9)); return Binary("Sub", v29540, Get(Get(s->LocalAt(14), Value("inventory")), s->LocalAt(9))); }()); return Binary("Add", v29539, ([&]() -> Value { auto fn29541 = PrepareDictionaryGet(s->LocalAt(2)); Arguments args29542; args29542.positional.reserve(2); args29542.Add(s->LocalAt(9), false); args29542.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn29541, std::move(args29542)); }())); }()); return Binary("Sub", v29538, ([&]() -> Value { auto fn29543 = PrepareDictionaryGet(Get(s->LocalAt(14), Value("own"))); Arguments args29544; args29544.positional.reserve(2); args29544.Add(s->LocalAt(9), false); args29544.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn29543, std::move(args29544)); }())); }());
s->SetAt(19, v29537);
if (static_cast<bool>(([&]() -> Value { auto v29545 = s->LocalAt(19); Value v29546; v29546 = Value(int64_t{2}); if (!static_cast<bool>(Binary("GtE", v29545, v29546))) return Value(false); v29545 = v29546; return Value(true); }()))) {
auto v29547 = s->LocalAt(19);
Put(s->LocalAt(18), Tuple({([&]() -> Value { auto v29548 = s->LocalAt(21); return Binary("Sub", v29548, Value(int64_t{1})); }()), s->LocalAt(6)}), v29547);
}
}
}
auto v29549 = Tuple({Get(s->LocalAt(20), Value("evs")), Get(s->LocalAt(20), Value("index"))});
auto unpack29550 = Iterate(v29549);
ValidateUnpack(unpack29550, 2, false);
s->SetAt(3, unpack29550.at(0));
s->SetAt(7, unpack29550.at(1));
if (static_cast<bool>(Unary("Not", s->LocalAt(3)))) {
return Value{};
}
auto v29551 = Tuple({Get(s->LocalAt(20), Value("m")), Get(s->LocalAt(20), Value("f")), Get(s->LocalAt(20), Value("near")), Get(s->LocalAt(20), Value("score"))});
auto unpack29552 = Iterate(v29551);
ValidateUnpack(unpack29552, 4, false);
s->SetAt(10, unpack29552.at(0));
s->SetAt(4, unpack29552.at(1));
s->SetAt(11, unpack29552.at(2));
s->SetAt(17, unpack29552.at(3));
auto v29553 = Get(s->LocalAt(20), Value("best"));
s->SetAt(0, v29553);
auto v29554 = Value(false);
s->SetAt(16, v29554);
while (static_cast<bool>(([&]() -> Value { auto v29555 = Get(s->LocalAt(20), Value("done")); Value v29556; v29556 = ([&]() -> Value { auto v29557 = s->LocalAt(21); return Binary("Sub", v29557, Value(int64_t{2})); }()); if (!static_cast<bool>(Binary("LtE", v29555, v29556))) return Value(false); v29555 = v29556; return Value(true); }()))) {
auto v29558 = Get(s->LocalAt(20), Value("done"));
s->SetAt(22, v29558);
auto v29559 = s->LocalAt(20);
auto v29560 = Value("done");
auto v29561 = Get(v29559, v29560);
Put(v29559, v29560, Inplace("Add", v29561, Value(int64_t{1})));
for (const auto& item29562 : Iterate(([&]() -> Value { auto fn29563 = s->Global("range"); Arguments args29564; args29564.Add(Value(int64_t{3}), false); return Call(c, fn29563, std::move(args29564)); }()))) {
s->SetAt(6, item29562);
auto v29565 = ([&]() -> Value { auto v29566 = ([&]() -> Value { auto v29567 = Tuple({s->LocalAt(22), s->LocalAt(6)}); Value v29568; v29568 = s->LocalAt(18); if (!static_cast<bool>(Binary("In", v29567, v29568))) return Value(false); v29567 = v29568; return Value(true); }()); if (static_cast<bool>(v29566)) return v29566; v29566 = ([&]() -> Value { auto v29569 = Tuple({([&]() -> Value { auto v29571 = s->LocalAt(22); return Binary("Sub", v29571, Value(int64_t{1})); }()), s->LocalAt(6)}); Value v29570; v29570 = s->LocalAt(18); if (!static_cast<bool>(Binary("In", v29569, v29570))) return Value(false); v29569 = v29570; return Value(true); }()); if (static_cast<bool>(v29566)) return v29566; v29566 = ([&]() -> Value { auto v29572 = Tuple({([&]() -> Value { auto v29574 = s->LocalAt(22); return Binary("Add", v29574, Value(int64_t{1})); }()), s->LocalAt(6)}); Value v29573; v29573 = s->LocalAt(18); if (!static_cast<bool>(Binary("In", v29572, v29573))) return Value(false); v29572 = v29573; return Value(true); }()); return v29566; }());
s->SetAt(5, v29565);
for (const auto& item29575 : Iterate(([&]() -> Value { auto fn29576 = PrepareDictionaryGet(s->LocalAt(7)); Arguments args29577; args29577.positional.reserve(2); args29577.Add(Tuple({s->LocalAt(22), s->LocalAt(6)}), false); args29577.Add(Tuple({}), false); return CallDictionaryGet(c, fn29576, std::move(args29577)); }()))) {
s->SetAt(1, item29575);
if (static_cast<bool>(s->LocalAt(5))) {
auto v29578 = s->LocalAt(10);
auto v29579 = s->LocalAt(1);
auto v29580 = Get(v29578, v29579);
Put(v29578, v29579, Inplace("Add", v29580, Value(int64_t{1})));
auto v29581 = s->LocalAt(17);
auto v29582 = s->LocalAt(1);
auto v29583 = Get(v29581, v29582);
Put(v29581, v29582, Inplace("Add", v29583, Value(1.0)));
}
else {
auto v29584 = s->LocalAt(4);
auto v29585 = s->LocalAt(1);
auto v29586 = Get(v29584, v29585);
Put(v29584, v29585, Inplace("Add", v29586, Value(int64_t{1})));
auto v29587 = s->LocalAt(17);
auto v29588 = s->LocalAt(1);
auto v29589 = Get(v29587, v29588);
Put(v29587, v29588, Inplace("Sub", v29589, s->Global("_V92_Q_PF")));
if (static_cast<bool>(([&]() -> Value { auto v29590 = s->LocalAt(1); Value v29591; v29591 = s->LocalAt(0); if (!static_cast<bool>(Binary("Eq", v29590, v29591))) return Value(false); v29590 = v29591; return Value(true); }()))) {
auto v29592 = Value(true);
s->SetAt(16, v29592);
}
}
}
if (static_cast<bool>(([&]() -> Value { auto v29593 = Tuple({s->LocalAt(22), s->LocalAt(6)}); Value v29594; v29594 = s->LocalAt(18); if (!static_cast<bool>(Binary("In", v29593, v29594))) return Value(false); v29593 = v29594; return Value(true); }()))) {
auto v29595 = ([&]() -> Value { auto v29596 = ([&]() -> Value { auto v29597 = ([&]() -> Value { auto fn29598 = s->Global("set"); Arguments args29599; args29599.Add(([&]() -> Value { auto fn29600 = PrepareDictionaryGet(s->LocalAt(7)); Arguments args29601; args29601.positional.reserve(2); args29601.Add(Tuple({([&]() -> Value { auto v29602 = s->LocalAt(22); return Binary("Sub", v29602, Value(int64_t{1})); }()), s->LocalAt(6)}), false); args29601.Add(Tuple({}), false); return CallDictionaryGet(c, fn29600, std::move(args29601)); }()), false); return Call(c, fn29598, std::move(args29599)); }()); return Binary("BitOr", v29597, ([&]() -> Value { auto fn29603 = s->Global("set"); Arguments args29604; args29604.Add(([&]() -> Value { auto fn29605 = PrepareDictionaryGet(s->LocalAt(7)); Arguments args29606; args29606.positional.reserve(2); args29606.Add(Tuple({s->LocalAt(22), s->LocalAt(6)}), false); args29606.Add(Tuple({}), false); return CallDictionaryGet(c, fn29605, std::move(args29606)); }()), false); return Call(c, fn29603, std::move(args29604)); }())); }()); return Binary("BitOr", v29596, ([&]() -> Value { auto fn29607 = s->Global("set"); Arguments args29608; args29608.Add(([&]() -> Value { auto fn29609 = PrepareDictionaryGet(s->LocalAt(7)); Arguments args29610; args29610.positional.reserve(2); args29610.Add(Tuple({([&]() -> Value { auto v29611 = s->LocalAt(22); return Binary("Add", v29611, Value(int64_t{1})); }()), s->LocalAt(6)}), false); args29610.Add(Tuple({}), false); return CallDictionaryGet(c, fn29609, std::move(args29610)); }()), false); return Call(c, fn29607, std::move(args29608)); }())); }());
s->SetAt(23, v29595);
for (const auto& item29612 : Iterate(s->LocalAt(23))) {
s->SetAt(1, item29612);
auto v29613 = s->LocalAt(11);
auto v29614 = s->LocalAt(1);
auto v29615 = Get(v29613, v29614);
Put(v29613, v29614, Inplace("Add", v29615, Value(int64_t{1})));
auto v29616 = s->LocalAt(17);
auto v29617 = s->LocalAt(1);
auto v29618 = Get(v29616, v29617);
Put(v29616, v29617, Inplace("Add", v29618, s->Global("_V92_Q_PM")));
if (static_cast<bool>(([&]() -> Value { auto v29619 = Get(s->LocalAt(17), s->LocalAt(1)); Value v29620; v29620 = Get(s->LocalAt(17), s->LocalAt(0)); if (!static_cast<bool>(Binary("Gt", v29619, v29620))) return Value(false); v29619 = v29620; return Value(true); }()))) {
auto v29621 = s->LocalAt(1);
s->SetAt(0, v29621);
}
}
}
for (const auto& item29622 : Iterate(([&]() -> Value { auto fn29623 = PrepareDictionaryGet(s->LocalAt(7)); Arguments args29624; args29624.positional.reserve(2); args29624.Add(Tuple({s->LocalAt(22), s->LocalAt(6)}), false); args29624.Add(Tuple({}), false); return CallDictionaryGet(c, fn29623, std::move(args29624)); }()))) {
s->SetAt(1, item29622);
if (static_cast<bool>(([&]() -> Value { auto v29625 = Get(s->LocalAt(17), s->LocalAt(1)); Value v29626; v29626 = Get(s->LocalAt(17), s->LocalAt(0)); if (!static_cast<bool>(Binary("Gt", v29625, v29626))) return Value(false); v29625 = v29626; return Value(true); }()))) {
auto v29627 = s->LocalAt(1);
s->SetAt(0, v29627);
}
}
}
}
if (static_cast<bool>(s->LocalAt(16))) {
auto v29628 = ([&]() -> Value { auto fn29629 = s->Global("max"); Arguments args29630; args29630.Add(([&]() -> Value { auto fn29631 = s->Global("range"); Arguments args29632; args29632.Add(([&]() -> Value { auto fn29633 = s->Global("len"); Arguments args29634; args29634.Add(s->LocalAt(17), false); return Call(c, fn29633, std::move(args29634)); }()), false); return Call(c, fn29631, std::move(args29632)); }()), false); args29630.Keyword("key", Attribute(s->LocalAt(17), "__getitem__")); return Call(c, fn29629, std::move(args29630)); }());
s->SetAt(0, v29628);
}
auto v29635 = s->LocalAt(0);
Put(s->LocalAt(20), Value("best"), v29635);
return {};
}
}  // namespace kagg::opponents::compiled
