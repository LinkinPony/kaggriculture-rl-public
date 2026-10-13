// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_074acee25ec1948ba8d0(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"animal", "d", "day_from", "out", "placed_day", "spec"};
s->PrepareSlots(s_names);
auto v24234 = Get(s->Global("_HD2_SPEC"), s->LocalAt(0));
s->SetAt(5, v24234);
auto v24235 = ([&]() -> Value { auto dict24236 = Dict(); return dict24236; }());
s->SetAt(3, v24235);
for (const auto& item24237 : Iterate(([&]() -> Value { auto fn24238 = s->Global("range"); Arguments args24239; args24239.positional.reserve(2); args24239.Add(([&]() -> Value { auto fn24240 = s->Global("max"); Arguments args24241; args24241.positional.reserve(2); args24241.Add(s->LocalAt(2), false); args24241.Add(([&]() -> Value { auto v24242 = s->LocalAt(4); return Binary("Add", v24242, Get(s->LocalAt(5), Value("first"))); }()), false); return Call(c, fn24240, std::move(args24241)); }()), false); args24239.Add(Value(int64_t{30}), false); return Call(c, fn24238, std::move(args24239)); }()))) {
s->SetAt(1, item24237);
if (static_cast<bool>(([&]() -> Value { auto v24243 = ([&]() -> Value { auto v24245 = ([&]() -> Value { auto v24246 = ([&]() -> Value { auto v24247 = s->LocalAt(1); return Binary("Sub", v24247, s->LocalAt(4)); }()); return Binary("Sub", v24246, Get(s->LocalAt(5), Value("first"))); }()); return Binary("Mod", v24245, Get(s->LocalAt(5), Value("interval"))); }()); Value v24244; v24244 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v24243, v24244))) return Value(false); v24243 = v24244; return Value(true); }()))) {
auto v24248 = ([&]() -> Value { auto v24249 = ([&]() -> Value { auto v24250 = ([&]() -> Value { auto fn24251 = PrepareDictionaryGet(s->LocalAt(3)); Arguments args24252; args24252.positional.reserve(2); args24252.Add(s->LocalAt(1), false); args24252.Add(Value(0.0), false); return CallDictionaryGet(c, fn24251, std::move(args24252)); }()); return Binary("Add", v24250, Value(1.0)); }()); return Binary("Add", v24249, ([&]() -> Value { auto v24253 = ([&]() -> Value { auto v24254 = Get(s->LocalAt(5), Value("per")); return Binary("Sub", v24254, Value(int64_t{1})); }()); return Binary("Mult", v24253, s->Global("_HD2_CARE")); }())); }());
Put(s->LocalAt(3), s->LocalAt(1), v24248);
}
}
return s->LocalAt(3);
return {};
}
}  // namespace kagg::opponents::compiled
