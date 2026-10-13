// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_8e841a931c44ef3d4d1a(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "actor", "command", "commands", "displaced", "native", "observation", "player", "repair", "result", "state", "step"};
s->PrepareSlots(s_names);
auto v15621 = ([&]() -> Value { auto fn15622 = PrepareDictionaryGet(s->LocalAt(10)); Arguments args15623; args15623.Add(Value("repair"), false); return CallDictionaryGet(c, fn15622, std::move(args15623)); }());
s->SetAt(8, v15621);
if (static_cast<bool>(Unary("Not", s->LocalAt(8)))) {
return s->LocalAt(0);
}
auto v15624 = ([&]() -> Value { auto fn15625 = s->Global("int"); Arguments args15626; args15626.Add(Get(s->LocalAt(6), Value("step")), false); return Call(c, fn15625, std::move(args15626)); }());
s->SetAt(11, v15624);
auto v15627 = ([&]() -> Value { auto fn15628 = s->Global("int"); Arguments args15629; args15629.Add(Get(s->LocalAt(6), Value("player")), false); return Call(c, fn15628, std::move(args15629)); }());
s->SetAt(7, v15627);
auto v15630 = ([&]() -> Value { auto v15631 = ([&]() -> Value { auto fn15632 = PrepareDictionaryGet(Attribute(Attribute(s->Global("_IMPL"), "chassis"), "players")); Arguments args15633; args15633.Add(s->LocalAt(7), false); return CallDictionaryGet(c, fn15632, std::move(args15633)); }()); if (static_cast<bool>(v15631)) return v15631; v15631 = ([&]() -> Value { auto dict15634 = Dict(); return dict15634; }()); return v15631; }());
s->SetAt(5, v15630);
if (static_cast<bool>(([&]() -> Value { auto v15635 = ([&]() -> Value { auto v15636 = s->LocalAt(11); Value v15637; v15637 = Get(s->LocalAt(8), Value("next_step")); if (!static_cast<bool>(Binary("NotEq", v15636, v15637))) return Value(false); v15636 = v15637; return Value(true); }()); if (static_cast<bool>(v15635)) return v15635; v15635 = ([&]() -> Value { auto v15638 = s->LocalAt(11); Value v15639; v15639 = Get(s->LocalAt(8), Value("deadline")); if (!static_cast<bool>(Binary("Gt", v15638, v15639))) return Value(false); v15638 = v15639; return Value(true); }()); if (static_cast<bool>(v15635)) return v15635; v15635 = ([&]() -> Value { auto v15640 = ([&]() -> Value { auto fn15642 = PrepareDictionaryGet(s->LocalAt(5)); Arguments args15643; args15643.Add(Value("route"), false); return CallDictionaryGet(c, fn15642, std::move(args15643)); }()); Value v15641; v15641 = Get(s->LocalAt(8), Value("route")); if (!static_cast<bool>(Binary("NotEq", v15640, v15641))) return Value(false); v15640 = v15641; return Value(true); }()); return v15635; }()))) {
(void)([&]() -> Value { auto fn15644 = Attribute(s->LocalAt(10), "pop"); Arguments args15645; args15645.positional.reserve(2); args15645.Add(Value("repair"), false); args15645.Add(Value{}, false); return Call(c, fn15644, std::move(args15645)); }());
auto v15646 = s->Global("_R132_REPORT");
auto v15647 = Value("weed_repair_aborted");
auto v15648 = Get(v15646, v15647);
Put(v15646, v15647, Inplace("Add", v15648, Value(int64_t{1})));
return s->LocalAt(0);
}
auto v15649 = Get(s->LocalAt(8), Value("actor"));
s->SetAt(1, v15649);
auto v15650 = ([&]() -> Value { auto fn15651 = s->Global("_r132_commands"); Arguments args15652; args15652.Add(s->LocalAt(0), false); return Call(c, fn15651, std::move(args15652)); }());
s->SetAt(3, v15650);
if (static_cast<bool>(([&]() -> Value { auto v15653 = ([&]() -> Value { auto v15654 = s->LocalAt(1); Value v15655; v15655 = ([&]() -> Value { auto fn15656 = s->Global("len"); Arguments args15657; args15657.Add(s->LocalAt(3), false); return Call(c, fn15656, std::move(args15657)); }()); if (!static_cast<bool>(Binary("GtE", v15654, v15655))) return Value(false); v15654 = v15655; return Value(true); }()); if (static_cast<bool>(v15653)) return v15653; v15653 = Unary("Not", Get(s->LocalAt(8), Value("queue"))); return v15653; }()))) {
(void)([&]() -> Value { auto fn15658 = Attribute(s->LocalAt(10), "pop"); Arguments args15659; args15659.positional.reserve(2); args15659.Add(Value("repair"), false); args15659.Add(Value{}, false); return Call(c, fn15658, std::move(args15659)); }());
auto v15660 = s->Global("_R132_REPORT");
auto v15661 = Value("weed_repair_aborted");
auto v15662 = Get(v15660, v15661);
Put(v15660, v15661, Inplace("Add", v15662, Value(int64_t{1})));
return s->LocalAt(0);
}
auto v15663 = ([&]() -> Value { auto fn15664 = Attribute(Get(s->LocalAt(8), Value("queue")), "pop"); Arguments args15665; args15665.Add(Value(int64_t{0}), false); return Call(c, fn15664, std::move(args15665)); }());
s->SetAt(2, v15663);
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto fn15666 = s->Global("_r132_command_valid"); Arguments args15667; args15667.positional.reserve(4); args15667.Add(s->LocalAt(6), false); args15667.Add(s->LocalAt(0), false); args15667.Add(s->LocalAt(1), false); args15667.Add(s->LocalAt(2), false); return Call(c, fn15666, std::move(args15667)); }())))) {
(void)([&]() -> Value { auto fn15668 = Attribute(s->LocalAt(10), "pop"); Arguments args15669; args15669.positional.reserve(2); args15669.Add(Value("repair"), false); args15669.Add(Value{}, false); return Call(c, fn15668, std::move(args15669)); }());
auto v15670 = s->Global("_R132_REPORT");
auto v15671 = Value("weed_repair_aborted");
auto v15672 = Get(v15670, v15671);
Put(v15670, v15671, Inplace("Add", v15672, Value(int64_t{1})));
return s->LocalAt(0);
}
auto v15673 = Get(s->LocalAt(3), s->LocalAt(1));
s->SetAt(4, v15673);
if (static_cast<bool>(([&]() -> Value { auto v15674 = s->LocalAt(4); Value v15675; v15675 = List({Value("PASS")}); if (!static_cast<bool>(Binary("NotEq", v15674, v15675))) return Value(false); v15674 = v15675; return Value(true); }()))) {
(void)([&]() -> Value { auto fn15676 = Attribute(Get(s->LocalAt(8), Value("queue")), "append"); Arguments args15677; args15677.Add(([&]() -> Value { auto fn15678 = s->Global("list"); Arguments args15679; args15679.Add(s->LocalAt(4), false); return Call(c, fn15678, std::move(args15679)); }()), false); return Call(c, fn15676, std::move(args15677)); }());
}
if (static_cast<bool>(([&]() -> Value { auto v15680 = ([&]() -> Value { auto v15681 = s->LocalAt(11); Value v15682; v15682 = Get(s->LocalAt(8), Value("deadline")); if (!static_cast<bool>(Binary("GtE", v15681, v15682))) return Value(false); v15681 = v15682; return Value(true); }()); if (!static_cast<bool>(v15680)) return v15680; v15680 = Get(s->LocalAt(8), Value("queue")); return v15680; }()))) {
(void)([&]() -> Value { auto fn15683 = Attribute(s->LocalAt(10), "pop"); Arguments args15684; args15684.positional.reserve(2); args15684.Add(Value("repair"), false); args15684.Add(Value{}, false); return Call(c, fn15683, std::move(args15684)); }());
auto v15685 = s->Global("_R132_REPORT");
auto v15686 = Value("weed_repair_aborted");
auto v15687 = Get(v15685, v15686);
Put(v15685, v15686, Inplace("Add", v15687, Value(int64_t{1})));
return s->LocalAt(0);
}
auto v15688 = ([&]() -> Value { auto fn15689 = s->Global("_r132_set_command"); Arguments args15690; args15690.positional.reserve(3); args15690.Add(s->LocalAt(0), false); args15690.Add(s->LocalAt(1), false); args15690.Add(s->LocalAt(2), false); return Call(c, fn15689, std::move(args15690)); }());
s->SetAt(9, v15688);
auto v15691 = ([&]() -> Value { auto v15692 = s->LocalAt(11); return Binary("Add", v15692, Value(int64_t{1})); }());
Put(s->LocalAt(8), Value("next_step"), v15691);
auto v15693 = s->Global("_R132_REPORT");
auto v15694 = Value("weed_repair_shifted_steps");
auto v15695 = Get(v15693, v15694);
Put(v15693, v15694, Inplace("Add", v15695, Value(int64_t{1})));
if (static_cast<bool>(([&]() -> Value { auto v15696 = Slice(s->LocalAt(2), Value{}, Value(int64_t{1}), Value{}); Value v15697; v15697 = List({Value("PLANT")}); if (!static_cast<bool>(Binary("Eq", v15696, v15697))) return Value(false); v15696 = v15697; return Value(true); }()))) {
auto v15698 = s->Global("_R132_REPORT");
auto v15699 = Value("weed_repair_plants");
auto v15700 = Get(v15698, v15699);
Put(v15698, v15699, Inplace("Add", v15700, Value(int64_t{1})));
}
if (static_cast<bool>(([&]() -> Value { auto v15701 = s->LocalAt(2); Value v15702; v15702 = List({Value("WATER")}); if (!static_cast<bool>(Binary("Eq", v15701, v15702))) return Value(false); v15701 = v15702; return Value(true); }()))) {
auto v15703 = s->Global("_R132_REPORT");
auto v15704 = Value("weed_repair_waters");
auto v15705 = Get(v15703, v15704);
Put(v15703, v15704, Inplace("Add", v15705, Value(int64_t{1})));
}
if (static_cast<bool>(Unary("Not", Get(s->LocalAt(8), Value("queue"))))) {
(void)([&]() -> Value { auto fn15706 = Attribute(s->LocalAt(10), "pop"); Arguments args15707; args15707.positional.reserve(2); args15707.Add(Value("repair"), false); args15707.Add(Value{}, false); return Call(c, fn15706, std::move(args15707)); }());
auto v15708 = s->Global("_R132_REPORT");
auto v15709 = Value("weed_repair_completed");
auto v15710 = Get(v15708, v15709);
Put(v15708, v15709, Inplace("Add", v15710, Value(int64_t{1})));
}
return s->LocalAt(9);
return {};
}
}  // namespace kagg::opponents::compiled
