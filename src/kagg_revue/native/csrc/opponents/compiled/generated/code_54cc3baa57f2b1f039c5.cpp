// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_54cc3baa57f2b1f039c5(Context& c, const ScopePtr& s) {
if (static_cast<bool>(([&]() -> Value { auto v27247 = s->Global("_V92_P_LIB"); Value v27248; v27248 = Value{}; if (!static_cast<bool>(Binary("Is", v27247, v27248))) return Value(false); v27247 = v27248; return Value(true); }()))) {
auto v27249 = ([&]() -> Value { auto dict27250 = Dict(); return dict27250; }());
Put(s->globals, "_V92_P_LIB", v27249);
}
return s->Global("_V92_P_LIB");
return {};
}
}  // namespace kagg::opponents::compiled
