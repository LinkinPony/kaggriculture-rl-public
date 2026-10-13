// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_f119e35edfa3b8db337f(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"x"};
s->PrepareSlots(s_names);
return Unary("USub", Get(s->LocalAt(0), Value(int64_t{0})));
return {};
}
}  // namespace kagg::opponents::compiled
