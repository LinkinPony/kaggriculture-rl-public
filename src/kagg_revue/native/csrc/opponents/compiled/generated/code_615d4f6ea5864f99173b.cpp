// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_615d4f6ea5864f99173b(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "actor", "available", "blocked", "c", "changed", "commands", "demand", "farm", "kept", "obs", "pos", "private", "state", "valid"};
s->PrepareSlots(s_names);
auto v10839 = ([&]() -> Value { Arguments args10840; args10840.Add(([&]() -> Value { auto v10841 = ([&]() -> Value { auto fn10842 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args10843; args10843.Add(Value("farmer"), false); return CallDictionaryGet(c, fn10842, std::move(args10843)); }()); if (static_cast<bool>(v10841)) return v10841; v10841 = List({Value("PASS")}); return v10841; }()), false); args10840.Add(([&]() -> Value { auto v10844 = ([&]() -> Value { auto fn10845 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args10846; args10846.Add(Value("hands"), false); return CallDictionaryGet(c, fn10845, std::move(args10846)); }()); if (static_cast<bool>(v10844)) return v10844; v10844 = List({}); return v10844; }()), true); return List(std::move(args10840.positional)); }());
s->SetAt(6, v10839);
auto v10847 = ([&]() -> Value { auto dict10848 = Dict(); return dict10848; }());
s->SetAt(7, v10847);
for (const auto& item10849 : Iterate(s->LocalAt(6))) {
s->SetAt(4, item10849);
if (static_cast<bool>(([&]() -> Value { auto v10850 = ([&]() -> Value { auto v10851 = ([&]() -> Value { auto fn10853 = s->Global("len"); Arguments args10854; args10854.Add(s->LocalAt(4), false); return Call(c, fn10853, std::move(args10854)); }()); Value v10852; v10852 = Value(int64_t{1}); if (!static_cast<bool>(Binary("Gt", v10851, v10852))) return Value(false); v10851 = v10852; return Value(true); }()); if (!static_cast<bool>(v10850)) return v10850; v10850 = ([&]() -> Value { auto v10855 = Get(s->LocalAt(4), Value(int64_t{0})); Value v10856; v10856 = Value("PLANT"); if (!static_cast<bool>(Binary("Eq", v10855, v10856))) return Value(false); v10855 = v10856; return Value(true); }()); return v10850; }()))) {
auto v10857 = ([&]() -> Value { auto v10858 = ([&]() -> Value { auto fn10859 = PrepareDictionaryGet(s->LocalAt(7)); Arguments args10860; args10860.positional.reserve(2); args10860.Add(Get(s->LocalAt(4), Value(int64_t{1})), false); args10860.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn10859, std::move(args10860)); }()); return Binary("Add", v10858, Value(int64_t{1})); }());
Put(s->LocalAt(7), Get(s->LocalAt(4), Value(int64_t{1})), v10857);
}
}
if (static_cast<bool>(Unary("Not", s->LocalAt(7)))) {
return s->LocalAt(0);
}
auto v10861 = Get(Get(s->LocalAt(10), Value("private")), Value("seeds"));
s->SetAt(2, v10861);
auto v10862 = ([&]() -> Value { auto comp10863 = std::make_shared<Scope>(); comp10863->globals = s->globals; comp10863->parent = s; static constexpr const char* comp10863_names[] = {"n", "p"}; comp10863->PrepareSlots(comp10863_names); auto result10864 = List(); for (const auto& item10865 : Iterate(([&]() -> Value { auto fn10866 = Attribute(s->LocalAt(7), "items"); Arguments args10867; return Call(c, fn10866, std::move(args10867)); }()))) { auto unpack10868 = Iterate(item10865); ValidateUnpack(unpack10868, 2, false); comp10863->SetAt(1, unpack10868.at(0)); comp10863->SetAt(0, unpack10868.at(1)); if (!static_cast<bool>(([&]() -> Value { auto v10869 = comp10863->LocalAt(0); Value v10870; v10870 = ([&]() -> Value { auto fn10871 = PrepareDictionaryGet(comp10863->Captured("available")); Arguments args10872; args10872.positional.reserve(2); args10872.Add(comp10863->LocalAt(1), false); args10872.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn10871, std::move(args10872)); }()); if (!static_cast<bool>(Binary("Gt", v10869, v10870))) return Value(false); v10869 = v10870; return Value(true); }()))) continue; result10864.node()->sequence.push_back(comp10863->LocalAt(1)); } return Set(result10864.node()->sequence); }());
s->SetAt(3, v10862);
auto v10873 = ([&]() -> Value { auto fn10874 = Get(s->Global("_PLANNER_NS"), Value("_clone_state")); Arguments args10875; args10875.positional.reserve(2); args10875.Add(Get(Get(s->LocalAt(10), Value("farms")), Get(s->LocalAt(10), Value("player"))), false); args10875.Add(Get(s->LocalAt(10), Value("private")), false); return Call(c, fn10874, std::move(args10875)); }());
auto unpack10876 = Iterate(v10873);
ValidateUnpack(unpack10876, 2, false);
s->SetAt(8, unpack10876.at(0));
s->SetAt(12, unpack10876.at(1));
auto v10877 = Value(false);
s->SetAt(5, v10877);
auto v10878 = List({});
s->SetAt(9, v10878);
for (const auto& item10879 : Iterate(([&]() -> Value { auto fn10880 = s->Global("enumerate"); Arguments args10881; args10881.Add(s->LocalAt(6), false); return Call(c, fn10880, std::move(args10881)); }()))) {
auto unpack10882 = Iterate(item10879);
ValidateUnpack(unpack10882, 2, false);
s->SetAt(1, unpack10882.at(0));
s->SetAt(4, unpack10882.at(1));
if (static_cast<bool>(([&]() -> Value { auto v10883 = ([&]() -> Value { auto v10884 = ([&]() -> Value { auto fn10886 = s->Global("len"); Arguments args10887; args10887.Add(s->LocalAt(4), false); return Call(c, fn10886, std::move(args10887)); }()); Value v10885; v10885 = Value(int64_t{1}); if (!static_cast<bool>(Binary("Gt", v10884, v10885))) return Value(false); v10884 = v10885; return Value(true); }()); if (!static_cast<bool>(v10883)) return v10883; v10883 = ([&]() -> Value { auto v10888 = Get(s->LocalAt(4), Value(int64_t{0})); Value v10889; v10889 = Value("PLANT"); if (!static_cast<bool>(Binary("Eq", v10888, v10889))) return Value(false); v10888 = v10889; return Value(true); }()); return v10883; }()))) {
auto v10890 = (static_cast<bool>(([&]() -> Value { auto v10891 = s->LocalAt(1); Value v10892; v10892 = ([&]() -> Value { auto fn10893 = s->Global("len"); Arguments args10894; args10894.Add(Get(s->LocalAt(12), Value("inventories")), false); return Call(c, fn10893, std::move(args10894)); }()); if (!static_cast<bool>(Binary("GtE", v10891, v10892))) return Value(false); v10891 = v10892; return Value(true); }())) ? Value{} : (static_cast<bool>(([&]() -> Value { auto v10895 = s->LocalAt(1); Value v10896; v10896 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v10895, v10896))) return Value(false); v10895 = v10896; return Value(true); }())) ? Get(s->LocalAt(8), Value("farmer")) : Get(Get(s->LocalAt(8), Value("hands")), ([&]() -> Value { auto v10897 = s->LocalAt(1); return Binary("Sub", v10897, Value(int64_t{1})); }()))));
s->SetAt(11, v10890);
auto v10898 = ([&]() -> Value { auto v10899 = ([&]() -> Value { auto v10900 = s->LocalAt(11); Value v10901; v10901 = Value{}; if (!static_cast<bool>(Binary("IsNot", v10900, v10901))) return Value(false); v10900 = v10901; return Value(true); }()); if (!static_cast<bool>(v10899)) return v10899; v10899 = ([&]() -> Value { auto v10902 = Get(Get(Get(s->LocalAt(8), Value("tiles")), Get(s->LocalAt(11), Value(int64_t{1}))), Get(s->LocalAt(11), Value(int64_t{0}))); Value v10903; v10903 = Value{}; if (!static_cast<bool>(Binary("Is", v10902, v10903))) return Value(false); v10902 = v10903; return Value(true); }()); if (!static_cast<bool>(v10899)) return v10899; v10899 = ([&]() -> Value { auto v10904 = ([&]() -> Value { auto fn10906 = PrepareDictionaryGet(Get(s->LocalAt(12), Value("seeds"))); Arguments args10907; args10907.positional.reserve(2); args10907.Add(Get(s->LocalAt(4), Value(int64_t{1})), false); args10907.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn10906, std::move(args10907)); }()); Value v10905; v10905 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v10904, v10905))) return Value(false); v10904 = v10905; return Value(true); }()); return v10899; }());
s->SetAt(14, v10898);
if (static_cast<bool>(Unary("Not", s->LocalAt(14)))) {
auto v10908 = List({Value("PASS")});
Put(s->LocalAt(6), s->LocalAt(1), v10908);
auto v10909 = Value(true);
s->SetAt(5, v10909);
auto v10910 = s->Global("_R124_REPORT");
auto v10911 = Value("opening_atomic_dropped");
auto v10912 = Get(v10910, v10911);
Put(v10910, v10911, Inplace("Add", v10912, Value(int64_t{1})));
}
else {
if (static_cast<bool>(([&]() -> Value { auto v10913 = Get(s->LocalAt(4), Value(int64_t{1})); Value v10914; v10914 = s->LocalAt(3); if (!static_cast<bool>(Binary("In", v10913, v10914))) return Value(false); v10913 = v10914; return Value(true); }()))) {
(void)([&]() -> Value { auto fn10915 = Attribute(s->LocalAt(9), "append"); Arguments args10916; args10916.Add(([&]() -> Value { auto fn10917 = s->Global("dict"); Arguments args10918; args10918.Keyword("xy", ([&]() -> Value { auto fn10919 = s->Global("list"); Arguments args10920; args10920.Add(s->LocalAt(11), false); return Call(c, fn10919, std::move(args10920)); }())); args10918.Keyword("crop", Get(s->LocalAt(4), Value(int64_t{1}))); args10918.Keyword("birth", Value(int64_t{0})); return Call(c, fn10917, std::move(args10918)); }()), false); return Call(c, fn10915, std::move(args10916)); }());
auto v10921 = s->Global("_R124_REPORT");
auto v10922 = Value("opening_atomic_rescued_requests");
auto v10923 = Get(v10921, v10922);
Put(v10921, v10922, Inplace("Add", v10923, Value(int64_t{1})));
}
}
}
if (static_cast<bool>(([&]() -> Value { auto v10924 = s->LocalAt(1); Value v10925; v10925 = ([&]() -> Value { auto fn10926 = s->Global("len"); Arguments args10927; args10927.Add(Get(s->LocalAt(12), Value("inventories")), false); return Call(c, fn10926, std::move(args10927)); }()); if (!static_cast<bool>(Binary("Lt", v10924, v10925))) return Value(false); v10924 = v10925; return Value(true); }()))) {
(void)([&]() -> Value { auto fn10928 = Get(s->Global("_PLANNER_NS"), Value("_apply_unit_action")); Arguments args10929; args10929.positional.reserve(8); args10929.Add(s->LocalAt(8), false); args10929.Add(s->LocalAt(12), false); args10929.Add(s->LocalAt(1), false); args10929.Add(Get(s->LocalAt(6), s->LocalAt(1)), false); args10929.Add(Value(int64_t{10}), false); args10929.Add(Value(int64_t{0}), false); args10929.Add(Value(int64_t{24}), false); args10929.Add(Value(int64_t{100}), false); return Call(c, fn10928, std::move(args10929)); }());
}
}
if (static_cast<bool>(s->LocalAt(9))) {
auto v10930 = s->LocalAt(9);
Put(s->LocalAt(13), Value("pending_plants"), v10930);
}
if (static_cast<bool>(s->LocalAt(5))) {
auto v10931 = ([&]() -> Value { auto fn10932 = s->Global("dict"); Arguments args10933; args10933.Add(s->LocalAt(0), false); args10933.Keyword("farmer", Get(s->LocalAt(6), Value(int64_t{0}))); args10933.Keyword("hands", Slice(s->LocalAt(6), Value(int64_t{1}), Value{}, Value{})); return Call(c, fn10932, std::move(args10933)); }());
s->SetAt(0, v10931);
}
return s->LocalAt(0);
return {};
}
}  // namespace kagg::opponents::compiled
