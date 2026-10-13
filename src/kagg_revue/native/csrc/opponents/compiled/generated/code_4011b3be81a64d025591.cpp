// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_4011b3be81a64d025591(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"pos"};
s->PrepareSlots(s_names);
return ([&]() -> Value { auto fn4460 = s->Global("min"); Arguments args4461; args4461.Add(Tuple({Tuple({Value(int64_t{4}), Value(int64_t{4})}), Tuple({Value(int64_t{5}), Value(int64_t{4})}), Tuple({Value(int64_t{4}), Value(int64_t{5})}), Tuple({Value(int64_t{5}), Value(int64_t{5})})}), false); args4461.Keyword("key", Define(&Code_3bc355037ccd5ca7843b, s, Signature{{"p"}, {}, {}, {}, "", "", ([]() -> std::span<const char* const> { static constexpr const char* names[] = {"p"}; return names; }())}, true, "<lambda>")); return Call(c, fn4460, std::move(args4461)); }());
return {};
}
}  // namespace kagg::opponents::compiled
