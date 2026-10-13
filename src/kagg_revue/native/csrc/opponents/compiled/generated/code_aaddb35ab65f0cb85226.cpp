// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_aaddb35ab65f0cb85226(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"s"};
s->PrepareSlots(s_names);
return Tuple({Unary("USub", Get(s->LocalAt(0), Value(int64_t{0}))), Unary("USub", Get(s->LocalAt(0), Value(int64_t{1}))), Get(s->LocalAt(0), Value(int64_t{2})), Get(s->LocalAt(0), Value(int64_t{4}))});
return {};
}
}  // namespace kagg::opponents::compiled
