// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_609a2f72a1dcb06c7e5d(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"it"};
s->PrepareSlots(s_names);
return Unary("USub", ([&]() -> Value { auto fn19093 = s->Global("int"); Arguments args19094; args19094.Add(([&]() -> Value { auto fn19095 = PrepareDictionaryGet(s->Captured("prices")); Arguments args19096; args19096.positional.reserve(2); args19096.Add(s->LocalAt(0), false); args19096.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn19095, std::move(args19096)); }()), false); return Call(c, fn19093, std::move(args19094)); }()));
return {};
}
}  // namespace kagg::opponents::compiled
