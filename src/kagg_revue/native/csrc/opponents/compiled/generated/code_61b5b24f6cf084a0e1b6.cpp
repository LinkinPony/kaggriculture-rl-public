// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_61b5b24f6cf084a0e1b6(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"obs", "self"};
s->PrepareSlots(s_names);
(void)([&]() -> Value { auto fn4335 = Attribute(MakeSuper(s->Global("FarmView"), s->LocalAt(1)), "__init__"); Arguments args4336; args4336.positional.reserve(3); args4336.Add(s->LocalAt(0), false); args4336.Add(([&]() -> Value { auto fn4337 = s->Global("int"); Arguments args4338; args4338.Add(Get(s->LocalAt(0), Value("player")), false); return Call(c, fn4337, std::move(args4338)); }()), false); args4336.Add(Attribute(Attribute(s->Global("_IMPL"), "chassis"), "cfg"), false); return Call(c, fn4335, std::move(args4336)); }());
return {};
}
}  // namespace kagg::opponents::compiled
