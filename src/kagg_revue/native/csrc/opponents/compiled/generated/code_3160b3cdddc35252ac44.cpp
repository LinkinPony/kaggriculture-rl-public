// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_3160b3cdddc35252ac44(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "before", "budget", "i", "n", "obs", "order", "player", "reserve", "result"};
s->PrepareSlots(s_names);
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto comp10765 = std::make_shared<Scope>(); comp10765->globals = s->globals; comp10765->parent = s; static constexpr const char* comp10765_names[] = {"o"}; comp10765->PrepareSlots(comp10765_names); auto result10766 = List(); for (const auto& item10767 : Iterate(([&]() -> Value { auto fn10768 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args10769; args10769.positional.reserve(2); args10769.Add(Value("market"), false); args10769.Add(List({}), false); return CallDictionaryGet(c, fn10768, std::move(args10769)); }()))) { comp10765->SetAt(0, item10767); if (static_cast<bool>(([&]() -> Value { auto v10770 = comp10765->LocalAt(0); if (!static_cast<bool>(v10770)) return v10770; v10770 = ([&]() -> Value { auto v10771 = Get(comp10765->LocalAt(0), Value(int64_t{0})); Value v10772; v10772 = Value("BUY_SEED"); if (!static_cast<bool>(Binary("Eq", v10771, v10772))) return Value(false); v10771 = v10772; return Value(true); }()); return v10770; }()))) return Value(true); } return Value(false); }())))) {
return s->LocalAt(0);
}
auto v10773 = ([&]() -> Value { auto fn10774 = s->Global("int"); Arguments args10775; args10775.Add(Get(s->LocalAt(5), Value("player")), false); return Call(c, fn10774, std::move(args10775)); }());
s->SetAt(7, v10773);
auto v10776 = ([&]() -> Value { auto fn10777 = s->Global("dict"); Arguments args10778; args10778.Add(s->LocalAt(5), false); args10778.Keyword("farms", ([&]() -> Value { auto comp10779 = std::make_shared<Scope>(); comp10779->globals = s->globals; comp10779->parent = s; static constexpr const char* comp10779_names[] = {"f"}; comp10779->PrepareSlots(comp10779_names); auto result10780 = List(); for (const auto& item10781 : Iterate(Get(s->LocalAt(5), Value("farms")))) { comp10779->SetAt(0, item10781); result10780.node()->sequence.push_back(([&]() -> Value { auto fn10782 = comp10779->Global("dict"); Arguments args10783; args10783.Add(comp10779->LocalAt(0), false); return Call(c, fn10782, std::move(args10783)); }())); } return result10780; }())); return Call(c, fn10777, std::move(args10778)); }());
s->SetAt(2, v10776);
auto v10784 = Get(Get(s->LocalAt(2), Value("farms")), s->LocalAt(7));
auto v10785 = Value("money");
auto v10786 = Get(v10784, v10785);
Put(v10784, v10785, Inplace("Sub", v10786, s->LocalAt(8)));
if (static_cast<bool>(([&]() -> Value { auto fn10787 = s->Global("_r97_budget"); Arguments args10788; args10788.positional.reserve(2); args10788.Add(s->LocalAt(2), false); args10788.Add(([&]() -> Value { auto fn10789 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args10790; args10790.positional.reserve(2); args10790.Add(Value("market"), false); args10790.Add(List({}), false); return CallDictionaryGet(c, fn10789, std::move(args10790)); }()), false); return Call(c, fn10787, std::move(args10788)); }()))) {
return s->LocalAt(0);
}
auto v10791 = ([&]() -> Value { auto fn10792 = Attribute(s->Global("copy"), "deepcopy"); Arguments args10793; args10793.Add(s->LocalAt(0), false); return Call(c, fn10792, std::move(args10793)); }());
s->SetAt(9, v10791);
for (const auto& item10794 : Iterate(([&]() -> Value { auto fn10795 = s->Global("range"); Arguments args10796; args10796.positional.reserve(3); args10796.Add(([&]() -> Value { auto v10797 = ([&]() -> Value { auto fn10798 = s->Global("len"); Arguments args10799; args10799.Add(Get(s->LocalAt(9), Value("market")), false); return Call(c, fn10798, std::move(args10799)); }()); return Binary("Sub", v10797, Value(int64_t{1})); }()), false); args10796.Add(Unary("USub", Value(int64_t{1})), false); args10796.Add(Unary("USub", Value(int64_t{1})), false); return Call(c, fn10795, std::move(args10796)); }()))) {
s->SetAt(3, item10794);
auto v10800 = Get(Get(s->LocalAt(9), Value("market")), s->LocalAt(3));
s->SetAt(6, v10800);
if (static_cast<bool>(([&]() -> Value { auto v10801 = ([&]() -> Value { auto v10802 = ([&]() -> Value { auto fn10804 = s->Global("len"); Arguments args10805; args10805.Add(s->LocalAt(6), false); return Call(c, fn10804, std::move(args10805)); }()); Value v10803; v10803 = Value(int64_t{3}); if (!static_cast<bool>(Binary("Lt", v10802, v10803))) return Value(false); v10802 = v10803; return Value(true); }()); if (static_cast<bool>(v10801)) return v10801; v10801 = ([&]() -> Value { auto v10806 = Get(s->LocalAt(6), Value(int64_t{0})); Value v10807; v10807 = Value("BUY_SEED"); if (!static_cast<bool>(Binary("NotEq", v10806, v10807))) return Value(false); v10806 = v10807; return Value(true); }()); return v10801; }()))) {
continue;
}
auto v10808 = ([&]() -> Value { auto fn10809 = s->Global("max"); Arguments args10810; args10810.positional.reserve(2); args10810.Add(Value(int64_t{0}), false); args10810.Add(([&]() -> Value { auto fn10811 = s->Global("int"); Arguments args10812; args10812.Add(Get(s->LocalAt(6), Value(int64_t{2})), false); return Call(c, fn10811, std::move(args10812)); }()), false); return Call(c, fn10809, std::move(args10810)); }());
s->SetAt(1, v10808);
auto v10813 = s->LocalAt(1);
Put(s->LocalAt(6), Value(int64_t{2}), v10813);
while (static_cast<bool>(([&]() -> Value { auto v10814 = ([&]() -> Value { auto v10815 = Get(s->LocalAt(6), Value(int64_t{2})); Value v10816; v10816 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v10815, v10816))) return Value(false); v10815 = v10816; return Value(true); }()); if (!static_cast<bool>(v10814)) return v10814; v10814 = Unary("Not", ([&]() -> Value { auto fn10817 = s->Global("_r97_budget"); Arguments args10818; args10818.positional.reserve(2); args10818.Add(s->LocalAt(2), false); args10818.Add(Get(s->LocalAt(9), Value("market")), false); return Call(c, fn10817, std::move(args10818)); }())); return v10814; }()))) {
auto v10819 = s->LocalAt(6);
auto v10820 = Value(int64_t{2});
auto v10821 = Get(v10819, v10820);
Put(v10819, v10820, Inplace("Sub", v10821, Value(int64_t{1})));
}
auto v10822 = ([&]() -> Value { auto v10823 = s->LocalAt(1); return Binary("Sub", v10823, Get(s->LocalAt(6), Value(int64_t{2}))); }());
s->SetAt(4, v10822);
if (static_cast<bool>(s->LocalAt(4))) {
auto v10824 = s->Global("_R124_REPORT");
auto v10825 = Value("opening_seed_budget_units");
auto v10826 = Get(v10824, v10825);
Put(v10824, v10825, Inplace("Add", v10826, s->LocalAt(4)));
auto v10827 = s->Global("_R124_REPORT");
auto v10828 = Value("opening_seed_budget_cost");
auto v10829 = Get(v10827, v10828);
Put(v10827, v10828, Inplace("Add", v10829, ([&]() -> Value { auto v10830 = s->LocalAt(4); return Binary("Mult", v10830, Get(([&]() -> Value { auto dict10831 = Dict(); auto key10832 = Value("WHEAT"); Put(dict10831, key10832, Value(int64_t{10})); auto key10833 = Value("CARROT"); Put(dict10831, key10833, Value(int64_t{20})); auto key10834 = Value("TOMATO"); Put(dict10831, key10834, Value(int64_t{50})); auto key10835 = Value("STRAWBERRY"); Put(dict10831, key10835, Value(int64_t{100})); auto key10836 = Value("MELON"); Put(dict10831, key10836, Value(int64_t{80})); return dict10831; }()), Get(s->LocalAt(6), Value(int64_t{1})))); }())));
}
if (static_cast<bool>(([&]() -> Value { auto fn10837 = s->Global("_r97_budget"); Arguments args10838; args10838.positional.reserve(2); args10838.Add(s->LocalAt(2), false); args10838.Add(Get(s->LocalAt(9), Value("market")), false); return Call(c, fn10837, std::move(args10838)); }()))) {
break;
}
}
return s->LocalAt(9);
return {};
}
}  // namespace kagg::opponents::compiled
