// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_85fb8a22aecc06cd2c35(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "configuration", "observation", "step"};
s->PrepareSlots(s_names);
auto v19592 = ([&]() -> Value { auto fn19593 = s->Global("_V44Y_HOST"); Arguments args19594; args19594.positional.reserve(2); args19594.Add(s->LocalAt(2), false); args19594.Add(s->LocalAt(1), false); return Call(c, fn19593, std::move(args19594)); }());
s->SetAt(0, v19592);
try {
auto v19596 = ([&]() -> Value { auto fn19597 = s->Global("int"); Arguments args19598; args19598.Add(([&]() -> Value { auto fn19599 = PrepareDictionaryGet(s->LocalAt(2)); Arguments args19600; args19600.positional.reserve(2); args19600.Add(Value("step"), false); args19600.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn19599, std::move(args19600)); }()), false); return Call(c, fn19597, std::move(args19598)); }());
s->SetAt(3, v19596);
if (static_cast<bool>(([&]() -> Value { auto v19601 = ([&]() -> Value { auto v19602 = s->LocalAt(3); Value v19603; v19603 = Value(int64_t{216}); if (!static_cast<bool>(Binary("GtE", v19602, v19603))) return Value(false); v19602 = v19603; return Value(true); }()); if (!static_cast<bool>(v19601)) return v19601; v19601 = ([&]() -> Value { auto v19604 = Unary("Not", s->Global("_V44Y_REORDER_GATE")); if (static_cast<bool>(v19604)) return v19604; v19604 = ([&]() -> Value { auto fn19605 = s->Global("_v44y_clone_gate"); Arguments args19606; args19606.Add(s->LocalAt(2), false); return Call(c, fn19605, std::move(args19606)); }()); return v19604; }()); return v19601; }()))) {
auto v19607 = ([&]() -> Value { auto fn19608 = s->Global("_v44y_reorder"); Arguments args19609; args19609.positional.reserve(2); args19609.Add(s->LocalAt(2), false); args19609.Add(s->LocalAt(0), false); return Call(c, fn19608, std::move(args19609)); }());
s->SetAt(0, v19607);
}
} catch (const Error& error19595) {
if (Matches(error19595, s->Global("Exception"))) {
auto v19610 = s->Global("_V44Y_REPORT");
auto v19611 = Value("v44y_errors");
auto v19612 = Get(v19610, v19611);
Put(v19610, v19611, Inplace("Add", v19612, Value(int64_t{1})));
}
else { throw; }
}
return s->LocalAt(0);
return {};
}
}  // namespace kagg::opponents::compiled
