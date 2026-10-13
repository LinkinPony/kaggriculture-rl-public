// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_85d5ef60b1b7a09a1eaa(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "obs", "state"};
s->PrepareSlots(s_names);
if (static_cast<bool>(([&]() -> Value { auto v31175 = ([&]() -> Value { auto v31177 = ([&]() -> Value { auto fn31178 = s->Global("int"); Arguments args31179; args31179.Add(Get(s->LocalAt(1), Value("step")), false); return Call(c, fn31178, std::move(args31179)); }()); return Binary("FloorDiv", v31177, Value(int64_t{24})); }()); Value v31176; v31176 = Value(int64_t{29}); if (!static_cast<bool>(Binary("Eq", v31175, v31176))) return Value(false); v31175 = v31176; return Value(true); }()))) {
return s->LocalAt(0);
}
return ([&]() -> Value { auto fn31180 = s->Global("_VT_RESCUE"); Arguments args31181; args31181.positional.reserve(3); args31181.Add(s->LocalAt(1), false); args31181.Add(s->LocalAt(0), false); args31181.Add(s->LocalAt(2), false); return Call(c, fn31180, std::move(args31181)); }());
return {};
}
}  // namespace kagg::opponents::compiled
