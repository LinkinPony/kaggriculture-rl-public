// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_daf7e0be7aa2c0bf89a9(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"configuration", "k", "observation", "result"};
s->PrepareSlots(s_names);
if (static_cast<bool>(([&]() -> Value { auto v8760 = ([&]() -> Value { auto fn8761 = s->Global("isinstance"); Arguments args8762; args8762.positional.reserve(2); args8762.Add(s->LocalAt(2), false); args8762.Add(s->Global("dict"), false); return Call(c, fn8761, std::move(args8762)); }()); if (!static_cast<bool>(v8760)) return v8760; v8760 = ([&]() -> Value { auto v8763 = ([&]() -> Value { auto fn8765 = PrepareDictionaryGet(s->LocalAt(2)); Arguments args8766; args8766.Add(Value("step"), false); return CallDictionaryGet(c, fn8765, std::move(args8766)); }()); Value v8764; v8764 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v8763, v8764))) return Value(false); v8763 = v8764; return Value(true); }()); return v8760; }()))) {
for (const auto& item8767 : Iterate(s->Global("_R53_LABOR_REPORT"))) {
s->SetAt(1, item8767);
auto v8768 = Value(int64_t{0});
Put(s->Global("_R53_LABOR_REPORT"), s->LocalAt(1), v8768);
}
}
auto v8769 = ([&]() -> Value { auto fn8770 = s->Global("_R53_LABOR_PARENT"); Arguments args8771; args8771.positional.reserve(2); args8771.Add(s->LocalAt(2), false); args8771.Add(s->LocalAt(0), false); return Call(c, fn8770, std::move(args8771)); }());
s->SetAt(3, v8769);
(void)([&]() -> Value { auto fn8772 = Attribute(s->Global("_R53_LABOR_COMBINED"), "update"); Arguments args8773; args8773.Add(([&]() -> Value { auto fn8774 = s->Global("getattr"); Arguments args8775; args8775.positional.reserve(3); args8775.Add(s->Global("_R53_LABOR_PARENT"), false); args8775.Add(Value("telemetry"), false); args8775.Add(([&]() -> Value { auto dict8776 = Dict(); return dict8776; }()), false); return Call(c, fn8774, std::move(args8775)); }()), false); return Call(c, fn8772, std::move(args8773)); }());
(void)([&]() -> Value { auto fn8777 = Attribute(s->Global("_R53_LABOR_COMBINED"), "update"); Arguments args8778; args8778.Add(s->Global("_R53_LABOR_REPORT"), false); return Call(c, fn8777, std::move(args8778)); }());
return s->LocalAt(3);
return {};
}
}  // namespace kagg::opponents::compiled
