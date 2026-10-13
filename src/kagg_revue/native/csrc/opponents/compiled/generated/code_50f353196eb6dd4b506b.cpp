// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_50f353196eb6dd4b506b(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"_", "action", "actor", "all_commands", "amount", "before_inv", "before_shed", "blocked", "cap", "command", "config", "decay_coordinates", "delta", "demand", "deposited", "detailed", "dx", "dy", "events", "executed", "expiry_end", "farm", "farm0", "final_liquidate", "inv", "item", "n", "nx", "ny", "obs", "offset", "order_cap", "overflow", "planted", "pos", "pre_market", "preserve_final_commands", "prices", "private", "private0", "quantity", "requested", "rows", "schedule", "size", "snapshots", "sold", "step", "t", "turns", "xy"};
s->PrepareSlots(s_names);
auto v16581 = ([&]() -> Value { auto fn16582 = s->Global("_settings"); Arguments args16583; args16583.Add(s->LocalAt(10), false); return Call(c, fn16582, std::move(args16583)); }());
auto unpack16584 = Iterate(v16581);
ValidateUnpack(unpack16584, 4, false);
s->SetAt(44, unpack16584.at(0));
s->SetAt(49, unpack16584.at(1));
s->SetAt(8, unpack16584.at(2));
s->SetAt(31, unpack16584.at(3));
auto v16585 = ([&]() -> Value { auto fn16586 = s->Global("int"); Arguments args16587; args16587.Add(([&]() -> Value { auto fn16588 = s->Global("_get"); Arguments args16589; args16589.positional.reserve(3); args16589.Add(s->LocalAt(29), false); args16589.Add(Value("step"), false); args16589.Add(Unary("USub", Value(int64_t{1})), false); return Call(c, fn16588, std::move(args16589)); }()), false); return Call(c, fn16586, std::move(args16587)); }());
s->SetAt(47, v16585);
if (static_cast<bool>(([&]() -> Value { auto v16590 = ([&]() -> Value { auto v16591 = s->LocalAt(47); Value v16592; v16592 = s->Global("START"); if (!static_cast<bool>(Binary("Lt", v16591, v16592))) return Value(false); v16591 = v16592; return Value(true); }()); if (static_cast<bool>(v16590)) return v16590; v16590 = ([&]() -> Value { auto v16593 = ([&]() -> Value { auto v16595 = ([&]() -> Value { auto v16596 = s->LocalAt(47); return Binary("Add", v16596, ([&]() -> Value { auto fn16597 = s->Global("len"); Arguments args16598; args16598.Add(s->LocalAt(43), false); return Call(c, fn16597, std::move(args16598)); }())); }()); return Binary("Sub", v16595, Value(int64_t{1})); }()); Value v16594; v16594 = s->Global("FINAL"); if (!static_cast<bool>(Binary("Gt", v16593, v16594))) return Value(false); v16593 = v16594; return Value(true); }()); if (static_cast<bool>(v16590)) return v16590; v16590 = Unary("Not", s->LocalAt(43)); return v16590; }()))) {
Raise(([&]() -> Value { auto fn16599 = s->Global("Unsupported"); Arguments args16600; args16600.Add(Value("outside 712..718; no day boundary or terminal auto-drop"), false); return Call(c, fn16599, std::move(args16600)); }()));
}
if (static_cast<bool>(([&]() -> Value { auto comp16601 = std::make_shared<Scope>(); comp16601->globals = s->globals; comp16601->parent = s; static constexpr const char* comp16601_names[] = {"t"}; comp16601->PrepareSlots(comp16601_names); auto result16602 = List(); for (const auto& item16603 : Iterate(([&]() -> Value { auto fn16604 = s->Global("range"); Arguments args16605; args16605.positional.reserve(2); args16605.Add(s->LocalAt(47), false); args16605.Add(([&]() -> Value { auto v16606 = s->LocalAt(47); return Binary("Add", v16606, ([&]() -> Value { auto fn16607 = s->Global("len"); Arguments args16608; args16608.Add(s->LocalAt(43), false); return Call(c, fn16607, std::move(args16608)); }())); }()), false); return Call(c, fn16604, std::move(args16605)); }()))) { comp16601->SetAt(0, item16603); if (static_cast<bool>(([&]() -> Value { auto v16609 = ([&]() -> Value { auto v16611 = ([&]() -> Value { auto v16612 = comp16601->LocalAt(0); return Binary("Add", v16612, Value(int64_t{1})); }()); return Binary("Mod", v16611, comp16601->Captured("turns")); }()); Value v16610; v16610 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v16609, v16610))) return Value(false); v16609 = v16610; return Value(true); }()))) return Value(true); } return Value(false); }()))) {
Raise(([&]() -> Value { auto fn16613 = s->Global("Unsupported"); Arguments args16614; args16614.Add(Value("day boundary"), false); return Call(c, fn16613, std::move(args16614)); }()));
}
auto v16615 = ([&]() -> Value { auto fn16616 = s->Global("physical_state"); Arguments args16617; args16617.Add(s->LocalAt(29), false); return Call(c, fn16616, std::move(args16617)); }());
auto unpack16618 = Iterate(v16615);
ValidateUnpack(unpack16618, 2, false);
s->SetAt(22, unpack16618.at(0));
s->SetAt(39, unpack16618.at(1));
auto v16619 = ([&]() -> Value { auto fn16620 = s->Global("_clone_state"); Arguments args16621; args16621.positional.reserve(2); args16621.Add(s->LocalAt(22), false); args16621.Add(s->LocalAt(39), false); return Call(c, fn16620, std::move(args16621)); }());
auto unpack16622 = Iterate(v16619);
ValidateUnpack(unpack16622, 2, false);
s->SetAt(21, unpack16622.at(0));
s->SetAt(38, unpack16622.at(1));
auto v16623 = ([&]() -> Value { auto v16624 = ([&]() -> Value { auto v16625 = s->LocalAt(47); return Binary("Add", v16625, ([&]() -> Value { auto fn16626 = s->Global("len"); Arguments args16627; args16627.Add(s->LocalAt(43), false); return Call(c, fn16626, std::move(args16627)); }())); }()); return Binary("Sub", v16624, Value(int64_t{1})); }());
s->SetAt(20, v16623);
auto v16628 = ([&]() -> Value { auto comp16629 = std::make_shared<Scope>(); comp16629->globals = s->globals; comp16629->parent = s; static constexpr const char* comp16629_names[] = {"row", "tile", "x", "y"}; comp16629->PrepareSlots(comp16629_names); auto result16630 = List(); for (const auto& item16631 : Iterate(([&]() -> Value { auto fn16632 = s->Global("enumerate"); Arguments args16633; args16633.Add(Get(s->LocalAt(21), Value("tiles")), false); return Call(c, fn16632, std::move(args16633)); }()))) { auto unpack16634 = Iterate(item16631); ValidateUnpack(unpack16634, 2, false); comp16629->SetAt(3, unpack16634.at(0)); comp16629->SetAt(0, unpack16634.at(1)); for (const auto& item16635 : Iterate(([&]() -> Value { auto fn16636 = comp16629->Global("enumerate"); Arguments args16637; args16637.Add(comp16629->LocalAt(0), false); return Call(c, fn16636, std::move(args16637)); }()))) { auto unpack16638 = Iterate(item16635); ValidateUnpack(unpack16638, 2, false); comp16629->SetAt(2, unpack16638.at(0)); comp16629->SetAt(1, unpack16638.at(1)); if (!static_cast<bool>(([&]() -> Value { auto v16639 = ([&]() -> Value { auto fn16640 = comp16629->Global("isinstance"); Arguments args16641; args16641.positional.reserve(2); args16641.Add(comp16629->LocalAt(1), false); args16641.Add(comp16629->Global("dict"), false); return Call(c, fn16640, std::move(args16641)); }()); if (!static_cast<bool>(v16639)) return v16639; v16639 = ([&]() -> Value { auto v16642 = ([&]() -> Value { auto fn16644 = PrepareDictionaryGet(comp16629->LocalAt(1)); Arguments args16645; args16645.Add(Value("kind"), false); return CallDictionaryGet(c, fn16644, std::move(args16645)); }()); Value v16643; v16643 = Value("PLANT"); if (!static_cast<bool>(Binary("Eq", v16642, v16643))) return Value(false); v16642 = v16643; return Value(true); }()); if (!static_cast<bool>(v16639)) return v16639; v16639 = ([&]() -> Value { auto v16646 = Value(int64_t{0}); Value v16647; v16647 = Get(comp16629->LocalAt(1), Value("max_lifespan_step")); if (!static_cast<bool>(Binary("LtE", v16646, v16647))) return Value(false); v16646 = v16647; v16647 = comp16629->Captured("expiry_end"); if (!static_cast<bool>(Binary("LtE", v16646, v16647))) return Value(false); v16646 = v16647; return Value(true); }()); return v16639; }()))) continue; result16630.node()->sequence.push_back(Tuple({comp16629->LocalAt(3), comp16629->LocalAt(2)})); } } return Set(result16630.node()->sequence); }());
s->SetAt(11, v16628);
auto v16648 = ([&]() -> Value { auto v16649 = Value(int64_t{1}); return Binary("Add", v16649, ([&]() -> Value { auto fn16650 = s->Global("len"); Arguments args16651; args16651.Add(Get(s->LocalAt(21), Value("hands")), false); return Call(c, fn16650, std::move(args16651)); }())); }());
s->SetAt(26, v16648);
if (static_cast<bool>(([&]() -> Value { auto v16652 = ([&]() -> Value { auto v16653 = ([&]() -> Value { auto fn16655 = s->Global("len"); Arguments args16656; args16656.Add(Get(s->LocalAt(38), Value("inventories")), false); return Call(c, fn16655, std::move(args16656)); }()); Value v16654; v16654 = s->LocalAt(26); if (!static_cast<bool>(Binary("NotEq", v16653, v16654))) return Value(false); v16653 = v16654; return Value(true); }()); if (static_cast<bool>(v16652)) return v16652; v16652 = ([&]() -> Value { auto v16657 = s->LocalAt(26); Value v16658; v16658 = Value(int64_t{32}); if (!static_cast<bool>(Binary("Gt", v16657, v16658))) return Value(false); v16657 = v16658; return Value(true); }()); return v16652; }()))) {
Raise(([&]() -> Value { auto fn16659 = s->Global("Unsupported"); Arguments args16660; args16660.Add(Value("invalid/unbounded worker inventory shape"), false); return Call(c, fn16659, std::move(args16660)); }()));
}
(void)([&]() -> Value { auto fn16661 = s->Global("_validate"); Arguments args16662; args16662.positional.reserve(3); args16662.Add(s->LocalAt(43), false); args16662.Add(s->LocalAt(26), false); args16662.Add(s->LocalAt(31), false); return Call(c, fn16661, std::move(args16662)); }());
auto v16663 = ([&]() -> Value { auto comp16664 = std::make_shared<Scope>(); comp16664->globals = s->globals; comp16664->parent = s; static constexpr const char* comp16664_names[] = {"_"}; comp16664->PrepareSlots(comp16664_names); auto result16665 = List(); for (const auto& item16666 : Iterate(([&]() -> Value { auto fn16667 = s->Global("range"); Arguments args16668; args16668.Add(s->LocalAt(26), false); return Call(c, fn16667, std::move(args16668)); }()))) { comp16664->SetAt(0, item16666); result16665.node()->sequence.push_back(([&]() -> Value { auto fn16669 = comp16664->Global("dict"); Arguments args16670; return Call(c, fn16669, std::move(args16670)); }())); } return result16665; }());
s->SetAt(14, v16663);
auto v16671 = ([&]() -> Value { auto dict16672 = Dict(); return dict16672; }());
s->SetAt(46, v16671);
auto v16673 = Tuple({List({}), List({}), List({})});
auto unpack16674 = Iterate(v16673);
ValidateUnpack(unpack16674, 3, false);
s->SetAt(45, unpack16674.at(0));
s->SetAt(42, unpack16674.at(1));
s->SetAt(18, unpack16674.at(2));
auto v16675 = ([&]() -> Value { auto fn16676 = s->Global("_clone_schedule"); Arguments args16677; args16677.Add(s->LocalAt(43), false); return Call(c, fn16676, std::move(args16677)); }());
s->SetAt(19, v16675);
auto v16678 = Value(int64_t{0});
s->SetAt(32, v16678);
for (const auto& item16679 : Iterate(([&]() -> Value { auto fn16680 = s->Global("enumerate"); Arguments args16681; args16681.Add(s->LocalAt(19), false); return Call(c, fn16680, std::move(args16681)); }()))) {
auto unpack16682 = Iterate(item16679);
ValidateUnpack(unpack16682, 2, false);
s->SetAt(30, unpack16682.at(0));
s->SetAt(1, unpack16682.at(1));
auto v16683 = ([&]() -> Value { auto v16684 = s->LocalAt(47); return Binary("Add", v16684, s->LocalAt(30)); }());
s->SetAt(48, v16683);
if (static_cast<bool>(s->LocalAt(15))) {
(void)([&]() -> Value { auto fn16685 = Attribute(s->LocalAt(45), "append"); Arguments args16686; args16686.Add(([&]() -> Value { auto fn16687 = s->Global("_clone_state"); Arguments args16688; args16688.positional.reserve(2); args16688.Add(s->LocalAt(21), false); args16688.Add(s->LocalAt(38), false); return Call(c, fn16687, std::move(args16688)); }()), false); return Call(c, fn16685, std::move(args16686)); }());
}
if (static_cast<bool>(([&]() -> Value { auto v16689 = ([&]() -> Value { auto v16690 = s->LocalAt(48); Value v16691; v16691 = s->Global("FINAL"); if (!static_cast<bool>(Binary("Eq", v16690, v16691))) return Value(false); v16690 = v16691; return Value(true); }()); if (!static_cast<bool>(v16689)) return v16689; v16689 = Unary("Not", s->LocalAt(36)); return v16689; }()))) {
auto v16692 = ([&]() -> Value { auto fn16693 = s->Global("shop_liquidation"); Arguments args16694; args16694.positional.reserve(3); args16694.Add(s->LocalAt(21), false); args16694.Add(s->LocalAt(38), false); args16694.Add(Get(([&]() -> Value { auto fn16695 = s->Global("_get"); Arguments args16696; args16696.positional.reserve(2); args16696.Add(s->LocalAt(29), false); args16696.Add(Value("market"), false); return Call(c, fn16695, std::move(args16696)); }()), Value("prices")), false); return Call(c, fn16693, std::move(args16694)); }());
s->SetAt(1, v16692);
auto v16697 = s->LocalAt(1);
Put(s->LocalAt(19), s->LocalAt(30), v16697);
}
auto v16698 = ([&]() -> Value { Arguments args16699; args16699.Add(([&]() -> Value { auto fn16700 = PrepareDictionaryGet(s->LocalAt(1)); Arguments args16701; args16701.positional.reserve(2); args16701.Add(Value("farmer"), false); args16701.Add(List({Value("PASS")}), false); return CallDictionaryGet(c, fn16700, std::move(args16701)); }()), false); args16699.Add(([&]() -> Value { auto fn16702 = PrepareDictionaryGet(s->LocalAt(1)); Arguments args16703; args16703.positional.reserve(2); args16703.Add(Value("hands"), false); args16703.Add(List({}), false); return CallDictionaryGet(c, fn16702, std::move(args16703)); }()), true); return List(std::move(args16699.positional)); }());
s->SetAt(3, v16698);
auto v16704 = ([&]() -> Value { auto dict16705 = Dict(); return dict16705; }());
s->SetAt(13, v16704);
for (const auto& item16706 : Iterate(s->LocalAt(3))) {
s->SetAt(9, item16706);
if (static_cast<bool>(([&]() -> Value { auto v16707 = Get(s->LocalAt(9), Value(int64_t{0})); Value v16708; v16708 = Value("PLANT"); if (!static_cast<bool>(Binary("Eq", v16707, v16708))) return Value(false); v16707 = v16708; return Value(true); }()))) {
auto v16709 = ([&]() -> Value { auto v16710 = ([&]() -> Value { auto fn16711 = PrepareDictionaryGet(s->LocalAt(13)); Arguments args16712; args16712.positional.reserve(2); args16712.Add(Get(s->LocalAt(9), Value(int64_t{1})), false); args16712.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn16711, std::move(args16712)); }()); return Binary("Add", v16710, Value(int64_t{1})); }());
Put(s->LocalAt(13), Get(s->LocalAt(9), Value(int64_t{1})), v16709);
}
}
auto v16713 = ([&]() -> Value { auto comp16714 = std::make_shared<Scope>(); comp16714->globals = s->globals; comp16714->parent = s; static constexpr const char* comp16714_names[] = {"count", "item"}; comp16714->PrepareSlots(comp16714_names); auto result16715 = List(); for (const auto& item16716 : Iterate(([&]() -> Value { auto fn16717 = Attribute(s->LocalAt(13), "items"); Arguments args16718; return Call(c, fn16717, std::move(args16718)); }()))) { auto unpack16719 = Iterate(item16716); ValidateUnpack(unpack16719, 2, false); comp16714->SetAt(1, unpack16719.at(0)); comp16714->SetAt(0, unpack16719.at(1)); if (!static_cast<bool>(([&]() -> Value { auto v16720 = comp16714->LocalAt(0); Value v16721; v16721 = ([&]() -> Value { auto fn16722 = PrepareDictionaryGet(Get(comp16714->Captured("private"), Value("seeds"))); Arguments args16723; args16723.positional.reserve(2); args16723.Add(comp16714->LocalAt(1), false); args16723.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn16722, std::move(args16723)); }()); if (!static_cast<bool>(Binary("Gt", v16720, v16721))) return Value(false); v16720 = v16721; return Value(true); }()))) continue; result16715.node()->sequence.push_back(comp16714->LocalAt(1)); } return Set(result16715.node()->sequence); }());
s->SetAt(7, v16713);
for (const auto& item16724 : Iterate(([&]() -> Value { auto fn16725 = s->Global("enumerate"); Arguments args16726; args16726.Add(([&]() -> Value { auto fn16727 = s->Global("_commands"); Arguments args16728; args16728.positional.reserve(2); args16728.Add(s->LocalAt(1), false); args16728.Add(s->LocalAt(26), false); return Call(c, fn16727, std::move(args16728)); }()), false); return Call(c, fn16725, std::move(args16726)); }()))) {
auto unpack16729 = Iterate(item16724);
ValidateUnpack(unpack16729, 2, false);
s->SetAt(2, unpack16729.at(0));
s->SetAt(9, unpack16729.at(1));
if (static_cast<bool>(([&]() -> Value { auto v16730 = ([&]() -> Value { auto v16731 = Get(s->LocalAt(9), Value(int64_t{0})); Value v16732; v16732 = Value("PLANT"); if (!static_cast<bool>(Binary("Eq", v16731, v16732))) return Value(false); v16731 = v16732; return Value(true); }()); if (!static_cast<bool>(v16730)) return v16730; v16730 = ([&]() -> Value { auto v16733 = Get(s->LocalAt(9), Value(int64_t{1})); Value v16734; v16734 = s->LocalAt(7); if (!static_cast<bool>(Binary("In", v16733, v16734))) return Value(false); v16733 = v16734; return Value(true); }()); return v16730; }()))) {
auto v16735 = List({Value("PASS")});
s->SetAt(9, v16735);
}
if (static_cast<bool>(([&]() -> Value { auto v16736 = Get(s->LocalAt(9), Value(int64_t{0})); Value v16737; v16737 = Value("PASS"); if (!static_cast<bool>(Binary("Eq", v16736, v16737))) return Value(false); v16736 = v16737; return Value(true); }()))) {
continue;
}
auto v16738 = (static_cast<bool>(([&]() -> Value { auto v16739 = s->LocalAt(2); Value v16740; v16740 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v16739, v16740))) return Value(false); v16739 = v16740; return Value(true); }())) ? Get(s->LocalAt(21), Value("farmer")) : Get(Get(s->LocalAt(21), Value("hands")), ([&]() -> Value { auto v16741 = s->LocalAt(2); return Binary("Sub", v16741, Value(int64_t{1})); }())));
s->SetAt(34, v16738);
if (static_cast<bool>(([&]() -> Value { auto v16742 = Get(s->LocalAt(9), Value(int64_t{0})); Value v16743; v16743 = s->Global("FARMER_MOVES"); if (!static_cast<bool>(Binary("In", v16742, v16743))) return Value(false); v16742 = v16743; return Value(true); }()))) {
auto v16744 = Get(s->Global("FARMER_MOVES"), Get(s->LocalAt(9), Value(int64_t{0})));
auto unpack16745 = Iterate(v16744);
ValidateUnpack(unpack16745, 2, false);
s->SetAt(16, unpack16745.at(0));
s->SetAt(17, unpack16745.at(1));
auto v16746 = Tuple({([&]() -> Value { auto v16747 = Get(s->LocalAt(34), Value(int64_t{0})); return Binary("Add", v16747, s->LocalAt(16)); }()), ([&]() -> Value { auto v16748 = Get(s->LocalAt(34), Value(int64_t{1})); return Binary("Add", v16748, s->LocalAt(17)); }())});
auto unpack16749 = Iterate(v16746);
ValidateUnpack(unpack16749, 2, false);
s->SetAt(27, unpack16749.at(0));
s->SetAt(28, unpack16749.at(1));
if (static_cast<bool>(([&]() -> Value { auto v16750 = ([&]() -> Value { auto v16751 = Value(int64_t{0}); Value v16752; v16752 = s->LocalAt(27); if (!static_cast<bool>(Binary("LtE", v16751, v16752))) return Value(false); v16751 = v16752; v16752 = s->LocalAt(44); if (!static_cast<bool>(Binary("Lt", v16751, v16752))) return Value(false); v16751 = v16752; return Value(true); }()); if (!static_cast<bool>(v16750)) return v16750; v16750 = ([&]() -> Value { auto v16753 = Value(int64_t{0}); Value v16754; v16754 = s->LocalAt(28); if (!static_cast<bool>(Binary("LtE", v16753, v16754))) return Value(false); v16753 = v16754; v16754 = s->LocalAt(44); if (!static_cast<bool>(Binary("Lt", v16753, v16754))) return Value(false); v16753 = v16754; return Value(true); }()); return v16750; }()))) {
if (static_cast<bool>(([&]() -> Value { auto v16755 = s->LocalAt(2); Value v16756; v16756 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v16755, v16756))) return Value(false); v16755 = v16756; return Value(true); }()))) {
auto v16757 = List({s->LocalAt(27), s->LocalAt(28)});
Put(s->LocalAt(21), Value("farmer"), v16757);
}
else {
auto v16758 = List({s->LocalAt(27), s->LocalAt(28)});
Put(Get(s->LocalAt(21), Value("hands")), ([&]() -> Value { auto v16759 = s->LocalAt(2); return Binary("Sub", v16759, Value(int64_t{1})); }()), v16758);
}
}
continue;
}
if (static_cast<bool>(([&]() -> Value { auto v16760 = ([&]() -> Value { auto v16761 = Get(s->LocalAt(9), Value(int64_t{0})); Value v16762; v16762 = Value("DROP"); if (!static_cast<bool>(Binary("Eq", v16761, v16762))) return Value(false); v16761 = v16762; return Value(true); }()); if (!static_cast<bool>(v16760)) return v16760; v16760 = Unary("Not", Get(Get(s->LocalAt(38), Value("inventories")), s->LocalAt(2))); return v16760; }()))) {
continue;
}
auto v16763 = ([&]() -> Value { auto fn16764 = s->Global("tuple"); Arguments args16765; args16765.Add(s->LocalAt(34), false); return Call(c, fn16764, std::move(args16765)); }());
s->SetAt(50, v16763);
auto v16766 = Get(Get(s->LocalAt(38), Value("inventories")), s->LocalAt(2));
s->SetAt(24, v16766);
auto v16767 = (static_cast<bool>(([&]() -> Value { auto v16768 = Get(s->LocalAt(9), Value(int64_t{0})); Value v16769; v16769 = Set({Value("DROP"), Value("HARVEST"), Value("COLLECT_FERTILIZER")}); if (!static_cast<bool>(Binary("In", v16768, v16769))) return Value(false); v16768 = v16769; return Value(true); }())) ? ([&]() -> Value { auto fn16770 = s->Global("dict"); Arguments args16771; args16771.Add(s->LocalAt(24), false); return Call(c, fn16770, std::move(args16771)); }()) : Value{});
s->SetAt(5, v16767);
auto v16772 = (static_cast<bool>(([&]() -> Value { auto v16773 = Get(s->LocalAt(9), Value(int64_t{0})); Value v16774; v16774 = Set({Value("DROP"), Value("PLACE")}); if (!static_cast<bool>(Binary("In", v16773, v16774))) return Value(false); v16773 = v16774; return Value(true); }())) ? ([&]() -> Value { auto fn16775 = s->Global("dict"); Arguments args16776; args16776.Add(Get(s->LocalAt(38), Value("shed")), false); return Call(c, fn16775, std::move(args16776)); }()) : Value{});
s->SetAt(6, v16772);
(void)([&]() -> Value { auto fn16777 = s->Global("_apply_unit_action"); Arguments args16778; args16778.positional.reserve(8); args16778.Add(s->LocalAt(21), false); args16778.Add(s->LocalAt(38), false); args16778.Add(s->LocalAt(2), false); args16778.Add(s->LocalAt(9), false); args16778.Add(s->LocalAt(44), false); args16778.Add(([&]() -> Value { auto v16779 = s->LocalAt(48); return Binary("FloorDiv", v16779, s->LocalAt(49)); }()), false); args16778.Add(s->LocalAt(49), false); args16778.Add(s->LocalAt(8), false); return Call(c, fn16777, std::move(args16778)); }());
if (static_cast<bool>(([&]() -> Value { auto v16780 = Get(s->LocalAt(9), Value(int64_t{0})); Value v16781; v16781 = Value("PLANT"); if (!static_cast<bool>(Binary("Eq", v16780, v16781))) return Value(false); v16780 = v16781; return Value(true); }()))) {
auto v16782 = Get(Get(Get(s->LocalAt(21), Value("tiles")), Get(s->LocalAt(50), Value(int64_t{1}))), Get(s->LocalAt(50), Value(int64_t{0})));
s->SetAt(33, v16782);
if (static_cast<bool>(([&]() -> Value { auto v16783 = ([&]() -> Value { auto fn16784 = s->Global("isinstance"); Arguments args16785; args16785.positional.reserve(2); args16785.Add(s->LocalAt(33), false); args16785.Add(s->Global("dict"), false); return Call(c, fn16784, std::move(args16785)); }()); if (!static_cast<bool>(v16783)) return v16783; v16783 = ([&]() -> Value { auto v16786 = ([&]() -> Value { auto fn16788 = PrepareDictionaryGet(s->LocalAt(33)); Arguments args16789; args16789.Add(Value("kind"), false); return CallDictionaryGet(c, fn16788, std::move(args16789)); }()); Value v16787; v16787 = Value("PLANT"); if (!static_cast<bool>(Binary("Eq", v16786, v16787))) return Value(false); v16786 = v16787; return Value(true); }()); if (!static_cast<bool>(v16783)) return v16783; v16783 = ([&]() -> Value { auto v16790 = Value(int64_t{0}); Value v16791; v16791 = Get(s->LocalAt(33), Value("max_lifespan_step")); if (!static_cast<bool>(Binary("LtE", v16790, v16791))) return Value(false); v16790 = v16791; v16791 = s->LocalAt(20); if (!static_cast<bool>(Binary("LtE", v16790, v16791))) return Value(false); v16790 = v16791; return Value(true); }()); return v16783; }()))) {
(void)([&]() -> Value { auto fn16792 = Attribute(s->LocalAt(11), "add"); Arguments args16793; args16793.Add(Tuple({Get(s->LocalAt(50), Value(int64_t{1})), Get(s->LocalAt(50), Value(int64_t{0}))}), false); return Call(c, fn16792, std::move(args16793)); }());
}
}
if (static_cast<bool>(([&]() -> Value { auto v16794 = s->LocalAt(6); Value v16795; v16795 = Value{}; if (!static_cast<bool>(Binary("IsNot", v16794, v16795))) return Value(false); v16794 = v16795; return Value(true); }()))) {
auto v16796 = ([&]() -> Value { auto comp16797 = std::make_shared<Scope>(); comp16797->globals = s->globals; comp16797->parent = s; static constexpr const char* comp16797_names[] = {"amount", "item"}; comp16797->PrepareSlots(comp16797_names); auto result16798 = Dict(); for (const auto& item16799 : Iterate(([&]() -> Value { auto fn16800 = Attribute(Get(s->LocalAt(38), Value("shed")), "items"); Arguments args16801; return Call(c, fn16800, std::move(args16801)); }()))) { auto unpack16802 = Iterate(item16799); ValidateUnpack(unpack16802, 2, false); comp16797->SetAt(1, unpack16802.at(0)); comp16797->SetAt(0, unpack16802.at(1)); if (!static_cast<bool>(([&]() -> Value { auto v16803 = comp16797->LocalAt(0); Value v16804; v16804 = ([&]() -> Value { auto fn16805 = PrepareDictionaryGet(comp16797->Captured("before_shed")); Arguments args16806; args16806.positional.reserve(2); args16806.Add(comp16797->LocalAt(1), false); args16806.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn16805, std::move(args16806)); }()); if (!static_cast<bool>(Binary("Gt", v16803, v16804))) return Value(false); v16803 = v16804; return Value(true); }()))) continue; Put(result16798, comp16797->LocalAt(1), ([&]() -> Value { auto v16807 = comp16797->LocalAt(0); return Binary("Sub", v16807, ([&]() -> Value { auto fn16808 = PrepareDictionaryGet(comp16797->Captured("before_shed")); Arguments args16809; args16809.positional.reserve(2); args16809.Add(comp16797->LocalAt(1), false); args16809.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn16808, std::move(args16809)); }())); }())); } return result16798; }());
s->SetAt(12, v16796);
for (const auto& item16810 : Iterate(([&]() -> Value { auto fn16811 = Attribute(s->LocalAt(12), "items"); Arguments args16812; return Call(c, fn16811, std::move(args16812)); }()))) {
auto unpack16813 = Iterate(item16810);
ValidateUnpack(unpack16813, 2, false);
s->SetAt(25, unpack16813.at(0));
s->SetAt(4, unpack16813.at(1));
auto v16814 = ([&]() -> Value { auto v16815 = ([&]() -> Value { auto fn16816 = PrepareDictionaryGet(Get(s->LocalAt(14), s->LocalAt(2))); Arguments args16817; args16817.positional.reserve(2); args16817.Add(s->LocalAt(25), false); args16817.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn16816, std::move(args16817)); }()); return Binary("Add", v16815, s->LocalAt(4)); }());
Put(Get(s->LocalAt(14), s->LocalAt(2)), s->LocalAt(25), v16814);
}
if (static_cast<bool>(s->LocalAt(12))) {
(void)([&]() -> Value { auto fn16818 = Attribute(s->LocalAt(18), "append"); Arguments args16819; args16819.Add(([&]() -> Value { auto dict16820 = Dict(); auto key16821 = Value("offset"); Put(dict16820, key16821, s->LocalAt(30)); auto key16822 = Value("actor"); Put(dict16820, key16822, s->LocalAt(2)); auto key16823 = Value("op"); Put(dict16820, key16823, Get(s->LocalAt(9), Value(int64_t{0}))); auto key16824 = Value("xy"); Put(dict16820, key16824, s->LocalAt(50)); auto key16825 = Value("deposited"); Put(dict16820, key16825, s->LocalAt(12)); return dict16820; }()), false); return Call(c, fn16818, std::move(args16819)); }());
}
if (static_cast<bool>(([&]() -> Value { auto v16826 = Get(s->LocalAt(9), Value(int64_t{0})); Value v16827; v16827 = Value("DROP"); if (!static_cast<bool>(Binary("Eq", v16826, v16827))) return Value(false); v16826 = v16827; return Value(true); }()))) {
auto v16828 = s->LocalAt(32);
s->SetAt(32, Inplace("Add", v16828, ([&]() -> Value { auto fn16829 = s->Global("sum"); Arguments args16830; args16830.Add(([&]() -> Value { auto comp16831 = std::make_shared<Scope>(); comp16831->globals = s->globals; comp16831->parent = s; static constexpr const char* comp16831_names[] = {"amount", "item"}; comp16831->PrepareSlots(comp16831_names); auto result16832 = List(); for (const auto& item16833 : Iterate(([&]() -> Value { auto fn16834 = Attribute(s->LocalAt(5), "items"); Arguments args16835; return Call(c, fn16834, std::move(args16835)); }()))) { auto unpack16836 = Iterate(item16833); ValidateUnpack(unpack16836, 2, false); comp16831->SetAt(1, unpack16836.at(0)); comp16831->SetAt(0, unpack16836.at(1)); result16832.node()->sequence.push_back(([&]() -> Value { auto fn16837 = comp16831->Global("max"); Arguments args16838; args16838.positional.reserve(2); args16838.Add(Value(int64_t{0}), false); args16838.Add(([&]() -> Value { auto v16839 = ([&]() -> Value { auto v16840 = comp16831->LocalAt(0); return Binary("Sub", v16840, ([&]() -> Value { auto fn16841 = PrepareDictionaryGet(comp16831->Captured("inv")); Arguments args16842; args16842.positional.reserve(2); args16842.Add(comp16831->LocalAt(1), false); args16842.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn16841, std::move(args16842)); }())); }()); return Binary("Sub", v16839, ([&]() -> Value { auto fn16843 = PrepareDictionaryGet(comp16831->Captured("delta")); Arguments args16844; args16844.positional.reserve(2); args16844.Add(comp16831->LocalAt(1), false); args16844.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn16843, std::move(args16844)); }())); }()), false); return Call(c, fn16837, std::move(args16838)); }())); } return result16832; }()), false); return Call(c, fn16829, std::move(args16830)); }())));
}
}
if (static_cast<bool>(([&]() -> Value { auto v16845 = Get(s->LocalAt(9), Value(int64_t{0})); Value v16846; v16846 = Set({Value("HARVEST"), Value("COLLECT_FERTILIZER")}); if (!static_cast<bool>(Binary("In", v16845, v16846))) return Value(false); v16845 = v16846; return Value(true); }()))) {
auto v16847 = ([&]() -> Value { auto comp16848 = std::make_shared<Scope>(); comp16848->globals = s->globals; comp16848->parent = s; static constexpr const char* comp16848_names[] = {"amount", "item"}; comp16848->PrepareSlots(comp16848_names); auto result16849 = Dict(); for (const auto& item16850 : Iterate(([&]() -> Value { auto fn16851 = Attribute(s->LocalAt(24), "items"); Arguments args16852; return Call(c, fn16851, std::move(args16852)); }()))) { auto unpack16853 = Iterate(item16850); ValidateUnpack(unpack16853, 2, false); comp16848->SetAt(1, unpack16853.at(0)); comp16848->SetAt(0, unpack16853.at(1)); if (!static_cast<bool>(([&]() -> Value { auto v16854 = comp16848->LocalAt(0); Value v16855; v16855 = ([&]() -> Value { auto fn16856 = PrepareDictionaryGet(comp16848->Captured("before_inv")); Arguments args16857; args16857.positional.reserve(2); args16857.Add(comp16848->LocalAt(1), false); args16857.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn16856, std::move(args16857)); }()); if (!static_cast<bool>(Binary("Gt", v16854, v16855))) return Value(false); v16854 = v16855; return Value(true); }()))) continue; Put(result16849, comp16848->LocalAt(1), ([&]() -> Value { auto v16858 = comp16848->LocalAt(0); return Binary("Sub", v16858, ([&]() -> Value { auto fn16859 = PrepareDictionaryGet(comp16848->Captured("before_inv")); Arguments args16860; args16860.positional.reserve(2); args16860.Add(comp16848->LocalAt(1), false); args16860.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn16859, std::move(args16860)); }())); }())); } return result16849; }());
s->SetAt(12, v16847);
if (static_cast<bool>(s->LocalAt(12))) {
(void)([&]() -> Value { auto fn16861 = Attribute(s->LocalAt(18), "append"); Arguments args16862; args16862.Add(([&]() -> Value { auto dict16863 = Dict(); auto key16864 = Value("offset"); Put(dict16863, key16864, s->LocalAt(30)); auto key16865 = Value("actor"); Put(dict16863, key16865, s->LocalAt(2)); auto key16866 = Value("op"); Put(dict16863, key16866, Get(s->LocalAt(9), Value(int64_t{0}))); auto key16867 = Value("xy"); Put(dict16863, key16867, s->LocalAt(50)); auto key16868 = Value("acquired"); Put(dict16863, key16868, s->LocalAt(12)); return dict16863; }()), false); return Call(c, fn16861, std::move(args16862)); }());
}
}
}
auto v16869 = ([&]() -> Value { auto fn16870 = s->Global("dict"); Arguments args16871; args16871.Add(Get(s->LocalAt(38), Value("shed")), false); return Call(c, fn16870, std::move(args16871)); }());
s->SetAt(35, v16869);
if (static_cast<bool>(([&]() -> Value { auto v16872 = ([&]() -> Value { auto v16873 = s->LocalAt(48); Value v16874; v16874 = s->Global("FINAL"); if (!static_cast<bool>(Binary("Eq", v16873, v16874))) return Value(false); v16873 = v16874; return Value(true); }()); if (!static_cast<bool>(v16872)) return v16872; v16872 = s->LocalAt(36); if (!static_cast<bool>(v16872)) return v16872; v16872 = s->LocalAt(23); return v16872; }()))) {
auto v16875 = ([&]() -> Value { auto fn16876 = s->Global("liquidation"); Arguments args16877; args16877.positional.reserve(3); args16877.Add(s->LocalAt(35), false); args16877.Add(List({}), false); args16877.Add(s->LocalAt(31), false); return Call(c, fn16876, std::move(args16877)); }());
Put(s->LocalAt(1), Value("market"), v16875);
auto v16878 = Get(([&]() -> Value { auto fn16879 = s->Global("_get"); Arguments args16880; args16880.positional.reserve(2); args16880.Add(s->LocalAt(29), false); args16880.Add(Value("market"), false); return Call(c, fn16879, std::move(args16880)); }()), Value("prices"));
s->SetAt(37, v16878);
(void)([&]() -> Value { auto fn16881 = Attribute(Get(s->LocalAt(1), Value("market")), "sort"); Arguments args16882; args16882.Keyword("key", Define(&Code_a50a4829c38607a2c264, s, Signature{{"order"}, {}, {}, {}, "", "", ([]() -> std::span<const char* const> { static constexpr const char* names[] = {"order"}; return names; }())}, true, "<lambda>")); return Call(c, fn16881, std::move(args16882)); }());
}
for (const auto& item16888 : Iterate(([&]() -> Value { auto fn16889 = PrepareDictionaryGet(s->LocalAt(1)); Arguments args16890; args16890.positional.reserve(2); args16890.Add(Value("market"), false); args16890.Add(List({}), false); return CallDictionaryGet(c, fn16889, std::move(args16890)); }()))) {
auto unpack16891 = Iterate(item16888);
ValidateUnpack(unpack16891, 3, false);
s->SetAt(0, unpack16891.at(0));
s->SetAt(25, unpack16891.at(1));
s->SetAt(41, unpack16891.at(2));
auto v16892 = ([&]() -> Value { auto fn16893 = s->Global("min"); Arguments args16894; args16894.positional.reserve(3); args16894.Add(s->LocalAt(41), false); args16894.Add(([&]() -> Value { auto fn16895 = PrepareDictionaryGet(Get(s->LocalAt(38), Value("shed"))); Arguments args16896; args16896.positional.reserve(2); args16896.Add(s->LocalAt(25), false); args16896.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn16895, std::move(args16896)); }()), false); args16894.Add(Value(int64_t{99999}), false); return Call(c, fn16893, std::move(args16894)); }());
s->SetAt(40, v16892);
if (static_cast<bool>(([&]() -> Value { auto v16897 = s->LocalAt(40); Value v16898; v16898 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v16897, v16898))) return Value(false); v16897 = v16898; return Value(true); }()))) {
auto v16899 = Get(s->LocalAt(38), Value("shed"));
auto v16900 = s->LocalAt(25);
auto v16901 = Get(v16899, v16900);
Put(v16899, v16900, Inplace("Sub", v16901, s->LocalAt(40)));
auto v16902 = ([&]() -> Value { auto v16903 = ([&]() -> Value { auto fn16904 = PrepareDictionaryGet(s->LocalAt(46)); Arguments args16905; args16905.positional.reserve(2); args16905.Add(s->LocalAt(25), false); args16905.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn16904, std::move(args16905)); }()); return Binary("Add", v16903, s->LocalAt(40)); }());
Put(s->LocalAt(46), s->LocalAt(25), v16902);
}
}
(void)([&]() -> Value { auto fn16906 = s->Global("_exp303_decay"); Arguments args16907; args16907.positional.reserve(3); args16907.Add(s->LocalAt(21), false); args16907.Add(s->LocalAt(48), false); args16907.Add(s->LocalAt(11), false); return Call(c, fn16906, std::move(args16907)); }());
(void)([&]() -> Value { auto fn16908 = Attribute(s->LocalAt(42), "append"); Arguments args16909; args16909.Add(([&]() -> Value { auto dict16910 = Dict(); auto key16911 = Value("pre_market_shed"); Put(dict16910, key16911, s->LocalAt(35)); auto key16912 = Value("post_market_shed"); Put(dict16910, key16912, ([&]() -> Value { auto fn16913 = s->Global("dict"); Arguments args16914; args16914.Add(Get(s->LocalAt(38), Value("shed")), false); return Call(c, fn16913, std::move(args16914)); }())); auto key16915 = Value("deposited_by_actor"); Put(dict16910, key16915, ([&]() -> Value { auto comp16916 = std::make_shared<Scope>(); comp16916->globals = s->globals; comp16916->parent = s; static constexpr const char* comp16916_names[] = {"v"}; comp16916->PrepareSlots(comp16916_names); auto result16917 = List(); for (const auto& item16918 : Iterate(s->LocalAt(14))) { comp16916->SetAt(0, item16918); result16917.node()->sequence.push_back(([&]() -> Value { auto fn16919 = comp16916->Global("dict"); Arguments args16920; args16920.Add(comp16916->LocalAt(0), false); return Call(c, fn16919, std::move(args16920)); }())); } return result16917; }())); auto key16921 = Value("sold"); Put(dict16910, key16921, ([&]() -> Value { auto fn16922 = s->Global("dict"); Arguments args16923; args16923.Add(s->LocalAt(46), false); return Call(c, fn16922, std::move(args16923)); }())); return dict16910; }()), false); return Call(c, fn16908, std::move(args16909)); }());
}
if (static_cast<bool>(s->LocalAt(15))) {
(void)([&]() -> Value { auto fn16924 = Attribute(s->LocalAt(45), "append"); Arguments args16925; args16925.Add(([&]() -> Value { auto fn16926 = s->Global("_clone_state"); Arguments args16927; args16927.positional.reserve(2); args16927.Add(s->LocalAt(21), false); args16927.Add(s->LocalAt(38), false); return Call(c, fn16926, std::move(args16927)); }()), false); return Call(c, fn16924, std::move(args16925)); }());
}
return ([&]() -> Value { auto dict16928 = Dict(); auto key16929 = Value("rows"); Put(dict16928, key16929, s->LocalAt(42)); auto key16930 = Value("states"); Put(dict16928, key16930, s->LocalAt(45)); auto key16931 = Value("events"); Put(dict16928, key16931, s->LocalAt(18)); auto key16932 = Value("actions"); Put(dict16928, key16932, s->LocalAt(19)); auto key16933 = Value("overflow_units"); Put(dict16928, key16933, s->LocalAt(32)); auto key16934 = Value("farm"); Put(dict16928, key16934, s->LocalAt(21)); auto key16935 = Value("private"); Put(dict16928, key16935, s->LocalAt(38)); auto key16936 = Value("sold"); Put(dict16928, key16936, s->LocalAt(46)); return dict16928; }());
return {};
}
}  // namespace kagg::opponents::compiled
