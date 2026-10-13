// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_4e86b4c3ba0b6eabef71(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"io"};
s->PrepareSlots(s_names);
return Tuple({Unary("USub", ([&]() -> Value { auto fn23243 = s->Global("_r37_quote_priority"); Arguments args23244; args23244.positional.reserve(3); args23244.Add(s->Captured("observation"), false); args23244.Add(Get(s->LocalAt(0), Value(int64_t{1})), false); args23244.Add(s->Captured("proj"), false); return Call(c, fn23243, std::move(args23244)); }())), Get(s->LocalAt(0), Value(int64_t{0}))});
return {};
}
}  // namespace kagg::opponents::compiled
