// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_0a64692532ce2cb79e4d(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"idx", "private"};
s->PrepareSlots(s_names);
while (static_cast<bool>(([&]() -> Value { auto v2148 = ([&]() -> Value { auto fn2150 = s->Global("len"); Arguments args2151; args2151.Add(Get(s->LocalAt(1), Value("inventories")), false); return Call(c, fn2150, std::move(args2151)); }()); Value v2149; v2149 = s->LocalAt(0); if (!static_cast<bool>(Binary("LtE", v2148, v2149))) return Value(false); v2148 = v2149; return Value(true); }()))) {
(void)([&]() -> Value { auto fn2152 = Attribute(Get(s->LocalAt(1), Value("inventories")), "append"); Arguments args2153; args2153.Add(([&]() -> Value { auto dict2154 = Dict(); return dict2154; }()), false); return Call(c, fn2152, std::move(args2153)); }());
}
return Get(Get(s->LocalAt(1), Value("inventories")), s->LocalAt(0));
return {};
}
}  // namespace kagg::opponents::compiled
