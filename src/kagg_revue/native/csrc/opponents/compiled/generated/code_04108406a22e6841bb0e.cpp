// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_04108406a22e6841bb0e(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"current", "index", "inventory", "item", "observation", "order", "orders", "own_orders", "pair", "params", "quantity", "quote", "revenue", "rival_orders", "side", "sold", "stock", "stocks"};
s->PrepareSlots(s_names);
auto v15731 = ([&]() -> Value { auto fn15732 = s->Global("dict"); Arguments args15733; args15733.Add(Get(Get(s->LocalAt(4), Value("market")), Value("inventory")), false); return Call(c, fn15732, std::move(args15733)); }());
s->SetAt(2, v15731);
auto v15734 = ([&]() -> Value { auto fn15735 = s->Global("_r132_price_params"); Arguments args15736; args15736.Add(s->LocalAt(4), false); return Call(c, fn15735, std::move(args15736)); }());
s->SetAt(9, v15734);
auto v15737 = List({([&]() -> Value { auto fn15738 = s->Global("dict"); Arguments args15739; args15739.Add(s->LocalAt(16), false); return Call(c, fn15738, std::move(args15739)); }()), ([&]() -> Value { auto fn15740 = s->Global("dict"); Arguments args15741; args15741.Add(s->LocalAt(16), false); return Call(c, fn15740, std::move(args15741)); }())});
s->SetAt(17, v15737);
auto v15742 = Value(int64_t{0});
s->SetAt(12, v15742);
for (const auto& item15743 : Iterate(([&]() -> Value { auto fn15744 = s->Global("range"); Arguments args15745; args15745.Add(([&]() -> Value { auto fn15746 = s->Global("max"); Arguments args15747; args15747.positional.reserve(2); args15747.Add(([&]() -> Value { auto fn15748 = s->Global("len"); Arguments args15749; args15749.Add(s->LocalAt(7), false); return Call(c, fn15748, std::move(args15749)); }()), false); args15747.Add(([&]() -> Value { auto fn15750 = s->Global("len"); Arguments args15751; args15751.Add(s->LocalAt(13), false); return Call(c, fn15750, std::move(args15751)); }()), false); return Call(c, fn15746, std::move(args15747)); }()), false); return Call(c, fn15744, std::move(args15745)); }()))) {
s->SetAt(1, item15743);
auto v15752 = List({});
s->SetAt(8, v15752);
for (const auto& item15753 : Iterate(([&]() -> Value { auto fn15754 = s->Global("enumerate"); Arguments args15755; args15755.Add(Tuple({s->LocalAt(7), s->LocalAt(13)}), false); return Call(c, fn15754, std::move(args15755)); }()))) {
auto unpack15756 = Iterate(item15753);
ValidateUnpack(unpack15756, 2, false);
s->SetAt(14, unpack15756.at(0));
s->SetAt(6, unpack15756.at(1));
if (static_cast<bool>(([&]() -> Value { auto v15757 = s->LocalAt(1); Value v15758; v15758 = ([&]() -> Value { auto fn15759 = s->Global("len"); Arguments args15760; args15760.Add(s->LocalAt(6), false); return Call(c, fn15759, std::move(args15760)); }()); if (!static_cast<bool>(Binary("GtE", v15757, v15758))) return Value(false); v15757 = v15758; return Value(true); }()))) {
(void)([&]() -> Value { auto fn15761 = Attribute(s->LocalAt(8), "append"); Arguments args15762; args15762.Add(Value{}, false); return Call(c, fn15761, std::move(args15762)); }());
continue;
}
auto v15763 = Get(s->LocalAt(6), s->LocalAt(1));
s->SetAt(5, v15763);
if (static_cast<bool>(([&]() -> Value { auto v15764 = Unary("Not", s->LocalAt(5)); if (static_cast<bool>(v15764)) return v15764; v15764 = ([&]() -> Value { auto v15765 = ([&]() -> Value { auto fn15767 = s->Global("len"); Arguments args15768; args15768.Add(s->LocalAt(5), false); return Call(c, fn15767, std::move(args15768)); }()); Value v15766; v15766 = Value(int64_t{3}); if (!static_cast<bool>(Binary("Lt", v15765, v15766))) return Value(false); v15765 = v15766; return Value(true); }()); if (static_cast<bool>(v15764)) return v15764; v15764 = ([&]() -> Value { auto v15769 = Get(s->LocalAt(5), Value(int64_t{0})); Value v15770; v15770 = Value("SELL"); if (!static_cast<bool>(Binary("NotEq", v15769, v15770))) return Value(false); v15769 = v15770; return Value(true); }()); return v15764; }()))) {
(void)([&]() -> Value { auto fn15771 = Attribute(s->LocalAt(8), "append"); Arguments args15772; args15772.Add(Value{}, false); return Call(c, fn15771, std::move(args15772)); }());
continue;
}
auto v15773 = Get(s->LocalAt(5), Value(int64_t{1}));
s->SetAt(3, v15773);
auto v15774 = ([&]() -> Value { auto fn15775 = s->Global("min"); Arguments args15776; args15776.positional.reserve(2); args15776.Add(([&]() -> Value { auto fn15777 = s->Global("max"); Arguments args15778; args15778.positional.reserve(2); args15778.Add(Value(int64_t{0}), false); args15778.Add(([&]() -> Value { auto fn15779 = s->Global("int"); Arguments args15780; args15780.Add(Get(s->LocalAt(5), Value(int64_t{2})), false); return Call(c, fn15779, std::move(args15780)); }()), false); return Call(c, fn15777, std::move(args15778)); }()), false); args15776.Add(([&]() -> Value { auto fn15781 = s->Global("max"); Arguments args15782; args15782.positional.reserve(2); args15782.Add(Value(int64_t{0}), false); args15782.Add(([&]() -> Value { auto fn15783 = s->Global("int"); Arguments args15784; args15784.Add(([&]() -> Value { auto fn15785 = PrepareDictionaryGet(Get(s->LocalAt(17), s->LocalAt(14))); Arguments args15786; args15786.positional.reserve(2); args15786.Add(s->LocalAt(3), false); args15786.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn15785, std::move(args15786)); }()), false); return Call(c, fn15783, std::move(args15784)); }()), false); return Call(c, fn15781, std::move(args15782)); }()), false); return Call(c, fn15775, std::move(args15776)); }());
s->SetAt(10, v15774);
(void)([&]() -> Value { auto fn15787 = Attribute(s->LocalAt(8), "append"); Arguments args15788; args15788.Add(List({s->LocalAt(3), s->LocalAt(10)}), false); return Call(c, fn15787, std::move(args15788)); }());
}
while (static_cast<bool>(([&]() -> Value { auto comp15789 = std::make_shared<Scope>(); comp15789->globals = s->globals; comp15789->parent = s; static constexpr const char* comp15789_names[] = {"current"}; comp15789->PrepareSlots(comp15789_names); auto result15790 = List(); for (const auto& item15791 : Iterate(s->LocalAt(8))) { comp15789->SetAt(0, item15791); if (static_cast<bool>(([&]() -> Value { auto v15792 = ([&]() -> Value { auto v15793 = comp15789->LocalAt(0); Value v15794; v15794 = Value{}; if (!static_cast<bool>(Binary("IsNot", v15793, v15794))) return Value(false); v15793 = v15794; return Value(true); }()); if (!static_cast<bool>(v15792)) return v15792; v15792 = ([&]() -> Value { auto v15795 = Get(comp15789->LocalAt(0), Value(int64_t{1})); Value v15796; v15796 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v15795, v15796))) return Value(false); v15795 = v15796; return Value(true); }()); return v15792; }()))) return Value(true); } return Value(false); }()))) {
auto v15797 = List({});
s->SetAt(15, v15797);
for (const auto& item15798 : Iterate(([&]() -> Value { auto fn15799 = s->Global("enumerate"); Arguments args15800; args15800.Add(s->LocalAt(8), false); return Call(c, fn15799, std::move(args15800)); }()))) {
auto unpack15801 = Iterate(item15798);
ValidateUnpack(unpack15801, 2, false);
s->SetAt(14, unpack15801.at(0));
s->SetAt(0, unpack15801.at(1));
if (static_cast<bool>(([&]() -> Value { auto v15802 = ([&]() -> Value { auto v15803 = s->LocalAt(0); Value v15804; v15804 = Value{}; if (!static_cast<bool>(Binary("Is", v15803, v15804))) return Value(false); v15803 = v15804; return Value(true); }()); if (static_cast<bool>(v15802)) return v15802; v15802 = ([&]() -> Value { auto v15805 = Get(s->LocalAt(0), Value(int64_t{1})); Value v15806; v15806 = Value(int64_t{0}); if (!static_cast<bool>(Binary("LtE", v15805, v15806))) return Value(false); v15805 = v15806; return Value(true); }()); return v15802; }()))) {
continue;
}
auto v15807 = Get(s->LocalAt(0), Value(int64_t{0}));
s->SetAt(3, v15807);
auto v15808 = ([&]() -> Value { auto fn15809 = s->Global("_r37_market_price"); Arguments args15810; args15810.positional.reserve(3); args15810.Add(s->LocalAt(3), false); args15810.Add(Get(s->LocalAt(2), s->LocalAt(3)), false); args15810.Add(s->LocalAt(9), false); return Call(c, fn15809, std::move(args15810)); }());
s->SetAt(11, v15808);
if (static_cast<bool>(([&]() -> Value { auto v15811 = s->LocalAt(14); Value v15812; v15812 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v15811, v15812))) return Value(false); v15811 = v15812; return Value(true); }()))) {
auto v15813 = s->LocalAt(12);
s->SetAt(12, Inplace("Add", v15813, s->LocalAt(11)));
}
auto v15814 = s->LocalAt(0);
auto v15815 = Value(int64_t{1});
auto v15816 = Get(v15814, v15815);
Put(v15814, v15815, Inplace("Sub", v15816, Value(int64_t{1})));
auto v15817 = ([&]() -> Value { auto fn15818 = s->Global("max"); Arguments args15819; args15819.positional.reserve(2); args15819.Add(Value(int64_t{0}), false); args15819.Add(([&]() -> Value { auto v15820 = ([&]() -> Value { auto fn15821 = PrepareDictionaryGet(Get(s->LocalAt(17), s->LocalAt(14))); Arguments args15822; args15822.positional.reserve(2); args15822.Add(s->LocalAt(3), false); args15822.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn15821, std::move(args15822)); }()); return Binary("Sub", v15820, Value(int64_t{1})); }()), false); return Call(c, fn15818, std::move(args15819)); }());
Put(Get(s->LocalAt(17), s->LocalAt(14)), s->LocalAt(3), v15817);
(void)([&]() -> Value { auto fn15823 = Attribute(s->LocalAt(15), "append"); Arguments args15824; args15824.Add(Tuple({s->LocalAt(3), s->LocalAt(11)}), false); return Call(c, fn15823, std::move(args15824)); }());
}
for (const auto& item15825 : Iterate(s->LocalAt(15))) {
auto unpack15826 = Iterate(item15825);
ValidateUnpack(unpack15826, 2, false);
s->SetAt(3, unpack15826.at(0));
s->SetAt(11, unpack15826.at(1));
if (static_cast<bool>(([&]() -> Value { auto v15827 = s->LocalAt(11); Value v15828; v15828 = Value(int64_t{1}); if (!static_cast<bool>(Binary("Gt", v15827, v15828))) return Value(false); v15827 = v15828; return Value(true); }()))) {
auto v15829 = s->LocalAt(2);
auto v15830 = s->LocalAt(3);
auto v15831 = Get(v15829, v15830);
Put(v15829, v15830, Inplace("Add", v15831, Value(int64_t{1})));
}
}
}
}
return s->LocalAt(12);
return {};
}
}  // namespace kagg::opponents::compiled
