// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_4f2bae485e4b3a168896(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"item", "name", "products", "shops", "total"};
s->PrepareSlots(s_names);
auto v24204 = Value(0.0);
s->SetAt(4, v24204);
for (const auto& item24205 : Iterate(s->LocalAt(3))) {
s->SetAt(1, item24205);
auto v24206 = ([&]() -> Value { auto fn24207 = PrepareDictionaryGet(s->Global("_HD2_SHOP_TYPES")); Arguments args24208; args24208.positional.reserve(2); args24208.Add(s->LocalAt(1), false); args24208.Add(Tuple({}), false); return CallDictionaryGet(c, fn24207, std::move(args24208)); }());
s->SetAt(2, v24206);
if (static_cast<bool>(([&]() -> Value { auto v24209 = s->LocalAt(0); Value v24210; v24210 = s->LocalAt(2); if (!static_cast<bool>(Binary("In", v24209, v24210))) return Value(false); v24209 = v24210; return Value(true); }()))) {
auto v24211 = s->LocalAt(4);
s->SetAt(4, Inplace("Add", v24211, ([&]() -> Value { auto v24212 = Value(6.0); return Binary("Mult", v24212, (static_cast<bool>(([&]() -> Value { auto v24213 = ([&]() -> Value { auto fn24215 = s->Global("len"); Arguments args24216; args24216.Add(s->LocalAt(2), false); return Call(c, fn24215, std::move(args24216)); }()); Value v24214; v24214 = Value(int64_t{1}); if (!static_cast<bool>(Binary("Eq", v24213, v24214))) return Value(false); v24213 = v24214; return Value(true); }())) ? Value(int64_t{2}) : Value(int64_t{1}))); }())));
}
}
return s->LocalAt(4);
return {};
}
}  // namespace kagg::opponents::compiled
