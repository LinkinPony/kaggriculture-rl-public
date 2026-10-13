// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_1f1f83cc29b5e2a7b018(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "projected", "self", "step"};
s->PrepareSlots(s_names);
if (static_cast<bool>(([&]() -> Value { auto v1727 = s->LocalAt(3); Value v1728; v1728 = s->Global("LAST_ACT_STEP"); if (!static_cast<bool>(Binary("Lt", v1727, v1728))) return Value(false); v1727 = v1728; return Value(true); }()))) {
return Value{};
}
auto v1729 = Slice(([&]() -> Value { auto comp1730 = std::make_shared<Scope>(); comp1730->globals = s->globals; comp1730->parent = s; static constexpr const char* comp1730_names[] = {"item", "qty"}; comp1730->PrepareSlots(comp1730_names); auto result1731 = List(); for (const auto& item1732 : Iterate(([&]() -> Value { auto fn1733 = Attribute(s->LocalAt(1), "items"); Arguments args1734; return Call(c, fn1733, std::move(args1734)); }()))) { auto unpack1735 = Iterate(item1732); ValidateUnpack(unpack1735, 2, false); comp1730->SetAt(0, unpack1735.at(0)); comp1730->SetAt(1, unpack1735.at(1)); if (!static_cast<bool>(([&]() -> Value { auto v1736 = ([&]() -> Value { auto v1737 = comp1730->LocalAt(1); Value v1738; v1738 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v1737, v1738))) return Value(false); v1737 = v1738; return Value(true); }()); if (!static_cast<bool>(v1736)) return v1736; v1736 = ([&]() -> Value { auto v1739 = comp1730->LocalAt(0); Value v1740; v1740 = comp1730->Global("PRODUCTS"); if (!static_cast<bool>(Binary("In", v1739, v1740))) return Value(false); v1739 = v1740; return Value(true); }()); return v1736; }()))) continue; result1731.node()->sequence.push_back(List({Value("SELL"), comp1730->LocalAt(0), comp1730->LocalAt(1)})); } return result1731; }()), Value{}, Get(Attribute(s->LocalAt(2), "cfg"), Value("max_orders")), Value{});
Put(s->LocalAt(0), Value("market"), v1729);
return {};
}
}  // namespace kagg::opponents::compiled
