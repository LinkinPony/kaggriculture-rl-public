// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_0fcb78f073ea469d3324(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"it"};
s->PrepareSlots(s_names);
return Tuple({([&]() -> Value { auto v1587 = ([&]() -> Value { auto fn1589 = Attribute(s->Captured("self"), "future_sells"); Arguments args1590; args1590.positional.reserve(3); args1590.Add(s->Captured("route"), false); args1590.Add(s->LocalAt(0), false); args1590.Add(([&]() -> Value { auto v1591 = s->Captured("step"); return Binary("Add", v1591, Value(int64_t{1})); }()), false); return Call(c, fn1589, std::move(args1590)); }()); Value v1588; v1588 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v1587, v1588))) return Value(false); v1587 = v1588; return Value(true); }()), Unary("USub", ([&]() -> Value { auto fn1592 = PrepareDictionaryGet(Attribute(s->Captured("view"), "prices")); Arguments args1593; args1593.positional.reserve(2); args1593.Add(s->LocalAt(0), false); args1593.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn1592, std::move(args1593)); }())), s->LocalAt(0)});
return {};
}
}  // namespace kagg::opponents::compiled
