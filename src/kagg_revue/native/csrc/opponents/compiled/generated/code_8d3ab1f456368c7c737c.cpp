// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_8d3ab1f456368c7c737c(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"_", "action", "added", "avail", "block", "budget", "candidates", "cash", "cfg", "existing", "item", "item_need", "market", "o", "others", "planned", "price", "protected", "qty", "route", "self", "sells", "shortfall", "step", "view"};
s->PrepareSlots(s_names);
auto v1326 = Attribute(s->LocalAt(20), "cfg");
s->SetAt(8, v1326);
auto v1327 = Get(s->LocalAt(8), Value("block_turns"));
s->SetAt(4, v1327);
if (static_cast<bool>(([&]() -> Value { auto v1328 = ([&]() -> Value { auto v1329 = s->LocalAt(4); Value v1330; v1330 = Value(int64_t{0}); if (!static_cast<bool>(Binary("LtE", v1329, v1330))) return Value(false); v1329 = v1330; return Value(true); }()); if (static_cast<bool>(v1328)) return v1328; v1328 = ([&]() -> Value { auto v1331 = ([&]() -> Value { auto v1333 = s->LocalAt(23); return Binary("Mod", v1333, s->LocalAt(4)); }()); Value v1332; v1332 = Value(int64_t{0}); if (!static_cast<bool>(Binary("NotEq", v1331, v1332))) return Value(false); v1331 = v1332; return Value(true); }()); return v1328; }()))) {
return Value{};
}
auto v1334 = ([&]() -> Value { auto fn1335 = Attribute(s->LocalAt(20), "_block_requirements"); Arguments args1336; args1336.positional.reserve(4); args1336.Add(s->LocalAt(24), false); args1336.Add(s->LocalAt(19), false); args1336.Add(s->LocalAt(23), false); args1336.Add(([&]() -> Value { auto v1337 = s->LocalAt(23); return Binary("Add", v1337, s->LocalAt(4)); }()), false); return Call(c, fn1335, std::move(args1336)); }());
auto unpack1338 = Iterate(v1334);
ValidateUnpack(unpack1338, 2, false);
s->SetAt(5, unpack1338.at(0));
s->SetAt(11, unpack1338.at(1));
auto v1339 = ([&]() -> Value { auto fn1340 = Attribute(s->LocalAt(1), "setdefault"); Arguments args1341; args1341.positional.reserve(2); args1341.Add(Value("market"), false); args1341.Add(List({}), false); return Call(c, fn1340, std::move(args1341)); }());
s->SetAt(12, v1339);
auto v1342 = ([&]() -> Value { auto dict1343 = Dict(); return dict1343; }());
s->SetAt(9, v1342);
for (const auto& item1344 : Iterate(s->LocalAt(12))) {
s->SetAt(13, item1344);
if (static_cast<bool>(([&]() -> Value { auto v1345 = s->LocalAt(13); if (!static_cast<bool>(v1345)) return v1345; v1345 = ([&]() -> Value { auto v1346 = Get(s->LocalAt(13), Value(int64_t{0})); Value v1347; v1347 = Value("SELL"); if (!static_cast<bool>(Binary("Eq", v1346, v1347))) return Value(false); v1346 = v1347; return Value(true); }()); if (!static_cast<bool>(v1345)) return v1345; v1345 = ([&]() -> Value { auto v1348 = ([&]() -> Value { auto fn1350 = s->Global("len"); Arguments args1351; args1351.Add(s->LocalAt(13), false); return Call(c, fn1350, std::move(args1351)); }()); Value v1349; v1349 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v1348, v1349))) return Value(false); v1348 = v1349; return Value(true); }()); return v1345; }()))) {
auto v1352 = ([&]() -> Value { auto v1353 = ([&]() -> Value { auto fn1354 = PrepareDictionaryGet(s->LocalAt(9)); Arguments args1355; args1355.positional.reserve(2); args1355.Add(Get(s->LocalAt(13), Value(int64_t{1})), false); args1355.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn1354, std::move(args1355)); }()); return Binary("Add", v1353, ([&]() -> Value { auto fn1356 = s->Global("max"); Arguments args1357; args1357.positional.reserve(2); args1357.Add(Value(int64_t{0}), false); args1357.Add(([&]() -> Value { auto fn1358 = s->Global("_int"); Arguments args1359; args1359.Add(Get(s->LocalAt(13), Value(int64_t{2})), false); return Call(c, fn1358, std::move(args1359)); }()), false); return Call(c, fn1356, std::move(args1357)); }())); }());
Put(s->LocalAt(9), Get(s->LocalAt(13), Value(int64_t{1})), v1352);
}
}
auto v1360 = Attribute(s->LocalAt(24), "money");
s->SetAt(7, v1360);
for (const auto& item1361 : Iterate(s->Global("PRODUCTS"))) {
s->SetAt(10, item1361);
auto v1362 = ([&]() -> Value { auto fn1363 = s->Global("max"); Arguments args1364; args1364.positional.reserve(2); args1364.Add(([&]() -> Value { auto fn1365 = PrepareDictionaryGet(s->LocalAt(9)); Arguments args1366; args1366.positional.reserve(2); args1366.Add(s->LocalAt(10), false); args1366.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn1365, std::move(args1366)); }()), false); args1364.Add(([&]() -> Value { auto v1367 = ([&]() -> Value { auto fn1368 = Attribute(s->LocalAt(20), "future_sells"); Arguments args1369; args1369.positional.reserve(3); args1369.Add(s->LocalAt(19), false); args1369.Add(s->LocalAt(10), false); args1369.Add(s->LocalAt(23), false); return Call(c, fn1368, std::move(args1369)); }()); return Binary("Sub", v1367, ([&]() -> Value { auto fn1370 = Attribute(s->LocalAt(20), "future_sells"); Arguments args1371; args1371.positional.reserve(3); args1371.Add(s->LocalAt(19), false); args1371.Add(s->LocalAt(10), false); args1371.Add(([&]() -> Value { auto v1372 = s->LocalAt(23); return Binary("Add", v1372, s->LocalAt(4)); }()), false); return Call(c, fn1370, std::move(args1371)); }())); }()), false); return Call(c, fn1363, std::move(args1364)); }());
s->SetAt(15, v1362);
auto v1373 = s->LocalAt(7);
s->SetAt(7, Inplace("Add", v1373, ([&]() -> Value { auto v1374 = ([&]() -> Value { auto fn1375 = s->Global("min"); Arguments args1376; args1376.positional.reserve(2); args1376.Add(([&]() -> Value { auto fn1377 = PrepareDictionaryGet(Attribute(s->LocalAt(24), "shed")); Arguments args1378; args1378.positional.reserve(2); args1378.Add(s->LocalAt(10), false); args1378.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn1377, std::move(args1378)); }()), false); args1376.Add(s->LocalAt(15), false); return Call(c, fn1375, std::move(args1376)); }()); return Binary("Mult", v1374, ([&]() -> Value { auto fn1379 = PrepareDictionaryGet(Attribute(s->LocalAt(24), "prices")); Arguments args1380; args1380.positional.reserve(2); args1380.Add(s->LocalAt(10), false); args1380.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn1379, std::move(args1380)); }())); }())));
}
auto v1381 = ([&]() -> Value { auto v1382 = s->LocalAt(5); return Binary("Sub", v1382, s->LocalAt(7)); }());
s->SetAt(22, v1381);
if (static_cast<bool>(([&]() -> Value { auto v1383 = s->LocalAt(22); Value v1384; v1384 = Value(int64_t{0}); if (!static_cast<bool>(Binary("LtE", v1383, v1384))) return Value(false); v1383 = v1384; return Value(true); }()))) {
return Value{};
}
auto v1385 = List({});
s->SetAt(6, v1385);
for (const auto& item1386 : Iterate(s->Global("PRODUCTS"))) {
s->SetAt(10, item1386);
auto v1387 = ([&]() -> Value { auto fn1388 = PrepareDictionaryGet(Attribute(s->LocalAt(24), "prices")); Arguments args1389; args1389.positional.reserve(2); args1389.Add(s->LocalAt(10), false); args1389.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn1388, std::move(args1389)); }());
s->SetAt(16, v1387);
if (static_cast<bool>(([&]() -> Value { auto v1390 = s->LocalAt(16); Value v1391; v1391 = Get(s->LocalAt(8), Value("min_sell_price")); if (!static_cast<bool>(Binary("Lt", v1390, v1391))) return Value(false); v1390 = v1391; return Value(true); }()))) {
continue;
}
auto v1392 = ([&]() -> Value { auto fn1393 = s->Global("max"); Arguments args1394; args1394.positional.reserve(2); args1394.Add(Value(int64_t{0}), false); args1394.Add(([&]() -> Value { auto v1395 = ([&]() -> Value { auto fn1396 = PrepareDictionaryGet(s->LocalAt(11)); Arguments args1397; args1397.positional.reserve(2); args1397.Add(s->LocalAt(10), false); args1397.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn1396, std::move(args1397)); }()); return Binary("Sub", v1395, ([&]() -> Value { auto fn1398 = Attribute(s->LocalAt(24), "in_hands"); Arguments args1399; args1399.Add(s->LocalAt(10), false); return Call(c, fn1398, std::move(args1399)); }())); }()), false); return Call(c, fn1393, std::move(args1394)); }());
s->SetAt(17, v1392);
auto v1400 = ([&]() -> Value { auto v1401 = ([&]() -> Value { auto v1402 = ([&]() -> Value { auto fn1403 = PrepareDictionaryGet(Attribute(s->LocalAt(24), "shed")); Arguments args1404; args1404.positional.reserve(2); args1404.Add(s->LocalAt(10), false); args1404.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn1403, std::move(args1404)); }()); return Binary("Sub", v1402, s->LocalAt(17)); }()); return Binary("Sub", v1401, ([&]() -> Value { auto fn1405 = PrepareDictionaryGet(s->LocalAt(9)); Arguments args1406; args1406.positional.reserve(2); args1406.Add(s->LocalAt(10), false); args1406.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn1405, std::move(args1406)); }())); }());
s->SetAt(3, v1400);
if (static_cast<bool>(([&]() -> Value { auto v1407 = s->LocalAt(3); Value v1408; v1408 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v1407, v1408))) return Value(false); v1407 = v1408; return Value(true); }()))) {
(void)([&]() -> Value { auto fn1409 = Attribute(s->LocalAt(6), "append"); Arguments args1410; args1410.Add(Tuple({Unary("USub", s->LocalAt(16)), s->LocalAt(10), s->LocalAt(3), s->LocalAt(16)}), false); return Call(c, fn1409, std::move(args1410)); }());
}
}
(void)([&]() -> Value { auto fn1411 = Attribute(s->LocalAt(6), "sort"); Arguments args1412; return Call(c, fn1411, std::move(args1412)); }());
auto v1413 = Value(false);
s->SetAt(2, v1413);
for (const auto& item1414 : Iterate(s->LocalAt(6))) {
auto unpack1415 = Iterate(item1414);
ValidateUnpack(unpack1415, 4, false);
s->SetAt(0, unpack1415.at(0));
s->SetAt(10, unpack1415.at(1));
s->SetAt(3, unpack1415.at(2));
s->SetAt(16, unpack1415.at(3));
if (static_cast<bool>(([&]() -> Value { auto v1416 = s->LocalAt(22); Value v1417; v1417 = Value(int64_t{0}); if (!static_cast<bool>(Binary("LtE", v1416, v1417))) return Value(false); v1416 = v1417; return Value(true); }()))) {
break;
}
auto v1418 = ([&]() -> Value { auto fn1419 = s->Global("min"); Arguments args1420; args1420.positional.reserve(2); args1420.Add(s->LocalAt(3), false); args1420.Add(Unary("USub", ([&]() -> Value { auto v1421 = Unary("USub", ([&]() -> Value { auto fn1422 = s->Global("int"); Arguments args1423; args1423.Add(s->LocalAt(22), false); return Call(c, fn1422, std::move(args1423)); }())); return Binary("FloorDiv", v1421, s->LocalAt(16)); }())), false); return Call(c, fn1419, std::move(args1420)); }());
s->SetAt(18, v1418);
if (static_cast<bool>(([&]() -> Value { auto fn1424 = Attribute(s->LocalAt(20), "_add_sell"); Arguments args1425; args1425.positional.reserve(4); args1425.Add(s->LocalAt(1), false); args1425.Add(s->LocalAt(10), false); args1425.Add(s->LocalAt(18), false); args1425.Add(Get(s->LocalAt(8), Value("max_orders")), false); return Call(c, fn1424, std::move(args1425)); }()))) {
auto v1426 = s->LocalAt(22);
s->SetAt(22, Inplace("Sub", v1426, ([&]() -> Value { auto v1427 = s->LocalAt(18); return Binary("Mult", v1427, s->LocalAt(16)); }())));
auto v1428 = Value(true);
s->SetAt(2, v1428);
}
}
if (static_cast<bool>(s->LocalAt(2))) {
auto v1429 = ([&]() -> Value { auto comp1430 = std::make_shared<Scope>(); comp1430->globals = s->globals; comp1430->parent = s; static constexpr const char* comp1430_names[] = {"o"}; comp1430->PrepareSlots(comp1430_names); auto result1431 = List(); for (const auto& item1432 : Iterate(s->LocalAt(12))) { comp1430->SetAt(0, item1432); if (!static_cast<bool>(([&]() -> Value { auto v1433 = comp1430->LocalAt(0); if (!static_cast<bool>(v1433)) return v1433; v1433 = ([&]() -> Value { auto v1434 = Get(comp1430->LocalAt(0), Value(int64_t{0})); Value v1435; v1435 = Value("SELL"); if (!static_cast<bool>(Binary("Eq", v1434, v1435))) return Value(false); v1434 = v1435; return Value(true); }()); return v1433; }()))) continue; result1431.node()->sequence.push_back(comp1430->LocalAt(0)); } return result1431; }());
s->SetAt(21, v1429);
auto v1436 = ([&]() -> Value { auto comp1437 = std::make_shared<Scope>(); comp1437->globals = s->globals; comp1437->parent = s; static constexpr const char* comp1437_names[] = {"o"}; comp1437->PrepareSlots(comp1437_names); auto result1438 = List(); for (const auto& item1439 : Iterate(s->LocalAt(12))) { comp1437->SetAt(0, item1439); if (!static_cast<bool>(Unary("Not", ([&]() -> Value { auto v1440 = comp1437->LocalAt(0); if (!static_cast<bool>(v1440)) return v1440; v1440 = ([&]() -> Value { auto v1441 = Get(comp1437->LocalAt(0), Value(int64_t{0})); Value v1442; v1442 = Value("SELL"); if (!static_cast<bool>(Binary("Eq", v1441, v1442))) return Value(false); v1441 = v1442; return Value(true); }()); return v1440; }())))) continue; result1438.node()->sequence.push_back(comp1437->LocalAt(0)); } return result1438; }());
s->SetAt(14, v1436);
auto v1443 = ([&]() -> Value { auto v1444 = s->LocalAt(21); return Binary("Add", v1444, s->LocalAt(14)); }());
Put(s->LocalAt(1), Value("market"), v1443);
}
return {};
}
}  // namespace kagg::opponents::compiled
