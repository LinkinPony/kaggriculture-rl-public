// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_f376600a5251d38c60c5(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "cash", "cost", "farm", "hires", "market", "o", "obs", "op", "prices", "quads", "shed"};
s->PrepareSlots(s_names);
auto v19722 = Get(Get(s->LocalAt(7), Value("farms")), ([&]() -> Value { auto fn19723 = s->Global("int"); Arguments args19724; args19724.Add(Get(s->LocalAt(7), Value("player")), false); return Call(c, fn19723, std::move(args19724)); }()));
s->SetAt(3, v19722);
auto v19725 = Get(Get(s->LocalAt(7), Value("market")), Value("prices"));
s->SetAt(9, v19725);
auto v19726 = Get(Get(s->LocalAt(7), Value("private")), Value("shed"));
s->SetAt(11, v19726);
try {
auto v19728 = ([&]() -> Value { auto fn19729 = s->Global("projected_shed"); Arguments args19730; args19730.positional.reserve(2); args19730.Add(([&]() -> Value { auto dict19731 = Dict(); auto key19732 = Value("farmer"); Put(dict19731, key19732, ([&]() -> Value { auto v19733 = ([&]() -> Value { auto fn19734 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args19735; args19735.Add(Value("farmer"), false); return CallDictionaryGet(c, fn19734, std::move(args19735)); }()); if (static_cast<bool>(v19733)) return v19733; v19733 = List({Value("PASS")}); return v19733; }())); auto key19736 = Value("hands"); Put(dict19731, key19736, ([&]() -> Value { auto v19737 = ([&]() -> Value { auto fn19738 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args19739; args19739.Add(Value("hands"), false); return CallDictionaryGet(c, fn19738, std::move(args19739)); }()); if (static_cast<bool>(v19737)) return v19737; v19737 = List({}); return v19737; }())); auto key19740 = Value("market"); Put(dict19731, key19740, List({})); return dict19731; }()), false); args19730.Add(([&]() -> Value { auto fn19741 = s->Global("FarmView"); Arguments args19742; args19742.Add(s->LocalAt(7), false); return Call(c, fn19741, std::move(args19742)); }()), false); return Call(c, fn19729, std::move(args19730)); }());
s->SetAt(11, v19728);
} catch (const Error& error19727) {
if (Matches(error19727, s->Global("Exception"))) {
}
else { throw; }
}
auto v19743 = ([&]() -> Value { auto fn19744 = s->Global("float"); Arguments args19745; args19745.Add(Get(s->LocalAt(3), Value("money")), false); return Call(c, fn19744, std::move(args19745)); }());
s->SetAt(1, v19743);
auto v19746 = Value(0.0);
s->SetAt(2, v19746);
auto v19747 = ([&]() -> Value { auto fn19748 = s->Global("int"); Arguments args19749; args19749.Add(([&]() -> Value { auto v19750 = ([&]() -> Value { auto fn19751 = PrepareDictionaryGet(s->LocalAt(3)); Arguments args19752; args19752.positional.reserve(2); args19752.Add(Value("hires_today"), false); args19752.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn19751, std::move(args19752)); }()); if (static_cast<bool>(v19750)) return v19750; v19750 = Value(int64_t{0}); return v19750; }()), false); return Call(c, fn19748, std::move(args19749)); }());
s->SetAt(4, v19747);
auto v19753 = ([&]() -> Value { auto fn19754 = s->Global("len"); Arguments args19755; args19755.Add(([&]() -> Value { auto v19756 = ([&]() -> Value { auto fn19757 = PrepareDictionaryGet(s->LocalAt(3)); Arguments args19758; args19758.positional.reserve(2); args19758.Add(Value("unlocked_quadrants"), false); args19758.Add(List({}), false); return CallDictionaryGet(c, fn19757, std::move(args19758)); }()); if (static_cast<bool>(v19756)) return v19756; v19756 = List({}); return v19756; }()), false); return Call(c, fn19754, std::move(args19755)); }());
s->SetAt(10, v19753);
for (const auto& item19759 : Iterate(s->LocalAt(5))) {
s->SetAt(6, item19759);
if (static_cast<bool>(Unary("Not", s->LocalAt(6)))) {
continue;
}
auto v19760 = Get(s->LocalAt(6), Value(int64_t{0}));
s->SetAt(8, v19760);
if (static_cast<bool>(([&]() -> Value { auto v19761 = ([&]() -> Value { auto v19762 = s->LocalAt(8); Value v19763; v19763 = Value("SELL"); if (!static_cast<bool>(Binary("Eq", v19762, v19763))) return Value(false); v19762 = v19763; return Value(true); }()); if (!static_cast<bool>(v19761)) return v19761; v19761 = ([&]() -> Value { auto v19764 = ([&]() -> Value { auto fn19766 = s->Global("len"); Arguments args19767; args19767.Add(s->LocalAt(6), false); return Call(c, fn19766, std::move(args19767)); }()); Value v19765; v19765 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v19764, v19765))) return Value(false); v19764 = v19765; return Value(true); }()); return v19761; }()))) {
auto v19768 = s->LocalAt(1);
s->SetAt(1, Inplace("Add", v19768, ([&]() -> Value { auto v19769 = ([&]() -> Value { auto v19770 = Value(0.8); return Binary("Mult", v19770, ([&]() -> Value { auto fn19771 = s->Global("min"); Arguments args19772; args19772.positional.reserve(2); args19772.Add(([&]() -> Value { auto fn19773 = s->Global("max"); Arguments args19774; args19774.positional.reserve(2); args19774.Add(Value(int64_t{0}), false); args19774.Add(([&]() -> Value { auto fn19775 = s->Global("int"); Arguments args19776; args19776.Add(Get(s->LocalAt(6), Value(int64_t{2})), false); return Call(c, fn19775, std::move(args19776)); }()), false); return Call(c, fn19773, std::move(args19774)); }()), false); args19772.Add(([&]() -> Value { auto fn19777 = s->Global("int"); Arguments args19778; args19778.Add(([&]() -> Value { auto fn19779 = PrepareDictionaryGet(s->LocalAt(11)); Arguments args19780; args19780.positional.reserve(2); args19780.Add(Get(s->LocalAt(6), Value(int64_t{1})), false); args19780.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn19779, std::move(args19780)); }()), false); return Call(c, fn19777, std::move(args19778)); }()), false); return Call(c, fn19771, std::move(args19772)); }())); }()); return Binary("Mult", v19769, ([&]() -> Value { auto fn19781 = s->Global("float"); Arguments args19782; args19782.Add(([&]() -> Value { auto fn19783 = PrepareDictionaryGet(s->LocalAt(9)); Arguments args19784; args19784.positional.reserve(2); args19784.Add(Get(s->LocalAt(6), Value(int64_t{1})), false); args19784.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn19783, std::move(args19784)); }()), false); return Call(c, fn19781, std::move(args19782)); }())); }())));
}
else {
if (static_cast<bool>(([&]() -> Value { auto v19785 = ([&]() -> Value { auto v19786 = s->LocalAt(8); Value v19787; v19787 = Value("BUY_ANIMAL"); if (!static_cast<bool>(Binary("Eq", v19786, v19787))) return Value(false); v19786 = v19787; return Value(true); }()); if (!static_cast<bool>(v19785)) return v19785; v19785 = ([&]() -> Value { auto v19788 = ([&]() -> Value { auto fn19790 = s->Global("len"); Arguments args19791; args19791.Add(s->LocalAt(6), false); return Call(c, fn19790, std::move(args19791)); }()); Value v19789; v19789 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v19788, v19789))) return Value(false); v19788 = v19789; return Value(true); }()); return v19785; }()))) {
auto v19792 = s->LocalAt(2);
s->SetAt(2, Inplace("Add", v19792, ([&]() -> Value { auto v19793 = ([&]() -> Value { auto fn19794 = s->Global("int"); Arguments args19795; args19795.Add(Get(s->LocalAt(6), Value(int64_t{2})), false); return Call(c, fn19794, std::move(args19795)); }()); return Binary("Mult", v19793, ([&]() -> Value { auto fn19796 = PrepareDictionaryGet(s->Global("_Y_COST")); Arguments args19797; args19797.positional.reserve(2); args19797.Add(Get(s->LocalAt(6), Value(int64_t{1})), false); args19797.Add(Value(int64_t{500}), false); return CallDictionaryGet(c, fn19796, std::move(args19797)); }())); }())));
}
else {
if (static_cast<bool>(([&]() -> Value { auto v19798 = ([&]() -> Value { auto v19799 = s->LocalAt(8); Value v19800; v19800 = Value("BUY_PRODUCT"); if (!static_cast<bool>(Binary("Eq", v19799, v19800))) return Value(false); v19799 = v19800; return Value(true); }()); if (!static_cast<bool>(v19798)) return v19798; v19798 = ([&]() -> Value { auto v19801 = ([&]() -> Value { auto fn19803 = s->Global("len"); Arguments args19804; args19804.Add(s->LocalAt(6), false); return Call(c, fn19803, std::move(args19804)); }()); Value v19802; v19802 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v19801, v19802))) return Value(false); v19801 = v19802; return Value(true); }()); return v19798; }()))) {
auto v19805 = s->LocalAt(2);
s->SetAt(2, Inplace("Add", v19805, ([&]() -> Value { auto v19806 = ([&]() -> Value { auto fn19807 = s->Global("int"); Arguments args19808; args19808.Add(Get(s->LocalAt(6), Value(int64_t{2})), false); return Call(c, fn19807, std::move(args19808)); }()); return Binary("Mult", v19806, ([&]() -> Value { auto v19809 = ([&]() -> Value { auto fn19810 = s->Global("float"); Arguments args19811; args19811.Add(([&]() -> Value { auto fn19812 = PrepareDictionaryGet(s->LocalAt(9)); Arguments args19813; args19813.positional.reserve(2); args19813.Add(Get(s->LocalAt(6), Value(int64_t{1})), false); args19813.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn19812, std::move(args19813)); }()), false); return Call(c, fn19810, std::move(args19811)); }()); return Binary("Add", v19809, Value(int64_t{10})); }())); }())));
}
else {
if (static_cast<bool>(([&]() -> Value { auto v19814 = ([&]() -> Value { auto v19815 = s->LocalAt(8); Value v19816; v19816 = Value("BUY_SEED"); if (!static_cast<bool>(Binary("Eq", v19815, v19816))) return Value(false); v19815 = v19816; return Value(true); }()); if (!static_cast<bool>(v19814)) return v19814; v19814 = ([&]() -> Value { auto v19817 = ([&]() -> Value { auto fn19819 = s->Global("len"); Arguments args19820; args19820.Add(s->LocalAt(6), false); return Call(c, fn19819, std::move(args19820)); }()); Value v19818; v19818 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v19817, v19818))) return Value(false); v19817 = v19818; return Value(true); }()); return v19814; }()))) {
auto v19821 = s->LocalAt(2);
s->SetAt(2, Inplace("Add", v19821, ([&]() -> Value { auto v19822 = ([&]() -> Value { auto fn19823 = s->Global("int"); Arguments args19824; args19824.Add(Get(s->LocalAt(6), Value(int64_t{2})), false); return Call(c, fn19823, std::move(args19824)); }()); return Binary("Mult", v19822, ([&]() -> Value { auto fn19825 = PrepareDictionaryGet(s->Global("_Y_SEED")); Arguments args19826; args19826.positional.reserve(2); args19826.Add(Get(s->LocalAt(6), Value(int64_t{1})), false); args19826.Add(Value(int64_t{100}), false); return CallDictionaryGet(c, fn19825, std::move(args19826)); }())); }())));
}
else {
if (static_cast<bool>(([&]() -> Value { auto v19827 = s->LocalAt(8); Value v19828; v19828 = Value("BUY_LAND"); if (!static_cast<bool>(Binary("Eq", v19827, v19828))) return Value(false); v19827 = v19828; return Value(true); }()))) {
auto v19829 = s->LocalAt(2);
s->SetAt(2, Inplace("Add", v19829, Get(Tuple({Value(int64_t{1000}), Value(int64_t{2000}), Value(int64_t{4000})}), ([&]() -> Value { auto fn19830 = s->Global("min"); Arguments args19831; args19831.positional.reserve(2); args19831.Add(Value(int64_t{2}), false); args19831.Add(([&]() -> Value { auto fn19832 = s->Global("max"); Arguments args19833; args19833.positional.reserve(2); args19833.Add(Value(int64_t{0}), false); args19833.Add(([&]() -> Value { auto v19834 = s->LocalAt(10); return Binary("Sub", v19834, Value(int64_t{1})); }()), false); return Call(c, fn19832, std::move(args19833)); }()), false); return Call(c, fn19830, std::move(args19831)); }()))));
}
else {
if (static_cast<bool>(([&]() -> Value { auto v19835 = s->LocalAt(8); Value v19836; v19836 = Value("HIRE"); if (!static_cast<bool>(Binary("Eq", v19835, v19836))) return Value(false); v19835 = v19836; return Value(true); }()))) {
auto v19837 = s->LocalAt(2);
s->SetAt(2, Inplace("Add", v19837, ([&]() -> Value { auto fn19838 = s->Global("_y_fib"); Arguments args19839; args19839.Add(s->LocalAt(4), false); return Call(c, fn19838, std::move(args19839)); }())));
auto v19840 = s->LocalAt(4);
s->SetAt(4, Inplace("Add", v19840, Value(int64_t{1})));
}
}
}
}
}
}
}
return ([&]() -> Value { auto v19841 = s->LocalAt(1); return Binary("Sub", v19841, s->LocalAt(2)); }());
return {};
}
}  // namespace kagg::opponents::compiled
