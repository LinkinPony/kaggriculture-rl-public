// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_5b6b0f5274f63f739b6d(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"shops"};
s->PrepareSlots(s_names);
return (static_cast<bool>(Get(s->Global("_E363_STATE"), Value("mirror_like"))) ? ([&]() -> Value { auto fn27864 = s->Global("_E361_PAIR"); Arguments args27865; args27865.Add(s->LocalAt(0), false); return Call(c, fn27864, std::move(args27865)); }()) : ([&]() -> Value { auto fn27866 = s->Global("_E363_MERGED_PAIR"); Arguments args27867; args27867.Add(s->LocalAt(0), false); return Call(c, fn27866, std::move(args27867)); }()));
return {};
}
}  // namespace kagg::opponents::compiled
