// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_3aef308901f8a4b7c45d(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"farm", "out", "row", "t", "x", "y"};
s->PrepareSlots(s_names);
auto v22506 = ([&]() -> Value { auto dict22507 = Dict(); return dict22507; }());
s->SetAt(1, v22506);
for (const auto& item22508 : Iterate(([&]() -> Value { auto fn22509 = s->Global("enumerate"); Arguments args22510; args22510.Add(Get(s->LocalAt(0), Value("tiles")), false); return Call(c, fn22509, std::move(args22510)); }()))) {
auto unpack22511 = Iterate(item22508);
ValidateUnpack(unpack22511, 2, false);
s->SetAt(5, unpack22511.at(0));
s->SetAt(2, unpack22511.at(1));
for (const auto& item22512 : Iterate(([&]() -> Value { auto fn22513 = s->Global("enumerate"); Arguments args22514; args22514.Add(s->LocalAt(2), false); return Call(c, fn22513, std::move(args22514)); }()))) {
auto unpack22515 = Iterate(item22512);
ValidateUnpack(unpack22515, 2, false);
s->SetAt(4, unpack22515.at(0));
s->SetAt(3, unpack22515.at(1));
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto fn22516 = s->Global("isinstance"); Arguments args22517; args22517.positional.reserve(2); args22517.Add(s->LocalAt(3), false); args22517.Add(s->Global("dict"), false); return Call(c, fn22516, std::move(args22517)); }())))) {
continue;
}
if (static_cast<bool>(([&]() -> Value { auto v22518 = ([&]() -> Value { auto v22519 = ([&]() -> Value { auto fn22521 = PrepareDictionaryGet(s->LocalAt(3)); Arguments args22522; args22522.Add(Value("kind"), false); return CallDictionaryGet(c, fn22521, std::move(args22522)); }()); Value v22520; v22520 = Value("PLANT"); if (!static_cast<bool>(Binary("Eq", v22519, v22520))) return Value(false); v22519 = v22520; return Value(true); }()); if (!static_cast<bool>(v22518)) return v22518; v22518 = ([&]() -> Value { auto fn22523 = PrepareDictionaryGet(s->LocalAt(3)); Arguments args22524; args22524.Add(Value("crop"), false); return CallDictionaryGet(c, fn22523, std::move(args22524)); }()); return v22518; }()))) {
auto v22525 = Tuple({Value("P"), Get(s->LocalAt(3), Value("crop")), ([&]() -> Value { auto fn22526 = s->Global("int"); Arguments args22527; args22527.Add(([&]() -> Value { auto fn22528 = PrepareDictionaryGet(s->LocalAt(3)); Arguments args22529; args22529.positional.reserve(2); args22529.Add(Value("planted_day"), false); args22529.Add(Unary("USub", Value(int64_t{1})), false); return CallDictionaryGet(c, fn22528, std::move(args22529)); }()), false); return Call(c, fn22526, std::move(args22527)); }()), ([&]() -> Value { auto fn22530 = s->Global("int"); Arguments args22531; args22531.Add(([&]() -> Value { auto fn22532 = PrepareDictionaryGet(s->LocalAt(3)); Arguments args22533; args22533.positional.reserve(2); args22533.Add(Value("yield_units"), false); args22533.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn22532, std::move(args22533)); }()), false); return Call(c, fn22530, std::move(args22531)); }())});
Put(s->LocalAt(1), Tuple({s->LocalAt(4), s->LocalAt(5)}), v22525);
}
else {
if (static_cast<bool>(([&]() -> Value { auto v22534 = ([&]() -> Value { auto fn22536 = PrepareDictionaryGet(s->LocalAt(3)); Arguments args22537; args22537.Add(Value("animal"), false); return CallDictionaryGet(c, fn22536, std::move(args22537)); }()); Value v22535; v22535 = s->Global("_OR2_ANIMAL"); if (!static_cast<bool>(Binary("In", v22534, v22535))) return Value(false); v22534 = v22535; return Value(true); }()))) {
auto v22538 = Tuple({Value("A"), Get(s->Global("_OR2_ANIMAL"), Get(s->LocalAt(3), Value("animal"))), ([&]() -> Value { auto fn22539 = s->Global("int"); Arguments args22540; args22540.Add(([&]() -> Value { auto fn22541 = PrepareDictionaryGet(s->LocalAt(3)); Arguments args22542; args22542.positional.reserve(2); args22542.Add(Value("placed_day"), false); args22542.Add(Unary("USub", Value(int64_t{1})), false); return CallDictionaryGet(c, fn22541, std::move(args22542)); }()), false); return Call(c, fn22539, std::move(args22540)); }()), ([&]() -> Value { auto fn22543 = s->Global("int"); Arguments args22544; args22544.Add(([&]() -> Value { auto fn22545 = PrepareDictionaryGet(s->LocalAt(3)); Arguments args22546; args22546.positional.reserve(2); args22546.Add(Value("yield_units"), false); args22546.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn22545, std::move(args22546)); }()), false); return Call(c, fn22543, std::move(args22544)); }())});
Put(s->LocalAt(1), Tuple({s->LocalAt(4), s->LocalAt(5)}), v22538);
}
}
}
}
return s->LocalAt(1);
return {};
}
}  // namespace kagg::opponents::compiled
