// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_503f07641b899fd3ab5c(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"I0", "T", "amp", "base", "f", "inventory", "item", "p", "params", "price"};
s->PrepareSlots(s_names);
auto v6185 = Get(([&]() -> Value { auto v6186 = s->LocalAt(8); if (static_cast<bool>(v6186)) return v6186; v6186 = s->Global("_R37_MARKET_PARAMS"); return v6186; }()), s->LocalAt(6));
s->SetAt(7, v6185);
auto v6187 = Get(s->LocalAt(7), Value("base"));
s->SetAt(3, v6187);
auto v6188 = Get(s->LocalAt(7), Value("I0"));
s->SetAt(0, v6188);
auto v6189 = Get(s->LocalAt(7), Value("T"));
s->SetAt(1, v6189);
if (static_cast<bool>(([&]() -> Value { auto v6190 = s->LocalAt(5); Value v6191; v6191 = s->LocalAt(0); if (!static_cast<bool>(Binary("Lt", v6190, v6191))) return Value(false); v6190 = v6191; return Value(true); }()))) {
auto v6192 = Get(s->LocalAt(7), Value("below_func"));
s->SetAt(4, v6192);
auto v6193 = ([&]() -> Value { auto v6194 = ([&]() -> Value { auto v6195 = Get(s->LocalAt(7), Value("below_target")); return Binary("Mult", v6195, s->LocalAt(3)); }()); return Binary("Div", v6194, ([&]() -> Value { auto fn6196 = s->Global("_r37_shape"); Arguments args6197; args6197.positional.reserve(3); args6197.Add(s->LocalAt(4), false); args6197.Add(s->LocalAt(1), false); args6197.Add(s->LocalAt(1), false); return Call(c, fn6196, std::move(args6197)); }())); }());
s->SetAt(2, v6193);
auto v6198 = ([&]() -> Value { auto v6199 = s->LocalAt(3); return Binary("Add", v6199, ([&]() -> Value { auto v6200 = s->LocalAt(2); return Binary("Mult", v6200, ([&]() -> Value { auto fn6201 = s->Global("_r37_shape"); Arguments args6202; args6202.positional.reserve(3); args6202.Add(s->LocalAt(4), false); args6202.Add(([&]() -> Value { auto v6203 = s->LocalAt(0); return Binary("Sub", v6203, s->LocalAt(5)); }()), false); args6202.Add(s->LocalAt(1), false); return Call(c, fn6201, std::move(args6202)); }())); }())); }());
s->SetAt(9, v6198);
}
else {
auto v6204 = Get(s->LocalAt(7), Value("above_func"));
s->SetAt(4, v6204);
auto v6205 = ([&]() -> Value { auto v6206 = ([&]() -> Value { auto v6207 = Get(s->LocalAt(7), Value("above_target")); return Binary("Mult", v6207, s->LocalAt(3)); }()); return Binary("Div", v6206, ([&]() -> Value { auto fn6208 = s->Global("_r37_shape"); Arguments args6209; args6209.positional.reserve(3); args6209.Add(s->LocalAt(4), false); args6209.Add(s->LocalAt(1), false); args6209.Add(s->LocalAt(1), false); return Call(c, fn6208, std::move(args6209)); }())); }());
s->SetAt(2, v6205);
auto v6210 = ([&]() -> Value { auto v6211 = s->LocalAt(3); return Binary("Sub", v6211, ([&]() -> Value { auto v6212 = s->LocalAt(2); return Binary("Mult", v6212, ([&]() -> Value { auto fn6213 = s->Global("_r37_shape"); Arguments args6214; args6214.positional.reserve(3); args6214.Add(s->LocalAt(4), false); args6214.Add(([&]() -> Value { auto v6215 = s->LocalAt(5); return Binary("Sub", v6215, s->LocalAt(0)); }()), false); args6214.Add(s->LocalAt(1), false); return Call(c, fn6213, std::move(args6214)); }())); }())); }());
s->SetAt(9, v6210);
}
return ([&]() -> Value { auto fn6216 = s->Global("max"); Arguments args6217; args6217.positional.reserve(2); args6217.Add(s->Global("_R37_PRICE_FLOOR"), false); args6217.Add(([&]() -> Value { auto fn6218 = s->Global("int"); Arguments args6219; args6219.Add(([&]() -> Value { auto fn6220 = s->Global("round"); Arguments args6221; args6221.Add(s->LocalAt(9), false); return Call(c, fn6220, std::move(args6221)); }()), false); return Call(c, fn6218, std::move(args6219)); }()), false); return Call(c, fn6216, std::move(args6217)); }());
return {};
}
}  // namespace kagg::opponents::compiled
