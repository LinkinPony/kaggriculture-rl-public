// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_e4778ae5dc8b1b8a6566(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"inv", "item", "n"};
s->PrepareSlots(s_names);
auto v2155 = ([&]() -> Value { auto v2156 = ([&]() -> Value { auto fn2157 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args2158; args2158.positional.reserve(2); args2158.Add(s->LocalAt(1), false); args2158.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn2157, std::move(args2158)); }()); return Binary("Add", v2156, s->LocalAt(2)); }());
Put(s->LocalAt(0), s->LocalAt(1), v2155);
return {};
}
}  // namespace kagg::opponents::compiled
