// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_31b01b545fe1a3ca23e9(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "actor", "bonus", "changed", "command", "commands", "day", "expected", "farm", "item", "native", "obs", "player", "positions", "prices", "result", "step", "tape", "tile"};
s->PrepareSlots(s_names);
auto v14854 = ([&]() -> Value { auto fn14855 = s->Global("int"); Arguments args14856; args14856.Add(Get(s->LocalAt(11), Value("step")), false); return Call(c, fn14855, std::move(args14856)); }());
s->SetAt(16, v14854);
auto v14857 = ([&]() -> Value { auto v14858 = s->LocalAt(16); return Binary("FloorDiv", v14858, Value(int64_t{24})); }());
s->SetAt(6, v14857);
if (static_cast<bool>(([&]() -> Value { auto v14859 = Unary("Not", ([&]() -> Value { auto v14860 = Value(int64_t{10}); Value v14861; v14861 = s->LocalAt(6); if (!static_cast<bool>(Binary("LtE", v14860, v14861))) return Value(false); v14860 = v14861; v14861 = Value(int64_t{28}); if (!static_cast<bool>(Binary("LtE", v14860, v14861))) return Value(false); v14860 = v14861; return Value(true); }())); if (static_cast<bool>(v14859)) return v14859; v14859 = ([&]() -> Value { auto v14862 = ([&]() -> Value { auto v14864 = s->LocalAt(16); return Binary("Mod", v14864, Value(int64_t{24})); }()); Value v14863; v14863 = Value(int64_t{21}); if (!static_cast<bool>(Binary("Gt", v14862, v14863))) return Value(false); v14862 = v14863; return Value(true); }()); return v14859; }()))) {
return s->LocalAt(0);
}
auto v14865 = ([&]() -> Value { auto fn14866 = s->Global("int"); Arguments args14867; args14867.Add(Get(s->LocalAt(11), Value("player")), false); return Call(c, fn14866, std::move(args14867)); }());
s->SetAt(12, v14865);
auto v14868 = Get(Attribute(Attribute(s->Global("_IMPL"), "chassis"), "players"), s->LocalAt(12));
s->SetAt(10, v14868);
auto v14869 = ([&]() -> Value { auto fn14870 = s->Global("_v219_native_day"); Arguments args14871; args14871.positional.reserve(2); args14871.Add(s->LocalAt(10), false); args14871.Add(s->LocalAt(6), false); return Call(c, fn14870, std::move(args14871)); }());
s->SetAt(17, v14869);
auto v14872 = ([&]() -> Value { auto fn14873 = s->Global("max"); Arguments args14874; args14874.Add(([&]() -> Value { auto comp14875 = std::make_shared<Scope>(); comp14875->globals = s->globals; comp14875->parent = s; static constexpr const char* comp14875_names[] = {"a"}; comp14875->PrepareSlots(comp14875_names); auto result14876 = List(); for (const auto& item14877 : Iterate(s->LocalAt(17))) { comp14875->SetAt(0, item14877); result14876.node()->sequence.push_back(([&]() -> Value { auto fn14878 = comp14875->Global("len"); Arguments args14879; args14879.Add(([&]() -> Value { auto fn14880 = PrepareDictionaryGet(comp14875->LocalAt(0)); Arguments args14881; args14881.positional.reserve(2); args14881.Add(Value("hands"), false); args14881.Add(List({}), false); return CallDictionaryGet(c, fn14880, std::move(args14881)); }()), false); return Call(c, fn14878, std::move(args14879)); }())); } return result14876; }()), false); return Call(c, fn14873, std::move(args14874)); }());
s->SetAt(7, v14872);
auto v14882 = Get(Get(s->LocalAt(11), Value("farms")), s->LocalAt(12));
s->SetAt(8, v14882);
auto v14883 = ([&]() -> Value { Arguments args14884; args14884.Add(Get(s->LocalAt(8), Value("farmer")), false); args14884.Add(Get(s->LocalAt(8), Value("hands")), true); return List(std::move(args14884.positional)); }());
s->SetAt(13, v14883);
auto v14885 = ([&]() -> Value { Arguments args14886; args14886.Add(([&]() -> Value { auto v14887 = ([&]() -> Value { auto fn14888 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args14889; args14889.Add(Value("farmer"), false); return CallDictionaryGet(c, fn14888, std::move(args14889)); }()); if (static_cast<bool>(v14887)) return v14887; v14887 = List({Value("PASS")}); return v14887; }()), false); args14886.Add(([&]() -> Value { auto v14890 = ([&]() -> Value { auto fn14891 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args14892; args14892.Add(Value("hands"), false); return CallDictionaryGet(c, fn14891, std::move(args14892)); }()); if (static_cast<bool>(v14890)) return v14890; v14890 = List({}); return v14890; }()), true); return List(std::move(args14886.positional)); }());
s->SetAt(5, v14885);
auto v14893 = Get(Get(s->LocalAt(11), Value("market")), Value("prices"));
s->SetAt(14, v14893);
auto v14894 = Value(false);
s->SetAt(3, v14894);
for (const auto& item14895 : Iterate(([&]() -> Value { auto fn14896 = s->Global("enumerate"); Arguments args14897; args14897.Add(Slice(s->LocalAt(5), Value{}, ([&]() -> Value { auto v14898 = s->LocalAt(7); return Binary("Add", v14898, Value(int64_t{1})); }()), Value{}), false); return Call(c, fn14896, std::move(args14897)); }()))) {
auto unpack14899 = Iterate(item14895);
ValidateUnpack(unpack14899, 2, false);
s->SetAt(1, unpack14899.at(0));
s->SetAt(4, unpack14899.at(1));
if (static_cast<bool>(([&]() -> Value { auto v14900 = ([&]() -> Value { auto v14901 = s->LocalAt(4); Value v14902; v14902 = List({Value("FEED")}); if (!static_cast<bool>(Binary("NotEq", v14901, v14902))) return Value(false); v14901 = v14902; return Value(true); }()); if (static_cast<bool>(v14900)) return v14900; v14900 = ([&]() -> Value { auto v14903 = s->LocalAt(1); Value v14904; v14904 = ([&]() -> Value { auto fn14905 = s->Global("len"); Arguments args14906; args14906.Add(s->LocalAt(13), false); return Call(c, fn14905, std::move(args14906)); }()); if (!static_cast<bool>(Binary("GtE", v14903, v14904))) return Value(false); v14903 = v14904; return Value(true); }()); return v14900; }()))) {
continue;
}
auto v14907 = ([&]() -> Value { auto fn14908 = s->Global("_tile_at"); Arguments args14909; args14909.positional.reserve(2); args14909.Add(Get(s->LocalAt(8), Value("tiles")), false); args14909.Add(Get(s->LocalAt(13), s->LocalAt(1)), false); return Call(c, fn14908, std::move(args14909)); }());
s->SetAt(18, v14907);
if (static_cast<bool>(([&]() -> Value { auto v14910 = Unary("Not", ([&]() -> Value { auto fn14911 = s->Global("isinstance"); Arguments args14912; args14912.positional.reserve(2); args14912.Add(s->LocalAt(18), false); args14912.Add(s->Global("dict"), false); return Call(c, fn14911, std::move(args14912)); }())); if (static_cast<bool>(v14910)) return v14910; v14910 = ([&]() -> Value { auto v14913 = ([&]() -> Value { auto fn14915 = PrepareDictionaryGet(s->LocalAt(18)); Arguments args14916; args14916.Add(Value("animal"), false); return CallDictionaryGet(c, fn14915, std::move(args14916)); }()); Value v14914; v14914 = Tuple({Value("GOOSE"), Value("COW"), Value("SHEEP")}); if (!static_cast<bool>(Binary("NotIn", v14913, v14914))) return Value(false); v14913 = v14914; return Value(true); }()); return v14910; }()))) {
continue;
}
if (static_cast<bool>(([&]() -> Value { auto v14917 = ([&]() -> Value { auto fn14918 = PrepareDictionaryGet(s->LocalAt(18)); Arguments args14919; args14919.Add(Value("fed_today"), false); return CallDictionaryGet(c, fn14918, std::move(args14919)); }()); if (static_cast<bool>(v14917)) return v14917; v14917 = ([&]() -> Value { auto v14920 = ([&]() -> Value { auto fn14922 = s->Global("int"); Arguments args14923; args14923.Add(([&]() -> Value { auto fn14924 = PrepareDictionaryGet(s->LocalAt(18)); Arguments args14925; args14925.positional.reserve(2); args14925.Add(Value("consecutive_unfed"), false); args14925.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn14924, std::move(args14925)); }()), false); return Call(c, fn14922, std::move(args14923)); }()); Value v14921; v14921 = Value(int64_t{0}); if (!static_cast<bool>(Binary("NotEq", v14920, v14921))) return Value(false); v14920 = v14921; return Value(true); }()); return v14917; }()))) {
continue;
}
if (static_cast<bool>(([&]() -> Value { auto v14926 = ([&]() -> Value { auto fn14928 = s->Global("int"); Arguments args14929; args14929.Add(([&]() -> Value { auto fn14930 = PrepareDictionaryGet(Get(Get(Get(s->LocalAt(11), Value("private")), Value("inventories")), s->LocalAt(1))); Arguments args14931; args14931.positional.reserve(2); args14931.Add(Value("WHEAT"), false); args14931.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn14930, std::move(args14931)); }()), false); return Call(c, fn14928, std::move(args14929)); }()); Value v14927; v14927 = Value(int64_t{0}); if (!static_cast<bool>(Binary("LtE", v14926, v14927))) return Value(false); v14926 = v14927; return Value(true); }()))) {
continue;
}
auto v14932 = Get(([&]() -> Value { auto dict14933 = Dict(); auto key14934 = Value("GOOSE"); Put(dict14933, key14934, Value("EGG")); auto key14935 = Value("COW"); Put(dict14933, key14935, Value("MILK")); auto key14936 = Value("SHEEP"); Put(dict14933, key14936, Value("WOOL")); return dict14933; }()), Get(s->LocalAt(18), Value("animal")));
s->SetAt(9, v14932);
auto v14937 = ([&]() -> Value { auto v14938 = Value(int64_t{1}); return Binary("Add", v14938, ([&]() -> Value { auto fn14939 = s->Global("max"); Arguments args14940; args14940.positional.reserve(2); args14940.Add(Value(int64_t{0}), false); args14940.Add(([&]() -> Value { auto fn14941 = s->Global("int"); Arguments args14942; args14942.Add(([&]() -> Value { auto fn14943 = PrepareDictionaryGet(s->LocalAt(18)); Arguments args14944; args14944.positional.reserve(2); args14944.Add(Value("pending_care_bonus"), false); args14944.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn14943, std::move(args14944)); }()), false); return Call(c, fn14941, std::move(args14942)); }()), false); return Call(c, fn14939, std::move(args14940)); }())); }());
s->SetAt(2, v14937);
if (static_cast<bool>(([&]() -> Value { auto v14945 = ([&]() -> Value { auto v14947 = ([&]() -> Value { auto v14948 = s->LocalAt(2); return Binary("Mult", v14948, ([&]() -> Value { auto v14949 = ([&]() -> Value { auto fn14950 = s->Global("float"); Arguments args14951; args14951.Add(Get(s->LocalAt(14), s->LocalAt(9)), false); return Call(c, fn14950, std::move(args14951)); }()); return Binary("Add", v14949, Value(int64_t{5})); }())); }()); return Binary("Mult", v14947, Value(1.25)); }()); Value v14946; v14946 = ([&]() -> Value { auto fn14952 = s->Global("float"); Arguments args14953; args14953.Add(Get(s->LocalAt(14), Value("WHEAT")), false); return Call(c, fn14952, std::move(args14953)); }()); if (!static_cast<bool>(Binary("GtE", v14945, v14946))) return Value(false); v14945 = v14946; return Value(true); }()))) {
continue;
}
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto fn14954 = s->Global("_r86_next_feed"); Arguments args14955; args14955.positional.reserve(2); args14955.Add(s->LocalAt(11), false); args14955.Add(Get(s->LocalAt(13), s->LocalAt(1)), false); return Call(c, fn14954, std::move(args14955)); }())))) {
continue;
}
auto v14956 = List({Value("PASS")});
Put(s->LocalAt(5), s->LocalAt(1), v14956);
auto v14957 = Value(true);
s->SetAt(3, v14957);
auto v14958 = s->Global("_R85_REPORT");
auto v14959 = Value("feed_skips");
auto v14960 = Get(v14958, v14959);
Put(v14958, v14959, Inplace("Add", v14960, Value(int64_t{1})));
}
if (static_cast<bool>(Unary("Not", s->LocalAt(3)))) {
return s->LocalAt(0);
}
auto v14961 = ([&]() -> Value { auto fn14962 = Attribute(s->Global("copy"), "deepcopy"); Arguments args14963; args14963.Add(s->LocalAt(0), false); return Call(c, fn14962, std::move(args14963)); }());
s->SetAt(15, v14961);
auto v14964 = Tuple({Get(s->LocalAt(5), Value(int64_t{0})), Slice(s->LocalAt(5), Value(int64_t{1}), Value{}, Value{})});
auto unpack14965 = Iterate(v14964);
ValidateUnpack(unpack14965, 2, false);
Put(s->LocalAt(15), Value("farmer"), unpack14965.at(0));
Put(s->LocalAt(15), Value("hands"), unpack14965.at(1));
return s->LocalAt(15);
return {};
}
}  // namespace kagg::opponents::compiled
