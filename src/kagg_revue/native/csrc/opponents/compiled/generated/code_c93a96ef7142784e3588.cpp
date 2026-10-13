// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_c93a96ef7142784e3588(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"a", "c", "demand", "key", "native", "o", "obs", "player", "route", "step", "t"};
s->PrepareSlots(s_names);
auto v9945 = ([&]() -> Value { auto fn9946 = s->Global("int"); Arguments args9947; args9947.Add(Get(s->LocalAt(6), Value("step")), false); return Call(c, fn9946, std::move(args9947)); }());
s->SetAt(9, v9945);
auto v9948 = ([&]() -> Value { auto fn9949 = s->Global("int"); Arguments args9950; args9950.Add(Get(s->LocalAt(6), Value("player")), false); return Call(c, fn9949, std::move(args9950)); }());
s->SetAt(7, v9948);
auto v9951 = Get(Attribute(Attribute(s->Global("_IMPL"), "chassis"), "players"), s->LocalAt(7));
s->SetAt(4, v9951);
auto v9952 = Get(s->LocalAt(4), Value("route"));
s->SetAt(8, v9952);
auto v9953 = Tuple({s->LocalAt(8), s->LocalAt(9)});
s->SetAt(3, v9953);
if (static_cast<bool>(([&]() -> Value { auto v9954 = s->LocalAt(3); Value v9955; v9955 = s->Global("_R95_RESERVES"); if (!static_cast<bool>(Binary("NotIn", v9954, v9955))) return Value(false); v9954 = v9955; return Value(true); }()))) {
auto v9956 = Value(int64_t{6});
s->SetAt(2, v9956);
for (const auto& item9957 : Iterate(([&]() -> Value { auto fn9958 = s->Global("range"); Arguments args9959; args9959.positional.reserve(2); args9959.Add(([&]() -> Value { auto v9960 = s->LocalAt(9); return Binary("Add", v9960, Value(int64_t{1})); }()), false); args9959.Add(([&]() -> Value { auto fn9961 = s->Global("min"); Arguments args9962; args9962.positional.reserve(2); args9962.Add(Value(int64_t{719}), false); args9962.Add(([&]() -> Value { auto v9963 = s->LocalAt(9); return Binary("Add", v9963, Value(int64_t{49})); }()), false); return Call(c, fn9961, std::move(args9962)); }()), false); return Call(c, fn9958, std::move(args9959)); }()))) {
s->SetAt(10, item9957);
auto v9964 = Get(Get(Attribute(Attribute(s->Global("_IMPL"), "chassis"), "routes"), (static_cast<bool>(([&]() -> Value { auto v9965 = s->LocalAt(10); Value v9966; v9966 = Value(int64_t{648}); if (!static_cast<bool>(Binary("GtE", v9965, v9966))) return Value(false); v9965 = v9966; return Value(true); }())) ? Value(int64_t{2}) : s->LocalAt(8))), s->LocalAt(10));
s->SetAt(0, v9964);
for (const auto& item9967 : Iterate(([&]() -> Value { Arguments args9968; args9968.Add(([&]() -> Value { auto v9969 = ([&]() -> Value { auto fn9970 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args9971; args9971.Add(Value("farmer"), false); return CallDictionaryGet(c, fn9970, std::move(args9971)); }()); if (static_cast<bool>(v9969)) return v9969; v9969 = List({Value("PASS")}); return v9969; }()), false); args9968.Add(([&]() -> Value { auto v9972 = ([&]() -> Value { auto fn9973 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args9974; args9974.Add(Value("hands"), false); return CallDictionaryGet(c, fn9973, std::move(args9974)); }()); if (static_cast<bool>(v9972)) return v9972; v9972 = List({}); return v9972; }()), true); return List(std::move(args9968.positional)); }()))) {
s->SetAt(1, item9967);
if (static_cast<bool>(([&]() -> Value { auto v9975 = Slice(s->LocalAt(1), Value{}, Value(int64_t{2}), Value{}); Value v9976; v9976 = List({Value("PICKUP"), Value("WHEAT")}); if (!static_cast<bool>(Binary("Eq", v9975, v9976))) return Value(false); v9975 = v9976; return Value(true); }()))) {
auto v9977 = s->LocalAt(2);
s->SetAt(2, Inplace("Add", v9977, ([&]() -> Value { auto fn9978 = s->Global("max"); Arguments args9979; args9979.positional.reserve(2); args9979.Add(Value(int64_t{0}), false); args9979.Add((static_cast<bool>(([&]() -> Value { auto v9980 = ([&]() -> Value { auto fn9982 = s->Global("len"); Arguments args9983; args9983.Add(s->LocalAt(1), false); return Call(c, fn9982, std::move(args9983)); }()); Value v9981; v9981 = Value(int64_t{2}); if (!static_cast<bool>(Binary("Gt", v9980, v9981))) return Value(false); v9980 = v9981; return Value(true); }())) ? ([&]() -> Value { auto fn9984 = s->Global("int"); Arguments args9985; args9985.Add(Get(s->LocalAt(1), Value(int64_t{2})), false); return Call(c, fn9984, std::move(args9985)); }()) : Value(int64_t{1})), false); return Call(c, fn9978, std::move(args9979)); }())));
}
}
for (const auto& item9986 : Iterate(([&]() -> Value { auto fn9987 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args9988; args9988.positional.reserve(2); args9988.Add(Value("market"), false); args9988.Add(List({}), false); return CallDictionaryGet(c, fn9987, std::move(args9988)); }()))) {
s->SetAt(5, item9986);
if (static_cast<bool>(([&]() -> Value { auto v9989 = ([&]() -> Value { auto v9990 = ([&]() -> Value { auto fn9992 = s->Global("len"); Arguments args9993; args9993.Add(s->LocalAt(5), false); return Call(c, fn9992, std::move(args9993)); }()); Value v9991; v9991 = Value(int64_t{2}); if (!static_cast<bool>(Binary("Gt", v9990, v9991))) return Value(false); v9990 = v9991; return Value(true); }()); if (!static_cast<bool>(v9989)) return v9989; v9989 = ([&]() -> Value { auto v9994 = Slice(s->LocalAt(5), Value{}, Value(int64_t{2}), Value{}); Value v9995; v9995 = List({Value("SELL"), Value("WHEAT")}); if (!static_cast<bool>(Binary("Eq", v9994, v9995))) return Value(false); v9994 = v9995; return Value(true); }()); return v9989; }()))) {
auto v9996 = s->LocalAt(2);
s->SetAt(2, Inplace("Add", v9996, ([&]() -> Value { auto fn9997 = s->Global("max"); Arguments args9998; args9998.positional.reserve(2); args9998.Add(Value(int64_t{0}), false); args9998.Add(([&]() -> Value { auto fn9999 = s->Global("int"); Arguments args10000; args10000.Add(Get(s->LocalAt(5), Value(int64_t{2})), false); return Call(c, fn9999, std::move(args10000)); }()), false); return Call(c, fn9997, std::move(args9998)); }())));
}
}
}
auto v10001 = s->LocalAt(2);
Put(s->Global("_R95_RESERVES"), s->LocalAt(3), v10001);
}
auto v10002 = Get(s->Global("_R95_RESERVES"), s->LocalAt(3));
s->SetAt(2, v10002);
if (static_cast<bool>(([&]() -> Value { auto v10003 = ([&]() -> Value { auto fn10005 = Attribute(Get(Get(s->LocalAt(6), Value("town")), Value("unlocked_shops")), "count"); Arguments args10006; args10006.Add(Value("YARN_STORE"), false); return Call(c, fn10005, std::move(args10006)); }()); Value v10004; v10004 = Value(int64_t{2}); if (!static_cast<bool>(Binary("GtE", v10003, v10004))) return Value(false); v10003 = v10004; return Value(true); }()))) {
auto v10007 = s->LocalAt(2);
s->SetAt(2, Inplace("Add", v10007, ([&]() -> Value { auto v10008 = Value(int64_t{6}); return Binary("Mult", v10008, ([&]() -> Value { auto fn10009 = s->Global("len"); Arguments args10010; args10010.Add(([&]() -> Value { auto comp10011 = std::make_shared<Scope>(); comp10011->globals = s->globals; comp10011->parent = s; static constexpr const char* comp10011_names[] = {"t"}; comp10011->PrepareSlots(comp10011_names); auto result10012 = List(); for (const auto& item10013 : Iterate(([&]() -> Value { auto fn10014 = s->Global("range"); Arguments args10015; args10015.positional.reserve(2); args10015.Add(([&]() -> Value { auto v10016 = s->LocalAt(9); return Binary("Add", v10016, Value(int64_t{1})); }()), false); args10015.Add(([&]() -> Value { auto v10017 = s->LocalAt(9); return Binary("Add", v10017, Value(int64_t{49})); }()), false); return Call(c, fn10014, std::move(args10015)); }()))) { comp10011->SetAt(0, item10013); if (!static_cast<bool>(([&]() -> Value { auto v10018 = ([&]() -> Value { auto v10020 = comp10011->LocalAt(0); return Binary("FloorDiv", v10020, Value(int64_t{24})); }()); Value v10019; v10019 = Value(int64_t{12}); if (!static_cast<bool>(Binary("GtE", v10018, v10019))) return Value(false); v10018 = v10019; return Value(true); }()))) continue; result10012.node()->sequence.push_back(([&]() -> Value { auto v10021 = comp10011->LocalAt(0); return Binary("FloorDiv", v10021, Value(int64_t{24})); }())); } return Set(result10012.node()->sequence); }()), false); return Call(c, fn10009, std::move(args10010)); }())); }())));
}
return s->LocalAt(2);
return {};
}
}  // namespace kagg::opponents::compiled
