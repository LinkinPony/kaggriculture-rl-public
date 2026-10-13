// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_575620d0e9ae135add8d(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"default", "key", "obj"};
s->PrepareSlots(s_names);
return (static_cast<bool>(([&]() -> Value { auto fn2522 = s->Global("isinstance"); Arguments args2523; args2523.positional.reserve(2); args2523.Add(s->LocalAt(2), false); args2523.Add(s->Global("dict"), false); return Call(c, fn2522, std::move(args2523)); }())) ? ([&]() -> Value { auto fn2524 = PrepareDictionaryGet(s->LocalAt(2)); Arguments args2525; args2525.positional.reserve(2); args2525.Add(s->LocalAt(1), false); args2525.Add(s->LocalAt(0), false); return CallDictionaryGet(c, fn2524, std::move(args2525)); }()) : ([&]() -> Value { auto fn2526 = s->Global("getattr"); Arguments args2527; args2527.positional.reserve(3); args2527.Add(s->LocalAt(2), false); args2527.Add(s->LocalAt(1), false); args2527.Add(s->LocalAt(0), false); return Call(c, fn2526, std::move(args2527)); }()));
return {};
}
}  // namespace kagg::opponents::compiled
