// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_bf82af8aaec312ae358a(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"shops"};
s->PrepareSlots(s_names);
return ([&]() -> Value { auto v27759 = ([&]() -> Value { auto fn27760 = s->Global("_E352_ORIG_PAIR"); Arguments args27761; args27761.Add(s->LocalAt(0), false); return Call(c, fn27760, std::move(args27761)); }()); return Binary("Add", v27759, ([&]() -> Value { auto fn27762 = s->Global("_e352_streams"); Arguments args27763; args27763.Add(([&]() -> Value { auto fn27764 = s->Global("tuple"); Arguments args27765; args27765.Add(s->LocalAt(0), false); return Call(c, fn27764, std::move(args27765)); }()), false); return Call(c, fn27762, std::move(args27763)); }())); }());
return {};
}
}  // namespace kagg::opponents::compiled
