// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_617516fb9178365b0b3c(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "best", "buys", "cmd", "configuration", "cow", "day", "evs", "extra", "farm", "i", "k", "keep", "key", "market", "n", "no_milk", "o", "observation", "plan", "planned", "pos", "positions", "product", "seat", "shop_ok", "shops_now", "st", "step", "stock", "tile", "units", "x", "y"};
s->PrepareSlots(s_names);
auto v25318 = ([&]() -> Value { auto fn25319 = s->Global("_CS_PARENT"); Arguments args25320; args25320.positional.reserve(2); args25320.Add(s->LocalAt(18), false); args25320.Add(s->LocalAt(4), false); return Call(c, fn25319, std::move(args25320)); }());
s->SetAt(0, v25318);
try {
auto v25322 = ([&]() -> Value { auto fn25323 = s->Global("int"); Arguments args25324; args25324.Add(Get(s->LocalAt(18), Value("player")), false); return Call(c, fn25323, std::move(args25324)); }());
s->SetAt(24, v25322);
auto v25325 = ([&]() -> Value { auto fn25326 = s->Global("int"); Arguments args25327; args25327.Add(Get(s->LocalAt(18), Value("step")), false); return Call(c, fn25326, std::move(args25327)); }());
s->SetAt(28, v25325);
auto v25328 = ([&]() -> Value { auto fn25329 = PrepareDictionaryGet(s->Global("_CS_STATE")); Arguments args25330; args25330.Add(s->LocalAt(24), false); return CallDictionaryGet(c, fn25329, std::move(args25330)); }());
s->SetAt(27, v25328);
if (static_cast<bool>(([&]() -> Value { auto v25331 = ([&]() -> Value { auto v25332 = s->LocalAt(27); Value v25333; v25333 = Value{}; if (!static_cast<bool>(Binary("Is", v25332, v25333))) return Value(false); v25332 = v25333; return Value(true); }()); if (static_cast<bool>(v25331)) return v25331; v25331 = ([&]() -> Value { auto v25334 = s->LocalAt(28); Value v25335; v25335 = Get(s->LocalAt(27), Value("step")); if (!static_cast<bool>(Binary("LtE", v25334, v25335))) return Value(false); v25334 = v25335; return Value(true); }()); return v25331; }()))) {
auto v25336 = ([&]() -> Value { auto dict25337 = Dict(); auto key25338 = Value("step"); Put(dict25337, key25338, Unary("USub", Value(int64_t{1}))); auto key25339 = Value("decided"); Put(dict25337, key25339, Value(false)); auto key25340 = Value("mode"); Put(dict25337, key25340, Value{}); auto key25341 = Value("plan"); Put(dict25337, key25341, Value{}); auto key25342 = Value("broken"); Put(dict25337, key25342, Value(false)); auto key25343 = Value("sites"); Put(dict25337, key25343, ([&]() -> Value { auto dict25344 = Dict(); return dict25344; }())); auto key25345 = Value("pending"); Put(dict25337, key25345, List({})); auto key25346 = Value("credit"); Put(dict25337, key25346, Value(int64_t{0})); return dict25337; }());
s->SetAt(27, v25336);
Put(s->Global("_CS_STATE"), s->LocalAt(24), v25336);
if (static_cast<bool>(([&]() -> Value { auto v25347 = s->LocalAt(28); Value v25348; v25348 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v25347, v25348))) return Value(false); v25347 = v25348; return Value(true); }()))) {
(void)([&]() -> Value { auto fn25349 = Attribute(s->Global("_CS_REPORT"), "update"); Arguments args25350; args25350.Keyword("cs_decision", Value("")); args25350.Keyword("cs_ev", Value("")); args25350.Keyword("cs_rewrites", Value(int64_t{0})); args25350.Keyword("cs_broken", Value(int64_t{0})); args25350.Keyword("cs_credit", Value(int64_t{0})); args25350.Keyword("cs_sold", Value(int64_t{0})); args25350.Keyword("cs_errors", Value(int64_t{0})); return Call(c, fn25349, std::move(args25350)); }());
}
}
auto v25351 = s->LocalAt(28);
Put(s->LocalAt(27), Value("step"), v25351);
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto fn25352 = s->Global("isinstance"); Arguments args25353; args25353.positional.reserve(2); args25353.Add(s->LocalAt(0), false); args25353.Add(s->Global("dict"), false); return Call(c, fn25352, std::move(args25353)); }())))) {
return s->LocalAt(0);
}
auto v25354 = Get(Get(s->LocalAt(18), Value("farms")), s->LocalAt(24));
s->SetAt(9, v25354);
auto v25355 = ([&]() -> Value { auto v25356 = List({Get(s->LocalAt(9), Value("farmer"))}); return Binary("Add", v25356, ([&]() -> Value { auto fn25357 = s->Global("list"); Arguments args25358; args25358.Add(Get(s->LocalAt(9), Value("hands")), false); return Call(c, fn25357, std::move(args25358)); }())); }());
s->SetAt(22, v25355);
auto v25359 = ([&]() -> Value { auto comp25360 = std::make_shared<Scope>(); comp25360->globals = s->globals; comp25360->parent = s; static constexpr const char* comp25360_names[] = {"o"}; comp25360->PrepareSlots(comp25360_names); auto result25361 = List(); for (const auto& item25362 : Iterate(([&]() -> Value { auto v25363 = ([&]() -> Value { auto fn25364 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args25365; args25365.Add(Value("market"), false); return CallDictionaryGet(c, fn25364, std::move(args25365)); }()); if (static_cast<bool>(v25363)) return v25363; v25363 = List({}); return v25363; }()))) { comp25360->SetAt(0, item25362); result25361.node()->sequence.push_back(([&]() -> Value { auto fn25366 = comp25360->Global("list"); Arguments args25367; args25367.Add(comp25360->LocalAt(0), false); return Call(c, fn25366, std::move(args25367)); }())); } return result25361; }());
s->SetAt(14, v25359);
if (static_cast<bool>(Get(s->LocalAt(27), Value("pending")))) {
auto v25368 = List({});
s->SetAt(12, v25368);
for (const auto& item25369 : Iterate(Get(s->LocalAt(27), Value("pending")))) {
auto unpack25370 = Iterate(item25369);
ValidateUnpack(unpack25370, 3, false);
s->SetAt(32, unpack25370.at(0));
s->SetAt(33, unpack25370.at(1));
s->SetAt(6, unpack25370.at(2));
auto v25371 = Get(Get(Get(s->LocalAt(9), Value("tiles")), s->LocalAt(33)), s->LocalAt(32));
s->SetAt(30, v25371);
if (static_cast<bool>(([&]() -> Value { auto v25372 = ([&]() -> Value { auto fn25373 = s->Global("isinstance"); Arguments args25374; args25374.positional.reserve(2); args25374.Add(s->LocalAt(30), false); args25374.Add(s->Global("dict"), false); return Call(c, fn25373, std::move(args25374)); }()); if (!static_cast<bool>(v25372)) return v25372; v25372 = ([&]() -> Value { auto v25375 = ([&]() -> Value { auto fn25377 = PrepareDictionaryGet(s->LocalAt(30)); Arguments args25378; args25378.Add(Value("animal"), false); return CallDictionaryGet(c, fn25377, std::move(args25378)); }()); Value v25376; v25376 = Get(s->LocalAt(27), Value("mode")); if (!static_cast<bool>(Binary("Eq", v25375, v25376))) return Value(false); v25375 = v25376; return Value(true); }()); if (!static_cast<bool>(v25372)) return v25372; v25372 = ([&]() -> Value { auto v25379 = ([&]() -> Value { auto fn25381 = PrepareDictionaryGet(s->LocalAt(30)); Arguments args25382; args25382.Add(Value("placed_day"), false); return CallDictionaryGet(c, fn25381, std::move(args25382)); }()); Value v25380; v25380 = s->LocalAt(6); if (!static_cast<bool>(Binary("Eq", v25379, v25380))) return Value(false); v25379 = v25380; return Value(true); }()); return v25372; }()))) {
auto v25383 = s->LocalAt(6);
Put(Get(s->LocalAt(27), Value("sites")), Tuple({s->LocalAt(32), s->LocalAt(33)}), v25383);
}
else {
if (static_cast<bool>(([&]() -> Value { auto v25384 = ([&]() -> Value { auto v25386 = s->LocalAt(28); return Binary("FloorDiv", v25386, Value(int64_t{24})); }()); Value v25385; v25385 = s->LocalAt(6); if (!static_cast<bool>(Binary("LtE", v25384, v25385))) return Value(false); v25384 = v25385; return Value(true); }()))) {
(void)([&]() -> Value { auto fn25387 = Attribute(s->LocalAt(12), "append"); Arguments args25388; args25388.Add(Tuple({s->LocalAt(32), s->LocalAt(33), s->LocalAt(6)}), false); return Call(c, fn25387, std::move(args25388)); }());
}
}
}
auto v25389 = s->LocalAt(12);
Put(s->LocalAt(27), Value("pending"), v25389);
}
if (static_cast<bool>(([&]() -> Value { auto v25390 = Unary("Not", Get(s->LocalAt(27), Value("decided"))); if (!static_cast<bool>(v25390)) return v25390; v25390 = ([&]() -> Value { auto v25391 = s->Global("_CS_FROM"); Value v25392; v25392 = s->LocalAt(28); if (!static_cast<bool>(Binary("LtE", v25391, v25392))) return Value(false); v25391 = v25392; v25392 = s->Global("_CS_TO"); if (!static_cast<bool>(Binary("Lt", v25391, v25392))) return Value(false); v25391 = v25392; return Value(true); }()); return v25390; }()))) {
auto v25393 = ([&]() -> Value { auto comp25394 = std::make_shared<Scope>(); comp25394->globals = s->globals; comp25394->parent = s; static constexpr const char* comp25394_names[] = {"o"}; comp25394->PrepareSlots(comp25394_names); auto result25395 = List(); for (const auto& item25396 : Iterate(s->LocalAt(14))) { comp25394->SetAt(0, item25396); if (!static_cast<bool>(([&]() -> Value { auto v25397 = ([&]() -> Value { auto v25398 = ([&]() -> Value { auto fn25400 = comp25394->Global("len"); Arguments args25401; args25401.Add(comp25394->LocalAt(0), false); return Call(c, fn25400, std::move(args25401)); }()); Value v25399; v25399 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v25398, v25399))) return Value(false); v25398 = v25399; return Value(true); }()); if (!static_cast<bool>(v25397)) return v25397; v25397 = ([&]() -> Value { auto v25402 = Get(comp25394->LocalAt(0), Value(int64_t{0})); Value v25403; v25403 = Value("BUY_ANIMAL"); if (!static_cast<bool>(Binary("Eq", v25402, v25403))) return Value(false); v25402 = v25403; return Value(true); }()); if (!static_cast<bool>(v25397)) return v25397; v25397 = ([&]() -> Value { auto v25404 = Get(comp25394->LocalAt(0), Value(int64_t{1})); Value v25405; v25405 = Value("COW"); if (!static_cast<bool>(Binary("Eq", v25404, v25405))) return Value(false); v25404 = v25405; return Value(true); }()); if (!static_cast<bool>(v25397)) return v25397; v25397 = ([&]() -> Value { auto v25406 = ([&]() -> Value { auto fn25408 = comp25394->Global("int"); Arguments args25409; args25409.Add(Get(comp25394->LocalAt(0), Value(int64_t{2})), false); return Call(c, fn25408, std::move(args25409)); }()); Value v25407; v25407 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v25406, v25407))) return Value(false); v25406 = v25407; return Value(true); }()); return v25397; }()))) continue; result25395.node()->sequence.push_back(comp25394->LocalAt(0)); } return result25395; }());
s->SetAt(2, v25393);
auto v25410 = ([&]() -> Value { auto fn25411 = s->Global("list"); Arguments args25412; args25412.Add(([&]() -> Value { auto v25413 = ([&]() -> Value { auto fn25414 = PrepareDictionaryGet(([&]() -> Value { auto v25416 = ([&]() -> Value { auto fn25417 = PrepareDictionaryGet(s->LocalAt(18)); Arguments args25418; args25418.Add(Value("town"), false); return CallDictionaryGet(c, fn25417, std::move(args25418)); }()); if (static_cast<bool>(v25416)) return v25416; v25416 = ([&]() -> Value { auto dict25419 = Dict(); return dict25419; }()); return v25416; }())); Arguments args25415; args25415.Add(Value("unlocked_shops"), false); return CallDictionaryGet(c, fn25414, std::move(args25415)); }()); if (static_cast<bool>(v25413)) return v25413; v25413 = List({}); return v25413; }()), false); return Call(c, fn25411, std::move(args25412)); }());
s->SetAt(26, v25410);
auto v25420 = Value(true);
s->SetAt(25, v25420);
if (static_cast<bool>(s->Global("_CS_SHOP_RULE"))) {
auto v25421 = Unary("Not", ([&]() -> Value { auto comp25422 = std::make_shared<Scope>(); comp25422->globals = s->globals; comp25422->parent = s; static constexpr const char* comp25422_names[] = {"s"}; comp25422->PrepareSlots(comp25422_names); auto result25423 = List(); for (const auto& item25424 : Iterate(s->LocalAt(26))) { comp25422->SetAt(0, item25424); if (static_cast<bool>(([&]() -> Value { auto v25425 = comp25422->LocalAt(0); Value v25426; v25426 = Tuple({Value("PIZZA_SHOP"), Value("ICE_CREAM_SHOP"), Value("SMOOTHIE_SHOP")}); if (!static_cast<bool>(Binary("In", v25425, v25426))) return Value(false); v25425 = v25426; return Value(true); }()))) return Value(true); } return Value(false); }()));
s->SetAt(16, v25421);
if (static_cast<bool>(([&]() -> Value { auto v25427 = s->Global("_CS_SHOP_RULE"); Value v25428; v25428 = Value("nomilk"); if (!static_cast<bool>(Binary("Eq", v25427, v25428))) return Value(false); v25427 = v25428; return Value(true); }()))) {
auto v25429 = ([&]() -> Value { auto v25430 = s->LocalAt(16); if (!static_cast<bool>(v25430)) return v25430; v25430 = ([&]() -> Value { auto v25431 = Value("YARN_STORE"); Value v25432; v25432 = s->LocalAt(26); if (!static_cast<bool>(Binary("NotIn", v25431, v25432))) return Value(false); v25431 = v25432; return Value(true); }()); return v25430; }());
s->SetAt(25, v25429);
}
else {
auto v25433 = ([&]() -> Value { auto v25434 = s->LocalAt(16); if (!static_cast<bool>(v25434)) return v25434; v25434 = ([&]() -> Value { auto comp25435 = std::make_shared<Scope>(); comp25435->globals = s->globals; comp25435->parent = s; static constexpr const char* comp25435_names[] = {"s"}; comp25435->PrepareSlots(comp25435_names); auto result25436 = List(); for (const auto& item25437 : Iterate(s->LocalAt(26))) { comp25435->SetAt(0, item25437); if (static_cast<bool>(([&]() -> Value { auto v25438 = comp25435->LocalAt(0); Value v25439; v25439 = Tuple({Value("BAKERY"), Value("BRUNCH_SPOT")}); if (!static_cast<bool>(Binary("In", v25438, v25439))) return Value(false); v25438 = v25439; return Value(true); }()))) return Value(true); } return Value(false); }()); return v25434; }());
s->SetAt(25, v25433);
}
}
if (static_cast<bool>(([&]() -> Value { auto v25440 = s->LocalAt(2); if (!static_cast<bool>(v25440)) return v25440; v25440 = Unary("Not", s->LocalAt(25)); return v25440; }()))) {
auto v25441 = Value(true);
Put(s->LocalAt(27), Value("decided"), v25441);
auto v25442 = ([&]() -> Value { auto v25443 = Value("shoprule@%d"); return Binary("Mod", v25443, s->LocalAt(28)); }());
Put(s->Global("_CS_REPORT"), Value("cs_decision"), v25442);
}
else {
if (static_cast<bool>(s->LocalAt(2))) {
auto v25444 = Value(true);
Put(s->LocalAt(27), Value("decided"), v25444);
auto v25445 = ([&]() -> Value { auto fn25446 = s->Global("sum"); Arguments args25447; args25447.Add(([&]() -> Value { auto comp25448 = std::make_shared<Scope>(); comp25448->globals = s->globals; comp25448->parent = s; static constexpr const char* comp25448_names[] = {"o"}; comp25448->PrepareSlots(comp25448_names); auto result25449 = List(); for (const auto& item25450 : Iterate(s->LocalAt(2))) { comp25448->SetAt(0, item25450); result25449.node()->sequence.push_back(([&]() -> Value { auto fn25451 = comp25448->Global("int"); Arguments args25452; args25452.Add(Get(comp25448->LocalAt(0), Value(int64_t{2})), false); return Call(c, fn25451, std::move(args25452)); }())); } return result25449; }()), false); return Call(c, fn25446, std::move(args25447)); }());
s->SetAt(11, v25445);
auto v25453 = ([&]() -> Value { auto comp25454 = std::make_shared<Scope>(); comp25454->globals = s->globals; comp25454->parent = s; static constexpr const char* comp25454_names[] = {"opt"}; comp25454->PrepareSlots(comp25454_names); auto result25455 = Dict(); for (const auto& item25456 : Iterate(([&]() -> Value { auto v25457 = Tuple({Value("COW")}); return Binary("Add", v25457, ([&]() -> Value { auto fn25458 = s->Global("tuple"); Arguments args25459; args25459.Add(s->Global("_CS_OPTIONS"), false); return Call(c, fn25458, std::move(args25459)); }())); }()))) { comp25454->SetAt(0, item25456); Put(result25455, comp25454->LocalAt(0), Get(([&]() -> Value { auto fn25460 = comp25454->Global("_hd2_ev"); Arguments args25461; args25461.positional.reserve(4); args25461.Add(comp25454->LocalAt(0), false); args25461.Add(comp25454->Captured("k"), false); args25461.Add(comp25454->Captured("observation"), false); args25461.Add(comp25454->Captured("st"), false); return Call(c, fn25460, std::move(args25461)); }()), Value(int64_t{0}))); } return result25455; }());
s->SetAt(7, v25453);
auto v25462 = ([&]() -> Value { auto fn25463 = Attribute(Value(","), "join"); Arguments args25464; args25464.Add(([&]() -> Value { auto comp25465 = std::make_shared<Scope>(); comp25465->globals = s->globals; comp25465->parent = s; static constexpr const char* comp25465_names[] = {"o", "v"}; comp25465->PrepareSlots(comp25465_names); auto result25466 = List(); for (const auto& item25467 : Iterate(([&]() -> Value { auto fn25468 = s->Global("sorted"); Arguments args25469; args25469.Add(([&]() -> Value { auto fn25470 = Attribute(s->LocalAt(7), "items"); Arguments args25471; return Call(c, fn25470, std::move(args25471)); }()), false); return Call(c, fn25468, std::move(args25469)); }()))) { auto unpack25472 = Iterate(item25467); ValidateUnpack(unpack25472, 2, false); comp25465->SetAt(0, unpack25472.at(0)); comp25465->SetAt(1, unpack25472.at(1)); result25466.node()->sequence.push_back(([&]() -> Value { auto v25473 = Value("%s:%d"); return Binary("Mod", v25473, Tuple({comp25465->LocalAt(0), comp25465->LocalAt(1)})); }())); } return result25466; }()), false); return Call(c, fn25463, std::move(args25464)); }());
Put(s->Global("_CS_REPORT"), Value("cs_ev"), v25462);
auto v25474 = ([&]() -> Value { auto fn25475 = s->Global("max"); Arguments args25476; args25476.Add(s->Global("_CS_OPTIONS"), false); args25476.Keyword("key", Define(&Code_6e86b435f3167c12f9f7, s, Signature{{"o"}, {}, {}, {}, "", "", ([]() -> std::span<const char* const> { static constexpr const char* names[] = {"o"}; return names; }())}, true, "<lambda>")); return Call(c, fn25475, std::move(args25476)); }());
s->SetAt(1, v25474);
auto v25477 = Get(s->LocalAt(7), Value("COW"));
s->SetAt(5, v25477);
if (static_cast<bool>(([&]() -> Value { auto v25478 = ([&]() -> Value { auto v25479 = ([&]() -> Value { auto v25481 = Get(s->LocalAt(7), s->LocalAt(1)); return Binary("Sub", v25481, s->LocalAt(5)); }()); Value v25480; v25480 = s->Global("_CS_MIN_GAIN"); if (!static_cast<bool>(Binary("GtE", v25479, v25480))) return Value(false); v25479 = v25480; return Value(true); }()); if (!static_cast<bool>(v25478)) return v25478; v25478 = ([&]() -> Value { auto v25482 = Get(s->LocalAt(7), s->LocalAt(1)); Value v25483; v25483 = ([&]() -> Value { auto v25484 = s->Global("_CS_RATIO"); return Binary("Mult", v25484, ([&]() -> Value { auto fn25485 = s->Global("max"); Arguments args25486; args25486.positional.reserve(2); args25486.Add(s->LocalAt(5), false); args25486.Add(Value(1.0), false); return Call(c, fn25485, std::move(args25486)); }())); }()); if (!static_cast<bool>(Binary("GtE", v25482, v25483))) return Value(false); v25482 = v25483; return Value(true); }()); return v25478; }()))) {
auto v25487 = ([&]() -> Value { auto fn25488 = s->Global("_cs_plan"); Arguments args25489; args25489.positional.reserve(4); args25489.Add(s->LocalAt(18), false); args25489.Add(s->LocalAt(0), false); args25489.Add(s->LocalAt(11), false); args25489.Add(s->LocalAt(1), false); return Call(c, fn25488, std::move(args25489)); }());
s->SetAt(19, v25487);
if (static_cast<bool>(([&]() -> Value { auto v25490 = s->LocalAt(19); Value v25491; v25491 = Value{}; if (!static_cast<bool>(Binary("IsNot", v25490, v25491))) return Value(false); v25490 = v25491; return Value(true); }()))) {
auto v25492 = Tuple({s->LocalAt(1), s->LocalAt(19)});
auto unpack25493 = Iterate(v25492);
ValidateUnpack(unpack25493, 2, false);
Put(s->LocalAt(27), Value("mode"), unpack25493.at(0));
Put(s->LocalAt(27), Value("plan"), unpack25493.at(1));
auto v25494 = ([&]() -> Value { auto v25495 = Value("%s@%d"); return Binary("Mod", v25495, Tuple({s->LocalAt(1), s->LocalAt(28)})); }());
Put(s->Global("_CS_REPORT"), Value("cs_decision"), v25494);
for (const auto& item25496 : Iterate(s->LocalAt(14))) {
s->SetAt(17, item25496);
if (static_cast<bool>(([&]() -> Value { auto v25497 = ([&]() -> Value { auto v25498 = ([&]() -> Value { auto fn25500 = s->Global("len"); Arguments args25501; args25501.Add(s->LocalAt(17), false); return Call(c, fn25500, std::move(args25501)); }()); Value v25499; v25499 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v25498, v25499))) return Value(false); v25498 = v25499; return Value(true); }()); if (!static_cast<bool>(v25497)) return v25497; v25497 = ([&]() -> Value { auto v25502 = Get(s->LocalAt(17), Value(int64_t{0})); Value v25503; v25503 = Value("BUY_ANIMAL"); if (!static_cast<bool>(Binary("Eq", v25502, v25503))) return Value(false); v25502 = v25503; return Value(true); }()); if (!static_cast<bool>(v25497)) return v25497; v25497 = ([&]() -> Value { auto v25504 = Get(s->LocalAt(17), Value(int64_t{1})); Value v25505; v25505 = Value("COW"); if (!static_cast<bool>(Binary("Eq", v25504, v25505))) return Value(false); v25504 = v25505; return Value(true); }()); return v25497; }()))) {
auto v25506 = s->LocalAt(1);
Put(s->LocalAt(17), Value(int64_t{1}), v25506);
auto v25507 = s->Global("_CS_REPORT");
auto v25508 = Value("cs_rewrites");
auto v25509 = Get(v25507, v25508);
Put(v25507, v25508, Inplace("Add", v25509, Value(int64_t{1})));
}
}
}
else {
auto v25510 = ([&]() -> Value { auto v25511 = Value("noplan@%d"); return Binary("Mod", v25511, s->LocalAt(28)); }());
Put(s->Global("_CS_REPORT"), Value("cs_decision"), v25510);
}
}
else {
auto v25512 = ([&]() -> Value { auto v25513 = Value("keep@%d"); return Binary("Mod", v25513, s->LocalAt(28)); }());
Put(s->Global("_CS_REPORT"), Value("cs_decision"), v25512);
}
}
}
}
if (static_cast<bool>(([&]() -> Value { auto v25514 = Get(s->LocalAt(27), Value("mode")); if (!static_cast<bool>(v25514)) return v25514; v25514 = Get(s->LocalAt(27), Value("plan")); if (!static_cast<bool>(v25514)) return v25514; v25514 = Unary("Not", Get(s->LocalAt(27), Value("broken"))); return v25514; }()))) {
auto v25515 = Get(s->LocalAt(27), Value("plan"));
s->SetAt(19, v25515);
auto v25516 = ([&]() -> Value { auto v25517 = List({([&]() -> Value { auto v25518 = ([&]() -> Value { auto fn25519 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args25520; args25520.Add(Value("farmer"), false); return CallDictionaryGet(c, fn25519, std::move(args25520)); }()); if (static_cast<bool>(v25518)) return v25518; v25518 = List({Value("PASS")}); return v25518; }())}); return Binary("Add", v25517, ([&]() -> Value { auto fn25521 = s->Global("list"); Arguments args25522; args25522.Add(([&]() -> Value { auto v25523 = ([&]() -> Value { auto fn25524 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args25525; args25525.Add(Value("hands"), false); return CallDictionaryGet(c, fn25524, std::move(args25525)); }()); if (static_cast<bool>(v25523)) return v25523; v25523 = List({}); return v25523; }()), false); return Call(c, fn25521, std::move(args25522)); }())); }());
s->SetAt(31, v25516);
for (const auto& item25526 : Iterate(([&]() -> Value { auto fn25527 = s->Global("range"); Arguments args25528; args25528.Add(([&]() -> Value { auto fn25529 = s->Global("min"); Arguments args25530; args25530.positional.reserve(2); args25530.Add(([&]() -> Value { auto fn25531 = s->Global("len"); Arguments args25532; args25532.Add(s->LocalAt(31), false); return Call(c, fn25531, std::move(args25532)); }()), false); args25530.Add(([&]() -> Value { auto fn25533 = s->Global("len"); Arguments args25534; args25534.Add(s->LocalAt(22), false); return Call(c, fn25533, std::move(args25534)); }()), false); return Call(c, fn25529, std::move(args25530)); }()), false); return Call(c, fn25527, std::move(args25528)); }()))) {
s->SetAt(10, item25526);
auto v25535 = ([&]() -> Value { auto v25536 = Get(s->LocalAt(31), s->LocalAt(10)); if (static_cast<bool>(v25536)) return v25536; v25536 = List({Value("PASS")}); return v25536; }());
s->SetAt(3, v25535);
auto v25537 = Tuple({([&]() -> Value { auto fn25538 = s->Global("int"); Arguments args25539; args25539.Add(Get(Get(s->LocalAt(22), s->LocalAt(10)), Value(int64_t{0})), false); return Call(c, fn25538, std::move(args25539)); }()), ([&]() -> Value { auto fn25540 = s->Global("int"); Arguments args25541; args25541.Add(Get(Get(s->LocalAt(22), s->LocalAt(10)), Value(int64_t{1})), false); return Call(c, fn25540, std::move(args25541)); }())});
s->SetAt(21, v25537);
auto v25542 = Tuple({s->LocalAt(28), s->LocalAt(10)});
s->SetAt(13, v25542);
if (static_cast<bool>(([&]() -> Value { auto v25543 = s->LocalAt(13); Value v25544; v25544 = Get(s->LocalAt(19), Value("builds")); if (!static_cast<bool>(Binary("In", v25543, v25544))) return Value(false); v25543 = v25544; return Value(true); }()))) {
if (static_cast<bool>(([&]() -> Value { auto v25545 = ([&]() -> Value { auto v25546 = s->LocalAt(3); Value v25547; v25547 = List({Value("BUILD_PASTURE")}); if (!static_cast<bool>(Binary("Eq", v25546, v25547))) return Value(false); v25546 = v25547; return Value(true); }()); if (!static_cast<bool>(v25545)) return v25545; v25545 = ([&]() -> Value { auto v25548 = s->LocalAt(21); Value v25549; v25549 = Get(Get(s->LocalAt(19), Value("builds")), s->LocalAt(13)); if (!static_cast<bool>(Binary("Eq", v25548, v25549))) return Value(false); v25548 = v25549; return Value(true); }()); return v25545; }()))) {
auto v25550 = List({Value("BUILD_COOP")});
Put(s->LocalAt(31), s->LocalAt(10), v25550);
auto v25551 = s->Global("_CS_REPORT");
auto v25552 = Value("cs_rewrites");
auto v25553 = Get(v25551, v25552);
Put(v25551, v25552, Inplace("Add", v25553, Value(int64_t{1})));
}
else {
auto v25554 = Value(true);
Put(s->LocalAt(27), Value("broken"), v25554);
}
}
if (static_cast<bool>(([&]() -> Value { auto v25555 = s->LocalAt(13); Value v25556; v25556 = Get(s->LocalAt(19), Value("pickups")); if (!static_cast<bool>(Binary("In", v25555, v25556))) return Value(false); v25555 = v25556; return Value(true); }()))) {
if (static_cast<bool>(([&]() -> Value { auto v25557 = ([&]() -> Value { auto v25558 = ([&]() -> Value { auto fn25560 = s->Global("len"); Arguments args25561; args25561.Add(s->LocalAt(3), false); return Call(c, fn25560, std::move(args25561)); }()); Value v25559; v25559 = Value(int64_t{2}); if (!static_cast<bool>(Binary("GtE", v25558, v25559))) return Value(false); v25558 = v25559; return Value(true); }()); if (!static_cast<bool>(v25557)) return v25557; v25557 = ([&]() -> Value { auto v25562 = Get(s->LocalAt(3), Value(int64_t{0})); Value v25563; v25563 = Value("PICKUP"); if (!static_cast<bool>(Binary("Eq", v25562, v25563))) return Value(false); v25562 = v25563; return Value(true); }()); if (!static_cast<bool>(v25557)) return v25557; v25557 = ([&]() -> Value { auto v25564 = Get(s->LocalAt(3), Value(int64_t{1})); Value v25565; v25565 = Value("COW"); if (!static_cast<bool>(Binary("Eq", v25564, v25565))) return Value(false); v25564 = v25565; return Value(true); }()); return v25557; }()))) {
auto v25566 = ([&]() -> Value { auto v25567 = List({Value("PICKUP"), Get(s->LocalAt(27), Value("mode"))}); return Binary("Add", v25567, ([&]() -> Value { auto fn25568 = s->Global("list"); Arguments args25569; args25569.Add(Slice(s->LocalAt(3), Value(int64_t{2}), Value{}, Value{}), false); return Call(c, fn25568, std::move(args25569)); }())); }());
Put(s->LocalAt(31), s->LocalAt(10), v25566);
auto v25570 = s->Global("_CS_REPORT");
auto v25571 = Value("cs_rewrites");
auto v25572 = Get(v25570, v25571);
Put(v25570, v25571, Inplace("Add", v25572, Value(int64_t{1})));
}
else {
auto v25573 = Value(true);
Put(s->LocalAt(27), Value("broken"), v25573);
}
}
if (static_cast<bool>(([&]() -> Value { auto v25574 = s->LocalAt(13); Value v25575; v25575 = Get(s->LocalAt(19), Value("places")); if (!static_cast<bool>(Binary("In", v25574, v25575))) return Value(false); v25574 = v25575; return Value(true); }()))) {
if (static_cast<bool>(([&]() -> Value { auto v25576 = ([&]() -> Value { auto v25577 = ([&]() -> Value { auto fn25579 = s->Global("len"); Arguments args25580; args25580.Add(s->LocalAt(3), false); return Call(c, fn25579, std::move(args25580)); }()); Value v25578; v25578 = Value(int64_t{2}); if (!static_cast<bool>(Binary("GtE", v25577, v25578))) return Value(false); v25577 = v25578; return Value(true); }()); if (!static_cast<bool>(v25576)) return v25576; v25576 = ([&]() -> Value { auto v25581 = Get(s->LocalAt(3), Value(int64_t{0})); Value v25582; v25582 = Value("PLACE"); if (!static_cast<bool>(Binary("Eq", v25581, v25582))) return Value(false); v25581 = v25582; return Value(true); }()); if (!static_cast<bool>(v25576)) return v25576; v25576 = ([&]() -> Value { auto v25583 = Get(s->LocalAt(3), Value(int64_t{1})); Value v25584; v25584 = Value("COW"); if (!static_cast<bool>(Binary("Eq", v25583, v25584))) return Value(false); v25583 = v25584; return Value(true); }()); if (!static_cast<bool>(v25576)) return v25576; v25576 = ([&]() -> Value { auto v25585 = s->LocalAt(21); Value v25586; v25586 = Get(Get(s->LocalAt(19), Value("places")), s->LocalAt(13)); if (!static_cast<bool>(Binary("Eq", v25585, v25586))) return Value(false); v25585 = v25586; return Value(true); }()); return v25576; }()))) {
auto v25587 = ([&]() -> Value { auto v25588 = List({Value("PLACE"), Get(s->LocalAt(27), Value("mode"))}); return Binary("Add", v25588, ([&]() -> Value { auto fn25589 = s->Global("list"); Arguments args25590; args25590.Add(Slice(s->LocalAt(3), Value(int64_t{2}), Value{}, Value{}), false); return Call(c, fn25589, std::move(args25590)); }())); }());
Put(s->LocalAt(31), s->LocalAt(10), v25587);
(void)([&]() -> Value { auto fn25591 = Attribute(Get(s->LocalAt(27), Value("pending")), "append"); Arguments args25592; args25592.Add(Tuple({Get(s->LocalAt(21), Value(int64_t{0})), Get(s->LocalAt(21), Value(int64_t{1})), ([&]() -> Value { auto v25593 = s->LocalAt(28); return Binary("FloorDiv", v25593, Value(int64_t{24})); }())}), false); return Call(c, fn25591, std::move(args25592)); }());
auto v25594 = s->Global("_CS_REPORT");
auto v25595 = Value("cs_rewrites");
auto v25596 = Get(v25594, v25595);
Put(v25594, v25595, Inplace("Add", v25596, Value(int64_t{1})));
}
else {
auto v25597 = Value(true);
Put(s->LocalAt(27), Value("broken"), v25597);
}
}
}
if (static_cast<bool>(Get(s->LocalAt(27), Value("broken")))) {
auto v25598 = s->Global("_CS_REPORT");
auto v25599 = Value("cs_broken");
auto v25600 = Get(v25598, v25599);
Put(v25598, v25599, Inplace("Add", v25600, Value(int64_t{1})));
}
auto v25601 = ([&]() -> Value { auto fn25602 = s->Global("dict"); Arguments args25603; args25603.Add(s->LocalAt(0), false); return Call(c, fn25602, std::move(args25603)); }());
s->SetAt(0, v25601);
auto v25604 = Get(s->LocalAt(31), Value(int64_t{0}));
Put(s->LocalAt(0), Value("farmer"), v25604);
auto v25605 = Slice(s->LocalAt(31), Value(int64_t{1}), Value{}, Value{});
Put(s->LocalAt(0), Value("hands"), v25605);
}
if (static_cast<bool>(Get(s->LocalAt(27), Value("sites")))) {
auto v25606 = Get(Get(s->Global("_HD2_SPEC"), Get(s->LocalAt(27), Value("mode"))), Value("product"));
s->SetAt(23, v25606);
auto v25607 = ([&]() -> Value { auto v25608 = List({([&]() -> Value { auto v25609 = ([&]() -> Value { auto fn25610 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args25611; args25611.Add(Value("farmer"), false); return CallDictionaryGet(c, fn25610, std::move(args25611)); }()); if (static_cast<bool>(v25609)) return v25609; v25609 = List({Value("PASS")}); return v25609; }())}); return Binary("Add", v25608, ([&]() -> Value { auto fn25612 = s->Global("list"); Arguments args25613; args25613.Add(([&]() -> Value { auto v25614 = ([&]() -> Value { auto fn25615 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args25616; args25616.Add(Value("hands"), false); return CallDictionaryGet(c, fn25615, std::move(args25616)); }()); if (static_cast<bool>(v25614)) return v25614; v25614 = List({}); return v25614; }()), false); return Call(c, fn25612, std::move(args25613)); }())); }());
s->SetAt(31, v25607);
for (const auto& item25617 : Iterate(([&]() -> Value { auto fn25618 = s->Global("range"); Arguments args25619; args25619.Add(([&]() -> Value { auto fn25620 = s->Global("min"); Arguments args25621; args25621.positional.reserve(2); args25621.Add(([&]() -> Value { auto fn25622 = s->Global("len"); Arguments args25623; args25623.Add(s->LocalAt(31), false); return Call(c, fn25622, std::move(args25623)); }()), false); args25621.Add(([&]() -> Value { auto fn25624 = s->Global("len"); Arguments args25625; args25625.Add(s->LocalAt(22), false); return Call(c, fn25624, std::move(args25625)); }()), false); return Call(c, fn25620, std::move(args25621)); }()), false); return Call(c, fn25618, std::move(args25619)); }()))) {
s->SetAt(10, item25617);
auto v25626 = Tuple({([&]() -> Value { auto fn25627 = s->Global("int"); Arguments args25628; args25628.Add(Get(Get(s->LocalAt(22), s->LocalAt(10)), Value(int64_t{0})), false); return Call(c, fn25627, std::move(args25628)); }()), ([&]() -> Value { auto fn25629 = s->Global("int"); Arguments args25630; args25630.Add(Get(Get(s->LocalAt(22), s->LocalAt(10)), Value(int64_t{1})), false); return Call(c, fn25629, std::move(args25630)); }())});
auto unpack25631 = Iterate(v25626);
ValidateUnpack(unpack25631, 2, false);
s->SetAt(32, unpack25631.at(0));
s->SetAt(33, unpack25631.at(1));
auto v25632 = Get(Get(Get(s->LocalAt(9), Value("tiles")), s->LocalAt(33)), s->LocalAt(32));
s->SetAt(30, v25632);
if (static_cast<bool>(([&]() -> Value { auto v25633 = ([&]() -> Value { auto v25634 = Get(s->LocalAt(31), s->LocalAt(10)); Value v25635; v25635 = List({Value("HARVEST")}); if (!static_cast<bool>(Binary("Eq", v25634, v25635))) return Value(false); v25634 = v25635; return Value(true); }()); if (!static_cast<bool>(v25633)) return v25633; v25633 = ([&]() -> Value { auto v25636 = Tuple({s->LocalAt(32), s->LocalAt(33)}); Value v25637; v25637 = Get(s->LocalAt(27), Value("sites")); if (!static_cast<bool>(Binary("In", v25636, v25637))) return Value(false); v25636 = v25637; return Value(true); }()); if (!static_cast<bool>(v25633)) return v25633; v25633 = ([&]() -> Value { auto fn25638 = s->Global("isinstance"); Arguments args25639; args25639.positional.reserve(2); args25639.Add(s->LocalAt(30), false); args25639.Add(s->Global("dict"), false); return Call(c, fn25638, std::move(args25639)); }()); if (!static_cast<bool>(v25633)) return v25633; v25633 = ([&]() -> Value { auto v25640 = ([&]() -> Value { auto fn25642 = PrepareDictionaryGet(s->LocalAt(30)); Arguments args25643; args25643.Add(Value("animal"), false); return CallDictionaryGet(c, fn25642, std::move(args25643)); }()); Value v25641; v25641 = Get(s->LocalAt(27), Value("mode")); if (!static_cast<bool>(Binary("Eq", v25640, v25641))) return Value(false); v25640 = v25641; return Value(true); }()); return v25633; }()))) {
auto v25644 = ([&]() -> Value { auto fn25645 = s->Global("max"); Arguments args25646; args25646.positional.reserve(2); args25646.Add(Value(int64_t{0}), false); args25646.Add(([&]() -> Value { auto fn25647 = s->Global("int"); Arguments args25648; args25648.Add(([&]() -> Value { auto fn25649 = PrepareDictionaryGet(s->LocalAt(30)); Arguments args25650; args25650.positional.reserve(2); args25650.Add(Value("yield_units"), false); args25650.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn25649, std::move(args25650)); }()), false); return Call(c, fn25647, std::move(args25648)); }()), false); return Call(c, fn25645, std::move(args25646)); }());
s->SetAt(15, v25644);
auto v25651 = s->LocalAt(27);
auto v25652 = Value("credit");
auto v25653 = Get(v25651, v25652);
Put(v25651, v25652, Inplace("Add", v25653, s->LocalAt(15)));
auto v25654 = s->Global("_CS_REPORT");
auto v25655 = Value("cs_credit");
auto v25656 = Get(v25654, v25655);
Put(v25654, v25655, Inplace("Add", v25656, s->LocalAt(15)));
}
}
if (static_cast<bool>(([&]() -> Value { auto v25657 = Get(s->LocalAt(27), Value("credit")); Value v25658; v25658 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v25657, v25658))) return Value(false); v25657 = v25658; return Value(true); }()))) {
auto v25659 = ([&]() -> Value { auto fn25660 = s->Global("projected_shed"); Arguments args25661; args25661.positional.reserve(2); args25661.Add(s->LocalAt(0), false); args25661.Add(([&]() -> Value { auto fn25662 = s->Global("FarmView"); Arguments args25663; args25663.Add(s->LocalAt(18), false); return Call(c, fn25662, std::move(args25663)); }()), false); return Call(c, fn25660, std::move(args25661)); }());
s->SetAt(29, v25659);
auto v25664 = ([&]() -> Value { auto fn25665 = s->Global("sum"); Arguments args25666; args25666.Add(([&]() -> Value { auto comp25667 = std::make_shared<Scope>(); comp25667->globals = s->globals; comp25667->parent = s; static constexpr const char* comp25667_names[] = {"o"}; comp25667->PrepareSlots(comp25667_names); auto result25668 = List(); for (const auto& item25669 : Iterate(s->LocalAt(14))) { comp25667->SetAt(0, item25669); if (!static_cast<bool>(([&]() -> Value { auto v25670 = ([&]() -> Value { auto v25671 = ([&]() -> Value { auto fn25673 = comp25667->Global("len"); Arguments args25674; args25674.Add(comp25667->LocalAt(0), false); return Call(c, fn25673, std::move(args25674)); }()); Value v25672; v25672 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v25671, v25672))) return Value(false); v25671 = v25672; return Value(true); }()); if (!static_cast<bool>(v25670)) return v25670; v25670 = ([&]() -> Value { auto v25675 = Slice(comp25667->LocalAt(0), Value{}, Value(int64_t{2}), Value{}); Value v25676; v25676 = List({Value("SELL"), comp25667->Captured("product")}); if (!static_cast<bool>(Binary("Eq", v25675, v25676))) return Value(false); v25675 = v25676; return Value(true); }()); return v25670; }()))) continue; result25668.node()->sequence.push_back(([&]() -> Value { auto fn25677 = comp25667->Global("max"); Arguments args25678; args25678.positional.reserve(2); args25678.Add(Value(int64_t{0}), false); args25678.Add(([&]() -> Value { auto fn25679 = comp25667->Global("int"); Arguments args25680; args25680.Add(Get(comp25667->LocalAt(0), Value(int64_t{2})), false); return Call(c, fn25679, std::move(args25680)); }()), false); return Call(c, fn25677, std::move(args25678)); }())); } return result25668; }()), false); return Call(c, fn25665, std::move(args25666)); }());
s->SetAt(20, v25664);
auto v25681 = ([&]() -> Value { auto fn25682 = s->Global("min"); Arguments args25683; args25683.positional.reserve(2); args25683.Add(Get(s->LocalAt(27), Value("credit")), false); args25683.Add(([&]() -> Value { auto fn25684 = s->Global("max"); Arguments args25685; args25685.positional.reserve(2); args25685.Add(Value(int64_t{0}), false); args25685.Add(([&]() -> Value { auto v25686 = ([&]() -> Value { auto fn25687 = s->Global("int"); Arguments args25688; args25688.Add(([&]() -> Value { auto fn25689 = PrepareDictionaryGet(s->LocalAt(29)); Arguments args25690; args25690.positional.reserve(2); args25690.Add(s->LocalAt(23), false); args25690.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn25689, std::move(args25690)); }()), false); return Call(c, fn25687, std::move(args25688)); }()); return Binary("Sub", v25686, s->LocalAt(20)); }()), false); return Call(c, fn25684, std::move(args25685)); }()), false); return Call(c, fn25682, std::move(args25683)); }());
s->SetAt(8, v25681);
if (static_cast<bool>(([&]() -> Value { auto v25691 = s->LocalAt(8); Value v25692; v25692 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v25691, v25692))) return Value(false); v25691 = v25692; return Value(true); }()))) {
bool exhausted25693 = true;
for (const auto& item25694 : Iterate(s->LocalAt(14))) {
s->SetAt(17, item25694);
if (static_cast<bool>(([&]() -> Value { auto v25695 = ([&]() -> Value { auto v25696 = ([&]() -> Value { auto fn25698 = s->Global("len"); Arguments args25699; args25699.Add(s->LocalAt(17), false); return Call(c, fn25698, std::move(args25699)); }()); Value v25697; v25697 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v25696, v25697))) return Value(false); v25696 = v25697; return Value(true); }()); if (!static_cast<bool>(v25695)) return v25695; v25695 = ([&]() -> Value { auto v25700 = Slice(s->LocalAt(17), Value{}, Value(int64_t{2}), Value{}); Value v25701; v25701 = List({Value("SELL"), s->LocalAt(23)}); if (!static_cast<bool>(Binary("Eq", v25700, v25701))) return Value(false); v25700 = v25701; return Value(true); }()); return v25695; }()))) {
auto v25702 = ([&]() -> Value { auto v25703 = ([&]() -> Value { auto fn25704 = s->Global("int"); Arguments args25705; args25705.Add(Get(s->LocalAt(17), Value(int64_t{2})), false); return Call(c, fn25704, std::move(args25705)); }()); return Binary("Add", v25703, s->LocalAt(8)); }());
Put(s->LocalAt(17), Value(int64_t{2}), v25702);
exhausted25693 = false;
break;
}
}
if (exhausted25693) {
if (static_cast<bool>(([&]() -> Value { auto v25706 = ([&]() -> Value { auto fn25708 = s->Global("len"); Arguments args25709; args25709.Add(s->LocalAt(14), false); return Call(c, fn25708, std::move(args25709)); }()); Value v25707; v25707 = Value(int64_t{10}); if (!static_cast<bool>(Binary("Lt", v25706, v25707))) return Value(false); v25706 = v25707; return Value(true); }()))) {
(void)([&]() -> Value { auto fn25710 = Attribute(s->LocalAt(14), "insert"); Arguments args25711; args25711.positional.reserve(2); args25711.Add(Value(int64_t{0}), false); args25711.Add(List({Value("SELL"), s->LocalAt(23), s->LocalAt(8)}), false); return Call(c, fn25710, std::move(args25711)); }());
}
else {
auto v25712 = Value(int64_t{0});
s->SetAt(8, v25712);
}
}
auto v25713 = s->LocalAt(27);
auto v25714 = Value("credit");
auto v25715 = Get(v25713, v25714);
Put(v25713, v25714, Inplace("Sub", v25715, s->LocalAt(8)));
auto v25716 = s->Global("_CS_REPORT");
auto v25717 = Value("cs_sold");
auto v25718 = Get(v25716, v25717);
Put(v25716, v25717, Inplace("Add", v25718, s->LocalAt(8)));
}
}
}
auto v25719 = ([&]() -> Value { auto fn25720 = s->Global("dict"); Arguments args25721; args25721.Add(s->LocalAt(0), false); return Call(c, fn25720, std::move(args25721)); }());
s->SetAt(0, v25719);
auto v25722 = s->LocalAt(14);
Put(s->LocalAt(0), Value("market"), v25722);
} catch (const Error& error25321) {
if (Matches(error25321, s->Global("Exception"))) {
auto v25723 = s->Global("_CS_REPORT");
auto v25724 = Value("cs_errors");
auto v25725 = Get(v25723, v25724);
Put(v25723, v25724, Inplace("Add", v25725, Value(int64_t{1})));
}
else { throw; }
}
return s->LocalAt(0);
return {};
}
}  // namespace kagg::opponents::compiled
