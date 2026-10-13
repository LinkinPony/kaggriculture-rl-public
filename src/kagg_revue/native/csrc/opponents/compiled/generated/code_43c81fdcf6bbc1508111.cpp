// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_43c81fdcf6bbc1508111(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "day", "extra", "have", "item", "o", "planned", "projected", "route", "self", "step", "surplus", "view"};
s->PrepareSlots(s_names);
auto v1670 = ([&]() -> Value { auto dict1671 = Dict(); return dict1671; }());
s->SetAt(6, v1670);
for (const auto& item1672 : Iterate(([&]() -> Value { auto v1673 = ([&]() -> Value { auto fn1674 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args1675; args1675.Add(Value("market"), false); return CallDictionaryGet(c, fn1674, std::move(args1675)); }()); if (static_cast<bool>(v1673)) return v1673; v1673 = List({}); return v1673; }()))) {
s->SetAt(5, item1672);
if (static_cast<bool>(([&]() -> Value { auto v1676 = s->LocalAt(5); if (!static_cast<bool>(v1676)) return v1676; v1676 = ([&]() -> Value { auto v1677 = Get(s->LocalAt(5), Value(int64_t{0})); Value v1678; v1678 = Value("SELL"); if (!static_cast<bool>(Binary("Eq", v1677, v1678))) return Value(false); v1677 = v1678; return Value(true); }()); if (!static_cast<bool>(v1676)) return v1676; v1676 = ([&]() -> Value { auto v1679 = ([&]() -> Value { auto fn1681 = s->Global("len"); Arguments args1682; args1682.Add(s->LocalAt(5), false); return Call(c, fn1681, std::move(args1682)); }()); Value v1680; v1680 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v1679, v1680))) return Value(false); v1679 = v1680; return Value(true); }()); return v1676; }()))) {
auto v1683 = ([&]() -> Value { auto v1684 = ([&]() -> Value { auto fn1685 = PrepareDictionaryGet(s->LocalAt(6)); Arguments args1686; args1686.positional.reserve(2); args1686.Add(Get(s->LocalAt(5), Value(int64_t{1})), false); args1686.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn1685, std::move(args1686)); }()); return Binary("Add", v1684, ([&]() -> Value { auto fn1687 = s->Global("_int"); Arguments args1688; args1688.Add(Get(s->LocalAt(5), Value(int64_t{2})), false); return Call(c, fn1687, std::move(args1688)); }())); }());
Put(s->LocalAt(6), Get(s->LocalAt(5), Value(int64_t{1})), v1683);
}
}
auto v1689 = ([&]() -> Value { auto v1690 = s->LocalAt(10); return Binary("FloorDiv", v1690, Get(Attribute(s->LocalAt(9), "cfg"), Value("turns_per_day"))); }());
s->SetAt(1, v1689);
auto v1691 = List({});
s->SetAt(2, v1691);
for (const auto& item1692 : Iterate(s->Global("PRODUCTS"))) {
s->SetAt(4, item1692);
auto v1693 = ([&]() -> Value { auto v1694 = ([&]() -> Value { auto fn1695 = PrepareDictionaryGet(s->LocalAt(7)); Arguments args1696; args1696.positional.reserve(2); args1696.Add(s->LocalAt(4), false); args1696.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn1695, std::move(args1696)); }()); return Binary("Sub", v1694, ([&]() -> Value { auto fn1697 = PrepareDictionaryGet(s->LocalAt(6)); Arguments args1698; args1698.positional.reserve(2); args1698.Add(s->LocalAt(4), false); args1698.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn1697, std::move(args1698)); }())); }());
s->SetAt(3, v1693);
if (static_cast<bool>(([&]() -> Value { auto v1699 = s->LocalAt(3); Value v1700; v1700 = Value(int64_t{0}); if (!static_cast<bool>(Binary("LtE", v1699, v1700))) return Value(false); v1699 = v1700; return Value(true); }()))) {
continue;
}
auto v1701 = (static_cast<bool>(([&]() -> Value { auto v1702 = s->LocalAt(1); Value v1703; v1703 = Value(int64_t{29}); if (!static_cast<bool>(Binary("GtE", v1702, v1703))) return Value(false); v1702 = v1703; return Value(true); }())) ? s->LocalAt(3) : ([&]() -> Value { auto v1704 = s->LocalAt(3); return Binary("Sub", v1704, ([&]() -> Value { auto fn1705 = Attribute(s->LocalAt(9), "future_sells"); Arguments args1706; args1706.positional.reserve(3); args1706.Add(s->LocalAt(8), false); args1706.Add(s->LocalAt(4), false); args1706.Add(([&]() -> Value { auto v1707 = s->LocalAt(10); return Binary("Add", v1707, Value(int64_t{1})); }()), false); return Call(c, fn1705, std::move(args1706)); }())); }()));
s->SetAt(11, v1701);
if (static_cast<bool>(([&]() -> Value { auto v1708 = ([&]() -> Value { auto v1709 = s->LocalAt(11); Value v1710; v1710 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v1709, v1710))) return Value(false); v1709 = v1710; return Value(true); }()); if (!static_cast<bool>(v1708)) return v1708; v1708 = ([&]() -> Value { auto v1711 = ([&]() -> Value { auto fn1713 = PrepareDictionaryGet(Attribute(s->LocalAt(12), "prices")); Arguments args1714; args1714.positional.reserve(2); args1714.Add(s->LocalAt(4), false); args1714.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn1713, std::move(args1714)); }()); Value v1712; v1712 = Value(int64_t{1}); if (!static_cast<bool>(Binary("Gt", v1711, v1712))) return Value(false); v1711 = v1712; return Value(true); }()); return v1708; }()))) {
(void)([&]() -> Value { auto fn1715 = Attribute(s->LocalAt(2), "append"); Arguments args1716; args1716.Add(List({Value("SELL"), s->LocalAt(4), s->LocalAt(11)}), false); return Call(c, fn1715, std::move(args1716)); }());
}
}
(void)([&]() -> Value { auto fn1717 = Attribute(s->LocalAt(2), "sort"); Arguments args1718; args1718.Keyword("key", Define(&Code_d78a80d0729f6c751328, s, Signature{{"o"}, {}, {}, {}, "", "", ([]() -> std::span<const char* const> { static constexpr const char* names[] = {"o"}; return names; }())}, true, "<lambda>")); return Call(c, fn1717, std::move(args1718)); }());
auto v1722 = ([&]() -> Value { auto v1723 = ([&]() -> Value { auto v1724 = ([&]() -> Value { auto fn1725 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args1726; args1726.Add(Value("market"), false); return CallDictionaryGet(c, fn1725, std::move(args1726)); }()); if (static_cast<bool>(v1724)) return v1724; v1724 = List({}); return v1724; }()); return Binary("Add", v1723, s->LocalAt(2)); }());
Put(s->LocalAt(0), Value("market"), v1722);
return {};
}
}  // namespace kagg::opponents::compiled
