// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_048f14bde208f4f784eb(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"board_size", "farm", "mls", "step", "tile", "x", "y"};
s->PrepareSlots(s_names);
auto v2471 = ([&]() -> Value { auto fn2472 = s->Global("len"); Arguments args2473; args2473.Add(Get(s->LocalAt(1), Value("tiles")), false); return Call(c, fn2472, std::move(args2473)); }());
s->SetAt(0, v2471);
for (const auto& item2474 : Iterate(([&]() -> Value { auto fn2475 = s->Global("range"); Arguments args2476; args2476.Add(s->LocalAt(0), false); return Call(c, fn2475, std::move(args2476)); }()))) {
s->SetAt(6, item2474);
for (const auto& item2477 : Iterate(([&]() -> Value { auto fn2478 = s->Global("range"); Arguments args2479; args2479.Add(s->LocalAt(0), false); return Call(c, fn2478, std::move(args2479)); }()))) {
s->SetAt(5, item2477);
auto v2480 = Get(Get(Get(s->LocalAt(1), Value("tiles")), s->LocalAt(6)), s->LocalAt(5));
s->SetAt(4, v2480);
if (static_cast<bool>(([&]() -> Value { auto v2481 = Unary("Not", ([&]() -> Value { auto fn2482 = s->Global("isinstance"); Arguments args2483; args2483.positional.reserve(2); args2483.Add(s->LocalAt(4), false); args2483.Add(s->Global("dict"), false); return Call(c, fn2482, std::move(args2483)); }())); if (static_cast<bool>(v2481)) return v2481; v2481 = ([&]() -> Value { auto v2484 = ([&]() -> Value { auto fn2486 = PrepareDictionaryGet(s->LocalAt(4)); Arguments args2487; args2487.Add(Value("kind"), false); return CallDictionaryGet(c, fn2486, std::move(args2487)); }()); Value v2485; v2485 = Value("PLANT"); if (!static_cast<bool>(Binary("NotEq", v2484, v2485))) return Value(false); v2484 = v2485; return Value(true); }()); return v2481; }()))) {
continue;
}
auto v2488 = Get(s->LocalAt(4), Value("max_lifespan_step"));
s->SetAt(2, v2488);
if (static_cast<bool>(([&]() -> Value { auto v2489 = ([&]() -> Value { auto v2490 = s->LocalAt(2); Value v2491; v2491 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Lt", v2490, v2491))) return Value(false); v2490 = v2491; return Value(true); }()); if (static_cast<bool>(v2489)) return v2489; v2489 = ([&]() -> Value { auto v2492 = s->LocalAt(3); Value v2493; v2493 = s->LocalAt(2); if (!static_cast<bool>(Binary("Lt", v2492, v2493))) return Value(false); v2492 = v2493; return Value(true); }()); return v2489; }()))) {
continue;
}
if (static_cast<bool>(([&]() -> Value { auto v2494 = ([&]() -> Value { auto v2496 = ([&]() -> Value { auto v2497 = s->LocalAt(3); return Binary("Sub", v2497, s->LocalAt(2)); }()); return Binary("Mod", v2496, Value(int64_t{2})); }()); Value v2495; v2495 = Value(int64_t{0}); if (!static_cast<bool>(Binary("NotEq", v2494, v2495))) return Value(false); v2494 = v2495; return Value(true); }()))) {
continue;
}
auto v2498 = s->LocalAt(4);
auto v2499 = Value("yield_units");
auto v2500 = Get(v2498, v2499);
Put(v2498, v2499, Inplace("Sub", v2500, Value(int64_t{1})));
if (static_cast<bool>(([&]() -> Value { auto v2501 = Get(s->LocalAt(4), Value("yield_units")); Value v2502; v2502 = Value(int64_t{0}); if (!static_cast<bool>(Binary("LtE", v2501, v2502))) return Value(false); v2501 = v2502; return Value(true); }()))) {
auto v2503 = ([&]() -> Value { auto dict2504 = Dict(); auto key2505 = Value("kind"); Put(dict2504, key2505, Value("WEED")); return dict2504; }());
Put(Get(Get(s->LocalAt(1), Value("tiles")), s->LocalAt(6)), s->LocalAt(5), v2503);
}
}
}
return {};
}
}  // namespace kagg::opponents::compiled
