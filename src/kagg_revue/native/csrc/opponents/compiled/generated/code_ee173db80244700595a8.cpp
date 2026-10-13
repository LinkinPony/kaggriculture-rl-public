// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_ee173db80244700595a8(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "configuration", "horizon", "n", "o", "observation", "own", "player", "st", "step", "stock"};
s->PrepareSlots(s_names);
auto v29925 = Tuple({([&]() -> Value { auto fn29926 = s->Global("int"); Arguments args29927; args29927.Add(Get(s->LocalAt(5), Value("player")), false); return Call(c, fn29926, std::move(args29927)); }()), ([&]() -> Value { auto fn29928 = s->Global("int"); Arguments args29929; args29929.Add(Get(s->LocalAt(5), Value("step")), false); return Call(c, fn29928, std::move(args29929)); }())});
auto unpack29930 = Iterate(v29925);
ValidateUnpack(unpack29930, 2, false);
s->SetAt(7, unpack29930.at(0));
s->SetAt(9, unpack29930.at(1));
auto v29931 = ([&]() -> Value { auto fn29932 = PrepareDictionaryGet(s->Global("_V9_RACE")); Arguments args29933; args29933.Add(s->LocalAt(7), false); return CallDictionaryGet(c, fn29932, std::move(args29933)); }());
s->SetAt(8, v29931);
if (static_cast<bool>(([&]() -> Value { auto v29934 = ([&]() -> Value { auto v29935 = s->LocalAt(8); Value v29936; v29936 = Value{}; if (!static_cast<bool>(Binary("Is", v29935, v29936))) return Value(false); v29935 = v29936; return Value(true); }()); if (static_cast<bool>(v29934)) return v29934; v29934 = ([&]() -> Value { auto v29937 = s->LocalAt(9); Value v29938; v29938 = Get(s->LocalAt(8), Value("step")); if (!static_cast<bool>(Binary("LtE", v29937, v29938))) return Value(false); v29937 = v29938; return Value(true); }()); return v29934; }()))) {
auto v29939 = ([&]() -> Value { auto dict29940 = Dict(); auto key29941 = Value("step"); Put(dict29940, key29941, Unary("USub", Value(int64_t{1}))); auto key29942 = Value("lead"); Put(dict29940, key29942, Unary("USub", s->Global("V9_RACE_MARGIN"))); auto key29943 = Value("prev"); Put(dict29940, key29943, Value{}); return dict29940; }());
s->SetAt(8, v29939);
Put(s->Global("_V9_RACE"), s->LocalAt(7), v29939);
if (static_cast<bool>(([&]() -> Value { auto v29944 = s->LocalAt(9); Value v29945; v29945 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v29944, v29945))) return Value(false); v29944 = v29945; return Value(true); }()))) {
(void)([&]() -> Value { auto fn29946 = Attribute(s->Global("_V9_RACE_REPORT"), "update"); Arguments args29947; args29947.Keyword("rival_sales", Value(int64_t{0})); args29947.Keyword("leads", Value(int64_t{0})); args29947.Keyword("race_errors", Value(int64_t{0})); return Call(c, fn29946, std::move(args29947)); }());
}
}
auto v29948 = s->LocalAt(9);
Put(s->LocalAt(8), Value("step"), v29948);
try {
(void)([&]() -> Value { auto fn29950 = s->Global("_v9_race_update"); Arguments args29951; args29951.positional.reserve(2); args29951.Add(s->LocalAt(5), false); args29951.Add(s->LocalAt(8), false); return Call(c, fn29950, std::move(args29951)); }());
auto v29952 = ([&]() -> Value { auto fn29953 = s->Global("min"); Arguments args29954; args29954.positional.reserve(2); args29954.Add(s->Global("V9_RACE_MAX"), false); args29954.Add(([&]() -> Value { auto fn29955 = s->Global("max"); Arguments args29956; args29956.positional.reserve(2); args29956.Add(s->Global("V9_RACE_DEFAULT"), false); args29956.Add(([&]() -> Value { auto v29957 = Get(s->LocalAt(8), Value("lead")); return Binary("Add", v29957, s->Global("V9_RACE_MARGIN")); }()), false); return Call(c, fn29955, std::move(args29956)); }()), false); return Call(c, fn29953, std::move(args29954)); }());
s->SetAt(2, v29952);
auto v29958 = ([&]() -> Value { auto fn29959 = Attribute(s->Global("dict"), "fromkeys"); Arguments args29960; args29960.positional.reserve(2); args29960.Add(s->Global("V9_RACE_ITEMS"), false); args29960.Add(s->LocalAt(2), false); return Call(c, fn29959, std::move(args29960)); }());
Put(s->Global("_V9_ITEM_HZ"), s->LocalAt(7), v29958);
} catch (const Error& error29949) {
if (Matches(error29949, s->Global("Exception"))) {
auto v29961 = s->Global("_V9_RACE_REPORT");
auto v29962 = Value("race_errors");
auto v29963 = Get(v29961, v29962);
Put(v29961, v29962, Inplace("Add", v29963, Value(int64_t{1})));
(void)([&]() -> Value { auto fn29964 = Attribute(s->Global("_V9_ITEM_HZ"), "pop"); Arguments args29965; args29965.positional.reserve(2); args29965.Add(s->LocalAt(7), false); args29965.Add(Value{}, false); return Call(c, fn29964, std::move(args29965)); }());
}
else { throw; }
}
auto v29966 = ([&]() -> Value { auto fn29967 = s->Global("_V9_RACE_PARENT"); Arguments args29968; args29968.positional.reserve(2); args29968.Add(s->LocalAt(5), false); args29968.Add(s->LocalAt(1), false); return Call(c, fn29967, std::move(args29968)); }());
s->SetAt(0, v29966);
try {
auto v29970 = ([&]() -> Value { auto fn29971 = s->Global("projected_shed"); Arguments args29972; args29972.positional.reserve(2); args29972.Add(s->LocalAt(0), false); args29972.Add(([&]() -> Value { auto fn29973 = s->Global("FarmView"); Arguments args29974; args29974.Add(s->LocalAt(5), false); return Call(c, fn29973, std::move(args29974)); }()), false); return Call(c, fn29971, std::move(args29972)); }());
s->SetAt(10, v29970);
auto v29975 = ([&]() -> Value { auto dict29976 = Dict(); return dict29976; }());
s->SetAt(6, v29975);
for (const auto& item29977 : Iterate(([&]() -> Value { auto v29978 = ([&]() -> Value { auto fn29979 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args29980; args29980.Add(Value("market"), false); return CallDictionaryGet(c, fn29979, std::move(args29980)); }()); if (static_cast<bool>(v29978)) return v29978; v29978 = List({}); return v29978; }()))) {
s->SetAt(4, item29977);
if (static_cast<bool>(([&]() -> Value { auto v29981 = s->LocalAt(4); if (!static_cast<bool>(v29981)) return v29981; v29981 = ([&]() -> Value { auto v29982 = Get(s->LocalAt(4), Value(int64_t{0})); Value v29983; v29983 = Value("SELL"); if (!static_cast<bool>(Binary("Eq", v29982, v29983))) return Value(false); v29982 = v29983; return Value(true); }()); if (!static_cast<bool>(v29981)) return v29981; v29981 = ([&]() -> Value { auto v29984 = ([&]() -> Value { auto fn29986 = s->Global("len"); Arguments args29987; args29987.Add(s->LocalAt(4), false); return Call(c, fn29986, std::move(args29987)); }()); Value v29985; v29985 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v29984, v29985))) return Value(false); v29984 = v29985; return Value(true); }()); if (!static_cast<bool>(v29981)) return v29981; v29981 = ([&]() -> Value { auto v29988 = Get(s->LocalAt(4), Value(int64_t{1})); Value v29989; v29989 = s->Global("V9_RACE_ITEMS"); if (!static_cast<bool>(Binary("In", v29988, v29989))) return Value(false); v29988 = v29989; return Value(true); }()); return v29981; }()))) {
auto v29990 = ([&]() -> Value { auto fn29991 = s->Global("min"); Arguments args29992; args29992.positional.reserve(2); args29992.Add(([&]() -> Value { auto fn29993 = s->Global("max"); Arguments args29994; args29994.positional.reserve(2); args29994.Add(Value(int64_t{0}), false); args29994.Add(([&]() -> Value { auto fn29995 = s->Global("int"); Arguments args29996; args29996.Add(Get(s->LocalAt(4), Value(int64_t{2})), false); return Call(c, fn29995, std::move(args29996)); }()), false); return Call(c, fn29993, std::move(args29994)); }()), false); args29992.Add(([&]() -> Value { auto fn29997 = s->Global("max"); Arguments args29998; args29998.positional.reserve(2); args29998.Add(Value(int64_t{0}), false); args29998.Add(([&]() -> Value { auto v29999 = ([&]() -> Value { auto fn30000 = PrepareDictionaryGet(s->LocalAt(10)); Arguments args30001; args30001.positional.reserve(2); args30001.Add(Get(s->LocalAt(4), Value(int64_t{1})), false); args30001.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn30000, std::move(args30001)); }()); return Binary("Sub", v29999, ([&]() -> Value { auto fn30002 = PrepareDictionaryGet(s->LocalAt(6)); Arguments args30003; args30003.positional.reserve(2); args30003.Add(Get(s->LocalAt(4), Value(int64_t{1})), false); args30003.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn30002, std::move(args30003)); }())); }()), false); return Call(c, fn29997, std::move(args29998)); }()), false); return Call(c, fn29991, std::move(args29992)); }());
s->SetAt(3, v29990);
auto v30004 = ([&]() -> Value { auto v30005 = ([&]() -> Value { auto fn30006 = PrepareDictionaryGet(s->LocalAt(6)); Arguments args30007; args30007.positional.reserve(2); args30007.Add(Get(s->LocalAt(4), Value(int64_t{1})), false); args30007.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn30006, std::move(args30007)); }()); return Binary("Add", v30005, s->LocalAt(3)); }());
Put(s->LocalAt(6), Get(s->LocalAt(4), Value(int64_t{1})), v30004);
}
}
auto v30008 = ([&]() -> Value { auto dict30009 = Dict(); auto key30010 = Value("step"); Put(dict30009, key30010, s->LocalAt(9)); auto key30011 = Value("inventory"); Put(dict30009, key30011, ([&]() -> Value { auto fn30012 = s->Global("dict"); Arguments args30013; args30013.Add(Get(Get(s->LocalAt(5), Value("market")), Value("inventory")), false); return Call(c, fn30012, std::move(args30013)); }())); auto key30014 = Value("prices"); Put(dict30009, key30014, ([&]() -> Value { auto fn30015 = s->Global("dict"); Arguments args30016; args30016.Add(Get(Get(s->LocalAt(5), Value("market")), Value("prices")), false); return Call(c, fn30015, std::move(args30016)); }())); auto key30017 = Value("own"); Put(dict30009, key30017, s->LocalAt(6)); auto key30018 = Value("left"); Put(dict30009, key30018, ([&]() -> Value { auto comp30019 = std::make_shared<Scope>(); comp30019->globals = s->globals; comp30019->parent = s; static constexpr const char* comp30019_names[] = {"item"}; comp30019->PrepareSlots(comp30019_names); auto result30020 = Dict(); for (const auto& item30021 : Iterate(s->Global("V9_RACE_ITEMS"))) { comp30019->SetAt(0, item30021); Put(result30020, comp30019->LocalAt(0), ([&]() -> Value { auto v30022 = ([&]() -> Value { auto fn30023 = PrepareDictionaryGet(comp30019->Captured("stock")); Arguments args30024; args30024.positional.reserve(2); args30024.Add(comp30019->LocalAt(0), false); args30024.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn30023, std::move(args30024)); }()); return Binary("Sub", v30022, ([&]() -> Value { auto fn30025 = PrepareDictionaryGet(comp30019->Captured("own")); Arguments args30026; args30026.positional.reserve(2); args30026.Add(comp30019->LocalAt(0), false); args30026.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn30025, std::move(args30026)); }())); }())); } return result30020; }())); auto key30027 = Value("shops"); Put(dict30009, key30027, ([&]() -> Value { auto fn30028 = s->Global("list"); Arguments args30029; args30029.Add(Get(Get(s->LocalAt(5), Value("town")), Value("unlocked_shops")), false); return Call(c, fn30028, std::move(args30029)); }())); return dict30009; }());
Put(s->LocalAt(8), Value("prev"), v30008);
} catch (const Error& error29969) {
if (Matches(error29969, s->Global("Exception"))) {
auto v30030 = s->Global("_V9_RACE_REPORT");
auto v30031 = Value("race_errors");
auto v30032 = Get(v30030, v30031);
Put(v30030, v30031, Inplace("Add", v30032, Value(int64_t{1})));
auto v30033 = Value{};
Put(s->LocalAt(8), Value("prev"), v30033);
}
else { throw; }
}
return s->LocalAt(0);
return {};
}
}  // namespace kagg::opponents::compiled
