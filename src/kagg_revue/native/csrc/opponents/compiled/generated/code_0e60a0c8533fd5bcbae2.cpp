// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_0e60a0c8533fd5bcbae2(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"col", "item", "n", "o", "p", "route", "self", "step", "t", "table", "tape"};
s->PrepareSlots(s_names);
auto v478 = ([&]() -> Value { auto fn479 = PrepareDictionaryGet(Attribute(s->LocalAt(6), "_future_sells")); Arguments args480; args480.Add(s->LocalAt(5), false); return CallDictionaryGet(c, fn479, std::move(args480)); }());
s->SetAt(9, v478);
if (static_cast<bool>(([&]() -> Value { auto v481 = s->LocalAt(9); Value v482; v482 = Value{}; if (!static_cast<bool>(Binary("Is", v481, v482))) return Value(false); v481 = v482; return Value(true); }()))) {
auto v483 = Get(Attribute(s->LocalAt(6), "routes"), s->LocalAt(5));
s->SetAt(10, v483);
auto v484 = ([&]() -> Value { auto fn485 = s->Global("len"); Arguments args486; args486.Add(s->LocalAt(10), false); return Call(c, fn485, std::move(args486)); }());
s->SetAt(2, v484);
auto v487 = ([&]() -> Value { auto comp488 = std::make_shared<Scope>(); comp488->globals = s->globals; comp488->parent = s; static constexpr const char* comp488_names[] = {"p"}; comp488->PrepareSlots(comp488_names); auto result489 = Dict(); for (const auto& item490 : Iterate(s->Global("PRODUCTS"))) { comp488->SetAt(0, item490); Put(result489, comp488->LocalAt(0), ([&]() -> Value { auto v491 = List({Value(int64_t{0})}); return Binary("Mult", v491, ([&]() -> Value { auto v492 = comp488->Captured("n"); return Binary("Add", v492, Value(int64_t{1})); }())); }())); } return result489; }());
s->SetAt(9, v487);
for (const auto& item493 : Iterate(([&]() -> Value { auto fn494 = s->Global("range"); Arguments args495; args495.positional.reserve(3); args495.Add(([&]() -> Value { auto v496 = s->LocalAt(2); return Binary("Sub", v496, Value(int64_t{1})); }()), false); args495.Add(Unary("USub", Value(int64_t{1})), false); args495.Add(Unary("USub", Value(int64_t{1})), false); return Call(c, fn494, std::move(args495)); }()))) {
s->SetAt(8, item493);
for (const auto& item497 : Iterate(s->Global("PRODUCTS"))) {
s->SetAt(4, item497);
auto v498 = Get(Get(s->LocalAt(9), s->LocalAt(4)), ([&]() -> Value { auto v499 = s->LocalAt(8); return Binary("Add", v499, Value(int64_t{1})); }()));
Put(Get(s->LocalAt(9), s->LocalAt(4)), s->LocalAt(8), v498);
}
for (const auto& item500 : Iterate((static_cast<bool>(([&]() -> Value { auto fn501 = s->Global("isinstance"); Arguments args502; args502.positional.reserve(2); args502.Add(Get(s->LocalAt(10), s->LocalAt(8)), false); args502.Add(s->Global("dict"), false); return Call(c, fn501, std::move(args502)); }())) ? ([&]() -> Value { auto v503 = ([&]() -> Value { auto fn504 = PrepareDictionaryGet(Get(s->LocalAt(10), s->LocalAt(8))); Arguments args505; args505.Add(Value("market"), false); return CallDictionaryGet(c, fn504, std::move(args505)); }()); if (static_cast<bool>(v503)) return v503; v503 = List({}); return v503; }()) : List({})))) {
s->SetAt(3, item500);
if (static_cast<bool>(([&]() -> Value { auto v506 = s->LocalAt(3); if (!static_cast<bool>(v506)) return v506; v506 = ([&]() -> Value { auto v507 = Get(s->LocalAt(3), Value(int64_t{0})); Value v508; v508 = Value("SELL"); if (!static_cast<bool>(Binary("Eq", v507, v508))) return Value(false); v507 = v508; return Value(true); }()); if (!static_cast<bool>(v506)) return v506; v506 = ([&]() -> Value { auto v509 = ([&]() -> Value { auto fn511 = s->Global("len"); Arguments args512; args512.Add(s->LocalAt(3), false); return Call(c, fn511, std::move(args512)); }()); Value v510; v510 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v509, v510))) return Value(false); v509 = v510; return Value(true); }()); if (!static_cast<bool>(v506)) return v506; v506 = ([&]() -> Value { auto v513 = Get(s->LocalAt(3), Value(int64_t{1})); Value v514; v514 = s->LocalAt(9); if (!static_cast<bool>(Binary("In", v513, v514))) return Value(false); v513 = v514; return Value(true); }()); return v506; }()))) {
auto v515 = Get(s->LocalAt(9), Get(s->LocalAt(3), Value(int64_t{1})));
auto v516 = s->LocalAt(8);
auto v517 = Get(v515, v516);
Put(v515, v516, Inplace("Add", v517, ([&]() -> Value { auto fn518 = s->Global("max"); Arguments args519; args519.positional.reserve(2); args519.Add(Value(int64_t{0}), false); args519.Add(([&]() -> Value { auto fn520 = s->Global("_int"); Arguments args521; args521.Add(Get(s->LocalAt(3), Value(int64_t{2})), false); return Call(c, fn520, std::move(args521)); }()), false); return Call(c, fn518, std::move(args519)); }())));
}
}
}
auto v522 = s->LocalAt(9);
Put(Attribute(s->LocalAt(6), "_future_sells"), s->LocalAt(5), v522);
}
auto v523 = ([&]() -> Value { auto fn524 = PrepareDictionaryGet(s->LocalAt(9)); Arguments args525; args525.Add(s->LocalAt(1), false); return CallDictionaryGet(c, fn524, std::move(args525)); }());
s->SetAt(0, v523);
return (static_cast<bool>(([&]() -> Value { auto v526 = s->LocalAt(0); if (!static_cast<bool>(v526)) return v526; v526 = ([&]() -> Value { auto v527 = Value(int64_t{0}); Value v528; v528 = s->LocalAt(7); if (!static_cast<bool>(Binary("LtE", v527, v528))) return Value(false); v527 = v528; v528 = ([&]() -> Value { auto fn529 = s->Global("len"); Arguments args530; args530.Add(s->LocalAt(0), false); return Call(c, fn529, std::move(args530)); }()); if (!static_cast<bool>(Binary("Lt", v527, v528))) return Value(false); v527 = v528; return Value(true); }()); return v526; }())) ? Get(s->LocalAt(0), s->LocalAt(7)) : Value(int64_t{0}));
return {};
}
}  // namespace kagg::opponents::compiled
