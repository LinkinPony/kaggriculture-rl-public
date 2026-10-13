// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_8ab10f25b4629ca7f3ba(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"_", "action", "after", "bag", "best", "final", "item", "loss", "n", "obs", "orders", "original", "private", "proposed", "released", "remaining", "stock", "tail", "take"};
s->PrepareSlots(s_names);
if (static_cast<bool>(([&]() -> Value { auto v30651 = ([&]() -> Value { auto v30653 = ([&]() -> Value { auto fn30654 = s->Global("int"); Arguments args30655; args30655.Add(Get(s->LocalAt(9), Value("step")), false); return Call(c, fn30654, std::move(args30655)); }()); return Binary("Mod", v30653, Value(int64_t{24})); }()); Value v30652; v30652 = Value(int64_t{23}); if (!static_cast<bool>(Binary("NotEq", v30651, v30652))) return Value(false); v30651 = v30652; return Value(true); }()))) {
return s->LocalAt(1);
}
auto v30656 = ([&]() -> Value { auto v30657 = ([&]() -> Value { auto fn30658 = PrepareDictionaryGet(s->LocalAt(1)); Arguments args30659; args30659.Add(Value("market"), false); return CallDictionaryGet(c, fn30658, std::move(args30659)); }()); if (static_cast<bool>(v30657)) return v30657; v30657 = List({}); return v30657; }());
s->SetAt(10, v30656);
if (static_cast<bool>(([&]() -> Value { auto v30660 = ([&]() -> Value { auto v30661 = ([&]() -> Value { auto fn30663 = s->Global("len"); Arguments args30664; args30664.Add(s->LocalAt(10), false); return Call(c, fn30663, std::move(args30664)); }()); Value v30662; v30662 = Value(int64_t{10}); if (!static_cast<bool>(Binary("GtE", v30661, v30662))) return Value(false); v30661 = v30662; return Value(true); }()); if (static_cast<bool>(v30660)) return v30660; v30660 = Unary("Not", ([&]() -> Value { auto fn30665 = s->Global("_r97_budget"); Arguments args30666; args30666.positional.reserve(2); args30666.Add(s->LocalAt(9), false); args30666.Add(s->LocalAt(10), false); return Call(c, fn30665, std::move(args30666)); }())); return v30660; }()))) {
return s->LocalAt(1);
}
auto v30667 = ([&]() -> Value { auto fn30668 = s->Global("_ov_fields"); Arguments args30669; args30669.positional.reserve(2); args30669.Add(s->LocalAt(9), false); args30669.Add(s->LocalAt(1), false); return Call(c, fn30668, std::move(args30669)); }());
auto unpack30670 = Iterate(v30667);
ValidateUnpack(unpack30670, 2, false);
s->SetAt(0, unpack30670.at(0));
s->SetAt(12, unpack30670.at(1));
auto v30671 = ([&]() -> Value { auto fn30672 = s->Global("_r97_market_stock"); Arguments args30673; args30673.positional.reserve(2); args30673.Add(Get(s->LocalAt(12), Value("shed")), false); args30673.Add(s->LocalAt(10), false); return Call(c, fn30672, std::move(args30673)); }());
auto unpack30674 = Iterate(v30671);
ValidateUnpack(unpack30674, 3, false);
s->SetAt(16, unpack30674.at(0));
s->SetAt(0, unpack30674.at(1));
s->SetAt(0, unpack30674.at(2));
auto v30675 = ([&]() -> Value { auto fn30676 = s->Global("_r97_delivery"); Arguments args30677; args30677.positional.reserve(3); args30677.Add(s->LocalAt(16), false); args30677.Add(s->LocalAt(12), false); args30677.Add(Value(true), false); return Call(c, fn30676, std::move(args30677)); }());
auto unpack30678 = Iterate(v30675);
ValidateUnpack(unpack30678, 2, false);
s->SetAt(11, unpack30678.at(0));
s->SetAt(7, unpack30678.at(1));
if (static_cast<bool>(Unary("Not", s->LocalAt(7)))) {
return s->LocalAt(1);
}
auto v30679 = ([&]() -> Value { auto fn30680 = s->Global("max"); Arguments args30681; args30681.positional.reserve(2); args30681.Add(Value(int64_t{0}), false); args30681.Add(([&]() -> Value { auto v30682 = Value(int64_t{100}); return Binary("Sub", v30682, ([&]() -> Value { auto fn30683 = s->Global("sum"); Arguments args30684; args30684.Add(([&]() -> Value { auto fn30685 = Attribute(s->LocalAt(16), "values"); Arguments args30686; return Call(c, fn30685, std::move(args30686)); }()), false); return Call(c, fn30683, std::move(args30684)); }())); }()), false); return Call(c, fn30680, std::move(args30681)); }());
s->SetAt(15, v30679);
auto v30687 = List({});
s->SetAt(17, v30687);
for (const auto& item30688 : Iterate(Get(s->LocalAt(12), Value("inventories")))) {
s->SetAt(3, item30688);
for (const auto& item30689 : Iterate(([&]() -> Value { auto fn30690 = Attribute(s->LocalAt(3), "items"); Arguments args30691; return Call(c, fn30690, std::move(args30691)); }()))) {
auto unpack30692 = Iterate(item30689);
ValidateUnpack(unpack30692, 2, false);
s->SetAt(6, unpack30692.at(0));
s->SetAt(8, unpack30692.at(1));
auto v30693 = ([&]() -> Value { auto fn30694 = s->Global("max"); Arguments args30695; args30695.positional.reserve(2); args30695.Add(Value(int64_t{0}), false); args30695.Add(([&]() -> Value { auto fn30696 = s->Global("int"); Arguments args30697; args30697.Add(s->LocalAt(8), false); return Call(c, fn30696, std::move(args30697)); }()), false); return Call(c, fn30694, std::move(args30695)); }());
s->SetAt(8, v30693);
auto v30698 = ([&]() -> Value { auto fn30699 = s->Global("min"); Arguments args30700; args30700.positional.reserve(2); args30700.Add(s->LocalAt(8), false); args30700.Add(s->LocalAt(15), false); return Call(c, fn30699, std::move(args30700)); }());
s->SetAt(18, v30698);
auto v30701 = s->LocalAt(15);
s->SetAt(15, Inplace("Sub", v30701, s->LocalAt(18)));
if (static_cast<bool>(([&]() -> Value { auto v30702 = s->LocalAt(8); Value v30703; v30703 = s->LocalAt(18); if (!static_cast<bool>(Binary("Gt", v30702, v30703))) return Value(false); v30702 = v30703; return Value(true); }()))) {
(void)([&]() -> Value { auto fn30704 = Attribute(s->LocalAt(17), "extend"); Arguments args30705; args30705.Add(([&]() -> Value { auto v30706 = List({s->LocalAt(6)}); return Binary("Mult", v30706, ([&]() -> Value { auto v30707 = s->LocalAt(8); return Binary("Sub", v30707, s->LocalAt(18)); }())); }()), false); return Call(c, fn30704, std::move(args30705)); }());
}
}
}
auto v30708 = ([&]() -> Value { auto dict30709 = Dict(); return dict30709; }());
s->SetAt(14, v30708);
auto v30710 = Value{};
s->SetAt(4, v30710);
for (const auto& item30711 : Iterate(s->LocalAt(17))) {
s->SetAt(6, item30711);
auto v30712 = ([&]() -> Value { auto v30713 = ([&]() -> Value { auto fn30714 = PrepareDictionaryGet(s->LocalAt(14)); Arguments args30715; args30715.positional.reserve(2); args30715.Add(s->LocalAt(6), false); args30715.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn30714, std::move(args30715)); }()); return Binary("Add", v30713, Value(int64_t{1})); }());
Put(s->LocalAt(14), s->LocalAt(6), v30712);
if (static_cast<bool>(([&]() -> Value { auto v30716 = ([&]() -> Value { auto v30717 = s->LocalAt(6); Value v30718; v30718 = Get(Get(s->LocalAt(9), Value("market")), Value("prices")); if (!static_cast<bool>(Binary("NotIn", v30717, v30718))) return Value(false); v30717 = v30718; return Value(true); }()); if (static_cast<bool>(v30716)) return v30716; v30716 = ([&]() -> Value { auto v30719 = Get(s->LocalAt(14), s->LocalAt(6)); Value v30720; v30720 = ([&]() -> Value { auto fn30721 = PrepareDictionaryGet(s->LocalAt(16)); Arguments args30722; args30722.positional.reserve(2); args30722.Add(s->LocalAt(6), false); args30722.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn30721, std::move(args30722)); }()); if (!static_cast<bool>(Binary("Gt", v30719, v30720))) return Value(false); v30719 = v30720; return Value(true); }()); return v30716; }()))) {
break;
}
if (static_cast<bool>(([&]() -> Value { auto v30723 = ([&]() -> Value { auto v30725 = ([&]() -> Value { auto fn30726 = s->Global("len"); Arguments args30727; args30727.Add(s->LocalAt(10), false); return Call(c, fn30726, std::move(args30727)); }()); return Binary("Add", v30725, ([&]() -> Value { auto fn30728 = s->Global("len"); Arguments args30729; args30729.Add(s->LocalAt(14), false); return Call(c, fn30728, std::move(args30729)); }())); }()); Value v30724; v30724 = Value(int64_t{10}); if (!static_cast<bool>(Binary("Gt", v30723, v30724))) return Value(false); v30723 = v30724; return Value(true); }()))) {
break;
}
auto v30730 = ([&]() -> Value { auto v30731 = ([&]() -> Value { auto fn30732 = s->Global("list"); Arguments args30733; args30733.Add(s->LocalAt(10), false); return Call(c, fn30732, std::move(args30733)); }()); return Binary("Add", v30731, ([&]() -> Value { auto comp30734 = std::make_shared<Scope>(); comp30734->globals = s->globals; comp30734->parent = s; static constexpr const char* comp30734_names[] = {"n", "p"}; comp30734->PrepareSlots(comp30734_names); auto result30735 = List(); for (const auto& item30736 : Iterate(([&]() -> Value { auto fn30737 = Attribute(s->LocalAt(14), "items"); Arguments args30738; return Call(c, fn30737, std::move(args30738)); }()))) { auto unpack30739 = Iterate(item30736); ValidateUnpack(unpack30739, 2, false); comp30734->SetAt(1, unpack30739.at(0)); comp30734->SetAt(0, unpack30739.at(1)); result30735.node()->sequence.push_back(List({Value("SELL"), comp30734->LocalAt(1), comp30734->LocalAt(0)})); } return result30735; }())); }());
s->SetAt(13, v30730);
auto v30740 = ([&]() -> Value { auto fn30741 = s->Global("_r97_market_stock"); Arguments args30742; args30742.positional.reserve(2); args30742.Add(Get(s->LocalAt(12), Value("shed")), false); args30742.Add(s->LocalAt(13), false); return Call(c, fn30741, std::move(args30742)); }());
auto unpack30743 = Iterate(v30740);
ValidateUnpack(unpack30743, 3, false);
s->SetAt(2, unpack30743.at(0));
s->SetAt(0, unpack30743.at(1));
s->SetAt(0, unpack30743.at(2));
auto v30744 = ([&]() -> Value { auto fn30745 = s->Global("_r97_delivery"); Arguments args30746; args30746.positional.reserve(3); args30746.Add(s->LocalAt(2), false); args30746.Add(s->LocalAt(12), false); args30746.Add(Value(true), false); return Call(c, fn30745, std::move(args30746)); }());
auto unpack30747 = Iterate(v30744);
ValidateUnpack(unpack30747, 2, false);
s->SetAt(5, unpack30747.at(0));
s->SetAt(0, unpack30747.at(1));
if (static_cast<bool>(([&]() -> Value { auto fn30748 = s->Global("_ov_same"); Arguments args30749; args30749.positional.reserve(2); args30749.Add(s->LocalAt(11), false); args30749.Add(s->LocalAt(5), false); return Call(c, fn30748, std::move(args30749)); }()))) {
auto v30750 = Tuple({s->LocalAt(13), ([&]() -> Value { auto fn30751 = s->Global("dict"); Arguments args30752; args30752.Add(s->LocalAt(14), false); return Call(c, fn30751, std::move(args30752)); }())});
s->SetAt(4, v30750);
}
}
if (static_cast<bool>(([&]() -> Value { auto v30753 = s->LocalAt(4); Value v30754; v30754 = Value{}; if (!static_cast<bool>(Binary("Is", v30753, v30754))) return Value(false); v30753 = v30754; return Value(true); }()))) {
return s->LocalAt(1);
}
auto v30755 = s->Global("_OV_REPORT");
auto v30756 = Value("ov_turns");
auto v30757 = Get(v30755, v30756);
Put(v30755, v30756, Inplace("Add", v30757, Value(int64_t{1})));
auto v30758 = s->Global("_OV_REPORT");
auto v30759 = Value("ov_units");
auto v30760 = Get(v30758, v30759);
Put(v30758, v30759, Inplace("Add", v30760, ([&]() -> Value { auto fn30761 = s->Global("sum"); Arguments args30762; args30762.Add(([&]() -> Value { auto fn30763 = Attribute(Get(s->LocalAt(4), Value(int64_t{1})), "values"); Arguments args30764; return Call(c, fn30763, std::move(args30764)); }()), false); return Call(c, fn30761, std::move(args30762)); }())));
return ([&]() -> Value { auto fn30765 = s->Global("dict"); Arguments args30766; args30766.Add(s->LocalAt(1), false); args30766.Keyword("market", Get(s->LocalAt(4), Value(int64_t{0}))); return Call(c, fn30765, std::move(args30766)); }());
return {};
}
}  // namespace kagg::opponents::compiled
