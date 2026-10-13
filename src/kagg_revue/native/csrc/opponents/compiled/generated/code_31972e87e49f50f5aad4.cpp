// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_31972e87e49f50f5aad4(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "actor", "affordable", "cash", "extra", "farm", "item", "market", "mode", "n", "obs", "order", "planned", "positions", "private", "q", "seat", "seed_cost", "spec", "st", "stock", "tile", "units", "work", "workers", "x", "y"};
s->PrepareSlots(s_names);
auto v24661 = Get(s->LocalAt(19), Value("mode"));
s->SetAt(8, v24661);
auto v24662 = Get(s->Global("_HD2_SPEC"), s->LocalAt(8));
s->SetAt(18, v24662);
auto v24663 = Get(s->LocalAt(18), Value("product"));
s->SetAt(6, v24663);
auto v24664 = ([&]() -> Value { auto fn24665 = s->Global("int"); Arguments args24666; args24666.Add(Get(s->LocalAt(10), Value("player")), false); return Call(c, fn24665, std::move(args24666)); }());
s->SetAt(16, v24664);
auto v24667 = Get(Get(s->LocalAt(10), Value("farms")), s->LocalAt(16));
s->SetAt(5, v24667);
auto v24668 = Get(s->LocalAt(10), Value("private"));
s->SetAt(14, v24668);
auto v24669 = ([&]() -> Value { auto v24670 = List({Get(s->LocalAt(5), Value("farmer"))}); return Binary("Add", v24670, ([&]() -> Value { auto fn24671 = s->Global("list"); Arguments args24672; args24672.Add(Get(s->LocalAt(5), Value("hands")), false); return Call(c, fn24671, std::move(args24672)); }())); }());
s->SetAt(13, v24669);
auto v24673 = ([&]() -> Value { auto v24674 = ([&]() -> Value { auto fn24675 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args24676; args24676.Add(Value("market"), false); return CallDictionaryGet(c, fn24675, std::move(args24676)); }()); if (static_cast<bool>(v24674)) return v24674; v24674 = List({}); return v24674; }());
s->SetAt(7, v24673);
auto v24677 = ([&]() -> Value { auto fn24678 = s->Global("float"); Arguments args24679; args24679.Add(([&]() -> Value { auto fn24680 = PrepareDictionaryGet(s->LocalAt(5)); Arguments args24681; args24681.positional.reserve(2); args24681.Add(Value("money"), false); args24681.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn24680, std::move(args24681)); }()), false); return Call(c, fn24678, std::move(args24679)); }());
s->SetAt(3, v24677);
auto v24682 = ([&]() -> Value { auto dict24683 = Dict(); auto key24684 = Value("WHEAT"); Put(dict24683, key24684, Value(int64_t{10})); auto key24685 = Value("CARROT"); Put(dict24683, key24685, Value(int64_t{20})); auto key24686 = Value("TOMATO"); Put(dict24683, key24686, Value(int64_t{50})); auto key24687 = Value("STRAWBERRY"); Put(dict24683, key24687, Value(int64_t{100})); auto key24688 = Value("MELON"); Put(dict24683, key24688, Value(int64_t{80})); return dict24683; }());
s->SetAt(17, v24682);
for (const auto& item24689 : Iterate(s->LocalAt(7))) {
s->SetAt(11, item24689);
if (static_cast<bool>(([&]() -> Value { auto v24690 = ([&]() -> Value { auto v24691 = ([&]() -> Value { auto fn24693 = s->Global("len"); Arguments args24694; args24694.Add(s->LocalAt(11), false); return Call(c, fn24693, std::move(args24694)); }()); Value v24692; v24692 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v24691, v24692))) return Value(false); v24691 = v24692; return Value(true); }()); if (!static_cast<bool>(v24690)) return v24690; v24690 = ([&]() -> Value { auto v24695 = Get(s->LocalAt(11), Value(int64_t{0})); Value v24696; v24696 = Value("BUY_ANIMAL"); if (!static_cast<bool>(Binary("Eq", v24695, v24696))) return Value(false); v24695 = v24696; return Value(true); }()); if (!static_cast<bool>(v24690)) return v24690; v24690 = ([&]() -> Value { auto v24697 = Get(s->LocalAt(11), Value(int64_t{1})); Value v24698; v24698 = Value("GOOSE"); if (!static_cast<bool>(Binary("Eq", v24697, v24698))) return Value(false); v24697 = v24698; return Value(true); }()); return v24690; }()))) {
auto v24699 = ([&]() -> Value { auto fn24700 = s->Global("max"); Arguments args24701; args24701.positional.reserve(2); args24701.Add(Value(int64_t{0}), false); args24701.Add(([&]() -> Value { auto fn24702 = s->Global("int"); Arguments args24703; args24703.Add(Get(s->LocalAt(11), Value(int64_t{2})), false); return Call(c, fn24702, std::move(args24703)); }()), false); return Call(c, fn24700, std::move(args24701)); }());
s->SetAt(9, v24699);
auto v24704 = ([&]() -> Value { auto fn24705 = s->Global("int"); Arguments args24706; args24706.Add(([&]() -> Value { auto v24707 = ([&]() -> Value { auto fn24708 = s->Global("max"); Arguments args24709; args24709.positional.reserve(2); args24709.Add(Value(0.0), false); args24709.Add(s->LocalAt(3), false); return Call(c, fn24708, std::move(args24709)); }()); return Binary("FloorDiv", v24707, Get(s->LocalAt(18), Value("cost"))); }()), false); return Call(c, fn24705, std::move(args24706)); }());
s->SetAt(2, v24704);
auto v24710 = s->LocalAt(8);
Put(s->LocalAt(11), Value(int64_t{1}), v24710);
auto v24711 = ([&]() -> Value { auto fn24712 = s->Global("min"); Arguments args24713; args24713.positional.reserve(2); args24713.Add(s->LocalAt(9), false); args24713.Add(s->LocalAt(2), false); return Call(c, fn24712, std::move(args24713)); }());
Put(s->LocalAt(11), Value(int64_t{2}), v24711);
auto v24714 = s->LocalAt(3);
s->SetAt(3, Inplace("Sub", v24714, ([&]() -> Value { auto v24715 = Get(s->LocalAt(11), Value(int64_t{2})); return Binary("Mult", v24715, Get(s->LocalAt(18), Value("cost"))); }())));
auto v24716 = s->Global("_HD2_REPORT");
auto v24717 = Value("hd2_rewrites");
auto v24718 = Get(v24716, v24717);
Put(v24716, v24717, Inplace("Add", v24718, Value(int64_t{1})));
}
else {
if (static_cast<bool>(([&]() -> Value { auto v24719 = ([&]() -> Value { auto v24720 = ([&]() -> Value { auto fn24722 = s->Global("len"); Arguments args24723; args24723.Add(s->LocalAt(11), false); return Call(c, fn24722, std::move(args24723)); }()); Value v24721; v24721 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v24720, v24721))) return Value(false); v24720 = v24721; return Value(true); }()); if (!static_cast<bool>(v24719)) return v24719; v24719 = ([&]() -> Value { auto v24724 = Get(s->LocalAt(11), Value(int64_t{0})); Value v24725; v24725 = Tuple({Value("BUY_ANIMAL"), Value("BUY_SEED"), Value("BUY_PRODUCT")}); if (!static_cast<bool>(Binary("In", v24724, v24725))) return Value(false); v24724 = v24725; return Value(true); }()); return v24719; }()))) {
auto v24726 = ([&]() -> Value { auto fn24727 = s->Global("max"); Arguments args24728; args24728.positional.reserve(2); args24728.Add(Value(int64_t{0}), false); args24728.Add(([&]() -> Value { auto fn24729 = s->Global("int"); Arguments args24730; args24730.Add(Get(s->LocalAt(11), Value(int64_t{2})), false); return Call(c, fn24729, std::move(args24730)); }()), false); return Call(c, fn24727, std::move(args24728)); }());
s->SetAt(15, v24726);
if (static_cast<bool>(([&]() -> Value { auto v24731 = Get(s->LocalAt(11), Value(int64_t{0})); Value v24732; v24732 = Value("BUY_ANIMAL"); if (!static_cast<bool>(Binary("Eq", v24731, v24732))) return Value(false); v24731 = v24732; return Value(true); }()))) {
auto v24733 = s->LocalAt(3);
s->SetAt(3, Inplace("Sub", v24733, ([&]() -> Value { auto v24734 = s->LocalAt(15); return Binary("Mult", v24734, ([&]() -> Value { auto fn24735 = PrepareDictionaryGet(([&]() -> Value { auto dict24737 = Dict(); auto key24738 = Value("GOOSE"); Put(dict24737, key24738, Value(int64_t{300})); auto key24739 = Value("COW"); Put(dict24737, key24739, Value(int64_t{400})); auto key24740 = Value("SHEEP"); Put(dict24737, key24740, Value(int64_t{500})); return dict24737; }())); Arguments args24736; args24736.positional.reserve(2); args24736.Add(Get(s->LocalAt(11), Value(int64_t{1})), false); args24736.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn24735, std::move(args24736)); }())); }())));
}
else {
if (static_cast<bool>(([&]() -> Value { auto v24741 = Get(s->LocalAt(11), Value(int64_t{0})); Value v24742; v24742 = Value("BUY_SEED"); if (!static_cast<bool>(Binary("Eq", v24741, v24742))) return Value(false); v24741 = v24742; return Value(true); }()))) {
auto v24743 = s->LocalAt(3);
s->SetAt(3, Inplace("Sub", v24743, ([&]() -> Value { auto v24744 = s->LocalAt(15); return Binary("Mult", v24744, ([&]() -> Value { auto fn24745 = PrepareDictionaryGet(s->LocalAt(17)); Arguments args24746; args24746.positional.reserve(2); args24746.Add(Get(s->LocalAt(11), Value(int64_t{1})), false); args24746.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn24745, std::move(args24746)); }())); }())));
}
else {
auto v24747 = s->LocalAt(3);
s->SetAt(3, Inplace("Sub", v24747, ([&]() -> Value { auto v24748 = s->LocalAt(15); return Binary("Mult", v24748, ([&]() -> Value { auto fn24749 = s->Global("int"); Arguments args24750; args24750.Add(([&]() -> Value { auto fn24751 = PrepareDictionaryGet(([&]() -> Value { auto v24753 = Get(Get(s->LocalAt(10), Value("market")), Value("prices")); if (static_cast<bool>(v24753)) return v24753; v24753 = ([&]() -> Value { auto dict24754 = Dict(); return dict24754; }()); return v24753; }())); Arguments args24752; args24752.positional.reserve(2); args24752.Add(Get(s->LocalAt(11), Value(int64_t{1})), false); args24752.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn24751, std::move(args24752)); }()), false); return Call(c, fn24749, std::move(args24750)); }())); }())));
}
}
}
else {
if (static_cast<bool>(([&]() -> Value { auto v24755 = s->LocalAt(11); if (!static_cast<bool>(v24755)) return v24755; v24755 = ([&]() -> Value { auto v24756 = Get(s->LocalAt(11), Value(int64_t{0})); Value v24757; v24757 = Value("BUY_LAND"); if (!static_cast<bool>(Binary("Eq", v24756, v24757))) return Value(false); v24756 = v24757; return Value(true); }()); return v24755; }()))) {
auto v24758 = s->LocalAt(3);
s->SetAt(3, Inplace("Sub", v24758, Value(int64_t{4000})));
}
}
}
}
auto v24759 = ([&]() -> Value { auto v24760 = List({([&]() -> Value { auto v24761 = ([&]() -> Value { auto fn24762 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args24763; args24763.Add(Value("farmer"), false); return CallDictionaryGet(c, fn24762, std::move(args24763)); }()); if (static_cast<bool>(v24761)) return v24761; v24761 = List({Value("PASS")}); return v24761; }())}); return Binary("Add", v24760, ([&]() -> Value { auto fn24764 = s->Global("list"); Arguments args24765; args24765.Add(([&]() -> Value { auto v24766 = ([&]() -> Value { auto fn24767 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args24768; args24768.Add(Value("hands"), false); return CallDictionaryGet(c, fn24767, std::move(args24768)); }()); if (static_cast<bool>(v24766)) return v24766; v24766 = List({}); return v24766; }()), false); return Call(c, fn24764, std::move(args24765)); }())); }());
s->SetAt(24, v24759);
for (const auto& item24769 : Iterate(([&]() -> Value { auto fn24770 = s->Global("enumerate"); Arguments args24771; args24771.Add(Slice(s->LocalAt(24), Value{}, ([&]() -> Value { auto fn24772 = s->Global("len"); Arguments args24773; args24773.Add(s->LocalAt(13), false); return Call(c, fn24772, std::move(args24773)); }()), Value{}), false); return Call(c, fn24770, std::move(args24771)); }()))) {
auto unpack24774 = Iterate(item24769);
ValidateUnpack(unpack24774, 2, false);
s->SetAt(1, unpack24774.at(0));
s->SetAt(23, unpack24774.at(1));
if (static_cast<bool>(Unary("Not", s->LocalAt(23)))) {
continue;
}
auto v24775 = Get(s->LocalAt(13), s->LocalAt(1));
auto unpack24776 = Iterate(v24775);
ValidateUnpack(unpack24776, 2, false);
s->SetAt(25, unpack24776.at(0));
s->SetAt(26, unpack24776.at(1));
auto v24777 = Get(Get(Get(s->LocalAt(5), Value("tiles")), s->LocalAt(26)), s->LocalAt(25));
s->SetAt(21, v24777);
if (static_cast<bool>(([&]() -> Value { auto v24778 = Get(s->LocalAt(23), Value(int64_t{0})); Value v24779; v24779 = Value("BUILD_COOP"); if (!static_cast<bool>(Binary("Eq", v24778, v24779))) return Value(false); v24778 = v24779; return Value(true); }()))) {
auto v24780 = List({Value("BUILD_PASTURE")});
Put(s->LocalAt(24), s->LocalAt(1), v24780);
auto v24781 = s->Global("_HD2_REPORT");
auto v24782 = Value("hd2_rewrites");
auto v24783 = Get(v24781, v24782);
Put(v24781, v24782, Inplace("Add", v24783, Value(int64_t{1})));
}
else {
if (static_cast<bool>(([&]() -> Value { auto v24784 = ([&]() -> Value { auto v24785 = ([&]() -> Value { auto fn24787 = s->Global("len"); Arguments args24788; args24788.Add(s->LocalAt(23), false); return Call(c, fn24787, std::move(args24788)); }()); Value v24786; v24786 = Value(int64_t{2}); if (!static_cast<bool>(Binary("GtE", v24785, v24786))) return Value(false); v24785 = v24786; return Value(true); }()); if (!static_cast<bool>(v24784)) return v24784; v24784 = ([&]() -> Value { auto v24789 = Get(s->LocalAt(23), Value(int64_t{0})); Value v24790; v24790 = Tuple({Value("PICKUP"), Value("PLACE")}); if (!static_cast<bool>(Binary("In", v24789, v24790))) return Value(false); v24789 = v24790; return Value(true); }()); if (!static_cast<bool>(v24784)) return v24784; v24784 = ([&]() -> Value { auto v24791 = Get(s->LocalAt(23), Value(int64_t{1})); Value v24792; v24792 = Value("GOOSE"); if (!static_cast<bool>(Binary("Eq", v24791, v24792))) return Value(false); v24791 = v24792; return Value(true); }()); return v24784; }()))) {
auto v24793 = ([&]() -> Value { auto v24794 = List({Get(s->LocalAt(23), Value(int64_t{0})), s->LocalAt(8)}); return Binary("Add", v24794, ([&]() -> Value { auto fn24795 = s->Global("list"); Arguments args24796; args24796.Add(Slice(s->LocalAt(23), Value(int64_t{2}), Value{}, Value{}), false); return Call(c, fn24795, std::move(args24796)); }())); }());
Put(s->LocalAt(24), s->LocalAt(1), v24793);
auto v24797 = s->Global("_HD2_REPORT");
auto v24798 = Value("hd2_rewrites");
auto v24799 = Get(v24797, v24798);
Put(v24797, v24798, Inplace("Add", v24799, Value(int64_t{1})));
if (static_cast<bool>(([&]() -> Value { auto v24800 = Get(s->LocalAt(23), Value(int64_t{0})); Value v24801; v24801 = Value("PLACE"); if (!static_cast<bool>(Binary("Eq", v24800, v24801))) return Value(false); v24800 = v24801; return Value(true); }()))) {
(void)([&]() -> Value { auto fn24802 = Attribute(Get(s->LocalAt(19), Value("pending")), "append"); Arguments args24803; args24803.Add(Tuple({s->LocalAt(25), s->LocalAt(26), ([&]() -> Value { auto v24804 = ([&]() -> Value { auto fn24805 = s->Global("int"); Arguments args24806; args24806.Add(Get(s->LocalAt(10), Value("step")), false); return Call(c, fn24805, std::move(args24806)); }()); return Binary("FloorDiv", v24804, Value(int64_t{24})); }())}), false); return Call(c, fn24802, std::move(args24803)); }());
}
}
else {
if (static_cast<bool>(([&]() -> Value { auto v24807 = ([&]() -> Value { auto v24808 = ([&]() -> Value { auto fn24810 = s->Global("len"); Arguments args24811; args24811.Add(s->LocalAt(23), false); return Call(c, fn24810, std::move(args24811)); }()); Value v24809; v24809 = Value(int64_t{2}); if (!static_cast<bool>(Binary("GtE", v24808, v24809))) return Value(false); v24808 = v24809; return Value(true); }()); if (!static_cast<bool>(v24807)) return v24807; v24807 = ([&]() -> Value { auto v24812 = Get(s->LocalAt(23), Value(int64_t{0})); Value v24813; v24813 = Value("PLACE"); if (!static_cast<bool>(Binary("Eq", v24812, v24813))) return Value(false); v24812 = v24813; return Value(true); }()); if (!static_cast<bool>(v24807)) return v24807; v24807 = ([&]() -> Value { auto v24814 = Get(s->LocalAt(23), Value(int64_t{1})); Value v24815; v24815 = Value("EGG"); if (!static_cast<bool>(Binary("Eq", v24814, v24815))) return Value(false); v24814 = v24815; return Value(true); }()); return v24807; }()))) {
auto v24816 = ([&]() -> Value { auto v24817 = List({Value("PLACE"), s->LocalAt(6)}); return Binary("Add", v24817, ([&]() -> Value { auto fn24818 = s->Global("list"); Arguments args24819; args24819.Add(Slice(s->LocalAt(23), Value(int64_t{2}), Value{}, Value{}), false); return Call(c, fn24818, std::move(args24819)); }())); }());
Put(s->LocalAt(24), s->LocalAt(1), v24816);
auto v24820 = s->Global("_HD2_REPORT");
auto v24821 = Value("hd2_rewrites");
auto v24822 = Get(v24820, v24821);
Put(v24820, v24821, Inplace("Add", v24822, Value(int64_t{1})));
}
else {
if (static_cast<bool>(([&]() -> Value { auto v24823 = ([&]() -> Value { auto v24824 = s->LocalAt(23); Value v24825; v24825 = List({Value("HARVEST")}); if (!static_cast<bool>(Binary("Eq", v24824, v24825))) return Value(false); v24824 = v24825; return Value(true); }()); if (!static_cast<bool>(v24823)) return v24823; v24823 = ([&]() -> Value { auto v24826 = Tuple({s->LocalAt(25), s->LocalAt(26)}); Value v24827; v24827 = Get(s->LocalAt(19), Value("sites")); if (!static_cast<bool>(Binary("In", v24826, v24827))) return Value(false); v24826 = v24827; return Value(true); }()); if (!static_cast<bool>(v24823)) return v24823; v24823 = ([&]() -> Value { auto fn24828 = s->Global("isinstance"); Arguments args24829; args24829.positional.reserve(2); args24829.Add(s->LocalAt(21), false); args24829.Add(s->Global("dict"), false); return Call(c, fn24828, std::move(args24829)); }()); if (!static_cast<bool>(v24823)) return v24823; v24823 = ([&]() -> Value { auto v24830 = ([&]() -> Value { auto fn24832 = PrepareDictionaryGet(s->LocalAt(21)); Arguments args24833; args24833.Add(Value("animal"), false); return CallDictionaryGet(c, fn24832, std::move(args24833)); }()); Value v24831; v24831 = s->LocalAt(8); if (!static_cast<bool>(Binary("Eq", v24830, v24831))) return Value(false); v24830 = v24831; return Value(true); }()); return v24823; }()))) {
auto v24834 = ([&]() -> Value { auto fn24835 = s->Global("max"); Arguments args24836; args24836.positional.reserve(2); args24836.Add(Value(int64_t{0}), false); args24836.Add(([&]() -> Value { auto fn24837 = s->Global("int"); Arguments args24838; args24838.Add(([&]() -> Value { auto fn24839 = PrepareDictionaryGet(s->LocalAt(21)); Arguments args24840; args24840.positional.reserve(2); args24840.Add(Value("yield_units"), false); args24840.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn24839, std::move(args24840)); }()), false); return Call(c, fn24837, std::move(args24838)); }()), false); return Call(c, fn24835, std::move(args24836)); }());
s->SetAt(22, v24834);
auto v24841 = s->LocalAt(19);
auto v24842 = Value("credit");
auto v24843 = Get(v24841, v24842);
Put(v24841, v24842, Inplace("Add", v24843, s->LocalAt(22)));
auto v24844 = s->Global("_HD2_REPORT");
auto v24845 = Value("hd2_credit_units");
auto v24846 = Get(v24844, v24845);
Put(v24844, v24845, Inplace("Add", v24846, s->LocalAt(22)));
}
}
}
}
}
auto v24847 = Get(s->LocalAt(24), Value(int64_t{0}));
Put(s->LocalAt(0), Value("farmer"), v24847);
auto v24848 = Slice(s->LocalAt(24), Value(int64_t{1}), Value{}, Value{});
Put(s->LocalAt(0), Value("hands"), v24848);
if (static_cast<bool>(([&]() -> Value { auto v24849 = Get(s->LocalAt(19), Value("credit")); Value v24850; v24850 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v24849, v24850))) return Value(false); v24849 = v24850; return Value(true); }()))) {
try {
auto v24852 = ([&]() -> Value { auto fn24853 = s->Global("projected_shed"); Arguments args24854; args24854.positional.reserve(2); args24854.Add(s->LocalAt(0), false); args24854.Add(([&]() -> Value { auto fn24855 = s->Global("FarmView"); Arguments args24856; args24856.Add(s->LocalAt(10), false); return Call(c, fn24855, std::move(args24856)); }()), false); return Call(c, fn24853, std::move(args24854)); }());
s->SetAt(20, v24852);
} catch (const Error& error24851) {
if (Matches(error24851, s->Global("Exception"))) {
auto v24857 = ([&]() -> Value { auto fn24858 = s->Global("dict"); Arguments args24859; args24859.Add(([&]() -> Value { auto v24860 = ([&]() -> Value { auto fn24861 = PrepareDictionaryGet(s->LocalAt(14)); Arguments args24862; args24862.Add(Value("shed"), false); return CallDictionaryGet(c, fn24861, std::move(args24862)); }()); if (static_cast<bool>(v24860)) return v24860; v24860 = ([&]() -> Value { auto dict24863 = Dict(); return dict24863; }()); return v24860; }()), false); return Call(c, fn24858, std::move(args24859)); }());
s->SetAt(20, v24857);
}
else { throw; }
}
auto v24864 = ([&]() -> Value { auto fn24865 = s->Global("sum"); Arguments args24866; args24866.Add(([&]() -> Value { auto comp24867 = std::make_shared<Scope>(); comp24867->globals = s->globals; comp24867->parent = s; static constexpr const char* comp24867_names[] = {"o"}; comp24867->PrepareSlots(comp24867_names); auto result24868 = List(); for (const auto& item24869 : Iterate(s->LocalAt(7))) { comp24867->SetAt(0, item24869); if (!static_cast<bool>(([&]() -> Value { auto v24870 = ([&]() -> Value { auto v24871 = ([&]() -> Value { auto fn24873 = comp24867->Global("len"); Arguments args24874; args24874.Add(comp24867->LocalAt(0), false); return Call(c, fn24873, std::move(args24874)); }()); Value v24872; v24872 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v24871, v24872))) return Value(false); v24871 = v24872; return Value(true); }()); if (!static_cast<bool>(v24870)) return v24870; v24870 = ([&]() -> Value { auto v24875 = Slice(comp24867->LocalAt(0), Value{}, Value(int64_t{2}), Value{}); Value v24876; v24876 = List({Value("SELL"), comp24867->Captured("item")}); if (!static_cast<bool>(Binary("Eq", v24875, v24876))) return Value(false); v24875 = v24876; return Value(true); }()); return v24870; }()))) continue; result24868.node()->sequence.push_back(([&]() -> Value { auto fn24877 = comp24867->Global("max"); Arguments args24878; args24878.positional.reserve(2); args24878.Add(Value(int64_t{0}), false); args24878.Add(([&]() -> Value { auto fn24879 = comp24867->Global("int"); Arguments args24880; args24880.Add(Get(comp24867->LocalAt(0), Value(int64_t{2})), false); return Call(c, fn24879, std::move(args24880)); }()), false); return Call(c, fn24877, std::move(args24878)); }())); } return result24868; }()), false); return Call(c, fn24865, std::move(args24866)); }());
s->SetAt(12, v24864);
auto v24881 = ([&]() -> Value { auto fn24882 = s->Global("min"); Arguments args24883; args24883.positional.reserve(2); args24883.Add(Get(s->LocalAt(19), Value("credit")), false); args24883.Add(([&]() -> Value { auto fn24884 = s->Global("max"); Arguments args24885; args24885.positional.reserve(2); args24885.Add(Value(int64_t{0}), false); args24885.Add(([&]() -> Value { auto v24886 = ([&]() -> Value { auto fn24887 = s->Global("int"); Arguments args24888; args24888.Add(([&]() -> Value { auto fn24889 = PrepareDictionaryGet(s->LocalAt(20)); Arguments args24890; args24890.positional.reserve(2); args24890.Add(s->LocalAt(6), false); args24890.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn24889, std::move(args24890)); }()), false); return Call(c, fn24887, std::move(args24888)); }()); return Binary("Sub", v24886, s->LocalAt(12)); }()), false); return Call(c, fn24884, std::move(args24885)); }()), false); return Call(c, fn24882, std::move(args24883)); }());
s->SetAt(4, v24881);
if (static_cast<bool>(([&]() -> Value { auto v24891 = s->LocalAt(4); Value v24892; v24892 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v24891, v24892))) return Value(false); v24891 = v24892; return Value(true); }()))) {
bool exhausted24893 = true;
for (const auto& item24894 : Iterate(s->LocalAt(7))) {
s->SetAt(11, item24894);
if (static_cast<bool>(([&]() -> Value { auto v24895 = ([&]() -> Value { auto v24896 = ([&]() -> Value { auto fn24898 = s->Global("len"); Arguments args24899; args24899.Add(s->LocalAt(11), false); return Call(c, fn24898, std::move(args24899)); }()); Value v24897; v24897 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v24896, v24897))) return Value(false); v24896 = v24897; return Value(true); }()); if (!static_cast<bool>(v24895)) return v24895; v24895 = ([&]() -> Value { auto v24900 = Slice(s->LocalAt(11), Value{}, Value(int64_t{2}), Value{}); Value v24901; v24901 = List({Value("SELL"), s->LocalAt(6)}); if (!static_cast<bool>(Binary("Eq", v24900, v24901))) return Value(false); v24900 = v24901; return Value(true); }()); return v24895; }()))) {
auto v24902 = ([&]() -> Value { auto v24903 = ([&]() -> Value { auto fn24904 = s->Global("int"); Arguments args24905; args24905.Add(Get(s->LocalAt(11), Value(int64_t{2})), false); return Call(c, fn24904, std::move(args24905)); }()); return Binary("Add", v24903, s->LocalAt(4)); }());
Put(s->LocalAt(11), Value(int64_t{2}), v24902);
exhausted24893 = false;
break;
}
}
if (exhausted24893) {
if (static_cast<bool>(([&]() -> Value { auto v24906 = ([&]() -> Value { auto fn24908 = s->Global("len"); Arguments args24909; args24909.Add(s->LocalAt(7), false); return Call(c, fn24908, std::move(args24909)); }()); Value v24907; v24907 = Value(int64_t{10}); if (!static_cast<bool>(Binary("Lt", v24906, v24907))) return Value(false); v24906 = v24907; return Value(true); }()))) {
(void)([&]() -> Value { auto fn24910 = Attribute(s->LocalAt(7), "insert"); Arguments args24911; args24911.positional.reserve(2); args24911.Add(Value(int64_t{0}), false); args24911.Add(List({Value("SELL"), s->LocalAt(6), s->LocalAt(4)}), false); return Call(c, fn24910, std::move(args24911)); }());
}
else {
auto v24912 = Value(int64_t{0});
s->SetAt(4, v24912);
}
}
auto v24913 = s->LocalAt(19);
auto v24914 = Value("credit");
auto v24915 = Get(v24913, v24914);
Put(v24913, v24914, Inplace("Sub", v24915, s->LocalAt(4)));
auto v24916 = s->Global("_HD2_REPORT");
auto v24917 = Value("hd2_sold_units");
auto v24918 = Get(v24916, v24917);
Put(v24916, v24917, Inplace("Add", v24918, s->LocalAt(4)));
}
}
auto v24919 = s->LocalAt(7);
Put(s->LocalAt(0), Value("market"), v24919);
return {};
}
}  // namespace kagg::opponents::compiled
