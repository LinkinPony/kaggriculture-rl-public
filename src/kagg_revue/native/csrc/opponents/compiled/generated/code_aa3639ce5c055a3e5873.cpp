// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_aa3639ce5c055a3e5873(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "actor", "blocked", "c", "commands", "demand", "farm", "obs", "private"};
s->PrepareSlots(s_names);
auto v30576 = ([&]() -> Value { auto fn30577 = Get(s->Global("_PLANNER_NS"), Value("_clone_state")); Arguments args30578; args30578.positional.reserve(2); args30578.Add(Get(Get(s->LocalAt(7), Value("farms")), Get(s->LocalAt(7), Value("player"))), false); args30578.Add(Get(s->LocalAt(7), Value("private")), false); return Call(c, fn30577, std::move(args30578)); }());
auto unpack30579 = Iterate(v30576);
ValidateUnpack(unpack30579, 2, false);
s->SetAt(6, unpack30579.at(0));
s->SetAt(8, unpack30579.at(1));
auto v30580 = ([&]() -> Value { Arguments args30581; args30581.Add(([&]() -> Value { auto v30582 = ([&]() -> Value { auto fn30583 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args30584; args30584.Add(Value("farmer"), false); return CallDictionaryGet(c, fn30583, std::move(args30584)); }()); if (static_cast<bool>(v30582)) return v30582; v30582 = List({Value("PASS")}); return v30582; }()), false); args30581.Add(([&]() -> Value { auto v30585 = ([&]() -> Value { auto fn30586 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args30587; args30587.Add(Value("hands"), false); return CallDictionaryGet(c, fn30586, std::move(args30587)); }()); if (static_cast<bool>(v30585)) return v30585; v30585 = List({}); return v30585; }()), true); return List(std::move(args30581.positional)); }());
s->SetAt(4, v30580);
auto v30588 = ([&]() -> Value { auto dict30589 = Dict(); return dict30589; }());
s->SetAt(5, v30588);
for (const auto& item30590 : Iterate(s->LocalAt(4))) {
s->SetAt(3, item30590);
if (static_cast<bool>(([&]() -> Value { auto v30591 = ([&]() -> Value { auto v30592 = ([&]() -> Value { auto fn30594 = s->Global("len"); Arguments args30595; args30595.Add(s->LocalAt(3), false); return Call(c, fn30594, std::move(args30595)); }()); Value v30593; v30593 = Value(int64_t{1}); if (!static_cast<bool>(Binary("Gt", v30592, v30593))) return Value(false); v30592 = v30593; return Value(true); }()); if (!static_cast<bool>(v30591)) return v30591; v30591 = ([&]() -> Value { auto v30596 = Get(s->LocalAt(3), Value(int64_t{0})); Value v30597; v30597 = Value("PLANT"); if (!static_cast<bool>(Binary("Eq", v30596, v30597))) return Value(false); v30596 = v30597; return Value(true); }()); return v30591; }()))) {
auto v30598 = ([&]() -> Value { auto v30599 = ([&]() -> Value { auto fn30600 = PrepareDictionaryGet(s->LocalAt(5)); Arguments args30601; args30601.positional.reserve(2); args30601.Add(Get(s->LocalAt(3), Value(int64_t{1})), false); args30601.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn30600, std::move(args30601)); }()); return Binary("Add", v30599, Value(int64_t{1})); }());
Put(s->LocalAt(5), Get(s->LocalAt(3), Value(int64_t{1})), v30598);
}
}
auto v30602 = ([&]() -> Value { auto comp30603 = std::make_shared<Scope>(); comp30603->globals = s->globals; comp30603->parent = s; static constexpr const char* comp30603_names[] = {"n", "p"}; comp30603->PrepareSlots(comp30603_names); auto result30604 = List(); for (const auto& item30605 : Iterate(([&]() -> Value { auto fn30606 = Attribute(s->LocalAt(5), "items"); Arguments args30607; return Call(c, fn30606, std::move(args30607)); }()))) { auto unpack30608 = Iterate(item30605); ValidateUnpack(unpack30608, 2, false); comp30603->SetAt(1, unpack30608.at(0)); comp30603->SetAt(0, unpack30608.at(1)); if (!static_cast<bool>(([&]() -> Value { auto v30609 = comp30603->LocalAt(0); Value v30610; v30610 = ([&]() -> Value { auto fn30611 = PrepareDictionaryGet(Get(comp30603->Captured("private"), Value("seeds"))); Arguments args30612; args30612.positional.reserve(2); args30612.Add(comp30603->LocalAt(1), false); args30612.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn30611, std::move(args30612)); }()); if (!static_cast<bool>(Binary("Gt", v30609, v30610))) return Value(false); v30609 = v30610; return Value(true); }()))) continue; result30604.node()->sequence.push_back(comp30603->LocalAt(1)); } return Set(result30604.node()->sequence); }());
s->SetAt(2, v30602);
for (const auto& item30613 : Iterate(([&]() -> Value { auto fn30614 = s->Global("enumerate"); Arguments args30615; args30615.Add(Slice(s->LocalAt(4), Value{}, ([&]() -> Value { auto fn30616 = s->Global("len"); Arguments args30617; args30617.Add(Get(s->LocalAt(8), Value("inventories")), false); return Call(c, fn30616, std::move(args30617)); }()), Value{}), false); return Call(c, fn30614, std::move(args30615)); }()))) {
auto unpack30618 = Iterate(item30613);
ValidateUnpack(unpack30618, 2, false);
s->SetAt(1, unpack30618.at(0));
s->SetAt(3, unpack30618.at(1));
if (static_cast<bool>(([&]() -> Value { auto v30619 = ([&]() -> Value { auto v30620 = ([&]() -> Value { auto fn30622 = s->Global("len"); Arguments args30623; args30623.Add(s->LocalAt(3), false); return Call(c, fn30622, std::move(args30623)); }()); Value v30621; v30621 = Value(int64_t{1}); if (!static_cast<bool>(Binary("Gt", v30620, v30621))) return Value(false); v30620 = v30621; return Value(true); }()); if (!static_cast<bool>(v30619)) return v30619; v30619 = ([&]() -> Value { auto v30624 = Get(s->LocalAt(3), Value(int64_t{0})); Value v30625; v30625 = Value("PLANT"); if (!static_cast<bool>(Binary("Eq", v30624, v30625))) return Value(false); v30624 = v30625; return Value(true); }()); if (!static_cast<bool>(v30619)) return v30619; v30619 = ([&]() -> Value { auto v30626 = Get(s->LocalAt(3), Value(int64_t{1})); Value v30627; v30627 = s->LocalAt(2); if (!static_cast<bool>(Binary("In", v30626, v30627))) return Value(false); v30626 = v30627; return Value(true); }()); return v30619; }()))) {
continue;
}
(void)([&]() -> Value { auto fn30628 = Get(s->Global("_PLANNER_NS"), Value("_apply_unit_action")); Arguments args30629; args30629.positional.reserve(8); args30629.Add(s->LocalAt(6), false); args30629.Add(s->LocalAt(8), false); args30629.Add(s->LocalAt(1), false); args30629.Add(s->LocalAt(3), false); args30629.Add(Value(int64_t{10}), false); args30629.Add(([&]() -> Value { auto v30630 = ([&]() -> Value { auto fn30631 = s->Global("int"); Arguments args30632; args30632.Add(Get(s->LocalAt(7), Value("step")), false); return Call(c, fn30631, std::move(args30632)); }()); return Binary("FloorDiv", v30630, Value(int64_t{24})); }()), false); args30629.Add(Value(int64_t{24}), false); args30629.Add(Value(int64_t{100}), false); return Call(c, fn30628, std::move(args30629)); }());
}
return Tuple({s->LocalAt(6), s->LocalAt(8)});
return {};
}
}  // namespace kagg::opponents::compiled
