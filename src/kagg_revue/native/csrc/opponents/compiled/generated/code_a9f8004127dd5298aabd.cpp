// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_a9f8004127dd5298aabd(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"a", "access", "actor", "chosen", "command", "commands", "day", "dx", "dy", "feeds", "hour", "key", "native", "obs", "op", "order", "player", "pos", "positions", "route", "step", "target", "tomorrow", "wheat"};
s->PrepareSlots(s_names);
auto v9753 = ([&]() -> Value { auto fn9754 = s->Global("int"); Arguments args9755; args9755.Add(Get(s->LocalAt(13), Value("step")), false); return Call(c, fn9754, std::move(args9755)); }());
s->SetAt(20, v9753);
auto v9756 = ([&]() -> Value { auto v9757 = s->LocalAt(20); return Binary("FloorDiv", v9757, Value(int64_t{24})); }());
s->SetAt(6, v9756);
if (static_cast<bool>(([&]() -> Value { auto v9758 = s->LocalAt(6); Value v9759; v9759 = Value(int64_t{28}); if (!static_cast<bool>(Binary("Eq", v9758, v9759))) return Value(false); v9758 = v9759; return Value(true); }()))) {
return Value(true);
}
auto v9760 = ([&]() -> Value { auto fn9761 = s->Global("int"); Arguments args9762; args9762.Add(Get(s->LocalAt(13), Value("player")), false); return Call(c, fn9761, std::move(args9762)); }());
s->SetAt(16, v9760);
auto v9763 = Get(Attribute(Attribute(s->Global("_IMPL"), "chassis"), "players"), s->LocalAt(16));
s->SetAt(12, v9763);
auto v9764 = ([&]() -> Value { auto v9765 = s->LocalAt(6); return Binary("Add", v9765, Value(int64_t{1})); }());
s->SetAt(22, v9764);
auto v9766 = (static_cast<bool>(([&]() -> Value { auto v9767 = s->LocalAt(22); Value v9768; v9768 = Value(int64_t{27}); if (!static_cast<bool>(Binary("GtE", v9767, v9768))) return Value(false); v9767 = v9768; return Value(true); }())) ? Value(int64_t{2}) : Get(s->LocalAt(12), Value("route")));
s->SetAt(19, v9766);
auto v9769 = Tuple({s->LocalAt(19), s->LocalAt(22)});
s->SetAt(11, v9769);
if (static_cast<bool>(([&]() -> Value { auto v9770 = s->LocalAt(11); Value v9771; v9771 = s->Global("_R86_FEED_CACHE"); if (!static_cast<bool>(Binary("NotIn", v9770, v9771))) return Value(false); v9770 = v9771; return Value(true); }()))) {
auto v9772 = List({Tuple({Value(int64_t{4}), Value(int64_t{4})})});
s->SetAt(18, v9772);
auto v9773 = List({Value(int64_t{0})});
s->SetAt(23, v9773);
auto v9774 = Tuple({Tuple({Value(int64_t{4}), Value(int64_t{4})}), Tuple({Value(int64_t{5}), Value(int64_t{4})}), Tuple({Value(int64_t{4}), Value(int64_t{5})}), Tuple({Value(int64_t{5}), Value(int64_t{5})})});
s->SetAt(1, v9774);
auto v9775 = ([&]() -> Value { auto fn9776 = s->Global("set"); Arguments args9777; return Call(c, fn9776, std::move(args9777)); }());
s->SetAt(9, v9775);
for (const auto& item9778 : Iterate(([&]() -> Value { auto fn9779 = s->Global("range"); Arguments args9780; args9780.Add(Value(int64_t{24}), false); return Call(c, fn9779, std::move(args9780)); }()))) {
s->SetAt(10, item9778);
auto v9781 = Get(Get(Attribute(Attribute(s->Global("_IMPL"), "chassis"), "routes"), s->LocalAt(19)), ([&]() -> Value { auto v9782 = ([&]() -> Value { auto v9783 = s->LocalAt(22); return Binary("Mult", v9783, Value(int64_t{24})); }()); return Binary("Add", v9782, s->LocalAt(10)); }()));
s->SetAt(0, v9781);
auto v9784 = ([&]() -> Value { Arguments args9785; args9785.Add(([&]() -> Value { auto v9786 = ([&]() -> Value { auto fn9787 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args9788; args9788.Add(Value("farmer"), false); return CallDictionaryGet(c, fn9787, std::move(args9788)); }()); if (static_cast<bool>(v9786)) return v9786; v9786 = List({Value("PASS")}); return v9786; }()), false); args9785.Add(([&]() -> Value { auto v9789 = ([&]() -> Value { auto fn9790 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args9791; args9791.Add(Value("hands"), false); return CallDictionaryGet(c, fn9790, std::move(args9791)); }()); if (static_cast<bool>(v9789)) return v9789; v9789 = List({}); return v9789; }()), true); return List(std::move(args9785.positional)); }());
s->SetAt(5, v9784);
for (const auto& item9792 : Iterate(([&]() -> Value { auto fn9793 = s->Global("enumerate"); Arguments args9794; args9794.Add(Slice(s->LocalAt(5), Value{}, ([&]() -> Value { auto fn9795 = s->Global("len"); Arguments args9796; args9796.Add(s->LocalAt(18), false); return Call(c, fn9795, std::move(args9796)); }()), Value{}), false); return Call(c, fn9793, std::move(args9794)); }()))) {
auto unpack9797 = Iterate(item9792);
ValidateUnpack(unpack9797, 2, false);
s->SetAt(2, unpack9797.at(0));
s->SetAt(4, unpack9797.at(1));
if (static_cast<bool>(Unary("Not", s->LocalAt(4)))) {
continue;
}
auto v9798 = Get(s->LocalAt(18), s->LocalAt(2));
s->SetAt(17, v9798);
auto v9799 = Get(s->LocalAt(4), Value(int64_t{0}));
s->SetAt(14, v9799);
if (static_cast<bool>(([&]() -> Value { auto v9800 = s->LocalAt(14); Value v9801; v9801 = s->Global("MOVES"); if (!static_cast<bool>(Binary("In", v9800, v9801))) return Value(false); v9800 = v9801; return Value(true); }()))) {
auto v9802 = Get(s->Global("MOVES"), s->LocalAt(14));
auto unpack9803 = Iterate(v9802);
ValidateUnpack(unpack9803, 2, false);
s->SetAt(7, unpack9803.at(0));
s->SetAt(8, unpack9803.at(1));
auto v9804 = Tuple({([&]() -> Value { auto fn9805 = s->Global("max"); Arguments args9806; args9806.positional.reserve(2); args9806.Add(Value(int64_t{0}), false); args9806.Add(([&]() -> Value { auto fn9807 = s->Global("min"); Arguments args9808; args9808.positional.reserve(2); args9808.Add(Value(int64_t{9}), false); args9808.Add(([&]() -> Value { auto v9809 = Get(s->LocalAt(17), Value(int64_t{0})); return Binary("Add", v9809, s->LocalAt(7)); }()), false); return Call(c, fn9807, std::move(args9808)); }()), false); return Call(c, fn9805, std::move(args9806)); }()), ([&]() -> Value { auto fn9810 = s->Global("max"); Arguments args9811; args9811.positional.reserve(2); args9811.Add(Value(int64_t{0}), false); args9811.Add(([&]() -> Value { auto fn9812 = s->Global("min"); Arguments args9813; args9813.positional.reserve(2); args9813.Add(Value(int64_t{9}), false); args9813.Add(([&]() -> Value { auto v9814 = Get(s->LocalAt(17), Value(int64_t{1})); return Binary("Add", v9814, s->LocalAt(8)); }()), false); return Call(c, fn9812, std::move(args9813)); }()), false); return Call(c, fn9810, std::move(args9811)); }())});
Put(s->LocalAt(18), s->LocalAt(2), v9804);
}
else {
if (static_cast<bool>(([&]() -> Value { auto v9815 = ([&]() -> Value { auto v9816 = Slice(s->LocalAt(4), Value{}, Value(int64_t{2}), Value{}); Value v9817; v9817 = List({Value("PICKUP"), Value("WHEAT")}); if (!static_cast<bool>(Binary("Eq", v9816, v9817))) return Value(false); v9816 = v9817; return Value(true); }()); if (!static_cast<bool>(v9815)) return v9815; v9815 = ([&]() -> Value { auto v9818 = s->LocalAt(17); Value v9819; v9819 = s->LocalAt(1); if (!static_cast<bool>(Binary("In", v9818, v9819))) return Value(false); v9818 = v9819; return Value(true); }()); return v9815; }()))) {
auto v9820 = s->LocalAt(23);
auto v9821 = s->LocalAt(2);
auto v9822 = Get(v9820, v9821);
Put(v9820, v9821, Inplace("Add", v9822, ([&]() -> Value { auto fn9823 = s->Global("max"); Arguments args9824; args9824.positional.reserve(2); args9824.Add(Value(int64_t{0}), false); args9824.Add((static_cast<bool>(([&]() -> Value { auto v9825 = ([&]() -> Value { auto fn9827 = s->Global("len"); Arguments args9828; args9828.Add(s->LocalAt(4), false); return Call(c, fn9827, std::move(args9828)); }()); Value v9826; v9826 = Value(int64_t{2}); if (!static_cast<bool>(Binary("Gt", v9825, v9826))) return Value(false); v9825 = v9826; return Value(true); }())) ? ([&]() -> Value { auto fn9829 = s->Global("int"); Arguments args9830; args9830.Add(Get(s->LocalAt(4), Value(int64_t{2})), false); return Call(c, fn9829, std::move(args9830)); }()) : Value(int64_t{1})), false); return Call(c, fn9823, std::move(args9824)); }())));
}
else {
if (static_cast<bool>(([&]() -> Value { auto v9831 = ([&]() -> Value { auto v9832 = s->LocalAt(14); Value v9833; v9833 = Value("FEED"); if (!static_cast<bool>(Binary("Eq", v9832, v9833))) return Value(false); v9832 = v9833; return Value(true); }()); if (!static_cast<bool>(v9831)) return v9831; v9831 = ([&]() -> Value { auto v9834 = Get(s->LocalAt(23), s->LocalAt(2)); Value v9835; v9835 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v9834, v9835))) return Value(false); v9834 = v9835; return Value(true); }()); return v9831; }()))) {
auto v9836 = s->LocalAt(23);
auto v9837 = s->LocalAt(2);
auto v9838 = Get(v9836, v9837);
Put(v9836, v9837, Inplace("Sub", v9838, Value(int64_t{1})));
if (static_cast<bool>(([&]() -> Value { auto v9839 = s->LocalAt(10); Value v9840; v9840 = Value(int64_t{21}); if (!static_cast<bool>(Binary("LtE", v9839, v9840))) return Value(false); v9839 = v9840; return Value(true); }()))) {
(void)([&]() -> Value { auto fn9841 = Attribute(s->LocalAt(9), "add"); Arguments args9842; args9842.Add(s->LocalAt(17), false); return Call(c, fn9841, std::move(args9842)); }());
}
}
else {
if (static_cast<bool>(([&]() -> Value { auto v9843 = ([&]() -> Value { auto v9844 = s->LocalAt(14); Value v9845; v9845 = Value("DROP"); if (!static_cast<bool>(Binary("Eq", v9844, v9845))) return Value(false); v9844 = v9845; return Value(true); }()); if (!static_cast<bool>(v9843)) return v9843; v9843 = ([&]() -> Value { auto v9846 = s->LocalAt(17); Value v9847; v9847 = s->LocalAt(1); if (!static_cast<bool>(Binary("In", v9846, v9847))) return Value(false); v9846 = v9847; return Value(true); }()); return v9843; }()))) {
auto v9848 = Value(int64_t{0});
Put(s->LocalAt(23), s->LocalAt(2), v9848);
}
else {
if (static_cast<bool>(([&]() -> Value { auto v9849 = ([&]() -> Value { auto v9850 = Slice(s->LocalAt(4), Value{}, Value(int64_t{2}), Value{}); Value v9851; v9851 = List({Value("PLACE"), Value("WHEAT")}); if (!static_cast<bool>(Binary("Eq", v9850, v9851))) return Value(false); v9850 = v9851; return Value(true); }()); if (!static_cast<bool>(v9849)) return v9849; v9849 = ([&]() -> Value { auto v9852 = s->LocalAt(17); Value v9853; v9853 = s->LocalAt(1); if (!static_cast<bool>(Binary("In", v9852, v9853))) return Value(false); v9852 = v9853; return Value(true); }()); return v9849; }()))) {
auto v9854 = ([&]() -> Value { auto fn9855 = s->Global("max"); Arguments args9856; args9856.positional.reserve(2); args9856.Add(Value(int64_t{0}), false); args9856.Add(([&]() -> Value { auto v9857 = Get(s->LocalAt(23), s->LocalAt(2)); return Binary("Sub", v9857, ([&]() -> Value { auto fn9858 = s->Global("max"); Arguments args9859; args9859.positional.reserve(2); args9859.Add(Value(int64_t{0}), false); args9859.Add((static_cast<bool>(([&]() -> Value { auto v9860 = ([&]() -> Value { auto fn9862 = s->Global("len"); Arguments args9863; args9863.Add(s->LocalAt(4), false); return Call(c, fn9862, std::move(args9863)); }()); Value v9861; v9861 = Value(int64_t{2}); if (!static_cast<bool>(Binary("Gt", v9860, v9861))) return Value(false); v9860 = v9861; return Value(true); }())) ? ([&]() -> Value { auto fn9864 = s->Global("int"); Arguments args9865; args9865.Add(Get(s->LocalAt(4), Value(int64_t{2})), false); return Call(c, fn9864, std::move(args9865)); }()) : Value(int64_t{1})), false); return Call(c, fn9858, std::move(args9859)); }())); }()), false); return Call(c, fn9855, std::move(args9856)); }());
Put(s->LocalAt(23), s->LocalAt(2), v9854);
}
}
}
}
}
}
for (const auto& item9866 : Iterate(([&]() -> Value { auto fn9867 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args9868; args9868.positional.reserve(2); args9868.Add(Value("market"), false); args9868.Add(List({}), false); return CallDictionaryGet(c, fn9867, std::move(args9868)); }()))) {
s->SetAt(15, item9866);
if (static_cast<bool>(([&]() -> Value { auto v9869 = s->LocalAt(15); if (!static_cast<bool>(v9869)) return v9869; v9869 = ([&]() -> Value { auto v9870 = Get(s->LocalAt(15), Value(int64_t{0})); Value v9871; v9871 = Value("HIRE"); if (!static_cast<bool>(Binary("Eq", v9870, v9871))) return Value(false); v9870 = v9871; return Value(true); }()); return v9869; }()))) {
auto v9872 = ([&]() -> Value { auto fn9873 = s->Global("min"); Arguments args9874; args9874.Add(s->LocalAt(1), false); args9874.Keyword("key", Define(&Code_395d0a2fa9584cb73fa1, s, Signature{{"p"}, {}, {}, {}, "", "", ([]() -> std::span<const char* const> { static constexpr const char* names[] = {"p"}; return names; }())}, true, "<lambda>")); return Call(c, fn9873, std::move(args9874)); }());
s->SetAt(3, v9872);
(void)([&]() -> Value { auto fn9879 = Attribute(s->LocalAt(18), "append"); Arguments args9880; args9880.Add(s->LocalAt(3), false); return Call(c, fn9879, std::move(args9880)); }());
(void)([&]() -> Value { auto fn9881 = Attribute(s->LocalAt(23), "append"); Arguments args9882; args9882.Add(Value(int64_t{0}), false); return Call(c, fn9881, std::move(args9882)); }());
}
}
}
auto v9883 = ([&]() -> Value { auto fn9884 = s->Global("frozenset"); Arguments args9885; args9885.Add(s->LocalAt(9), false); return Call(c, fn9884, std::move(args9885)); }());
Put(s->Global("_R86_FEED_CACHE"), s->LocalAt(11), v9883);
}
return ([&]() -> Value { auto v9886 = ([&]() -> Value { auto fn9888 = s->Global("tuple"); Arguments args9889; args9889.Add(s->LocalAt(21), false); return Call(c, fn9888, std::move(args9889)); }()); Value v9887; v9887 = Get(s->Global("_R86_FEED_CACHE"), s->LocalAt(11)); if (!static_cast<bool>(Binary("In", v9886, v9887))) return Value(false); v9886 = v9887; return Value(true); }());
return {};
}
}  // namespace kagg::opponents::compiled
