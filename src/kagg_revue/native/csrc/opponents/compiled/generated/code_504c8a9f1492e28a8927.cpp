// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_504c8a9f1492e28a8927(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"b"};
s->PrepareSlots(s_names);
return Tuple({([&]() -> Value { auto v18138 = Unary("USub", Get(s->LocalAt(0), Value(int64_t{2}))); return Binary("Div", v18138, Get(s->LocalAt(0), Value(int64_t{3}))); }()), Unary("USub", Get(s->LocalAt(0), Value(int64_t{2}))), Get(s->LocalAt(0), Value(int64_t{0}))});
return {};
}
}  // namespace kagg::opponents::compiled
