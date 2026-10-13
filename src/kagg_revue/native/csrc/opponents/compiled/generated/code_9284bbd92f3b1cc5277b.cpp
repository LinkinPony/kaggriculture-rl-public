// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_9284bbd92f3b1cc5277b(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"configuration", "observation"};
s->PrepareSlots(s_names);
try {
return ([&]() -> Value { auto fn4323 = s->Global("_V28_CORE"); Arguments args4324; args4324.positional.reserve(2); args4324.Add(s->LocalAt(1), false); args4324.Add(s->LocalAt(0), false); return Call(c, fn4323, std::move(args4324)); }());
} catch (const Error& error4322) {
if (Matches(error4322, s->Global("Exception"))) {
auto v4325 = Attribute(Attribute(s->Global("_IMPL"), "chassis"), "diagnostics");
auto v4326 = Value("v28_entry_errors");
auto v4327 = Get(v4325, v4326);
Put(v4325, v4326, Inplace("Add", v4327, Value(int64_t{1})));
return ([&]() -> Value { auto dict4328 = Dict(); auto key4329 = Value("farmer"); Put(dict4328, key4329, List({Value("PASS")})); auto key4330 = Value("hands"); Put(dict4328, key4330, List({})); auto key4331 = Value("market"); Put(dict4328, key4331, List({})); return dict4328; }());
}
else { throw; }
}
return {};
}
}  // namespace kagg::opponents::compiled
