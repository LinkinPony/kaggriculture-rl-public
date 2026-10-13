// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_7a557af06c965b219a68(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"pos", "target", "targets"};
s->PrepareSlots(s_names);
auto v3134 = ([&]() -> Value { auto fn3135 = s->Global("_shed_access_tiles"); Arguments args3136; args3136.Add(Value(int64_t{10}), false); return Call(c, fn3135, std::move(args3136)); }());
s->SetAt(2, v3134);
auto v3137 = ([&]() -> Value { auto fn3138 = s->Global("min"); Arguments args3139; args3139.Add(s->LocalAt(2), false); args3139.Keyword("key", Define(&Code_1086356f921902e593fb, s, Signature{{"xy"}, {}, {}, {}, "", "", ([]() -> std::span<const char* const> { static constexpr const char* names[] = {"xy"}; return names; }())}, true, "<lambda>")); return Call(c, fn3138, std::move(args3139)); }());
s->SetAt(1, v3137);
return ([&]() -> Value { auto v3149 = ([&]() -> Value { auto fn3150 = s->Global("_walk"); Arguments args3151; args3151.positional.reserve(2); args3151.Add(s->LocalAt(0), false); args3151.Add(s->LocalAt(1), false); return Call(c, fn3150, std::move(args3151)); }()); return Binary("Add", v3149, List({List({Value("DROP")})})); }());
return {};
}
}  // namespace kagg::opponents::compiled
