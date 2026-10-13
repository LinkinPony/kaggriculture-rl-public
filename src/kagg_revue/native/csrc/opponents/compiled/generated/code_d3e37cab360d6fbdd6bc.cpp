// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_d3e37cab360d6fbdd6bc(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "already", "best", "changed", "i", "item", "market", "native", "obs", "ours", "qty", "result", "st", "step", "stock", "t", "tape", "votes"};
s->PrepareSlots(s_names);
auto v27439 = ([&]() -> Value { auto fn27440 = s->Global("int"); Arguments args27441; args27441.Add(Get(s->LocalAt(8), Value("step")), false); return Call(c, fn27440, std::move(args27441)); }());
s->SetAt(13, v27439);
(void)([&]() -> Value { auto fn27442 = s->Global("_v92_p_update"); Arguments args27443; args27443.positional.reserve(2); args27443.Add(s->LocalAt(8), false); args27443.Add(s->LocalAt(12), false); return Call(c, fn27442, std::move(args27443)); }());
if (static_cast<bool>(([&]() -> Value { auto v27444 = ([&]() -> Value { auto v27445 = s->LocalAt(13); Value v27446; v27446 = Value(int64_t{150}); if (!static_cast<bool>(Binary("Lt", v27445, v27446))) return Value(false); v27445 = v27446; return Value(true); }()); if (static_cast<bool>(v27444)) return v27444; v27444 = ([&]() -> Value { auto v27447 = s->LocalAt(13); Value v27448; v27448 = Value(int64_t{700}); if (!static_cast<bool>(Binary("GtE", v27447, v27448))) return Value(false); v27447 = v27448; return Value(true); }()); return v27444; }()))) {
return s->LocalAt(0);
}
if (static_cast<bool>(([&]() -> Value { auto v27449 = ([&]() -> Value { auto v27450 = ([&]() -> Value { auto v27452 = s->LocalAt(13); return Binary("Mod", v27452, s->Global("_V92_P_EVERY")); }()); Value v27451; v27451 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v27450, v27451))) return Value(false); v27450 = v27451; return Value(true); }()); if (static_cast<bool>(v27449)) return v27449; v27449 = ([&]() -> Value { auto v27453 = Value("best"); Value v27454; v27454 = s->LocalAt(12); if (!static_cast<bool>(Binary("NotIn", v27453, v27454))) return Value(false); v27453 = v27454; return Value(true); }()); return v27449; }()))) {
auto v27455 = ([&]() -> Value { auto fn27456 = s->Global("_v92_p_forecast"); Arguments args27457; args27457.positional.reserve(2); args27457.Add(s->LocalAt(8), false); args27457.Add(s->LocalAt(12), false); return Call(c, fn27456, std::move(args27457)); }());
Put(s->LocalAt(12), Value("best"), v27455);
}
auto v27458 = Get(s->LocalAt(12), Value("best"));
s->SetAt(2, v27458);
if (static_cast<bool>(Unary("Not", s->LocalAt(2)))) {
return s->LocalAt(0);
}
auto v27459 = ([&]() -> Value { auto fn27460 = PrepareDictionaryGet(Attribute(Attribute(s->Global("_IMPL"), "chassis"), "players")); Arguments args27461; args27461.Add(([&]() -> Value { auto fn27462 = s->Global("int"); Arguments args27463; args27463.Add(Get(s->LocalAt(8), Value("player")), false); return Call(c, fn27462, std::move(args27463)); }()), false); return CallDictionaryGet(c, fn27460, std::move(args27461)); }());
s->SetAt(7, v27459);
if (static_cast<bool>(([&]() -> Value { auto v27464 = Unary("Not", s->LocalAt(7)); if (static_cast<bool>(v27464)) return v27464; v27464 = ([&]() -> Value { auto v27465 = ([&]() -> Value { auto fn27467 = PrepareDictionaryGet(s->LocalAt(7)); Arguments args27468; args27468.Add(Value("route"), false); return CallDictionaryGet(c, fn27467, std::move(args27468)); }()); Value v27466; v27466 = Attribute(Attribute(s->Global("_IMPL"), "chassis"), "routes"); if (!static_cast<bool>(Binary("NotIn", v27465, v27466))) return Value(false); v27465 = v27466; return Value(true); }()); return v27464; }()))) {
return s->LocalAt(0);
}
auto v27469 = Get(Attribute(Attribute(s->Global("_IMPL"), "chassis"), "routes"), Get(s->LocalAt(7), Value("route")));
s->SetAt(16, v27469);
auto v27470 = ([&]() -> Value { auto comp27471 = std::make_shared<Scope>(); comp27471->globals = s->globals; comp27471->parent = s; static constexpr const char* comp27471_names[] = {"o"}; comp27471->PrepareSlots(comp27471_names); auto result27472 = List(); for (const auto& item27473 : Iterate(([&]() -> Value { auto v27474 = ([&]() -> Value { auto fn27475 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args27476; args27476.Add(Value("market"), false); return CallDictionaryGet(c, fn27475, std::move(args27476)); }()); if (static_cast<bool>(v27474)) return v27474; v27474 = List({}); return v27474; }()))) { comp27471->SetAt(0, item27473); result27472.node()->sequence.push_back(([&]() -> Value { auto fn27477 = comp27471->Global("list"); Arguments args27478; args27478.Add(comp27471->LocalAt(0), false); return Call(c, fn27477, std::move(args27478)); }())); } return result27472; }());
s->SetAt(6, v27470);
auto v27479 = ([&]() -> Value { auto comp27480 = std::make_shared<Scope>(); comp27480->globals = s->globals; comp27480->parent = s; static constexpr const char* comp27480_names[] = {"o"}; comp27480->PrepareSlots(comp27480_names); auto result27481 = List(); for (const auto& item27482 : Iterate(s->LocalAt(6))) { comp27480->SetAt(0, item27482); if (!static_cast<bool>(([&]() -> Value { auto v27483 = ([&]() -> Value { auto v27484 = ([&]() -> Value { auto fn27486 = comp27480->Global("len"); Arguments args27487; args27487.Add(comp27480->LocalAt(0), false); return Call(c, fn27486, std::move(args27487)); }()); Value v27485; v27485 = Value(int64_t{1}); if (!static_cast<bool>(Binary("Gt", v27484, v27485))) return Value(false); v27484 = v27485; return Value(true); }()); if (!static_cast<bool>(v27483)) return v27483; v27483 = ([&]() -> Value { auto v27488 = Get(comp27480->LocalAt(0), Value(int64_t{0})); Value v27489; v27489 = Tuple({Value("SELL"), Value("BUY_PRODUCT")}); if (!static_cast<bool>(Binary("In", v27488, v27489))) return Value(false); v27488 = v27489; return Value(true); }()); return v27483; }()))) continue; result27481.node()->sequence.push_back(Get(comp27480->LocalAt(0), Value(int64_t{1}))); } return Set(result27481.node()->sequence); }());
s->SetAt(1, v27479);
auto v27490 = ([&]() -> Value { auto fn27491 = s->Global("projected_shed"); Arguments args27492; args27492.positional.reserve(2); args27492.Add(s->LocalAt(0), false); args27492.Add(([&]() -> Value { auto fn27493 = s->Global("FarmView"); Arguments args27494; args27494.Add(s->LocalAt(8), false); return Call(c, fn27493, std::move(args27494)); }()), false); return Call(c, fn27491, std::move(args27492)); }());
s->SetAt(14, v27490);
auto v27495 = Value(false);
s->SetAt(3, v27495);
for (const auto& item27496 : Iterate(([&]() -> Value { auto fn27497 = s->Global("enumerate"); Arguments args27498; args27498.Add(s->Global("_V92_P_ITEMS"), false); return Call(c, fn27497, std::move(args27498)); }()))) {
auto unpack27499 = Iterate(item27496);
ValidateUnpack(unpack27499, 2, false);
s->SetAt(4, unpack27499.at(0));
s->SetAt(5, unpack27499.at(1));
if (static_cast<bool>(([&]() -> Value { auto v27500 = ([&]() -> Value { auto v27501 = s->LocalAt(5); Value v27502; v27502 = s->Global("_V92_P_USE"); if (!static_cast<bool>(Binary("NotIn", v27501, v27502))) return Value(false); v27501 = v27502; return Value(true); }()); if (static_cast<bool>(v27500)) return v27500; v27500 = ([&]() -> Value { auto v27503 = s->LocalAt(5); Value v27504; v27504 = s->LocalAt(1); if (!static_cast<bool>(Binary("In", v27503, v27504))) return Value(false); v27503 = v27504; return Value(true); }()); if (static_cast<bool>(v27500)) return v27500; v27500 = ([&]() -> Value { auto v27505 = ([&]() -> Value { auto fn27507 = s->Global("len"); Arguments args27508; args27508.Add(s->LocalAt(6), false); return Call(c, fn27507, std::move(args27508)); }()); Value v27506; v27506 = s->Global("MAX_ORDERS"); if (!static_cast<bool>(Binary("GtE", v27505, v27506))) return Value(false); v27505 = v27506; return Value(true); }()); return v27500; }()))) {
continue;
}
auto v27509 = ([&]() -> Value { auto fn27510 = s->Global("sum"); Arguments args27511; args27511.Add(([&]() -> Value { auto comp27512 = std::make_shared<Scope>(); comp27512->globals = s->globals; comp27512->parent = s; static constexpr const char* comp27512_names[] = {"ev"}; comp27512->PrepareSlots(comp27512_names); auto result27513 = List(); for (const auto& item27514 : Iterate(s->LocalAt(2))) { comp27512->SetAt(0, item27514); if (!static_cast<bool>(([&]() -> Value { auto v27515 = ([&]() -> Value { auto v27517 = ([&]() -> Value { auto fn27518 = PrepareDictionaryGet(comp27512->LocalAt(0)); Arguments args27519; args27519.positional.reserve(2); args27519.Add(Tuple({([&]() -> Value { auto v27520 = comp27512->Captured("step"); return Binary("Add", v27520, Value(int64_t{1})); }()), comp27512->Captured("i")}), false); args27519.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn27518, std::move(args27519)); }()); return Binary("Add", v27517, ([&]() -> Value { auto fn27521 = PrepareDictionaryGet(comp27512->LocalAt(0)); Arguments args27522; args27522.positional.reserve(2); args27522.Add(Tuple({([&]() -> Value { auto v27523 = comp27512->Captured("step"); return Binary("Add", v27523, Value(int64_t{2})); }()), comp27512->Captured("i")}), false); args27522.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn27521, std::move(args27522)); }())); }()); Value v27516; v27516 = comp27512->Global("_V92_P_K"); if (!static_cast<bool>(Binary("GtE", v27515, v27516))) return Value(false); v27515 = v27516; return Value(true); }()))) continue; result27513.node()->sequence.push_back(Value(int64_t{1})); } return result27513; }()), false); return Call(c, fn27510, std::move(args27511)); }());
s->SetAt(17, v27509);
if (static_cast<bool>(([&]() -> Value { auto v27524 = s->LocalAt(17); Value v27525; v27525 = Value(int64_t{1}); if (!static_cast<bool>(Binary("Lt", v27524, v27525))) return Value(false); v27524 = v27525; return Value(true); }()))) {
continue;
}
auto v27526 = Value(int64_t{0});
s->SetAt(9, v27526);
for (const auto& item27527 : Iterate(([&]() -> Value { auto fn27528 = s->Global("range"); Arguments args27529; args27529.positional.reserve(2); args27529.Add(([&]() -> Value { auto v27530 = s->LocalAt(13); return Binary("Add", v27530, Value(int64_t{1})); }()), false); args27529.Add(([&]() -> Value { auto fn27531 = s->Global("min"); Arguments args27532; args27532.positional.reserve(2); args27532.Add(([&]() -> Value { auto fn27533 = s->Global("len"); Arguments args27534; args27534.Add(s->LocalAt(16), false); return Call(c, fn27533, std::move(args27534)); }()), false); args27532.Add(([&]() -> Value { auto v27535 = ([&]() -> Value { auto v27536 = s->LocalAt(13); return Binary("Add", v27536, s->Global("_V92_P_H")); }()); return Binary("Add", v27535, Value(int64_t{1})); }()), false); return Call(c, fn27531, std::move(args27532)); }()), false); return Call(c, fn27528, std::move(args27529)); }()))) {
s->SetAt(15, item27527);
auto v27537 = s->LocalAt(9);
s->SetAt(9, Inplace("Add", v27537, ([&]() -> Value { auto fn27538 = s->Global("sum"); Arguments args27539; args27539.Add(([&]() -> Value { auto comp27540 = std::make_shared<Scope>(); comp27540->globals = s->globals; comp27540->parent = s; static constexpr const char* comp27540_names[] = {"o"}; comp27540->PrepareSlots(comp27540_names); auto result27541 = List(); for (const auto& item27542 : Iterate(([&]() -> Value { auto v27543 = ([&]() -> Value { auto fn27544 = PrepareDictionaryGet(([&]() -> Value { auto v27546 = Get(s->LocalAt(16), s->LocalAt(15)); if (static_cast<bool>(v27546)) return v27546; v27546 = ([&]() -> Value { auto dict27547 = Dict(); return dict27547; }()); return v27546; }())); Arguments args27545; args27545.Add(Value("market"), false); return CallDictionaryGet(c, fn27544, std::move(args27545)); }()); if (static_cast<bool>(v27543)) return v27543; v27543 = List({}); return v27543; }()))) { comp27540->SetAt(0, item27542); if (!static_cast<bool>(([&]() -> Value { auto v27548 = ([&]() -> Value { auto v27549 = ([&]() -> Value { auto fn27551 = comp27540->Global("len"); Arguments args27552; args27552.Add(comp27540->LocalAt(0), false); return Call(c, fn27551, std::move(args27552)); }()); Value v27550; v27550 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v27549, v27550))) return Value(false); v27549 = v27550; return Value(true); }()); if (!static_cast<bool>(v27548)) return v27548; v27548 = ([&]() -> Value { auto v27553 = Get(comp27540->LocalAt(0), Value(int64_t{0})); Value v27554; v27554 = Value("SELL"); if (!static_cast<bool>(Binary("Eq", v27553, v27554))) return Value(false); v27553 = v27554; return Value(true); }()); if (!static_cast<bool>(v27548)) return v27548; v27548 = ([&]() -> Value { auto v27555 = Get(comp27540->LocalAt(0), Value(int64_t{1})); Value v27556; v27556 = comp27540->Captured("item"); if (!static_cast<bool>(Binary("Eq", v27555, v27556))) return Value(false); v27555 = v27556; return Value(true); }()); return v27548; }()))) continue; result27541.node()->sequence.push_back(([&]() -> Value { auto fn27557 = comp27540->Global("min"); Arguments args27558; args27558.positional.reserve(2); args27558.Add(Value(int64_t{100}), false); args27558.Add(([&]() -> Value { auto fn27559 = comp27540->Global("int"); Arguments args27560; args27560.Add(Get(comp27540->LocalAt(0), Value(int64_t{2})), false); return Call(c, fn27559, std::move(args27560)); }()), false); return Call(c, fn27557, std::move(args27558)); }())); } return result27541; }()), false); return Call(c, fn27538, std::move(args27539)); }())));
}
auto v27561 = ([&]() -> Value { auto fn27562 = s->Global("min"); Arguments args27563; args27563.positional.reserve(2); args27563.Add(([&]() -> Value { auto fn27564 = s->Global("int"); Arguments args27565; args27565.Add(([&]() -> Value { auto fn27566 = PrepareDictionaryGet(s->LocalAt(14)); Arguments args27567; args27567.positional.reserve(2); args27567.Add(s->LocalAt(5), false); args27567.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn27566, std::move(args27567)); }()), false); return Call(c, fn27564, std::move(args27565)); }()), false); args27563.Add(s->LocalAt(9), false); return Call(c, fn27562, std::move(args27563)); }());
s->SetAt(10, v27561);
if (static_cast<bool>(([&]() -> Value { auto v27568 = s->LocalAt(10); Value v27569; v27569 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v27568, v27569))) return Value(false); v27568 = v27569; return Value(true); }()))) {
(void)([&]() -> Value { auto fn27570 = Attribute(s->LocalAt(6), "insert"); Arguments args27571; args27571.positional.reserve(2); args27571.Add(Value(int64_t{0}), false); args27571.Add(List({Value("SELL"), s->LocalAt(5), s->LocalAt(10)}), false); return Call(c, fn27570, std::move(args27571)); }());
auto v27572 = s->Global("_V92_P_REPORT");
auto v27573 = Value("pred_units");
auto v27574 = Get(v27572, v27573);
Put(v27572, v27573, Inplace("Add", v27574, s->LocalAt(10)));
auto v27575 = s->Global("_V92_P_REPORT");
auto v27576 = Value("pred_fires");
auto v27577 = Get(v27575, v27576);
Put(v27575, v27576, Inplace("Add", v27577, Value(int64_t{1})));
auto v27578 = Value(true);
s->SetAt(3, v27578);
}
}
if (static_cast<bool>(Unary("Not", s->LocalAt(3)))) {
return s->LocalAt(0);
}
auto v27579 = ([&]() -> Value { auto fn27580 = s->Global("dict"); Arguments args27581; args27581.Add(s->LocalAt(0), false); return Call(c, fn27580, std::move(args27581)); }());
s->SetAt(11, v27579);
auto v27582 = Slice(s->LocalAt(6), Value{}, s->Global("MAX_ORDERS"), Value{});
Put(s->LocalAt(11), Value("market"), v27582);
return s->LocalAt(11);
return {};
}
}  // namespace kagg::opponents::compiled
