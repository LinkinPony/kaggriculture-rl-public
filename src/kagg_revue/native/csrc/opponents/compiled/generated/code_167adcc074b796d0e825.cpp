// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_167adcc074b796d0e825(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"configuration", "observation", "player", "result", "state", "step"};
s->PrepareSlots(s_names);
auto v9691 = ([&]() -> Value { auto fn9692 = s->Global("_R85_PARENT"); Arguments args9693; args9693.positional.reserve(2); args9693.Add(s->LocalAt(1), false); args9693.Add(s->LocalAt(0), false); return Call(c, fn9692, std::move(args9693)); }());
s->SetAt(3, v9691);
try {
auto v9695 = ([&]() -> Value { auto fn9696 = s->Global("int"); Arguments args9697; args9697.Add(Get(s->LocalAt(1), Value("step")), false); return Call(c, fn9696, std::move(args9697)); }());
s->SetAt(5, v9695);
auto v9698 = ([&]() -> Value { auto fn9699 = s->Global("int"); Arguments args9700; args9700.Add(Get(s->LocalAt(1), Value("player")), false); return Call(c, fn9699, std::move(args9700)); }());
s->SetAt(2, v9698);
auto v9701 = ([&]() -> Value { auto fn9702 = PrepareDictionaryGet(s->Global("_R85_STATES")); Arguments args9703; args9703.Add(s->LocalAt(2), false); return CallDictionaryGet(c, fn9702, std::move(args9703)); }());
s->SetAt(4, v9701);
if (static_cast<bool>(([&]() -> Value { auto v9704 = ([&]() -> Value { auto v9705 = s->LocalAt(4); Value v9706; v9706 = Value{}; if (!static_cast<bool>(Binary("Is", v9705, v9706))) return Value(false); v9705 = v9706; return Value(true); }()); if (static_cast<bool>(v9704)) return v9704; v9704 = ([&]() -> Value { auto v9707 = s->LocalAt(5); Value v9708; v9708 = Get(s->LocalAt(4), Value("step")); if (!static_cast<bool>(Binary("LtE", v9707, v9708))) return Value(false); v9707 = v9708; return Value(true); }()); return v9704; }()))) {
auto v9709 = ([&]() -> Value { auto dict9710 = Dict(); auto key9711 = Value("step"); Put(dict9710, key9711, Unary("USub", Value(int64_t{1}))); return dict9710; }());
s->SetAt(4, v9709);
Put(s->Global("_R85_STATES"), s->LocalAt(2), v9709);
(void)([&]() -> Value { auto fn9712 = Attribute(s->Global("_R85_REPORT"), "update"); Arguments args9713; args9713.Keyword("feed_skips", Value(int64_t{0})); args9713.Keyword("fert_sale_turns", Value(int64_t{0})); args9713.Keyword("fert_sale_units", Value(int64_t{0})); args9713.Keyword("economic_overlay_errors", Value(int64_t{0})); return Call(c, fn9712, std::move(args9713)); }());
}
auto v9714 = s->LocalAt(5);
Put(s->LocalAt(4), Value("step"), v9714);
if (static_cast<bool>(([&]() -> Value { auto v9715 = ([&]() -> Value { auto v9716 = s->LocalAt(0); Value v9717; v9717 = Value{}; if (!static_cast<bool>(Binary("IsNot", v9716, v9717))) return Value(false); v9716 = v9717; return Value(true); }()); if (!static_cast<bool>(v9715)) return v9715; v9715 = ([&]() -> Value { auto comp9718 = std::make_shared<Scope>(); comp9718->globals = s->globals; comp9718->parent = s; static constexpr const char* comp9718_names[] = {"k", "v"}; comp9718->PrepareSlots(comp9718_names); auto result9719 = List(); for (const auto& item9720 : Iterate(List({Tuple({Value("boardSize"), Value(int64_t{10})}), Tuple({Value("turnsPerDay"), Value(int64_t{24})}), Tuple({Value("shedCapacity"), Value(int64_t{100})}), Tuple({Value("maxMarketOrdersPerTurn"), Value(int64_t{10})})}))) { auto unpack9721 = Iterate(item9720); ValidateUnpack(unpack9721, 2, false); comp9718->SetAt(0, unpack9721.at(0)); comp9718->SetAt(1, unpack9721.at(1)); if (static_cast<bool>(([&]() -> Value { auto v9722 = ([&]() -> Value { auto fn9724 = PrepareDictionaryGet(comp9718->Captured("configuration")); Arguments args9725; args9725.positional.reserve(2); args9725.Add(comp9718->LocalAt(0), false); args9725.Add(comp9718->LocalAt(1), false); return CallDictionaryGet(c, fn9724, std::move(args9725)); }()); Value v9723; v9723 = comp9718->LocalAt(1); if (!static_cast<bool>(Binary("NotEq", v9722, v9723))) return Value(false); v9722 = v9723; return Value(true); }()))) return Value(true); } return Value(false); }()); return v9715; }()))) {
return s->LocalAt(3);
}
if (static_cast<bool>(s->Global("_R85_FEED"))) {
auto v9726 = ([&]() -> Value { auto fn9727 = s->Global("_r85_feed"); Arguments args9728; args9728.positional.reserve(2); args9728.Add(s->LocalAt(1), false); args9728.Add(s->LocalAt(3), false); return Call(c, fn9727, std::move(args9728)); }());
s->SetAt(3, v9726);
}
if (static_cast<bool>(s->Global("_R85_FERT"))) {
auto v9729 = ([&]() -> Value { auto fn9730 = s->Global("_r85_fertilizer"); Arguments args9731; args9731.positional.reserve(3); args9731.Add(s->LocalAt(1), false); args9731.Add(s->LocalAt(3), false); args9731.Add(s->LocalAt(4), false); return Call(c, fn9730, std::move(args9731)); }());
s->SetAt(3, v9729);
}
if (static_cast<bool>(([&]() -> Value { auto v9732 = ([&]() -> Value { auto v9734 = s->LocalAt(5); return Binary("Mod", v9734, Value(int64_t{24})); }()); Value v9733; v9733 = Value(int64_t{23}); if (!static_cast<bool>(Binary("Eq", v9732, v9733))) return Value(false); v9732 = v9733; return Value(true); }()))) {
auto v9735 = ([&]() -> Value { auto fn9736 = s->Global("_r51_close_warehouse"); Arguments args9737; args9737.positional.reserve(2); args9737.Add(s->LocalAt(1), false); args9737.Add(s->LocalAt(3), false); return Call(c, fn9736, std::move(args9737)); }());
s->SetAt(3, v9735);
}
} catch (const Error& error9694) {
if (Matches(error9694, s->Global("Exception"))) {
auto v9738 = ([&]() -> Value { auto v9739 = ([&]() -> Value { auto fn9740 = PrepareDictionaryGet(s->Global("_R85_REPORT")); Arguments args9741; args9741.positional.reserve(2); args9741.Add(Value("economic_overlay_errors"), false); args9741.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn9740, std::move(args9741)); }()); return Binary("Add", v9739, Value(int64_t{1})); }());
Put(s->Global("_R85_REPORT"), Value("economic_overlay_errors"), v9738);
}
else { throw; }
}
(void)([&]() -> Value { auto fn9742 = Attribute(s->Global("_R85_REPORT"), "update"); Arguments args9743; args9743.Add(([&]() -> Value { auto fn9744 = s->Global("getattr"); Arguments args9745; args9745.positional.reserve(3); args9745.Add(s->Global("_R85_PARENT"), false); args9745.Add(Value("telemetry"), false); args9745.Add(([&]() -> Value { auto dict9746 = Dict(); return dict9746; }()), false); return Call(c, fn9744, std::move(args9745)); }()), false); return Call(c, fn9742, std::move(args9743)); }());
return s->LocalAt(3);
return {};
}
}  // namespace kagg::opponents::compiled
