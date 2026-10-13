#include "opponents/compiled/typed.hpp"
// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_61896df3a0335b213461(Context& c, const ScopePtr& s) {
if (auto result = TypedShed(c, s)) return *result;
static constexpr const char* s_names[] = {"act", "action", "cap", "held", "i", "inv", "item", "k", "op", "proj", "qty", "self", "take", "total", "units", "v", "view"};
s->PrepareSlots(s_names);
auto v762 = Get(Attribute(s->LocalAt(11), "cfg"), Value("shed_capacity"));
s->SetAt(2, v762);
auto v763 = ([&]() -> Value { auto comp764 = std::make_shared<Scope>(); comp764->globals = s->globals; comp764->parent = s; static constexpr const char* comp764_names[] = {"p"}; comp764->PrepareSlots(comp764_names); auto result765 = Dict(); for (const auto& item766 : Iterate(s->Global("PRODUCTS"))) { comp764->SetAt(0, item766); Put(result765, comp764->LocalAt(0), ([&]() -> Value { auto fn767 = PrepareDictionaryGet(Attribute(comp764->Captured("view"), "shed")); Arguments args768; args768.positional.reserve(2); args768.Add(comp764->LocalAt(0), false); args768.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn767, std::move(args768)); }())); } return result765; }());
s->SetAt(9, v763);
for (const auto& item769 : Iterate(([&]() -> Value { auto fn770 = Attribute(Attribute(s->LocalAt(16), "shed"), "items"); Arguments args771; return Call(c, fn770, std::move(args771)); }()))) {
auto unpack772 = Iterate(item769);
ValidateUnpack(unpack772, 2, false);
s->SetAt(7, unpack772.at(0));
s->SetAt(15, unpack772.at(1));
(void)([&]() -> Value { auto fn773 = Attribute(s->LocalAt(9), "setdefault"); Arguments args774; args774.positional.reserve(2); args774.Add(s->LocalAt(7), false); args774.Add(s->LocalAt(15), false); return Call(c, fn773, std::move(args774)); }());
}
auto v775 = ([&]() -> Value { auto fn776 = s->Global("sum"); Arguments args777; args777.Add(([&]() -> Value { auto fn778 = Attribute(s->LocalAt(9), "values"); Arguments args779; return Call(c, fn778, std::move(args779)); }()), false); return Call(c, fn776, std::move(args777)); }());
s->SetAt(13, v775);
auto v780 = ([&]() -> Value { auto v781 = List({([&]() -> Value { auto v782 = ([&]() -> Value { auto fn783 = PrepareDictionaryGet(s->LocalAt(1)); Arguments args784; args784.Add(Value("farmer"), false); return CallDictionaryGet(c, fn783, std::move(args784)); }()); if (static_cast<bool>(v782)) return v782; v782 = List({Value("PASS")}); return v782; }())}); return Binary("Add", v781, ([&]() -> Value { auto fn785 = s->Global("list"); Arguments args786; args786.Add(([&]() -> Value { auto v787 = ([&]() -> Value { auto fn788 = PrepareDictionaryGet(s->LocalAt(1)); Arguments args789; args789.Add(Value("hands"), false); return CallDictionaryGet(c, fn788, std::move(args789)); }()); if (static_cast<bool>(v787)) return v787; v787 = List({}); return v787; }()), false); return Call(c, fn785, std::move(args786)); }())); }());
s->SetAt(14, v780);
for (const auto& item790 : Iterate(([&]() -> Value { auto fn791 = s->Global("range"); Arguments args792; args792.Add(([&]() -> Value { auto fn793 = s->Global("min"); Arguments args794; args794.positional.reserve(2); args794.Add(([&]() -> Value { auto fn795 = s->Global("len"); Arguments args796; args796.Add(s->LocalAt(14), false); return Call(c, fn795, std::move(args796)); }()), false); args794.Add(([&]() -> Value { auto fn797 = s->Global("len"); Arguments args798; args798.Add(Attribute(s->LocalAt(16), "positions"), false); return Call(c, fn797, std::move(args798)); }()), false); return Call(c, fn793, std::move(args794)); }()), false); return Call(c, fn791, std::move(args792)); }()))) {
s->SetAt(4, item790);
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto fn799 = s->Global("_shed_adjacent"); Arguments args800; args800.positional.reserve(2); args800.Add(Get(Attribute(s->LocalAt(16), "positions"), s->LocalAt(4)), false); args800.Add(Attribute(s->LocalAt(16), "board"), false); return Call(c, fn799, std::move(args800)); }())))) {
continue;
}
auto v801 = Get(s->LocalAt(14), s->LocalAt(4));
s->SetAt(0, v801);
auto v802 = (static_cast<bool>(s->LocalAt(0)) ? Get(s->LocalAt(0), Value(int64_t{0})) : Value("PASS"));
s->SetAt(8, v802);
auto v803 = ([&]() -> Value { auto fn804 = Attribute(s->LocalAt(16), "inv"); Arguments args805; args805.Add(s->LocalAt(4), false); return Call(c, fn804, std::move(args805)); }());
s->SetAt(5, v803);
if (static_cast<bool>(([&]() -> Value { auto v806 = ([&]() -> Value { auto v807 = s->LocalAt(8); Value v808; v808 = Value("PICKUP"); if (!static_cast<bool>(Binary("Eq", v807, v808))) return Value(false); v807 = v808; return Value(true); }()); if (!static_cast<bool>(v806)) return v806; v806 = ([&]() -> Value { auto v809 = ([&]() -> Value { auto fn811 = s->Global("len"); Arguments args812; args812.Add(s->LocalAt(0), false); return Call(c, fn811, std::move(args812)); }()); Value v810; v810 = Value(int64_t{2}); if (!static_cast<bool>(Binary("GtE", v809, v810))) return Value(false); v809 = v810; return Value(true); }()); if (!static_cast<bool>(v806)) return v806; v806 = ([&]() -> Value { auto v813 = Get(s->LocalAt(0), Value(int64_t{1})); Value v814; v814 = s->LocalAt(9); if (!static_cast<bool>(Binary("In", v813, v814))) return Value(false); v813 = v814; return Value(true); }()); return v806; }()))) {
auto v815 = ([&]() -> Value { auto fn816 = s->Global("min"); Arguments args817; args817.positional.reserve(2); args817.Add(Get(s->LocalAt(9), Get(s->LocalAt(0), Value(int64_t{1}))), false); args817.Add(([&]() -> Value { auto fn818 = s->Global("max"); Arguments args819; args819.positional.reserve(2); args819.Add(Value(int64_t{0}), false); args819.Add((static_cast<bool>(([&]() -> Value { auto v820 = ([&]() -> Value { auto fn822 = s->Global("len"); Arguments args823; args823.Add(s->LocalAt(0), false); return Call(c, fn822, std::move(args823)); }()); Value v821; v821 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v820, v821))) return Value(false); v820 = v821; return Value(true); }())) ? ([&]() -> Value { auto fn824 = s->Global("_int"); Arguments args825; args825.Add(Get(s->LocalAt(0), Value(int64_t{2})), false); return Call(c, fn824, std::move(args825)); }()) : Value(int64_t{1})), false); return Call(c, fn818, std::move(args819)); }()), false); return Call(c, fn816, std::move(args817)); }());
s->SetAt(10, v815);
auto v826 = s->LocalAt(9);
auto v827 = Get(s->LocalAt(0), Value(int64_t{1}));
auto v828 = Get(v826, v827);
Put(v826, v827, Inplace("Sub", v828, s->LocalAt(10)));
auto v829 = s->LocalAt(13);
s->SetAt(13, Inplace("Sub", v829, s->LocalAt(10)));
}
else {
if (static_cast<bool>(([&]() -> Value { auto v830 = s->LocalAt(8); Value v831; v831 = Value("DROP"); if (!static_cast<bool>(Binary("Eq", v830, v831))) return Value(false); v830 = v831; return Value(true); }()))) {
for (const auto& item832 : Iterate(([&]() -> Value { auto fn833 = Attribute(s->LocalAt(5), "items"); Arguments args834; return Call(c, fn833, std::move(args834)); }()))) {
auto unpack835 = Iterate(item832);
ValidateUnpack(unpack835, 2, false);
s->SetAt(6, unpack835.at(0));
s->SetAt(3, unpack835.at(1));
auto v836 = ([&]() -> Value { auto fn837 = s->Global("min"); Arguments args838; args838.positional.reserve(2); args838.Add(([&]() -> Value { auto fn839 = s->Global("max"); Arguments args840; args840.positional.reserve(2); args840.Add(Value(int64_t{0}), false); args840.Add(([&]() -> Value { auto fn841 = s->Global("_int"); Arguments args842; args842.Add(s->LocalAt(3), false); return Call(c, fn841, std::move(args842)); }()), false); return Call(c, fn839, std::move(args840)); }()), false); args838.Add(([&]() -> Value { auto fn843 = s->Global("max"); Arguments args844; args844.positional.reserve(2); args844.Add(Value(int64_t{0}), false); args844.Add(([&]() -> Value { auto v845 = s->LocalAt(2); return Binary("Sub", v845, s->LocalAt(13)); }()), false); return Call(c, fn843, std::move(args844)); }()), false); return Call(c, fn837, std::move(args838)); }());
s->SetAt(12, v836);
if (static_cast<bool>(([&]() -> Value { auto v846 = s->LocalAt(12); Value v847; v847 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v846, v847))) return Value(false); v846 = v847; return Value(true); }()))) {
auto v848 = ([&]() -> Value { auto v849 = ([&]() -> Value { auto fn850 = PrepareDictionaryGet(s->LocalAt(9)); Arguments args851; args851.positional.reserve(2); args851.Add(s->LocalAt(6), false); args851.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn850, std::move(args851)); }()); return Binary("Add", v849, s->LocalAt(12)); }());
Put(s->LocalAt(9), s->LocalAt(6), v848);
auto v852 = s->LocalAt(13);
s->SetAt(13, Inplace("Add", v852, s->LocalAt(12)));
}
}
}
else {
if (static_cast<bool>(([&]() -> Value { auto v853 = ([&]() -> Value { auto v854 = s->LocalAt(8); Value v855; v855 = Value("PLACE"); if (!static_cast<bool>(Binary("Eq", v854, v855))) return Value(false); v854 = v855; return Value(true); }()); if (!static_cast<bool>(v853)) return v853; v853 = ([&]() -> Value { auto v856 = ([&]() -> Value { auto fn858 = s->Global("len"); Arguments args859; args859.Add(s->LocalAt(0), false); return Call(c, fn858, std::move(args859)); }()); Value v857; v857 = Value(int64_t{2}); if (!static_cast<bool>(Binary("GtE", v856, v857))) return Value(false); v856 = v857; return Value(true); }()); if (!static_cast<bool>(v853)) return v853; v853 = ([&]() -> Value { auto v860 = Get(s->LocalAt(0), Value(int64_t{1})); Value v861; v861 = s->Global("ANIMAL_STRUCTURE"); if (!static_cast<bool>(Binary("NotIn", v860, v861))) return Value(false); v860 = v861; return Value(true); }()); return v853; }()))) {
auto v862 = Get(s->LocalAt(0), Value(int64_t{1}));
s->SetAt(6, v862);
auto v863 = ([&]() -> Value { auto fn864 = s->Global("min"); Arguments args865; args865.positional.reserve(3); args865.Add(([&]() -> Value { auto fn866 = s->Global("max"); Arguments args867; args867.positional.reserve(2); args867.Add(Value(int64_t{0}), false); args867.Add((static_cast<bool>(([&]() -> Value { auto v868 = ([&]() -> Value { auto fn870 = s->Global("len"); Arguments args871; args871.Add(s->LocalAt(0), false); return Call(c, fn870, std::move(args871)); }()); Value v869; v869 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v868, v869))) return Value(false); v868 = v869; return Value(true); }())) ? ([&]() -> Value { auto fn872 = s->Global("_int"); Arguments args873; args873.Add(Get(s->LocalAt(0), Value(int64_t{2})), false); return Call(c, fn872, std::move(args873)); }()) : Value(int64_t{1})), false); return Call(c, fn866, std::move(args867)); }()), false); args865.Add(([&]() -> Value { auto fn874 = s->Global("max"); Arguments args875; args875.positional.reserve(2); args875.Add(Value(int64_t{0}), false); args875.Add(([&]() -> Value { auto fn876 = s->Global("_int"); Arguments args877; args877.Add(([&]() -> Value { auto fn878 = s->Global("_get"); Arguments args879; args879.positional.reserve(3); args879.Add(s->LocalAt(5), false); args879.Add(s->LocalAt(6), false); args879.Add(Value(int64_t{0}), false); return Call(c, fn878, std::move(args879)); }()), false); return Call(c, fn876, std::move(args877)); }()), false); return Call(c, fn874, std::move(args875)); }()), false); args865.Add(([&]() -> Value { auto fn880 = s->Global("max"); Arguments args881; args881.positional.reserve(2); args881.Add(Value(int64_t{0}), false); args881.Add(([&]() -> Value { auto v882 = s->LocalAt(2); return Binary("Sub", v882, s->LocalAt(13)); }()), false); return Call(c, fn880, std::move(args881)); }()), false); return Call(c, fn864, std::move(args865)); }());
s->SetAt(12, v863);
if (static_cast<bool>(([&]() -> Value { auto v883 = s->LocalAt(12); Value v884; v884 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v883, v884))) return Value(false); v883 = v884; return Value(true); }()))) {
auto v885 = ([&]() -> Value { auto v886 = ([&]() -> Value { auto fn887 = PrepareDictionaryGet(s->LocalAt(9)); Arguments args888; args888.positional.reserve(2); args888.Add(s->LocalAt(6), false); args888.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn887, std::move(args888)); }()); return Binary("Add", v886, s->LocalAt(12)); }());
Put(s->LocalAt(9), s->LocalAt(6), v885);
auto v889 = s->LocalAt(13);
s->SetAt(13, Inplace("Add", v889, s->LocalAt(12)));
}
}
}
}
}
return s->LocalAt(9);
return {};
}
}  // namespace kagg::opponents::compiled
