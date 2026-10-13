// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_c7f9c0d02e7c8a0bb201(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"draw", "item", "name", "products", "shops", "step"};
s->PrepareSlots(s_names);
auto v22480 = ([&]() -> Value { auto dict22481 = Dict(); return dict22481; }());
s->SetAt(0, v22480);
if (static_cast<bool>(([&]() -> Value { auto v22482 = ([&]() -> Value { auto v22484 = s->LocalAt(5); return Binary("Mod", v22484, Value(int64_t{4})); }()); Value v22483; v22483 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v22482, v22483))) return Value(false); v22482 = v22483; return Value(true); }()))) {
for (const auto& item22485 : Iterate(s->LocalAt(4))) {
s->SetAt(2, item22485);
auto v22486 = ([&]() -> Value { auto fn22487 = PrepareDictionaryGet(s->Global("_OR2_SHOPS")); Arguments args22488; args22488.positional.reserve(2); args22488.Add(s->LocalAt(2), false); args22488.Add(Tuple({}), false); return CallDictionaryGet(c, fn22487, std::move(args22488)); }());
s->SetAt(3, v22486);
for (const auto& item22489 : Iterate(s->LocalAt(3))) {
s->SetAt(1, item22489);
auto v22490 = ([&]() -> Value { auto v22491 = ([&]() -> Value { auto fn22492 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args22493; args22493.positional.reserve(2); args22493.Add(s->LocalAt(1), false); args22493.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn22492, std::move(args22493)); }()); return Binary("Add", v22491, (static_cast<bool>(([&]() -> Value { auto v22494 = ([&]() -> Value { auto fn22496 = s->Global("len"); Arguments args22497; args22497.Add(s->LocalAt(3), false); return Call(c, fn22496, std::move(args22497)); }()); Value v22495; v22495 = Value(int64_t{1}); if (!static_cast<bool>(Binary("Eq", v22494, v22495))) return Value(false); v22494 = v22495; return Value(true); }())) ? Value(int64_t{2}) : Value(int64_t{1}))); }());
Put(s->LocalAt(0), s->LocalAt(1), v22490);
}
}
}
if (static_cast<bool>(([&]() -> Value { auto v22498 = ([&]() -> Value { auto v22500 = s->LocalAt(5); return Binary("Mod", v22500, Value(int64_t{24})); }()); Value v22499; v22499 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v22498, v22499))) return Value(false); v22498 = v22499; return Value(true); }()))) {
for (const auto& item22501 : Iterate(s->Global("_OR2_ITEMS"))) {
s->SetAt(1, item22501);
auto v22502 = ([&]() -> Value { auto v22503 = ([&]() -> Value { auto fn22504 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args22505; args22505.positional.reserve(2); args22505.Add(s->LocalAt(1), false); args22505.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn22504, std::move(args22505)); }()); return Binary("Add", v22503, Value(int64_t{1})); }());
Put(s->LocalAt(0), s->LocalAt(1), v22502);
}
}
return s->LocalAt(0);
return {};
}
}  // namespace kagg::opponents::compiled
