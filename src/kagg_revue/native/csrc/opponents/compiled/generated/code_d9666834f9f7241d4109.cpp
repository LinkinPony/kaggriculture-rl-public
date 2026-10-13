// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_d9666834f9f7241d4109(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"before", "gained", "observation", "pending", "state", "step"};
s->PrepareSlots(s_names);
auto v16145 = ([&]() -> Value { auto fn16146 = Attribute(s->LocalAt(4), "pop"); Arguments args16147; args16147.positional.reserve(2); args16147.Add(Value("pending"), false); args16147.Add(Value{}, false); return Call(c, fn16146, std::move(args16147)); }());
s->SetAt(3, v16145);
if (static_cast<bool>(Unary("Not", s->LocalAt(3)))) {
return Value{};
}
auto v16148 = s->LocalAt(3);
auto unpack16149 = Iterate(v16148);
ValidateUnpack(unpack16149, 2, false);
s->SetAt(5, unpack16149.at(0));
s->SetAt(0, unpack16149.at(1));
auto v16150 = ([&]() -> Value { auto fn16151 = s->Global("max"); Arguments args16152; args16152.positional.reserve(2); args16152.Add(Value(int64_t{0}), false); args16152.Add(([&]() -> Value { auto v16153 = ([&]() -> Value { auto fn16154 = s->Global("int"); Arguments args16155; args16155.Add(([&]() -> Value { auto fn16156 = PrepareDictionaryGet(Get(Get(s->LocalAt(2), Value("private")), Value("shed"))); Arguments args16157; args16157.positional.reserve(2); args16157.Add(Value("GOOSE"), false); args16157.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn16156, std::move(args16157)); }()), false); return Call(c, fn16154, std::move(args16155)); }()); return Binary("Sub", v16153, s->LocalAt(0)); }()), false); return Call(c, fn16151, std::move(args16152)); }());
s->SetAt(1, v16150);
if (static_cast<bool>(([&]() -> Value { auto v16158 = ([&]() -> Value { auto v16159 = ([&]() -> Value { auto fn16161 = s->Global("int"); Arguments args16162; args16162.Add(Get(s->LocalAt(2), Value("step")), false); return Call(c, fn16161, std::move(args16162)); }()); Value v16160; v16160 = s->LocalAt(5); if (!static_cast<bool>(Binary("Eq", v16159, v16160))) return Value(false); v16159 = v16160; return Value(true); }()); if (!static_cast<bool>(v16158)) return v16158; v16158 = ([&]() -> Value { auto v16163 = s->LocalAt(1); Value v16164; v16164 = Get(s->LocalAt(4), Value("quota")); if (!static_cast<bool>(Binary("GtE", v16163, v16164))) return Value(false); v16163 = v16164; return Value(true); }()); return v16158; }()))) {
auto v16165 = Value(true);
Put(s->LocalAt(4), Value("confirmed"), v16165);
auto v16166 = s->Global("_R134_REPORT");
auto v16167 = Value("egg_substitution_confirmed_units");
auto v16168 = Get(v16166, v16167);
Put(v16166, v16167, Inplace("Add", v16168, Get(s->LocalAt(4), Value("quota"))));
}
else {
auto v16169 = Value(false);
Put(s->LocalAt(4), Value("confirmed"), v16169);
auto v16170 = s->Global("_R134_REPORT");
auto v16171 = Value("egg_substitution_purchase_shortfalls");
auto v16172 = Get(v16170, v16171);
Put(v16170, v16171, Inplace("Add", v16172, Get(s->LocalAt(4), Value("quota"))));
}
return {};
}
}  // namespace kagg::opponents::compiled
