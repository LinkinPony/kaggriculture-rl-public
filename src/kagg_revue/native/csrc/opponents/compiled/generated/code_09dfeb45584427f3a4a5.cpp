// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_09dfeb45584427f3a4a5(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"configuration", "observation"};
s->PrepareSlots(s_names);
if (static_cast<bool>(([&]() -> Value { auto v30166 = ([&]() -> Value { auto fn30168 = s->Global("int"); Arguments args30169; args30169.Add(Get(s->LocalAt(1), Value("step")), false); return Call(c, fn30168, std::move(args30169)); }()); Value v30167; v30167 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v30166, v30167))) return Value(false); v30166 = v30167; return Value(true); }()))) {
(void)([&]() -> Value { auto fn30170 = Attribute(s->Global("_v9_racepx_report"), "update"); Arguments args30171; args30171.Keyword("racepx_skipped", Value(int64_t{0})); args30171.Keyword("racepx_sold", Value(int64_t{0})); args30171.Keyword("racepx_errors", Value(int64_t{0})); return Call(c, fn30170, std::move(args30171)); }());
}
try {
return ([&]() -> Value { auto fn30173 = s->Global("_V9_RACEPX_PARENT"); Arguments args30174; args30174.positional.reserve(2); args30174.Add(s->LocalAt(1), false); args30174.Add(s->LocalAt(0), false); return Call(c, fn30173, std::move(args30174)); }());
} catch (const Error& error30172) {
if (Matches(error30172, s->Global("Exception"))) {
auto v30175 = s->Global("_v9_racepx_report");
auto v30176 = Value("racepx_errors");
auto v30177 = Get(v30175, v30176);
Put(v30175, v30176, Inplace("Add", v30177, Value(int64_t{1})));
return ([&]() -> Value { auto dict30178 = Dict(); auto key30179 = Value("farmer"); Put(dict30178, key30179, List({Value("PASS")})); auto key30180 = Value("hands"); Put(dict30178, key30180, List({})); auto key30181 = Value("market"); Put(dict30178, key30181, List({})); return dict30178; }());
}
else { throw; }
}
return {};
}
}  // namespace kagg::opponents::compiled
