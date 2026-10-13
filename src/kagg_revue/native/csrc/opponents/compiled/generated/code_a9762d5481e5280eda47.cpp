// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_a9762d5481e5280eda47(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"i"};
s->PrepareSlots(s_names);
return Tuple({([&]() -> Value { auto v3799 = ([&]() -> Value { auto fn3800 = PrepareDictionaryGet(s->Captured("prices")); Arguments args3801; args3801.positional.reserve(2); args3801.Add(s->LocalAt(0), false); args3801.Add(Value(int64_t{1}), false); return CallDictionaryGet(c, fn3800, std::move(args3801)); }()); return Binary("Mult", v3799, ([&]() -> Value { auto fn3802 = s->Global("min"); Arguments args3803; args3803.positional.reserve(2); args3803.Add(Get(s->Captured("inv"), s->LocalAt(0)), false); args3803.Add(s->Captured("room"), false); return Call(c, fn3802, std::move(args3803)); }())); }()), Unary("USub", ([&]() -> Value { auto fn3804 = Attribute(s->Global("PRODUCTS"), "index"); Arguments args3805; args3805.Add(s->LocalAt(0), false); return Call(c, fn3804, std::move(args3805)); }()))});
return {};
}
}  // namespace kagg::opponents::compiled
