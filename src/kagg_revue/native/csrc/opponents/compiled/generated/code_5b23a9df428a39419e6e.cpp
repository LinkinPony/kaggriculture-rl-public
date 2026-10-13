// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_5b23a9df428a39419e6e(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "configuration", "farms", "observation", "own", "player", "rival", "snapshot", "standard", "state", "step"};
s->PrepareSlots(s_names);
auto v18349 = Value{};
s->SetAt(9, v18349);
try {
auto v18351 = ([&]() -> Value { auto fn18352 = s->Global("int"); Arguments args18353; args18353.Add(Get(s->LocalAt(3), Value("player")), false); return Call(c, fn18352, std::move(args18353)); }());
s->SetAt(5, v18351);
auto v18354 = ([&]() -> Value { auto fn18355 = s->Global("int"); Arguments args18356; args18356.Add(Get(s->LocalAt(3), Value("step")), false); return Call(c, fn18355, std::move(args18356)); }());
s->SetAt(10, v18354);
auto v18357 = ([&]() -> Value { auto fn18358 = PrepareDictionaryGet(s->Global("_RACE_STATE")); Arguments args18359; args18359.Add(s->LocalAt(5), false); return CallDictionaryGet(c, fn18358, std::move(args18359)); }());
s->SetAt(9, v18357);
if (static_cast<bool>(([&]() -> Value { auto v18360 = ([&]() -> Value { auto v18361 = s->LocalAt(9); Value v18362; v18362 = Value{}; if (!static_cast<bool>(Binary("Is", v18361, v18362))) return Value(false); v18361 = v18362; return Value(true); }()); if (static_cast<bool>(v18360)) return v18360; v18360 = ([&]() -> Value { auto v18363 = s->LocalAt(10); Value v18364; v18364 = Get(s->LocalAt(9), Value("step")); if (!static_cast<bool>(Binary("LtE", v18363, v18364))) return Value(false); v18363 = v18364; return Value(true); }()); return v18360; }()))) {
auto v18365 = ([&]() -> Value { auto dict18366 = Dict(); auto key18367 = Value("step"); Put(dict18366, key18367, Unary("USub", Value(int64_t{1}))); auto key18368 = Value("hist"); Put(dict18366, key18368, List({})); auto key18369 = Value("horizon"); Put(dict18366, key18369, Value(int64_t{0})); auto key18370 = Value("level"); Put(dict18366, key18370, s->Global("_RACE_HORIZON_CLONE")); auto key18371 = Value("prev"); Put(dict18366, key18371, Value{}); auto key18372 = Value("prev_action"); Put(dict18366, key18372, Value{}); return dict18366; }());
s->SetAt(9, v18365);
Put(s->Global("_RACE_STATE"), s->LocalAt(5), v18365);
}
if (static_cast<bool>(([&]() -> Value { auto v18373 = s->LocalAt(10); Value v18374; v18374 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v18373, v18374))) return Value(false); v18373 = v18374; return Value(true); }()))) {
(void)([&]() -> Value { auto fn18375 = Attribute(s->Global("_RACE_REPORT"), "update"); Arguments args18376; args18376.Keyword("race_clone_turns", Value(int64_t{0})); args18376.Keyword("race_horizon_turns", Value(int64_t{0})); args18376.Keyword("race_lost_races", Value(int64_t{0})); args18376.Keyword("race_escalations", Value(int64_t{0})); args18376.Keyword("race_errors", Value(int64_t{0})); return Call(c, fn18375, std::move(args18376)); }());
}
auto v18377 = s->LocalAt(10);
Put(s->LocalAt(9), Value("step"), v18377);
auto v18378 = Value(int64_t{0});
Put(s->LocalAt(9), Value("horizon"), v18378);
if (static_cast<bool>(([&]() -> Value { auto v18379 = s->LocalAt(10); Value v18380; v18380 = Value(int64_t{1}); if (!static_cast<bool>(Binary("Eq", v18379, v18380))) return Value(false); v18379 = v18380; return Value(true); }()))) {
try {
auto v18382 = Get(s->LocalAt(3), Value("farms"));
s->SetAt(2, v18382);
auto v18383 = Get(Get(s->LocalAt(2), ([&]() -> Value { auto v18384 = Value(int64_t{1}); return Binary("Sub", v18384, s->LocalAt(5)); }())), Value("money"));
s->SetAt(6, v18383);
auto v18385 = Get(Get(s->LocalAt(2), s->LocalAt(5)), Value("money"));
s->SetAt(4, v18385);
auto v18386 = (static_cast<bool>(([&]() -> Value { auto v18387 = ([&]() -> Value { auto v18388 = ([&]() -> Value { auto fn18390 = s->Global("abs"); Arguments args18391; args18391.Add(([&]() -> Value { auto v18392 = ([&]() -> Value { auto fn18393 = s->Global("float"); Arguments args18394; args18394.Add(s->LocalAt(6), false); return Call(c, fn18393, std::move(args18394)); }()); return Binary("Sub", v18392, ([&]() -> Value { auto fn18395 = s->Global("float"); Arguments args18396; args18396.Add(s->LocalAt(4), false); return Call(c, fn18395, std::move(args18396)); }())); }()), false); return Call(c, fn18390, std::move(args18391)); }()); Value v18389; v18389 = Value(0.5); if (!static_cast<bool>(Binary("Lt", v18388, v18389))) return Value(false); v18388 = v18389; return Value(true); }()); if (!static_cast<bool>(v18387)) return v18387; v18387 = ([&]() -> Value { auto v18397 = s->Global("_RACE_HORIZON_MIRROR"); Value v18398; v18398 = Get(s->LocalAt(9), Value("level")); if (!static_cast<bool>(Binary("Gt", v18397, v18398))) return Value(false); v18397 = v18398; return Value(true); }()); return v18387; }())) ? s->Global("_RACE_HORIZON_MIRROR") : Get(s->LocalAt(9), Value("level")));
Put(s->LocalAt(9), Value("level"), v18386);
auto v18399 = ([&]() -> Value { auto fn18400 = s->Global("int"); Arguments args18401; args18401.Add(([&]() -> Value { auto v18402 = ([&]() -> Value { auto fn18404 = s->Global("abs"); Arguments args18405; args18405.Add(([&]() -> Value { auto v18406 = ([&]() -> Value { auto fn18407 = s->Global("float"); Arguments args18408; args18408.Add(s->LocalAt(6), false); return Call(c, fn18407, std::move(args18408)); }()); return Binary("Sub", v18406, ([&]() -> Value { auto fn18409 = s->Global("float"); Arguments args18410; args18410.Add(s->LocalAt(4), false); return Call(c, fn18409, std::move(args18410)); }())); }()), false); return Call(c, fn18404, std::move(args18405)); }()); Value v18403; v18403 = Value(0.5); if (!static_cast<bool>(Binary("Lt", v18402, v18403))) return Value(false); v18402 = v18403; return Value(true); }()), false); return Call(c, fn18400, std::move(args18401)); }());
Put(s->Global("_RACE_REPORT"), Value("race_mirror"), v18399);
} catch (const Error& error18381) {
if (Matches(error18381, s->Global("Exception"))) {
auto v18411 = s->Global("_RACE_REPORT");
auto v18412 = Value("race_errors");
auto v18413 = Get(v18411, v18412);
Put(v18411, v18412, Inplace("Add", v18413, Value(int64_t{1})));
}
else { throw; }
}
}
auto v18414 = ([&]() -> Value { auto v18415 = ([&]() -> Value { auto v18416 = s->LocalAt(1); Value v18417; v18417 = Value{}; if (!static_cast<bool>(Binary("Is", v18416, v18417))) return Value(false); v18416 = v18417; return Value(true); }()); if (static_cast<bool>(v18415)) return v18415; v18415 = ([&]() -> Value { auto comp18418 = std::make_shared<Scope>(); comp18418->globals = s->globals; comp18418->parent = s; static constexpr const char* comp18418_names[] = {"k", "v"}; comp18418->PrepareSlots(comp18418_names); auto result18419 = List(); for (const auto& item18420 : Iterate(List({Tuple({Value("boardSize"), Value(int64_t{10})}), Tuple({Value("turnsPerDay"), Value(int64_t{24})}), Tuple({Value("shedCapacity"), Value(int64_t{100})}), Tuple({Value("maxMarketOrdersPerTurn"), Value(int64_t{10})})}))) { auto unpack18421 = Iterate(item18420); ValidateUnpack(unpack18421, 2, false); comp18418->SetAt(0, unpack18421.at(0)); comp18418->SetAt(1, unpack18421.at(1)); if (!static_cast<bool>(([&]() -> Value { auto v18422 = ([&]() -> Value { auto fn18424 = PrepareDictionaryGet(comp18418->Captured("configuration")); Arguments args18425; args18425.positional.reserve(2); args18425.Add(comp18418->LocalAt(0), false); args18425.Add(comp18418->LocalAt(1), false); return CallDictionaryGet(c, fn18424, std::move(args18425)); }()); Value v18423; v18423 = comp18418->LocalAt(1); if (!static_cast<bool>(Binary("Eq", v18422, v18423))) return Value(false); v18422 = v18423; return Value(true); }()))) return Value(false); } return Value(true); }()); return v18415; }());
s->SetAt(8, v18414);
if (static_cast<bool>(([&]() -> Value { auto v18426 = s->LocalAt(8); if (!static_cast<bool>(v18426)) return v18426; v18426 = ([&]() -> Value { auto v18427 = Value(int64_t{216}); Value v18428; v18428 = s->LocalAt(10); if (!static_cast<bool>(Binary("LtE", v18427, v18428))) return Value(false); v18427 = v18428; v18428 = Value(int64_t{696}); if (!static_cast<bool>(Binary("Lt", v18427, v18428))) return Value(false); v18427 = v18428; return Value(true); }()); if (!static_cast<bool>(v18426)) return v18426; v18426 = ([&]() -> Value { auto fn18429 = s->Global("_race_clone"); Arguments args18430; args18430.positional.reserve(2); args18430.Add(s->LocalAt(3), false); args18430.Add(s->LocalAt(9), false); return Call(c, fn18429, std::move(args18430)); }()); return v18426; }()))) {
auto v18431 = s->Global("_RACE_REPORT");
auto v18432 = Value("race_clone_turns");
auto v18433 = Get(v18431, v18432);
Put(v18431, v18432, Inplace("Add", v18433, Value(int64_t{1})));
if (static_cast<bool>(([&]() -> Value { auto v18434 = ([&]() -> Value { auto v18435 = Get(s->LocalAt(9), Value("level")); Value v18436; v18436 = s->Global("_RACE_HORIZON_ESCALATED"); if (!static_cast<bool>(Binary("Lt", v18435, v18436))) return Value(false); v18435 = v18436; return Value(true); }()); if (!static_cast<bool>(v18434)) return v18434; v18434 = ([&]() -> Value { auto fn18437 = s->Global("_race_lost"); Arguments args18438; args18438.positional.reserve(2); args18438.Add(s->LocalAt(3), false); args18438.Add(s->LocalAt(9), false); return Call(c, fn18437, std::move(args18438)); }()); return v18434; }()))) {
auto v18439 = s->Global("_RACE_REPORT");
auto v18440 = Value("race_lost_races");
auto v18441 = Get(v18439, v18440);
Put(v18439, v18440, Inplace("Add", v18441, Value(int64_t{1})));
auto v18442 = s->Global("_RACE_HORIZON_ESCALATED");
Put(s->LocalAt(9), Value("level"), v18442);
auto v18443 = s->Global("_RACE_REPORT");
auto v18444 = Value("race_escalations");
auto v18445 = Get(v18443, v18444);
Put(v18443, v18444, Inplace("Add", v18445, Value(int64_t{1})));
}
auto v18446 = Get(s->LocalAt(9), Value("level"));
Put(s->LocalAt(9), Value("horizon"), v18446);
auto v18447 = s->Global("_RACE_REPORT");
auto v18448 = Value("race_horizon_turns");
auto v18449 = Get(v18447, v18448);
Put(v18447, v18448, Inplace("Add", v18449, Value(int64_t{1})));
}
} catch (const Error& error18350) {
if (Matches(error18350, s->Global("Exception"))) {
auto v18450 = s->Global("_RACE_REPORT");
auto v18451 = Value("race_errors");
auto v18452 = Get(v18450, v18451);
Put(v18450, v18451, Inplace("Add", v18452, Value(int64_t{1})));
}
else { throw; }
}
auto v18453 = Value{};
s->SetAt(7, v18453);
try {
if (static_cast<bool>(([&]() -> Value { auto v18455 = ([&]() -> Value { auto v18456 = s->LocalAt(9); Value v18457; v18457 = Value{}; if (!static_cast<bool>(Binary("IsNot", v18456, v18457))) return Value(false); v18456 = v18457; return Value(true); }()); if (!static_cast<bool>(v18455)) return v18455; v18455 = ([&]() -> Value { auto v18458 = Value(int64_t{215}); Value v18459; v18459 = ([&]() -> Value { auto fn18460 = s->Global("int"); Arguments args18461; args18461.Add(Get(s->LocalAt(3), Value("step")), false); return Call(c, fn18460, std::move(args18461)); }()); if (!static_cast<bool>(Binary("LtE", v18458, v18459))) return Value(false); v18458 = v18459; v18459 = Value(int64_t{696}); if (!static_cast<bool>(Binary("Lt", v18458, v18459))) return Value(false); v18458 = v18459; return Value(true); }()); return v18455; }()))) {
auto v18462 = ([&]() -> Value { auto fn18463 = s->Global("_race_snapshot"); Arguments args18464; args18464.Add(s->LocalAt(3), false); return Call(c, fn18463, std::move(args18464)); }());
s->SetAt(7, v18462);
}
} catch (const Error& error18454) {
if (Matches(error18454, s->Global("Exception"))) {
auto v18465 = s->Global("_RACE_REPORT");
auto v18466 = Value("race_errors");
auto v18467 = Get(v18465, v18466);
Put(v18465, v18466, Inplace("Add", v18467, Value(int64_t{1})));
}
else { throw; }
}
auto v18468 = ([&]() -> Value { auto fn18469 = s->Global("_RACE_PARENT"); Arguments args18470; args18470.positional.reserve(2); args18470.Add(s->LocalAt(3), false); args18470.Add(s->LocalAt(1), false); return Call(c, fn18469, std::move(args18470)); }());
s->SetAt(0, v18468);
try {
if (static_cast<bool>(([&]() -> Value { auto v18472 = s->LocalAt(9); Value v18473; v18473 = Value{}; if (!static_cast<bool>(Binary("IsNot", v18472, v18473))) return Value(false); v18472 = v18473; return Value(true); }()))) {
auto v18474 = s->LocalAt(7);
Put(s->LocalAt(9), Value("prev"), v18474);
auto v18475 = (static_cast<bool>(([&]() -> Value { auto v18476 = s->LocalAt(7); Value v18477; v18477 = Value{}; if (!static_cast<bool>(Binary("IsNot", v18476, v18477))) return Value(false); v18476 = v18477; return Value(true); }())) ? s->LocalAt(0) : Value{});
Put(s->LocalAt(9), Value("prev_action"), v18475);
}
} catch (const Error& error18471) {
if (Matches(error18471, s->Global("Exception"))) {
auto v18478 = s->Global("_RACE_REPORT");
auto v18479 = Value("race_errors");
auto v18480 = Get(v18478, v18479);
Put(v18478, v18479, Inplace("Add", v18480, Value(int64_t{1})));
}
else { throw; }
}
(void)([&]() -> Value { auto fn18481 = Attribute(s->Global("_RACE_REPORT"), "update"); Arguments args18482; args18482.Add(([&]() -> Value { auto fn18483 = s->Global("getattr"); Arguments args18484; args18484.positional.reserve(3); args18484.Add(s->Global("_RACE_PARENT"), false); args18484.Add(Value("telemetry"), false); args18484.Add(([&]() -> Value { auto dict18485 = Dict(); return dict18485; }()), false); return Call(c, fn18483, std::move(args18484)); }()), false); return Call(c, fn18481, std::move(args18482)); }());
return s->LocalAt(0);
return {};
}
}  // namespace kagg::opponents::compiled
