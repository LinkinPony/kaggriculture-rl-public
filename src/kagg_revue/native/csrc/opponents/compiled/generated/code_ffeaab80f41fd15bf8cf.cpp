// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_ffeaab80f41fd15bf8cf(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "configuration", "day", "observation", "seat", "st", "step"};
s->PrepareSlots(s_names);
auto v24949 = ([&]() -> Value { auto fn24950 = s->Global("_HD2_PARENT"); Arguments args24951; args24951.positional.reserve(2); args24951.Add(s->LocalAt(3), false); args24951.Add(s->LocalAt(1), false); return Call(c, fn24950, std::move(args24951)); }());
s->SetAt(0, v24949);
try {
auto v24953 = ([&]() -> Value { auto fn24954 = s->Global("int"); Arguments args24955; args24955.Add(Get(s->LocalAt(3), Value("player")), false); return Call(c, fn24954, std::move(args24955)); }());
s->SetAt(4, v24953);
auto v24956 = ([&]() -> Value { auto fn24957 = s->Global("int"); Arguments args24958; args24958.Add(Get(s->LocalAt(3), Value("step")), false); return Call(c, fn24957, std::move(args24958)); }());
s->SetAt(6, v24956);
auto v24959 = ([&]() -> Value { auto fn24960 = PrepareDictionaryGet(s->Global("_HD2_STATE")); Arguments args24961; args24961.Add(s->LocalAt(4), false); return CallDictionaryGet(c, fn24960, std::move(args24961)); }());
s->SetAt(5, v24959);
if (static_cast<bool>(([&]() -> Value { auto v24962 = ([&]() -> Value { auto v24963 = s->LocalAt(5); Value v24964; v24964 = Value{}; if (!static_cast<bool>(Binary("Is", v24963, v24964))) return Value(false); v24963 = v24964; return Value(true); }()); if (static_cast<bool>(v24962)) return v24962; v24962 = ([&]() -> Value { auto v24965 = s->LocalAt(6); Value v24966; v24966 = Get(s->LocalAt(5), Value("step")); if (!static_cast<bool>(Binary("LtE", v24965, v24966))) return Value(false); v24965 = v24966; return Value(true); }()); return v24962; }()))) {
auto v24967 = ([&]() -> Value { auto dict24968 = Dict(); auto key24969 = Value("step"); Put(dict24968, key24969, Unary("USub", Value(int64_t{1}))); auto key24970 = Value("inv"); Put(dict24968, key24970, ([&]() -> Value { auto dict24971 = Dict(); return dict24971; }())); auto key24972 = Value("decided"); Put(dict24968, key24972, Value(false)); auto key24973 = Value("mode"); Put(dict24968, key24973, Value{}); auto key24974 = Value("pending"); Put(dict24968, key24974, List({})); auto key24975 = Value("sites"); Put(dict24968, key24975, ([&]() -> Value { auto dict24976 = Dict(); return dict24976; }())); auto key24977 = Value("credit"); Put(dict24968, key24977, Value(int64_t{0})); return dict24968; }());
s->SetAt(5, v24967);
Put(s->Global("_HD2_STATE"), s->LocalAt(4), v24967);
if (static_cast<bool>(([&]() -> Value { auto v24978 = s->LocalAt(6); Value v24979; v24979 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v24978, v24979))) return Value(false); v24978 = v24979; return Value(true); }()))) {
(void)([&]() -> Value { auto fn24980 = Attribute(s->Global("_HD2_REPORT"), "update"); Arguments args24981; args24981.Keyword("hd2_decision", Value("")); args24981.Keyword("hd2_ev", Value("")); args24981.Keyword("hd2_rewrites", Value(int64_t{0})); args24981.Keyword("hd2_credit_units", Value(int64_t{0})); args24981.Keyword("hd2_sold_units", Value(int64_t{0})); args24981.Keyword("hd2_errors", Value(int64_t{0})); return Call(c, fn24980, std::move(args24981)); }());
}
}
auto v24982 = s->LocalAt(6);
Put(s->LocalAt(5), Value("step"), v24982);
auto v24983 = ([&]() -> Value { auto v24984 = s->LocalAt(6); return Binary("FloorDiv", v24984, Value(int64_t{24})); }());
s->SetAt(2, v24983);
if (static_cast<bool>(([&]() -> Value { auto v24985 = s->LocalAt(2); Value v24986; v24986 = Get(s->LocalAt(5), Value("inv")); if (!static_cast<bool>(Binary("NotIn", v24985, v24986))) return Value(false); v24985 = v24986; return Value(true); }()))) {
auto v24987 = ([&]() -> Value { auto fn24988 = s->Global("dict"); Arguments args24989; args24989.Add(Get(Get(s->LocalAt(3), Value("market")), Value("inventory")), false); return Call(c, fn24988, std::move(args24989)); }());
Put(Get(s->LocalAt(5), Value("inv")), s->LocalAt(2), v24987);
}
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto fn24990 = s->Global("isinstance"); Arguments args24991; args24991.positional.reserve(2); args24991.Add(s->LocalAt(0), false); args24991.Add(s->Global("dict"), false); return Call(c, fn24990, std::move(args24991)); }())))) {
return s->LocalAt(0);
}
if (static_cast<bool>(Get(s->LocalAt(5), Value("mode")))) {
(void)([&]() -> Value { auto fn24992 = s->Global("_hd2_confirm"); Arguments args24993; args24993.positional.reserve(2); args24993.Add(s->LocalAt(3), false); args24993.Add(s->LocalAt(5), false); return Call(c, fn24992, std::move(args24993)); }());
}
else {
if (static_cast<bool>(Unary("Not", Get(s->LocalAt(5), Value("decided"))))) {
(void)([&]() -> Value { auto fn24994 = s->Global("_hd2_decide"); Arguments args24995; args24995.positional.reserve(3); args24995.Add(s->LocalAt(3), false); args24995.Add(s->LocalAt(0), false); args24995.Add(s->LocalAt(5), false); return Call(c, fn24994, std::move(args24995)); }());
}
}
if (static_cast<bool>(Get(s->LocalAt(5), Value("mode")))) {
auto v24996 = ([&]() -> Value { auto fn24997 = Attribute(s->Global("copy"), "deepcopy"); Arguments args24998; args24998.Add(s->LocalAt(0), false); return Call(c, fn24997, std::move(args24998)); }());
s->SetAt(0, v24996);
(void)([&]() -> Value { auto fn24999 = s->Global("_hd2_rewrite"); Arguments args25000; args25000.positional.reserve(3); args25000.Add(s->LocalAt(3), false); args25000.Add(s->LocalAt(0), false); args25000.Add(s->LocalAt(5), false); return Call(c, fn24999, std::move(args25000)); }());
}
} catch (const Error& error24952) {
if (Matches(error24952, s->Global("Exception"))) {
auto v25001 = s->Global("_HD2_REPORT");
auto v25002 = Value("hd2_errors");
auto v25003 = Get(v25001, v25002);
Put(v25001, v25002, Inplace("Add", v25003, Value(int64_t{1})));
}
else { throw; }
}
return s->LocalAt(0);
return {};
}
}  // namespace kagg::opponents::compiled
