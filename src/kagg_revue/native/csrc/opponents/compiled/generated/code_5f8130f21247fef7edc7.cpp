// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_5f8130f21247fef7edc7(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"_", "action", "inventory", "item", "obs", "orders", "private", "q"};
s->PrepareSlots(s_names);
auto v11485 = ([&]() -> Value { auto v11486 = ([&]() -> Value { auto fn11487 = PrepareDictionaryGet(s->LocalAt(1)); Arguments args11488; args11488.Add(Value("market"), false); return CallDictionaryGet(c, fn11487, std::move(args11488)); }()); if (static_cast<bool>(v11486)) return v11486; v11486 = List({}); return v11486; }());
s->SetAt(5, v11485);
if (static_cast<bool>(([&]() -> Value { auto v11489 = Unary("Not", s->LocalAt(5)); if (static_cast<bool>(v11489)) return v11489; v11489 = ([&]() -> Value { auto v11490 = ([&]() -> Value { auto fn11492 = s->Global("len"); Arguments args11493; args11493.Add(Get(s->LocalAt(5), Value(int64_t{0})), false); return Call(c, fn11492, std::move(args11493)); }()); Value v11491; v11491 = Value(int64_t{3}); if (!static_cast<bool>(Binary("Lt", v11490, v11491))) return Value(false); v11490 = v11491; return Value(true); }()); if (static_cast<bool>(v11489)) return v11489; v11489 = ([&]() -> Value { auto v11494 = Get(Get(s->LocalAt(5), Value(int64_t{0})), Value(int64_t{0})); Value v11495; v11495 = Value("SELL"); if (!static_cast<bool>(Binary("NotEq", v11494, v11495))) return Value(false); v11494 = v11495; return Value(true); }()); if (static_cast<bool>(v11489)) return v11489; v11489 = ([&]() -> Value { auto v11496 = Get(Get(s->LocalAt(5), Value(int64_t{0})), Value(int64_t{1})); Value v11497; v11497 = Value("WHEAT"); if (!static_cast<bool>(Binary("Eq", v11496, v11497))) return Value(false); v11496 = v11497; return Value(true); }()); return v11489; }()))) {
return Value(int64_t{0});
}
auto v11498 = Get(Get(s->LocalAt(5), Value(int64_t{0})), Value(int64_t{1}));
s->SetAt(3, v11498);
if (static_cast<bool>(([&]() -> Value { auto v11499 = s->LocalAt(3); Value v11500; v11500 = Get(Get(s->LocalAt(4), Value("market")), Value("inventory")); if (!static_cast<bool>(Binary("NotIn", v11499, v11500))) return Value(false); v11499 = v11500; return Value(true); }()))) {
return Value(int64_t{0});
}
auto v11501 = ([&]() -> Value { auto fn11502 = s->Global("_r127_fields"); Arguments args11503; args11503.positional.reserve(2); args11503.Add(s->LocalAt(4), false); args11503.Add(s->LocalAt(1), false); return Call(c, fn11502, std::move(args11503)); }());
auto unpack11504 = Iterate(v11501);
ValidateUnpack(unpack11504, 2, false);
s->SetAt(0, unpack11504.at(0));
s->SetAt(6, unpack11504.at(1));
auto v11505 = ([&]() -> Value { auto fn11506 = s->Global("min"); Arguments args11507; args11507.positional.reserve(2); args11507.Add(([&]() -> Value { auto fn11508 = s->Global("max"); Arguments args11509; args11509.positional.reserve(2); args11509.Add(Value(int64_t{0}), false); args11509.Add(([&]() -> Value { auto fn11510 = s->Global("int"); Arguments args11511; args11511.Add(Get(Get(s->LocalAt(5), Value(int64_t{0})), Value(int64_t{2})), false); return Call(c, fn11510, std::move(args11511)); }()), false); return Call(c, fn11508, std::move(args11509)); }()), false); args11507.Add(([&]() -> Value { auto fn11512 = s->Global("max"); Arguments args11513; args11513.positional.reserve(2); args11513.Add(Value(int64_t{0}), false); args11513.Add(([&]() -> Value { auto fn11514 = s->Global("int"); Arguments args11515; args11515.Add(([&]() -> Value { auto fn11516 = PrepareDictionaryGet(Get(s->LocalAt(6), Value("shed"))); Arguments args11517; args11517.positional.reserve(2); args11517.Add(s->LocalAt(3), false); args11517.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn11516, std::move(args11517)); }()), false); return Call(c, fn11514, std::move(args11515)); }()), false); return Call(c, fn11512, std::move(args11513)); }()), false); return Call(c, fn11506, std::move(args11507)); }());
s->SetAt(7, v11505);
auto v11518 = ([&]() -> Value { auto fn11519 = s->Global("int"); Arguments args11520; args11520.Add(Get(Get(Get(s->LocalAt(4), Value("market")), Value("inventory")), s->LocalAt(3)), false); return Call(c, fn11519, std::move(args11520)); }());
s->SetAt(2, v11518);
return ([&]() -> Value { auto fn11521 = s->Global("sum"); Arguments args11522; args11522.Add(([&]() -> Value { auto comp11523 = std::make_shared<Scope>(); comp11523->globals = s->globals; comp11523->parent = s; static constexpr const char* comp11523_names[] = {"j"}; comp11523->PrepareSlots(comp11523_names); auto result11524 = List(); for (const auto& item11525 : Iterate(([&]() -> Value { auto fn11526 = s->Global("range"); Arguments args11527; args11527.Add(s->LocalAt(7), false); return Call(c, fn11526, std::move(args11527)); }()))) { comp11523->SetAt(0, item11525); result11524.node()->sequence.push_back(([&]() -> Value { auto fn11528 = comp11523->Global("_r37_market_price"); Arguments args11529; args11529.positional.reserve(2); args11529.Add(comp11523->Captured("item"), false); args11529.Add(([&]() -> Value { auto v11530 = comp11523->Captured("inventory"); return Binary("Add", v11530, ([&]() -> Value { auto v11531 = Value(int64_t{2}); return Binary("Mult", v11531, comp11523->LocalAt(0)); }())); }()), false); return Call(c, fn11528, std::move(args11529)); }())); } return result11524; }()), false); return Call(c, fn11521, std::move(args11522)); }());
return {};
}
}  // namespace kagg::opponents::compiled
