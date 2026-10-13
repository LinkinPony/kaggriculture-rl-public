// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_15002331ccaad0224650(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"native", "seat", "t", "tape"};
s->PrepareSlots(s_names);
auto v23355 = ([&]() -> Value { auto fn23356 = PrepareDictionaryGet(Attribute(Attribute(s->Global("_IMPL"), "chassis"), "players")); Arguments args23357; args23357.Add(s->LocalAt(1), false); return CallDictionaryGet(c, fn23356, std::move(args23357)); }());
s->SetAt(0, v23355);
if (static_cast<bool>(([&]() -> Value { auto v23358 = Unary("Not", s->LocalAt(0)); if (static_cast<bool>(v23358)) return v23358; v23358 = ([&]() -> Value { auto v23359 = s->LocalAt(2); Value v23360; v23360 = Value(int64_t{719}); if (!static_cast<bool>(Binary("Gt", v23359, v23360))) return Value(false); v23359 = v23360; return Value(true); }()); return v23358; }()))) {
return ([&]() -> Value { auto dict23361 = Dict(); return dict23361; }());
}
auto v23362 = Get(Attribute(Attribute(s->Global("_IMPL"), "chassis"), "routes"), (static_cast<bool>(([&]() -> Value { auto v23363 = s->LocalAt(2); Value v23364; v23364 = Value(int64_t{648}); if (!static_cast<bool>(Binary("GtE", v23363, v23364))) return Value(false); v23363 = v23364; return Value(true); }())) ? Value(int64_t{2}) : Get(s->LocalAt(0), Value("route"))));
s->SetAt(3, v23362);
return (static_cast<bool>(([&]() -> Value { auto v23365 = ([&]() -> Value { auto v23366 = s->LocalAt(2); Value v23367; v23367 = ([&]() -> Value { auto fn23368 = s->Global("len"); Arguments args23369; args23369.Add(s->LocalAt(3), false); return Call(c, fn23368, std::move(args23369)); }()); if (!static_cast<bool>(Binary("Lt", v23366, v23367))) return Value(false); v23366 = v23367; return Value(true); }()); if (!static_cast<bool>(v23365)) return v23365; v23365 = ([&]() -> Value { auto fn23370 = s->Global("isinstance"); Arguments args23371; args23371.positional.reserve(2); args23371.Add(Get(s->LocalAt(3), s->LocalAt(2)), false); args23371.Add(s->Global("dict"), false); return Call(c, fn23370, std::move(args23371)); }()); return v23365; }())) ? Get(s->LocalAt(3), s->LocalAt(2)) : ([&]() -> Value { auto dict23372 = Dict(); return dict23372; }()));
return {};
}
}  // namespace kagg::opponents::compiled
