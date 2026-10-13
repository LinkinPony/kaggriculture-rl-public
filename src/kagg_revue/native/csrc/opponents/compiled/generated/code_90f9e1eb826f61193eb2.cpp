// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_90f9e1eb826f61193eb2(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "configuration", "observation"};
s->PrepareSlots(s_names);
try {
auto v5237 = ([&]() -> Value { auto fn5238 = s->Global("_ORDER_PARENT"); Arguments args5239; args5239.positional.reserve(2); args5239.Add(s->LocalAt(2), false); args5239.Add(s->LocalAt(1), false); return Call(c, fn5238, std::move(args5239)); }());
s->SetAt(0, v5237);
if (static_cast<bool>(([&]() -> Value { auto v5240 = ([&]() -> Value { auto fn5242 = s->Global("int"); Arguments args5243; args5243.Add(Get(s->LocalAt(2), Value("step")), false); return Call(c, fn5242, std::move(args5243)); }()); Value v5241; v5241 = Value(int64_t{144}); if (!static_cast<bool>(Binary("GtE", v5240, v5241))) return Value(false); v5240 = v5241; return Value(true); }()))) {
auto v5244 = ([&]() -> Value { auto fn5245 = s->Global("_v224_sales_first"); Arguments args5246; args5246.Add(s->LocalAt(0), false); return Call(c, fn5245, std::move(args5246)); }());
s->SetAt(0, v5244);
}
return s->LocalAt(0);
} catch (const Error& error5236) {
if (Matches(error5236, s->Global("Exception"))) {
auto v5247 = s->Global("_V219_REPORT");
auto v5248 = Value("errors");
auto v5249 = Get(v5247, v5248);
Put(v5247, v5248, Inplace("Add", v5249, Value(int64_t{1})));
return ([&]() -> Value { auto dict5250 = Dict(); auto key5251 = Value("farmer"); Put(dict5250, key5251, List({Value("PASS")})); auto key5252 = Value("hands"); Put(dict5250, key5252, List({})); auto key5253 = Value("market"); Put(dict5250, key5253, List({})); return dict5250; }());
}
else { throw; }
}
return {};
}
}  // namespace kagg::opponents::compiled
