// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_0c29da4c75e9b27ed1ec(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"native", "obs", "offset", "step"};
s->PrepareSlots(s_names);
auto v11476 = ([&]() -> Value { auto v11477 = ([&]() -> Value { auto fn11478 = s->Global("int"); Arguments args11479; args11479.Add(Get(s->LocalAt(1), Value("step")), false); return Call(c, fn11478, std::move(args11479)); }()); return Binary("Add", v11477, s->LocalAt(2)); }());
s->SetAt(3, v11476);
auto v11480 = Get(Attribute(Attribute(s->Global("_IMPL"), "chassis"), "players"), ([&]() -> Value { auto fn11481 = s->Global("int"); Arguments args11482; args11482.Add(Get(s->LocalAt(1), Value("player")), false); return Call(c, fn11481, std::move(args11482)); }()));
s->SetAt(0, v11480);
return Get(Get(Attribute(Attribute(s->Global("_IMPL"), "chassis"), "routes"), (static_cast<bool>(([&]() -> Value { auto v11483 = s->LocalAt(3); Value v11484; v11484 = Value(int64_t{648}); if (!static_cast<bool>(Binary("GtE", v11483, v11484))) return Value(false); v11483 = v11484; return Value(true); }())) ? Value(int64_t{2}) : Get(s->LocalAt(0), Value("route")))), s->LocalAt(3));
return {};
}
}  // namespace kagg::opponents::compiled
