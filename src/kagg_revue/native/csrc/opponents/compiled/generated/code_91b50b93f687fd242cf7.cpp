// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_91b50b93f687fd242cf7(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"default", "getter", "key", "value"};
s->PrepareSlots(s_names);
if (static_cast<bool>(([&]() -> Value { auto fn50 = s->Global("isinstance"); Arguments args51; args51.positional.reserve(2); args51.Add(s->LocalAt(3), false); args51.Add(s->Global("dict"), false); return Call(c, fn50, std::move(args51)); }()))) {
return ([&]() -> Value { auto fn52 = PrepareDictionaryGet(s->LocalAt(3)); Arguments args53; args53.positional.reserve(2); args53.Add(s->LocalAt(2), false); args53.Add(s->LocalAt(0), false); return CallDictionaryGet(c, fn52, std::move(args53)); }());
}
auto v54 = ([&]() -> Value { auto fn55 = s->Global("getattr"); Arguments args56; args56.positional.reserve(3); args56.Add(s->LocalAt(3), false); args56.Add(Value("get"), false); args56.Add(Value{}, false); return Call(c, fn55, std::move(args56)); }());
s->SetAt(1, v54);
if (static_cast<bool>(([&]() -> Value { auto fn57 = s->Global("callable"); Arguments args58; args58.Add(s->LocalAt(1), false); return Call(c, fn57, std::move(args58)); }()))) {
return ([&]() -> Value { auto fn59 = s->LocalAt(1); Arguments args60; args60.positional.reserve(2); args60.Add(s->LocalAt(2), false); args60.Add(s->LocalAt(0), false); return Call(c, fn59, std::move(args60)); }());
}
return ([&]() -> Value { auto fn61 = s->Global("getattr"); Arguments args62; args62.positional.reserve(3); args62.Add(s->LocalAt(3), false); args62.Add(s->LocalAt(2), false); args62.Add(s->LocalAt(0), false); return Call(c, fn61, std::move(args62)); }());
return {};
}
}  // namespace kagg::opponents::compiled
