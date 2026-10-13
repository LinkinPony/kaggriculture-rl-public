// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_b83ebc203f559a5139f0(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "n"};
s->PrepareSlots(s_names);
return Tuple({([&]() -> Value { auto fn3695 = s->Global("_commands"); Arguments args3696; args3696.positional.reserve(2); args3696.Add(s->LocalAt(0), false); args3696.Add(s->LocalAt(1), false); return Call(c, fn3695, std::move(args3696)); }()), ([&]() -> Value { auto fn3697 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args3698; args3698.positional.reserve(2); args3698.Add(Value("market"), false); args3698.Add(List({}), false); return CallDictionaryGet(c, fn3697, std::move(args3698)); }())});
return {};
}
}  // namespace kagg::opponents::compiled
