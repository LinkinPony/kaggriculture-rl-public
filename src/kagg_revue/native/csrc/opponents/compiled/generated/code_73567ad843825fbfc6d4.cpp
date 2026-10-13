// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_73567ad843825fbfc6d4(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"act", "action", "avail", "b", "back", "best", "born", "bought", "bought_items", "configuration", "debts", "draw", "fixed", "got", "idx", "inv_now", "item", "k", "kind", "left", "movable", "moved", "native", "new", "o", "observation", "old", "orders", "owed", "own", "plan", "planned", "pos", "prev", "proj", "q", "refund", "rival", "score", "scored", "seat", "selling", "selling_items", "sells", "st", "step", "stock", "sval", "t", "take", "tape", "tiles", "v39", "value", "weakest", "y"};
s->PrepareSlots(s_names);
auto v22596 = ([&]() -> Value { auto fn22597 = s->Global("_OR2_PARENT"); Arguments args22598; args22598.positional.reserve(2); args22598.Add(s->LocalAt(25), false); args22598.Add(s->LocalAt(9), false); return Call(c, fn22597, std::move(args22598)); }());
s->SetAt(1, v22596);
try {
auto v22600 = ([&]() -> Value { auto fn22601 = s->Global("int"); Arguments args22602; args22602.Add(Get(s->LocalAt(25), Value("step")), false); return Call(c, fn22601, std::move(args22602)); }());
s->SetAt(45, v22600);
auto v22603 = ([&]() -> Value { auto fn22604 = s->Global("int"); Arguments args22605; args22605.Add(Get(s->LocalAt(25), Value("player")), false); return Call(c, fn22604, std::move(args22605)); }());
s->SetAt(40, v22603);
auto v22606 = ([&]() -> Value { auto fn22607 = PrepareDictionaryGet(s->Global("_OR2_STATE")); Arguments args22608; args22608.Add(s->LocalAt(40), false); return CallDictionaryGet(c, fn22607, std::move(args22608)); }());
s->SetAt(44, v22606);
if (static_cast<bool>(([&]() -> Value { auto v22609 = ([&]() -> Value { auto v22610 = s->LocalAt(45); Value v22611; v22611 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v22610, v22611))) return Value(false); v22610 = v22611; return Value(true); }()); if (static_cast<bool>(v22609)) return v22609; v22609 = ([&]() -> Value { auto v22612 = s->LocalAt(44); Value v22613; v22613 = Value{}; if (!static_cast<bool>(Binary("Is", v22612, v22613))) return Value(false); v22612 = v22613; return Value(true); }()); if (static_cast<bool>(v22609)) return v22609; v22609 = ([&]() -> Value { auto v22614 = s->LocalAt(45); Value v22615; v22615 = ([&]() -> Value { auto fn22616 = PrepareDictionaryGet(s->LocalAt(44)); Arguments args22617; args22617.positional.reserve(2); args22617.Add(Value("step"), false); args22617.Add(Unary("USub", Value(int64_t{1})), false); return CallDictionaryGet(c, fn22616, std::move(args22617)); }()); if (!static_cast<bool>(Binary("LtE", v22614, v22615))) return Value(false); v22614 = v22615; return Value(true); }()); return v22609; }()))) {
auto v22618 = ([&]() -> Value { auto dict22619 = Dict(); auto key22620 = Value("step"); Put(dict22619, key22620, Unary("USub", Value(int64_t{1}))); auto key22621 = Value("stock"); Put(dict22619, key22621, ([&]() -> Value { auto comp22622 = std::make_shared<Scope>(); comp22622->globals = s->globals; comp22622->parent = s; static constexpr const char* comp22622_names[] = {"i"}; comp22622->PrepareSlots(comp22622_names); auto result22623 = Dict(); for (const auto& item22624 : Iterate(s->Global("_OR2_ITEMS"))) { comp22622->SetAt(0, item22624); Put(result22623, comp22622->LocalAt(0), Value(int64_t{0})); } return result22623; }())); auto key22625 = Value("prev"); Put(dict22619, key22625, Value{}); return dict22619; }());
s->SetAt(44, v22618);
Put(s->Global("_OR2_STATE"), s->LocalAt(40), v22618);
if (static_cast<bool>(([&]() -> Value { auto v22626 = s->LocalAt(45); Value v22627; v22627 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v22626, v22627))) return Value(false); v22626 = v22627; return Value(true); }()))) {
for (const auto& item22628 : Iterate(s->Global("_OR2_REPORT"))) {
s->SetAt(17, item22628);
auto v22629 = Value(int64_t{0});
Put(s->Global("_OR2_REPORT"), s->LocalAt(17), v22629);
}
}
}
auto v22630 = Get(Get(s->LocalAt(25), Value("farms")), ([&]() -> Value { auto v22631 = Value(int64_t{1}); return Binary("Sub", v22631, s->LocalAt(40)); }()));
s->SetAt(37, v22630);
auto v22632 = ([&]() -> Value { auto fn22633 = s->Global("_or2_tiles"); Arguments args22634; args22634.Add(s->LocalAt(37), false); return Call(c, fn22633, std::move(args22634)); }());
s->SetAt(51, v22632);
auto v22635 = ([&]() -> Value { auto comp22636 = std::make_shared<Scope>(); comp22636->globals = s->globals; comp22636->parent = s; static constexpr const char* comp22636_names[] = {"i"}; comp22636->PrepareSlots(comp22636_names); auto result22637 = Dict(); for (const auto& item22638 : Iterate(s->Global("_OR2_ITEMS"))) { comp22636->SetAt(0, item22638); Put(result22637, comp22636->LocalAt(0), ([&]() -> Value { auto fn22639 = comp22636->Global("int"); Arguments args22640; args22640.Add(([&]() -> Value { auto fn22641 = PrepareDictionaryGet(Get(Get(comp22636->Captured("observation"), Value("market")), Value("inventory"))); Arguments args22642; args22642.positional.reserve(2); args22642.Add(comp22636->LocalAt(0), false); args22642.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn22641, std::move(args22642)); }()), false); return Call(c, fn22639, std::move(args22640)); }())); } return result22637; }());
s->SetAt(15, v22635);
auto v22643 = Get(s->LocalAt(44), Value("prev"));
s->SetAt(33, v22643);
if (static_cast<bool>(([&]() -> Value { auto v22644 = s->LocalAt(33); if (!static_cast<bool>(v22644)) return v22644; v22644 = ([&]() -> Value { auto v22645 = Get(s->LocalAt(33), Value("step")); Value v22646; v22646 = ([&]() -> Value { auto v22647 = s->LocalAt(45); return Binary("Sub", v22647, Value(int64_t{1})); }()); if (!static_cast<bool>(Binary("Eq", v22645, v22646))) return Value(false); v22645 = v22646; return Value(true); }()); return v22644; }()))) {
auto v22648 = Get(s->LocalAt(44), Value("stock"));
s->SetAt(46, v22648);
for (const auto& item22649 : Iterate(([&]() -> Value { auto fn22650 = Attribute(Get(s->LocalAt(33), Value("tiles")), "items"); Arguments args22651; return Call(c, fn22650, std::move(args22651)); }()))) {
auto unpack22652 = Iterate(item22649);
ValidateUnpack(unpack22652, 2, false);
s->SetAt(32, unpack22652.at(0));
s->SetAt(26, unpack22652.at(1));
auto v22653 = s->LocalAt(26);
auto unpack22654 = Iterate(v22653);
ValidateUnpack(unpack22654, 4, false);
s->SetAt(18, unpack22654.at(0));
s->SetAt(16, unpack22654.at(1));
s->SetAt(6, unpack22654.at(2));
s->SetAt(55, unpack22654.at(3));
if (static_cast<bool>(([&]() -> Value { auto v22655 = s->LocalAt(55); Value v22656; v22656 = Value(int64_t{0}); if (!static_cast<bool>(Binary("LtE", v22655, v22656))) return Value(false); v22655 = v22656; return Value(true); }()))) {
continue;
}
auto v22657 = ([&]() -> Value { auto fn22658 = PrepareDictionaryGet(s->LocalAt(51)); Arguments args22659; args22659.Add(s->LocalAt(32), false); return CallDictionaryGet(c, fn22658, std::move(args22659)); }());
s->SetAt(23, v22657);
auto v22660 = Value(int64_t{0});
s->SetAt(13, v22660);
if (static_cast<bool>(([&]() -> Value { auto v22661 = ([&]() -> Value { auto v22662 = s->LocalAt(18); Value v22663; v22663 = Value("P"); if (!static_cast<bool>(Binary("Eq", v22662, v22663))) return Value(false); v22662 = v22663; return Value(true); }()); if (!static_cast<bool>(v22661)) return v22661; v22661 = ([&]() -> Value { auto v22664 = s->LocalAt(16); Value v22665; v22665 = s->Global("_OR2_ONGOING"); if (!static_cast<bool>(Binary("NotIn", v22664, v22665))) return Value(false); v22664 = v22665; return Value(true); }()); return v22661; }()))) {
if (static_cast<bool>(([&]() -> Value { auto v22666 = ([&]() -> Value { auto v22667 = ([&]() -> Value { auto v22668 = s->LocalAt(23); Value v22669; v22669 = Value{}; if (!static_cast<bool>(Binary("Is", v22668, v22669))) return Value(false); v22668 = v22669; return Value(true); }()); if (!static_cast<bool>(v22667)) return v22667; v22667 = Unary("Not", ([&]() -> Value { auto fn22670 = s->Global("_OR2_WEED"); Arguments args22671; args22671.positional.reserve(2); args22671.Add(s->LocalAt(37), false); args22671.Add(s->LocalAt(32), false); return Call(c, fn22670, std::move(args22671)); }())); return v22667; }()); if (static_cast<bool>(v22666)) return v22666; v22666 = ([&]() -> Value { auto v22672 = ([&]() -> Value { auto v22673 = s->LocalAt(23); Value v22674; v22674 = Value{}; if (!static_cast<bool>(Binary("IsNot", v22673, v22674))) return Value(false); v22673 = v22674; return Value(true); }()); if (!static_cast<bool>(v22672)) return v22672; v22672 = ([&]() -> Value { auto v22675 = Get(s->LocalAt(23), Value(int64_t{2})); Value v22676; v22676 = s->LocalAt(6); if (!static_cast<bool>(Binary("NotEq", v22675, v22676))) return Value(false); v22675 = v22676; return Value(true); }()); return v22672; }()); return v22666; }()))) {
auto v22677 = s->LocalAt(55);
s->SetAt(13, v22677);
}
}
else {
if (static_cast<bool>(([&]() -> Value { auto v22678 = ([&]() -> Value { auto v22679 = s->LocalAt(23); Value v22680; v22680 = Value{}; if (!static_cast<bool>(Binary("IsNot", v22679, v22680))) return Value(false); v22679 = v22680; return Value(true); }()); if (!static_cast<bool>(v22678)) return v22678; v22678 = ([&]() -> Value { auto v22681 = Get(s->LocalAt(23), Value(int64_t{0})); Value v22682; v22682 = s->LocalAt(18); if (!static_cast<bool>(Binary("Eq", v22681, v22682))) return Value(false); v22681 = v22682; return Value(true); }()); if (!static_cast<bool>(v22678)) return v22678; v22678 = ([&]() -> Value { auto v22683 = Get(s->LocalAt(23), Value(int64_t{1})); Value v22684; v22684 = s->LocalAt(16); if (!static_cast<bool>(Binary("Eq", v22683, v22684))) return Value(false); v22683 = v22684; return Value(true); }()); if (!static_cast<bool>(v22678)) return v22678; v22678 = ([&]() -> Value { auto v22685 = Get(s->LocalAt(23), Value(int64_t{2})); Value v22686; v22686 = s->LocalAt(6); if (!static_cast<bool>(Binary("Eq", v22685, v22686))) return Value(false); v22685 = v22686; return Value(true); }()); if (!static_cast<bool>(v22678)) return v22678; v22678 = ([&]() -> Value { auto v22687 = Get(s->LocalAt(23), Value(int64_t{3})); Value v22688; v22688 = s->LocalAt(55); if (!static_cast<bool>(Binary("Lt", v22687, v22688))) return Value(false); v22687 = v22688; return Value(true); }()); return v22678; }()))) {
if (static_cast<bool>(([&]() -> Value { auto v22689 = ([&]() -> Value { auto v22691 = s->LocalAt(45); return Binary("Mod", v22691, Value(int64_t{24})); }()); Value v22690; v22690 = Value(int64_t{0}); if (!static_cast<bool>(Binary("NotEq", v22689, v22690))) return Value(false); v22689 = v22690; return Value(true); }()))) {
auto v22692 = ([&]() -> Value { auto v22693 = s->LocalAt(55); return Binary("Sub", v22693, Get(s->LocalAt(23), Value(int64_t{3}))); }());
s->SetAt(13, v22692);
}
else {
if (static_cast<bool>(([&]() -> Value { auto v22694 = Get(s->LocalAt(23), Value(int64_t{3})); Value v22695; v22695 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v22694, v22695))) return Value(false); v22694 = v22695; return Value(true); }()))) {
auto v22696 = s->LocalAt(55);
s->SetAt(13, v22696);
}
}
}
}
if (static_cast<bool>(([&]() -> Value { auto v22697 = s->LocalAt(13); Value v22698; v22698 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v22697, v22698))) return Value(false); v22697 = v22698; return Value(true); }()))) {
auto v22699 = ([&]() -> Value { auto v22700 = ([&]() -> Value { auto fn22701 = PrepareDictionaryGet(s->LocalAt(46)); Arguments args22702; args22702.positional.reserve(2); args22702.Add(s->LocalAt(16), false); args22702.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn22701, std::move(args22702)); }()); return Binary("Add", v22700, s->LocalAt(13)); }());
Put(s->LocalAt(46), s->LocalAt(16), v22699);
auto v22703 = s->Global("_OR2_REPORT");
auto v22704 = Value("or2_rival_harvest");
auto v22705 = Get(v22703, v22704);
Put(v22703, v22704, Inplace("Add", v22705, s->LocalAt(13)));
}
}
auto v22706 = ([&]() -> Value { auto fn22707 = s->Global("_or2_draw"); Arguments args22708; args22708.positional.reserve(2); args22708.Add(Get(s->LocalAt(33), Value("shops")), false); args22708.Add(Get(s->LocalAt(33), Value("step")), false); return Call(c, fn22707, std::move(args22708)); }());
s->SetAt(11, v22706);
for (const auto& item22709 : Iterate(s->Global("_OR2_ITEMS"))) {
s->SetAt(16, item22709);
if (static_cast<bool>(([&]() -> Value { auto v22710 = ([&]() -> Value { auto fn22712 = PrepareDictionaryGet(Get(s->LocalAt(33), Value("prices"))); Arguments args22713; args22713.positional.reserve(2); args22713.Add(s->LocalAt(16), false); args22713.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn22712, std::move(args22713)); }()); Value v22711; v22711 = Value(int64_t{1}); if (!static_cast<bool>(Binary("LtE", v22710, v22711))) return Value(false); v22710 = v22711; return Value(true); }()))) {
continue;
}
auto v22714 = ([&]() -> Value { auto v22715 = ([&]() -> Value { auto v22716 = ([&]() -> Value { auto v22717 = Get(s->LocalAt(15), s->LocalAt(16)); return Binary("Sub", v22717, Get(Get(s->LocalAt(33), Value("inv")), s->LocalAt(16))); }()); return Binary("Add", v22716, ([&]() -> Value { auto fn22718 = PrepareDictionaryGet(s->LocalAt(11)); Arguments args22719; args22719.positional.reserve(2); args22719.Add(s->LocalAt(16), false); args22719.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn22718, std::move(args22719)); }())); }()); return Binary("Sub", v22715, ([&]() -> Value { auto fn22720 = PrepareDictionaryGet(Get(s->LocalAt(33), Value("own"))); Arguments args22721; args22721.positional.reserve(2); args22721.Add(s->LocalAt(16), false); args22721.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn22720, std::move(args22721)); }())); }());
s->SetAt(21, v22714);
if (static_cast<bool>(([&]() -> Value { auto v22722 = s->LocalAt(21); Value v22723; v22723 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v22722, v22723))) return Value(false); v22722 = v22723; return Value(true); }()))) {
auto v22724 = ([&]() -> Value { auto fn22725 = s->Global("max"); Arguments args22726; args22726.positional.reserve(2); args22726.Add(Value(int64_t{0}), false); args22726.Add(([&]() -> Value { auto v22727 = ([&]() -> Value { auto fn22728 = PrepareDictionaryGet(s->LocalAt(46)); Arguments args22729; args22729.positional.reserve(2); args22729.Add(s->LocalAt(16), false); args22729.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn22728, std::move(args22729)); }()); return Binary("Sub", v22727, s->LocalAt(21)); }()), false); return Call(c, fn22725, std::move(args22726)); }());
Put(s->LocalAt(46), s->LocalAt(16), v22724);
auto v22730 = s->Global("_OR2_REPORT");
auto v22731 = Value("or2_rival_sold");
auto v22732 = Get(v22730, v22731);
Put(v22730, v22731, Inplace("Add", v22732, s->LocalAt(21)));
}
}
}
auto v22733 = ([&]() -> Value { auto dict22734 = Dict(); return dict22734; }());
s->SetAt(29, v22733);
if (static_cast<bool>(([&]() -> Value { auto fn22735 = s->Global("isinstance"); Arguments args22736; args22736.positional.reserve(2); args22736.Add(s->LocalAt(1), false); args22736.Add(s->Global("dict"), false); return Call(c, fn22735, std::move(args22736)); }()))) {
auto v22737 = ([&]() -> Value { auto comp22738 = std::make_shared<Scope>(); comp22738->globals = s->globals; comp22738->parent = s; static constexpr const char* comp22738_names[] = {"o"}; comp22738->PrepareSlots(comp22738_names); auto result22739 = List(); for (const auto& item22740 : Iterate(([&]() -> Value { auto v22741 = ([&]() -> Value { auto fn22742 = PrepareDictionaryGet(s->LocalAt(1)); Arguments args22743; args22743.Add(Value("market"), false); return CallDictionaryGet(c, fn22742, std::move(args22743)); }()); if (static_cast<bool>(v22741)) return v22741; v22741 = List({}); return v22741; }()))) { comp22738->SetAt(0, item22740); result22739.node()->sequence.push_back(([&]() -> Value { auto fn22744 = comp22738->Global("list"); Arguments args22745; args22745.Add(comp22738->LocalAt(0), false); return Call(c, fn22744, std::move(args22745)); }())); } return result22739; }());
s->SetAt(27, v22737);
auto v22746 = ([&]() -> Value { auto fn22747 = s->Global("dict"); Arguments args22748; args22748.Add(([&]() -> Value { auto fn22749 = s->Global("projected_shed"); Arguments args22750; args22750.positional.reserve(2); args22750.Add(s->LocalAt(1), false); args22750.Add(([&]() -> Value { auto fn22751 = s->Global("FarmView"); Arguments args22752; args22752.Add(s->LocalAt(25), false); return Call(c, fn22751, std::move(args22752)); }()), false); return Call(c, fn22749, std::move(args22750)); }()), false); return Call(c, fn22747, std::move(args22748)); }());
s->SetAt(34, v22746);
if (static_cast<bool>(([&]() -> Value { auto v22753 = ([&]() -> Value { auto v22754 = s->Global("_OR2_SN_K"); Value v22755; v22755 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v22754, v22755))) return Value(false); v22754 = v22755; return Value(true); }()); if (!static_cast<bool>(v22753)) return v22753; v22753 = ([&]() -> Value { auto v22756 = Value(int64_t{24}); Value v22757; v22757 = s->LocalAt(45); if (!static_cast<bool>(Binary("LtE", v22756, v22757))) return Value(false); v22756 = v22757; v22757 = Value(int64_t{694}); if (!static_cast<bool>(Binary("Lt", v22756, v22757))) return Value(false); v22756 = v22757; return Value(true); }()); return v22753; }()))) {
auto v22758 = ([&]() -> Value { auto fn22759 = PrepareDictionaryGet(Attribute(Attribute(s->Global("_IMPL"), "chassis"), "players")); Arguments args22760; args22760.Add(s->LocalAt(40), false); return CallDictionaryGet(c, fn22759, std::move(args22760)); }());
s->SetAt(22, v22758);
auto v22761 = (static_cast<bool>(s->LocalAt(22)) ? ([&]() -> Value { auto fn22762 = Attribute(Get(s->LocalAt(22), Value("sell_state")), "setdefault"); Arguments args22763; args22763.positional.reserve(2); args22763.Add(Value("r36_debts"), false); args22763.Add(([&]() -> Value { auto dict22764 = Dict(); return dict22764; }()), false); return Call(c, fn22762, std::move(args22763)); }()) : Value{});
s->SetAt(10, v22761);
for (const auto& item22765 : Iterate(s->Global("_OR2_SN_ITEMS"))) {
s->SetAt(16, item22765);
if (static_cast<bool>(([&]() -> Value { auto v22766 = ([&]() -> Value { auto v22767 = s->LocalAt(10); Value v22768; v22768 = Value{}; if (!static_cast<bool>(Binary("Is", v22767, v22768))) return Value(false); v22767 = v22768; return Value(true); }()); if (static_cast<bool>(v22766)) return v22766; v22766 = ([&]() -> Value { auto v22769 = ([&]() -> Value { auto fn22771 = s->Global("int"); Arguments args22772; args22772.Add(([&]() -> Value { auto fn22773 = PrepareDictionaryGet(Get(s->LocalAt(44), Value("stock"))); Arguments args22774; args22774.positional.reserve(2); args22774.Add(s->LocalAt(16), false); args22774.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn22773, std::move(args22774)); }()), false); return Call(c, fn22771, std::move(args22772)); }()); Value v22770; v22770 = s->Global("_OR2_SN_K"); if (!static_cast<bool>(Binary("Lt", v22769, v22770))) return Value(false); v22769 = v22770; return Value(true); }()); return v22766; }()))) {
continue;
}
if (static_cast<bool>(([&]() -> Value { auto v22775 = ([&]() -> Value { auto v22776 = ([&]() -> Value { auto fn22778 = s->Global("int"); Arguments args22779; args22779.Add(([&]() -> Value { auto fn22780 = PrepareDictionaryGet(Get(Get(s->LocalAt(25), Value("market")), Value("prices"))); Arguments args22781; args22781.positional.reserve(2); args22781.Add(s->LocalAt(16), false); args22781.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn22780, std::move(args22781)); }()), false); return Call(c, fn22778, std::move(args22779)); }()); Value v22777; v22777 = Value(int64_t{2}); if (!static_cast<bool>(Binary("Lt", v22776, v22777))) return Value(false); v22776 = v22777; return Value(true); }()); if (static_cast<bool>(v22775)) return v22775; v22775 = ([&]() -> Value { auto v22782 = ([&]() -> Value { auto fn22784 = s->Global("len"); Arguments args22785; args22785.Add(s->LocalAt(27), false); return Call(c, fn22784, std::move(args22785)); }()); Value v22783; v22783 = Value(int64_t{10}); if (!static_cast<bool>(Binary("GtE", v22782, v22783))) return Value(false); v22782 = v22783; return Value(true); }()); return v22775; }()))) {
continue;
}
if (static_cast<bool>(([&]() -> Value { auto comp22786 = std::make_shared<Scope>(); comp22786->globals = s->globals; comp22786->parent = s; static constexpr const char* comp22786_names[] = {"o"}; comp22786->PrepareSlots(comp22786_names); auto result22787 = List(); for (const auto& item22788 : Iterate(s->LocalAt(27))) { comp22786->SetAt(0, item22788); if (static_cast<bool>(([&]() -> Value { auto v22789 = ([&]() -> Value { auto v22790 = ([&]() -> Value { auto fn22792 = comp22786->Global("len"); Arguments args22793; args22793.Add(comp22786->LocalAt(0), false); return Call(c, fn22792, std::move(args22793)); }()); Value v22791; v22791 = Value(int64_t{2}); if (!static_cast<bool>(Binary("GtE", v22790, v22791))) return Value(false); v22790 = v22791; return Value(true); }()); if (!static_cast<bool>(v22789)) return v22789; v22789 = ([&]() -> Value { auto v22794 = Get(comp22786->LocalAt(0), Value(int64_t{0})); Value v22795; v22795 = Tuple({Value("BUY_PRODUCT"), Value("BUY_ANIMAL")}); if (!static_cast<bool>(Binary("In", v22794, v22795))) return Value(false); v22794 = v22795; return Value(true); }()); if (!static_cast<bool>(v22789)) return v22789; v22789 = ([&]() -> Value { auto v22796 = Get(comp22786->LocalAt(0), Value(int64_t{1})); Value v22797; v22797 = comp22786->Captured("item"); if (!static_cast<bool>(Binary("Eq", v22796, v22797))) return Value(false); v22796 = v22797; return Value(true); }()); return v22789; }()))) return Value(true); } return Value(false); }()))) {
continue;
}
auto v22798 = ([&]() -> Value { auto fn22799 = s->Global("sum"); Arguments args22800; args22800.Add(([&]() -> Value { auto comp22801 = std::make_shared<Scope>(); comp22801->globals = s->globals; comp22801->parent = s; static constexpr const char* comp22801_names[] = {"o"}; comp22801->PrepareSlots(comp22801_names); auto result22802 = List(); for (const auto& item22803 : Iterate(s->LocalAt(27))) { comp22801->SetAt(0, item22803); if (!static_cast<bool>(([&]() -> Value { auto v22804 = ([&]() -> Value { auto v22805 = ([&]() -> Value { auto fn22807 = comp22801->Global("len"); Arguments args22808; args22808.Add(comp22801->LocalAt(0), false); return Call(c, fn22807, std::move(args22808)); }()); Value v22806; v22806 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v22805, v22806))) return Value(false); v22805 = v22806; return Value(true); }()); if (!static_cast<bool>(v22804)) return v22804; v22804 = ([&]() -> Value { auto v22809 = Get(comp22801->LocalAt(0), Value(int64_t{0})); Value v22810; v22810 = Value("SELL"); if (!static_cast<bool>(Binary("Eq", v22809, v22810))) return Value(false); v22809 = v22810; return Value(true); }()); if (!static_cast<bool>(v22804)) return v22804; v22804 = ([&]() -> Value { auto v22811 = Get(comp22801->LocalAt(0), Value(int64_t{1})); Value v22812; v22812 = comp22801->Captured("item"); if (!static_cast<bool>(Binary("Eq", v22811, v22812))) return Value(false); v22811 = v22812; return Value(true); }()); return v22804; }()))) continue; result22802.node()->sequence.push_back(([&]() -> Value { auto fn22813 = comp22801->Global("max"); Arguments args22814; args22814.positional.reserve(2); args22814.Add(Value(int64_t{0}), false); args22814.Add(([&]() -> Value { auto fn22815 = comp22801->Global("int"); Arguments args22816; args22816.Add(Get(comp22801->LocalAt(0), Value(int64_t{2})), false); return Call(c, fn22815, std::move(args22816)); }()), false); return Call(c, fn22813, std::move(args22814)); }())); } return result22802; }()), false); return Call(c, fn22799, std::move(args22800)); }());
s->SetAt(41, v22798);
auto v22817 = ([&]() -> Value { auto v22818 = ([&]() -> Value { auto fn22819 = s->Global("int"); Arguments args22820; args22820.Add(([&]() -> Value { auto fn22821 = PrepareDictionaryGet(s->LocalAt(34)); Arguments args22822; args22822.positional.reserve(2); args22822.Add(s->LocalAt(16), false); args22822.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn22821, std::move(args22822)); }()), false); return Call(c, fn22819, std::move(args22820)); }()); return Binary("Sub", v22818, s->LocalAt(41)); }());
s->SetAt(2, v22817);
auto v22823 = Value(int64_t{0});
s->SetAt(49, v22823);
for (const auto& item22824 : Iterate(([&]() -> Value { auto fn22825 = s->Global("range"); Arguments args22826; args22826.positional.reserve(2); args22826.Add(([&]() -> Value { auto v22827 = s->LocalAt(45); return Binary("Add", v22827, Value(int64_t{1})); }()), false); args22826.Add(([&]() -> Value { auto v22828 = ([&]() -> Value { auto fn22829 = s->Global("min"); Arguments args22830; args22830.positional.reserve(2); args22830.Add(Value(int64_t{694}), false); args22830.Add(([&]() -> Value { auto v22831 = s->LocalAt(45); return Binary("Add", v22831, s->Global("_OR2_SN_H")); }()), false); return Call(c, fn22829, std::move(args22830)); }()); return Binary("Add", v22828, Value(int64_t{1})); }()), false); return Call(c, fn22825, std::move(args22826)); }()))) {
s->SetAt(48, item22824);
if (static_cast<bool>(([&]() -> Value { auto v22832 = s->LocalAt(49); Value v22833; v22833 = s->LocalAt(2); if (!static_cast<bool>(Binary("GtE", v22832, v22833))) return Value(false); v22832 = v22833; return Value(true); }()))) {
break;
}
auto v22834 = Get(Attribute(Attribute(s->Global("_IMPL"), "chassis"), "routes"), (static_cast<bool>(([&]() -> Value { auto v22835 = s->LocalAt(48); Value v22836; v22836 = Value(int64_t{648}); if (!static_cast<bool>(Binary("GtE", v22835, v22836))) return Value(false); v22835 = v22836; return Value(true); }())) ? Value(int64_t{2}) : Get(s->LocalAt(22), Value("route"))));
s->SetAt(50, v22834);
auto v22837 = (static_cast<bool>(([&]() -> Value { auto v22838 = ([&]() -> Value { auto v22839 = s->LocalAt(48); Value v22840; v22840 = ([&]() -> Value { auto fn22841 = s->Global("len"); Arguments args22842; args22842.Add(s->LocalAt(50), false); return Call(c, fn22841, std::move(args22842)); }()); if (!static_cast<bool>(Binary("Lt", v22839, v22840))) return Value(false); v22839 = v22840; return Value(true); }()); if (!static_cast<bool>(v22838)) return v22838; v22838 = ([&]() -> Value { auto fn22843 = s->Global("isinstance"); Arguments args22844; args22844.positional.reserve(2); args22844.Add(Get(s->LocalAt(50), s->LocalAt(48)), false); args22844.Add(s->Global("dict"), false); return Call(c, fn22843, std::move(args22844)); }()); return v22838; }())) ? Get(s->LocalAt(50), s->LocalAt(48)) : ([&]() -> Value { auto dict22845 = Dict(); return dict22845; }()));
s->SetAt(0, v22837);
auto v22846 = ([&]() -> Value { auto fn22847 = s->Global("sum"); Arguments args22848; args22848.Add(([&]() -> Value { auto comp22849 = std::make_shared<Scope>(); comp22849->globals = s->globals; comp22849->parent = s; static constexpr const char* comp22849_names[] = {"o"}; comp22849->PrepareSlots(comp22849_names); auto result22850 = List(); for (const auto& item22851 : Iterate(([&]() -> Value { auto v22852 = ([&]() -> Value { auto fn22853 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args22854; args22854.Add(Value("market"), false); return CallDictionaryGet(c, fn22853, std::move(args22854)); }()); if (static_cast<bool>(v22852)) return v22852; v22852 = List({}); return v22852; }()))) { comp22849->SetAt(0, item22851); if (!static_cast<bool>(([&]() -> Value { auto v22855 = ([&]() -> Value { auto v22856 = ([&]() -> Value { auto fn22858 = comp22849->Global("len"); Arguments args22859; args22859.Add(comp22849->LocalAt(0), false); return Call(c, fn22858, std::move(args22859)); }()); Value v22857; v22857 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v22856, v22857))) return Value(false); v22856 = v22857; return Value(true); }()); if (!static_cast<bool>(v22855)) return v22855; v22855 = ([&]() -> Value { auto v22860 = Get(comp22849->LocalAt(0), Value(int64_t{0})); Value v22861; v22861 = Value("SELL"); if (!static_cast<bool>(Binary("Eq", v22860, v22861))) return Value(false); v22860 = v22861; return Value(true); }()); if (!static_cast<bool>(v22855)) return v22855; v22855 = ([&]() -> Value { auto v22862 = Get(comp22849->LocalAt(0), Value(int64_t{1})); Value v22863; v22863 = comp22849->Captured("item"); if (!static_cast<bool>(Binary("Eq", v22862, v22863))) return Value(false); v22862 = v22863; return Value(true); }()); return v22855; }()))) continue; result22850.node()->sequence.push_back(([&]() -> Value { auto fn22864 = comp22849->Global("max"); Arguments args22865; args22865.positional.reserve(2); args22865.Add(Value(int64_t{0}), false); args22865.Add(([&]() -> Value { auto fn22866 = comp22849->Global("int"); Arguments args22867; args22867.Add(Get(comp22849->LocalAt(0), Value(int64_t{2})), false); return Call(c, fn22866, std::move(args22867)); }()), false); return Call(c, fn22864, std::move(args22865)); }())); } return result22850; }()), false); return Call(c, fn22847, std::move(args22848)); }());
s->SetAt(31, v22846);
auto v22868 = s->LocalAt(31);
s->SetAt(31, Inplace("Sub", v22868, ([&]() -> Value { auto fn22869 = PrepareDictionaryGet(([&]() -> Value { auto fn22871 = PrepareDictionaryGet(s->LocalAt(10)); Arguments args22872; args22872.positional.reserve(2); args22872.Add(s->LocalAt(48), false); args22872.Add(([&]() -> Value { auto dict22873 = Dict(); return dict22873; }()), false); return CallDictionaryGet(c, fn22871, std::move(args22872)); }())); Arguments args22870; args22870.positional.reserve(2); args22870.Add(s->LocalAt(16), false); args22870.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn22869, std::move(args22870)); }())));
auto v22874 = ([&]() -> Value { auto fn22875 = s->Global("min"); Arguments args22876; args22876.positional.reserve(2); args22876.Add(s->LocalAt(31), false); args22876.Add(([&]() -> Value { auto v22877 = s->LocalAt(2); return Binary("Sub", v22877, s->LocalAt(49)); }()), false); return Call(c, fn22875, std::move(args22876)); }());
s->SetAt(35, v22874);
if (static_cast<bool>(([&]() -> Value { auto v22878 = s->LocalAt(35); Value v22879; v22879 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v22878, v22879))) return Value(false); v22878 = v22879; return Value(true); }()))) {
auto v22880 = ([&]() -> Value { auto v22881 = ([&]() -> Value { auto fn22882 = PrepareDictionaryGet(([&]() -> Value { auto fn22884 = PrepareDictionaryGet(s->LocalAt(10)); Arguments args22885; args22885.positional.reserve(2); args22885.Add(s->LocalAt(48), false); args22885.Add(([&]() -> Value { auto dict22886 = Dict(); return dict22886; }()), false); return CallDictionaryGet(c, fn22884, std::move(args22885)); }())); Arguments args22883; args22883.positional.reserve(2); args22883.Add(s->LocalAt(16), false); args22883.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn22882, std::move(args22883)); }()); return Binary("Add", v22881, s->LocalAt(35)); }());
Put(([&]() -> Value { auto fn22887 = Attribute(s->LocalAt(10), "setdefault"); Arguments args22888; args22888.positional.reserve(2); args22888.Add(s->LocalAt(48), false); args22888.Add(([&]() -> Value { auto dict22889 = Dict(); return dict22889; }()), false); return Call(c, fn22887, std::move(args22888)); }()), s->LocalAt(16), v22880);
auto v22890 = s->LocalAt(49);
s->SetAt(49, Inplace("Add", v22890, s->LocalAt(35)));
}
}
if (static_cast<bool>(([&]() -> Value { auto v22891 = s->LocalAt(49); Value v22892; v22892 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v22891, v22892))) return Value(false); v22891 = v22892; return Value(true); }()))) {
bool exhausted22893 = true;
for (const auto& item22894 : Iterate(s->LocalAt(27))) {
s->SetAt(24, item22894);
if (static_cast<bool>(([&]() -> Value { auto v22895 = ([&]() -> Value { auto v22896 = ([&]() -> Value { auto fn22898 = s->Global("len"); Arguments args22899; args22899.Add(s->LocalAt(24), false); return Call(c, fn22898, std::move(args22899)); }()); Value v22897; v22897 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v22896, v22897))) return Value(false); v22896 = v22897; return Value(true); }()); if (!static_cast<bool>(v22895)) return v22895; v22895 = ([&]() -> Value { auto v22900 = Get(s->LocalAt(24), Value(int64_t{0})); Value v22901; v22901 = Value("SELL"); if (!static_cast<bool>(Binary("Eq", v22900, v22901))) return Value(false); v22900 = v22901; return Value(true); }()); if (!static_cast<bool>(v22895)) return v22895; v22895 = ([&]() -> Value { auto v22902 = Get(s->LocalAt(24), Value(int64_t{1})); Value v22903; v22903 = s->LocalAt(16); if (!static_cast<bool>(Binary("Eq", v22902, v22903))) return Value(false); v22902 = v22903; return Value(true); }()); return v22895; }()))) {
auto v22904 = ([&]() -> Value { auto v22905 = ([&]() -> Value { auto fn22906 = s->Global("int"); Arguments args22907; args22907.Add(Get(s->LocalAt(24), Value(int64_t{2})), false); return Call(c, fn22906, std::move(args22907)); }()); return Binary("Add", v22905, s->LocalAt(49)); }());
Put(s->LocalAt(24), Value(int64_t{2}), v22904);
exhausted22893 = false;
break;
}
}
if (exhausted22893) {
(void)([&]() -> Value { auto fn22908 = Attribute(s->LocalAt(27), "append"); Arguments args22909; args22909.Add(List({Value("SELL"), s->LocalAt(16), s->LocalAt(49)}), false); return Call(c, fn22908, std::move(args22909)); }());
}
auto v22910 = ([&]() -> Value { auto v22911 = ([&]() -> Value { auto fn22912 = PrepareDictionaryGet(s->Global("_OR2_REPORT")); Arguments args22913; args22913.positional.reserve(2); args22913.Add(Value("or2_sellnow"), false); args22913.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn22912, std::move(args22913)); }()); return Binary("Add", v22911, s->LocalAt(49)); }());
Put(s->Global("_OR2_REPORT"), Value("or2_sellnow"), v22910);
auto v22914 = ([&]() -> Value { auto fn22915 = s->Global("dict"); Arguments args22916; args22916.Add(s->LocalAt(1), false); return Call(c, fn22915, std::move(args22916)); }());
s->SetAt(1, v22914);
auto v22917 = s->LocalAt(27);
Put(s->LocalAt(1), Value("market"), v22917);
}
}
}
if (static_cast<bool>(([&]() -> Value { auto v22918 = ([&]() -> Value { auto v22919 = s->Global("_OR2_SLOT_H"); Value v22920; v22920 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v22919, v22920))) return Value(false); v22919 = v22920; return Value(true); }()); if (!static_cast<bool>(v22918)) return v22918; v22918 = ([&]() -> Value { auto v22921 = Value(int64_t{288}); Value v22922; v22922 = s->LocalAt(45); if (!static_cast<bool>(Binary("LtE", v22921, v22922))) return Value(false); v22921 = v22922; v22922 = Value(int64_t{694}); if (!static_cast<bool>(Binary("Lt", v22921, v22922))) return Value(false); v22921 = v22922; return Value(true); }()); if (!static_cast<bool>(v22918)) return v22918; v22918 = ([&]() -> Value { auto v22923 = ([&]() -> Value { auto fn22925 = s->Global("len"); Arguments args22926; args22926.Add(s->LocalAt(27), false); return Call(c, fn22925, std::move(args22926)); }()); Value v22924; v22924 = Value(int64_t{10}); if (!static_cast<bool>(Binary("GtE", v22923, v22924))) return Value(false); v22923 = v22924; return Value(true); }()); return v22918; }()))) {
auto v22927 = ([&]() -> Value { auto fn22928 = PrepareDictionaryGet(Attribute(Attribute(s->Global("_IMPL"), "chassis"), "players")); Arguments args22929; args22929.Add(s->LocalAt(40), false); return CallDictionaryGet(c, fn22928, std::move(args22929)); }());
s->SetAt(22, v22927);
auto v22930 = (static_cast<bool>(s->LocalAt(22)) ? ([&]() -> Value { auto fn22931 = Attribute(Get(s->LocalAt(22), Value("sell_state")), "setdefault"); Arguments args22932; args22932.positional.reserve(2); args22932.Add(Value("r36_debts"), false); args22932.Add(([&]() -> Value { auto dict22933 = Dict(); return dict22933; }()), false); return Call(c, fn22931, std::move(args22932)); }()) : Value{});
s->SetAt(10, v22930);
auto v22934 = ([&]() -> Value { auto comp22935 = std::make_shared<Scope>(); comp22935->globals = s->globals; comp22935->parent = s; static constexpr const char* comp22935_names[] = {"o"}; comp22935->PrepareSlots(comp22935_names); auto result22936 = List(); for (const auto& item22937 : Iterate(s->LocalAt(27))) { comp22935->SetAt(0, item22937); if (!static_cast<bool>(([&]() -> Value { auto v22938 = ([&]() -> Value { auto v22939 = ([&]() -> Value { auto fn22941 = comp22935->Global("len"); Arguments args22942; args22942.Add(comp22935->LocalAt(0), false); return Call(c, fn22941, std::move(args22942)); }()); Value v22940; v22940 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v22939, v22940))) return Value(false); v22939 = v22940; return Value(true); }()); if (!static_cast<bool>(v22938)) return v22938; v22938 = ([&]() -> Value { auto v22943 = Get(comp22935->LocalAt(0), Value(int64_t{0})); Value v22944; v22944 = Value("SELL"); if (!static_cast<bool>(Binary("Eq", v22943, v22944))) return Value(false); v22943 = v22944; return Value(true); }()); return v22938; }()))) continue; result22936.node()->sequence.push_back(comp22935->LocalAt(0)); } return result22936; }());
s->SetAt(43, v22934);
auto v22945 = ([&]() -> Value { auto comp22946 = std::make_shared<Scope>(); comp22946->globals = s->globals; comp22946->parent = s; static constexpr const char* comp22946_names[] = {"o"}; comp22946->PrepareSlots(comp22946_names); auto result22947 = List(); for (const auto& item22948 : Iterate(s->LocalAt(43))) { comp22946->SetAt(0, item22948); result22947.node()->sequence.push_back(Get(comp22946->LocalAt(0), Value(int64_t{1}))); } return Set(result22947.node()->sequence); }());
s->SetAt(42, v22945);
auto v22949 = ([&]() -> Value { auto comp22950 = std::make_shared<Scope>(); comp22950->globals = s->globals; comp22950->parent = s; static constexpr const char* comp22950_names[] = {"o"}; comp22950->PrepareSlots(comp22950_names); auto result22951 = List(); for (const auto& item22952 : Iterate(s->LocalAt(27))) { comp22950->SetAt(0, item22952); if (!static_cast<bool>(([&]() -> Value { auto v22953 = ([&]() -> Value { auto v22954 = ([&]() -> Value { auto fn22956 = comp22950->Global("len"); Arguments args22957; args22957.Add(comp22950->LocalAt(0), false); return Call(c, fn22956, std::move(args22957)); }()); Value v22955; v22955 = Value(int64_t{2}); if (!static_cast<bool>(Binary("GtE", v22954, v22955))) return Value(false); v22954 = v22955; return Value(true); }()); if (!static_cast<bool>(v22953)) return v22953; v22953 = ([&]() -> Value { auto v22958 = Get(comp22950->LocalAt(0), Value(int64_t{0})); Value v22959; v22959 = Tuple({Value("BUY_PRODUCT"), Value("BUY_ANIMAL")}); if (!static_cast<bool>(Binary("In", v22958, v22959))) return Value(false); v22958 = v22959; return Value(true); }()); return v22953; }()))) continue; result22951.node()->sequence.push_back(Get(comp22950->LocalAt(0), Value(int64_t{1}))); } return Set(result22951.node()->sequence); }());
s->SetAt(8, v22949);
auto v22960 = Value{};
s->SetAt(5, v22960);
for (const auto& item22961 : Iterate(s->Global("_OR2_SN_ITEMS"))) {
s->SetAt(16, item22961);
if (static_cast<bool>(([&]() -> Value { auto v22962 = ([&]() -> Value { auto v22963 = s->LocalAt(10); Value v22964; v22964 = Value{}; if (!static_cast<bool>(Binary("Is", v22963, v22964))) return Value(false); v22963 = v22964; return Value(true); }()); if (static_cast<bool>(v22962)) return v22962; v22962 = ([&]() -> Value { auto v22965 = s->LocalAt(16); Value v22966; v22966 = s->LocalAt(42); if (!static_cast<bool>(Binary("In", v22965, v22966))) return Value(false); v22965 = v22966; return Value(true); }()); if (static_cast<bool>(v22962)) return v22962; v22962 = ([&]() -> Value { auto v22967 = s->LocalAt(16); Value v22968; v22968 = s->LocalAt(8); if (!static_cast<bool>(Binary("In", v22967, v22968))) return Value(false); v22967 = v22968; return Value(true); }()); return v22962; }()))) {
continue;
}
auto v22969 = ([&]() -> Value { auto fn22970 = s->Global("int"); Arguments args22971; args22971.Add(([&]() -> Value { auto fn22972 = PrepareDictionaryGet(s->LocalAt(34)); Arguments args22973; args22973.positional.reserve(2); args22973.Add(s->LocalAt(16), false); args22973.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn22972, std::move(args22973)); }()), false); return Call(c, fn22970, std::move(args22971)); }());
s->SetAt(2, v22969);
if (static_cast<bool>(([&]() -> Value { auto v22974 = ([&]() -> Value { auto v22975 = s->LocalAt(2); Value v22976; v22976 = Value(int64_t{0}); if (!static_cast<bool>(Binary("LtE", v22975, v22976))) return Value(false); v22975 = v22976; return Value(true); }()); if (static_cast<bool>(v22974)) return v22974; v22974 = ([&]() -> Value { auto v22977 = ([&]() -> Value { auto fn22979 = s->Global("int"); Arguments args22980; args22980.Add(([&]() -> Value { auto fn22981 = PrepareDictionaryGet(Get(Get(s->LocalAt(25), Value("market")), Value("prices"))); Arguments args22982; args22982.positional.reserve(2); args22982.Add(s->LocalAt(16), false); args22982.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn22981, std::move(args22982)); }()), false); return Call(c, fn22979, std::move(args22980)); }()); Value v22978; v22978 = Value(int64_t{2}); if (!static_cast<bool>(Binary("Lt", v22977, v22978))) return Value(false); v22977 = v22978; return Value(true); }()); return v22974; }()))) {
continue;
}
auto v22983 = Tuple({List({}), Value(int64_t{0})});
auto unpack22984 = Iterate(v22983);
ValidateUnpack(unpack22984, 2, false);
s->SetAt(30, unpack22984.at(0));
s->SetAt(49, unpack22984.at(1));
for (const auto& item22985 : Iterate(([&]() -> Value { auto fn22986 = s->Global("range"); Arguments args22987; args22987.positional.reserve(2); args22987.Add(([&]() -> Value { auto v22988 = s->LocalAt(45); return Binary("Add", v22988, Value(int64_t{1})); }()), false); args22987.Add(([&]() -> Value { auto v22989 = ([&]() -> Value { auto fn22990 = s->Global("min"); Arguments args22991; args22991.positional.reserve(2); args22991.Add(Value(int64_t{694}), false); args22991.Add(([&]() -> Value { auto v22992 = s->LocalAt(45); return Binary("Add", v22992, s->Global("_OR2_SLOT_H")); }()), false); return Call(c, fn22990, std::move(args22991)); }()); return Binary("Add", v22989, Value(int64_t{1})); }()), false); return Call(c, fn22986, std::move(args22987)); }()))) {
s->SetAt(48, item22985);
if (static_cast<bool>(([&]() -> Value { auto v22993 = s->LocalAt(49); Value v22994; v22994 = s->LocalAt(2); if (!static_cast<bool>(Binary("GtE", v22993, v22994))) return Value(false); v22993 = v22994; return Value(true); }()))) {
break;
}
auto v22995 = Get(Attribute(Attribute(s->Global("_IMPL"), "chassis"), "routes"), (static_cast<bool>(([&]() -> Value { auto v22996 = s->LocalAt(48); Value v22997; v22997 = Value(int64_t{648}); if (!static_cast<bool>(Binary("GtE", v22996, v22997))) return Value(false); v22996 = v22997; return Value(true); }())) ? Value(int64_t{2}) : Get(s->LocalAt(22), Value("route"))));
s->SetAt(50, v22995);
auto v22998 = (static_cast<bool>(([&]() -> Value { auto v22999 = ([&]() -> Value { auto v23000 = s->LocalAt(48); Value v23001; v23001 = ([&]() -> Value { auto fn23002 = s->Global("len"); Arguments args23003; args23003.Add(s->LocalAt(50), false); return Call(c, fn23002, std::move(args23003)); }()); if (!static_cast<bool>(Binary("Lt", v23000, v23001))) return Value(false); v23000 = v23001; return Value(true); }()); if (!static_cast<bool>(v22999)) return v22999; v22999 = ([&]() -> Value { auto fn23004 = s->Global("isinstance"); Arguments args23005; args23005.positional.reserve(2); args23005.Add(Get(s->LocalAt(50), s->LocalAt(48)), false); args23005.Add(s->Global("dict"), false); return Call(c, fn23004, std::move(args23005)); }()); return v22999; }())) ? Get(s->LocalAt(50), s->LocalAt(48)) : ([&]() -> Value { auto dict23006 = Dict(); return dict23006; }()));
s->SetAt(0, v22998);
auto v23007 = ([&]() -> Value { auto fn23008 = s->Global("sum"); Arguments args23009; args23009.Add(([&]() -> Value { auto comp23010 = std::make_shared<Scope>(); comp23010->globals = s->globals; comp23010->parent = s; static constexpr const char* comp23010_names[] = {"o"}; comp23010->PrepareSlots(comp23010_names); auto result23011 = List(); for (const auto& item23012 : Iterate(([&]() -> Value { auto v23013 = ([&]() -> Value { auto fn23014 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args23015; args23015.Add(Value("market"), false); return CallDictionaryGet(c, fn23014, std::move(args23015)); }()); if (static_cast<bool>(v23013)) return v23013; v23013 = List({}); return v23013; }()))) { comp23010->SetAt(0, item23012); if (!static_cast<bool>(([&]() -> Value { auto v23016 = ([&]() -> Value { auto v23017 = ([&]() -> Value { auto fn23019 = comp23010->Global("len"); Arguments args23020; args23020.Add(comp23010->LocalAt(0), false); return Call(c, fn23019, std::move(args23020)); }()); Value v23018; v23018 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v23017, v23018))) return Value(false); v23017 = v23018; return Value(true); }()); if (!static_cast<bool>(v23016)) return v23016; v23016 = ([&]() -> Value { auto v23021 = Get(comp23010->LocalAt(0), Value(int64_t{0})); Value v23022; v23022 = Value("SELL"); if (!static_cast<bool>(Binary("Eq", v23021, v23022))) return Value(false); v23021 = v23022; return Value(true); }()); if (!static_cast<bool>(v23016)) return v23016; v23016 = ([&]() -> Value { auto v23023 = Get(comp23010->LocalAt(0), Value(int64_t{1})); Value v23024; v23024 = comp23010->Captured("item"); if (!static_cast<bool>(Binary("Eq", v23023, v23024))) return Value(false); v23023 = v23024; return Value(true); }()); return v23016; }()))) continue; result23011.node()->sequence.push_back(([&]() -> Value { auto fn23025 = comp23010->Global("max"); Arguments args23026; args23026.positional.reserve(2); args23026.Add(Value(int64_t{0}), false); args23026.Add(([&]() -> Value { auto fn23027 = comp23010->Global("int"); Arguments args23028; args23028.Add(Get(comp23010->LocalAt(0), Value(int64_t{2})), false); return Call(c, fn23027, std::move(args23028)); }()), false); return Call(c, fn23025, std::move(args23026)); }())); } return result23011; }()), false); return Call(c, fn23008, std::move(args23009)); }());
s->SetAt(31, v23007);
auto v23029 = ([&]() -> Value { auto fn23030 = s->Global("min"); Arguments args23031; args23031.positional.reserve(2); args23031.Add(([&]() -> Value { auto v23032 = s->LocalAt(31); return Binary("Sub", v23032, ([&]() -> Value { auto fn23033 = PrepareDictionaryGet(([&]() -> Value { auto fn23035 = PrepareDictionaryGet(s->LocalAt(10)); Arguments args23036; args23036.positional.reserve(2); args23036.Add(s->LocalAt(48), false); args23036.Add(([&]() -> Value { auto dict23037 = Dict(); return dict23037; }()), false); return CallDictionaryGet(c, fn23035, std::move(args23036)); }())); Arguments args23034; args23034.positional.reserve(2); args23034.Add(s->LocalAt(16), false); args23034.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn23033, std::move(args23034)); }())); }()), false); args23031.Add(([&]() -> Value { auto v23038 = s->LocalAt(2); return Binary("Sub", v23038, s->LocalAt(49)); }()), false); return Call(c, fn23030, std::move(args23031)); }());
s->SetAt(35, v23029);
if (static_cast<bool>(([&]() -> Value { auto v23039 = s->LocalAt(35); Value v23040; v23040 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v23039, v23040))) return Value(false); v23039 = v23040; return Value(true); }()))) {
(void)([&]() -> Value { auto fn23041 = Attribute(s->LocalAt(30), "append"); Arguments args23042; args23042.Add(Tuple({s->LocalAt(48), s->LocalAt(35)}), false); return Call(c, fn23041, std::move(args23042)); }());
auto v23043 = s->LocalAt(49);
s->SetAt(49, Inplace("Add", v23043, s->LocalAt(35)));
}
}
if (static_cast<bool>(([&]() -> Value { auto v23044 = s->LocalAt(49); Value v23045; v23045 = Value(int64_t{0}); if (!static_cast<bool>(Binary("LtE", v23044, v23045))) return Value(false); v23044 = v23045; return Value(true); }()))) {
continue;
}
auto v23046 = ([&]() -> Value { auto fn23047 = s->Global("min"); Arguments args23048; args23048.positional.reserve(2); args23048.Add(s->Global("_OR2_CAP"), false); args23048.Add(([&]() -> Value { auto fn23049 = s->Global("int"); Arguments args23050; args23050.Add(([&]() -> Value { auto fn23051 = PrepareDictionaryGet(Get(s->LocalAt(44), Value("stock"))); Arguments args23052; args23052.positional.reserve(2); args23052.Add(s->LocalAt(16), false); args23052.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn23051, std::move(args23052)); }()), false); return Call(c, fn23049, std::move(args23050)); }()), false); return Call(c, fn23047, std::move(args23048)); }());
s->SetAt(3, v23046);
auto v23053 = ([&]() -> Value { auto fn23054 = s->Global("_or2_exposure"); Arguments args23055; args23055.positional.reserve(4); args23055.Add(s->LocalAt(25), false); args23055.Add(s->LocalAt(16), false); args23055.Add(s->LocalAt(49), false); args23055.Add(([&]() -> Value { auto fn23056 = s->Global("max"); Arguments args23057; args23057.positional.reserve(2); args23057.Add(Value(int64_t{1}), false); args23057.Add(s->LocalAt(3), false); return Call(c, fn23056, std::move(args23057)); }()), false); return Call(c, fn23054, std::move(args23055)); }());
s->SetAt(53, v23053);
if (static_cast<bool>(([&]() -> Value { auto v23058 = ([&]() -> Value { auto v23059 = s->LocalAt(5); Value v23060; v23060 = Value{}; if (!static_cast<bool>(Binary("Is", v23059, v23060))) return Value(false); v23059 = v23060; return Value(true); }()); if (static_cast<bool>(v23058)) return v23058; v23058 = ([&]() -> Value { auto v23061 = s->LocalAt(53); Value v23062; v23062 = Get(s->LocalAt(5), Value(int64_t{0})); if (!static_cast<bool>(Binary("Gt", v23061, v23062))) return Value(false); v23061 = v23062; return Value(true); }()); return v23058; }()))) {
auto v23063 = Tuple({s->LocalAt(53), s->LocalAt(16), s->LocalAt(49), s->LocalAt(30)});
s->SetAt(5, v23063);
}
}
if (static_cast<bool>(([&]() -> Value { auto v23064 = ([&]() -> Value { auto v23065 = s->LocalAt(5); Value v23066; v23066 = Value{}; if (!static_cast<bool>(Binary("IsNot", v23065, v23066))) return Value(false); v23065 = v23066; return Value(true); }()); if (!static_cast<bool>(v23064)) return v23064; v23064 = s->LocalAt(43); return v23064; }()))) {
s->SetAt(47, Define(&Code_eb7f503974c0d1160bd7, s, Signature{{"o"}, {}, {}, {}, "", "", ([]() -> std::span<const char* const> { static constexpr const char* names[] = {"o", "q"}; return names; }())}, true, "sval"));
s->definitions.push_back("sval");
auto v23090 = ([&]() -> Value { auto fn23091 = s->Global("min"); Arguments args23092; args23092.Add(s->LocalAt(43), false); args23092.Keyword("key", s->LocalAt(47)); return Call(c, fn23091, std::move(args23092)); }());
s->SetAt(54, v23090);
if (static_cast<bool>(([&]() -> Value { auto v23093 = ([&]() -> Value { auto v23094 = ([&]() -> Value { auto v23095 = Get(s->LocalAt(5), Value(int64_t{0})); Value v23096; v23096 = ([&]() -> Value { auto v23097 = ([&]() -> Value { auto fn23098 = s->LocalAt(47); Arguments args23099; args23099.Add(s->LocalAt(54), false); return Call(c, fn23098, std::move(args23099)); }()); return Binary("Add", v23097, s->Global("_OR2_SLOT_MARGIN")); }()); if (!static_cast<bool>(Binary("Gt", v23095, v23096))) return Value(false); v23095 = v23096; return Value(true); }()); if (!static_cast<bool>(v23094)) return v23094; v23094 = ([&]() -> Value { auto v23100 = Get(s->LocalAt(54), Value(int64_t{1})); Value v23101; v23101 = Tuple({Value("WHEAT"), Value("FERTILIZER")}); if (!static_cast<bool>(Binary("NotIn", v23100, v23101))) return Value(false); v23100 = v23101; return Value(true); }()); return v23094; }()); if (static_cast<bool>(v23093)) return v23093; v23093 = ([&]() -> Value { auto v23102 = ([&]() -> Value { auto v23103 = Get(s->LocalAt(5), Value(int64_t{0})); Value v23104; v23104 = ([&]() -> Value { auto v23105 = ([&]() -> Value { auto fn23106 = s->LocalAt(47); Arguments args23107; args23107.Add(s->LocalAt(54), false); return Call(c, fn23106, std::move(args23107)); }()); return Binary("Add", v23105, s->Global("_OR2_SLOT_MARGIN")); }()); if (!static_cast<bool>(Binary("Gt", v23103, v23104))) return Value(false); v23103 = v23104; return Value(true); }()); if (!static_cast<bool>(v23102)) return v23102; v23102 = ([&]() -> Value { auto v23108 = ([&]() -> Value { auto fn23110 = s->Global("int"); Arguments args23111; args23111.Add(Get(s->LocalAt(54), Value(int64_t{2})), false); return Call(c, fn23110, std::move(args23111)); }()); Value v23109; v23109 = Value(int64_t{2}); if (!static_cast<bool>(Binary("LtE", v23108, v23109))) return Value(false); v23108 = v23109; return Value(true); }()); return v23102; }()); return v23093; }()))) {
auto v23112 = ([&]() -> Value { auto fn23113 = s->Global("max"); Arguments args23114; args23114.positional.reserve(2); args23114.Add(Value(int64_t{0}), false); args23114.Add(([&]() -> Value { auto fn23115 = s->Global("int"); Arguments args23116; args23116.Add(Get(s->LocalAt(54), Value(int64_t{2})), false); return Call(c, fn23115, std::move(args23116)); }()), false); return Call(c, fn23113, std::move(args23114)); }());
s->SetAt(36, v23112);
for (const auto& item23117 : Iterate(([&]() -> Value { auto fn23118 = s->Global("range"); Arguments args23119; args23119.positional.reserve(2); args23119.Add(([&]() -> Value { auto v23120 = s->LocalAt(45); return Binary("Add", v23120, Value(int64_t{1})); }()), false); args23119.Add(([&]() -> Value { auto v23121 = s->LocalAt(45); return Binary("Add", v23121, Value(int64_t{49})); }()), false); return Call(c, fn23118, std::move(args23119)); }()))) {
s->SetAt(48, item23117);
if (static_cast<bool>(([&]() -> Value { auto v23122 = s->LocalAt(36); Value v23123; v23123 = Value(int64_t{0}); if (!static_cast<bool>(Binary("LtE", v23122, v23123))) return Value(false); v23122 = v23123; return Value(true); }()))) {
break;
}
auto v23124 = ([&]() -> Value { auto fn23125 = PrepareDictionaryGet(([&]() -> Value { auto fn23127 = PrepareDictionaryGet(s->LocalAt(10)); Arguments args23128; args23128.positional.reserve(2); args23128.Add(s->LocalAt(48), false); args23128.Add(([&]() -> Value { auto dict23129 = Dict(); return dict23129; }()), false); return CallDictionaryGet(c, fn23127, std::move(args23128)); }())); Arguments args23126; args23126.positional.reserve(2); args23126.Add(Get(s->LocalAt(54), Value(int64_t{1})), false); args23126.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn23125, std::move(args23126)); }());
s->SetAt(28, v23124);
auto v23130 = ([&]() -> Value { auto fn23131 = s->Global("min"); Arguments args23132; args23132.positional.reserve(2); args23132.Add(s->LocalAt(28), false); args23132.Add(s->LocalAt(36), false); return Call(c, fn23131, std::move(args23132)); }());
s->SetAt(4, v23130);
if (static_cast<bool>(([&]() -> Value { auto v23133 = s->LocalAt(4); Value v23134; v23134 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v23133, v23134))) return Value(false); v23133 = v23134; return Value(true); }()))) {
auto v23135 = ([&]() -> Value { auto v23136 = s->LocalAt(28); return Binary("Sub", v23136, s->LocalAt(4)); }());
Put(Get(s->LocalAt(10), s->LocalAt(48)), Get(s->LocalAt(54), Value(int64_t{1})), v23135);
auto v23137 = s->LocalAt(36);
s->SetAt(36, Inplace("Sub", v23137, s->LocalAt(4)));
}
}
(void)([&]() -> Value { auto fn23138 = Attribute(s->LocalAt(27), "remove"); Arguments args23139; args23139.Add(s->LocalAt(54), false); return Call(c, fn23138, std::move(args23139)); }());
(void)([&]() -> Value { auto fn23140 = Attribute(s->LocalAt(27), "append"); Arguments args23141; args23141.Add(List({Value("SELL"), Get(s->LocalAt(5), Value(int64_t{1})), Get(s->LocalAt(5), Value(int64_t{2}))}), false); return Call(c, fn23140, std::move(args23141)); }());
for (const auto& item23142 : Iterate(Get(s->LocalAt(5), Value(int64_t{3})))) {
auto unpack23143 = Iterate(item23142);
ValidateUnpack(unpack23143, 2, false);
s->SetAt(48, unpack23143.at(0));
s->SetAt(35, unpack23143.at(1));
auto v23144 = ([&]() -> Value { auto v23145 = ([&]() -> Value { auto fn23146 = PrepareDictionaryGet(([&]() -> Value { auto fn23148 = PrepareDictionaryGet(s->LocalAt(10)); Arguments args23149; args23149.positional.reserve(2); args23149.Add(s->LocalAt(48), false); args23149.Add(([&]() -> Value { auto dict23150 = Dict(); return dict23150; }()), false); return CallDictionaryGet(c, fn23148, std::move(args23149)); }())); Arguments args23147; args23147.positional.reserve(2); args23147.Add(Get(s->LocalAt(5), Value(int64_t{1})), false); args23147.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn23146, std::move(args23147)); }()); return Binary("Add", v23145, s->LocalAt(35)); }());
Put(([&]() -> Value { auto fn23151 = Attribute(s->LocalAt(10), "setdefault"); Arguments args23152; args23152.positional.reserve(2); args23152.Add(s->LocalAt(48), false); args23152.Add(([&]() -> Value { auto dict23153 = Dict(); return dict23153; }()), false); return Call(c, fn23151, std::move(args23152)); }()), Get(s->LocalAt(5), Value(int64_t{1})), v23144);
}
auto v23154 = ([&]() -> Value { auto v23155 = ([&]() -> Value { auto fn23156 = PrepareDictionaryGet(s->Global("_OR2_REPORT")); Arguments args23157; args23157.positional.reserve(2); args23157.Add(Value("or2_slot_swaps"), false); args23157.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn23156, std::move(args23157)); }()); return Binary("Add", v23155, Value(int64_t{1})); }());
Put(s->Global("_OR2_REPORT"), Value("or2_slot_swaps"), v23154);
auto v23158 = ([&]() -> Value { auto fn23159 = s->Global("dict"); Arguments args23160; args23160.Add(s->LocalAt(1), false); return Call(c, fn23159, std::move(args23160)); }());
s->SetAt(1, v23158);
auto v23161 = s->LocalAt(27);
Put(s->LocalAt(1), Value("market"), v23161);
}
}
}
auto v23162 = ([&]() -> Value { auto fn23163 = s->Global("dict"); Arguments args23164; args23164.Add(s->LocalAt(34), false); return Call(c, fn23163, std::move(args23164)); }());
s->SetAt(19, v23162);
auto v23165 = Tuple({List({}), List({}), ([&]() -> Value { auto fn23166 = s->Global("set"); Arguments args23167; return Call(c, fn23166, std::move(args23167)); }())});
auto unpack23168 = Iterate(v23165);
ValidateUnpack(unpack23168, 3, false);
s->SetAt(20, unpack23168.at(0));
s->SetAt(12, unpack23168.at(1));
s->SetAt(7, unpack23168.at(2));
for (const auto& item23169 : Iterate(([&]() -> Value { auto fn23170 = s->Global("enumerate"); Arguments args23171; args23171.Add(s->LocalAt(27), false); return Call(c, fn23170, std::move(args23171)); }()))) {
auto unpack23172 = Iterate(item23169);
ValidateUnpack(unpack23172, 2, false);
s->SetAt(14, unpack23172.at(0));
s->SetAt(24, unpack23172.at(1));
if (static_cast<bool>(([&]() -> Value { auto v23173 = ([&]() -> Value { auto v23174 = ([&]() -> Value { auto fn23176 = s->Global("len"); Arguments args23177; args23177.Add(s->LocalAt(24), false); return Call(c, fn23176, std::move(args23177)); }()); Value v23175; v23175 = Value(int64_t{2}); if (!static_cast<bool>(Binary("GtE", v23174, v23175))) return Value(false); v23174 = v23175; return Value(true); }()); if (!static_cast<bool>(v23173)) return v23173; v23173 = ([&]() -> Value { auto v23178 = Get(s->LocalAt(24), Value(int64_t{0})); Value v23179; v23179 = Tuple({Value("BUY_PRODUCT"), Value("BUY_ANIMAL")}); if (!static_cast<bool>(Binary("In", v23178, v23179))) return Value(false); v23178 = v23179; return Value(true); }()); return v23173; }()))) {
(void)([&]() -> Value { auto fn23180 = Attribute(s->LocalAt(7), "add"); Arguments args23181; args23181.Add(Get(s->LocalAt(24), Value(int64_t{1})), false); return Call(c, fn23180, std::move(args23181)); }());
}
if (static_cast<bool>(([&]() -> Value { auto v23182 = ([&]() -> Value { auto v23183 = ([&]() -> Value { auto fn23185 = s->Global("len"); Arguments args23186; args23186.Add(s->LocalAt(24), false); return Call(c, fn23185, std::move(args23186)); }()); Value v23184; v23184 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v23183, v23184))) return Value(false); v23183 = v23184; return Value(true); }()); if (!static_cast<bool>(v23182)) return v23182; v23182 = ([&]() -> Value { auto v23187 = Get(s->LocalAt(24), Value(int64_t{0})); Value v23188; v23188 = Value("SELL"); if (!static_cast<bool>(Binary("Eq", v23187, v23188))) return Value(false); v23187 = v23188; return Value(true); }()); if (!static_cast<bool>(v23182)) return v23182; v23182 = ([&]() -> Value { auto v23189 = ([&]() -> Value { auto fn23191 = s->Global("int"); Arguments args23192; args23192.Add(Get(s->LocalAt(24), Value(int64_t{2})), false); return Call(c, fn23191, std::move(args23192)); }()); Value v23190; v23190 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v23189, v23190))) return Value(false); v23189 = v23190; return Value(true); }()); if (!static_cast<bool>(v23182)) return v23182; v23182 = ([&]() -> Value { auto v23193 = Get(s->LocalAt(24), Value(int64_t{1})); Value v23194; v23194 = s->LocalAt(7); if (!static_cast<bool>(Binary("NotIn", v23193, v23194))) return Value(false); v23193 = v23194; return Value(true); }()); return v23182; }()))) {
(void)([&]() -> Value { auto fn23195 = Attribute(s->LocalAt(20), "append"); Arguments args23196; args23196.Add(Tuple({s->LocalAt(14), s->LocalAt(24)}), false); return Call(c, fn23195, std::move(args23196)); }());
}
else {
(void)([&]() -> Value { auto fn23197 = Attribute(s->LocalAt(12), "append"); Arguments args23198; args23198.Add(Tuple({s->LocalAt(14), s->LocalAt(24)}), false); return Call(c, fn23197, std::move(args23198)); }());
}
}
if (static_cast<bool>(([&]() -> Value { auto v23199 = s->LocalAt(20); if (!static_cast<bool>(v23199)) return v23199; v23199 = ([&]() -> Value { auto v23200 = s->LocalAt(45); Value v23201; v23201 = Value(int64_t{1}); if (!static_cast<bool>(Binary("GtE", v23200, v23201))) return Value(false); v23200 = v23201; return Value(true); }()); return v23199; }()))) {
s->SetAt(38, Define(&Code_901d361625ccbf8c6886, s, Signature{{"io"}, {}, {}, {}, "", "", ([]() -> std::span<const char* const> { static constexpr const char* names[] = {"b", "io", "item", "qty"}; return names; }())}, true, "score"));
s->definitions.push_back("score");
auto v23225 = ([&]() -> Value { auto fn23226 = s->Global("sorted"); Arguments args23227; args23227.Add(s->LocalAt(20), false); args23227.Keyword("key", s->LocalAt(38)); return Call(c, fn23226, std::move(args23227)); }());
s->SetAt(39, v23225);
auto v23228 = ([&]() -> Value { auto v23229 = ([&]() -> Value { auto comp23230 = std::make_shared<Scope>(); comp23230->globals = s->globals; comp23230->parent = s; static constexpr const char* comp23230_names[] = {"_", "o"}; comp23230->PrepareSlots(comp23230_names); auto result23231 = List(); for (const auto& item23232 : Iterate(s->LocalAt(39))) { auto unpack23233 = Iterate(item23232); ValidateUnpack(unpack23233, 2, false); comp23230->SetAt(0, unpack23233.at(0)); comp23230->SetAt(1, unpack23233.at(1)); result23231.node()->sequence.push_back(comp23230->LocalAt(1)); } return result23231; }()); return Binary("Add", v23229, ([&]() -> Value { auto comp23234 = std::make_shared<Scope>(); comp23234->globals = s->globals; comp23234->parent = s; static constexpr const char* comp23234_names[] = {"_", "o"}; comp23234->PrepareSlots(comp23234_names); auto result23235 = List(); for (const auto& item23236 : Iterate(s->LocalAt(12))) { auto unpack23237 = Iterate(item23236); ValidateUnpack(unpack23237, 2, false); comp23234->SetAt(0, unpack23237.at(0)); comp23234->SetAt(1, unpack23237.at(1)); result23235.node()->sequence.push_back(comp23234->LocalAt(1)); } return result23235; }())); }());
s->SetAt(23, v23228);
if (static_cast<bool>(([&]() -> Value { auto v23238 = s->LocalAt(23); Value v23239; v23239 = s->LocalAt(27); if (!static_cast<bool>(Binary("NotEq", v23238, v23239))) return Value(false); v23238 = v23239; return Value(true); }()))) {
auto v23240 = ([&]() -> Value { auto fn23241 = s->Global("sorted"); Arguments args23242; args23242.Add(s->LocalAt(20), false); args23242.Keyword("key", Define(&Code_4e86b4c3ba0b6eabef71, s, Signature{{"io"}, {}, {}, {}, "", "", ([]() -> std::span<const char* const> { static constexpr const char* names[] = {"io"}; return names; }())}, true, "<lambda>")); return Call(c, fn23241, std::move(args23242)); }());
s->SetAt(52, v23240);
if (static_cast<bool>(([&]() -> Value { auto v23245 = ([&]() -> Value { auto comp23247 = std::make_shared<Scope>(); comp23247->globals = s->globals; comp23247->parent = s; static constexpr const char* comp23247_names[] = {"_", "o"}; comp23247->PrepareSlots(comp23247_names); auto result23248 = List(); for (const auto& item23249 : Iterate(s->LocalAt(52))) { auto unpack23250 = Iterate(item23249); ValidateUnpack(unpack23250, 2, false); comp23247->SetAt(0, unpack23250.at(0)); comp23247->SetAt(1, unpack23250.at(1)); result23248.node()->sequence.push_back(comp23247->LocalAt(1)); } return result23248; }()); Value v23246; v23246 = ([&]() -> Value { auto comp23251 = std::make_shared<Scope>(); comp23251->globals = s->globals; comp23251->parent = s; static constexpr const char* comp23251_names[] = {"_", "o"}; comp23251->PrepareSlots(comp23251_names); auto result23252 = List(); for (const auto& item23253 : Iterate(s->LocalAt(39))) { auto unpack23254 = Iterate(item23253); ValidateUnpack(unpack23254, 2, false); comp23251->SetAt(0, unpack23254.at(0)); comp23251->SetAt(1, unpack23254.at(1)); result23252.node()->sequence.push_back(comp23251->LocalAt(1)); } return result23252; }()); if (!static_cast<bool>(Binary("NotEq", v23245, v23246))) return Value(false); v23245 = v23246; return Value(true); }()))) {
auto v23255 = s->Global("_OR2_REPORT");
auto v23256 = Value("or2_changed_vs_v39");
auto v23257 = Get(v23255, v23256);
Put(v23255, v23256, Inplace("Add", v23257, Value(int64_t{1})));
}
auto v23258 = s->Global("_OR2_REPORT");
auto v23259 = Value("or2_reordered");
auto v23260 = Get(v23258, v23259);
Put(v23258, v23259, Inplace("Add", v23260, Value(int64_t{1})));
auto v23261 = ([&]() -> Value { auto fn23262 = s->Global("dict"); Arguments args23263; args23263.Add(s->LocalAt(1), false); return Call(c, fn23262, std::move(args23263)); }());
s->SetAt(1, v23261);
auto v23264 = s->LocalAt(23);
Put(s->LocalAt(1), Value("market"), v23264);
auto v23265 = s->LocalAt(23);
s->SetAt(27, v23265);
}
}
for (const auto& item23266 : Iterate(Slice(s->LocalAt(27), Value{}, Value(int64_t{10}), Value{}))) {
s->SetAt(24, item23266);
if (static_cast<bool>(([&]() -> Value { auto v23267 = ([&]() -> Value { auto v23268 = ([&]() -> Value { auto fn23270 = s->Global("len"); Arguments args23271; args23271.Add(s->LocalAt(24), false); return Call(c, fn23270, std::move(args23271)); }()); Value v23269; v23269 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v23268, v23269))) return Value(false); v23268 = v23269; return Value(true); }()); if (!static_cast<bool>(v23267)) return v23267; v23267 = ([&]() -> Value { auto v23272 = Get(s->LocalAt(24), Value(int64_t{0})); Value v23273; v23273 = Value("SELL"); if (!static_cast<bool>(Binary("Eq", v23272, v23273))) return Value(false); v23272 = v23273; return Value(true); }()); if (!static_cast<bool>(v23267)) return v23267; v23267 = ([&]() -> Value { auto v23274 = Get(s->LocalAt(24), Value(int64_t{1})); Value v23275; v23275 = s->Global("_OR2_ITEMS"); if (!static_cast<bool>(Binary("In", v23274, v23275))) return Value(false); v23274 = v23275; return Value(true); }()); return v23267; }()))) {
auto v23276 = ([&]() -> Value { auto fn23277 = s->Global("min"); Arguments args23278; args23278.positional.reserve(2); args23278.Add(([&]() -> Value { auto fn23279 = s->Global("max"); Arguments args23280; args23280.positional.reserve(2); args23280.Add(Value(int64_t{0}), false); args23280.Add(([&]() -> Value { auto fn23281 = s->Global("int"); Arguments args23282; args23282.Add(Get(s->LocalAt(24), Value(int64_t{2})), false); return Call(c, fn23281, std::move(args23282)); }()), false); return Call(c, fn23279, std::move(args23280)); }()), false); args23278.Add(([&]() -> Value { auto fn23283 = s->Global("max"); Arguments args23284; args23284.positional.reserve(2); args23284.Add(Value(int64_t{0}), false); args23284.Add(([&]() -> Value { auto fn23285 = s->Global("int"); Arguments args23286; args23286.Add(([&]() -> Value { auto fn23287 = PrepareDictionaryGet(s->LocalAt(19)); Arguments args23288; args23288.positional.reserve(2); args23288.Add(Get(s->LocalAt(24), Value(int64_t{1})), false); args23288.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn23287, std::move(args23288)); }()), false); return Call(c, fn23285, std::move(args23286)); }()), false); return Call(c, fn23283, std::move(args23284)); }()), false); return Call(c, fn23277, std::move(args23278)); }());
s->SetAt(13, v23276);
auto v23289 = ([&]() -> Value { auto v23290 = ([&]() -> Value { auto fn23291 = PrepareDictionaryGet(s->LocalAt(19)); Arguments args23292; args23292.positional.reserve(2); args23292.Add(Get(s->LocalAt(24), Value(int64_t{1})), false); args23292.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn23291, std::move(args23292)); }()); return Binary("Sub", v23290, s->LocalAt(13)); }());
Put(s->LocalAt(19), Get(s->LocalAt(24), Value(int64_t{1})), v23289);
auto v23293 = ([&]() -> Value { auto v23294 = ([&]() -> Value { auto fn23295 = PrepareDictionaryGet(s->LocalAt(29)); Arguments args23296; args23296.positional.reserve(2); args23296.Add(Get(s->LocalAt(24), Value(int64_t{1})), false); args23296.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn23295, std::move(args23296)); }()); return Binary("Add", v23294, s->LocalAt(13)); }());
Put(s->LocalAt(29), Get(s->LocalAt(24), Value(int64_t{1})), v23293);
}
}
}
auto v23297 = ([&]() -> Value { auto dict23298 = Dict(); auto key23299 = Value("step"); Put(dict23298, key23299, s->LocalAt(45)); auto key23300 = Value("tiles"); Put(dict23298, key23300, s->LocalAt(51)); auto key23301 = Value("inv"); Put(dict23298, key23301, s->LocalAt(15)); auto key23302 = Value("own"); Put(dict23298, key23302, s->LocalAt(29)); auto key23303 = Value("prices"); Put(dict23298, key23303, ([&]() -> Value { auto fn23304 = s->Global("dict"); Arguments args23305; args23305.Add(Get(Get(s->LocalAt(25), Value("market")), Value("prices")), false); return Call(c, fn23304, std::move(args23305)); }())); auto key23306 = Value("shops"); Put(dict23298, key23306, ([&]() -> Value { auto fn23307 = s->Global("list"); Arguments args23308; args23308.Add(([&]() -> Value { auto v23309 = ([&]() -> Value { auto fn23310 = PrepareDictionaryGet(([&]() -> Value { auto v23312 = ([&]() -> Value { auto fn23313 = PrepareDictionaryGet(s->LocalAt(25)); Arguments args23314; args23314.Add(Value("town"), false); return CallDictionaryGet(c, fn23313, std::move(args23314)); }()); if (static_cast<bool>(v23312)) return v23312; v23312 = ([&]() -> Value { auto dict23315 = Dict(); return dict23315; }()); return v23312; }())); Arguments args23311; args23311.Add(Value("unlocked_shops"), false); return CallDictionaryGet(c, fn23310, std::move(args23311)); }()); if (static_cast<bool>(v23309)) return v23309; v23309 = List({}); return v23309; }()), false); return Call(c, fn23307, std::move(args23308)); }())); return dict23298; }());
Put(s->LocalAt(44), Value("prev"), v23297);
auto v23316 = s->LocalAt(45);
Put(s->LocalAt(44), Value("step"), v23316);
} catch (const Error& error22599) {
if (Matches(error22599, s->Global("Exception"))) {
auto v23317 = s->Global("_OR2_REPORT");
auto v23318 = Value("or2_errors");
auto v23319 = Get(v23317, v23318);
Put(v23317, v23318, Inplace("Add", v23319, Value(int64_t{1})));
}
else { throw; }
}
return s->LocalAt(1);
return {};
}
}  // namespace kagg::opponents::compiled
