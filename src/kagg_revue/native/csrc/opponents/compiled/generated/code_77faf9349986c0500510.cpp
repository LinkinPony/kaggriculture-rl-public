// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_77faf9349986c0500510(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"agent", "chassis", "opponent_plan", "router", "routes", "settings"};
s->PrepareSlots(s_names);
auto v1741 = ([&]() -> Value { auto fn1742 = s->Global("Chassis"); Arguments args1743; args1743.positional.reserve(4); args1743.Add(s->LocalAt(4), false); args1743.Add(s->LocalAt(3), false); args1743.Add(s->LocalAt(5), false); args1743.Add(s->LocalAt(2), false); return Call(c, fn1742, std::move(args1743)); }());
s->SetAt(1, v1741);
s->SetAt(0, Define(&Code_04e7a4ff86df20c6b3c2, s, Signature{{"observation", "configuration"}, {Value{}}, {}, {}, "", "", ([]() -> std::span<const char* const> { static constexpr const char* names[] = {"configuration", "farms", "hands", "observation", "player", "step", "tape"}; return names; }())}, true, "agent"));
s->definitions.push_back("agent");
auto v1801 = s->LocalAt(1);
SetAttribute(s->LocalAt(0), "chassis", v1801);
return s->LocalAt(0);
return {};
}
}  // namespace kagg::opponents::compiled
