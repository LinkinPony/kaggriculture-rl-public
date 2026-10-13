// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_f91c98efad5435140892(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"cd", "crop", "day", "turns_per_day"};
s->PrepareSlots(s_names);
auto v2107 = Get(s->Global("CROPS"), s->LocalAt(1));
s->SetAt(0, v2107);
return ([&]() -> Value { auto dict2108 = Dict(); auto key2109 = Value("kind"); Put(dict2108, key2109, Value("PLANT")); auto key2110 = Value("crop"); Put(dict2108, key2110, s->LocalAt(1)); auto key2111 = Value("planted_day"); Put(dict2108, key2111, s->LocalAt(2)); auto key2112 = Value("watered_today"); Put(dict2108, key2112, Value(false)); auto key2113 = Value("consecutive_unwatered"); Put(dict2108, key2113, Value(int64_t{1})); auto key2114 = Value("yield_units"); Put(dict2108, key2114, (static_cast<bool>(Get(s->LocalAt(0), Value("ongoing"))) ? Value(int64_t{0}) : Value(int64_t{1}))); auto key2115 = Value("max_lifespan_step"); Put(dict2108, key2115, (static_cast<bool>(Get(s->LocalAt(0), Value("ongoing"))) ? Unary("USub", Value(int64_t{1})) : ([&]() -> Value { auto v2116 = ([&]() -> Value { auto v2117 = ([&]() -> Value { auto v2118 = s->LocalAt(2); return Binary("Add", v2118, Get(s->LocalAt(0), Value("max_yield_day"))); }()); return Binary("Add", v2117, Value(int64_t{1})); }()); return Binary("Mult", v2116, s->LocalAt(3)); }()))); auto key2119 = Value("fertilized_until_day"); Put(dict2108, key2119, Unary("USub", Value(int64_t{1}))); return dict2108; }());
return {};
}
}  // namespace kagg::opponents::compiled
