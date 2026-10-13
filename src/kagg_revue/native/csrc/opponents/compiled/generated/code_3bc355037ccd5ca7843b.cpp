// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_3bc355037ccd5ca7843b(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"p"};
s->PrepareSlots(s_names);
return ([&]() -> Value { auto v4462 = ([&]() -> Value { auto fn4463 = s->Global("abs"); Arguments args4464; args4464.Add(([&]() -> Value { auto v4465 = Get(s->Captured("pos"), Value(int64_t{0})); return Binary("Sub", v4465, Get(s->LocalAt(0), Value(int64_t{0}))); }()), false); return Call(c, fn4463, std::move(args4464)); }()); return Binary("Add", v4462, ([&]() -> Value { auto fn4466 = s->Global("abs"); Arguments args4467; args4467.Add(([&]() -> Value { auto v4468 = Get(s->Captured("pos"), Value(int64_t{1})); return Binary("Sub", v4468, Get(s->LocalAt(0), Value(int64_t{1}))); }()), false); return Call(c, fn4466, std::move(args4467)); }())); }());
return {};
}
}  // namespace kagg::opponents::compiled
