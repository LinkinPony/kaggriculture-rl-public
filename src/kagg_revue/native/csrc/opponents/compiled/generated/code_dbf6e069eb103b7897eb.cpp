// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_dbf6e069eb103b7897eb(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "configuration", "observation", "st", "standard"};
s->PrepareSlots(s_names);
auto v18946 = ([&]() -> Value { auto fn18947 = s->Global("_ADV_PARENT"); Arguments args18948; args18948.positional.reserve(2); args18948.Add(s->LocalAt(2), false); args18948.Add(s->LocalAt(1), false); return Call(c, fn18947, std::move(args18948)); }());
s->SetAt(0, v18946);
try {
if (static_cast<bool>(([&]() -> Value { auto v18950 = ([&]() -> Value { auto fn18952 = s->Global("int"); Arguments args18953; args18953.Add(Get(s->LocalAt(2), Value("step")), false); return Call(c, fn18952, std::move(args18953)); }()); Value v18951; v18951 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v18950, v18951))) return Value(false); v18950 = v18951; return Value(true); }()))) {
(void)([&]() -> Value { auto fn18954 = Attribute(s->Global("_ADV_REPORT"), "update"); Arguments args18955; args18955.Keyword("adv_turns", Value(int64_t{0})); args18955.Keyword("adv_units", Value(int64_t{0})); args18955.Keyword("adv_errors", Value(int64_t{0})); return Call(c, fn18954, std::move(args18955)); }());
}
auto v18956 = ([&]() -> Value { auto v18957 = ([&]() -> Value { auto v18958 = s->LocalAt(1); Value v18959; v18959 = Value{}; if (!static_cast<bool>(Binary("Is", v18958, v18959))) return Value(false); v18958 = v18959; return Value(true); }()); if (static_cast<bool>(v18957)) return v18957; v18957 = ([&]() -> Value { auto comp18960 = std::make_shared<Scope>(); comp18960->globals = s->globals; comp18960->parent = s; static constexpr const char* comp18960_names[] = {"k", "v"}; comp18960->PrepareSlots(comp18960_names); auto result18961 = List(); for (const auto& item18962 : Iterate(List({Tuple({Value("boardSize"), Value(int64_t{10})}), Tuple({Value("turnsPerDay"), Value(int64_t{24})}), Tuple({Value("shedCapacity"), Value(int64_t{100})}), Tuple({Value("maxMarketOrdersPerTurn"), Value(int64_t{10})})}))) { auto unpack18963 = Iterate(item18962); ValidateUnpack(unpack18963, 2, false); comp18960->SetAt(0, unpack18963.at(0)); comp18960->SetAt(1, unpack18963.at(1)); if (!static_cast<bool>(([&]() -> Value { auto v18964 = ([&]() -> Value { auto fn18966 = PrepareDictionaryGet(comp18960->Captured("configuration")); Arguments args18967; args18967.positional.reserve(2); args18967.Add(comp18960->LocalAt(0), false); args18967.Add(comp18960->LocalAt(1), false); return CallDictionaryGet(c, fn18966, std::move(args18967)); }()); Value v18965; v18965 = comp18960->LocalAt(1); if (!static_cast<bool>(Binary("Eq", v18964, v18965))) return Value(false); v18964 = v18965; return Value(true); }()))) return Value(false); } return Value(true); }()); return v18957; }());
s->SetAt(4, v18956);
if (static_cast<bool>(s->LocalAt(4))) {
auto v18968 = ([&]() -> Value { auto fn18969 = s->Global("_adv_apply"); Arguments args18970; args18970.positional.reserve(2); args18970.Add(s->LocalAt(2), false); args18970.Add(s->LocalAt(0), false); return Call(c, fn18969, std::move(args18970)); }());
s->SetAt(0, v18968);
}
if (static_cast<bool>(([&]() -> Value { auto v18971 = s->LocalAt(4); if (!static_cast<bool>(v18971)) return v18971; v18971 = s->Global("_ADV_FRONT"); return v18971; }()))) {
auto v18972 = ([&]() -> Value { auto fn18973 = s->Global("_adv_frontload"); Arguments args18974; args18974.positional.reserve(2); args18974.Add(s->LocalAt(2), false); args18974.Add(s->LocalAt(0), false); return Call(c, fn18973, std::move(args18974)); }());
s->SetAt(0, v18972);
}
auto v18975 = ([&]() -> Value { auto fn18976 = PrepareDictionaryGet(s->Global("_RACE_STATE")); Arguments args18977; args18977.Add(([&]() -> Value { auto fn18978 = s->Global("int"); Arguments args18979; args18979.Add(Get(s->LocalAt(2), Value("player")), false); return Call(c, fn18978, std::move(args18979)); }()), false); return CallDictionaryGet(c, fn18976, std::move(args18977)); }());
s->SetAt(3, v18975);
if (static_cast<bool>(([&]() -> Value { auto v18980 = ([&]() -> Value { auto v18981 = s->LocalAt(3); Value v18982; v18982 = Value{}; if (!static_cast<bool>(Binary("IsNot", v18981, v18982))) return Value(false); v18981 = v18982; return Value(true); }()); if (!static_cast<bool>(v18980)) return v18980; v18980 = ([&]() -> Value { auto v18983 = ([&]() -> Value { auto fn18985 = PrepareDictionaryGet(s->LocalAt(3)); Arguments args18986; args18986.Add(Value("prev_action"), false); return CallDictionaryGet(c, fn18985, std::move(args18986)); }()); Value v18984; v18984 = Value{}; if (!static_cast<bool>(Binary("IsNot", v18983, v18984))) return Value(false); v18983 = v18984; return Value(true); }()); if (!static_cast<bool>(v18980)) return v18980; v18980 = ([&]() -> Value { auto v18987 = ([&]() -> Value { auto fn18989 = PrepareDictionaryGet(s->LocalAt(3)); Arguments args18990; args18990.Add(Value("step"), false); return CallDictionaryGet(c, fn18989, std::move(args18990)); }()); Value v18988; v18988 = ([&]() -> Value { auto fn18991 = s->Global("int"); Arguments args18992; args18992.Add(Get(s->LocalAt(2), Value("step")), false); return Call(c, fn18991, std::move(args18992)); }()); if (!static_cast<bool>(Binary("Eq", v18987, v18988))) return Value(false); v18987 = v18988; return Value(true); }()); return v18980; }()))) {
auto v18993 = s->LocalAt(0);
Put(s->LocalAt(3), Value("prev_action"), v18993);
}
} catch (const Error& error18949) {
if (Matches(error18949, s->Global("Exception"))) {
auto v18994 = s->Global("_ADV_REPORT");
auto v18995 = Value("adv_errors");
auto v18996 = Get(v18994, v18995);
Put(v18994, v18995, Inplace("Add", v18996, Value(int64_t{1})));
}
else { throw; }
}
(void)([&]() -> Value { auto fn18997 = Attribute(s->Global("_ADV_REPORT"), "update"); Arguments args18998; args18998.Add(([&]() -> Value { auto fn18999 = s->Global("getattr"); Arguments args19000; args19000.positional.reserve(3); args19000.Add(s->Global("_ADV_PARENT"), false); args19000.Add(Value("telemetry"), false); args19000.Add(([&]() -> Value { auto dict19001 = Dict(); return dict19001; }()), false); return Call(c, fn18999, std::move(args19000)); }()), false); return Call(c, fn18997, std::move(args18998)); }());
return s->LocalAt(0);
return {};
}
}  // namespace kagg::opponents::compiled
