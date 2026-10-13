// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_46676c00a824d33d7fea(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"day", "native", "tape"};
s->PrepareSlots(s_names);
auto v4372 = Get(Attribute(Attribute(s->Global("_IMPL"), "chassis"), "routes"), Get(s->LocalAt(1), Value("route")));
s->SetAt(2, v4372);
return Slice(s->LocalAt(2), ([&]() -> Value { auto v4373 = s->LocalAt(0); return Binary("Mult", v4373, Value(int64_t{24})); }()), ([&]() -> Value { auto fn4374 = s->Global("min"); Arguments args4375; args4375.positional.reserve(2); args4375.Add(([&]() -> Value { auto v4376 = ([&]() -> Value { auto v4377 = s->LocalAt(0); return Binary("Add", v4377, Value(int64_t{1})); }()); return Binary("Mult", v4376, Value(int64_t{24})); }()), false); args4375.Add(Value(int64_t{719}), false); return Call(c, fn4374, std::move(args4375)); }()), Value{});
return {};
}
}  // namespace kagg::opponents::compiled
