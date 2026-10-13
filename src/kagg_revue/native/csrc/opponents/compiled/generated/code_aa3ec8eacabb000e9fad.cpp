// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_aa3ec8eacabb000e9fad(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "cfg", "configuration", "lead_available", "next_sup", "observation", "player", "projected", "raw", "route", "self", "st", "step", "view"};
s->PrepareSlots(s_names);
if (static_cast<bool>(([&]() -> Value { auto v531 = ([&]() -> Value { auto fn533 = s->Global("len"); Arguments args534; args534.Add(([&]() -> Value { auto v535 = ([&]() -> Value { auto fn536 = s->Global("_get"); Arguments args537; args537.positional.reserve(3); args537.Add(s->LocalAt(5), false); args537.Add(Value("farms"), false); args537.Add(List({}), false); return Call(c, fn536, std::move(args537)); }()); if (static_cast<bool>(v535)) return v535; v535 = List({}); return v535; }()), false); return Call(c, fn533, std::move(args534)); }()); Value v532; v532 = Value(int64_t{2}); if (!static_cast<bool>(Binary("Lt", v531, v532))) return Value(false); v531 = v532; return Value(true); }()))) {
Raise(([&]() -> Value { auto fn538 = s->Global("ValueError"); Arguments args539; args539.Add(Value("incomplete observation"), false); return Call(c, fn538, std::move(args539)); }()));
}
auto v540 = ([&]() -> Value { auto fn541 = s->Global("_step_of"); Arguments args542; args542.Add(s->LocalAt(5), false); return Call(c, fn541, std::move(args542)); }());
s->SetAt(12, v540);
auto v543 = ([&]() -> Value { auto fn544 = s->Global("_int"); Arguments args545; args545.Add(([&]() -> Value { auto fn546 = s->Global("_get"); Arguments args547; args547.positional.reserve(3); args547.Add(s->LocalAt(5), false); args547.Add(Value("player"), false); args547.Add(Value(int64_t{0}), false); return Call(c, fn546, std::move(args547)); }()), false); return Call(c, fn544, std::move(args545)); }());
s->SetAt(6, v543);
auto v548 = ([&]() -> Value { auto fn549 = Attribute(s->LocalAt(10), "_state"); Arguments args550; args550.positional.reserve(2); args550.Add(s->LocalAt(6), false); args550.Add(s->LocalAt(12), false); return Call(c, fn549, std::move(args550)); }());
s->SetAt(11, v548);
auto v551 = Attribute(s->LocalAt(10), "cfg");
s->SetAt(1, v551);
auto v552 = ([&]() -> Value { auto fn553 = s->Global("_View"); Arguments args554; args554.positional.reserve(3); args554.Add(s->LocalAt(5), false); args554.Add(s->LocalAt(6), false); args554.Add(s->LocalAt(1), false); return Call(c, fn553, std::move(args554)); }());
s->SetAt(13, v552);
auto v555 = ([&]() -> Value { auto fn556 = Attribute(s->LocalAt(10), "router"); Arguments args557; args557.positional.reserve(3); args557.Add(s->LocalAt(5), false); args557.Add(s->LocalAt(12), false); args557.Add(Get(s->LocalAt(11), Value("router_state")), false); return Call(c, fn556, std::move(args557)); }());
s->SetAt(9, v555);
if (static_cast<bool>(([&]() -> Value { auto v558 = s->LocalAt(9); Value v559; v559 = Attribute(s->LocalAt(10), "routes"); if (!static_cast<bool>(Binary("NotIn", v558, v559))) return Value(false); v558 = v559; return Value(true); }()))) {
auto v560 = (static_cast<bool>(([&]() -> Value { auto v561 = Get(s->LocalAt(11), Value("route")); Value v562; v562 = Attribute(s->LocalAt(10), "routes"); if (!static_cast<bool>(Binary("In", v561, v562))) return Value(false); v561 = v562; return Value(true); }())) ? Get(s->LocalAt(11), Value("route")) : ([&]() -> Value { auto fn563 = s->Global("next"); Arguments args564; args564.Add(([&]() -> Value { auto fn565 = s->Global("iter"); Arguments args566; args566.Add(Attribute(s->LocalAt(10), "routes"), false); return Call(c, fn565, std::move(args566)); }()), false); return Call(c, fn563, std::move(args564)); }()));
s->SetAt(9, v560);
}
auto v567 = s->LocalAt(9);
Put(s->LocalAt(11), Value("route"), v567);
auto v568 = ([&]() -> Value { auto fn569 = Attribute(s->LocalAt(10), "_route_action"); Arguments args570; args570.positional.reserve(2); args570.Add(s->LocalAt(9), false); args570.Add(s->LocalAt(12), false); return Call(c, fn569, std::move(args570)); }());
s->SetAt(0, v568);
auto v571 = ([&]() -> Value { auto fn572 = Attribute(s->Global("copy"), "deepcopy"); Arguments args573; args573.Add(s->LocalAt(0), false); return Call(c, fn572, std::move(args573)); }());
s->SetAt(8, v571);
try {
if (static_cast<bool>(Get(s->LocalAt(1), Value("hand_align")))) {
(void)([&]() -> Value { auto fn575 = Attribute(s->LocalAt(10), "_hand_align"); Arguments args576; args576.positional.reserve(2); args576.Add(s->LocalAt(0), false); args576.Add(s->LocalAt(13), false); return Call(c, fn575, std::move(args576)); }());
}
if (static_cast<bool>(Get(s->LocalAt(1), Value("weed_repair")))) {
(void)([&]() -> Value { auto fn577 = Attribute(s->LocalAt(10), "_weed_repair"); Arguments args578; args578.positional.reserve(5); args578.Add(s->LocalAt(0), false); args578.Add(s->LocalAt(13), false); args578.Add(s->LocalAt(11), false); args578.Add(s->LocalAt(9), false); args578.Add(s->LocalAt(12), false); return Call(c, fn577, std::move(args578)); }());
}
if (static_cast<bool>(([&]() -> Value { auto v579 = Get(s->LocalAt(1), Value("sell_lead")); if (static_cast<bool>(v579)) return v579; v579 = Get(s->LocalAt(1), Value("front_run")); return v579; }()))) {
(void)([&]() -> Value { auto fn580 = Attribute(s->LocalAt(10), "_apply_suppression"); Arguments args581; args581.positional.reserve(3); args581.Add(s->LocalAt(0), false); args581.Add(Get(s->LocalAt(11), Value("sell_state")), false); args581.Add(s->LocalAt(12), false); return Call(c, fn580, std::move(args581)); }());
}
auto v582 = ([&]() -> Value { auto fn583 = Attribute(s->LocalAt(10), "_projected_shed"); Arguments args584; args584.positional.reserve(2); args584.Add(s->LocalAt(0), false); args584.Add(s->LocalAt(13), false); return Call(c, fn583, std::move(args584)); }());
s->SetAt(7, v582);
auto v585 = ([&]() -> Value { auto fn586 = s->Global("dict"); Arguments args587; args587.Add(s->LocalAt(7), false); return Call(c, fn586, std::move(args587)); }());
s->SetAt(3, v585);
auto v588 = ([&]() -> Value { auto dict589 = Dict(); auto key590 = Value("due_step"); Put(dict589, key590, Unary("USub", Value(int64_t{1}))); auto key591 = Value("suppress"); Put(dict589, key591, ([&]() -> Value { auto dict592 = Dict(); return dict592; }())); auto key593 = Value("r36_debts"); Put(dict589, key593, ([&]() -> Value { auto fn594 = PrepareDictionaryGet(Get(s->LocalAt(11), Value("sell_state"))); Arguments args595; args595.positional.reserve(2); args595.Add(Value("r36_debts"), false); args595.Add(([&]() -> Value { auto dict596 = Dict(); return dict596; }()), false); return CallDictionaryGet(c, fn594, std::move(args595)); }())); return dict589; }());
s->SetAt(4, v588);
if (static_cast<bool>(Get(s->LocalAt(1), Value("sell_lead")))) {
(void)([&]() -> Value { auto fn597 = Attribute(s->LocalAt(10), "_sell_lead"); Arguments args598; args598.positional.reserve(6); args598.Add(s->LocalAt(0), false); args598.Add(s->LocalAt(13), false); args598.Add(s->LocalAt(3), false); args598.Add(s->LocalAt(9), false); args598.Add(s->LocalAt(12), false); args598.Add(s->LocalAt(4), false); return Call(c, fn597, std::move(args598)); }());
}
if (static_cast<bool>(([&]() -> Value { auto v599 = Get(s->LocalAt(1), Value("front_run")); if (!static_cast<bool>(v599)) return v599; v599 = Attribute(s->LocalAt(10), "opponent_plan"); return v599; }()))) {
(void)([&]() -> Value { auto fn600 = Attribute(s->LocalAt(10), "_front_run"); Arguments args601; args601.positional.reserve(6); args601.Add(s->LocalAt(0), false); args601.Add(s->LocalAt(13), false); args601.Add(s->LocalAt(3), false); args601.Add(s->LocalAt(9), false); args601.Add(s->LocalAt(12), false); args601.Add(s->LocalAt(4), false); return Call(c, fn600, std::move(args601)); }());
}
auto v602 = s->LocalAt(4);
Put(s->LocalAt(11), Value("sell_state"), v602);
if (static_cast<bool>(Get(s->LocalAt(1), Value("budget_guard")))) {
(void)([&]() -> Value { auto fn603 = Attribute(s->LocalAt(10), "_budget_guard"); Arguments args604; args604.positional.reserve(4); args604.Add(s->LocalAt(0), false); args604.Add(s->LocalAt(13), false); args604.Add(s->LocalAt(9), false); args604.Add(s->LocalAt(12), false); return Call(c, fn603, std::move(args604)); }());
}
if (static_cast<bool>(Get(s->LocalAt(1), Value("room_guard")))) {
(void)([&]() -> Value { auto fn605 = Attribute(s->LocalAt(10), "_room_guard"); Arguments args606; args606.positional.reserve(4); args606.Add(s->LocalAt(0), false); args606.Add(s->LocalAt(13), false); args606.Add(s->LocalAt(9), false); args606.Add(s->LocalAt(12), false); return Call(c, fn605, std::move(args606)); }());
}
if (static_cast<bool>(Get(s->LocalAt(1), Value("clamp_sells")))) {
(void)([&]() -> Value { auto fn607 = Attribute(s->LocalAt(10), "_clamp_sells"); Arguments args608; args608.positional.reserve(2); args608.Add(s->LocalAt(0), false); args608.Add(s->LocalAt(7), false); return Call(c, fn607, std::move(args608)); }());
}
if (static_cast<bool>(Get(s->LocalAt(1), Value("dead_stock")))) {
(void)([&]() -> Value { auto fn609 = Attribute(s->LocalAt(10), "_dead_stock"); Arguments args610; args610.positional.reserve(5); args610.Add(s->LocalAt(0), false); args610.Add(s->LocalAt(13), false); args610.Add(s->LocalAt(7), false); args610.Add(s->LocalAt(9), false); args610.Add(s->LocalAt(12), false); return Call(c, fn609, std::move(args610)); }());
}
if (static_cast<bool>(Get(s->LocalAt(1), Value("terminal_liquidation")))) {
(void)([&]() -> Value { auto fn611 = Attribute(s->LocalAt(10), "_terminal_liquidation"); Arguments args612; args612.positional.reserve(3); args612.Add(s->LocalAt(0), false); args612.Add(s->LocalAt(7), false); args612.Add(s->LocalAt(12), false); return Call(c, fn611, std::move(args612)); }());
}
auto v613 = Slice(Get(s->LocalAt(0), Value("market")), Value{}, Get(s->LocalAt(1), Value("max_orders")), Value{});
Put(s->LocalAt(0), Value("market"), v613);
return s->LocalAt(0);
} catch (const Error& error574) {
if (Matches(error574, s->Global("Exception"))) {
auto v614 = Attribute(s->LocalAt(10), "diagnostics");
auto v615 = Value("layer_fallbacks");
auto v616 = Get(v614, v615);
Put(v614, v615, Inplace("Add", v616, Value(int64_t{1})));
return s->LocalAt(8);
}
else { throw; }
}
return {};
}
}  // namespace kagg::opponents::compiled
