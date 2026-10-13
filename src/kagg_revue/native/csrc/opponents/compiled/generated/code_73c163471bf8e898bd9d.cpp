// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_73c163471bf8e898bd9d(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"observation", "raw"};
s->PrepareSlots(s_names);
auto v74 = ([&]() -> Value { auto fn75 = s->Global("_get"); Arguments args76; args76.positional.reserve(2); args76.Add(s->LocalAt(0), false); args76.Add(Value("step"), false); return Call(c, fn75, std::move(args76)); }());
s->SetAt(1, v74);
if (static_cast<bool>(([&]() -> Value { auto v77 = s->LocalAt(1); Value v78; v78 = Value{}; if (!static_cast<bool>(Binary("IsNot", v77, v78))) return Value(false); v77 = v78; return Value(true); }()))) {
return ([&]() -> Value { auto fn79 = s->Global("_int"); Arguments args80; args80.Add(s->LocalAt(1), false); return Call(c, fn79, std::move(args80)); }());
}
return ([&]() -> Value { auto v81 = ([&]() -> Value { auto v82 = ([&]() -> Value { auto fn83 = s->Global("_int"); Arguments args84; args84.Add(([&]() -> Value { auto fn85 = s->Global("_get"); Arguments args86; args86.positional.reserve(3); args86.Add(s->LocalAt(0), false); args86.Add(Value("day"), false); args86.Add(Value(int64_t{0}), false); return Call(c, fn85, std::move(args86)); }()), false); return Call(c, fn83, std::move(args84)); }()); return Binary("Mult", v82, Value(int64_t{24})); }()); return Binary("Add", v81, ([&]() -> Value { auto fn87 = s->Global("_int"); Arguments args88; args88.Add(([&]() -> Value { auto fn89 = s->Global("_get"); Arguments args90; args90.positional.reserve(3); args90.Add(s->LocalAt(0), false); args90.Add(Value("hour"), false); args90.Add(Value(int64_t{0}), false); return Call(c, fn89, std::move(args90)); }()), false); return Call(c, fn87, std::move(args88)); }())); }());
return {};
}
}  // namespace kagg::opponents::compiled
