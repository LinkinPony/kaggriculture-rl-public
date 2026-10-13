// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_c070f01f6c88c6c2f460(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "best", "buys", "cash", "evs", "extra_cost", "farm", "gain", "goose", "k", "k_plan", "market", "obs", "ok_ratio", "st", "step"};
s->PrepareSlots(s_names);
auto v24554 = ([&]() -> Value { auto v24555 = ([&]() -> Value { auto fn24556 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args24557; args24557.Add(Value("market"), false); return CallDictionaryGet(c, fn24556, std::move(args24557)); }()); if (static_cast<bool>(v24555)) return v24555; v24555 = List({}); return v24555; }());
s->SetAt(11, v24554);
auto v24558 = ([&]() -> Value { auto comp24559 = std::make_shared<Scope>(); comp24559->globals = s->globals; comp24559->parent = s; static constexpr const char* comp24559_names[] = {"o"}; comp24559->PrepareSlots(comp24559_names); auto result24560 = List(); for (const auto& item24561 : Iterate(s->LocalAt(11))) { comp24559->SetAt(0, item24561); if (!static_cast<bool>(([&]() -> Value { auto v24562 = ([&]() -> Value { auto v24563 = ([&]() -> Value { auto fn24565 = comp24559->Global("len"); Arguments args24566; args24566.Add(comp24559->LocalAt(0), false); return Call(c, fn24565, std::move(args24566)); }()); Value v24564; v24564 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v24563, v24564))) return Value(false); v24563 = v24564; return Value(true); }()); if (!static_cast<bool>(v24562)) return v24562; v24562 = ([&]() -> Value { auto v24567 = Get(comp24559->LocalAt(0), Value(int64_t{0})); Value v24568; v24568 = Value("BUY_ANIMAL"); if (!static_cast<bool>(Binary("Eq", v24567, v24568))) return Value(false); v24567 = v24568; return Value(true); }()); if (!static_cast<bool>(v24562)) return v24562; v24562 = ([&]() -> Value { auto v24569 = Get(comp24559->LocalAt(0), Value(int64_t{1})); Value v24570; v24570 = Value("GOOSE"); if (!static_cast<bool>(Binary("Eq", v24569, v24570))) return Value(false); v24569 = v24570; return Value(true); }()); return v24562; }()))) continue; result24560.node()->sequence.push_back(comp24559->LocalAt(0)); } return result24560; }());
s->SetAt(2, v24558);
if (static_cast<bool>(Unary("Not", s->LocalAt(2)))) {
return Value{};
}
auto v24571 = Value(true);
Put(s->LocalAt(14), Value("decided"), v24571);
auto v24572 = ([&]() -> Value { auto fn24573 = s->Global("int"); Arguments args24574; args24574.Add(Get(s->LocalAt(12), Value("step")), false); return Call(c, fn24573, std::move(args24574)); }());
s->SetAt(15, v24572);
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto v24575 = s->Global("_HD2_FROM"); Value v24576; v24576 = s->LocalAt(15); if (!static_cast<bool>(Binary("LtE", v24575, v24576))) return Value(false); v24575 = v24576; v24576 = s->Global("_HD2_TO"); if (!static_cast<bool>(Binary("Lt", v24575, v24576))) return Value(false); v24575 = v24576; return Value(true); }())))) {
return Value{};
}
auto v24577 = Get(Get(s->LocalAt(12), Value("farms")), ([&]() -> Value { auto fn24578 = s->Global("int"); Arguments args24579; args24579.Add(Get(s->LocalAt(12), Value("player")), false); return Call(c, fn24578, std::move(args24579)); }()));
s->SetAt(6, v24577);
if (static_cast<bool>(([&]() -> Value { auto comp24580 = std::make_shared<Scope>(); comp24580->globals = s->globals; comp24580->parent = s; static constexpr const char* comp24580_names[] = {"row", "t"}; comp24580->PrepareSlots(comp24580_names); auto result24581 = List(); for (const auto& item24582 : Iterate(Get(s->LocalAt(6), Value("tiles")))) { comp24580->SetAt(0, item24582); for (const auto& item24583 : Iterate(comp24580->LocalAt(0))) { comp24580->SetAt(1, item24583); if (static_cast<bool>(([&]() -> Value { auto v24584 = ([&]() -> Value { auto fn24585 = comp24580->Global("isinstance"); Arguments args24586; args24586.positional.reserve(2); args24586.Add(comp24580->LocalAt(1), false); args24586.Add(comp24580->Global("dict"), false); return Call(c, fn24585, std::move(args24586)); }()); if (!static_cast<bool>(v24584)) return v24584; v24584 = ([&]() -> Value { auto v24587 = ([&]() -> Value { auto fn24589 = PrepareDictionaryGet(comp24580->LocalAt(1)); Arguments args24590; args24590.Add(Value("kind"), false); return CallDictionaryGet(c, fn24589, std::move(args24590)); }()); Value v24588; v24588 = Value("COOP"); if (!static_cast<bool>(Binary("Eq", v24587, v24588))) return Value(false); v24587 = v24588; return Value(true); }()); return v24584; }()))) return Value(true); } } return Value(false); }()))) {
auto v24591 = Value("skip:coop_exists");
Put(s->Global("_HD2_REPORT"), Value("hd2_decision"), v24591);
return Value{};
}
auto v24592 = ([&]() -> Value { auto fn24593 = s->Global("sum"); Arguments args24594; args24594.Add(([&]() -> Value { auto comp24595 = std::make_shared<Scope>(); comp24595->globals = s->globals; comp24595->parent = s; static constexpr const char* comp24595_names[] = {"o"}; comp24595->PrepareSlots(comp24595_names); auto result24596 = List(); for (const auto& item24597 : Iterate(s->LocalAt(2))) { comp24595->SetAt(0, item24597); result24596.node()->sequence.push_back(([&]() -> Value { auto fn24598 = comp24595->Global("max"); Arguments args24599; args24599.positional.reserve(2); args24599.Add(Value(int64_t{0}), false); args24599.Add(([&]() -> Value { auto fn24600 = comp24595->Global("int"); Arguments args24601; args24601.Add(Get(comp24595->LocalAt(0), Value(int64_t{2})), false); return Call(c, fn24600, std::move(args24601)); }()), false); return Call(c, fn24598, std::move(args24599)); }())); } return result24596; }()), false); return Call(c, fn24593, std::move(args24594)); }());
s->SetAt(9, v24592);
auto v24602 = ([&]() -> Value { auto fn24603 = s->Global("max"); Arguments args24604; args24604.positional.reserve(2); args24604.Add(s->LocalAt(9), false); args24604.Add(Value(int64_t{3}), false); return Call(c, fn24603, std::move(args24604)); }());
s->SetAt(10, v24602);
auto v24605 = ([&]() -> Value { auto comp24606 = std::make_shared<Scope>(); comp24606->globals = s->globals; comp24606->parent = s; static constexpr const char* comp24606_names[] = {"opt"}; comp24606->PrepareSlots(comp24606_names); auto result24607 = Dict(); for (const auto& item24608 : Iterate(([&]() -> Value { auto v24609 = Tuple({Value("GOOSE")}); return Binary("Add", v24609, ([&]() -> Value { auto fn24610 = s->Global("tuple"); Arguments args24611; args24611.Add(s->Global("_HD2_OPTIONS"), false); return Call(c, fn24610, std::move(args24611)); }())); }()))) { comp24606->SetAt(0, item24608); Put(result24607, comp24606->LocalAt(0), Get(([&]() -> Value { auto fn24612 = comp24606->Global("_hd2_ev"); Arguments args24613; args24613.positional.reserve(4); args24613.Add(comp24606->LocalAt(0), false); args24613.Add(comp24606->Captured("k_plan"), false); args24613.Add(comp24606->Captured("obs"), false); args24613.Add(comp24606->Captured("st"), false); return Call(c, fn24612, std::move(args24613)); }()), Value(int64_t{0}))); } return result24607; }());
s->SetAt(4, v24605);
auto v24614 = ([&]() -> Value { auto fn24615 = Attribute(Value(","), "join"); Arguments args24616; args24616.Add(([&]() -> Value { auto comp24617 = std::make_shared<Scope>(); comp24617->globals = s->globals; comp24617->parent = s; static constexpr const char* comp24617_names[] = {"o", "v"}; comp24617->PrepareSlots(comp24617_names); auto result24618 = List(); for (const auto& item24619 : Iterate(([&]() -> Value { auto fn24620 = s->Global("sorted"); Arguments args24621; args24621.Add(([&]() -> Value { auto fn24622 = Attribute(s->LocalAt(4), "items"); Arguments args24623; return Call(c, fn24622, std::move(args24623)); }()), false); return Call(c, fn24620, std::move(args24621)); }()))) { auto unpack24624 = Iterate(item24619); ValidateUnpack(unpack24624, 2, false); comp24617->SetAt(0, unpack24624.at(0)); comp24617->SetAt(1, unpack24624.at(1)); result24618.node()->sequence.push_back(([&]() -> Value { auto v24625 = Value("%s:%d"); return Binary("Mod", v24625, Tuple({comp24617->LocalAt(0), comp24617->LocalAt(1)})); }())); } return result24618; }()), false); return Call(c, fn24615, std::move(args24616)); }());
Put(s->Global("_HD2_REPORT"), Value("hd2_ev"), v24614);
auto v24626 = (static_cast<bool>(s->Global("_HD2_OPTIONS")) ? ([&]() -> Value { auto fn24627 = s->Global("max"); Arguments args24628; args24628.Add(s->Global("_HD2_OPTIONS"), false); args24628.Keyword("key", Define(&Code_16a3d48d5ed2a5185225, s, Signature{{"o"}, {}, {}, {}, "", "", ([]() -> std::span<const char* const> { static constexpr const char* names[] = {"o"}; return names; }())}, true, "<lambda>")); return Call(c, fn24627, std::move(args24628)); }()) : Value{});
s->SetAt(1, v24626);
auto v24629 = Get(s->LocalAt(4), Value("GOOSE"));
s->SetAt(8, v24629);
if (static_cast<bool>(([&]() -> Value { auto v24630 = s->LocalAt(1); Value v24631; v24631 = Value{}; if (!static_cast<bool>(Binary("Is", v24630, v24631))) return Value(false); v24630 = v24631; return Value(true); }()))) {
return Value{};
}
auto v24632 = ([&]() -> Value { auto v24633 = Get(s->LocalAt(4), s->LocalAt(1)); return Binary("Sub", v24633, s->LocalAt(8)); }());
s->SetAt(7, v24632);
auto v24634 = ([&]() -> Value { auto v24635 = Get(s->LocalAt(4), s->LocalAt(1)); Value v24636; v24636 = ([&]() -> Value { auto v24637 = s->Global("_HD2_RATIO"); return Binary("Mult", v24637, ([&]() -> Value { auto fn24638 = s->Global("max"); Arguments args24639; args24639.positional.reserve(2); args24639.Add(s->LocalAt(8), false); args24639.Add(Value(1.0), false); return Call(c, fn24638, std::move(args24639)); }())); }()); if (!static_cast<bool>(Binary("GtE", v24635, v24636))) return Value(false); v24635 = v24636; return Value(true); }());
s->SetAt(13, v24634);
auto v24640 = ([&]() -> Value { auto v24641 = ([&]() -> Value { auto v24642 = Get(Get(s->Global("_HD2_SPEC"), s->LocalAt(1)), Value("cost")); return Binary("Sub", v24642, Value(int64_t{300})); }()); return Binary("Mult", v24641, s->LocalAt(9)); }());
s->SetAt(5, v24640);
auto v24643 = ([&]() -> Value { auto fn24644 = s->Global("float"); Arguments args24645; args24645.Add(([&]() -> Value { auto fn24646 = PrepareDictionaryGet(s->LocalAt(6)); Arguments args24647; args24647.positional.reserve(2); args24647.Add(Value("money"), false); args24647.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn24646, std::move(args24647)); }()), false); return Call(c, fn24644, std::move(args24645)); }());
s->SetAt(3, v24643);
if (static_cast<bool>(([&]() -> Value { auto v24648 = ([&]() -> Value { auto v24649 = s->LocalAt(7); Value v24650; v24650 = s->Global("_HD2_MIN_GAIN"); if (!static_cast<bool>(Binary("GtE", v24649, v24650))) return Value(false); v24649 = v24650; return Value(true); }()); if (!static_cast<bool>(v24648)) return v24648; v24648 = s->LocalAt(13); if (!static_cast<bool>(v24648)) return v24648; v24648 = ([&]() -> Value { auto v24651 = s->LocalAt(3); Value v24652; v24652 = ([&]() -> Value { auto v24653 = ([&]() -> Value { auto v24654 = ([&]() -> Value { auto v24655 = Value(int64_t{300}); return Binary("Mult", v24655, s->LocalAt(9)); }()); return Binary("Add", v24654, s->LocalAt(5)); }()); return Binary("Add", v24653, Value(int64_t{50})); }()); if (!static_cast<bool>(Binary("GtE", v24651, v24652))) return Value(false); v24651 = v24652; return Value(true); }()); return v24648; }()))) {
auto v24656 = s->LocalAt(1);
Put(s->LocalAt(14), Value("mode"), v24656);
auto v24657 = ([&]() -> Value { auto v24658 = Value("%s@%d"); return Binary("Mod", v24658, Tuple({s->LocalAt(1), s->LocalAt(15)})); }());
Put(s->Global("_HD2_REPORT"), Value("hd2_decision"), v24657);
}
else {
auto v24659 = ([&]() -> Value { auto v24660 = Value("keep@%d"); return Binary("Mod", v24660, s->LocalAt(15)); }());
Put(s->Global("_HD2_REPORT"), Value("hd2_decision"), v24659);
}
return {};
}
}  // namespace kagg::opponents::compiled
