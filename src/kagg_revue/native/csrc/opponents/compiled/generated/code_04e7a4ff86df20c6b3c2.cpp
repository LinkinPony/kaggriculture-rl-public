// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_04e7a4ff86df20c6b3c2(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"configuration", "farms", "hands", "observation", "player", "step", "tape"};
s->PrepareSlots(s_names);
try {
return ([&]() -> Value { auto fn1745 = Attribute(s->Captured("chassis"), "act"); Arguments args1746; args1746.positional.reserve(2); args1746.Add(s->LocalAt(3), false); args1746.Add(s->LocalAt(0), false); return Call(c, fn1745, std::move(args1746)); }());
} catch (const Error& error1744) {
if (Matches(error1744, s->Global("Exception"))) {
auto v1747 = Attribute(s->Captured("chassis"), "diagnostics");
auto v1748 = Value("entry_fallbacks");
auto v1749 = Get(v1747, v1748);
Put(v1747, v1748, Inplace("Add", v1749, Value(int64_t{1})));
try {
auto v1751 = ([&]() -> Value { auto fn1752 = s->Global("_step_of"); Arguments args1753; args1753.Add(s->LocalAt(3), false); return Call(c, fn1752, std::move(args1753)); }());
s->SetAt(5, v1751);
auto v1754 = ([&]() -> Value { auto fn1755 = s->Global("_int"); Arguments args1756; args1756.Add(([&]() -> Value { auto fn1757 = s->Global("_get"); Arguments args1758; args1758.positional.reserve(3); args1758.Add(s->LocalAt(3), false); args1758.Add(Value("player"), false); args1758.Add(Value(int64_t{0}), false); return Call(c, fn1757, std::move(args1758)); }()), false); return Call(c, fn1755, std::move(args1756)); }());
s->SetAt(4, v1754);
auto v1759 = ([&]() -> Value { auto fn1760 = PrepareDictionaryGet(Attribute(s->Captured("chassis"), "routes")); Arguments args1761; args1761.positional.reserve(2); args1761.Add(([&]() -> Value { auto fn1762 = PrepareDictionaryGet(([&]() -> Value { auto fn1764 = PrepareDictionaryGet(Attribute(s->Captured("chassis"), "players")); Arguments args1765; args1765.positional.reserve(2); args1765.Add(s->LocalAt(4), false); args1765.Add(([&]() -> Value { auto dict1766 = Dict(); return dict1766; }()), false); return CallDictionaryGet(c, fn1764, std::move(args1765)); }())); Arguments args1763; args1763.Add(Value("route"), false); return CallDictionaryGet(c, fn1762, std::move(args1763)); }()), false); args1761.Add(([&]() -> Value { auto fn1767 = s->Global("next"); Arguments args1768; args1768.Add(([&]() -> Value { auto fn1769 = s->Global("iter"); Arguments args1770; args1770.Add(([&]() -> Value { auto fn1771 = Attribute(Attribute(s->Captured("chassis"), "routes"), "values"); Arguments args1772; return Call(c, fn1771, std::move(args1772)); }()), false); return Call(c, fn1769, std::move(args1770)); }()), false); return Call(c, fn1767, std::move(args1768)); }()), false); return CallDictionaryGet(c, fn1760, std::move(args1761)); }());
s->SetAt(6, v1759);
if (static_cast<bool>(([&]() -> Value { auto v1773 = Value(int64_t{0}); Value v1774; v1774 = s->LocalAt(5); if (!static_cast<bool>(Binary("LtE", v1773, v1774))) return Value(false); v1773 = v1774; v1774 = ([&]() -> Value { auto fn1775 = s->Global("len"); Arguments args1776; args1776.Add(s->LocalAt(6), false); return Call(c, fn1775, std::move(args1776)); }()); if (!static_cast<bool>(Binary("Lt", v1773, v1774))) return Value(false); v1773 = v1774; return Value(true); }()))) {
return ([&]() -> Value { auto fn1777 = Attribute(s->Global("copy"), "deepcopy"); Arguments args1778; args1778.Add(Get(s->LocalAt(6), s->LocalAt(5)), false); return Call(c, fn1777, std::move(args1778)); }());
}
} catch (const Error& error1750) {
if (Matches(error1750, s->Global("Exception"))) {
}
else { throw; }
}
try {
auto v1780 = ([&]() -> Value { auto v1781 = ([&]() -> Value { auto fn1782 = s->Global("_get"); Arguments args1783; args1783.positional.reserve(3); args1783.Add(s->LocalAt(3), false); args1783.Add(Value("farms"), false); args1783.Add(List({}), false); return Call(c, fn1782, std::move(args1783)); }()); if (static_cast<bool>(v1781)) return v1781; v1781 = List({}); return v1781; }());
s->SetAt(1, v1780);
auto v1784 = ([&]() -> Value { auto v1785 = ([&]() -> Value { auto fn1786 = s->Global("_get"); Arguments args1787; args1787.positional.reserve(3); args1787.Add(Get(s->LocalAt(1), ([&]() -> Value { auto fn1788 = s->Global("_int"); Arguments args1789; args1789.Add(([&]() -> Value { auto fn1790 = s->Global("_get"); Arguments args1791; args1791.positional.reserve(3); args1791.Add(s->LocalAt(3), false); args1791.Add(Value("player"), false); args1791.Add(Value(int64_t{0}), false); return Call(c, fn1790, std::move(args1791)); }()), false); return Call(c, fn1788, std::move(args1789)); }())), false); args1787.Add(Value("hands"), false); args1787.Add(List({}), false); return Call(c, fn1786, std::move(args1787)); }()); if (static_cast<bool>(v1785)) return v1785; v1785 = List({}); return v1785; }());
s->SetAt(2, v1784);
return ([&]() -> Value { auto dict1792 = Dict(); auto key1793 = Value("farmer"); Put(dict1792, key1793, List({Value("PASS")})); auto key1794 = Value("hands"); Put(dict1792, key1794, ([&]() -> Value { auto comp1795 = std::make_shared<Scope>(); comp1795->globals = s->globals; comp1795->parent = s; static constexpr const char* comp1795_names[] = {"_"}; comp1795->PrepareSlots(comp1795_names); auto result1796 = List(); for (const auto& item1797 : Iterate(s->LocalAt(2))) { comp1795->SetAt(0, item1797); result1796.node()->sequence.push_back(List({Value("PASS")})); } return result1796; }())); auto key1798 = Value("market"); Put(dict1792, key1798, List({})); return dict1792; }());
} catch (const Error& error1779) {
if (Matches(error1779, s->Global("Exception"))) {
return ([&]() -> Value { auto fn1799 = Attribute(s->Global("copy"), "deepcopy"); Arguments args1800; args1800.Add(s->Global("PASS_ACTION"), false); return Call(c, fn1799, std::move(args1800)); }());
}
else { throw; }
}
}
else { throw; }
}
return {};
}
}  // namespace kagg::opponents::compiled
