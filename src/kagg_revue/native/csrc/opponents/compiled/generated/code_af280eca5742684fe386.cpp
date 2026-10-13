// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_af280eca5742684fe386(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "h", "obs", "player", "saved"};
s->PrepareSlots(s_names);
auto v13094 = ([&]() -> Value { auto fn13095 = s->Global("int"); Arguments args13096; args13096.Add(Get(s->LocalAt(2), Value("player")), false); return Call(c, fn13095, std::move(args13096)); }());
s->SetAt(3, v13094);
auto v13097 = ([&]() -> Value { auto fn13098 = PrepareDictionaryGet(([&]() -> Value { auto fn13100 = PrepareDictionaryGet(s->Global("_RACE_STATE")); Arguments args13101; args13101.positional.reserve(2); args13101.Add(s->LocalAt(3), false); args13101.Add(([&]() -> Value { auto dict13102 = Dict(); return dict13102; }()), false); return CallDictionaryGet(c, fn13100, std::move(args13101)); }())); Arguments args13099; args13099.positional.reserve(2); args13099.Add(Value("horizon"), false); args13099.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn13098, std::move(args13099)); }());
s->SetAt(1, v13097);
if (static_cast<bool>(([&]() -> Value { auto v13103 = s->LocalAt(1); Value v13104; v13104 = ([&]() -> Value { auto fn13105 = PrepareDictionaryGet(s->Global("_R37_HORIZONS")); Arguments args13106; args13106.positional.reserve(2); args13106.Add(s->LocalAt(3), false); args13106.Add(Value(int64_t{2}), false); return CallDictionaryGet(c, fn13105, std::move(args13106)); }()); if (!static_cast<bool>(Binary("Gt", v13103, v13104))) return Value(false); v13103 = v13104; return Value(true); }()))) {
auto v13107 = ([&]() -> Value { auto fn13108 = PrepareDictionaryGet(s->Global("_R37_HORIZONS")); Arguments args13109; args13109.Add(s->LocalAt(3), false); return CallDictionaryGet(c, fn13108, std::move(args13109)); }());
s->SetAt(4, v13107);
auto v13110 = s->LocalAt(1);
Put(s->Global("_R37_HORIZONS"), s->LocalAt(3), v13110);
{
Value returned13111;
try {
returned13111 = ([&]() -> Value { auto fn13112 = s->Global("_RACE_ORIG_RESERVE"); Arguments args13113; args13113.positional.reserve(2); args13113.Add(s->LocalAt(2), false); args13113.Add(s->LocalAt(0), false); return Call(c, fn13112, std::move(args13113)); }());
} catch (...) {
if (static_cast<bool>(([&]() -> Value { auto v13114 = s->LocalAt(4); Value v13115; v13115 = Value{}; if (!static_cast<bool>(Binary("Is", v13114, v13115))) return Value(false); v13114 = v13115; return Value(true); }()))) {
(void)([&]() -> Value { auto fn13116 = Attribute(s->Global("_R37_HORIZONS"), "pop"); Arguments args13117; args13117.positional.reserve(2); args13117.Add(s->LocalAt(3), false); args13117.Add(Value{}, false); return Call(c, fn13116, std::move(args13117)); }());
}
else {
auto v13118 = s->LocalAt(4);
Put(s->Global("_R37_HORIZONS"), s->LocalAt(3), v13118);
}
throw;
}
if (static_cast<bool>(([&]() -> Value { auto v13119 = s->LocalAt(4); Value v13120; v13120 = Value{}; if (!static_cast<bool>(Binary("Is", v13119, v13120))) return Value(false); v13119 = v13120; return Value(true); }()))) {
(void)([&]() -> Value { auto fn13121 = Attribute(s->Global("_R37_HORIZONS"), "pop"); Arguments args13122; args13122.positional.reserve(2); args13122.Add(s->LocalAt(3), false); args13122.Add(Value{}, false); return Call(c, fn13121, std::move(args13122)); }());
}
else {
auto v13123 = s->LocalAt(4);
Put(s->Global("_R37_HORIZONS"), s->LocalAt(3), v13123);
}
return returned13111;
}
}
return ([&]() -> Value { auto fn13124 = s->Global("_RACE_ORIG_RESERVE"); Arguments args13125; args13125.positional.reserve(2); args13125.Add(s->LocalAt(2), false); args13125.Add(s->LocalAt(0), false); return Call(c, fn13124, std::move(args13125)); }());
return {};
}
}  // namespace kagg::opponents::compiled
