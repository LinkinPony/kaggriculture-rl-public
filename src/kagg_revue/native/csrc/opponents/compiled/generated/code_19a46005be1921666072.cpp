// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_19a46005be1921666072(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"before", "inv", "item", "native", "observation", "order", "pinv", "planned", "player", "prev", "prev_action", "prices", "rival", "sold", "state", "step", "town"};
s->PrepareSlots(s_names);
auto v18237 = ([&]() -> Value { auto fn18238 = PrepareDictionaryGet(s->LocalAt(14)); Arguments args18239; args18239.Add(Value("prev"), false); return CallDictionaryGet(c, fn18238, std::move(args18239)); }());
s->SetAt(9, v18237);
auto v18240 = ([&]() -> Value { auto fn18241 = PrepareDictionaryGet(s->LocalAt(14)); Arguments args18242; args18242.Add(Value("prev_action"), false); return CallDictionaryGet(c, fn18241, std::move(args18242)); }());
s->SetAt(10, v18240);
if (static_cast<bool>(([&]() -> Value { auto v18243 = ([&]() -> Value { auto v18244 = s->LocalAt(9); Value v18245; v18245 = Value{}; if (!static_cast<bool>(Binary("Is", v18244, v18245))) return Value(false); v18244 = v18245; return Value(true); }()); if (static_cast<bool>(v18243)) return v18243; v18243 = ([&]() -> Value { auto v18246 = s->LocalAt(10); Value v18247; v18247 = Value{}; if (!static_cast<bool>(Binary("Is", v18246, v18247))) return Value(false); v18246 = v18247; return Value(true); }()); return v18243; }()))) {
return Value(false);
}
auto v18248 = ([&]() -> Value { auto fn18249 = s->Global("int"); Arguments args18250; args18250.Add(Get(s->LocalAt(4), Value("step")), false); return Call(c, fn18249, std::move(args18250)); }());
s->SetAt(15, v18248);
auto v18251 = ([&]() -> Value { auto fn18252 = s->Global("int"); Arguments args18253; args18253.Add(Get(s->LocalAt(4), Value("player")), false); return Call(c, fn18252, std::move(args18253)); }());
s->SetAt(8, v18251);
if (static_cast<bool>(([&]() -> Value { auto v18254 = ([&]() -> Value { auto v18255 = s->LocalAt(15); Value v18256; v18256 = ([&]() -> Value { auto v18257 = Get(s->LocalAt(9), Value("step")); return Binary("Add", v18257, Value(int64_t{1})); }()); if (!static_cast<bool>(Binary("NotEq", v18255, v18256))) return Value(false); v18255 = v18256; return Value(true); }()); if (static_cast<bool>(v18254)) return v18254; v18254 = ([&]() -> Value { auto v18258 = ([&]() -> Value { auto v18260 = s->LocalAt(15); return Binary("Mod", v18260, Value(int64_t{24})); }()); Value v18259; v18259 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v18258, v18259))) return Value(false); v18258 = v18259; return Value(true); }()); return v18254; }()))) {
return Value(false);
}
auto v18261 = Get(Get(s->LocalAt(4), Value("market")), Value("inventory"));
s->SetAt(1, v18261);
auto v18262 = Get(s->LocalAt(9), Value("inventory"));
s->SetAt(6, v18262);
auto v18263 = Get(s->LocalAt(9), Value("prices"));
s->SetAt(11, v18263);
auto v18264 = ([&]() -> Value { auto fn18265 = s->Global("_race_town"); Arguments args18266; args18266.positional.reserve(2); args18266.Add(([&]() -> Value { auto v18267 = s->LocalAt(15); return Binary("Sub", v18267, Value(int64_t{1})); }()), false); args18266.Add(Get(s->LocalAt(9), Value("shops")), false); return Call(c, fn18265, std::move(args18266)); }());
s->SetAt(16, v18264);
auto v18268 = ([&]() -> Value { auto dict18269 = Dict(); return dict18269; }());
s->SetAt(13, v18268);
for (const auto& item18270 : Iterate(([&]() -> Value { auto fn18271 = PrepareDictionaryGet(s->LocalAt(10)); Arguments args18272; args18272.positional.reserve(2); args18272.Add(Value("market"), false); args18272.Add(List({}), false); return CallDictionaryGet(c, fn18271, std::move(args18272)); }()))) {
s->SetAt(5, item18270);
if (static_cast<bool>(([&]() -> Value { auto v18273 = ([&]() -> Value { auto v18274 = ([&]() -> Value { auto fn18276 = s->Global("len"); Arguments args18277; args18277.Add(s->LocalAt(5), false); return Call(c, fn18276, std::move(args18277)); }()); Value v18275; v18275 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v18274, v18275))) return Value(false); v18274 = v18275; return Value(true); }()); if (!static_cast<bool>(v18273)) return v18273; v18273 = ([&]() -> Value { auto v18278 = Get(s->LocalAt(5), Value(int64_t{0})); Value v18279; v18279 = Value("SELL"); if (!static_cast<bool>(Binary("Eq", v18278, v18279))) return Value(false); v18278 = v18279; return Value(true); }()); if (!static_cast<bool>(v18273)) return v18273; v18273 = ([&]() -> Value { auto v18280 = Get(s->LocalAt(5), Value(int64_t{1})); Value v18281; v18281 = s->Global("_RACE_ITEMS"); if (!static_cast<bool>(Binary("In", v18280, v18281))) return Value(false); v18280 = v18281; return Value(true); }()); return v18273; }()))) {
auto v18282 = Value(int64_t{1});
Put(s->LocalAt(13), Get(s->LocalAt(5), Value(int64_t{1})), v18282);
}
}
auto v18283 = Get(Attribute(Attribute(s->Global("_IMPL"), "chassis"), "players"), s->LocalAt(8));
s->SetAt(3, v18283);
for (const auto& item18284 : Iterate(s->Global("_RACE_ITEMS"))) {
s->SetAt(2, item18284);
auto v18285 = ([&]() -> Value { auto fn18286 = s->Global("int"); Arguments args18287; args18287.Add(([&]() -> Value { auto fn18288 = PrepareDictionaryGet(Attribute(Get(s->LocalAt(9), Value("view")), "shed")); Arguments args18289; args18289.positional.reserve(2); args18289.Add(s->LocalAt(2), false); args18289.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn18288, std::move(args18289)); }()), false); return Call(c, fn18286, std::move(args18287)); }());
s->SetAt(0, v18285);
if (static_cast<bool>(([&]() -> Value { auto v18290 = ([&]() -> Value { auto v18291 = s->LocalAt(0); Value v18292; v18292 = Value(int64_t{0}); if (!static_cast<bool>(Binary("LtE", v18291, v18292))) return Value(false); v18291 = v18292; return Value(true); }()); if (static_cast<bool>(v18290)) return v18290; v18290 = ([&]() -> Value { auto v18293 = s->LocalAt(2); Value v18294; v18294 = s->LocalAt(13); if (!static_cast<bool>(Binary("In", v18293, v18294))) return Value(false); v18293 = v18294; return Value(true); }()); if (static_cast<bool>(v18290)) return v18290; v18290 = ([&]() -> Value { auto v18295 = ([&]() -> Value { auto fn18297 = PrepareDictionaryGet(s->LocalAt(11)); Arguments args18298; args18298.positional.reserve(2); args18298.Add(s->LocalAt(2), false); args18298.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn18297, std::move(args18298)); }()); Value v18296; v18296 = Value(int64_t{1}); if (!static_cast<bool>(Binary("LtE", v18295, v18296))) return Value(false); v18295 = v18296; return Value(true); }()); return v18290; }()))) {
continue;
}
auto v18299 = ([&]() -> Value { auto v18300 = ([&]() -> Value { auto v18301 = ([&]() -> Value { auto fn18302 = s->Global("int"); Arguments args18303; args18303.Add(Get(s->LocalAt(1), s->LocalAt(2)), false); return Call(c, fn18302, std::move(args18303)); }()); return Binary("Sub", v18301, ([&]() -> Value { auto fn18304 = s->Global("int"); Arguments args18305; args18305.Add(Get(s->LocalAt(6), s->LocalAt(2)), false); return Call(c, fn18304, std::move(args18305)); }())); }()); return Binary("Add", v18300, ([&]() -> Value { auto fn18306 = PrepareDictionaryGet(s->LocalAt(16)); Arguments args18307; args18307.positional.reserve(2); args18307.Add(s->LocalAt(2), false); args18307.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn18306, std::move(args18307)); }())); }());
s->SetAt(12, v18299);
if (static_cast<bool>(([&]() -> Value { auto v18308 = s->LocalAt(12); Value v18309; v18309 = Value(int64_t{0}); if (!static_cast<bool>(Binary("LtE", v18308, v18309))) return Value(false); v18308 = v18309; return Value(true); }()))) {
continue;
}
s->SetAt(7, Define(&Code_76656203c26c7e595844, s, Signature{{"t"}, {}, {}, {}, "", "", ([]() -> std::span<const char* const> { static constexpr const char* names[] = {"future", "t"}; return names; }())}, true, "planned"));
s->definitions.push_back("planned");
if (static_cast<bool>(([&]() -> Value { auto comp18327 = std::make_shared<Scope>(); comp18327->globals = s->globals; comp18327->parent = s; static constexpr const char* comp18327_names[] = {"t"}; comp18327->PrepareSlots(comp18327_names); auto result18328 = List(); for (const auto& item18329 : Iterate(([&]() -> Value { auto fn18330 = s->Global("range"); Arguments args18331; args18331.positional.reserve(2); args18331.Add(([&]() -> Value { auto v18332 = s->LocalAt(15); return Binary("Sub", v18332, Value(int64_t{1})); }()), false); args18331.Add(([&]() -> Value { auto fn18333 = s->Global("min"); Arguments args18334; args18334.positional.reserve(2); args18334.Add(Value(int64_t{719}), false); args18334.Add(([&]() -> Value { auto v18335 = s->LocalAt(15); return Binary("Add", v18335, Value(int64_t{5})); }()), false); return Call(c, fn18333, std::move(args18334)); }()), false); return Call(c, fn18330, std::move(args18331)); }()))) { comp18327->SetAt(0, item18329); if (static_cast<bool>(([&]() -> Value { auto fn18336 = comp18327->Captured("planned"); Arguments args18337; args18337.Add(comp18327->LocalAt(0), false); return Call(c, fn18336, std::move(args18337)); }()))) return Value(true); } return Value(false); }()))) {
continue;
}
if (static_cast<bool>(([&]() -> Value { auto comp18338 = std::make_shared<Scope>(); comp18338->globals = s->globals; comp18338->parent = s; static constexpr const char* comp18338_names[] = {"t"}; comp18338->PrepareSlots(comp18338_names); auto result18339 = List(); for (const auto& item18340 : Iterate(([&]() -> Value { auto fn18341 = s->Global("range"); Arguments args18342; args18342.positional.reserve(2); args18342.Add(([&]() -> Value { auto v18343 = s->LocalAt(15); return Binary("Add", v18343, Value(int64_t{5})); }()), false); args18342.Add(([&]() -> Value { auto fn18344 = s->Global("min"); Arguments args18345; args18345.positional.reserve(2); args18345.Add(Value(int64_t{719}), false); args18345.Add(([&]() -> Value { auto v18346 = s->LocalAt(15); return Binary("Add", v18346, Value(int64_t{24})); }()), false); return Call(c, fn18344, std::move(args18345)); }()), false); return Call(c, fn18341, std::move(args18342)); }()))) { comp18338->SetAt(0, item18340); if (static_cast<bool>(([&]() -> Value { auto fn18347 = comp18338->Captured("planned"); Arguments args18348; args18348.Add(comp18338->LocalAt(0), false); return Call(c, fn18347, std::move(args18348)); }()))) return Value(true); } return Value(false); }()))) {
return Value(true);
}
}
return Value(false);
return {};
}
}  // namespace kagg::opponents::compiled
