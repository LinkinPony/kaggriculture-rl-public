// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_61ed35006b440990de21(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "actor", "command", "hands", "result"};
s->PrepareSlots(s_names);
auto v15417 = ([&]() -> Value { auto fn15418 = Attribute(s->Global("copy"), "deepcopy"); Arguments args15419; args15419.Add(s->LocalAt(0), false); return Call(c, fn15418, std::move(args15419)); }());
s->SetAt(4, v15417);
if (static_cast<bool>(([&]() -> Value { auto v15420 = s->LocalAt(1); Value v15421; v15421 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v15420, v15421))) return Value(false); v15420 = v15421; return Value(true); }()))) {
auto v15422 = ([&]() -> Value { auto fn15423 = s->Global("list"); Arguments args15424; args15424.Add(s->LocalAt(2), false); return Call(c, fn15423, std::move(args15424)); }());
Put(s->LocalAt(4), Value("farmer"), v15422);
}
else {
auto v15425 = ([&]() -> Value { auto fn15426 = s->Global("list"); Arguments args15427; args15427.Add(([&]() -> Value { auto v15428 = ([&]() -> Value { auto fn15429 = PrepareDictionaryGet(s->LocalAt(4)); Arguments args15430; args15430.Add(Value("hands"), false); return CallDictionaryGet(c, fn15429, std::move(args15430)); }()); if (static_cast<bool>(v15428)) return v15428; v15428 = List({}); return v15428; }()), false); return Call(c, fn15426, std::move(args15427)); }());
s->SetAt(3, v15425);
if (static_cast<bool>(([&]() -> Value { auto v15431 = ([&]() -> Value { auto v15433 = s->LocalAt(1); return Binary("Sub", v15433, Value(int64_t{1})); }()); Value v15432; v15432 = ([&]() -> Value { auto fn15434 = s->Global("len"); Arguments args15435; args15435.Add(s->LocalAt(3), false); return Call(c, fn15434, std::move(args15435)); }()); if (!static_cast<bool>(Binary("GtE", v15431, v15432))) return Value(false); v15431 = v15432; return Value(true); }()))) {
return s->LocalAt(0);
}
auto v15436 = ([&]() -> Value { auto fn15437 = s->Global("list"); Arguments args15438; args15438.Add(s->LocalAt(2), false); return Call(c, fn15437, std::move(args15438)); }());
Put(s->LocalAt(3), ([&]() -> Value { auto v15439 = s->LocalAt(1); return Binary("Sub", v15439, Value(int64_t{1})); }()), v15436);
auto v15440 = s->LocalAt(3);
Put(s->LocalAt(4), Value("hands"), v15440);
}
return s->LocalAt(4);
return {};
}
}  // namespace kagg::opponents::compiled
