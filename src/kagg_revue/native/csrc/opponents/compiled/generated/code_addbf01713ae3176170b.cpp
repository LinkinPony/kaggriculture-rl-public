// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_addbf01713ae3176170b(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"player", "self", "st", "step"};
s->PrepareSlots(s_names);
auto v441 = ([&]() -> Value { auto fn442 = PrepareDictionaryGet(Attribute(s->LocalAt(1), "players")); Arguments args443; args443.Add(s->LocalAt(0), false); return CallDictionaryGet(c, fn442, std::move(args443)); }());
s->SetAt(2, v441);
if (static_cast<bool>(([&]() -> Value { auto v444 = ([&]() -> Value { auto v445 = s->LocalAt(2); Value v446; v446 = Value{}; if (!static_cast<bool>(Binary("Is", v445, v446))) return Value(false); v445 = v446; return Value(true); }()); if (static_cast<bool>(v444)) return v444; v444 = ([&]() -> Value { auto v447 = s->LocalAt(3); Value v448; v448 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v447, v448))) return Value(false); v447 = v448; return Value(true); }()); if (static_cast<bool>(v444)) return v444; v444 = ([&]() -> Value { auto v449 = s->LocalAt(3); Value v450; v450 = Get(s->LocalAt(2), Value("last_step")); if (!static_cast<bool>(Binary("LtE", v449, v450))) return Value(false); v449 = v450; return Value(true); }()); return v444; }()))) {
auto v451 = ([&]() -> Value { auto dict452 = Dict(); auto key453 = Value("last_step"); Put(dict452, key453, Unary("USub", Value(int64_t{1}))); auto key454 = Value("route"); Put(dict452, key454, Value{}); auto key455 = Value("router_state"); Put(dict452, key455, ([&]() -> Value { auto dict456 = Dict(); return dict456; }())); auto key457 = Value("pending"); Put(dict452, key457, ([&]() -> Value { auto dict458 = Dict(); return dict458; }())); auto key459 = Value("sell_state"); Put(dict452, key459, ([&]() -> Value { auto dict460 = Dict(); auto key461 = Value("due_step"); Put(dict460, key461, Unary("USub", Value(int64_t{1}))); auto key462 = Value("suppress"); Put(dict460, key462, ([&]() -> Value { auto dict463 = Dict(); return dict463; }())); return dict460; }())); return dict452; }());
s->SetAt(2, v451);
auto v464 = s->LocalAt(2);
Put(Attribute(s->LocalAt(1), "players"), s->LocalAt(0), v464);
}
auto v465 = s->LocalAt(3);
Put(s->LocalAt(2), Value("last_step"), v465);
return s->LocalAt(2);
return {};
}
}  // namespace kagg::opponents::compiled
