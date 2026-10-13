// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_21668680fa369be97722(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"_", "act", "action", "i", "is_weed", "next_op", "next_units", "noop", "nxt", "pending", "pos", "queue", "replay", "route", "self", "st", "step", "tape", "tile", "units", "view"};
s->PrepareSlots(s_names);
auto v642 = ([&]() -> Value { auto v643 = List({([&]() -> Value { auto v644 = ([&]() -> Value { auto fn645 = PrepareDictionaryGet(s->LocalAt(2)); Arguments args646; args646.Add(Value("farmer"), false); return CallDictionaryGet(c, fn645, std::move(args646)); }()); if (static_cast<bool>(v644)) return v644; v644 = List({Value("PASS")}); return v644; }())}); return Binary("Add", v643, ([&]() -> Value { auto fn647 = s->Global("list"); Arguments args648; args648.Add(([&]() -> Value { auto v649 = ([&]() -> Value { auto fn650 = PrepareDictionaryGet(s->LocalAt(2)); Arguments args651; args651.Add(Value("hands"), false); return CallDictionaryGet(c, fn650, std::move(args651)); }()); if (static_cast<bool>(v649)) return v649; v649 = List({}); return v649; }()), false); return Call(c, fn647, std::move(args648)); }())); }());
s->SetAt(19, v642);
auto v652 = Get(s->LocalAt(15), Value("pending"));
s->SetAt(9, v652);
auto v653 = Get(Attribute(s->LocalAt(14), "routes"), s->LocalAt(13));
s->SetAt(17, v653);
auto v654 = (static_cast<bool>(([&]() -> Value { auto v655 = ([&]() -> Value { auto v656 = ([&]() -> Value { auto v658 = s->LocalAt(16); return Binary("Add", v658, Value(int64_t{1})); }()); Value v657; v657 = ([&]() -> Value { auto fn659 = s->Global("len"); Arguments args660; args660.Add(s->LocalAt(17), false); return Call(c, fn659, std::move(args660)); }()); if (!static_cast<bool>(Binary("Lt", v656, v657))) return Value(false); v656 = v657; return Value(true); }()); if (!static_cast<bool>(v655)) return v655; v655 = ([&]() -> Value { auto fn661 = s->Global("isinstance"); Arguments args662; args662.positional.reserve(2); args662.Add(Get(s->LocalAt(17), ([&]() -> Value { auto v663 = s->LocalAt(16); return Binary("Add", v663, Value(int64_t{1})); }())), false); args662.Add(s->Global("dict"), false); return Call(c, fn661, std::move(args662)); }()); return v655; }())) ? Get(s->LocalAt(17), ([&]() -> Value { auto v664 = s->LocalAt(16); return Binary("Add", v664, Value(int64_t{1})); }())) : ([&]() -> Value { auto dict665 = Dict(); return dict665; }()));
s->SetAt(8, v654);
auto v666 = ([&]() -> Value { auto v667 = List({([&]() -> Value { auto v668 = ([&]() -> Value { auto fn669 = PrepareDictionaryGet(s->LocalAt(8)); Arguments args670; args670.Add(Value("farmer"), false); return CallDictionaryGet(c, fn669, std::move(args670)); }()); if (static_cast<bool>(v668)) return v668; v668 = List({Value("PASS")}); return v668; }())}); return Binary("Add", v667, ([&]() -> Value { auto fn671 = s->Global("list"); Arguments args672; args672.Add(([&]() -> Value { auto v673 = ([&]() -> Value { auto fn674 = PrepareDictionaryGet(s->LocalAt(8)); Arguments args675; args675.Add(Value("hands"), false); return CallDictionaryGet(c, fn674, std::move(args675)); }()); if (static_cast<bool>(v673)) return v673; v673 = List({}); return v673; }()), false); return Call(c, fn671, std::move(args672)); }())); }());
s->SetAt(6, v666);
for (const auto& item676 : Iterate(([&]() -> Value { auto fn677 = s->Global("range"); Arguments args678; args678.Add(([&]() -> Value { auto fn679 = s->Global("min"); Arguments args680; args680.positional.reserve(2); args680.Add(([&]() -> Value { auto fn681 = s->Global("len"); Arguments args682; args682.Add(s->LocalAt(19), false); return Call(c, fn681, std::move(args682)); }()), false); args680.Add(([&]() -> Value { auto fn683 = s->Global("len"); Arguments args684; args684.Add(Attribute(s->LocalAt(20), "positions"), false); return Call(c, fn683, std::move(args684)); }()), false); return Call(c, fn679, std::move(args680)); }()), false); return Call(c, fn677, std::move(args678)); }()))) {
s->SetAt(3, item676);
auto v685 = Get(Attribute(s->LocalAt(20), "positions"), s->LocalAt(3));
s->SetAt(10, v685);
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto fn686 = s->Global("isinstance"); Arguments args687; args687.positional.reserve(2); args687.Add(s->LocalAt(10), false); args687.Add(Tuple({s->Global("list"), s->Global("tuple")}), false); return Call(c, fn686, std::move(args687)); }())))) {
continue;
}
auto v688 = Tuple({([&]() -> Value { auto fn689 = s->Global("int"); Arguments args690; args690.Add(Get(s->LocalAt(10), Value(int64_t{0})), false); return Call(c, fn689, std::move(args690)); }()), ([&]() -> Value { auto fn691 = s->Global("int"); Arguments args692; args692.Add(Get(s->LocalAt(10), Value(int64_t{1})), false); return Call(c, fn691, std::move(args692)); }())});
s->SetAt(10, v688);
auto v693 = ([&]() -> Value { auto fn694 = s->Global("_tile_at"); Arguments args695; args695.positional.reserve(2); args695.Add(Attribute(s->LocalAt(20), "tiles"), false); args695.Add(s->LocalAt(10), false); return Call(c, fn694, std::move(args695)); }());
s->SetAt(18, v693);
auto v696 = ([&]() -> Value { auto fn697 = s->Global("list"); Arguments args698; args698.Add(Get(s->LocalAt(19), s->LocalAt(3)), false); return Call(c, fn697, std::move(args698)); }());
s->SetAt(1, v696);
auto v699 = ([&]() -> Value { auto fn700 = PrepareDictionaryGet(s->LocalAt(9)); Arguments args701; args701.Add(s->LocalAt(3), false); return CallDictionaryGet(c, fn700, std::move(args701)); }());
s->SetAt(11, v699);
if (static_cast<bool>(([&]() -> Value { auto v702 = s->LocalAt(11); if (!static_cast<bool>(v702)) return v702; v702 = ([&]() -> Value { auto v703 = Get(Get(s->LocalAt(11), Value(int64_t{0})), Value(int64_t{0})); Value v704; v704 = s->LocalAt(10); if (!static_cast<bool>(Binary("NotEq", v703, v704))) return Value(false); v703 = v704; return Value(true); }()); return v702; }()))) {
(void)([&]() -> Value { auto fn705 = Attribute(s->LocalAt(9), "pop"); Arguments args706; args706.positional.reserve(2); args706.Add(s->LocalAt(3), false); args706.Add(Value{}, false); return Call(c, fn705, std::move(args706)); }());
auto v707 = Value{};
s->SetAt(11, v707);
}
auto v708 = ([&]() -> Value { auto v709 = ([&]() -> Value { auto fn710 = s->Global("isinstance"); Arguments args711; args711.positional.reserve(2); args711.Add(s->LocalAt(18), false); args711.Add(s->Global("dict"), false); return Call(c, fn710, std::move(args711)); }()); if (!static_cast<bool>(v709)) return v709; v709 = ([&]() -> Value { auto v712 = ([&]() -> Value { auto fn714 = s->Global("_get"); Arguments args715; args715.positional.reserve(2); args715.Add(s->LocalAt(18), false); args715.Add(Value("kind"), false); return Call(c, fn714, std::move(args715)); }()); Value v713; v713 = Value("WEED"); if (!static_cast<bool>(Binary("Eq", v712, v713))) return Value(false); v712 = v713; return Value(true); }()); return v709; }());
s->SetAt(4, v708);
auto v716 = ([&]() -> Value { auto fn717 = s->Global("_is_noop"); Arguments args718; args718.positional.reserve(6); args718.Add(s->LocalAt(1), false); args718.Add(s->LocalAt(18), false); args718.Add(([&]() -> Value { auto fn719 = Attribute(s->LocalAt(20), "inv"); Arguments args720; args720.Add(s->LocalAt(3), false); return Call(c, fn719, std::move(args720)); }()), false); args718.Add(Attribute(s->LocalAt(20), "seeds"), false); args718.Add(s->LocalAt(10), false); args718.Add(Attribute(s->LocalAt(20), "board"), false); return Call(c, fn717, std::move(args718)); }());
s->SetAt(7, v716);
auto v721 = (static_cast<bool>(([&]() -> Value { auto v722 = ([&]() -> Value { auto v723 = s->LocalAt(3); Value v724; v724 = ([&]() -> Value { auto fn725 = s->Global("len"); Arguments args726; args726.Add(s->LocalAt(6), false); return Call(c, fn725, std::move(args726)); }()); if (!static_cast<bool>(Binary("Lt", v723, v724))) return Value(false); v723 = v724; return Value(true); }()); if (!static_cast<bool>(v722)) return v722; v722 = Get(s->LocalAt(6), s->LocalAt(3)); return v722; }())) ? Get(Get(s->LocalAt(6), s->LocalAt(3)), Value(int64_t{0})) : Value("PASS"));
s->SetAt(5, v721);
if (static_cast<bool>(([&]() -> Value { auto v727 = s->LocalAt(1); if (!static_cast<bool>(v727)) return v727; v727 = ([&]() -> Value { auto v728 = Get(s->LocalAt(1), Value(int64_t{0})); Value v729; v729 = Tuple({Value("PLANT"), Value("BUILD_COOP"), Value("BUILD_PASTURE")}); if (!static_cast<bool>(Binary("In", v728, v729))) return Value(false); v728 = v729; return Value(true); }()); if (!static_cast<bool>(v727)) return v727; v727 = s->LocalAt(4); return v727; }()))) {
(void)([&]() -> Value { auto fn730 = Attribute(([&]() -> Value { auto fn732 = Attribute(s->LocalAt(9), "setdefault"); Arguments args733; args733.positional.reserve(2); args733.Add(s->LocalAt(3), false); args733.Add(List({}), false); return Call(c, fn732, std::move(args733)); }()), "append"); Arguments args731; args731.Add(Tuple({s->LocalAt(10), s->LocalAt(1)}), false); return Call(c, fn730, std::move(args731)); }());
auto v734 = List({Value("DIG")});
s->SetAt(1, v734);
}
else {
if (static_cast<bool>(([&]() -> Value { auto v735 = s->LocalAt(11); if (!static_cast<bool>(v735)) return v735; v735 = s->LocalAt(7); return v735; }()))) {
auto v736 = Get(s->LocalAt(11), Value(int64_t{0}));
auto unpack737 = Iterate(v736);
ValidateUnpack(unpack737, 2, false);
s->SetAt(0, unpack737.at(0));
s->SetAt(12, unpack737.at(1));
if (static_cast<bool>(([&]() -> Value { auto v738 = ([&]() -> Value { auto v739 = Get(s->LocalAt(12), Value(int64_t{0})); Value v740; v740 = Value("PLANT"); if (!static_cast<bool>(Binary("Eq", v739, v740))) return Value(false); v739 = v740; return Value(true); }()); if (!static_cast<bool>(v738)) return v738; v738 = ([&]() -> Value { auto v741 = s->LocalAt(5); Value v742; v742 = s->Global("MOVES"); if (!static_cast<bool>(Binary("In", v741, v742))) return Value(false); v741 = v742; return Value(true); }()); return v738; }()))) {
(void)([&]() -> Value { auto fn743 = Attribute(s->LocalAt(9), "pop"); Arguments args744; args744.positional.reserve(2); args744.Add(s->LocalAt(3), false); args744.Add(Value{}, false); return Call(c, fn743, std::move(args744)); }());
}
else {
(void)([&]() -> Value { auto fn745 = Attribute(s->LocalAt(11), "pop"); Arguments args746; args746.Add(Value(int64_t{0}), false); return Call(c, fn745, std::move(args746)); }());
if (static_cast<bool>(([&]() -> Value { auto v747 = s->LocalAt(1); if (!static_cast<bool>(v747)) return v747; v747 = ([&]() -> Value { auto v748 = Get(s->LocalAt(1), Value(int64_t{0})); Value v749; v749 = Value("PASS"); if (!static_cast<bool>(Binary("NotEq", v748, v749))) return Value(false); v748 = v749; return Value(true); }()); if (!static_cast<bool>(v747)) return v747; v747 = ([&]() -> Value { auto v750 = Get(s->LocalAt(1), Value(int64_t{0})); Value v751; v751 = s->Global("MOVES"); if (!static_cast<bool>(Binary("NotIn", v750, v751))) return Value(false); v750 = v751; return Value(true); }()); return v747; }()))) {
(void)([&]() -> Value { auto fn752 = Attribute(s->LocalAt(11), "append"); Arguments args753; args753.Add(Tuple({s->LocalAt(10), s->LocalAt(1)}), false); return Call(c, fn752, std::move(args753)); }());
}
auto v754 = s->LocalAt(12);
s->SetAt(1, v754);
if (static_cast<bool>(Unary("Not", s->LocalAt(11)))) {
(void)([&]() -> Value { auto fn755 = Attribute(s->LocalAt(9), "pop"); Arguments args756; args756.positional.reserve(2); args756.Add(s->LocalAt(3), false); args756.Add(Value{}, false); return Call(c, fn755, std::move(args756)); }());
}
}
}
else {
if (static_cast<bool>(([&]() -> Value { auto v757 = s->LocalAt(4); if (!static_cast<bool>(v757)) return v757; v757 = s->LocalAt(7); return v757; }()))) {
auto v758 = List({Value("DIG")});
s->SetAt(1, v758);
}
}
}
auto v759 = s->LocalAt(1);
Put(s->LocalAt(19), s->LocalAt(3), v759);
}
auto v760 = Get(s->LocalAt(19), Value(int64_t{0}));
Put(s->LocalAt(2), Value("farmer"), v760);
auto v761 = Slice(s->LocalAt(19), Value(int64_t{1}), Value{}, Value{});
Put(s->LocalAt(2), Value("hands"), v761);
return {};
}
}  // namespace kagg::opponents::compiled
