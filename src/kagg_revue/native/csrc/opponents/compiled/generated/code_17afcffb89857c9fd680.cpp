// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_17afcffb89857c9fd680(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"o"};
s->PrepareSlots(s_names);
return ([&]() -> Value { auto v2005 = Unary("USub", ([&]() -> Value { auto fn2006 = PrepareDictionaryGet(Attribute(s->Captured("view"), "prices")); Arguments args2007; args2007.positional.reserve(2); args2007.Add(Get(s->LocalAt(0), Value(int64_t{1})), false); args2007.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn2006, std::move(args2007)); }())); return Binary("Mult", v2005, Get(s->LocalAt(0), Value(int64_t{2}))); }());
return {};
}
}  // namespace kagg::opponents::compiled
