// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_467597876a8298777d97(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"configuration", "observation"};
s->PrepareSlots(s_names);
if (static_cast<bool>(([&]() -> Value { auto v30453 = ([&]() -> Value { auto fn30455 = s->Global("int"); Arguments args30456; args30456.Add(Get(s->LocalAt(1), Value("step")), false); return Call(c, fn30455, std::move(args30456)); }()); Value v30454; v30454 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v30453, v30454))) return Value(false); v30453 = v30454; return Value(true); }()))) {
(void)([&]() -> Value { auto fn30457 = Attribute(s->Global("_v9_racegate_report"), "update"); Arguments args30458; args30458.Keyword("racegate_reserved_units", Value(int64_t{0})); args30458.Keyword("racegate_errors", Value(int64_t{0})); return Call(c, fn30457, std::move(args30458)); }());
}
try {
return ([&]() -> Value { auto fn30460 = s->Global("_V9_RACEGATE_PARENT"); Arguments args30461; args30461.positional.reserve(2); args30461.Add(s->LocalAt(1), false); args30461.Add(s->LocalAt(0), false); return Call(c, fn30460, std::move(args30461)); }());
} catch (const Error& error30459) {
if (Matches(error30459, s->Global("Exception"))) {
auto v30462 = s->Global("_v9_racegate_report");
auto v30463 = Value("racegate_errors");
auto v30464 = Get(v30462, v30463);
Put(v30462, v30463, Inplace("Add", v30464, Value(int64_t{1})));
return ([&]() -> Value { auto dict30465 = Dict(); auto key30466 = Value("farmer"); Put(dict30465, key30466, List({Value("PASS")})); auto key30467 = Value("hands"); Put(dict30465, key30467, List({})); auto key30468 = Value("market"); Put(dict30465, key30468, List({})); return dict30465; }());
}
else { throw; }
}
return {};
}
}  // namespace kagg::opponents::compiled
