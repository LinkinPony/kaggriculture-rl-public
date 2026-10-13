// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_902364d2b0fcbf62ad99(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"config", "obs"};
s->PrepareSlots(s_names);
if (static_cast<bool>(([&]() -> Value { auto fn5145 = PrepareDictionaryGet(([&]() -> Value { auto fn5147 = PrepareDictionaryGet(s->Global("_V219_STATES")); Arguments args5148; args5148.positional.reserve(2); args5148.Add(([&]() -> Value { auto fn5149 = s->Global("int"); Arguments args5150; args5150.Add(Get(s->LocalAt(1), Value("player")), false); return Call(c, fn5149, std::move(args5150)); }()), false); args5148.Add(([&]() -> Value { auto dict5151 = Dict(); return dict5151; }()), false); return CallDictionaryGet(c, fn5147, std::move(args5148)); }())); Arguments args5146; args5146.Add(Value("committed"), false); return CallDictionaryGet(c, fn5145, std::move(args5146)); }()))) {
return Value{};
}
return ([&]() -> Value { auto fn5152 = s->Global("_ORIGINAL_SHADOW_TERMINAL"); Arguments args5153; args5153.positional.reserve(2); args5153.Add(s->LocalAt(1), false); args5153.Add(s->LocalAt(0), false); return Call(c, fn5152, std::move(args5153)); }());
return {};
}
}  // namespace kagg::opponents::compiled
