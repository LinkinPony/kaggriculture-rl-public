// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_1fd8a91bd718ce14ae3e(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"c", "ev", "evs", "index", "k", "key", "parity"};
s->PrepareSlots(s_names);
auto v29451 = Tuple({Value("index"), s->LocalAt(6)});
s->SetAt(5, v29451);
if (static_cast<bool>(([&]() -> Value { auto v29452 = s->LocalAt(5); Value v29453; v29453 = s->Global("_V92_Q_CACHE"); if (!static_cast<bool>(Binary("NotIn", v29452, v29453))) return Value(false); v29452 = v29453; return Value(true); }()))) {
auto v29454 = ([&]() -> Value { auto comp29455 = std::make_shared<Scope>(); comp29455->globals = s->globals; comp29455->parent = s; static constexpr const char* comp29455_names[] = {"ep", "ev"}; comp29455->PrepareSlots(comp29455_names); auto result29456 = List(); for (const auto& item29457 : Iterate(([&]() -> Value { auto fn29458 = s->Global("_v92_q_streams"); Arguments args29459; return Call(c, fn29458, std::move(args29459)); }()))) { auto unpack29460 = Iterate(item29457); ValidateUnpack(unpack29460, 2, false); comp29455->SetAt(0, unpack29460.at(0)); comp29455->SetAt(1, unpack29460.at(1)); if (!static_cast<bool>(([&]() -> Value { auto v29461 = ([&]() -> Value { auto v29462 = comp29455->Captured("parity"); Value v29463; v29463 = Value{}; if (!static_cast<bool>(Binary("Is", v29462, v29463))) return Value(false); v29462 = v29463; return Value(true); }()); if (static_cast<bool>(v29461)) return v29461; v29461 = ([&]() -> Value { auto v29464 = ([&]() -> Value { auto v29466 = comp29455->LocalAt(0); return Binary("Mod", v29466, Value(int64_t{2})); }()); Value v29465; v29465 = comp29455->Captured("parity"); if (!static_cast<bool>(Binary("NotEq", v29464, v29465))) return Value(false); v29464 = v29465; return Value(true); }()); return v29461; }()))) continue; result29456.node()->sequence.push_back(comp29455->LocalAt(1)); } return result29456; }());
s->SetAt(2, v29454);
auto v29467 = ([&]() -> Value { auto dict29468 = Dict(); return dict29468; }());
s->SetAt(3, v29467);
for (const auto& item29469 : Iterate(([&]() -> Value { auto fn29470 = s->Global("enumerate"); Arguments args29471; args29471.Add(s->LocalAt(2), false); return Call(c, fn29470, std::move(args29471)); }()))) {
auto unpack29472 = Iterate(item29469);
ValidateUnpack(unpack29472, 2, false);
s->SetAt(0, unpack29472.at(0));
s->SetAt(1, unpack29472.at(1));
for (const auto& item29473 : Iterate(s->LocalAt(1))) {
s->SetAt(4, item29473);
(void)([&]() -> Value { auto fn29474 = Attribute(([&]() -> Value { auto fn29476 = Attribute(s->LocalAt(3), "setdefault"); Arguments args29477; args29477.positional.reserve(2); args29477.Add(s->LocalAt(4), false); args29477.Add(List({}), false); return Call(c, fn29476, std::move(args29477)); }()), "append"); Arguments args29475; args29475.Add(s->LocalAt(0), false); return Call(c, fn29474, std::move(args29475)); }());
}
}
auto v29478 = Tuple({s->LocalAt(2), s->LocalAt(3)});
Put(s->Global("_V92_Q_CACHE"), s->LocalAt(5), v29478);
}
return Get(s->Global("_V92_Q_CACHE"), s->LocalAt(5));
return {};
}
}  // namespace kagg::opponents::compiled
