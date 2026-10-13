// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_82f06cd51aab12ee8f52(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "budget", "committed", "day", "deadline", "expected", "extra", "farm", "hour", "incoming", "initial", "last_native_hire", "market", "native", "o", "obs", "parent_hires", "planned", "result", "state", "step", "stock"};
s->PrepareSlots(s_names);
auto v28619 = ([&]() -> Value { auto fn28620 = s->Global("int"); Arguments args28621; args28621.Add(Get(s->LocalAt(15), Value("step")), false); return Call(c, fn28620, std::move(args28621)); }());
s->SetAt(20, v28619);
auto v28622 = ([&]() -> Value { auto v28623 = s->LocalAt(20); return Binary("FloorDiv", v28623, Value(int64_t{24})); }());
s->SetAt(3, v28622);
auto v28624 = ([&]() -> Value { auto v28625 = s->LocalAt(20); return Binary("Mod", v28625, Value(int64_t{24})); }());
s->SetAt(8, v28624);
if (static_cast<bool>(([&]() -> Value { auto v28626 = ([&]() -> Value { auto fn28628 = PrepareDictionaryGet(s->LocalAt(19)); Arguments args28629; args28629.Add(Value("requested_day"), false); return CallDictionaryGet(c, fn28628, std::move(args28629)); }()); Value v28627; v28627 = s->LocalAt(3); if (!static_cast<bool>(Binary("Eq", v28626, v28627))) return Value(false); v28626 = v28627; return Value(true); }()))) {
return s->LocalAt(0);
}
auto v28630 = ([&]() -> Value { auto fn28631 = PrepareDictionaryGet(s->LocalAt(19)); Arguments args28632; args28632.Add(Value("committed"), false); return CallDictionaryGet(c, fn28631, std::move(args28632)); }());
s->SetAt(2, v28630);
if (static_cast<bool>(([&]() -> Value { auto v28633 = Unary("Not", s->LocalAt(2)); if (!static_cast<bool>(v28633)) return v28633; v28633 = ([&]() -> Value { auto v28634 = ([&]() -> Value { auto v28635 = s->LocalAt(8); Value v28636; v28636 = (static_cast<bool>(([&]() -> Value { auto v28637 = s->LocalAt(3); Value v28638; v28638 = Value(int64_t{11}); if (!static_cast<bool>(Binary("Eq", v28637, v28638))) return Value(false); v28637 = v28638; return Value(true); }())) ? Value(int64_t{3}) : Value(int64_t{1})); if (!static_cast<bool>(Binary("Gt", v28635, v28636))) return Value(false); v28635 = v28636; return Value(true); }()); if (static_cast<bool>(v28634)) return v28634; v28634 = ([&]() -> Value { auto v28639 = s->LocalAt(3); Value v28640; v28640 = Tuple({Value(int64_t{11}), Value(int64_t{12})}); if (!static_cast<bool>(Binary("NotIn", v28639, v28640))) return Value(false); v28639 = v28640; return Value(true); }()); if (static_cast<bool>(v28634)) return v28634; v28634 = Unary("Not", ([&]() -> Value { auto fn28641 = s->Global("_v233_eligible"); Arguments args28642; args28642.positional.reserve(2); args28642.Add(s->LocalAt(15), false); args28642.Add(s->LocalAt(13), false); return Call(c, fn28641, std::move(args28642)); }())); return v28634; }()); return v28633; }()))) {
return s->LocalAt(0);
}
auto v28643 = ([&]() -> Value { auto fn28644 = s->Global("_v219_native_day"); Arguments args28645; args28645.positional.reserve(2); args28645.Add(s->LocalAt(13), false); args28645.Add(s->LocalAt(3), false); return Call(c, fn28644, std::move(args28645)); }());
s->SetAt(17, v28643);
auto v28646 = (static_cast<bool>(s->LocalAt(2)) ? Value(int64_t{2}) : (static_cast<bool>(([&]() -> Value { auto v28647 = s->LocalAt(3); Value v28648; v28648 = Value(int64_t{11}); if (!static_cast<bool>(Binary("Eq", v28647, v28648))) return Value(false); v28647 = v28648; return Value(true); }())) ? Value(int64_t{3}) : Value(int64_t{1})));
s->SetAt(4, v28646);
if (static_cast<bool>(s->LocalAt(2))) {
auto v28649 = ([&]() -> Value { auto fn28650 = s->Global("max"); Arguments args28651; args28651.Add(([&]() -> Value { auto comp28652 = std::make_shared<Scope>(); comp28652->globals = s->globals; comp28652->parent = s; static constexpr const char* comp28652_names[] = {"a", "h"}; comp28652->PrepareSlots(comp28652_names); auto result28653 = List(); for (const auto& item28654 : Iterate(([&]() -> Value { auto fn28655 = s->Global("enumerate"); Arguments args28656; args28656.Add(s->LocalAt(17), false); return Call(c, fn28655, std::move(args28656)); }()))) { auto unpack28657 = Iterate(item28654); ValidateUnpack(unpack28657, 2, false); comp28652->SetAt(1, unpack28657.at(0)); comp28652->SetAt(0, unpack28657.at(1)); if (!static_cast<bool>(([&]() -> Value { auto comp28658 = std::make_shared<Scope>(); comp28658->globals = comp28652->globals; comp28658->parent = comp28652; static constexpr const char* comp28658_names[] = {"o"}; comp28658->PrepareSlots(comp28658_names); auto result28659 = List(); for (const auto& item28660 : Iterate(([&]() -> Value { auto fn28661 = PrepareDictionaryGet(comp28652->LocalAt(0)); Arguments args28662; args28662.positional.reserve(2); args28662.Add(Value("market"), false); args28662.Add(List({}), false); return CallDictionaryGet(c, fn28661, std::move(args28662)); }()))) { comp28658->SetAt(0, item28660); if (static_cast<bool>(([&]() -> Value { auto v28663 = comp28658->LocalAt(0); if (!static_cast<bool>(v28663)) return v28663; v28663 = ([&]() -> Value { auto v28664 = Get(comp28658->LocalAt(0), Value(int64_t{0})); Value v28665; v28665 = Value("HIRE"); if (!static_cast<bool>(Binary("Eq", v28664, v28665))) return Value(false); v28664 = v28665; return Value(true); }()); return v28663; }()))) return Value(true); } return Value(false); }()))) continue; result28653.node()->sequence.push_back(comp28652->LocalAt(1)); } return result28653; }()), false); args28651.Keyword("default", Value(int64_t{0})); return Call(c, fn28650, std::move(args28651)); }());
s->SetAt(11, v28649);
if (static_cast<bool>(([&]() -> Value { auto v28666 = Value(int64_t{2}); Value v28667; v28667 = s->LocalAt(11); if (!static_cast<bool>(Binary("Lt", v28666, v28667))) return Value(false); v28666 = v28667; v28667 = Value(int64_t{6}); if (!static_cast<bool>(Binary("LtE", v28666, v28667))) return Value(false); v28666 = v28667; return Value(true); }()))) {
auto v28668 = Value(int64_t{6});
s->SetAt(4, v28668);
}
}
if (static_cast<bool>(([&]() -> Value { auto v28669 = s->LocalAt(8); Value v28670; v28670 = s->LocalAt(4); if (!static_cast<bool>(Binary("Gt", v28669, v28670))) return Value(false); v28669 = v28670; return Value(true); }()))) {
return s->LocalAt(0);
}
if (static_cast<bool>(([&]() -> Value { auto comp28671 = std::make_shared<Scope>(); comp28671->globals = s->globals; comp28671->parent = s; static constexpr const char* comp28671_names[] = {"a", "o"}; comp28671->PrepareSlots(comp28671_names); auto result28672 = List(); for (const auto& item28673 : Iterate(Slice(s->LocalAt(17), ([&]() -> Value { auto v28674 = s->LocalAt(8); return Binary("Add", v28674, Value(int64_t{1})); }()), Value{}, Value{}))) { comp28671->SetAt(0, item28673); for (const auto& item28675 : Iterate(([&]() -> Value { auto fn28676 = PrepareDictionaryGet(comp28671->LocalAt(0)); Arguments args28677; args28677.positional.reserve(2); args28677.Add(Value("market"), false); args28677.Add(List({}), false); return CallDictionaryGet(c, fn28676, std::move(args28677)); }()))) { comp28671->SetAt(1, item28675); if (static_cast<bool>(([&]() -> Value { auto v28678 = comp28671->LocalAt(1); if (!static_cast<bool>(v28678)) return v28678; v28678 = ([&]() -> Value { auto v28679 = Get(comp28671->LocalAt(1), Value(int64_t{0})); Value v28680; v28680 = Value("HIRE"); if (!static_cast<bool>(Binary("Eq", v28679, v28680))) return Value(false); v28679 = v28680; return Value(true); }()); return v28678; }()))) return Value(true); } } return Value(false); }()))) {
return s->LocalAt(0);
}
auto v28681 = Get(Get(s->LocalAt(15), Value("farms")), Get(s->LocalAt(15), Value("player")));
s->SetAt(7, v28681);
auto v28682 = ([&]() -> Value { auto fn28683 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args28684; args28684.positional.reserve(2); args28684.Add(Value("market"), false); args28684.Add(List({}), false); return CallDictionaryGet(c, fn28683, std::move(args28684)); }());
s->SetAt(12, v28682);
auto v28685 = ([&]() -> Value { auto fn28686 = s->Global("sum"); Arguments args28687; args28687.Add(([&]() -> Value { auto comp28688 = std::make_shared<Scope>(); comp28688->globals = s->globals; comp28688->parent = s; static constexpr const char* comp28688_names[] = {"o"}; comp28688->PrepareSlots(comp28688_names); auto result28689 = List(); for (const auto& item28690 : Iterate(s->LocalAt(12))) { comp28688->SetAt(0, item28690); result28689.node()->sequence.push_back(([&]() -> Value { auto v28691 = ([&]() -> Value { auto fn28692 = comp28688->Global("bool"); Arguments args28693; args28693.Add(comp28688->LocalAt(0), false); return Call(c, fn28692, std::move(args28693)); }()); if (!static_cast<bool>(v28691)) return v28691; v28691 = ([&]() -> Value { auto v28694 = Get(comp28688->LocalAt(0), Value(int64_t{0})); Value v28695; v28695 = Value("HIRE"); if (!static_cast<bool>(Binary("Eq", v28694, v28695))) return Value(false); v28694 = v28695; return Value(true); }()); return v28691; }())); } return result28689; }()), false); return Call(c, fn28686, std::move(args28687)); }());
s->SetAt(16, v28685);
auto v28696 = ([&]() -> Value { auto fn28697 = s->Global("max"); Arguments args28698; args28698.Add(([&]() -> Value { auto comp28699 = std::make_shared<Scope>(); comp28699->globals = s->globals; comp28699->parent = s; static constexpr const char* comp28699_names[] = {"a"}; comp28699->PrepareSlots(comp28699_names); auto result28700 = List(); for (const auto& item28701 : Iterate(s->LocalAt(17))) { comp28699->SetAt(0, item28701); result28700.node()->sequence.push_back(([&]() -> Value { auto fn28702 = comp28699->Global("len"); Arguments args28703; args28703.Add(([&]() -> Value { auto fn28704 = PrepareDictionaryGet(comp28699->LocalAt(0)); Arguments args28705; args28705.positional.reserve(2); args28705.Add(Value("hands"), false); args28705.Add(List({}), false); return CallDictionaryGet(c, fn28704, std::move(args28705)); }()), false); return Call(c, fn28702, std::move(args28703)); }())); } return result28700; }()), false); return Call(c, fn28697, std::move(args28698)); }());
s->SetAt(5, v28696);
if (static_cast<bool>(([&]() -> Value { auto v28706 = ([&]() -> Value { auto v28708 = ([&]() -> Value { auto fn28709 = s->Global("len"); Arguments args28710; args28710.Add(Get(s->LocalAt(7), Value("hands")), false); return Call(c, fn28709, std::move(args28710)); }()); return Binary("Add", v28708, s->LocalAt(16)); }()); Value v28707; v28707 = s->LocalAt(5); if (!static_cast<bool>(Binary("NotEq", v28706, v28707))) return Value(false); v28706 = v28707; return Value(true); }()))) {
return s->LocalAt(0);
}
auto v28711 = Unary("Not", ([&]() -> Value { auto fn28712 = PrepareDictionaryGet(s->LocalAt(19)); Arguments args28713; args28713.Add(Value("committed"), false); return CallDictionaryGet(c, fn28712, std::move(args28713)); }()));
s->SetAt(10, v28711);
auto v28714 = ([&]() -> Value { auto v28715 = (static_cast<bool>(s->LocalAt(10)) ? List({List({Value("BUY_LAND")}), List({Value("BUY_ANIMAL"), Value("SHEEP"), Value(int64_t{6})})}) : List({})); return Binary("Add", v28715, List({List({Value("BUY_PRODUCT"), Value("WHEAT"), Value(int64_t{6})}), List({Value("HIRE")}), List({Value("HIRE")})})); }());
s->SetAt(6, v28714);
if (static_cast<bool>(([&]() -> Value { auto v28716 = ([&]() -> Value { auto v28718 = ([&]() -> Value { auto fn28719 = s->Global("len"); Arguments args28720; args28720.Add(s->LocalAt(12), false); return Call(c, fn28719, std::move(args28720)); }()); return Binary("Add", v28718, ([&]() -> Value { auto fn28721 = s->Global("len"); Arguments args28722; args28722.Add(s->LocalAt(6), false); return Call(c, fn28721, std::move(args28722)); }())); }()); Value v28717; v28717 = s->Global("MAX_ORDERS"); if (!static_cast<bool>(Binary("Gt", v28716, v28717))) return Value(false); v28716 = v28717; return Value(true); }()))) {
return s->LocalAt(0);
}
auto v28723 = ([&]() -> Value { auto fn28724 = s->Global("projected_shed"); Arguments args28725; args28725.positional.reserve(2); args28725.Add(s->LocalAt(0), false); args28725.Add(([&]() -> Value { auto fn28726 = s->Global("FarmView"); Arguments args28727; args28727.Add(s->LocalAt(15), false); return Call(c, fn28726, std::move(args28727)); }()), false); return Call(c, fn28724, std::move(args28725)); }());
s->SetAt(21, v28723);
auto v28728 = ([&]() -> Value { auto v28729 = Value(int64_t{6}); return Binary("Add", v28729, ([&]() -> Value { auto v28730 = Value(int64_t{6}); return Binary("Mult", v28730, s->LocalAt(10)); }())); }());
s->SetAt(9, v28728);
auto v28731 = ([&]() -> Value { auto v28732 = ([&]() -> Value { auto v28733 = Value(int64_t{7000}); return Binary("Mult", v28733, s->LocalAt(10)); }()); return Binary("Add", v28732, ([&]() -> Value { auto v28734 = Value(int64_t{6}); return Binary("Mult", v28734, ([&]() -> Value { auto v28735 = ([&]() -> Value { auto fn28736 = s->Global("int"); Arguments args28737; args28737.Add(Get(Get(Get(s->LocalAt(15), Value("market")), Value("prices")), Value("WHEAT")), false); return Call(c, fn28736, std::move(args28737)); }()); return Binary("Add", v28735, Value(int64_t{10})); }())); }())); }());
s->SetAt(1, v28731);
auto v28738 = s->LocalAt(1);
s->SetAt(1, Inplace("Add", v28738, ([&]() -> Value { auto fn28739 = s->Global("sum"); Arguments args28740; args28740.Add(([&]() -> Value { auto comp28741 = std::make_shared<Scope>(); comp28741->globals = s->globals; comp28741->parent = s; static constexpr const char* comp28741_names[] = {"n"}; comp28741->PrepareSlots(comp28741_names); auto result28742 = List(); for (const auto& item28743 : Iterate(([&]() -> Value { auto fn28744 = s->Global("range"); Arguments args28745; args28745.positional.reserve(2); args28745.Add(Get(s->LocalAt(7), Value("hires_today")), false); args28745.Add(([&]() -> Value { auto v28746 = ([&]() -> Value { auto v28747 = Get(s->LocalAt(7), Value("hires_today")); return Binary("Add", v28747, s->LocalAt(16)); }()); return Binary("Add", v28746, Value(int64_t{2})); }()), false); return Call(c, fn28744, std::move(args28745)); }()))) { comp28741->SetAt(0, item28743); result28742.node()->sequence.push_back(([&]() -> Value { auto fn28748 = comp28741->Global("_v219_fib"); Arguments args28749; args28749.Add(comp28741->LocalAt(0), false); return Call(c, fn28748, std::move(args28749)); }())); } return result28742; }()), false); return Call(c, fn28739, std::move(args28740)); }())));
for (const auto& item28750 : Iterate(s->LocalAt(12))) {
s->SetAt(14, item28750);
if (static_cast<bool>(Unary("Not", s->LocalAt(14)))) {
continue;
}
if (static_cast<bool>(([&]() -> Value { auto v28751 = Get(s->LocalAt(14), Value(int64_t{0})); Value v28752; v28752 = Value("BUY_LAND"); if (!static_cast<bool>(Binary("Eq", v28751, v28752))) return Value(false); v28751 = v28752; return Value(true); }()))) {
return s->LocalAt(0);
}
if (static_cast<bool>(([&]() -> Value { auto v28753 = Get(s->LocalAt(14), Value(int64_t{0})); Value v28754; v28754 = Value("BUY_PRODUCT"); if (!static_cast<bool>(Binary("Eq", v28753, v28754))) return Value(false); v28753 = v28754; return Value(true); }()))) {
auto v28755 = s->LocalAt(9);
s->SetAt(9, Inplace("Add", v28755, ([&]() -> Value { auto fn28756 = s->Global("int"); Arguments args28757; args28757.Add(Get(s->LocalAt(14), Value(int64_t{2})), false); return Call(c, fn28756, std::move(args28757)); }())));
auto v28758 = s->LocalAt(1);
s->SetAt(1, Inplace("Add", v28758, ([&]() -> Value { auto v28759 = ([&]() -> Value { auto fn28760 = s->Global("int"); Arguments args28761; args28761.Add(Get(s->LocalAt(14), Value(int64_t{2})), false); return Call(c, fn28760, std::move(args28761)); }()); return Binary("Mult", v28759, ([&]() -> Value { auto v28762 = ([&]() -> Value { auto fn28763 = s->Global("int"); Arguments args28764; args28764.Add(Get(Get(Get(s->LocalAt(15), Value("market")), Value("prices")), Get(s->LocalAt(14), Value(int64_t{1}))), false); return Call(c, fn28763, std::move(args28764)); }()); return Binary("Add", v28762, Value(int64_t{10})); }())); }())));
}
else {
if (static_cast<bool>(([&]() -> Value { auto v28765 = Get(s->LocalAt(14), Value(int64_t{0})); Value v28766; v28766 = Value("BUY_ANIMAL"); if (!static_cast<bool>(Binary("Eq", v28765, v28766))) return Value(false); v28765 = v28766; return Value(true); }()))) {
auto v28767 = s->LocalAt(9);
s->SetAt(9, Inplace("Add", v28767, ([&]() -> Value { auto fn28768 = s->Global("int"); Arguments args28769; args28769.Add(Get(s->LocalAt(14), Value(int64_t{2})), false); return Call(c, fn28768, std::move(args28769)); }())));
auto v28770 = s->LocalAt(1);
s->SetAt(1, Inplace("Add", v28770, ([&]() -> Value { auto v28771 = ([&]() -> Value { auto fn28772 = s->Global("int"); Arguments args28773; args28773.Add(Get(s->LocalAt(14), Value(int64_t{2})), false); return Call(c, fn28772, std::move(args28773)); }()); return Binary("Mult", v28771, Get(([&]() -> Value { auto dict28774 = Dict(); auto key28775 = Value("SHEEP"); Put(dict28774, key28775, Value(int64_t{500})); auto key28776 = Value("COW"); Put(dict28774, key28776, Value(int64_t{400})); auto key28777 = Value("GOOSE"); Put(dict28774, key28777, Value(int64_t{300})); return dict28774; }()), Get(s->LocalAt(14), Value(int64_t{1})))); }())));
}
else {
if (static_cast<bool>(([&]() -> Value { auto v28778 = Get(s->LocalAt(14), Value(int64_t{0})); Value v28779; v28779 = Value("BUY_SEED"); if (!static_cast<bool>(Binary("Eq", v28778, v28779))) return Value(false); v28778 = v28779; return Value(true); }()))) {
auto v28780 = s->LocalAt(1);
s->SetAt(1, Inplace("Add", v28780, ([&]() -> Value { auto v28781 = ([&]() -> Value { auto fn28782 = s->Global("int"); Arguments args28783; args28783.Add(Get(s->LocalAt(14), Value(int64_t{2})), false); return Call(c, fn28782, std::move(args28783)); }()); return Binary("Mult", v28781, Get(([&]() -> Value { auto dict28784 = Dict(); auto key28785 = Value("WHEAT"); Put(dict28784, key28785, Value(int64_t{10})); auto key28786 = Value("CARROT"); Put(dict28784, key28786, Value(int64_t{20})); auto key28787 = Value("TOMATO"); Put(dict28784, key28787, Value(int64_t{50})); auto key28788 = Value("STRAWBERRY"); Put(dict28784, key28788, Value(int64_t{100})); auto key28789 = Value("MELON"); Put(dict28784, key28789, Value(int64_t{80})); return dict28784; }()), Get(s->LocalAt(14), Value(int64_t{1})))); }())));
}
}
}
}
if (static_cast<bool>(([&]() -> Value { auto v28790 = ([&]() -> Value { auto v28792 = ([&]() -> Value { auto fn28793 = s->Global("sum"); Arguments args28794; args28794.Add(([&]() -> Value { auto fn28795 = Attribute(s->LocalAt(21), "values"); Arguments args28796; return Call(c, fn28795, std::move(args28796)); }()), false); return Call(c, fn28793, std::move(args28794)); }()); return Binary("Add", v28792, s->LocalAt(9)); }()); Value v28791; v28791 = Value(int64_t{100}); if (!static_cast<bool>(Binary("Gt", v28790, v28791))) return Value(false); v28790 = v28791; return Value(true); }()))) {
auto v28797 = s->Global("_V233_REPORT");
auto v28798 = Value("sheep_capacity_declines");
auto v28799 = Get(v28797, v28798);
Put(v28797, v28798, Inplace("Add", v28799, Value(int64_t{1})));
return s->LocalAt(0);
}
if (static_cast<bool>(([&]() -> Value { auto v28800 = Get(s->LocalAt(7), Value("money")); Value v28801; v28801 = ([&]() -> Value { auto v28802 = s->LocalAt(1); return Binary("Add", v28802, (static_cast<bool>(s->LocalAt(10)) ? Value(int64_t{3000}) : Value(int64_t{1000}))); }()); if (!static_cast<bool>(Binary("Lt", v28800, v28801))) return Value(false); v28800 = v28801; return Value(true); }()))) {
auto v28803 = s->Global("_V233_REPORT");
auto v28804 = Value("sheep_budget_declines");
auto v28805 = Get(v28803, v28804);
Put(v28803, v28804, Inplace("Add", v28805, Value(int64_t{1})));
return s->LocalAt(0);
}
auto v28806 = s->LocalAt(3);
Put(s->LocalAt(19), Value("requested_day"), v28806);
auto v28807 = ([&]() -> Value { auto dict28808 = Dict(); auto key28809 = Value("first"); Put(dict28808, key28809, ([&]() -> Value { auto v28810 = s->LocalAt(5); return Binary("Add", v28810, Value(int64_t{1})); }())); auto key28811 = Value("initial"); Put(dict28808, key28811, s->LocalAt(10)); return dict28808; }());
Put(s->LocalAt(19), Value("pending"), v28807);
auto v28812 = s->Global("_V233_REPORT");
auto v28813 = Value("sheep_hire_requests");
auto v28814 = Get(v28812, v28813);
Put(v28812, v28813, Inplace("Add", v28814, Value(int64_t{2})));
auto v28815 = s->Global("_V233_REPORT");
auto v28816 = Value("sheep_feed_buy_requests");
auto v28817 = Get(v28815, v28816);
Put(v28815, v28816, Inplace("Add", v28817, Value(int64_t{6})));
if (static_cast<bool>(s->LocalAt(10))) {
auto v28818 = s->Global("_V233_REPORT");
auto v28819 = Value("sheep_commit_requests");
auto v28820 = Get(v28818, v28819);
Put(v28818, v28819, Inplace("Add", v28820, Value(int64_t{1})));
}
auto v28821 = ([&]() -> Value { auto fn28822 = Attribute(s->Global("copy"), "deepcopy"); Arguments args28823; args28823.Add(s->LocalAt(0), false); return Call(c, fn28822, std::move(args28823)); }());
s->SetAt(18, v28821);
auto v28824 = ([&]() -> Value { auto v28825 = s->LocalAt(12); return Binary("Add", v28825, s->LocalAt(6)); }());
Put(s->LocalAt(18), Value("market"), v28824);
return s->LocalAt(18);
return {};
}
}  // namespace kagg::opponents::compiled
