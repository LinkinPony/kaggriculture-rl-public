// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_f4c7d0c9d9f3739bd552(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "configuration", "name", "observation", "seat", "state", "step"};
s->PrepareSlots(s_names);
auto v5712 = ([&]() -> Value { auto fn5713 = s->Global("int"); Arguments args5714; args5714.Add(Get(s->LocalAt(3), Value("step")), false); return Call(c, fn5713, std::move(args5714)); }());
s->SetAt(6, v5712);
auto v5715 = ([&]() -> Value { auto fn5716 = s->Global("int"); Arguments args5717; args5717.Add(Get(s->LocalAt(3), Value("player")), false); return Call(c, fn5716, std::move(args5717)); }());
s->SetAt(4, v5715);
auto v5718 = ([&]() -> Value { auto fn5719 = PrepareDictionaryGet(s->Global("_V231_STATES")); Arguments args5720; args5720.Add(s->LocalAt(4), false); return CallDictionaryGet(c, fn5719, std::move(args5720)); }());
s->SetAt(5, v5718);
if (static_cast<bool>(([&]() -> Value { auto v5721 = ([&]() -> Value { auto v5722 = s->LocalAt(5); Value v5723; v5723 = Value{}; if (!static_cast<bool>(Binary("Is", v5722, v5723))) return Value(false); v5722 = v5723; return Value(true); }()); if (static_cast<bool>(v5721)) return v5721; v5721 = ([&]() -> Value { auto v5724 = s->LocalAt(6); Value v5725; v5725 = Get(s->LocalAt(5), Value("last")); if (!static_cast<bool>(Binary("LtE", v5724, v5725))) return Value(false); v5724 = v5725; return Value(true); }()); return v5721; }()))) {
auto v5726 = ([&]() -> Value { auto fn5727 = s->Global("_v231_new_state"); Arguments args5728; return Call(c, fn5727, std::move(args5728)); }());
s->SetAt(5, v5726);
Put(s->Global("_V231_STATES"), s->LocalAt(4), v5726);
}
auto v5729 = ([&]() -> Value { auto fn5730 = s->Global("_V231_PARENT"); Arguments args5731; args5731.positional.reserve(2); args5731.Add(s->LocalAt(3), false); args5731.Add(s->LocalAt(1), false); return Call(c, fn5730, std::move(args5731)); }());
s->SetAt(0, v5729);
auto v5732 = ([&]() -> Value { auto fn5733 = s->Global("_v231_controller"); Arguments args5734; args5734.positional.reserve(4); args5734.Add(s->LocalAt(3), false); args5734.Add(s->LocalAt(0), false); args5734.Add(s->LocalAt(5), false); args5734.Add(s->Global("_V231_CAP"), false); return Call(c, fn5733, std::move(args5734)); }());
s->SetAt(0, v5732);
(void)([&]() -> Value { auto fn5735 = Attribute(s->Global("_V231_REPORT"), "clear"); Arguments args5736; return Call(c, fn5735, std::move(args5736)); }());
(void)([&]() -> Value { auto fn5737 = Attribute(s->Global("_V231_REPORT"), "update"); Arguments args5738; args5738.Add(Attribute(s->Global("_V231_PARENT"), "telemetry"), false); return Call(c, fn5737, std::move(args5738)); }());
for (const auto& item5739 : Iterate(Tuple({Value("confirmed"), Value("reserved"), Value("requested"), Value("failed_purchase_units"), Value("picked"), Value("placed"), Value("failed_placements"), Value("extra_milk_harvested"), Value("extra_milk_sale_requests"), Value("milk_credit")}))) {
s->SetAt(2, item5739);
auto v5740 = Get(s->LocalAt(5), s->LocalAt(2));
Put(s->Global("_V231_REPORT"), ([&]() -> Value { auto v5741 = Value("cattle_"); return Binary("Add", v5741, s->LocalAt(2)); }()), v5740);
}
auto v5742 = ([&]() -> Value { auto fn5743 = s->Global("sum"); Arguments args5744; args5744.Add(([&]() -> Value { auto fn5745 = Attribute(Get(s->LocalAt(5), Value("carrying")), "values"); Arguments args5746; return Call(c, fn5745, std::move(args5746)); }()), false); return Call(c, fn5743, std::move(args5744)); }());
Put(s->Global("_V231_REPORT"), Value("cattle_carried_pending"), v5742);
return s->LocalAt(0);
return {};
}
}  // namespace kagg::opponents::compiled
