// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_59d3508d805c604d8635(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "expected", "hands", "self", "view"};
s->PrepareSlots(s_names);
auto v617 = ([&]() -> Value { auto fn618 = s->Global("max"); Arguments args619; args619.positional.reserve(2); args619.Add(Value(int64_t{0}), false); args619.Add(([&]() -> Value { auto v620 = ([&]() -> Value { auto fn621 = s->Global("len"); Arguments args622; args622.Add(Attribute(s->LocalAt(4), "positions"), false); return Call(c, fn621, std::move(args622)); }()); return Binary("Sub", v620, Value(int64_t{1})); }()), false); return Call(c, fn618, std::move(args619)); }());
s->SetAt(1, v617);
auto v623 = ([&]() -> Value { auto fn624 = s->Global("list"); Arguments args625; args625.Add(([&]() -> Value { auto v626 = ([&]() -> Value { auto fn627 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args628; args628.Add(Value("hands"), false); return CallDictionaryGet(c, fn627, std::move(args628)); }()); if (static_cast<bool>(v626)) return v626; v626 = List({}); return v626; }()), false); return Call(c, fn624, std::move(args625)); }());
s->SetAt(2, v623);
(void)([&]() -> Value { auto fn629 = Attribute(s->LocalAt(2), "extend"); Arguments args630; args630.Add(([&]() -> Value { auto comp631 = std::make_shared<Scope>(); comp631->globals = s->globals; comp631->parent = s; static constexpr const char* comp631_names[] = {"_"}; comp631->PrepareSlots(comp631_names); auto result632 = List(); for (const auto& item633 : Iterate(([&]() -> Value { auto fn634 = s->Global("range"); Arguments args635; args635.Add(([&]() -> Value { auto fn636 = s->Global("max"); Arguments args637; args637.positional.reserve(2); args637.Add(Value(int64_t{0}), false); args637.Add(([&]() -> Value { auto v638 = s->LocalAt(1); return Binary("Sub", v638, ([&]() -> Value { auto fn639 = s->Global("len"); Arguments args640; args640.Add(s->LocalAt(2), false); return Call(c, fn639, std::move(args640)); }())); }()), false); return Call(c, fn636, std::move(args637)); }()), false); return Call(c, fn634, std::move(args635)); }()))) { comp631->SetAt(0, item633); result632.node()->sequence.push_back(List({Value("PASS")})); } return result632; }()), false); return Call(c, fn629, std::move(args630)); }());
auto v641 = Slice(s->LocalAt(2), Value{}, s->LocalAt(1), Value{});
Put(s->LocalAt(0), Value("hands"), v641);
return {};
}
}  // namespace kagg::opponents::compiled
