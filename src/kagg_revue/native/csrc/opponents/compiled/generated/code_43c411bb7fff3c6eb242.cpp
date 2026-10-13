// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_43c411bb7fff3c6eb242(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "key", "result", "schedule", "value"};
s->PrepareSlots(s_names);
auto v2637 = List({});
s->SetAt(2, v2637);
for (const auto& item2638 : Iterate(s->LocalAt(3))) {
s->SetAt(0, item2638);
auto v2639 = ([&]() -> Value { auto fn2640 = s->Global("dict"); Arguments args2641; args2641.Add(s->LocalAt(0), false); return Call(c, fn2640, std::move(args2641)); }());
s->SetAt(4, v2639);
if (static_cast<bool>(([&]() -> Value { auto v2642 = Value("farmer"); Value v2643; v2643 = s->LocalAt(0); if (!static_cast<bool>(Binary("In", v2642, v2643))) return Value(false); v2642 = v2643; return Value(true); }()))) {
auto v2644 = ([&]() -> Value { auto fn2645 = s->Global("list"); Arguments args2646; args2646.Add(Get(s->LocalAt(0), Value("farmer")), false); return Call(c, fn2645, std::move(args2646)); }());
Put(s->LocalAt(4), Value("farmer"), v2644);
}
for (const auto& item2647 : Iterate(List({Value("hands"), Value("market")}))) {
s->SetAt(1, item2647);
if (static_cast<bool>(([&]() -> Value { auto v2648 = s->LocalAt(1); Value v2649; v2649 = s->LocalAt(0); if (!static_cast<bool>(Binary("In", v2648, v2649))) return Value(false); v2648 = v2649; return Value(true); }()))) {
auto v2650 = ([&]() -> Value { auto comp2651 = std::make_shared<Scope>(); comp2651->globals = s->globals; comp2651->parent = s; static constexpr const char* comp2651_names[] = {"command"}; comp2651->PrepareSlots(comp2651_names); auto result2652 = List(); for (const auto& item2653 : Iterate(Get(s->LocalAt(0), s->LocalAt(1)))) { comp2651->SetAt(0, item2653); result2652.node()->sequence.push_back(([&]() -> Value { auto fn2654 = comp2651->Global("list"); Arguments args2655; args2655.Add(comp2651->LocalAt(0), false); return Call(c, fn2654, std::move(args2655)); }())); } return result2652; }());
Put(s->LocalAt(4), s->LocalAt(1), v2650);
}
}
(void)([&]() -> Value { auto fn2656 = Attribute(s->LocalAt(2), "append"); Arguments args2657; args2657.Add(s->LocalAt(4), false); return Call(c, fn2656, std::move(args2657)); }());
}
return s->LocalAt(2);
return {};
}
}  // namespace kagg::opponents::compiled
