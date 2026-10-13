// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_c8076df2398a4a015390(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"egg_shops", "milk_shops", "obs", "prices", "shops"};
s->PrepareSlots(s_names);
auto v21240 = Get(Get(s->LocalAt(2), Value("town")), Value("unlocked_shops"));
s->SetAt(4, v21240);
auto v21241 = Get(Get(s->LocalAt(2), Value("market")), Value("prices"));
s->SetAt(3, v21241);
auto v21242 = ([&]() -> Value { auto fn21243 = s->Global("sum"); Arguments args21244; args21244.Add(([&]() -> Value { auto comp21245 = std::make_shared<Scope>(); comp21245->globals = s->globals; comp21245->parent = s; static constexpr const char* comp21245_names[] = {"s"}; comp21245->PrepareSlots(comp21245_names); auto result21246 = List(); for (const auto& item21247 : Iterate(s->LocalAt(4))) { comp21245->SetAt(0, item21247); result21246.node()->sequence.push_back(([&]() -> Value { auto v21248 = comp21245->LocalAt(0); Value v21249; v21249 = Tuple({Value("BAKERY"), Value("BRUNCH_SPOT")}); if (!static_cast<bool>(Binary("In", v21248, v21249))) return Value(false); v21248 = v21249; return Value(true); }())); } return result21246; }()), false); return Call(c, fn21243, std::move(args21244)); }());
s->SetAt(0, v21242);
if (static_cast<bool>(([&]() -> Value { auto v21250 = ([&]() -> Value { auto v21251 = s->LocalAt(0); Value v21252; v21252 = s->Global("V9_HERD_MAX_EGG_SHOPS"); if (!static_cast<bool>(Binary("LtE", v21251, v21252))) return Value(false); v21251 = v21252; return Value(true); }()); if (!static_cast<bool>(v21250)) return v21250; v21250 = ([&]() -> Value { auto v21253 = Value("YARN_STORE"); Value v21254; v21254 = s->LocalAt(4); if (!static_cast<bool>(Binary("In", v21253, v21254))) return Value(false); v21253 = v21254; return Value(true); }()); if (!static_cast<bool>(v21250)) return v21250; v21250 = ([&]() -> Value { auto v21255 = ([&]() -> Value { auto fn21257 = s->Global("int"); Arguments args21258; args21258.Add(([&]() -> Value { auto fn21259 = PrepareDictionaryGet(s->LocalAt(3)); Arguments args21260; args21260.positional.reserve(2); args21260.Add(Value("WOOL"), false); args21260.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn21259, std::move(args21260)); }()), false); return Call(c, fn21257, std::move(args21258)); }()); Value v21256; v21256 = s->Global("V9_HERD_MIN_WOOL"); if (!static_cast<bool>(Binary("GtE", v21255, v21256))) return Value(false); v21255 = v21256; return Value(true); }()); return v21250; }()))) {
return Value("SHEEP");
}
auto v21261 = ([&]() -> Value { auto fn21262 = s->Global("sum"); Arguments args21263; args21263.Add(([&]() -> Value { auto comp21264 = std::make_shared<Scope>(); comp21264->globals = s->globals; comp21264->parent = s; static constexpr const char* comp21264_names[] = {"s"}; comp21264->PrepareSlots(comp21264_names); auto result21265 = List(); for (const auto& item21266 : Iterate(s->LocalAt(4))) { comp21264->SetAt(0, item21266); result21265.node()->sequence.push_back(([&]() -> Value { auto v21267 = comp21264->LocalAt(0); Value v21268; v21268 = Tuple({Value("PIZZA_SHOP"), Value("ICE_CREAM_SHOP"), Value("SMOOTHIE_SHOP")}); if (!static_cast<bool>(Binary("In", v21267, v21268))) return Value(false); v21267 = v21268; return Value(true); }())); } return result21265; }()), false); return Call(c, fn21262, std::move(args21263)); }());
s->SetAt(1, v21261);
if (static_cast<bool>(([&]() -> Value { auto v21269 = ([&]() -> Value { auto v21270 = s->LocalAt(0); Value v21271; v21271 = s->Global("V9_HERD_MAX_EGG_SHOPS_COW"); if (!static_cast<bool>(Binary("LtE", v21270, v21271))) return Value(false); v21270 = v21271; return Value(true); }()); if (!static_cast<bool>(v21269)) return v21269; v21269 = ([&]() -> Value { auto v21272 = s->LocalAt(1); Value v21273; v21273 = s->Global("V9_HERD_MIN_MILK_SHOPS"); if (!static_cast<bool>(Binary("GtE", v21272, v21273))) return Value(false); v21272 = v21273; return Value(true); }()); if (!static_cast<bool>(v21269)) return v21269; v21269 = ([&]() -> Value { auto v21274 = ([&]() -> Value { auto fn21276 = s->Global("int"); Arguments args21277; args21277.Add(([&]() -> Value { auto fn21278 = PrepareDictionaryGet(s->LocalAt(3)); Arguments args21279; args21279.positional.reserve(2); args21279.Add(Value("MILK"), false); args21279.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn21278, std::move(args21279)); }()), false); return Call(c, fn21276, std::move(args21277)); }()); Value v21275; v21275 = s->Global("V9_HERD_MIN_MILK"); if (!static_cast<bool>(Binary("GtE", v21274, v21275))) return Value(false); v21274 = v21275; return Value(true); }()); return v21269; }()))) {
return Value("COW");
}
return Value{};
return {};
}
}  // namespace kagg::opponents::compiled
