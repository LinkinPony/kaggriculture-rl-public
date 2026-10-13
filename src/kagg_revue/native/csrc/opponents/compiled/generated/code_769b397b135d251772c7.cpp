// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_769b397b135d251772c7(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "configuration", "observation"};
s->PrepareSlots(s_names);
auto v26765 = ([&]() -> Value { auto fn26766 = s->Global("_E343_YX_BASE"); Arguments args26767; args26767.positional.reserve(2); args26767.Add(s->LocalAt(2), false); args26767.Add(s->LocalAt(1), false); return Call(c, fn26766, std::move(args26767)); }());
s->SetAt(0, v26765);
try {
if (static_cast<bool>(([&]() -> Value { auto v26769 = s->Global("_E343_YX_DAY11"); if (!static_cast<bool>(v26769)) return v26769; v26769 = ([&]() -> Value { auto v26770 = ([&]() -> Value { auto v26772 = ([&]() -> Value { auto fn26773 = s->Global("int"); Arguments args26774; args26774.Add(Get(s->LocalAt(2), Value("step")), false); return Call(c, fn26773, std::move(args26774)); }()); return Binary("FloorDiv", v26772, Value(int64_t{24})); }()); Value v26771; v26771 = Value(int64_t{11}); if (!static_cast<bool>(Binary("Eq", v26770, v26771))) return Value(false); v26770 = v26771; return Value(true); }()); return v26769; }()))) {
return ([&]() -> Value { auto fn26775 = s->Global("_e343_yx_day11"); Arguments args26776; args26776.positional.reserve(3); args26776.Add(s->LocalAt(2), false); args26776.Add(s->LocalAt(1), false); args26776.Add(s->LocalAt(0), false); return Call(c, fn26775, std::move(args26776)); }());
}
} catch (const Error& error26768) {
if (Matches(error26768, s->Global("Exception"))) {
auto v26777 = s->Global("_E343_YX_REPORT");
auto v26778 = Value("yx_errors");
auto v26779 = Get(v26777, v26778);
Put(v26777, v26778, Inplace("Add", v26779, Value(int64_t{1})));
}
else { throw; }
}
return s->LocalAt(0);
return {};
}
}  // namespace kagg::opponents::compiled
