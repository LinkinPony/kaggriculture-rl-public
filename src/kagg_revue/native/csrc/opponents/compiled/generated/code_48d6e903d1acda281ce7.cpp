// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_48d6e903d1acda281ce7(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "configuration", "observation", "player", "st", "step"};
s->PrepareSlots(s_names);
auto v29385 = Tuple({([&]() -> Value { auto fn29386 = s->Global("int"); Arguments args29387; args29387.Add(Get(s->LocalAt(2), Value("player")), false); return Call(c, fn29386, std::move(args29387)); }()), ([&]() -> Value { auto fn29388 = s->Global("int"); Arguments args29389; args29389.Add(Get(s->LocalAt(2), Value("step")), false); return Call(c, fn29388, std::move(args29389)); }())});
auto unpack29390 = Iterate(v29385);
ValidateUnpack(unpack29390, 2, false);
s->SetAt(3, unpack29390.at(0));
s->SetAt(5, unpack29390.at(1));
auto v29391 = ([&]() -> Value { auto fn29392 = PrepareDictionaryGet(s->Global("_V92_P")); Arguments args29393; args29393.Add(s->LocalAt(3), false); return CallDictionaryGet(c, fn29392, std::move(args29393)); }());
s->SetAt(4, v29391);
if (static_cast<bool>(([&]() -> Value { auto v29394 = ([&]() -> Value { auto v29395 = s->LocalAt(4); Value v29396; v29396 = Value{}; if (!static_cast<bool>(Binary("Is", v29395, v29396))) return Value(false); v29395 = v29396; return Value(true); }()); if (static_cast<bool>(v29394)) return v29394; v29394 = ([&]() -> Value { auto v29397 = s->LocalAt(5); Value v29398; v29398 = Get(s->LocalAt(4), Value("step")); if (!static_cast<bool>(Binary("LtE", v29397, v29398))) return Value(false); v29397 = v29398; return Value(true); }()); return v29394; }()))) {
auto v29399 = ([&]() -> Value { auto dict29400 = Dict(); auto key29401 = Value("step"); Put(dict29400, key29401, Unary("USub", Value(int64_t{1}))); auto key29402 = Value("obs"); Put(dict29400, key29402, ([&]() -> Value { auto dict29403 = Dict(); return dict29403; }())); return dict29400; }());
s->SetAt(4, v29399);
Put(s->Global("_V92_P"), s->LocalAt(3), v29399);
}
auto v29404 = s->LocalAt(5);
Put(s->LocalAt(4), Value("step"), v29404);
auto v29405 = ([&]() -> Value { auto fn29406 = s->Global("_V92_P_PARENT"); Arguments args29407; args29407.positional.reserve(2); args29407.Add(s->LocalAt(2), false); args29407.Add(s->LocalAt(1), false); return Call(c, fn29406, std::move(args29407)); }());
s->SetAt(0, v29405);
try {
return ([&]() -> Value { auto fn29409 = s->Global("_v92_predict"); Arguments args29410; args29410.positional.reserve(3); args29410.Add(s->LocalAt(2), false); args29410.Add(s->LocalAt(0), false); args29410.Add(s->LocalAt(4), false); return Call(c, fn29409, std::move(args29410)); }());
} catch (const Error& error29408) {
if (Matches(error29408, s->Global("Exception"))) {
auto v29411 = s->Global("_V92_P_REPORT");
auto v29412 = Value("pred_errors");
auto v29413 = Get(v29411, v29412);
Put(v29411, v29412, Inplace("Add", v29413, Value(int64_t{1})));
return s->LocalAt(0);
}
else { throw; }
}
return {};
}
}  // namespace kagg::opponents::compiled
