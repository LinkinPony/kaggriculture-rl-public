// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_25069e2b85fb664a6c22(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"item", "observation", "params", "patch"};
s->PrepareSlots(s_names);
auto v15711 = ([&]() -> Value { auto comp15712 = std::make_shared<Scope>(); comp15712->globals = s->globals; comp15712->parent = s; static constexpr const char* comp15712_names[] = {"item", "values"}; comp15712->PrepareSlots(comp15712_names); auto result15713 = Dict(); for (const auto& item15714 : Iterate(([&]() -> Value { auto fn15715 = Attribute(s->Global("_R37_MARKET_PARAMS"), "items"); Arguments args15716; return Call(c, fn15715, std::move(args15716)); }()))) { auto unpack15717 = Iterate(item15714); ValidateUnpack(unpack15717, 2, false); comp15712->SetAt(0, unpack15717.at(0)); comp15712->SetAt(1, unpack15717.at(1)); Put(result15713, comp15712->LocalAt(0), ([&]() -> Value { auto fn15718 = comp15712->Global("dict"); Arguments args15719; args15719.Add(comp15712->LocalAt(1), false); return Call(c, fn15718, std::move(args15719)); }())); } return result15713; }());
s->SetAt(2, v15711);
for (const auto& item15720 : Iterate(([&]() -> Value { auto fn15721 = Attribute(([&]() -> Value { auto fn15723 = PrepareDictionaryGet(Get(s->LocalAt(1), Value("market"))); Arguments args15724; args15724.positional.reserve(2); args15724.Add(Value("params"), false); args15724.Add(([&]() -> Value { auto dict15725 = Dict(); return dict15725; }()), false); return CallDictionaryGet(c, fn15723, std::move(args15724)); }()), "items"); Arguments args15722; return Call(c, fn15721, std::move(args15722)); }()))) {
auto unpack15726 = Iterate(item15720);
ValidateUnpack(unpack15726, 2, false);
s->SetAt(0, unpack15726.at(0));
s->SetAt(3, unpack15726.at(1));
if (static_cast<bool>(([&]() -> Value { auto v15727 = s->LocalAt(0); Value v15728; v15728 = s->LocalAt(2); if (!static_cast<bool>(Binary("In", v15727, v15728))) return Value(false); v15727 = v15728; return Value(true); }()))) {
(void)([&]() -> Value { auto fn15729 = Attribute(Get(s->LocalAt(2), s->LocalAt(0)), "update"); Arguments args15730; args15730.Add(s->LocalAt(3), false); return Call(c, fn15729, std::move(args15730)); }());
}
}
return s->LocalAt(2);
return {};
}
}  // namespace kagg::opponents::compiled
