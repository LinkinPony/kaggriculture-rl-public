// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_43905c1ed9495daf0cc1(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"_", "a", "b", "n"};
s->PrepareSlots(s_names);
auto v4364 = Tuple({Value(int64_t{1}), Value(int64_t{1})});
auto unpack4365 = Iterate(v4364);
ValidateUnpack(unpack4365, 2, false);
s->SetAt(1, unpack4365.at(0));
s->SetAt(2, unpack4365.at(1));
for (const auto& item4366 : Iterate(([&]() -> Value { auto fn4367 = s->Global("range"); Arguments args4368; args4368.Add(s->LocalAt(3), false); return Call(c, fn4367, std::move(args4368)); }()))) {
s->SetAt(0, item4366);
auto v4369 = Tuple({s->LocalAt(2), ([&]() -> Value { auto v4370 = s->LocalAt(1); return Binary("Add", v4370, s->LocalAt(2)); }())});
auto unpack4371 = Iterate(v4369);
ValidateUnpack(unpack4371, 2, false);
s->SetAt(1, unpack4371.at(0));
s->SetAt(2, unpack4371.at(1));
}
return s->LocalAt(1);
return {};
}
}  // namespace kagg::opponents::compiled
