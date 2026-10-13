// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_147603540158fc8a1882(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"a", "action", "avail", "cap", "carried", "cfg", "consumed", "fillable", "i", "item", "market", "needed", "o", "op", "planned_buys", "planned_sells", "priority", "produced", "qty", "route", "self", "shed_total", "step", "tile", "units", "view"};
s->PrepareSlots(s_names);
auto v1445 = Attribute(s->LocalAt(20), "cfg");
s->SetAt(5, v1445);
if (static_cast<bool>(([&]() -> Value { auto v1446 = ([&]() -> Value { auto v1448 = s->LocalAt(22); return Binary("Mod", v1448, Get(s->LocalAt(5), Value("turns_per_day"))); }()); Value v1447; v1447 = ([&]() -> Value { auto v1449 = Get(s->LocalAt(5), Value("turns_per_day")); return Binary("Sub", v1449, Value(int64_t{1})); }()); if (!static_cast<bool>(Binary("NotEq", v1446, v1447))) return Value(false); v1446 = v1447; return Value(true); }()))) {
return Value{};
}
auto v1450 = Get(s->LocalAt(5), Value("shed_capacity"));
s->SetAt(3, v1450);
auto v1451 = ([&]() -> Value { auto v1452 = List({([&]() -> Value { auto v1453 = ([&]() -> Value { auto fn1454 = PrepareDictionaryGet(s->LocalAt(1)); Arguments args1455; args1455.Add(Value("farmer"), false); return CallDictionaryGet(c, fn1454, std::move(args1455)); }()); if (static_cast<bool>(v1453)) return v1453; v1453 = List({Value("PASS")}); return v1453; }())}); return Binary("Add", v1452, ([&]() -> Value { auto fn1456 = s->Global("list"); Arguments args1457; args1457.Add(([&]() -> Value { auto v1458 = ([&]() -> Value { auto fn1459 = PrepareDictionaryGet(s->LocalAt(1)); Arguments args1460; args1460.Add(Value("hands"), false); return CallDictionaryGet(c, fn1459, std::move(args1460)); }()); if (static_cast<bool>(v1458)) return v1458; v1458 = List({}); return v1458; }()), false); return Call(c, fn1456, std::move(args1457)); }())); }());
s->SetAt(24, v1451);
auto v1461 = ([&]() -> Value { auto fn1462 = s->Global("sum"); Arguments args1463; args1463.Add(([&]() -> Value { auto comp1464 = std::make_shared<Scope>(); comp1464->globals = s->globals; comp1464->parent = s; static constexpr const char* comp1464_names[] = {"inv", "n"}; comp1464->PrepareSlots(comp1464_names); auto result1465 = List(); for (const auto& item1466 : Iterate(Attribute(s->LocalAt(25), "invs"))) { comp1464->SetAt(0, item1466); for (const auto& item1467 : Iterate(([&]() -> Value { auto fn1468 = Attribute(comp1464->LocalAt(0), "values"); Arguments args1469; return Call(c, fn1468, std::move(args1469)); }()))) { comp1464->SetAt(1, item1467); result1465.node()->sequence.push_back(([&]() -> Value { auto fn1470 = comp1464->Global("max"); Arguments args1471; args1471.positional.reserve(2); args1471.Add(Value(int64_t{0}), false); args1471.Add(([&]() -> Value { auto fn1472 = comp1464->Global("_int"); Arguments args1473; args1473.Add(comp1464->LocalAt(1), false); return Call(c, fn1472, std::move(args1473)); }()), false); return Call(c, fn1470, std::move(args1471)); }())); } } return result1465; }()), false); return Call(c, fn1462, std::move(args1463)); }());
s->SetAt(4, v1461);
auto v1474 = Value(int64_t{0});
s->SetAt(17, v1474);
s->SetAt(6, v1474);
for (const auto& item1475 : Iterate(([&]() -> Value { auto fn1476 = s->Global("range"); Arguments args1477; args1477.Add(([&]() -> Value { auto fn1478 = s->Global("min"); Arguments args1479; args1479.positional.reserve(2); args1479.Add(([&]() -> Value { auto fn1480 = s->Global("len"); Arguments args1481; args1481.Add(s->LocalAt(24), false); return Call(c, fn1480, std::move(args1481)); }()), false); args1479.Add(([&]() -> Value { auto fn1482 = s->Global("len"); Arguments args1483; args1483.Add(Attribute(s->LocalAt(25), "positions"), false); return Call(c, fn1482, std::move(args1483)); }()), false); return Call(c, fn1478, std::move(args1479)); }()), false); return Call(c, fn1476, std::move(args1477)); }()))) {
s->SetAt(8, item1475);
auto v1484 = ([&]() -> Value { auto fn1485 = s->Global("_tile_at"); Arguments args1486; args1486.positional.reserve(2); args1486.Add(Attribute(s->LocalAt(25), "tiles"), false); args1486.Add(Get(Attribute(s->LocalAt(25), "positions"), s->LocalAt(8)), false); return Call(c, fn1485, std::move(args1486)); }());
s->SetAt(23, v1484);
auto v1487 = Get(s->LocalAt(24), s->LocalAt(8));
s->SetAt(0, v1487);
if (static_cast<bool>(Unary("Not", s->LocalAt(0)))) {
continue;
}
auto v1488 = Get(s->LocalAt(0), Value(int64_t{0}));
s->SetAt(13, v1488);
if (static_cast<bool>(([&]() -> Value { auto v1489 = ([&]() -> Value { auto v1490 = s->LocalAt(13); Value v1491; v1491 = Value("HARVEST"); if (!static_cast<bool>(Binary("Eq", v1490, v1491))) return Value(false); v1490 = v1491; return Value(true); }()); if (!static_cast<bool>(v1489)) return v1489; v1489 = ([&]() -> Value { auto fn1492 = s->Global("isinstance"); Arguments args1493; args1493.positional.reserve(2); args1493.Add(s->LocalAt(23), false); args1493.Add(s->Global("dict"), false); return Call(c, fn1492, std::move(args1493)); }()); return v1489; }()))) {
auto v1494 = s->LocalAt(17);
s->SetAt(17, Inplace("Add", v1494, ([&]() -> Value { auto fn1495 = s->Global("max"); Arguments args1496; args1496.positional.reserve(2); args1496.Add(Value(int64_t{0}), false); args1496.Add(([&]() -> Value { auto fn1497 = s->Global("_int"); Arguments args1498; args1498.Add(([&]() -> Value { auto fn1499 = s->Global("_get"); Arguments args1500; args1500.positional.reserve(3); args1500.Add(s->LocalAt(23), false); args1500.Add(Value("yield_units"), false); args1500.Add(Value(int64_t{0}), false); return Call(c, fn1499, std::move(args1500)); }()), false); return Call(c, fn1497, std::move(args1498)); }()), false); return Call(c, fn1495, std::move(args1496)); }())));
}
else {
if (static_cast<bool>(([&]() -> Value { auto v1501 = ([&]() -> Value { auto v1502 = s->LocalAt(13); Value v1503; v1503 = Value("COLLECT_FERTILIZER"); if (!static_cast<bool>(Binary("Eq", v1502, v1503))) return Value(false); v1502 = v1503; return Value(true); }()); if (!static_cast<bool>(v1501)) return v1501; v1501 = ([&]() -> Value { auto fn1504 = s->Global("isinstance"); Arguments args1505; args1505.positional.reserve(2); args1505.Add(s->LocalAt(23), false); args1505.Add(s->Global("dict"), false); return Call(c, fn1504, std::move(args1505)); }()); if (!static_cast<bool>(v1501)) return v1501; v1501 = ([&]() -> Value { auto fn1506 = s->Global("_get"); Arguments args1507; args1507.positional.reserve(2); args1507.Add(s->LocalAt(23), false); args1507.Add(Value("fertilizer_available"), false); return Call(c, fn1506, std::move(args1507)); }()); return v1501; }()))) {
auto v1508 = s->LocalAt(17);
s->SetAt(17, Inplace("Add", v1508, Value(int64_t{1})));
}
else {
if (static_cast<bool>(([&]() -> Value { auto v1509 = s->LocalAt(13); Value v1510; v1510 = Tuple({Value("FEED"), Value("FERTILIZE")}); if (!static_cast<bool>(Binary("In", v1509, v1510))) return Value(false); v1509 = v1510; return Value(true); }()))) {
auto v1511 = s->LocalAt(6);
s->SetAt(6, Inplace("Add", v1511, Value(int64_t{1})));
}
else {
if (static_cast<bool>(([&]() -> Value { auto v1512 = ([&]() -> Value { auto v1513 = s->LocalAt(13); Value v1514; v1514 = Value("PLACE"); if (!static_cast<bool>(Binary("Eq", v1513, v1514))) return Value(false); v1513 = v1514; return Value(true); }()); if (!static_cast<bool>(v1512)) return v1512; v1512 = ([&]() -> Value { auto v1515 = ([&]() -> Value { auto fn1517 = s->Global("len"); Arguments args1518; args1518.Add(s->LocalAt(0), false); return Call(c, fn1517, std::move(args1518)); }()); Value v1516; v1516 = Value(int64_t{1}); if (!static_cast<bool>(Binary("Gt", v1515, v1516))) return Value(false); v1515 = v1516; return Value(true); }()); if (!static_cast<bool>(v1512)) return v1512; v1512 = ([&]() -> Value { auto v1519 = Get(s->LocalAt(0), Value(int64_t{1})); Value v1520; v1520 = s->Global("ANIMAL_STRUCTURE"); if (!static_cast<bool>(Binary("In", v1519, v1520))) return Value(false); v1519 = v1520; return Value(true); }()); return v1512; }()))) {
auto v1521 = s->LocalAt(6);
s->SetAt(6, Inplace("Add", v1521, Value(int64_t{1})));
}
}
}
}
}
auto v1522 = ([&]() -> Value { auto fn1523 = Attribute(s->LocalAt(1), "setdefault"); Arguments args1524; args1524.positional.reserve(2); args1524.Add(Value("market"), false); args1524.Add(List({}), false); return Call(c, fn1523, std::move(args1524)); }());
s->SetAt(10, v1522);
auto v1525 = Tuple({([&]() -> Value { auto dict1526 = Dict(); return dict1526; }()), Value(int64_t{0})});
auto unpack1527 = Iterate(v1525);
ValidateUnpack(unpack1527, 2, false);
s->SetAt(15, unpack1527.at(0));
s->SetAt(14, unpack1527.at(1));
for (const auto& item1528 : Iterate(s->LocalAt(10))) {
s->SetAt(12, item1528);
if (static_cast<bool>(Unary("Not", s->LocalAt(12)))) {
continue;
}
if (static_cast<bool>(([&]() -> Value { auto v1529 = ([&]() -> Value { auto v1530 = Get(s->LocalAt(12), Value(int64_t{0})); Value v1531; v1531 = Value("SELL"); if (!static_cast<bool>(Binary("Eq", v1530, v1531))) return Value(false); v1530 = v1531; return Value(true); }()); if (!static_cast<bool>(v1529)) return v1529; v1529 = ([&]() -> Value { auto v1532 = ([&]() -> Value { auto fn1534 = s->Global("len"); Arguments args1535; args1535.Add(s->LocalAt(12), false); return Call(c, fn1534, std::move(args1535)); }()); Value v1533; v1533 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v1532, v1533))) return Value(false); v1532 = v1533; return Value(true); }()); return v1529; }()))) {
auto v1536 = ([&]() -> Value { auto v1537 = ([&]() -> Value { auto fn1538 = PrepareDictionaryGet(s->LocalAt(15)); Arguments args1539; args1539.positional.reserve(2); args1539.Add(Get(s->LocalAt(12), Value(int64_t{1})), false); args1539.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn1538, std::move(args1539)); }()); return Binary("Add", v1537, ([&]() -> Value { auto fn1540 = s->Global("max"); Arguments args1541; args1541.positional.reserve(2); args1541.Add(Value(int64_t{0}), false); args1541.Add(([&]() -> Value { auto fn1542 = s->Global("_int"); Arguments args1543; args1543.Add(Get(s->LocalAt(12), Value(int64_t{2})), false); return Call(c, fn1542, std::move(args1543)); }()), false); return Call(c, fn1540, std::move(args1541)); }())); }());
Put(s->LocalAt(15), Get(s->LocalAt(12), Value(int64_t{1})), v1536);
}
else {
if (static_cast<bool>(([&]() -> Value { auto v1544 = ([&]() -> Value { auto v1545 = Get(s->LocalAt(12), Value(int64_t{0})); Value v1546; v1546 = Tuple({Value("BUY_PRODUCT"), Value("BUY_ANIMAL")}); if (!static_cast<bool>(Binary("In", v1545, v1546))) return Value(false); v1545 = v1546; return Value(true); }()); if (!static_cast<bool>(v1544)) return v1544; v1544 = ([&]() -> Value { auto v1547 = ([&]() -> Value { auto fn1549 = s->Global("len"); Arguments args1550; args1550.Add(s->LocalAt(12), false); return Call(c, fn1549, std::move(args1550)); }()); Value v1548; v1548 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v1547, v1548))) return Value(false); v1547 = v1548; return Value(true); }()); return v1544; }()))) {
auto v1551 = s->LocalAt(14);
s->SetAt(14, Inplace("Add", v1551, ([&]() -> Value { auto fn1552 = s->Global("max"); Arguments args1553; args1553.positional.reserve(2); args1553.Add(Value(int64_t{0}), false); args1553.Add(([&]() -> Value { auto fn1554 = s->Global("_int"); Arguments args1555; args1555.Add(Get(s->LocalAt(12), Value(int64_t{2})), false); return Call(c, fn1554, std::move(args1555)); }()), false); return Call(c, fn1552, std::move(args1553)); }())));
}
}
}
auto v1556 = ([&]() -> Value { auto fn1557 = s->Global("sum"); Arguments args1558; args1558.Add(([&]() -> Value { auto fn1559 = Attribute(Attribute(s->LocalAt(25), "shed"), "values"); Arguments args1560; return Call(c, fn1559, std::move(args1560)); }()), false); return Call(c, fn1557, std::move(args1558)); }());
s->SetAt(21, v1556);
auto v1561 = ([&]() -> Value { auto fn1562 = s->Global("sum"); Arguments args1563; args1563.Add(([&]() -> Value { auto comp1564 = std::make_shared<Scope>(); comp1564->globals = s->globals; comp1564->parent = s; static constexpr const char* comp1564_names[] = {"it", "n"}; comp1564->PrepareSlots(comp1564_names); auto result1565 = List(); for (const auto& item1566 : Iterate(([&]() -> Value { auto fn1567 = Attribute(s->LocalAt(15), "items"); Arguments args1568; return Call(c, fn1567, std::move(args1568)); }()))) { auto unpack1569 = Iterate(item1566); ValidateUnpack(unpack1569, 2, false); comp1564->SetAt(0, unpack1569.at(0)); comp1564->SetAt(1, unpack1569.at(1)); result1565.node()->sequence.push_back(([&]() -> Value { auto fn1570 = comp1564->Global("min"); Arguments args1571; args1571.positional.reserve(2); args1571.Add(([&]() -> Value { auto fn1572 = PrepareDictionaryGet(Attribute(comp1564->Captured("view"), "shed")); Arguments args1573; args1573.positional.reserve(2); args1573.Add(comp1564->LocalAt(0), false); args1573.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn1572, std::move(args1573)); }()), false); args1571.Add(comp1564->LocalAt(1), false); return Call(c, fn1570, std::move(args1571)); }())); } return result1565; }()), false); return Call(c, fn1562, std::move(args1563)); }());
s->SetAt(7, v1561);
auto v1574 = ([&]() -> Value { auto v1575 = ([&]() -> Value { auto v1576 = ([&]() -> Value { auto v1577 = ([&]() -> Value { auto v1578 = ([&]() -> Value { auto v1579 = ([&]() -> Value { auto v1580 = s->LocalAt(21); return Binary("Add", v1580, s->LocalAt(4)); }()); return Binary("Add", v1579, s->LocalAt(17)); }()); return Binary("Sub", v1578, s->LocalAt(6)); }()); return Binary("Add", v1577, s->LocalAt(14)); }()); return Binary("Sub", v1576, s->LocalAt(7)); }()); return Binary("Sub", v1575, ([&]() -> Value { auto v1581 = s->LocalAt(3); return Binary("Sub", v1581, Value(int64_t{1})); }())); }());
s->SetAt(11, v1574);
if (static_cast<bool>(([&]() -> Value { auto v1582 = s->LocalAt(11); Value v1583; v1583 = Value(int64_t{0}); if (!static_cast<bool>(Binary("LtE", v1582, v1583))) return Value(false); v1582 = v1583; return Value(true); }()))) {
return Value{};
}
auto v1584 = ([&]() -> Value { auto fn1585 = s->Global("sorted"); Arguments args1586; args1586.Add(s->Global("PRODUCTS"), false); args1586.Keyword("key", Define(&Code_0fcb78f073ea469d3324, s, Signature{{"it"}, {}, {}, {}, "", "", ([]() -> std::span<const char* const> { static constexpr const char* names[] = {"it"}; return names; }())}, true, "<lambda>")); return Call(c, fn1585, std::move(args1586)); }());
s->SetAt(16, v1584);
for (const auto& item1594 : Iterate(s->LocalAt(16))) {
s->SetAt(9, item1594);
auto v1595 = ([&]() -> Value { auto fn1596 = s->Global("max"); Arguments args1597; args1597.positional.reserve(2); args1597.Add(Value(int64_t{0}), false); args1597.Add(([&]() -> Value { auto v1598 = ([&]() -> Value { auto fn1599 = PrepareDictionaryGet(Attribute(s->LocalAt(25), "shed")); Arguments args1600; args1600.positional.reserve(2); args1600.Add(s->LocalAt(9), false); args1600.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn1599, std::move(args1600)); }()); return Binary("Sub", v1598, ([&]() -> Value { auto fn1601 = PrepareDictionaryGet(s->LocalAt(15)); Arguments args1602; args1602.positional.reserve(2); args1602.Add(s->LocalAt(9), false); args1602.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn1601, std::move(args1602)); }())); }()), false); return Call(c, fn1596, std::move(args1597)); }());
s->SetAt(2, v1595);
auto v1603 = ([&]() -> Value { auto fn1604 = s->Global("min"); Arguments args1605; args1605.positional.reserve(2); args1605.Add(s->LocalAt(11), false); args1605.Add(s->LocalAt(2), false); return Call(c, fn1604, std::move(args1605)); }());
s->SetAt(18, v1603);
if (static_cast<bool>(([&]() -> Value { auto v1606 = ([&]() -> Value { auto v1607 = s->LocalAt(18); Value v1608; v1608 = Value(int64_t{0}); if (!static_cast<bool>(Binary("LtE", v1607, v1608))) return Value(false); v1607 = v1608; return Value(true); }()); if (static_cast<bool>(v1606)) return v1606; v1606 = ([&]() -> Value { auto v1609 = ([&]() -> Value { auto fn1611 = PrepareDictionaryGet(Attribute(s->LocalAt(25), "prices")); Arguments args1612; args1612.positional.reserve(2); args1612.Add(s->LocalAt(9), false); args1612.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn1611, std::move(args1612)); }()); Value v1610; v1610 = Value(int64_t{1}); if (!static_cast<bool>(Binary("Lt", v1609, v1610))) return Value(false); v1609 = v1610; return Value(true); }()); return v1606; }()))) {
continue;
}
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto fn1613 = Attribute(s->LocalAt(20), "_add_sell"); Arguments args1614; args1614.positional.reserve(4); args1614.Add(s->LocalAt(1), false); args1614.Add(s->LocalAt(9), false); args1614.Add(s->LocalAt(18), false); args1614.Add(Get(s->LocalAt(5), Value("max_orders")), false); return Call(c, fn1613, std::move(args1614)); }())))) {
continue;
}
auto v1615 = ([&]() -> Value { auto v1616 = ([&]() -> Value { auto fn1617 = PrepareDictionaryGet(s->LocalAt(15)); Arguments args1618; args1618.positional.reserve(2); args1618.Add(s->LocalAt(9), false); args1618.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn1617, std::move(args1618)); }()); return Binary("Add", v1616, s->LocalAt(18)); }());
Put(s->LocalAt(15), s->LocalAt(9), v1615);
auto v1619 = s->LocalAt(11);
s->SetAt(11, Inplace("Sub", v1619, s->LocalAt(18)));
if (static_cast<bool>(([&]() -> Value { auto v1620 = s->LocalAt(11); Value v1621; v1621 = Value(int64_t{0}); if (!static_cast<bool>(Binary("LtE", v1620, v1621))) return Value(false); v1620 = v1621; return Value(true); }()))) {
break;
}
}
return {};
}
}  // namespace kagg::opponents::compiled
