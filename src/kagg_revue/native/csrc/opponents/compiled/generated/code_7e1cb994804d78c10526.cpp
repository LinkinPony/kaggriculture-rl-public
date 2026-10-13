// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_7e1cb994804d78c10526(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"farm", "idx"};
s->PrepareSlots(s_names);
if (static_cast<bool>(([&]() -> Value { auto v2131 = s->LocalAt(1); Value v2132; v2132 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v2131, v2132))) return Value(false); v2131 = v2132; return Value(true); }()))) {
return Get(s->LocalAt(0), Value("farmer"));
}
return (static_cast<bool>(([&]() -> Value { auto v2133 = ([&]() -> Value { auto v2135 = s->LocalAt(1); return Binary("Sub", v2135, Value(int64_t{1})); }()); Value v2134; v2134 = ([&]() -> Value { auto fn2136 = s->Global("len"); Arguments args2137; args2137.Add(Get(s->LocalAt(0), Value("hands")), false); return Call(c, fn2136, std::move(args2137)); }()); if (!static_cast<bool>(Binary("Lt", v2133, v2134))) return Value(false); v2133 = v2134; return Value(true); }())) ? Get(Get(s->LocalAt(0), Value("hands")), ([&]() -> Value { auto v2138 = s->LocalAt(1); return Binary("Sub", v2138, Value(int64_t{1})); }())) : Value{});
return {};
}
}  // namespace kagg::opponents::compiled
