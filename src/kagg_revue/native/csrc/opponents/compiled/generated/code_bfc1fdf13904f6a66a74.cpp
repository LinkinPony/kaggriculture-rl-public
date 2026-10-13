// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_bfc1fdf13904f6a66a74(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"draw", "item", "items", "shop", "shops", "step"};
s->PrepareSlots(s_names);
auto v27204 = ([&]() -> Value { auto fn27205 = Attribute(s->Global("dict"), "fromkeys"); Arguments args27206; args27206.positional.reserve(2); args27206.Add(s->Global("V9_RACE_ITEMS"), false); args27206.Add(Value(int64_t{0}), false); return Call(c, fn27205, std::move(args27206)); }());
s->SetAt(0, v27204);
if (static_cast<bool>(([&]() -> Value { auto v27207 = ([&]() -> Value { auto v27209 = s->LocalAt(5); return Binary("Mod", v27209, Value(int64_t{4})); }()); Value v27208; v27208 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v27207, v27208))) return Value(false); v27207 = v27208; return Value(true); }()))) {
for (const auto& item27210 : Iterate(s->LocalAt(4))) {
s->SetAt(3, item27210);
auto v27211 = ([&]() -> Value { auto fn27212 = PrepareDictionaryGet(s->Global("_V9_SHOP_ITEMS")); Arguments args27213; args27213.positional.reserve(2); args27213.Add(s->LocalAt(3), false); args27213.Add(Tuple({}), false); return CallDictionaryGet(c, fn27212, std::move(args27213)); }());
s->SetAt(2, v27211);
for (const auto& item27214 : Iterate(s->LocalAt(2))) {
s->SetAt(1, item27214);
if (static_cast<bool>(([&]() -> Value { auto v27215 = s->LocalAt(1); Value v27216; v27216 = s->LocalAt(0); if (!static_cast<bool>(Binary("In", v27215, v27216))) return Value(false); v27215 = v27216; return Value(true); }()))) {
auto v27217 = s->LocalAt(0);
auto v27218 = s->LocalAt(1);
auto v27219 = Get(v27217, v27218);
Put(v27217, v27218, Inplace("Add", v27219, (static_cast<bool>(([&]() -> Value { auto v27220 = ([&]() -> Value { auto fn27222 = s->Global("len"); Arguments args27223; args27223.Add(s->LocalAt(2), false); return Call(c, fn27222, std::move(args27223)); }()); Value v27221; v27221 = Value(int64_t{1}); if (!static_cast<bool>(Binary("Eq", v27220, v27221))) return Value(false); v27220 = v27221; return Value(true); }())) ? Value(int64_t{2}) : Value(int64_t{1}))));
}
}
}
}
if (static_cast<bool>(([&]() -> Value { auto v27224 = ([&]() -> Value { auto v27226 = s->LocalAt(5); return Binary("Mod", v27226, Value(int64_t{24})); }()); Value v27225; v27225 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v27224, v27225))) return Value(false); v27224 = v27225; return Value(true); }()))) {
for (const auto& item27227 : Iterate(s->LocalAt(0))) {
s->SetAt(1, item27227);
auto v27228 = s->LocalAt(0);
auto v27229 = s->LocalAt(1);
auto v27230 = Get(v27228, v27229);
Put(v27228, v27229, Inplace("Add", v27230, Value(int64_t{1})));
}
}
return s->LocalAt(0);
return {};
}
}  // namespace kagg::opponents::compiled
