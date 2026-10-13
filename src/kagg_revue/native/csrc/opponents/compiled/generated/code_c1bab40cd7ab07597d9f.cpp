// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_c1bab40cd7ab07597d9f(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "avail", "have", "kept", "n", "o", "projected"};
s->PrepareSlots(s_names);
auto v1622 = ([&]() -> Value { auto fn1623 = s->Global("dict"); Arguments args1624; args1624.Add(s->LocalAt(6), false); return Call(c, fn1623, std::move(args1624)); }());
s->SetAt(1, v1622);
auto v1625 = List({});
s->SetAt(3, v1625);
for (const auto& item1626 : Iterate(([&]() -> Value { auto v1627 = ([&]() -> Value { auto fn1628 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args1629; args1629.Add(Value("market"), false); return CallDictionaryGet(c, fn1628, std::move(args1629)); }()); if (static_cast<bool>(v1627)) return v1627; v1627 = List({}); return v1627; }()))) {
s->SetAt(5, item1626);
if (static_cast<bool>(([&]() -> Value { auto v1630 = s->LocalAt(5); if (!static_cast<bool>(v1630)) return v1630; v1630 = ([&]() -> Value { auto v1631 = Get(s->LocalAt(5), Value(int64_t{0})); Value v1632; v1632 = Value("SELL"); if (!static_cast<bool>(Binary("Eq", v1631, v1632))) return Value(false); v1631 = v1632; return Value(true); }()); if (!static_cast<bool>(v1630)) return v1630; v1630 = ([&]() -> Value { auto v1633 = ([&]() -> Value { auto fn1635 = s->Global("len"); Arguments args1636; args1636.Add(s->LocalAt(5), false); return Call(c, fn1635, std::move(args1636)); }()); Value v1634; v1634 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v1633, v1634))) return Value(false); v1633 = v1634; return Value(true); }()); return v1630; }()))) {
auto v1637 = ([&]() -> Value { auto fn1638 = PrepareDictionaryGet(s->LocalAt(1)); Arguments args1639; args1639.positional.reserve(2); args1639.Add(Get(s->LocalAt(5), Value(int64_t{1})), false); args1639.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn1638, std::move(args1639)); }());
s->SetAt(2, v1637);
auto v1640 = ([&]() -> Value { auto fn1641 = s->Global("min"); Arguments args1642; args1642.positional.reserve(2); args1642.Add(([&]() -> Value { auto fn1643 = s->Global("_int"); Arguments args1644; args1644.Add(Get(s->LocalAt(5), Value(int64_t{2})), false); return Call(c, fn1643, std::move(args1644)); }()), false); args1642.Add(s->LocalAt(2), false); return Call(c, fn1641, std::move(args1642)); }());
s->SetAt(4, v1640);
auto v1645 = ([&]() -> Value { auto fn1646 = s->Global("max"); Arguments args1647; args1647.positional.reserve(2); args1647.Add(Value(int64_t{0}), false); args1647.Add(s->LocalAt(4), false); return Call(c, fn1646, std::move(args1647)); }());
s->SetAt(4, v1645);
auto v1648 = ([&]() -> Value { auto v1649 = s->LocalAt(2); return Binary("Sub", v1649, s->LocalAt(4)); }());
Put(s->LocalAt(1), Get(s->LocalAt(5), Value(int64_t{1})), v1648);
(void)([&]() -> Value { auto fn1650 = Attribute(s->LocalAt(3), "append"); Arguments args1651; args1651.Add(List({Value("SELL"), Get(s->LocalAt(5), Value(int64_t{1})), s->LocalAt(4)}), false); return Call(c, fn1650, std::move(args1651)); }());
}
else {
(void)([&]() -> Value { auto fn1652 = Attribute(s->LocalAt(3), "append"); Arguments args1653; args1653.Add(s->LocalAt(5), false); return Call(c, fn1652, std::move(args1653)); }());
if (static_cast<bool>(([&]() -> Value { auto v1654 = s->LocalAt(5); if (!static_cast<bool>(v1654)) return v1654; v1654 = ([&]() -> Value { auto v1655 = Get(s->LocalAt(5), Value(int64_t{0})); Value v1656; v1656 = Tuple({Value("BUY_PRODUCT"), Value("BUY_ANIMAL")}); if (!static_cast<bool>(Binary("In", v1655, v1656))) return Value(false); v1655 = v1656; return Value(true); }()); if (!static_cast<bool>(v1654)) return v1654; v1654 = ([&]() -> Value { auto v1657 = ([&]() -> Value { auto fn1659 = s->Global("len"); Arguments args1660; args1660.Add(s->LocalAt(5), false); return Call(c, fn1659, std::move(args1660)); }()); Value v1658; v1658 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v1657, v1658))) return Value(false); v1657 = v1658; return Value(true); }()); return v1654; }()))) {
auto v1661 = ([&]() -> Value { auto v1662 = ([&]() -> Value { auto fn1663 = PrepareDictionaryGet(s->LocalAt(1)); Arguments args1664; args1664.positional.reserve(2); args1664.Add(Get(s->LocalAt(5), Value(int64_t{1})), false); args1664.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn1663, std::move(args1664)); }()); return Binary("Add", v1662, ([&]() -> Value { auto fn1665 = s->Global("max"); Arguments args1666; args1666.positional.reserve(2); args1666.Add(Value(int64_t{0}), false); args1666.Add(([&]() -> Value { auto fn1667 = s->Global("_int"); Arguments args1668; args1668.Add(Get(s->LocalAt(5), Value(int64_t{2})), false); return Call(c, fn1667, std::move(args1668)); }()), false); return Call(c, fn1665, std::move(args1666)); }())); }());
Put(s->LocalAt(1), Get(s->LocalAt(5), Value(int64_t{1})), v1661);
}
}
}
auto v1669 = s->LocalAt(3);
Put(s->LocalAt(0), Value("market"), v1669);
return {};
}
}  // namespace kagg::opponents::compiled
