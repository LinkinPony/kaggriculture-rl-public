// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_66b384d6e7699ead49e4(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"it"};
s->PrepareSlots(s_names);
return Unary("USub", ([&]() -> Value { auto fn18772 = s->Global("int"); Arguments args18773; args18773.Add(([&]() -> Value { auto fn18774 = PrepareDictionaryGet(s->Captured("prices")); Arguments args18775; args18775.positional.reserve(2); args18775.Add(s->LocalAt(0), false); args18775.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn18774, std::move(args18775)); }()), false); return Call(c, fn18772, std::move(args18773)); }()));
return {};
}
}  // namespace kagg::opponents::compiled
