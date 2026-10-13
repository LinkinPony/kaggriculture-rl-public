// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_21105331f7dc4e896a77(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"day", "farm", "keep", "obs", "st", "tile", "x", "y"};
s->PrepareSlots(s_names);
auto v24920 = Get(Get(s->LocalAt(3), Value("farms")), ([&]() -> Value { auto fn24921 = s->Global("int"); Arguments args24922; args24922.Add(Get(s->LocalAt(3), Value("player")), false); return Call(c, fn24921, std::move(args24922)); }()));
s->SetAt(1, v24920);
auto v24923 = List({});
s->SetAt(2, v24923);
for (const auto& item24924 : Iterate(Get(s->LocalAt(4), Value("pending")))) {
auto unpack24925 = Iterate(item24924);
ValidateUnpack(unpack24925, 3, false);
s->SetAt(6, unpack24925.at(0));
s->SetAt(7, unpack24925.at(1));
s->SetAt(0, unpack24925.at(2));
auto v24926 = Get(Get(Get(s->LocalAt(1), Value("tiles")), s->LocalAt(7)), s->LocalAt(6));
s->SetAt(5, v24926);
if (static_cast<bool>(([&]() -> Value { auto v24927 = ([&]() -> Value { auto fn24928 = s->Global("isinstance"); Arguments args24929; args24929.positional.reserve(2); args24929.Add(s->LocalAt(5), false); args24929.Add(s->Global("dict"), false); return Call(c, fn24928, std::move(args24929)); }()); if (!static_cast<bool>(v24927)) return v24927; v24927 = ([&]() -> Value { auto v24930 = ([&]() -> Value { auto fn24932 = PrepareDictionaryGet(s->LocalAt(5)); Arguments args24933; args24933.Add(Value("animal"), false); return CallDictionaryGet(c, fn24932, std::move(args24933)); }()); Value v24931; v24931 = Get(s->LocalAt(4), Value("mode")); if (!static_cast<bool>(Binary("Eq", v24930, v24931))) return Value(false); v24930 = v24931; return Value(true); }()); if (!static_cast<bool>(v24927)) return v24927; v24927 = ([&]() -> Value { auto v24934 = ([&]() -> Value { auto fn24936 = PrepareDictionaryGet(s->LocalAt(5)); Arguments args24937; args24937.Add(Value("placed_day"), false); return CallDictionaryGet(c, fn24936, std::move(args24937)); }()); Value v24935; v24935 = s->LocalAt(0); if (!static_cast<bool>(Binary("Eq", v24934, v24935))) return Value(false); v24934 = v24935; return Value(true); }()); return v24927; }()))) {
auto v24938 = s->LocalAt(0);
Put(Get(s->LocalAt(4), Value("sites")), Tuple({s->LocalAt(6), s->LocalAt(7)}), v24938);
}
else {
if (static_cast<bool>(([&]() -> Value { auto v24939 = ([&]() -> Value { auto v24941 = ([&]() -> Value { auto fn24942 = s->Global("int"); Arguments args24943; args24943.Add(Get(s->LocalAt(3), Value("step")), false); return Call(c, fn24942, std::move(args24943)); }()); return Binary("FloorDiv", v24941, Value(int64_t{24})); }()); Value v24940; v24940 = ([&]() -> Value { auto v24944 = s->LocalAt(0); return Binary("Add", v24944, Value(int64_t{1})); }()); if (!static_cast<bool>(Binary("LtE", v24939, v24940))) return Value(false); v24939 = v24940; return Value(true); }()))) {
(void)([&]() -> Value { auto fn24945 = Attribute(s->LocalAt(2), "append"); Arguments args24946; args24946.Add(Tuple({s->LocalAt(6), s->LocalAt(7), s->LocalAt(0)}), false); return Call(c, fn24945, std::move(args24946)); }());
}
}
}
auto v24947 = s->LocalAt(2);
Put(s->LocalAt(4), Value("pending"), v24947);
return {};
}
}  // namespace kagg::opponents::compiled
