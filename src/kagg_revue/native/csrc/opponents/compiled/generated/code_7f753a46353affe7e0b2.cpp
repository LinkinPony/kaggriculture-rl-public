// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_7f753a46353affe7e0b2(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"configuration", "observation", "pending", "player", "result", "standard", "state", "step"};
s->PrepareSlots(s_names);
auto v12093 = ([&]() -> Value { auto fn12094 = s->Global("_R128_PARENT"); Arguments args12095; args12095.positional.reserve(2); args12095.Add(s->LocalAt(1), false); args12095.Add(s->LocalAt(0), false); return Call(c, fn12094, std::move(args12095)); }());
s->SetAt(4, v12093);
try {
auto v12097 = ([&]() -> Value { auto fn12098 = s->Global("int"); Arguments args12099; args12099.Add(Get(s->LocalAt(1), Value("player")), false); return Call(c, fn12098, std::move(args12099)); }());
s->SetAt(3, v12097);
auto v12100 = ([&]() -> Value { auto fn12101 = s->Global("int"); Arguments args12102; args12102.Add(Get(s->LocalAt(1), Value("step")), false); return Call(c, fn12101, std::move(args12102)); }());
s->SetAt(7, v12100);
auto v12103 = ([&]() -> Value { auto fn12104 = PrepareDictionaryGet(s->Global("_R128_STATES")); Arguments args12105; args12105.Add(s->LocalAt(3), false); return CallDictionaryGet(c, fn12104, std::move(args12105)); }());
s->SetAt(6, v12103);
if (static_cast<bool>(([&]() -> Value { auto v12106 = ([&]() -> Value { auto v12107 = s->LocalAt(6); Value v12108; v12108 = Value{}; if (!static_cast<bool>(Binary("Is", v12107, v12108))) return Value(false); v12107 = v12108; return Value(true); }()); if (static_cast<bool>(v12106)) return v12106; v12106 = ([&]() -> Value { auto v12109 = s->LocalAt(7); Value v12110; v12110 = Get(s->LocalAt(6), Value("step")); if (!static_cast<bool>(Binary("LtE", v12109, v12110))) return Value(false); v12109 = v12110; return Value(true); }()); return v12106; }()))) {
auto v12111 = ([&]() -> Value { auto dict12112 = Dict(); auto key12113 = Value("step"); Put(dict12112, key12113, Unary("USub", Value(int64_t{1}))); return dict12112; }());
s->SetAt(6, v12111);
Put(s->Global("_R128_STATES"), s->LocalAt(3), v12111);
(void)([&]() -> Value { auto fn12114 = Attribute(s->Global("_R128_REPORT"), "update"); Arguments args12115; args12115.Keyword("service_requested_units", Value(int64_t{0})); args12115.Keyword("service_confirmed_units", Value(int64_t{0})); args12115.Keyword("service_idle_preloads", Value(int64_t{0})); args12115.Keyword("service_swaps_started", Value(int64_t{0})); args12115.Keyword("service_swaps_completed", Value(int64_t{0})); args12115.Keyword("service_capacity_declines", Value(int64_t{0})); args12115.Keyword("service_arrival_errors", Value(int64_t{0})); args12115.Keyword("service_swap_errors", Value(int64_t{0})); args12115.Keyword("sale_credit_orders", Value(int64_t{0})); args12115.Keyword("sale_credit_lower_bound", Value(int64_t{0})); args12115.Keyword("sale_credit_grain_units", Value(int64_t{0})); args12115.Keyword("sale_credit_confirmed_units", Value(int64_t{0})); args12115.Keyword("sale_credit_errors", Value(int64_t{0})); args12115.Keyword("service_errors", Value(int64_t{0})); return Call(c, fn12114, std::move(args12115)); }());
}
auto v12116 = s->LocalAt(7);
Put(s->LocalAt(6), Value("step"), v12116);
auto v12117 = ([&]() -> Value { auto fn12118 = Attribute(s->LocalAt(6), "pop"); Arguments args12119; args12119.positional.reserve(2); args12119.Add(Value("credit_pending"), false); args12119.Add(Value{}, false); return Call(c, fn12118, std::move(args12119)); }());
s->SetAt(2, v12117);
if (static_cast<bool>(s->LocalAt(2))) {
if (static_cast<bool>(([&]() -> Value { auto v12120 = ([&]() -> Value { auto v12121 = Get(s->LocalAt(2), Value(int64_t{0})); Value v12122; v12122 = s->LocalAt(7); if (!static_cast<bool>(Binary("NotEq", v12121, v12122))) return Value(false); v12121 = v12122; return Value(true); }()); if (static_cast<bool>(v12120)) return v12120; v12120 = ([&]() -> Value { auto v12123 = ([&]() -> Value { auto fn12125 = PrepareDictionaryGet(Get(Get(s->LocalAt(1), Value("private")), Value("shed"))); Arguments args12126; args12126.positional.reserve(2); args12126.Add(Value("WHEAT"), false); args12126.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn12125, std::move(args12126)); }()); Value v12124; v12124 = Get(s->LocalAt(2), Value(int64_t{1})); if (!static_cast<bool>(Binary("Lt", v12123, v12124))) return Value(false); v12123 = v12124; return Value(true); }()); return v12120; }()))) {
auto v12127 = s->Global("_R128_REPORT");
auto v12128 = Value("sale_credit_errors");
auto v12129 = Get(v12127, v12128);
Put(v12127, v12128, Inplace("Add", v12129, Value(int64_t{1})));
}
else {
auto v12130 = s->Global("_R128_REPORT");
auto v12131 = Value("sale_credit_confirmed_units");
auto v12132 = Get(v12130, v12131);
Put(v12130, v12131, Inplace("Add", v12132, Get(s->LocalAt(2), Value(int64_t{2}))));
}
}
auto v12133 = ([&]() -> Value { auto v12134 = ([&]() -> Value { auto v12135 = s->LocalAt(0); Value v12136; v12136 = Value{}; if (!static_cast<bool>(Binary("Is", v12135, v12136))) return Value(false); v12135 = v12136; return Value(true); }()); if (static_cast<bool>(v12134)) return v12134; v12134 = ([&]() -> Value { auto comp12137 = std::make_shared<Scope>(); comp12137->globals = s->globals; comp12137->parent = s; static constexpr const char* comp12137_names[] = {"k", "v"}; comp12137->PrepareSlots(comp12137_names); auto result12138 = List(); for (const auto& item12139 : Iterate(List({Tuple({Value("boardSize"), Value(int64_t{10})}), Tuple({Value("turnsPerDay"), Value(int64_t{24})}), Tuple({Value("shedCapacity"), Value(int64_t{100})}), Tuple({Value("maxMarketOrdersPerTurn"), Value(int64_t{10})}), Tuple({Value("farmHandCostMult"), Value(int64_t{1})})}))) { auto unpack12140 = Iterate(item12139); ValidateUnpack(unpack12140, 2, false); comp12137->SetAt(0, unpack12140.at(0)); comp12137->SetAt(1, unpack12140.at(1)); if (!static_cast<bool>(([&]() -> Value { auto v12141 = ([&]() -> Value { auto fn12143 = PrepareDictionaryGet(comp12137->Captured("configuration")); Arguments args12144; args12144.positional.reserve(2); args12144.Add(comp12137->LocalAt(0), false); args12144.Add(comp12137->LocalAt(1), false); return CallDictionaryGet(c, fn12143, std::move(args12144)); }()); Value v12142; v12142 = comp12137->LocalAt(1); if (!static_cast<bool>(Binary("Eq", v12141, v12142))) return Value(false); v12141 = v12142; return Value(true); }()))) return Value(false); } return Value(true); }()); return v12134; }());
s->SetAt(5, v12133);
if (static_cast<bool>(s->LocalAt(5))) {
auto v12145 = ([&]() -> Value { auto fn12146 = s->Global("_r128_credit_supply"); Arguments args12147; args12147.positional.reserve(3); args12147.Add(s->LocalAt(1), false); args12147.Add(([&]() -> Value { auto fn12148 = s->Global("_r128_service"); Arguments args12149; args12149.positional.reserve(3); args12149.Add(s->LocalAt(1), false); args12149.Add(s->LocalAt(4), false); args12149.Add(s->LocalAt(6), false); return Call(c, fn12148, std::move(args12149)); }()), false); args12147.Add(s->LocalAt(6), false); return Call(c, fn12146, std::move(args12147)); }());
s->SetAt(4, v12145);
}
} catch (const Error& error12096) {
if (Matches(error12096, s->Global("Exception"))) {
auto v12150 = ([&]() -> Value { auto v12151 = ([&]() -> Value { auto fn12152 = PrepareDictionaryGet(s->Global("_R128_REPORT")); Arguments args12153; args12153.positional.reserve(2); args12153.Add(Value("service_errors"), false); args12153.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn12152, std::move(args12153)); }()); return Binary("Add", v12151, Value(int64_t{1})); }());
Put(s->Global("_R128_REPORT"), Value("service_errors"), v12150);
}
else { throw; }
}
(void)([&]() -> Value { auto fn12154 = Attribute(s->Global("_R128_REPORT"), "update"); Arguments args12155; args12155.Add(([&]() -> Value { auto fn12156 = s->Global("getattr"); Arguments args12157; args12157.positional.reserve(3); args12157.Add(s->Global("_R128_PARENT"), false); args12157.Add(Value("telemetry"), false); args12157.Add(([&]() -> Value { auto dict12158 = Dict(); return dict12158; }()), false); return Call(c, fn12156, std::move(args12157)); }()), false); return Call(c, fn12154, std::move(args12155)); }());
(void)([&]() -> Value { auto fn12159 = Attribute(s->Global("_R128_REPORT"), "update"); Arguments args12160; args12160.Add(s->Global("_R97_REPORT"), false); return Call(c, fn12159, std::move(args12160)); }());
return s->LocalAt(4);
return {};
}
}  // namespace kagg::opponents::compiled
