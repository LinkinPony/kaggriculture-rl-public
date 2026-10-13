// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_7f74f3b8c06f90ce593a(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"default", "value"};
s->PrepareSlots(s_names);
try {
return ([&]() -> Value { auto fn64 = s->Global("int"); Arguments args65; args65.Add(s->LocalAt(1), false); return Call(c, fn64, std::move(args65)); }());
} catch (const Error& error63) {
if (Matches(error63, Tuple({s->Global("TypeError"), s->Global("ValueError")}))) {
return s->LocalAt(0);
}
else { throw; }
}
return {};
}
}  // namespace kagg::opponents::compiled
