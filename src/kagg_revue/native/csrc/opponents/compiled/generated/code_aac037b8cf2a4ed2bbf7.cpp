// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_aac037b8cf2a4ed2bbf7(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "configuration", "observation"};
s->PrepareSlots(s_names);
if (static_cast<bool>(([&]() -> Value { auto v21667 = ([&]() -> Value { auto fn21669 = s->Global("int"); Arguments args21670; args21670.Add(Get(s->LocalAt(2), Value("step")), false); return Call(c, fn21669, std::move(args21670)); }()); Value v21668; v21668 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v21667, v21668))) return Value(false); v21667 = v21668; return Value(true); }()))) {
(void)([&]() -> Value { auto fn21671 = Attribute(s->Global("_V9_FERT_REPORT"), "update"); Arguments args21672; args21672.Keyword("fert_applied", Value(int64_t{0})); args21672.Keyword("fert_errors", Value(int64_t{0})); return Call(c, fn21671, std::move(args21672)); }());
}
auto v21673 = ([&]() -> Value { auto fn21674 = s->Global("_V9_FERT_PARENT"); Arguments args21675; args21675.positional.reserve(2); args21675.Add(s->LocalAt(2), false); args21675.Add(s->LocalAt(1), false); return Call(c, fn21674, std::move(args21675)); }());
s->SetAt(0, v21673);
try {
return ([&]() -> Value { auto fn21677 = s->Global("_v9_fert"); Arguments args21678; args21678.positional.reserve(2); args21678.Add(s->LocalAt(2), false); args21678.Add(s->LocalAt(0), false); return Call(c, fn21677, std::move(args21678)); }());
} catch (const Error& error21676) {
if (Matches(error21676, s->Global("Exception"))) {
auto v21679 = s->Global("_V9_FERT_REPORT");
auto v21680 = Value("fert_errors");
auto v21681 = Get(v21679, v21680);
Put(v21679, v21680, Inplace("Add", v21681, Value(int64_t{1})));
return s->LocalAt(0);
}
else { throw; }
}
return {};
}
}  // namespace kagg::opponents::compiled
