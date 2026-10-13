// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_e8de42884f50e21f4760(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"cap", "config", "last", "orders", "size", "turns"};
s->PrepareSlots(s_names);
auto v2528 = ([&]() -> Value { auto comp2529 = std::make_shared<Scope>(); comp2529->globals = s->globals; comp2529->parent = s; static constexpr const char* comp2529_names[] = {"d", "k"}; comp2529->PrepareSlots(comp2529_names); auto result2530 = List(); for (const auto& item2531 : Iterate(List({Tuple({Value("boardSize"), Value(int64_t{10})}), Tuple({Value("turnsPerDay"), Value(int64_t{24})}), Tuple({Value("episodeSteps"), Value(int64_t{720})})}))) { auto unpack2532 = Iterate(item2531); ValidateUnpack(unpack2532, 2, false); comp2529->SetAt(1, unpack2532.at(0)); comp2529->SetAt(0, unpack2532.at(1)); result2530.node()->sequence.push_back(([&]() -> Value { auto fn2533 = comp2529->Global("_get"); Arguments args2534; args2534.positional.reserve(3); args2534.Add(comp2529->Captured("config"), false); args2534.Add(comp2529->LocalAt(1), false); args2534.Add(comp2529->LocalAt(0), false); return Call(c, fn2533, std::move(args2534)); }())); } return result2530; }());
auto unpack2535 = Iterate(v2528);
ValidateUnpack(unpack2535, 3, false);
s->SetAt(4, unpack2535.at(0));
s->SetAt(5, unpack2535.at(1));
s->SetAt(2, unpack2535.at(2));
if (static_cast<bool>(([&]() -> Value { auto v2536 = Tuple({s->LocalAt(4), s->LocalAt(5), s->LocalAt(2)}); Value v2537; v2537 = Tuple({Value(int64_t{10}), Value(int64_t{24}), Value(int64_t{720})}); if (!static_cast<bool>(Binary("NotEq", v2536, v2537))) return Value(false); v2536 = v2537; return Value(true); }()))) {
Raise(([&]() -> Value { auto fn2538 = s->Global("Unsupported"); Arguments args2539; args2539.Add(Value("requires pinned 10x10/24/720 terminal window"), false); return Call(c, fn2538, std::move(args2539)); }()));
}
auto v2540 = ([&]() -> Value { auto fn2541 = s->Global("int"); Arguments args2542; args2542.Add(([&]() -> Value { auto fn2543 = s->Global("_get"); Arguments args2544; args2544.positional.reserve(3); args2544.Add(s->LocalAt(1), false); args2544.Add(Value("shedCapacity"), false); args2544.Add(Value(int64_t{100}), false); return Call(c, fn2543, std::move(args2544)); }()), false); return Call(c, fn2541, std::move(args2542)); }());
s->SetAt(0, v2540);
auto v2545 = ([&]() -> Value { auto fn2546 = s->Global("min"); Arguments args2547; args2547.positional.reserve(2); args2547.Add(Value(int64_t{10}), false); args2547.Add(([&]() -> Value { auto fn2548 = s->Global("int"); Arguments args2549; args2549.Add(([&]() -> Value { auto fn2550 = s->Global("_get"); Arguments args2551; args2551.positional.reserve(3); args2551.Add(s->LocalAt(1), false); args2551.Add(Value("maxMarketOrdersPerTurn"), false); args2551.Add(Value(int64_t{10}), false); return Call(c, fn2550, std::move(args2551)); }()), false); return Call(c, fn2548, std::move(args2549)); }()), false); return Call(c, fn2546, std::move(args2547)); }());
s->SetAt(3, v2545);
if (static_cast<bool>(([&]() -> Value { auto v2552 = ([&]() -> Value { auto v2553 = s->LocalAt(0); Value v2554; v2554 = Value(int64_t{1}); if (!static_cast<bool>(Binary("Lt", v2553, v2554))) return Value(false); v2553 = v2554; return Value(true); }()); if (static_cast<bool>(v2552)) return v2552; v2552 = ([&]() -> Value { auto v2555 = s->LocalAt(3); Value v2556; v2556 = Value(int64_t{1}); if (!static_cast<bool>(Binary("Lt", v2555, v2556))) return Value(false); v2555 = v2556; return Value(true); }()); return v2552; }()))) {
Raise(([&]() -> Value { auto fn2557 = s->Global("Unsupported"); Arguments args2558; args2558.Add(Value("invalid capacity/order limit"), false); return Call(c, fn2557, std::move(args2558)); }()));
}
return Tuple({s->LocalAt(4), s->LocalAt(5), s->LocalAt(0), s->LocalAt(3)});
return {};
}
}  // namespace kagg::opponents::compiled
