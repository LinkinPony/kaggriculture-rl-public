// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_6cf44ff59664fa9cd1ee(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"pos", "targets"};
s->PrepareSlots(s_names);
return (static_cast<bool>(s->LocalAt(1)) ? ([&]() -> Value { auto fn26799 = s->Global("min"); Arguments args26800; args26800.Add(([&]() -> Value { auto fn26801 = s->Global("_r53_permutations"); Arguments args26802; args26802.Add(s->LocalAt(1), false); return Call(c, fn26801, std::move(args26802)); }()), false); args26800.Keyword("key", Define(&Code_ab8bec2114d376a330e3, s, Signature{{"path"}, {}, {}, {}, "", "", ([]() -> std::span<const char* const> { static constexpr const char* names[] = {"path"}; return names; }())}, true, "<lambda>")); return Call(c, fn26799, std::move(args26800)); }()) : Tuple({}));
return {};
}
}  // namespace kagg::opponents::compiled
