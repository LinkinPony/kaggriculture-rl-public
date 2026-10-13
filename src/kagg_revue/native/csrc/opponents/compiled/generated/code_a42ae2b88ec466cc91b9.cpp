// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_a42ae2b88ec466cc91b9(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"c", "clean", "d", "held", "hires", "native", "o", "obs", "pickups", "prices", "private", "spend", "step", "t", "tape"};
s->PrepareSlots(s_names);
auto v30805 = ([&]() -> Value { auto fn30806 = s->Global("int"); Arguments args30807; args30807.Add(Get(s->LocalAt(7), Value("step")), false); return Call(c, fn30806, std::move(args30807)); }());
s->SetAt(12, v30805);
if (static_cast<bool>(([&]() -> Value { auto v30808 = ([&]() -> Value { auto v30810 = s->LocalAt(12); return Binary("FloorDiv", v30810, Value(int64_t{24})); }()); Value v30809; v30809 = Value(int64_t{11}); if (!static_cast<bool>(Binary("NotEq", v30808, v30809))) return Value(false); v30808 = v30809; return Value(true); }()))) {
return ([&]() -> Value { auto fn30811 = s->Global("_VE_ELIGIBLE"); Arguments args30812; args30812.positional.reserve(2); args30812.Add(s->LocalAt(7), false); args30812.Add(s->LocalAt(5), false); return Call(c, fn30811, std::move(args30812)); }());
}
auto v30813 = Get(Attribute(Attribute(s->Global("_IMPL"), "chassis"), "routes"), Get(s->LocalAt(5), Value("route")));
s->SetAt(14, v30813);
auto v30814 = Get(s->LocalAt(7), Value("private"));
s->SetAt(10, v30814);
auto v30815 = ([&]() -> Value { auto v30816 = ([&]() -> Value { auto fn30817 = s->Global("int"); Arguments args30818; args30818.Add(([&]() -> Value { auto fn30819 = PrepareDictionaryGet(Get(s->LocalAt(10), Value("shed"))); Arguments args30820; args30820.positional.reserve(2); args30820.Add(Value("SHEEP"), false); args30820.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn30819, std::move(args30820)); }()), false); return Call(c, fn30817, std::move(args30818)); }()); return Binary("Add", v30816, ([&]() -> Value { auto fn30821 = s->Global("sum"); Arguments args30822; args30822.Add(([&]() -> Value { auto comp30823 = std::make_shared<Scope>(); comp30823->globals = s->globals; comp30823->parent = s; static constexpr const char* comp30823_names[] = {"i"}; comp30823->PrepareSlots(comp30823_names); auto result30824 = List(); for (const auto& item30825 : Iterate(Get(s->LocalAt(10), Value("inventories")))) { comp30823->SetAt(0, item30825); result30824.node()->sequence.push_back(([&]() -> Value { auto fn30826 = comp30823->Global("int"); Arguments args30827; args30827.Add(([&]() -> Value { auto fn30828 = PrepareDictionaryGet(comp30823->LocalAt(0)); Arguments args30829; args30829.positional.reserve(2); args30829.Add(Value("SHEEP"), false); args30829.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn30828, std::move(args30829)); }()), false); return Call(c, fn30826, std::move(args30827)); }())); } return result30824; }()), false); return Call(c, fn30821, std::move(args30822)); }())); }());
s->SetAt(3, v30815);
auto v30830 = Value(int64_t{0});
s->SetAt(8, v30830);
for (const auto& item30831 : Iterate(([&]() -> Value { auto fn30832 = s->Global("range"); Arguments args30833; args30833.positional.reserve(2); args30833.Add(s->LocalAt(12), false); args30833.Add(([&]() -> Value { auto v30834 = Value(int64_t{12}); return Binary("Mult", v30834, Value(int64_t{24})); }()), false); return Call(c, fn30832, std::move(args30833)); }()))) {
s->SetAt(13, item30831);
for (const auto& item30835 : Iterate(([&]() -> Value { auto v30836 = List({([&]() -> Value { auto fn30837 = PrepareDictionaryGet(Get(s->LocalAt(14), s->LocalAt(13))); Arguments args30838; args30838.Add(Value("farmer"), false); return CallDictionaryGet(c, fn30837, std::move(args30838)); }())}); return Binary("Add", v30836, ([&]() -> Value { auto fn30839 = PrepareDictionaryGet(Get(s->LocalAt(14), s->LocalAt(13))); Arguments args30840; args30840.positional.reserve(2); args30840.Add(Value("hands"), false); args30840.Add(List({}), false); return CallDictionaryGet(c, fn30839, std::move(args30840)); }())); }()))) {
s->SetAt(0, item30835);
if (static_cast<bool>(([&]() -> Value { auto v30841 = s->LocalAt(0); if (!static_cast<bool>(v30841)) return v30841; v30841 = ([&]() -> Value { auto v30842 = Get(s->LocalAt(0), Value(int64_t{0})); Value v30843; v30843 = Value("PICKUP"); if (!static_cast<bool>(Binary("Eq", v30842, v30843))) return Value(false); v30842 = v30843; return Value(true); }()); if (!static_cast<bool>(v30841)) return v30841; v30841 = ([&]() -> Value { auto v30844 = ([&]() -> Value { auto fn30846 = s->Global("len"); Arguments args30847; args30847.Add(s->LocalAt(0), false); return Call(c, fn30846, std::move(args30847)); }()); Value v30845; v30845 = Value(int64_t{1}); if (!static_cast<bool>(Binary("Gt", v30844, v30845))) return Value(false); v30844 = v30845; return Value(true); }()); if (!static_cast<bool>(v30841)) return v30841; v30841 = ([&]() -> Value { auto v30848 = Get(s->LocalAt(0), Value(int64_t{1})); Value v30849; v30849 = Value("SHEEP"); if (!static_cast<bool>(Binary("Eq", v30848, v30849))) return Value(false); v30848 = v30849; return Value(true); }()); return v30841; }()))) {
auto v30850 = s->LocalAt(8);
s->SetAt(8, Inplace("Add", v30850, (static_cast<bool>(([&]() -> Value { auto v30851 = ([&]() -> Value { auto fn30853 = s->Global("len"); Arguments args30854; args30854.Add(s->LocalAt(0), false); return Call(c, fn30853, std::move(args30854)); }()); Value v30852; v30852 = Value(int64_t{2}); if (!static_cast<bool>(Binary("Gt", v30851, v30852))) return Value(false); v30851 = v30852; return Value(true); }())) ? ([&]() -> Value { auto fn30855 = s->Global("int"); Arguments args30856; args30856.Add(Get(s->LocalAt(0), Value(int64_t{2})), false); return Call(c, fn30855, std::move(args30856)); }()) : Value(int64_t{1}))));
}
}
}
if (static_cast<bool>(([&]() -> Value { auto v30857 = s->LocalAt(3); Value v30858; v30858 = s->LocalAt(8); if (!static_cast<bool>(Binary("Gt", v30857, v30858))) return Value(false); v30857 = v30858; return Value(true); }()))) {
return Value(false);
}
auto v30859 = ([&]() -> Value { auto fn30860 = s->Global("dict"); Arguments args30861; args30861.Add(s->LocalAt(10), false); args30861.Keyword("shed", ([&]() -> Value { auto fn30862 = s->Global("dict"); Arguments args30863; args30863.Add(Get(s->LocalAt(10), Value("shed")), false); args30863.Keyword("SHEEP", Value(int64_t{0})); return Call(c, fn30862, std::move(args30863)); }())); args30861.Keyword("inventories", ([&]() -> Value { auto comp30864 = std::make_shared<Scope>(); comp30864->globals = s->globals; comp30864->parent = s; static constexpr const char* comp30864_names[] = {"i"}; comp30864->PrepareSlots(comp30864_names); auto result30865 = List(); for (const auto& item30866 : Iterate(Get(s->LocalAt(10), Value("inventories")))) { comp30864->SetAt(0, item30866); result30865.node()->sequence.push_back(([&]() -> Value { auto comp30867 = std::make_shared<Scope>(); comp30867->globals = comp30864->globals; comp30867->parent = comp30864; static constexpr const char* comp30867_names[] = {"k", "v"}; comp30867->PrepareSlots(comp30867_names); auto result30868 = Dict(); for (const auto& item30869 : Iterate(([&]() -> Value { auto fn30870 = Attribute(comp30864->LocalAt(0), "items"); Arguments args30871; return Call(c, fn30870, std::move(args30871)); }()))) { auto unpack30872 = Iterate(item30869); ValidateUnpack(unpack30872, 2, false); comp30867->SetAt(0, unpack30872.at(0)); comp30867->SetAt(1, unpack30872.at(1)); if (!static_cast<bool>(([&]() -> Value { auto v30873 = comp30867->LocalAt(0); Value v30874; v30874 = Value("SHEEP"); if (!static_cast<bool>(Binary("NotEq", v30873, v30874))) return Value(false); v30873 = v30874; return Value(true); }()))) continue; Put(result30868, comp30867->LocalAt(0), comp30867->LocalAt(1)); } return result30868; }())); } return result30865; }())); return Call(c, fn30860, std::move(args30861)); }());
s->SetAt(1, v30859);
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto fn30875 = s->Global("_VE_ELIGIBLE"); Arguments args30876; args30876.positional.reserve(2); args30876.Add(([&]() -> Value { auto fn30877 = s->Global("dict"); Arguments args30878; args30878.Add(s->LocalAt(7), false); args30878.Keyword("private", s->LocalAt(1)); return Call(c, fn30877, std::move(args30878)); }()), false); args30876.Add(s->LocalAt(5), false); return Call(c, fn30875, std::move(args30876)); }())))) {
return Value(false);
}
auto v30879 = s->Global("_VE_REPORT");
auto v30880 = Value("ve_day11_checks");
auto v30881 = Get(v30879, v30880);
Put(v30879, v30880, Inplace("Add", v30881, Value(int64_t{1})));
auto v30882 = Get(Get(s->LocalAt(7), Value("market")), Value("prices"));
s->SetAt(9, v30882);
auto v30883 = Value(int64_t{0});
s->SetAt(11, v30883);
auto v30884 = ([&]() -> Value { auto dict30885 = Dict(); return dict30885; }());
s->SetAt(4, v30884);
for (const auto& item30886 : Iterate(([&]() -> Value { auto fn30887 = s->Global("range"); Arguments args30888; args30888.positional.reserve(2); args30888.Add(([&]() -> Value { auto v30889 = s->LocalAt(12); return Binary("Add", v30889, Value(int64_t{1})); }()), false); args30888.Add(([&]() -> Value { auto fn30890 = s->Global("min"); Arguments args30891; args30891.positional.reserve(2); args30891.Add(([&]() -> Value { auto fn30892 = s->Global("len"); Arguments args30893; args30893.Add(s->LocalAt(14), false); return Call(c, fn30892, std::move(args30893)); }()), false); args30891.Add(([&]() -> Value { auto v30894 = Value(int64_t{13}); return Binary("Mult", v30894, Value(int64_t{24})); }()), false); return Call(c, fn30890, std::move(args30891)); }()), false); return Call(c, fn30887, std::move(args30888)); }()))) {
s->SetAt(13, item30886);
for (const auto& item30895 : Iterate(([&]() -> Value { auto fn30896 = PrepareDictionaryGet(Get(s->LocalAt(14), s->LocalAt(13))); Arguments args30897; args30897.positional.reserve(2); args30897.Add(Value("market"), false); args30897.Add(List({}), false); return CallDictionaryGet(c, fn30896, std::move(args30897)); }()))) {
s->SetAt(6, item30895);
if (static_cast<bool>(Unary("Not", s->LocalAt(6)))) {
continue;
}
if (static_cast<bool>(([&]() -> Value { auto v30898 = ([&]() -> Value { auto v30899 = Get(s->LocalAt(6), Value(int64_t{0})); Value v30900; v30900 = Value("BUY_LAND"); if (!static_cast<bool>(Binary("Eq", v30899, v30900))) return Value(false); v30899 = v30900; return Value(true); }()); if (static_cast<bool>(v30898)) return v30898; v30898 = ([&]() -> Value { auto v30901 = Slice(s->LocalAt(6), Value{}, Value(int64_t{2}), Value{}); Value v30902; v30902 = List({Value("BUY_ANIMAL"), Value("SHEEP")}); if (!static_cast<bool>(Binary("Eq", v30901, v30902))) return Value(false); v30901 = v30902; return Value(true); }()); return v30898; }()))) {
return Value(false);
}
if (static_cast<bool>(([&]() -> Value { auto v30903 = Get(s->LocalAt(6), Value(int64_t{0})); Value v30904; v30904 = Value("BUY_SEED"); if (!static_cast<bool>(Binary("Eq", v30903, v30904))) return Value(false); v30903 = v30904; return Value(true); }()))) {
auto v30905 = s->LocalAt(11);
s->SetAt(11, Inplace("Add", v30905, ([&]() -> Value { auto v30906 = ([&]() -> Value { auto fn30907 = s->Global("int"); Arguments args30908; args30908.Add(Get(s->LocalAt(6), Value(int64_t{2})), false); return Call(c, fn30907, std::move(args30908)); }()); return Binary("Mult", v30906, ([&]() -> Value { auto fn30909 = PrepareDictionaryGet(s->Global("_VE_SEED")); Arguments args30910; args30910.positional.reserve(2); args30910.Add(Get(s->LocalAt(6), Value(int64_t{1})), false); args30910.Add(Value(int64_t{100}), false); return CallDictionaryGet(c, fn30909, std::move(args30910)); }())); }())));
}
else {
if (static_cast<bool>(([&]() -> Value { auto v30911 = Get(s->LocalAt(6), Value(int64_t{0})); Value v30912; v30912 = Value("BUY_PRODUCT"); if (!static_cast<bool>(Binary("Eq", v30911, v30912))) return Value(false); v30911 = v30912; return Value(true); }()))) {
auto v30913 = s->LocalAt(11);
s->SetAt(11, Inplace("Add", v30913, ([&]() -> Value { auto v30914 = ([&]() -> Value { auto fn30915 = s->Global("int"); Arguments args30916; args30916.Add(Get(s->LocalAt(6), Value(int64_t{2})), false); return Call(c, fn30915, std::move(args30916)); }()); return Binary("Mult", v30914, ([&]() -> Value { auto v30917 = ([&]() -> Value { auto fn30918 = s->Global("int"); Arguments args30919; args30919.Add(([&]() -> Value { auto fn30920 = PrepareDictionaryGet(s->LocalAt(9)); Arguments args30921; args30921.positional.reserve(2); args30921.Add(Get(s->LocalAt(6), Value(int64_t{1})), false); args30921.Add(Value(int64_t{50}), false); return CallDictionaryGet(c, fn30920, std::move(args30921)); }()), false); return Call(c, fn30918, std::move(args30919)); }()); return Binary("Add", v30917, Value(int64_t{10})); }())); }())));
}
else {
if (static_cast<bool>(([&]() -> Value { auto v30922 = Get(s->LocalAt(6), Value(int64_t{0})); Value v30923; v30923 = Value("BUY_ANIMAL"); if (!static_cast<bool>(Binary("Eq", v30922, v30923))) return Value(false); v30922 = v30923; return Value(true); }()))) {
auto v30924 = s->LocalAt(11);
s->SetAt(11, Inplace("Add", v30924, ([&]() -> Value { auto v30925 = ([&]() -> Value { auto fn30926 = s->Global("int"); Arguments args30927; args30927.Add(Get(s->LocalAt(6), Value(int64_t{2})), false); return Call(c, fn30926, std::move(args30927)); }()); return Binary("Mult", v30925, ([&]() -> Value { auto fn30928 = PrepareDictionaryGet(s->Global("_VE_ANIMAL")); Arguments args30929; args30929.positional.reserve(2); args30929.Add(Get(s->LocalAt(6), Value(int64_t{1})), false); args30929.Add(Value(int64_t{500}), false); return CallDictionaryGet(c, fn30928, std::move(args30929)); }())); }())));
}
else {
if (static_cast<bool>(([&]() -> Value { auto v30930 = Get(s->LocalAt(6), Value(int64_t{0})); Value v30931; v30931 = Value("HIRE"); if (!static_cast<bool>(Binary("Eq", v30930, v30931))) return Value(false); v30930 = v30931; return Value(true); }()))) {
auto v30932 = ([&]() -> Value { auto v30933 = s->LocalAt(13); return Binary("FloorDiv", v30933, Value(int64_t{24})); }());
s->SetAt(2, v30932);
auto v30934 = s->LocalAt(11);
s->SetAt(11, Inplace("Add", v30934, ([&]() -> Value { auto fn30935 = s->Global("_v219_fib"); Arguments args30936; args30936.Add(([&]() -> Value { auto fn30937 = PrepareDictionaryGet(s->LocalAt(4)); Arguments args30938; args30938.positional.reserve(2); args30938.Add(s->LocalAt(2), false); args30938.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn30937, std::move(args30938)); }()), false); return Call(c, fn30935, std::move(args30936)); }())));
auto v30939 = ([&]() -> Value { auto v30940 = ([&]() -> Value { auto fn30941 = PrepareDictionaryGet(s->LocalAt(4)); Arguments args30942; args30942.positional.reserve(2); args30942.Add(s->LocalAt(2), false); args30942.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn30941, std::move(args30942)); }()); return Binary("Add", v30940, Value(int64_t{1})); }());
Put(s->LocalAt(4), s->LocalAt(2), v30939);
}
}
}
}
}
}
if (static_cast<bool>(([&]() -> Value { auto v30943 = Get(Get(Get(s->LocalAt(7), Value("farms")), Get(s->LocalAt(7), Value("player"))), Value("money")); Value v30944; v30944 = ([&]() -> Value { auto v30945 = ([&]() -> Value { auto v30946 = Value(int64_t{7000}); return Binary("Add", v30946, Value(int64_t{3000})); }()); return Binary("Add", v30945, s->LocalAt(11)); }()); if (!static_cast<bool>(Binary("Lt", v30943, v30944))) return Value(false); v30943 = v30944; return Value(true); }()))) {
auto v30947 = s->Global("_VE_REPORT");
auto v30948 = Value("ve_day11_budget_declines");
auto v30949 = Get(v30947, v30948);
Put(v30947, v30948, Inplace("Add", v30949, Value(int64_t{1})));
return Value(false);
}
auto v30950 = s->Global("_VE_REPORT");
auto v30951 = Value("ve_day11_ok");
auto v30952 = Get(v30950, v30951);
Put(v30950, v30951, Inplace("Add", v30952, Value(int64_t{1})));
return Value(true);
return {};
}
}  // namespace kagg::opponents::compiled
