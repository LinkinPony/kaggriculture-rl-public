// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_e89297d952c53ac14076(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "configuration", "observation", "player", "st", "step"};
s->PrepareSlots(s_names);
auto v21191 = Tuple({([&]() -> Value { auto fn21192 = s->Global("int"); Arguments args21193; args21193.Add(Get(s->LocalAt(2), Value("player")), false); return Call(c, fn21192, std::move(args21193)); }()), ([&]() -> Value { auto fn21194 = s->Global("int"); Arguments args21195; args21195.Add(Get(s->LocalAt(2), Value("step")), false); return Call(c, fn21194, std::move(args21195)); }())});
auto unpack21196 = Iterate(v21191);
ValidateUnpack(unpack21196, 2, false);
s->SetAt(3, unpack21196.at(0));
s->SetAt(5, unpack21196.at(1));
auto v21197 = ([&]() -> Value { auto fn21198 = PrepareDictionaryGet(s->Global("_V9_CARROT")); Arguments args21199; args21199.Add(s->LocalAt(3), false); return CallDictionaryGet(c, fn21198, std::move(args21199)); }());
s->SetAt(4, v21197);
if (static_cast<bool>(([&]() -> Value { auto v21200 = ([&]() -> Value { auto v21201 = s->LocalAt(4); Value v21202; v21202 = Value{}; if (!static_cast<bool>(Binary("Is", v21201, v21202))) return Value(false); v21201 = v21202; return Value(true); }()); if (static_cast<bool>(v21200)) return v21200; v21200 = ([&]() -> Value { auto v21203 = s->LocalAt(5); Value v21204; v21204 = Get(s->LocalAt(4), Value("step")); if (!static_cast<bool>(Binary("LtE", v21203, v21204))) return Value(false); v21203 = v21204; return Value(true); }()); return v21200; }()))) {
auto v21205 = ([&]() -> Value { auto dict21206 = Dict(); auto key21207 = Value("step"); Put(dict21206, key21207, Unary("USub", Value(int64_t{1}))); return dict21206; }());
s->SetAt(4, v21205);
Put(s->Global("_V9_CARROT"), s->LocalAt(3), v21205);
if (static_cast<bool>(([&]() -> Value { auto v21208 = s->LocalAt(5); Value v21209; v21209 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v21208, v21209))) return Value(false); v21208 = v21209; return Value(true); }()))) {
(void)([&]() -> Value { auto fn21210 = Attribute(s->Global("_V9_CARROT_REPORT"), "update"); Arguments args21211; args21211.Keyword("carrot_swaps", Value(int64_t{0})); args21211.Keyword("carrot_seed_swaps", Value(int64_t{0})); args21211.Keyword("carrot_errors", Value(int64_t{0})); return Call(c, fn21210, std::move(args21211)); }());
}
}
auto v21212 = s->LocalAt(5);
Put(s->LocalAt(4), Value("step"), v21212);
auto v21213 = ([&]() -> Value { auto fn21214 = s->Global("_V9_CARROT_PARENT"); Arguments args21215; args21215.positional.reserve(2); args21215.Add(s->LocalAt(2), false); args21215.Add(s->LocalAt(1), false); return Call(c, fn21214, std::move(args21215)); }());
s->SetAt(0, v21213);
try {
return ([&]() -> Value { auto fn21217 = s->Global("_v9_carrot"); Arguments args21218; args21218.positional.reserve(3); args21218.Add(s->LocalAt(2), false); args21218.Add(s->LocalAt(0), false); args21218.Add(s->LocalAt(4), false); return Call(c, fn21217, std::move(args21218)); }());
} catch (const Error& error21216) {
if (Matches(error21216, s->Global("Exception"))) {
auto v21219 = s->Global("_V9_CARROT_REPORT");
auto v21220 = Value("carrot_errors");
auto v21221 = Get(v21219, v21220);
Put(v21219, v21220, Inplace("Add", v21221, Value(int64_t{1})));
return s->LocalAt(0);
}
else { throw; }
}
return {};
}
}  // namespace kagg::opponents::compiled
