// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_ec7c35cd6adf702bbe71(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"p"};
s->PrepareSlots(s_names);
return Tuple({Unary("USub", Get(s->LocalAt(0), Value(int64_t{0}))), Get(s->LocalAt(0), Value(int64_t{1})), Get(s->LocalAt(0), Value(int64_t{2}))});
return {};
}
}  // namespace kagg::opponents::compiled
