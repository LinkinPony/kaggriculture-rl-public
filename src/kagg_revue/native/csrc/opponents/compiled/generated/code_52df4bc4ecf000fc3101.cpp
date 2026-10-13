// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_52df4bc4ecf000fc3101(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action"};
s->PrepareSlots(s_names);
return ([&]() -> Value { Arguments args11469; args11469.Add(([&]() -> Value { auto v11470 = ([&]() -> Value { auto fn11471 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args11472; args11472.Add(Value("farmer"), false); return CallDictionaryGet(c, fn11471, std::move(args11472)); }()); if (static_cast<bool>(v11470)) return v11470; v11470 = List({Value("PASS")}); return v11470; }()), false); args11469.Add(([&]() -> Value { auto v11473 = ([&]() -> Value { auto fn11474 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args11475; args11475.Add(Value("hands"), false); return CallDictionaryGet(c, fn11474, std::move(args11475)); }()); if (static_cast<bool>(v11473)) return v11473; v11473 = List({}); return v11473; }()), true); return List(std::move(args11469.positional)); }());
return {};
}
}  // namespace kagg::opponents::compiled
