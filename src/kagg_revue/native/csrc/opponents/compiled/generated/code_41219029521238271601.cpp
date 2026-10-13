// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_41219029521238271601(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"farm", "idx", "pos"};
s->PrepareSlots(s_names);
if (static_cast<bool>(([&]() -> Value { auto v2139 = s->LocalAt(1); Value v2140; v2140 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v2139, v2140))) return Value(false); v2139 = v2140; return Value(true); }()))) {
auto v2141 = ([&]() -> Value { auto fn2142 = s->Global("list"); Arguments args2143; args2143.Add(s->LocalAt(2), false); return Call(c, fn2142, std::move(args2143)); }());
Put(s->LocalAt(0), Value("farmer"), v2141);
}
else {
auto v2144 = ([&]() -> Value { auto fn2145 = s->Global("list"); Arguments args2146; args2146.Add(s->LocalAt(2), false); return Call(c, fn2145, std::move(args2146)); }());
Put(Get(s->LocalAt(0), Value("hands")), ([&]() -> Value { auto v2147 = s->LocalAt(1); return Binary("Sub", v2147, Value(int64_t{1})); }()), v2144);
}
return {};
}
}  // namespace kagg::opponents::compiled
