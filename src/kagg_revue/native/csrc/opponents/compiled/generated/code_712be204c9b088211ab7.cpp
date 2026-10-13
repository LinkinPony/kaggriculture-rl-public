#include "opponents/compiled/typed.hpp"
// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_712be204c9b088211ab7(Context& c, const ScopePtr& s) {
if (auto result = TypedInputs(c, s)) return *result;
static constexpr const char* s_names[] = {"a", "access", "actor", "c", "cap", "counts", "day", "dx", "dy", "expected", "farm", "first", "item", "last", "line", "o", "obs", "pos", "route", "seen", "step", "t", "tape", "target", "targets", "tile", "x", "xy", "y"};
s->PrepareSlots(s_names);
auto v7501 = ([&]() -> Value { auto fn7502 = s->Global("int"); Arguments args7503; args7503.Add(Get(s->LocalAt(16), Value("step")), false); return Call(c, fn7502, std::move(args7503)); }());
s->SetAt(20, v7501);
auto v7504 = ([&]() -> Value { auto v7505 = s->LocalAt(20); return Binary("FloorDiv", v7505, Value(int64_t{24})); }());
s->SetAt(6, v7504);
auto v7506 = Get(Get(s->LocalAt(16), Value("farms")), Get(s->LocalAt(16), Value("player")));
s->SetAt(10, v7506);
auto v7507 = ([&]() -> Value { auto v7508 = List({([&]() -> Value { auto fn7509 = s->Global("list"); Arguments args7510; args7510.Add(Get(s->LocalAt(10), Value("farmer")), false); return Call(c, fn7509, std::move(args7510)); }())}); return Binary("Add", v7508, ([&]() -> Value { auto comp7511 = std::make_shared<Scope>(); comp7511->globals = s->globals; comp7511->parent = s; static constexpr const char* comp7511_names[] = {"p"}; comp7511->PrepareSlots(comp7511_names); auto result7512 = List(); for (const auto& item7513 : Iterate(Slice(Get(s->LocalAt(10), Value("hands")), Value{}, s->LocalAt(9), Value{}))) { comp7511->SetAt(0, item7513); result7512.node()->sequence.push_back(([&]() -> Value { auto fn7514 = comp7511->Global("list"); Arguments args7515; args7515.Add(comp7511->LocalAt(0), false); return Call(c, fn7514, std::move(args7515)); }())); } return result7512; }())); }());
s->SetAt(17, v7507);
auto v7516 = ([&]() -> Value { auto dict7517 = Dict(); return dict7517; }());
s->SetAt(24, v7516);
for (const auto& item7518 : Iterate(([&]() -> Value { auto fn7519 = s->Global("enumerate"); Arguments args7520; args7520.Add(Get(s->LocalAt(10), Value("tiles")), false); return Call(c, fn7519, std::move(args7520)); }()))) {
auto unpack7521 = Iterate(item7518);
ValidateUnpack(unpack7521, 2, false);
s->SetAt(28, unpack7521.at(0));
s->SetAt(14, unpack7521.at(1));
for (const auto& item7522 : Iterate(([&]() -> Value { auto fn7523 = s->Global("enumerate"); Arguments args7524; args7524.Add(s->LocalAt(14), false); return Call(c, fn7523, std::move(args7524)); }()))) {
auto unpack7525 = Iterate(item7522);
ValidateUnpack(unpack7525, 2, false);
s->SetAt(26, unpack7525.at(0));
s->SetAt(25, unpack7525.at(1));
if (static_cast<bool>(([&]() -> Value { auto v7526 = Unary("Not", ([&]() -> Value { auto fn7527 = s->Global("isinstance"); Arguments args7528; args7528.positional.reserve(2); args7528.Add(s->LocalAt(25), false); args7528.Add(s->Global("dict"), false); return Call(c, fn7527, std::move(args7528)); }())); if (static_cast<bool>(v7526)) return v7526; v7526 = ([&]() -> Value { auto v7529 = ([&]() -> Value { auto fn7531 = PrepareDictionaryGet(s->LocalAt(25)); Arguments args7532; args7532.Add(Value("crop"), false); return CallDictionaryGet(c, fn7531, std::move(args7532)); }()); Value v7530; v7530 = s->Global("_R51_INPUT_CROPS"); if (!static_cast<bool>(Binary("NotIn", v7529, v7530))) return Value(false); v7529 = v7530; return Value(true); }()); return v7526; }()))) {
continue;
}
auto v7533 = Get(s->LocalAt(25), Value("crop"));
s->SetAt(12, v7533);
auto v7534 = Get(s->Global("_R51_INPUT_CROPS"), s->LocalAt(12));
auto unpack7535 = Iterate(v7534);
ValidateUnpack(unpack7535, 3, false);
s->SetAt(11, unpack7535.at(0));
s->SetAt(13, unpack7535.at(1));
s->SetAt(4, unpack7535.at(2));
if (static_cast<bool>(([&]() -> Value { auto v7536 = Value(int64_t{1}); Value v7537; v7537 = ([&]() -> Value { auto v7538 = s->LocalAt(6); return Binary("Sub", v7538, Get(s->LocalAt(25), Value("planted_day"))); }()); if (!static_cast<bool>(Binary("LtE", v7536, v7537))) return Value(false); v7536 = v7537; v7537 = s->LocalAt(13); if (!static_cast<bool>(Binary("Lt", v7536, v7537))) return Value(false); v7536 = v7537; return Value(true); }()))) {
auto v7539 = ([&]() -> Value { auto dict7540 = Dict(); auto key7541 = Value("crop"); Put(dict7540, key7541, s->LocalAt(12)); auto key7542 = Value("birth"); Put(dict7540, key7542, Get(s->LocalAt(25), Value("planted_day"))); auto key7543 = Value("yield"); Put(dict7540, key7543, Get(s->LocalAt(25), Value("yield_units"))); auto key7544 = Value("until"); Put(dict7540, key7544, ([&]() -> Value { auto fn7545 = PrepareDictionaryGet(s->LocalAt(25)); Arguments args7546; args7546.positional.reserve(2); args7546.Add(Value("fertilized_until_day"), false); args7546.Add(Unary("USub", Value(int64_t{1})), false); return CallDictionaryGet(c, fn7545, std::move(args7546)); }())); auto key7547 = Value("watered"); Put(dict7540, key7547, ([&]() -> Value { auto fn7548 = PrepareDictionaryGet(s->LocalAt(25)); Arguments args7549; args7549.positional.reserve(2); args7549.Add(Value("watered_today"), false); args7549.Add(Value(false), false); return CallDictionaryGet(c, fn7548, std::move(args7549)); }())); auto key7550 = Value("water"); Put(dict7540, key7550, List({})); auto key7551 = Value("harvest"); Put(dict7540, key7551, Value{}); auto key7552 = Value("first"); Put(dict7540, key7552, s->LocalAt(11)); auto key7553 = Value("last"); Put(dict7540, key7553, s->LocalAt(13)); auto key7554 = Value("cap"); Put(dict7540, key7554, s->LocalAt(4)); return dict7540; }());
Put(s->LocalAt(24), Tuple({s->LocalAt(26), s->LocalAt(28)}), v7539);
}
}
}
auto v7555 = Tuple({Tuple({Value(int64_t{4}), Value(int64_t{4})}), Tuple({Value(int64_t{5}), Value(int64_t{4})}), Tuple({Value(int64_t{4}), Value(int64_t{5})}), Tuple({Value(int64_t{5}), Value(int64_t{5})})});
s->SetAt(1, v7555);
auto v7556 = ([&]() -> Value { auto fn7557 = s->Global("set"); Arguments args7558; return Call(c, fn7557, std::move(args7558)); }());
s->SetAt(19, v7556);
for (const auto& item7559 : Iterate(([&]() -> Value { auto fn7560 = s->Global("range"); Arguments args7561; args7561.positional.reserve(2); args7561.Add(s->LocalAt(20), false); args7561.Add(([&]() -> Value { auto fn7562 = s->Global("min"); Arguments args7563; args7563.positional.reserve(2); args7563.Add(Value(int64_t{712}), false); args7563.Add(([&]() -> Value { auto v7564 = ([&]() -> Value { auto v7565 = s->LocalAt(6); return Binary("Add", v7565, Value(int64_t{4})); }()); return Binary("Mult", v7564, Value(int64_t{24})); }()), false); return Call(c, fn7562, std::move(args7563)); }()), false); return Call(c, fn7560, std::move(args7561)); }()))) {
s->SetAt(21, item7559);
auto v7566 = Get(Attribute(Attribute(s->Global("_IMPL"), "chassis"), "routes"), (static_cast<bool>(([&]() -> Value { auto v7567 = s->LocalAt(21); Value v7568; v7568 = Value(int64_t{648}); if (!static_cast<bool>(Binary("GtE", v7567, v7568))) return Value(false); v7567 = v7568; return Value(true); }())) ? Value(int64_t{2}) : s->LocalAt(18)));
s->SetAt(22, v7566);
auto v7569 = Get(s->LocalAt(22), s->LocalAt(21));
s->SetAt(0, v7569);
for (const auto& item7570 : Iterate(([&]() -> Value { auto fn7571 = s->Global("enumerate"); Arguments args7572; args7572.Add(Slice(([&]() -> Value { Arguments args7575; args7575.Add(([&]() -> Value { auto v7576 = ([&]() -> Value { auto fn7577 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args7578; args7578.Add(Value("farmer"), false); return CallDictionaryGet(c, fn7577, std::move(args7578)); }()); if (static_cast<bool>(v7576)) return v7576; v7576 = List({Value("PASS")}); return v7576; }()), false); args7575.Add(([&]() -> Value { auto v7579 = ([&]() -> Value { auto fn7580 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args7581; args7581.Add(Value("hands"), false); return CallDictionaryGet(c, fn7580, std::move(args7581)); }()); if (static_cast<bool>(v7579)) return v7579; v7579 = List({}); return v7579; }()), true); return List(std::move(args7575.positional)); }()), Value{}, ([&]() -> Value { auto fn7573 = s->Global("len"); Arguments args7574; args7574.Add(s->LocalAt(17), false); return Call(c, fn7573, std::move(args7574)); }()), Value{}), false); return Call(c, fn7571, std::move(args7572)); }()))) {
auto unpack7582 = Iterate(item7570);
ValidateUnpack(unpack7582, 2, false);
s->SetAt(2, unpack7582.at(0));
s->SetAt(3, unpack7582.at(1));
if (static_cast<bool>(Unary("Not", s->LocalAt(3)))) {
continue;
}
auto v7583 = ([&]() -> Value { auto fn7584 = s->Global("tuple"); Arguments args7585; args7585.Add(Get(s->LocalAt(17), s->LocalAt(2)), false); return Call(c, fn7584, std::move(args7585)); }());
s->SetAt(27, v7583);
auto v7586 = ([&]() -> Value { auto fn7587 = PrepareDictionaryGet(s->LocalAt(24)); Arguments args7588; args7588.Add(s->LocalAt(27), false); return CallDictionaryGet(c, fn7587, std::move(args7588)); }());
s->SetAt(23, v7586);
if (static_cast<bool>(([&]() -> Value { auto v7589 = ([&]() -> Value { auto v7590 = s->LocalAt(23); Value v7591; v7591 = Value{}; if (!static_cast<bool>(Binary("IsNot", v7590, v7591))) return Value(false); v7590 = v7591; return Value(true); }()); if (!static_cast<bool>(v7589)) return v7589; v7589 = ([&]() -> Value { auto v7592 = Get(s->LocalAt(23), Value("harvest")); Value v7593; v7593 = Value{}; if (!static_cast<bool>(Binary("Is", v7592, v7593))) return Value(false); v7592 = v7593; return Value(true); }()); return v7589; }()))) {
if (static_cast<bool>(([&]() -> Value { auto v7594 = ([&]() -> Value { auto v7595 = Get(s->LocalAt(3), Value(int64_t{0})); Value v7596; v7596 = Value("WATER"); if (!static_cast<bool>(Binary("Eq", v7595, v7596))) return Value(false); v7595 = v7596; return Value(true); }()); if (!static_cast<bool>(v7594)) return v7594; v7594 = ([&]() -> Value { auto v7597 = Tuple({([&]() -> Value { auto v7599 = s->LocalAt(21); return Binary("FloorDiv", v7599, Value(int64_t{24})); }()), s->LocalAt(27)}); Value v7598; v7598 = s->LocalAt(19); if (!static_cast<bool>(Binary("NotIn", v7597, v7598))) return Value(false); v7597 = v7598; return Value(true); }()); return v7594; }()))) {
(void)([&]() -> Value { auto fn7600 = Attribute(s->LocalAt(19), "add"); Arguments args7601; args7601.Add(Tuple({([&]() -> Value { auto v7602 = s->LocalAt(21); return Binary("FloorDiv", v7602, Value(int64_t{24})); }()), s->LocalAt(27)}), false); return Call(c, fn7600, std::move(args7601)); }());
if (static_cast<bool>(([&]() -> Value { auto v7603 = Unary("Not", ([&]() -> Value { auto v7604 = ([&]() -> Value { auto v7605 = ([&]() -> Value { auto v7607 = s->LocalAt(21); return Binary("FloorDiv", v7607, Value(int64_t{24})); }()); Value v7606; v7606 = s->LocalAt(6); if (!static_cast<bool>(Binary("Eq", v7605, v7606))) return Value(false); v7605 = v7606; return Value(true); }()); if (!static_cast<bool>(v7604)) return v7604; v7604 = Get(s->LocalAt(23), Value("watered")); return v7604; }())); if (!static_cast<bool>(v7603)) return v7603; v7603 = ([&]() -> Value { auto v7608 = Get(s->LocalAt(23), Value("first")); Value v7609; v7609 = ([&]() -> Value { auto v7610 = ([&]() -> Value { auto v7611 = s->LocalAt(21); return Binary("FloorDiv", v7611, Value(int64_t{24})); }()); return Binary("Sub", v7610, Get(s->LocalAt(23), Value("birth"))); }()); if (!static_cast<bool>(Binary("LtE", v7608, v7609))) return Value(false); v7608 = v7609; v7609 = Get(s->LocalAt(23), Value("last")); if (!static_cast<bool>(Binary("LtE", v7608, v7609))) return Value(false); v7608 = v7609; return Value(true); }()); return v7603; }()))) {
(void)([&]() -> Value { auto fn7612 = Attribute(Get(s->LocalAt(23), Value("water")), "append"); Arguments args7613; args7613.Add(s->LocalAt(21), false); return Call(c, fn7612, std::move(args7613)); }());
}
}
if (static_cast<bool>(([&]() -> Value { auto v7614 = Get(s->LocalAt(3), Value(int64_t{0})); Value v7615; v7615 = Value("HARVEST"); if (!static_cast<bool>(Binary("Eq", v7614, v7615))) return Value(false); v7614 = v7615; return Value(true); }()))) {
auto v7616 = s->LocalAt(21);
Put(s->LocalAt(23), Value("harvest"), v7616);
}
}
if (static_cast<bool>(([&]() -> Value { auto v7617 = Get(s->LocalAt(3), Value(int64_t{0})); Value v7618; v7618 = s->Global("MOVES"); if (!static_cast<bool>(Binary("In", v7617, v7618))) return Value(false); v7617 = v7618; return Value(true); }()))) {
auto v7619 = Get(s->Global("MOVES"), Get(s->LocalAt(3), Value(int64_t{0})));
auto unpack7620 = Iterate(v7619);
ValidateUnpack(unpack7620, 2, false);
s->SetAt(7, unpack7620.at(0));
s->SetAt(8, unpack7620.at(1));
auto v7621 = List({([&]() -> Value { auto fn7622 = s->Global("max"); Arguments args7623; args7623.positional.reserve(2); args7623.Add(Value(int64_t{0}), false); args7623.Add(([&]() -> Value { auto fn7624 = s->Global("min"); Arguments args7625; args7625.positional.reserve(2); args7625.Add(Value(int64_t{9}), false); args7625.Add(([&]() -> Value { auto v7626 = Get(Get(s->LocalAt(17), s->LocalAt(2)), Value(int64_t{0})); return Binary("Add", v7626, s->LocalAt(7)); }()), false); return Call(c, fn7624, std::move(args7625)); }()), false); return Call(c, fn7622, std::move(args7623)); }()), ([&]() -> Value { auto fn7627 = s->Global("max"); Arguments args7628; args7628.positional.reserve(2); args7628.Add(Value(int64_t{0}), false); args7628.Add(([&]() -> Value { auto fn7629 = s->Global("min"); Arguments args7630; args7630.positional.reserve(2); args7630.Add(Value(int64_t{9}), false); args7630.Add(([&]() -> Value { auto v7631 = Get(Get(s->LocalAt(17), s->LocalAt(2)), Value(int64_t{1})); return Binary("Add", v7631, s->LocalAt(8)); }()), false); return Call(c, fn7629, std::move(args7630)); }()), false); return Call(c, fn7627, std::move(args7628)); }())});
Put(s->LocalAt(17), s->LocalAt(2), v7621);
}
}
for (const auto& item7632 : Iterate(([&]() -> Value { auto fn7633 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args7634; args7634.positional.reserve(2); args7634.Add(Value("market"), false); args7634.Add(List({}), false); return CallDictionaryGet(c, fn7633, std::move(args7634)); }()))) {
s->SetAt(15, item7632);
if (static_cast<bool>(([&]() -> Value { auto v7635 = s->LocalAt(15); if (!static_cast<bool>(v7635)) return v7635; v7635 = ([&]() -> Value { auto v7636 = Get(s->LocalAt(15), Value(int64_t{0})); Value v7637; v7637 = Value("HIRE"); if (!static_cast<bool>(Binary("Eq", v7636, v7637))) return Value(false); v7636 = v7637; return Value(true); }()); return v7635; }()))) {
auto v7638 = ([&]() -> Value { auto comp7639 = std::make_shared<Scope>(); comp7639->globals = s->globals; comp7639->parent = s; static constexpr const char* comp7639_names[] = {"p"}; comp7639->PrepareSlots(comp7639_names); auto result7640 = Dict(); for (const auto& item7641 : Iterate(s->LocalAt(1))) { comp7639->SetAt(0, item7641); Put(result7640, comp7639->LocalAt(0), ([&]() -> Value { auto fn7642 = comp7639->Global("sum"); Arguments args7643; args7643.Add(([&]() -> Value { auto comp7644 = std::make_shared<Scope>(); comp7644->globals = comp7639->globals; comp7644->parent = comp7639; static constexpr const char* comp7644_names[] = {"q"}; comp7644->PrepareSlots(comp7644_names); auto result7645 = List(); for (const auto& item7646 : Iterate(comp7639->Captured("pos"))) { comp7644->SetAt(0, item7646); result7645.node()->sequence.push_back(([&]() -> Value { auto v7647 = ([&]() -> Value { auto fn7649 = comp7644->Global("tuple"); Arguments args7650; args7650.Add(comp7644->LocalAt(0), false); return Call(c, fn7649, std::move(args7650)); }()); Value v7648; v7648 = comp7644->Captured("p"); if (!static_cast<bool>(Binary("Eq", v7647, v7648))) return Value(false); v7647 = v7648; return Value(true); }())); } return result7645; }()), false); return Call(c, fn7642, std::move(args7643)); }())); } return result7640; }());
s->SetAt(5, v7638);
(void)([&]() -> Value { auto fn7651 = Attribute(s->LocalAt(17), "append"); Arguments args7652; args7652.Add(([&]() -> Value { auto fn7653 = s->Global("list"); Arguments args7654; args7654.Add(([&]() -> Value { auto fn7655 = s->Global("min"); Arguments args7656; args7656.Add(s->LocalAt(1), false); args7656.Keyword("key", Define(&Code_c84b15e4d6dc326f19a7, s, Signature{{"p"}, {}, {}, {}, "", "", ([]() -> std::span<const char* const> { static constexpr const char* names[] = {"p"}; return names; }())}, true, "<lambda>")); return Call(c, fn7655, std::move(args7656)); }()), false); return Call(c, fn7653, std::move(args7654)); }()), false); return Call(c, fn7651, std::move(args7652)); }());
}
}
if (static_cast<bool>(([&]() -> Value { auto v7659 = ([&]() -> Value { auto v7661 = ([&]() -> Value { auto v7662 = s->LocalAt(21); return Binary("Add", v7662, Value(int64_t{1})); }()); return Binary("Mod", v7661, Value(int64_t{24})); }()); Value v7660; v7660 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v7659, v7660))) return Value(false); v7659 = v7660; return Value(true); }()))) {
auto v7663 = List({List({Value(int64_t{4}), Value(int64_t{4})})});
s->SetAt(17, v7663);
}
}
return s->LocalAt(24);
return {};
}
}  // namespace kagg::opponents::compiled
