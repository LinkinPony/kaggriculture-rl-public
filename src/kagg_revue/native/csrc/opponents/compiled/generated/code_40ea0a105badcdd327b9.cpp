// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_40ea0a105badcdd327b9(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"order"};
s->PrepareSlots(s_names);
return ([&]() -> Value { auto v3019 = Unary("USub", ([&]() -> Value { auto fn3020 = s->Global("int"); Arguments args3021; args3021.Add(([&]() -> Value { auto fn3022 = PrepareDictionaryGet(s->Captured("prices")); Arguments args3023; args3023.positional.reserve(2); args3023.Add(Get(s->LocalAt(0), Value(int64_t{1})), false); args3023.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn3022, std::move(args3023)); }()), false); return Call(c, fn3020, std::move(args3021)); }())); return Binary("Mult", v3019, Get(s->LocalAt(0), Value(int64_t{2}))); }());
return {};
}
}  // namespace kagg::opponents::compiled
