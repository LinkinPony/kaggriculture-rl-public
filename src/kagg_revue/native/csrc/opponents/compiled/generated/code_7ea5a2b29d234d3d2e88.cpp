// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_7ea5a2b29d234d3d2e88(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"coordinates", "farm", "mls", "step", "tile", "x", "y"};
s->PrepareSlots(s_names);
for (const auto& item16553 : Iterate(([&]() -> Value { auto fn16554 = s->Global("sorted"); Arguments args16555; args16555.Add(s->LocalAt(0), false); return Call(c, fn16554, std::move(args16555)); }()))) {
auto unpack16556 = Iterate(item16553);
ValidateUnpack(unpack16556, 2, false);
s->SetAt(6, unpack16556.at(0));
s->SetAt(5, unpack16556.at(1));
auto v16557 = Get(Get(Get(s->LocalAt(1), Value("tiles")), s->LocalAt(6)), s->LocalAt(5));
s->SetAt(4, v16557);
if (static_cast<bool>(([&]() -> Value { auto v16558 = Unary("Not", ([&]() -> Value { auto fn16559 = s->Global("isinstance"); Arguments args16560; args16560.positional.reserve(2); args16560.Add(s->LocalAt(4), false); args16560.Add(s->Global("dict"), false); return Call(c, fn16559, std::move(args16560)); }())); if (static_cast<bool>(v16558)) return v16558; v16558 = ([&]() -> Value { auto v16561 = ([&]() -> Value { auto fn16563 = PrepareDictionaryGet(s->LocalAt(4)); Arguments args16564; args16564.Add(Value("kind"), false); return CallDictionaryGet(c, fn16563, std::move(args16564)); }()); Value v16562; v16562 = Value("PLANT"); if (!static_cast<bool>(Binary("NotEq", v16561, v16562))) return Value(false); v16561 = v16562; return Value(true); }()); return v16558; }()))) {
continue;
}
auto v16565 = Get(s->LocalAt(4), Value("max_lifespan_step"));
s->SetAt(2, v16565);
if (static_cast<bool>(([&]() -> Value { auto v16566 = ([&]() -> Value { auto v16567 = s->LocalAt(2); Value v16568; v16568 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Lt", v16567, v16568))) return Value(false); v16567 = v16568; return Value(true); }()); if (static_cast<bool>(v16566)) return v16566; v16566 = ([&]() -> Value { auto v16569 = s->LocalAt(3); Value v16570; v16570 = s->LocalAt(2); if (!static_cast<bool>(Binary("Lt", v16569, v16570))) return Value(false); v16569 = v16570; return Value(true); }()); if (static_cast<bool>(v16566)) return v16566; v16566 = ([&]() -> Value { auto v16571 = ([&]() -> Value { auto v16572 = s->LocalAt(3); return Binary("Sub", v16572, s->LocalAt(2)); }()); return Binary("Mod", v16571, Value(int64_t{2})); }()); return v16566; }()))) {
continue;
}
auto v16573 = s->LocalAt(4);
auto v16574 = Value("yield_units");
auto v16575 = Get(v16573, v16574);
Put(v16573, v16574, Inplace("Sub", v16575, Value(int64_t{1})));
if (static_cast<bool>(([&]() -> Value { auto v16576 = Get(s->LocalAt(4), Value("yield_units")); Value v16577; v16577 = Value(int64_t{0}); if (!static_cast<bool>(Binary("LtE", v16576, v16577))) return Value(false); v16576 = v16577; return Value(true); }()))) {
auto v16578 = ([&]() -> Value { auto dict16579 = Dict(); auto key16580 = Value("kind"); Put(dict16579, key16580, Value("WEED")); return dict16579; }());
Put(Get(Get(s->LocalAt(1), Value("tiles")), s->LocalAt(6)), s->LocalAt(5), v16578);
}
}
return {};
}
}  // namespace kagg::opponents::compiled
