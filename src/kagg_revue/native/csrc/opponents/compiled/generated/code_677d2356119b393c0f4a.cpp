// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_677d2356119b393c0f4a(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"obs", "player", "st", "step"};
s->PrepareSlots(s_names);
auto v19560 = ([&]() -> Value { auto fn19561 = s->Global("int"); Arguments args19562; args19562.Add(Get(s->LocalAt(0), Value("player")), false); return Call(c, fn19561, std::move(args19562)); }());
s->SetAt(1, v19560);
auto v19563 = ([&]() -> Value { auto fn19564 = s->Global("int"); Arguments args19565; args19565.Add(Get(s->LocalAt(0), Value("step")), false); return Call(c, fn19564, std::move(args19565)); }());
s->SetAt(3, v19563);
auto v19566 = ([&]() -> Value { auto v19567 = ([&]() -> Value { auto fn19568 = PrepareDictionaryGet(s->Global("_RACE_STATE")); Arguments args19569; args19569.Add(s->LocalAt(1), false); return CallDictionaryGet(c, fn19568, std::move(args19569)); }()); if (static_cast<bool>(v19567)) return v19567; v19567 = ([&]() -> Value { auto dict19570 = Dict(); return dict19570; }()); return v19567; }());
s->SetAt(2, v19566);
if (static_cast<bool>(([&]() -> Value { auto v19571 = ([&]() -> Value { auto fn19573 = PrepareDictionaryGet(s->LocalAt(2)); Arguments args19574; args19574.positional.reserve(2); args19574.Add(Value("horizon"), false); args19574.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn19573, std::move(args19574)); }()); Value v19572; v19572 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v19571, v19572))) return Value(false); v19571 = v19572; return Value(true); }()))) {
return Value(true);
}
if (static_cast<bool>(([&]() -> Value { auto v19575 = ([&]() -> Value { auto v19576 = s->LocalAt(3); Value v19577; v19577 = Value(int64_t{696}); if (!static_cast<bool>(Binary("GtE", v19576, v19577))) return Value(false); v19576 = v19577; return Value(true); }()); if (!static_cast<bool>(v19575)) return v19575; v19575 = ([&]() -> Value { auto v19578 = ([&]() -> Value { auto fn19580 = s->Global("len"); Arguments args19581; args19581.Add(([&]() -> Value { auto fn19582 = PrepareDictionaryGet(s->LocalAt(2)); Arguments args19583; args19583.positional.reserve(2); args19583.Add(Value("hist"), false); args19583.Add(List({}), false); return CallDictionaryGet(c, fn19582, std::move(args19583)); }()), false); return Call(c, fn19580, std::move(args19581)); }()); Value v19579; v19579 = Value(int64_t{4}); if (!static_cast<bool>(Binary("GtE", v19578, v19579))) return Value(false); v19578 = v19579; return Value(true); }()); if (!static_cast<bool>(v19575)) return v19575; v19575 = ([&]() -> Value { auto v19584 = ([&]() -> Value { auto fn19586 = s->Global("sum"); Arguments args19587; args19587.Add(Get(s->LocalAt(2), Value("hist")), false); return Call(c, fn19586, std::move(args19587)); }()); Value v19585; v19585 = Value(int64_t{4}); if (!static_cast<bool>(Binary("GtE", v19584, v19585))) return Value(false); v19584 = v19585; return Value(true); }()); return v19575; }()))) {
return ([&]() -> Value { auto v19588 = ([&]() -> Value { auto fn19590 = s->Global("_r37_similarity"); Arguments args19591; args19591.Add(s->LocalAt(0), false); return Call(c, fn19590, std::move(args19591)); }()); Value v19589; v19589 = Value(0.95); if (!static_cast<bool>(Binary("GtE", v19588, v19589))) return Value(false); v19588 = v19589; return Value(true); }());
}
return Value(false);
return {};
}
}  // namespace kagg::opponents::compiled
