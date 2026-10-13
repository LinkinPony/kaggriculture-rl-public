// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_44fefeb8690d12224809(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"_", "a", "b", "n"};
s->PrepareSlots(s_names);
auto v19714 = Tuple({Value(int64_t{1}), Value(int64_t{1})});
auto unpack19715 = Iterate(v19714);
ValidateUnpack(unpack19715, 2, false);
s->SetAt(1, unpack19715.at(0));
s->SetAt(2, unpack19715.at(1));
for (const auto& item19716 : Iterate(([&]() -> Value { auto fn19717 = s->Global("range"); Arguments args19718; args19718.Add(s->LocalAt(3), false); return Call(c, fn19717, std::move(args19718)); }()))) {
s->SetAt(0, item19716);
auto v19719 = Tuple({s->LocalAt(2), ([&]() -> Value { auto v19720 = s->LocalAt(1); return Binary("Add", v19720, s->LocalAt(2)); }())});
auto unpack19721 = Iterate(v19719);
ValidateUnpack(unpack19721, 2, false);
s->SetAt(1, unpack19721.at(0));
s->SetAt(2, unpack19721.at(1));
}
return s->LocalAt(1);
return {};
}
}  // namespace kagg::opponents::compiled
