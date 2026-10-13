// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_c3e638ae7bebfa34f40e(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "configuration", "market", "observation", "standard", "step"};
s->PrepareSlots(s_names);
auto v18499 = ([&]() -> Value { auto fn18500 = s->Global("_OPEN_PARENT"); Arguments args18501; args18501.positional.reserve(2); args18501.Add(s->LocalAt(3), false); args18501.Add(s->LocalAt(1), false); return Call(c, fn18500, std::move(args18501)); }());
s->SetAt(0, v18499);
try {
auto v18503 = ([&]() -> Value { auto fn18504 = s->Global("int"); Arguments args18505; args18505.Add(Get(s->LocalAt(3), Value("step")), false); return Call(c, fn18504, std::move(args18505)); }());
s->SetAt(5, v18503);
if (static_cast<bool>(([&]() -> Value { auto v18506 = s->LocalAt(5); Value v18507; v18507 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v18506, v18507))) return Value(false); v18506 = v18507; return Value(true); }()))) {
(void)([&]() -> Value { auto fn18508 = Attribute(s->Global("_OPEN_REPORT"), "update"); Arguments args18509; args18509.Keyword("open_turns", Value(int64_t{0})); args18509.Keyword("open_errors", Value(int64_t{0})); args18509.Keyword("open_attack", Value(int64_t{0})); return Call(c, fn18508, std::move(args18509)); }());
}
auto v18510 = ([&]() -> Value { auto v18511 = ([&]() -> Value { auto v18512 = s->LocalAt(1); Value v18513; v18513 = Value{}; if (!static_cast<bool>(Binary("Is", v18512, v18513))) return Value(false); v18512 = v18513; return Value(true); }()); if (static_cast<bool>(v18511)) return v18511; v18511 = ([&]() -> Value { auto comp18514 = std::make_shared<Scope>(); comp18514->globals = s->globals; comp18514->parent = s; static constexpr const char* comp18514_names[] = {"k", "v"}; comp18514->PrepareSlots(comp18514_names); auto result18515 = List(); for (const auto& item18516 : Iterate(List({Tuple({Value("boardSize"), Value(int64_t{10})}), Tuple({Value("turnsPerDay"), Value(int64_t{24})}), Tuple({Value("shedCapacity"), Value(int64_t{100})}), Tuple({Value("maxMarketOrdersPerTurn"), Value(int64_t{10})}), Tuple({Value("startingMoney"), Value(int64_t{3000})})}))) { auto unpack18517 = Iterate(item18516); ValidateUnpack(unpack18517, 2, false); comp18514->SetAt(0, unpack18517.at(0)); comp18514->SetAt(1, unpack18517.at(1)); if (!static_cast<bool>(([&]() -> Value { auto v18518 = ([&]() -> Value { auto fn18520 = PrepareDictionaryGet(comp18514->Captured("configuration")); Arguments args18521; args18521.positional.reserve(2); args18521.Add(comp18514->LocalAt(0), false); args18521.Add(comp18514->LocalAt(1), false); return CallDictionaryGet(c, fn18520, std::move(args18521)); }()); Value v18519; v18519 = comp18514->LocalAt(1); if (!static_cast<bool>(Binary("Eq", v18518, v18519))) return Value(false); v18518 = v18519; return Value(true); }()))) return Value(false); } return Value(true); }()); return v18511; }());
s->SetAt(4, v18510);
if (static_cast<bool>(([&]() -> Value { auto v18522 = s->LocalAt(4); if (!static_cast<bool>(v18522)) return v18522; v18522 = ([&]() -> Value { auto v18523 = s->LocalAt(5); Value v18524; v18524 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v18523, v18524))) return Value(false); v18523 = v18524; return Value(true); }()); if (!static_cast<bool>(v18522)) return v18522; v18522 = ([&]() -> Value { auto v18525 = ([&]() -> Value { auto fn18527 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args18528; args18528.Add(Value("market"), false); return CallDictionaryGet(c, fn18527, std::move(args18528)); }()); Value v18526; v18526 = List({List({Value("BUY_PRODUCT"), Value("WHEAT"), Value(int64_t{5})}), List({Value("BUY_PRODUCT"), Value("WHEAT"), Value(int64_t{10})}), List({Value("SELL"), Value("WHEAT"), Value(int64_t{60})})}); if (!static_cast<bool>(Binary("Eq", v18525, v18526))) return Value(false); v18525 = v18526; return Value(true); }()); return v18522; }()))) {
auto v18529 = ([&]() -> Value { auto fn18530 = s->Global("dict"); Arguments args18531; args18531.Add(s->LocalAt(0), false); args18531.Keyword("market", ([&]() -> Value { auto comp18532 = std::make_shared<Scope>(); comp18532->globals = s->globals; comp18532->parent = s; static constexpr const char* comp18532_names[] = {"o"}; comp18532->PrepareSlots(comp18532_names); auto result18533 = List(); for (const auto& item18534 : Iterate(s->Global("_OPEN_STEP0"))) { comp18532->SetAt(0, item18534); result18533.node()->sequence.push_back(([&]() -> Value { auto fn18535 = comp18532->Global("list"); Arguments args18536; args18536.Add(comp18532->LocalAt(0), false); return Call(c, fn18535, std::move(args18536)); }())); } return result18533; }())); return Call(c, fn18530, std::move(args18531)); }());
s->SetAt(0, v18529);
auto v18537 = s->Global("_OPEN_REPORT");
auto v18538 = Value("open_turns");
auto v18539 = Get(v18537, v18538);
Put(v18537, v18538, Inplace("Add", v18539, Value(int64_t{1})));
}
else {
if (static_cast<bool>(([&]() -> Value { auto v18540 = s->LocalAt(4); if (!static_cast<bool>(v18540)) return v18540; v18540 = ([&]() -> Value { auto v18541 = s->LocalAt(5); Value v18542; v18542 = Value(int64_t{1}); if (!static_cast<bool>(Binary("Eq", v18541, v18542))) return Value(false); v18541 = v18542; return Value(true); }()); return v18540; }()))) {
auto v18543 = ([&]() -> Value { auto comp18544 = std::make_shared<Scope>(); comp18544->globals = s->globals; comp18544->parent = s; static constexpr const char* comp18544_names[] = {"o"}; comp18544->PrepareSlots(comp18544_names); auto result18545 = List(); for (const auto& item18546 : Iterate(([&]() -> Value { auto fn18547 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args18548; args18548.positional.reserve(2); args18548.Add(Value("market"), false); args18548.Add(List({}), false); return CallDictionaryGet(c, fn18547, std::move(args18548)); }()))) { comp18544->SetAt(0, item18546); result18545.node()->sequence.push_back(([&]() -> Value { auto fn18549 = comp18544->Global("list"); Arguments args18550; args18550.Add(comp18544->LocalAt(0), false); return Call(c, fn18549, std::move(args18550)); }())); } return result18545; }());
s->SetAt(2, v18543);
if (static_cast<bool>(([&]() -> Value { auto v18551 = ([&]() -> Value { auto v18552 = ([&]() -> Value { auto fn18554 = s->Global("len"); Arguments args18555; args18555.Add(s->LocalAt(2), false); return Call(c, fn18554, std::move(args18555)); }()); Value v18553; v18553 = Value(int64_t{2}); if (!static_cast<bool>(Binary("GtE", v18552, v18553))) return Value(false); v18552 = v18553; return Value(true); }()); if (!static_cast<bool>(v18551)) return v18551; v18551 = ([&]() -> Value { auto v18556 = Get(s->LocalAt(2), Value(int64_t{0})); Value v18557; v18557 = List({Value("SELL"), Value("WHEAT"), Value(int64_t{13})}); if (!static_cast<bool>(Binary("Eq", v18556, v18557))) return Value(false); v18556 = v18557; return Value(true); }()); if (!static_cast<bool>(v18551)) return v18551; v18551 = ([&]() -> Value { auto v18558 = Get(s->LocalAt(2), Value(int64_t{1})); Value v18559; v18559 = List({Value("BUY_PRODUCT"), Value("WHEAT"), Value(int64_t{5})}); if (!static_cast<bool>(Binary("Eq", v18558, v18559))) return Value(false); v18558 = v18559; return Value(true); }()); return v18551; }()))) {
auto v18560 = Slice(s->LocalAt(2), Value(int64_t{2}), Value{}, Value{});
s->SetAt(2, v18560);
auto v18561 = s->Global("_OPEN_REPORT");
auto v18562 = Value("open_turns");
auto v18563 = Get(v18561, v18562);
Put(v18561, v18562, Inplace("Add", v18563, Value(int64_t{1})));
if (static_cast<bool>(([&]() -> Value { auto v18564 = s->Global("_OPEN_ATTACK"); if (!static_cast<bool>(v18564)) return v18564; v18564 = ([&]() -> Value { auto v18565 = ([&]() -> Value { auto fn18567 = s->Global("float"); Arguments args18568; args18568.Add(Get(Get(Get(s->LocalAt(3), Value("farms")), ([&]() -> Value { auto fn18569 = s->Global("int"); Arguments args18570; args18570.Add(Get(s->LocalAt(3), Value("player")), false); return Call(c, fn18569, std::move(args18570)); }())), Value("money")), false); return Call(c, fn18567, std::move(args18568)); }()); Value v18566; v18566 = s->Global("_OPEN_ATTACK_MIN_CASH"); if (!static_cast<bool>(Binary("GtE", v18565, v18566))) return Value(false); v18565 = v18566; return Value(true); }()); return v18564; }()))) {
auto v18571 = ([&]() -> Value { auto v18572 = List({List({Value("BUY_PRODUCT"), Value("WHEAT"), s->Global("_OPEN_ATTACK")})}); return Binary("Add", v18572, s->LocalAt(2)); }());
s->SetAt(2, v18571);
auto v18573 = Value(int64_t{1});
Put(s->Global("_OPEN_REPORT"), Value("open_attack"), v18573);
}
auto v18574 = ([&]() -> Value { auto fn18575 = s->Global("dict"); Arguments args18576; args18576.Add(s->LocalAt(0), false); args18576.Keyword("market", s->LocalAt(2)); return Call(c, fn18575, std::move(args18576)); }());
s->SetAt(0, v18574);
}
}
else {
if (static_cast<bool>(([&]() -> Value { auto v18577 = s->LocalAt(4); if (!static_cast<bool>(v18577)) return v18577; v18577 = ([&]() -> Value { auto v18578 = s->LocalAt(5); Value v18579; v18579 = Value(int64_t{2}); if (!static_cast<bool>(Binary("Eq", v18578, v18579))) return Value(false); v18578 = v18579; return Value(true); }()); if (!static_cast<bool>(v18577)) return v18577; v18577 = ([&]() -> Value { auto fn18580 = PrepareDictionaryGet(s->Global("_OPEN_REPORT")); Arguments args18581; args18581.Add(Value("open_attack"), false); return CallDictionaryGet(c, fn18580, std::move(args18581)); }()); return v18577; }()))) {
auto v18582 = ([&]() -> Value { auto fn18583 = s->Global("dict"); Arguments args18584; args18584.Add(s->LocalAt(0), false); args18584.Keyword("market", ([&]() -> Value { auto v18585 = List({List({Value("SELL"), Value("WHEAT"), s->Global("_OPEN_ATTACK")})}); return Binary("Add", v18585, Slice(([&]() -> Value { auto comp18586 = std::make_shared<Scope>(); comp18586->globals = s->globals; comp18586->parent = s; static constexpr const char* comp18586_names[] = {"o"}; comp18586->PrepareSlots(comp18586_names); auto result18587 = List(); for (const auto& item18588 : Iterate(([&]() -> Value { auto fn18589 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args18590; args18590.positional.reserve(2); args18590.Add(Value("market"), false); args18590.Add(List({}), false); return CallDictionaryGet(c, fn18589, std::move(args18590)); }()))) { comp18586->SetAt(0, item18588); result18587.node()->sequence.push_back(([&]() -> Value { auto fn18591 = comp18586->Global("list"); Arguments args18592; args18592.Add(comp18586->LocalAt(0), false); return Call(c, fn18591, std::move(args18592)); }())); } return result18587; }()), Value{}, Value(int64_t{9}), Value{})); }())); return Call(c, fn18583, std::move(args18584)); }());
s->SetAt(0, v18582);
auto v18593 = s->Global("_OPEN_REPORT");
auto v18594 = Value("open_turns");
auto v18595 = Get(v18593, v18594);
Put(v18593, v18594, Inplace("Add", v18595, Value(int64_t{1})));
}
}
}
} catch (const Error& error18502) {
if (Matches(error18502, s->Global("Exception"))) {
auto v18596 = s->Global("_OPEN_REPORT");
auto v18597 = Value("open_errors");
auto v18598 = Get(v18596, v18597);
Put(v18596, v18597, Inplace("Add", v18598, Value(int64_t{1})));
}
else { throw; }
}
(void)([&]() -> Value { auto fn18599 = Attribute(s->Global("_OPEN_REPORT"), "update"); Arguments args18600; args18600.Add(([&]() -> Value { auto fn18601 = s->Global("getattr"); Arguments args18602; args18602.positional.reserve(3); args18602.Add(s->Global("_OPEN_PARENT"), false); args18602.Add(Value("telemetry"), false); args18602.Add(([&]() -> Value { auto dict18603 = Dict(); return dict18603; }()), false); return Call(c, fn18601, std::move(args18602)); }()), false); return Call(c, fn18599, std::move(args18600)); }());
return s->LocalAt(0);
return {};
}
}  // namespace kagg::opponents::compiled
