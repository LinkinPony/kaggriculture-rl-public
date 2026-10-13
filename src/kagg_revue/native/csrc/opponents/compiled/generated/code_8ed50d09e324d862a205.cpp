// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_8ed50d09e324d862a205(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"before", "held", "inv", "item", "observation", "order", "pinv", "prev", "prev_action", "prices", "rival", "shed", "sold", "state", "step", "town"};
s->PrepareSlots(s_names);
auto v13004 = ([&]() -> Value { auto fn13005 = PrepareDictionaryGet(s->LocalAt(13)); Arguments args13006; args13006.Add(Value("prev"), false); return CallDictionaryGet(c, fn13005, std::move(args13006)); }());
s->SetAt(7, v13004);
auto v13007 = ([&]() -> Value { auto fn13008 = PrepareDictionaryGet(s->LocalAt(13)); Arguments args13009; args13009.Add(Value("prev_action"), false); return CallDictionaryGet(c, fn13008, std::move(args13009)); }());
s->SetAt(8, v13007);
if (static_cast<bool>(([&]() -> Value { auto v13010 = ([&]() -> Value { auto v13011 = s->LocalAt(7); Value v13012; v13012 = Value{}; if (!static_cast<bool>(Binary("Is", v13011, v13012))) return Value(false); v13011 = v13012; return Value(true); }()); if (static_cast<bool>(v13010)) return v13010; v13010 = ([&]() -> Value { auto v13013 = s->LocalAt(8); Value v13014; v13014 = Value{}; if (!static_cast<bool>(Binary("Is", v13013, v13014))) return Value(false); v13013 = v13014; return Value(true); }()); return v13010; }()))) {
return Value(false);
}
auto v13015 = ([&]() -> Value { auto fn13016 = s->Global("int"); Arguments args13017; args13017.Add(Get(s->LocalAt(4), Value("step")), false); return Call(c, fn13016, std::move(args13017)); }());
s->SetAt(14, v13015);
if (static_cast<bool>(([&]() -> Value { auto v13018 = ([&]() -> Value { auto v13019 = s->LocalAt(14); Value v13020; v13020 = ([&]() -> Value { auto v13021 = Get(s->LocalAt(7), Value("step")); return Binary("Add", v13021, Value(int64_t{1})); }()); if (!static_cast<bool>(Binary("NotEq", v13019, v13020))) return Value(false); v13019 = v13020; return Value(true); }()); if (static_cast<bool>(v13018)) return v13018; v13018 = ([&]() -> Value { auto v13022 = ([&]() -> Value { auto v13024 = s->LocalAt(14); return Binary("Mod", v13024, Value(int64_t{24})); }()); Value v13023; v13023 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v13022, v13023))) return Value(false); v13022 = v13023; return Value(true); }()); return v13018; }()))) {
return Value(false);
}
auto v13025 = Get(Get(s->LocalAt(4), Value("private")), Value("shed"));
s->SetAt(11, v13025);
auto v13026 = Get(Get(s->LocalAt(4), Value("market")), Value("inventory"));
s->SetAt(2, v13026);
auto v13027 = Get(s->LocalAt(7), Value("inventory"));
s->SetAt(6, v13027);
auto v13028 = Get(s->LocalAt(7), Value("prices"));
s->SetAt(9, v13028);
auto v13029 = ([&]() -> Value { auto fn13030 = s->Global("_race_town"); Arguments args13031; args13031.positional.reserve(2); args13031.Add(([&]() -> Value { auto v13032 = s->LocalAt(14); return Binary("Sub", v13032, Value(int64_t{1})); }()), false); args13031.Add(Get(s->LocalAt(7), Value("shops")), false); return Call(c, fn13030, std::move(args13031)); }());
s->SetAt(15, v13029);
auto v13033 = ([&]() -> Value { auto dict13034 = Dict(); return dict13034; }());
s->SetAt(12, v13033);
for (const auto& item13035 : Iterate(([&]() -> Value { auto fn13036 = PrepareDictionaryGet(s->LocalAt(8)); Arguments args13037; args13037.positional.reserve(2); args13037.Add(Value("market"), false); args13037.Add(List({}), false); return CallDictionaryGet(c, fn13036, std::move(args13037)); }()))) {
s->SetAt(5, item13035);
if (static_cast<bool>(([&]() -> Value { auto v13038 = ([&]() -> Value { auto v13039 = ([&]() -> Value { auto fn13041 = s->Global("len"); Arguments args13042; args13042.Add(s->LocalAt(5), false); return Call(c, fn13041, std::move(args13042)); }()); Value v13040; v13040 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v13039, v13040))) return Value(false); v13039 = v13040; return Value(true); }()); if (!static_cast<bool>(v13038)) return v13038; v13038 = ([&]() -> Value { auto v13043 = Get(s->LocalAt(5), Value(int64_t{0})); Value v13044; v13044 = Value("SELL"); if (!static_cast<bool>(Binary("Eq", v13043, v13044))) return Value(false); v13043 = v13044; return Value(true); }()); if (!static_cast<bool>(v13038)) return v13038; v13038 = ([&]() -> Value { auto v13045 = Get(s->LocalAt(5), Value(int64_t{1})); Value v13046; v13046 = s->Global("_RACE_ITEMS"); if (!static_cast<bool>(Binary("In", v13045, v13046))) return Value(false); v13045 = v13046; return Value(true); }()); return v13038; }()))) {
auto v13047 = Value(int64_t{1});
Put(s->LocalAt(12), Get(s->LocalAt(5), Value(int64_t{1})), v13047);
}
}
for (const auto& item13048 : Iterate(s->Global("_RACE_ITEMS"))) {
s->SetAt(3, item13048);
auto v13049 = ([&]() -> Value { auto fn13050 = s->Global("int"); Arguments args13051; args13051.Add(([&]() -> Value { auto fn13052 = PrepareDictionaryGet(s->LocalAt(11)); Arguments args13053; args13053.positional.reserve(2); args13053.Add(s->LocalAt(3), false); args13053.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn13052, std::move(args13053)); }()), false); return Call(c, fn13050, std::move(args13051)); }());
s->SetAt(1, v13049);
auto v13054 = ([&]() -> Value { auto fn13055 = s->Global("int"); Arguments args13056; args13056.Add(([&]() -> Value { auto fn13057 = PrepareDictionaryGet(Attribute(Get(s->LocalAt(7), Value("view")), "shed")); Arguments args13058; args13058.positional.reserve(2); args13058.Add(s->LocalAt(3), false); args13058.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn13057, std::move(args13058)); }()), false); return Call(c, fn13055, std::move(args13056)); }());
s->SetAt(0, v13054);
if (static_cast<bool>(([&]() -> Value { auto v13059 = ([&]() -> Value { auto v13060 = s->LocalAt(1); Value v13061; v13061 = s->LocalAt(0); if (!static_cast<bool>(Binary("LtE", v13060, v13061))) return Value(false); v13060 = v13061; return Value(true); }()); if (static_cast<bool>(v13059)) return v13059; v13059 = ([&]() -> Value { auto v13062 = s->LocalAt(3); Value v13063; v13063 = s->LocalAt(12); if (!static_cast<bool>(Binary("In", v13062, v13063))) return Value(false); v13062 = v13063; return Value(true); }()); if (static_cast<bool>(v13059)) return v13059; v13059 = ([&]() -> Value { auto v13064 = ([&]() -> Value { auto fn13066 = PrepareDictionaryGet(s->LocalAt(9)); Arguments args13067; args13067.positional.reserve(2); args13067.Add(s->LocalAt(3), false); args13067.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn13066, std::move(args13067)); }()); Value v13065; v13065 = Value(int64_t{1}); if (!static_cast<bool>(Binary("LtE", v13064, v13065))) return Value(false); v13064 = v13065; return Value(true); }()); return v13059; }()))) {
continue;
}
auto v13068 = ([&]() -> Value { auto v13069 = ([&]() -> Value { auto v13070 = ([&]() -> Value { auto fn13071 = s->Global("int"); Arguments args13072; args13072.Add(Get(s->LocalAt(2), s->LocalAt(3)), false); return Call(c, fn13071, std::move(args13072)); }()); return Binary("Sub", v13070, ([&]() -> Value { auto fn13073 = s->Global("int"); Arguments args13074; args13074.Add(Get(s->LocalAt(6), s->LocalAt(3)), false); return Call(c, fn13073, std::move(args13074)); }())); }()); return Binary("Add", v13069, ([&]() -> Value { auto fn13075 = PrepareDictionaryGet(s->LocalAt(15)); Arguments args13076; args13076.positional.reserve(2); args13076.Add(s->LocalAt(3), false); args13076.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn13075, std::move(args13076)); }())); }());
s->SetAt(10, v13068);
if (static_cast<bool>(([&]() -> Value { auto v13077 = s->LocalAt(10); Value v13078; v13078 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v13077, v13078))) return Value(false); v13077 = v13078; return Value(true); }()))) {
return Value(true);
}
}
return Value(false);
return {};
}
}  // namespace kagg::opponents::compiled
