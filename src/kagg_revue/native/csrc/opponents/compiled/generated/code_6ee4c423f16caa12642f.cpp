// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_6ee4c423f16caa12642f(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"a", "animal", "day"};
s->PrepareSlots(s_names);
auto v2120 = Get(s->Global("ANIMALS"), s->LocalAt(1));
s->SetAt(0, v2120);
return ([&]() -> Value { auto dict2121 = Dict(); auto key2122 = Value("kind"); Put(dict2121, key2122, Get(s->LocalAt(0), Value("structure"))); auto key2123 = Value("animal"); Put(dict2121, key2123, s->LocalAt(1)); auto key2124 = Value("placed_day"); Put(dict2121, key2124, s->LocalAt(2)); auto key2125 = Value("yield_units"); Put(dict2121, key2125, Value(int64_t{0})); auto key2126 = Value("consecutive_unfed"); Put(dict2121, key2126, Value(int64_t{0})); auto key2127 = Value("fed_today"); Put(dict2121, key2127, Value(false)); auto key2128 = Value("cared_today"); Put(dict2121, key2128, Value(false)); auto key2129 = Value("fertilizer_available"); Put(dict2121, key2129, Value(false)); auto key2130 = Value("pending_care_bonus"); Put(dict2121, key2130, Value(int64_t{0})); return dict2121; }());
return {};
}
}  // namespace kagg::opponents::compiled
