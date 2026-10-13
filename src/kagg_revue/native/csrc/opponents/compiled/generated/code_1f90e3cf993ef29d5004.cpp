// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_1f90e3cf993ef29d5004(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"_", "actor", "bundles", "carried", "chosen", "cursor", "direct", "distance", "event", "farm", "first", "future_deposits", "horizon", "inventory", "item", "key", "mature", "max_per_actor", "obligation", "offset", "operations", "ops", "owners", "pos", "prefix_deposits", "prices", "private", "proposals", "route", "row", "run", "second", "seen", "stops", "tile", "value", "variants", "x", "xy", "y"};
s->PrepareSlots(s_names);
auto v12692 = ([&]() -> Value { auto dict12693 = Dict(); return dict12693; }());
s->SetAt(22, v12692);
for (const auto& item12694 : Iterate(Get(s->LocalAt(30), Value("events")))) {
s->SetAt(8, item12694);
if (static_cast<bool>(([&]() -> Value { auto v12695 = Value("acquired"); Value v12696; v12696 = s->LocalAt(8); if (!static_cast<bool>(Binary("In", v12695, v12696))) return Value(false); v12695 = v12696; return Value(true); }()))) {
(void)([&]() -> Value { auto fn12697 = Attribute(([&]() -> Value { auto fn12699 = Attribute(s->LocalAt(22), "setdefault"); Arguments args12700; args12700.positional.reserve(2); args12700.Add(Tuple({([&]() -> Value { auto fn12701 = s->Global("tuple"); Arguments args12702; args12702.Add(Get(s->LocalAt(8), Value("xy")), false); return Call(c, fn12701, std::move(args12702)); }()), Get(s->LocalAt(8), Value("op"))}), false); args12700.Add(([&]() -> Value { auto fn12703 = s->Global("set"); Arguments args12704; return Call(c, fn12703, std::move(args12704)); }()), false); return Call(c, fn12699, std::move(args12700)); }()), "add"); Arguments args12698; args12698.Add(Get(s->LocalAt(8), Value("actor")), false); return Call(c, fn12697, std::move(args12698)); }());
}
}
auto v12705 = List({});
s->SetAt(27, v12705);
auto v12706 = ([&]() -> Value { auto fn12707 = s->Global("set"); Arguments args12708; return Call(c, fn12707, std::move(args12708)); }());
s->SetAt(32, v12706);
auto v12709 = ([&]() -> Value { auto fn12710 = s->Global("len"); Arguments args12711; args12711.Add(Get(s->LocalAt(30), Value("rows")), false); return Call(c, fn12710, std::move(args12711)); }());
s->SetAt(12, v12709);
for (const auto& item12712 : Iterate(([&]() -> Value { auto fn12713 = s->Global("range"); Arguments args12714; args12714.Add(s->LocalAt(12), false); return Call(c, fn12713, std::move(args12714)); }()))) {
s->SetAt(19, item12712);
auto v12715 = Get(Get(s->LocalAt(30), Value("states")), s->LocalAt(19));
auto unpack12716 = Iterate(v12715);
ValidateUnpack(unpack12716, 2, false);
s->SetAt(9, unpack12716.at(0));
s->SetAt(26, unpack12716.at(1));
auto v12717 = ([&]() -> Value { auto fn12718 = s->Global("tuple"); Arguments args12719; args12719.Add((static_cast<bool>(([&]() -> Value { auto v12720 = s->LocalAt(1); Value v12721; v12721 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v12720, v12721))) return Value(false); v12720 = v12721; return Value(true); }())) ? Get(s->LocalAt(9), Value("farmer")) : Get(Get(s->LocalAt(9), Value("hands")), ([&]() -> Value { auto v12722 = s->LocalAt(1); return Binary("Sub", v12722, Value(int64_t{1})); }()))), false); return Call(c, fn12718, std::move(args12719)); }());
s->SetAt(23, v12717);
auto v12723 = Get(Get(s->LocalAt(26), Value("inventories")), s->LocalAt(1));
s->SetAt(13, v12723);
auto v12724 = ([&]() -> Value { auto fn12725 = s->Global("sum"); Arguments args12726; args12726.Add(([&]() -> Value { auto comp12727 = std::make_shared<Scope>(); comp12727->globals = s->globals; comp12727->parent = s; static constexpr const char* comp12727_names[] = {"count", "item"}; comp12727->PrepareSlots(comp12727_names); auto result12728 = List(); for (const auto& item12729 : Iterate(([&]() -> Value { auto fn12730 = Attribute(s->LocalAt(13), "items"); Arguments args12731; return Call(c, fn12730, std::move(args12731)); }()))) { auto unpack12732 = Iterate(item12729); ValidateUnpack(unpack12732, 2, false); comp12727->SetAt(1, unpack12732.at(0)); comp12727->SetAt(0, unpack12732.at(1)); result12728.node()->sequence.push_back(([&]() -> Value { auto v12733 = ([&]() -> Value { auto fn12734 = PrepareDictionaryGet(comp12727->Captured("prices")); Arguments args12735; args12735.positional.reserve(2); args12735.Add(comp12727->LocalAt(1), false); args12735.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn12734, std::move(args12735)); }()); return Binary("Mult", v12733, comp12727->LocalAt(0)); }())); } return result12728; }()), false); return Call(c, fn12725, std::move(args12726)); }());
s->SetAt(3, v12724);
auto v12736 = (static_cast<bool>(s->LocalAt(19)) ? Get(Get(Get(Get(s->LocalAt(30), Value("rows")), ([&]() -> Value { auto v12737 = s->LocalAt(19); return Binary("Sub", v12737, Value(int64_t{1})); }())), Value("deposited_by_actor")), s->LocalAt(1)) : ([&]() -> Value { auto dict12738 = Dict(); return dict12738; }()));
s->SetAt(24, v12736);
auto v12739 = Get(Get(Get(Get(s->LocalAt(30), Value("rows")), Unary("USub", Value(int64_t{1}))), Value("deposited_by_actor")), s->LocalAt(1));
s->SetAt(11, v12739);
auto v12740 = ([&]() -> Value { auto fn12741 = s->Global("sum"); Arguments args12742; args12742.Add(([&]() -> Value { auto comp12743 = std::make_shared<Scope>(); comp12743->globals = s->globals; comp12743->parent = s; static constexpr const char* comp12743_names[] = {"count", "item"}; comp12743->PrepareSlots(comp12743_names); auto result12744 = List(); for (const auto& item12745 : Iterate(([&]() -> Value { auto fn12746 = Attribute(s->LocalAt(11), "items"); Arguments args12747; return Call(c, fn12746, std::move(args12747)); }()))) { auto unpack12748 = Iterate(item12745); ValidateUnpack(unpack12748, 2, false); comp12743->SetAt(1, unpack12748.at(0)); comp12743->SetAt(0, unpack12748.at(1)); result12744.node()->sequence.push_back(([&]() -> Value { auto v12749 = ([&]() -> Value { auto fn12750 = PrepareDictionaryGet(comp12743->Captured("prices")); Arguments args12751; args12751.positional.reserve(2); args12751.Add(comp12743->LocalAt(1), false); args12751.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn12750, std::move(args12751)); }()); return Binary("Mult", v12749, ([&]() -> Value { auto v12752 = comp12743->LocalAt(0); return Binary("Sub", v12752, ([&]() -> Value { auto fn12753 = PrepareDictionaryGet(comp12743->Captured("prefix_deposits")); Arguments args12754; args12754.positional.reserve(2); args12754.Add(comp12743->LocalAt(1), false); args12754.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn12753, std::move(args12754)); }())); }())); }())); } return result12744; }()), false); return Call(c, fn12741, std::move(args12742)); }());
s->SetAt(18, v12740);
auto v12755 = List({});
s->SetAt(2, v12755);
for (const auto& item12756 : Iterate(([&]() -> Value { auto fn12757 = s->Global("enumerate"); Arguments args12758; args12758.Add(Get(s->LocalAt(9), Value("tiles")), false); return Call(c, fn12757, std::move(args12758)); }()))) {
auto unpack12759 = Iterate(item12756);
ValidateUnpack(unpack12759, 2, false);
s->SetAt(39, unpack12759.at(0));
s->SetAt(29, unpack12759.at(1));
for (const auto& item12760 : Iterate(([&]() -> Value { auto fn12761 = s->Global("enumerate"); Arguments args12762; args12762.Add(s->LocalAt(29), false); return Call(c, fn12761, std::move(args12762)); }()))) {
auto unpack12763 = Iterate(item12760);
ValidateUnpack(unpack12763, 2, false);
s->SetAt(37, unpack12763.at(0));
s->SetAt(34, unpack12763.at(1));
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto fn12764 = s->Global("isinstance"); Arguments args12765; args12765.positional.reserve(2); args12765.Add(s->LocalAt(34), false); args12765.Add(s->Global("dict"), false); return Call(c, fn12764, std::move(args12765)); }())))) {
continue;
}
auto v12766 = Tuple({Tuple({s->LocalAt(37), s->LocalAt(39)}), List({}), Value(int64_t{0})});
auto unpack12767 = Iterate(v12766);
ValidateUnpack(unpack12767, 3, false);
s->SetAt(38, unpack12767.at(0));
s->SetAt(20, unpack12767.at(1));
s->SetAt(35, unpack12767.at(2));
if (static_cast<bool>(([&]() -> Value { auto v12768 = ([&]() -> Value { auto fn12770 = PrepareDictionaryGet(s->LocalAt(34)); Arguments args12771; args12771.positional.reserve(2); args12771.Add(Value("yield_units"), false); args12771.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn12770, std::move(args12771)); }()); Value v12769; v12769 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v12768, v12769))) return Value(false); v12768 = v12769; return Value(true); }()))) {
auto v12772 = (static_cast<bool>(([&]() -> Value { auto v12773 = ([&]() -> Value { auto fn12775 = PrepareDictionaryGet(s->LocalAt(34)); Arguments args12776; args12776.Add(Value("kind"), false); return CallDictionaryGet(c, fn12775, std::move(args12776)); }()); Value v12774; v12774 = Value("PLANT"); if (!static_cast<bool>(Binary("Eq", v12773, v12774))) return Value(false); v12773 = v12774; return Value(true); }())) ? ([&]() -> Value { auto fn12777 = PrepareDictionaryGet(s->LocalAt(34)); Arguments args12778; args12778.Add(Value("crop"), false); return CallDictionaryGet(c, fn12777, std::move(args12778)); }()) : ([&]() -> Value { auto fn12779 = PrepareDictionaryGet(([&]() -> Value { auto fn12781 = PrepareDictionaryGet(s->Global("ANIMALS")); Arguments args12782; args12782.positional.reserve(2); args12782.Add(([&]() -> Value { auto fn12783 = PrepareDictionaryGet(s->LocalAt(34)); Arguments args12784; args12784.Add(Value("animal"), false); return CallDictionaryGet(c, fn12783, std::move(args12784)); }()), false); args12782.Add(([&]() -> Value { auto dict12785 = Dict(); return dict12785; }()), false); return CallDictionaryGet(c, fn12781, std::move(args12782)); }())); Arguments args12780; args12780.Add(Value("product"), false); return CallDictionaryGet(c, fn12779, std::move(args12780)); }()));
s->SetAt(14, v12772);
auto v12786 = ([&]() -> Value { auto v12787 = s->LocalAt(14); if (!static_cast<bool>(v12787)) return v12787; v12787 = ([&]() -> Value { auto v12788 = ([&]() -> Value { auto v12789 = Value("animal"); Value v12790; v12790 = s->LocalAt(34); if (!static_cast<bool>(Binary("In", v12789, v12790))) return Value(false); v12789 = v12790; return Value(true); }()); if (static_cast<bool>(v12788)) return v12788; v12788 = ([&]() -> Value { auto v12791 = ([&]() -> Value { auto v12793 = ([&]() -> Value { auto v12794 = ([&]() -> Value { auto v12795 = s->Global("START"); return Binary("Add", v12795, s->LocalAt(19)); }()); return Binary("FloorDiv", v12794, Value(int64_t{24})); }()); return Binary("Sub", v12793, Get(s->LocalAt(34), Value("planted_day"))); }()); Value v12792; v12792 = Get(Get(s->Global("CROPS"), s->LocalAt(14)), Value("first_yield_day")); if (!static_cast<bool>(Binary("GtE", v12791, v12792))) return Value(false); v12791 = v12792; return Value(true); }()); return v12788; }()); return v12787; }());
s->SetAt(16, v12786);
if (static_cast<bool>(([&]() -> Value { auto v12796 = s->LocalAt(16); if (!static_cast<bool>(v12796)) return v12796; v12796 = Unary("Not", ([&]() -> Value { auto v12797 = ([&]() -> Value { auto fn12798 = PrepareDictionaryGet(s->LocalAt(22)); Arguments args12799; args12799.positional.reserve(2); args12799.Add(Tuple({s->LocalAt(38), Value("HARVEST")}), false); args12799.Add(([&]() -> Value { auto fn12800 = s->Global("set"); Arguments args12801; return Call(c, fn12800, std::move(args12801)); }()), false); return CallDictionaryGet(c, fn12798, std::move(args12799)); }()); return Binary("Sub", v12797, Set({s->LocalAt(1)})); }())); return v12796; }()))) {
(void)([&]() -> Value { auto fn12802 = Attribute(s->LocalAt(20), "append"); Arguments args12803; args12803.Add(List({Value("HARVEST")}), false); return Call(c, fn12802, std::move(args12803)); }());
auto v12804 = s->LocalAt(35);
s->SetAt(35, Inplace("Add", v12804, ([&]() -> Value { auto v12805 = Get(s->LocalAt(25), s->LocalAt(14)); return Binary("Mult", v12805, Get(s->LocalAt(34), Value("yield_units"))); }())));
}
}
if (static_cast<bool>(([&]() -> Value { auto v12806 = ([&]() -> Value { auto fn12807 = PrepareDictionaryGet(s->LocalAt(34)); Arguments args12808; args12808.Add(Value("fertilizer_available"), false); return CallDictionaryGet(c, fn12807, std::move(args12808)); }()); if (!static_cast<bool>(v12806)) return v12806; v12806 = ([&]() -> Value { auto v12809 = Value("animal"); Value v12810; v12810 = s->LocalAt(34); if (!static_cast<bool>(Binary("In", v12809, v12810))) return Value(false); v12809 = v12810; return Value(true); }()); if (!static_cast<bool>(v12806)) return v12806; v12806 = Unary("Not", ([&]() -> Value { auto v12811 = ([&]() -> Value { auto fn12812 = PrepareDictionaryGet(s->LocalAt(22)); Arguments args12813; args12813.positional.reserve(2); args12813.Add(Tuple({s->LocalAt(38), Value("COLLECT_FERTILIZER")}), false); args12813.Add(([&]() -> Value { auto fn12814 = s->Global("set"); Arguments args12815; return Call(c, fn12814, std::move(args12815)); }()), false); return CallDictionaryGet(c, fn12812, std::move(args12813)); }()); return Binary("Sub", v12811, Set({s->LocalAt(1)})); }())); return v12806; }()))) {
(void)([&]() -> Value { auto fn12816 = Attribute(s->LocalAt(20), "append"); Arguments args12817; args12817.Add(List({Value("COLLECT_FERTILIZER")}), false); return Call(c, fn12816, std::move(args12817)); }());
auto v12818 = s->LocalAt(35);
s->SetAt(35, Inplace("Add", v12818, Get(s->LocalAt(25), Value("FERTILIZER"))));
}
if (static_cast<bool>(s->LocalAt(20))) {
auto v12819 = ([&]() -> Value { auto v12820 = ([&]() -> Value { auto v12821 = ([&]() -> Value { auto v12822 = ([&]() -> Value { auto fn12823 = s->Global("abs"); Arguments args12824; args12824.Add(([&]() -> Value { auto v12825 = Get(s->LocalAt(23), Value(int64_t{0})); return Binary("Sub", v12825, Get(s->LocalAt(38), Value(int64_t{0}))); }()), false); return Call(c, fn12823, std::move(args12824)); }()); return Binary("Add", v12822, ([&]() -> Value { auto fn12826 = s->Global("abs"); Arguments args12827; args12827.Add(([&]() -> Value { auto v12828 = Get(s->LocalAt(23), Value(int64_t{1})); return Binary("Sub", v12828, Get(s->LocalAt(38), Value(int64_t{1}))); }()), false); return Call(c, fn12826, std::move(args12827)); }())); }()); return Binary("Add", v12821, ([&]() -> Value { auto fn12829 = s->Global("len"); Arguments args12830; args12830.Add(s->LocalAt(20), false); return Call(c, fn12829, std::move(args12830)); }())); }()); return Binary("Add", v12820, Get(s->Global("_R150_HOME_DISTANCE"), s->LocalAt(38))); }());
s->SetAt(7, v12819);
if (static_cast<bool>(([&]() -> Value { auto v12831 = s->LocalAt(7); Value v12832; v12832 = ([&]() -> Value { auto v12833 = s->LocalAt(12); return Binary("Sub", v12833, s->LocalAt(19)); }()); if (!static_cast<bool>(Binary("LtE", v12831, v12832))) return Value(false); v12831 = v12832; return Value(true); }()))) {
(void)([&]() -> Value { auto fn12834 = Attribute(s->LocalAt(2), "append"); Arguments args12835; args12835.Add(Tuple({s->LocalAt(38), s->LocalAt(20), s->LocalAt(35), s->LocalAt(7)}), false); return Call(c, fn12834, std::move(args12835)); }());
}
}
}
}
(void)([&]() -> Value { auto fn12836 = Attribute(s->LocalAt(2), "sort"); Arguments args12837; args12837.Keyword("key", Define(&Code_7919700657fcef6a8187, s, Signature{{"b"}, {}, {}, {}, "", "", ([]() -> std::span<const char* const> { static constexpr const char* names[] = {"b"}; return names; }())}, true, "<lambda>")); return Call(c, fn12836, std::move(args12837)); }());
auto v12838 = (static_cast<bool>(s->LocalAt(3)) ? List({Tuple({List({}), s->LocalAt(3)})}) : List({}));
s->SetAt(36, v12838);
for (const auto& item12839 : Iterate(Slice(s->LocalAt(2), Value{}, Value(int64_t{6}), Value{}))) {
auto unpack12840 = Iterate(item12839);
ValidateUnpack(unpack12840, 4, false);
s->SetAt(38, unpack12840.at(0));
s->SetAt(21, unpack12840.at(1));
s->SetAt(35, unpack12840.at(2));
s->SetAt(0, unpack12840.at(3));
(void)([&]() -> Value { auto fn12841 = Attribute(s->LocalAt(36), "append"); Arguments args12842; args12842.Add(Tuple({List({Tuple({s->LocalAt(38), s->LocalAt(21)})}), ([&]() -> Value { auto v12843 = s->LocalAt(3); return Binary("Add", v12843, s->LocalAt(35)); }())}), false); return Call(c, fn12841, std::move(args12842)); }());
}
for (const auto& item12844 : Iterate(Slice(s->LocalAt(2), Value{}, Value(int64_t{3}), Value{}))) {
s->SetAt(10, item12844);
for (const auto& item12845 : Iterate(Slice(s->LocalAt(2), Value{}, Value(int64_t{3}), Value{}))) {
s->SetAt(31, item12845);
if (static_cast<bool>(([&]() -> Value { auto v12846 = Get(s->LocalAt(10), Value(int64_t{0})); Value v12847; v12847 = Get(s->LocalAt(31), Value(int64_t{0})); if (!static_cast<bool>(Binary("NotEq", v12846, v12847))) return Value(false); v12846 = v12847; return Value(true); }()))) {
(void)([&]() -> Value { auto fn12848 = Attribute(s->LocalAt(36), "append"); Arguments args12849; args12849.Add(Tuple({List({Tuple({Get(s->LocalAt(10), Value(int64_t{0})), Get(s->LocalAt(10), Value(int64_t{1}))}), Tuple({Get(s->LocalAt(31), Value(int64_t{0})), Get(s->LocalAt(31), Value(int64_t{1}))})}), ([&]() -> Value { auto v12850 = ([&]() -> Value { auto v12851 = s->LocalAt(3); return Binary("Add", v12851, Get(s->LocalAt(10), Value(int64_t{2}))); }()); return Binary("Add", v12850, Get(s->LocalAt(31), Value(int64_t{2}))); }())}), false); return Call(c, fn12848, std::move(args12849)); }());
}
}
}
for (const auto& item12852 : Iterate(s->LocalAt(36))) {
auto unpack12853 = Iterate(item12852);
ValidateUnpack(unpack12853, 2, false);
s->SetAt(33, unpack12853.at(0));
s->SetAt(35, unpack12853.at(1));
auto v12854 = Tuple({List({}), s->LocalAt(23)});
auto unpack12855 = Iterate(v12854);
ValidateUnpack(unpack12855, 2, false);
s->SetAt(28, unpack12855.at(0));
s->SetAt(5, unpack12855.at(1));
for (const auto& item12856 : Iterate(s->LocalAt(33))) {
auto unpack12857 = Iterate(item12856);
ValidateUnpack(unpack12857, 2, false);
s->SetAt(38, unpack12857.at(0));
s->SetAt(21, unpack12857.at(1));
auto v12858 = s->LocalAt(28);
s->SetAt(28, Inplace("Add", v12858, ([&]() -> Value { auto v12859 = ([&]() -> Value { auto fn12860 = s->Global("_walk"); Arguments args12861; args12861.positional.reserve(2); args12861.Add(s->LocalAt(5), false); args12861.Add(s->LocalAt(38), false); return Call(c, fn12860, std::move(args12861)); }()); return Binary("Add", v12859, s->LocalAt(21)); }())));
auto v12862 = s->LocalAt(38);
s->SetAt(5, v12862);
}
auto v12863 = s->LocalAt(28);
s->SetAt(28, Inplace("Add", v12863, ([&]() -> Value { auto fn12864 = s->Global("_return"); Arguments args12865; args12865.Add(s->LocalAt(5), false); return Call(c, fn12864, std::move(args12865)); }())));
if (static_cast<bool>(([&]() -> Value { auto v12866 = ([&]() -> Value { auto fn12868 = s->Global("len"); Arguments args12869; args12869.Add(s->LocalAt(28), false); return Call(c, fn12868, std::move(args12869)); }()); Value v12867; v12867 = ([&]() -> Value { auto v12870 = s->LocalAt(12); return Binary("Sub", v12870, s->LocalAt(19)); }()); if (!static_cast<bool>(Binary("Gt", v12866, v12867))) return Value(false); v12866 = v12867; return Value(true); }()))) {
continue;
}
auto v12871 = s->LocalAt(28);
s->SetAt(28, Inplace("Add", v12871, ([&]() -> Value { auto v12872 = List({List({Value("PASS")})}); return Binary("Mult", v12872, ([&]() -> Value { auto v12873 = ([&]() -> Value { auto v12874 = s->LocalAt(12); return Binary("Sub", v12874, s->LocalAt(19)); }()); return Binary("Sub", v12873, ([&]() -> Value { auto fn12875 = s->Global("len"); Arguments args12876; args12876.Add(s->LocalAt(28), false); return Call(c, fn12875, std::move(args12876)); }())); }())); }())));
auto v12877 = Tuple({s->LocalAt(19), ([&]() -> Value { auto fn12878 = s->Global("tuple"); Arguments args12879; args12879.Add(([&]() -> Value { auto comp12880 = std::make_shared<Scope>(); comp12880->globals = s->globals; comp12880->parent = s; static constexpr const char* comp12880_names[] = {"c"}; comp12880->PrepareSlots(comp12880_names); auto result12881 = List(); for (const auto& item12882 : Iterate(s->LocalAt(28))) { comp12880->SetAt(0, item12882); result12881.node()->sequence.push_back(([&]() -> Value { auto fn12883 = comp12880->Global("tuple"); Arguments args12884; args12884.Add(comp12880->LocalAt(0), false); return Call(c, fn12883, std::move(args12884)); }())); } return result12881; }()), false); return Call(c, fn12878, std::move(args12879)); }())});
s->SetAt(15, v12877);
if (static_cast<bool>(([&]() -> Value { auto v12885 = s->LocalAt(15); Value v12886; v12886 = s->LocalAt(32); if (!static_cast<bool>(Binary("NotIn", v12885, v12886))) return Value(false); v12885 = v12886; return Value(true); }()))) {
(void)([&]() -> Value { auto fn12887 = Attribute(s->LocalAt(32), "add"); Arguments args12888; args12888.Add(s->LocalAt(15), false); return Call(c, fn12887, std::move(args12888)); }());
(void)([&]() -> Value { auto fn12889 = Attribute(s->LocalAt(27), "append"); Arguments args12890; args12890.Add(Tuple({([&]() -> Value { auto v12891 = s->LocalAt(35); return Binary("Sub", v12891, s->LocalAt(18)); }()), s->LocalAt(19), s->LocalAt(28), ([&]() -> Value { auto fn12892 = s->Global("len"); Arguments args12893; args12893.Add(s->LocalAt(33), false); return Call(c, fn12892, std::move(args12893)); }())}), false); return Call(c, fn12889, std::move(args12890)); }());
}
}
}
(void)([&]() -> Value { auto fn12894 = Attribute(s->LocalAt(27), "sort"); Arguments args12895; args12895.Keyword("key", Define(&Code_85a5717568583c703879, s, Signature{{"p"}, {}, {}, {}, "", "", ([]() -> std::span<const char* const> { static constexpr const char* names[] = {"p"}; return names; }())}, true, "<lambda>")); return Call(c, fn12894, std::move(args12895)); }());
auto v12896 = Slice(([&]() -> Value { auto comp12897 = std::make_shared<Scope>(); comp12897->globals = s->globals; comp12897->parent = s; static constexpr const char* comp12897_names[] = {"p"}; comp12897->PrepareSlots(comp12897_names); auto result12898 = List(); for (const auto& item12899 : Iterate(s->LocalAt(27))) { comp12897->SetAt(0, item12899); if (!static_cast<bool>(([&]() -> Value { auto v12900 = ([&]() -> Value { auto v12901 = Get(comp12897->LocalAt(0), Value(int64_t{3})); Value v12902; v12902 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v12901, v12902))) return Value(false); v12901 = v12902; return Value(true); }()); if (!static_cast<bool>(v12900)) return v12900; v12900 = ([&]() -> Value { auto v12903 = Get(comp12897->LocalAt(0), Value(int64_t{0})); Value v12904; v12904 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v12903, v12904))) return Value(false); v12903 = v12904; return Value(true); }()); return v12900; }()))) continue; result12898.node()->sequence.push_back(comp12897->LocalAt(0)); } return result12898; }()), Value{}, Value(int64_t{2}), Value{});
s->SetAt(6, v12896);
auto v12905 = ([&]() -> Value { auto v12906 = s->LocalAt(6); return Binary("Add", v12906, ([&]() -> Value { auto comp12907 = std::make_shared<Scope>(); comp12907->globals = s->globals; comp12907->parent = s; static constexpr const char* comp12907_names[] = {"p"}; comp12907->PrepareSlots(comp12907_names); auto result12908 = List(); for (const auto& item12909 : Iterate(s->LocalAt(27))) { comp12907->SetAt(0, item12909); if (!static_cast<bool>(([&]() -> Value { auto v12910 = comp12907->LocalAt(0); Value v12911; v12911 = comp12907->Captured("direct"); if (!static_cast<bool>(Binary("NotIn", v12910, v12911))) return Value(false); v12910 = v12911; return Value(true); }()))) continue; result12908.node()->sequence.push_back(comp12907->LocalAt(0)); } return result12908; }())); }());
s->SetAt(4, v12905);
return Slice(s->LocalAt(4), Value{}, s->LocalAt(17), Value{});
return {};
}
}  // namespace kagg::opponents::compiled
