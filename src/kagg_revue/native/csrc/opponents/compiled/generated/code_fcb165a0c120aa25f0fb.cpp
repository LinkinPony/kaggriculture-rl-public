// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_fcb165a0c120aa25f0fb(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "configuration", "observation", "player", "st", "step"};
s->PrepareSlots(s_names);
auto v21458 = Tuple({([&]() -> Value { auto fn21459 = s->Global("int"); Arguments args21460; args21460.Add(Get(s->LocalAt(2), Value("player")), false); return Call(c, fn21459, std::move(args21460)); }()), ([&]() -> Value { auto fn21461 = s->Global("int"); Arguments args21462; args21462.Add(Get(s->LocalAt(2), Value("step")), false); return Call(c, fn21461, std::move(args21462)); }())});
auto unpack21463 = Iterate(v21458);
ValidateUnpack(unpack21463, 2, false);
s->SetAt(3, unpack21463.at(0));
s->SetAt(5, unpack21463.at(1));
auto v21464 = ([&]() -> Value { auto fn21465 = PrepareDictionaryGet(s->Global("_V9_HERD")); Arguments args21466; args21466.Add(s->LocalAt(3), false); return CallDictionaryGet(c, fn21465, std::move(args21466)); }());
s->SetAt(4, v21464);
if (static_cast<bool>(([&]() -> Value { auto v21467 = ([&]() -> Value { auto v21468 = s->LocalAt(4); Value v21469; v21469 = Value{}; if (!static_cast<bool>(Binary("Is", v21468, v21469))) return Value(false); v21468 = v21469; return Value(true); }()); if (static_cast<bool>(v21467)) return v21467; v21467 = ([&]() -> Value { auto v21470 = s->LocalAt(5); Value v21471; v21471 = Get(s->LocalAt(4), Value("step")); if (!static_cast<bool>(Binary("LtE", v21470, v21471))) return Value(false); v21470 = v21471; return Value(true); }()); return v21467; }()))) {
auto v21472 = ([&]() -> Value { auto dict21473 = Dict(); auto key21474 = Value("step"); Put(dict21473, key21474, Unary("USub", Value(int64_t{1}))); return dict21473; }());
s->SetAt(4, v21472);
Put(s->Global("_V9_HERD"), s->LocalAt(3), v21472);
if (static_cast<bool>(([&]() -> Value { auto v21475 = s->LocalAt(5); Value v21476; v21476 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v21475, v21476))) return Value(false); v21475 = v21476; return Value(true); }()))) {
(void)([&]() -> Value { auto fn21477 = Attribute(s->Global("_V9_HERD_REPORT"), "update"); Arguments args21478; args21478.Keyword("herd_species", Value("")); args21478.Keyword("herd_rewrites", Value(int64_t{0})); args21478.Keyword("herd_extra_sold", Value(int64_t{0})); args21478.Keyword("herd_errors", Value(int64_t{0})); return Call(c, fn21477, std::move(args21478)); }());
}
}
auto v21479 = s->LocalAt(5);
Put(s->LocalAt(4), Value("step"), v21479);
auto v21480 = ([&]() -> Value { auto fn21481 = s->Global("_V9_HERD_PARENT"); Arguments args21482; args21482.positional.reserve(2); args21482.Add(s->LocalAt(2), false); args21482.Add(s->LocalAt(1), false); return Call(c, fn21481, std::move(args21482)); }());
s->SetAt(0, v21480);
try {
return ([&]() -> Value { auto fn21484 = s->Global("_v9_herd"); Arguments args21485; args21485.positional.reserve(3); args21485.Add(s->LocalAt(2), false); args21485.Add(s->LocalAt(0), false); args21485.Add(s->LocalAt(4), false); return Call(c, fn21484, std::move(args21485)); }());
} catch (const Error& error21483) {
if (Matches(error21483, s->Global("Exception"))) {
auto v21486 = s->Global("_V9_HERD_REPORT");
auto v21487 = Value("herd_errors");
auto v21488 = Get(v21486, v21487);
Put(v21486, v21487, Inplace("Add", v21488, Value(int64_t{1})));
return s->LocalAt(0);
}
else { throw; }
}
return {};
}
}  // namespace kagg::opponents::compiled
