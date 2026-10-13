// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_90ac5092d36fcf70dc38(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "configuration", "observation"};
s->PrepareSlots(s_names);
auto v30767 = ([&]() -> Value { auto fn30768 = s->Global("_P_overflow_338343"); Arguments args30769; args30769.positional.reserve(2); args30769.Add(s->LocalAt(2), false); args30769.Add(s->LocalAt(1), false); return Call(c, fn30768, std::move(args30769)); }());
s->SetAt(0, v30767);
try {
return ([&]() -> Value { auto fn30771 = s->Global("_ov_apply"); Arguments args30772; args30772.positional.reserve(2); args30772.Add(s->LocalAt(2), false); args30772.Add(s->LocalAt(0), false); return Call(c, fn30771, std::move(args30772)); }());
} catch (const Error& error30770) {
if (Matches(error30770, s->Global("Exception"))) {
auto v30773 = s->Global("_OV_REPORT");
auto v30774 = Value("ov_errors");
auto v30775 = Get(v30773, v30774);
Put(v30773, v30774, Inplace("Add", v30775, Value(int64_t{1})));
return s->LocalAt(0);
}
else { throw; }
}
return {};
}
}  // namespace kagg::opponents::compiled
