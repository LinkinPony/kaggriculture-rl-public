// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_326b75b51373e8ec408a(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action"};
s->PrepareSlots(s_names);
return ([&]() -> Value { Arguments args15410; args15410.Add(([&]() -> Value { auto v15411 = ([&]() -> Value { auto fn15412 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args15413; args15413.Add(Value("farmer"), false); return CallDictionaryGet(c, fn15412, std::move(args15413)); }()); if (static_cast<bool>(v15411)) return v15411; v15411 = List({Value("PASS")}); return v15411; }()), false); args15410.Add(([&]() -> Value { auto v15414 = ([&]() -> Value { auto fn15415 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args15416; args15416.Add(Value("hands"), false); return CallDictionaryGet(c, fn15415, std::move(args15416)); }()); if (static_cast<bool>(v15414)) return v15414; v15414 = List({}); return v15414; }()), true); return List(std::move(args15410.positional)); }());
return {};
}
}  // namespace kagg::opponents::compiled
