// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_07cbd8879b012287d132(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "configuration", "item", "o", "obs", "own", "p", "q", "step", "stock"};
s->PrepareSlots(s_names);
auto v27632 = ([&]() -> Value { auto fn27633 = s->Global("int"); Arguments args27634; args27634.Add(Get(s->LocalAt(4), Value("player")), false); return Call(c, fn27633, std::move(args27634)); }());
s->SetAt(6, v27632);
auto v27635 = ([&]() -> Value { auto fn27636 = s->Global("int"); Arguments args27637; args27637.Add(Get(s->LocalAt(4), Value("step")), false); return Call(c, fn27636, std::move(args27637)); }());
s->SetAt(8, v27635);
if (static_cast<bool>(([&]() -> Value { auto v27638 = s->LocalAt(8); Value v27639; v27639 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v27638, v27639))) return Value(false); v27638 = v27639; return Value(true); }()))) {
(void)([&]() -> Value { auto fn27640 = Attribute(s->Global("_V92_P"), "pop"); Arguments args27641; args27641.positional.reserve(2); args27641.Add(s->LocalAt(6), false); args27641.Add(Value{}, false); return Call(c, fn27640, std::move(args27641)); }());
if (static_cast<bool>(Unary("Not", Value(false)))) {
(void)([&]() -> Value { auto fn27642 = Attribute(s->Global("_V9_RACE"), "pop"); Arguments args27643; args27643.positional.reserve(2); args27643.Add(s->LocalAt(6), false); args27643.Add(Value{}, false); return Call(c, fn27642, std::move(args27643)); }());
}
(void)([&]() -> Value { auto fn27644 = Attribute(s->Global("_V92_P_REPORT"), "update"); Arguments args27645; args27645.Keyword("pred_units", Value(int64_t{0})); args27645.Keyword("pred_fires", Value(int64_t{0})); args27645.Keyword("pred_errors", Value(int64_t{0})); return Call(c, fn27644, std::move(args27645)); }());
(void)([&]() -> Value { auto fn27646 = Attribute(s->Global("_E350_REPORT"), "update"); Arguments args27647; args27647.Keyword("e350_snapshots", Value(int64_t{0})); args27647.Keyword("e350_errors", Value(int64_t{0})); return Call(c, fn27646, std::move(args27647)); }());
}
auto v27648 = ([&]() -> Value { auto fn27649 = s->Global("_E350_FINAL"); Arguments args27650; args27650.positional.reserve(2); args27650.Add(s->LocalAt(4), false); args27650.Add(s->LocalAt(1), false); return Call(c, fn27649, std::move(args27650)); }());
s->SetAt(0, v27648);
if (static_cast<bool>(Value(false))) {
return s->LocalAt(0);
}
try {
auto v27652 = ([&]() -> Value { auto fn27653 = s->Global("dict"); Arguments args27654; args27654.Add(([&]() -> Value { auto fn27655 = s->Global("projected_shed"); Arguments args27656; args27656.positional.reserve(2); args27656.Add(s->LocalAt(0), false); args27656.Add(([&]() -> Value { auto fn27657 = s->Global("FarmView"); Arguments args27658; args27658.Add(s->LocalAt(4), false); return Call(c, fn27657, std::move(args27658)); }()), false); return Call(c, fn27655, std::move(args27656)); }()), false); return Call(c, fn27653, std::move(args27654)); }());
s->SetAt(9, v27652);
auto v27659 = ([&]() -> Value { auto dict27660 = Dict(); return dict27660; }());
s->SetAt(5, v27659);
for (const auto& item27661 : Iterate(([&]() -> Value { auto v27662 = ([&]() -> Value { auto fn27663 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args27664; args27664.Add(Value("market"), false); return CallDictionaryGet(c, fn27663, std::move(args27664)); }()); if (static_cast<bool>(v27662)) return v27662; v27662 = List({}); return v27662; }()))) {
s->SetAt(3, item27661);
if (static_cast<bool>(([&]() -> Value { auto v27665 = s->LocalAt(3); if (!static_cast<bool>(v27665)) return v27665; v27665 = ([&]() -> Value { auto v27666 = ([&]() -> Value { auto fn27668 = s->Global("len"); Arguments args27669; args27669.Add(s->LocalAt(3), false); return Call(c, fn27668, std::move(args27669)); }()); Value v27667; v27667 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v27666, v27667))) return Value(false); v27666 = v27667; return Value(true); }()); if (!static_cast<bool>(v27665)) return v27665; v27665 = ([&]() -> Value { auto v27670 = Get(s->LocalAt(3), Value(int64_t{0})); Value v27671; v27671 = Value("SELL"); if (!static_cast<bool>(Binary("Eq", v27670, v27671))) return Value(false); v27670 = v27671; return Value(true); }()); if (!static_cast<bool>(v27665)) return v27665; v27665 = ([&]() -> Value { auto v27672 = Get(s->LocalAt(3), Value(int64_t{1})); Value v27673; v27673 = s->Global("_V92_P_ITEMS"); if (!static_cast<bool>(Binary("In", v27672, v27673))) return Value(false); v27672 = v27673; return Value(true); }()); return v27665; }()))) {
auto v27674 = Get(s->LocalAt(3), Value(int64_t{1}));
s->SetAt(2, v27674);
auto v27675 = ([&]() -> Value { auto fn27676 = s->Global("min"); Arguments args27677; args27677.positional.reserve(2); args27677.Add(([&]() -> Value { auto fn27678 = s->Global("max"); Arguments args27679; args27679.positional.reserve(2); args27679.Add(Value(int64_t{0}), false); args27679.Add(([&]() -> Value { auto fn27680 = s->Global("int"); Arguments args27681; args27681.Add(Get(s->LocalAt(3), Value(int64_t{2})), false); return Call(c, fn27680, std::move(args27681)); }()), false); return Call(c, fn27678, std::move(args27679)); }()), false); args27677.Add(([&]() -> Value { auto fn27682 = s->Global("max"); Arguments args27683; args27683.positional.reserve(2); args27683.Add(Value(int64_t{0}), false); args27683.Add(([&]() -> Value { auto fn27684 = s->Global("int"); Arguments args27685; args27685.Add(([&]() -> Value { auto fn27686 = PrepareDictionaryGet(s->LocalAt(9)); Arguments args27687; args27687.positional.reserve(2); args27687.Add(s->LocalAt(2), false); args27687.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn27686, std::move(args27687)); }()), false); return Call(c, fn27684, std::move(args27685)); }()), false); return Call(c, fn27682, std::move(args27683)); }()), false); return Call(c, fn27676, std::move(args27677)); }());
s->SetAt(7, v27675);
auto v27688 = ([&]() -> Value { auto v27689 = ([&]() -> Value { auto fn27690 = PrepareDictionaryGet(s->LocalAt(9)); Arguments args27691; args27691.positional.reserve(2); args27691.Add(s->LocalAt(2), false); args27691.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn27690, std::move(args27691)); }()); return Binary("Sub", v27689, s->LocalAt(7)); }());
Put(s->LocalAt(9), s->LocalAt(2), v27688);
auto v27692 = ([&]() -> Value { auto v27693 = ([&]() -> Value { auto fn27694 = PrepareDictionaryGet(s->LocalAt(5)); Arguments args27695; args27695.positional.reserve(2); args27695.Add(s->LocalAt(2), false); args27695.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn27694, std::move(args27695)); }()); return Binary("Add", v27693, s->LocalAt(7)); }());
Put(s->LocalAt(5), s->LocalAt(2), v27692);
}
}
auto v27696 = ([&]() -> Value { auto dict27697 = Dict(); auto key27698 = Value("prev"); Put(dict27697, key27698, ([&]() -> Value { auto dict27699 = Dict(); auto key27700 = Value("step"); Put(dict27699, key27700, s->LocalAt(8)); auto key27701 = Value("shops"); Put(dict27699, key27701, ([&]() -> Value { auto fn27702 = s->Global("list"); Arguments args27703; args27703.Add(([&]() -> Value { auto fn27704 = PrepareDictionaryGet(Get(s->LocalAt(4), Value("town"))); Arguments args27705; args27705.positional.reserve(2); args27705.Add(Value("unlocked_shops"), false); args27705.Add(List({}), false); return CallDictionaryGet(c, fn27704, std::move(args27705)); }()), false); return Call(c, fn27702, std::move(args27703)); }())); auto key27706 = Value("inventory"); Put(dict27699, key27706, ([&]() -> Value { auto fn27707 = s->Global("dict"); Arguments args27708; args27708.Add(Get(Get(s->LocalAt(4), Value("market")), Value("inventory")), false); return Call(c, fn27707, std::move(args27708)); }())); auto key27709 = Value("prices"); Put(dict27699, key27709, ([&]() -> Value { auto fn27710 = s->Global("dict"); Arguments args27711; args27711.Add(Get(Get(s->LocalAt(4), Value("market")), Value("prices")), false); return Call(c, fn27710, std::move(args27711)); }())); auto key27712 = Value("own"); Put(dict27699, key27712, s->LocalAt(5)); return dict27699; }())); return dict27697; }());
Put(s->Global("_V9_RACE"), s->LocalAt(6), v27696);
auto v27713 = s->Global("_E350_REPORT");
auto v27714 = Value("e350_snapshots");
auto v27715 = Get(v27713, v27714);
Put(v27713, v27714, Inplace("Add", v27715, Value(int64_t{1})));
} catch (const Error& error27651) {
if (Matches(error27651, s->Global("Exception"))) {
auto v27716 = s->Global("_E350_REPORT");
auto v27717 = Value("e350_errors");
auto v27718 = Get(v27716, v27717);
Put(v27716, v27717, Inplace("Add", v27718, Value(int64_t{1})));
}
else { throw; }
}
return s->LocalAt(0);
return {};
}
}  // namespace kagg::opponents::compiled
