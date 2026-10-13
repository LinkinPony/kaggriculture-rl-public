// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_ca796eff1cb2bcdf2a90(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"configuration", "observation", "result"};
s->PrepareSlots(s_names);
auto v8533 = ([&]() -> Value { auto fn8534 = s->Global("_R51_WAREHOUSE_PARENT"); Arguments args8535; args8535.positional.reserve(2); args8535.Add(s->LocalAt(1), false); args8535.Add(s->LocalAt(0), false); return Call(c, fn8534, std::move(args8535)); }());
s->SetAt(2, v8533);
try {
if (static_cast<bool>(([&]() -> Value { auto v8537 = ([&]() -> Value { auto fn8539 = s->Global("int"); Arguments args8540; args8540.Add(Get(s->LocalAt(1), Value("step")), false); return Call(c, fn8539, std::move(args8540)); }()); Value v8538; v8538 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v8537, v8538))) return Value(false); v8537 = v8538; return Value(true); }()))) {
(void)([&]() -> Value { auto fn8541 = Attribute(s->Global("_R51_WAREHOUSE_REPORT"), "update"); Arguments args8542; args8542.Keyword("warehouse_changed_turns", Value(int64_t{0})); args8542.Keyword("warehouse_extra_sales", Value(int64_t{0})); args8542.Keyword("warehouse_projected_unresolved", Value(int64_t{0})); args8542.Keyword("warehouse_errors", Value(int64_t{0})); return Call(c, fn8541, std::move(args8542)); }());
}
if (static_cast<bool>(([&]() -> Value { auto v8543 = ([&]() -> Value { auto v8544 = s->LocalAt(0); Value v8545; v8545 = Value{}; if (!static_cast<bool>(Binary("Is", v8544, v8545))) return Value(false); v8544 = v8545; return Value(true); }()); if (static_cast<bool>(v8543)) return v8543; v8543 = ([&]() -> Value { auto comp8546 = std::make_shared<Scope>(); comp8546->globals = s->globals; comp8546->parent = s; static constexpr const char* comp8546_names[] = {"k", "v"}; comp8546->PrepareSlots(comp8546_names); auto result8547 = List(); for (const auto& item8548 : Iterate(List({Tuple({Value("boardSize"), Value(int64_t{10})}), Tuple({Value("turnsPerDay"), Value(int64_t{24})}), Tuple({Value("shedCapacity"), Value(int64_t{100})}), Tuple({Value("maxMarketOrdersPerTurn"), Value(int64_t{10})})}))) { auto unpack8549 = Iterate(item8548); ValidateUnpack(unpack8549, 2, false); comp8546->SetAt(0, unpack8549.at(0)); comp8546->SetAt(1, unpack8549.at(1)); if (!static_cast<bool>(([&]() -> Value { auto v8550 = ([&]() -> Value { auto fn8552 = PrepareDictionaryGet(comp8546->Captured("configuration")); Arguments args8553; args8553.positional.reserve(2); args8553.Add(comp8546->LocalAt(0), false); args8553.Add(comp8546->LocalAt(1), false); return CallDictionaryGet(c, fn8552, std::move(args8553)); }()); Value v8551; v8551 = comp8546->LocalAt(1); if (!static_cast<bool>(Binary("Eq", v8550, v8551))) return Value(false); v8550 = v8551; return Value(true); }()))) return Value(false); } return Value(true); }()); return v8543; }()))) {
auto v8554 = ([&]() -> Value { auto fn8555 = s->Global("_r51_close_warehouse"); Arguments args8556; args8556.positional.reserve(2); args8556.Add(s->LocalAt(1), false); args8556.Add(s->LocalAt(2), false); return Call(c, fn8555, std::move(args8556)); }());
s->SetAt(2, v8554);
}
} catch (const Error& error8536) {
if (Matches(error8536, s->Global("Exception"))) {
auto v8557 = ([&]() -> Value { auto v8558 = ([&]() -> Value { auto fn8559 = PrepareDictionaryGet(s->Global("_R51_WAREHOUSE_REPORT")); Arguments args8560; args8560.positional.reserve(2); args8560.Add(Value("warehouse_errors"), false); args8560.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn8559, std::move(args8560)); }()); return Binary("Add", v8558, Value(int64_t{1})); }());
Put(s->Global("_R51_WAREHOUSE_REPORT"), Value("warehouse_errors"), v8557);
}
else { throw; }
}
(void)([&]() -> Value { auto fn8561 = Attribute(s->Global("_R51_WAREHOUSE_REPORT"), "update"); Arguments args8562; args8562.Add(([&]() -> Value { auto fn8563 = s->Global("getattr"); Arguments args8564; args8564.positional.reserve(3); args8564.Add(s->Global("_R51_WAREHOUSE_PARENT"), false); args8564.Add(Value("telemetry"), false); args8564.Add(([&]() -> Value { auto dict8565 = Dict(); return dict8565; }()), false); return Call(c, fn8563, std::move(args8564)); }()), false); return Call(c, fn8561, std::move(args8562)); }());
return s->LocalAt(2);
return {};
}
}  // namespace kagg::opponents::compiled
