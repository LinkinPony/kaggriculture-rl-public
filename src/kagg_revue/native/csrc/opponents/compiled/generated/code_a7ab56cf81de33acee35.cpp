// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_a7ab56cf81de33acee35(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"p"};
s->PrepareSlots(s_names);
return Tuple({([&]() -> Value { auto v6965 = ([&]() -> Value { auto fn6966 = s->Global("abs"); Arguments args6967; args6967.Add(([&]() -> Value { auto v6968 = Get(s->Captured("pos"), Value(int64_t{0})); return Binary("Sub", v6968, Get(s->LocalAt(0), Value(int64_t{0}))); }()), false); return Call(c, fn6966, std::move(args6967)); }()); return Binary("Add", v6965, ([&]() -> Value { auto fn6969 = s->Global("abs"); Arguments args6970; args6970.Add(([&]() -> Value { auto v6971 = Get(s->Captured("pos"), Value(int64_t{1})); return Binary("Sub", v6971, Get(s->LocalAt(0), Value(int64_t{1}))); }()), false); return Call(c, fn6969, std::move(args6970)); }())); }()), s->LocalAt(0)});
return {};
}
}  // namespace kagg::opponents::compiled
