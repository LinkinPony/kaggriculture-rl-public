// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_5167e6dcd8767b747dd5(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"dsf", "t"};
s->PrepareSlots(s_names);
auto v26448 = ([&]() -> Value { auto v26449 = ([&]() -> Value { auto v26450 = ([&]() -> Value { auto v26451 = s->Captured("day"); return Binary("Add", v26451, Value(int64_t{1})); }()); return Binary("Sub", v26450, ([&]() -> Value { auto fn26452 = s->Global("int"); Arguments args26453; args26453.Add(([&]() -> Value { auto fn26454 = PrepareDictionaryGet(s->LocalAt(1)); Arguments args26455; args26455.positional.reserve(2); args26455.Add(Value("placed_day"), false); args26455.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn26454, std::move(args26455)); }()), false); return Call(c, fn26452, std::move(args26453)); }())); }()); return Binary("Sub", v26449, Value(int64_t{6})); }());
s->SetAt(0, v26448);
return ([&]() -> Value { auto v26456 = ([&]() -> Value { auto v26457 = s->LocalAt(0); Value v26458; v26458 = Value(int64_t{0}); if (!static_cast<bool>(Binary("GtE", v26457, v26458))) return Value(false); v26457 = v26458; return Value(true); }()); if (!static_cast<bool>(v26456)) return v26456; v26456 = ([&]() -> Value { auto v26459 = ([&]() -> Value { auto v26461 = s->LocalAt(0); return Binary("Mod", v26461, Value(int64_t{3})); }()); Value v26460; v26460 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v26459, v26460))) return Value(false); v26459 = v26460; return Value(true); }()); return v26456; }());
return {};
}
}  // namespace kagg::opponents::compiled
