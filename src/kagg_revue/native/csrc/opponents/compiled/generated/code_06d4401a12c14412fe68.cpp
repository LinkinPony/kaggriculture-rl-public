// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_06d4401a12c14412fe68(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"T", "func", "u", "x"};
s->PrepareSlots(s_names);
auto v6150 = ([&]() -> Value { auto fn6151 = s->Global("max"); Arguments args6152; args6152.positional.reserve(2); args6152.Add(Value(0.0), false); args6152.Add(s->LocalAt(3), false); return Call(c, fn6151, std::move(args6152)); }());
s->SetAt(3, v6150);
if (static_cast<bool>(([&]() -> Value { auto v6153 = s->LocalAt(1); Value v6154; v6154 = Value("linear"); if (!static_cast<bool>(Binary("Eq", v6153, v6154))) return Value(false); v6153 = v6154; return Value(true); }()))) {
return s->LocalAt(3);
}
if (static_cast<bool>(([&]() -> Value { auto v6155 = s->LocalAt(1); Value v6156; v6156 = Value("sq"); if (!static_cast<bool>(Binary("Eq", v6155, v6156))) return Value(false); v6155 = v6156; return Value(true); }()))) {
return ([&]() -> Value { auto v6157 = s->LocalAt(3); return Binary("Mult", v6157, s->LocalAt(3)); }());
}
if (static_cast<bool>(([&]() -> Value { auto v6158 = s->LocalAt(1); Value v6159; v6159 = Value("sqrt"); if (!static_cast<bool>(Binary("Eq", v6158, v6159))) return Value(false); v6158 = v6159; return Value(true); }()))) {
return ([&]() -> Value { auto fn6160 = Attribute(s->Global("math"), "sqrt"); Arguments args6161; args6161.Add(s->LocalAt(3), false); return Call(c, fn6160, std::move(args6161)); }());
}
if (static_cast<bool>(([&]() -> Value { auto v6162 = s->LocalAt(1); Value v6163; v6163 = Value("log"); if (!static_cast<bool>(Binary("Eq", v6162, v6163))) return Value(false); v6162 = v6163; return Value(true); }()))) {
return ([&]() -> Value { auto fn6164 = Attribute(s->Global("math"), "log"); Arguments args6165; args6165.Add(([&]() -> Value { auto v6166 = Value(1.0); return Binary("Add", v6166, s->LocalAt(3)); }()), false); return Call(c, fn6164, std::move(args6165)); }());
}
if (static_cast<bool>(([&]() -> Value { auto v6167 = s->LocalAt(1); Value v6168; v6168 = Value("log10"); if (!static_cast<bool>(Binary("Eq", v6167, v6168))) return Value(false); v6167 = v6168; return Value(true); }()))) {
return ([&]() -> Value { auto fn6169 = Attribute(s->Global("math"), "log10"); Arguments args6170; args6170.Add(([&]() -> Value { auto v6171 = Value(1.0); return Binary("Add", v6171, s->LocalAt(3)); }()), false); return Call(c, fn6169, std::move(args6170)); }());
}
if (static_cast<bool>(([&]() -> Value { auto v6172 = s->LocalAt(1); Value v6173; v6173 = Value("hinge"); if (!static_cast<bool>(Binary("Eq", v6172, v6173))) return Value(false); v6172 = v6173; return Value(true); }()))) {
if (static_cast<bool>(([&]() -> Value { auto v6174 = Unary("Not", s->LocalAt(0)); if (static_cast<bool>(v6174)) return v6174; v6174 = ([&]() -> Value { auto v6175 = s->LocalAt(0); Value v6176; v6176 = Value(int64_t{0}); if (!static_cast<bool>(Binary("LtE", v6175, v6176))) return Value(false); v6175 = v6176; return Value(true); }()); return v6174; }()))) {
return s->LocalAt(3);
}
auto v6177 = ([&]() -> Value { auto v6178 = s->LocalAt(3); return Binary("Div", v6178, s->LocalAt(0)); }());
s->SetAt(2, v6177);
return ([&]() -> Value { auto v6179 = s->LocalAt(2); return Binary("Add", v6179, ([&]() -> Value { auto v6180 = s->Global("_R37_HINGE_GAIN"); return Binary("Mult", v6180, ([&]() -> Value { auto v6181 = ([&]() -> Value { auto fn6182 = s->Global("max"); Arguments args6183; args6183.positional.reserve(2); args6183.Add(Value(0.0), false); args6183.Add(([&]() -> Value { auto v6184 = s->LocalAt(2); return Binary("Sub", v6184, Value(1.0)); }()), false); return Call(c, fn6182, std::move(args6183)); }()); return Binary("Pow", v6181, Value(int64_t{2})); }())); }())); }());
}
return s->LocalAt(3);
return {};
}
}  // namespace kagg::opponents::compiled
