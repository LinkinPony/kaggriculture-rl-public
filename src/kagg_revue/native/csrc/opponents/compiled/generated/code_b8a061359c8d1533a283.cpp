// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_b8a061359c8d1533a283(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"_", "access", "act", "action", "board", "cmd", "dx", "dy", "farm", "half", "i", "nx", "ny", "obs", "occ", "out", "p", "positions", "seat", "step", "t", "units"};
s->PrepareSlots(s_names);
auto v23373 = ([&]() -> Value { auto fn23374 = s->Global("int"); Arguments args23375; args23375.Add(Get(s->LocalAt(13), Value("player")), false); return Call(c, fn23374, std::move(args23375)); }());
s->SetAt(18, v23373);
auto v23376 = ([&]() -> Value { auto fn23377 = s->Global("int"); Arguments args23378; args23378.Add(Get(s->LocalAt(13), Value("step")), false); return Call(c, fn23377, std::move(args23378)); }());
s->SetAt(19, v23376);
auto v23379 = Get(Get(s->LocalAt(13), Value("farms")), s->LocalAt(18));
s->SetAt(8, v23379);
auto v23380 = ([&]() -> Value { auto fn23381 = s->Global("len"); Arguments args23382; args23382.Add(Get(s->LocalAt(8), Value("tiles")), false); return Call(c, fn23381, std::move(args23382)); }());
s->SetAt(4, v23380);
auto v23383 = ([&]() -> Value { auto v23384 = s->LocalAt(4); return Binary("FloorDiv", v23384, Value(int64_t{2})); }());
s->SetAt(9, v23383);
auto v23385 = List({Tuple({([&]() -> Value { auto v23386 = s->LocalAt(9); return Binary("Sub", v23386, Value(int64_t{1})); }()), ([&]() -> Value { auto v23387 = s->LocalAt(9); return Binary("Sub", v23387, Value(int64_t{1})); }())}), Tuple({s->LocalAt(9), ([&]() -> Value { auto v23388 = s->LocalAt(9); return Binary("Sub", v23388, Value(int64_t{1})); }())}), Tuple({([&]() -> Value { auto v23389 = s->LocalAt(9); return Binary("Sub", v23389, Value(int64_t{1})); }()), s->LocalAt(9)}), Tuple({s->LocalAt(9), s->LocalAt(9)})});
s->SetAt(1, v23385);
auto v23390 = ([&]() -> Value { auto v23391 = List({([&]() -> Value { auto fn23392 = s->Global("list"); Arguments args23393; args23393.Add(Get(s->LocalAt(8), Value("farmer")), false); return Call(c, fn23392, std::move(args23393)); }())}); return Binary("Add", v23391, ([&]() -> Value { auto comp23394 = std::make_shared<Scope>(); comp23394->globals = s->globals; comp23394->parent = s; static constexpr const char* comp23394_names[] = {"h"}; comp23394->PrepareSlots(comp23394_names); auto result23395 = List(); for (const auto& item23396 : Iterate(Get(s->LocalAt(8), Value("hands")))) { comp23394->SetAt(0, item23396); result23395.node()->sequence.push_back(([&]() -> Value { auto fn23397 = comp23394->Global("list"); Arguments args23398; args23398.Add(comp23394->LocalAt(0), false); return Call(c, fn23397, std::move(args23398)); }())); } return result23395; }())); }());
s->SetAt(17, v23390);
auto v23399 = ([&]() -> Value { auto dict23400 = Dict(); return dict23400; }());
s->SetAt(15, v23399);
for (const auto& item23401 : Iterate(([&]() -> Value { auto fn23402 = s->Global("range"); Arguments args23403; args23403.positional.reserve(2); args23403.Add(s->LocalAt(19), false); args23403.Add(([&]() -> Value { auto v23404 = ([&]() -> Value { auto v23405 = ([&]() -> Value { auto v23406 = s->LocalAt(19); return Binary("FloorDiv", v23406, Value(int64_t{24})); }()); return Binary("Add", v23405, Value(int64_t{1})); }()); return Binary("Mult", v23404, Value(int64_t{24})); }()), false); return Call(c, fn23402, std::move(args23403)); }()))) {
s->SetAt(20, item23401);
auto v23407 = (static_cast<bool>(([&]() -> Value { auto v23408 = s->LocalAt(20); Value v23409; v23409 = s->LocalAt(19); if (!static_cast<bool>(Binary("Eq", v23408, v23409))) return Value(false); v23408 = v23409; return Value(true); }())) ? s->LocalAt(3) : ([&]() -> Value { auto fn23410 = s->Global("_ch_tape"); Arguments args23411; args23411.positional.reserve(2); args23411.Add(s->LocalAt(18), false); args23411.Add(s->LocalAt(20), false); return Call(c, fn23410, std::move(args23411)); }()));
s->SetAt(2, v23407);
auto v23412 = ([&]() -> Value { auto v23413 = List({([&]() -> Value { auto v23414 = ([&]() -> Value { auto fn23415 = PrepareDictionaryGet(s->LocalAt(2)); Arguments args23416; args23416.Add(Value("farmer"), false); return CallDictionaryGet(c, fn23415, std::move(args23416)); }()); if (static_cast<bool>(v23414)) return v23414; v23414 = List({Value("PASS")}); return v23414; }())}); return Binary("Add", v23413, ([&]() -> Value { auto fn23417 = s->Global("list"); Arguments args23418; args23418.Add(([&]() -> Value { auto v23419 = ([&]() -> Value { auto fn23420 = PrepareDictionaryGet(s->LocalAt(2)); Arguments args23421; args23421.Add(Value("hands"), false); return CallDictionaryGet(c, fn23420, std::move(args23421)); }()); if (static_cast<bool>(v23419)) return v23419; v23419 = List({}); return v23419; }()), false); return Call(c, fn23417, std::move(args23418)); }())); }());
s->SetAt(21, v23412);
for (const auto& item23422 : Iterate(([&]() -> Value { auto fn23423 = s->Global("range"); Arguments args23424; args23424.Add(([&]() -> Value { auto fn23425 = s->Global("len"); Arguments args23426; args23426.Add(s->LocalAt(17), false); return Call(c, fn23425, std::move(args23426)); }()), false); return Call(c, fn23423, std::move(args23424)); }()))) {
s->SetAt(10, item23422);
auto v23427 = (static_cast<bool>(([&]() -> Value { auto v23428 = ([&]() -> Value { auto v23429 = s->LocalAt(10); Value v23430; v23430 = ([&]() -> Value { auto fn23431 = s->Global("len"); Arguments args23432; args23432.Add(s->LocalAt(21), false); return Call(c, fn23431, std::move(args23432)); }()); if (!static_cast<bool>(Binary("Lt", v23429, v23430))) return Value(false); v23429 = v23430; return Value(true); }()); if (!static_cast<bool>(v23428)) return v23428; v23428 = Get(s->LocalAt(21), s->LocalAt(10)); return v23428; }())) ? Get(s->LocalAt(21), s->LocalAt(10)) : List({Value("PASS")}));
s->SetAt(5, v23427);
if (static_cast<bool>(([&]() -> Value { auto v23433 = Get(s->LocalAt(5), Value(int64_t{0})); Value v23434; v23434 = s->Global("_CH_MOVES"); if (!static_cast<bool>(Binary("In", v23433, v23434))) return Value(false); v23433 = v23434; return Value(true); }()))) {
auto v23435 = Get(s->Global("_CH_MOVES"), Get(s->LocalAt(5), Value(int64_t{0})));
auto unpack23436 = Iterate(v23435);
ValidateUnpack(unpack23436, 2, false);
s->SetAt(6, unpack23436.at(0));
s->SetAt(7, unpack23436.at(1));
auto v23437 = Tuple({([&]() -> Value { auto v23438 = Get(Get(s->LocalAt(17), s->LocalAt(10)), Value(int64_t{0})); return Binary("Add", v23438, s->LocalAt(6)); }()), ([&]() -> Value { auto v23439 = Get(Get(s->LocalAt(17), s->LocalAt(10)), Value(int64_t{1})); return Binary("Add", v23439, s->LocalAt(7)); }())});
auto unpack23440 = Iterate(v23437);
ValidateUnpack(unpack23440, 2, false);
s->SetAt(11, unpack23440.at(0));
s->SetAt(12, unpack23440.at(1));
if (static_cast<bool>(([&]() -> Value { auto v23441 = ([&]() -> Value { auto v23442 = Value(int64_t{0}); Value v23443; v23443 = s->LocalAt(11); if (!static_cast<bool>(Binary("LtE", v23442, v23443))) return Value(false); v23442 = v23443; v23443 = s->LocalAt(4); if (!static_cast<bool>(Binary("Lt", v23442, v23443))) return Value(false); v23442 = v23443; return Value(true); }()); if (!static_cast<bool>(v23441)) return v23441; v23441 = ([&]() -> Value { auto v23444 = Value(int64_t{0}); Value v23445; v23445 = s->LocalAt(12); if (!static_cast<bool>(Binary("LtE", v23444, v23445))) return Value(false); v23444 = v23445; v23445 = s->LocalAt(4); if (!static_cast<bool>(Binary("Lt", v23444, v23445))) return Value(false); v23444 = v23445; return Value(true); }()); return v23441; }()))) {
auto v23446 = List({s->LocalAt(11), s->LocalAt(12)});
Put(s->LocalAt(17), s->LocalAt(10), v23446);
}
}
else {
if (static_cast<bool>(([&]() -> Value { auto v23447 = s->LocalAt(20); Value v23448; v23448 = s->LocalAt(19); if (!static_cast<bool>(Binary("Gt", v23447, v23448))) return Value(false); v23447 = v23448; return Value(true); }()))) {
(void)([&]() -> Value { auto fn23449 = Attribute(([&]() -> Value { auto fn23451 = Attribute(s->LocalAt(15), "setdefault"); Arguments args23452; args23452.positional.reserve(2); args23452.Add(([&]() -> Value { auto fn23453 = s->Global("tuple"); Arguments args23454; args23454.Add(Get(s->LocalAt(17), s->LocalAt(10)), false); return Call(c, fn23453, std::move(args23454)); }()), false); args23452.Add(List({}), false); return Call(c, fn23451, std::move(args23452)); }()), "append"); Arguments args23450; args23450.Add(Tuple({s->LocalAt(20), Get(s->LocalAt(5), Value(int64_t{0}))}), false); return Call(c, fn23449, std::move(args23450)); }());
}
}
}
for (const auto& item23455 : Iterate(([&]() -> Value { auto fn23456 = s->Global("range"); Arguments args23457; args23457.Add(([&]() -> Value { auto fn23458 = s->Global("sum"); Arguments args23459; args23459.Add(([&]() -> Value { auto comp23460 = std::make_shared<Scope>(); comp23460->globals = s->globals; comp23460->parent = s; static constexpr const char* comp23460_names[] = {"o"}; comp23460->PrepareSlots(comp23460_names); auto result23461 = List(); for (const auto& item23462 : Iterate(([&]() -> Value { auto v23463 = ([&]() -> Value { auto fn23464 = PrepareDictionaryGet(s->LocalAt(2)); Arguments args23465; args23465.Add(Value("market"), false); return CallDictionaryGet(c, fn23464, std::move(args23465)); }()); if (static_cast<bool>(v23463)) return v23463; v23463 = List({}); return v23463; }()))) { comp23460->SetAt(0, item23462); if (!static_cast<bool>(([&]() -> Value { auto v23466 = comp23460->LocalAt(0); if (!static_cast<bool>(v23466)) return v23466; v23466 = ([&]() -> Value { auto v23467 = Get(comp23460->LocalAt(0), Value(int64_t{0})); Value v23468; v23468 = Value("HIRE"); if (!static_cast<bool>(Binary("Eq", v23467, v23468))) return Value(false); v23467 = v23468; return Value(true); }()); return v23466; }()))) continue; result23461.node()->sequence.push_back(Value(int64_t{1})); } return result23461; }()), false); return Call(c, fn23458, std::move(args23459)); }()), false); return Call(c, fn23456, std::move(args23457)); }()))) {
s->SetAt(0, item23455);
auto v23469 = ([&]() -> Value { auto comp23470 = std::make_shared<Scope>(); comp23470->globals = s->globals; comp23470->parent = s; static constexpr const char* comp23470_names[] = {"a"}; comp23470->PrepareSlots(comp23470_names); auto result23471 = Dict(); for (const auto& item23472 : Iterate(s->LocalAt(1))) { comp23470->SetAt(0, item23472); Put(result23471, comp23470->LocalAt(0), Value(int64_t{0})); } return result23471; }());
s->SetAt(14, v23469);
for (const auto& item23473 : Iterate(s->LocalAt(17))) {
s->SetAt(16, item23473);
if (static_cast<bool>(([&]() -> Value { auto v23474 = ([&]() -> Value { auto fn23476 = s->Global("tuple"); Arguments args23477; args23477.Add(s->LocalAt(16), false); return Call(c, fn23476, std::move(args23477)); }()); Value v23475; v23475 = s->LocalAt(14); if (!static_cast<bool>(Binary("In", v23474, v23475))) return Value(false); v23474 = v23475; return Value(true); }()))) {
auto v23478 = s->LocalAt(14);
auto v23479 = ([&]() -> Value { auto fn23481 = s->Global("tuple"); Arguments args23482; args23482.Add(s->LocalAt(16), false); return Call(c, fn23481, std::move(args23482)); }());
auto v23480 = Get(v23478, v23479);
Put(v23478, v23479, Inplace("Add", v23480, Value(int64_t{1})));
}
}
(void)([&]() -> Value { auto fn23483 = Attribute(s->LocalAt(17), "append"); Arguments args23484; args23484.Add(([&]() -> Value { auto fn23485 = s->Global("list"); Arguments args23486; args23486.Add(([&]() -> Value { auto fn23487 = s->Global("min"); Arguments args23488; args23488.Add(s->LocalAt(1), false); args23488.Keyword("key", Define(&Code_0f7a33b2f75505746dc6, s, Signature{{"a"}, {}, {}, {}, "", "", ([]() -> std::span<const char* const> { static constexpr const char* names[] = {"a"}; return names; }())}, true, "<lambda>")); return Call(c, fn23487, std::move(args23488)); }()), false); return Call(c, fn23485, std::move(args23486)); }()), false); return Call(c, fn23483, std::move(args23484)); }());
}
}
return s->LocalAt(15);
return {};
}
}  // namespace kagg::opponents::compiled
