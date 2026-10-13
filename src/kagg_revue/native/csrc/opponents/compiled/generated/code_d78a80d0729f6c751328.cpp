// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_d78a80d0729f6c751328(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"o"};
s->PrepareSlots(s_names);
return ([&]() -> Value { auto v1719 = Unary("USub", ([&]() -> Value { auto fn1720 = PrepareDictionaryGet(Attribute(s->Captured("view"), "prices")); Arguments args1721; args1721.positional.reserve(2); args1721.Add(Get(s->LocalAt(0), Value(int64_t{1})), false); args1721.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn1720, std::move(args1721)); }())); return Binary("Mult", v1719, Get(s->LocalAt(0), Value(int64_t{2}))); }());
return {};
}
}  // namespace kagg::opponents::compiled
