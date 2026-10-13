// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_0c36edde5143571af4e0(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"advanced", "after", "before", "buys", "c", "commands", "farm", "final", "i", "item", "loss", "need", "obs", "oldbuys", "oldcommands", "oldfarm", "oldfinal", "oldloss", "oldprivate", "oldsales", "oldstock", "orders", "pending", "private", "sales", "stock"};
s->PrepareSlots(s_names);
auto v11588 = ([&]() -> Value { auto v11589 = ([&]() -> Value { auto fn11590 = PrepareDictionaryGet(s->LocalAt(2)); Arguments args11591; args11591.Add(Value("market"), false); return CallDictionaryGet(c, fn11590, std::move(args11591)); }()); if (static_cast<bool>(v11589)) return v11589; v11589 = List({}); return v11589; }());
s->SetAt(21, v11588);
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto fn11592 = s->Global("_r97_budget"); Arguments args11593; args11593.positional.reserve(2); args11593.Add(s->LocalAt(12), false); args11593.Add(s->LocalAt(21), false); return Call(c, fn11592, std::move(args11593)); }())))) {
return Tuple({Value(false), Value{}});
}
auto v11594 = ([&]() -> Value { auto fn11595 = s->Global("_r127_fields"); Arguments args11596; args11596.positional.reserve(2); args11596.Add(s->LocalAt(12), false); args11596.Add(s->LocalAt(2), false); return Call(c, fn11595, std::move(args11596)); }());
auto unpack11597 = Iterate(v11594);
ValidateUnpack(unpack11597, 2, false);
s->SetAt(15, unpack11597.at(0));
s->SetAt(18, unpack11597.at(1));
auto v11598 = ([&]() -> Value { auto fn11599 = s->Global("_r127_fields"); Arguments args11600; args11600.positional.reserve(2); args11600.Add(s->LocalAt(12), false); args11600.Add(s->LocalAt(1), false); return Call(c, fn11599, std::move(args11600)); }());
auto unpack11601 = Iterate(v11598);
ValidateUnpack(unpack11601, 2, false);
s->SetAt(6, unpack11601.at(0));
s->SetAt(23, unpack11601.at(1));
auto v11602 = ([&]() -> Value { auto fn11603 = s->Global("_r128_commands"); Arguments args11604; args11604.Add(s->LocalAt(2), false); return Call(c, fn11603, std::move(args11604)); }());
s->SetAt(14, v11602);
auto v11605 = ([&]() -> Value { auto fn11606 = s->Global("_r128_commands"); Arguments args11607; args11607.Add(s->LocalAt(1), false); return Call(c, fn11606, std::move(args11607)); }());
s->SetAt(5, v11605);
for (const auto& item11608 : Iterate(([&]() -> Value { auto fn11609 = s->Global("enumerate"); Arguments args11610; args11610.Add(Slice(s->LocalAt(14), Value{}, ([&]() -> Value { auto fn11611 = s->Global("len"); Arguments args11612; args11612.Add(Get(s->LocalAt(23), Value("inventories")), false); return Call(c, fn11611, std::move(args11612)); }()), Value{}), false); return Call(c, fn11609, std::move(args11610)); }()))) {
auto unpack11613 = Iterate(item11608);
ValidateUnpack(unpack11613, 2, false);
s->SetAt(8, unpack11613.at(0));
s->SetAt(4, unpack11613.at(1));
if (static_cast<bool>(([&]() -> Value { auto v11614 = s->LocalAt(4); if (!static_cast<bool>(v11614)) return v11614; v11614 = ([&]() -> Value { auto v11615 = Get(s->LocalAt(4), Value(int64_t{0})); Value v11616; v11616 = Value("PICKUP"); if (!static_cast<bool>(Binary("Eq", v11615, v11616))) return Value(false); v11615 = v11616; return Value(true); }()); if (!static_cast<bool>(v11614)) return v11614; v11614 = ([&]() -> Value { auto v11617 = s->LocalAt(4); Value v11618; v11618 = Get(s->LocalAt(5), s->LocalAt(8)); if (!static_cast<bool>(Binary("Eq", v11617, v11618))) return Value(false); v11617 = v11618; return Value(true); }()); return v11614; }()))) {
auto v11619 = Get(s->LocalAt(4), Value(int64_t{1}));
s->SetAt(9, v11619);
if (static_cast<bool>(([&]() -> Value { auto v11620 = ([&]() -> Value { auto fn11622 = PrepareDictionaryGet(Get(Get(s->LocalAt(23), Value("inventories")), s->LocalAt(8))); Arguments args11623; args11623.positional.reserve(2); args11623.Add(s->LocalAt(9), false); args11623.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn11622, std::move(args11623)); }()); Value v11621; v11621 = ([&]() -> Value { auto fn11624 = PrepareDictionaryGet(Get(Get(s->LocalAt(18), Value("inventories")), s->LocalAt(8))); Arguments args11625; args11625.positional.reserve(2); args11625.Add(s->LocalAt(9), false); args11625.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn11624, std::move(args11625)); }()); if (!static_cast<bool>(Binary("Lt", v11620, v11621))) return Value(false); v11620 = v11621; return Value(true); }()))) {
return Tuple({Value(false), Value{}});
}
}
}
auto v11626 = ([&]() -> Value { auto fn11627 = s->Global("_r97_market_stock"); Arguments args11628; args11628.positional.reserve(2); args11628.Add(Get(s->LocalAt(18), Value("shed")), false); args11628.Add(s->LocalAt(21), false); return Call(c, fn11627, std::move(args11628)); }());
auto unpack11629 = Iterate(v11626);
ValidateUnpack(unpack11629, 3, false);
s->SetAt(20, unpack11629.at(0));
s->SetAt(13, unpack11629.at(1));
s->SetAt(19, unpack11629.at(2));
auto v11630 = ([&]() -> Value { auto fn11631 = s->Global("_r97_market_stock"); Arguments args11632; args11632.positional.reserve(2); args11632.Add(Get(s->LocalAt(23), Value("shed")), false); args11632.Add(s->LocalAt(21), false); return Call(c, fn11631, std::move(args11632)); }());
auto unpack11633 = Iterate(v11630);
ValidateUnpack(unpack11633, 3, false);
s->SetAt(25, unpack11633.at(0));
s->SetAt(3, unpack11633.at(1));
s->SetAt(24, unpack11633.at(2));
auto v11634 = ([&]() -> Value { auto fn11635 = s->Global("_r97_delivery"); Arguments args11636; args11636.positional.reserve(3); args11636.Add(s->LocalAt(20), false); args11636.Add(s->LocalAt(18), false); args11636.Add(([&]() -> Value { auto v11637 = ([&]() -> Value { auto v11639 = ([&]() -> Value { auto fn11640 = s->Global("int"); Arguments args11641; args11641.Add(Get(s->LocalAt(12), Value("step")), false); return Call(c, fn11640, std::move(args11641)); }()); return Binary("Mod", v11639, Value(int64_t{24})); }()); Value v11638; v11638 = Value(int64_t{23}); if (!static_cast<bool>(Binary("Eq", v11637, v11638))) return Value(false); v11637 = v11638; return Value(true); }()), false); return Call(c, fn11635, std::move(args11636)); }());
auto unpack11642 = Iterate(v11634);
ValidateUnpack(unpack11642, 2, false);
s->SetAt(16, unpack11642.at(0));
s->SetAt(17, unpack11642.at(1));
auto v11643 = ([&]() -> Value { auto fn11644 = s->Global("_r97_delivery"); Arguments args11645; args11645.positional.reserve(3); args11645.Add(s->LocalAt(25), false); args11645.Add(s->LocalAt(23), false); args11645.Add(([&]() -> Value { auto v11646 = ([&]() -> Value { auto v11648 = ([&]() -> Value { auto fn11649 = s->Global("int"); Arguments args11650; args11650.Add(Get(s->LocalAt(12), Value("step")), false); return Call(c, fn11649, std::move(args11650)); }()); return Binary("Mod", v11648, Value(int64_t{24})); }()); Value v11647; v11647 = Value(int64_t{23}); if (!static_cast<bool>(Binary("Eq", v11646, v11647))) return Value(false); v11646 = v11647; return Value(true); }()), false); return Call(c, fn11644, std::move(args11645)); }());
auto unpack11651 = Iterate(v11643);
ValidateUnpack(unpack11651, 2, false);
s->SetAt(7, unpack11651.at(0));
s->SetAt(10, unpack11651.at(1));
if (static_cast<bool>(([&]() -> Value { auto v11652 = ([&]() -> Value { auto comp11653 = std::make_shared<Scope>(); comp11653->globals = s->globals; comp11653->parent = s; static constexpr const char* comp11653_names[] = {"i", "q"}; comp11653->PrepareSlots(comp11653_names); auto result11654 = List(); for (const auto& item11655 : Iterate(([&]() -> Value { auto fn11656 = Attribute(s->LocalAt(13), "items"); Arguments args11657; return Call(c, fn11656, std::move(args11657)); }()))) { auto unpack11658 = Iterate(item11655); ValidateUnpack(unpack11658, 2, false); comp11653->SetAt(0, unpack11658.at(0)); comp11653->SetAt(1, unpack11658.at(1)); if (static_cast<bool>(([&]() -> Value { auto v11659 = ([&]() -> Value { auto fn11661 = PrepareDictionaryGet(comp11653->Captured("buys")); Arguments args11662; args11662.positional.reserve(2); args11662.Add(comp11653->LocalAt(0), false); args11662.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn11661, std::move(args11662)); }()); Value v11660; v11660 = comp11653->LocalAt(1); if (!static_cast<bool>(Binary("Lt", v11659, v11660))) return Value(false); v11659 = v11660; return Value(true); }()))) return Value(true); } return Value(false); }()); if (static_cast<bool>(v11652)) return v11652; v11652 = ([&]() -> Value { auto comp11663 = std::make_shared<Scope>(); comp11663->globals = s->globals; comp11663->parent = s; static constexpr const char* comp11663_names[] = {"i", "q"}; comp11663->PrepareSlots(comp11663_names); auto result11664 = List(); for (const auto& item11665 : Iterate(([&]() -> Value { auto fn11666 = Attribute(s->LocalAt(19), "items"); Arguments args11667; return Call(c, fn11666, std::move(args11667)); }()))) { auto unpack11668 = Iterate(item11665); ValidateUnpack(unpack11668, 2, false); comp11663->SetAt(0, unpack11668.at(0)); comp11663->SetAt(1, unpack11668.at(1)); if (static_cast<bool>(([&]() -> Value { auto v11669 = ([&]() -> Value { auto fn11671 = PrepareDictionaryGet(comp11663->Captured("sales")); Arguments args11672; args11672.positional.reserve(2); args11672.Add(comp11663->LocalAt(0), false); args11672.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn11671, std::move(args11672)); }()); Value v11670; v11670 = comp11663->LocalAt(1); if (!static_cast<bool>(Binary("Lt", v11669, v11670))) return Value(false); v11669 = v11670; return Value(true); }()))) return Value(true); } return Value(false); }()); if (static_cast<bool>(v11652)) return v11652; v11652 = ([&]() -> Value { auto comp11673 = std::make_shared<Scope>(); comp11673->globals = s->globals; comp11673->parent = s; static constexpr const char* comp11673_names[] = {"p", "q"}; comp11673->PrepareSlots(comp11673_names); auto result11674 = List(); for (const auto& item11675 : Iterate(([&]() -> Value { auto fn11676 = Attribute(s->LocalAt(10), "items"); Arguments args11677; return Call(c, fn11676, std::move(args11677)); }()))) { auto unpack11678 = Iterate(item11675); ValidateUnpack(unpack11678, 2, false); comp11673->SetAt(0, unpack11678.at(0)); comp11673->SetAt(1, unpack11678.at(1)); if (static_cast<bool>(([&]() -> Value { auto v11679 = comp11673->LocalAt(1); Value v11680; v11680 = ([&]() -> Value { auto fn11681 = PrepareDictionaryGet(comp11673->Captured("oldloss")); Arguments args11682; args11682.positional.reserve(2); args11682.Add(comp11673->LocalAt(0), false); args11682.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn11681, std::move(args11682)); }()); if (!static_cast<bool>(Binary("Gt", v11679, v11680))) return Value(false); v11679 = v11680; return Value(true); }()))) return Value(true); } return Value(false); }()); return v11652; }()))) {
return Tuple({Value(false), Value{}});
}
auto v11683 = ([&]() -> Value { auto fn11684 = s->Global("_r128_next_need"); Arguments args11685; args11685.positional.reserve(4); args11685.Add(s->LocalAt(12), false); args11685.Add(s->LocalAt(6), false); args11685.Add(s->LocalAt(21), false); args11685.Add(s->LocalAt(0), false); return Call(c, fn11684, std::move(args11685)); }());
s->SetAt(11, v11683);
auto v11686 = ([&]() -> Value { auto fn11687 = PrepareDictionaryGet(([&]() -> Value { auto fn11689 = PrepareDictionaryGet(s->Global("_R127_STATES")); Arguments args11690; args11690.positional.reserve(2); args11690.Add(([&]() -> Value { auto fn11691 = s->Global("int"); Arguments args11692; args11692.Add(Get(s->LocalAt(12), Value("player")), false); return Call(c, fn11691, std::move(args11692)); }()), false); args11690.Add(([&]() -> Value { auto dict11693 = Dict(); return dict11693; }()), false); return CallDictionaryGet(c, fn11689, std::move(args11690)); }())); Arguments args11688; args11688.Add(Value("pending_grain"), false); return CallDictionaryGet(c, fn11687, std::move(args11688)); }());
s->SetAt(22, v11686);
if (static_cast<bool>(([&]() -> Value { auto v11694 = s->LocalAt(22); if (!static_cast<bool>(v11694)) return v11694; v11694 = ([&]() -> Value { auto v11695 = Get(s->LocalAt(22), Value(int64_t{0})); Value v11696; v11696 = ([&]() -> Value { auto v11697 = ([&]() -> Value { auto fn11698 = s->Global("int"); Arguments args11699; args11699.Add(Get(s->LocalAt(12), Value("step")), false); return Call(c, fn11698, std::move(args11699)); }()); return Binary("Add", v11697, Value(int64_t{1})); }()); if (!static_cast<bool>(Binary("Eq", v11695, v11696))) return Value(false); v11695 = v11696; return Value(true); }()); return v11694; }()))) {
auto v11700 = ([&]() -> Value { auto fn11701 = s->Global("max"); Arguments args11702; args11702.positional.reserve(2); args11702.Add(s->LocalAt(11), false); args11702.Add(Get(s->LocalAt(22), Value(int64_t{1})), false); return Call(c, fn11701, std::move(args11702)); }());
s->SetAt(11, v11700);
}
if (static_cast<bool>(([&]() -> Value { auto v11703 = ([&]() -> Value { auto fn11705 = PrepareDictionaryGet(s->LocalAt(7)); Arguments args11706; args11706.positional.reserve(2); args11706.Add(Value("WHEAT"), false); args11706.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn11705, std::move(args11706)); }()); Value v11704; v11704 = ([&]() -> Value { auto fn11707 = s->Global("min"); Arguments args11708; args11708.positional.reserve(2); args11708.Add(s->LocalAt(11), false); args11708.Add(([&]() -> Value { auto fn11709 = PrepareDictionaryGet(s->LocalAt(16)); Arguments args11710; args11710.positional.reserve(2); args11710.Add(Value("WHEAT"), false); args11710.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn11709, std::move(args11710)); }()), false); return Call(c, fn11707, std::move(args11708)); }()); if (!static_cast<bool>(Binary("Lt", v11703, v11704))) return Value(false); v11703 = v11704; return Value(true); }()))) {
return Tuple({Value(false), Value{}});
}
return Tuple({Value(true), s->LocalAt(23)});
return {};
}
}  // namespace kagg::opponents::compiled
