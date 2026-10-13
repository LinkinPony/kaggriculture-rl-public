// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_f7b71e07c7aa3e67e857(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"pos", "tiles", "x", "y"};
s->PrepareSlots(s_names);
try {
auto v108 = Tuple({([&]() -> Value { auto fn109 = s->Global("int"); Arguments args110; args110.Add(Get(s->LocalAt(0), Value(int64_t{0})), false); return Call(c, fn109, std::move(args110)); }()), ([&]() -> Value { auto fn111 = s->Global("int"); Arguments args112; args112.Add(Get(s->LocalAt(0), Value(int64_t{1})), false); return Call(c, fn111, std::move(args112)); }())});
auto unpack113 = Iterate(v108);
ValidateUnpack(unpack113, 2, false);
s->SetAt(2, unpack113.at(0));
s->SetAt(3, unpack113.at(1));
return Get(Get(s->LocalAt(1), s->LocalAt(3)), s->LocalAt(2));
} catch (const Error& error107) {
if (Matches(error107, Tuple({s->Global("TypeError"), s->Global("ValueError"), s->Global("IndexError")}))) {
return Value("LOCKED");
}
else { throw; }
}
return {};
}
}  // namespace kagg::opponents::compiled
