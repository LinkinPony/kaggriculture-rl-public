// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_2612e3cf8dc84a36e58a(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"configuration", "observation", "player", "result", "step"};
s->PrepareSlots(s_names);
auto v10693 = ([&]() -> Value { auto fn10694 = s->Global("_R97_PARENT"); Arguments args10695; args10695.positional.reserve(2); args10695.Add(s->LocalAt(1), false); args10695.Add(s->LocalAt(0), false); return Call(c, fn10694, std::move(args10695)); }());
s->SetAt(3, v10693);
try {
auto v10697 = ([&]() -> Value { auto fn10698 = s->Global("int"); Arguments args10699; args10699.Add(Get(s->LocalAt(1), Value("player")), false); return Call(c, fn10698, std::move(args10699)); }());
s->SetAt(2, v10697);
auto v10700 = ([&]() -> Value { auto fn10701 = s->Global("int"); Arguments args10702; args10702.Add(Get(s->LocalAt(1), Value("step")), false); return Call(c, fn10701, std::move(args10702)); }());
s->SetAt(4, v10700);
if (static_cast<bool>(([&]() -> Value { auto v10703 = ([&]() -> Value { auto v10704 = s->LocalAt(2); Value v10705; v10705 = s->Global("_R97_LAST"); if (!static_cast<bool>(Binary("NotIn", v10704, v10705))) return Value(false); v10704 = v10705; return Value(true); }()); if (static_cast<bool>(v10703)) return v10703; v10703 = ([&]() -> Value { auto v10706 = s->LocalAt(4); Value v10707; v10707 = Get(s->Global("_R97_LAST"), s->LocalAt(2)); if (!static_cast<bool>(Binary("LtE", v10706, v10707))) return Value(false); v10706 = v10707; return Value(true); }()); return v10703; }()))) {
(void)([&]() -> Value { auto fn10708 = Attribute(s->Global("_R97_REPORT"), "update"); Arguments args10709; args10709.Keyword("supply_guard_changes", Value(int64_t{0})); args10709.Keyword("supply_grain_protected", Value(int64_t{0})); args10709.Keyword("supply_buy_units", Value(int64_t{0})); args10709.Keyword("supply_early_changes", Value(int64_t{0})); args10709.Keyword("supply_early_units", Value(int64_t{0})); args10709.Keyword("supply_prefund_changes", Value(int64_t{0})); args10709.Keyword("supply_prefund_units", Value(int64_t{0})); args10709.Keyword("supply_slot_declines", Value(int64_t{0})); args10709.Keyword("supply_capacity_declines", Value(int64_t{0})); args10709.Keyword("supply_budget_declines", Value(int64_t{0})); args10709.Keyword("supply_errors", Value(int64_t{0})); return Call(c, fn10708, std::move(args10709)); }());
}
auto v10710 = s->LocalAt(4);
Put(s->Global("_R97_LAST"), s->LocalAt(2), v10710);
if (static_cast<bool>(([&]() -> Value { auto v10711 = ([&]() -> Value { auto v10712 = s->LocalAt(0); Value v10713; v10713 = Value{}; if (!static_cast<bool>(Binary("Is", v10712, v10713))) return Value(false); v10712 = v10713; return Value(true); }()); if (static_cast<bool>(v10711)) return v10711; v10711 = ([&]() -> Value { auto comp10714 = std::make_shared<Scope>(); comp10714->globals = s->globals; comp10714->parent = s; static constexpr const char* comp10714_names[] = {"k", "v"}; comp10714->PrepareSlots(comp10714_names); auto result10715 = List(); for (const auto& item10716 : Iterate(List({Tuple({Value("boardSize"), Value(int64_t{10})}), Tuple({Value("turnsPerDay"), Value(int64_t{24})}), Tuple({Value("shedCapacity"), Value(int64_t{100})}), Tuple({Value("maxMarketOrdersPerTurn"), Value(int64_t{10})}), Tuple({Value("farmHandCostMult"), Value(int64_t{1})})}))) { auto unpack10717 = Iterate(item10716); ValidateUnpack(unpack10717, 2, false); comp10714->SetAt(0, unpack10717.at(0)); comp10714->SetAt(1, unpack10717.at(1)); if (!static_cast<bool>(([&]() -> Value { auto v10718 = ([&]() -> Value { auto fn10720 = PrepareDictionaryGet(comp10714->Captured("configuration")); Arguments args10721; args10721.positional.reserve(2); args10721.Add(comp10714->LocalAt(0), false); args10721.Add(comp10714->LocalAt(1), false); return CallDictionaryGet(c, fn10720, std::move(args10721)); }()); Value v10719; v10719 = comp10714->LocalAt(1); if (!static_cast<bool>(Binary("Eq", v10718, v10719))) return Value(false); v10718 = v10719; return Value(true); }()))) return Value(false); } return Value(true); }()); return v10711; }()))) {
auto v10722 = ([&]() -> Value { auto fn10723 = s->Global("_r97_supply"); Arguments args10724; args10724.positional.reserve(2); args10724.Add(s->LocalAt(1), false); args10724.Add(s->LocalAt(3), false); return Call(c, fn10723, std::move(args10724)); }());
s->SetAt(3, v10722);
}
} catch (const Error& error10696) {
if (Matches(error10696, s->Global("Exception"))) {
auto v10725 = ([&]() -> Value { auto v10726 = ([&]() -> Value { auto fn10727 = PrepareDictionaryGet(s->Global("_R97_REPORT")); Arguments args10728; args10728.positional.reserve(2); args10728.Add(Value("supply_errors"), false); args10728.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn10727, std::move(args10728)); }()); return Binary("Add", v10726, Value(int64_t{1})); }());
Put(s->Global("_R97_REPORT"), Value("supply_errors"), v10725);
}
else { throw; }
}
(void)([&]() -> Value { auto fn10729 = Attribute(s->Global("_R97_REPORT"), "update"); Arguments args10730; args10730.Add(([&]() -> Value { auto fn10731 = s->Global("getattr"); Arguments args10732; args10732.positional.reserve(3); args10732.Add(s->Global("_R97_PARENT"), false); args10732.Add(Value("telemetry"), false); args10732.Add(([&]() -> Value { auto dict10733 = Dict(); return dict10733; }()), false); return Call(c, fn10731, std::move(args10732)); }()), false); return Call(c, fn10729, std::move(args10730)); }());
return s->LocalAt(3);
return {};
}
}  // namespace kagg::opponents::compiled
