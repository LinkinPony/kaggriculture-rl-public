// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_870a7223ccac928b7e17(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "configuration", "observation", "player", "st", "step"};
s->PrepareSlots(s_names);
auto v30541 = Tuple({([&]() -> Value { auto fn30542 = s->Global("int"); Arguments args30543; args30543.Add(Get(s->LocalAt(2), Value("player")), false); return Call(c, fn30542, std::move(args30543)); }()), ([&]() -> Value { auto fn30544 = s->Global("int"); Arguments args30545; args30545.Add(Get(s->LocalAt(2), Value("step")), false); return Call(c, fn30544, std::move(args30545)); }())});
auto unpack30546 = Iterate(v30541);
ValidateUnpack(unpack30546, 2, false);
s->SetAt(3, unpack30546.at(0));
s->SetAt(5, unpack30546.at(1));
auto v30547 = ([&]() -> Value { auto fn30548 = PrepareDictionaryGet(s->Global("_CT")); Arguments args30549; args30549.Add(s->LocalAt(3), false); return CallDictionaryGet(c, fn30548, std::move(args30549)); }());
s->SetAt(4, v30547);
if (static_cast<bool>(([&]() -> Value { auto v30550 = ([&]() -> Value { auto v30551 = s->LocalAt(4); Value v30552; v30552 = Value{}; if (!static_cast<bool>(Binary("Is", v30551, v30552))) return Value(false); v30551 = v30552; return Value(true); }()); if (static_cast<bool>(v30550)) return v30550; v30550 = ([&]() -> Value { auto v30553 = s->LocalAt(5); Value v30554; v30554 = Get(s->LocalAt(4), Value("step")); if (!static_cast<bool>(Binary("LtE", v30553, v30554))) return Value(false); v30553 = v30554; return Value(true); }()); return v30550; }()))) {
auto v30555 = ([&]() -> Value { auto dict30556 = Dict(); auto key30557 = Value("step"); Put(dict30556, key30557, Unary("USub", Value(int64_t{1}))); return dict30556; }());
s->SetAt(4, v30555);
Put(s->Global("_CT"), s->LocalAt(3), v30555);
}
auto v30558 = s->LocalAt(5);
Put(s->LocalAt(4), Value("step"), v30558);
auto v30559 = ([&]() -> Value { auto fn30560 = s->Global("_P_ctrtable_336053"); Arguments args30561; args30561.positional.reserve(2); args30561.Add(s->LocalAt(2), false); args30561.Add(s->LocalAt(1), false); return Call(c, fn30560, std::move(args30561)); }());
s->SetAt(0, v30559);
try {
return ([&]() -> Value { auto fn30563 = s->Global("_ct_apply"); Arguments args30564; args30564.positional.reserve(3); args30564.Add(s->LocalAt(2), false); args30564.Add(s->LocalAt(0), false); args30564.Add(s->LocalAt(4), false); return Call(c, fn30563, std::move(args30564)); }());
} catch (const Error& error30562) {
if (Matches(error30562, s->Global("Exception"))) {
auto v30565 = s->Global("_CT_REPORT");
auto v30566 = Value("ct_errors");
auto v30567 = Get(v30565, v30566);
Put(v30565, v30566, Inplace("Add", v30567, Value(int64_t{1})));
return s->LocalAt(0);
}
else { throw; }
}
return {};
}
}  // namespace kagg::opponents::compiled
