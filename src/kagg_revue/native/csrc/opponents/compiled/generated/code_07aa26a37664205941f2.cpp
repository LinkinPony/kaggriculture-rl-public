// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_07aa26a37664205941f2(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "day", "extra", "held", "market", "obs", "result", "sold", "state", "step", "stock"};
s->PrepareSlots(s_names);
auto v9623 = ([&]() -> Value { auto fn9624 = s->Global("int"); Arguments args9625; args9625.Add(Get(s->LocalAt(5), Value("step")), false); return Call(c, fn9624, std::move(args9625)); }());
s->SetAt(9, v9623);
auto v9626 = ([&]() -> Value { auto v9627 = s->LocalAt(9); return Binary("FloorDiv", v9627, Value(int64_t{24})); }());
s->SetAt(1, v9626);
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto v9628 = Value(int64_t{6}); Value v9629; v9629 = s->LocalAt(1); if (!static_cast<bool>(Binary("LtE", v9628, v9629))) return Value(false); v9628 = v9629; v9629 = Value(int64_t{28}); if (!static_cast<bool>(Binary("LtE", v9628, v9629))) return Value(false); v9628 = v9629; return Value(true); }())))) {
return s->LocalAt(0);
}
auto v9630 = ([&]() -> Value { auto fn9631 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args9632; args9632.positional.reserve(2); args9632.Add(Value("market"), false); args9632.Add(List({}), false); return CallDictionaryGet(c, fn9631, std::move(args9632)); }());
s->SetAt(4, v9630);
if (static_cast<bool>(([&]() -> Value { auto v9633 = ([&]() -> Value { auto v9634 = ([&]() -> Value { auto fn9636 = s->Global("len"); Arguments args9637; args9637.Add(s->LocalAt(4), false); return Call(c, fn9636, std::move(args9637)); }()); Value v9635; v9635 = s->Global("MAX_ORDERS"); if (!static_cast<bool>(Binary("GtE", v9634, v9635))) return Value(false); v9634 = v9635; return Value(true); }()); if (static_cast<bool>(v9633)) return v9633; v9633 = ([&]() -> Value { auto comp9638 = std::make_shared<Scope>(); comp9638->globals = s->globals; comp9638->parent = s; static constexpr const char* comp9638_names[] = {"o"}; comp9638->PrepareSlots(comp9638_names); auto result9639 = List(); for (const auto& item9640 : Iterate(s->LocalAt(4))) { comp9638->SetAt(0, item9640); if (static_cast<bool>(([&]() -> Value { auto v9641 = comp9638->LocalAt(0); if (!static_cast<bool>(v9641)) return v9641; v9641 = ([&]() -> Value { auto v9642 = Get(comp9638->LocalAt(0), Value(int64_t{0})); Value v9643; v9643 = Value("SELL"); if (!static_cast<bool>(Binary("NotEq", v9642, v9643))) return Value(false); v9642 = v9643; return Value(true); }()); return v9641; }()))) return Value(true); } return Value(false); }()); return v9633; }()))) {
return s->LocalAt(0);
}
auto v9644 = ([&]() -> Value { auto fn9645 = s->Global("projected_shed"); Arguments args9646; args9646.positional.reserve(2); args9646.Add(s->LocalAt(0), false); args9646.Add(([&]() -> Value { auto fn9647 = s->Global("FarmView"); Arguments args9648; args9648.Add(s->LocalAt(5), false); return Call(c, fn9647, std::move(args9648)); }()), false); return Call(c, fn9645, std::move(args9646)); }());
s->SetAt(10, v9644);
auto v9649 = ([&]() -> Value { auto fn9650 = s->Global("max"); Arguments args9651; args9651.positional.reserve(2); args9651.Add(Value(int64_t{0}), false); args9651.Add(([&]() -> Value { auto fn9652 = s->Global("int"); Arguments args9653; args9653.Add(([&]() -> Value { auto fn9654 = PrepareDictionaryGet(s->LocalAt(10)); Arguments args9655; args9655.positional.reserve(2); args9655.Add(Value("FERTILIZER"), false); args9655.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn9654, std::move(args9655)); }()), false); return Call(c, fn9652, std::move(args9653)); }()), false); return Call(c, fn9650, std::move(args9651)); }());
s->SetAt(3, v9649);
auto v9656 = ([&]() -> Value { auto fn9657 = s->Global("sum"); Arguments args9658; args9658.Add(([&]() -> Value { auto comp9659 = std::make_shared<Scope>(); comp9659->globals = s->globals; comp9659->parent = s; static constexpr const char* comp9659_names[] = {"o"}; comp9659->PrepareSlots(comp9659_names); auto result9660 = List(); for (const auto& item9661 : Iterate(s->LocalAt(4))) { comp9659->SetAt(0, item9661); if (!static_cast<bool>(([&]() -> Value { auto v9662 = ([&]() -> Value { auto v9663 = ([&]() -> Value { auto fn9665 = comp9659->Global("len"); Arguments args9666; args9666.Add(comp9659->LocalAt(0), false); return Call(c, fn9665, std::move(args9666)); }()); Value v9664; v9664 = Value(int64_t{2}); if (!static_cast<bool>(Binary("Gt", v9663, v9664))) return Value(false); v9663 = v9664; return Value(true); }()); if (!static_cast<bool>(v9662)) return v9662; v9662 = ([&]() -> Value { auto v9667 = Slice(comp9659->LocalAt(0), Value{}, Value(int64_t{2}), Value{}); Value v9668; v9668 = List({Value("SELL"), Value("FERTILIZER")}); if (!static_cast<bool>(Binary("Eq", v9667, v9668))) return Value(false); v9667 = v9668; return Value(true); }()); return v9662; }()))) continue; result9660.node()->sequence.push_back(([&]() -> Value { auto fn9669 = comp9659->Global("max"); Arguments args9670; args9670.positional.reserve(2); args9670.Add(Value(int64_t{0}), false); args9670.Add(([&]() -> Value { auto fn9671 = comp9659->Global("int"); Arguments args9672; args9672.Add(Get(comp9659->LocalAt(0), Value(int64_t{2})), false); return Call(c, fn9671, std::move(args9672)); }()), false); return Call(c, fn9669, std::move(args9670)); }())); } return result9660; }()), false); return Call(c, fn9657, std::move(args9658)); }());
s->SetAt(7, v9656);
auto v9673 = ([&]() -> Value { auto v9674 = ([&]() -> Value { auto v9675 = s->LocalAt(3); return Binary("Sub", v9675, s->LocalAt(7)); }()); return Binary("Sub", v9674, ([&]() -> Value { auto fn9676 = s->Global("_r85_reserve"); Arguments args9677; args9677.positional.reserve(2); args9677.Add(s->LocalAt(5), false); args9677.Add(s->LocalAt(8), false); return Call(c, fn9676, std::move(args9677)); }())); }());
s->SetAt(2, v9673);
if (static_cast<bool>(([&]() -> Value { auto v9678 = s->LocalAt(2); Value v9679; v9679 = Value(int64_t{0}); if (!static_cast<bool>(Binary("LtE", v9678, v9679))) return Value(false); v9678 = v9679; return Value(true); }()))) {
return s->LocalAt(0);
}
auto v9680 = ([&]() -> Value { auto fn9681 = Attribute(s->Global("copy"), "deepcopy"); Arguments args9682; args9682.Add(s->LocalAt(0), false); return Call(c, fn9681, std::move(args9682)); }());
s->SetAt(6, v9680);
(void)([&]() -> Value { auto fn9683 = Attribute(Get(s->LocalAt(6), Value("market")), "append"); Arguments args9684; args9684.Add(List({Value("SELL"), Value("FERTILIZER"), s->LocalAt(2)}), false); return Call(c, fn9683, std::move(args9684)); }());
auto v9685 = s->Global("_R85_REPORT");
auto v9686 = Value("fert_sale_turns");
auto v9687 = Get(v9685, v9686);
Put(v9685, v9686, Inplace("Add", v9687, Value(int64_t{1})));
auto v9688 = s->Global("_R85_REPORT");
auto v9689 = Value("fert_sale_units");
auto v9690 = Get(v9688, v9689);
Put(v9688, v9689, Inplace("Add", v9690, s->LocalAt(2)));
return s->LocalAt(6);
return {};
}
}  // namespace kagg::opponents::compiled
