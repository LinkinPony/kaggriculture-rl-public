// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_247b5d0fc6a14c9ac57f(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"configuration", "observation"};
s->PrepareSlots(s_names);
if (static_cast<bool>(([&]() -> Value { auto v27840 = ([&]() -> Value { auto fn27842 = s->Global("int"); Arguments args27843; args27843.Add(Get(s->LocalAt(1), Value("step")), false); return Call(c, fn27842, std::move(args27843)); }()); Value v27841; v27841 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v27840, v27841))) return Value(false); v27840 = v27841; return Value(true); }()))) {
(void)([&]() -> Value { auto fn27844 = Attribute(s->Global("_E361_REPORT"), "update"); Arguments args27845; args27845.Keyword("new_best", Value(int64_t{0})); args27845.Keyword("errors", Value(int64_t{0})); return Call(c, fn27844, std::move(args27845)); }());
}
try {
return ([&]() -> Value { auto fn27847 = s->Global("_E361_PARENT"); Arguments args27848; args27848.positional.reserve(2); args27848.Add(s->LocalAt(1), false); args27848.Add(s->LocalAt(0), false); return Call(c, fn27847, std::move(args27848)); }());
} catch (const Error& error27846) {
if (Matches(error27846, s->Global("Exception"))) {
auto v27849 = s->Global("_E361_REPORT");
auto v27850 = Value("errors");
auto v27851 = Get(v27849, v27850);
Put(v27849, v27850, Inplace("Add", v27851, Value(int64_t{1})));
return ([&]() -> Value { auto fn27852 = s->Global("dict"); Arguments args27853; args27853.Keyword("farmer", List({Value("PASS")})); args27853.Keyword("hands", List({})); args27853.Keyword("market", List({})); return Call(c, fn27852, std::move(args27853)); }());
}
else { throw; }
}
return {};
}
}  // namespace kagg::opponents::compiled
