// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_2f08282e8d999de60c5d(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"ev", "out", "path", "x"};
s->PrepareSlots(s_names);
if (static_cast<bool>(([&]() -> Value { auto v29430 = Value("streams"); Value v29431; v29431 = s->Global("_V92_Q_CACHE"); if (!static_cast<bool>(Binary("NotIn", v29430, v29431))) return Value(false); v29430 = v29431; return Value(true); }()))) {
auto v29432 = ([&]() -> Value { auto fn29433 = PrepareDictionaryGet(Attribute(s->Global("_v92_os"), "environ")); Arguments args29434; args29434.Add(Value("V92_SELL_LIB"), false); return CallDictionaryGet(c, fn29433, std::move(args29434)); }());
s->SetAt(2, v29432);
auto v29435 = List({});
s->SetAt(1, v29435);
if (static_cast<bool>(s->LocalAt(2))) {
for (const auto& item29436 : Iterate(([&]() -> Value { auto fn29437 = Attribute(s->Global("_v92_json"), "load"); Arguments args29438; args29438.Add(([&]() -> Value { auto fn29439 = s->Global("open"); Arguments args29440; args29440.Add(s->LocalAt(2), false); return Call(c, fn29439, std::move(args29440)); }()), false); return Call(c, fn29437, std::move(args29438)); }()))) {
s->SetAt(3, item29436);
auto v29441 = ([&]() -> Value { auto comp29442 = std::make_shared<Scope>(); comp29442->globals = s->globals; comp29442->parent = s; static constexpr const char* comp29442_names[] = {"i", "q", "t"}; comp29442->PrepareSlots(comp29442_names); auto result29443 = Dict(); for (const auto& item29444 : Iterate(Get(s->LocalAt(3), Value("ev")))) { auto unpack29445 = Iterate(item29444); ValidateUnpack(unpack29445, 3, false); comp29442->SetAt(2, unpack29445.at(0)); comp29442->SetAt(0, unpack29445.at(1)); comp29442->SetAt(1, unpack29445.at(2)); if (!static_cast<bool>(([&]() -> Value { auto v29446 = comp29442->LocalAt(0); Value v29447; v29447 = Value(int64_t{2}); if (!static_cast<bool>(Binary("LtE", v29446, v29447))) return Value(false); v29446 = v29447; return Value(true); }()))) continue; Put(result29443, Tuple({comp29442->LocalAt(2), comp29442->LocalAt(0)}), comp29442->LocalAt(1)); } return result29443; }());
s->SetAt(0, v29441);
if (static_cast<bool>(s->LocalAt(0))) {
(void)([&]() -> Value { auto fn29448 = Attribute(s->LocalAt(1), "append"); Arguments args29449; args29449.Add(Tuple({Get(s->LocalAt(3), Value("ep")), s->LocalAt(0)}), false); return Call(c, fn29448, std::move(args29449)); }());
}
}
}
auto v29450 = s->LocalAt(1);
Put(s->Global("_V92_Q_CACHE"), Value("streams"), v29450);
}
return Get(s->Global("_V92_Q_CACHE"), Value("streams"));
return {};
}
}  // namespace kagg::opponents::compiled
