// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_0ab79e7935f213dfa1b7(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "cargo", "changed", "command", "commands", "crew", "day", "delivered", "end", "existing", "farm", "index", "inventories", "inventory", "item", "market", "n", "native", "obs", "plan", "plans", "player", "pos", "positions", "prices", "result", "route", "st", "step", "tape", "unit"};
s->PrepareSlots(s_names);
auto v20638 = ([&]() -> Value { auto fn20639 = s->Global("int"); Arguments args20640; args20640.Add(Get(s->LocalAt(18), Value("step")), false); return Call(c, fn20639, std::move(args20640)); }());
s->SetAt(28, v20638);
auto v20641 = ([&]() -> Value { auto fn20642 = s->Global("int"); Arguments args20643; args20643.Add(Get(s->LocalAt(18), Value("player")), false); return Call(c, fn20642, std::move(args20643)); }());
s->SetAt(21, v20641);
if (static_cast<bool>(([&]() -> Value { auto v20644 = ([&]() -> Value { auto v20645 = s->LocalAt(28); Value v20646; v20646 = Value(int64_t{718}); if (!static_cast<bool>(Binary("GtE", v20645, v20646))) return Value(false); v20645 = v20646; return Value(true); }()); if (static_cast<bool>(v20644)) return v20644; v20644 = ([&]() -> Value { auto v20647 = ([&]() -> Value { auto v20649 = s->LocalAt(28); return Binary("Mod", v20649, Value(int64_t{24})); }()); Value v20648; v20648 = s->Global("V9_COURIER_FROM_HOUR"); if (!static_cast<bool>(Binary("Lt", v20647, v20648))) return Value(false); v20647 = v20648; return Value(true); }()); return v20644; }()))) {
return s->LocalAt(0);
}
auto v20650 = ([&]() -> Value { auto v20651 = s->LocalAt(28); return Binary("FloorDiv", v20651, Value(int64_t{24})); }());
s->SetAt(6, v20650);
if (static_cast<bool>(([&]() -> Value { auto v20652 = ([&]() -> Value { auto fn20654 = PrepareDictionaryGet(s->LocalAt(27)); Arguments args20655; args20655.Add(Value("day"), false); return CallDictionaryGet(c, fn20654, std::move(args20655)); }()); Value v20653; v20653 = s->LocalAt(6); if (!static_cast<bool>(Binary("NotEq", v20652, v20653))) return Value(false); v20652 = v20653; return Value(true); }()))) {
auto v20656 = s->LocalAt(6);
Put(s->LocalAt(27), Value("day"), v20656);
auto v20657 = ([&]() -> Value { auto dict20658 = Dict(); return dict20658; }());
Put(s->LocalAt(27), Value("plans"), v20657);
}
auto v20659 = ([&]() -> Value { auto fn20660 = PrepareDictionaryGet(Attribute(Attribute(s->Global("_IMPL"), "chassis"), "players")); Arguments args20661; args20661.Add(s->LocalAt(21), false); return CallDictionaryGet(c, fn20660, std::move(args20661)); }());
s->SetAt(17, v20659);
if (static_cast<bool>(([&]() -> Value { auto v20662 = Unary("Not", s->LocalAt(17)); if (static_cast<bool>(v20662)) return v20662; v20662 = ([&]() -> Value { auto v20663 = ([&]() -> Value { auto fn20665 = PrepareDictionaryGet(s->LocalAt(17)); Arguments args20666; args20666.Add(Value("route"), false); return CallDictionaryGet(c, fn20665, std::move(args20666)); }()); Value v20664; v20664 = Attribute(Attribute(s->Global("_IMPL"), "chassis"), "routes"); if (!static_cast<bool>(Binary("NotIn", v20663, v20664))) return Value(false); v20663 = v20664; return Value(true); }()); return v20662; }()))) {
return s->LocalAt(0);
}
auto v20667 = Get(Attribute(Attribute(s->Global("_IMPL"), "chassis"), "routes"), Get(s->LocalAt(17), Value("route")));
s->SetAt(29, v20667);
auto v20668 = Get(Get(s->LocalAt(18), Value("farms")), s->LocalAt(21));
s->SetAt(10, v20668);
auto v20669 = ([&]() -> Value { auto v20670 = List({([&]() -> Value { auto fn20671 = s->Global("tuple"); Arguments args20672; args20672.Add(Get(s->LocalAt(10), Value("farmer")), false); return Call(c, fn20671, std::move(args20672)); }())}); return Binary("Add", v20670, ([&]() -> Value { auto comp20673 = std::make_shared<Scope>(); comp20673->globals = s->globals; comp20673->parent = s; static constexpr const char* comp20673_names[] = {"p"}; comp20673->PrepareSlots(comp20673_names); auto result20674 = List(); for (const auto& item20675 : Iterate(Get(s->LocalAt(10), Value("hands")))) { comp20673->SetAt(0, item20675); result20674.node()->sequence.push_back(([&]() -> Value { auto fn20676 = comp20673->Global("tuple"); Arguments args20677; args20677.Add(comp20673->LocalAt(0), false); return Call(c, fn20676, std::move(args20677)); }())); } return result20674; }())); }());
s->SetAt(23, v20669);
auto v20678 = Get(Get(s->LocalAt(18), Value("private")), Value("inventories"));
s->SetAt(12, v20678);
auto v20679 = ([&]() -> Value { auto v20680 = List({([&]() -> Value { auto fn20681 = s->Global("list"); Arguments args20682; args20682.Add(([&]() -> Value { auto v20683 = ([&]() -> Value { auto fn20684 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args20685; args20685.Add(Value("farmer"), false); return CallDictionaryGet(c, fn20684, std::move(args20685)); }()); if (static_cast<bool>(v20683)) return v20683; v20683 = List({Value("PASS")}); return v20683; }()), false); return Call(c, fn20681, std::move(args20682)); }())}); return Binary("Add", v20680, ([&]() -> Value { auto comp20686 = std::make_shared<Scope>(); comp20686->globals = s->globals; comp20686->parent = s; static constexpr const char* comp20686_names[] = {"c"}; comp20686->PrepareSlots(comp20686_names); auto result20687 = List(); for (const auto& item20688 : Iterate(([&]() -> Value { auto v20689 = ([&]() -> Value { auto fn20690 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args20691; args20691.Add(Value("hands"), false); return CallDictionaryGet(c, fn20690, std::move(args20691)); }()); if (static_cast<bool>(v20689)) return v20689; v20689 = List({}); return v20689; }()))) { comp20686->SetAt(0, item20688); result20687.node()->sequence.push_back(([&]() -> Value { auto fn20692 = comp20686->Global("list"); Arguments args20693; args20693.Add(comp20686->LocalAt(0), false); return Call(c, fn20692, std::move(args20693)); }())); } return result20687; }())); }());
s->SetAt(4, v20679);
auto v20694 = s->LocalAt(4);
s->SetAt(4, Inplace("Add", v20694, ([&]() -> Value { auto v20695 = List({List({Value("PASS")})}); return Binary("Mult", v20695, ([&]() -> Value { auto v20696 = ([&]() -> Value { auto fn20697 = s->Global("len"); Arguments args20698; args20698.Add(s->LocalAt(23), false); return Call(c, fn20697, std::move(args20698)); }()); return Binary("Sub", v20696, ([&]() -> Value { auto fn20699 = s->Global("len"); Arguments args20700; args20700.Add(s->LocalAt(4), false); return Call(c, fn20699, std::move(args20700)); }())); }())); }())));
auto v20701 = ([&]() -> Value { auto v20702 = ([&]() -> Value { auto v20703 = s->LocalAt(6); return Binary("Mult", v20703, Value(int64_t{24})); }()); return Binary("Add", v20702, Value(int64_t{23})); }());
s->SetAt(8, v20701);
auto v20704 = Get(s->LocalAt(27), Value("plans"));
s->SetAt(20, v20704);
auto v20705 = ([&]() -> Value { auto v20706 = Value(int64_t{1}); return Binary("Add", v20706, ([&]() -> Value { auto fn20707 = s->Global("max"); Arguments args20708; args20708.Add(([&]() -> Value { auto comp20709 = std::make_shared<Scope>(); comp20709->globals = s->globals; comp20709->parent = s; static constexpr const char* comp20709_names[] = {"t"}; comp20709->PrepareSlots(comp20709_names); auto result20710 = List(); for (const auto& item20711 : Iterate(([&]() -> Value { auto fn20712 = s->Global("range"); Arguments args20713; args20713.positional.reserve(2); args20713.Add(([&]() -> Value { auto v20714 = s->LocalAt(6); return Binary("Mult", v20714, Value(int64_t{24})); }()), false); args20713.Add(([&]() -> Value { auto fn20715 = s->Global("min"); Arguments args20716; args20716.positional.reserve(2); args20716.Add(([&]() -> Value { auto fn20717 = s->Global("len"); Arguments args20718; args20718.Add(s->LocalAt(29), false); return Call(c, fn20717, std::move(args20718)); }()), false); args20716.Add(([&]() -> Value { auto v20719 = s->LocalAt(8); return Binary("Add", v20719, Value(int64_t{1})); }()), false); return Call(c, fn20715, std::move(args20716)); }()), false); return Call(c, fn20712, std::move(args20713)); }()))) { comp20709->SetAt(0, item20711); result20710.node()->sequence.push_back(([&]() -> Value { auto fn20720 = comp20709->Global("len"); Arguments args20721; args20721.Add(([&]() -> Value { auto v20722 = ([&]() -> Value { auto fn20723 = PrepareDictionaryGet(Get(comp20709->Captured("tape"), comp20709->LocalAt(0))); Arguments args20724; args20724.Add(Value("hands"), false); return CallDictionaryGet(c, fn20723, std::move(args20724)); }()); if (static_cast<bool>(v20722)) return v20722; v20722 = List({}); return v20722; }()), false); return Call(c, fn20720, std::move(args20721)); }())); } return result20710; }()), false); return Call(c, fn20707, std::move(args20708)); }())); }());
s->SetAt(5, v20705);
auto v20725 = ([&]() -> Value { auto dict20726 = Dict(); return dict20726; }());
s->SetAt(7, v20725);
auto v20727 = Value(false);
s->SetAt(2, v20727);
for (const auto& item20728 : Iterate(([&]() -> Value { auto fn20729 = s->Global("enumerate"); Arguments args20730; args20730.Add(Slice(s->LocalAt(23), Value{}, s->LocalAt(5), Value{}), false); return Call(c, fn20729, std::move(args20730)); }()))) {
auto unpack20731 = Iterate(item20728);
ValidateUnpack(unpack20731, 2, false);
s->SetAt(30, unpack20731.at(0));
s->SetAt(22, unpack20731.at(1));
auto v20732 = (static_cast<bool>(([&]() -> Value { auto v20733 = s->LocalAt(30); Value v20734; v20734 = ([&]() -> Value { auto fn20735 = s->Global("len"); Arguments args20736; args20736.Add(s->LocalAt(12), false); return Call(c, fn20735, std::move(args20736)); }()); if (!static_cast<bool>(Binary("Lt", v20733, v20734))) return Value(false); v20733 = v20734; return Value(true); }())) ? Get(s->LocalAt(12), s->LocalAt(30)) : ([&]() -> Value { auto dict20737 = Dict(); return dict20737; }()));
s->SetAt(13, v20732);
auto v20738 = ([&]() -> Value { auto comp20739 = std::make_shared<Scope>(); comp20739->globals = s->globals; comp20739->parent = s; static constexpr const char* comp20739_names[] = {"k", "v"}; comp20739->PrepareSlots(comp20739_names); auto result20740 = Dict(); for (const auto& item20741 : Iterate(([&]() -> Value { auto fn20742 = Attribute(s->LocalAt(13), "items"); Arguments args20743; return Call(c, fn20742, std::move(args20743)); }()))) { auto unpack20744 = Iterate(item20741); ValidateUnpack(unpack20744, 2, false); comp20739->SetAt(0, unpack20744.at(0)); comp20739->SetAt(1, unpack20744.at(1)); if (!static_cast<bool>(([&]() -> Value { auto v20745 = ([&]() -> Value { auto v20746 = comp20739->LocalAt(0); Value v20747; v20747 = comp20739->Global("V9_COURIER_ITEMS"); if (!static_cast<bool>(Binary("In", v20746, v20747))) return Value(false); v20746 = v20747; return Value(true); }()); if (!static_cast<bool>(v20745)) return v20745; v20745 = ([&]() -> Value { auto v20748 = ([&]() -> Value { auto fn20750 = comp20739->Global("int"); Arguments args20751; args20751.Add(comp20739->LocalAt(1), false); return Call(c, fn20750, std::move(args20751)); }()); Value v20749; v20749 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v20748, v20749))) return Value(false); v20748 = v20749; return Value(true); }()); return v20745; }()))) continue; Put(result20740, comp20739->LocalAt(0), ([&]() -> Value { auto fn20752 = comp20739->Global("int"); Arguments args20753; args20753.Add(comp20739->LocalAt(1), false); return Call(c, fn20752, std::move(args20753)); }())); } return result20740; }());
s->SetAt(1, v20738);
auto v20754 = ([&]() -> Value { auto fn20755 = PrepareDictionaryGet(s->LocalAt(20)); Arguments args20756; args20756.Add(s->LocalAt(30), false); return CallDictionaryGet(c, fn20755, std::move(args20756)); }());
s->SetAt(19, v20754);
if (static_cast<bool>(([&]() -> Value { auto v20757 = s->LocalAt(19); Value v20758; v20758 = Value{}; if (!static_cast<bool>(Binary("Is", v20757, v20758))) return Value(false); v20757 = v20758; return Value(true); }()))) {
if (static_cast<bool>(([&]() -> Value { auto v20759 = Unary("Not", s->LocalAt(1)); if (static_cast<bool>(v20759)) return v20759; v20759 = ([&]() -> Value { auto fn20760 = PrepareDictionaryGet(([&]() -> Value { auto fn20762 = PrepareDictionaryGet(s->LocalAt(17)); Arguments args20763; args20763.positional.reserve(2); args20763.Add(Value("pending"), false); args20763.Add(([&]() -> Value { auto dict20764 = Dict(); return dict20764; }()), false); return CallDictionaryGet(c, fn20762, std::move(args20763)); }())); Arguments args20761; args20761.Add(s->LocalAt(30), false); return CallDictionaryGet(c, fn20760, std::move(args20761)); }()); return v20759; }()))) {
continue;
}
auto v20765 = ([&]() -> Value { auto fn20766 = s->Global("_v9_courier_plan"); Arguments args20767; args20767.positional.reserve(6); args20767.Add(s->LocalAt(29), false); args20767.Add(s->LocalAt(30), false); args20767.Add(s->LocalAt(22), false); args20767.Add(s->LocalAt(4), false); args20767.Add(s->LocalAt(28), false); args20767.Add(s->LocalAt(8), false); return Call(c, fn20766, std::move(args20767)); }());
s->SetAt(26, v20765);
if (static_cast<bool>(([&]() -> Value { auto v20768 = s->LocalAt(26); Value v20769; v20769 = Value{}; if (!static_cast<bool>(Binary("Is", v20768, v20769))) return Value(false); v20768 = v20769; return Value(true); }()))) {
continue;
}
auto v20770 = ([&]() -> Value { auto dict20771 = Dict(); auto key20772 = Value("route"); Put(dict20771, key20772, s->LocalAt(26)); auto key20773 = Value("start"); Put(dict20771, key20773, s->LocalAt(28)); return dict20771; }());
s->SetAt(19, v20770);
Put(s->LocalAt(20), s->LocalAt(30), v20770);
auto v20774 = s->Global("_V9_COURIER_REPORT");
auto v20775 = Value("courier_trips");
auto v20776 = Get(v20774, v20775);
Put(v20774, v20775, Inplace("Add", v20776, Value(int64_t{1})));
}
auto v20777 = ([&]() -> Value { auto v20778 = s->LocalAt(28); return Binary("Sub", v20778, Get(s->LocalAt(19), Value("start"))); }());
s->SetAt(11, v20777);
if (static_cast<bool>(([&]() -> Value { auto v20779 = s->LocalAt(11); Value v20780; v20780 = ([&]() -> Value { auto fn20781 = s->Global("len"); Arguments args20782; args20782.Add(Get(s->LocalAt(19), Value("route")), false); return Call(c, fn20781, std::move(args20782)); }()); if (!static_cast<bool>(Binary("GtE", v20779, v20780))) return Value(false); v20779 = v20780; return Value(true); }()))) {
continue;
}
auto v20783 = Get(Get(s->LocalAt(19), Value("route")), s->LocalAt(11));
s->SetAt(3, v20783);
if (static_cast<bool>(([&]() -> Value { auto v20784 = s->LocalAt(3); Value v20785; v20785 = List({Value("DROP")}); if (!static_cast<bool>(Binary("Eq", v20784, v20785))) return Value(false); v20784 = v20785; return Value(true); }()))) {
if (static_cast<bool>(([&]() -> Value { auto v20786 = s->LocalAt(22); Value v20787; v20787 = s->Global("_V9_COURIER_ACCESS"); if (!static_cast<bool>(Binary("NotIn", v20786, v20787))) return Value(false); v20786 = v20787; return Value(true); }()))) {
auto v20788 = ([&]() -> Value { auto dict20789 = Dict(); auto key20790 = Value("route"); Put(dict20789, key20790, List({})); auto key20791 = Value("start"); Put(dict20789, key20791, s->LocalAt(28)); return dict20789; }());
Put(s->LocalAt(20), s->LocalAt(30), v20788);
continue;
}
for (const auto& item20792 : Iterate(([&]() -> Value { auto fn20793 = Attribute(s->LocalAt(1), "items"); Arguments args20794; return Call(c, fn20793, std::move(args20794)); }()))) {
auto unpack20795 = Iterate(item20792);
ValidateUnpack(unpack20795, 2, false);
s->SetAt(14, unpack20795.at(0));
s->SetAt(16, unpack20795.at(1));
auto v20796 = ([&]() -> Value { auto v20797 = ([&]() -> Value { auto fn20798 = PrepareDictionaryGet(s->LocalAt(7)); Arguments args20799; args20799.positional.reserve(2); args20799.Add(s->LocalAt(14), false); args20799.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn20798, std::move(args20799)); }()); return Binary("Add", v20797, s->LocalAt(16)); }());
Put(s->LocalAt(7), s->LocalAt(14), v20796);
}
}
auto v20800 = s->LocalAt(3);
Put(s->LocalAt(4), s->LocalAt(30), v20800);
auto v20801 = Value(true);
s->SetAt(2, v20801);
}
if (static_cast<bool>(Unary("Not", s->LocalAt(2)))) {
return s->LocalAt(0);
}
auto v20802 = ([&]() -> Value { auto fn20803 = s->Global("dict"); Arguments args20804; args20804.Add(s->LocalAt(0), false); return Call(c, fn20803, std::move(args20804)); }());
s->SetAt(25, v20802);
auto v20805 = Tuple({Get(s->LocalAt(4), Value(int64_t{0})), Slice(s->LocalAt(4), Value(int64_t{1}), Value{}, Value{})});
auto unpack20806 = Iterate(v20805);
ValidateUnpack(unpack20806, 2, false);
Put(s->LocalAt(25), Value("farmer"), unpack20806.at(0));
Put(s->LocalAt(25), Value("hands"), unpack20806.at(1));
if (static_cast<bool>(s->LocalAt(7))) {
auto v20807 = ([&]() -> Value { auto comp20808 = std::make_shared<Scope>(); comp20808->globals = s->globals; comp20808->parent = s; static constexpr const char* comp20808_names[] = {"o"}; comp20808->PrepareSlots(comp20808_names); auto result20809 = List(); for (const auto& item20810 : Iterate(([&]() -> Value { auto v20811 = ([&]() -> Value { auto fn20812 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args20813; args20813.Add(Value("market"), false); return CallDictionaryGet(c, fn20812, std::move(args20813)); }()); if (static_cast<bool>(v20811)) return v20811; v20811 = List({}); return v20811; }()))) { comp20808->SetAt(0, item20810); result20809.node()->sequence.push_back(([&]() -> Value { auto fn20814 = comp20808->Global("list"); Arguments args20815; args20815.Add(comp20808->LocalAt(0), false); return Call(c, fn20814, std::move(args20815)); }())); } return result20809; }());
s->SetAt(15, v20807);
auto v20816 = Get(Get(s->LocalAt(18), Value("market")), Value("prices"));
s->SetAt(24, v20816);
for (const auto& item20817 : Iterate(([&]() -> Value { auto fn20818 = s->Global("sorted"); Arguments args20819; args20819.Add(([&]() -> Value { auto fn20820 = Attribute(s->LocalAt(7), "items"); Arguments args20821; return Call(c, fn20820, std::move(args20821)); }()), false); args20819.Keyword("key", Define(&Code_3209e188f8a0bd920454, s, Signature{{"kv"}, {}, {}, {}, "", "", ([]() -> std::span<const char* const> { static constexpr const char* names[] = {"kv"}; return names; }())}, true, "<lambda>")); return Call(c, fn20818, std::move(args20819)); }()))) {
auto unpack20827 = Iterate(item20817);
ValidateUnpack(unpack20827, 2, false);
s->SetAt(14, unpack20827.at(0));
s->SetAt(16, unpack20827.at(1));
if (static_cast<bool>(([&]() -> Value { auto v20828 = ([&]() -> Value { auto fn20830 = s->Global("int"); Arguments args20831; args20831.Add(([&]() -> Value { auto fn20832 = PrepareDictionaryGet(s->LocalAt(24)); Arguments args20833; args20833.positional.reserve(2); args20833.Add(s->LocalAt(14), false); args20833.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn20832, std::move(args20833)); }()), false); return Call(c, fn20830, std::move(args20831)); }()); Value v20829; v20829 = Value(int64_t{2}); if (!static_cast<bool>(Binary("Lt", v20828, v20829))) return Value(false); v20828 = v20829; return Value(true); }()))) {
continue;
}
auto v20834 = ([&]() -> Value { auto comp20835 = std::make_shared<Scope>(); comp20835->globals = s->globals; comp20835->parent = s; static constexpr const char* comp20835_names[] = {"o"}; comp20835->PrepareSlots(comp20835_names); auto result20836 = List(); auto fallback = Value{}; for (const auto& item20837 : Iterate(s->LocalAt(15))) { comp20835->SetAt(0, item20837); if (!static_cast<bool>(([&]() -> Value { auto v20838 = comp20835->LocalAt(0); if (!static_cast<bool>(v20838)) return v20838; v20838 = ([&]() -> Value { auto v20839 = Get(comp20835->LocalAt(0), Value(int64_t{0})); Value v20840; v20840 = Value("SELL"); if (!static_cast<bool>(Binary("Eq", v20839, v20840))) return Value(false); v20839 = v20840; return Value(true); }()); if (!static_cast<bool>(v20838)) return v20838; v20838 = ([&]() -> Value { auto v20841 = ([&]() -> Value { auto fn20843 = comp20835->Global("len"); Arguments args20844; args20844.Add(comp20835->LocalAt(0), false); return Call(c, fn20843, std::move(args20844)); }()); Value v20842; v20842 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v20841, v20842))) return Value(false); v20841 = v20842; return Value(true); }()); if (!static_cast<bool>(v20838)) return v20838; v20838 = ([&]() -> Value { auto v20845 = Get(comp20835->LocalAt(0), Value(int64_t{1})); Value v20846; v20846 = comp20835->Captured("item"); if (!static_cast<bool>(Binary("Eq", v20845, v20846))) return Value(false); v20845 = v20846; return Value(true); }()); return v20838; }()))) continue; return comp20835->LocalAt(0); } return fallback; }());
s->SetAt(9, v20834);
if (static_cast<bool>(([&]() -> Value { auto v20847 = s->LocalAt(9); Value v20848; v20848 = Value{}; if (!static_cast<bool>(Binary("IsNot", v20847, v20848))) return Value(false); v20847 = v20848; return Value(true); }()))) {
auto v20849 = ([&]() -> Value { auto v20850 = ([&]() -> Value { auto fn20851 = s->Global("int"); Arguments args20852; args20852.Add(Get(s->LocalAt(9), Value(int64_t{2})), false); return Call(c, fn20851, std::move(args20852)); }()); return Binary("Add", v20850, s->LocalAt(16)); }());
Put(s->LocalAt(9), Value(int64_t{2}), v20849);
(void)([&]() -> Value { auto fn20853 = Attribute(s->LocalAt(15), "remove"); Arguments args20854; args20854.Add(s->LocalAt(9), false); return Call(c, fn20853, std::move(args20854)); }());
(void)([&]() -> Value { auto fn20855 = Attribute(s->LocalAt(15), "insert"); Arguments args20856; args20856.positional.reserve(2); args20856.Add(Value(int64_t{0}), false); args20856.Add(s->LocalAt(9), false); return Call(c, fn20855, std::move(args20856)); }());
}
else {
if (static_cast<bool>(([&]() -> Value { auto v20857 = ([&]() -> Value { auto fn20859 = s->Global("len"); Arguments args20860; args20860.Add(s->LocalAt(15), false); return Call(c, fn20859, std::move(args20860)); }()); Value v20858; v20858 = s->Global("MAX_ORDERS"); if (!static_cast<bool>(Binary("Lt", v20857, v20858))) return Value(false); v20857 = v20858; return Value(true); }()))) {
(void)([&]() -> Value { auto fn20861 = Attribute(s->LocalAt(15), "insert"); Arguments args20862; args20862.positional.reserve(2); args20862.Add(Value(int64_t{0}), false); args20862.Add(List({Value("SELL"), s->LocalAt(14), s->LocalAt(16)}), false); return Call(c, fn20861, std::move(args20862)); }());
}
}
auto v20863 = s->Global("_V9_COURIER_REPORT");
auto v20864 = Value("courier_units");
auto v20865 = Get(v20863, v20864);
Put(v20863, v20864, Inplace("Add", v20865, s->LocalAt(16)));
}
auto v20866 = s->LocalAt(15);
Put(s->LocalAt(25), Value("market"), v20866);
}
return s->LocalAt(25);
return {};
}
}  // namespace kagg::opponents::compiled
