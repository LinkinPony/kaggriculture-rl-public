// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_a23b5490cb2932733b40(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "added", "avail", "booked", "commands", "d", "debts", "extra", "first", "hit", "it", "item", "market", "n", "native", "o", "obs", "off", "picked", "plan", "player", "prices", "protected", "q", "selling", "step", "stock", "t", "take"};
s->PrepareSlots(s_names);
auto v18626 = ([&]() -> Value { auto fn18627 = s->Global("int"); Arguments args18628; args18628.Add(Get(s->LocalAt(16), Value("step")), false); return Call(c, fn18627, std::move(args18628)); }());
s->SetAt(25, v18626);
auto v18629 = ([&]() -> Value { auto fn18630 = s->Global("int"); Arguments args18631; args18631.Add(Get(s->LocalAt(16), Value("player")), false); return Call(c, fn18630, std::move(args18631)); }());
s->SetAt(20, v18629);
if (static_cast<bool>(([&]() -> Value { auto v18632 = ([&]() -> Value { auto v18633 = ([&]() -> Value { auto v18635 = s->LocalAt(25); return Binary("Mod", v18635, Value(int64_t{24})); }()); Value v18634; v18634 = Value(int64_t{23}); if (!static_cast<bool>(Binary("Eq", v18633, v18634))) return Value(false); v18633 = v18634; return Value(true); }()); if (static_cast<bool>(v18632)) return v18632; v18632 = Unary("Not", ([&]() -> Value { auto v18636 = s->Global("_ADV_FROM"); Value v18637; v18637 = s->LocalAt(25); if (!static_cast<bool>(Binary("LtE", v18636, v18637))) return Value(false); v18636 = v18637; v18637 = s->Global("_ADV_TO"); if (!static_cast<bool>(Binary("Lt", v18636, v18637))) return Value(false); v18636 = v18637; return Value(true); }())); return v18632; }()))) {
return s->LocalAt(0);
}
auto v18638 = Get(Attribute(Attribute(s->Global("_IMPL"), "chassis"), "players"), s->LocalAt(20));
s->SetAt(14, v18638);
auto v18639 = ([&]() -> Value { auto fn18640 = Attribute(Get(s->LocalAt(14), Value("sell_state")), "setdefault"); Arguments args18641; args18641.positional.reserve(2); args18641.Add(Value("r36_debts"), false); args18641.Add(([&]() -> Value { auto dict18642 = Dict(); return dict18642; }()), false); return Call(c, fn18640, std::move(args18641)); }());
s->SetAt(6, v18639);
auto v18643 = List({});
s->SetAt(19, v18643);
auto v18644 = Value{};
s->SetAt(8, v18644);
for (const auto& item18645 : Iterate(([&]() -> Value { auto fn18646 = s->Global("range"); Arguments args18647; args18647.positional.reserve(2); args18647.Add(Value(int64_t{1}), false); args18647.Add(([&]() -> Value { auto v18648 = s->Global("_ADV_LOOK"); return Binary("Add", v18648, Value(int64_t{1})); }()), false); return Call(c, fn18646, std::move(args18647)); }()))) {
s->SetAt(17, item18645);
auto v18649 = ([&]() -> Value { auto v18650 = s->LocalAt(25); return Binary("Add", v18650, s->LocalAt(17)); }());
s->SetAt(27, v18649);
if (static_cast<bool>(([&]() -> Value { auto v18651 = s->LocalAt(27); Value v18652; v18652 = Value(int64_t{718}); if (!static_cast<bool>(Binary("Gt", v18651, v18652))) return Value(false); v18651 = v18652; return Value(true); }()))) {
break;
}
for (const auto& item18653 : Iterate(([&]() -> Value { auto fn18654 = s->Global("_adv_future"); Arguments args18655; args18655.positional.reserve(2); args18655.Add(s->LocalAt(20), false); args18655.Add(s->LocalAt(27), false); return Call(c, fn18654, std::move(args18655)); }()))) {
s->SetAt(15, item18653);
if (static_cast<bool>(([&]() -> Value { auto v18656 = Unary("Not", s->LocalAt(15)); if (static_cast<bool>(v18656)) return v18656; v18656 = ([&]() -> Value { auto v18657 = ([&]() -> Value { auto fn18659 = s->Global("len"); Arguments args18660; args18660.Add(s->LocalAt(15), false); return Call(c, fn18659, std::move(args18660)); }()); Value v18658; v18658 = Value(int64_t{3}); if (!static_cast<bool>(Binary("Lt", v18657, v18658))) return Value(false); v18657 = v18658; return Value(true); }()); return v18656; }()))) {
continue;
}
if (static_cast<bool>(([&]() -> Value { auto v18661 = s->LocalAt(8); Value v18662; v18662 = Value{}; if (!static_cast<bool>(Binary("Is", v18661, v18662))) return Value(false); v18661 = v18662; return Value(true); }()))) {
auto v18663 = s->LocalAt(15);
s->SetAt(8, v18663);
}
if (static_cast<bool>(([&]() -> Value { auto v18664 = ([&]() -> Value { auto v18665 = Get(s->LocalAt(15), Value(int64_t{0})); Value v18666; v18666 = Value("SELL"); if (!static_cast<bool>(Binary("Eq", v18665, v18666))) return Value(false); v18665 = v18666; return Value(true); }()); if (!static_cast<bool>(v18664)) return v18664; v18664 = ([&]() -> Value { auto v18667 = Get(s->LocalAt(15), Value(int64_t{1})); Value v18668; v18668 = s->Global("_ADV_ITEMS"); if (!static_cast<bool>(Binary("In", v18667, v18668))) return Value(false); v18667 = v18668; return Value(true); }()); return v18664; }()))) {
try {
auto v18670 = ([&]() -> Value { auto fn18671 = s->Global("max"); Arguments args18672; args18672.positional.reserve(2); args18672.Add(Value(int64_t{0}), false); args18672.Add(([&]() -> Value { auto fn18673 = s->Global("int"); Arguments args18674; args18674.Add(Get(s->LocalAt(15), Value(int64_t{2})), false); return Call(c, fn18673, std::move(args18674)); }()), false); return Call(c, fn18671, std::move(args18672)); }());
s->SetAt(23, v18670);
} catch (const Error& error18669) {
if (Matches(error18669, s->Global("Exception"))) {
auto v18675 = Value(int64_t{0});
s->SetAt(23, v18675);
}
else { throw; }
}
if (static_cast<bool>(s->Global("_ADV_SUBTRACT_DEBTS"))) {
auto v18676 = s->LocalAt(23);
s->SetAt(23, Inplace("Sub", v18676, ([&]() -> Value { auto fn18677 = PrepareDictionaryGet(([&]() -> Value { auto fn18679 = PrepareDictionaryGet(s->LocalAt(6)); Arguments args18680; args18680.positional.reserve(2); args18680.Add(s->LocalAt(27), false); args18680.Add(([&]() -> Value { auto dict18681 = Dict(); return dict18681; }()), false); return CallDictionaryGet(c, fn18679, std::move(args18680)); }())); Arguments args18678; args18678.positional.reserve(2); args18678.Add(Get(s->LocalAt(15), Value(int64_t{1})), false); args18678.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn18677, std::move(args18678)); }())));
}
if (static_cast<bool>(([&]() -> Value { auto v18682 = s->LocalAt(23); Value v18683; v18683 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v18682, v18683))) return Value(false); v18682 = v18683; return Value(true); }()))) {
(void)([&]() -> Value { auto fn18684 = Attribute(s->LocalAt(19), "append"); Arguments args18685; args18685.Add(Tuple({s->LocalAt(27), Get(s->LocalAt(15), Value(int64_t{1})), s->LocalAt(23)}), false); return Call(c, fn18684, std::move(args18685)); }());
}
}
}
}
auto v18686 = (static_cast<bool>(([&]() -> Value { auto v18687 = s->Global("_ADV_PROTECT"); if (!static_cast<bool>(v18687)) return v18687; v18687 = ([&]() -> Value { auto v18688 = s->LocalAt(8); Value v18689; v18689 = Value{}; if (!static_cast<bool>(Binary("IsNot", v18688, v18689))) return Value(false); v18688 = v18689; return Value(true); }()); if (!static_cast<bool>(v18687)) return v18687; v18687 = ([&]() -> Value { auto v18690 = Get(s->LocalAt(8), Value(int64_t{0})); Value v18691; v18691 = Value("SELL"); if (!static_cast<bool>(Binary("Eq", v18690, v18691))) return Value(false); v18690 = v18691; return Value(true); }()); return v18687; }())) ? Get(s->LocalAt(8), Value(int64_t{1})) : Value{});
s->SetAt(22, v18686);
auto v18692 = ([&]() -> Value { auto comp18693 = std::make_shared<Scope>(); comp18693->globals = s->globals; comp18693->parent = s; static constexpr const char* comp18693_names[] = {"item", "q", "t"}; comp18693->PrepareSlots(comp18693_names); auto result18694 = List(); for (const auto& item18695 : Iterate(s->LocalAt(19))) { auto unpack18696 = Iterate(item18695); ValidateUnpack(unpack18696, 3, false); comp18693->SetAt(2, unpack18696.at(0)); comp18693->SetAt(0, unpack18696.at(1)); comp18693->SetAt(1, unpack18696.at(2)); if (!static_cast<bool>(([&]() -> Value { auto v18697 = comp18693->LocalAt(0); Value v18698; v18698 = comp18693->Captured("protected"); if (!static_cast<bool>(Binary("NotEq", v18697, v18698))) return Value(false); v18697 = v18698; return Value(true); }()))) continue; result18694.node()->sequence.push_back(Tuple({comp18693->LocalAt(2), comp18693->LocalAt(0), comp18693->LocalAt(1)})); } return result18694; }());
s->SetAt(19, v18692);
if (static_cast<bool>(Unary("Not", s->LocalAt(19)))) {
return s->LocalAt(0);
}
auto v18699 = ([&]() -> Value { auto comp18700 = std::make_shared<Scope>(); comp18700->globals = s->globals; comp18700->parent = s; static constexpr const char* comp18700_names[] = {"o"}; comp18700->PrepareSlots(comp18700_names); auto result18701 = List(); for (const auto& item18702 : Iterate(([&]() -> Value { auto v18703 = ([&]() -> Value { auto fn18704 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args18705; args18705.Add(Value("market"), false); return CallDictionaryGet(c, fn18704, std::move(args18705)); }()); if (static_cast<bool>(v18703)) return v18703; v18703 = List({}); return v18703; }()))) { comp18700->SetAt(0, item18702); result18701.node()->sequence.push_back(([&]() -> Value { auto fn18706 = comp18700->Global("list"); Arguments args18707; args18707.Add(comp18700->LocalAt(0), false); return Call(c, fn18706, std::move(args18707)); }())); } return result18701; }());
s->SetAt(12, v18699);
if (static_cast<bool>(([&]() -> Value { auto comp18708 = std::make_shared<Scope>(); comp18708->globals = s->globals; comp18708->parent = s; static constexpr const char* comp18708_names[] = {"o"}; comp18708->PrepareSlots(comp18708_names); auto result18709 = List(); for (const auto& item18710 : Iterate(s->LocalAt(12))) { comp18708->SetAt(0, item18710); if (static_cast<bool>(([&]() -> Value { auto v18711 = ([&]() -> Value { auto v18712 = ([&]() -> Value { auto fn18714 = comp18708->Global("len"); Arguments args18715; args18715.Add(comp18708->LocalAt(0), false); return Call(c, fn18714, std::move(args18715)); }()); Value v18713; v18713 = Value(int64_t{1}); if (!static_cast<bool>(Binary("Gt", v18712, v18713))) return Value(false); v18712 = v18713; return Value(true); }()); if (!static_cast<bool>(v18711)) return v18711; v18711 = ([&]() -> Value { auto v18716 = Get(comp18708->LocalAt(0), Value(int64_t{0})); Value v18717; v18717 = Value("BUY_PRODUCT"); if (!static_cast<bool>(Binary("Eq", v18716, v18717))) return Value(false); v18716 = v18717; return Value(true); }()); return v18711; }()))) return Value(true); } return Value(false); }()))) {
return s->LocalAt(0);
}
auto v18718 = ([&]() -> Value { auto fn18719 = s->Global("projected_shed"); Arguments args18720; args18720.positional.reserve(2); args18720.Add(s->LocalAt(0), false); args18720.Add(([&]() -> Value { auto fn18721 = s->Global("FarmView"); Arguments args18722; args18722.Add(s->LocalAt(16), false); return Call(c, fn18721, std::move(args18722)); }()), false); return Call(c, fn18719, std::move(args18720)); }());
s->SetAt(26, v18718);
auto v18723 = ([&]() -> Value { auto dict18724 = Dict(); return dict18724; }());
s->SetAt(24, v18723);
for (const auto& item18725 : Iterate(s->LocalAt(12))) {
s->SetAt(15, item18725);
if (static_cast<bool>(([&]() -> Value { auto v18726 = ([&]() -> Value { auto v18727 = ([&]() -> Value { auto fn18729 = s->Global("len"); Arguments args18730; args18730.Add(s->LocalAt(15), false); return Call(c, fn18729, std::move(args18730)); }()); Value v18728; v18728 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v18727, v18728))) return Value(false); v18727 = v18728; return Value(true); }()); if (!static_cast<bool>(v18726)) return v18726; v18726 = ([&]() -> Value { auto v18731 = Get(s->LocalAt(15), Value(int64_t{0})); Value v18732; v18732 = Value("SELL"); if (!static_cast<bool>(Binary("Eq", v18731, v18732))) return Value(false); v18731 = v18732; return Value(true); }()); return v18726; }()))) {
try {
auto v18734 = ([&]() -> Value { auto v18735 = ([&]() -> Value { auto fn18736 = PrepareDictionaryGet(s->LocalAt(24)); Arguments args18737; args18737.positional.reserve(2); args18737.Add(Get(s->LocalAt(15), Value(int64_t{1})), false); args18737.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn18736, std::move(args18737)); }()); return Binary("Add", v18735, ([&]() -> Value { auto fn18738 = s->Global("max"); Arguments args18739; args18739.positional.reserve(2); args18739.Add(Value(int64_t{0}), false); args18739.Add(([&]() -> Value { auto fn18740 = s->Global("int"); Arguments args18741; args18741.Add(Get(s->LocalAt(15), Value(int64_t{2})), false); return Call(c, fn18740, std::move(args18741)); }()), false); return Call(c, fn18738, std::move(args18739)); }())); }());
Put(s->LocalAt(24), Get(s->LocalAt(15), Value(int64_t{1})), v18734);
} catch (const Error& error18733) {
if (Matches(error18733, s->Global("Exception"))) {
return s->LocalAt(0);
}
else { throw; }
}
}
}
auto v18742 = ([&]() -> Value { Arguments args18743; args18743.Add(([&]() -> Value { auto v18744 = ([&]() -> Value { auto fn18745 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args18746; args18746.Add(Value("farmer"), false); return CallDictionaryGet(c, fn18745, std::move(args18746)); }()); if (static_cast<bool>(v18744)) return v18744; v18744 = List({Value("PASS")}); return v18744; }()), false); args18743.Add(([&]() -> Value { auto v18747 = ([&]() -> Value { auto fn18748 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args18749; args18749.Add(Value("hands"), false); return CallDictionaryGet(c, fn18748, std::move(args18749)); }()); if (static_cast<bool>(v18747)) return v18747; v18747 = List({}); return v18747; }()), true); return List(std::move(args18743.positional)); }());
s->SetAt(4, v18742);
auto v18750 = ([&]() -> Value { auto comp18751 = std::make_shared<Scope>(); comp18751->globals = s->globals; comp18751->parent = s; static constexpr const char* comp18751_names[] = {"c"}; comp18751->PrepareSlots(comp18751_names); auto result18752 = List(); for (const auto& item18753 : Iterate(s->LocalAt(4))) { comp18751->SetAt(0, item18753); if (!static_cast<bool>(([&]() -> Value { auto v18754 = ([&]() -> Value { auto v18755 = ([&]() -> Value { auto fn18757 = comp18751->Global("len"); Arguments args18758; args18758.Add(comp18751->LocalAt(0), false); return Call(c, fn18757, std::move(args18758)); }()); Value v18756; v18756 = Value(int64_t{1}); if (!static_cast<bool>(Binary("Gt", v18755, v18756))) return Value(false); v18755 = v18756; return Value(true); }()); if (!static_cast<bool>(v18754)) return v18754; v18754 = ([&]() -> Value { auto v18759 = Get(comp18751->LocalAt(0), Value(int64_t{0})); Value v18760; v18760 = Value("PICKUP"); if (!static_cast<bool>(Binary("Eq", v18759, v18760))) return Value(false); v18759 = v18760; return Value(true); }()); return v18754; }()))) continue; result18752.node()->sequence.push_back(Get(comp18751->LocalAt(0), Value(int64_t{1}))); } return Set(result18752.node()->sequence); }());
s->SetAt(18, v18750);
auto v18761 = Get(Get(s->LocalAt(16), Value("market")), Value("prices"));
s->SetAt(21, v18761);
auto v18762 = Value(int64_t{0});
s->SetAt(1, v18762);
auto v18763 = List({});
s->SetAt(7, v18763);
auto v18764 = List({});
s->SetAt(3, v18764);
for (const auto& item18765 : Iterate(([&]() -> Value { auto fn18766 = s->Global("sorted"); Arguments args18767; args18767.Add(([&]() -> Value { auto comp18768 = std::make_shared<Scope>(); comp18768->globals = s->globals; comp18768->parent = s; static constexpr const char* comp18768_names[] = {"_", "it"}; comp18768->PrepareSlots(comp18768_names); auto result18769 = List(); for (const auto& item18770 : Iterate(s->LocalAt(19))) { auto unpack18771 = Iterate(item18770); ValidateUnpack(unpack18771, 3, false); comp18768->SetAt(0, unpack18771.at(0)); comp18768->SetAt(1, unpack18771.at(1)); comp18768->SetAt(0, unpack18771.at(2)); result18769.node()->sequence.push_back(comp18768->LocalAt(1)); } return Set(result18769.node()->sequence); }()), false); args18767.Keyword("key", Define(&Code_66b384d6e7699ead49e4, s, Signature{{"it"}, {}, {}, {}, "", "", ([]() -> std::span<const char* const> { static constexpr const char* names[] = {"it"}; return names; }())}, true, "<lambda>")); return Call(c, fn18766, std::move(args18767)); }()))) {
s->SetAt(11, item18765);
if (static_cast<bool>(([&]() -> Value { auto v18776 = ([&]() -> Value { auto v18777 = s->LocalAt(11); Value v18778; v18778 = s->LocalAt(18); if (!static_cast<bool>(Binary("In", v18777, v18778))) return Value(false); v18777 = v18778; return Value(true); }()); if (static_cast<bool>(v18776)) return v18776; v18776 = ([&]() -> Value { auto v18779 = ([&]() -> Value { auto fn18781 = s->Global("int"); Arguments args18782; args18782.Add(([&]() -> Value { auto fn18783 = PrepareDictionaryGet(s->LocalAt(21)); Arguments args18784; args18784.positional.reserve(2); args18784.Add(s->LocalAt(11), false); args18784.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn18783, std::move(args18784)); }()), false); return Call(c, fn18781, std::move(args18782)); }()); Value v18780; v18780 = Value(int64_t{2}); if (!static_cast<bool>(Binary("Lt", v18779, v18780))) return Value(false); v18779 = v18780; return Value(true); }()); return v18776; }()))) {
continue;
}
auto v18785 = ([&]() -> Value { auto v18786 = ([&]() -> Value { auto fn18787 = s->Global("int"); Arguments args18788; args18788.Add(([&]() -> Value { auto fn18789 = PrepareDictionaryGet(s->LocalAt(26)); Arguments args18790; args18790.positional.reserve(2); args18790.Add(s->LocalAt(11), false); args18790.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn18789, std::move(args18790)); }()), false); return Call(c, fn18787, std::move(args18788)); }()); return Binary("Sub", v18786, ([&]() -> Value { auto fn18791 = PrepareDictionaryGet(s->LocalAt(24)); Arguments args18792; args18792.positional.reserve(2); args18792.Add(s->LocalAt(11), false); args18792.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn18791, std::move(args18792)); }())); }());
s->SetAt(2, v18785);
if (static_cast<bool>(([&]() -> Value { auto v18793 = s->LocalAt(2); Value v18794; v18794 = Value(int64_t{1}); if (!static_cast<bool>(Binary("Lt", v18793, v18794))) return Value(false); v18793 = v18794; return Value(true); }()))) {
continue;
}
auto v18795 = ([&]() -> Value { auto comp18796 = std::make_shared<Scope>(); comp18796->globals = s->globals; comp18796->parent = s; static constexpr const char* comp18796_names[] = {"o"}; comp18796->PrepareSlots(comp18796_names); auto result18797 = List(); auto fallback = Value{}; for (const auto& item18798 : Iterate(s->LocalAt(12))) { comp18796->SetAt(0, item18798); if (!static_cast<bool>(([&]() -> Value { auto v18799 = ([&]() -> Value { auto v18800 = ([&]() -> Value { auto fn18802 = comp18796->Global("len"); Arguments args18803; args18803.Add(comp18796->LocalAt(0), false); return Call(c, fn18802, std::move(args18803)); }()); Value v18801; v18801 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v18800, v18801))) return Value(false); v18800 = v18801; return Value(true); }()); if (!static_cast<bool>(v18799)) return v18799; v18799 = ([&]() -> Value { auto v18804 = Get(comp18796->LocalAt(0), Value(int64_t{0})); Value v18805; v18805 = Value("SELL"); if (!static_cast<bool>(Binary("Eq", v18804, v18805))) return Value(false); v18804 = v18805; return Value(true); }()); if (!static_cast<bool>(v18799)) return v18799; v18799 = ([&]() -> Value { auto v18806 = Get(comp18796->LocalAt(0), Value(int64_t{1})); Value v18807; v18807 = comp18796->Captured("item"); if (!static_cast<bool>(Binary("Eq", v18806, v18807))) return Value(false); v18806 = v18807; return Value(true); }()); return v18799; }()))) continue; return comp18796->LocalAt(0); } return fallback; }());
s->SetAt(9, v18795);
if (static_cast<bool>(([&]() -> Value { auto v18808 = ([&]() -> Value { auto v18809 = s->LocalAt(9); Value v18810; v18810 = Value{}; if (!static_cast<bool>(Binary("Is", v18809, v18810))) return Value(false); v18809 = v18810; return Value(true); }()); if (!static_cast<bool>(v18808)) return v18808; v18808 = ([&]() -> Value { auto v18811 = ([&]() -> Value { auto v18813 = ([&]() -> Value { auto fn18814 = s->Global("len"); Arguments args18815; args18815.Add(s->LocalAt(12), false); return Call(c, fn18814, std::move(args18815)); }()); return Binary("Add", v18813, ([&]() -> Value { auto fn18816 = s->Global("len"); Arguments args18817; args18817.Add(s->LocalAt(7), false); return Call(c, fn18816, std::move(args18817)); }())); }()); Value v18812; v18812 = Value(int64_t{10}); if (!static_cast<bool>(Binary("GtE", v18811, v18812))) return Value(false); v18811 = v18812; return Value(true); }()); return v18808; }()))) {
continue;
}
auto v18818 = Value(int64_t{0});
s->SetAt(13, v18818);
for (const auto& item18819 : Iterate(s->LocalAt(19))) {
auto unpack18820 = Iterate(item18819);
ValidateUnpack(unpack18820, 3, false);
s->SetAt(27, unpack18820.at(0));
s->SetAt(10, unpack18820.at(1));
s->SetAt(23, unpack18820.at(2));
if (static_cast<bool>(([&]() -> Value { auto v18821 = ([&]() -> Value { auto v18822 = s->LocalAt(10); Value v18823; v18823 = s->LocalAt(11); if (!static_cast<bool>(Binary("NotEq", v18822, v18823))) return Value(false); v18822 = v18823; return Value(true); }()); if (static_cast<bool>(v18821)) return v18821; v18821 = ([&]() -> Value { auto v18824 = s->LocalAt(2); Value v18825; v18825 = Value(int64_t{0}); if (!static_cast<bool>(Binary("LtE", v18824, v18825))) return Value(false); v18824 = v18825; return Value(true); }()); return v18821; }()))) {
continue;
}
auto v18826 = ([&]() -> Value { auto fn18827 = s->Global("min"); Arguments args18828; args18828.positional.reserve(2); args18828.Add(s->LocalAt(23), false); args18828.Add(s->LocalAt(2), false); return Call(c, fn18827, std::move(args18828)); }());
s->SetAt(28, v18826);
(void)([&]() -> Value { auto fn18829 = Attribute(s->LocalAt(3), "append"); Arguments args18830; args18830.Add(Tuple({s->LocalAt(27), s->LocalAt(11), s->LocalAt(28)}), false); return Call(c, fn18829, std::move(args18830)); }());
auto v18831 = s->LocalAt(13);
s->SetAt(13, Inplace("Add", v18831, s->LocalAt(28)));
auto v18832 = s->LocalAt(2);
s->SetAt(2, Inplace("Sub", v18832, s->LocalAt(28)));
}
if (static_cast<bool>(([&]() -> Value { auto v18833 = s->LocalAt(13); Value v18834; v18834 = Value(int64_t{1}); if (!static_cast<bool>(Binary("Lt", v18833, v18834))) return Value(false); v18833 = v18834; return Value(true); }()))) {
continue;
}
if (static_cast<bool>(([&]() -> Value { auto v18835 = s->LocalAt(9); Value v18836; v18836 = Value{}; if (!static_cast<bool>(Binary("IsNot", v18835, v18836))) return Value(false); v18835 = v18836; return Value(true); }()))) {
auto v18837 = ([&]() -> Value { auto v18838 = ([&]() -> Value { auto fn18839 = s->Global("int"); Arguments args18840; args18840.Add(Get(s->LocalAt(9), Value(int64_t{2})), false); return Call(c, fn18839, std::move(args18840)); }()); return Binary("Add", v18838, s->LocalAt(13)); }());
Put(s->LocalAt(9), Value(int64_t{2}), v18837);
}
else {
(void)([&]() -> Value { auto fn18841 = Attribute(s->LocalAt(7), "append"); Arguments args18842; args18842.Add(List({Value("SELL"), s->LocalAt(11), s->LocalAt(13)}), false); return Call(c, fn18841, std::move(args18842)); }());
}
auto v18843 = s->LocalAt(1);
s->SetAt(1, Inplace("Add", v18843, s->LocalAt(13)));
}
if (static_cast<bool>(Unary("Not", s->LocalAt(1)))) {
return s->LocalAt(0);
}
for (const auto& item18844 : Iterate((static_cast<bool>(s->Global("_ADV_BOOK")) ? s->LocalAt(3) : List({})))) {
auto unpack18845 = Iterate(item18844);
ValidateUnpack(unpack18845, 3, false);
s->SetAt(27, unpack18845.at(0));
s->SetAt(11, unpack18845.at(1));
s->SetAt(28, unpack18845.at(2));
auto v18846 = ([&]() -> Value { auto fn18847 = Attribute(s->LocalAt(6), "setdefault"); Arguments args18848; args18848.positional.reserve(2); args18848.Add(s->LocalAt(27), false); args18848.Add(([&]() -> Value { auto dict18849 = Dict(); return dict18849; }()), false); return Call(c, fn18847, std::move(args18848)); }());
s->SetAt(5, v18846);
auto v18850 = ([&]() -> Value { auto v18851 = ([&]() -> Value { auto fn18852 = PrepareDictionaryGet(s->LocalAt(5)); Arguments args18853; args18853.positional.reserve(2); args18853.Add(s->LocalAt(11), false); args18853.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn18852, std::move(args18853)); }()); return Binary("Add", v18851, s->LocalAt(28)); }());
Put(s->LocalAt(5), s->LocalAt(11), v18850);
}
auto v18854 = s->Global("_ADV_REPORT");
auto v18855 = Value("adv_turns");
auto v18856 = Get(v18854, v18855);
Put(v18854, v18855, Inplace("Add", v18856, Value(int64_t{1})));
auto v18857 = s->Global("_ADV_REPORT");
auto v18858 = Value("adv_units");
auto v18859 = Get(v18857, v18858);
Put(v18857, v18858, Inplace("Add", v18859, s->LocalAt(1)));
return ([&]() -> Value { auto fn18860 = s->Global("dict"); Arguments args18861; args18861.Add(s->LocalAt(0), false); args18861.Keyword("market", ([&]() -> Value { auto v18862 = s->LocalAt(7); return Binary("Add", v18862, s->LocalAt(12)); }())); return Call(c, fn18860, std::move(args18861)); }());
return {};
}
}  // namespace kagg::opponents::compiled
