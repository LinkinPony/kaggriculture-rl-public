// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_a423402db469189e15ca(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"_", "act", "action", "board", "cmd", "dx", "dy", "farm", "half", "i", "nx", "ny", "obs", "out", "pos", "positions", "seat", "start", "step", "t", "t_end", "units"};
s->PrepareSlots(s_names);
auto v21763 = ([&]() -> Value { auto fn21764 = s->Global("int"); Arguments args21765; args21765.Add(Get(s->LocalAt(12), Value("player")), false); return Call(c, fn21764, std::move(args21765)); }());
s->SetAt(16, v21763);
auto v21766 = ([&]() -> Value { auto fn21767 = s->Global("int"); Arguments args21768; args21768.Add(Get(s->LocalAt(12), Value("step")), false); return Call(c, fn21767, std::move(args21768)); }());
s->SetAt(18, v21766);
auto v21769 = Get(Get(s->LocalAt(12), Value("farms")), s->LocalAt(16));
s->SetAt(7, v21769);
auto v21770 = ([&]() -> Value { auto fn21771 = s->Global("len"); Arguments args21772; args21772.Add(Get(s->LocalAt(7), Value("tiles")), false); return Call(c, fn21771, std::move(args21772)); }());
s->SetAt(3, v21770);
auto v21773 = ([&]() -> Value { auto v21774 = s->LocalAt(3); return Binary("FloorDiv", v21774, Value(int64_t{2})); }());
s->SetAt(8, v21773);
auto v21775 = ([&]() -> Value { auto v21776 = List({([&]() -> Value { auto fn21777 = s->Global("list"); Arguments args21778; args21778.Add(Get(s->LocalAt(7), Value("farmer")), false); return Call(c, fn21777, std::move(args21778)); }())}); return Binary("Add", v21776, ([&]() -> Value { auto comp21779 = std::make_shared<Scope>(); comp21779->globals = s->globals; comp21779->parent = s; static constexpr const char* comp21779_names[] = {"h"}; comp21779->PrepareSlots(comp21779_names); auto result21780 = List(); for (const auto& item21781 : Iterate(Get(s->LocalAt(7), Value("hands")))) { comp21779->SetAt(0, item21781); result21780.node()->sequence.push_back(([&]() -> Value { auto fn21782 = comp21779->Global("list"); Arguments args21783; args21783.Add(comp21779->LocalAt(0), false); return Call(c, fn21782, std::move(args21783)); }())); } return result21780; }())); }());
s->SetAt(15, v21775);
auto v21784 = List({});
s->SetAt(13, v21784);
for (const auto& item21785 : Iterate(([&]() -> Value { auto fn21786 = s->Global("range"); Arguments args21787; args21787.positional.reserve(2); args21787.Add(s->LocalAt(18), false); args21787.Add(([&]() -> Value { auto v21788 = ([&]() -> Value { auto fn21789 = s->Global("min"); Arguments args21790; args21790.positional.reserve(2); args21790.Add(s->LocalAt(20), false); args21790.Add(Value(int64_t{719}), false); return Call(c, fn21789, std::move(args21790)); }()); return Binary("Add", v21788, Value(int64_t{1})); }()), false); return Call(c, fn21786, std::move(args21787)); }()))) {
s->SetAt(19, item21785);
auto v21791 = (static_cast<bool>(([&]() -> Value { auto v21792 = s->LocalAt(19); Value v21793; v21793 = s->LocalAt(18); if (!static_cast<bool>(Binary("Eq", v21792, v21793))) return Value(false); v21792 = v21793; return Value(true); }())) ? s->LocalAt(2) : ([&]() -> Value { auto fn21794 = s->Global("_ca_tape"); Arguments args21795; args21795.positional.reserve(2); args21795.Add(s->LocalAt(16), false); args21795.Add(s->LocalAt(19), false); return Call(c, fn21794, std::move(args21795)); }()));
s->SetAt(1, v21791);
auto v21796 = ([&]() -> Value { auto v21797 = List({([&]() -> Value { auto v21798 = ([&]() -> Value { auto fn21799 = PrepareDictionaryGet(s->LocalAt(1)); Arguments args21800; args21800.Add(Value("farmer"), false); return CallDictionaryGet(c, fn21799, std::move(args21800)); }()); if (static_cast<bool>(v21798)) return v21798; v21798 = List({Value("PASS")}); return v21798; }())}); return Binary("Add", v21797, ([&]() -> Value { auto fn21801 = s->Global("list"); Arguments args21802; args21802.Add(([&]() -> Value { auto v21803 = ([&]() -> Value { auto fn21804 = PrepareDictionaryGet(s->LocalAt(1)); Arguments args21805; args21805.Add(Value("hands"), false); return CallDictionaryGet(c, fn21804, std::move(args21805)); }()); if (static_cast<bool>(v21803)) return v21803; v21803 = List({}); return v21803; }()), false); return Call(c, fn21801, std::move(args21802)); }())); }());
s->SetAt(21, v21796);
for (const auto& item21806 : Iterate(([&]() -> Value { auto fn21807 = s->Global("range"); Arguments args21808; args21808.Add(([&]() -> Value { auto fn21809 = s->Global("len"); Arguments args21810; args21810.Add(s->LocalAt(15), false); return Call(c, fn21809, std::move(args21810)); }()), false); return Call(c, fn21807, std::move(args21808)); }()))) {
s->SetAt(9, item21806);
auto v21811 = (static_cast<bool>(([&]() -> Value { auto v21812 = ([&]() -> Value { auto v21813 = s->LocalAt(9); Value v21814; v21814 = ([&]() -> Value { auto fn21815 = s->Global("len"); Arguments args21816; args21816.Add(s->LocalAt(21), false); return Call(c, fn21815, std::move(args21816)); }()); if (!static_cast<bool>(Binary("Lt", v21813, v21814))) return Value(false); v21813 = v21814; return Value(true); }()); if (!static_cast<bool>(v21812)) return v21812; v21812 = Get(s->LocalAt(21), s->LocalAt(9)); return v21812; }())) ? Get(s->LocalAt(21), s->LocalAt(9)) : List({Value("PASS")}));
s->SetAt(4, v21811);
if (static_cast<bool>(([&]() -> Value { auto v21817 = Get(s->LocalAt(4), Value(int64_t{0})); Value v21818; v21818 = s->Global("_CA_MOVES"); if (!static_cast<bool>(Binary("In", v21817, v21818))) return Value(false); v21817 = v21818; return Value(true); }()))) {
auto v21819 = Get(s->Global("_CA_MOVES"), Get(s->LocalAt(4), Value(int64_t{0})));
auto unpack21820 = Iterate(v21819);
ValidateUnpack(unpack21820, 2, false);
s->SetAt(5, unpack21820.at(0));
s->SetAt(6, unpack21820.at(1));
auto v21821 = Tuple({([&]() -> Value { auto v21822 = Get(Get(s->LocalAt(15), s->LocalAt(9)), Value(int64_t{0})); return Binary("Add", v21822, s->LocalAt(5)); }()), ([&]() -> Value { auto v21823 = Get(Get(s->LocalAt(15), s->LocalAt(9)), Value(int64_t{1})); return Binary("Add", v21823, s->LocalAt(6)); }())});
auto unpack21824 = Iterate(v21821);
ValidateUnpack(unpack21824, 2, false);
s->SetAt(10, unpack21824.at(0));
s->SetAt(11, unpack21824.at(1));
if (static_cast<bool>(([&]() -> Value { auto v21825 = ([&]() -> Value { auto v21826 = Value(int64_t{0}); Value v21827; v21827 = s->LocalAt(10); if (!static_cast<bool>(Binary("LtE", v21826, v21827))) return Value(false); v21826 = v21827; v21827 = s->LocalAt(3); if (!static_cast<bool>(Binary("Lt", v21826, v21827))) return Value(false); v21826 = v21827; return Value(true); }()); if (!static_cast<bool>(v21825)) return v21825; v21825 = ([&]() -> Value { auto v21828 = Value(int64_t{0}); Value v21829; v21829 = s->LocalAt(11); if (!static_cast<bool>(Binary("LtE", v21828, v21829))) return Value(false); v21828 = v21829; v21829 = s->LocalAt(3); if (!static_cast<bool>(Binary("Lt", v21828, v21829))) return Value(false); v21828 = v21829; return Value(true); }()); return v21825; }()))) {
auto v21830 = List({s->LocalAt(10), s->LocalAt(11)});
Put(s->LocalAt(15), s->LocalAt(9), v21830);
}
}
else {
if (static_cast<bool>(([&]() -> Value { auto v21831 = ([&]() -> Value { auto v21832 = ([&]() -> Value { auto fn21834 = s->Global("tuple"); Arguments args21835; args21835.Add(Get(s->LocalAt(15), s->LocalAt(9)), false); return Call(c, fn21834, std::move(args21835)); }()); Value v21833; v21833 = s->LocalAt(14); if (!static_cast<bool>(Binary("Eq", v21832, v21833))) return Value(false); v21832 = v21833; return Value(true); }()); if (!static_cast<bool>(v21831)) return v21831; v21831 = ([&]() -> Value { auto v21836 = ([&]() -> Value { auto v21837 = s->LocalAt(17); Value v21838; v21838 = Value{}; if (!static_cast<bool>(Binary("Is", v21837, v21838))) return Value(false); v21837 = v21838; return Value(true); }()); if (static_cast<bool>(v21836)) return v21836; v21836 = ([&]() -> Value { auto v21839 = s->LocalAt(19); Value v21840; v21840 = s->LocalAt(17); if (!static_cast<bool>(Binary("GtE", v21839, v21840))) return Value(false); v21839 = v21840; return Value(true); }()); return v21836; }()); return v21831; }()))) {
(void)([&]() -> Value { auto fn21841 = Attribute(s->LocalAt(13), "append"); Arguments args21842; args21842.Add(Tuple({s->LocalAt(19), s->LocalAt(9), Get(s->LocalAt(4), Value(int64_t{0}))}), false); return Call(c, fn21841, std::move(args21842)); }());
}
}
}
for (const auto& item21843 : Iterate(([&]() -> Value { auto fn21844 = s->Global("range"); Arguments args21845; args21845.Add(([&]() -> Value { auto fn21846 = s->Global("sum"); Arguments args21847; args21847.Add(([&]() -> Value { auto comp21848 = std::make_shared<Scope>(); comp21848->globals = s->globals; comp21848->parent = s; static constexpr const char* comp21848_names[] = {"o"}; comp21848->PrepareSlots(comp21848_names); auto result21849 = List(); for (const auto& item21850 : Iterate(([&]() -> Value { auto v21851 = ([&]() -> Value { auto fn21852 = PrepareDictionaryGet(s->LocalAt(1)); Arguments args21853; args21853.Add(Value("market"), false); return CallDictionaryGet(c, fn21852, std::move(args21853)); }()); if (static_cast<bool>(v21851)) return v21851; v21851 = List({}); return v21851; }()))) { comp21848->SetAt(0, item21850); if (!static_cast<bool>(([&]() -> Value { auto v21854 = comp21848->LocalAt(0); if (!static_cast<bool>(v21854)) return v21854; v21854 = ([&]() -> Value { auto v21855 = Get(comp21848->LocalAt(0), Value(int64_t{0})); Value v21856; v21856 = Value("HIRE"); if (!static_cast<bool>(Binary("Eq", v21855, v21856))) return Value(false); v21855 = v21856; return Value(true); }()); return v21854; }()))) continue; result21849.node()->sequence.push_back(Value(int64_t{1})); } return result21849; }()), false); return Call(c, fn21846, std::move(args21847)); }()), false); return Call(c, fn21844, std::move(args21845)); }()))) {
s->SetAt(0, item21843);
(void)([&]() -> Value { auto fn21857 = Attribute(s->LocalAt(15), "append"); Arguments args21858; args21858.Add(([&]() -> Value { auto fn21859 = s->Global("_ca_spawn"); Arguments args21860; args21860.positional.reserve(2); args21860.Add(s->LocalAt(15), false); args21860.Add(s->LocalAt(3), false); return Call(c, fn21859, std::move(args21860)); }()), false); return Call(c, fn21857, std::move(args21858)); }());
}
if (static_cast<bool>(([&]() -> Value { auto v21861 = ([&]() -> Value { auto v21863 = s->LocalAt(19); return Binary("Mod", v21863, Value(int64_t{24})); }()); Value v21862; v21862 = Value(int64_t{23}); if (!static_cast<bool>(Binary("Eq", v21861, v21862))) return Value(false); v21861 = v21862; return Value(true); }()))) {
auto v21864 = List({List({([&]() -> Value { auto v21865 = s->LocalAt(8); return Binary("Sub", v21865, Value(int64_t{1})); }()), ([&]() -> Value { auto v21866 = s->LocalAt(8); return Binary("Sub", v21866, Value(int64_t{1})); }())})});
s->SetAt(15, v21864);
}
}
return s->LocalAt(13);
return {};
}
}  // namespace kagg::opponents::compiled
