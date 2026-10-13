// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_2e35d72a6aa531572bbb(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"configuration", "observation", "result"};
s->PrepareSlots(s_names);
auto v10125 = ([&]() -> Value { auto fn10126 = s->Global("_R95_PARENT"); Arguments args10127; args10127.positional.reserve(2); args10127.Add(s->LocalAt(1), false); args10127.Add(s->LocalAt(0), false); return Call(c, fn10126, std::move(args10127)); }());
s->SetAt(2, v10125);
try {
if (static_cast<bool>(([&]() -> Value { auto v10129 = ([&]() -> Value { auto fn10131 = s->Global("int"); Arguments args10132; args10132.Add(Get(s->LocalAt(1), Value("step")), false); return Call(c, fn10131, std::move(args10132)); }()); Value v10130; v10130 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v10129, v10130))) return Value(false); v10129 = v10130; return Value(true); }()))) {
(void)([&]() -> Value { auto fn10133 = Attribute(s->Global("_R95_REPORT"), "update"); Arguments args10134; args10134.Keyword("replenishment_trim_turns", Value(int64_t{0})); args10134.Keyword("replenishment_trim_units", Value(int64_t{0})); args10134.Keyword("replenishment_errors", Value(int64_t{0})); return Call(c, fn10133, std::move(args10134)); }());
}
if (static_cast<bool>(([&]() -> Value { auto v10135 = ([&]() -> Value { auto v10136 = s->LocalAt(0); Value v10137; v10137 = Value{}; if (!static_cast<bool>(Binary("IsNot", v10136, v10137))) return Value(false); v10136 = v10137; return Value(true); }()); if (!static_cast<bool>(v10135)) return v10135; v10135 = ([&]() -> Value { auto comp10138 = std::make_shared<Scope>(); comp10138->globals = s->globals; comp10138->parent = s; static constexpr const char* comp10138_names[] = {"k", "v"}; comp10138->PrepareSlots(comp10138_names); auto result10139 = List(); for (const auto& item10140 : Iterate(List({Tuple({Value("boardSize"), Value(int64_t{10})}), Tuple({Value("turnsPerDay"), Value(int64_t{24})}), Tuple({Value("shedCapacity"), Value(int64_t{100})}), Tuple({Value("maxMarketOrdersPerTurn"), Value(int64_t{10})})}))) { auto unpack10141 = Iterate(item10140); ValidateUnpack(unpack10141, 2, false); comp10138->SetAt(0, unpack10141.at(0)); comp10138->SetAt(1, unpack10141.at(1)); if (static_cast<bool>(([&]() -> Value { auto v10142 = ([&]() -> Value { auto fn10144 = PrepareDictionaryGet(comp10138->Captured("configuration")); Arguments args10145; args10145.positional.reserve(2); args10145.Add(comp10138->LocalAt(0), false); args10145.Add(comp10138->LocalAt(1), false); return CallDictionaryGet(c, fn10144, std::move(args10145)); }()); Value v10143; v10143 = comp10138->LocalAt(1); if (!static_cast<bool>(Binary("NotEq", v10142, v10143))) return Value(false); v10142 = v10143; return Value(true); }()))) return Value(true); } return Value(false); }()); return v10135; }()))) {
return s->LocalAt(2);
}
auto v10146 = ([&]() -> Value { auto fn10147 = s->Global("_r95_replenish"); Arguments args10148; args10148.positional.reserve(2); args10148.Add(s->LocalAt(1), false); args10148.Add(s->LocalAt(2), false); return Call(c, fn10147, std::move(args10148)); }());
s->SetAt(2, v10146);
} catch (const Error& error10128) {
if (Matches(error10128, s->Global("Exception"))) {
auto v10149 = ([&]() -> Value { auto v10150 = ([&]() -> Value { auto fn10151 = PrepareDictionaryGet(s->Global("_R95_REPORT")); Arguments args10152; args10152.positional.reserve(2); args10152.Add(Value("replenishment_errors"), false); args10152.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn10151, std::move(args10152)); }()); return Binary("Add", v10150, Value(int64_t{1})); }());
Put(s->Global("_R95_REPORT"), Value("replenishment_errors"), v10149);
}
else { throw; }
}
(void)([&]() -> Value { auto fn10153 = Attribute(s->Global("_R95_REPORT"), "update"); Arguments args10154; args10154.Add(([&]() -> Value { auto fn10155 = s->Global("getattr"); Arguments args10156; args10156.positional.reserve(3); args10156.Add(s->Global("_R95_PARENT"), false); args10156.Add(Value("telemetry"), false); args10156.Add(([&]() -> Value { auto dict10157 = Dict(); return dict10157; }()), false); return Call(c, fn10155, std::move(args10156)); }()), false); return Call(c, fn10153, std::move(args10154)); }());
return s->LocalAt(2);
return {};
}
}  // namespace kagg::opponents::compiled
