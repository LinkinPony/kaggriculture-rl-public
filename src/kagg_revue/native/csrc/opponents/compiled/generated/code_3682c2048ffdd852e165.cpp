// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_3682c2048ffdd852e165(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "configuration", "observation", "player", "probe_state", "state", "step"};
s->PrepareSlots(s_names);
auto v6550 = Tuple({([&]() -> Value { auto fn6551 = s->Global("int"); Arguments args6552; args6552.Add(Get(s->LocalAt(2), Value("player")), false); return Call(c, fn6551, std::move(args6552)); }()), ([&]() -> Value { auto fn6553 = s->Global("int"); Arguments args6554; args6554.Add(Get(s->LocalAt(2), Value("step")), false); return Call(c, fn6553, std::move(args6554)); }())});
auto unpack6555 = Iterate(v6550);
ValidateUnpack(unpack6555, 2, false);
s->SetAt(3, unpack6555.at(0));
s->SetAt(6, unpack6555.at(1));
auto v6556 = ([&]() -> Value { auto fn6557 = PrepareDictionaryGet(s->Global("_R37_PLAYERS")); Arguments args6558; args6558.Add(s->LocalAt(3), false); return CallDictionaryGet(c, fn6557, std::move(args6558)); }());
s->SetAt(5, v6556);
if (static_cast<bool>(([&]() -> Value { auto v6559 = ([&]() -> Value { auto v6560 = s->LocalAt(5); Value v6561; v6561 = Value{}; if (!static_cast<bool>(Binary("Is", v6560, v6561))) return Value(false); v6560 = v6561; return Value(true); }()); if (static_cast<bool>(v6559)) return v6559; v6559 = ([&]() -> Value { auto v6562 = s->LocalAt(6); Value v6563; v6563 = Get(s->LocalAt(5), Value("step")); if (!static_cast<bool>(Binary("LtE", v6562, v6563))) return Value(false); v6562 = v6563; return Value(true); }()); return v6559; }()))) {
auto v6564 = ([&]() -> Value { auto dict6565 = Dict(); auto key6566 = Value("step"); Put(dict6565, key6566, Unary("USub", Value(int64_t{1}))); auto key6567 = Value("streak"); Put(dict6565, key6567, Value(int64_t{0})); return dict6565; }());
s->SetAt(5, v6564);
Put(s->Global("_R37_PLAYERS"), s->LocalAt(3), v6564);
}
if (static_cast<bool>(([&]() -> Value { auto v6568 = s->LocalAt(6); Value v6569; v6569 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v6568, v6569))) return Value(false); v6568 = v6569; return Value(true); }()))) {
(void)([&]() -> Value { auto fn6570 = Attribute(s->Global("_R37_STATS"), "update"); Arguments args6571; args6571.Keyword("quote_reordered_turns", Value(int64_t{0})); args6571.Keyword("three_turn_calls", Value(int64_t{0})); args6571.Keyword("nocturne_errors", Value(int64_t{0})); return Call(c, fn6570, std::move(args6571)); }());
}
auto v6572 = s->LocalAt(6);
Put(s->LocalAt(5), Value("step"), v6572);
auto v6573 = Value(int64_t{2});
Put(s->Global("_R37_HORIZONS"), s->LocalAt(3), v6573);
auto v6574 = ([&]() -> Value { auto fn6575 = s->Global("_r44_before"); Arguments args6576; args6576.Add(s->LocalAt(2), false); return Call(c, fn6575, std::move(args6576)); }());
s->SetAt(4, v6574);
try {
if (static_cast<bool>(([&]() -> Value { auto v6578 = s->Global("_R37_ADAPTIVE"); if (!static_cast<bool>(v6578)) return v6578; v6578 = ([&]() -> Value { auto v6579 = s->LocalAt(6); Value v6580; v6580 = Value(int64_t{648}); if (!static_cast<bool>(Binary("Lt", v6579, v6580))) return Value(false); v6579 = v6580; return Value(true); }()); return v6578; }()))) {
auto v6581 = (static_cast<bool>(([&]() -> Value { auto v6582 = ([&]() -> Value { auto fn6584 = s->Global("_r37_similarity"); Arguments args6585; args6585.Add(s->LocalAt(2), false); return Call(c, fn6584, std::move(args6585)); }()); Value v6583; v6583 = Value(0.9); if (!static_cast<bool>(Binary("GtE", v6582, v6583))) return Value(false); v6582 = v6583; return Value(true); }())) ? ([&]() -> Value { auto v6586 = Get(s->LocalAt(5), Value("streak")); return Binary("Add", v6586, Value(int64_t{1})); }()) : Value(int64_t{0}));
Put(s->LocalAt(5), Value("streak"), v6581);
if (static_cast<bool>(([&]() -> Value { auto v6587 = ([&]() -> Value { auto v6588 = Value(int64_t{336}); Value v6589; v6589 = s->LocalAt(6); if (!static_cast<bool>(Binary("LtE", v6588, v6589))) return Value(false); v6588 = v6589; v6589 = Value(int64_t{648}); if (!static_cast<bool>(Binary("Lt", v6588, v6589))) return Value(false); v6588 = v6589; return Value(true); }()); if (!static_cast<bool>(v6587)) return v6587; v6587 = ([&]() -> Value { auto v6590 = Get(s->LocalAt(5), Value("streak")); Value v6591; v6591 = Value(int64_t{6}); if (!static_cast<bool>(Binary("GtE", v6590, v6591))) return Value(false); v6590 = v6591; return Value(true); }()); return v6587; }()))) {
auto v6592 = Value(int64_t{3});
Put(s->Global("_R37_HORIZONS"), s->LocalAt(3), v6592);
auto v6593 = s->Global("_R37_STATS");
auto v6594 = Value("three_turn_calls");
auto v6595 = Get(v6593, v6594);
Put(v6593, v6594, Inplace("Add", v6595, Value(int64_t{1})));
}
}
} catch (const Error& error6577) {
if (Matches(error6577, s->Global("Exception"))) {
auto v6596 = s->Global("_R37_STATS");
auto v6597 = Value("nocturne_errors");
auto v6598 = Get(v6596, v6597);
Put(v6596, v6597, Inplace("Add", v6598, Value(int64_t{1})));
}
else { throw; }
}
if (static_cast<bool>(([&]() -> Value { auto v6599 = ([&]() -> Value { auto v6600 = Get(s->Global("_R37_HORIZONS"), s->LocalAt(3)); Value v6601; v6601 = Value(int64_t{3}); if (!static_cast<bool>(Binary("Eq", v6600, v6601))) return Value(false); v6600 = v6601; return Value(true); }()); if (!static_cast<bool>(v6599)) return v6599; v6599 = Get(s->LocalAt(4), Value("matched")); return v6599; }()))) {
auto v6602 = Value(int64_t{4});
Put(s->Global("_R37_HORIZONS"), s->LocalAt(3), v6602);
auto v6603 = s->Global("_R44_REPORT");
auto v6604 = Value("probe_four_turn_calls");
auto v6605 = Get(v6603, v6604);
Put(v6603, v6604, Inplace("Add", v6605, Value(int64_t{1})));
}
if (static_cast<bool>(([&]() -> Value { auto v6606 = Value(int64_t{288}); Value v6607; v6607 = s->LocalAt(6); if (!static_cast<bool>(Binary("LtE", v6606, v6607))) return Value(false); v6606 = v6607; v6607 = Value(int64_t{696}); if (!static_cast<bool>(Binary("Lt", v6606, v6607))) return Value(false); v6606 = v6607; return Value(true); }()))) {
auto v6608 = Value(int64_t{4});
Put(s->Global("_R37_HORIZONS"), s->LocalAt(3), v6608);
}
auto v6609 = ([&]() -> Value { auto fn6610 = s->Global("_R37_PARENT"); Arguments args6611; args6611.positional.reserve(2); args6611.Add(s->LocalAt(2), false); args6611.Add(s->LocalAt(1), false); return Call(c, fn6610, std::move(args6611)); }());
s->SetAt(0, v6609);
(void)([&]() -> Value { auto fn6612 = s->Global("_r44_after"); Arguments args6613; args6613.positional.reserve(3); args6613.Add(s->LocalAt(2), false); args6613.Add(s->LocalAt(0), false); args6613.Add(s->LocalAt(4), false); return Call(c, fn6612, std::move(args6613)); }());
if (static_cast<bool>(([&]() -> Value { auto v6614 = s->Global("_R37_QUOTE"); if (!static_cast<bool>(v6614)) return v6614; v6614 = ([&]() -> Value { auto v6615 = s->LocalAt(6); Value v6616; v6616 = Value(int64_t{288}); if (!static_cast<bool>(Binary("GtE", v6615, v6616))) return Value(false); v6615 = v6616; return Value(true); }()); return v6614; }()))) {
try {
auto v6618 = ([&]() -> Value { auto fn6619 = s->Global("_r37_reorder_sales"); Arguments args6620; args6620.positional.reserve(2); args6620.Add(s->LocalAt(2), false); args6620.Add(s->LocalAt(0), false); return Call(c, fn6619, std::move(args6620)); }());
s->SetAt(0, v6618);
} catch (const Error& error6617) {
if (Matches(error6617, s->Global("Exception"))) {
auto v6621 = s->Global("_R37_STATS");
auto v6622 = Value("nocturne_errors");
auto v6623 = Get(v6621, v6622);
Put(v6621, v6622, Inplace("Add", v6623, Value(int64_t{1})));
}
else { throw; }
}
}
(void)([&]() -> Value { auto fn6624 = Attribute(s->Global("_R37_REPORT"), "update"); Arguments args6625; args6625.Add(([&]() -> Value { auto fn6626 = s->Global("getattr"); Arguments args6627; args6627.positional.reserve(3); args6627.Add(s->Global("_R37_PARENT"), false); args6627.Add(Value("telemetry"), false); args6627.Add(([&]() -> Value { auto dict6628 = Dict(); return dict6628; }()), false); return Call(c, fn6626, std::move(args6627)); }()), false); return Call(c, fn6624, std::move(args6625)); }());
(void)([&]() -> Value { auto fn6629 = Attribute(s->Global("_R37_REPORT"), "update"); Arguments args6630; args6630.Add(s->Global("_R37_STATS"), false); return Call(c, fn6629, std::move(args6630)); }());
(void)([&]() -> Value { auto fn6631 = Attribute(s->Global("_R37_REPORT"), "update"); Arguments args6632; args6632.Add(s->Global("_R44_REPORT"), false); return Call(c, fn6631, std::move(args6632)); }());
return s->LocalAt(0);
return {};
}
}  // namespace kagg::opponents::compiled
