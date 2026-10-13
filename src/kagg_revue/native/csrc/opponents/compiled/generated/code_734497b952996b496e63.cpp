// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_734497b952996b496e63(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"baseline", "candidate", "new", "old"};
s->PrepareSlots(s_names);
if (static_cast<bool>(Get(s->LocalAt(1), Value("overflow_units")))) {
return Value(false);
}
for (const auto& item3083 : Iterate(([&]() -> Value { auto fn3084 = s->Global("zip"); Arguments args3085; args3085.positional.reserve(2); args3085.Add(Get(s->LocalAt(1), Value("rows")), false); args3085.Add(Get(s->LocalAt(0), Value("rows")), false); return Call(c, fn3084, std::move(args3085)); }()))) {
auto unpack3086 = Iterate(item3083);
ValidateUnpack(unpack3086, 2, false);
s->SetAt(2, unpack3086.at(0));
s->SetAt(3, unpack3086.at(1));
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto fn3087 = s->Global("_ge"); Arguments args3088; args3088.positional.reserve(2); args3088.Add(Get(s->LocalAt(2), Value("pre_market_shed")), false); args3088.Add(Get(s->LocalAt(3), Value("pre_market_shed")), false); return Call(c, fn3087, std::move(args3088)); }())))) {
return Value(false);
}
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto fn3089 = s->Global("_ge"); Arguments args3090; args3090.positional.reserve(2); args3090.Add(Get(s->LocalAt(2), Value("sold")), false); args3090.Add(Get(s->LocalAt(3), Value("sold")), false); return Call(c, fn3089, std::move(args3090)); }())))) {
return Value(false);
}
if (static_cast<bool>(([&]() -> Value { auto comp3091 = std::make_shared<Scope>(); comp3091->globals = s->globals; comp3091->parent = s; static constexpr const char* comp3091_names[] = {"a", "b"}; comp3091->PrepareSlots(comp3091_names); auto result3092 = List(); for (const auto& item3093 : Iterate(([&]() -> Value { auto fn3094 = s->Global("zip"); Arguments args3095; args3095.positional.reserve(2); args3095.Add(Get(s->LocalAt(2), Value("deposited_by_actor")), false); args3095.Add(Get(s->LocalAt(3), Value("deposited_by_actor")), false); return Call(c, fn3094, std::move(args3095)); }()))) { auto unpack3096 = Iterate(item3093); ValidateUnpack(unpack3096, 2, false); comp3091->SetAt(0, unpack3096.at(0)); comp3091->SetAt(1, unpack3096.at(1)); if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto fn3097 = comp3091->Global("_ge"); Arguments args3098; args3098.positional.reserve(2); args3098.Add(comp3091->LocalAt(0), false); args3098.Add(comp3091->LocalAt(1), false); return Call(c, fn3097, std::move(args3098)); }())))) return Value(true); } return Value(false); }()))) {
return Value(false);
}
}
return Value(true);
return {};
}
}  // namespace kagg::opponents::compiled
