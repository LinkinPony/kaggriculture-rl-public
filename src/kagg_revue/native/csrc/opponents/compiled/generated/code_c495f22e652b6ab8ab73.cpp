// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_c495f22e652b6ab8ab73(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "age", "changed", "farm", "intent", "k", "obs", "player", "positions", "prev", "st", "step", "tape_now", "tape_prev", "tile", "tiles", "tx", "units", "x", "y"};
s->PrepareSlots(s_names);
auto v25758 = ([&]() -> Value { auto fn25759 = s->Global("int"); Arguments args25760; args25760.Add(Get(s->LocalAt(6), Value("step")), false); return Call(c, fn25759, std::move(args25760)); }());
s->SetAt(11, v25758);
auto v25761 = ([&]() -> Value { auto fn25762 = s->Global("int"); Arguments args25763; args25763.Add(Get(s->LocalAt(6), Value("player")), false); return Call(c, fn25762, std::move(args25763)); }());
s->SetAt(7, v25761);
auto v25764 = ([&]() -> Value { auto fn25765 = Attribute(s->Global("_E343_WL_STATE"), "setdefault"); Arguments args25766; args25766.positional.reserve(2); args25766.Add(s->LocalAt(7), false); args25766.Add(([&]() -> Value { auto dict25767 = Dict(); auto key25768 = Value("step"); Put(dict25767, key25768, Unary("USub", Value(int64_t{1}))); auto key25769 = Value("active"); Put(dict25767, key25769, ([&]() -> Value { auto dict25770 = Dict(); return dict25770; }())); return dict25767; }()), false); return Call(c, fn25765, std::move(args25766)); }());
s->SetAt(10, v25764);
if (static_cast<bool>(([&]() -> Value { auto v25771 = s->LocalAt(11); Value v25772; v25772 = Get(s->LocalAt(10), Value("step")); if (!static_cast<bool>(Binary("LtE", v25771, v25772))) return Value(false); v25771 = v25772; return Value(true); }()))) {
auto v25773 = ([&]() -> Value { auto dict25774 = Dict(); return dict25774; }());
Put(s->LocalAt(10), Value("active"), v25773);
}
auto v25775 = s->LocalAt(11);
Put(s->LocalAt(10), Value("step"), v25775);
if (static_cast<bool>(([&]() -> Value { auto v25776 = ([&]() -> Value { auto v25778 = s->LocalAt(11); return Binary("Mod", v25778, Value(int64_t{24})); }()); Value v25777; v25777 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v25776, v25777))) return Value(false); v25776 = v25777; return Value(true); }()))) {
auto v25779 = ([&]() -> Value { auto dict25780 = Dict(); return dict25780; }());
Put(s->LocalAt(10), Value("active"), v25779);
}
auto v25781 = Get(Get(s->LocalAt(6), Value("farms")), s->LocalAt(7));
s->SetAt(3, v25781);
auto v25782 = ([&]() -> Value { Arguments args25783; args25783.Add(([&]() -> Value { auto fn25784 = s->Global("tuple"); Arguments args25785; args25785.Add(Get(s->LocalAt(3), Value("farmer")), false); return Call(c, fn25784, std::move(args25785)); }()), false); args25783.Add(([&]() -> Value { auto fn25786 = s->Global("map"); Arguments args25787; args25787.positional.reserve(2); args25787.Add(s->Global("tuple"), false); args25787.Add(Get(s->LocalAt(3), Value("hands")), false); return Call(c, fn25786, std::move(args25787)); }()), true); return List(std::move(args25783.positional)); }());
s->SetAt(8, v25782);
auto v25788 = Get(s->LocalAt(3), Value("tiles"));
s->SetAt(15, v25788);
auto v25789 = ([&]() -> Value { Arguments args25790; args25790.Add(([&]() -> Value { auto fn25791 = s->Global("list"); Arguments args25792; args25792.Add(([&]() -> Value { auto v25793 = ([&]() -> Value { auto fn25794 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args25795; args25795.Add(Value("farmer"), false); return CallDictionaryGet(c, fn25794, std::move(args25795)); }()); if (static_cast<bool>(v25793)) return v25793; v25793 = List({Value("PASS")}); return v25793; }()), false); return Call(c, fn25791, std::move(args25792)); }()), false); args25790.Add(([&]() -> Value { auto comp25796 = std::make_shared<Scope>(); comp25796->globals = s->globals; comp25796->parent = s; static constexpr const char* comp25796_names[] = {"h"}; comp25796->PrepareSlots(comp25796_names); auto result25797 = List(); for (const auto& item25798 : Iterate(([&]() -> Value { auto v25799 = ([&]() -> Value { auto fn25800 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args25801; args25801.Add(Value("hands"), false); return CallDictionaryGet(c, fn25800, std::move(args25801)); }()); if (static_cast<bool>(v25799)) return v25799; v25799 = List({}); return v25799; }()))) { comp25796->SetAt(0, item25798); result25797.node()->sequence.push_back((static_cast<bool>(([&]() -> Value { auto fn25802 = comp25796->Global("isinstance"); Arguments args25803; args25803.positional.reserve(2); args25803.Add(comp25796->LocalAt(0), false); args25803.Add(comp25796->Global("list"), false); return Call(c, fn25802, std::move(args25803)); }())) ? ([&]() -> Value { auto fn25804 = comp25796->Global("list"); Arguments args25805; args25805.Add(comp25796->LocalAt(0), false); return Call(c, fn25804, std::move(args25805)); }()) : List({Value("PASS")}))); } return result25797; }()), true); return List(std::move(args25790.positional)); }());
s->SetAt(17, v25789);
auto v25806 = ([&]() -> Value { auto fn25807 = s->Global("_e343_tape_units"); Arguments args25808; args25808.positional.reserve(2); args25808.Add(s->LocalAt(7), false); args25808.Add(s->LocalAt(11), false); return Call(c, fn25807, std::move(args25808)); }());
s->SetAt(12, v25806);
auto v25809 = ([&]() -> Value { auto fn25810 = s->Global("_e343_tape_units"); Arguments args25811; args25811.positional.reserve(2); args25811.Add(s->LocalAt(7), false); args25811.Add(([&]() -> Value { auto v25812 = s->LocalAt(11); return Binary("Sub", v25812, Value(int64_t{1})); }()), false); return Call(c, fn25810, std::move(args25811)); }());
s->SetAt(13, v25809);
auto v25813 = Value(false);
s->SetAt(2, v25813);
for (const auto& item25814 : Iterate(([&]() -> Value { auto fn25815 = s->Global("list"); Arguments args25816; args25816.Add(([&]() -> Value { auto fn25817 = Attribute(Get(s->LocalAt(10), Value("active")), "items"); Arguments args25818; return Call(c, fn25817, std::move(args25818)); }()), false); return Call(c, fn25815, std::move(args25816)); }()))) {
auto unpack25819 = Iterate(item25814);
ValidateUnpack(unpack25819, 2, false);
s->SetAt(5, unpack25819.at(0));
s->SetAt(16, unpack25819.at(1));
if (static_cast<bool>(([&]() -> Value { auto v25820 = ([&]() -> Value { auto v25821 = s->LocalAt(5); Value v25822; v25822 = ([&]() -> Value { auto fn25823 = s->Global("len"); Arguments args25824; args25824.Add(s->LocalAt(17), false); return Call(c, fn25823, std::move(args25824)); }()); if (!static_cast<bool>(Binary("GtE", v25821, v25822))) return Value(false); v25821 = v25822; return Value(true); }()); if (static_cast<bool>(v25820)) return v25820; v25820 = ([&]() -> Value { auto v25825 = s->LocalAt(5); Value v25826; v25826 = ([&]() -> Value { auto fn25827 = s->Global("len"); Arguments args25828; args25828.Add(s->LocalAt(8), false); return Call(c, fn25827, std::move(args25828)); }()); if (!static_cast<bool>(Binary("GtE", v25825, v25826))) return Value(false); v25825 = v25826; return Value(true); }()); return v25820; }()))) {
(void)([&]() -> Value { auto fn25829 = Attribute(Get(s->LocalAt(10), Value("active")), "pop"); Arguments args25830; args25830.positional.reserve(2); args25830.Add(s->LocalAt(5), false); args25830.Add(Value{}, false); return Call(c, fn25829, std::move(args25830)); }());
continue;
}
auto v25831 = ([&]() -> Value { auto v25832 = s->LocalAt(11); return Binary("Sub", v25832, Get(s->LocalAt(16), Value("start"))); }());
s->SetAt(1, v25831);
if (static_cast<bool>(([&]() -> Value { auto v25833 = s->LocalAt(1); Value v25834; v25834 = Value(int64_t{1}); if (!static_cast<bool>(Binary("Eq", v25833, v25834))) return Value(false); v25833 = v25834; return Value(true); }()))) {
auto v25835 = ([&]() -> Value { auto fn25836 = s->Global("list"); Arguments args25837; args25837.Add(Get(s->LocalAt(16), Value("intended")), false); return Call(c, fn25836, std::move(args25837)); }());
Put(s->LocalAt(17), s->LocalAt(5), v25835);
auto v25838 = Value(true);
s->SetAt(2, v25838);
auto v25839 = s->Global("_E343_WL_REPORT");
auto v25840 = Value("replays");
auto v25841 = Get(v25839, v25840);
Put(v25839, v25840, Inplace("Add", v25841, Value(int64_t{1})));
}
else {
if (static_cast<bool>(([&]() -> Value { auto v25842 = Value(int64_t{2}); Value v25843; v25843 = s->LocalAt(1); if (!static_cast<bool>(Binary("LtE", v25842, v25843))) return Value(false); v25842 = v25843; v25843 = ([&]() -> Value { auto v25844 = Value(int64_t{1}); return Binary("Add", v25844, s->Global("_E343_WL_STEPS")); }()); if (!static_cast<bool>(Binary("LtE", v25842, v25843))) return Value(false); v25842 = v25843; return Value(true); }()))) {
auto v25845 = (static_cast<bool>(([&]() -> Value { auto v25846 = s->LocalAt(5); Value v25847; v25847 = ([&]() -> Value { auto fn25848 = s->Global("len"); Arguments args25849; args25849.Add(s->LocalAt(13), false); return Call(c, fn25848, std::move(args25849)); }()); if (!static_cast<bool>(Binary("Lt", v25846, v25847))) return Value(false); v25846 = v25847; return Value(true); }())) ? Get(s->LocalAt(13), s->LocalAt(5)) : List({Value("PASS")}));
s->SetAt(9, v25845);
auto v25850 = (static_cast<bool>(([&]() -> Value { auto v25851 = ([&]() -> Value { auto fn25852 = s->Global("isinstance"); Arguments args25853; args25853.positional.reserve(2); args25853.Add(s->LocalAt(9), false); args25853.Add(s->Global("list"), false); return Call(c, fn25852, std::move(args25853)); }()); if (!static_cast<bool>(v25851)) return v25851; v25851 = s->LocalAt(9); return v25851; }())) ? ([&]() -> Value { auto fn25854 = s->Global("list"); Arguments args25855; args25855.Add(s->LocalAt(9), false); return Call(c, fn25854, std::move(args25855)); }()) : List({Value("PASS")}));
Put(s->LocalAt(17), s->LocalAt(5), v25850);
auto v25856 = Value(true);
s->SetAt(2, v25856);
auto v25857 = s->Global("_E343_WL_REPORT");
auto v25858 = Value("replays");
auto v25859 = Get(v25857, v25858);
Put(v25857, v25858, Inplace("Add", v25859, Value(int64_t{1})));
}
else {
(void)([&]() -> Value { auto fn25860 = Attribute(Get(s->LocalAt(10), Value("active")), "pop"); Arguments args25861; args25861.positional.reserve(2); args25861.Add(s->LocalAt(5), false); args25861.Add(Value{}, false); return Call(c, fn25860, std::move(args25861)); }());
}
}
}
for (const auto& item25862 : Iterate(([&]() -> Value { auto fn25863 = s->Global("range"); Arguments args25864; args25864.Add(([&]() -> Value { auto fn25865 = s->Global("min"); Arguments args25866; args25866.positional.reserve(3); args25866.Add(([&]() -> Value { auto fn25867 = s->Global("len"); Arguments args25868; args25868.Add(s->LocalAt(17), false); return Call(c, fn25867, std::move(args25868)); }()), false); args25866.Add(([&]() -> Value { auto fn25869 = s->Global("len"); Arguments args25870; args25870.Add(s->LocalAt(8), false); return Call(c, fn25869, std::move(args25870)); }()), false); args25866.Add(([&]() -> Value { auto fn25871 = s->Global("len"); Arguments args25872; args25872.Add(s->LocalAt(12), false); return Call(c, fn25871, std::move(args25872)); }()), false); return Call(c, fn25865, std::move(args25866)); }()), false); return Call(c, fn25863, std::move(args25864)); }()))) {
s->SetAt(5, item25862);
if (static_cast<bool>(([&]() -> Value { auto v25873 = s->LocalAt(5); Value v25874; v25874 = Get(s->LocalAt(10), Value("active")); if (!static_cast<bool>(Binary("In", v25873, v25874))) return Value(false); v25873 = v25874; return Value(true); }()))) {
continue;
}
auto v25875 = Get(s->LocalAt(12), s->LocalAt(5));
s->SetAt(4, v25875);
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto v25876 = ([&]() -> Value { auto fn25877 = s->Global("isinstance"); Arguments args25878; args25878.positional.reserve(2); args25878.Add(s->LocalAt(4), false); args25878.Add(s->Global("list"), false); return Call(c, fn25877, std::move(args25878)); }()); if (!static_cast<bool>(v25876)) return v25876; v25876 = s->LocalAt(4); if (!static_cast<bool>(v25876)) return v25876; v25876 = ([&]() -> Value { auto v25879 = Get(s->LocalAt(4), Value(int64_t{0})); Value v25880; v25880 = s->Global("_E343_WL_OPS"); if (!static_cast<bool>(Binary("In", v25879, v25880))) return Value(false); v25879 = v25880; return Value(true); }()); return v25876; }())))) {
continue;
}
auto v25881 = Get(s->LocalAt(8), s->LocalAt(5));
auto unpack25882 = Iterate(v25881);
ValidateUnpack(unpack25882, 2, false);
s->SetAt(18, unpack25882.at(0));
s->SetAt(19, unpack25882.at(1));
auto v25883 = Get(Get(s->LocalAt(15), s->LocalAt(19)), s->LocalAt(18));
s->SetAt(14, v25883);
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto v25884 = ([&]() -> Value { auto fn25885 = s->Global("isinstance"); Arguments args25886; args25886.positional.reserve(2); args25886.Add(s->LocalAt(14), false); args25886.Add(s->Global("dict"), false); return Call(c, fn25885, std::move(args25886)); }()); if (!static_cast<bool>(v25884)) return v25884; v25884 = ([&]() -> Value { auto v25887 = ([&]() -> Value { auto fn25889 = PrepareDictionaryGet(s->LocalAt(14)); Arguments args25890; args25890.Add(Value("kind"), false); return CallDictionaryGet(c, fn25889, std::move(args25890)); }()); Value v25888; v25888 = Value("WEED"); if (!static_cast<bool>(Binary("Eq", v25887, v25888))) return Value(false); v25887 = v25888; return Value(true); }()); return v25884; }())))) {
continue;
}
if (static_cast<bool>(([&]() -> Value { auto v25891 = Get(s->LocalAt(17), s->LocalAt(5)); Value v25892; v25892 = List({Value("DIG")}); if (!static_cast<bool>(Binary("NotEq", v25891, v25892))) return Value(false); v25891 = v25892; return Value(true); }()))) {
auto v25893 = List({Value("DIG")});
Put(s->LocalAt(17), s->LocalAt(5), v25893);
auto v25894 = Value(true);
s->SetAt(2, v25894);
}
auto v25895 = ([&]() -> Value { auto dict25896 = Dict(); auto key25897 = Value("start"); Put(dict25896, key25897, s->LocalAt(11)); auto key25898 = Value("intended"); Put(dict25896, key25898, ([&]() -> Value { auto fn25899 = s->Global("list"); Arguments args25900; args25900.Add(s->LocalAt(4), false); return Call(c, fn25899, std::move(args25900)); }())); return dict25896; }());
Put(Get(s->LocalAt(10), Value("active")), s->LocalAt(5), v25895);
auto v25901 = s->Global("_E343_WL_REPORT");
auto v25902 = Value("events");
auto v25903 = Get(v25901, v25902);
Put(v25901, v25902, Inplace("Add", v25903, Value(int64_t{1})));
}
if (static_cast<bool>(Unary("Not", s->LocalAt(2)))) {
return s->LocalAt(0);
}
return ([&]() -> Value { auto fn25904 = s->Global("dict"); Arguments args25905; args25905.Add(s->LocalAt(0), false); args25905.Keyword("farmer", Get(s->LocalAt(17), Value(int64_t{0}))); args25905.Keyword("hands", Slice(s->LocalAt(17), Value(int64_t{1}), Value{}, Value{})); return Call(c, fn25904, std::move(args25905)); }());
return {};
}
}  // namespace kagg::opponents::compiled
