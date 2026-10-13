// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_3cfe37e0333f18bb3ead(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"access", "board", "half", "occ", "p", "positions"};
s->PrepareSlots(s_names);
auto v21736 = ([&]() -> Value { auto v21737 = s->LocalAt(1); return Binary("FloorDiv", v21737, Value(int64_t{2})); }());
s->SetAt(2, v21736);
auto v21738 = List({Tuple({([&]() -> Value { auto v21739 = s->LocalAt(2); return Binary("Sub", v21739, Value(int64_t{1})); }()), ([&]() -> Value { auto v21740 = s->LocalAt(2); return Binary("Sub", v21740, Value(int64_t{1})); }())}), Tuple({s->LocalAt(2), ([&]() -> Value { auto v21741 = s->LocalAt(2); return Binary("Sub", v21741, Value(int64_t{1})); }())}), Tuple({([&]() -> Value { auto v21742 = s->LocalAt(2); return Binary("Sub", v21742, Value(int64_t{1})); }()), s->LocalAt(2)}), Tuple({s->LocalAt(2), s->LocalAt(2)})});
s->SetAt(0, v21738);
auto v21743 = ([&]() -> Value { auto comp21744 = std::make_shared<Scope>(); comp21744->globals = s->globals; comp21744->parent = s; static constexpr const char* comp21744_names[] = {"a"}; comp21744->PrepareSlots(comp21744_names); auto result21745 = Dict(); for (const auto& item21746 : Iterate(s->LocalAt(0))) { comp21744->SetAt(0, item21746); Put(result21745, comp21744->LocalAt(0), Value(int64_t{0})); } return result21745; }());
s->SetAt(3, v21743);
for (const auto& item21747 : Iterate(s->LocalAt(5))) {
s->SetAt(4, item21747);
if (static_cast<bool>(([&]() -> Value { auto v21748 = ([&]() -> Value { auto fn21750 = s->Global("tuple"); Arguments args21751; args21751.Add(s->LocalAt(4), false); return Call(c, fn21750, std::move(args21751)); }()); Value v21749; v21749 = s->LocalAt(3); if (!static_cast<bool>(Binary("In", v21748, v21749))) return Value(false); v21748 = v21749; return Value(true); }()))) {
auto v21752 = s->LocalAt(3);
auto v21753 = ([&]() -> Value { auto fn21755 = s->Global("tuple"); Arguments args21756; args21756.Add(s->LocalAt(4), false); return Call(c, fn21755, std::move(args21756)); }());
auto v21754 = Get(v21752, v21753);
Put(v21752, v21753, Inplace("Add", v21754, Value(int64_t{1})));
}
}
return ([&]() -> Value { auto fn21757 = s->Global("list"); Arguments args21758; args21758.Add(([&]() -> Value { auto fn21759 = s->Global("min"); Arguments args21760; args21760.Add(s->LocalAt(0), false); args21760.Keyword("key", Define(&Code_11687f747d60c958da20, s, Signature{{"a"}, {}, {}, {}, "", "", ([]() -> std::span<const char* const> { static constexpr const char* names[] = {"a"}; return names; }())}, true, "<lambda>")); return Call(c, fn21759, std::move(args21760)); }()), false); return Call(c, fn21757, std::move(args21758)); }());
return {};
}
}  // namespace kagg::opponents::compiled
