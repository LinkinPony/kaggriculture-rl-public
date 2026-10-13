// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_b722cb8fcb19df79be89(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"p"};
s->PrepareSlots(s_names);
return Tuple({([&]() -> Value { auto v26417 = ([&]() -> Value { auto fn26418 = s->Global("abs"); Arguments args26419; args26419.Add(([&]() -> Value { auto v26420 = Get(s->Captured("pos"), Value(int64_t{0})); return Binary("Sub", v26420, Get(s->LocalAt(0), Value(int64_t{0}))); }()), false); return Call(c, fn26418, std::move(args26419)); }()); return Binary("Add", v26417, ([&]() -> Value { auto fn26421 = s->Global("abs"); Arguments args26422; args26422.Add(([&]() -> Value { auto v26423 = Get(s->Captured("pos"), Value(int64_t{1})); return Binary("Sub", v26423, Get(s->LocalAt(0), Value(int64_t{1}))); }()), false); return Call(c, fn26421, std::move(args26422)); }())); }()), s->LocalAt(0)});
return {};
}
}  // namespace kagg::opponents::compiled
