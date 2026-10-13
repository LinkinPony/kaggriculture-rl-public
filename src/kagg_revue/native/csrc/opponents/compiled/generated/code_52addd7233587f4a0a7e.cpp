// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_52addd7233587f4a0a7e(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "budget", "changed", "count", "crop_workers", "day", "deadline", "expected", "extra", "farm", "fertilizer", "fertilizer_quantity", "labor", "latest_hire", "native", "obs", "offset", "order", "parent_hires", "planned", "private", "remaining", "state", "step"};
s->PrepareSlots(s_names);
auto v4469 = ([&]() -> Value { auto fn4470 = s->Global("int"); Arguments args4471; args4471.Add(Get(s->LocalAt(15), Value("step")), false); return Call(c, fn4470, std::move(args4471)); }());
s->SetAt(23, v4469);
auto v4472 = ([&]() -> Value { auto v4473 = s->LocalAt(23); return Binary("FloorDiv", v4473, Value(int64_t{24})); }());
s->SetAt(5, v4472);
auto v4474 = ([&]() -> Value { auto v4475 = s->LocalAt(23); return Binary("Mod", v4475, Value(int64_t{24})); }());
s->SetAt(16, v4474);
auto v4476 = Get(Get(s->LocalAt(15), Value("farms")), Get(s->LocalAt(15), Value("player")));
s->SetAt(9, v4476);
auto v4477 = Get(s->LocalAt(15), Value("private"));
s->SetAt(20, v4477);
if (static_cast<bool>(([&]() -> Value { auto v4478 = Unary("Not", ([&]() -> Value { auto fn4479 = PrepareDictionaryGet(s->LocalAt(22)); Arguments args4480; args4480.Add(Value("committed"), false); return CallDictionaryGet(c, fn4479, std::move(args4480)); }())); if (!static_cast<bool>(v4478)) return v4478; v4478 = ([&]() -> Value { auto v4481 = s->LocalAt(5); Value v4482; v4482 = Value(int64_t{18}); if (!static_cast<bool>(Binary("NotEq", v4481, v4482))) return Value(false); v4481 = v4482; return Value(true); }()); return v4478; }()))) {
return s->LocalAt(0);
}
if (static_cast<bool>(([&]() -> Value { auto v4483 = ([&]() -> Value { auto fn4485 = PrepareDictionaryGet(s->LocalAt(22)); Arguments args4486; args4486.Add(Value("requested_day"), false); return CallDictionaryGet(c, fn4485, std::move(args4486)); }()); Value v4484; v4484 = s->LocalAt(5); if (!static_cast<bool>(Binary("Eq", v4483, v4484))) return Value(false); v4483 = v4484; return Value(true); }()))) {
return s->LocalAt(0);
}
auto v4487 = ([&]() -> Value { auto fn4488 = s->Global("_v219_native_day"); Arguments args4489; args4489.positional.reserve(2); args4489.Add(s->LocalAt(14), false); args4489.Add(s->LocalAt(5), false); return Call(c, fn4488, std::move(args4489)); }());
s->SetAt(19, v4487);
auto v4490 = ([&]() -> Value { auto fn4491 = s->Global("max"); Arguments args4492; args4492.Add(([&]() -> Value { auto comp4493 = std::make_shared<Scope>(); comp4493->globals = s->globals; comp4493->parent = s; static constexpr const char* comp4493_names[] = {"a", "i"}; comp4493->PrepareSlots(comp4493_names); auto result4494 = List(); for (const auto& item4495 : Iterate(([&]() -> Value { auto fn4496 = s->Global("enumerate"); Arguments args4497; args4497.Add(s->LocalAt(19), false); return Call(c, fn4496, std::move(args4497)); }()))) { auto unpack4498 = Iterate(item4495); ValidateUnpack(unpack4498, 2, false); comp4493->SetAt(1, unpack4498.at(0)); comp4493->SetAt(0, unpack4498.at(1)); if (!static_cast<bool>(([&]() -> Value { auto comp4499 = std::make_shared<Scope>(); comp4499->globals = comp4493->globals; comp4499->parent = comp4493; static constexpr const char* comp4499_names[] = {"o"}; comp4499->PrepareSlots(comp4499_names); auto result4500 = List(); for (const auto& item4501 : Iterate(([&]() -> Value { auto fn4502 = PrepareDictionaryGet(comp4493->LocalAt(0)); Arguments args4503; args4503.positional.reserve(2); args4503.Add(Value("market"), false); args4503.Add(List({}), false); return CallDictionaryGet(c, fn4502, std::move(args4503)); }()))) { comp4499->SetAt(0, item4501); if (static_cast<bool>(([&]() -> Value { auto v4504 = comp4499->LocalAt(0); if (!static_cast<bool>(v4504)) return v4504; v4504 = ([&]() -> Value { auto v4505 = Get(comp4499->LocalAt(0), Value(int64_t{0})); Value v4506; v4506 = Value("HIRE"); if (!static_cast<bool>(Binary("Eq", v4505, v4506))) return Value(false); v4505 = v4506; return Value(true); }()); return v4504; }()))) return Value(true); } return Value(false); }()))) continue; result4494.node()->sequence.push_back(comp4493->LocalAt(1)); } return result4494; }()), false); args4492.Keyword("default", Unary("USub", Value(int64_t{1}))); return Call(c, fn4491, std::move(args4492)); }());
s->SetAt(13, v4490);
auto v4507 = (static_cast<bool>(([&]() -> Value { auto v4508 = ([&]() -> Value { auto fn4509 = PrepareDictionaryGet(s->LocalAt(22)); Arguments args4510; args4510.Add(Value("committed"), false); return CallDictionaryGet(c, fn4509, std::move(args4510)); }()); if (!static_cast<bool>(v4508)) return v4508; v4508 = ([&]() -> Value { auto v4511 = Value(int64_t{3}); Value v4512; v4512 = s->LocalAt(13); if (!static_cast<bool>(Binary("Lt", v4511, v4512))) return Value(false); v4511 = v4512; v4512 = Value(int64_t{6}); if (!static_cast<bool>(Binary("LtE", v4511, v4512))) return Value(false); v4511 = v4512; return Value(true); }()); return v4508; }())) ? Value(int64_t{6}) : Value(int64_t{3}));
s->SetAt(6, v4507);
if (static_cast<bool>(([&]() -> Value { auto v4513 = s->LocalAt(16); Value v4514; v4514 = s->LocalAt(6); if (!static_cast<bool>(Binary("Gt", v4513, v4514))) return Value(false); v4513 = v4514; return Value(true); }()))) {
return s->LocalAt(0);
}
auto v4515 = Slice(s->LocalAt(19), ([&]() -> Value { auto v4516 = s->LocalAt(16); return Binary("Add", v4516, Value(int64_t{1})); }()), Value{}, Value{});
s->SetAt(21, v4515);
if (static_cast<bool>(([&]() -> Value { auto comp4517 = std::make_shared<Scope>(); comp4517->globals = s->globals; comp4517->parent = s; static constexpr const char* comp4517_names[] = {"a", "o"}; comp4517->PrepareSlots(comp4517_names); auto result4518 = List(); for (const auto& item4519 : Iterate(s->LocalAt(21))) { comp4517->SetAt(0, item4519); for (const auto& item4520 : Iterate(([&]() -> Value { auto fn4521 = PrepareDictionaryGet(comp4517->LocalAt(0)); Arguments args4522; args4522.positional.reserve(2); args4522.Add(Value("market"), false); args4522.Add(List({}), false); return CallDictionaryGet(c, fn4521, std::move(args4522)); }()))) { comp4517->SetAt(1, item4520); if (static_cast<bool>(([&]() -> Value { auto v4523 = comp4517->LocalAt(1); if (!static_cast<bool>(v4523)) return v4523; v4523 = ([&]() -> Value { auto v4524 = Get(comp4517->LocalAt(1), Value(int64_t{0})); Value v4525; v4525 = Value("HIRE"); if (!static_cast<bool>(Binary("Eq", v4524, v4525))) return Value(false); v4524 = v4525; return Value(true); }()); return v4523; }()))) return Value(true); } } return Value(false); }()))) {
return s->LocalAt(0);
}
auto v4526 = ([&]() -> Value { auto fn4527 = s->Global("sum"); Arguments args4528; args4528.Add(([&]() -> Value { auto comp4529 = std::make_shared<Scope>(); comp4529->globals = s->globals; comp4529->parent = s; static constexpr const char* comp4529_names[] = {"o"}; comp4529->PrepareSlots(comp4529_names); auto result4530 = List(); for (const auto& item4531 : Iterate(Get(s->LocalAt(0), Value("market")))) { comp4529->SetAt(0, item4531); result4530.node()->sequence.push_back(([&]() -> Value { auto v4532 = ([&]() -> Value { auto fn4533 = comp4529->Global("bool"); Arguments args4534; args4534.Add(comp4529->LocalAt(0), false); return Call(c, fn4533, std::move(args4534)); }()); if (!static_cast<bool>(v4532)) return v4532; v4532 = ([&]() -> Value { auto v4535 = Get(comp4529->LocalAt(0), Value(int64_t{0})); Value v4536; v4536 = Value("HIRE"); if (!static_cast<bool>(Binary("Eq", v4535, v4536))) return Value(false); v4535 = v4536; return Value(true); }()); return v4532; }())); } return result4530; }()), false); return Call(c, fn4527, std::move(args4528)); }());
s->SetAt(18, v4526);
auto v4537 = ([&]() -> Value { auto fn4538 = s->Global("max"); Arguments args4539; args4539.Add(([&]() -> Value { auto comp4540 = std::make_shared<Scope>(); comp4540->globals = s->globals; comp4540->parent = s; static constexpr const char* comp4540_names[] = {"a"}; comp4540->PrepareSlots(comp4540_names); auto result4541 = List(); for (const auto& item4542 : Iterate(s->LocalAt(19))) { comp4540->SetAt(0, item4542); result4541.node()->sequence.push_back(([&]() -> Value { auto fn4543 = comp4540->Global("len"); Arguments args4544; args4544.Add(([&]() -> Value { auto fn4545 = PrepareDictionaryGet(comp4540->LocalAt(0)); Arguments args4546; args4546.positional.reserve(2); args4546.Add(Value("hands"), false); args4546.Add(List({}), false); return CallDictionaryGet(c, fn4545, std::move(args4546)); }()), false); return Call(c, fn4543, std::move(args4544)); }())); } return result4541; }()), false); return Call(c, fn4538, std::move(args4539)); }());
s->SetAt(7, v4537);
if (static_cast<bool>(([&]() -> Value { auto v4547 = ([&]() -> Value { auto v4549 = ([&]() -> Value { auto fn4550 = s->Global("len"); Arguments args4551; args4551.Add(Get(s->LocalAt(9), Value("hands")), false); return Call(c, fn4550, std::move(args4551)); }()); return Binary("Add", v4549, s->LocalAt(18)); }()); Value v4548; v4548 = s->LocalAt(7); if (!static_cast<bool>(Binary("NotEq", v4547, v4548))) return Value(false); v4547 = v4548; return Value(true); }()))) {
return s->LocalAt(0);
}
auto v4552 = ([&]() -> Value { auto fn4553 = s->Global("bool"); Arguments args4554; args4554.Add(([&]() -> Value { auto v4555 = s->Global("_V219_FERTILIZE"); if (!static_cast<bool>(v4555)) return v4555; v4555 = ([&]() -> Value { auto v4556 = s->LocalAt(5); Value v4557; v4557 = Tuple({Value(int64_t{24}), Value(int64_t{27})}); if (!static_cast<bool>(Binary("In", v4556, v4557))) return Value(false); v4556 = v4557; return Value(true); }()); if (!static_cast<bool>(v4555)) return v4555; v4555 = ([&]() -> Value { auto fn4558 = s->Global("_r79_tomato_fertilizer_worthwhile"); Arguments args4559; args4559.positional.reserve(2); args4559.Add(s->LocalAt(15), false); args4559.Add(s->LocalAt(0), false); return Call(c, fn4558, std::move(args4559)); }()); return v4555; }()), false); return Call(c, fn4553, std::move(args4554)); }());
s->SetAt(10, v4552);
auto v4560 = (static_cast<bool>(([&]() -> Value { auto v4561 = ([&]() -> Value { auto v4562 = s->LocalAt(5); Value v4563; v4563 = Tuple({Value(int64_t{19}), Value(int64_t{20}), Value(int64_t{21}), Value(int64_t{22}), Value(int64_t{23}), Value(int64_t{25})}); if (!static_cast<bool>(Binary("In", v4562, v4563))) return Value(false); v4562 = v4563; return Value(true); }()); if (!static_cast<bool>(v4561)) return v4561; v4561 = ([&]() -> Value { auto v4564 = s->LocalAt(16); Value v4565; v4565 = Value(int64_t{2}); if (!static_cast<bool>(Binary("LtE", v4564, v4565))) return Value(false); v4564 = v4565; return Value(true); }()); return v4561; }())) ? Value(int64_t{1}) : (static_cast<bool>(([&]() -> Value { auto v4566 = Value(int64_t{26}); Value v4567; v4567 = s->LocalAt(5); if (!static_cast<bool>(Binary("LtE", v4566, v4567))) return Value(false); v4566 = v4567; v4567 = Value(int64_t{28}); if (!static_cast<bool>(Binary("LtE", v4566, v4567))) return Value(false); v4566 = v4567; return Value(true); }())) ? Value(int64_t{3}) : Value(int64_t{2})));
s->SetAt(4, v4560);
auto v4568 = ([&]() -> Value { auto fn4569 = s->Global("_r53_labor_assignment"); Arguments args4570; args4570.positional.reserve(3); args4570.Add(s->LocalAt(15), false); args4570.Add(s->LocalAt(0), false); args4570.Add(s->LocalAt(10), false); return Call(c, fn4569, std::move(args4570)); }());
s->SetAt(12, v4568);
if (static_cast<bool>(([&]() -> Value { auto v4571 = s->LocalAt(12); Value v4572; v4572 = Value{}; if (!static_cast<bool>(Binary("IsNot", v4571, v4572))) return Value(false); v4571 = v4572; return Value(true); }()))) {
auto v4573 = Get(s->LocalAt(12), Value("workers"));
s->SetAt(4, v4573);
}
auto v4574 = ([&]() -> Value { auto v4575 = s->LocalAt(4); return Binary("Add", v4575, ([&]() -> Value { auto fn4576 = s->Global("int"); Arguments args4577; args4577.Add(([&]() -> Value { auto v4578 = s->LocalAt(10); if (!static_cast<bool>(v4578)) return v4578; v4578 = ([&]() -> Value { auto v4579 = s->LocalAt(5); Value v4580; v4580 = Value(int64_t{27}); if (!static_cast<bool>(Binary("Eq", v4579, v4580))) return Value(false); v4579 = v4580; return Value(true); }()); if (!static_cast<bool>(v4578)) return v4578; v4578 = ([&]() -> Value { auto v4581 = s->LocalAt(12); Value v4582; v4582 = Value{}; if (!static_cast<bool>(Binary("Is", v4581, v4582))) return Value(false); v4581 = v4582; return Value(true); }()); return v4578; }()), false); return Call(c, fn4576, std::move(args4577)); }())); }());
s->SetAt(3, v4574);
auto v4583 = List({});
s->SetAt(8, v4583);
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto fn4584 = PrepareDictionaryGet(s->LocalAt(22)); Arguments args4585; args4585.Add(Value("committed"), false); return CallDictionaryGet(c, fn4584, std::move(args4585)); }())))) {
auto v4586 = s->LocalAt(8);
s->SetAt(8, Inplace("Add", v4586, List({List({Value("BUY_LAND")}), List({Value("BUY_SEED"), Value("TOMATO"), Value(int64_t{10})})})));
}
auto v4587 = (static_cast<bool>(s->LocalAt(10)) ? ([&]() -> Value { auto fn4588 = s->Global("_r70_parent_fert_qty"); Arguments args4589; args4589.positional.reserve(4); args4589.Add(s->LocalAt(15), false); args4589.Add(s->LocalAt(0), false); args4589.Add(s->LocalAt(19), false); args4589.Add(s->LocalAt(16), false); return Call(c, fn4588, std::move(args4589)); }()) : Value(int64_t{0}));
s->SetAt(11, v4587);
if (static_cast<bool>(s->LocalAt(10))) {
(void)([&]() -> Value { auto fn4590 = Attribute(s->LocalAt(8), "append"); Arguments args4591; args4591.Add(List({Value("BUY_PRODUCT"), Value("FERTILIZER"), s->LocalAt(11)}), false); return Call(c, fn4590, std::move(args4591)); }());
}
auto v4592 = s->LocalAt(8);
s->SetAt(8, Inplace("Add", v4592, ([&]() -> Value { auto comp4593 = std::make_shared<Scope>(); comp4593->globals = s->globals; comp4593->parent = s; static constexpr const char* comp4593_names[] = {"_"}; comp4593->PrepareSlots(comp4593_names); auto result4594 = List(); for (const auto& item4595 : Iterate(([&]() -> Value { auto fn4596 = s->Global("range"); Arguments args4597; args4597.Add(s->LocalAt(3), false); return Call(c, fn4596, std::move(args4597)); }()))) { comp4593->SetAt(0, item4595); result4594.node()->sequence.push_back(List({Value("HIRE")})); } return result4594; }())));
if (static_cast<bool>(([&]() -> Value { auto v4598 = ([&]() -> Value { auto v4600 = ([&]() -> Value { auto fn4601 = s->Global("len"); Arguments args4602; args4602.Add(Get(s->LocalAt(0), Value("market")), false); return Call(c, fn4601, std::move(args4602)); }()); return Binary("Add", v4600, ([&]() -> Value { auto fn4603 = s->Global("len"); Arguments args4604; args4604.Add(s->LocalAt(8), false); return Call(c, fn4603, std::move(args4604)); }())); }()); Value v4599; v4599 = s->Global("MAX_ORDERS"); if (!static_cast<bool>(Binary("Gt", v4598, v4599))) return Value(false); v4598 = v4599; return Value(true); }()))) {
return s->LocalAt(0);
}
auto v4605 = ([&]() -> Value { auto fn4606 = s->Global("sum"); Arguments args4607; args4607.Add(([&]() -> Value { auto comp4608 = std::make_shared<Scope>(); comp4608->globals = s->globals; comp4608->parent = s; static constexpr const char* comp4608_names[] = {"n"}; comp4608->PrepareSlots(comp4608_names); auto result4609 = List(); for (const auto& item4610 : Iterate(([&]() -> Value { auto fn4611 = s->Global("range"); Arguments args4612; args4612.positional.reserve(2); args4612.Add(Get(s->LocalAt(9), Value("hires_today")), false); args4612.Add(([&]() -> Value { auto v4613 = ([&]() -> Value { auto v4614 = Get(s->LocalAt(9), Value("hires_today")); return Binary("Add", v4614, s->LocalAt(18)); }()); return Binary("Add", v4613, s->LocalAt(3)); }()), false); return Call(c, fn4611, std::move(args4612)); }()))) { comp4608->SetAt(0, item4610); result4609.node()->sequence.push_back(([&]() -> Value { auto fn4615 = comp4608->Global("_v219_fib"); Arguments args4616; args4616.Add(comp4608->LocalAt(0), false); return Call(c, fn4615, std::move(args4616)); }())); } return result4609; }()), false); return Call(c, fn4606, std::move(args4607)); }());
s->SetAt(1, v4605);
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto fn4617 = PrepareDictionaryGet(s->LocalAt(22)); Arguments args4618; args4618.Add(Value("committed"), false); return CallDictionaryGet(c, fn4617, std::move(args4618)); }())))) {
auto v4619 = s->LocalAt(1);
s->SetAt(1, Inplace("Add", v4619, Value(int64_t{4500})));
}
if (static_cast<bool>(s->LocalAt(10))) {
auto v4620 = s->LocalAt(1);
s->SetAt(1, Inplace("Add", v4620, ([&]() -> Value { auto v4621 = s->LocalAt(11); return Binary("Mult", v4621, ([&]() -> Value { auto v4622 = Get(Get(Get(s->LocalAt(15), Value("market")), Value("prices")), Value("FERTILIZER")); return Binary("Add", v4622, Value(int64_t{5})); }())); }())));
}
for (const auto& item4623 : Iterate(Get(s->LocalAt(0), Value("market")))) {
s->SetAt(17, item4623);
if (static_cast<bool>(Unary("Not", s->LocalAt(17)))) {
continue;
}
if (static_cast<bool>(([&]() -> Value { auto v4624 = Get(s->LocalAt(17), Value(int64_t{0})); Value v4625; v4625 = Value("BUY_PRODUCT"); if (!static_cast<bool>(Binary("Eq", v4624, v4625))) return Value(false); v4624 = v4625; return Value(true); }()))) {
auto v4626 = s->LocalAt(1);
s->SetAt(1, Inplace("Add", v4626, ([&]() -> Value { auto v4627 = ([&]() -> Value { auto fn4628 = s->Global("int"); Arguments args4629; args4629.Add(Get(s->LocalAt(17), Value(int64_t{2})), false); return Call(c, fn4628, std::move(args4629)); }()); return Binary("Mult", v4627, ([&]() -> Value { auto v4630 = ([&]() -> Value { auto fn4631 = s->Global("int"); Arguments args4632; args4632.Add(Get(Get(Get(s->LocalAt(15), Value("market")), Value("prices")), Get(s->LocalAt(17), Value(int64_t{1}))), false); return Call(c, fn4631, std::move(args4632)); }()); return Binary("Add", v4630, Value(int64_t{10})); }())); }())));
}
else {
if (static_cast<bool>(([&]() -> Value { auto v4633 = Get(s->LocalAt(17), Value(int64_t{0})); Value v4634; v4634 = Value("BUY_ANIMAL"); if (!static_cast<bool>(Binary("Eq", v4633, v4634))) return Value(false); v4633 = v4634; return Value(true); }()))) {
auto v4635 = s->LocalAt(1);
s->SetAt(1, Inplace("Add", v4635, ([&]() -> Value { auto v4636 = ([&]() -> Value { auto fn4637 = s->Global("int"); Arguments args4638; args4638.Add(Get(s->LocalAt(17), Value(int64_t{2})), false); return Call(c, fn4637, std::move(args4638)); }()); return Binary("Mult", v4636, Get(([&]() -> Value { auto dict4639 = Dict(); auto key4640 = Value("COW"); Put(dict4639, key4640, Value(int64_t{400})); auto key4641 = Value("SHEEP"); Put(dict4639, key4641, Value(int64_t{500})); auto key4642 = Value("GOOSE"); Put(dict4639, key4642, Value(int64_t{300})); return dict4639; }()), Get(s->LocalAt(17), Value(int64_t{1})))); }())));
}
else {
if (static_cast<bool>(([&]() -> Value { auto v4643 = Get(s->LocalAt(17), Value(int64_t{0})); Value v4644; v4644 = Value("BUY_SEED"); if (!static_cast<bool>(Binary("Eq", v4643, v4644))) return Value(false); v4643 = v4644; return Value(true); }()))) {
auto v4645 = s->LocalAt(1);
s->SetAt(1, Inplace("Add", v4645, ([&]() -> Value { auto v4646 = ([&]() -> Value { auto fn4647 = s->Global("int"); Arguments args4648; args4648.Add(Get(s->LocalAt(17), Value(int64_t{2})), false); return Call(c, fn4647, std::move(args4648)); }()); return Binary("Mult", v4646, Get(([&]() -> Value { auto dict4649 = Dict(); auto key4650 = Value("WHEAT"); Put(dict4649, key4650, Value(int64_t{10})); auto key4651 = Value("CARROT"); Put(dict4649, key4651, Value(int64_t{20})); auto key4652 = Value("TOMATO"); Put(dict4649, key4652, Value(int64_t{50})); auto key4653 = Value("STRAWBERRY"); Put(dict4649, key4653, Value(int64_t{100})); auto key4654 = Value("MELON"); Put(dict4649, key4654, Value(int64_t{80})); return dict4649; }()), Get(s->LocalAt(17), Value(int64_t{1})))); }())));
}
}
}
}
if (static_cast<bool>(([&]() -> Value { auto v4655 = Get(s->LocalAt(9), Value("money")); Value v4656; v4656 = ([&]() -> Value { auto v4657 = s->LocalAt(1); return Binary("Add", v4657, Value(int64_t{3000})); }()); if (!static_cast<bool>(Binary("Lt", v4655, v4656))) return Value(false); v4655 = v4656; return Value(true); }()))) {
auto v4658 = s->Global("_V219_REPORT");
auto v4659 = Value("budget_declines");
auto v4660 = Get(v4658, v4659);
Put(v4658, v4659, Inplace("Add", v4660, Value(int64_t{1})));
return s->LocalAt(0);
}
auto v4661 = ([&]() -> Value { auto dict4662 = Dict(); auto key4663 = Value("step"); Put(dict4662, key4663, s->LocalAt(23)); auto key4664 = Value("first_actor"); Put(dict4662, key4664, ([&]() -> Value { auto v4665 = s->LocalAt(7); return Binary("Add", v4665, Value(int64_t{1})); }())); auto key4666 = Value("count"); Put(dict4662, key4666, s->LocalAt(3)); auto key4667 = Value("crop_workers"); Put(dict4662, key4667, s->LocalAt(4)); auto key4668 = Value("fertilizer"); Put(dict4662, key4668, s->LocalAt(10)); auto key4669 = Value("labor"); Put(dict4662, key4669, s->LocalAt(12)); return dict4662; }());
Put(s->LocalAt(22), Value("pending"), v4661);
if (static_cast<bool>(([&]() -> Value { auto v4670 = s->LocalAt(12); Value v4671; v4671 = Value{}; if (!static_cast<bool>(Binary("IsNot", v4670, v4671))) return Value(false); v4670 = v4671; return Value(true); }()))) {
auto v4672 = s->Global("_R53_LABOR_REPORT");
auto v4673 = Value("labor_requests");
auto v4674 = Get(v4672, v4673);
Put(v4672, v4673, Inplace("Add", v4674, Value(int64_t{1})));
auto v4675 = s->Global("_R53_LABOR_REPORT");
auto v4676 = Value("labor_hires_avoided");
auto v4677 = Get(v4675, v4676);
Put(v4675, v4676, Inplace("Add", v4677, Value(int64_t{1})));
auto v4678 = s->Global("_R53_LABOR_REPORT");
auto v4679 = ([&]() -> Value { auto v4681 = Value("labor_day"); return Binary("Add", v4681, ([&]() -> Value { auto fn4682 = s->Global("str"); Arguments args4683; args4683.Add(s->LocalAt(5), false); return Call(c, fn4682, std::move(args4683)); }())); }());
auto v4680 = Get(v4678, v4679);
Put(v4678, v4679, Inplace("Add", v4680, Value(int64_t{1})));
}
auto v4684 = s->LocalAt(5);
Put(s->LocalAt(22), Value("requested_day"), v4684);
auto v4685 = s->Global("_V219_REPORT");
auto v4686 = Value("hire_requests");
auto v4687 = Get(v4685, v4686);
Put(v4685, v4686, Inplace("Add", v4687, s->LocalAt(3)));
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto fn4688 = PrepareDictionaryGet(s->LocalAt(22)); Arguments args4689; args4689.Add(Value("committed"), false); return CallDictionaryGet(c, fn4688, std::move(args4689)); }())))) {
auto v4690 = Value(true);
Put(s->LocalAt(22), Value("committed"), v4690);
auto v4691 = s->Global("_V219_REPORT");
auto v4692 = Value("commitments");
auto v4693 = Get(v4691, v4692);
Put(v4691, v4692, Inplace("Add", v4693, Value(int64_t{1})));
}
auto v4694 = ([&]() -> Value { auto fn4695 = Attribute(s->Global("copy"), "deepcopy"); Arguments args4696; args4696.Add(s->LocalAt(0), false); return Call(c, fn4695, std::move(args4696)); }());
s->SetAt(2, v4694);
auto v4697 = s->LocalAt(2);
auto v4698 = Value("market");
auto v4699 = Get(v4697, v4698);
Put(v4697, v4698, Inplace("Add", v4699, s->LocalAt(8)));
return s->LocalAt(2);
return {};
}
}  // namespace kagg::opponents::compiled
