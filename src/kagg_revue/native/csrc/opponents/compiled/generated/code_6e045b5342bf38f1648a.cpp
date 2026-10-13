// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_6e045b5342bf38f1648a(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"o"};
s->PrepareSlots(s_names);
return ([&]() -> Value { auto v3973 = Unary("USub", ([&]() -> Value { auto fn3974 = PrepareDictionaryGet(Attribute(s->Captured("view"), "prices")); Arguments args3975; args3975.positional.reserve(2); args3975.Add(Get(s->LocalAt(0), Value(int64_t{1})), false); args3975.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn3974, std::move(args3975)); }())); return Binary("Mult", v3973, Get(s->LocalAt(0), Value(int64_t{2}))); }());
return {};
}
}  // namespace kagg::opponents::compiled
