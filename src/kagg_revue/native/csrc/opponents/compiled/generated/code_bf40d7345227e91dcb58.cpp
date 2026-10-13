// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_bf40d7345227e91dcb58(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"a", "actor", "cache", "carried", "dedicated", "desired", "inputs", "key", "native", "obs", "parent", "pending", "pickup", "plan", "player", "purchase", "reserve", "role", "route", "state", "step", "t"};
s->PrepareSlots(s_names);
auto v9473 = ([&]() -> Value { auto fn9474 = s->Global("int"); Arguments args9475; args9475.Add(Get(s->LocalAt(9), Value("step")), false); return Call(c, fn9474, std::move(args9475)); }());
s->SetAt(20, v9473);
auto v9476 = ([&]() -> Value { auto fn9477 = s->Global("int"); Arguments args9478; args9478.Add(Get(s->LocalAt(9), Value("player")), false); return Call(c, fn9477, std::move(args9478)); }());
s->SetAt(14, v9476);
auto v9479 = Get(Attribute(Attribute(s->Global("_IMPL"), "chassis"), "players"), s->LocalAt(14));
s->SetAt(8, v9479);
auto v9480 = Get(s->LocalAt(8), Value("route"));
s->SetAt(18, v9480);
auto v9481 = Tuple({s->LocalAt(18), s->LocalAt(20)});
s->SetAt(7, v9481);
auto v9482 = ([&]() -> Value { auto fn9483 = Attribute(s->LocalAt(19), "setdefault"); Arguments args9484; args9484.positional.reserve(2); args9484.Add(Value("native_reserves"), false); args9484.Add(([&]() -> Value { auto dict9485 = Dict(); return dict9485; }()), false); return Call(c, fn9483, std::move(args9484)); }());
s->SetAt(2, v9482);
if (static_cast<bool>(([&]() -> Value { auto v9486 = s->LocalAt(18); Value v9487; v9487 = s->LocalAt(2); if (!static_cast<bool>(Binary("NotIn", v9486, v9487))) return Value(false); v9486 = v9487; return Value(true); }()))) {
auto v9488 = ([&]() -> Value { auto v9489 = List({Value(int64_t{0})}); return Binary("Mult", v9489, Value(int64_t{720})); }());
s->SetAt(16, v9488);
for (const auto& item9490 : Iterate(([&]() -> Value { auto fn9491 = s->Global("range"); Arguments args9492; args9492.positional.reserve(3); args9492.Add(Value(int64_t{718}), false); args9492.Add(Unary("USub", Value(int64_t{1})), false); args9492.Add(Unary("USub", Value(int64_t{1})), false); return Call(c, fn9491, std::move(args9492)); }()))) {
s->SetAt(21, item9490);
auto v9493 = Get(Get(Attribute(Attribute(s->Global("_IMPL"), "chassis"), "routes"), (static_cast<bool>(([&]() -> Value { auto v9494 = s->LocalAt(21); Value v9495; v9495 = Value(int64_t{648}); if (!static_cast<bool>(Binary("GtE", v9494, v9495))) return Value(false); v9494 = v9495; return Value(true); }())) ? Value(int64_t{2}) : s->LocalAt(18))), s->LocalAt(21));
s->SetAt(0, v9493);
auto v9496 = ([&]() -> Value { auto fn9497 = s->Global("sum"); Arguments args9498; args9498.Add(([&]() -> Value { auto comp9499 = std::make_shared<Scope>(); comp9499->globals = s->globals; comp9499->parent = s; static constexpr const char* comp9499_names[] = {"c"}; comp9499->PrepareSlots(comp9499_names); auto result9500 = List(); for (const auto& item9501 : Iterate(([&]() -> Value { Arguments args9502; args9502.Add(([&]() -> Value { auto v9503 = ([&]() -> Value { auto fn9504 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args9505; args9505.Add(Value("farmer"), false); return CallDictionaryGet(c, fn9504, std::move(args9505)); }()); if (static_cast<bool>(v9503)) return v9503; v9503 = List({Value("PASS")}); return v9503; }()), false); args9502.Add(([&]() -> Value { auto v9506 = ([&]() -> Value { auto fn9507 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args9508; args9508.Add(Value("hands"), false); return CallDictionaryGet(c, fn9507, std::move(args9508)); }()); if (static_cast<bool>(v9506)) return v9506; v9506 = List({}); return v9506; }()), true); return List(std::move(args9502.positional)); }()))) { comp9499->SetAt(0, item9501); if (!static_cast<bool>(([&]() -> Value { auto v9509 = ([&]() -> Value { auto v9510 = ([&]() -> Value { auto fn9512 = comp9499->Global("len"); Arguments args9513; args9513.Add(comp9499->LocalAt(0), false); return Call(c, fn9512, std::move(args9513)); }()); Value v9511; v9511 = Value(int64_t{1}); if (!static_cast<bool>(Binary("Gt", v9510, v9511))) return Value(false); v9510 = v9511; return Value(true); }()); if (!static_cast<bool>(v9509)) return v9509; v9509 = ([&]() -> Value { auto v9514 = Slice(comp9499->LocalAt(0), Value{}, Value(int64_t{2}), Value{}); Value v9515; v9515 = List({Value("PICKUP"), Value("FERTILIZER")}); if (!static_cast<bool>(Binary("Eq", v9514, v9515))) return Value(false); v9514 = v9515; return Value(true); }()); return v9509; }()))) continue; result9500.node()->sequence.push_back(([&]() -> Value { auto fn9516 = comp9499->Global("max"); Arguments args9517; args9517.positional.reserve(2); args9517.Add(Value(int64_t{0}), false); args9517.Add((static_cast<bool>(([&]() -> Value { auto v9518 = ([&]() -> Value { auto fn9520 = comp9499->Global("len"); Arguments args9521; args9521.Add(comp9499->LocalAt(0), false); return Call(c, fn9520, std::move(args9521)); }()); Value v9519; v9519 = Value(int64_t{2}); if (!static_cast<bool>(Binary("Gt", v9518, v9519))) return Value(false); v9518 = v9519; return Value(true); }())) ? ([&]() -> Value { auto fn9522 = comp9499->Global("int"); Arguments args9523; args9523.Add(Get(comp9499->LocalAt(0), Value(int64_t{2})), false); return Call(c, fn9522, std::move(args9523)); }()) : Value(int64_t{1})), false); return Call(c, fn9516, std::move(args9517)); }())); } return result9500; }()), false); return Call(c, fn9497, std::move(args9498)); }());
s->SetAt(12, v9496);
auto v9524 = ([&]() -> Value { auto fn9525 = s->Global("sum"); Arguments args9526; args9526.Add(([&]() -> Value { auto comp9527 = std::make_shared<Scope>(); comp9527->globals = s->globals; comp9527->parent = s; static constexpr const char* comp9527_names[] = {"o"}; comp9527->PrepareSlots(comp9527_names); auto result9528 = List(); for (const auto& item9529 : Iterate(([&]() -> Value { auto fn9530 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args9531; args9531.positional.reserve(2); args9531.Add(Value("market"), false); args9531.Add(List({}), false); return CallDictionaryGet(c, fn9530, std::move(args9531)); }()))) { comp9527->SetAt(0, item9529); if (!static_cast<bool>(([&]() -> Value { auto v9532 = ([&]() -> Value { auto v9533 = ([&]() -> Value { auto fn9535 = comp9527->Global("len"); Arguments args9536; args9536.Add(comp9527->LocalAt(0), false); return Call(c, fn9535, std::move(args9536)); }()); Value v9534; v9534 = Value(int64_t{2}); if (!static_cast<bool>(Binary("Gt", v9533, v9534))) return Value(false); v9533 = v9534; return Value(true); }()); if (!static_cast<bool>(v9532)) return v9532; v9532 = ([&]() -> Value { auto v9537 = Slice(comp9527->LocalAt(0), Value{}, Value(int64_t{2}), Value{}); Value v9538; v9538 = List({Value("BUY_PRODUCT"), Value("FERTILIZER")}); if (!static_cast<bool>(Binary("Eq", v9537, v9538))) return Value(false); v9537 = v9538; return Value(true); }()); return v9532; }()))) continue; result9528.node()->sequence.push_back(([&]() -> Value { auto fn9539 = comp9527->Global("max"); Arguments args9540; args9540.positional.reserve(2); args9540.Add(Value(int64_t{0}), false); args9540.Add(([&]() -> Value { auto fn9541 = comp9527->Global("int"); Arguments args9542; args9542.Add(Get(comp9527->LocalAt(0), Value(int64_t{2})), false); return Call(c, fn9541, std::move(args9542)); }()), false); return Call(c, fn9539, std::move(args9540)); }())); } return result9528; }()), false); return Call(c, fn9525, std::move(args9526)); }());
s->SetAt(15, v9524);
auto v9543 = ([&]() -> Value { auto v9544 = s->LocalAt(12); return Binary("Add", v9544, ([&]() -> Value { auto fn9545 = s->Global("max"); Arguments args9546; args9546.positional.reserve(2); args9546.Add(Value(int64_t{0}), false); args9546.Add(([&]() -> Value { auto v9547 = Get(s->LocalAt(16), ([&]() -> Value { auto v9548 = s->LocalAt(21); return Binary("Add", v9548, Value(int64_t{1})); }())); return Binary("Sub", v9547, s->LocalAt(15)); }()), false); return Call(c, fn9545, std::move(args9546)); }())); }());
Put(s->LocalAt(16), s->LocalAt(21), v9543);
}
auto v9549 = s->LocalAt(16);
Put(s->LocalAt(2), s->LocalAt(18), v9549);
}
auto v9550 = Value(int64_t{0});
s->SetAt(4, v9550);
for (const auto& item9551 : Iterate(Tuple({([&]() -> Value { auto fn9552 = PrepareDictionaryGet(s->Global("_V219_STATES")); Arguments args9553; args9553.positional.reserve(2); args9553.Add(s->LocalAt(14), false); args9553.Add(([&]() -> Value { auto dict9554 = Dict(); return dict9554; }()), false); return CallDictionaryGet(c, fn9552, std::move(args9553)); }()), ([&]() -> Value { auto fn9555 = PrepareDictionaryGet(s->Global("_V233_STATES")); Arguments args9556; args9556.positional.reserve(2); args9556.Add(s->LocalAt(14), false); args9556.Add(([&]() -> Value { auto dict9557 = Dict(); return dict9557; }()), false); return CallDictionaryGet(c, fn9555, std::move(args9556)); }())}))) {
s->SetAt(10, item9551);
for (const auto& item9558 : Iterate(([&]() -> Value { auto fn9559 = Attribute(([&]() -> Value { auto fn9561 = PrepareDictionaryGet(s->LocalAt(10)); Arguments args9562; args9562.positional.reserve(2); args9562.Add(Value("workers"), false); args9562.Add(([&]() -> Value { auto dict9563 = Dict(); return dict9563; }()), false); return CallDictionaryGet(c, fn9561, std::move(args9562)); }()), "items"); Arguments args9560; return Call(c, fn9559, std::move(args9560)); }()))) {
auto unpack9564 = Iterate(item9558);
ValidateUnpack(unpack9564, 2, false);
s->SetAt(1, unpack9564.at(0));
s->SetAt(17, unpack9564.at(1));
if (static_cast<bool>(([&]() -> Value { auto v9565 = Unary("Not", ([&]() -> Value { auto fn9566 = s->Global("isinstance"); Arguments args9567; args9567.positional.reserve(2); args9567.Add(s->LocalAt(17), false); args9567.Add(s->Global("dict"), false); return Call(c, fn9566, std::move(args9567)); }())); if (static_cast<bool>(v9565)) return v9565; v9565 = Unary("Not", ([&]() -> Value { auto fn9568 = PrepareDictionaryGet(s->LocalAt(17)); Arguments args9569; args9569.Add(Value("needs_fertilizer"), false); return CallDictionaryGet(c, fn9568, std::move(args9569)); }())); if (static_cast<bool>(v9565)) return v9565; v9565 = ([&]() -> Value { auto fn9570 = PrepareDictionaryGet(s->LocalAt(17)); Arguments args9571; args9571.Add(Value("loaded"), false); return CallDictionaryGet(c, fn9570, std::move(args9571)); }()); return v9565; }()))) {
continue;
}
auto v9572 = ([&]() -> Value { auto fn9573 = PrepareDictionaryGet(s->LocalAt(17)); Arguments args9574; args9574.positional.reserve(2); args9574.Add(Value("fertilizer_quantity"), false); args9574.Add((static_cast<bool>(([&]() -> Value { auto v9575 = ([&]() -> Value { auto fn9577 = PrepareDictionaryGet(s->LocalAt(17)); Arguments args9578; args9578.Add(Value("kind"), false); return CallDictionaryGet(c, fn9577, std::move(args9578)); }()); Value v9576; v9576 = Value("fertilizer"); if (!static_cast<bool>(Binary("Eq", v9575, v9576))) return Value(false); v9575 = v9576; return Value(true); }())) ? Value(int64_t{10}) : Value(int64_t{5})), false); return CallDictionaryGet(c, fn9573, std::move(args9574)); }());
s->SetAt(5, v9572);
auto v9579 = ([&]() -> Value { auto fn9580 = PrepareDictionaryGet(Get(Get(Get(s->LocalAt(9), Value("private")), Value("inventories")), s->LocalAt(1))); Arguments args9581; args9581.positional.reserve(2); args9581.Add(Value("FERTILIZER"), false); args9581.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn9580, std::move(args9581)); }());
s->SetAt(3, v9579);
auto v9582 = s->LocalAt(4);
s->SetAt(4, Inplace("Add", v9582, ([&]() -> Value { auto fn9583 = s->Global("max"); Arguments args9584; args9584.positional.reserve(2); args9584.Add(Value(int64_t{0}), false); args9584.Add(([&]() -> Value { auto v9585 = s->LocalAt(5); return Binary("Sub", v9585, s->LocalAt(3)); }()), false); return Call(c, fn9583, std::move(args9584)); }())));
}
auto v9586 = ([&]() -> Value { auto v9587 = ([&]() -> Value { auto fn9588 = PrepareDictionaryGet(s->LocalAt(10)); Arguments args9589; args9589.Add(Value("pending"), false); return CallDictionaryGet(c, fn9588, std::move(args9589)); }()); if (static_cast<bool>(v9587)) return v9587; v9587 = ([&]() -> Value { auto dict9590 = Dict(); return dict9590; }()); return v9587; }());
s->SetAt(11, v9586);
if (static_cast<bool>(([&]() -> Value { auto fn9591 = PrepareDictionaryGet(s->LocalAt(11)); Arguments args9592; args9592.Add(Value("fertilizer"), false); return CallDictionaryGet(c, fn9591, std::move(args9592)); }()))) {
auto v9593 = s->LocalAt(4);
s->SetAt(4, Inplace("Add", v9593, Value(int64_t{10})));
}
}
auto v9594 = ([&]() -> Value { auto fn9595 = PrepareDictionaryGet(s->Global("_R51_INPUT_STATES")); Arguments args9596; args9596.positional.reserve(2); args9596.Add(s->LocalAt(14), false); args9596.Add(([&]() -> Value { auto dict9597 = Dict(); return dict9597; }()), false); return CallDictionaryGet(c, fn9595, std::move(args9596)); }());
s->SetAt(6, v9594);
for (const auto& item9598 : Iterate(([&]() -> Value { auto fn9599 = Attribute(([&]() -> Value { auto dict9601 = Dict(); Merge(dict9601, ([&]() -> Value { auto fn9602 = PrepareDictionaryGet(s->LocalAt(6)); Arguments args9603; args9603.positional.reserve(2); args9603.Add(Value("workers"), false); args9603.Add(([&]() -> Value { auto dict9604 = Dict(); return dict9604; }()), false); return CallDictionaryGet(c, fn9602, std::move(args9603)); }())); Merge(dict9601, ([&]() -> Value { auto v9605 = ([&]() -> Value { auto fn9606 = PrepareDictionaryGet(s->LocalAt(6)); Arguments args9607; args9607.Add(Value("pending"), false); return CallDictionaryGet(c, fn9606, std::move(args9607)); }()); if (static_cast<bool>(v9605)) return v9605; v9605 = ([&]() -> Value { auto dict9608 = Dict(); return dict9608; }()); return v9605; }())); return dict9601; }()), "items"); Arguments args9600; return Call(c, fn9599, std::move(args9600)); }()))) {
auto unpack9609 = Iterate(item9598);
ValidateUnpack(unpack9609, 2, false);
s->SetAt(1, unpack9609.at(0));
s->SetAt(13, unpack9609.at(1));
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto fn9610 = PrepareDictionaryGet(s->LocalAt(13)); Arguments args9611; args9611.Add(Value("loaded"), false); return CallDictionaryGet(c, fn9610, std::move(args9611)); }())))) {
auto v9612 = s->LocalAt(4);
s->SetAt(4, Inplace("Add", v9612, ([&]() -> Value { auto fn9613 = s->Global("max"); Arguments args9614; args9614.positional.reserve(2); args9614.Add(Value(int64_t{0}), false); args9614.Add(([&]() -> Value { auto fn9615 = s->Global("int"); Arguments args9616; args9616.Add(Get(s->LocalAt(13), Value("quantity")), false); return Call(c, fn9615, std::move(args9616)); }()), false); return Call(c, fn9613, std::move(args9614)); }())));
}
}
return ([&]() -> Value { auto fn9617 = s->Global("max"); Arguments args9618; args9618.positional.reserve(2); args9618.Add(Value(int64_t{14}), false); args9618.Add(([&]() -> Value { auto v9619 = Get(Get(s->LocalAt(2), s->LocalAt(18)), ([&]() -> Value { auto fn9620 = s->Global("min"); Arguments args9621; args9621.positional.reserve(2); args9621.Add(Value(int64_t{719}), false); args9621.Add(([&]() -> Value { auto v9622 = s->LocalAt(20); return Binary("Add", v9622, Value(int64_t{1})); }()), false); return Call(c, fn9620, std::move(args9621)); }())); return Binary("Add", v9619, s->LocalAt(4)); }()), false); return Call(c, fn9617, std::move(args9618)); }());
return {};
}
}  // namespace kagg::opponents::compiled
