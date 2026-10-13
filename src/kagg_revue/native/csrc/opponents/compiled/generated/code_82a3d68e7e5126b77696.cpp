// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_82a3d68e7e5126b77696(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"_", "action", "baseline", "best_orders", "best_score", "current", "gain", "left", "observation", "orders", "player", "probe", "result", "right", "rival", "rival_orders", "score", "step", "stock", "trial", "trial_score"};
s->PrepareSlots(s_names);
auto v15832 = ([&]() -> Value { auto fn15833 = s->Global("int"); Arguments args15834; args15834.Add(Get(s->LocalAt(8), Value("step")), false); return Call(c, fn15833, std::move(args15834)); }());
s->SetAt(17, v15832);
auto v15835 = ([&]() -> Value { auto fn15836 = s->Global("int"); Arguments args15837; args15837.Add(Get(s->LocalAt(8), Value("player")), false); return Call(c, fn15836, std::move(args15837)); }());
s->SetAt(10, v15835);
auto v15838 = ([&]() -> Value { auto v15839 = Value(int64_t{1}); return Binary("Sub", v15839, s->LocalAt(10)); }());
s->SetAt(14, v15838);
auto v15840 = ([&]() -> Value { auto v15841 = ([&]() -> Value { auto fn15842 = PrepareDictionaryGet(s->LocalAt(1)); Arguments args15843; args15843.Add(Value("market"), false); return CallDictionaryGet(c, fn15842, std::move(args15843)); }()); if (static_cast<bool>(v15841)) return v15841; v15841 = List({}); return v15841; }());
s->SetAt(9, v15840);
auto v15844 = ([&]() -> Value { auto v15845 = ([&]() -> Value { auto fn15846 = PrepareDictionaryGet(s->Global("_R44_PROBES")); Arguments args15847; args15847.Add(s->LocalAt(10), false); return CallDictionaryGet(c, fn15846, std::move(args15847)); }()); if (static_cast<bool>(v15845)) return v15845; v15845 = ([&]() -> Value { auto dict15848 = Dict(); return dict15848; }()); return v15845; }());
s->SetAt(11, v15844);
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto v15849 = ([&]() -> Value { auto v15850 = Value(int64_t{336}); Value v15851; v15851 = s->LocalAt(17); if (!static_cast<bool>(Binary("LtE", v15850, v15851))) return Value(false); v15850 = v15851; v15851 = Value(int64_t{696}); if (!static_cast<bool>(Binary("Lt", v15850, v15851))) return Value(false); v15850 = v15851; return Value(true); }()); if (!static_cast<bool>(v15849)) return v15849; v15849 = ([&]() -> Value { auto v15852 = ([&]() -> Value { auto v15854 = s->LocalAt(17); return Binary("Mod", v15854, Value(int64_t{72})); }()); Value v15853; v15853 = Value(int64_t{71}); if (!static_cast<bool>(Binary("Eq", v15852, v15853))) return Value(false); v15852 = v15853; return Value(true); }()); if (!static_cast<bool>(v15849)) return v15849; v15849 = ([&]() -> Value { auto fn15855 = PrepareDictionaryGet(s->LocalAt(11)); Arguments args15856; args15856.Add(Value("matched"), false); return CallDictionaryGet(c, fn15855, std::move(args15856)); }()); return v15849; }())))) {
return s->LocalAt(1);
}
if (static_cast<bool>(([&]() -> Value { auto v15857 = Get(Get(Get(s->LocalAt(8), Value("farms")), s->LocalAt(10)), Value("money")); Value v15858; v15858 = ([&]() -> Value { auto v15859 = Get(Get(Get(s->LocalAt(8), Value("farms")), s->LocalAt(14)), Value("money")); return Binary("Add", v15859, Value(int64_t{500})); }()); if (!static_cast<bool>(Binary("Gt", v15857, v15858))) return Value(false); v15857 = v15858; return Value(true); }()))) {
return s->LocalAt(1);
}
if (static_cast<bool>(([&]() -> Value { auto v15860 = ([&]() -> Value { auto v15861 = ([&]() -> Value { auto fn15863 = s->Global("_r37_similarity"); Arguments args15864; args15864.Add(s->LocalAt(8), false); return Call(c, fn15863, std::move(args15864)); }()); Value v15862; v15862 = Value(0.9); if (!static_cast<bool>(Binary("Lt", v15861, v15862))) return Value(false); v15861 = v15862; return Value(true); }()); if (static_cast<bool>(v15860)) return v15860; v15860 = ([&]() -> Value { auto v15865 = ([&]() -> Value { auto fn15867 = s->Global("len"); Arguments args15868; args15868.Add(s->LocalAt(9), false); return Call(c, fn15867, std::move(args15868)); }()); Value v15866; v15866 = Value(int64_t{2}); if (!static_cast<bool>(Binary("Lt", v15865, v15866))) return Value(false); v15865 = v15866; return Value(true); }()); return v15860; }()))) {
return s->LocalAt(1);
}
if (static_cast<bool>(([&]() -> Value { auto comp15869 = std::make_shared<Scope>(); comp15869->globals = s->globals; comp15869->parent = s; static constexpr const char* comp15869_names[] = {"order"}; comp15869->PrepareSlots(comp15869_names); auto result15870 = List(); for (const auto& item15871 : Iterate(s->LocalAt(9))) { comp15869->SetAt(0, item15871); if (static_cast<bool>(([&]() -> Value { auto v15872 = Unary("Not", comp15869->LocalAt(0)); if (static_cast<bool>(v15872)) return v15872; v15872 = ([&]() -> Value { auto v15873 = ([&]() -> Value { auto fn15875 = comp15869->Global("len"); Arguments args15876; args15876.Add(comp15869->LocalAt(0), false); return Call(c, fn15875, std::move(args15876)); }()); Value v15874; v15874 = Value(int64_t{3}); if (!static_cast<bool>(Binary("Lt", v15873, v15874))) return Value(false); v15873 = v15874; return Value(true); }()); if (static_cast<bool>(v15872)) return v15872; v15872 = ([&]() -> Value { auto v15877 = Get(comp15869->LocalAt(0), Value(int64_t{0})); Value v15878; v15878 = Value("SELL"); if (!static_cast<bool>(Binary("NotEq", v15877, v15878))) return Value(false); v15877 = v15878; return Value(true); }()); if (static_cast<bool>(v15872)) return v15872; v15872 = ([&]() -> Value { auto v15879 = Get(comp15869->LocalAt(0), Value(int64_t{1})); Value v15880; v15880 = comp15869->Global("PRODUCTS"); if (!static_cast<bool>(Binary("NotIn", v15879, v15880))) return Value(false); v15879 = v15880; return Value(true); }()); if (static_cast<bool>(v15872)) return v15872; v15872 = ([&]() -> Value { auto v15881 = ([&]() -> Value { auto fn15883 = comp15869->Global("type"); Arguments args15884; args15884.Add(Get(comp15869->LocalAt(0), Value(int64_t{2})), false); return Call(c, fn15883, std::move(args15884)); }()); Value v15882; v15882 = comp15869->Global("int"); if (!static_cast<bool>(Binary("IsNot", v15881, v15882))) return Value(false); v15881 = v15882; return Value(true); }()); if (static_cast<bool>(v15872)) return v15872; v15872 = ([&]() -> Value { auto v15885 = Get(comp15869->LocalAt(0), Value(int64_t{2})); Value v15886; v15886 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Lt", v15885, v15886))) return Value(false); v15885 = v15886; return Value(true); }()); return v15872; }()))) return Value(true); } return Value(false); }()))) {
return s->LocalAt(1);
}
auto v15887 = ([&]() -> Value { auto fn15888 = s->Global("projected_shed"); Arguments args15889; args15889.positional.reserve(2); args15889.Add(s->LocalAt(1), false); args15889.Add(([&]() -> Value { auto fn15890 = s->Global("FarmView"); Arguments args15891; args15891.Add(s->LocalAt(8), false); return Call(c, fn15890, std::move(args15891)); }()), false); return Call(c, fn15888, std::move(args15889)); }());
s->SetAt(18, v15887);
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto comp15892 = std::make_shared<Scope>(); comp15892->globals = s->globals; comp15892->parent = s; static constexpr const char* comp15892_names[] = {"order"}; comp15892->PrepareSlots(comp15892_names); auto result15893 = List(); for (const auto& item15894 : Iterate(s->LocalAt(9))) { comp15892->SetAt(0, item15894); if (static_cast<bool>(([&]() -> Value { auto v15895 = ([&]() -> Value { auto fn15897 = comp15892->Global("min"); Arguments args15898; args15898.positional.reserve(2); args15898.Add(Get(comp15892->LocalAt(0), Value(int64_t{2})), false); args15898.Add(([&]() -> Value { auto fn15899 = comp15892->Global("max"); Arguments args15900; args15900.positional.reserve(2); args15900.Add(Value(int64_t{0}), false); args15900.Add(([&]() -> Value { auto fn15901 = comp15892->Global("int"); Arguments args15902; args15902.Add(([&]() -> Value { auto fn15903 = PrepareDictionaryGet(comp15892->Captured("stock")); Arguments args15904; args15904.positional.reserve(2); args15904.Add(Get(comp15892->LocalAt(0), Value(int64_t{1})), false); args15904.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn15903, std::move(args15904)); }()), false); return Call(c, fn15901, std::move(args15902)); }()), false); return Call(c, fn15899, std::move(args15900)); }()), false); return Call(c, fn15897, std::move(args15898)); }()); Value v15896; v15896 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v15895, v15896))) return Value(false); v15895 = v15896; return Value(true); }()))) return Value(true); } return Value(false); }())))) {
return s->LocalAt(1);
}
auto v15905 = ([&]() -> Value { auto fn15906 = Attribute(s->Global("copy"), "deepcopy"); Arguments args15907; args15907.Add(s->LocalAt(9), false); return Call(c, fn15906, std::move(args15907)); }());
s->SetAt(15, v15905);
auto v15908 = ([&]() -> Value { auto fn15909 = Attribute(s->Global("copy"), "deepcopy"); Arguments args15910; args15910.Add(s->LocalAt(9), false); return Call(c, fn15909, std::move(args15910)); }());
s->SetAt(5, v15908);
auto v15911 = ([&]() -> Value { auto fn15912 = s->Global("_r132_mirror_revenue"); Arguments args15913; args15913.positional.reserve(4); args15913.Add(s->LocalAt(8), false); args15913.Add(s->LocalAt(5), false); args15913.Add(s->LocalAt(15), false); args15913.Add(s->LocalAt(18), false); return Call(c, fn15912, std::move(args15913)); }());
s->SetAt(2, v15911);
auto v15914 = s->LocalAt(2);
s->SetAt(16, v15914);
for (const auto& item15915 : Iterate(([&]() -> Value { auto fn15916 = s->Global("range"); Arguments args15917; args15917.Add(Value(int64_t{10}), false); return Call(c, fn15916, std::move(args15917)); }()))) {
s->SetAt(0, item15915);
auto v15918 = s->LocalAt(16);
s->SetAt(4, v15918);
auto v15919 = Value{};
s->SetAt(3, v15919);
for (const auto& item15920 : Iterate(([&]() -> Value { auto fn15921 = s->Global("range"); Arguments args15922; args15922.Add(([&]() -> Value { auto fn15923 = s->Global("len"); Arguments args15924; args15924.Add(s->LocalAt(5), false); return Call(c, fn15923, std::move(args15924)); }()), false); return Call(c, fn15921, std::move(args15922)); }()))) {
s->SetAt(7, item15920);
for (const auto& item15925 : Iterate(([&]() -> Value { auto fn15926 = s->Global("range"); Arguments args15927; args15927.positional.reserve(2); args15927.Add(([&]() -> Value { auto v15928 = s->LocalAt(7); return Binary("Add", v15928, Value(int64_t{1})); }()), false); args15927.Add(([&]() -> Value { auto fn15929 = s->Global("len"); Arguments args15930; args15930.Add(s->LocalAt(5), false); return Call(c, fn15929, std::move(args15930)); }()), false); return Call(c, fn15926, std::move(args15927)); }()))) {
s->SetAt(13, item15925);
if (static_cast<bool>(([&]() -> Value { auto v15931 = Get(s->LocalAt(5), s->LocalAt(7)); Value v15932; v15932 = Get(s->LocalAt(5), s->LocalAt(13)); if (!static_cast<bool>(Binary("Eq", v15931, v15932))) return Value(false); v15931 = v15932; return Value(true); }()))) {
continue;
}
auto v15933 = ([&]() -> Value { auto fn15934 = Attribute(s->Global("copy"), "deepcopy"); Arguments args15935; args15935.Add(s->LocalAt(5), false); return Call(c, fn15934, std::move(args15935)); }());
s->SetAt(19, v15933);
auto v15936 = Tuple({Get(s->LocalAt(19), s->LocalAt(13)), Get(s->LocalAt(19), s->LocalAt(7))});
auto unpack15937 = Iterate(v15936);
ValidateUnpack(unpack15937, 2, false);
Put(s->LocalAt(19), s->LocalAt(7), unpack15937.at(0));
Put(s->LocalAt(19), s->LocalAt(13), unpack15937.at(1));
auto v15938 = ([&]() -> Value { auto fn15939 = s->Global("_r132_mirror_revenue"); Arguments args15940; args15940.positional.reserve(4); args15940.Add(s->LocalAt(8), false); args15940.Add(s->LocalAt(19), false); args15940.Add(s->LocalAt(15), false); args15940.Add(s->LocalAt(18), false); return Call(c, fn15939, std::move(args15940)); }());
s->SetAt(20, v15938);
if (static_cast<bool>(([&]() -> Value { auto v15941 = s->LocalAt(20); Value v15942; v15942 = s->LocalAt(4); if (!static_cast<bool>(Binary("Gt", v15941, v15942))) return Value(false); v15941 = v15942; return Value(true); }()))) {
auto v15943 = Tuple({s->LocalAt(20), s->LocalAt(19)});
auto unpack15944 = Iterate(v15943);
ValidateUnpack(unpack15944, 2, false);
s->SetAt(4, unpack15944.at(0));
s->SetAt(3, unpack15944.at(1));
}
}
}
if (static_cast<bool>(([&]() -> Value { auto v15945 = s->LocalAt(3); Value v15946; v15946 = Value{}; if (!static_cast<bool>(Binary("Is", v15945, v15946))) return Value(false); v15945 = v15946; return Value(true); }()))) {
break;
}
auto v15947 = Tuple({s->LocalAt(3), s->LocalAt(4)});
auto unpack15948 = Iterate(v15947);
ValidateUnpack(unpack15948, 2, false);
s->SetAt(5, unpack15948.at(0));
s->SetAt(16, unpack15948.at(1));
}
auto v15949 = ([&]() -> Value { auto v15950 = s->LocalAt(16); return Binary("Sub", v15950, s->LocalAt(2)); }());
s->SetAt(6, v15949);
if (static_cast<bool>(([&]() -> Value { auto v15951 = ([&]() -> Value { auto v15952 = s->LocalAt(6); Value v15953; v15953 = Value(int64_t{25}); if (!static_cast<bool>(Binary("Lt", v15952, v15953))) return Value(false); v15952 = v15953; return Value(true); }()); if (static_cast<bool>(v15951)) return v15951; v15951 = ([&]() -> Value { auto v15954 = s->LocalAt(5); Value v15955; v15955 = s->LocalAt(9); if (!static_cast<bool>(Binary("Eq", v15954, v15955))) return Value(false); v15954 = v15955; return Value(true); }()); return v15951; }()))) {
return s->LocalAt(1);
}
auto v15956 = s->Global("_R132_REPORT");
auto v15957 = Value("mirror_reorders");
auto v15958 = Get(v15956, v15957);
Put(v15956, v15957, Inplace("Add", v15958, Value(int64_t{1})));
auto v15959 = s->Global("_R132_REPORT");
auto v15960 = Value("mirror_modeled_gain");
auto v15961 = Get(v15959, v15960);
Put(v15959, v15960, Inplace("Add", v15961, s->LocalAt(6)));
auto v15962 = ([&]() -> Value { auto fn15963 = Attribute(s->Global("copy"), "deepcopy"); Arguments args15964; args15964.Add(s->LocalAt(1), false); return Call(c, fn15963, std::move(args15964)); }());
s->SetAt(12, v15962);
auto v15965 = s->LocalAt(5);
Put(s->LocalAt(12), Value("market"), v15965);
return s->LocalAt(12);
return {};
}
}  // namespace kagg::opponents::compiled
