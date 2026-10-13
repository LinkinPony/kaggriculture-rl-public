// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_4844caabf7b8586545fc(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"opponent_plan", "router", "routes", "self", "settings"};
s->PrepareSlots(s_names);
auto v410 = ([&]() -> Value { auto comp411 = std::make_shared<Scope>(); comp411->globals = s->globals; comp411->parent = s; static constexpr const char* comp411_names[] = {"rid", "tape"}; comp411->PrepareSlots(comp411_names); auto result412 = Dict(); for (const auto& item413 : Iterate(([&]() -> Value { auto fn414 = Attribute(s->LocalAt(2), "items"); Arguments args415; return Call(c, fn414, std::move(args415)); }()))) { auto unpack416 = Iterate(item413); ValidateUnpack(unpack416, 2, false); comp411->SetAt(0, unpack416.at(0)); comp411->SetAt(1, unpack416.at(1)); Put(result412, comp411->LocalAt(0), ([&]() -> Value { auto fn417 = comp411->Global("list"); Arguments args418; args418.Add(comp411->LocalAt(1), false); return Call(c, fn417, std::move(args418)); }())); } return result412; }());
SetAttribute(s->LocalAt(3), "routes", v410);
auto v419 = ([&]() -> Value { auto v420 = s->LocalAt(1); if (static_cast<bool>(v420)) return v420; v420 = Define(&Code_197c74236d7c0a5e20e9, s, Signature{{"observation", "step", "state"}, {}, {}, {}, "", "", ([]() -> std::span<const char* const> { static constexpr const char* names[] = {"observation", "state", "step"}; return names; }())}, true, "<lambda>"); return v420; }());
SetAttribute(s->LocalAt(3), "router", v419);
auto v425 = ([&]() -> Value { auto fn426 = s->Global("dict"); Arguments args427; args427.Add(s->Global("DEFAULT_SETTINGS"), false); return Call(c, fn426, std::move(args427)); }());
SetAttribute(s->LocalAt(3), "cfg", v425);
(void)([&]() -> Value { auto fn428 = Attribute(Attribute(s->LocalAt(3), "cfg"), "update"); Arguments args429; args429.Add(([&]() -> Value { auto v430 = s->LocalAt(4); if (static_cast<bool>(v430)) return v430; v430 = ([&]() -> Value { auto dict431 = Dict(); return dict431; }()); return v430; }()), false); return Call(c, fn428, std::move(args429)); }());
auto v432 = s->LocalAt(0);
SetAttribute(s->LocalAt(3), "opponent_plan", v432);
auto v433 = ([&]() -> Value { auto dict434 = Dict(); return dict434; }());
SetAttribute(s->LocalAt(3), "players", v433);
auto v435 = ([&]() -> Value { auto dict436 = Dict(); auto key437 = Value("layer_fallbacks"); Put(dict436, key437, Value(int64_t{0})); auto key438 = Value("entry_fallbacks"); Put(dict436, key438, Value(int64_t{0})); return dict436; }());
SetAttribute(s->LocalAt(3), "diagnostics", v435);
auto v439 = ([&]() -> Value { auto dict440 = Dict(); return dict440; }());
SetAttribute(s->LocalAt(3), "_future_sells", v439);
return {};
}
}  // namespace kagg::opponents::compiled
