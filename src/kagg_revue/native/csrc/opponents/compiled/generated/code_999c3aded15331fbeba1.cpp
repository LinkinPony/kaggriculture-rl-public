// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_999c3aded15331fbeba1(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"config", "obs"};
s->PrepareSlots(s_names);
if (static_cast<bool>(([&]() -> Value { auto fn7450 = PrepareDictionaryGet(([&]() -> Value { auto fn7452 = PrepareDictionaryGet(s->Global("_V233_STATES")); Arguments args7453; args7453.positional.reserve(2); args7453.Add(([&]() -> Value { auto fn7454 = s->Global("int"); Arguments args7455; args7455.Add(Get(s->LocalAt(1), Value("player")), false); return Call(c, fn7454, std::move(args7455)); }()), false); args7453.Add(([&]() -> Value { auto dict7456 = Dict(); return dict7456; }()), false); return CallDictionaryGet(c, fn7452, std::move(args7453)); }())); Arguments args7451; args7451.Add(Value("committed"), false); return CallDictionaryGet(c, fn7450, std::move(args7451)); }()))) {
return Value{};
}
return ([&]() -> Value { auto fn7457 = s->Global("_R46_SHADOW_PARENT"); Arguments args7458; args7458.positional.reserve(2); args7458.Add(s->LocalAt(1), false); args7458.Add(s->LocalAt(0), false); return Call(c, fn7457, std::move(args7458)); }());
return {};
}
}  // namespace kagg::opponents::compiled
