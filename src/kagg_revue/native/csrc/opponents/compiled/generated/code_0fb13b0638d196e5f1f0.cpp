// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_0fb13b0638d196e5f1f0(Context& c, const ScopePtr& s) {
if (auto result = InputPath(c, s)) return *result;
static constexpr const char* s_names[] = {"action", "arrival", "beam", "best", "candidate", "carrot", "day", "depth", "expanded", "fertilizer", "gain", "gross", "index", "item", "new_gross", "new_path", "now", "obs", "path", "pos", "prices", "ready", "score", "start", "step", "target", "targets", "used", "wheat", "xy"};
s->PrepareSlots(s_names);
auto v7700 = ([&]() -> Value { auto fn7701 = s->Global("int"); Arguments args7702; args7702.Add(Get(s->LocalAt(17), Value("step")), false); return Call(c, fn7701, std::move(args7702)); }());
s->SetAt(24, v7700);
auto v7703 = ([&]() -> Value { auto v7704 = s->LocalAt(24); return Binary("FloorDiv", v7704, Value(int64_t{24})); }());
s->SetAt(6, v7703);
auto v7705 = ([&]() -> Value { auto fn7706 = s->Global("_r62_input_start"); Arguments args7707; args7707.positional.reserve(3); args7707.Add(s->LocalAt(17), false); args7707.Add(s->LocalAt(0), false); args7707.Add(s->LocalAt(12), false); return Call(c, fn7706, std::move(args7707)); }());
auto unpack7708 = Iterate(v7705);
ValidateUnpack(unpack7708, 2, false);
s->SetAt(21, unpack7708.at(0));
s->SetAt(23, unpack7708.at(1));
auto v7709 = ([&]() -> Value { auto comp7710 = std::make_shared<Scope>(); comp7710->globals = s->globals; comp7710->parent = s; static constexpr const char* comp7710_names[] = {"p"}; comp7710->PrepareSlots(comp7710_names); auto result7711 = Dict(); for (const auto& item7712 : Iterate(Tuple({Value("WHEAT"), Value("CARROT")}))) { comp7710->SetAt(0, item7712); Put(result7711, comp7710->LocalAt(0), ([&]() -> Value { auto fn7713 = comp7710->Global("max"); Arguments args7714; args7714.positional.reserve(2); args7714.Add(Value(int64_t{1}), false); args7714.Add(([&]() -> Value { auto v7715 = ([&]() -> Value { auto fn7716 = comp7710->Global("int"); Arguments args7717; args7717.Add(Get(Get(Get(comp7710->Captured("obs"), Value("market")), Value("prices")), comp7710->LocalAt(0)), false); return Call(c, fn7716, std::move(args7717)); }()); return Binary("Sub", v7715, Value(int64_t{2})); }()), false); return Call(c, fn7713, std::move(args7714)); }())); } return result7711; }());
s->SetAt(20, v7709);
auto v7718 = ([&]() -> Value { auto fn7719 = s->Global("max"); Arguments args7720; args7720.positional.reserve(2); args7720.Add(Value(int64_t{1}), false); args7720.Add(([&]() -> Value { auto v7721 = ([&]() -> Value { auto fn7722 = s->Global("_r37_market_price"); Arguments args7723; args7723.positional.reserve(2); args7723.Add(Value("FERTILIZER"), false); args7723.Add(([&]() -> Value { auto v7724 = Get(Get(Get(s->LocalAt(17), Value("market")), Value("inventory")), Value("FERTILIZER")); return Binary("Sub", v7724, Value(int64_t{16})); }()), false); return Call(c, fn7722, std::move(args7723)); }()); return Binary("Add", v7721, Value(int64_t{2})); }()), false); return Call(c, fn7719, std::move(args7720)); }());
s->SetAt(9, v7718);
auto v7725 = List({Tuple({Value(int64_t{0}), Value(int64_t{0}), s->LocalAt(21), s->LocalAt(23), Tuple({}), ([&]() -> Value { auto fn7726 = s->Global("frozenset"); Arguments args7727; return Call(c, fn7726, std::move(args7727)); }()), Value(int64_t{0}), Value(int64_t{0})})});
s->SetAt(2, v7725);
auto v7728 = Value{};
s->SetAt(3, v7728);
for (const auto& item7729 : Iterate(([&]() -> Value { auto fn7730 = s->Global("range"); Arguments args7731; args7731.Add(Value(int64_t{8}), false); return Call(c, fn7730, std::move(args7731)); }()))) {
s->SetAt(7, item7729);
auto v7732 = List({});
s->SetAt(8, v7732);
for (const auto& item7733 : Iterate(s->LocalAt(2))) {
auto unpack7734 = Iterate(item7733);
ValidateUnpack(unpack7734, 8, false);
s->SetAt(22, unpack7734.at(0));
s->SetAt(11, unpack7734.at(1));
s->SetAt(16, unpack7734.at(2));
s->SetAt(19, unpack7734.at(3));
s->SetAt(18, unpack7734.at(4));
s->SetAt(27, unpack7734.at(5));
s->SetAt(28, unpack7734.at(6));
s->SetAt(5, unpack7734.at(7));
for (const auto& item7735 : Iterate(([&]() -> Value { auto fn7736 = Attribute(s->LocalAt(26), "items"); Arguments args7737; return Call(c, fn7736, std::move(args7737)); }()))) {
auto unpack7738 = Iterate(item7735);
ValidateUnpack(unpack7738, 2, false);
s->SetAt(29, unpack7738.at(0));
s->SetAt(25, unpack7738.at(1));
if (static_cast<bool>(([&]() -> Value { auto v7739 = s->LocalAt(29); Value v7740; v7740 = s->LocalAt(27); if (!static_cast<bool>(Binary("In", v7739, v7740))) return Value(false); v7739 = v7740; return Value(true); }()))) {
continue;
}
auto v7741 = ([&]() -> Value { auto v7742 = ([&]() -> Value { auto v7743 = s->LocalAt(16); return Binary("Add", v7743, ([&]() -> Value { auto fn7744 = s->Global("abs"); Arguments args7745; args7745.Add(([&]() -> Value { auto v7746 = Get(s->LocalAt(19), Value(int64_t{0})); return Binary("Sub", v7746, Get(s->LocalAt(29), Value(int64_t{0}))); }()), false); return Call(c, fn7744, std::move(args7745)); }())); }()); return Binary("Add", v7742, ([&]() -> Value { auto fn7747 = s->Global("abs"); Arguments args7748; args7748.Add(([&]() -> Value { auto v7749 = Get(s->LocalAt(19), Value(int64_t{1})); return Binary("Sub", v7749, Get(s->LocalAt(29), Value(int64_t{1}))); }()), false); return Call(c, fn7747, std::move(args7748)); }())); }());
s->SetAt(1, v7741);
if (static_cast<bool>(([&]() -> Value { auto v7750 = s->LocalAt(1); Value v7751; v7751 = ([&]() -> Value { auto v7752 = ([&]() -> Value { auto v7753 = s->LocalAt(6); return Binary("Mult", v7753, Value(int64_t{24})); }()); return Binary("Add", v7752, Value(int64_t{23})); }()); if (!static_cast<bool>(Binary("GtE", v7750, v7751))) return Value(false); v7750 = v7751; return Value(true); }()))) {
continue;
}
auto v7754 = ([&]() -> Value { auto fn7755 = s->Global("_r51_input_gain"); Arguments args7756; args7756.positional.reserve(3); args7756.Add(s->LocalAt(25), false); args7756.Add(s->LocalAt(1), false); args7756.Add(s->LocalAt(6), false); return Call(c, fn7755, std::move(args7756)); }());
s->SetAt(10, v7754);
if (static_cast<bool>(Unary("Not", s->LocalAt(10)))) {
continue;
}
auto v7757 = Get(s->LocalAt(25), Value("crop"));
s->SetAt(13, v7757);
auto v7758 = ([&]() -> Value { auto v7759 = s->LocalAt(11); return Binary("Add", v7759, ([&]() -> Value { auto v7760 = s->LocalAt(10); return Binary("Mult", v7760, Get(s->LocalAt(20), s->LocalAt(13))); }())); }());
s->SetAt(14, v7758);
auto v7761 = ([&]() -> Value { auto v7762 = s->LocalAt(18); return Binary("Add", v7762, Tuple({Tuple({Get(s->LocalAt(29), Value(int64_t{0})), Get(s->LocalAt(29), Value(int64_t{1})), s->LocalAt(13), Get(s->LocalAt(25), Value("birth"))})})); }());
s->SetAt(15, v7761);
(void)([&]() -> Value { auto fn7763 = Attribute(s->LocalAt(8), "append"); Arguments args7764; args7764.Add(Tuple({([&]() -> Value { auto v7765 = s->LocalAt(14); return Binary("Sub", v7765, ([&]() -> Value { auto v7766 = ([&]() -> Value { auto v7767 = Value(1.5); return Binary("Mult", v7767, s->LocalAt(9)); }()); return Binary("Mult", v7766, ([&]() -> Value { auto fn7768 = s->Global("len"); Arguments args7769; args7769.Add(s->LocalAt(15), false); return Call(c, fn7768, std::move(args7769)); }())); }())); }()), s->LocalAt(14), ([&]() -> Value { auto v7770 = s->LocalAt(1); return Binary("Add", v7770, Value(int64_t{1})); }()), s->LocalAt(29), s->LocalAt(15), ([&]() -> Value { auto v7771 = s->LocalAt(27); return Binary("BitOr", v7771, Set({s->LocalAt(29)})); }()), ([&]() -> Value { auto v7772 = s->LocalAt(28); return Binary("Add", v7772, (static_cast<bool>(([&]() -> Value { auto v7773 = s->LocalAt(13); Value v7774; v7774 = Value("WHEAT"); if (!static_cast<bool>(Binary("Eq", v7773, v7774))) return Value(false); v7773 = v7774; return Value(true); }())) ? s->LocalAt(10) : Value(int64_t{0}))); }()), ([&]() -> Value { auto v7775 = s->LocalAt(5); return Binary("Add", v7775, (static_cast<bool>(([&]() -> Value { auto v7776 = s->LocalAt(13); Value v7777; v7777 = Value("CARROT"); if (!static_cast<bool>(Binary("Eq", v7776, v7777))) return Value(false); v7776 = v7777; return Value(true); }())) ? s->LocalAt(10) : Value(int64_t{0}))); }())}), false); return Call(c, fn7763, std::move(args7764)); }());
}
}
if (static_cast<bool>(Unary("Not", s->LocalAt(8)))) {
break;
}
(void)([&]() -> Value { auto fn7778 = Attribute(s->LocalAt(8), "sort"); Arguments args7779; args7779.Keyword("key", Define(&Code_aaddb35ab65f0cb85226, s, Signature{{"s"}, {}, {}, {}, "", "", ([]() -> std::span<const char* const> { static constexpr const char* names[] = {"s"}; return names; }())}, true, "<lambda>")); return Call(c, fn7778, std::move(args7779)); }());
auto v7780 = Slice(s->LocalAt(8), Value{}, Value(int64_t{8}), Value{});
s->SetAt(2, v7780);
if (static_cast<bool>(([&]() -> Value { auto v7781 = s->LocalAt(7); Value v7782; v7782 = Value(int64_t{2}); if (!static_cast<bool>(Binary("GtE", v7781, v7782))) return Value(false); v7781 = v7782; return Value(true); }()))) {
auto v7783 = Get(s->LocalAt(2), Value(int64_t{0}));
s->SetAt(4, v7783);
if (static_cast<bool>(([&]() -> Value { auto v7784 = ([&]() -> Value { auto v7785 = s->LocalAt(3); Value v7786; v7786 = Value{}; if (!static_cast<bool>(Binary("Is", v7785, v7786))) return Value(false); v7785 = v7786; return Value(true); }()); if (static_cast<bool>(v7784)) return v7784; v7784 = ([&]() -> Value { auto v7787 = Tuple({Unary("USub", Get(s->LocalAt(4), Value(int64_t{0}))), Unary("USub", Get(s->LocalAt(4), Value(int64_t{1}))), Get(s->LocalAt(4), Value(int64_t{2})), Get(s->LocalAt(4), Value(int64_t{4}))}); Value v7788; v7788 = Tuple({Unary("USub", Get(s->LocalAt(3), Value(int64_t{0}))), Unary("USub", Get(s->LocalAt(3), Value(int64_t{1}))), Get(s->LocalAt(3), Value(int64_t{2})), Get(s->LocalAt(3), Value(int64_t{4}))}); if (!static_cast<bool>(Binary("Lt", v7787, v7788))) return Value(false); v7787 = v7788; return Value(true); }()); return v7784; }()))) {
auto v7789 = s->LocalAt(4);
s->SetAt(3, v7789);
}
}
}
if (static_cast<bool>(([&]() -> Value { auto v7790 = s->LocalAt(3); Value v7791; v7791 = Value{}; if (!static_cast<bool>(Binary("Is", v7790, v7791))) return Value(false); v7790 = v7791; return Value(true); }()))) {
return Tuple({List({}), ([&]() -> Value { auto dict7792 = Dict(); auto key7793 = Value("WHEAT"); Put(dict7792, key7793, Value(int64_t{0})); auto key7794 = Value("CARROT"); Put(dict7792, key7794, Value(int64_t{0})); return dict7792; }())});
}
return Tuple({([&]() -> Value { auto fn7795 = s->Global("list"); Arguments args7796; args7796.Add(Get(s->LocalAt(3), Value(int64_t{4})), false); return Call(c, fn7795, std::move(args7796)); }()), ([&]() -> Value { auto dict7797 = Dict(); auto key7798 = Value("WHEAT"); Put(dict7797, key7798, Get(s->LocalAt(3), Value(int64_t{6}))); auto key7799 = Value("CARROT"); Put(dict7797, key7799, Get(s->LocalAt(3), Value(int64_t{7}))); return dict7797; }())});
return {};
}
}  // namespace kagg::opponents::compiled
