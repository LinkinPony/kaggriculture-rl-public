// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_1cec65720e5114d4abc6(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"access", "board", "half", "occ", "p", "positions"};
s->PrepareSlots(s_names);
auto v25049 = ([&]() -> Value { auto v25050 = s->LocalAt(1); return Binary("FloorDiv", v25050, Value(int64_t{2})); }());
s->SetAt(2, v25049);
auto v25051 = List({Tuple({([&]() -> Value { auto v25052 = s->LocalAt(2); return Binary("Sub", v25052, Value(int64_t{1})); }()), ([&]() -> Value { auto v25053 = s->LocalAt(2); return Binary("Sub", v25053, Value(int64_t{1})); }())}), Tuple({s->LocalAt(2), ([&]() -> Value { auto v25054 = s->LocalAt(2); return Binary("Sub", v25054, Value(int64_t{1})); }())}), Tuple({([&]() -> Value { auto v25055 = s->LocalAt(2); return Binary("Sub", v25055, Value(int64_t{1})); }()), s->LocalAt(2)}), Tuple({s->LocalAt(2), s->LocalAt(2)})});
s->SetAt(0, v25051);
auto v25056 = ([&]() -> Value { auto comp25057 = std::make_shared<Scope>(); comp25057->globals = s->globals; comp25057->parent = s; static constexpr const char* comp25057_names[] = {"a"}; comp25057->PrepareSlots(comp25057_names); auto result25058 = Dict(); for (const auto& item25059 : Iterate(s->LocalAt(0))) { comp25057->SetAt(0, item25059); Put(result25058, comp25057->LocalAt(0), Value(int64_t{0})); } return result25058; }());
s->SetAt(3, v25056);
for (const auto& item25060 : Iterate(s->LocalAt(5))) {
s->SetAt(4, item25060);
if (static_cast<bool>(([&]() -> Value { auto v25061 = ([&]() -> Value { auto fn25063 = s->Global("tuple"); Arguments args25064; args25064.Add(s->LocalAt(4), false); return Call(c, fn25063, std::move(args25064)); }()); Value v25062; v25062 = s->LocalAt(3); if (!static_cast<bool>(Binary("In", v25061, v25062))) return Value(false); v25061 = v25062; return Value(true); }()))) {
auto v25065 = s->LocalAt(3);
auto v25066 = ([&]() -> Value { auto fn25068 = s->Global("tuple"); Arguments args25069; args25069.Add(s->LocalAt(4), false); return Call(c, fn25068, std::move(args25069)); }());
auto v25067 = Get(v25065, v25066);
Put(v25065, v25066, Inplace("Add", v25067, Value(int64_t{1})));
}
}
return ([&]() -> Value { auto fn25070 = s->Global("list"); Arguments args25071; args25071.Add(([&]() -> Value { auto fn25072 = s->Global("min"); Arguments args25073; args25073.Add(s->LocalAt(0), false); args25073.Keyword("key", Define(&Code_11687f747d60c958da20, s, Signature{{"a"}, {}, {}, {}, "", "", ([]() -> std::span<const char* const> { static constexpr const char* names[] = {"a"}; return names; }())}, true, "<lambda>")); return Call(c, fn25072, std::move(args25073)); }()), false); return Call(c, fn25070, std::move(args25071)); }());
return {};
}
}  // namespace kagg::opponents::compiled
