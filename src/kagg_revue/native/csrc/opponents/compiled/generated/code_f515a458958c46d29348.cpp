// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_f515a458958c46d29348(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"a"};
s->PrepareSlots(s_names);
return ([&]() -> Value { auto v20622 = ([&]() -> Value { auto fn20623 = s->Global("abs"); Arguments args20624; args20624.Add(([&]() -> Value { auto v20625 = Get(s->LocalAt(0), Value(int64_t{0})); return Binary("Sub", v20625, Get(s->Captured("pos"), Value(int64_t{0}))); }()), false); return Call(c, fn20623, std::move(args20624)); }()); return Binary("Add", v20622, ([&]() -> Value { auto fn20626 = s->Global("abs"); Arguments args20627; args20627.Add(([&]() -> Value { auto v20628 = Get(s->LocalAt(0), Value(int64_t{1})); return Binary("Sub", v20628, Get(s->Captured("pos"), Value(int64_t{1}))); }()), false); return Call(c, fn20626, std::move(args20627)); }())); }());
return {};
}
}  // namespace kagg::opponents::compiled
