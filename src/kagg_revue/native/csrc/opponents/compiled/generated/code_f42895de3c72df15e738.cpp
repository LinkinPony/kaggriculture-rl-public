// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_f42895de3c72df15e738(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"it"};
s->PrepareSlots(s_names);
return Unary("USub", ([&]() -> Value { auto fn4284 = s->Global("int"); Arguments args4285; args4285.Add(([&]() -> Value { auto fn4286 = PrepareDictionaryGet(Attribute(s->Captured("view"), "prices")); Arguments args4287; args4287.positional.reserve(2); args4287.Add(s->LocalAt(0), false); args4287.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn4286, std::move(args4287)); }()), false); return Call(c, fn4284, std::move(args4285)); }()));
return {};
}
}  // namespace kagg::opponents::compiled
