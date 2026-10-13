// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_56d3a6a1436af6654ddc(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "actor", "command", "commands", "configuration", "day", "farm", "funded", "gained", "i", "item", "obs", "pending", "player", "previous", "private", "result", "state", "step", "targets"};
s->PrepareSlots(s_names);
auto v26568 = ([&]() -> Value { auto fn26569 = s->Global("int"); Arguments args26570; args26570.Add(Get(s->LocalAt(11), Value("step")), false); return Call(c, fn26569, std::move(args26570)); }());
s->SetAt(18, v26568);
auto v26571 = ([&]() -> Value { auto fn26572 = s->Global("int"); Arguments args26573; args26573.Add(Get(s->LocalAt(11), Value("player")), false); return Call(c, fn26572, std::move(args26573)); }());
s->SetAt(13, v26571);
auto v26574 = ([&]() -> Value { auto v26575 = s->LocalAt(18); return Binary("FloorDiv", v26575, Value(int64_t{24})); }());
s->SetAt(5, v26574);
auto v26576 = ([&]() -> Value { auto fn26577 = PrepareDictionaryGet(s->Global("_V233_STATES")); Arguments args26578; args26578.Add(s->LocalAt(13), false); return CallDictionaryGet(c, fn26577, std::move(args26578)); }());
s->SetAt(17, v26576);
if (static_cast<bool>(([&]() -> Value { auto v26579 = ([&]() -> Value { auto v26580 = s->LocalAt(17); Value v26581; v26581 = Value{}; if (!static_cast<bool>(Binary("Is", v26580, v26581))) return Value(false); v26580 = v26581; return Value(true); }()); if (static_cast<bool>(v26579)) return v26579; v26579 = ([&]() -> Value { auto v26582 = s->LocalAt(18); Value v26583; v26583 = Get(s->LocalAt(17), Value("last_step")); if (!static_cast<bool>(Binary("Lt", v26582, v26583))) return Value(false); v26582 = v26583; return Value(true); }()); return v26579; }()))) {
auto v26584 = ([&]() -> Value { auto dict26585 = Dict(); auto key26586 = Value("last_step"); Put(dict26585, key26586, s->LocalAt(18)); auto key26587 = Value("day"); Put(dict26585, key26587, Unary("USub", Value(int64_t{1}))); auto key26588 = Value("workers"); Put(dict26585, key26588, ([&]() -> Value { auto dict26589 = Dict(); return dict26589; }())); auto key26590 = Value("work"); Put(dict26585, key26590, ([&]() -> Value { auto dict26591 = Dict(); return dict26591; }())); auto key26592 = Value("credit"); Put(dict26585, key26592, ([&]() -> Value { auto dict26593 = Dict(); auto key26594 = Value("WOOL"); Put(dict26593, key26594, Value(int64_t{0})); auto key26595 = Value("FERTILIZER"); Put(dict26593, key26595, Value(int64_t{0})); return dict26593; }())); return dict26585; }());
s->SetAt(17, v26584);
auto v26596 = s->LocalAt(17);
Put(s->Global("_V233_STATES"), s->LocalAt(13), v26596);
}
auto v26597 = s->LocalAt(18);
Put(s->LocalAt(17), Value("last_step"), v26597);
if (static_cast<bool>(([&]() -> Value { auto v26598 = ([&]() -> Value { auto v26599 = s->LocalAt(4); Value v26600; v26600 = Value{}; if (!static_cast<bool>(Binary("IsNot", v26599, v26600))) return Value(false); v26599 = v26600; return Value(true); }()); if (!static_cast<bool>(v26598)) return v26598; v26598 = ([&]() -> Value { auto comp26601 = std::make_shared<Scope>(); comp26601->globals = s->globals; comp26601->parent = s; static constexpr const char* comp26601_names[] = {"k", "v"}; comp26601->PrepareSlots(comp26601_names); auto result26602 = List(); for (const auto& item26603 : Iterate(Tuple({Tuple({Value("boardSize"), Value(int64_t{10})}), Tuple({Value("turnsPerDay"), Value(int64_t{24})}), Tuple({Value("shedCapacity"), Value(int64_t{100})}), Tuple({Value("maxMarketOrdersPerTurn"), Value(int64_t{10})})}))) { auto unpack26604 = Iterate(item26603); ValidateUnpack(unpack26604, 2, false); comp26601->SetAt(0, unpack26604.at(0)); comp26601->SetAt(1, unpack26604.at(1)); if (static_cast<bool>(([&]() -> Value { auto v26605 = ([&]() -> Value { auto fn26607 = PrepareDictionaryGet(comp26601->Captured("configuration")); Arguments args26608; args26608.positional.reserve(2); args26608.Add(comp26601->LocalAt(0), false); args26608.Add(comp26601->LocalAt(1), false); return CallDictionaryGet(c, fn26607, std::move(args26608)); }()); Value v26606; v26606 = comp26601->LocalAt(1); if (!static_cast<bool>(Binary("NotEq", v26605, v26606))) return Value(false); v26605 = v26606; return Value(true); }()))) return Value(true); } return Value(false); }()); return v26598; }()))) {
return s->LocalAt(0);
}
auto v26609 = Get(Get(s->LocalAt(11), Value("farms")), s->LocalAt(13));
s->SetAt(6, v26609);
auto v26610 = Get(s->LocalAt(11), Value("private"));
s->SetAt(15, v26610);
if (static_cast<bool>(([&]() -> Value { auto v26611 = Get(s->LocalAt(17), Value("day")); Value v26612; v26612 = s->LocalAt(5); if (!static_cast<bool>(Binary("NotEq", v26611, v26612))) return Value(false); v26611 = v26612; return Value(true); }()))) {
auto v26613 = s->LocalAt(5);
Put(s->LocalAt(17), Value("day"), v26613);
auto v26614 = ([&]() -> Value { auto dict26615 = Dict(); return dict26615; }());
Put(s->LocalAt(17), Value("workers"), v26614);
auto v26616 = ([&]() -> Value { auto dict26617 = Dict(); return dict26617; }());
Put(s->LocalAt(17), Value("work"), v26616);
auto v26618 = Value(int64_t{0});
Put(s->LocalAt(17), Value("rescue_today"), v26618);
}
for (const auto& item26619 : Iterate(([&]() -> Value { auto fn26620 = Attribute(Get(s->LocalAt(17), Value("work")), "items"); Arguments args26621; return Call(c, fn26620, std::move(args26621)); }()))) {
auto unpack26622 = Iterate(item26619);
ValidateUnpack(unpack26622, 2, false);
s->SetAt(1, unpack26622.at(0));
s->SetAt(14, unpack26622.at(1));
if (static_cast<bool>(([&]() -> Value { auto v26623 = ([&]() -> Value { auto v26624 = Get(s->LocalAt(14), Value("step")); Value v26625; v26625 = ([&]() -> Value { auto v26626 = s->LocalAt(18); return Binary("Sub", v26626, Value(int64_t{1})); }()); if (!static_cast<bool>(Binary("NotEq", v26624, v26625))) return Value(false); v26624 = v26625; return Value(true); }()); if (static_cast<bool>(v26623)) return v26623; v26623 = ([&]() -> Value { auto v26627 = s->LocalAt(1); Value v26628; v26628 = ([&]() -> Value { auto fn26629 = s->Global("len"); Arguments args26630; args26630.Add(Get(s->LocalAt(15), Value("inventories")), false); return Call(c, fn26629, std::move(args26630)); }()); if (!static_cast<bool>(Binary("GtE", v26627, v26628))) return Value(false); v26627 = v26628; return Value(true); }()); return v26623; }()))) {
continue;
}
auto v26631 = ([&]() -> Value { auto fn26632 = PrepareDictionaryGet(([&]() -> Value { auto dict26634 = Dict(); auto key26635 = Value("HARVEST"); Put(dict26634, key26635, Value("WOOL")); auto key26636 = Value("COLLECT_FERTILIZER"); Put(dict26634, key26636, Value("FERTILIZER")); return dict26634; }())); Arguments args26633; args26633.Add(Get(Get(s->LocalAt(14), Value("command")), Value(int64_t{0})), false); return CallDictionaryGet(c, fn26632, std::move(args26633)); }());
s->SetAt(10, v26631);
if (static_cast<bool>(s->LocalAt(10))) {
auto v26637 = ([&]() -> Value { auto fn26638 = s->Global("max"); Arguments args26639; args26639.positional.reserve(2); args26639.Add(Value(int64_t{0}), false); args26639.Add(([&]() -> Value { auto v26640 = ([&]() -> Value { auto fn26641 = PrepareDictionaryGet(Get(Get(s->LocalAt(15), Value("inventories")), s->LocalAt(1))); Arguments args26642; args26642.positional.reserve(2); args26642.Add(s->LocalAt(10), false); args26642.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn26641, std::move(args26642)); }()); return Binary("Sub", v26640, ([&]() -> Value { auto fn26643 = PrepareDictionaryGet(Get(s->LocalAt(14), Value("inventory"))); Arguments args26644; args26644.positional.reserve(2); args26644.Add(s->LocalAt(10), false); args26644.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn26643, std::move(args26644)); }())); }()), false); return Call(c, fn26638, std::move(args26639)); }());
s->SetAt(8, v26637);
auto v26645 = Get(s->LocalAt(17), Value("credit"));
auto v26646 = s->LocalAt(10);
auto v26647 = Get(v26645, v26646);
Put(v26645, v26646, Inplace("Add", v26647, s->LocalAt(8)));
}
}
auto v26648 = ([&]() -> Value { auto fn26649 = Attribute(s->LocalAt(17), "pop"); Arguments args26650; args26650.positional.reserve(2); args26650.Add(Value("pending"), false); args26650.Add(Value{}, false); return Call(c, fn26649, std::move(args26650)); }());
s->SetAt(12, v26648);
if (static_cast<bool>(s->LocalAt(12))) {
auto v26651 = ([&]() -> Value { auto v26652 = ([&]() -> Value { auto v26653 = Value("SE"); Value v26654; v26654 = Get(s->LocalAt(6), Value("unlocked_quadrants")); if (!static_cast<bool>(Binary("In", v26653, v26654))) return Value(false); v26653 = v26654; return Value(true); }()); if (!static_cast<bool>(v26652)) return v26652; v26652 = ([&]() -> Value { auto v26655 = Unary("Not", Get(s->LocalAt(12), Value("initial"))); if (static_cast<bool>(v26655)) return v26655; v26655 = ([&]() -> Value { auto v26656 = ([&]() -> Value { auto fn26658 = PrepareDictionaryGet(Get(s->LocalAt(15), Value("shed"))); Arguments args26659; args26659.positional.reserve(2); args26659.Add(Value("SHEEP"), false); args26659.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn26658, std::move(args26659)); }()); Value v26657; v26657 = Value(int64_t{6}); if (!static_cast<bool>(Binary("GtE", v26656, v26657))) return Value(false); v26656 = v26657; return Value(true); }()); return v26655; }()); return v26652; }());
s->SetAt(7, v26651);
if (static_cast<bool>(Unary("Not", s->LocalAt(7)))) {
auto v26660 = s->Global("_V233_REPORT");
auto v26661 = Value("sheep_purchase_shortfalls");
auto v26662 = Get(v26660, v26661);
Put(v26660, v26661, Inplace("Add", v26662, Value(int64_t{1})));
}
else {
if (static_cast<bool>(([&]() -> Value { auto v26663 = ([&]() -> Value { auto fn26665 = s->Global("len"); Arguments args26666; args26666.Add(Get(s->LocalAt(6), Value("hands")), false); return Call(c, fn26665, std::move(args26666)); }()); Value v26664; v26664 = ([&]() -> Value { auto v26667 = ([&]() -> Value { auto v26668 = Get(s->LocalAt(12), Value("first")); return Binary("Add", v26668, ([&]() -> Value { auto fn26669 = PrepareDictionaryGet(s->LocalAt(12)); Arguments args26670; args26670.positional.reserve(2); args26670.Add(Value("count"), false); args26670.Add(Value(int64_t{2}), false); return CallDictionaryGet(c, fn26669, std::move(args26670)); }())); }()); return Binary("Sub", v26667, Value(int64_t{1})); }()); if (!static_cast<bool>(Binary("Lt", v26663, v26664))) return Value(false); v26663 = v26664; return Value(true); }()))) {
auto v26671 = s->Global("_V233_REPORT");
auto v26672 = Value("sheep_hire_shortfalls");
auto v26673 = Get(v26671, v26672);
Put(v26671, v26672, Inplace("Add", v26673, Value(int64_t{1})));
}
else {
if (static_cast<bool>(([&]() -> Value { auto v26674 = ([&]() -> Value { auto fn26676 = PrepareDictionaryGet(s->LocalAt(12)); Arguments args26677; args26677.positional.reserve(2); args26677.Add(Value("count"), false); args26677.Add(Value(int64_t{2}), false); return CallDictionaryGet(c, fn26676, std::move(args26677)); }()); Value v26675; v26675 = Value(int64_t{1}); if (!static_cast<bool>(Binary("Eq", v26674, v26675))) return Value(false); v26674 = v26675; return Value(true); }()))) {
auto v26678 = ([&]() -> Value { auto comp26679 = std::make_shared<Scope>(); comp26679->globals = s->globals; comp26679->parent = s; static constexpr const char* comp26679_names[] = {"t"}; comp26679->PrepareSlots(comp26679_names); auto result26680 = List(); for (const auto& item26681 : Iterate(Get(s->LocalAt(12), Value("targets")))) { comp26679->SetAt(0, item26681); result26680.node()->sequence.push_back(([&]() -> Value { auto fn26682 = comp26679->Global("tuple"); Arguments args26683; args26683.Add(comp26679->LocalAt(0), false); return Call(c, fn26682, std::move(args26683)); }())); } return result26680; }());
Put(Get(s->LocalAt(17), Value("workers")), Get(s->LocalAt(12), Value("first")), v26678);
auto v26684 = s->Global("_V233_REPORT");
auto v26685 = Value("sheep_workers_confirmed");
auto v26686 = Get(v26684, v26685);
Put(v26684, v26685, Inplace("Add", v26686, Value(int64_t{1})));
auto v26687 = s->Global("_SL_REPORT");
auto v26688 = Value("confirmed");
auto v26689 = Get(v26687, v26688);
Put(v26687, v26688, Inplace("Add", v26689, Value(int64_t{1})));
}
else {
for (const auto& item26690 : Iterate(([&]() -> Value { auto fn26691 = s->Global("range"); Arguments args26692; args26692.Add(Value(int64_t{2}), false); return Call(c, fn26691, std::move(args26692)); }()))) {
s->SetAt(9, item26690);
auto v26693 = ([&]() -> Value { auto comp26694 = std::make_shared<Scope>(); comp26694->globals = s->globals; comp26694->parent = s; static constexpr const char* comp26694_names[] = {"x"}; comp26694->PrepareSlots(comp26694_names); auto result26695 = List(); for (const auto& item26696 : Iterate(([&]() -> Value { auto fn26697 = s->Global("range"); Arguments args26698; args26698.positional.reserve(2); args26698.Add(Value(int64_t{5}), false); args26698.Add(Value(int64_t{8}), false); return Call(c, fn26697, std::move(args26698)); }()))) { comp26694->SetAt(0, item26696); result26695.node()->sequence.push_back(Tuple({comp26694->LocalAt(0), ([&]() -> Value { auto v26699 = Value(int64_t{5}); return Binary("Add", v26699, comp26694->Captured("i")); }())})); } return result26695; }());
Put(Get(s->LocalAt(17), Value("workers")), ([&]() -> Value { auto v26700 = Get(s->LocalAt(12), Value("first")); return Binary("Add", v26700, s->LocalAt(9)); }()), v26693);
}
auto v26701 = s->Global("_V233_REPORT");
auto v26702 = Value("sheep_workers_confirmed");
auto v26703 = Get(v26701, v26702);
Put(v26701, v26702, Inplace("Add", v26703, Value(int64_t{2})));
if (static_cast<bool>(Get(s->LocalAt(12), Value("initial")))) {
auto v26704 = Value(true);
Put(s->LocalAt(17), Value("committed"), v26704);
auto v26705 = s->Global("_V233_REPORT");
auto v26706 = Value("sheep_committed");
auto v26707 = Get(v26705, v26706);
Put(v26705, v26706, Inplace("Add", v26707, Value(int64_t{1})));
}
}
}
}
}
auto v26708 = ([&]() -> Value { auto fn26709 = s->Global("_e343_yx_request"); Arguments args26710; args26710.positional.reserve(4); args26710.Add(s->LocalAt(11), false); args26710.Add(s->LocalAt(0), false); args26710.Add(s->LocalAt(17), false); args26710.Add(Get(Attribute(Attribute(s->Global("_IMPL"), "chassis"), "players"), s->LocalAt(13)), false); return Call(c, fn26709, std::move(args26710)); }());
s->SetAt(0, v26708);
if (static_cast<bool>(([&]() -> Value { auto v26711 = Unary("Not", ([&]() -> Value { auto fn26712 = PrepareDictionaryGet(s->LocalAt(17)); Arguments args26713; args26713.Add(Value("committed"), false); return CallDictionaryGet(c, fn26712, std::move(args26713)); }())); if (static_cast<bool>(v26711)) return v26711; v26711 = Unary("Not", Get(s->LocalAt(17), Value("workers"))); return v26711; }()))) {
return s->LocalAt(0);
}
auto v26714 = ([&]() -> Value { auto fn26715 = Attribute(s->Global("copy"), "deepcopy"); Arguments args26716; args26716.Add(s->LocalAt(0), false); return Call(c, fn26715, std::move(args26716)); }());
s->SetAt(16, v26714);
auto v26717 = ([&]() -> Value { auto v26718 = List({([&]() -> Value { auto v26719 = ([&]() -> Value { auto fn26720 = PrepareDictionaryGet(s->LocalAt(16)); Arguments args26721; args26721.Add(Value("farmer"), false); return CallDictionaryGet(c, fn26720, std::move(args26721)); }()); if (static_cast<bool>(v26719)) return v26719; v26719 = List({Value("PASS")}); return v26719; }())}); return Binary("Add", v26718, ([&]() -> Value { auto fn26722 = s->Global("list"); Arguments args26723; args26723.Add(([&]() -> Value { auto v26724 = ([&]() -> Value { auto fn26725 = PrepareDictionaryGet(s->LocalAt(16)); Arguments args26726; args26726.Add(Value("hands"), false); return CallDictionaryGet(c, fn26725, std::move(args26726)); }()); if (static_cast<bool>(v26724)) return v26724; v26724 = List({}); return v26724; }()), false); return Call(c, fn26722, std::move(args26723)); }())); }());
s->SetAt(3, v26717);
auto v26727 = s->LocalAt(3);
s->SetAt(3, Inplace("Add", v26727, ([&]() -> Value { auto comp26728 = std::make_shared<Scope>(); comp26728->globals = s->globals; comp26728->parent = s; static constexpr const char* comp26728_names[] = {"_"}; comp26728->PrepareSlots(comp26728_names); auto result26729 = List(); for (const auto& item26730 : Iterate(([&]() -> Value { auto fn26731 = s->Global("range"); Arguments args26732; args26732.Add(([&]() -> Value { auto v26733 = ([&]() -> Value { auto v26734 = ([&]() -> Value { auto fn26735 = s->Global("len"); Arguments args26736; args26736.Add(Get(s->LocalAt(6), Value("hands")), false); return Call(c, fn26735, std::move(args26736)); }()); return Binary("Add", v26734, Value(int64_t{1})); }()); return Binary("Sub", v26733, ([&]() -> Value { auto fn26737 = s->Global("len"); Arguments args26738; args26738.Add(s->LocalAt(3), false); return Call(c, fn26737, std::move(args26738)); }())); }()), false); return Call(c, fn26731, std::move(args26732)); }()))) { comp26728->SetAt(0, item26730); result26729.node()->sequence.push_back(List({Value("PASS")})); } return result26729; }())));
auto v26739 = ([&]() -> Value { auto dict26740 = Dict(); return dict26740; }());
Put(s->LocalAt(17), Value("work"), v26739);
for (const auto& item26741 : Iterate(([&]() -> Value { auto fn26742 = Attribute(Get(s->LocalAt(17), Value("workers")), "items"); Arguments args26743; return Call(c, fn26742, std::move(args26743)); }()))) {
auto unpack26744 = Iterate(item26741);
ValidateUnpack(unpack26744, 2, false);
s->SetAt(1, unpack26744.at(0));
s->SetAt(19, unpack26744.at(1));
if (static_cast<bool>(([&]() -> Value { auto v26745 = s->LocalAt(1); Value v26746; v26746 = ([&]() -> Value { auto fn26747 = s->Global("len"); Arguments args26748; args26748.Add(s->LocalAt(3), false); return Call(c, fn26747, std::move(args26748)); }()); if (!static_cast<bool>(Binary("GtE", v26745, v26746))) return Value(false); v26745 = v26746; return Value(true); }()))) {
continue;
}
auto v26749 = ([&]() -> Value { auto fn26750 = s->Global("_E343_YX_ORIG_WORKER"); Arguments args26751; args26751.positional.reserve(3); args26751.Add(s->LocalAt(11), false); args26751.Add(s->LocalAt(1), false); args26751.Add(s->LocalAt(19), false); return Call(c, fn26750, std::move(args26751)); }());
s->SetAt(2, v26749);
auto v26752 = s->LocalAt(2);
Put(s->LocalAt(3), s->LocalAt(1), v26752);
auto v26753 = ([&]() -> Value { auto dict26754 = Dict(); auto key26755 = Value("step"); Put(dict26754, key26755, s->LocalAt(18)); auto key26756 = Value("command"); Put(dict26754, key26756, s->LocalAt(2)); auto key26757 = Value("inventory"); Put(dict26754, key26757, ([&]() -> Value { auto fn26758 = s->Global("dict"); Arguments args26759; args26759.Add(Get(Get(s->LocalAt(15), Value("inventories")), s->LocalAt(1)), false); return Call(c, fn26758, std::move(args26759)); }())); return dict26754; }());
Put(Get(s->LocalAt(17), Value("work")), s->LocalAt(1), v26753);
}
auto v26760 = Tuple({Get(s->LocalAt(3), Value(int64_t{0})), Slice(s->LocalAt(3), Value(int64_t{1}), Value{}, Value{})});
auto unpack26761 = Iterate(v26760);
ValidateUnpack(unpack26761, 2, false);
Put(s->LocalAt(16), Value("farmer"), unpack26761.at(0));
Put(s->LocalAt(16), Value("hands"), unpack26761.at(1));
auto v26762 = ([&]() -> Value { auto fn26763 = s->Global("_v234_rescue"); Arguments args26764; args26764.positional.reserve(3); args26764.Add(s->LocalAt(11), false); args26764.Add(s->LocalAt(16), false); args26764.Add(s->LocalAt(17), false); return Call(c, fn26763, std::move(args26764)); }());
s->SetAt(16, v26762);
return s->LocalAt(16);
return {};
}
}  // namespace kagg::opponents::compiled
