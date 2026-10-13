// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_3e7521f3d394b7a67501(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "debts", "obs", "own", "player", "st", "step"};
s->PrepareSlots(s_names);
auto v6495 = ([&]() -> Value { auto fn6496 = s->Global("int"); Arguments args6497; args6497.Add(Get(s->LocalAt(2), Value("step")), false); return Call(c, fn6496, std::move(args6497)); }());
s->SetAt(6, v6495);
auto v6498 = ([&]() -> Value { auto fn6499 = s->Global("int"); Arguments args6500; args6500.Add(Get(s->LocalAt(2), Value("player")), false); return Call(c, fn6499, std::move(args6500)); }());
s->SetAt(4, v6498);
if (static_cast<bool>(([&]() -> Value { auto v6501 = Unary("Not", ([&]() -> Value { auto v6502 = Value(int64_t{336}); Value v6503; v6503 = s->LocalAt(6); if (!static_cast<bool>(Binary("LtE", v6502, v6503))) return Value(false); v6502 = v6503; v6503 = Value(int64_t{648}); if (!static_cast<bool>(Binary("Lt", v6502, v6503))) return Value(false); v6502 = v6503; return Value(true); }())); if (static_cast<bool>(v6501)) return v6501; v6501 = Get(s->LocalAt(5), Value("matched")); return v6501; }()))) {
return Value{};
}
if (static_cast<bool>(([&]() -> Value { auto v6504 = Unary("Not", Get(s->LocalAt(0), Value("market"))); if (static_cast<bool>(v6504)) return v6504; v6504 = ([&]() -> Value { auto comp6505 = std::make_shared<Scope>(); comp6505->globals = s->globals; comp6505->parent = s; static constexpr const char* comp6505_names[] = {"o"}; comp6505->PrepareSlots(comp6505_names); auto result6506 = List(); for (const auto& item6507 : Iterate(Get(s->LocalAt(0), Value("market")))) { comp6505->SetAt(0, item6507); if (static_cast<bool>(([&]() -> Value { auto v6508 = comp6505->LocalAt(0); if (!static_cast<bool>(v6508)) return v6508; v6508 = ([&]() -> Value { auto v6509 = Get(comp6505->LocalAt(0), Value(int64_t{0})); Value v6510; v6510 = Value("SELL"); if (!static_cast<bool>(Binary("NotEq", v6509, v6510))) return Value(false); v6509 = v6510; return Value(true); }()); return v6508; }()))) return Value(true); } return Value(false); }()); return v6504; }()))) {
return Value{};
}
auto v6511 = ([&]() -> Value { auto fn6512 = PrepareDictionaryGet(Get(Get(Attribute(Attribute(s->Global("_IMPL"), "chassis"), "players"), s->LocalAt(4)), Value("sell_state"))); Arguments args6513; args6513.positional.reserve(2); args6513.Add(Value("r36_debts"), false); args6513.Add(([&]() -> Value { auto dict6514 = Dict(); return dict6514; }()), false); return CallDictionaryGet(c, fn6512, std::move(args6513)); }());
s->SetAt(1, v6511);
auto v6515 = ([&]() -> Value { auto fn6516 = PrepareDictionaryGet(s->LocalAt(1)); Arguments args6517; args6517.positional.reserve(2); args6517.Add(([&]() -> Value { auto v6518 = s->LocalAt(6); return Binary("Add", v6518, Value(int64_t{3})); }()), false); args6517.Add(([&]() -> Value { auto dict6519 = Dict(); return dict6519; }()), false); return CallDictionaryGet(c, fn6516, std::move(args6517)); }());
s->SetAt(3, v6515);
if (static_cast<bool>(s->LocalAt(3))) {
auto v6520 = ([&]() -> Value { auto fn6521 = s->Global("sum"); Arguments args6522; args6522.Add(([&]() -> Value { auto comp6523 = std::make_shared<Scope>(); comp6523->globals = s->globals; comp6523->parent = s; static constexpr const char* comp6523_names[] = {"item", "n"}; comp6523->PrepareSlots(comp6523_names); auto result6524 = List(); for (const auto& item6525 : Iterate(([&]() -> Value { auto fn6526 = Attribute(s->LocalAt(3), "items"); Arguments args6527; return Call(c, fn6526, std::move(args6527)); }()))) { auto unpack6528 = Iterate(item6525); ValidateUnpack(unpack6528, 2, false); comp6523->SetAt(0, unpack6528.at(0)); comp6523->SetAt(1, unpack6528.at(1)); result6524.node()->sequence.push_back(([&]() -> Value { auto v6529 = ([&]() -> Value { auto fn6530 = comp6523->Global("max"); Arguments args6531; args6531.positional.reserve(2); args6531.Add(Value(int64_t{0}), false); args6531.Add(([&]() -> Value { auto fn6532 = comp6523->Global("int"); Arguments args6533; args6533.Add(comp6523->LocalAt(1), false); return Call(c, fn6532, std::move(args6533)); }()), false); return Call(c, fn6530, std::move(args6531)); }()); return Binary("Mult", v6529, ([&]() -> Value { auto fn6534 = comp6523->Global("int"); Arguments args6535; args6535.Add(([&]() -> Value { auto fn6536 = PrepareDictionaryGet(Get(Get(comp6523->Captured("obs"), Value("market")), Value("prices"))); Arguments args6537; args6537.positional.reserve(2); args6537.Add(comp6523->LocalAt(0), false); args6537.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn6536, std::move(args6537)); }()), false); return Call(c, fn6534, std::move(args6535)); }())); }())); } return result6524; }()), false); return Call(c, fn6521, std::move(args6522)); }());
Put(s->LocalAt(5), Value("probe"), v6520);
}
return {};
}
}  // namespace kagg::opponents::compiled
