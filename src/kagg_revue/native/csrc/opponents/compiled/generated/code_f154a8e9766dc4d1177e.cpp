// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_f154a8e9766dc4d1177e(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"shops"};
s->PrepareSlots(s_names);
return ([&]() -> Value { auto v27817 = ([&]() -> Value { auto fn27818 = s->Global("_E361_PAIR"); Arguments args27819; args27819.Add(s->LocalAt(0), false); return Call(c, fn27818, std::move(args27819)); }()); return Binary("Add", v27817, ([&]() -> Value { auto fn27820 = PrepareDictionaryGet(s->Global("_E361_LIB")); Arguments args27821; args27821.positional.reserve(2); args27821.Add(([&]() -> Value { auto fn27822 = s->Global("tuple"); Arguments args27823; args27823.Add(s->LocalAt(0), false); return Call(c, fn27822, std::move(args27823)); }()), false); args27821.Add(List({}), false); return CallDictionaryGet(c, fn27820, std::move(args27821)); }())); }());
return {};
}
}  // namespace kagg::opponents::compiled
