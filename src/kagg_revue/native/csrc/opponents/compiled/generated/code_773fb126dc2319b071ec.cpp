// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_773fb126dc2319b071ec(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"_", "a", "b", "n"};
s->PrepareSlots(s_names);
auto v66 = Tuple({Value(int64_t{1}), Value(int64_t{1})});
auto unpack67 = Iterate(v66);
ValidateUnpack(unpack67, 2, false);
s->SetAt(1, unpack67.at(0));
s->SetAt(2, unpack67.at(1));
for (const auto& item68 : Iterate(([&]() -> Value { auto fn69 = s->Global("range"); Arguments args70; args70.Add(s->LocalAt(3), false); return Call(c, fn69, std::move(args70)); }()))) {
s->SetAt(0, item68);
auto v71 = Tuple({s->LocalAt(2), ([&]() -> Value { auto v72 = s->LocalAt(1); return Binary("Add", v72, s->LocalAt(2)); }())});
auto unpack73 = Iterate(v71);
ValidateUnpack(unpack73, 2, false);
s->SetAt(1, unpack73.at(0));
s->SetAt(2, unpack73.at(1));
}
return s->LocalAt(1);
return {};
}
}  // namespace kagg::opponents::compiled
