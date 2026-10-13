// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_181b59f18f058931bfc5(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"item", "self"};
s->PrepareSlots(s_names);
return ([&]() -> Value { auto fn398 = s->Global("sum"); Arguments args399; args399.Add(([&]() -> Value { auto comp400 = std::make_shared<Scope>(); comp400->globals = s->globals; comp400->parent = s; static constexpr const char* comp400_names[] = {"inv"}; comp400->PrepareSlots(comp400_names); auto result401 = List(); for (const auto& item402 : Iterate(Attribute(s->LocalAt(1), "invs"))) { comp400->SetAt(0, item402); result401.node()->sequence.push_back(([&]() -> Value { auto fn403 = comp400->Global("max"); Arguments args404; args404.positional.reserve(2); args404.Add(Value(int64_t{0}), false); args404.Add(([&]() -> Value { auto fn405 = comp400->Global("_int"); Arguments args406; args406.Add(([&]() -> Value { auto fn407 = comp400->Global("_get"); Arguments args408; args408.positional.reserve(3); args408.Add(comp400->LocalAt(0), false); args408.Add(comp400->Captured("item"), false); args408.Add(Value(int64_t{0}), false); return Call(c, fn407, std::move(args408)); }()), false); return Call(c, fn405, std::move(args406)); }()), false); return Call(c, fn403, std::move(args404)); }())); } return result401; }()), false); return Call(c, fn398, std::move(args399)); }());
return {};
}
}  // namespace kagg::opponents::compiled
