// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_99ea796892e627acf0ec(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"p"};
s->PrepareSlots(s_names);
return Unary("USub", ([&]() -> Value { auto fn8351 = PrepareDictionaryGet(Get(Get(s->Captured("obs"), Value("market")), Value("prices"))); Arguments args8352; args8352.positional.reserve(2); args8352.Add(s->LocalAt(0), false); args8352.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn8351, std::move(args8352)); }()));
return {};
}
}  // namespace kagg::opponents::compiled
