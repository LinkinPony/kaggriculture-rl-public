// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_1086356f921902e593fb(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"xy"};
s->PrepareSlots(s_names);
return Tuple({([&]() -> Value { auto v3140 = ([&]() -> Value { auto fn3141 = s->Global("abs"); Arguments args3142; args3142.Add(([&]() -> Value { auto v3143 = Get(s->Captured("pos"), Value(int64_t{0})); return Binary("Sub", v3143, Get(s->LocalAt(0), Value(int64_t{0}))); }()), false); return Call(c, fn3141, std::move(args3142)); }()); return Binary("Add", v3140, ([&]() -> Value { auto fn3144 = s->Global("abs"); Arguments args3145; args3145.Add(([&]() -> Value { auto v3146 = Get(s->Captured("pos"), Value(int64_t{1})); return Binary("Sub", v3146, Get(s->LocalAt(0), Value(int64_t{1}))); }()), false); return Call(c, fn3144, std::move(args3145)); }())); }()), ([&]() -> Value { auto fn3147 = Attribute(s->Captured("targets"), "index"); Arguments args3148; args3148.Add(s->LocalAt(0), false); return Call(c, fn3147, std::move(args3148)); }())});
return {};
}
}  // namespace kagg::opponents::compiled
