// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_5cc805d33f89c4199cd3(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"a", "b", "farms", "matches", "observation", "own", "rival", "sa", "sb", "total"};
s->PrepareSlots(s_names);
auto v6222 = Get(s->LocalAt(4), Value("farms"));
s->SetAt(2, v6222);
auto v6223 = Tuple({Get(s->LocalAt(2), Get(s->LocalAt(4), Value("player"))), Get(s->LocalAt(2), ([&]() -> Value { auto v6224 = Value(int64_t{1}); return Binary("Sub", v6224, Get(s->LocalAt(4), Value("player"))); }()))});
auto unpack6225 = Iterate(v6223);
ValidateUnpack(unpack6225, 2, false);
s->SetAt(5, unpack6225.at(0));
s->SetAt(6, unpack6225.at(1));
if (static_cast<bool>(([&]() -> Value { auto v6226 = Get(s->LocalAt(5), Value("unlocked_quadrants")); Value v6227; v6227 = Get(s->LocalAt(6), Value("unlocked_quadrants")); if (!static_cast<bool>(Binary("NotEq", v6226, v6227))) return Value(false); v6226 = v6227; return Value(true); }()))) {
return Value(0.0);
}
auto v6228 = Value(int64_t{0});
s->SetAt(3, v6228);
s->SetAt(9, v6228);
for (const auto& item6229 : Iterate(([&]() -> Value { auto fn6230 = s->Global("zip"); Arguments args6231; args6231.positional.reserve(2); args6231.Add(([&]() -> Value { auto comp6232 = std::make_shared<Scope>(); comp6232->globals = s->globals; comp6232->parent = s; static constexpr const char* comp6232_names[] = {"row", "t"}; comp6232->PrepareSlots(comp6232_names); auto result6233 = List(); for (const auto& item6234 : Iterate(Get(s->LocalAt(5), Value("tiles")))) { comp6232->SetAt(0, item6234); for (const auto& item6235 : Iterate(comp6232->LocalAt(0))) { comp6232->SetAt(1, item6235); result6233.node()->sequence.push_back(comp6232->LocalAt(1)); } } return result6233; }()), false); args6231.Add(([&]() -> Value { auto comp6236 = std::make_shared<Scope>(); comp6236->globals = s->globals; comp6236->parent = s; static constexpr const char* comp6236_names[] = {"row", "t"}; comp6236->PrepareSlots(comp6236_names); auto result6237 = List(); for (const auto& item6238 : Iterate(Get(s->LocalAt(6), Value("tiles")))) { comp6236->SetAt(0, item6238); for (const auto& item6239 : Iterate(comp6236->LocalAt(0))) { comp6236->SetAt(1, item6239); result6237.node()->sequence.push_back(comp6236->LocalAt(1)); } } return result6237; }()), false); return Call(c, fn6230, std::move(args6231)); }()))) {
auto unpack6240 = Iterate(item6229);
ValidateUnpack(unpack6240, 2, false);
s->SetAt(0, unpack6240.at(0));
s->SetAt(1, unpack6240.at(1));
auto v6241 = (static_cast<bool>(([&]() -> Value { auto fn6242 = s->Global("isinstance"); Arguments args6243; args6243.positional.reserve(2); args6243.Add(s->LocalAt(0), false); args6243.Add(s->Global("dict"), false); return Call(c, fn6242, std::move(args6243)); }())) ? Tuple({([&]() -> Value { auto fn6244 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args6245; args6245.Add(Value("crop"), false); return CallDictionaryGet(c, fn6244, std::move(args6245)); }()), ([&]() -> Value { auto fn6246 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args6247; args6247.Add(Value("animal"), false); return CallDictionaryGet(c, fn6246, std::move(args6247)); }())}) : Tuple({Value{}, Value{}}));
s->SetAt(7, v6241);
auto v6248 = (static_cast<bool>(([&]() -> Value { auto fn6249 = s->Global("isinstance"); Arguments args6250; args6250.positional.reserve(2); args6250.Add(s->LocalAt(1), false); args6250.Add(s->Global("dict"), false); return Call(c, fn6249, std::move(args6250)); }())) ? Tuple({([&]() -> Value { auto fn6251 = PrepareDictionaryGet(s->LocalAt(1)); Arguments args6252; args6252.Add(Value("crop"), false); return CallDictionaryGet(c, fn6251, std::move(args6252)); }()), ([&]() -> Value { auto fn6253 = PrepareDictionaryGet(s->LocalAt(1)); Arguments args6254; args6254.Add(Value("animal"), false); return CallDictionaryGet(c, fn6253, std::move(args6254)); }())}) : Tuple({Value{}, Value{}}));
s->SetAt(8, v6248);
if (static_cast<bool>(([&]() -> Value { auto v6255 = ([&]() -> Value { auto v6256 = s->LocalAt(7); Value v6257; v6257 = Tuple({Value{}, Value{}}); if (!static_cast<bool>(Binary("NotEq", v6256, v6257))) return Value(false); v6256 = v6257; return Value(true); }()); if (static_cast<bool>(v6255)) return v6255; v6255 = ([&]() -> Value { auto v6258 = s->LocalAt(8); Value v6259; v6259 = Tuple({Value{}, Value{}}); if (!static_cast<bool>(Binary("NotEq", v6258, v6259))) return Value(false); v6258 = v6259; return Value(true); }()); return v6255; }()))) {
auto v6260 = s->LocalAt(9);
s->SetAt(9, Inplace("Add", v6260, Value(int64_t{1})));
auto v6261 = s->LocalAt(3);
s->SetAt(3, Inplace("Add", v6261, ([&]() -> Value { auto v6262 = s->LocalAt(7); Value v6263; v6263 = s->LocalAt(8); if (!static_cast<bool>(Binary("Eq", v6262, v6263))) return Value(false); v6262 = v6263; return Value(true); }())));
}
}
return (static_cast<bool>(([&]() -> Value { auto v6264 = s->LocalAt(9); Value v6265; v6265 = Value(int64_t{8}); if (!static_cast<bool>(Binary("GtE", v6264, v6265))) return Value(false); v6264 = v6265; return Value(true); }())) ? ([&]() -> Value { auto v6266 = s->LocalAt(3); return Binary("Div", v6266, s->LocalAt(9)); }()) : Value(0.0));
return {};
}
}  // namespace kagg::opponents::compiled
