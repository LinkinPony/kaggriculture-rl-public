// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_3209e188f8a0bd920454(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"kv"};
s->PrepareSlots(s_names);
return ([&]() -> Value { auto v20822 = Unary("USub", ([&]() -> Value { auto fn20823 = s->Global("int"); Arguments args20824; args20824.Add(([&]() -> Value { auto fn20825 = PrepareDictionaryGet(s->Captured("prices")); Arguments args20826; args20826.positional.reserve(2); args20826.Add(Get(s->LocalAt(0), Value(int64_t{0})), false); args20826.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn20825, std::move(args20826)); }()), false); return Call(c, fn20823, std::move(args20824)); }())); return Binary("Mult", v20822, Get(s->LocalAt(0), Value(int64_t{1}))); }());
return {};
}
}  // namespace kagg::opponents::compiled
