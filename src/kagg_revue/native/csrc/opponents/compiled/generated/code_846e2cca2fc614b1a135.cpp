// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_846e2cca2fc614b1a135(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"_", "action", "actor", "after", "arrivals", "c", "commands", "cs", "farm", "future", "held", "item", "nxt", "obs", "old_pending", "pending", "positions", "prefetches", "private", "projected_farm", "projected_private", "proposed", "q", "result", "safe", "state", "step", "swaps", "tile", "x", "y"};
s->PrepareSlots(s_names);
auto v11766 = ([&]() -> Value { auto fn11767 = s->Global("int"); Arguments args11768; args11768.Add(Get(s->LocalAt(13), Value("step")), false); return Call(c, fn11767, std::move(args11768)); }());
s->SetAt(26, v11766);
auto v11769 = Get(Get(s->LocalAt(13), Value("farms")), Get(s->LocalAt(13), Value("player")));
s->SetAt(8, v11769);
auto v11770 = Get(s->LocalAt(13), Value("private"));
s->SetAt(18, v11770);
auto v11771 = ([&]() -> Value { Arguments args11772; args11772.Add(Get(s->LocalAt(8), Value("farmer")), false); args11772.Add(Get(s->LocalAt(8), Value("hands")), true); return List(std::move(args11772.positional)); }());
s->SetAt(16, v11771);
for (const auto& item11773 : Iterate(([&]() -> Value { auto fn11774 = Attribute(s->LocalAt(25), "pop"); Arguments args11775; args11775.positional.reserve(2); args11775.Add(Value("arrivals"), false); args11775.Add(List({}), false); return Call(c, fn11774, std::move(args11775)); }()))) {
s->SetAt(11, item11773);
if (static_cast<bool>(([&]() -> Value { auto v11776 = ([&]() -> Value { auto v11777 = Get(s->LocalAt(11), Value("step")); Value v11778; v11778 = s->LocalAt(26); if (!static_cast<bool>(Binary("NotEq", v11777, v11778))) return Value(false); v11777 = v11778; return Value(true); }()); if (static_cast<bool>(v11776)) return v11776; v11776 = ([&]() -> Value { auto v11779 = Get(s->LocalAt(11), Value("actor")); Value v11780; v11780 = ([&]() -> Value { auto fn11781 = s->Global("len"); Arguments args11782; args11782.Add(Get(s->LocalAt(18), Value("inventories")), false); return Call(c, fn11781, std::move(args11782)); }()); if (!static_cast<bool>(Binary("GtE", v11779, v11780))) return Value(false); v11779 = v11780; return Value(true); }()); if (static_cast<bool>(v11776)) return v11776; v11776 = ([&]() -> Value { auto v11783 = ([&]() -> Value { auto fn11785 = PrepareDictionaryGet(Get(Get(s->LocalAt(18), Value("inventories")), Get(s->LocalAt(11), Value("actor")))); Arguments args11786; args11786.positional.reserve(2); args11786.Add(Value("WHEAT"), false); args11786.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn11785, std::move(args11786)); }()); Value v11784; v11784 = Get(s->LocalAt(11), Value("expected")); if (!static_cast<bool>(Binary("Lt", v11783, v11784))) return Value(false); v11783 = v11784; return Value(true); }()); return v11776; }()))) {
auto v11787 = s->Global("_R128_REPORT");
auto v11788 = Value("service_arrival_errors");
auto v11789 = Get(v11787, v11788);
Put(v11787, v11788, Inplace("Add", v11789, Value(int64_t{1})));
}
else {
auto v11790 = s->Global("_R128_REPORT");
auto v11791 = Value("service_confirmed_units");
auto v11792 = Get(v11790, v11791);
Put(v11790, v11791, Inplace("Add", v11792, Get(s->LocalAt(11), Value("quantity"))));
}
}
auto v11793 = ([&]() -> Value { auto fn11794 = Attribute(s->LocalAt(25), "pop"); Arguments args11795; args11795.positional.reserve(2); args11795.Add(Value("swaps"), false); args11795.Add(([&]() -> Value { auto dict11796 = Dict(); return dict11796; }()), false); return Call(c, fn11794, std::move(args11795)); }());
s->SetAt(14, v11793);
auto v11797 = s->LocalAt(1);
s->SetAt(23, v11797);
auto v11798 = ([&]() -> Value { auto fn11799 = s->Global("_r128_commands"); Arguments args11800; args11800.Add(s->LocalAt(23), false); return Call(c, fn11799, std::move(args11800)); }());
s->SetAt(7, v11798);
for (const auto& item11801 : Iterate(([&]() -> Value { auto fn11802 = Attribute(s->LocalAt(14), "items"); Arguments args11803; return Call(c, fn11802, std::move(args11803)); }()))) {
auto unpack11804 = Iterate(item11801);
ValidateUnpack(unpack11804, 2, false);
s->SetAt(2, unpack11804.at(0));
s->SetAt(15, unpack11804.at(1));
if (static_cast<bool>(([&]() -> Value { auto v11805 = ([&]() -> Value { auto v11806 = s->LocalAt(26); Value v11807; v11807 = Get(s->LocalAt(15), Value("step")); if (!static_cast<bool>(Binary("NotEq", v11806, v11807))) return Value(false); v11806 = v11807; return Value(true); }()); if (static_cast<bool>(v11805)) return v11805; v11805 = ([&]() -> Value { auto v11808 = s->LocalAt(2); Value v11809; v11809 = ([&]() -> Value { auto fn11810 = s->Global("len"); Arguments args11811; args11811.Add(s->LocalAt(16), false); return Call(c, fn11810, std::move(args11811)); }()); if (!static_cast<bool>(Binary("GtE", v11808, v11809))) return Value(false); v11808 = v11809; return Value(true); }()); if (static_cast<bool>(v11805)) return v11805; v11805 = ([&]() -> Value { auto v11812 = ([&]() -> Value { auto fn11814 = s->Global("list"); Arguments args11815; args11815.Add(Get(s->LocalAt(16), s->LocalAt(2)), false); return Call(c, fn11814, std::move(args11815)); }()); Value v11813; v11813 = Get(s->LocalAt(15), Value("xy")); if (!static_cast<bool>(Binary("NotEq", v11812, v11813))) return Value(false); v11812 = v11813; return Value(true); }()); if (static_cast<bool>(v11805)) return v11805; v11805 = ([&]() -> Value { auto v11816 = Get(s->LocalAt(7), s->LocalAt(2)); Value v11817; v11817 = Get(s->LocalAt(15), Value("pickup")); if (!static_cast<bool>(Binary("NotEq", v11816, v11817))) return Value(false); v11816 = v11817; return Value(true); }()); return v11805; }()))) {
auto v11818 = s->Global("_R128_REPORT");
auto v11819 = Value("service_swap_errors");
auto v11820 = Get(v11818, v11819);
Put(v11818, v11819, Inplace("Add", v11820, Value(int64_t{1})));
continue;
}
auto v11821 = Get(s->LocalAt(16), s->LocalAt(2));
auto unpack11822 = Iterate(v11821);
ValidateUnpack(unpack11822, 2, false);
s->SetAt(29, unpack11822.at(0));
s->SetAt(30, unpack11822.at(1));
auto v11823 = Get(Get(Get(s->LocalAt(8), Value("tiles")), s->LocalAt(30)), s->LocalAt(29));
s->SetAt(28, v11823);
if (static_cast<bool>(([&]() -> Value { auto v11824 = Unary("Not", ([&]() -> Value { auto fn11825 = s->Global("isinstance"); Arguments args11826; args11826.positional.reserve(2); args11826.Add(s->LocalAt(28), false); args11826.Add(s->Global("dict"), false); return Call(c, fn11825, std::move(args11826)); }())); if (static_cast<bool>(v11824)) return v11824; v11824 = ([&]() -> Value { auto v11827 = ([&]() -> Value { auto fn11829 = PrepareDictionaryGet(s->LocalAt(28)); Arguments args11830; args11830.Add(Value("animal"), false); return CallDictionaryGet(c, fn11829, std::move(args11830)); }()); Value v11828; v11828 = Get(s->LocalAt(15), Value("animal")); if (!static_cast<bool>(Binary("NotEq", v11827, v11828))) return Value(false); v11827 = v11828; return Value(true); }()); if (static_cast<bool>(v11824)) return v11824; v11824 = ([&]() -> Value { auto v11831 = ([&]() -> Value { auto fn11833 = PrepareDictionaryGet(s->LocalAt(28)); Arguments args11834; args11834.Add(Value("placed_day"), false); return CallDictionaryGet(c, fn11833, std::move(args11834)); }()); Value v11832; v11832 = Get(s->LocalAt(15), Value("birth")); if (!static_cast<bool>(Binary("NotEq", v11831, v11832))) return Value(false); v11831 = v11832; return Value(true); }()); return v11824; }()))) {
auto v11835 = s->Global("_R128_REPORT");
auto v11836 = Value("service_swap_errors");
auto v11837 = Get(v11835, v11836);
Put(v11835, v11836, Inplace("Add", v11837, Value(int64_t{1})));
continue;
}
if (static_cast<bool>(([&]() -> Value { auto v11838 = ([&]() -> Value { auto fn11840 = PrepareDictionaryGet(Get(Get(s->LocalAt(18), Value("inventories")), s->LocalAt(2))); Arguments args11841; args11841.positional.reserve(2); args11841.Add(Value("WHEAT"), false); args11841.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn11840, std::move(args11841)); }()); Value v11839; v11839 = ([&]() -> Value { auto v11842 = Get(s->LocalAt(15), Value("quantity")); return Binary("Add", v11842, Value(int64_t{1})); }()); if (!static_cast<bool>(Binary("Lt", v11838, v11839))) return Value(false); v11838 = v11839; return Value(true); }()))) {
auto v11843 = s->Global("_R128_REPORT");
auto v11844 = Value("service_swap_errors");
auto v11845 = Get(v11843, v11844);
Put(v11843, v11844, Inplace("Add", v11845, Value(int64_t{1})));
continue;
}
auto v11846 = (static_cast<bool>(([&]() -> Value { auto fn11847 = PrepareDictionaryGet(s->LocalAt(28)); Arguments args11848; args11848.Add(Value("fed_today"), false); return CallDictionaryGet(c, fn11847, std::move(args11848)); }())) ? List({Value("PASS")}) : List({Value("FEED")}));
Put(s->LocalAt(7), s->LocalAt(2), v11846);
auto v11849 = s->Global("_R128_REPORT");
auto v11850 = Value("service_swaps_completed");
auto v11851 = Get(v11849, v11850);
Put(v11849, v11850, Inplace("Add", v11851, Value(int64_t{1})));
}
if (static_cast<bool>(s->LocalAt(14))) {
auto v11852 = ([&]() -> Value { auto fn11853 = s->Global("dict"); Arguments args11854; args11854.Add(s->LocalAt(23), false); args11854.Keyword("farmer", Get(s->LocalAt(7), Value(int64_t{0}))); args11854.Keyword("hands", Slice(s->LocalAt(7), Value(int64_t{1}), Value{}, Value{})); return Call(c, fn11853, std::move(args11854)); }());
s->SetAt(21, v11852);
auto v11855 = ([&]() -> Value { auto fn11856 = s->Global("_r128_field_safe"); Arguments args11857; args11857.positional.reserve(4); args11857.Add(s->LocalAt(13), false); args11857.Add(s->LocalAt(23), false); args11857.Add(s->LocalAt(21), false); args11857.Add(([&]() -> Value { auto dict11858 = Dict(); return dict11858; }()), false); return Call(c, fn11856, std::move(args11857)); }());
auto unpack11859 = Iterate(v11855);
ValidateUnpack(unpack11859, 2, false);
s->SetAt(24, unpack11859.at(0));
s->SetAt(0, unpack11859.at(1));
if (static_cast<bool>(s->LocalAt(24))) {
auto v11860 = s->LocalAt(21);
s->SetAt(23, v11860);
}
else {
auto v11861 = s->Global("_R128_REPORT");
auto v11862 = Value("service_swap_errors");
auto v11863 = Get(v11861, v11862);
Put(v11861, v11862, Inplace("Add", v11863, Value(int64_t{1})));
}
}
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto v11864 = Value(int64_t{144}); Value v11865; v11865 = s->LocalAt(26); if (!static_cast<bool>(Binary("LtE", v11864, v11865))) return Value(false); v11864 = v11865; v11865 = Value(int64_t{647}); if (!static_cast<bool>(Binary("Lt", v11864, v11865))) return Value(false); v11864 = v11865; return Value(true); }())))) {
return s->LocalAt(23);
}
auto v11866 = ([&]() -> Value { auto fn11867 = s->Global("_r128_commands"); Arguments args11868; args11868.Add(s->LocalAt(23), false); return Call(c, fn11867, std::move(args11868)); }());
s->SetAt(7, v11866);
auto v11869 = ([&]() -> Value { auto fn11870 = s->Global("_r128_commands"); Arguments args11871; args11871.Add(([&]() -> Value { auto fn11872 = s->Global("_r128_future"); Arguments args11873; args11873.Add(s->LocalAt(13), false); return Call(c, fn11872, std::move(args11873)); }()), false); return Call(c, fn11870, std::move(args11871)); }());
s->SetAt(9, v11869);
auto v11874 = ([&]() -> Value { auto fn11875 = Attribute(s->Global("copy"), "deepcopy"); Arguments args11876; args11876.Add(s->LocalAt(23), false); return Call(c, fn11875, std::move(args11876)); }());
s->SetAt(21, v11874);
auto v11877 = ([&]() -> Value { auto fn11878 = s->Global("_r128_commands"); Arguments args11879; args11879.Add(s->LocalAt(21), false); return Call(c, fn11878, std::move(args11879)); }());
s->SetAt(6, v11877);
auto v11880 = ([&]() -> Value { auto dict11881 = Dict(); return dict11881; }());
s->SetAt(27, v11880);
auto v11882 = List({});
s->SetAt(4, v11882);
auto v11883 = Value(int64_t{0});
s->SetAt(17, v11883);
auto v11884 = ([&]() -> Value { auto fn11885 = s->Global("_r127_fields"); Arguments args11886; args11886.positional.reserve(2); args11886.Add(s->LocalAt(13), false); args11886.Add(s->LocalAt(23), false); return Call(c, fn11885, std::move(args11886)); }());
auto unpack11887 = Iterate(v11884);
ValidateUnpack(unpack11887, 2, false);
s->SetAt(19, unpack11887.at(0));
s->SetAt(20, unpack11887.at(1));
for (const auto& item11888 : Iterate(([&]() -> Value { auto fn11889 = s->Global("enumerate"); Arguments args11890; args11890.Add(Slice(s->LocalAt(7), Value{}, ([&]() -> Value { auto fn11891 = s->Global("len"); Arguments args11892; args11892.Add(Get(s->LocalAt(18), Value("inventories")), false); return Call(c, fn11891, std::move(args11892)); }()), Value{}), false); return Call(c, fn11889, std::move(args11890)); }()))) {
auto unpack11893 = Iterate(item11888);
ValidateUnpack(unpack11893, 2, false);
s->SetAt(2, unpack11893.at(0));
s->SetAt(5, unpack11893.at(1));
auto v11894 = Get(s->LocalAt(16), s->LocalAt(2));
auto unpack11895 = Iterate(v11894);
ValidateUnpack(unpack11895, 2, false);
s->SetAt(29, unpack11895.at(0));
s->SetAt(30, unpack11895.at(1));
if (static_cast<bool>(([&]() -> Value { auto v11896 = Tuple({s->LocalAt(29), s->LocalAt(30)}); Value v11897; v11897 = Tuple({Tuple({Value(int64_t{4}), Value(int64_t{4})}), Tuple({Value(int64_t{5}), Value(int64_t{4})}), Tuple({Value(int64_t{4}), Value(int64_t{5})}), Tuple({Value(int64_t{5}), Value(int64_t{5})})}); if (!static_cast<bool>(Binary("NotIn", v11896, v11897))) return Value(false); v11896 = v11897; return Value(true); }()))) {
continue;
}
auto v11898 = ([&]() -> Value { auto fn11899 = s->Global("max"); Arguments args11900; args11900.positional.reserve(2); args11900.Add(Value(int64_t{0}), false); args11900.Add(([&]() -> Value { auto fn11901 = s->Global("int"); Arguments args11902; args11902.Add(([&]() -> Value { auto fn11903 = PrepareDictionaryGet(Get(Get(s->LocalAt(18), Value("inventories")), s->LocalAt(2))); Arguments args11904; args11904.positional.reserve(2); args11904.Add(Value("WHEAT"), false); args11904.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn11903, std::move(args11904)); }()), false); return Call(c, fn11901, std::move(args11902)); }()), false); return Call(c, fn11899, std::move(args11900)); }());
s->SetAt(10, v11898);
auto v11905 = Get(Get(Get(s->LocalAt(8), Value("tiles")), s->LocalAt(30)), s->LocalAt(29));
s->SetAt(28, v11905);
auto v11906 = (static_cast<bool>(([&]() -> Value { auto v11907 = s->LocalAt(2); Value v11908; v11908 = ([&]() -> Value { auto fn11909 = s->Global("len"); Arguments args11910; args11910.Add(s->LocalAt(9), false); return Call(c, fn11909, std::move(args11910)); }()); if (!static_cast<bool>(Binary("Lt", v11907, v11908))) return Value(false); v11907 = v11908; return Value(true); }())) ? Get(s->LocalAt(9), s->LocalAt(2)) : List({Value("PASS")}));
s->SetAt(12, v11906);
if (static_cast<bool>(([&]() -> Value { auto v11911 = ([&]() -> Value { auto v11912 = s->LocalAt(5); Value v11913; v11913 = List({Value("FEED")}); if (!static_cast<bool>(Binary("Eq", v11912, v11913))) return Value(false); v11912 = v11913; return Value(true); }()); if (!static_cast<bool>(v11911)) return v11911; v11911 = ([&]() -> Value { auto v11914 = s->LocalAt(10); Value v11915; v11915 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v11914, v11915))) return Value(false); v11914 = v11915; return Value(true); }()); if (!static_cast<bool>(v11911)) return v11911; v11911 = ([&]() -> Value { auto v11916 = ([&]() -> Value { auto v11918 = s->LocalAt(26); return Binary("Mod", v11918, Value(int64_t{24})); }()); Value v11917; v11917 = Value(int64_t{21}); if (!static_cast<bool>(Binary("LtE", v11916, v11917))) return Value(false); v11916 = v11917; return Value(true); }()); if (!static_cast<bool>(v11911)) return v11911; v11911 = ([&]() -> Value { auto fn11919 = s->Global("isinstance"); Arguments args11920; args11920.positional.reserve(2); args11920.Add(s->LocalAt(28), false); args11920.Add(s->Global("dict"), false); return Call(c, fn11919, std::move(args11920)); }()); if (!static_cast<bool>(v11911)) return v11911; v11911 = ([&]() -> Value { auto fn11921 = PrepareDictionaryGet(s->LocalAt(28)); Arguments args11922; args11922.Add(Value("animal"), false); return CallDictionaryGet(c, fn11921, std::move(args11922)); }()); if (!static_cast<bool>(v11911)) return v11911; v11911 = Unary("Not", ([&]() -> Value { auto fn11923 = PrepareDictionaryGet(s->LocalAt(28)); Arguments args11924; args11924.Add(Value("fed_today"), false); return CallDictionaryGet(c, fn11923, std::move(args11924)); }())); if (!static_cast<bool>(v11911)) return v11911; v11911 = ([&]() -> Value { auto v11925 = Slice(s->LocalAt(12), Value{}, Value(int64_t{2}), Value{}); Value v11926; v11926 = List({Value("PICKUP"), Value("WHEAT")}); if (!static_cast<bool>(Binary("Eq", v11925, v11926))) return Value(false); v11925 = v11926; return Value(true); }()); return v11911; }()))) {
auto v11927 = ([&]() -> Value { auto fn11928 = s->Global("max"); Arguments args11929; args11929.positional.reserve(2); args11929.Add(Value(int64_t{0}), false); args11929.Add((static_cast<bool>(([&]() -> Value { auto v11930 = ([&]() -> Value { auto fn11932 = s->Global("len"); Arguments args11933; args11933.Add(s->LocalAt(12), false); return Call(c, fn11932, std::move(args11933)); }()); Value v11931; v11931 = Value(int64_t{2}); if (!static_cast<bool>(Binary("Gt", v11930, v11931))) return Value(false); v11930 = v11931; return Value(true); }())) ? ([&]() -> Value { auto fn11934 = s->Global("int"); Arguments args11935; args11935.Add(Get(s->LocalAt(12), Value(int64_t{2})), false); return Call(c, fn11934, std::move(args11935)); }()) : Value(int64_t{1})), false); return Call(c, fn11928, std::move(args11929)); }());
s->SetAt(22, v11927);
if (static_cast<bool>(Unary("Not", s->LocalAt(22)))) {
continue;
}
auto v11936 = List({Value("PICKUP"), Value("WHEAT"), ([&]() -> Value { auto v11937 = s->LocalAt(22); return Binary("Add", v11937, Value(int64_t{1})); }())});
Put(s->LocalAt(6), s->LocalAt(2), v11936);
auto v11938 = ([&]() -> Value { auto fn11939 = s->Global("dict"); Arguments args11940; args11940.Keyword("step", ([&]() -> Value { auto v11941 = s->LocalAt(26); return Binary("Add", v11941, Value(int64_t{1})); }())); args11940.Keyword("xy", List({s->LocalAt(29), s->LocalAt(30)})); args11940.Keyword("animal", Get(s->LocalAt(28), Value("animal"))); args11940.Keyword("birth", ([&]() -> Value { auto fn11942 = PrepareDictionaryGet(s->LocalAt(28)); Arguments args11943; args11943.Add(Value("placed_day"), false); return CallDictionaryGet(c, fn11942, std::move(args11943)); }())); args11940.Keyword("quantity", s->LocalAt(22)); args11940.Keyword("pickup", ([&]() -> Value { auto fn11944 = Attribute(s->Global("copy"), "deepcopy"); Arguments args11945; args11945.Add(s->LocalAt(12), false); return Call(c, fn11944, std::move(args11945)); }())); return Call(c, fn11939, std::move(args11940)); }());
Put(s->LocalAt(27), s->LocalAt(2), v11938);
(void)([&]() -> Value { auto fn11946 = Attribute(s->LocalAt(4), "append"); Arguments args11947; args11947.Add(([&]() -> Value { auto fn11948 = s->Global("dict"); Arguments args11949; args11949.Keyword("step", ([&]() -> Value { auto v11950 = s->LocalAt(26); return Binary("Add", v11950, Value(int64_t{1})); }())); args11949.Keyword("actor", s->LocalAt(2)); args11949.Keyword("expected", ([&]() -> Value { auto v11951 = s->LocalAt(22); return Binary("Add", v11951, Value(int64_t{1})); }())); args11949.Keyword("quantity", ([&]() -> Value { auto v11952 = s->LocalAt(22); return Binary("Add", v11952, Value(int64_t{1})); }())); return Call(c, fn11948, std::move(args11949)); }()), false); return Call(c, fn11946, std::move(args11947)); }());
}
else {
if (static_cast<bool>(([&]() -> Value { auto v11953 = s->LocalAt(5); Value v11954; v11954 = List({Value("PASS")}); if (!static_cast<bool>(Binary("Eq", v11953, v11954))) return Value(false); v11953 = v11954; return Value(true); }()))) {
auto v11955 = ([&]() -> Value { auto fn11956 = s->Global("_r128_food_need"); Arguments args11957; args11957.positional.reserve(4); args11957.Add(s->LocalAt(13), false); args11957.Add(s->LocalAt(19), false); args11957.Add(s->LocalAt(20), false); args11957.Add(s->LocalAt(2), false); return Call(c, fn11956, std::move(args11957)); }());
s->SetAt(22, v11955);
if (static_cast<bool>(s->LocalAt(22))) {
auto v11958 = List({Value("PICKUP"), Value("WHEAT"), s->LocalAt(22)});
Put(s->LocalAt(6), s->LocalAt(2), v11958);
auto v11959 = s->LocalAt(17);
s->SetAt(17, Inplace("Add", v11959, Value(int64_t{1})));
(void)([&]() -> Value { auto fn11960 = Attribute(s->LocalAt(4), "append"); Arguments args11961; args11961.Add(([&]() -> Value { auto fn11962 = s->Global("dict"); Arguments args11963; args11963.Keyword("step", ([&]() -> Value { auto v11964 = s->LocalAt(26); return Binary("Add", v11964, Value(int64_t{1})); }())); args11963.Keyword("actor", s->LocalAt(2)); args11963.Keyword("expected", ([&]() -> Value { auto v11965 = s->LocalAt(10); return Binary("Add", v11965, s->LocalAt(22)); }())); args11963.Keyword("quantity", s->LocalAt(22)); return Call(c, fn11962, std::move(args11963)); }()), false); return Call(c, fn11960, std::move(args11961)); }());
}
}
}
}
if (static_cast<bool>(Unary("Not", s->LocalAt(4)))) {
return s->LocalAt(23);
}
auto v11966 = Get(s->LocalAt(6), Value(int64_t{0}));
Put(s->LocalAt(21), Value("farmer"), v11966);
auto v11967 = Slice(s->LocalAt(6), Value(int64_t{1}), Value{}, Value{});
Put(s->LocalAt(21), Value("hands"), v11967);
auto v11968 = ([&]() -> Value { auto fn11969 = s->Global("_r128_field_safe"); Arguments args11970; args11970.positional.reserve(4); args11970.Add(s->LocalAt(13), false); args11970.Add(s->LocalAt(23), false); args11970.Add(s->LocalAt(21), false); args11970.Add(s->LocalAt(27), false); return Call(c, fn11969, std::move(args11970)); }());
auto unpack11971 = Iterate(v11968);
ValidateUnpack(unpack11971, 2, false);
s->SetAt(24, unpack11971.at(0));
s->SetAt(3, unpack11971.at(1));
if (static_cast<bool>(([&]() -> Value { auto v11972 = Unary("Not", s->LocalAt(24)); if (static_cast<bool>(v11972)) return v11972; v11972 = ([&]() -> Value { auto comp11973 = std::make_shared<Scope>(); comp11973->globals = s->globals; comp11973->parent = s; static constexpr const char* comp11973_names[] = {"p"}; comp11973->PrepareSlots(comp11973_names); auto result11974 = List(); for (const auto& item11975 : Iterate(s->LocalAt(4))) { comp11973->SetAt(0, item11975); if (static_cast<bool>(([&]() -> Value { auto v11976 = ([&]() -> Value { auto fn11978 = PrepareDictionaryGet(Get(Get(comp11973->Captured("after"), Value("inventories")), Get(comp11973->LocalAt(0), Value("actor")))); Arguments args11979; args11979.positional.reserve(2); args11979.Add(Value("WHEAT"), false); args11979.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn11978, std::move(args11979)); }()); Value v11977; v11977 = Get(comp11973->LocalAt(0), Value("expected")); if (!static_cast<bool>(Binary("Lt", v11976, v11977))) return Value(false); v11976 = v11977; return Value(true); }()))) return Value(true); } return Value(false); }()); return v11972; }()))) {
auto v11980 = s->Global("_R128_REPORT");
auto v11981 = Value("service_capacity_declines");
auto v11982 = Get(v11980, v11981);
Put(v11980, v11981, Inplace("Add", v11982, Value(int64_t{1})));
return s->LocalAt(23);
}
auto v11983 = s->LocalAt(27);
Put(s->LocalAt(25), Value("swaps"), v11983);
auto v11984 = s->LocalAt(4);
Put(s->LocalAt(25), Value("arrivals"), v11984);
auto v11985 = s->Global("_R128_REPORT");
auto v11986 = Value("service_swaps_started");
auto v11987 = Get(v11985, v11986);
Put(v11985, v11986, Inplace("Add", v11987, ([&]() -> Value { auto fn11988 = s->Global("len"); Arguments args11989; args11989.Add(s->LocalAt(27), false); return Call(c, fn11988, std::move(args11989)); }())));
auto v11990 = s->Global("_R128_REPORT");
auto v11991 = Value("service_idle_preloads");
auto v11992 = Get(v11990, v11991);
Put(v11990, v11991, Inplace("Add", v11992, s->LocalAt(17)));
auto v11993 = s->Global("_R128_REPORT");
auto v11994 = Value("service_requested_units");
auto v11995 = Get(v11993, v11994);
Put(v11993, v11994, Inplace("Add", v11995, ([&]() -> Value { auto fn11996 = s->Global("sum"); Arguments args11997; args11997.Add(([&]() -> Value { auto comp11998 = std::make_shared<Scope>(); comp11998->globals = s->globals; comp11998->parent = s; static constexpr const char* comp11998_names[] = {"p"}; comp11998->PrepareSlots(comp11998_names); auto result11999 = List(); for (const auto& item12000 : Iterate(s->LocalAt(4))) { comp11998->SetAt(0, item12000); result11999.node()->sequence.push_back(Get(comp11998->LocalAt(0), Value("quantity"))); } return result11999; }()), false); return Call(c, fn11996, std::move(args11997)); }())));
return s->LocalAt(21);
return {};
}
}  // namespace kagg::opponents::compiled
