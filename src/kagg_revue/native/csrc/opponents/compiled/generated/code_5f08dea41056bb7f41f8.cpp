// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_5f08dea41056bb7f41f8(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"idx", "self"};
s->PrepareSlots(s_names);
return (static_cast<bool>(([&]() -> Value { auto v393 = s->LocalAt(0); Value v394; v394 = ([&]() -> Value { auto fn395 = s->Global("len"); Arguments args396; args396.Add(Attribute(s->LocalAt(1), "invs"), false); return Call(c, fn395, std::move(args396)); }()); if (!static_cast<bool>(Binary("Lt", v393, v394))) return Value(false); v393 = v394; return Value(true); }())) ? Get(Attribute(s->LocalAt(1), "invs"), s->LocalAt(0)) : ([&]() -> Value { auto dict397 = Dict(); return dict397; }()));
return {};
}
}  // namespace kagg::opponents::compiled
