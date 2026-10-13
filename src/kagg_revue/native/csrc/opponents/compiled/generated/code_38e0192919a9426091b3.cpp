// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_38e0192919a9426091b3(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "configuration", "obs", "p", "st", "step"};
s->PrepareSlots(s_names);
auto v27601 = ([&]() -> Value { auto fn27602 = s->Global("int"); Arguments args27603; args27603.Add(Get(s->LocalAt(2), Value("player")), false); return Call(c, fn27602, std::move(args27603)); }());
s->SetAt(3, v27601);
auto v27604 = ([&]() -> Value { auto fn27605 = s->Global("int"); Arguments args27606; args27606.Add(Get(s->LocalAt(2), Value("step")), false); return Call(c, fn27605, std::move(args27606)); }());
s->SetAt(5, v27604);
auto v27607 = ([&]() -> Value { auto fn27608 = PrepareDictionaryGet(s->Global("_V92_P")); Arguments args27609; args27609.Add(s->LocalAt(3), false); return CallDictionaryGet(c, fn27608, std::move(args27609)); }());
s->SetAt(4, v27607);
if (static_cast<bool>(([&]() -> Value { auto v27610 = ([&]() -> Value { auto v27611 = s->LocalAt(4); Value v27612; v27612 = Value{}; if (!static_cast<bool>(Binary("Is", v27611, v27612))) return Value(false); v27611 = v27612; return Value(true); }()); if (static_cast<bool>(v27610)) return v27610; v27610 = ([&]() -> Value { auto v27613 = s->LocalAt(5); Value v27614; v27614 = Get(s->LocalAt(4), Value("step")); if (!static_cast<bool>(Binary("LtE", v27613, v27614))) return Value(false); v27613 = v27614; return Value(true); }()); return v27610; }()))) {
auto v27615 = ([&]() -> Value { auto dict27616 = Dict(); auto key27617 = Value("step"); Put(dict27616, key27617, Unary("USub", Value(int64_t{1}))); auto key27618 = Value("obs"); Put(dict27616, key27618, ([&]() -> Value { auto dict27619 = Dict(); return dict27619; }())); return dict27616; }());
s->SetAt(4, v27615);
Put(s->Global("_V92_P"), s->LocalAt(3), v27615);
}
auto v27620 = s->LocalAt(5);
Put(s->LocalAt(4), Value("step"), v27620);
auto v27621 = ([&]() -> Value { auto fn27622 = s->Global("_E350_INNER"); Arguments args27623; args27623.positional.reserve(2); args27623.Add(s->LocalAt(2), false); args27623.Add(s->LocalAt(1), false); return Call(c, fn27622, std::move(args27623)); }());
s->SetAt(0, v27621);
try {
return ([&]() -> Value { auto fn27625 = s->Global("_v92_predict"); Arguments args27626; args27626.positional.reserve(3); args27626.Add(s->LocalAt(2), false); args27626.Add(s->LocalAt(0), false); args27626.Add(s->LocalAt(4), false); return Call(c, fn27625, std::move(args27626)); }());
} catch (const Error& error27624) {
if (Matches(error27624, s->Global("Exception"))) {
auto v27627 = s->Global("_V92_P_REPORT");
auto v27628 = Value("pred_errors");
auto v27629 = Get(v27627, v27628);
Put(v27627, v27628, Inplace("Add", v27629, Value(int64_t{1})));
return s->LocalAt(0);
}
else { throw; }
}
return {};
}
}  // namespace kagg::opponents::compiled
