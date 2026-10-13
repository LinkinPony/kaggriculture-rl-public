// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_ecb7a2e03cfad3a5ebdf(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"evs", "index", "n", "parity"};
s->PrepareSlots(s_names);
auto v29479 = (static_cast<bool>(([&]() -> Value { auto v29480 = s->Global("_V92_EP"); Value v29481; v29481 = Value{}; if (!static_cast<bool>(Binary("Is", v29480, v29481))) return Value(false); v29480 = v29481; return Value(true); }())) ? Value{} : ([&]() -> Value { auto v29482 = s->Global("_V92_EP"); return Binary("Mod", v29482, Value(int64_t{2})); }()));
s->SetAt(3, v29479);
auto v29483 = ([&]() -> Value { auto fn29484 = s->Global("_v92_q_index"); Arguments args29485; args29485.Add(s->LocalAt(3), false); return Call(c, fn29484, std::move(args29485)); }());
auto unpack29486 = Iterate(v29483);
ValidateUnpack(unpack29486, 2, false);
s->SetAt(0, unpack29486.at(0));
s->SetAt(1, unpack29486.at(1));
auto v29487 = ([&]() -> Value { auto fn29488 = s->Global("len"); Arguments args29489; args29489.Add(s->LocalAt(0), false); return Call(c, fn29488, std::move(args29489)); }());
s->SetAt(2, v29487);
return ([&]() -> Value { auto dict29490 = Dict(); auto key29491 = Value("step"); Put(dict29490, key29491, Unary("USub", Value(int64_t{1}))); auto key29492 = Value("obs"); Put(dict29490, key29492, ([&]() -> Value { auto dict29493 = Dict(); return dict29493; }())); auto key29494 = Value("evs"); Put(dict29490, key29494, s->LocalAt(0)); auto key29495 = Value("index"); Put(dict29490, key29495, s->LocalAt(1)); auto key29496 = Value("m"); Put(dict29490, key29496, ([&]() -> Value { auto v29497 = List({Value(int64_t{0})}); return Binary("Mult", v29497, s->LocalAt(2)); }())); auto key29498 = Value("f"); Put(dict29490, key29498, ([&]() -> Value { auto v29499 = List({Value(int64_t{0})}); return Binary("Mult", v29499, s->LocalAt(2)); }())); auto key29500 = Value("near"); Put(dict29490, key29500, ([&]() -> Value { auto v29501 = List({Value(int64_t{0})}); return Binary("Mult", v29501, s->LocalAt(2)); }())); auto key29502 = Value("score"); Put(dict29490, key29502, ([&]() -> Value { auto v29503 = List({Value(0.0)}); return Binary("Mult", v29503, s->LocalAt(2)); }())); auto key29504 = Value("best"); Put(dict29490, key29504, (static_cast<bool>(s->LocalAt(2)) ? Value(int64_t{0}) : Value{})); auto key29505 = Value("done"); Put(dict29490, key29505, Value(int64_t{150})); return dict29490; }());
return {};
}
}  // namespace kagg::opponents::compiled
