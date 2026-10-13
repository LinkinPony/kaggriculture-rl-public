// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_bc22562d42cc3a420129(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"configuration", "observation", "player", "result", "state", "step"};
s->PrepareSlots(s_names);
auto v15966 = ([&]() -> Value { auto fn15967 = s->Global("_R132_PARENT"); Arguments args15968; args15968.positional.reserve(2); args15968.Add(s->LocalAt(1), false); args15968.Add(s->LocalAt(0), false); return Call(c, fn15967, std::move(args15968)); }());
s->SetAt(3, v15966);
try {
auto v15970 = ([&]() -> Value { auto fn15971 = s->Global("int"); Arguments args15972; args15972.Add(Get(s->LocalAt(1), Value("player")), false); return Call(c, fn15971, std::move(args15972)); }());
s->SetAt(2, v15970);
auto v15973 = ([&]() -> Value { auto fn15974 = s->Global("int"); Arguments args15975; args15975.Add(([&]() -> Value { auto fn15976 = PrepareDictionaryGet(s->LocalAt(1)); Arguments args15977; args15977.positional.reserve(2); args15977.Add(Value("step"), false); args15977.Add(([&]() -> Value { auto v15978 = ([&]() -> Value { auto v15979 = Get(s->LocalAt(1), Value("day")); return Binary("Mult", v15979, Value(int64_t{24})); }()); return Binary("Add", v15978, Get(s->LocalAt(1), Value("hour"))); }()), false); return CallDictionaryGet(c, fn15976, std::move(args15977)); }()), false); return Call(c, fn15974, std::move(args15975)); }());
s->SetAt(5, v15973);
auto v15980 = ([&]() -> Value { auto fn15981 = PrepareDictionaryGet(s->Global("_R132_STATES")); Arguments args15982; args15982.Add(s->LocalAt(2), false); return CallDictionaryGet(c, fn15981, std::move(args15982)); }());
s->SetAt(4, v15980);
if (static_cast<bool>(([&]() -> Value { auto v15983 = ([&]() -> Value { auto v15984 = s->LocalAt(4); Value v15985; v15985 = Value{}; if (!static_cast<bool>(Binary("Is", v15984, v15985))) return Value(false); v15984 = v15985; return Value(true); }()); if (static_cast<bool>(v15983)) return v15983; v15983 = ([&]() -> Value { auto v15986 = s->LocalAt(5); Value v15987; v15987 = Get(s->LocalAt(4), Value("step")); if (!static_cast<bool>(Binary("LtE", v15986, v15987))) return Value(false); v15986 = v15987; return Value(true); }()); return v15983; }()))) {
auto v15988 = ([&]() -> Value { auto dict15989 = Dict(); auto key15990 = Value("step"); Put(dict15989, key15990, Unary("USub", Value(int64_t{1}))); return dict15989; }());
s->SetAt(4, v15988);
Put(s->Global("_R132_STATES"), s->LocalAt(2), v15988);
(void)([&]() -> Value { auto fn15991 = Attribute(s->Global("_R132_REPORT"), "update"); Arguments args15992; args15992.Keyword("weed_repair_started", Value(int64_t{0})); args15992.Keyword("weed_repair_shifted_steps", Value(int64_t{0})); args15992.Keyword("weed_repair_plants", Value(int64_t{0})); args15992.Keyword("weed_repair_waters", Value(int64_t{0})); args15992.Keyword("weed_repair_completed", Value(int64_t{0})); args15992.Keyword("weed_repair_aborted", Value(int64_t{0})); args15992.Keyword("mirror_reorders", Value(int64_t{0})); args15992.Keyword("mirror_modeled_gain", Value(int64_t{0})); args15992.Keyword("replay_guard_errors", Value(int64_t{0})); return Call(c, fn15991, std::move(args15992)); }());
}
auto v15993 = s->LocalAt(5);
Put(s->LocalAt(4), Value("step"), v15993);
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto fn15994 = s->Global("_r132_standard"); Arguments args15995; args15995.Add(s->LocalAt(0), false); return Call(c, fn15994, std::move(args15995)); }())))) {
return s->LocalAt(3);
}
if (static_cast<bool>(([&]() -> Value { auto fn15996 = PrepareDictionaryGet(s->LocalAt(4)); Arguments args15997; args15997.Add(Value("repair"), false); return CallDictionaryGet(c, fn15996, std::move(args15997)); }()))) {
auto v15998 = ([&]() -> Value { auto fn15999 = s->Global("_r132_continue_repair"); Arguments args16000; args16000.positional.reserve(3); args16000.Add(s->LocalAt(1), false); args16000.Add(s->LocalAt(3), false); args16000.Add(s->LocalAt(4), false); return Call(c, fn15999, std::move(args16000)); }());
s->SetAt(3, v15998);
}
else {
(void)([&]() -> Value { auto fn16001 = s->Global("_r132_start_repair"); Arguments args16002; args16002.positional.reserve(3); args16002.Add(s->LocalAt(1), false); args16002.Add(s->LocalAt(3), false); args16002.Add(s->LocalAt(4), false); return Call(c, fn16001, std::move(args16002)); }());
}
auto v16003 = ([&]() -> Value { auto fn16004 = s->Global("_r132_mirror_reorder"); Arguments args16005; args16005.positional.reserve(2); args16005.Add(s->LocalAt(1), false); args16005.Add(s->LocalAt(3), false); return Call(c, fn16004, std::move(args16005)); }());
s->SetAt(3, v16003);
} catch (const Error& error15969) {
if (Matches(error15969, s->Global("Exception"))) {
auto v16006 = ([&]() -> Value { auto v16007 = ([&]() -> Value { auto fn16008 = PrepareDictionaryGet(s->Global("_R132_REPORT")); Arguments args16009; args16009.positional.reserve(2); args16009.Add(Value("replay_guard_errors"), false); args16009.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn16008, std::move(args16009)); }()); return Binary("Add", v16007, Value(int64_t{1})); }());
Put(s->Global("_R132_REPORT"), Value("replay_guard_errors"), v16006);
}
else { throw; }
}
(void)([&]() -> Value { auto fn16010 = Attribute(s->Global("_R132_REPORT"), "update"); Arguments args16011; args16011.Add(([&]() -> Value { auto fn16012 = s->Global("getattr"); Arguments args16013; args16013.positional.reserve(3); args16013.Add(s->Global("_R132_PARENT"), false); args16013.Add(Value("telemetry"), false); args16013.Add(([&]() -> Value { auto dict16014 = Dict(); return dict16014; }()), false); return Call(c, fn16012, std::move(args16013)); }()), false); return Call(c, fn16010, std::move(args16011)); }());
return s->LocalAt(3);
return {};
}
}  // namespace kagg::opponents::compiled
