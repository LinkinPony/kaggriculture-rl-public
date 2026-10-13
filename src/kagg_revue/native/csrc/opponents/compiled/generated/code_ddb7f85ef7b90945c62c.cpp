// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_ddb7f85ef7b90945c62c(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"a", "b"};
s->PrepareSlots(s_names);
return ([&]() -> Value { auto v26792 = ([&]() -> Value { auto fn26793 = s->Global("abs"); Arguments args26794; args26794.Add(([&]() -> Value { auto v26795 = Get(s->LocalAt(0), Value(int64_t{0})); return Binary("Sub", v26795, Get(s->LocalAt(1), Value(int64_t{0}))); }()), false); return Call(c, fn26793, std::move(args26794)); }()); return Binary("Add", v26792, ([&]() -> Value { auto fn26796 = s->Global("abs"); Arguments args26797; args26797.Add(([&]() -> Value { auto v26798 = Get(s->LocalAt(0), Value(int64_t{1})); return Binary("Sub", v26798, Get(s->LocalAt(1), Value(int64_t{1}))); }()), false); return Call(c, fn26796, std::move(args26797)); }())); }());
return {};
}
}  // namespace kagg::opponents::compiled
