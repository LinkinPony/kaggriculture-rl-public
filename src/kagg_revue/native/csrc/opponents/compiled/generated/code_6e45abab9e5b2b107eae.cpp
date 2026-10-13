// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_6e45abab9e5b2b107eae(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "before", "configuration", "observation"};
s->PrepareSlots(s_names);
auto v5258 = Get(s->Global("_V219_REPORT"), Value("errors"));
s->SetAt(1, v5258);
try {
auto v5260 = ([&]() -> Value { auto fn5261 = s->Global("_V31_CORE"); Arguments args5262; args5262.positional.reserve(2); args5262.Add(s->LocalAt(3), false); args5262.Add(s->LocalAt(2), false); return Call(c, fn5261, std::move(args5262)); }());
s->SetAt(0, v5260);
auto v5263 = Attribute(Attribute(s->Global("_IMPL"), "chassis"), "diagnostics");
auto v5264 = Value("production_errors");
auto v5265 = Get(v5263, v5264);
Put(v5263, v5264, Inplace("Add", v5265, ([&]() -> Value { auto v5266 = Get(s->Global("_V219_REPORT"), Value("errors")); return Binary("Sub", v5266, s->LocalAt(1)); }())));
return s->LocalAt(0);
} catch (const Error& error5259) {
if (Matches(error5259, s->Global("Exception"))) {
auto v5267 = Attribute(Attribute(s->Global("_IMPL"), "chassis"), "diagnostics");
auto v5268 = Value("v31_entry_errors");
auto v5269 = Get(v5267, v5268);
Put(v5267, v5268, Inplace("Add", v5269, Value(int64_t{1})));
return ([&]() -> Value { auto dict5270 = Dict(); auto key5271 = Value("farmer"); Put(dict5270, key5271, List({Value("PASS")})); auto key5272 = Value("hands"); Put(dict5270, key5272, List({})); auto key5273 = Value("market"); Put(dict5270, key5273, List({})); return dict5270; }());
}
else { throw; }
}
return {};
}
}  // namespace kagg::opponents::compiled
