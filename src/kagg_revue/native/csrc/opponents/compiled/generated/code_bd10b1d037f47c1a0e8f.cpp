// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_bd10b1d037f47c1a0e8f(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "actor", "blocked", "c", "commands", "demand", "farm", "kept", "obs", "pos", "private", "removed", "result", "valid"};
s->PrepareSlots(s_names);
auto v12328 = ([&]() -> Value { auto comp12329 = std::make_shared<Scope>(); comp12329->globals = s->globals; comp12329->parent = s; static constexpr const char* comp12329_names[] = {"c"}; comp12329->PrepareSlots(comp12329_names); auto result12330 = List(); for (const auto& item12331 : Iterate(([&]() -> Value { Arguments args12332; args12332.Add(([&]() -> Value { auto v12333 = ([&]() -> Value { auto fn12334 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args12335; args12335.Add(Value("farmer"), false); return CallDictionaryGet(c, fn12334, std::move(args12335)); }()); if (static_cast<bool>(v12333)) return v12333; v12333 = List({Value("PASS")}); return v12333; }()), false); args12332.Add(([&]() -> Value { auto v12336 = ([&]() -> Value { auto fn12337 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args12338; args12338.Add(Value("hands"), false); return CallDictionaryGet(c, fn12337, std::move(args12338)); }()); if (static_cast<bool>(v12336)) return v12336; v12336 = List({}); return v12336; }()), true); return List(std::move(args12332.positional)); }()))) { comp12329->SetAt(0, item12331); result12330.node()->sequence.push_back(([&]() -> Value { auto fn12339 = comp12329->Global("list"); Arguments args12340; args12340.Add(comp12329->LocalAt(0), false); return Call(c, fn12339, std::move(args12340)); }())); } return result12330; }());
s->SetAt(4, v12328);
auto v12341 = ([&]() -> Value { auto dict12342 = Dict(); return dict12342; }());
s->SetAt(5, v12341);
for (const auto& item12343 : Iterate(s->LocalAt(4))) {
s->SetAt(3, item12343);
if (static_cast<bool>(([&]() -> Value { auto v12344 = ([&]() -> Value { auto v12345 = ([&]() -> Value { auto fn12347 = s->Global("len"); Arguments args12348; args12348.Add(s->LocalAt(3), false); return Call(c, fn12347, std::move(args12348)); }()); Value v12346; v12346 = Value(int64_t{1}); if (!static_cast<bool>(Binary("Gt", v12345, v12346))) return Value(false); v12345 = v12346; return Value(true); }()); if (!static_cast<bool>(v12344)) return v12344; v12344 = ([&]() -> Value { auto v12349 = Get(s->LocalAt(3), Value(int64_t{0})); Value v12350; v12350 = Value("PLANT"); if (!static_cast<bool>(Binary("Eq", v12349, v12350))) return Value(false); v12349 = v12350; return Value(true); }()); return v12344; }()))) {
auto v12351 = ([&]() -> Value { auto v12352 = ([&]() -> Value { auto fn12353 = PrepareDictionaryGet(s->LocalAt(5)); Arguments args12354; args12354.positional.reserve(2); args12354.Add(Get(s->LocalAt(3), Value(int64_t{1})), false); args12354.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn12353, std::move(args12354)); }()); return Binary("Add", v12352, Value(int64_t{1})); }());
Put(s->LocalAt(5), Get(s->LocalAt(3), Value(int64_t{1})), v12351);
}
}
auto v12355 = ([&]() -> Value { auto comp12356 = std::make_shared<Scope>(); comp12356->globals = s->globals; comp12356->parent = s; static constexpr const char* comp12356_names[] = {"n", "p"}; comp12356->PrepareSlots(comp12356_names); auto result12357 = List(); for (const auto& item12358 : Iterate(([&]() -> Value { auto fn12359 = Attribute(s->LocalAt(5), "items"); Arguments args12360; return Call(c, fn12359, std::move(args12360)); }()))) { auto unpack12361 = Iterate(item12358); ValidateUnpack(unpack12361, 2, false); comp12356->SetAt(1, unpack12361.at(0)); comp12356->SetAt(0, unpack12361.at(1)); if (!static_cast<bool>(([&]() -> Value { auto v12362 = comp12356->LocalAt(0); Value v12363; v12363 = ([&]() -> Value { auto fn12364 = PrepareDictionaryGet(Get(Get(comp12356->Captured("obs"), Value("private")), Value("seeds"))); Arguments args12365; args12365.positional.reserve(2); args12365.Add(comp12356->LocalAt(1), false); args12365.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn12364, std::move(args12365)); }()); if (!static_cast<bool>(Binary("Gt", v12362, v12363))) return Value(false); v12362 = v12363; return Value(true); }()))) continue; result12357.node()->sequence.push_back(comp12356->LocalAt(1)); } return Set(result12357.node()->sequence); }());
s->SetAt(2, v12355);
if (static_cast<bool>(Unary("Not", s->LocalAt(2)))) {
return s->LocalAt(0);
}
auto v12366 = ([&]() -> Value { auto fn12367 = Get(s->Global("_PLANNER_NS"), Value("_clone_state")); Arguments args12368; args12368.positional.reserve(2); args12368.Add(Get(Get(s->LocalAt(8), Value("farms")), Get(s->LocalAt(8), Value("player"))), false); args12368.Add(Get(s->LocalAt(8), Value("private")), false); return Call(c, fn12367, std::move(args12368)); }());
auto unpack12369 = Iterate(v12366);
ValidateUnpack(unpack12369, 2, false);
s->SetAt(6, unpack12369.at(0));
s->SetAt(10, unpack12369.at(1));
auto v12370 = Value(int64_t{0});
s->SetAt(7, v12370);
s->SetAt(11, v12370);
for (const auto& item12371 : Iterate(([&]() -> Value { auto fn12372 = s->Global("enumerate"); Arguments args12373; args12373.Add(s->LocalAt(4), false); return Call(c, fn12372, std::move(args12373)); }()))) {
auto unpack12374 = Iterate(item12371);
ValidateUnpack(unpack12374, 2, false);
s->SetAt(1, unpack12374.at(0));
s->SetAt(3, unpack12374.at(1));
if (static_cast<bool>(([&]() -> Value { auto v12375 = ([&]() -> Value { auto v12376 = ([&]() -> Value { auto fn12378 = s->Global("len"); Arguments args12379; args12379.Add(s->LocalAt(3), false); return Call(c, fn12378, std::move(args12379)); }()); Value v12377; v12377 = Value(int64_t{1}); if (!static_cast<bool>(Binary("Gt", v12376, v12377))) return Value(false); v12376 = v12377; return Value(true); }()); if (!static_cast<bool>(v12375)) return v12375; v12375 = ([&]() -> Value { auto v12380 = Get(s->LocalAt(3), Value(int64_t{0})); Value v12381; v12381 = Value("PLANT"); if (!static_cast<bool>(Binary("Eq", v12380, v12381))) return Value(false); v12380 = v12381; return Value(true); }()); if (!static_cast<bool>(v12375)) return v12375; v12375 = ([&]() -> Value { auto v12382 = Get(s->LocalAt(3), Value(int64_t{1})); Value v12383; v12383 = s->LocalAt(2); if (!static_cast<bool>(Binary("In", v12382, v12383))) return Value(false); v12382 = v12383; return Value(true); }()); return v12375; }()))) {
auto v12384 = (static_cast<bool>(([&]() -> Value { auto v12385 = s->LocalAt(1); Value v12386; v12386 = ([&]() -> Value { auto fn12387 = s->Global("len"); Arguments args12388; args12388.Add(Get(s->LocalAt(10), Value("inventories")), false); return Call(c, fn12387, std::move(args12388)); }()); if (!static_cast<bool>(Binary("GtE", v12385, v12386))) return Value(false); v12385 = v12386; return Value(true); }())) ? Value{} : (static_cast<bool>(([&]() -> Value { auto v12389 = s->LocalAt(1); Value v12390; v12390 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v12389, v12390))) return Value(false); v12389 = v12390; return Value(true); }())) ? Get(s->LocalAt(6), Value("farmer")) : Get(Get(s->LocalAt(6), Value("hands")), ([&]() -> Value { auto v12391 = s->LocalAt(1); return Binary("Sub", v12391, Value(int64_t{1})); }()))));
s->SetAt(9, v12384);
auto v12392 = ([&]() -> Value { auto v12393 = ([&]() -> Value { auto v12394 = s->LocalAt(9); Value v12395; v12395 = Value{}; if (!static_cast<bool>(Binary("IsNot", v12394, v12395))) return Value(false); v12394 = v12395; return Value(true); }()); if (!static_cast<bool>(v12393)) return v12393; v12393 = ([&]() -> Value { auto v12396 = Get(Get(Get(s->LocalAt(6), Value("tiles")), Get(s->LocalAt(9), Value(int64_t{1}))), Get(s->LocalAt(9), Value(int64_t{0}))); Value v12397; v12397 = Value{}; if (!static_cast<bool>(Binary("Is", v12396, v12397))) return Value(false); v12396 = v12397; return Value(true); }()); if (!static_cast<bool>(v12393)) return v12393; v12393 = ([&]() -> Value { auto v12398 = ([&]() -> Value { auto fn12400 = PrepareDictionaryGet(Get(s->LocalAt(10), Value("seeds"))); Arguments args12401; args12401.positional.reserve(2); args12401.Add(Get(s->LocalAt(3), Value(int64_t{1})), false); args12401.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn12400, std::move(args12401)); }()); Value v12399; v12399 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v12398, v12399))) return Value(false); v12398 = v12399; return Value(true); }()); return v12393; }());
s->SetAt(13, v12392);
if (static_cast<bool>(Unary("Not", s->LocalAt(13)))) {
auto v12402 = List({Value("PASS")});
Put(s->LocalAt(4), s->LocalAt(1), v12402);
auto v12403 = s->LocalAt(11);
s->SetAt(11, Inplace("Add", v12403, Value(int64_t{1})));
}
else {
auto v12404 = s->LocalAt(7);
s->SetAt(7, Inplace("Add", v12404, Value(int64_t{1})));
}
}
if (static_cast<bool>(([&]() -> Value { auto v12405 = s->LocalAt(1); Value v12406; v12406 = ([&]() -> Value { auto fn12407 = s->Global("len"); Arguments args12408; args12408.Add(Get(s->LocalAt(10), Value("inventories")), false); return Call(c, fn12407, std::move(args12408)); }()); if (!static_cast<bool>(Binary("Lt", v12405, v12406))) return Value(false); v12405 = v12406; return Value(true); }()))) {
(void)([&]() -> Value { auto fn12409 = Get(s->Global("_PLANNER_NS"), Value("_apply_unit_action")); Arguments args12410; args12410.positional.reserve(8); args12410.Add(s->LocalAt(6), false); args12410.Add(s->LocalAt(10), false); args12410.Add(s->LocalAt(1), false); args12410.Add(Get(s->LocalAt(4), s->LocalAt(1)), false); args12410.Add(Value(int64_t{10}), false); args12410.Add(([&]() -> Value { auto v12411 = ([&]() -> Value { auto fn12412 = s->Global("int"); Arguments args12413; args12413.Add(Get(s->LocalAt(8), Value("step")), false); return Call(c, fn12412, std::move(args12413)); }()); return Binary("FloorDiv", v12411, Value(int64_t{24})); }()), false); args12410.Add(Value(int64_t{24}), false); args12410.Add(Value(int64_t{100}), false); return Call(c, fn12409, std::move(args12410)); }());
}
}
if (static_cast<bool>(Unary("Not", s->LocalAt(11)))) {
return s->LocalAt(0);
}
auto v12414 = ([&]() -> Value { auto fn12415 = s->Global("dict"); Arguments args12416; args12416.Add(s->LocalAt(0), false); args12416.Keyword("farmer", Get(s->LocalAt(4), Value(int64_t{0}))); args12416.Keyword("hands", Slice(s->LocalAt(4), Value(int64_t{1}), Value{}, Value{})); return Call(c, fn12415, std::move(args12416)); }());
s->SetAt(12, v12414);
auto v12417 = ([&]() -> Value { auto fn12418 = s->Global("_r127_last_hour"); Arguments args12419; args12419.positional.reserve(2); args12419.Add(s->LocalAt(8), false); args12419.Add(s->LocalAt(12), false); return Call(c, fn12418, std::move(args12419)); }());
s->SetAt(12, v12417);
auto v12420 = s->Global("_R148_REPORT");
auto v12421 = Value("atomic_turns");
auto v12422 = Get(v12420, v12421);
Put(v12420, v12421, Inplace("Add", v12422, Value(int64_t{1})));
auto v12423 = s->Global("_R148_REPORT");
auto v12424 = Value("atomic_kept_requests");
auto v12425 = Get(v12423, v12424);
Put(v12423, v12424, Inplace("Add", v12425, s->LocalAt(7)));
auto v12426 = s->Global("_R148_REPORT");
auto v12427 = Value("atomic_removed_requests");
auto v12428 = Get(v12426, v12427);
Put(v12426, v12427, Inplace("Add", v12428, s->LocalAt(11)));
return s->LocalAt(12);
return {};
}
}  // namespace kagg::opponents::compiled
