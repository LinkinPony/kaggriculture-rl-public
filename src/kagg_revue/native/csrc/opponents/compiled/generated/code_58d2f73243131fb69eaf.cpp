// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_58d2f73243131fb69eaf(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "item", "market", "max_orders", "merge", "order", "qty"};
s->PrepareSlots(s_names);
auto v936 = ([&]() -> Value { auto fn937 = Attribute(s->LocalAt(0), "setdefault"); Arguments args938; args938.positional.reserve(2); args938.Add(Value("market"), false); args938.Add(List({}), false); return Call(c, fn937, std::move(args938)); }());
s->SetAt(2, v936);
if (static_cast<bool>(s->LocalAt(4))) {
for (const auto& item939 : Iterate(s->LocalAt(2))) {
s->SetAt(5, item939);
if (static_cast<bool>(([&]() -> Value { auto v940 = s->LocalAt(5); if (!static_cast<bool>(v940)) return v940; v940 = ([&]() -> Value { auto v941 = Get(s->LocalAt(5), Value(int64_t{0})); Value v942; v942 = Value("SELL"); if (!static_cast<bool>(Binary("Eq", v941, v942))) return Value(false); v941 = v942; return Value(true); }()); if (!static_cast<bool>(v940)) return v940; v940 = ([&]() -> Value { auto v943 = Get(s->LocalAt(5), Value(int64_t{1})); Value v944; v944 = s->LocalAt(1); if (!static_cast<bool>(Binary("Eq", v943, v944))) return Value(false); v943 = v944; return Value(true); }()); return v940; }()))) {
auto v945 = ([&]() -> Value { auto v946 = ([&]() -> Value { auto fn947 = s->Global("_int"); Arguments args948; args948.Add(Get(s->LocalAt(5), Value(int64_t{2})), false); return Call(c, fn947, std::move(args948)); }()); return Binary("Add", v946, s->LocalAt(6)); }());
Put(s->LocalAt(5), Value(int64_t{2}), v945);
return Value(true);
}
}
}
if (static_cast<bool>(([&]() -> Value { auto v949 = ([&]() -> Value { auto fn951 = s->Global("len"); Arguments args952; args952.Add(s->LocalAt(2), false); return Call(c, fn951, std::move(args952)); }()); Value v950; v950 = s->LocalAt(3); if (!static_cast<bool>(Binary("GtE", v949, v950))) return Value(false); v949 = v950; return Value(true); }()))) {
return Value(false);
}
(void)([&]() -> Value { auto fn953 = Attribute(s->LocalAt(2), "append"); Arguments args954; args954.Add(List({Value("SELL"), s->LocalAt(1), s->LocalAt(6)}), false); return Call(c, fn953, std::move(args954)); }());
return Value(true);
return {};
}
}  // namespace kagg::opponents::compiled
