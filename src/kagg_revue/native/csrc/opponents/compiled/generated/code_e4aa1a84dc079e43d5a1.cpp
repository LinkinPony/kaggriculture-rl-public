// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_e4aa1a84dc079e43d5a1(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"configuration", "observation", "player", "result", "state", "step"};
s->PrepareSlots(s_names);
auto v16319 = ([&]() -> Value { auto fn16320 = s->Global("_R134_PARENT"); Arguments args16321; args16321.positional.reserve(2); args16321.Add(s->LocalAt(1), false); args16321.Add(s->LocalAt(0), false); return Call(c, fn16320, std::move(args16321)); }());
s->SetAt(3, v16319);
try {
auto v16323 = ([&]() -> Value { auto fn16324 = s->Global("int"); Arguments args16325; args16325.Add(Get(s->LocalAt(1), Value("player")), false); return Call(c, fn16324, std::move(args16325)); }());
s->SetAt(2, v16323);
auto v16326 = ([&]() -> Value { auto fn16327 = s->Global("int"); Arguments args16328; args16328.Add(([&]() -> Value { auto fn16329 = PrepareDictionaryGet(s->LocalAt(1)); Arguments args16330; args16330.positional.reserve(2); args16330.Add(Value("step"), false); args16330.Add(([&]() -> Value { auto v16331 = ([&]() -> Value { auto v16332 = Get(s->LocalAt(1), Value("day")); return Binary("Mult", v16332, Value(int64_t{24})); }()); return Binary("Add", v16331, Get(s->LocalAt(1), Value("hour"))); }()), false); return CallDictionaryGet(c, fn16329, std::move(args16330)); }()), false); return Call(c, fn16327, std::move(args16328)); }());
s->SetAt(5, v16326);
auto v16333 = ([&]() -> Value { auto fn16334 = PrepareDictionaryGet(s->Global("_R134_STATES")); Arguments args16335; args16335.Add(s->LocalAt(2), false); return CallDictionaryGet(c, fn16334, std::move(args16335)); }());
s->SetAt(4, v16333);
if (static_cast<bool>(([&]() -> Value { auto v16336 = ([&]() -> Value { auto v16337 = s->LocalAt(4); Value v16338; v16338 = Value{}; if (!static_cast<bool>(Binary("Is", v16337, v16338))) return Value(false); v16337 = v16338; return Value(true); }()); if (static_cast<bool>(v16336)) return v16336; v16336 = ([&]() -> Value { auto v16339 = s->LocalAt(5); Value v16340; v16340 = Get(s->LocalAt(4), Value("step")); if (!static_cast<bool>(Binary("LtE", v16339, v16340))) return Value(false); v16339 = v16340; return Value(true); }()); return v16336; }()))) {
auto v16341 = ([&]() -> Value { auto dict16342 = Dict(); auto key16343 = Value("step"); Put(dict16342, key16343, Unary("USub", Value(int64_t{1}))); return dict16342; }());
s->SetAt(4, v16341);
Put(s->Global("_R134_STATES"), s->LocalAt(2), v16341);
(void)([&]() -> Value { auto fn16344 = Attribute(s->Global("_R134_REPORT"), "update"); Arguments args16345; args16345.Keyword("egg_substitution_requests", Value(int64_t{0})); args16345.Keyword("egg_substitution_confirmed_units", Value(int64_t{0})); args16345.Keyword("egg_substitution_purchase_shortfalls", Value(int64_t{0})); args16345.Keyword("egg_substitution_pickups", Value(int64_t{0})); args16345.Keyword("egg_substitution_coops", Value(int64_t{0})); args16345.Keyword("egg_substitution_placements", Value(int64_t{0})); args16345.Keyword("egg_substitution_completed", Value(int64_t{0})); args16345.Keyword("egg_substitution_aborted", Value(int64_t{0})); args16345.Keyword("egg_substitution_errors", Value(int64_t{0})); return Call(c, fn16344, std::move(args16345)); }());
}
auto v16346 = s->LocalAt(5);
Put(s->LocalAt(4), Value("step"), v16346);
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto fn16347 = s->Global("_r132_standard"); Arguments args16348; args16348.Add(s->LocalAt(0), false); return Call(c, fn16347, std::move(args16348)); }())))) {
return s->LocalAt(3);
}
(void)([&]() -> Value { auto fn16349 = s->Global("_r134_confirm_purchase"); Arguments args16350; args16350.positional.reserve(2); args16350.Add(s->LocalAt(1), false); args16350.Add(s->LocalAt(4), false); return Call(c, fn16349, std::move(args16350)); }());
auto v16351 = ([&]() -> Value { auto fn16352 = s->Global("_r134_commit"); Arguments args16353; args16353.positional.reserve(3); args16353.Add(s->LocalAt(1), false); args16353.Add(s->LocalAt(3), false); args16353.Add(s->LocalAt(4), false); return Call(c, fn16352, std::move(args16353)); }());
s->SetAt(3, v16351);
auto v16354 = ([&]() -> Value { auto fn16355 = s->Global("_r134_physical"); Arguments args16356; args16356.positional.reserve(3); args16356.Add(s->LocalAt(1), false); args16356.Add(s->LocalAt(3), false); args16356.Add(s->LocalAt(4), false); return Call(c, fn16355, std::move(args16356)); }());
s->SetAt(3, v16354);
} catch (const Error& error16322) {
if (Matches(error16322, s->Global("Exception"))) {
auto v16357 = ([&]() -> Value { auto v16358 = ([&]() -> Value { auto fn16359 = PrepareDictionaryGet(s->Global("_R134_REPORT")); Arguments args16360; args16360.positional.reserve(2); args16360.Add(Value("egg_substitution_errors"), false); args16360.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn16359, std::move(args16360)); }()); return Binary("Add", v16358, Value(int64_t{1})); }());
Put(s->Global("_R134_REPORT"), Value("egg_substitution_errors"), v16357);
}
else { throw; }
}
(void)([&]() -> Value { auto fn16361 = Attribute(s->Global("_R134_REPORT"), "update"); Arguments args16362; args16362.Add(([&]() -> Value { auto fn16363 = s->Global("getattr"); Arguments args16364; args16364.positional.reserve(3); args16364.Add(s->Global("_R134_PARENT"), false); args16364.Add(Value("telemetry"), false); args16364.Add(([&]() -> Value { auto dict16365 = Dict(); return dict16365; }()), false); return Call(c, fn16363, std::move(args16364)); }()), false); return Call(c, fn16361, std::move(args16362)); }());
return s->LocalAt(3);
return {};
}
}  // namespace kagg::opponents::compiled
