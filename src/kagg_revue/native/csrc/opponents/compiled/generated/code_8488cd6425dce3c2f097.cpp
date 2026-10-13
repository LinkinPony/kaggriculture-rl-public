// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_8488cd6425dce3c2f097(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "items", "market", "o", "obs", "plan", "result", "rival", "slot", "st", "step"};
s->PrepareSlots(s_names);
auto v30483 = ([&]() -> Value { auto fn30484 = s->Global("int"); Arguments args30485; args30485.Add(Get(s->LocalAt(4), Value("step")), false); return Call(c, fn30484, std::move(args30485)); }());
s->SetAt(10, v30483);
if (static_cast<bool>(([&]() -> Value { auto v30486 = s->LocalAt(10); Value v30487; v30487 = Value(int64_t{2}); if (!static_cast<bool>(Binary("Eq", v30486, v30487))) return Value(false); v30486 = v30487; return Value(true); }()))) {
auto v30488 = Get(Get(s->LocalAt(4), Value("farms")), ([&]() -> Value { auto v30489 = Value(int64_t{1}); return Binary("Sub", v30489, ([&]() -> Value { auto fn30490 = s->Global("int"); Arguments args30491; args30491.Add(Get(s->LocalAt(4), Value("player")), false); return Call(c, fn30490, std::move(args30491)); }())); }()));
s->SetAt(7, v30488);
auto v30492 = ([&]() -> Value { auto fn30493 = PrepareDictionaryGet(s->Global("CT_TABLE")); Arguments args30494; args30494.Add(Tuple({([&]() -> Value { auto fn30495 = s->Global("round"); Arguments args30496; args30496.positional.reserve(2); args30496.Add(([&]() -> Value { auto fn30497 = s->Global("float"); Arguments args30498; args30498.Add(Get(s->LocalAt(7), Value("money")), false); return Call(c, fn30497, std::move(args30498)); }()), false); args30496.Add(Value(int64_t{3}), false); return Call(c, fn30495, std::move(args30496)); }()), ([&]() -> Value { auto fn30499 = s->Global("int"); Arguments args30500; args30500.Add(Get(Get(Get(s->LocalAt(4), Value("market")), Value("inventory")), Value("WHEAT")), false); return Call(c, fn30499, std::move(args30500)); }())}), false); return CallDictionaryGet(c, fn30493, std::move(args30494)); }());
Put(s->LocalAt(9), Value("plan"), v30492);
if (static_cast<bool>(Get(s->LocalAt(9), Value("plan")))) {
auto v30501 = s->Global("_CT_REPORT");
auto v30502 = Value("ct_fired");
auto v30503 = Get(v30501, v30502);
Put(v30501, v30502, Inplace("Add", v30503, Value(int64_t{1})));
}
}
auto v30504 = ([&]() -> Value { auto fn30505 = PrepareDictionaryGet(s->LocalAt(9)); Arguments args30506; args30506.Add(Value("plan"), false); return CallDictionaryGet(c, fn30505, std::move(args30506)); }());
s->SetAt(5, v30504);
if (static_cast<bool>(Unary("Not", s->LocalAt(5)))) {
return s->LocalAt(0);
}
auto v30507 = ([&]() -> Value { auto fn30508 = s->Global("sorted"); Arguments args30509; args30509.Add(([&]() -> Value { auto comp30510 = std::make_shared<Scope>(); comp30510->globals = s->globals; comp30510->parent = s; static constexpr const char* comp30510_names[] = {"o", "slot", "t"}; comp30510->PrepareSlots(comp30510_names); auto result30511 = List(); for (const auto& item30512 : Iterate(s->LocalAt(5))) { auto unpack30513 = Iterate(item30512); ValidateUnpack(unpack30513, 3, false); comp30510->SetAt(2, unpack30513.at(0)); comp30510->SetAt(1, unpack30513.at(1)); comp30510->SetAt(0, unpack30513.at(2)); if (!static_cast<bool>(([&]() -> Value { auto v30514 = comp30510->LocalAt(2); Value v30515; v30515 = comp30510->Captured("step"); if (!static_cast<bool>(Binary("Eq", v30514, v30515))) return Value(false); v30514 = v30515; return Value(true); }()))) continue; result30511.node()->sequence.push_back(Tuple({comp30510->LocalAt(1), ([&]() -> Value { auto fn30516 = comp30510->Global("list"); Arguments args30517; args30517.Add(comp30510->LocalAt(0), false); return Call(c, fn30516, std::move(args30517)); }())})); } return result30511; }()), false); return Call(c, fn30508, std::move(args30509)); }());
s->SetAt(1, v30507);
if (static_cast<bool>(Unary("Not", s->LocalAt(1)))) {
return s->LocalAt(0);
}
auto v30518 = ([&]() -> Value { auto comp30519 = std::make_shared<Scope>(); comp30519->globals = s->globals; comp30519->parent = s; static constexpr const char* comp30519_names[] = {"o"}; comp30519->PrepareSlots(comp30519_names); auto result30520 = List(); for (const auto& item30521 : Iterate(([&]() -> Value { auto v30522 = ([&]() -> Value { auto fn30523 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args30524; args30524.Add(Value("market"), false); return CallDictionaryGet(c, fn30523, std::move(args30524)); }()); if (static_cast<bool>(v30522)) return v30522; v30522 = List({}); return v30522; }()))) { comp30519->SetAt(0, item30521); result30520.node()->sequence.push_back(([&]() -> Value { auto fn30525 = comp30519->Global("list"); Arguments args30526; args30526.Add(comp30519->LocalAt(0), false); return Call(c, fn30525, std::move(args30526)); }())); } return result30520; }());
s->SetAt(2, v30518);
for (const auto& item30527 : Iterate(s->LocalAt(1))) {
auto unpack30528 = Iterate(item30527);
ValidateUnpack(unpack30528, 2, false);
s->SetAt(8, unpack30528.at(0));
s->SetAt(3, unpack30528.at(1));
while (static_cast<bool>(([&]() -> Value { auto v30529 = ([&]() -> Value { auto fn30531 = s->Global("len"); Arguments args30532; args30532.Add(s->LocalAt(2), false); return Call(c, fn30531, std::move(args30532)); }()); Value v30530; v30530 = s->LocalAt(8); if (!static_cast<bool>(Binary("Lt", v30529, v30530))) return Value(false); v30529 = v30530; return Value(true); }()))) {
(void)([&]() -> Value { auto fn30533 = Attribute(s->LocalAt(2), "append"); Arguments args30534; args30534.Add(List({Value("SELL"), Value("WHEAT"), Value(int64_t{0})}), false); return Call(c, fn30533, std::move(args30534)); }());
}
(void)([&]() -> Value { auto fn30535 = Attribute(s->LocalAt(2), "insert"); Arguments args30536; args30536.positional.reserve(2); args30536.Add(s->LocalAt(8), false); args30536.Add(s->LocalAt(3), false); return Call(c, fn30535, std::move(args30536)); }());
}
auto v30537 = ([&]() -> Value { auto fn30538 = s->Global("dict"); Arguments args30539; args30539.Add(s->LocalAt(0), false); return Call(c, fn30538, std::move(args30539)); }());
s->SetAt(6, v30537);
auto v30540 = Slice(s->LocalAt(2), Value{}, s->Global("MAX_ORDERS"), Value{});
Put(s->LocalAt(6), Value("market"), v30540);
return s->LocalAt(6);
return {};
}
}  // namespace kagg::opponents::compiled
