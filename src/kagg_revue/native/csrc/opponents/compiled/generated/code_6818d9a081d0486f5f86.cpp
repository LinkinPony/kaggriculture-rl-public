// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_6818d9a081d0486f5f86(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "due", "order", "removed", "state", "step"};
s->PrepareSlots(s_names);
(void)([&]() -> Value { auto fn5760 = s->Global("_R36_NATIVE_SUPPRESS"); Arguments args5761; args5761.positional.reserve(3); args5761.Add(s->LocalAt(0), false); args5761.Add(s->LocalAt(4), false); args5761.Add(s->LocalAt(5), false); return Call(c, fn5760, std::move(args5761)); }());
auto v5762 = ([&]() -> Value { auto fn5763 = Attribute(([&]() -> Value { auto fn5765 = PrepareDictionaryGet(s->LocalAt(4)); Arguments args5766; args5766.positional.reserve(2); args5766.Add(Value("r36_debts"), false); args5766.Add(([&]() -> Value { auto dict5767 = Dict(); return dict5767; }()), false); return CallDictionaryGet(c, fn5765, std::move(args5766)); }()), "pop"); Arguments args5764; args5764.positional.reserve(2); args5764.Add(s->LocalAt(5), false); args5764.Add(([&]() -> Value { auto dict5768 = Dict(); return dict5768; }()), false); return Call(c, fn5763, std::move(args5764)); }());
s->SetAt(1, v5762);
for (const auto& item5769 : Iterate(([&]() -> Value { auto fn5770 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args5771; args5771.positional.reserve(2); args5771.Add(Value("market"), false); args5771.Add(List({}), false); return CallDictionaryGet(c, fn5770, std::move(args5771)); }()))) {
s->SetAt(2, item5769);
if (static_cast<bool>(([&]() -> Value { auto v5772 = ([&]() -> Value { auto v5773 = ([&]() -> Value { auto fn5775 = s->Global("len"); Arguments args5776; args5776.Add(s->LocalAt(2), false); return Call(c, fn5775, std::move(args5776)); }()); Value v5774; v5774 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v5773, v5774))) return Value(false); v5773 = v5774; return Value(true); }()); if (!static_cast<bool>(v5772)) return v5772; v5772 = ([&]() -> Value { auto v5777 = Get(s->LocalAt(2), Value(int64_t{0})); Value v5778; v5778 = Value("SELL"); if (!static_cast<bool>(Binary("Eq", v5777, v5778))) return Value(false); v5777 = v5778; return Value(true); }()); return v5772; }()))) {
auto v5779 = ([&]() -> Value { auto fn5780 = s->Global("min"); Arguments args5781; args5781.positional.reserve(2); args5781.Add(([&]() -> Value { auto fn5782 = s->Global("max"); Arguments args5783; args5783.positional.reserve(2); args5783.Add(Value(int64_t{0}), false); args5783.Add(([&]() -> Value { auto fn5784 = s->Global("int"); Arguments args5785; args5785.Add(Get(s->LocalAt(2), Value(int64_t{2})), false); return Call(c, fn5784, std::move(args5785)); }()), false); return Call(c, fn5782, std::move(args5783)); }()), false); args5781.Add(([&]() -> Value { auto fn5786 = PrepareDictionaryGet(s->LocalAt(1)); Arguments args5787; args5787.positional.reserve(2); args5787.Add(Get(s->LocalAt(2), Value(int64_t{1})), false); args5787.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn5786, std::move(args5787)); }()), false); return Call(c, fn5780, std::move(args5781)); }());
s->SetAt(3, v5779);
auto v5788 = s->LocalAt(2);
auto v5789 = Value(int64_t{2});
auto v5790 = Get(v5788, v5789);
Put(v5788, v5789, Inplace("Sub", v5790, s->LocalAt(3)));
auto v5791 = ([&]() -> Value { auto v5792 = ([&]() -> Value { auto fn5793 = PrepareDictionaryGet(s->LocalAt(1)); Arguments args5794; args5794.positional.reserve(2); args5794.Add(Get(s->LocalAt(2), Value(int64_t{1})), false); args5794.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn5793, std::move(args5794)); }()); return Binary("Sub", v5792, s->LocalAt(3)); }());
Put(s->LocalAt(1), Get(s->LocalAt(2), Value(int64_t{1})), v5791);
}
}
return {};
}
}  // namespace kagg::opponents::compiled
