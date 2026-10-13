// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_e45ac1449597d4c9cf4d(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"_", "action", "effective", "i", "item", "j", "kept", "market", "new", "o", "obs", "order", "private", "q", "qty", "remaining", "removed"};
s->PrepareSlots(s_names);
auto v20422 = ([&]() -> Value { auto v20423 = ([&]() -> Value { auto fn20424 = PrepareDictionaryGet(s->LocalAt(1)); Arguments args20425; args20425.Add(Value("market"), false); return CallDictionaryGet(c, fn20424, std::move(args20425)); }()); if (static_cast<bool>(v20423)) return v20423; v20423 = List({}); return v20423; }());
s->SetAt(7, v20422);
if (static_cast<bool>(([&]() -> Value { auto v20426 = ([&]() -> Value { auto v20427 = ([&]() -> Value { auto fn20429 = s->Global("int"); Arguments args20430; args20430.Add(Get(s->LocalAt(10), Value("step")), false); return Call(c, fn20429, std::move(args20430)); }()); Value v20428; v20428 = Value(int64_t{144}); if (!static_cast<bool>(Binary("Lt", v20427, v20428))) return Value(false); v20427 = v20428; return Value(true); }()); if (static_cast<bool>(v20426)) return v20426; v20426 = ([&]() -> Value { auto v20431 = ([&]() -> Value { auto fn20433 = s->Global("len"); Arguments args20434; args20434.Add(s->LocalAt(7), false); return Call(c, fn20433, std::move(args20434)); }()); Value v20432; v20432 = Value(int64_t{2}); if (!static_cast<bool>(Binary("Lt", v20431, v20432))) return Value(false); v20431 = v20432; return Value(true); }()); return v20426; }()))) {
return s->LocalAt(1);
}
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto comp20435 = std::make_shared<Scope>(); comp20435->globals = s->globals; comp20435->parent = s; static constexpr const char* comp20435_names[] = {"o"}; comp20435->PrepareSlots(comp20435_names); auto result20436 = List(); for (const auto& item20437 : Iterate(s->LocalAt(7))) { comp20435->SetAt(0, item20437); if (!static_cast<bool>(([&]() -> Value { auto v20438 = ([&]() -> Value { auto v20439 = ([&]() -> Value { auto fn20441 = comp20435->Global("len"); Arguments args20442; args20442.Add(comp20435->LocalAt(0), false); return Call(c, fn20441, std::move(args20442)); }()); Value v20440; v20440 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v20439, v20440))) return Value(false); v20439 = v20440; return Value(true); }()); if (!static_cast<bool>(v20438)) return v20438; v20438 = ([&]() -> Value { auto v20443 = Get(comp20435->LocalAt(0), Value(int64_t{0})); Value v20444; v20444 = Value("SELL"); if (!static_cast<bool>(Binary("Eq", v20443, v20444))) return Value(false); v20443 = v20444; return Value(true); }()); return v20438; }()))) return Value(false); } return Value(true); }())))) {
return ([&]() -> Value { auto fn20445 = s->Global("_E335_ORIGINAL_COMPACT"); Arguments args20446; args20446.positional.reserve(2); args20446.Add(s->LocalAt(10), false); args20446.Add(s->LocalAt(1), false); return Call(c, fn20445, std::move(args20446)); }());
}
auto v20447 = ([&]() -> Value { auto fn20448 = s->Global("_r127_fields"); Arguments args20449; args20449.positional.reserve(2); args20449.Add(s->LocalAt(10), false); args20449.Add(s->LocalAt(1), false); return Call(c, fn20448, std::move(args20449)); }());
auto unpack20450 = Iterate(v20447);
ValidateUnpack(unpack20450, 2, false);
s->SetAt(0, unpack20450.at(0));
s->SetAt(12, unpack20450.at(1));
auto v20451 = ([&]() -> Value { auto fn20452 = s->Global("dict"); Arguments args20453; args20453.Add(Get(s->LocalAt(12), Value("shed")), false); return Call(c, fn20452, std::move(args20453)); }());
s->SetAt(15, v20451);
auto v20454 = List({});
s->SetAt(2, v20454);
for (const auto& item20455 : Iterate(s->LocalAt(7))) {
s->SetAt(9, item20455);
auto v20456 = Get(s->LocalAt(9), Value(int64_t{1}));
s->SetAt(4, v20456);
auto v20457 = ([&]() -> Value { auto fn20458 = s->Global("min"); Arguments args20459; args20459.positional.reserve(2); args20459.Add(([&]() -> Value { auto fn20460 = s->Global("max"); Arguments args20461; args20461.positional.reserve(2); args20461.Add(Value(int64_t{0}), false); args20461.Add(([&]() -> Value { auto fn20462 = s->Global("int"); Arguments args20463; args20463.Add(Get(s->LocalAt(9), Value(int64_t{2})), false); return Call(c, fn20462, std::move(args20463)); }()), false); return Call(c, fn20460, std::move(args20461)); }()), false); args20459.Add(([&]() -> Value { auto fn20464 = s->Global("max"); Arguments args20465; args20465.positional.reserve(2); args20465.Add(Value(int64_t{0}), false); args20465.Add(([&]() -> Value { auto fn20466 = s->Global("int"); Arguments args20467; args20467.Add(([&]() -> Value { auto fn20468 = PrepareDictionaryGet(s->LocalAt(15)); Arguments args20469; args20469.positional.reserve(2); args20469.Add(s->LocalAt(4), false); args20469.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn20468, std::move(args20469)); }()), false); return Call(c, fn20466, std::move(args20467)); }()), false); return Call(c, fn20464, std::move(args20465)); }()), false); return Call(c, fn20458, std::move(args20459)); }());
s->SetAt(13, v20457);
auto v20470 = ([&]() -> Value { auto fn20471 = s->Global("max"); Arguments args20472; args20472.positional.reserve(2); args20472.Add(Value(int64_t{0}), false); args20472.Add(([&]() -> Value { auto v20473 = ([&]() -> Value { auto fn20474 = s->Global("int"); Arguments args20475; args20475.Add(([&]() -> Value { auto fn20476 = PrepareDictionaryGet(s->LocalAt(15)); Arguments args20477; args20477.positional.reserve(2); args20477.Add(s->LocalAt(4), false); args20477.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn20476, std::move(args20477)); }()), false); return Call(c, fn20474, std::move(args20475)); }()); return Binary("Sub", v20473, s->LocalAt(13)); }()), false); return Call(c, fn20471, std::move(args20472)); }());
Put(s->LocalAt(15), s->LocalAt(4), v20470);
(void)([&]() -> Value { auto fn20478 = Attribute(s->LocalAt(2), "append"); Arguments args20479; args20479.Add((static_cast<bool>(s->LocalAt(13)) ? List({Value("SELL"), s->LocalAt(4), s->LocalAt(13)}) : List({})), false); return Call(c, fn20478, std::move(args20479)); }());
}
auto v20480 = ([&]() -> Value { auto comp20481 = std::make_shared<Scope>(); comp20481->globals = s->globals; comp20481->parent = s; static constexpr const char* comp20481_names[] = {"o"}; comp20481->PrepareSlots(comp20481_names); auto result20482 = List(); for (const auto& item20483 : Iterate(s->LocalAt(2))) { comp20481->SetAt(0, item20483); result20482.node()->sequence.push_back(([&]() -> Value { auto fn20484 = comp20481->Global("list"); Arguments args20485; args20485.Add(comp20481->LocalAt(0), false); return Call(c, fn20484, std::move(args20485)); }())); } return result20482; }());
s->SetAt(8, v20480);
auto v20486 = Value(int64_t{0});
s->SetAt(3, v20486);
auto v20487 = Value(int64_t{0});
s->SetAt(16, v20487);
while (static_cast<bool>(([&]() -> Value { auto v20488 = s->LocalAt(3); Value v20489; v20489 = ([&]() -> Value { auto fn20490 = s->Global("len"); Arguments args20491; args20491.Add(s->LocalAt(2), false); return Call(c, fn20490, std::move(args20491)); }()); if (!static_cast<bool>(Binary("Lt", v20488, v20489))) return Value(false); v20488 = v20489; return Value(true); }()))) {
if (static_cast<bool>(([&]() -> Value { auto v20492 = Get(s->LocalAt(2), s->LocalAt(3)); if (!static_cast<bool>(v20492)) return v20492; v20492 = ([&]() -> Value { auto v20493 = Get(Get(s->LocalAt(2), s->LocalAt(3)), Value(int64_t{1})); Value v20494; v20494 = s->Global("_E334_ITEMS"); if (!static_cast<bool>(Binary("NotIn", v20493, v20494))) return Value(false); v20493 = v20494; return Value(true); }()); return v20492; }()))) {
auto v20495 = s->LocalAt(3);
s->SetAt(3, Inplace("Add", v20495, Value(int64_t{1})));
continue;
}
auto v20496 = ([&]() -> Value { auto v20497 = s->LocalAt(3); return Binary("Add", v20497, Value(int64_t{1})); }());
s->SetAt(5, v20496);
while (static_cast<bool>(([&]() -> Value { auto v20498 = ([&]() -> Value { auto v20499 = s->LocalAt(5); Value v20500; v20500 = ([&]() -> Value { auto fn20501 = s->Global("len"); Arguments args20502; args20502.Add(s->LocalAt(2), false); return Call(c, fn20501, std::move(args20502)); }()); if (!static_cast<bool>(Binary("Lt", v20499, v20500))) return Value(false); v20499 = v20500; return Value(true); }()); if (!static_cast<bool>(v20498)) return v20498; v20498 = ([&]() -> Value { auto v20503 = Unary("Not", Get(s->LocalAt(2), s->LocalAt(5))); if (static_cast<bool>(v20503)) return v20503; v20503 = ([&]() -> Value { auto v20504 = Get(Get(s->LocalAt(2), s->LocalAt(5)), Value(int64_t{1})); Value v20505; v20505 = s->Global("_E334_ITEMS"); if (!static_cast<bool>(Binary("In", v20504, v20505))) return Value(false); v20504 = v20505; return Value(true); }()); return v20503; }()); return v20498; }()))) {
auto v20506 = s->LocalAt(5);
s->SetAt(5, Inplace("Add", v20506, Value(int64_t{1})));
}
auto v20507 = List({});
s->SetAt(11, v20507);
auto v20508 = ([&]() -> Value { auto dict20509 = Dict(); return dict20509; }());
s->SetAt(14, v20508);
for (const auto& item20510 : Iterate(Slice(s->LocalAt(2), s->LocalAt(3), s->LocalAt(5), Value{}))) {
s->SetAt(9, item20510);
if (static_cast<bool>(Unary("Not", s->LocalAt(9)))) {
continue;
}
if (static_cast<bool>(([&]() -> Value { auto v20511 = Get(s->LocalAt(9), Value(int64_t{1})); Value v20512; v20512 = s->LocalAt(14); if (!static_cast<bool>(Binary("NotIn", v20511, v20512))) return Value(false); v20511 = v20512; return Value(true); }()))) {
(void)([&]() -> Value { auto fn20513 = Attribute(s->LocalAt(11), "append"); Arguments args20514; args20514.Add(Get(s->LocalAt(9), Value(int64_t{1})), false); return Call(c, fn20513, std::move(args20514)); }());
auto v20515 = Value(int64_t{0});
Put(s->LocalAt(14), Get(s->LocalAt(9), Value(int64_t{1})), v20515);
}
auto v20516 = s->LocalAt(14);
auto v20517 = Get(s->LocalAt(9), Value(int64_t{1}));
auto v20518 = Get(v20516, v20517);
Put(v20516, v20517, Inplace("Add", v20518, Get(s->LocalAt(9), Value(int64_t{2}))));
}
auto v20519 = ([&]() -> Value { auto comp20520 = std::make_shared<Scope>(); comp20520->globals = s->globals; comp20520->parent = s; static constexpr const char* comp20520_names[] = {"item"}; comp20520->PrepareSlots(comp20520_names); auto result20521 = List(); for (const auto& item20522 : Iterate(s->LocalAt(11))) { comp20520->SetAt(0, item20522); result20521.node()->sequence.push_back(List({Value("SELL"), comp20520->LocalAt(0), Get(comp20520->Captured("qty"), comp20520->LocalAt(0))})); } return result20521; }());
s->SetAt(6, v20519);
auto v20523 = ([&]() -> Value { auto v20524 = s->LocalAt(6); return Binary("Add", v20524, ([&]() -> Value { auto comp20525 = std::make_shared<Scope>(); comp20525->globals = s->globals; comp20525->parent = s; static constexpr const char* comp20525_names[] = {"_"}; comp20525->PrepareSlots(comp20525_names); auto result20526 = List(); for (const auto& item20527 : Iterate(([&]() -> Value { auto fn20528 = s->Global("range"); Arguments args20529; args20529.Add(([&]() -> Value { auto v20530 = ([&]() -> Value { auto v20531 = s->LocalAt(5); return Binary("Sub", v20531, s->LocalAt(3)); }()); return Binary("Sub", v20530, ([&]() -> Value { auto fn20532 = s->Global("len"); Arguments args20533; args20533.Add(s->LocalAt(6), false); return Call(c, fn20532, std::move(args20533)); }())); }()), false); return Call(c, fn20528, std::move(args20529)); }()))) { comp20525->SetAt(0, item20527); result20526.node()->sequence.push_back(List({})); } return result20526; }())); }());
PutSlice(s->LocalAt(8), s->LocalAt(3), s->LocalAt(5), Value{}, v20523);
auto v20534 = s->LocalAt(16);
s->SetAt(16, Inplace("Add", v20534, ([&]() -> Value { auto v20535 = ([&]() -> Value { auto v20536 = s->LocalAt(5); return Binary("Sub", v20536, s->LocalAt(3)); }()); return Binary("Sub", v20535, ([&]() -> Value { auto fn20537 = s->Global("len"); Arguments args20538; args20538.Add(s->LocalAt(6), false); return Call(c, fn20537, std::move(args20538)); }())); }())));
auto v20539 = s->LocalAt(5);
s->SetAt(3, v20539);
}
if (static_cast<bool>(([&]() -> Value { auto v20540 = s->LocalAt(8); Value v20541; v20541 = s->LocalAt(7); if (!static_cast<bool>(Binary("Eq", v20540, v20541))) return Value(false); v20540 = v20541; return Value(true); }()))) {
return s->LocalAt(1);
}
auto v20542 = s->Global("_E334_REPORT");
auto v20543 = Value("changed");
auto v20544 = Get(v20542, v20543);
Put(v20542, v20543, Inplace("Add", v20544, Value(int64_t{1})));
auto v20545 = s->Global("_E334_REPORT");
auto v20546 = Value("removed");
auto v20547 = Get(v20545, v20546);
Put(v20545, v20546, Inplace("Add", v20547, s->LocalAt(16)));
return ([&]() -> Value { auto fn20548 = s->Global("dict"); Arguments args20549; args20549.Add(s->LocalAt(1), false); args20549.Keyword("market", s->LocalAt(8)); return Call(c, fn20548, std::move(args20549)); }());
return {};
}
}  // namespace kagg::opponents::compiled
