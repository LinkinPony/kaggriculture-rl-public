// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_0e384ca5b18674556aee(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"a", "command", "commands", "end", "pos", "step", "t", "tape", "target", "unit", "units", "walk"};
s->PrepareSlots(s_names);
if (static_cast<bool>(([&]() -> Value { auto v20587 = Get(s->LocalAt(2), s->LocalAt(9)); if (!static_cast<bool>(v20587)) return v20587; v20587 = ([&]() -> Value { auto v20588 = Get(Get(s->LocalAt(2), s->LocalAt(9)), Value(int64_t{0})); Value v20589; v20589 = s->Global("_V9_COURIER_IDLE"); if (!static_cast<bool>(Binary("NotIn", v20588, v20589))) return Value(false); v20588 = v20589; return Value(true); }()); return v20587; }()))) {
return Value{};
}
for (const auto& item20590 : Iterate(([&]() -> Value { auto fn20591 = s->Global("range"); Arguments args20592; args20592.positional.reserve(2); args20592.Add(([&]() -> Value { auto v20593 = s->LocalAt(5); return Binary("Add", v20593, Value(int64_t{1})); }()), false); args20592.Add(([&]() -> Value { auto v20594 = s->LocalAt(3); return Binary("Add", v20594, Value(int64_t{1})); }()), false); return Call(c, fn20591, std::move(args20592)); }()))) {
s->SetAt(6, item20590);
auto v20595 = (static_cast<bool>(([&]() -> Value { auto v20596 = s->LocalAt(6); Value v20597; v20597 = ([&]() -> Value { auto fn20598 = s->Global("len"); Arguments args20599; args20599.Add(s->LocalAt(7), false); return Call(c, fn20598, std::move(args20599)); }()); if (!static_cast<bool>(Binary("Lt", v20596, v20597))) return Value(false); v20596 = v20597; return Value(true); }())) ? Get(s->LocalAt(7), s->LocalAt(6)) : ([&]() -> Value { auto dict20600 = Dict(); return dict20600; }()));
s->SetAt(0, v20595);
auto v20601 = ([&]() -> Value { auto v20602 = List({([&]() -> Value { auto v20603 = ([&]() -> Value { auto fn20604 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args20605; args20605.Add(Value("farmer"), false); return CallDictionaryGet(c, fn20604, std::move(args20605)); }()); if (static_cast<bool>(v20603)) return v20603; v20603 = List({Value("PASS")}); return v20603; }())}); return Binary("Add", v20602, ([&]() -> Value { auto fn20606 = s->Global("list"); Arguments args20607; args20607.Add(([&]() -> Value { auto v20608 = ([&]() -> Value { auto fn20609 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args20610; args20610.Add(Value("hands"), false); return CallDictionaryGet(c, fn20609, std::move(args20610)); }()); if (static_cast<bool>(v20608)) return v20608; v20608 = List({}); return v20608; }()), false); return Call(c, fn20606, std::move(args20607)); }())); }());
s->SetAt(10, v20601);
auto v20611 = (static_cast<bool>(([&]() -> Value { auto v20612 = s->LocalAt(9); Value v20613; v20613 = ([&]() -> Value { auto fn20614 = s->Global("len"); Arguments args20615; args20615.Add(s->LocalAt(10), false); return Call(c, fn20614, std::move(args20615)); }()); if (!static_cast<bool>(Binary("Lt", v20612, v20613))) return Value(false); v20612 = v20613; return Value(true); }())) ? Get(s->LocalAt(10), s->LocalAt(9)) : List({Value("PASS")}));
s->SetAt(1, v20611);
if (static_cast<bool>(([&]() -> Value { auto v20616 = s->LocalAt(1); if (!static_cast<bool>(v20616)) return v20616; v20616 = ([&]() -> Value { auto v20617 = Get(s->LocalAt(1), Value(int64_t{0})); Value v20618; v20618 = s->Global("_V9_COURIER_IDLE"); if (!static_cast<bool>(Binary("NotIn", v20617, v20618))) return Value(false); v20617 = v20618; return Value(true); }()); return v20616; }()))) {
return Value{};
}
}
auto v20619 = ([&]() -> Value { auto fn20620 = s->Global("min"); Arguments args20621; args20621.Add(s->Global("_V9_COURIER_ACCESS"), false); args20621.Keyword("key", Define(&Code_f515a458958c46d29348, s, Signature{{"a"}, {}, {}, {}, "", "", ([]() -> std::span<const char* const> { static constexpr const char* names[] = {"a"}; return names; }())}, true, "<lambda>")); return Call(c, fn20620, std::move(args20621)); }());
s->SetAt(8, v20619);
auto v20629 = ([&]() -> Value { auto fn20630 = s->Global("_v9_courier_walk"); Arguments args20631; args20631.positional.reserve(2); args20631.Add(s->LocalAt(4), false); args20631.Add(s->LocalAt(8), false); return Call(c, fn20630, std::move(args20631)); }());
s->SetAt(11, v20629);
return (static_cast<bool>(([&]() -> Value { auto v20632 = ([&]() -> Value { auto fn20634 = s->Global("len"); Arguments args20635; args20635.Add(s->LocalAt(11), false); return Call(c, fn20634, std::move(args20635)); }()); Value v20633; v20633 = ([&]() -> Value { auto v20636 = s->LocalAt(3); return Binary("Sub", v20636, s->LocalAt(5)); }()); if (!static_cast<bool>(Binary("LtE", v20632, v20633))) return Value(false); v20632 = v20633; return Value(true); }())) ? ([&]() -> Value { auto v20637 = s->LocalAt(11); return Binary("Add", v20637, List({List({Value("DROP")})})); }()) : Value{});
return {};
}
}  // namespace kagg::opponents::compiled
