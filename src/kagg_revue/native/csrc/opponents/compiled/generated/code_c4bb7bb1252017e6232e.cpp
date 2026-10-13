// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_c4bb7bb1252017e6232e(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"inventory", "item", "params"};
s->PrepareSlots(s_names);
return ([&]() -> Value { auto fn19183 = s->Global("_r37_market_price"); Arguments args19184; args19184.positional.reserve(3); args19184.Add(s->LocalAt(1), false); args19184.Add(s->LocalAt(0), false); args19184.Add(s->LocalAt(2), false); return Call(c, fn19183, std::move(args19184)); }());
return {};
}
}  // namespace kagg::opponents::compiled
