// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_b7c4beded1f6c3920c88(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "actor", "actors", "all_units", "available", "birth", "changed", "cmd", "crop", "day", "expected", "farm", "hour", "inv", "native", "native_pickups", "next_native", "o", "obs", "owned", "p", "parents", "pending", "plan", "planned", "plans", "player", "pos", "private", "purchases", "q", "state", "step", "stock", "targets", "tile", "topup", "total_cost", "total_q", "x", "y"};
s->PrepareSlots(s_names);
auto v7800 = ([&]() -> Value { auto fn7801 = s->Global("int"); Arguments args7802; args7802.Add(Get(s->LocalAt(18), Value("step")), false); return Call(c, fn7801, std::move(args7802)); }());
s->SetAt(32, v7800);
auto v7803 = ([&]() -> Value { auto v7804 = s->LocalAt(32); return Binary("FloorDiv", v7804, Value(int64_t{24})); }());
s->SetAt(9, v7803);
auto v7805 = ([&]() -> Value { auto v7806 = s->LocalAt(32); return Binary("Mod", v7806, Value(int64_t{24})); }());
s->SetAt(12, v7805);
auto v7807 = ([&]() -> Value { auto fn7808 = s->Global("int"); Arguments args7809; args7809.Add(Get(s->LocalAt(18), Value("player")), false); return Call(c, fn7808, std::move(args7809)); }());
s->SetAt(26, v7807);
auto v7810 = Get(Get(s->LocalAt(18), Value("farms")), s->LocalAt(26));
s->SetAt(11, v7810);
auto v7811 = Get(s->LocalAt(18), Value("private"));
s->SetAt(28, v7811);
auto v7812 = Get(Attribute(Attribute(s->Global("_IMPL"), "chassis"), "players"), s->LocalAt(26));
s->SetAt(14, v7812);
if (static_cast<bool>(([&]() -> Value { auto v7813 = ([&]() -> Value { auto fn7815 = PrepareDictionaryGet(s->LocalAt(31)); Arguments args7816; args7816.Add(Value("day"), false); return CallDictionaryGet(c, fn7815, std::move(args7816)); }()); Value v7814; v7814 = s->LocalAt(9); if (!static_cast<bool>(Binary("NotEq", v7813, v7814))) return Value(false); v7813 = v7814; return Value(true); }()))) {
(void)([&]() -> Value { auto fn7817 = Attribute(s->LocalAt(31), "update"); Arguments args7818; args7818.Keyword("day", s->LocalAt(9)); args7818.Keyword("workers", ([&]() -> Value { auto dict7819 = Dict(); return dict7819; }())); args7818.Keyword("pending", Value{}); args7818.Keyword("placed", List({})); return Call(c, fn7817, std::move(args7818)); }());
}
for (const auto& item7820 : Iterate(Get(s->LocalAt(31), Value("placed")))) {
auto unpack7821 = Iterate(item7820);
ValidateUnpack(unpack7821, 2, false);
s->SetAt(39, unpack7821.at(0));
s->SetAt(40, unpack7821.at(1));
auto v7822 = Get(Get(Get(s->LocalAt(11), Value("tiles")), s->LocalAt(40)), s->LocalAt(39));
s->SetAt(35, v7822);
if (static_cast<bool>(([&]() -> Value { auto v7823 = ([&]() -> Value { auto fn7824 = s->Global("isinstance"); Arguments args7825; args7825.positional.reserve(2); args7825.Add(s->LocalAt(35), false); args7825.Add(s->Global("dict"), false); return Call(c, fn7824, std::move(args7825)); }()); if (!static_cast<bool>(v7823)) return v7823; v7823 = ([&]() -> Value { auto v7826 = ([&]() -> Value { auto fn7828 = PrepareDictionaryGet(s->LocalAt(35)); Arguments args7829; args7829.positional.reserve(2); args7829.Add(Value("fertilized_until_day"), false); args7829.Add(Unary("USub", Value(int64_t{1})), false); return CallDictionaryGet(c, fn7828, std::move(args7829)); }()); Value v7827; v7827 = ([&]() -> Value { auto v7830 = s->LocalAt(9); return Binary("Add", v7830, Value(int64_t{2})); }()); if (!static_cast<bool>(Binary("GtE", v7826, v7827))) return Value(false); v7826 = v7827; return Value(true); }()); return v7823; }()))) {
auto v7831 = s->Global("_R51_INPUT_REPORT");
auto v7832 = Value("input_confirmed_applications");
auto v7833 = Get(v7831, v7832);
Put(v7831, v7832, Inplace("Add", v7833, Value(int64_t{1})));
}
else {
auto v7834 = s->Global("_R51_INPUT_REPORT");
auto v7835 = Value("input_application_errors");
auto v7836 = Get(v7834, v7835);
Put(v7834, v7835, Inplace("Add", v7836, Value(int64_t{1})));
}
}
auto v7837 = List({});
Put(s->LocalAt(31), Value("placed"), v7837);
if (static_cast<bool>(([&]() -> Value { auto fn7838 = PrepareDictionaryGet(s->LocalAt(31)); Arguments args7839; args7839.Add(Value("pending"), false); return CallDictionaryGet(c, fn7838, std::move(args7839)); }()))) {
auto v7840 = ([&]() -> Value { auto fn7841 = Attribute(s->LocalAt(31), "pop"); Arguments args7842; args7842.Add(Value("pending"), false); return Call(c, fn7841, std::move(args7842)); }());
s->SetAt(22, v7840);
for (const auto& item7843 : Iterate(([&]() -> Value { auto fn7844 = Attribute(s->LocalAt(22), "items"); Arguments args7845; return Call(c, fn7844, std::move(args7845)); }()))) {
auto unpack7846 = Iterate(item7843);
ValidateUnpack(unpack7846, 2, false);
s->SetAt(1, unpack7846.at(0));
s->SetAt(23, unpack7846.at(1));
if (static_cast<bool>(([&]() -> Value { auto v7847 = ([&]() -> Value { auto fn7849 = s->Global("len"); Arguments args7850; args7850.Add(Get(s->LocalAt(11), Value("hands")), false); return Call(c, fn7849, std::move(args7850)); }()); Value v7848; v7848 = s->LocalAt(1); if (!static_cast<bool>(Binary("GtE", v7847, v7848))) return Value(false); v7847 = v7848; return Value(true); }()))) {
auto v7851 = s->LocalAt(23);
Put(Get(s->LocalAt(31), Value("workers")), s->LocalAt(1), v7851);
auto v7852 = s->Global("_R51_INPUT_REPORT");
auto v7853 = Value("input_confirmed_hires");
auto v7854 = Get(v7852, v7853);
Put(v7852, v7853, Inplace("Add", v7854, Value(int64_t{1})));
}
else {
auto v7855 = s->Global("_R51_INPUT_REPORT");
auto v7856 = Value("input_hire_errors");
auto v7857 = Get(v7855, v7856);
Put(v7855, v7856, Inplace("Add", v7857, Value(int64_t{1})));
}
}
}
if (static_cast<bool>(Get(s->LocalAt(31), Value("workers")))) {
auto v7858 = ([&]() -> Value { auto fn7859 = Attribute(s->Global("copy"), "deepcopy"); Arguments args7860; args7860.Add(s->LocalAt(0), false); return Call(c, fn7859, std::move(args7860)); }());
s->SetAt(6, v7858);
for (const auto& item7861 : Iterate(([&]() -> Value { auto fn7862 = Attribute(Get(s->LocalAt(31), Value("workers")), "items"); Arguments args7863; return Call(c, fn7862, std::move(args7863)); }()))) {
auto unpack7864 = Iterate(item7861);
ValidateUnpack(unpack7864, 2, false);
s->SetAt(1, unpack7864.at(0));
s->SetAt(23, unpack7864.at(1));
auto v7865 = Get(Get(s->LocalAt(28), Value("inventories")), s->LocalAt(1));
s->SetAt(13, v7865);
auto v7866 = ([&]() -> Value { auto fn7867 = s->Global("tuple"); Arguments args7868; args7868.Add(Get(Get(s->LocalAt(11), Value("hands")), ([&]() -> Value { auto v7869 = s->LocalAt(1); return Binary("Sub", v7869, Value(int64_t{1})); }())), false); return Call(c, fn7867, std::move(args7868)); }());
s->SetAt(27, v7866);
auto v7870 = List({Value("PASS")});
s->SetAt(7, v7870);
if (static_cast<bool>(Unary("Not", Get(s->LocalAt(23), Value("loaded"))))) {
auto v7871 = ([&]() -> Value { auto fn7872 = s->Global("projected_shed"); Arguments args7873; args7873.positional.reserve(2); args7873.Add(s->LocalAt(6), false); args7873.Add(([&]() -> Value { auto fn7874 = s->Global("FarmView"); Arguments args7875; args7875.Add(s->LocalAt(18), false); return Call(c, fn7874, std::move(args7875)); }()), false); return Call(c, fn7872, std::move(args7873)); }());
s->SetAt(33, v7871);
auto v7876 = ([&]() -> Value { auto fn7877 = s->Global("min"); Arguments args7878; args7878.positional.reserve(2); args7878.Add(Get(s->LocalAt(23), Value("quantity")), false); args7878.Add(([&]() -> Value { auto fn7879 = s->Global("max"); Arguments args7880; args7880.positional.reserve(2); args7880.Add(Value(int64_t{0}), false); args7880.Add(([&]() -> Value { auto fn7881 = PrepareDictionaryGet(s->LocalAt(33)); Arguments args7882; args7882.positional.reserve(2); args7882.Add(Value("FERTILIZER"), false); args7882.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn7881, std::move(args7882)); }()), false); return Call(c, fn7879, std::move(args7880)); }()), false); return Call(c, fn7877, std::move(args7878)); }());
s->SetAt(30, v7876);
if (static_cast<bool>(([&]() -> Value { auto v7883 = s->LocalAt(30); if (!static_cast<bool>(v7883)) return v7883; v7883 = ([&]() -> Value { auto fn7884 = s->Global("_shed_adjacent"); Arguments args7885; args7885.positional.reserve(2); args7885.Add(s->LocalAt(27), false); args7885.Add(Value(int64_t{10}), false); return Call(c, fn7884, std::move(args7885)); }()); return v7883; }()))) {
auto v7886 = List({Value("PICKUP"), Value("FERTILIZER"), s->LocalAt(30)});
s->SetAt(7, v7886);
auto v7887 = Value(true);
Put(s->LocalAt(23), Value("loaded"), v7887);
auto v7888 = s->Global("_R51_INPUT_REPORT");
auto v7889 = Value("input_loaded_units");
auto v7890 = Get(v7888, v7889);
Put(v7888, v7889, Inplace("Add", v7890, s->LocalAt(30)));
if (static_cast<bool>(([&]() -> Value { auto v7891 = s->LocalAt(30); Value v7892; v7892 = Get(s->LocalAt(23), Value("quantity")); if (!static_cast<bool>(Binary("Lt", v7891, v7892))) return Value(false); v7891 = v7892; return Value(true); }()))) {
auto v7893 = s->Global("_R51_INPUT_REPORT");
auto v7894 = Value("input_stock_shortfalls");
auto v7895 = Get(v7893, v7894);
Put(v7893, v7894, Inplace("Add", v7895, ([&]() -> Value { auto v7896 = Get(s->LocalAt(23), Value("quantity")); return Binary("Sub", v7896, s->LocalAt(30)); }())));
}
}
}
else {
if (static_cast<bool>(([&]() -> Value { auto fn7897 = PrepareDictionaryGet(s->LocalAt(13)); Arguments args7898; args7898.positional.reserve(2); args7898.Add(Value("FERTILIZER"), false); args7898.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn7897, std::move(args7898)); }()))) {
while (static_cast<bool>(Get(s->LocalAt(23), Value("path")))) {
auto v7899 = Get(Get(s->LocalAt(23), Value("path")), Value(int64_t{0}));
auto unpack7900 = Iterate(v7899);
ValidateUnpack(unpack7900, 4, false);
s->SetAt(39, unpack7900.at(0));
s->SetAt(40, unpack7900.at(1));
s->SetAt(8, unpack7900.at(2));
s->SetAt(5, unpack7900.at(3));
auto v7901 = Get(Get(Get(s->LocalAt(11), Value("tiles")), s->LocalAt(40)), s->LocalAt(39));
s->SetAt(35, v7901);
if (static_cast<bool>(([&]() -> Value { auto v7902 = Unary("Not", ([&]() -> Value { auto fn7903 = s->Global("isinstance"); Arguments args7904; args7904.positional.reserve(2); args7904.Add(s->LocalAt(35), false); args7904.Add(s->Global("dict"), false); return Call(c, fn7903, std::move(args7904)); }())); if (static_cast<bool>(v7902)) return v7902; v7902 = ([&]() -> Value { auto v7905 = ([&]() -> Value { auto fn7907 = PrepareDictionaryGet(s->LocalAt(35)); Arguments args7908; args7908.Add(Value("crop"), false); return CallDictionaryGet(c, fn7907, std::move(args7908)); }()); Value v7906; v7906 = s->LocalAt(8); if (!static_cast<bool>(Binary("NotEq", v7905, v7906))) return Value(false); v7905 = v7906; return Value(true); }()); if (static_cast<bool>(v7902)) return v7902; v7902 = ([&]() -> Value { auto v7909 = ([&]() -> Value { auto fn7911 = PrepareDictionaryGet(s->LocalAt(35)); Arguments args7912; args7912.Add(Value("planted_day"), false); return CallDictionaryGet(c, fn7911, std::move(args7912)); }()); Value v7910; v7910 = s->LocalAt(5); if (!static_cast<bool>(Binary("NotEq", v7909, v7910))) return Value(false); v7909 = v7910; return Value(true); }()); if (static_cast<bool>(v7902)) return v7902; v7902 = ([&]() -> Value { auto v7913 = ([&]() -> Value { auto fn7915 = PrepareDictionaryGet(s->LocalAt(35)); Arguments args7916; args7916.positional.reserve(2); args7916.Add(Value("fertilized_until_day"), false); args7916.Add(Unary("USub", Value(int64_t{1})), false); return CallDictionaryGet(c, fn7915, std::move(args7916)); }()); Value v7914; v7914 = ([&]() -> Value { auto v7917 = s->LocalAt(9); return Binary("Add", v7917, Value(int64_t{2})); }()); if (!static_cast<bool>(Binary("GtE", v7913, v7914))) return Value(false); v7913 = v7914; return Value(true); }()); return v7902; }()))) {
(void)([&]() -> Value { auto fn7918 = Attribute(Get(s->LocalAt(23), Value("path")), "pop"); Arguments args7919; args7919.Add(Value(int64_t{0}), false); return Call(c, fn7918, std::move(args7919)); }());
continue;
}
auto v7920 = ([&]() -> Value { auto v7921 = ([&]() -> Value { auto fn7922 = s->Global("_v219_walk"); Arguments args7923; args7923.positional.reserve(2); args7923.Add(s->LocalAt(27), false); args7923.Add(Tuple({s->LocalAt(39), s->LocalAt(40)}), false); return Call(c, fn7922, std::move(args7923)); }()); if (static_cast<bool>(v7921)) return v7921; v7921 = List({Value("FERTILIZE")}); return v7921; }());
s->SetAt(7, v7920);
if (static_cast<bool>(([&]() -> Value { auto v7924 = s->LocalAt(7); Value v7925; v7925 = List({Value("FERTILIZE")}); if (!static_cast<bool>(Binary("Eq", v7924, v7925))) return Value(false); v7924 = v7925; return Value(true); }()))) {
(void)([&]() -> Value { auto fn7926 = Attribute(Get(s->LocalAt(31), Value("placed")), "append"); Arguments args7927; args7927.Add(Tuple({s->LocalAt(39), s->LocalAt(40)}), false); return Call(c, fn7926, std::move(args7927)); }());
(void)([&]() -> Value { auto fn7928 = Attribute(Get(s->LocalAt(23), Value("path")), "pop"); Arguments args7929; args7929.Add(Value(int64_t{0}), false); return Call(c, fn7928, std::move(args7929)); }());
auto v7930 = s->Global("_R51_INPUT_REPORT");
auto v7931 = Value("input_application_requests");
auto v7932 = Get(v7930, v7931);
Put(v7930, v7931, Inplace("Add", v7932, Value(int64_t{1})));
}
break;
}
}
}
auto v7933 = s->LocalAt(7);
Put(Get(s->LocalAt(6), Value("hands")), ([&]() -> Value { auto v7934 = s->LocalAt(1); return Binary("Sub", v7934, Value(int64_t{1})); }()), v7933);
}
return s->LocalAt(6);
}
if (static_cast<bool>(([&]() -> Value { auto v7935 = ([&]() -> Value { auto v7936 = s->LocalAt(12); Value v7937; v7937 = Tuple({Value(int64_t{1}), Value(int64_t{2}), Value(int64_t{3})}); if (!static_cast<bool>(Binary("NotIn", v7936, v7937))) return Value(false); v7936 = v7937; return Value(true); }()); if (static_cast<bool>(v7935)) return v7935; v7935 = Unary("Not", ([&]() -> Value { auto v7938 = Value(int64_t{12}); Value v7939; v7939 = s->LocalAt(9); if (!static_cast<bool>(Binary("LtE", v7938, v7939))) return Value(false); v7938 = v7939; v7939 = Value(int64_t{28}); if (!static_cast<bool>(Binary("LtE", v7938, v7939))) return Value(false); v7938 = v7939; return Value(true); }())); return v7935; }()))) {
return s->LocalAt(0);
}
auto v7940 = ([&]() -> Value { auto fn7941 = s->Global("_v219_native_day"); Arguments args7942; args7942.positional.reserve(2); args7942.Add(s->LocalAt(14), false); args7942.Add(s->LocalAt(9), false); return Call(c, fn7941, std::move(args7942)); }());
s->SetAt(24, v7940);
auto v7943 = ([&]() -> Value { auto fn7944 = s->Global("max"); Arguments args7945; args7945.Add(([&]() -> Value { auto comp7946 = std::make_shared<Scope>(); comp7946->globals = s->globals; comp7946->parent = s; static constexpr const char* comp7946_names[] = {"a"}; comp7946->PrepareSlots(comp7946_names); auto result7947 = List(); for (const auto& item7948 : Iterate(s->LocalAt(24))) { comp7946->SetAt(0, item7948); result7947.node()->sequence.push_back(([&]() -> Value { auto fn7949 = comp7946->Global("len"); Arguments args7950; args7950.Add(([&]() -> Value { auto fn7951 = PrepareDictionaryGet(comp7946->LocalAt(0)); Arguments args7952; args7952.positional.reserve(2); args7952.Add(Value("hands"), false); args7952.Add(List({}), false); return CallDictionaryGet(c, fn7951, std::move(args7952)); }()), false); return Call(c, fn7949, std::move(args7950)); }())); } return result7947; }()), false); return Call(c, fn7944, std::move(args7945)); }());
s->SetAt(10, v7943);
if (static_cast<bool>(([&]() -> Value { auto v7953 = ([&]() -> Value { auto comp7954 = std::make_shared<Scope>(); comp7954->globals = s->globals; comp7954->parent = s; static constexpr const char* comp7954_names[] = {"a", "o"}; comp7954->PrepareSlots(comp7954_names); auto result7955 = List(); for (const auto& item7956 : Iterate(Slice(s->LocalAt(24), s->LocalAt(12), Value{}, Value{}))) { comp7954->SetAt(0, item7956); for (const auto& item7957 : Iterate(([&]() -> Value { auto fn7958 = PrepareDictionaryGet(comp7954->LocalAt(0)); Arguments args7959; args7959.positional.reserve(2); args7959.Add(Value("market"), false); args7959.Add(List({}), false); return CallDictionaryGet(c, fn7958, std::move(args7959)); }()))) { comp7954->SetAt(1, item7957); if (static_cast<bool>(([&]() -> Value { auto v7960 = comp7954->LocalAt(1); if (!static_cast<bool>(v7960)) return v7960; v7960 = ([&]() -> Value { auto v7961 = Get(comp7954->LocalAt(1), Value(int64_t{0})); Value v7962; v7962 = Value("HIRE"); if (!static_cast<bool>(Binary("Eq", v7961, v7962))) return Value(false); v7961 = v7962; return Value(true); }()); return v7960; }()))) return Value(true); } } return Value(false); }()); if (static_cast<bool>(v7953)) return v7953; v7953 = Get(s->LocalAt(14), Value("pending")); return v7953; }()))) {
return s->LocalAt(0);
}
auto v7963 = List({([&]() -> Value { auto fn7964 = PrepareDictionaryGet(s->Global("_V219_STATES")); Arguments args7965; args7965.positional.reserve(2); args7965.Add(s->LocalAt(26), false); args7965.Add(([&]() -> Value { auto dict7966 = Dict(); return dict7966; }()), false); return CallDictionaryGet(c, fn7964, std::move(args7965)); }()), ([&]() -> Value { auto fn7967 = PrepareDictionaryGet(s->Global("_V233_STATES")); Arguments args7968; args7968.positional.reserve(2); args7968.Add(s->LocalAt(26), false); args7968.Add(([&]() -> Value { auto dict7969 = Dict(); return dict7969; }()), false); return CallDictionaryGet(c, fn7967, std::move(args7968)); }())});
s->SetAt(21, v7963);
if (static_cast<bool>(([&]() -> Value { auto v7970 = ([&]() -> Value { auto v7971 = s->LocalAt(9); Value v7972; v7972 = Tuple({Value(int64_t{12}), Value(int64_t{18})}); if (!static_cast<bool>(Binary("In", v7971, v7972))) return Value(false); v7971 = v7972; return Value(true); }()); if (static_cast<bool>(v7970)) return v7970; v7970 = ([&]() -> Value { auto comp7973 = std::make_shared<Scope>(); comp7973->globals = s->globals; comp7973->parent = s; static constexpr const char* comp7973_names[] = {"p"}; comp7973->PrepareSlots(comp7973_names); auto result7974 = List(); for (const auto& item7975 : Iterate(s->LocalAt(21))) { comp7973->SetAt(0, item7975); if (static_cast<bool>(([&]() -> Value { auto v7976 = ([&]() -> Value { auto fn7977 = PrepareDictionaryGet(comp7973->LocalAt(0)); Arguments args7978; args7978.Add(Value("committed"), false); return CallDictionaryGet(c, fn7977, std::move(args7978)); }()); if (!static_cast<bool>(v7976)) return v7976; v7976 = ([&]() -> Value { auto v7979 = ([&]() -> Value { auto fn7981 = PrepareDictionaryGet(comp7973->LocalAt(0)); Arguments args7982; args7982.Add(Value("requested_day"), false); return CallDictionaryGet(c, fn7981, std::move(args7982)); }()); Value v7980; v7980 = comp7973->Captured("day"); if (!static_cast<bool>(Binary("NotEq", v7979, v7980))) return Value(false); v7979 = v7980; return Value(true); }()); return v7976; }()))) return Value(true); } return Value(false); }()); return v7970; }()))) {
return s->LocalAt(0);
}
if (static_cast<bool>(([&]() -> Value { auto v7983 = ([&]() -> Value { auto comp7984 = std::make_shared<Scope>(); comp7984->globals = s->globals; comp7984->parent = s; static constexpr const char* comp7984_names[] = {"p"}; comp7984->PrepareSlots(comp7984_names); auto result7985 = List(); for (const auto& item7986 : Iterate(s->LocalAt(21))) { comp7984->SetAt(0, item7986); if (static_cast<bool>(([&]() -> Value { auto fn7987 = PrepareDictionaryGet(comp7984->LocalAt(0)); Arguments args7988; args7988.Add(Value("pending"), false); return CallDictionaryGet(c, fn7987, std::move(args7988)); }()))) return Value(true); } return Value(false); }()); if (static_cast<bool>(v7983)) return v7983; v7983 = ([&]() -> Value { auto comp7989 = std::make_shared<Scope>(); comp7989->globals = s->globals; comp7989->parent = s; static constexpr const char* comp7989_names[] = {"o"}; comp7989->PrepareSlots(comp7989_names); auto result7990 = List(); for (const auto& item7991 : Iterate(([&]() -> Value { auto fn7992 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args7993; args7993.positional.reserve(2); args7993.Add(Value("market"), false); args7993.Add(List({}), false); return CallDictionaryGet(c, fn7992, std::move(args7993)); }()))) { comp7989->SetAt(0, item7991); if (static_cast<bool>(([&]() -> Value { auto v7994 = comp7989->LocalAt(0); if (!static_cast<bool>(v7994)) return v7994; v7994 = ([&]() -> Value { auto v7995 = Get(comp7989->LocalAt(0), Value(int64_t{0})); Value v7996; v7996 = Value("HIRE"); if (!static_cast<bool>(Binary("Eq", v7995, v7996))) return Value(false); v7995 = v7996; return Value(true); }()); return v7994; }()))) return Value(true); } return Value(false); }()); return v7983; }()))) {
return s->LocalAt(0);
}
auto v7997 = ([&]() -> Value { auto fn7998 = s->Global("set"); Arguments args7999; args7999.Add(([&]() -> Value { auto fn8000 = s->Global("range"); Arguments args8001; args8001.positional.reserve(2); args8001.Add(Value(int64_t{1}), false); args8001.Add(([&]() -> Value { auto v8002 = s->LocalAt(10); return Binary("Add", v8002, Value(int64_t{1})); }()), false); return Call(c, fn8000, std::move(args8001)); }()), false); return Call(c, fn7998, std::move(args7999)); }());
s->SetAt(19, v7997);
for (const auto& item8003 : Iterate(s->LocalAt(21))) {
s->SetAt(20, item8003);
auto v8004 = ([&]() -> Value { auto fn8005 = s->Global("set"); Arguments args8006; args8006.Add(([&]() -> Value { auto fn8007 = PrepareDictionaryGet(s->LocalAt(20)); Arguments args8008; args8008.positional.reserve(2); args8008.Add(Value("workers"), false); args8008.Add(([&]() -> Value { auto dict8009 = Dict(); return dict8009; }()), false); return CallDictionaryGet(c, fn8007, std::move(args8008)); }()), false); return Call(c, fn8005, std::move(args8006)); }());
s->SetAt(2, v8004);
if (static_cast<bool>(([&]() -> Value { auto v8010 = s->LocalAt(19); return Binary("BitAnd", v8010, s->LocalAt(2)); }()))) {
return s->LocalAt(0);
}
auto v8011 = s->LocalAt(19);
s->SetAt(19, Inplace("BitOr", v8011, s->LocalAt(2)));
}
if (static_cast<bool>(([&]() -> Value { auto v8012 = s->LocalAt(19); Value v8013; v8013 = ([&]() -> Value { auto fn8014 = s->Global("set"); Arguments args8015; args8015.Add(([&]() -> Value { auto fn8016 = s->Global("range"); Arguments args8017; args8017.positional.reserve(2); args8017.Add(Value(int64_t{1}), false); args8017.Add(([&]() -> Value { auto v8018 = ([&]() -> Value { auto fn8019 = s->Global("len"); Arguments args8020; args8020.Add(Get(s->LocalAt(11), Value("hands")), false); return Call(c, fn8019, std::move(args8020)); }()); return Binary("Add", v8018, Value(int64_t{1})); }()), false); return Call(c, fn8016, std::move(args8017)); }()), false); return Call(c, fn8014, std::move(args8015)); }()); if (!static_cast<bool>(Binary("NotEq", v8012, v8013))) return Value(false); v8012 = v8013; return Value(true); }()))) {
return s->LocalAt(0);
}
auto v8021 = ([&]() -> Value { auto fn8022 = s->Global("_r51_input_forecast"); Arguments args8023; args8023.positional.reserve(3); args8023.Add(s->LocalAt(18), false); args8023.Add(Get(s->LocalAt(14), Value("route")), false); args8023.Add(s->LocalAt(10), false); return Call(c, fn8022, std::move(args8023)); }());
s->SetAt(34, v8021);
auto v8024 = List({});
s->SetAt(25, v8024);
auto v8025 = Value(int64_t{0});
s->SetAt(38, v8025);
auto v8026 = Value(int64_t{0});
s->SetAt(37, v8026);
auto v8027 = ([&]() -> Value { auto dict8028 = Dict(); auto key8029 = Value("WHEAT"); Put(dict8028, key8029, Value(int64_t{0})); auto key8030 = Value("CARROT"); Put(dict8028, key8030, Value(int64_t{0})); return dict8028; }());
s->SetAt(3, v8027);
auto v8031 = ([&]() -> Value { auto fn8032 = s->Global("projected_shed"); Arguments args8033; args8033.positional.reserve(2); args8033.Add(s->LocalAt(0), false); args8033.Add(([&]() -> Value { auto fn8034 = s->Global("FarmView"); Arguments args8035; args8035.Add(s->LocalAt(18), false); return Call(c, fn8034, std::move(args8035)); }()), false); return Call(c, fn8032, std::move(args8033)); }());
s->SetAt(33, v8031);
auto v8036 = ([&]() -> Value { auto fn8037 = s->Global("sum"); Arguments args8038; args8038.Add(([&]() -> Value { auto comp8039 = std::make_shared<Scope>(); comp8039->globals = s->globals; comp8039->parent = s; static constexpr const char* comp8039_names[] = {"o"}; comp8039->PrepareSlots(comp8039_names); auto result8040 = List(); for (const auto& item8041 : Iterate(([&]() -> Value { auto fn8042 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args8043; args8043.positional.reserve(2); args8043.Add(Value("market"), false); args8043.Add(List({}), false); return CallDictionaryGet(c, fn8042, std::move(args8043)); }()))) { comp8039->SetAt(0, item8041); if (!static_cast<bool>(([&]() -> Value { auto v8044 = ([&]() -> Value { auto v8045 = ([&]() -> Value { auto fn8047 = comp8039->Global("len"); Arguments args8048; args8048.Add(comp8039->LocalAt(0), false); return Call(c, fn8047, std::move(args8048)); }()); Value v8046; v8046 = Value(int64_t{2}); if (!static_cast<bool>(Binary("Gt", v8045, v8046))) return Value(false); v8045 = v8046; return Value(true); }()); if (!static_cast<bool>(v8044)) return v8044; v8044 = ([&]() -> Value { auto v8049 = Get(comp8039->LocalAt(0), Value(int64_t{0})); Value v8050; v8050 = Tuple({Value("BUY_PRODUCT"), Value("BUY_ANIMAL")}); if (!static_cast<bool>(Binary("In", v8049, v8050))) return Value(false); v8049 = v8050; return Value(true); }()); return v8044; }()))) continue; result8040.node()->sequence.push_back(([&]() -> Value { auto fn8051 = comp8039->Global("max"); Arguments args8052; args8052.positional.reserve(2); args8052.Add(Value(int64_t{0}), false); args8052.Add(([&]() -> Value { auto fn8053 = comp8039->Global("int"); Arguments args8054; args8054.Add(Get(comp8039->LocalAt(0), Value(int64_t{2})), false); return Call(c, fn8053, std::move(args8054)); }()), false); return Call(c, fn8051, std::move(args8052)); }())); } return result8040; }()), false); return Call(c, fn8037, std::move(args8038)); }());
s->SetAt(29, v8036);
auto v8055 = ([&]() -> Value { auto fn8056 = s->Global("max"); Arguments args8057; args8057.positional.reserve(2); args8057.Add(Value(int64_t{0}), false); args8057.Add(([&]() -> Value { auto fn8058 = PrepareDictionaryGet(s->LocalAt(33)); Arguments args8059; args8059.positional.reserve(2); args8059.Add(Value("FERTILIZER"), false); args8059.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn8058, std::move(args8059)); }()), false); return Call(c, fn8056, std::move(args8057)); }());
s->SetAt(4, v8055);
for (const auto& item8060 : Iterate(([&]() -> Value { auto fn8061 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args8062; args8062.positional.reserve(2); args8062.Add(Value("market"), false); args8062.Add(List({}), false); return CallDictionaryGet(c, fn8061, std::move(args8062)); }()))) {
s->SetAt(17, item8060);
if (static_cast<bool>(([&]() -> Value { auto v8063 = ([&]() -> Value { auto v8064 = ([&]() -> Value { auto fn8066 = s->Global("len"); Arguments args8067; args8067.Add(s->LocalAt(17), false); return Call(c, fn8066, std::move(args8067)); }()); Value v8065; v8065 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v8064, v8065))) return Value(false); v8064 = v8065; return Value(true); }()); if (!static_cast<bool>(v8063)) return v8063; v8063 = ([&]() -> Value { auto v8068 = Slice(s->LocalAt(17), Value{}, Value(int64_t{2}), Value{}); Value v8069; v8069 = List({Value("SELL"), Value("FERTILIZER")}); if (!static_cast<bool>(Binary("Eq", v8068, v8069))) return Value(false); v8068 = v8069; return Value(true); }()); return v8063; }()))) {
auto v8070 = ([&]() -> Value { auto fn8071 = s->Global("max"); Arguments args8072; args8072.positional.reserve(2); args8072.Add(Value(int64_t{0}), false); args8072.Add(([&]() -> Value { auto v8073 = s->LocalAt(4); return Binary("Sub", v8073, ([&]() -> Value { auto fn8074 = s->Global("max"); Arguments args8075; args8075.positional.reserve(2); args8075.Add(Value(int64_t{0}), false); args8075.Add(([&]() -> Value { auto fn8076 = s->Global("int"); Arguments args8077; args8077.Add(Get(s->LocalAt(17), Value(int64_t{2})), false); return Call(c, fn8076, std::move(args8077)); }()), false); return Call(c, fn8074, std::move(args8075)); }())); }()), false); return Call(c, fn8071, std::move(args8072)); }());
s->SetAt(4, v8070);
}
else {
if (static_cast<bool>(([&]() -> Value { auto v8078 = ([&]() -> Value { auto v8079 = ([&]() -> Value { auto fn8081 = s->Global("len"); Arguments args8082; args8082.Add(s->LocalAt(17), false); return Call(c, fn8081, std::move(args8082)); }()); Value v8080; v8080 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v8079, v8080))) return Value(false); v8079 = v8080; return Value(true); }()); if (!static_cast<bool>(v8078)) return v8078; v8078 = ([&]() -> Value { auto v8083 = Slice(s->LocalAt(17), Value{}, Value(int64_t{2}), Value{}); Value v8084; v8084 = List({Value("BUY_PRODUCT"), Value("FERTILIZER")}); if (!static_cast<bool>(Binary("Eq", v8083, v8084))) return Value(false); v8083 = v8084; return Value(true); }()); return v8078; }()))) {
auto v8085 = s->LocalAt(4);
s->SetAt(4, Inplace("Add", v8085, ([&]() -> Value { auto fn8086 = s->Global("max"); Arguments args8087; args8087.positional.reserve(2); args8087.Add(Value(int64_t{0}), false); args8087.Add(([&]() -> Value { auto fn8088 = s->Global("int"); Arguments args8089; args8089.Add(Get(s->LocalAt(17), Value(int64_t{2})), false); return Call(c, fn8088, std::move(args8089)); }()), false); return Call(c, fn8086, std::move(args8087)); }())));
}
}
}
auto v8090 = Get(s->LocalAt(24), ([&]() -> Value { auto v8091 = s->LocalAt(12); return Binary("Add", v8091, Value(int64_t{1})); }()));
s->SetAt(16, v8090);
auto v8092 = ([&]() -> Value { auto fn8093 = s->Global("sum"); Arguments args8094; args8094.Add(([&]() -> Value { auto comp8095 = std::make_shared<Scope>(); comp8095->globals = s->globals; comp8095->parent = s; static constexpr const char* comp8095_names[] = {"c"}; comp8095->PrepareSlots(comp8095_names); auto result8096 = List(); for (const auto& item8097 : Iterate(([&]() -> Value { Arguments args8098; args8098.Add(([&]() -> Value { auto v8099 = ([&]() -> Value { auto fn8100 = PrepareDictionaryGet(s->LocalAt(16)); Arguments args8101; args8101.Add(Value("farmer"), false); return CallDictionaryGet(c, fn8100, std::move(args8101)); }()); if (static_cast<bool>(v8099)) return v8099; v8099 = List({Value("PASS")}); return v8099; }()), false); args8098.Add(([&]() -> Value { auto v8102 = ([&]() -> Value { auto fn8103 = PrepareDictionaryGet(s->LocalAt(16)); Arguments args8104; args8104.Add(Value("hands"), false); return CallDictionaryGet(c, fn8103, std::move(args8104)); }()); if (static_cast<bool>(v8102)) return v8102; v8102 = List({}); return v8102; }()), true); return List(std::move(args8098.positional)); }()))) { comp8095->SetAt(0, item8097); if (!static_cast<bool>(([&]() -> Value { auto v8105 = ([&]() -> Value { auto v8106 = ([&]() -> Value { auto fn8108 = comp8095->Global("len"); Arguments args8109; args8109.Add(comp8095->LocalAt(0), false); return Call(c, fn8108, std::move(args8109)); }()); Value v8107; v8107 = Value(int64_t{1}); if (!static_cast<bool>(Binary("Gt", v8106, v8107))) return Value(false); v8106 = v8107; return Value(true); }()); if (!static_cast<bool>(v8105)) return v8105; v8105 = ([&]() -> Value { auto v8110 = Slice(comp8095->LocalAt(0), Value{}, Value(int64_t{2}), Value{}); Value v8111; v8111 = List({Value("PICKUP"), Value("FERTILIZER")}); if (!static_cast<bool>(Binary("Eq", v8110, v8111))) return Value(false); v8110 = v8111; return Value(true); }()); return v8105; }()))) continue; result8096.node()->sequence.push_back(([&]() -> Value { auto fn8112 = comp8095->Global("max"); Arguments args8113; args8113.positional.reserve(2); args8113.Add(Value(int64_t{0}), false); args8113.Add((static_cast<bool>(([&]() -> Value { auto v8114 = ([&]() -> Value { auto fn8116 = comp8095->Global("len"); Arguments args8117; args8117.Add(comp8095->LocalAt(0), false); return Call(c, fn8116, std::move(args8117)); }()); Value v8115; v8115 = Value(int64_t{2}); if (!static_cast<bool>(Binary("Gt", v8114, v8115))) return Value(false); v8114 = v8115; return Value(true); }())) ? ([&]() -> Value { auto fn8118 = comp8095->Global("int"); Arguments args8119; args8119.Add(Get(comp8095->LocalAt(0), Value(int64_t{2})), false); return Call(c, fn8118, std::move(args8119)); }()) : Value(int64_t{1})), false); return Call(c, fn8112, std::move(args8113)); }())); } return result8096; }()), false); return Call(c, fn8093, std::move(args8094)); }());
s->SetAt(15, v8092);
auto v8120 = ([&]() -> Value { auto fn8121 = s->Global("max"); Arguments args8122; args8122.positional.reserve(2); args8122.Add(Value(int64_t{0}), false); args8122.Add(([&]() -> Value { auto v8123 = s->LocalAt(15); return Binary("Sub", v8123, s->LocalAt(4)); }()), false); return Call(c, fn8121, std::move(args8122)); }());
s->SetAt(36, v8120);
auto v8124 = ([&]() -> Value { auto fn8125 = s->Global("_r68_joint_plans"); Arguments args8126; args8126.positional.reserve(6); args8126.Add(s->LocalAt(18), false); args8126.Add(s->LocalAt(0), false); args8126.Add(s->LocalAt(34), false); args8126.Add(s->LocalAt(33), false); args8126.Add(s->LocalAt(29), false); args8126.Add(s->LocalAt(36), false); return Call(c, fn8125, std::move(args8126)); }());
auto unpack8127 = Iterate(v8124);
ValidateUnpack(unpack8127, 4, false);
s->SetAt(25, unpack8127.at(0));
s->SetAt(38, unpack8127.at(1));
s->SetAt(37, unpack8127.at(2));
s->SetAt(3, unpack8127.at(3));
if (static_cast<bool>(Unary("Not", s->LocalAt(25)))) {
return s->LocalAt(0);
}
auto v8128 = ([&]() -> Value { auto comp8129 = std::make_shared<Scope>(); comp8129->globals = s->globals; comp8129->parent = s; static constexpr const char* comp8129_names[] = {"i", "plan"}; comp8129->PrepareSlots(comp8129_names); auto result8130 = Dict(); for (const auto& item8131 : Iterate(([&]() -> Value { auto fn8132 = s->Global("enumerate"); Arguments args8133; args8133.Add(s->LocalAt(25), false); return Call(c, fn8132, std::move(args8133)); }()))) { auto unpack8134 = Iterate(item8131); ValidateUnpack(unpack8134, 2, false); comp8129->SetAt(0, unpack8134.at(0)); comp8129->SetAt(1, unpack8134.at(1)); Put(result8130, ([&]() -> Value { auto v8135 = ([&]() -> Value { auto v8136 = ([&]() -> Value { auto fn8137 = comp8129->Global("len"); Arguments args8138; args8138.Add(Get(comp8129->Captured("farm"), Value("hands")), false); return Call(c, fn8137, std::move(args8138)); }()); return Binary("Add", v8136, Value(int64_t{1})); }()); return Binary("Add", v8135, comp8129->LocalAt(0)); }()), comp8129->LocalAt(1)); } return result8130; }());
Put(s->LocalAt(31), Value("pending"), v8128);
auto v8139 = s->Global("_R51_INPUT_REPORT");
auto v8140 = Value("input_hire_requests");
auto v8141 = Get(v8139, v8140);
Put(v8139, v8140, Inplace("Add", v8141, ([&]() -> Value { auto fn8142 = s->Global("len"); Arguments args8143; args8143.Add(s->LocalAt(25), false); return Call(c, fn8142, std::move(args8143)); }())));
auto v8144 = s->Global("_R51_INPUT_REPORT");
auto v8145 = Value("input_purchase_requests");
auto v8146 = Get(v8144, v8145);
Put(v8144, v8145, Inplace("Add", v8146, ([&]() -> Value { auto v8147 = s->LocalAt(38); return Binary("Add", v8147, s->LocalAt(36)); }())));
auto v8148 = s->Global("_R51_INPUT_REPORT");
auto v8149 = Value("input_forecast_wheat");
auto v8150 = Get(v8148, v8149);
Put(v8148, v8149, Inplace("Add", v8150, Get(s->LocalAt(3), Value("WHEAT"))));
auto v8151 = s->Global("_R51_INPUT_REPORT");
auto v8152 = Value("input_forecast_carrot");
auto v8153 = Get(v8151, v8152);
Put(v8151, v8152, Inplace("Add", v8153, Get(s->LocalAt(3), Value("CARROT"))));
auto v8154 = ([&]() -> Value { auto fn8155 = Attribute(s->Global("copy"), "deepcopy"); Arguments args8156; args8156.Add(s->LocalAt(0), false); return Call(c, fn8155, std::move(args8156)); }());
s->SetAt(6, v8154);
auto v8157 = s->LocalAt(6);
auto v8158 = Value("market");
auto v8159 = Get(v8157, v8158);
Put(v8157, v8158, Inplace("Add", v8159, ([&]() -> Value { auto v8160 = List({List({Value("BUY_PRODUCT"), Value("FERTILIZER"), ([&]() -> Value { auto v8161 = s->LocalAt(38); return Binary("Add", v8161, s->LocalAt(36)); }())})}); return Binary("Add", v8160, ([&]() -> Value { auto comp8162 = std::make_shared<Scope>(); comp8162->globals = s->globals; comp8162->parent = s; static constexpr const char* comp8162_names[] = {"_"}; comp8162->PrepareSlots(comp8162_names); auto result8163 = List(); for (const auto& item8164 : Iterate(s->LocalAt(25))) { comp8162->SetAt(0, item8164); result8163.node()->sequence.push_back(List({Value("HIRE")})); } return result8163; }())); }())));
return s->LocalAt(6);
return {};
}
}  // namespace kagg::opponents::compiled
