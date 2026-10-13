// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_e0ec9b49b525a83baee7(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "actor", "command", "commands", "configuration", "count", "day", "farm", "funded", "gained", "i", "item", "observation", "pending", "player", "previous", "private", "result", "scheduled", "state", "step", "stock", "targets"};
s->PrepareSlots(s_names);
auto v17550 = ([&]() -> Value { auto fn17551 = s->Global("_V233_PARENT"); Arguments args17552; args17552.positional.reserve(2); args17552.Add(s->LocalAt(12), false); args17552.Add(s->LocalAt(4), false); return Call(c, fn17551, std::move(args17552)); }());
s->SetAt(0, v17550);
auto v17553 = ([&]() -> Value { auto fn17554 = s->Global("int"); Arguments args17555; args17555.Add(Get(s->LocalAt(12), Value("step")), false); return Call(c, fn17554, std::move(args17555)); }());
s->SetAt(20, v17553);
auto v17556 = ([&]() -> Value { auto fn17557 = s->Global("int"); Arguments args17558; args17558.Add(Get(s->LocalAt(12), Value("player")), false); return Call(c, fn17557, std::move(args17558)); }());
s->SetAt(14, v17556);
auto v17559 = ([&]() -> Value { auto v17560 = s->LocalAt(20); return Binary("FloorDiv", v17560, Value(int64_t{24})); }());
s->SetAt(6, v17559);
auto v17561 = ([&]() -> Value { auto fn17562 = PrepareDictionaryGet(s->Global("_V233_STATES")); Arguments args17563; args17563.Add(s->LocalAt(14), false); return CallDictionaryGet(c, fn17562, std::move(args17563)); }());
s->SetAt(19, v17561);
if (static_cast<bool>(([&]() -> Value { auto v17564 = ([&]() -> Value { auto v17565 = s->LocalAt(19); Value v17566; v17566 = Value{}; if (!static_cast<bool>(Binary("Is", v17565, v17566))) return Value(false); v17565 = v17566; return Value(true); }()); if (static_cast<bool>(v17564)) return v17564; v17564 = ([&]() -> Value { auto v17567 = s->LocalAt(20); Value v17568; v17568 = Get(s->LocalAt(19), Value("last_step")); if (!static_cast<bool>(Binary("LtE", v17567, v17568))) return Value(false); v17567 = v17568; return Value(true); }()); return v17564; }()))) {
auto v17569 = ([&]() -> Value { auto dict17570 = Dict(); auto key17571 = Value("last_step"); Put(dict17570, key17571, s->LocalAt(20)); auto key17572 = Value("day"); Put(dict17570, key17572, Unary("USub", Value(int64_t{1}))); auto key17573 = Value("workers"); Put(dict17570, key17573, ([&]() -> Value { auto dict17574 = Dict(); return dict17574; }())); auto key17575 = Value("work"); Put(dict17570, key17575, ([&]() -> Value { auto dict17576 = Dict(); return dict17576; }())); auto key17577 = Value("credit"); Put(dict17570, key17577, ([&]() -> Value { auto dict17578 = Dict(); auto key17579 = Value("WOOL"); Put(dict17578, key17579, Value(int64_t{0})); auto key17580 = Value("FERTILIZER"); Put(dict17578, key17580, Value(int64_t{0})); return dict17578; }())); return dict17570; }());
s->SetAt(19, v17569);
auto v17581 = s->LocalAt(19);
Put(s->Global("_V233_STATES"), s->LocalAt(14), v17581);
}
auto v17582 = s->LocalAt(20);
Put(s->LocalAt(19), Value("last_step"), v17582);
if (static_cast<bool>(([&]() -> Value { auto v17583 = ([&]() -> Value { auto v17584 = s->LocalAt(4); Value v17585; v17585 = Value{}; if (!static_cast<bool>(Binary("IsNot", v17584, v17585))) return Value(false); v17584 = v17585; return Value(true); }()); if (!static_cast<bool>(v17583)) return v17583; v17583 = ([&]() -> Value { auto comp17586 = std::make_shared<Scope>(); comp17586->globals = s->globals; comp17586->parent = s; static constexpr const char* comp17586_names[] = {"k", "v"}; comp17586->PrepareSlots(comp17586_names); auto result17587 = List(); for (const auto& item17588 : Iterate(Tuple({Tuple({Value("boardSize"), Value(int64_t{10})}), Tuple({Value("turnsPerDay"), Value(int64_t{24})}), Tuple({Value("shedCapacity"), Value(int64_t{100})}), Tuple({Value("maxMarketOrdersPerTurn"), Value(int64_t{10})})}))) { auto unpack17589 = Iterate(item17588); ValidateUnpack(unpack17589, 2, false); comp17586->SetAt(0, unpack17589.at(0)); comp17586->SetAt(1, unpack17589.at(1)); if (static_cast<bool>(([&]() -> Value { auto v17590 = ([&]() -> Value { auto fn17592 = PrepareDictionaryGet(comp17586->Captured("configuration")); Arguments args17593; args17593.positional.reserve(2); args17593.Add(comp17586->LocalAt(0), false); args17593.Add(comp17586->LocalAt(1), false); return CallDictionaryGet(c, fn17592, std::move(args17593)); }()); Value v17591; v17591 = comp17586->LocalAt(1); if (!static_cast<bool>(Binary("NotEq", v17590, v17591))) return Value(false); v17590 = v17591; return Value(true); }()))) return Value(true); } return Value(false); }()); return v17583; }()))) {
return s->LocalAt(0);
}
if (static_cast<bool>(([&]() -> Value { auto v17594 = s->LocalAt(6); Value v17595; v17595 = Value(int64_t{12}); if (!static_cast<bool>(Binary("Lt", v17594, v17595))) return Value(false); v17594 = v17595; return Value(true); }()))) {
return s->LocalAt(0);
}
auto v17596 = Get(Get(s->LocalAt(12), Value("farms")), s->LocalAt(14));
s->SetAt(7, v17596);
auto v17597 = Get(s->LocalAt(12), Value("private"));
s->SetAt(16, v17597);
if (static_cast<bool>(([&]() -> Value { auto v17598 = Get(s->LocalAt(19), Value("day")); Value v17599; v17599 = s->LocalAt(6); if (!static_cast<bool>(Binary("NotEq", v17598, v17599))) return Value(false); v17598 = v17599; return Value(true); }()))) {
auto v17600 = s->LocalAt(6);
Put(s->LocalAt(19), Value("day"), v17600);
auto v17601 = ([&]() -> Value { auto dict17602 = Dict(); return dict17602; }());
Put(s->LocalAt(19), Value("workers"), v17601);
auto v17603 = ([&]() -> Value { auto dict17604 = Dict(); return dict17604; }());
Put(s->LocalAt(19), Value("work"), v17603);
auto v17605 = Value(int64_t{0});
Put(s->LocalAt(19), Value("rescue_today"), v17605);
}
for (const auto& item17606 : Iterate(([&]() -> Value { auto fn17607 = Attribute(Get(s->LocalAt(19), Value("work")), "items"); Arguments args17608; return Call(c, fn17607, std::move(args17608)); }()))) {
auto unpack17609 = Iterate(item17606);
ValidateUnpack(unpack17609, 2, false);
s->SetAt(1, unpack17609.at(0));
s->SetAt(15, unpack17609.at(1));
if (static_cast<bool>(([&]() -> Value { auto v17610 = ([&]() -> Value { auto v17611 = Get(s->LocalAt(15), Value("step")); Value v17612; v17612 = ([&]() -> Value { auto v17613 = s->LocalAt(20); return Binary("Sub", v17613, Value(int64_t{1})); }()); if (!static_cast<bool>(Binary("NotEq", v17611, v17612))) return Value(false); v17611 = v17612; return Value(true); }()); if (static_cast<bool>(v17610)) return v17610; v17610 = ([&]() -> Value { auto v17614 = s->LocalAt(1); Value v17615; v17615 = ([&]() -> Value { auto fn17616 = s->Global("len"); Arguments args17617; args17617.Add(Get(s->LocalAt(16), Value("inventories")), false); return Call(c, fn17616, std::move(args17617)); }()); if (!static_cast<bool>(Binary("GtE", v17614, v17615))) return Value(false); v17614 = v17615; return Value(true); }()); return v17610; }()))) {
continue;
}
auto v17618 = ([&]() -> Value { auto fn17619 = PrepareDictionaryGet(([&]() -> Value { auto dict17621 = Dict(); auto key17622 = Value("HARVEST"); Put(dict17621, key17622, Value("WOOL")); auto key17623 = Value("COLLECT_FERTILIZER"); Put(dict17621, key17623, Value("FERTILIZER")); return dict17621; }())); Arguments args17620; args17620.Add(Get(Get(s->LocalAt(15), Value("command")), Value(int64_t{0})), false); return CallDictionaryGet(c, fn17619, std::move(args17620)); }());
s->SetAt(11, v17618);
if (static_cast<bool>(s->LocalAt(11))) {
auto v17624 = ([&]() -> Value { auto fn17625 = s->Global("max"); Arguments args17626; args17626.positional.reserve(2); args17626.Add(Value(int64_t{0}), false); args17626.Add(([&]() -> Value { auto v17627 = ([&]() -> Value { auto fn17628 = PrepareDictionaryGet(Get(Get(s->LocalAt(16), Value("inventories")), s->LocalAt(1))); Arguments args17629; args17629.positional.reserve(2); args17629.Add(s->LocalAt(11), false); args17629.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn17628, std::move(args17629)); }()); return Binary("Sub", v17627, ([&]() -> Value { auto fn17630 = PrepareDictionaryGet(Get(s->LocalAt(15), Value("inventory"))); Arguments args17631; args17631.positional.reserve(2); args17631.Add(s->LocalAt(11), false); args17631.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn17630, std::move(args17631)); }())); }()), false); return Call(c, fn17625, std::move(args17626)); }());
s->SetAt(9, v17624);
auto v17632 = Get(s->LocalAt(19), Value("credit"));
auto v17633 = s->LocalAt(11);
auto v17634 = Get(v17632, v17633);
Put(v17632, v17633, Inplace("Add", v17634, s->LocalAt(9)));
auto v17635 = s->Global("_V233_REPORT");
auto v17636 = (static_cast<bool>(([&]() -> Value { auto v17638 = s->LocalAt(11); Value v17639; v17639 = Value("WOOL"); if (!static_cast<bool>(Binary("Eq", v17638, v17639))) return Value(false); v17638 = v17639; return Value(true); }())) ? Value("sheep_wool_harvested") : Value("sheep_fert_collected"));
auto v17637 = Get(v17635, v17636);
Put(v17635, v17636, Inplace("Add", v17637, s->LocalAt(9)));
}
}
auto v17640 = ([&]() -> Value { auto fn17641 = Attribute(s->LocalAt(19), "pop"); Arguments args17642; args17642.positional.reserve(2); args17642.Add(Value("pending"), false); args17642.Add(Value{}, false); return Call(c, fn17641, std::move(args17642)); }());
s->SetAt(13, v17640);
if (static_cast<bool>(s->LocalAt(13))) {
auto v17643 = ([&]() -> Value { auto v17644 = ([&]() -> Value { auto v17645 = Value("SE"); Value v17646; v17646 = Get(s->LocalAt(7), Value("unlocked_quadrants")); if (!static_cast<bool>(Binary("In", v17645, v17646))) return Value(false); v17645 = v17646; return Value(true); }()); if (!static_cast<bool>(v17644)) return v17644; v17644 = ([&]() -> Value { auto v17647 = Unary("Not", Get(s->LocalAt(13), Value("initial"))); if (static_cast<bool>(v17647)) return v17647; v17647 = ([&]() -> Value { auto v17648 = ([&]() -> Value { auto fn17650 = PrepareDictionaryGet(Get(s->LocalAt(16), Value("shed"))); Arguments args17651; args17651.positional.reserve(2); args17651.Add(Value("SHEEP"), false); args17651.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn17650, std::move(args17651)); }()); Value v17649; v17649 = Value(int64_t{6}); if (!static_cast<bool>(Binary("GtE", v17648, v17649))) return Value(false); v17648 = v17649; return Value(true); }()); return v17647; }()); return v17644; }());
s->SetAt(8, v17643);
if (static_cast<bool>(Unary("Not", s->LocalAt(8)))) {
auto v17652 = s->Global("_V233_REPORT");
auto v17653 = Value("sheep_purchase_shortfalls");
auto v17654 = Get(v17652, v17653);
Put(v17652, v17653, Inplace("Add", v17654, Value(int64_t{1})));
}
else {
if (static_cast<bool>(([&]() -> Value { auto v17655 = ([&]() -> Value { auto fn17657 = s->Global("len"); Arguments args17658; args17658.Add(Get(s->LocalAt(7), Value("hands")), false); return Call(c, fn17657, std::move(args17658)); }()); Value v17656; v17656 = ([&]() -> Value { auto v17659 = ([&]() -> Value { auto v17660 = Get(s->LocalAt(13), Value("first")); return Binary("Add", v17660, ([&]() -> Value { auto fn17661 = PrepareDictionaryGet(s->LocalAt(13)); Arguments args17662; args17662.positional.reserve(2); args17662.Add(Value("count"), false); args17662.Add(Value(int64_t{2}), false); return CallDictionaryGet(c, fn17661, std::move(args17662)); }())); }()); return Binary("Sub", v17659, Value(int64_t{1})); }()); if (!static_cast<bool>(Binary("Lt", v17655, v17656))) return Value(false); v17655 = v17656; return Value(true); }()))) {
auto v17663 = s->Global("_V233_REPORT");
auto v17664 = Value("sheep_hire_shortfalls");
auto v17665 = Get(v17663, v17664);
Put(v17663, v17664, Inplace("Add", v17665, Value(int64_t{1})));
}
else {
if (static_cast<bool>(([&]() -> Value { auto v17666 = ([&]() -> Value { auto fn17668 = PrepareDictionaryGet(s->LocalAt(13)); Arguments args17669; args17669.positional.reserve(2); args17669.Add(Value("count"), false); args17669.Add(Value(int64_t{2}), false); return CallDictionaryGet(c, fn17668, std::move(args17669)); }()); Value v17667; v17667 = Value(int64_t{1}); if (!static_cast<bool>(Binary("Eq", v17666, v17667))) return Value(false); v17666 = v17667; return Value(true); }()))) {
auto v17670 = ([&]() -> Value { auto comp17671 = std::make_shared<Scope>(); comp17671->globals = s->globals; comp17671->parent = s; static constexpr const char* comp17671_names[] = {"t"}; comp17671->PrepareSlots(comp17671_names); auto result17672 = List(); for (const auto& item17673 : Iterate(Get(s->LocalAt(13), Value("targets")))) { comp17671->SetAt(0, item17673); result17672.node()->sequence.push_back(([&]() -> Value { auto fn17674 = comp17671->Global("tuple"); Arguments args17675; args17675.Add(comp17671->LocalAt(0), false); return Call(c, fn17674, std::move(args17675)); }())); } return result17672; }());
Put(Get(s->LocalAt(19), Value("workers")), Get(s->LocalAt(13), Value("first")), v17670);
auto v17676 = s->Global("_V233_REPORT");
auto v17677 = Value("sheep_workers_confirmed");
auto v17678 = Get(v17676, v17677);
Put(v17676, v17677, Inplace("Add", v17678, Value(int64_t{1})));
auto v17679 = s->Global("_SL_REPORT");
auto v17680 = Value("confirmed");
auto v17681 = Get(v17679, v17680);
Put(v17679, v17680, Inplace("Add", v17681, Value(int64_t{1})));
}
else {
for (const auto& item17682 : Iterate(([&]() -> Value { auto fn17683 = s->Global("range"); Arguments args17684; args17684.Add(Value(int64_t{2}), false); return Call(c, fn17683, std::move(args17684)); }()))) {
s->SetAt(10, item17682);
auto v17685 = ([&]() -> Value { auto comp17686 = std::make_shared<Scope>(); comp17686->globals = s->globals; comp17686->parent = s; static constexpr const char* comp17686_names[] = {"x"}; comp17686->PrepareSlots(comp17686_names); auto result17687 = List(); for (const auto& item17688 : Iterate(([&]() -> Value { auto fn17689 = s->Global("range"); Arguments args17690; args17690.positional.reserve(2); args17690.Add(Value(int64_t{5}), false); args17690.Add(Value(int64_t{8}), false); return Call(c, fn17689, std::move(args17690)); }()))) { comp17686->SetAt(0, item17688); result17687.node()->sequence.push_back(Tuple({comp17686->LocalAt(0), ([&]() -> Value { auto v17691 = Value(int64_t{5}); return Binary("Add", v17691, comp17686->Captured("i")); }())})); } return result17687; }());
Put(Get(s->LocalAt(19), Value("workers")), ([&]() -> Value { auto v17692 = Get(s->LocalAt(13), Value("first")); return Binary("Add", v17692, s->LocalAt(10)); }()), v17685);
}
auto v17693 = s->Global("_V233_REPORT");
auto v17694 = Value("sheep_workers_confirmed");
auto v17695 = Get(v17693, v17694);
Put(v17693, v17694, Inplace("Add", v17695, Value(int64_t{2})));
if (static_cast<bool>(Get(s->LocalAt(13), Value("initial")))) {
auto v17696 = Value(true);
Put(s->LocalAt(19), Value("committed"), v17696);
auto v17697 = s->Global("_V233_REPORT");
auto v17698 = Value("sheep_committed");
auto v17699 = Get(v17697, v17698);
Put(v17697, v17698, Inplace("Add", v17699, Value(int64_t{1})));
}
}
}
}
}
auto v17700 = ([&]() -> Value { auto fn17701 = s->Global("_v233_request"); Arguments args17702; args17702.positional.reserve(4); args17702.Add(s->LocalAt(12), false); args17702.Add(s->LocalAt(0), false); args17702.Add(s->LocalAt(19), false); args17702.Add(Get(Attribute(Attribute(s->Global("_IMPL"), "chassis"), "players"), s->LocalAt(14)), false); return Call(c, fn17701, std::move(args17702)); }());
s->SetAt(0, v17700);
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto fn17703 = PrepareDictionaryGet(s->LocalAt(19)); Arguments args17704; args17704.Add(Value("committed"), false); return CallDictionaryGet(c, fn17703, std::move(args17704)); }())))) {
return s->LocalAt(0);
}
auto v17705 = ([&]() -> Value { auto fn17706 = Attribute(s->Global("copy"), "deepcopy"); Arguments args17707; args17707.Add(s->LocalAt(0), false); return Call(c, fn17706, std::move(args17707)); }());
s->SetAt(17, v17705);
auto v17708 = ([&]() -> Value { auto v17709 = List({([&]() -> Value { auto v17710 = ([&]() -> Value { auto fn17711 = PrepareDictionaryGet(s->LocalAt(17)); Arguments args17712; args17712.Add(Value("farmer"), false); return CallDictionaryGet(c, fn17711, std::move(args17712)); }()); if (static_cast<bool>(v17710)) return v17710; v17710 = List({Value("PASS")}); return v17710; }())}); return Binary("Add", v17709, ([&]() -> Value { auto fn17713 = s->Global("list"); Arguments args17714; args17714.Add(([&]() -> Value { auto v17715 = ([&]() -> Value { auto fn17716 = PrepareDictionaryGet(s->LocalAt(17)); Arguments args17717; args17717.Add(Value("hands"), false); return CallDictionaryGet(c, fn17716, std::move(args17717)); }()); if (static_cast<bool>(v17715)) return v17715; v17715 = List({}); return v17715; }()), false); return Call(c, fn17713, std::move(args17714)); }())); }());
s->SetAt(3, v17708);
auto v17718 = s->LocalAt(3);
s->SetAt(3, Inplace("Add", v17718, ([&]() -> Value { auto comp17719 = std::make_shared<Scope>(); comp17719->globals = s->globals; comp17719->parent = s; static constexpr const char* comp17719_names[] = {"_"}; comp17719->PrepareSlots(comp17719_names); auto result17720 = List(); for (const auto& item17721 : Iterate(([&]() -> Value { auto fn17722 = s->Global("range"); Arguments args17723; args17723.Add(([&]() -> Value { auto v17724 = ([&]() -> Value { auto v17725 = ([&]() -> Value { auto fn17726 = s->Global("len"); Arguments args17727; args17727.Add(Get(s->LocalAt(7), Value("hands")), false); return Call(c, fn17726, std::move(args17727)); }()); return Binary("Add", v17725, Value(int64_t{1})); }()); return Binary("Sub", v17724, ([&]() -> Value { auto fn17728 = s->Global("len"); Arguments args17729; args17729.Add(s->LocalAt(3), false); return Call(c, fn17728, std::move(args17729)); }())); }()), false); return Call(c, fn17722, std::move(args17723)); }()))) { comp17719->SetAt(0, item17721); result17720.node()->sequence.push_back(List({Value("PASS")})); } return result17720; }())));
auto v17730 = ([&]() -> Value { auto dict17731 = Dict(); return dict17731; }());
Put(s->LocalAt(19), Value("work"), v17730);
for (const auto& item17732 : Iterate(([&]() -> Value { auto fn17733 = Attribute(Get(s->LocalAt(19), Value("workers")), "items"); Arguments args17734; return Call(c, fn17733, std::move(args17734)); }()))) {
auto unpack17735 = Iterate(item17732);
ValidateUnpack(unpack17735, 2, false);
s->SetAt(1, unpack17735.at(0));
s->SetAt(22, unpack17735.at(1));
auto v17736 = ([&]() -> Value { auto fn17737 = s->Global("_v233_worker"); Arguments args17738; args17738.positional.reserve(3); args17738.Add(s->LocalAt(12), false); args17738.Add(s->LocalAt(1), false); args17738.Add(s->LocalAt(22), false); return Call(c, fn17737, std::move(args17738)); }());
s->SetAt(2, v17736);
auto v17739 = s->LocalAt(2);
Put(s->LocalAt(3), s->LocalAt(1), v17739);
auto v17740 = ([&]() -> Value { auto dict17741 = Dict(); auto key17742 = Value("step"); Put(dict17741, key17742, s->LocalAt(20)); auto key17743 = Value("command"); Put(dict17741, key17743, s->LocalAt(2)); auto key17744 = Value("inventory"); Put(dict17741, key17744, ([&]() -> Value { auto fn17745 = s->Global("dict"); Arguments args17746; args17746.Add(Get(Get(s->LocalAt(16), Value("inventories")), s->LocalAt(1)), false); return Call(c, fn17745, std::move(args17746)); }())); return dict17741; }());
Put(Get(s->LocalAt(19), Value("work")), s->LocalAt(1), v17740);
}
auto v17747 = Tuple({Get(s->LocalAt(3), Value(int64_t{0})), Slice(s->LocalAt(3), Value(int64_t{1}), Value{}, Value{})});
auto unpack17748 = Iterate(v17747);
ValidateUnpack(unpack17748, 2, false);
Put(s->LocalAt(17), Value("farmer"), unpack17748.at(0));
Put(s->LocalAt(17), Value("hands"), unpack17748.at(1));
auto v17749 = ([&]() -> Value { auto fn17750 = s->Global("_v234_rescue"); Arguments args17751; args17751.positional.reserve(3); args17751.Add(s->LocalAt(12), false); args17751.Add(s->LocalAt(17), false); args17751.Add(s->LocalAt(19), false); return Call(c, fn17750, std::move(args17751)); }());
s->SetAt(17, v17749);
auto v17752 = ([&]() -> Value { auto fn17753 = s->Global("projected_shed"); Arguments args17754; args17754.positional.reserve(2); args17754.Add(s->LocalAt(17), false); args17754.Add(([&]() -> Value { auto fn17755 = s->Global("FarmView"); Arguments args17756; args17756.Add(s->LocalAt(12), false); return Call(c, fn17755, std::move(args17756)); }()), false); return Call(c, fn17753, std::move(args17754)); }());
s->SetAt(21, v17752);
for (const auto& item17757 : Iterate(Tuple({Value("WOOL"), Value("FERTILIZER")}))) {
s->SetAt(11, item17757);
auto v17758 = ([&]() -> Value { auto fn17759 = s->Global("sum"); Arguments args17760; args17760.Add(([&]() -> Value { auto comp17761 = std::make_shared<Scope>(); comp17761->globals = s->globals; comp17761->parent = s; static constexpr const char* comp17761_names[] = {"o"}; comp17761->PrepareSlots(comp17761_names); auto result17762 = List(); for (const auto& item17763 : Iterate(Get(s->LocalAt(17), Value("market")))) { comp17761->SetAt(0, item17763); if (!static_cast<bool>(([&]() -> Value { auto v17764 = Slice(comp17761->LocalAt(0), Value{}, Value(int64_t{2}), Value{}); Value v17765; v17765 = List({Value("SELL"), comp17761->Captured("item")}); if (!static_cast<bool>(Binary("Eq", v17764, v17765))) return Value(false); v17764 = v17765; return Value(true); }()))) continue; result17762.node()->sequence.push_back(([&]() -> Value { auto fn17766 = comp17761->Global("int"); Arguments args17767; args17767.Add(Get(comp17761->LocalAt(0), Value(int64_t{2})), false); return Call(c, fn17766, std::move(args17767)); }())); } return result17762; }()), false); return Call(c, fn17759, std::move(args17760)); }());
s->SetAt(18, v17758);
auto v17768 = ([&]() -> Value { auto fn17769 = s->Global("min"); Arguments args17770; args17770.positional.reserve(2); args17770.Add(Get(Get(s->LocalAt(19), Value("credit")), s->LocalAt(11)), false); args17770.Add(([&]() -> Value { auto fn17771 = s->Global("max"); Arguments args17772; args17772.positional.reserve(2); args17772.Add(Value(int64_t{0}), false); args17772.Add(([&]() -> Value { auto v17773 = ([&]() -> Value { auto fn17774 = PrepareDictionaryGet(s->LocalAt(21)); Arguments args17775; args17775.positional.reserve(2); args17775.Add(s->LocalAt(11), false); args17775.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn17774, std::move(args17775)); }()); return Binary("Sub", v17773, s->LocalAt(18)); }()), false); return Call(c, fn17771, std::move(args17772)); }()), false); return Call(c, fn17769, std::move(args17770)); }());
s->SetAt(5, v17768);
if (static_cast<bool>(([&]() -> Value { auto v17776 = s->LocalAt(5); if (!static_cast<bool>(v17776)) return v17776; v17776 = ([&]() -> Value { auto v17777 = ([&]() -> Value { auto fn17779 = s->Global("len"); Arguments args17780; args17780.Add(Get(s->LocalAt(17), Value("market")), false); return Call(c, fn17779, std::move(args17780)); }()); Value v17778; v17778 = s->Global("MAX_ORDERS"); if (!static_cast<bool>(Binary("Lt", v17777, v17778))) return Value(false); v17777 = v17778; return Value(true); }()); return v17776; }()))) {
(void)([&]() -> Value { auto fn17781 = Attribute(Get(s->LocalAt(17), Value("market")), "append"); Arguments args17782; args17782.Add(List({Value("SELL"), s->LocalAt(11), s->LocalAt(5)}), false); return Call(c, fn17781, std::move(args17782)); }());
auto v17783 = Get(s->LocalAt(19), Value("credit"));
auto v17784 = s->LocalAt(11);
auto v17785 = Get(v17783, v17784);
Put(v17783, v17784, Inplace("Sub", v17785, s->LocalAt(5)));
auto v17786 = s->Global("_V233_REPORT");
auto v17787 = (static_cast<bool>(([&]() -> Value { auto v17789 = s->LocalAt(11); Value v17790; v17790 = Value("WOOL"); if (!static_cast<bool>(Binary("Eq", v17789, v17790))) return Value(false); v17789 = v17790; return Value(true); }())) ? Value("sheep_extra_wool_sales") : Value("sheep_extra_fert_sales"));
auto v17788 = Get(v17786, v17787);
Put(v17786, v17787, Inplace("Add", v17788, s->LocalAt(5)));
}
}
return s->LocalAt(17);
return {};
}
}  // namespace kagg::opponents::compiled
