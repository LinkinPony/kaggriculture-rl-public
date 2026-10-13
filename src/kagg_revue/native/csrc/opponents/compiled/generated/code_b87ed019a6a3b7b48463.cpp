// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_b87ed019a6a3b7b48463(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "configuration", "observation", "pending", "player", "standard", "step"};
s->PrepareSlots(s_names);
auto v12611 = ([&]() -> Value { auto fn12612 = s->Global("_R148_PARENT"); Arguments args12613; args12613.positional.reserve(2); args12613.Add(s->LocalAt(2), false); args12613.Add(s->LocalAt(1), false); return Call(c, fn12612, std::move(args12613)); }());
s->SetAt(0, v12611);
try {
auto v12615 = ([&]() -> Value { auto fn12616 = s->Global("int"); Arguments args12617; args12617.Add(Get(s->LocalAt(2), Value("player")), false); return Call(c, fn12616, std::move(args12617)); }());
s->SetAt(4, v12615);
auto v12618 = ([&]() -> Value { auto fn12619 = s->Global("int"); Arguments args12620; args12620.Add(Get(s->LocalAt(2), Value("step")), false); return Call(c, fn12619, std::move(args12620)); }());
s->SetAt(6, v12618);
if (static_cast<bool>(([&]() -> Value { auto v12621 = s->LocalAt(6); Value v12622; v12622 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v12621, v12622))) return Value(false); v12621 = v12622; return Value(true); }()))) {
(void)([&]() -> Value { auto fn12623 = Attribute(s->Global("_R148_PENDING"), "pop"); Arguments args12624; args12624.positional.reserve(2); args12624.Add(s->LocalAt(4), false); args12624.Add(Value{}, false); return Call(c, fn12623, std::move(args12624)); }());
(void)([&]() -> Value { auto fn12625 = Attribute(s->Global("_R148_REPORT"), "clear"); Arguments args12626; return Call(c, fn12625, std::move(args12626)); }());
(void)([&]() -> Value { auto fn12627 = Attribute(s->Global("_R148_REPORT"), "update"); Arguments args12628; args12628.Keyword("overflow_turns", Value(int64_t{0})); args12628.Keyword("overflow_units_reclaimed", Value(int64_t{0})); args12628.Keyword("overflow_quote_exposure", Value(int64_t{0})); args12628.Keyword("overflow_contract_checks", Value(int64_t{0})); args12628.Keyword("overflow_contract_errors", Value(int64_t{0})); args12628.Keyword("atomic_turns", Value(int64_t{0})); args12628.Keyword("atomic_kept_requests", Value(int64_t{0})); args12628.Keyword("atomic_removed_requests", Value(int64_t{0})); args12628.Keyword("seed_prefund_turns", Value(int64_t{0})); args12628.Keyword("seed_prefund_units", Value(int64_t{0})); args12628.Keyword("targeted_errors", Value(int64_t{0})); return Call(c, fn12627, std::move(args12628)); }());
}
auto v12629 = ([&]() -> Value { auto fn12630 = Attribute(s->Global("_R148_PENDING"), "pop"); Arguments args12631; args12631.positional.reserve(2); args12631.Add(s->LocalAt(4), false); args12631.Add(Value{}, false); return Call(c, fn12630, std::move(args12631)); }());
s->SetAt(3, v12629);
if (static_cast<bool>(s->LocalAt(3))) {
if (static_cast<bool>(([&]() -> Value { auto v12632 = ([&]() -> Value { auto v12633 = s->LocalAt(6); Value v12634; v12634 = Get(s->LocalAt(3), Value(int64_t{0})); if (!static_cast<bool>(Binary("NotEq", v12633, v12634))) return Value(false); v12633 = v12634; return Value(true); }()); if (static_cast<bool>(v12632)) return v12632; v12632 = Unary("Not", ([&]() -> Value { auto fn12635 = s->Global("_r148_same_stock"); Arguments args12636; args12636.positional.reserve(2); args12636.Add(Get(Get(s->LocalAt(2), Value("private")), Value("shed")), false); args12636.Add(Get(s->LocalAt(3), Value(int64_t{1})), false); return Call(c, fn12635, std::move(args12636)); }())); return v12632; }()))) {
auto v12637 = s->Global("_R148_REPORT");
auto v12638 = Value("overflow_contract_errors");
auto v12639 = Get(v12637, v12638);
Put(v12637, v12638, Inplace("Add", v12639, Value(int64_t{1})));
}
else {
auto v12640 = s->Global("_R148_REPORT");
auto v12641 = Value("overflow_contract_checks");
auto v12642 = Get(v12640, v12641);
Put(v12640, v12641, Inplace("Add", v12642, Value(int64_t{1})));
}
}
auto v12643 = ([&]() -> Value { auto v12644 = ([&]() -> Value { auto v12645 = s->LocalAt(1); Value v12646; v12646 = Value{}; if (!static_cast<bool>(Binary("Is", v12645, v12646))) return Value(false); v12645 = v12646; return Value(true); }()); if (static_cast<bool>(v12644)) return v12644; v12644 = ([&]() -> Value { auto comp12647 = std::make_shared<Scope>(); comp12647->globals = s->globals; comp12647->parent = s; static constexpr const char* comp12647_names[] = {"k", "v"}; comp12647->PrepareSlots(comp12647_names); auto result12648 = List(); for (const auto& item12649 : Iterate(List({Tuple({Value("boardSize"), Value(int64_t{10})}), Tuple({Value("turnsPerDay"), Value(int64_t{24})}), Tuple({Value("shedCapacity"), Value(int64_t{100})}), Tuple({Value("maxMarketOrdersPerTurn"), Value(int64_t{10})}), Tuple({Value("farmHandCostMult"), Value(int64_t{1})})}))) { auto unpack12650 = Iterate(item12649); ValidateUnpack(unpack12650, 2, false); comp12647->SetAt(0, unpack12650.at(0)); comp12647->SetAt(1, unpack12650.at(1)); if (!static_cast<bool>(([&]() -> Value { auto v12651 = ([&]() -> Value { auto fn12653 = PrepareDictionaryGet(comp12647->Captured("configuration")); Arguments args12654; args12654.positional.reserve(2); args12654.Add(comp12647->LocalAt(0), false); args12654.Add(comp12647->LocalAt(1), false); return CallDictionaryGet(c, fn12653, std::move(args12654)); }()); Value v12652; v12652 = comp12647->LocalAt(1); if (!static_cast<bool>(Binary("Eq", v12651, v12652))) return Value(false); v12651 = v12652; return Value(true); }()))) return Value(false); } return Value(true); }()); return v12644; }());
s->SetAt(5, v12643);
if (static_cast<bool>(s->LocalAt(5))) {
if (static_cast<bool>(s->Global("_R148_SEEDS"))) {
auto v12655 = ([&]() -> Value { auto fn12656 = s->Global("_r148_seed_prefund"); Arguments args12657; args12657.positional.reserve(2); args12657.Add(s->LocalAt(2), false); args12657.Add(([&]() -> Value { auto fn12658 = s->Global("_r148_atomic"); Arguments args12659; args12659.positional.reserve(2); args12659.Add(s->LocalAt(2), false); args12659.Add(s->LocalAt(0), false); return Call(c, fn12658, std::move(args12659)); }()), false); return Call(c, fn12656, std::move(args12657)); }());
s->SetAt(0, v12655);
}
if (static_cast<bool>(s->Global("_R148_OVERFLOW"))) {
auto v12660 = ([&]() -> Value { auto fn12661 = s->Global("_r148_overflow"); Arguments args12662; args12662.positional.reserve(2); args12662.Add(s->LocalAt(2), false); args12662.Add(s->LocalAt(0), false); return Call(c, fn12661, std::move(args12662)); }());
s->SetAt(0, v12660);
}
}
} catch (const Error& error12614) {
if (Matches(error12614, s->Global("Exception"))) {
auto v12663 = ([&]() -> Value { auto v12664 = ([&]() -> Value { auto fn12665 = PrepareDictionaryGet(s->Global("_R148_REPORT")); Arguments args12666; args12666.positional.reserve(2); args12666.Add(Value("targeted_errors"), false); args12666.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn12665, std::move(args12666)); }()); return Binary("Add", v12664, Value(int64_t{1})); }());
Put(s->Global("_R148_REPORT"), Value("targeted_errors"), v12663);
}
else { throw; }
}
(void)([&]() -> Value { auto fn12667 = Attribute(s->Global("_R148_REPORT"), "update"); Arguments args12668; args12668.Add(([&]() -> Value { auto fn12669 = s->Global("getattr"); Arguments args12670; args12670.positional.reserve(3); args12670.Add(s->Global("_R148_PARENT"), false); args12670.Add(Value("telemetry"), false); args12670.Add(([&]() -> Value { auto dict12671 = Dict(); return dict12671; }()), false); return Call(c, fn12669, std::move(args12670)); }()), false); return Call(c, fn12667, std::move(args12668)); }());
return s->LocalAt(0);
return {};
}
}  // namespace kagg::opponents::compiled
