// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_5f56cceebed99cf3d61b(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "base", "best", "best_orders", "blk", "blocks", "cand", "i", "inv0", "j", "key", "margin", "market", "n", "o", "obs", "opp", "orders", "out", "params", "perm", "seen", "stock", "v", "view"};
s->PrepareSlots(s_names);
auto v19418 = ([&]() -> Value { auto v19419 = ([&]() -> Value { auto fn19420 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args19421; args19421.Add(Value("market"), false); return CallDictionaryGet(c, fn19420, std::move(args19421)); }()); if (static_cast<bool>(v19419)) return v19419; v19419 = List({}); return v19419; }());
s->SetAt(12, v19418);
if (static_cast<bool>(([&]() -> Value { auto v19422 = ([&]() -> Value { auto fn19424 = s->Global("len"); Arguments args19425; args19425.Add(s->LocalAt(12), false); return Call(c, fn19424, std::move(args19425)); }()); Value v19423; v19423 = Value(int64_t{2}); if (!static_cast<bool>(Binary("Lt", v19422, v19423))) return Value(false); v19422 = v19423; return Value(true); }()))) {
return s->LocalAt(0);
}
auto v19426 = ([&]() -> Value { auto comp19427 = std::make_shared<Scope>(); comp19427->globals = s->globals; comp19427->parent = s; static constexpr const char* comp19427_names[] = {"o"}; comp19427->PrepareSlots(comp19427_names); auto result19428 = List(); for (const auto& item19429 : Iterate(s->LocalAt(12))) { comp19427->SetAt(0, item19429); result19428.node()->sequence.push_back((static_cast<bool>(([&]() -> Value { auto fn19430 = comp19427->Global("isinstance"); Arguments args19431; args19431.positional.reserve(2); args19431.Add(comp19427->LocalAt(0), false); args19431.Add(Tuple({comp19427->Global("list"), comp19427->Global("tuple")}), false); return Call(c, fn19430, std::move(args19431)); }())) ? ([&]() -> Value { auto fn19432 = comp19427->Global("list"); Arguments args19433; args19433.Add(comp19427->LocalAt(0), false); return Call(c, fn19432, std::move(args19433)); }()) : comp19427->LocalAt(0))); } return result19428; }());
s->SetAt(17, v19426);
auto v19434 = List({});
s->SetAt(5, v19434);
auto v19435 = Value(int64_t{0});
s->SetAt(7, v19435);
while (static_cast<bool>(([&]() -> Value { auto v19436 = s->LocalAt(7); Value v19437; v19437 = ([&]() -> Value { auto fn19438 = s->Global("len"); Arguments args19439; args19439.Add(s->LocalAt(17), false); return Call(c, fn19438, std::move(args19439)); }()); if (!static_cast<bool>(Binary("Lt", v19436, v19437))) return Value(false); v19436 = v19437; return Value(true); }()))) {
auto v19440 = Get(s->LocalAt(17), s->LocalAt(7));
s->SetAt(14, v19440);
if (static_cast<bool>(([&]() -> Value { auto v19441 = s->LocalAt(14); if (!static_cast<bool>(v19441)) return v19441; v19441 = ([&]() -> Value { auto v19442 = Get(s->LocalAt(14), Value(int64_t{0})); Value v19443; v19443 = Value("SELL"); if (!static_cast<bool>(Binary("Eq", v19442, v19443))) return Value(false); v19442 = v19443; return Value(true); }()); return v19441; }()))) {
auto v19444 = s->LocalAt(7);
s->SetAt(9, v19444);
while (static_cast<bool>(([&]() -> Value { auto v19445 = ([&]() -> Value { auto v19446 = s->LocalAt(9); Value v19447; v19447 = ([&]() -> Value { auto fn19448 = s->Global("len"); Arguments args19449; args19449.Add(s->LocalAt(17), false); return Call(c, fn19448, std::move(args19449)); }()); if (!static_cast<bool>(Binary("Lt", v19446, v19447))) return Value(false); v19446 = v19447; return Value(true); }()); if (!static_cast<bool>(v19445)) return v19445; v19445 = Get(s->LocalAt(17), s->LocalAt(9)); if (!static_cast<bool>(v19445)) return v19445; v19445 = ([&]() -> Value { auto v19450 = Get(Get(s->LocalAt(17), s->LocalAt(9)), Value(int64_t{0})); Value v19451; v19451 = Value("SELL"); if (!static_cast<bool>(Binary("Eq", v19450, v19451))) return Value(false); v19450 = v19451; return Value(true); }()); return v19445; }()))) {
auto v19452 = s->LocalAt(9);
s->SetAt(9, Inplace("Add", v19452, Value(int64_t{1})));
}
if (static_cast<bool>(([&]() -> Value { auto v19453 = Value(int64_t{2}); Value v19454; v19454 = ([&]() -> Value { auto v19455 = s->LocalAt(9); return Binary("Sub", v19455, s->LocalAt(7)); }()); if (!static_cast<bool>(Binary("LtE", v19453, v19454))) return Value(false); v19453 = v19454; v19454 = Value(int64_t{6}); if (!static_cast<bool>(Binary("LtE", v19453, v19454))) return Value(false); v19453 = v19454; return Value(true); }()))) {
(void)([&]() -> Value { auto fn19456 = Attribute(s->LocalAt(5), "append"); Arguments args19457; args19457.Add(Tuple({s->LocalAt(7), s->LocalAt(9)}), false); return Call(c, fn19456, std::move(args19457)); }());
}
auto v19458 = s->LocalAt(9);
s->SetAt(7, v19458);
}
else {
auto v19459 = s->LocalAt(7);
s->SetAt(7, Inplace("Add", v19459, Value(int64_t{1})));
}
}
if (static_cast<bool>(Unary("Not", s->LocalAt(5)))) {
return s->LocalAt(0);
}
auto v19460 = ([&]() -> Value { auto fn19461 = s->Global("FarmView"); Arguments args19462; args19462.Add(s->LocalAt(15), false); return Call(c, fn19461, std::move(args19462)); }());
s->SetAt(24, v19460);
auto v19463 = ([&]() -> Value { auto fn19464 = s->Global("projected_shed"); Arguments args19465; args19465.positional.reserve(2); args19465.Add(s->LocalAt(0), false); args19465.Add(s->LocalAt(24), false); return Call(c, fn19464, std::move(args19465)); }());
s->SetAt(22, v19463);
auto v19466 = ([&]() -> Value { auto comp19467 = std::make_shared<Scope>(); comp19467->globals = s->globals; comp19467->parent = s; static constexpr const char* comp19467_names[] = {"k", "v"}; comp19467->PrepareSlots(comp19467_names); auto result19468 = Dict(); for (const auto& item19469 : Iterate(([&]() -> Value { auto fn19470 = Attribute(s->LocalAt(22), "items"); Arguments args19471; return Call(c, fn19470, std::move(args19471)); }()))) { auto unpack19472 = Iterate(item19469); ValidateUnpack(unpack19472, 2, false); comp19467->SetAt(0, unpack19472.at(0)); comp19467->SetAt(1, unpack19472.at(1)); Put(result19468, comp19467->LocalAt(0), ([&]() -> Value { auto fn19473 = comp19467->Global("max"); Arguments args19474; args19474.positional.reserve(2); args19474.Add(Value(int64_t{0}), false); args19474.Add(([&]() -> Value { auto fn19475 = comp19467->Global("int"); Arguments args19476; args19476.Add(comp19467->LocalAt(1), false); return Call(c, fn19475, std::move(args19476)); }()), false); return Call(c, fn19473, std::move(args19474)); }())); } return result19468; }());
s->SetAt(22, v19466);
auto v19477 = ([&]() -> Value { auto fn19478 = s->Global("_v44y_params"); Arguments args19479; args19479.Add(s->LocalAt(15), false); return Call(c, fn19478, std::move(args19479)); }());
s->SetAt(19, v19477);
auto v19480 = ([&]() -> Value { auto comp19481 = std::make_shared<Scope>(); comp19481->globals = s->globals; comp19481->parent = s; static constexpr const char* comp19481_names[] = {"k", "v"}; comp19481->PrepareSlots(comp19481_names); auto result19482 = Dict(); for (const auto& item19483 : Iterate(([&]() -> Value { auto fn19484 = Attribute(Get(Get(s->LocalAt(15), Value("market")), Value("inventory")), "items"); Arguments args19485; return Call(c, fn19484, std::move(args19485)); }()))) { auto unpack19486 = Iterate(item19483); ValidateUnpack(unpack19486, 2, false); comp19481->SetAt(0, unpack19486.at(0)); comp19481->SetAt(1, unpack19486.at(1)); Put(result19482, comp19481->LocalAt(0), ([&]() -> Value { auto fn19487 = comp19481->Global("int"); Arguments args19488; args19488.Add(comp19481->LocalAt(1), false); return Call(c, fn19487, std::move(args19488)); }())); } return result19482; }());
s->SetAt(8, v19480);
auto v19489 = ([&]() -> Value { auto comp19490 = std::make_shared<Scope>(); comp19490->globals = s->globals; comp19490->parent = s; static constexpr const char* comp19490_names[] = {"o"}; comp19490->PrepareSlots(comp19490_names); auto result19491 = List(); for (const auto& item19492 : Iterate(s->LocalAt(17))) { comp19490->SetAt(0, item19492); result19491.node()->sequence.push_back(([&]() -> Value { auto fn19493 = comp19490->Global("list"); Arguments args19494; args19494.Add(comp19490->LocalAt(0), false); return Call(c, fn19493, std::move(args19494)); }())); } return result19491; }());
s->SetAt(16, v19489);
auto v19495 = ([&]() -> Value { auto fn19496 = s->Global("_v44y_factor_margin"); Arguments args19497; args19497.positional.reserve(4); args19497.Add(s->LocalAt(16), false); args19497.Add(s->LocalAt(8), false); args19497.Add(s->LocalAt(22), false); args19497.Add(s->LocalAt(19), false); return Call(c, fn19496, std::move(args19497)); }());
s->SetAt(11, v19495);
auto v19498 = ([&]() -> Value { auto fn19499 = s->LocalAt(11); Arguments args19500; args19500.Add(s->LocalAt(17), false); return Call(c, fn19499, std::move(args19500)); }());
s->SetAt(1, v19498);
auto v19501 = s->LocalAt(1);
s->SetAt(2, v19501);
auto v19502 = Value{};
s->SetAt(3, v19502);
for (const auto& item19503 : Iterate(s->LocalAt(5))) {
auto unpack19504 = Iterate(item19503);
ValidateUnpack(unpack19504, 2, false);
s->SetAt(7, unpack19504.at(0));
s->SetAt(9, unpack19504.at(1));
auto v19505 = Slice(s->LocalAt(17), s->LocalAt(7), s->LocalAt(9), Value{});
s->SetAt(4, v19505);
auto v19506 = ([&]() -> Value { auto v19507 = s->LocalAt(9); return Binary("Sub", v19507, s->LocalAt(7)); }());
s->SetAt(13, v19506);
auto v19508 = ([&]() -> Value { auto fn19509 = s->Global("set"); Arguments args19510; return Call(c, fn19509, std::move(args19510)); }());
s->SetAt(21, v19508);
for (const auto& item19511 : Iterate(([&]() -> Value { auto fn19512 = Attribute(s->Global("_v44y_it"), "permutations"); Arguments args19513; args19513.Add(([&]() -> Value { auto fn19514 = s->Global("range"); Arguments args19515; args19515.Add(s->LocalAt(13), false); return Call(c, fn19514, std::move(args19515)); }()), false); return Call(c, fn19512, std::move(args19513)); }()))) {
s->SetAt(20, item19511);
auto v19516 = ([&]() -> Value { auto fn19517 = s->Global("tuple"); Arguments args19518; args19518.Add(([&]() -> Value { auto comp19519 = std::make_shared<Scope>(); comp19519->globals = s->globals; comp19519->parent = s; static constexpr const char* comp19519_names[] = {"p"}; comp19519->PrepareSlots(comp19519_names); auto result19520 = List(); for (const auto& item19521 : Iterate(s->LocalAt(20))) { comp19519->SetAt(0, item19521); result19520.node()->sequence.push_back(Tuple({Get(Get(comp19519->Captured("blk"), comp19519->LocalAt(0)), Value(int64_t{1})), ([&]() -> Value { auto fn19522 = comp19519->Global("int"); Arguments args19523; args19523.Add(Get(Get(comp19519->Captured("blk"), comp19519->LocalAt(0)), Value(int64_t{2})), false); return Call(c, fn19522, std::move(args19523)); }())})); } return result19520; }()), false); return Call(c, fn19517, std::move(args19518)); }());
s->SetAt(10, v19516);
if (static_cast<bool>(([&]() -> Value { auto v19524 = s->LocalAt(10); Value v19525; v19525 = s->LocalAt(21); if (!static_cast<bool>(Binary("In", v19524, v19525))) return Value(false); v19524 = v19525; return Value(true); }()))) {
continue;
}
(void)([&]() -> Value { auto fn19526 = Attribute(s->LocalAt(21), "add"); Arguments args19527; args19527.Add(s->LocalAt(10), false); return Call(c, fn19526, std::move(args19527)); }());
auto v19528 = ([&]() -> Value { auto v19529 = ([&]() -> Value { auto v19530 = Slice(s->LocalAt(17), Value{}, s->LocalAt(7), Value{}); return Binary("Add", v19530, ([&]() -> Value { auto comp19531 = std::make_shared<Scope>(); comp19531->globals = s->globals; comp19531->parent = s; static constexpr const char* comp19531_names[] = {"p"}; comp19531->PrepareSlots(comp19531_names); auto result19532 = List(); for (const auto& item19533 : Iterate(s->LocalAt(20))) { comp19531->SetAt(0, item19533); result19532.node()->sequence.push_back(Get(comp19531->Captured("blk"), comp19531->LocalAt(0))); } return result19532; }())); }()); return Binary("Add", v19529, Slice(s->LocalAt(17), s->LocalAt(9), Value{}, Value{})); }());
s->SetAt(6, v19528);
auto v19534 = ([&]() -> Value { auto fn19535 = s->LocalAt(11); Arguments args19536; args19536.Add(s->LocalAt(6), false); return Call(c, fn19535, std::move(args19536)); }());
s->SetAt(23, v19534);
if (static_cast<bool>(([&]() -> Value { auto v19537 = s->LocalAt(23); Value v19538; v19538 = ([&]() -> Value { auto v19539 = s->LocalAt(2); return Binary("Add", v19539, Value(0.5)); }()); if (!static_cast<bool>(Binary("Gt", v19537, v19538))) return Value(false); v19537 = v19538; return Value(true); }()))) {
auto v19540 = s->LocalAt(23);
s->SetAt(2, v19540);
auto v19541 = s->LocalAt(6);
s->SetAt(3, v19541);
}
}
if (static_cast<bool>(([&]() -> Value { auto v19542 = s->LocalAt(3); Value v19543; v19543 = Value{}; if (!static_cast<bool>(Binary("IsNot", v19542, v19543))) return Value(false); v19542 = v19543; return Value(true); }()))) {
auto v19544 = s->LocalAt(3);
s->SetAt(17, v19544);
auto v19545 = Value{};
s->SetAt(3, v19545);
}
}
if (static_cast<bool>(([&]() -> Value { auto v19546 = s->LocalAt(2); Value v19547; v19547 = ([&]() -> Value { auto v19548 = s->LocalAt(1); return Binary("Add", v19548, Value(0.5)); }()); if (!static_cast<bool>(Binary("LtE", v19546, v19547))) return Value(false); v19546 = v19547; return Value(true); }()))) {
return s->LocalAt(0);
}
auto v19549 = s->Global("_V44Y_REPORT");
auto v19550 = Value("v44y_reorder_turns");
auto v19551 = Get(v19549, v19550);
Put(v19549, v19550, Inplace("Add", v19551, Value(int64_t{1})));
auto v19552 = s->Global("_V44Y_REPORT");
auto v19553 = Value("v44y_reorder_gain");
auto v19554 = Get(v19552, v19553);
Put(v19552, v19553, Inplace("Add", v19554, ([&]() -> Value { auto v19555 = s->LocalAt(2); return Binary("Sub", v19555, s->LocalAt(1)); }())));
auto v19556 = ([&]() -> Value { auto fn19557 = s->Global("dict"); Arguments args19558; args19558.Add(s->LocalAt(0), false); return Call(c, fn19557, std::move(args19558)); }());
s->SetAt(18, v19556);
auto v19559 = s->LocalAt(17);
Put(s->LocalAt(18), Value("market"), v19559);
return s->LocalAt(18);
return {};
}
}  // namespace kagg::opponents::compiled
