// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_58b8025e9383a97e7c2d(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "already", "changed", "ev", "i", "item", "market", "native", "obs", "ours", "qty", "result", "st", "step", "stock", "t", "tape"};
s->PrepareSlots(s_names);
auto v29636 = ([&]() -> Value { auto fn29637 = s->Global("int"); Arguments args29638; args29638.Add(Get(s->LocalAt(8), Value("step")), false); return Call(c, fn29637, std::move(args29638)); }());
s->SetAt(13, v29636);
(void)([&]() -> Value { auto fn29639 = s->Global("_v92_q_update"); Arguments args29640; args29640.positional.reserve(2); args29640.Add(s->LocalAt(8), false); args29640.Add(s->LocalAt(12), false); return Call(c, fn29639, std::move(args29640)); }());
if (static_cast<bool>(([&]() -> Value { auto v29641 = ([&]() -> Value { auto v29642 = s->LocalAt(13); Value v29643; v29643 = Value(int64_t{150}); if (!static_cast<bool>(Binary("Lt", v29642, v29643))) return Value(false); v29642 = v29643; return Value(true); }()); if (static_cast<bool>(v29641)) return v29641; v29641 = ([&]() -> Value { auto v29644 = s->LocalAt(13); Value v29645; v29645 = Value(int64_t{700}); if (!static_cast<bool>(Binary("GtE", v29644, v29645))) return Value(false); v29644 = v29645; return Value(true); }()); if (static_cast<bool>(v29641)) return v29641; v29641 = ([&]() -> Value { auto v29646 = Get(s->LocalAt(12), Value("best")); Value v29647; v29647 = Value{}; if (!static_cast<bool>(Binary("Is", v29646, v29647))) return Value(false); v29646 = v29647; return Value(true); }()); return v29641; }()))) {
return s->LocalAt(0);
}
auto v29648 = Get(Get(s->LocalAt(12), Value("evs")), Get(s->LocalAt(12), Value("best")));
s->SetAt(3, v29648);
auto v29649 = ([&]() -> Value { auto fn29650 = PrepareDictionaryGet(Attribute(Attribute(s->Global("_IMPL"), "chassis"), "players")); Arguments args29651; args29651.Add(([&]() -> Value { auto fn29652 = s->Global("int"); Arguments args29653; args29653.Add(Get(s->LocalAt(8), Value("player")), false); return Call(c, fn29652, std::move(args29653)); }()), false); return CallDictionaryGet(c, fn29650, std::move(args29651)); }());
s->SetAt(7, v29649);
if (static_cast<bool>(([&]() -> Value { auto v29654 = Unary("Not", s->LocalAt(7)); if (static_cast<bool>(v29654)) return v29654; v29654 = ([&]() -> Value { auto v29655 = ([&]() -> Value { auto fn29657 = PrepareDictionaryGet(s->LocalAt(7)); Arguments args29658; args29658.Add(Value("route"), false); return CallDictionaryGet(c, fn29657, std::move(args29658)); }()); Value v29656; v29656 = Attribute(Attribute(s->Global("_IMPL"), "chassis"), "routes"); if (!static_cast<bool>(Binary("NotIn", v29655, v29656))) return Value(false); v29655 = v29656; return Value(true); }()); return v29654; }()))) {
return s->LocalAt(0);
}
auto v29659 = Get(Attribute(Attribute(s->Global("_IMPL"), "chassis"), "routes"), Get(s->LocalAt(7), Value("route")));
s->SetAt(16, v29659);
auto v29660 = ([&]() -> Value { auto comp29661 = std::make_shared<Scope>(); comp29661->globals = s->globals; comp29661->parent = s; static constexpr const char* comp29661_names[] = {"o"}; comp29661->PrepareSlots(comp29661_names); auto result29662 = List(); for (const auto& item29663 : Iterate(([&]() -> Value { auto v29664 = ([&]() -> Value { auto fn29665 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args29666; args29666.Add(Value("market"), false); return CallDictionaryGet(c, fn29665, std::move(args29666)); }()); if (static_cast<bool>(v29664)) return v29664; v29664 = List({}); return v29664; }()))) { comp29661->SetAt(0, item29663); result29662.node()->sequence.push_back(([&]() -> Value { auto fn29667 = comp29661->Global("list"); Arguments args29668; args29668.Add(comp29661->LocalAt(0), false); return Call(c, fn29667, std::move(args29668)); }())); } return result29662; }());
s->SetAt(6, v29660);
auto v29669 = ([&]() -> Value { auto comp29670 = std::make_shared<Scope>(); comp29670->globals = s->globals; comp29670->parent = s; static constexpr const char* comp29670_names[] = {"o"}; comp29670->PrepareSlots(comp29670_names); auto result29671 = List(); for (const auto& item29672 : Iterate(s->LocalAt(6))) { comp29670->SetAt(0, item29672); if (!static_cast<bool>(([&]() -> Value { auto v29673 = ([&]() -> Value { auto v29674 = ([&]() -> Value { auto fn29676 = comp29670->Global("len"); Arguments args29677; args29677.Add(comp29670->LocalAt(0), false); return Call(c, fn29676, std::move(args29677)); }()); Value v29675; v29675 = Value(int64_t{1}); if (!static_cast<bool>(Binary("Gt", v29674, v29675))) return Value(false); v29674 = v29675; return Value(true); }()); if (!static_cast<bool>(v29673)) return v29673; v29673 = ([&]() -> Value { auto v29678 = Get(comp29670->LocalAt(0), Value(int64_t{0})); Value v29679; v29679 = Tuple({Value("SELL"), Value("BUY_PRODUCT")}); if (!static_cast<bool>(Binary("In", v29678, v29679))) return Value(false); v29678 = v29679; return Value(true); }()); return v29673; }()))) continue; result29671.node()->sequence.push_back(Get(comp29670->LocalAt(0), Value(int64_t{1}))); } return Set(result29671.node()->sequence); }());
s->SetAt(1, v29669);
auto v29680 = Value{};
s->SetAt(14, v29680);
auto v29681 = Value(false);
s->SetAt(2, v29681);
for (const auto& item29682 : Iterate(([&]() -> Value { auto fn29683 = s->Global("enumerate"); Arguments args29684; args29684.Add(s->Global("_V92_Q_ITEMS"), false); return Call(c, fn29683, std::move(args29684)); }()))) {
auto unpack29685 = Iterate(item29682);
ValidateUnpack(unpack29685, 2, false);
s->SetAt(4, unpack29685.at(0));
s->SetAt(5, unpack29685.at(1));
if (static_cast<bool>(([&]() -> Value { auto v29686 = ([&]() -> Value { auto v29687 = s->LocalAt(5); Value v29688; v29688 = s->LocalAt(1); if (!static_cast<bool>(Binary("In", v29687, v29688))) return Value(false); v29687 = v29688; return Value(true); }()); if (static_cast<bool>(v29686)) return v29686; v29686 = ([&]() -> Value { auto v29689 = ([&]() -> Value { auto fn29691 = s->Global("len"); Arguments args29692; args29692.Add(s->LocalAt(6), false); return Call(c, fn29691, std::move(args29692)); }()); Value v29690; v29690 = s->Global("MAX_ORDERS"); if (!static_cast<bool>(Binary("GtE", v29689, v29690))) return Value(false); v29689 = v29690; return Value(true); }()); return v29686; }()))) {
continue;
}
if (static_cast<bool>(([&]() -> Value { auto v29693 = ([&]() -> Value { auto v29695 = ([&]() -> Value { auto fn29696 = PrepareDictionaryGet(s->LocalAt(3)); Arguments args29697; args29697.positional.reserve(2); args29697.Add(Tuple({([&]() -> Value { auto v29698 = s->LocalAt(13); return Binary("Add", v29698, Value(int64_t{1})); }()), s->LocalAt(4)}), false); args29697.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn29696, std::move(args29697)); }()); return Binary("Add", v29695, ([&]() -> Value { auto fn29699 = PrepareDictionaryGet(s->LocalAt(3)); Arguments args29700; args29700.positional.reserve(2); args29700.Add(Tuple({([&]() -> Value { auto v29701 = s->LocalAt(13); return Binary("Add", v29701, Value(int64_t{2})); }()), s->LocalAt(4)}), false); args29700.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn29699, std::move(args29700)); }())); }()); Value v29694; v29694 = s->Global("_V92_Q_K"); if (!static_cast<bool>(Binary("Lt", v29693, v29694))) return Value(false); v29693 = v29694; return Value(true); }()))) {
continue;
}
auto v29702 = Value(int64_t{0});
s->SetAt(9, v29702);
for (const auto& item29703 : Iterate(([&]() -> Value { auto fn29704 = s->Global("range"); Arguments args29705; args29705.positional.reserve(2); args29705.Add(([&]() -> Value { auto v29706 = s->LocalAt(13); return Binary("Add", v29706, Value(int64_t{1})); }()), false); args29705.Add(([&]() -> Value { auto fn29707 = s->Global("min"); Arguments args29708; args29708.positional.reserve(2); args29708.Add(([&]() -> Value { auto fn29709 = s->Global("len"); Arguments args29710; args29710.Add(s->LocalAt(16), false); return Call(c, fn29709, std::move(args29710)); }()), false); args29708.Add(([&]() -> Value { auto v29711 = ([&]() -> Value { auto v29712 = s->LocalAt(13); return Binary("Add", v29712, s->Global("_V92_Q_H")); }()); return Binary("Add", v29711, Value(int64_t{1})); }()), false); return Call(c, fn29707, std::move(args29708)); }()), false); return Call(c, fn29704, std::move(args29705)); }()))) {
s->SetAt(15, item29703);
auto v29713 = s->LocalAt(9);
s->SetAt(9, Inplace("Add", v29713, ([&]() -> Value { auto fn29714 = s->Global("sum"); Arguments args29715; args29715.Add(([&]() -> Value { auto comp29716 = std::make_shared<Scope>(); comp29716->globals = s->globals; comp29716->parent = s; static constexpr const char* comp29716_names[] = {"o"}; comp29716->PrepareSlots(comp29716_names); auto result29717 = List(); for (const auto& item29718 : Iterate(([&]() -> Value { auto v29719 = ([&]() -> Value { auto fn29720 = PrepareDictionaryGet(([&]() -> Value { auto v29722 = Get(s->LocalAt(16), s->LocalAt(15)); if (static_cast<bool>(v29722)) return v29722; v29722 = ([&]() -> Value { auto dict29723 = Dict(); return dict29723; }()); return v29722; }())); Arguments args29721; args29721.Add(Value("market"), false); return CallDictionaryGet(c, fn29720, std::move(args29721)); }()); if (static_cast<bool>(v29719)) return v29719; v29719 = List({}); return v29719; }()))) { comp29716->SetAt(0, item29718); if (!static_cast<bool>(([&]() -> Value { auto v29724 = ([&]() -> Value { auto v29725 = ([&]() -> Value { auto fn29727 = comp29716->Global("len"); Arguments args29728; args29728.Add(comp29716->LocalAt(0), false); return Call(c, fn29727, std::move(args29728)); }()); Value v29726; v29726 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v29725, v29726))) return Value(false); v29725 = v29726; return Value(true); }()); if (!static_cast<bool>(v29724)) return v29724; v29724 = ([&]() -> Value { auto v29729 = Get(comp29716->LocalAt(0), Value(int64_t{0})); Value v29730; v29730 = Value("SELL"); if (!static_cast<bool>(Binary("Eq", v29729, v29730))) return Value(false); v29729 = v29730; return Value(true); }()); if (!static_cast<bool>(v29724)) return v29724; v29724 = ([&]() -> Value { auto v29731 = Get(comp29716->LocalAt(0), Value(int64_t{1})); Value v29732; v29732 = comp29716->Captured("item"); if (!static_cast<bool>(Binary("Eq", v29731, v29732))) return Value(false); v29731 = v29732; return Value(true); }()); return v29724; }()))) continue; result29717.node()->sequence.push_back(([&]() -> Value { auto fn29733 = comp29716->Global("min"); Arguments args29734; args29734.positional.reserve(2); args29734.Add(Value(int64_t{100}), false); args29734.Add(([&]() -> Value { auto fn29735 = comp29716->Global("int"); Arguments args29736; args29736.Add(Get(comp29716->LocalAt(0), Value(int64_t{2})), false); return Call(c, fn29735, std::move(args29736)); }()), false); return Call(c, fn29733, std::move(args29734)); }())); } return result29717; }()), false); return Call(c, fn29714, std::move(args29715)); }())));
}
if (static_cast<bool>(([&]() -> Value { auto v29737 = s->LocalAt(14); Value v29738; v29738 = Value{}; if (!static_cast<bool>(Binary("Is", v29737, v29738))) return Value(false); v29737 = v29738; return Value(true); }()))) {
auto v29739 = ([&]() -> Value { auto fn29740 = s->Global("projected_shed"); Arguments args29741; args29741.positional.reserve(2); args29741.Add(s->LocalAt(0), false); args29741.Add(([&]() -> Value { auto fn29742 = s->Global("FarmView"); Arguments args29743; args29743.Add(s->LocalAt(8), false); return Call(c, fn29742, std::move(args29743)); }()), false); return Call(c, fn29740, std::move(args29741)); }());
s->SetAt(14, v29739);
}
auto v29744 = ([&]() -> Value { auto fn29745 = s->Global("min"); Arguments args29746; args29746.positional.reserve(2); args29746.Add(([&]() -> Value { auto fn29747 = s->Global("int"); Arguments args29748; args29748.Add(([&]() -> Value { auto fn29749 = PrepareDictionaryGet(s->LocalAt(14)); Arguments args29750; args29750.positional.reserve(2); args29750.Add(s->LocalAt(5), false); args29750.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn29749, std::move(args29750)); }()), false); return Call(c, fn29747, std::move(args29748)); }()), false); args29746.Add(s->LocalAt(9), false); return Call(c, fn29745, std::move(args29746)); }());
s->SetAt(10, v29744);
if (static_cast<bool>(([&]() -> Value { auto v29751 = s->LocalAt(10); Value v29752; v29752 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v29751, v29752))) return Value(false); v29751 = v29752; return Value(true); }()))) {
(void)([&]() -> Value { auto fn29753 = Attribute(s->LocalAt(6), "insert"); Arguments args29754; args29754.positional.reserve(2); args29754.Add(Value(int64_t{0}), false); args29754.Add(List({Value("SELL"), s->LocalAt(5), s->LocalAt(10)}), false); return Call(c, fn29753, std::move(args29754)); }());
auto v29755 = s->Global("_V92_Q_REPORT");
auto v29756 = Value("pred_units");
auto v29757 = Get(v29755, v29756);
Put(v29755, v29756, Inplace("Add", v29757, s->LocalAt(10)));
auto v29758 = s->Global("_V92_Q_REPORT");
auto v29759 = Value("pred_fires");
auto v29760 = Get(v29758, v29759);
Put(v29758, v29759, Inplace("Add", v29760, Value(int64_t{1})));
auto v29761 = Value(true);
s->SetAt(2, v29761);
}
}
if (static_cast<bool>(Unary("Not", s->LocalAt(2)))) {
return s->LocalAt(0);
}
auto v29762 = ([&]() -> Value { auto fn29763 = s->Global("dict"); Arguments args29764; args29764.Add(s->LocalAt(0), false); return Call(c, fn29763, std::move(args29764)); }());
s->SetAt(11, v29762);
auto v29765 = Slice(s->LocalAt(6), Value{}, s->Global("MAX_ORDERS"), Value{});
Put(s->LocalAt(11), Value("market"), v29765);
return s->LocalAt(11);
return {};
}
}  // namespace kagg::opponents::compiled
