// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_ece5e9e357e4e85b92a1(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"after", "before", "draw", "inventory", "item", "native", "obs", "planned", "prev", "sold", "st", "step", "t", "tape"};
s->PrepareSlots(s_names);
auto v29853 = Get(s->LocalAt(10), Value("prev"));
s->SetAt(8, v29853);
auto v29854 = ([&]() -> Value { auto fn29855 = s->Global("int"); Arguments args29856; args29856.Add(Get(s->LocalAt(6), Value("step")), false); return Call(c, fn29855, std::move(args29856)); }());
s->SetAt(11, v29854);
if (static_cast<bool>(([&]() -> Value { auto v29857 = Unary("Not", s->LocalAt(8)); if (static_cast<bool>(v29857)) return v29857; v29857 = ([&]() -> Value { auto v29858 = Get(s->LocalAt(8), Value("step")); Value v29859; v29859 = ([&]() -> Value { auto v29860 = s->LocalAt(11); return Binary("Sub", v29860, Value(int64_t{1})); }()); if (!static_cast<bool>(Binary("NotEq", v29858, v29859))) return Value(false); v29858 = v29859; return Value(true); }()); return v29857; }()))) {
return Value{};
}
auto v29861 = ([&]() -> Value { auto fn29862 = PrepareDictionaryGet(Attribute(Attribute(s->Global("_IMPL"), "chassis"), "players")); Arguments args29863; args29863.Add(([&]() -> Value { auto fn29864 = s->Global("int"); Arguments args29865; args29865.Add(Get(s->LocalAt(6), Value("player")), false); return Call(c, fn29864, std::move(args29865)); }()), false); return CallDictionaryGet(c, fn29862, std::move(args29863)); }());
s->SetAt(5, v29861);
if (static_cast<bool>(([&]() -> Value { auto v29866 = Unary("Not", s->LocalAt(5)); if (static_cast<bool>(v29866)) return v29866; v29866 = ([&]() -> Value { auto v29867 = ([&]() -> Value { auto fn29869 = PrepareDictionaryGet(s->LocalAt(5)); Arguments args29870; args29870.Add(Value("route"), false); return CallDictionaryGet(c, fn29869, std::move(args29870)); }()); Value v29868; v29868 = Attribute(Attribute(s->Global("_IMPL"), "chassis"), "routes"); if (!static_cast<bool>(Binary("NotIn", v29867, v29868))) return Value(false); v29867 = v29868; return Value(true); }()); return v29866; }()))) {
return Value{};
}
auto v29871 = Get(Attribute(Attribute(s->Global("_IMPL"), "chassis"), "routes"), Get(s->LocalAt(5), Value("route")));
s->SetAt(13, v29871);
auto v29872 = Get(Get(s->LocalAt(6), Value("market")), Value("inventory"));
s->SetAt(3, v29872);
auto v29873 = ([&]() -> Value { auto fn29874 = s->Global("_v9_town_draw"); Arguments args29875; args29875.positional.reserve(2); args29875.Add(Get(s->LocalAt(8), Value("shops")), false); args29875.Add(Get(s->LocalAt(8), Value("step")), false); return Call(c, fn29874, std::move(args29875)); }());
s->SetAt(2, v29873);
auto v29876 = Get(s->LocalAt(8), Value("step"));
s->SetAt(12, v29876);
for (const auto& item29877 : Iterate(s->Global("V9_RACE_ITEMS"))) {
s->SetAt(4, item29877);
if (static_cast<bool>(([&]() -> Value { auto v29878 = ([&]() -> Value { auto fn29880 = PrepareDictionaryGet(Get(s->LocalAt(8), Value("prices"))); Arguments args29881; args29881.positional.reserve(2); args29881.Add(s->LocalAt(4), false); args29881.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn29880, std::move(args29881)); }()); Value v29879; v29879 = Value(int64_t{3}); if (!static_cast<bool>(Binary("LtE", v29878, v29879))) return Value(false); v29878 = v29879; return Value(true); }()))) {
continue;
}
auto v29882 = ([&]() -> Value { auto v29883 = ([&]() -> Value { auto v29884 = ([&]() -> Value { auto v29885 = Get(s->LocalAt(3), s->LocalAt(4)); return Binary("Sub", v29885, Get(Get(s->LocalAt(8), Value("inventory")), s->LocalAt(4))); }()); return Binary("Add", v29884, Get(s->LocalAt(2), s->LocalAt(4))); }()); return Binary("Sub", v29883, ([&]() -> Value { auto fn29886 = PrepareDictionaryGet(Get(s->LocalAt(8), Value("own"))); Arguments args29887; args29887.positional.reserve(2); args29887.Add(s->LocalAt(4), false); args29887.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn29886, std::move(args29887)); }())); }());
s->SetAt(9, v29882);
if (static_cast<bool>(([&]() -> Value { auto v29888 = s->LocalAt(9); Value v29889; v29889 = Value(int64_t{2}); if (!static_cast<bool>(Binary("Lt", v29888, v29889))) return Value(false); v29888 = v29889; return Value(true); }()))) {
continue;
}
auto v29890 = s->Global("_V9_RACE_REPORT");
auto v29891 = Value("rival_sales");
auto v29892 = Get(v29890, v29891);
Put(v29890, v29891, Inplace("Add", v29892, Value(int64_t{1})));
if (static_cast<bool>(([&]() -> Value { auto v29893 = ([&]() -> Value { auto fn29895 = PrepareDictionaryGet(Get(s->LocalAt(8), Value("left"))); Arguments args29896; args29896.positional.reserve(2); args29896.Add(s->LocalAt(4), false); args29896.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn29895, std::move(args29896)); }()); Value v29894; v29894 = Value(int64_t{0}); if (!static_cast<bool>(Binary("LtE", v29893, v29894))) return Value(false); v29893 = v29894; return Value(true); }()))) {
continue;
}
auto v29897 = ([&]() -> Value { auto fn29898 = s->Global("_v9_planned_sells"); Arguments args29899; args29899.positional.reserve(3); args29899.Add(s->LocalAt(13), false); args29899.Add(s->LocalAt(4), false); args29899.Add(s->LocalAt(12), false); return Call(c, fn29898, std::move(args29899)); }());
s->SetAt(7, v29897);
auto v29900 = ([&]() -> Value { auto comp29901 = std::make_shared<Scope>(); comp29901->globals = s->globals; comp29901->parent = s; static constexpr const char* comp29901_names[] = {"s"}; comp29901->PrepareSlots(comp29901_names); auto result29902 = List(); for (const auto& item29903 : Iterate(s->LocalAt(7))) { comp29901->SetAt(0, item29903); if (!static_cast<bool>(([&]() -> Value { auto v29904 = comp29901->LocalAt(0); Value v29905; v29905 = comp29901->Captured("t"); if (!static_cast<bool>(Binary("GtE", v29904, v29905))) return Value(false); v29904 = v29905; return Value(true); }()))) continue; result29902.node()->sequence.push_back(comp29901->LocalAt(0)); } return result29902; }());
s->SetAt(0, v29900);
auto v29906 = ([&]() -> Value { auto comp29907 = std::make_shared<Scope>(); comp29907->globals = s->globals; comp29907->parent = s; static constexpr const char* comp29907_names[] = {"s"}; comp29907->PrepareSlots(comp29907_names); auto result29908 = List(); for (const auto& item29909 : Iterate(s->LocalAt(7))) { comp29907->SetAt(0, item29909); if (!static_cast<bool>(([&]() -> Value { auto v29910 = comp29907->LocalAt(0); Value v29911; v29911 = comp29907->Captured("t"); if (!static_cast<bool>(Binary("Lt", v29910, v29911))) return Value(false); v29910 = v29911; return Value(true); }()))) continue; result29908.node()->sequence.push_back(comp29907->LocalAt(0)); } return result29908; }());
s->SetAt(1, v29906);
if (static_cast<bool>(([&]() -> Value { auto v29912 = Unary("Not", s->LocalAt(0)); if (static_cast<bool>(v29912)) return v29912; v29912 = ([&]() -> Value { auto v29913 = s->LocalAt(1); if (!static_cast<bool>(v29913)) return v29913; v29913 = ([&]() -> Value { auto v29914 = ([&]() -> Value { auto v29916 = s->LocalAt(12); return Binary("Sub", v29916, Get(s->LocalAt(1), Unary("USub", Value(int64_t{1})))); }()); Value v29915; v29915 = s->Global("V9_RACE_GAP"); if (!static_cast<bool>(Binary("Lt", v29914, v29915))) return Value(false); v29914 = v29915; return Value(true); }()); return v29913; }()); return v29912; }()))) {
continue;
}
auto v29917 = ([&]() -> Value { auto fn29918 = s->Global("max"); Arguments args29919; args29919.positional.reserve(2); args29919.Add(Get(s->LocalAt(10), Value("lead")), false); args29919.Add(([&]() -> Value { auto v29920 = Get(s->LocalAt(0), Value(int64_t{0})); return Binary("Sub", v29920, s->LocalAt(12)); }()), false); return Call(c, fn29918, std::move(args29919)); }());
Put(s->LocalAt(10), Value("lead"), v29917);
auto v29921 = s->Global("_V9_RACE_REPORT");
auto v29922 = Value("leads");
auto v29923 = Get(v29921, v29922);
Put(v29921, v29922, Inplace("Add", v29923, Value(int64_t{1})));
}
return {};
}
}  // namespace kagg::opponents::compiled
