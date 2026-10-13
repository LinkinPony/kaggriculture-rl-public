// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_1dfb4d95eea31b59fc17(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"end", "start", "tx", "ty", "x", "y"};
s->PrepareSlots(s_names);
auto v3111 = s->LocalAt(1);
auto unpack3112 = Iterate(v3111);
ValidateUnpack(unpack3112, 2, false);
s->SetAt(4, unpack3112.at(0));
s->SetAt(5, unpack3112.at(1));
auto v3113 = s->LocalAt(0);
auto unpack3114 = Iterate(v3113);
ValidateUnpack(unpack3114, 2, false);
s->SetAt(2, unpack3114.at(0));
s->SetAt(3, unpack3114.at(1));
return ([&]() -> Value { auto v3115 = ([&]() -> Value { auto v3116 = ([&]() -> Value { auto v3117 = ([&]() -> Value { auto v3118 = List({List({Value("EAST")})}); return Binary("Mult", v3118, ([&]() -> Value { auto fn3119 = s->Global("max"); Arguments args3120; args3120.positional.reserve(2); args3120.Add(Value(int64_t{0}), false); args3120.Add(([&]() -> Value { auto v3121 = s->LocalAt(2); return Binary("Sub", v3121, s->LocalAt(4)); }()), false); return Call(c, fn3119, std::move(args3120)); }())); }()); return Binary("Add", v3117, ([&]() -> Value { auto v3122 = List({List({Value("WEST")})}); return Binary("Mult", v3122, ([&]() -> Value { auto fn3123 = s->Global("max"); Arguments args3124; args3124.positional.reserve(2); args3124.Add(Value(int64_t{0}), false); args3124.Add(([&]() -> Value { auto v3125 = s->LocalAt(4); return Binary("Sub", v3125, s->LocalAt(2)); }()), false); return Call(c, fn3123, std::move(args3124)); }())); }())); }()); return Binary("Add", v3116, ([&]() -> Value { auto v3126 = List({List({Value("SOUTH")})}); return Binary("Mult", v3126, ([&]() -> Value { auto fn3127 = s->Global("max"); Arguments args3128; args3128.positional.reserve(2); args3128.Add(Value(int64_t{0}), false); args3128.Add(([&]() -> Value { auto v3129 = s->LocalAt(3); return Binary("Sub", v3129, s->LocalAt(5)); }()), false); return Call(c, fn3127, std::move(args3128)); }())); }())); }()); return Binary("Add", v3115, ([&]() -> Value { auto v3130 = List({List({Value("NORTH")})}); return Binary("Mult", v3130, ([&]() -> Value { auto fn3131 = s->Global("max"); Arguments args3132; args3132.positional.reserve(2); args3132.Add(Value(int64_t{0}), false); args3132.Add(([&]() -> Value { auto v3133 = s->LocalAt(5); return Binary("Sub", v3133, s->LocalAt(3)); }()), false); return Call(c, fn3131, std::move(args3132)); }())); }())); }());
return {};
}
}  // namespace kagg::opponents::compiled
