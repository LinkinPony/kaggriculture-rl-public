// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_d1b24a55d6b8f3e8d9c5(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"route", "self", "step", "tape"};
s->PrepareSlots(s_names);
auto v466 = Get(Attribute(s->LocalAt(1), "routes"), s->LocalAt(0));
s->SetAt(3, v466);
if (static_cast<bool>(([&]() -> Value { auto v467 = ([&]() -> Value { auto v468 = Value(int64_t{0}); Value v469; v469 = s->LocalAt(2); if (!static_cast<bool>(Binary("LtE", v468, v469))) return Value(false); v468 = v469; v469 = ([&]() -> Value { auto fn470 = s->Global("len"); Arguments args471; args471.Add(s->LocalAt(3), false); return Call(c, fn470, std::move(args471)); }()); if (!static_cast<bool>(Binary("Lt", v468, v469))) return Value(false); v468 = v469; return Value(true); }()); if (!static_cast<bool>(v467)) return v467; v467 = ([&]() -> Value { auto fn472 = s->Global("isinstance"); Arguments args473; args473.positional.reserve(2); args473.Add(Get(s->LocalAt(3), s->LocalAt(2)), false); args473.Add(s->Global("dict"), false); return Call(c, fn472, std::move(args473)); }()); return v467; }()))) {
return ([&]() -> Value { auto fn474 = Attribute(s->Global("copy"), "deepcopy"); Arguments args475; args475.Add(Get(s->LocalAt(3), s->LocalAt(2)), false); return Call(c, fn474, std::move(args475)); }());
}
return ([&]() -> Value { auto fn476 = Attribute(s->Global("copy"), "deepcopy"); Arguments args477; args477.Add(s->Global("PASS_ACTION"), false); return Call(c, fn476, std::move(args477)); }());
return {};
}
}  // namespace kagg::opponents::compiled
