// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_04e9b2c5a5290f012074(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "configuration", "observation"};
s->PrepareSlots(s_names);
try {
auto v5160 = ([&]() -> Value { auto fn5161 = s->Global("_EXPERIMENT_PARENT"); Arguments args5162; args5162.positional.reserve(2); args5162.Add(s->LocalAt(2), false); args5162.Add(s->LocalAt(1), false); return Call(c, fn5161, std::move(args5162)); }());
s->SetAt(0, v5160);
if (static_cast<bool>(([&]() -> Value { auto v5163 = s->Global("APPLY_TIMING"); if (!static_cast<bool>(v5163)) return v5163; v5163 = ([&]() -> Value { auto v5164 = ([&]() -> Value { auto fn5166 = s->Global("int"); Arguments args5167; args5167.Add(Get(s->LocalAt(2), Value("step")), false); return Call(c, fn5166, std::move(args5167)); }()); Value v5165; v5165 = Value(int64_t{144}); if (!static_cast<bool>(Binary("GtE", v5164, v5165))) return Value(false); v5164 = v5165; return Value(true); }()); return v5163; }()))) {
auto v5168 = ([&]() -> Value { auto fn5169 = s->Global("_v224_sales_first"); Arguments args5170; args5170.Add(s->LocalAt(0), false); return Call(c, fn5169, std::move(args5170)); }());
s->SetAt(0, v5168);
}
return s->LocalAt(0);
} catch (const Error& error5159) {
if (Matches(error5159, s->Global("Exception"))) {
auto v5171 = s->Global("_V219_REPORT");
auto v5172 = Value("errors");
auto v5173 = Get(v5171, v5172);
Put(v5171, v5172, Inplace("Add", v5173, Value(int64_t{1})));
return ([&]() -> Value { auto dict5174 = Dict(); auto key5175 = Value("farmer"); Put(dict5174, key5175, List({Value("PASS")})); auto key5176 = Value("hands"); Put(dict5174, key5176, List({})); auto key5177 = Value("market"); Put(dict5174, key5177, List({})); return dict5174; }());
}
else { throw; }
}
return {};
}
}  // namespace kagg::opponents::compiled
