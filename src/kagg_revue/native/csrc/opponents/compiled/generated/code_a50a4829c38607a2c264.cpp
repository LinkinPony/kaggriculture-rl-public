// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_a50a4829c38607a2c264(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"order"};
s->PrepareSlots(s_names);
return ([&]() -> Value { auto v16883 = Unary("USub", ([&]() -> Value { auto fn16884 = s->Global("int"); Arguments args16885; args16885.Add(([&]() -> Value { auto fn16886 = PrepareDictionaryGet(s->Captured("prices")); Arguments args16887; args16887.positional.reserve(2); args16887.Add(Get(s->LocalAt(0), Value(int64_t{1})), false); args16887.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn16886, std::move(args16887)); }()), false); return Call(c, fn16884, std::move(args16885)); }())); return Binary("Mult", v16883, Get(s->LocalAt(0), Value(int64_t{2}))); }());
return {};
}
}  // namespace kagg::opponents::compiled
