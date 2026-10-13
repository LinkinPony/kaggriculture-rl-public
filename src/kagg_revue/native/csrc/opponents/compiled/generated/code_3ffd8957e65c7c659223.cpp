// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_3ffd8957e65c7c659223(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"_", "animal_of", "base_demand", "base_prices", "carried", "d", "day", "existing", "extra_demand", "farm", "farm_index", "item", "k", "key", "market", "native", "new", "new_prices", "obs", "option", "order", "ours_existing", "params", "patch", "path", "revenue", "rival_existing", "row", "seat", "shed", "shops", "similar", "spec", "st", "swing", "t", "tape", "tile", "u", "unlocks_left"};
s->PrepareSlots(s_names);
auto v24255 = Get(s->Global("_HD2_SPEC"), s->LocalAt(19));
s->SetAt(32, v24255);
auto v24256 = Get(s->LocalAt(32), Value("product"));
s->SetAt(11, v24256);
auto v24257 = Get(([&]() -> Value { auto dict24258 = Dict(); auto key24259 = Value("EGG"); Put(dict24258, key24259, Value("GOOSE")); auto key24260 = Value("MILK"); Put(dict24258, key24260, Value("COW")); auto key24261 = Value("WOOL"); Put(dict24258, key24261, Value("SHEEP")); return dict24258; }()), s->LocalAt(11));
s->SetAt(1, v24257);
auto v24262 = ([&]() -> Value { auto v24263 = ([&]() -> Value { auto fn24264 = s->Global("int"); Arguments args24265; args24265.Add(Get(s->LocalAt(18), Value("step")), false); return Call(c, fn24264, std::move(args24265)); }()); return Binary("FloorDiv", v24263, Value(int64_t{24})); }());
s->SetAt(6, v24262);
auto v24266 = ([&]() -> Value { auto fn24267 = s->Global("int"); Arguments args24268; args24268.Add(Get(s->LocalAt(18), Value("player")), false); return Call(c, fn24267, std::move(args24268)); }());
s->SetAt(28, v24266);
auto v24269 = Get(s->LocalAt(18), Value("market"));
s->SetAt(14, v24269);
auto v24270 = ([&]() -> Value { auto comp24271 = std::make_shared<Scope>(); comp24271->globals = s->globals; comp24271->parent = s; static constexpr const char* comp24271_names[] = {"key", "v"}; comp24271->PrepareSlots(comp24271_names); auto result24272 = Dict(); for (const auto& item24273 : Iterate(([&]() -> Value { auto fn24274 = Attribute(s->Global("_R37_MARKET_PARAMS"), "items"); Arguments args24275; return Call(c, fn24274, std::move(args24275)); }()))) { auto unpack24276 = Iterate(item24273); ValidateUnpack(unpack24276, 2, false); comp24271->SetAt(0, unpack24276.at(0)); comp24271->SetAt(1, unpack24276.at(1)); Put(result24272, comp24271->LocalAt(0), ([&]() -> Value { auto fn24277 = comp24271->Global("dict"); Arguments args24278; args24278.Add(comp24271->LocalAt(1), false); return Call(c, fn24277, std::move(args24278)); }())); } return result24272; }());
s->SetAt(22, v24270);
for (const auto& item24279 : Iterate(([&]() -> Value { auto fn24280 = Attribute(([&]() -> Value { auto v24282 = ([&]() -> Value { auto fn24283 = PrepareDictionaryGet(s->LocalAt(14)); Arguments args24284; args24284.Add(Value("params"), false); return CallDictionaryGet(c, fn24283, std::move(args24284)); }()); if (static_cast<bool>(v24282)) return v24282; v24282 = ([&]() -> Value { auto dict24285 = Dict(); return dict24285; }()); return v24282; }()), "items"); Arguments args24281; return Call(c, fn24280, std::move(args24281)); }()))) {
auto unpack24286 = Iterate(item24279);
ValidateUnpack(unpack24286, 2, false);
s->SetAt(13, unpack24286.at(0));
s->SetAt(23, unpack24286.at(1));
if (static_cast<bool>(([&]() -> Value { auto v24287 = ([&]() -> Value { auto v24288 = s->LocalAt(13); Value v24289; v24289 = s->LocalAt(22); if (!static_cast<bool>(Binary("In", v24288, v24289))) return Value(false); v24288 = v24289; return Value(true); }()); if (!static_cast<bool>(v24287)) return v24287; v24287 = ([&]() -> Value { auto fn24290 = s->Global("isinstance"); Arguments args24291; args24291.positional.reserve(2); args24291.Add(s->LocalAt(23), false); args24291.Add(s->Global("dict"), false); return Call(c, fn24290, std::move(args24291)); }()); return v24287; }()))) {
(void)([&]() -> Value { auto fn24292 = Attribute(Get(s->LocalAt(22), s->LocalAt(13)), "update"); Arguments args24293; args24293.Add(s->LocalAt(23), false); return Call(c, fn24292, std::move(args24293)); }());
}
}
auto v24294 = List({([&]() -> Value { auto fn24295 = s->Global("dict"); Arguments args24296; return Call(c, fn24295, std::move(args24296)); }()), ([&]() -> Value { auto fn24297 = s->Global("dict"); Arguments args24298; return Call(c, fn24297, std::move(args24298)); }())});
s->SetAt(7, v24294);
for (const auto& item24299 : Iterate(([&]() -> Value { auto fn24300 = s->Global("enumerate"); Arguments args24301; args24301.Add(Get(s->LocalAt(18), Value("farms")), false); return Call(c, fn24300, std::move(args24301)); }()))) {
auto unpack24302 = Iterate(item24299);
ValidateUnpack(unpack24302, 2, false);
s->SetAt(10, unpack24302.at(0));
s->SetAt(9, unpack24302.at(1));
for (const auto& item24303 : Iterate(Get(s->LocalAt(9), Value("tiles")))) {
s->SetAt(27, item24303);
for (const auto& item24304 : Iterate(s->LocalAt(27))) {
s->SetAt(37, item24304);
if (static_cast<bool>(([&]() -> Value { auto v24305 = ([&]() -> Value { auto fn24306 = s->Global("isinstance"); Arguments args24307; args24307.positional.reserve(2); args24307.Add(s->LocalAt(37), false); args24307.Add(s->Global("dict"), false); return Call(c, fn24306, std::move(args24307)); }()); if (!static_cast<bool>(v24305)) return v24305; v24305 = ([&]() -> Value { auto v24308 = ([&]() -> Value { auto fn24310 = PrepareDictionaryGet(s->LocalAt(37)); Arguments args24311; args24311.Add(Value("animal"), false); return CallDictionaryGet(c, fn24310, std::move(args24311)); }()); Value v24309; v24309 = s->LocalAt(1); if (!static_cast<bool>(Binary("Eq", v24308, v24309))) return Value(false); v24308 = v24309; return Value(true); }()); return v24305; }()))) {
for (const auto& item24312 : Iterate(([&]() -> Value { auto fn24313 = Attribute(([&]() -> Value { auto fn24315 = s->Global("_hd2_schedule"); Arguments args24316; args24316.positional.reserve(3); args24316.Add(s->LocalAt(1), false); args24316.Add(([&]() -> Value { auto fn24317 = s->Global("int"); Arguments args24318; args24318.Add(([&]() -> Value { auto fn24319 = PrepareDictionaryGet(s->LocalAt(37)); Arguments args24320; args24320.positional.reserve(2); args24320.Add(Value("placed_day"), false); args24320.Add(s->LocalAt(6), false); return CallDictionaryGet(c, fn24319, std::move(args24320)); }()), false); return Call(c, fn24317, std::move(args24318)); }()), false); args24316.Add(([&]() -> Value { auto v24321 = s->LocalAt(6); return Binary("Add", v24321, Value(int64_t{1})); }()), false); return Call(c, fn24315, std::move(args24316)); }()), "items"); Arguments args24314; return Call(c, fn24313, std::move(args24314)); }()))) {
auto unpack24322 = Iterate(item24312);
ValidateUnpack(unpack24322, 2, false);
s->SetAt(5, unpack24322.at(0));
s->SetAt(38, unpack24322.at(1));
auto v24323 = ([&]() -> Value { auto v24324 = ([&]() -> Value { auto fn24325 = PrepareDictionaryGet(Get(s->LocalAt(7), s->LocalAt(10))); Arguments args24326; args24326.positional.reserve(2); args24326.Add(s->LocalAt(5), false); args24326.Add(Value(0.0), false); return CallDictionaryGet(c, fn24325, std::move(args24326)); }()); return Binary("Add", v24324, s->LocalAt(38)); }());
Put(Get(s->LocalAt(7), s->LocalAt(10)), s->LocalAt(5), v24323);
}
}
}
}
}
auto v24327 = ([&]() -> Value { auto v24328 = ([&]() -> Value { auto fn24329 = PrepareDictionaryGet(([&]() -> Value { auto v24331 = ([&]() -> Value { auto fn24332 = PrepareDictionaryGet(s->LocalAt(18)); Arguments args24333; args24333.Add(Value("private"), false); return CallDictionaryGet(c, fn24332, std::move(args24333)); }()); if (static_cast<bool>(v24331)) return v24331; v24331 = ([&]() -> Value { auto dict24334 = Dict(); return dict24334; }()); return v24331; }())); Arguments args24330; args24330.Add(Value("shed"), false); return CallDictionaryGet(c, fn24329, std::move(args24330)); }()); if (static_cast<bool>(v24328)) return v24328; v24328 = ([&]() -> Value { auto dict24335 = Dict(); return dict24335; }()); return v24328; }());
s->SetAt(29, v24327);
auto v24336 = ([&]() -> Value { auto fn24337 = s->Global("sum"); Arguments args24338; args24338.Add(([&]() -> Value { auto comp24339 = std::make_shared<Scope>(); comp24339->globals = s->globals; comp24339->parent = s; static constexpr const char* comp24339_names[] = {"inv"}; comp24339->PrepareSlots(comp24339_names); auto result24340 = List(); for (const auto& item24341 : Iterate(([&]() -> Value { auto v24342 = ([&]() -> Value { auto fn24343 = PrepareDictionaryGet(([&]() -> Value { auto v24345 = ([&]() -> Value { auto fn24346 = PrepareDictionaryGet(s->LocalAt(18)); Arguments args24347; args24347.Add(Value("private"), false); return CallDictionaryGet(c, fn24346, std::move(args24347)); }()); if (static_cast<bool>(v24345)) return v24345; v24345 = ([&]() -> Value { auto dict24348 = Dict(); return dict24348; }()); return v24345; }())); Arguments args24344; args24344.Add(Value("inventories"), false); return CallDictionaryGet(c, fn24343, std::move(args24344)); }()); if (static_cast<bool>(v24342)) return v24342; v24342 = List({}); return v24342; }()))) { comp24339->SetAt(0, item24341); result24340.node()->sequence.push_back(([&]() -> Value { auto fn24349 = comp24339->Global("int"); Arguments args24350; args24350.Add(([&]() -> Value { auto fn24351 = PrepareDictionaryGet(comp24339->LocalAt(0)); Arguments args24352; args24352.positional.reserve(2); args24352.Add(comp24339->Captured("animal_of"), false); args24352.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn24351, std::move(args24352)); }()), false); return Call(c, fn24349, std::move(args24350)); }())); } return result24340; }()), false); return Call(c, fn24337, std::move(args24338)); }());
s->SetAt(4, v24336);
for (const auto& item24353 : Iterate(([&]() -> Value { auto fn24354 = s->Global("range"); Arguments args24355; args24355.Add(([&]() -> Value { auto v24356 = ([&]() -> Value { auto fn24357 = s->Global("int"); Arguments args24358; args24358.Add(([&]() -> Value { auto fn24359 = PrepareDictionaryGet(s->LocalAt(29)); Arguments args24360; args24360.positional.reserve(2); args24360.Add(s->LocalAt(1), false); args24360.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn24359, std::move(args24360)); }()), false); return Call(c, fn24357, std::move(args24358)); }()); return Binary("Add", v24356, s->LocalAt(4)); }()), false); return Call(c, fn24354, std::move(args24355)); }()))) {
s->SetAt(0, item24353);
for (const auto& item24361 : Iterate(([&]() -> Value { auto fn24362 = Attribute(([&]() -> Value { auto fn24364 = s->Global("_hd2_schedule"); Arguments args24365; args24365.positional.reserve(3); args24365.Add(s->LocalAt(1), false); args24365.Add(([&]() -> Value { auto v24366 = s->LocalAt(6); return Binary("Add", v24366, Value(int64_t{1})); }()), false); args24365.Add(([&]() -> Value { auto v24367 = s->LocalAt(6); return Binary("Add", v24367, Value(int64_t{1})); }()), false); return Call(c, fn24364, std::move(args24365)); }()), "items"); Arguments args24363; return Call(c, fn24362, std::move(args24363)); }()))) {
auto unpack24368 = Iterate(item24361);
ValidateUnpack(unpack24368, 2, false);
s->SetAt(5, unpack24368.at(0));
s->SetAt(38, unpack24368.at(1));
auto v24369 = ([&]() -> Value { auto v24370 = ([&]() -> Value { auto fn24371 = PrepareDictionaryGet(Get(s->LocalAt(7), s->LocalAt(28))); Arguments args24372; args24372.positional.reserve(2); args24372.Add(s->LocalAt(5), false); args24372.Add(Value(0.0), false); return CallDictionaryGet(c, fn24371, std::move(args24372)); }()); return Binary("Add", v24370, s->LocalAt(38)); }());
Put(Get(s->LocalAt(7), s->LocalAt(28)), s->LocalAt(5), v24369);
}
}
auto v24373 = ([&]() -> Value { auto fn24374 = PrepareDictionaryGet(Attribute(Attribute(s->Global("_IMPL"), "chassis"), "players")); Arguments args24375; args24375.Add(s->LocalAt(28), false); return CallDictionaryGet(c, fn24374, std::move(args24375)); }());
s->SetAt(15, v24373);
if (static_cast<bool>(s->LocalAt(15))) {
auto v24376 = ([&]() -> Value { auto v24377 = ([&]() -> Value { auto fn24379 = s->Global("_r37_similarity"); Arguments args24380; args24380.Add(s->LocalAt(18), false); return Call(c, fn24379, std::move(args24380)); }()); Value v24378; v24378 = Value(0.9); if (!static_cast<bool>(Binary("GtE", v24377, v24378))) return Value(false); v24377 = v24378; return Value(true); }());
s->SetAt(31, v24376);
for (const auto& item24381 : Iterate(([&]() -> Value { auto fn24382 = s->Global("range"); Arguments args24383; args24383.positional.reserve(2); args24383.Add(([&]() -> Value { auto v24384 = ([&]() -> Value { auto fn24385 = s->Global("int"); Arguments args24386; args24386.Add(Get(s->LocalAt(18), Value("step")), false); return Call(c, fn24385, std::move(args24386)); }()); return Binary("Add", v24384, Value(int64_t{1})); }()), false); args24383.Add(Value(int64_t{696}), false); return Call(c, fn24382, std::move(args24383)); }()))) {
s->SetAt(35, item24381);
auto v24387 = Get(Attribute(Attribute(s->Global("_IMPL"), "chassis"), "routes"), (static_cast<bool>(([&]() -> Value { auto v24388 = s->LocalAt(35); Value v24389; v24389 = Value(int64_t{648}); if (!static_cast<bool>(Binary("GtE", v24388, v24389))) return Value(false); v24388 = v24389; return Value(true); }())) ? Value(int64_t{2}) : Get(s->LocalAt(15), Value("route"))));
s->SetAt(36, v24387);
if (static_cast<bool>(([&]() -> Value { auto v24390 = ([&]() -> Value { auto v24391 = s->LocalAt(35); Value v24392; v24392 = ([&]() -> Value { auto fn24393 = s->Global("len"); Arguments args24394; args24394.Add(s->LocalAt(36), false); return Call(c, fn24393, std::move(args24394)); }()); if (!static_cast<bool>(Binary("GtE", v24391, v24392))) return Value(false); v24391 = v24392; return Value(true); }()); if (static_cast<bool>(v24390)) return v24390; v24390 = Unary("Not", ([&]() -> Value { auto fn24395 = s->Global("isinstance"); Arguments args24396; args24396.positional.reserve(2); args24396.Add(Get(s->LocalAt(36), s->LocalAt(35)), false); args24396.Add(s->Global("dict"), false); return Call(c, fn24395, std::move(args24396)); }())); return v24390; }()))) {
continue;
}
for (const auto& item24397 : Iterate(([&]() -> Value { auto v24398 = ([&]() -> Value { auto fn24399 = PrepareDictionaryGet(Get(s->LocalAt(36), s->LocalAt(35))); Arguments args24400; args24400.positional.reserve(2); args24400.Add(Value("market"), false); args24400.Add(List({}), false); return CallDictionaryGet(c, fn24399, std::move(args24400)); }()); if (static_cast<bool>(v24398)) return v24398; v24398 = List({}); return v24398; }()))) {
s->SetAt(20, item24397);
if (static_cast<bool>(([&]() -> Value { auto v24401 = ([&]() -> Value { auto v24402 = ([&]() -> Value { auto fn24404 = s->Global("len"); Arguments args24405; args24405.Add(s->LocalAt(20), false); return Call(c, fn24404, std::move(args24405)); }()); Value v24403; v24403 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v24402, v24403))) return Value(false); v24402 = v24403; return Value(true); }()); if (!static_cast<bool>(v24401)) return v24401; v24401 = ([&]() -> Value { auto v24406 = Get(s->LocalAt(20), Value(int64_t{0})); Value v24407; v24407 = Value("BUY_ANIMAL"); if (!static_cast<bool>(Binary("Eq", v24406, v24407))) return Value(false); v24406 = v24407; return Value(true); }()); if (!static_cast<bool>(v24401)) return v24401; v24401 = ([&]() -> Value { auto v24408 = Get(s->LocalAt(20), Value(int64_t{1})); Value v24409; v24409 = s->LocalAt(1); if (!static_cast<bool>(Binary("Eq", v24408, v24409))) return Value(false); v24408 = v24409; return Value(true); }()); return v24401; }()))) {
for (const auto& item24410 : Iterate(([&]() -> Value { auto fn24411 = s->Global("range"); Arguments args24412; args24412.Add(([&]() -> Value { auto fn24413 = s->Global("max"); Arguments args24414; args24414.positional.reserve(2); args24414.Add(Value(int64_t{0}), false); args24414.Add(([&]() -> Value { auto fn24415 = s->Global("int"); Arguments args24416; args24416.Add(Get(s->LocalAt(20), Value(int64_t{2})), false); return Call(c, fn24415, std::move(args24416)); }()), false); return Call(c, fn24413, std::move(args24414)); }()), false); return Call(c, fn24411, std::move(args24412)); }()))) {
s->SetAt(0, item24410);
for (const auto& item24417 : Iterate(([&]() -> Value { auto fn24418 = Attribute(([&]() -> Value { auto fn24420 = s->Global("_hd2_schedule"); Arguments args24421; args24421.positional.reserve(3); args24421.Add(s->LocalAt(1), false); args24421.Add(([&]() -> Value { auto v24422 = ([&]() -> Value { auto v24423 = s->LocalAt(35); return Binary("FloorDiv", v24423, Value(int64_t{24})); }()); return Binary("Add", v24422, Value(int64_t{1})); }()), false); args24421.Add(([&]() -> Value { auto v24424 = s->LocalAt(6); return Binary("Add", v24424, Value(int64_t{1})); }()), false); return Call(c, fn24420, std::move(args24421)); }()), "items"); Arguments args24419; return Call(c, fn24418, std::move(args24419)); }()))) {
auto unpack24425 = Iterate(item24417);
ValidateUnpack(unpack24425, 2, false);
s->SetAt(5, unpack24425.at(0));
s->SetAt(38, unpack24425.at(1));
auto v24426 = ([&]() -> Value { auto v24427 = ([&]() -> Value { auto fn24428 = PrepareDictionaryGet(Get(s->LocalAt(7), s->LocalAt(28))); Arguments args24429; args24429.positional.reserve(2); args24429.Add(s->LocalAt(5), false); args24429.Add(Value(0.0), false); return CallDictionaryGet(c, fn24428, std::move(args24429)); }()); return Binary("Add", v24427, s->LocalAt(38)); }());
Put(Get(s->LocalAt(7), s->LocalAt(28)), s->LocalAt(5), v24426);
if (static_cast<bool>(s->LocalAt(31))) {
auto v24430 = ([&]() -> Value { auto v24431 = ([&]() -> Value { auto fn24432 = PrepareDictionaryGet(Get(s->LocalAt(7), ([&]() -> Value { auto v24434 = Value(int64_t{1}); return Binary("Sub", v24434, s->LocalAt(28)); }()))); Arguments args24433; args24433.positional.reserve(2); args24433.Add(s->LocalAt(5), false); args24433.Add(Value(0.0), false); return CallDictionaryGet(c, fn24432, std::move(args24433)); }()); return Binary("Add", v24431, s->LocalAt(38)); }());
Put(Get(s->LocalAt(7), ([&]() -> Value { auto v24435 = Value(int64_t{1}); return Binary("Sub", v24435, s->LocalAt(28)); }())), s->LocalAt(5), v24430);
}
}
}
}
}
}
}
auto v24436 = Tuple({Get(s->LocalAt(7), s->LocalAt(28)), Get(s->LocalAt(7), ([&]() -> Value { auto v24437 = Value(int64_t{1}); return Binary("Sub", v24437, s->LocalAt(28)); }()))});
auto unpack24438 = Iterate(v24436);
ValidateUnpack(unpack24438, 2, false);
s->SetAt(21, unpack24438.at(0));
s->SetAt(26, unpack24438.at(1));
auto v24439 = ([&]() -> Value { auto dict24440 = Dict(); return dict24440; }());
s->SetAt(16, v24439);
for (const auto& item24441 : Iterate(([&]() -> Value { auto fn24442 = Attribute(([&]() -> Value { auto fn24444 = s->Global("_hd2_schedule"); Arguments args24445; args24445.positional.reserve(3); args24445.Add(s->LocalAt(19), false); args24445.Add(([&]() -> Value { auto v24446 = s->LocalAt(6); return Binary("Add", v24446, Value(int64_t{1})); }()), false); args24445.Add(([&]() -> Value { auto v24447 = s->LocalAt(6); return Binary("Add", v24447, Value(int64_t{1})); }()), false); return Call(c, fn24444, std::move(args24445)); }()), "items"); Arguments args24443; return Call(c, fn24442, std::move(args24443)); }()))) {
auto unpack24448 = Iterate(item24441);
ValidateUnpack(unpack24448, 2, false);
s->SetAt(5, unpack24448.at(0));
s->SetAt(38, unpack24448.at(1));
auto v24449 = ([&]() -> Value { auto v24450 = s->LocalAt(38); return Binary("Mult", v24450, s->LocalAt(12)); }());
Put(s->LocalAt(16), s->LocalAt(5), v24449);
}
auto v24451 = ([&]() -> Value { auto fn24452 = s->Global("list"); Arguments args24453; args24453.Add(([&]() -> Value { auto v24454 = ([&]() -> Value { auto fn24455 = PrepareDictionaryGet(([&]() -> Value { auto v24457 = ([&]() -> Value { auto fn24458 = PrepareDictionaryGet(s->LocalAt(18)); Arguments args24459; args24459.Add(Value("town"), false); return CallDictionaryGet(c, fn24458, std::move(args24459)); }()); if (static_cast<bool>(v24457)) return v24457; v24457 = ([&]() -> Value { auto dict24460 = Dict(); return dict24460; }()); return v24457; }())); Arguments args24456; args24456.Add(Value("unlocked_shops"), false); return CallDictionaryGet(c, fn24455, std::move(args24456)); }()); if (static_cast<bool>(v24454)) return v24454; v24454 = List({}); return v24454; }()), false); return Call(c, fn24452, std::move(args24453)); }());
s->SetAt(30, v24451);
auto v24461 = ([&]() -> Value { auto fn24462 = s->Global("max"); Arguments args24463; args24463.positional.reserve(2); args24463.Add(Value(int64_t{0}), false); args24463.Add(([&]() -> Value { auto v24464 = Value(int64_t{8}); return Binary("Sub", v24464, ([&]() -> Value { auto fn24465 = s->Global("len"); Arguments args24466; args24466.Add(s->LocalAt(30), false); return Call(c, fn24465, std::move(args24466)); }())); }()), false); return Call(c, fn24462, std::move(args24463)); }());
s->SetAt(39, v24461);
auto v24467 = ([&]() -> Value { auto v24468 = ([&]() -> Value { auto fn24469 = s->Global("_hd2_daily_shop_demand"); Arguments args24470; args24470.positional.reserve(2); args24470.Add(s->LocalAt(11), false); args24470.Add(s->LocalAt(30), false); return Call(c, fn24469, std::move(args24470)); }()); return Binary("Add", v24468, Value(1.0)); }());
s->SetAt(2, v24467);
auto v24471 = ([&]() -> Value { auto v24472 = ([&]() -> Value { auto fn24473 = s->Global("_hd2_future_demand_per_day"); Arguments args24474; args24474.Add(s->LocalAt(11), false); return Call(c, fn24473, std::move(args24474)); }()); return Binary("Mult", v24472, s->Global("_HD2_FUTURE")); }());
s->SetAt(8, v24471);
s->SetAt(24, Define(&Code_00ebae454d1f150fd3ce, s, Signature{{"with_new"}, {}, {}, {}, "", "", ([]() -> std::span<const char* const> { static constexpr const char* names[] = {"_", "d", "inv", "opened", "price", "prices", "revenue", "units", "with_new"}; return names; }())}, true, "path"));
s->definitions.push_back("path");
auto v24530 = ([&]() -> Value { auto fn24531 = s->LocalAt(24); Arguments args24532; args24532.Add(Value(false), false); return Call(c, fn24531, std::move(args24532)); }());
auto unpack24533 = Iterate(v24530);
ValidateUnpack(unpack24533, 2, false);
s->SetAt(3, unpack24533.at(0));
s->SetAt(0, unpack24533.at(1));
auto v24534 = ([&]() -> Value { auto fn24535 = s->LocalAt(24); Arguments args24536; args24536.Add(Value(true), false); return Call(c, fn24535, std::move(args24536)); }());
auto unpack24537 = Iterate(v24534);
ValidateUnpack(unpack24537, 2, false);
s->SetAt(17, unpack24537.at(0));
s->SetAt(25, unpack24537.at(1));
auto v24538 = ([&]() -> Value { auto fn24539 = s->Global("sum"); Arguments args24540; args24540.Add(([&]() -> Value { auto comp24541 = std::make_shared<Scope>(); comp24541->globals = s->globals; comp24541->parent = s; static constexpr const char* comp24541_names[] = {"d"}; comp24541->PrepareSlots(comp24541_names); auto result24542 = List(); for (const auto& item24543 : Iterate(s->LocalAt(3))) { comp24541->SetAt(0, item24543); result24542.node()->sequence.push_back(([&]() -> Value { auto v24544 = ([&]() -> Value { auto v24545 = Get(comp24541->Captured("new_prices"), comp24541->LocalAt(0)); return Binary("Sub", v24545, Get(comp24541->Captured("base_prices"), comp24541->LocalAt(0))); }()); return Binary("Mult", v24544, ([&]() -> Value { auto v24546 = ([&]() -> Value { auto fn24547 = PrepareDictionaryGet(comp24541->Captured("ours_existing")); Arguments args24548; args24548.positional.reserve(2); args24548.Add(comp24541->LocalAt(0), false); args24548.Add(Value(0.0), false); return CallDictionaryGet(c, fn24547, std::move(args24548)); }()); return Binary("Sub", v24546, ([&]() -> Value { auto fn24549 = PrepareDictionaryGet(comp24541->Captured("rival_existing")); Arguments args24550; args24550.positional.reserve(2); args24550.Add(comp24541->LocalAt(0), false); args24550.Add(Value(0.0), false); return CallDictionaryGet(c, fn24549, std::move(args24550)); }())); }())); }())); } return result24542; }()), false); return Call(c, fn24539, std::move(args24540)); }());
s->SetAt(34, v24538);
return Tuple({([&]() -> Value { auto v24551 = ([&]() -> Value { auto v24552 = s->LocalAt(25); return Binary("Add", v24552, s->LocalAt(34)); }()); return Binary("Sub", v24551, ([&]() -> Value { auto v24553 = Get(s->LocalAt(32), Value("cost")); return Binary("Mult", v24553, s->LocalAt(12)); }())); }()), s->LocalAt(25)});
return {};
}
}  // namespace kagg::opponents::compiled
