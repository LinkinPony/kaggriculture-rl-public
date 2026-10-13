// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_197c74236d7c0a5e20e9(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"observation", "state", "step"};
s->PrepareSlots(s_names);
return ([&]() -> Value { auto fn421 = s->Global("next"); Arguments args422; args422.Add(([&]() -> Value { auto fn423 = s->Global("iter"); Arguments args424; args424.Add(Attribute(s->Captured("self"), "routes"), false); return Call(c, fn423, std::move(args424)); }()), false); return Call(c, fn421, std::move(args422)); }());
return {};
}
}  // namespace kagg::opponents::compiled
