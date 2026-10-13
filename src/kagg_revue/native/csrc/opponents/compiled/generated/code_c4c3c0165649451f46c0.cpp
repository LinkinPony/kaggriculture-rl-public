// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_c4c3c0165649451f46c0(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"v"};
s->PrepareSlots(s_names);
return Tuple({([&]() -> Value { auto v4888 = ([&]() -> Value { auto fn4889 = s->Global("abs"); Arguments args4890; args4890.Add(([&]() -> Value { auto v4891 = Get(s->Captured("pos"), Value(int64_t{0})); return Binary("Sub", v4891, Get(Get(s->LocalAt(0), Value(int64_t{0})), Value(int64_t{0}))); }()), false); return Call(c, fn4889, std::move(args4890)); }()); return Binary("Add", v4888, ([&]() -> Value { auto fn4892 = s->Global("abs"); Arguments args4893; args4893.Add(([&]() -> Value { auto v4894 = Get(s->Captured("pos"), Value(int64_t{1})); return Binary("Sub", v4894, Get(Get(s->LocalAt(0), Value(int64_t{0})), Value(int64_t{1}))); }()), false); return Call(c, fn4892, std::move(args4893)); }())); }()), ([&]() -> Value { auto fn4895 = Attribute(s->Captured("targets"), "index"); Arguments args4896; args4896.Add(Get(s->LocalAt(0), Value(int64_t{0})), false); return Call(c, fn4895, std::move(args4896)); }())});
return {};
}
}  // namespace kagg::opponents::compiled
