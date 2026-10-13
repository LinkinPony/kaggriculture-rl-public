// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_b3c3f8771c5a643b1e9d(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"inherited_market", "items", "max_orders", "order", "orders", "shed"};
s->PrepareSlots(s_names);
auto v2736 = List({});
s->SetAt(1, v2736);
for (const auto& item2737 : Iterate(s->LocalAt(0))) {
s->SetAt(3, item2737);
if (static_cast<bool>(([&]() -> Value { auto v2738 = Get(s->LocalAt(3), Value(int64_t{1})); Value v2739; v2739 = s->LocalAt(1); if (!static_cast<bool>(Binary("NotIn", v2738, v2739))) return Value(false); v2738 = v2739; return Value(true); }()))) {
(void)([&]() -> Value { auto fn2740 = Attribute(s->LocalAt(1), "append"); Arguments args2741; args2741.Add(Get(s->LocalAt(3), Value(int64_t{1})), false); return Call(c, fn2740, std::move(args2741)); }());
}
}
auto v2742 = s->LocalAt(1);
s->SetAt(1, Inplace("Add", v2742, ([&]() -> Value { auto comp2743 = std::make_shared<Scope>(); comp2743->globals = s->globals; comp2743->parent = s; static constexpr const char* comp2743_names[] = {"item"}; comp2743->PrepareSlots(comp2743_names); auto result2744 = List(); for (const auto& item2745 : Iterate(s->Global("PRODUCTS"))) { comp2743->SetAt(0, item2745); if (!static_cast<bool>(([&]() -> Value { auto v2746 = comp2743->LocalAt(0); Value v2747; v2747 = comp2743->Captured("items"); if (!static_cast<bool>(Binary("NotIn", v2746, v2747))) return Value(false); v2746 = v2747; return Value(true); }()))) continue; result2744.node()->sequence.push_back(comp2743->LocalAt(0)); } return result2744; }())));
auto v2748 = ([&]() -> Value { auto comp2749 = std::make_shared<Scope>(); comp2749->globals = s->globals; comp2749->parent = s; static constexpr const char* comp2749_names[] = {"item"}; comp2749->PrepareSlots(comp2749_names); auto result2750 = List(); for (const auto& item2751 : Iterate(s->LocalAt(1))) { comp2749->SetAt(0, item2751); if (!static_cast<bool>(([&]() -> Value { auto v2752 = ([&]() -> Value { auto fn2754 = PrepareDictionaryGet(comp2749->Captured("shed")); Arguments args2755; args2755.positional.reserve(2); args2755.Add(comp2749->LocalAt(0), false); args2755.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn2754, std::move(args2755)); }()); Value v2753; v2753 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v2752, v2753))) return Value(false); v2752 = v2753; return Value(true); }()))) continue; result2750.node()->sequence.push_back(List({Value("SELL"), comp2749->LocalAt(0), ([&]() -> Value { auto fn2756 = comp2749->Global("int"); Arguments args2757; args2757.Add(([&]() -> Value { auto fn2758 = PrepareDictionaryGet(comp2749->Captured("shed")); Arguments args2759; args2759.positional.reserve(2); args2759.Add(comp2749->LocalAt(0), false); args2759.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn2758, std::move(args2759)); }()), false); return Call(c, fn2756, std::move(args2757)); }())})); } return result2750; }());
s->SetAt(4, v2748);
if (static_cast<bool>(([&]() -> Value { auto v2760 = ([&]() -> Value { auto fn2762 = s->Global("len"); Arguments args2763; args2763.Add(s->LocalAt(4), false); return Call(c, fn2762, std::move(args2763)); }()); Value v2761; v2761 = ([&]() -> Value { auto fn2764 = s->Global("min"); Arguments args2765; args2765.positional.reserve(2); args2765.Add(Value(int64_t{10}), false); args2765.Add(s->LocalAt(2), false); return Call(c, fn2764, std::move(args2765)); }()); if (!static_cast<bool>(Binary("Gt", v2760, v2761))) return Value(false); v2760 = v2761; return Value(true); }()))) {
Raise(([&]() -> Value { auto fn2766 = s->Global("Unsupported"); Arguments args2767; args2767.Add(Value("actual final stock exceeds order slots"), false); return Call(c, fn2766, std::move(args2767)); }()));
}
return s->LocalAt(4);
return {};
}
}  // namespace kagg::opponents::compiled
