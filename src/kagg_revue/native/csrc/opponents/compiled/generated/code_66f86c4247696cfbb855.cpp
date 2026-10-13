// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_66f86c4247696cfbb855(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"actor", "command", "day", "desired", "distance", "home", "inv", "obs", "pos", "previous", "role", "state", "step", "target", "targets", "tile", "todo", "tomato", "view", "walk", "x", "y"};
s->PrepareSlots(s_names);
auto v4700 = ([&]() -> Value { auto v4701 = ([&]() -> Value { auto fn4702 = s->Global("int"); Arguments args4703; args4703.Add(Get(s->LocalAt(7), Value("step")), false); return Call(c, fn4702, std::move(args4703)); }()); return Binary("FloorDiv", v4701, Value(int64_t{24})); }());
s->SetAt(2, v4700);
auto v4704 = ([&]() -> Value { auto fn4705 = s->Global("int"); Arguments args4706; args4706.Add(Get(s->LocalAt(7), Value("step")), false); return Call(c, fn4705, std::move(args4706)); }());
s->SetAt(12, v4704);
auto v4707 = ([&]() -> Value { auto fn4708 = s->Global("FarmView"); Arguments args4709; args4709.Add(s->LocalAt(7), false); return Call(c, fn4708, std::move(args4709)); }());
s->SetAt(18, v4707);
auto v4710 = ([&]() -> Value { auto fn4711 = s->Global("tuple"); Arguments args4712; args4712.Add(Get(Attribute(s->LocalAt(18), "positions"), s->LocalAt(0)), false); return Call(c, fn4711, std::move(args4712)); }());
s->SetAt(8, v4710);
auto v4713 = ([&]() -> Value { auto fn4714 = Attribute(s->LocalAt(18), "inventory"); Arguments args4715; args4715.Add(s->LocalAt(0), false); return Call(c, fn4714, std::move(args4715)); }());
s->SetAt(6, v4713);
auto v4716 = Get(s->LocalAt(10), Value("targets"));
s->SetAt(14, v4716);
auto v4717 = ([&]() -> Value { auto fn4718 = PrepareDictionaryGet(Get(s->LocalAt(11), Value("last_work"))); Arguments args4719; args4719.Add(s->LocalAt(0), false); return CallDictionaryGet(c, fn4718, std::move(args4719)); }());
s->SetAt(9, v4717);
if (static_cast<bool>(([&]() -> Value { auto v4720 = s->LocalAt(9); if (!static_cast<bool>(v4720)) return v4720; v4720 = ([&]() -> Value { auto v4721 = Get(s->LocalAt(9), Value("step")); Value v4722; v4722 = ([&]() -> Value { auto v4723 = s->LocalAt(12); return Binary("Sub", v4723, Value(int64_t{1})); }()); if (!static_cast<bool>(Binary("Eq", v4721, v4722))) return Value(false); v4721 = v4722; return Value(true); }()); if (!static_cast<bool>(v4720)) return v4720; v4720 = ([&]() -> Value { auto v4724 = Get(s->LocalAt(9), Value("command")); Value v4725; v4725 = List({Value("HARVEST")}); if (!static_cast<bool>(Binary("Eq", v4724, v4725))) return Value(false); v4724 = v4725; return Value(true); }()); return v4720; }()))) {
auto v4726 = s->Global("_V219_REPORT");
auto v4727 = Value("confirmed_harvest_units");
auto v4728 = Get(v4726, v4727);
Put(v4726, v4727, Inplace("Add", v4728, ([&]() -> Value { auto fn4729 = s->Global("max"); Arguments args4730; args4730.positional.reserve(2); args4730.Add(Value(int64_t{0}), false); args4730.Add(([&]() -> Value { auto v4731 = ([&]() -> Value { auto fn4732 = s->Global("int"); Arguments args4733; args4733.Add(([&]() -> Value { auto fn4734 = PrepareDictionaryGet(s->LocalAt(6)); Arguments args4735; args4735.positional.reserve(2); args4735.Add(Value("TOMATO"), false); args4735.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn4734, std::move(args4735)); }()), false); return Call(c, fn4732, std::move(args4733)); }()); return Binary("Sub", v4731, Get(s->LocalAt(9), Value("tomatoes"))); }()), false); return Call(c, fn4729, std::move(args4730)); }())));
}
if (static_cast<bool>(([&]() -> Value { auto v4736 = ([&]() -> Value { auto fn4737 = PrepareDictionaryGet(s->LocalAt(10)); Arguments args4738; args4738.Add(Value("needs_fertilizer"), false); return CallDictionaryGet(c, fn4737, std::move(args4738)); }()); if (!static_cast<bool>(v4736)) return v4736; v4736 = Unary("Not", ([&]() -> Value { auto fn4739 = PrepareDictionaryGet(s->LocalAt(10)); Arguments args4740; args4740.Add(Value("loaded"), false); return CallDictionaryGet(c, fn4739, std::move(args4740)); }())); return v4736; }()))) {
auto v4741 = ([&]() -> Value { auto fn4742 = s->Global("_v219_home"); Arguments args4743; args4743.Add(s->LocalAt(8), false); return Call(c, fn4742, std::move(args4743)); }());
s->SetAt(5, v4741);
auto v4744 = ([&]() -> Value { auto fn4745 = s->Global("_v219_walk"); Arguments args4746; args4746.positional.reserve(2); args4746.Add(s->LocalAt(8), false); args4746.Add(s->LocalAt(5), false); return Call(c, fn4745, std::move(args4746)); }());
s->SetAt(19, v4744);
if (static_cast<bool>(s->LocalAt(19))) {
return s->LocalAt(19);
}
auto v4747 = ([&]() -> Value { auto fn4748 = PrepareDictionaryGet(s->LocalAt(10)); Arguments args4749; args4749.positional.reserve(2); args4749.Add(Value("fertilizer_quantity"), false); args4749.Add((static_cast<bool>(([&]() -> Value { auto v4750 = Get(s->LocalAt(10), Value("kind")); Value v4751; v4751 = Value("fertilizer"); if (!static_cast<bool>(Binary("Eq", v4750, v4751))) return Value(false); v4750 = v4751; return Value(true); }())) ? Value(int64_t{10}) : Value(int64_t{5})), false); return CallDictionaryGet(c, fn4748, std::move(args4749)); }());
s->SetAt(3, v4747);
if (static_cast<bool>(([&]() -> Value { auto v4752 = ([&]() -> Value { auto fn4754 = PrepareDictionaryGet(s->LocalAt(6)); Arguments args4755; args4755.positional.reserve(2); args4755.Add(Value("FERTILIZER"), false); args4755.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn4754, std::move(args4755)); }()); Value v4753; v4753 = s->LocalAt(3); if (!static_cast<bool>(Binary("GtE", v4752, v4753))) return Value(false); v4752 = v4753; return Value(true); }()))) {
auto v4756 = Value(true);
Put(s->LocalAt(10), Value("loaded"), v4756);
}
else {
if (static_cast<bool>(([&]() -> Value { auto fn4757 = PrepareDictionaryGet(s->LocalAt(10)); Arguments args4758; args4758.Add(Value("pickup_requested"), false); return CallDictionaryGet(c, fn4757, std::move(args4758)); }()))) {
auto v4759 = Value(true);
Put(s->LocalAt(10), Value("loaded"), v4759);
auto v4760 = ([&]() -> Value { auto fn4761 = s->Global("int"); Arguments args4762; args4762.Add(([&]() -> Value { auto fn4763 = PrepareDictionaryGet(s->LocalAt(6)); Arguments args4764; args4764.positional.reserve(2); args4764.Add(Value("FERTILIZER"), false); args4764.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn4763, std::move(args4764)); }()), false); return Call(c, fn4761, std::move(args4762)); }());
Put(s->LocalAt(10), Value("fertilizer_available"), v4760);
}
else {
if (static_cast<bool>(([&]() -> Value { auto v4765 = ([&]() -> Value { auto fn4767 = PrepareDictionaryGet(Attribute(s->LocalAt(18), "shed")); Arguments args4768; args4768.positional.reserve(2); args4768.Add(Value("FERTILIZER"), false); args4768.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn4767, std::move(args4768)); }()); Value v4766; v4766 = s->LocalAt(3); if (!static_cast<bool>(Binary("GtE", v4765, v4766))) return Value(false); v4765 = v4766; return Value(true); }()))) {
auto v4769 = Value(true);
Put(s->LocalAt(10), Value("pickup_requested"), v4769);
return List({Value("PICKUP"), Value("FERTILIZER"), s->LocalAt(3)});
}
else {
auto v4770 = Value(true);
Put(s->LocalAt(10), Value("loaded"), v4770);
}
}
}
}
auto v4771 = List({});
s->SetAt(16, v4771);
for (const auto& item4772 : Iterate(s->LocalAt(14))) {
s->SetAt(13, item4772);
auto v4773 = s->LocalAt(13);
auto unpack4774 = Iterate(v4773);
ValidateUnpack(unpack4774, 2, false);
s->SetAt(20, unpack4774.at(0));
s->SetAt(21, unpack4774.at(1));
auto v4775 = Get(Get(Attribute(s->LocalAt(18), "tiles"), s->LocalAt(21)), s->LocalAt(20));
s->SetAt(15, v4775);
auto v4776 = ([&]() -> Value { auto v4777 = ([&]() -> Value { auto fn4778 = s->Global("isinstance"); Arguments args4779; args4779.positional.reserve(2); args4779.Add(s->LocalAt(15), false); args4779.Add(s->Global("dict"), false); return Call(c, fn4778, std::move(args4779)); }()); if (!static_cast<bool>(v4777)) return v4777; v4777 = ([&]() -> Value { auto v4780 = ([&]() -> Value { auto fn4782 = PrepareDictionaryGet(s->LocalAt(15)); Arguments args4783; args4783.Add(Value("crop"), false); return CallDictionaryGet(c, fn4782, std::move(args4783)); }()); Value v4781; v4781 = Value("TOMATO"); if (!static_cast<bool>(Binary("Eq", v4780, v4781))) return Value(false); v4780 = v4781; return Value(true); }()); return v4777; }());
s->SetAt(17, v4776);
if (static_cast<bool>(([&]() -> Value { auto v4784 = s->LocalAt(17); if (!static_cast<bool>(v4784)) return v4784; v4784 = ([&]() -> Value { auto v4785 = s->LocalAt(13); Value v4786; v4786 = Get(s->LocalAt(11), Value("seen_plants")); if (!static_cast<bool>(Binary("NotIn", v4785, v4786))) return Value(false); v4785 = v4786; return Value(true); }()); return v4784; }()))) {
(void)([&]() -> Value { auto fn4787 = Attribute(Get(s->LocalAt(11), Value("seen_plants")), "add"); Arguments args4788; args4788.Add(s->LocalAt(13), false); return Call(c, fn4787, std::move(args4788)); }());
auto v4789 = s->Global("_V219_REPORT");
auto v4790 = Value("confirmed_plants");
auto v4791 = Get(v4789, v4790);
Put(v4789, v4790, Inplace("Add", v4791, Value(int64_t{1})));
}
if (static_cast<bool>(([&]() -> Value { auto v4792 = ([&]() -> Value { auto v4793 = s->LocalAt(13); Value v4794; v4794 = Get(s->LocalAt(11), Value("seen_plants")); if (!static_cast<bool>(Binary("In", v4793, v4794))) return Value(false); v4793 = v4794; return Value(true); }()); if (!static_cast<bool>(v4792)) return v4792; v4792 = Unary("Not", s->LocalAt(17)); if (!static_cast<bool>(v4792)) return v4792; v4792 = ([&]() -> Value { auto v4795 = s->LocalAt(13); Value v4796; v4796 = Get(s->LocalAt(11), Value("lost")); if (!static_cast<bool>(Binary("NotIn", v4795, v4796))) return Value(false); v4795 = v4796; return Value(true); }()); return v4792; }()))) {
(void)([&]() -> Value { auto fn4797 = Attribute(Get(s->LocalAt(11), Value("lost")), "add"); Arguments args4798; args4798.Add(s->LocalAt(13), false); return Call(c, fn4797, std::move(args4798)); }());
auto v4799 = s->Global("_V219_REPORT");
auto v4800 = Value("lost_plants");
auto v4801 = Get(v4799, v4800);
Put(v4799, v4800, Inplace("Add", v4801, Value(int64_t{1})));
}
auto v4802 = Value{};
s->SetAt(1, v4802);
if (static_cast<bool>(([&]() -> Value { auto v4803 = Get(s->LocalAt(10), Value("kind")); Value v4804; v4804 = Value("fertilizer"); if (!static_cast<bool>(Binary("Eq", v4803, v4804))) return Value(false); v4803 = v4804; return Value(true); }()))) {
if (static_cast<bool>(([&]() -> Value { auto v4805 = s->LocalAt(17); if (!static_cast<bool>(v4805)) return v4805; v4805 = ([&]() -> Value { auto v4806 = ([&]() -> Value { auto fn4808 = PrepareDictionaryGet(s->LocalAt(15)); Arguments args4809; args4809.positional.reserve(2); args4809.Add(Value("fertilized_until_day"), false); args4809.Add(Unary("USub", Value(int64_t{1})), false); return CallDictionaryGet(c, fn4808, std::move(args4809)); }()); Value v4807; v4807 = ([&]() -> Value { auto v4810 = s->LocalAt(2); return Binary("Add", v4810, Value(int64_t{2})); }()); if (!static_cast<bool>(Binary("Lt", v4806, v4807))) return Value(false); v4806 = v4807; return Value(true); }()); if (!static_cast<bool>(v4805)) return v4805; v4805 = ([&]() -> Value { auto v4811 = ([&]() -> Value { auto fn4813 = PrepareDictionaryGet(s->LocalAt(6)); Arguments args4814; args4814.positional.reserve(2); args4814.Add(Value("FERTILIZER"), false); args4814.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn4813, std::move(args4814)); }()); Value v4812; v4812 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v4811, v4812))) return Value(false); v4811 = v4812; return Value(true); }()); return v4805; }()))) {
auto v4815 = List({Value("FERTILIZE")});
s->SetAt(1, v4815);
}
}
else {
if (static_cast<bool>(([&]() -> Value { auto v4816 = ([&]() -> Value { auto v4817 = s->LocalAt(2); Value v4818; v4818 = Value(int64_t{18}); if (!static_cast<bool>(Binary("Eq", v4817, v4818))) return Value(false); v4817 = v4818; return Value(true); }()); if (!static_cast<bool>(v4816)) return v4816; v4816 = Unary("Not", s->LocalAt(17)); return v4816; }()))) {
if (static_cast<bool>(([&]() -> Value { auto v4819 = ([&]() -> Value { auto v4820 = s->LocalAt(15); Value v4821; v4821 = Value{}; if (!static_cast<bool>(Binary("Is", v4820, v4821))) return Value(false); v4820 = v4821; return Value(true); }()); if (!static_cast<bool>(v4819)) return v4819; v4819 = ([&]() -> Value { auto v4822 = ([&]() -> Value { auto fn4824 = PrepareDictionaryGet(Get(Get(s->LocalAt(7), Value("private")), Value("seeds"))); Arguments args4825; args4825.positional.reserve(2); args4825.Add(Value("TOMATO"), false); args4825.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn4824, std::move(args4825)); }()); Value v4823; v4823 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v4822, v4823))) return Value(false); v4822 = v4823; return Value(true); }()); return v4819; }()))) {
auto v4826 = List({Value("PLANT"), Value("TOMATO")});
s->SetAt(1, v4826);
}
else {
if (static_cast<bool>(([&]() -> Value { auto v4827 = ([&]() -> Value { auto fn4828 = s->Global("isinstance"); Arguments args4829; args4829.positional.reserve(2); args4829.Add(s->LocalAt(15), false); args4829.Add(s->Global("dict"), false); return Call(c, fn4828, std::move(args4829)); }()); if (!static_cast<bool>(v4827)) return v4827; v4827 = ([&]() -> Value { auto v4830 = ([&]() -> Value { auto fn4832 = PrepareDictionaryGet(s->LocalAt(15)); Arguments args4833; args4833.Add(Value("kind"), false); return CallDictionaryGet(c, fn4832, std::move(args4833)); }()); Value v4831; v4831 = Value("WEED"); if (!static_cast<bool>(Binary("Eq", v4830, v4831))) return Value(false); v4830 = v4831; return Value(true); }()); return v4827; }()))) {
auto v4834 = List({Value("DIG")});
s->SetAt(1, v4834);
}
}
}
else {
if (static_cast<bool>(s->LocalAt(17))) {
if (static_cast<bool>(([&]() -> Value { auto v4835 = ([&]() -> Value { auto v4836 = s->LocalAt(2); Value v4837; v4837 = Value(int64_t{29}); if (!static_cast<bool>(Binary("Lt", v4836, v4837))) return Value(false); v4836 = v4837; return Value(true); }()); if (!static_cast<bool>(v4835)) return v4835; v4835 = Unary("Not", ([&]() -> Value { auto fn4838 = PrepareDictionaryGet(s->LocalAt(15)); Arguments args4839; args4839.Add(Value("watered_today"), false); return CallDictionaryGet(c, fn4838, std::move(args4839)); }())); return v4835; }()))) {
auto v4840 = List({Value("WATER")});
s->SetAt(1, v4840);
}
else {
if (static_cast<bool>(([&]() -> Value { auto v4841 = ([&]() -> Value { auto fn4842 = PrepareDictionaryGet(s->LocalAt(10)); Arguments args4843; args4843.Add(Value("needs_fertilizer"), false); return CallDictionaryGet(c, fn4842, std::move(args4843)); }()); if (!static_cast<bool>(v4841)) return v4841; v4841 = ([&]() -> Value { auto v4844 = ([&]() -> Value { auto fn4846 = PrepareDictionaryGet(s->LocalAt(15)); Arguments args4847; args4847.positional.reserve(2); args4847.Add(Value("fertilized_until_day"), false); args4847.Add(Unary("USub", Value(int64_t{1})), false); return CallDictionaryGet(c, fn4846, std::move(args4847)); }()); Value v4845; v4845 = ([&]() -> Value { auto v4848 = s->LocalAt(2); return Binary("Add", v4848, Value(int64_t{2})); }()); if (!static_cast<bool>(Binary("Lt", v4844, v4845))) return Value(false); v4844 = v4845; return Value(true); }()); if (!static_cast<bool>(v4841)) return v4841; v4841 = ([&]() -> Value { auto v4849 = ([&]() -> Value { auto fn4851 = PrepareDictionaryGet(s->LocalAt(6)); Arguments args4852; args4852.positional.reserve(2); args4852.Add(Value("FERTILIZER"), false); args4852.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn4851, std::move(args4852)); }()); Value v4850; v4850 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v4849, v4850))) return Value(false); v4849 = v4850; return Value(true); }()); return v4841; }()))) {
auto v4853 = List({Value("FERTILIZE")});
s->SetAt(1, v4853);
}
else {
if (static_cast<bool>(([&]() -> Value { auto v4854 = ([&]() -> Value { auto fn4856 = PrepareDictionaryGet(s->LocalAt(15)); Arguments args4857; args4857.positional.reserve(2); args4857.Add(Value("yield_units"), false); args4857.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn4856, std::move(args4857)); }()); Value v4855; v4855 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v4854, v4855))) return Value(false); v4854 = v4855; return Value(true); }()))) {
auto v4858 = List({Value("HARVEST")});
s->SetAt(1, v4858);
}
}
}
}
}
}
if (static_cast<bool>(s->LocalAt(1))) {
(void)([&]() -> Value { auto fn4859 = Attribute(s->LocalAt(16), "append"); Arguments args4860; args4860.Add(Tuple({s->LocalAt(13), s->LocalAt(1)}), false); return Call(c, fn4859, std::move(args4860)); }());
}
}
auto v4861 = ([&]() -> Value { auto fn4862 = s->Global("_v219_home"); Arguments args4863; args4863.Add(s->LocalAt(8), false); return Call(c, fn4862, std::move(args4863)); }());
s->SetAt(5, v4861);
auto v4864 = ([&]() -> Value { auto v4865 = ([&]() -> Value { auto fn4866 = s->Global("abs"); Arguments args4867; args4867.Add(([&]() -> Value { auto v4868 = Get(s->LocalAt(8), Value(int64_t{0})); return Binary("Sub", v4868, Get(s->LocalAt(5), Value(int64_t{0}))); }()), false); return Call(c, fn4866, std::move(args4867)); }()); return Binary("Add", v4865, ([&]() -> Value { auto fn4869 = s->Global("abs"); Arguments args4870; args4870.Add(([&]() -> Value { auto v4871 = Get(s->LocalAt(8), Value(int64_t{1})); return Binary("Sub", v4871, Get(s->LocalAt(5), Value(int64_t{1}))); }()), false); return Call(c, fn4869, std::move(args4870)); }())); }());
s->SetAt(4, v4864);
if (static_cast<bool>(([&]() -> Value { auto v4872 = ([&]() -> Value { auto v4873 = s->LocalAt(12); Value v4874; v4874 = ([&]() -> Value { auto v4875 = Value(int64_t{718}); return Binary("Sub", v4875, s->LocalAt(4)); }()); if (!static_cast<bool>(Binary("GtE", v4873, v4874))) return Value(false); v4873 = v4874; return Value(true); }()); if (!static_cast<bool>(v4872)) return v4872; v4872 = ([&]() -> Value { auto fn4876 = PrepareDictionaryGet(s->LocalAt(6)); Arguments args4877; args4877.positional.reserve(2); args4877.Add(Value("TOMATO"), false); args4877.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn4876, std::move(args4877)); }()); return v4872; }()))) {
return ([&]() -> Value { auto v4878 = ([&]() -> Value { auto fn4879 = s->Global("_v219_walk"); Arguments args4880; args4880.positional.reserve(2); args4880.Add(s->LocalAt(8), false); args4880.Add(s->LocalAt(5), false); return Call(c, fn4879, std::move(args4880)); }()); if (static_cast<bool>(v4878)) return v4878; v4878 = List({Value("PLACE"), Value("TOMATO"), ([&]() -> Value { auto fn4881 = s->Global("int"); Arguments args4882; args4882.Add(([&]() -> Value { auto fn4883 = PrepareDictionaryGet(s->LocalAt(6)); Arguments args4884; args4884.positional.reserve(2); args4884.Add(Value("TOMATO"), false); args4884.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn4883, std::move(args4884)); }()), false); return Call(c, fn4881, std::move(args4882)); }())}); return v4878; }());
}
if (static_cast<bool>(s->LocalAt(16))) {
auto v4885 = ([&]() -> Value { auto fn4886 = s->Global("min"); Arguments args4887; args4887.Add(s->LocalAt(16), false); args4887.Keyword("key", Define(&Code_c4c3c0165649451f46c0, s, Signature{{"v"}, {}, {}, {}, "", "", ([]() -> std::span<const char* const> { static constexpr const char* names[] = {"v"}; return names; }())}, true, "<lambda>")); return Call(c, fn4886, std::move(args4887)); }());
auto unpack4897 = Iterate(v4885);
ValidateUnpack(unpack4897, 2, false);
s->SetAt(13, unpack4897.at(0));
s->SetAt(1, unpack4897.at(1));
return ([&]() -> Value { auto v4898 = ([&]() -> Value { auto fn4899 = s->Global("_v219_walk"); Arguments args4900; args4900.positional.reserve(2); args4900.Add(s->LocalAt(8), false); args4900.Add(s->LocalAt(13), false); return Call(c, fn4899, std::move(args4900)); }()); if (static_cast<bool>(v4898)) return v4898; v4898 = s->LocalAt(1); return v4898; }());
}
if (static_cast<bool>(([&]() -> Value { auto fn4901 = PrepareDictionaryGet(s->LocalAt(6)); Arguments args4902; args4902.positional.reserve(2); args4902.Add(Value("TOMATO"), false); args4902.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn4901, std::move(args4902)); }()))) {
return ([&]() -> Value { auto v4903 = ([&]() -> Value { auto fn4904 = s->Global("_v219_walk"); Arguments args4905; args4905.positional.reserve(2); args4905.Add(s->LocalAt(8), false); args4905.Add(s->LocalAt(5), false); return Call(c, fn4904, std::move(args4905)); }()); if (static_cast<bool>(v4903)) return v4903; v4903 = List({Value("PLACE"), Value("TOMATO"), ([&]() -> Value { auto fn4906 = s->Global("int"); Arguments args4907; args4907.Add(Get(s->LocalAt(6), Value("TOMATO")), false); return Call(c, fn4906, std::move(args4907)); }())}); return v4903; }());
}
if (static_cast<bool>(([&]() -> Value { auto fn4908 = s->Global("any"); Arguments args4909; args4909.Add(([&]() -> Value { auto fn4910 = Attribute(s->LocalAt(6), "values"); Arguments args4911; return Call(c, fn4910, std::move(args4911)); }()), false); return Call(c, fn4908, std::move(args4909)); }()))) {
return ([&]() -> Value { auto v4912 = ([&]() -> Value { auto fn4913 = s->Global("_v219_walk"); Arguments args4914; args4914.positional.reserve(2); args4914.Add(s->LocalAt(8), false); args4914.Add(s->LocalAt(5), false); return Call(c, fn4913, std::move(args4914)); }()); if (static_cast<bool>(v4912)) return v4912; v4912 = List({Value("DROP")}); return v4912; }());
}
return List({Value("PASS")});
return {};
}
}  // namespace kagg::opponents::compiled
