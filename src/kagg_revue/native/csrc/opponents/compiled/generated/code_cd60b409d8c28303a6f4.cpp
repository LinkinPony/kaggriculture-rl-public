// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_cd60b409d8c28303a6f4(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "budget", "day", "expected", "extra", "farm", "hour", "incoming", "initial", "market", "native", "o", "obs", "parent_hires", "planned", "result", "state", "step", "stock"};
s->PrepareSlots(s_names);
auto v14608 = ([&]() -> Value { auto fn14609 = s->Global("int"); Arguments args14610; args14610.Add(Get(s->LocalAt(12), Value("step")), false); return Call(c, fn14609, std::move(args14610)); }());
s->SetAt(17, v14608);
auto v14611 = ([&]() -> Value { auto v14612 = s->LocalAt(17); return Binary("FloorDiv", v14612, Value(int64_t{24})); }());
s->SetAt(2, v14611);
auto v14613 = ([&]() -> Value { auto v14614 = s->LocalAt(17); return Binary("Mod", v14614, Value(int64_t{24})); }());
s->SetAt(6, v14613);
if (static_cast<bool>(([&]() -> Value { auto v14615 = ([&]() -> Value { auto v14616 = s->LocalAt(6); Value v14617; v14617 = (static_cast<bool>(([&]() -> Value { auto fn14618 = PrepareDictionaryGet(s->LocalAt(16)); Arguments args14619; args14619.Add(Value("committed"), false); return CallDictionaryGet(c, fn14618, std::move(args14619)); }())) ? Value(int64_t{2}) : Value(int64_t{1})); if (!static_cast<bool>(Binary("Gt", v14616, v14617))) return Value(false); v14616 = v14617; return Value(true); }()); if (static_cast<bool>(v14615)) return v14615; v14615 = ([&]() -> Value { auto v14620 = ([&]() -> Value { auto fn14622 = PrepareDictionaryGet(s->LocalAt(16)); Arguments args14623; args14623.Add(Value("requested_day"), false); return CallDictionaryGet(c, fn14622, std::move(args14623)); }()); Value v14621; v14621 = s->LocalAt(2); if (!static_cast<bool>(Binary("Eq", v14620, v14621))) return Value(false); v14620 = v14621; return Value(true); }()); return v14615; }()))) {
return s->LocalAt(0);
}
if (static_cast<bool>(([&]() -> Value { auto v14624 = Unary("Not", ([&]() -> Value { auto fn14625 = PrepareDictionaryGet(s->LocalAt(16)); Arguments args14626; args14626.Add(Value("committed"), false); return CallDictionaryGet(c, fn14625, std::move(args14626)); }())); if (!static_cast<bool>(v14624)) return v14624; v14624 = ([&]() -> Value { auto v14627 = ([&]() -> Value { auto v14628 = s->LocalAt(2); Value v14629; v14629 = Value(int64_t{12}); if (!static_cast<bool>(Binary("NotEq", v14628, v14629))) return Value(false); v14628 = v14629; return Value(true); }()); if (static_cast<bool>(v14627)) return v14627; v14627 = Unary("Not", ([&]() -> Value { auto fn14630 = s->Global("_v233_eligible"); Arguments args14631; args14631.positional.reserve(2); args14631.Add(s->LocalAt(12), false); args14631.Add(s->LocalAt(10), false); return Call(c, fn14630, std::move(args14631)); }())); return v14627; }()); return v14624; }()))) {
return s->LocalAt(0);
}
auto v14632 = ([&]() -> Value { auto fn14633 = s->Global("_v219_native_day"); Arguments args14634; args14634.positional.reserve(2); args14634.Add(s->LocalAt(10), false); args14634.Add(s->LocalAt(2), false); return Call(c, fn14633, std::move(args14634)); }());
s->SetAt(14, v14632);
if (static_cast<bool>(([&]() -> Value { auto comp14635 = std::make_shared<Scope>(); comp14635->globals = s->globals; comp14635->parent = s; static constexpr const char* comp14635_names[] = {"a", "o"}; comp14635->PrepareSlots(comp14635_names); auto result14636 = List(); for (const auto& item14637 : Iterate(Slice(s->LocalAt(14), ([&]() -> Value { auto v14638 = s->LocalAt(6); return Binary("Add", v14638, Value(int64_t{1})); }()), Value{}, Value{}))) { comp14635->SetAt(0, item14637); for (const auto& item14639 : Iterate(([&]() -> Value { auto fn14640 = PrepareDictionaryGet(comp14635->LocalAt(0)); Arguments args14641; args14641.positional.reserve(2); args14641.Add(Value("market"), false); args14641.Add(List({}), false); return CallDictionaryGet(c, fn14640, std::move(args14641)); }()))) { comp14635->SetAt(1, item14639); if (static_cast<bool>(([&]() -> Value { auto v14642 = comp14635->LocalAt(1); if (!static_cast<bool>(v14642)) return v14642; v14642 = ([&]() -> Value { auto v14643 = Get(comp14635->LocalAt(1), Value(int64_t{0})); Value v14644; v14644 = Value("HIRE"); if (!static_cast<bool>(Binary("Eq", v14643, v14644))) return Value(false); v14643 = v14644; return Value(true); }()); return v14642; }()))) return Value(true); } } return Value(false); }()))) {
return s->LocalAt(0);
}
auto v14645 = Get(Get(s->LocalAt(12), Value("farms")), Get(s->LocalAt(12), Value("player")));
s->SetAt(5, v14645);
auto v14646 = ([&]() -> Value { auto fn14647 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args14648; args14648.positional.reserve(2); args14648.Add(Value("market"), false); args14648.Add(List({}), false); return CallDictionaryGet(c, fn14647, std::move(args14648)); }());
s->SetAt(9, v14646);
auto v14649 = ([&]() -> Value { auto fn14650 = s->Global("sum"); Arguments args14651; args14651.Add(([&]() -> Value { auto comp14652 = std::make_shared<Scope>(); comp14652->globals = s->globals; comp14652->parent = s; static constexpr const char* comp14652_names[] = {"o"}; comp14652->PrepareSlots(comp14652_names); auto result14653 = List(); for (const auto& item14654 : Iterate(s->LocalAt(9))) { comp14652->SetAt(0, item14654); result14653.node()->sequence.push_back(([&]() -> Value { auto v14655 = ([&]() -> Value { auto fn14656 = comp14652->Global("bool"); Arguments args14657; args14657.Add(comp14652->LocalAt(0), false); return Call(c, fn14656, std::move(args14657)); }()); if (!static_cast<bool>(v14655)) return v14655; v14655 = ([&]() -> Value { auto v14658 = Get(comp14652->LocalAt(0), Value(int64_t{0})); Value v14659; v14659 = Value("HIRE"); if (!static_cast<bool>(Binary("Eq", v14658, v14659))) return Value(false); v14658 = v14659; return Value(true); }()); return v14655; }())); } return result14653; }()), false); return Call(c, fn14650, std::move(args14651)); }());
s->SetAt(13, v14649);
auto v14660 = ([&]() -> Value { auto fn14661 = s->Global("max"); Arguments args14662; args14662.Add(([&]() -> Value { auto comp14663 = std::make_shared<Scope>(); comp14663->globals = s->globals; comp14663->parent = s; static constexpr const char* comp14663_names[] = {"a"}; comp14663->PrepareSlots(comp14663_names); auto result14664 = List(); for (const auto& item14665 : Iterate(s->LocalAt(14))) { comp14663->SetAt(0, item14665); result14664.node()->sequence.push_back(([&]() -> Value { auto fn14666 = comp14663->Global("len"); Arguments args14667; args14667.Add(([&]() -> Value { auto fn14668 = PrepareDictionaryGet(comp14663->LocalAt(0)); Arguments args14669; args14669.positional.reserve(2); args14669.Add(Value("hands"), false); args14669.Add(List({}), false); return CallDictionaryGet(c, fn14668, std::move(args14669)); }()), false); return Call(c, fn14666, std::move(args14667)); }())); } return result14664; }()), false); return Call(c, fn14661, std::move(args14662)); }());
s->SetAt(3, v14660);
if (static_cast<bool>(([&]() -> Value { auto v14670 = ([&]() -> Value { auto v14672 = ([&]() -> Value { auto fn14673 = s->Global("len"); Arguments args14674; args14674.Add(Get(s->LocalAt(5), Value("hands")), false); return Call(c, fn14673, std::move(args14674)); }()); return Binary("Add", v14672, s->LocalAt(13)); }()); Value v14671; v14671 = s->LocalAt(3); if (!static_cast<bool>(Binary("NotEq", v14670, v14671))) return Value(false); v14670 = v14671; return Value(true); }()))) {
return s->LocalAt(0);
}
auto v14675 = Unary("Not", ([&]() -> Value { auto fn14676 = PrepareDictionaryGet(s->LocalAt(16)); Arguments args14677; args14677.Add(Value("committed"), false); return CallDictionaryGet(c, fn14676, std::move(args14677)); }()));
s->SetAt(8, v14675);
auto v14678 = ([&]() -> Value { auto v14679 = (static_cast<bool>(s->LocalAt(8)) ? List({List({Value("BUY_LAND")}), List({Value("BUY_ANIMAL"), Value("SHEEP"), Value(int64_t{6})})}) : List({})); return Binary("Add", v14679, List({List({Value("BUY_PRODUCT"), Value("WHEAT"), Value(int64_t{6})}), List({Value("HIRE")}), List({Value("HIRE")})})); }());
s->SetAt(4, v14678);
if (static_cast<bool>(([&]() -> Value { auto v14680 = ([&]() -> Value { auto v14682 = ([&]() -> Value { auto fn14683 = s->Global("len"); Arguments args14684; args14684.Add(s->LocalAt(9), false); return Call(c, fn14683, std::move(args14684)); }()); return Binary("Add", v14682, ([&]() -> Value { auto fn14685 = s->Global("len"); Arguments args14686; args14686.Add(s->LocalAt(4), false); return Call(c, fn14685, std::move(args14686)); }())); }()); Value v14681; v14681 = s->Global("MAX_ORDERS"); if (!static_cast<bool>(Binary("Gt", v14680, v14681))) return Value(false); v14680 = v14681; return Value(true); }()))) {
return s->LocalAt(0);
}
auto v14687 = ([&]() -> Value { auto fn14688 = s->Global("projected_shed"); Arguments args14689; args14689.positional.reserve(2); args14689.Add(s->LocalAt(0), false); args14689.Add(([&]() -> Value { auto fn14690 = s->Global("FarmView"); Arguments args14691; args14691.Add(s->LocalAt(12), false); return Call(c, fn14690, std::move(args14691)); }()), false); return Call(c, fn14688, std::move(args14689)); }());
s->SetAt(18, v14687);
auto v14692 = ([&]() -> Value { auto v14693 = Value(int64_t{6}); return Binary("Add", v14693, ([&]() -> Value { auto v14694 = Value(int64_t{6}); return Binary("Mult", v14694, s->LocalAt(8)); }())); }());
s->SetAt(7, v14692);
auto v14695 = ([&]() -> Value { auto v14696 = ([&]() -> Value { auto v14697 = Value(int64_t{7000}); return Binary("Mult", v14697, s->LocalAt(8)); }()); return Binary("Add", v14696, ([&]() -> Value { auto v14698 = Value(int64_t{6}); return Binary("Mult", v14698, ([&]() -> Value { auto v14699 = ([&]() -> Value { auto fn14700 = s->Global("int"); Arguments args14701; args14701.Add(Get(Get(Get(s->LocalAt(12), Value("market")), Value("prices")), Value("WHEAT")), false); return Call(c, fn14700, std::move(args14701)); }()); return Binary("Add", v14699, Value(int64_t{10})); }())); }())); }());
s->SetAt(1, v14695);
auto v14702 = s->LocalAt(1);
s->SetAt(1, Inplace("Add", v14702, ([&]() -> Value { auto fn14703 = s->Global("sum"); Arguments args14704; args14704.Add(([&]() -> Value { auto comp14705 = std::make_shared<Scope>(); comp14705->globals = s->globals; comp14705->parent = s; static constexpr const char* comp14705_names[] = {"n"}; comp14705->PrepareSlots(comp14705_names); auto result14706 = List(); for (const auto& item14707 : Iterate(([&]() -> Value { auto fn14708 = s->Global("range"); Arguments args14709; args14709.positional.reserve(2); args14709.Add(Get(s->LocalAt(5), Value("hires_today")), false); args14709.Add(([&]() -> Value { auto v14710 = ([&]() -> Value { auto v14711 = Get(s->LocalAt(5), Value("hires_today")); return Binary("Add", v14711, s->LocalAt(13)); }()); return Binary("Add", v14710, Value(int64_t{2})); }()), false); return Call(c, fn14708, std::move(args14709)); }()))) { comp14705->SetAt(0, item14707); result14706.node()->sequence.push_back(([&]() -> Value { auto fn14712 = comp14705->Global("_v219_fib"); Arguments args14713; args14713.Add(comp14705->LocalAt(0), false); return Call(c, fn14712, std::move(args14713)); }())); } return result14706; }()), false); return Call(c, fn14703, std::move(args14704)); }())));
for (const auto& item14714 : Iterate(s->LocalAt(9))) {
s->SetAt(11, item14714);
if (static_cast<bool>(Unary("Not", s->LocalAt(11)))) {
continue;
}
if (static_cast<bool>(([&]() -> Value { auto v14715 = Get(s->LocalAt(11), Value(int64_t{0})); Value v14716; v14716 = Value("BUY_LAND"); if (!static_cast<bool>(Binary("Eq", v14715, v14716))) return Value(false); v14715 = v14716; return Value(true); }()))) {
return s->LocalAt(0);
}
if (static_cast<bool>(([&]() -> Value { auto v14717 = Get(s->LocalAt(11), Value(int64_t{0})); Value v14718; v14718 = Value("BUY_PRODUCT"); if (!static_cast<bool>(Binary("Eq", v14717, v14718))) return Value(false); v14717 = v14718; return Value(true); }()))) {
auto v14719 = s->LocalAt(7);
s->SetAt(7, Inplace("Add", v14719, ([&]() -> Value { auto fn14720 = s->Global("int"); Arguments args14721; args14721.Add(Get(s->LocalAt(11), Value(int64_t{2})), false); return Call(c, fn14720, std::move(args14721)); }())));
auto v14722 = s->LocalAt(1);
s->SetAt(1, Inplace("Add", v14722, ([&]() -> Value { auto v14723 = ([&]() -> Value { auto fn14724 = s->Global("int"); Arguments args14725; args14725.Add(Get(s->LocalAt(11), Value(int64_t{2})), false); return Call(c, fn14724, std::move(args14725)); }()); return Binary("Mult", v14723, ([&]() -> Value { auto v14726 = ([&]() -> Value { auto fn14727 = s->Global("int"); Arguments args14728; args14728.Add(Get(Get(Get(s->LocalAt(12), Value("market")), Value("prices")), Get(s->LocalAt(11), Value(int64_t{1}))), false); return Call(c, fn14727, std::move(args14728)); }()); return Binary("Add", v14726, Value(int64_t{10})); }())); }())));
}
else {
if (static_cast<bool>(([&]() -> Value { auto v14729 = Get(s->LocalAt(11), Value(int64_t{0})); Value v14730; v14730 = Value("BUY_ANIMAL"); if (!static_cast<bool>(Binary("Eq", v14729, v14730))) return Value(false); v14729 = v14730; return Value(true); }()))) {
auto v14731 = s->LocalAt(7);
s->SetAt(7, Inplace("Add", v14731, ([&]() -> Value { auto fn14732 = s->Global("int"); Arguments args14733; args14733.Add(Get(s->LocalAt(11), Value(int64_t{2})), false); return Call(c, fn14732, std::move(args14733)); }())));
auto v14734 = s->LocalAt(1);
s->SetAt(1, Inplace("Add", v14734, ([&]() -> Value { auto v14735 = ([&]() -> Value { auto fn14736 = s->Global("int"); Arguments args14737; args14737.Add(Get(s->LocalAt(11), Value(int64_t{2})), false); return Call(c, fn14736, std::move(args14737)); }()); return Binary("Mult", v14735, Get(([&]() -> Value { auto dict14738 = Dict(); auto key14739 = Value("SHEEP"); Put(dict14738, key14739, Value(int64_t{500})); auto key14740 = Value("COW"); Put(dict14738, key14740, Value(int64_t{400})); auto key14741 = Value("GOOSE"); Put(dict14738, key14741, Value(int64_t{300})); return dict14738; }()), Get(s->LocalAt(11), Value(int64_t{1})))); }())));
}
else {
if (static_cast<bool>(([&]() -> Value { auto v14742 = Get(s->LocalAt(11), Value(int64_t{0})); Value v14743; v14743 = Value("BUY_SEED"); if (!static_cast<bool>(Binary("Eq", v14742, v14743))) return Value(false); v14742 = v14743; return Value(true); }()))) {
auto v14744 = s->LocalAt(1);
s->SetAt(1, Inplace("Add", v14744, ([&]() -> Value { auto v14745 = ([&]() -> Value { auto fn14746 = s->Global("int"); Arguments args14747; args14747.Add(Get(s->LocalAt(11), Value(int64_t{2})), false); return Call(c, fn14746, std::move(args14747)); }()); return Binary("Mult", v14745, Get(([&]() -> Value { auto dict14748 = Dict(); auto key14749 = Value("WHEAT"); Put(dict14748, key14749, Value(int64_t{10})); auto key14750 = Value("CARROT"); Put(dict14748, key14750, Value(int64_t{20})); auto key14751 = Value("TOMATO"); Put(dict14748, key14751, Value(int64_t{50})); auto key14752 = Value("STRAWBERRY"); Put(dict14748, key14752, Value(int64_t{100})); auto key14753 = Value("MELON"); Put(dict14748, key14753, Value(int64_t{80})); return dict14748; }()), Get(s->LocalAt(11), Value(int64_t{1})))); }())));
}
}
}
}
if (static_cast<bool>(([&]() -> Value { auto v14754 = ([&]() -> Value { auto v14756 = ([&]() -> Value { auto fn14757 = s->Global("sum"); Arguments args14758; args14758.Add(([&]() -> Value { auto fn14759 = Attribute(s->LocalAt(18), "values"); Arguments args14760; return Call(c, fn14759, std::move(args14760)); }()), false); return Call(c, fn14757, std::move(args14758)); }()); return Binary("Add", v14756, s->LocalAt(7)); }()); Value v14755; v14755 = Value(int64_t{100}); if (!static_cast<bool>(Binary("Gt", v14754, v14755))) return Value(false); v14754 = v14755; return Value(true); }()))) {
auto v14761 = s->Global("_V233_REPORT");
auto v14762 = Value("sheep_capacity_declines");
auto v14763 = Get(v14761, v14762);
Put(v14761, v14762, Inplace("Add", v14763, Value(int64_t{1})));
return s->LocalAt(0);
}
if (static_cast<bool>(([&]() -> Value { auto v14764 = Get(s->LocalAt(5), Value("money")); Value v14765; v14765 = ([&]() -> Value { auto v14766 = s->LocalAt(1); return Binary("Add", v14766, (static_cast<bool>(s->LocalAt(8)) ? Value(int64_t{3000}) : Value(int64_t{1000}))); }()); if (!static_cast<bool>(Binary("Lt", v14764, v14765))) return Value(false); v14764 = v14765; return Value(true); }()))) {
auto v14767 = s->Global("_V233_REPORT");
auto v14768 = Value("sheep_budget_declines");
auto v14769 = Get(v14767, v14768);
Put(v14767, v14768, Inplace("Add", v14769, Value(int64_t{1})));
return s->LocalAt(0);
}
auto v14770 = s->LocalAt(2);
Put(s->LocalAt(16), Value("requested_day"), v14770);
auto v14771 = ([&]() -> Value { auto dict14772 = Dict(); auto key14773 = Value("first"); Put(dict14772, key14773, ([&]() -> Value { auto v14774 = s->LocalAt(3); return Binary("Add", v14774, Value(int64_t{1})); }())); auto key14775 = Value("initial"); Put(dict14772, key14775, s->LocalAt(8)); return dict14772; }());
Put(s->LocalAt(16), Value("pending"), v14771);
auto v14776 = s->Global("_V233_REPORT");
auto v14777 = Value("sheep_hire_requests");
auto v14778 = Get(v14776, v14777);
Put(v14776, v14777, Inplace("Add", v14778, Value(int64_t{2})));
auto v14779 = s->Global("_V233_REPORT");
auto v14780 = Value("sheep_feed_buy_requests");
auto v14781 = Get(v14779, v14780);
Put(v14779, v14780, Inplace("Add", v14781, Value(int64_t{6})));
if (static_cast<bool>(s->LocalAt(8))) {
auto v14782 = s->Global("_V233_REPORT");
auto v14783 = Value("sheep_commit_requests");
auto v14784 = Get(v14782, v14783);
Put(v14782, v14783, Inplace("Add", v14784, Value(int64_t{1})));
}
auto v14785 = ([&]() -> Value { auto fn14786 = Attribute(s->Global("copy"), "deepcopy"); Arguments args14787; args14787.Add(s->LocalAt(0), false); return Call(c, fn14786, std::move(args14787)); }());
s->SetAt(15, v14785);
auto v14788 = ([&]() -> Value { auto v14789 = s->LocalAt(9); return Binary("Add", v14789, s->LocalAt(4)); }());
Put(s->LocalAt(15), Value("market"), v14788);
return s->LocalAt(15);
return {};
}
}  // namespace kagg::opponents::compiled
