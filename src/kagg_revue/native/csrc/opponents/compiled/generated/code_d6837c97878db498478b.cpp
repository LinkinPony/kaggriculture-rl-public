// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_d6837c97878db498478b(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"a", "arg", "budget", "day", "end", "extra", "first", "hires_by_day", "item", "item_bal", "item_need", "k", "n", "o", "op", "qty", "quadrants", "route", "seed_bal", "seed_need", "self", "start", "t", "tape", "u", "view"};
s->PrepareSlots(s_names);
auto v1140 = Get(Attribute(s->LocalAt(20), "routes"), s->LocalAt(17));
s->SetAt(23, v1140);
auto v1141 = Value(0.0);
s->SetAt(2, v1141);
auto v1142 = Tuple({([&]() -> Value { auto dict1143 = Dict(); return dict1143; }()), ([&]() -> Value { auto dict1144 = Dict(); return dict1144; }())});
auto unpack1145 = Iterate(v1142);
ValidateUnpack(unpack1145, 2, false);
s->SetAt(18, unpack1145.at(0));
s->SetAt(9, unpack1145.at(1));
auto v1146 = Tuple({([&]() -> Value { auto dict1147 = Dict(); return dict1147; }()), ([&]() -> Value { auto dict1148 = Dict(); return dict1148; }())});
auto unpack1149 = Iterate(v1146);
ValidateUnpack(unpack1149, 2, false);
s->SetAt(19, unpack1149.at(0));
s->SetAt(10, unpack1149.at(1));
auto v1150 = ([&]() -> Value { auto dict1151 = Dict(); return dict1151; }());
s->SetAt(7, v1150);
auto v1152 = Attribute(s->LocalAt(25), "quadrants");
s->SetAt(16, v1152);
for (const auto& item1153 : Iterate(([&]() -> Value { auto fn1154 = s->Global("range"); Arguments args1155; args1155.positional.reserve(2); args1155.Add(s->LocalAt(21), false); args1155.Add(([&]() -> Value { auto fn1156 = s->Global("min"); Arguments args1157; args1157.positional.reserve(2); args1157.Add(s->LocalAt(4), false); args1157.Add(([&]() -> Value { auto fn1158 = s->Global("len"); Arguments args1159; args1159.Add(s->LocalAt(23), false); return Call(c, fn1158, std::move(args1159)); }()), false); return Call(c, fn1156, std::move(args1157)); }()), false); return Call(c, fn1154, std::move(args1155)); }()))) {
s->SetAt(22, item1153);
auto v1160 = (static_cast<bool>(([&]() -> Value { auto fn1161 = s->Global("isinstance"); Arguments args1162; args1162.positional.reserve(2); args1162.Add(Get(s->LocalAt(23), s->LocalAt(22)), false); args1162.Add(s->Global("dict"), false); return Call(c, fn1161, std::move(args1162)); }())) ? Get(s->LocalAt(23), s->LocalAt(22)) : ([&]() -> Value { auto dict1163 = Dict(); return dict1163; }()));
s->SetAt(0, v1160);
for (const auto& item1164 : Iterate(([&]() -> Value { auto v1165 = List({([&]() -> Value { auto v1166 = ([&]() -> Value { auto fn1167 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args1168; args1168.Add(Value("farmer"), false); return CallDictionaryGet(c, fn1167, std::move(args1168)); }()); if (static_cast<bool>(v1166)) return v1166; v1166 = List({Value("PASS")}); return v1166; }())}); return Binary("Add", v1165, ([&]() -> Value { auto fn1169 = s->Global("list"); Arguments args1170; args1170.Add(([&]() -> Value { auto v1171 = ([&]() -> Value { auto fn1172 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args1173; args1173.Add(Value("hands"), false); return CallDictionaryGet(c, fn1172, std::move(args1173)); }()); if (static_cast<bool>(v1171)) return v1171; v1171 = List({}); return v1171; }()), false); return Call(c, fn1169, std::move(args1170)); }())); }()))) {
s->SetAt(24, item1164);
if (static_cast<bool>(Unary("Not", s->LocalAt(24)))) {
continue;
}
auto v1174 = Get(s->LocalAt(24), Value(int64_t{0}));
s->SetAt(14, v1174);
auto v1175 = (static_cast<bool>(([&]() -> Value { auto v1176 = ([&]() -> Value { auto fn1178 = s->Global("len"); Arguments args1179; args1179.Add(s->LocalAt(24), false); return Call(c, fn1178, std::move(args1179)); }()); Value v1177; v1177 = Value(int64_t{1}); if (!static_cast<bool>(Binary("Gt", v1176, v1177))) return Value(false); v1176 = v1177; return Value(true); }())) ? Get(s->LocalAt(24), Value(int64_t{1})) : Value{});
s->SetAt(1, v1175);
auto v1180 = ([&]() -> Value { auto fn1181 = s->Global("max"); Arguments args1182; args1182.positional.reserve(2); args1182.Add(Value(int64_t{1}), false); args1182.Add((static_cast<bool>(([&]() -> Value { auto v1183 = ([&]() -> Value { auto fn1185 = s->Global("len"); Arguments args1186; args1186.Add(s->LocalAt(24), false); return Call(c, fn1185, std::move(args1186)); }()); Value v1184; v1184 = Value(int64_t{2}); if (!static_cast<bool>(Binary("Gt", v1183, v1184))) return Value(false); v1183 = v1184; return Value(true); }())) ? ([&]() -> Value { auto fn1187 = s->Global("_int"); Arguments args1188; args1188.Add(Get(s->LocalAt(24), Value(int64_t{2})), false); return Call(c, fn1187, std::move(args1188)); }()) : Value(int64_t{1})), false); return Call(c, fn1181, std::move(args1182)); }());
s->SetAt(15, v1180);
if (static_cast<bool>(([&]() -> Value { auto v1189 = ([&]() -> Value { auto v1190 = s->LocalAt(14); Value v1191; v1191 = Value("PLANT"); if (!static_cast<bool>(Binary("Eq", v1190, v1191))) return Value(false); v1190 = v1191; return Value(true); }()); if (!static_cast<bool>(v1189)) return v1189; v1189 = ([&]() -> Value { auto v1192 = s->LocalAt(1); Value v1193; v1193 = s->Global("SEED_PRICE"); if (!static_cast<bool>(Binary("In", v1192, v1193))) return Value(false); v1192 = v1193; return Value(true); }()); return v1189; }()))) {
auto v1194 = ([&]() -> Value { auto v1195 = ([&]() -> Value { auto fn1196 = PrepareDictionaryGet(s->LocalAt(18)); Arguments args1197; args1197.positional.reserve(2); args1197.Add(s->LocalAt(1), false); args1197.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn1196, std::move(args1197)); }()); return Binary("Sub", v1195, Value(int64_t{1})); }());
Put(s->LocalAt(18), s->LocalAt(1), v1194);
auto v1198 = ([&]() -> Value { auto fn1199 = s->Global("max"); Arguments args1200; args1200.positional.reserve(2); args1200.Add(([&]() -> Value { auto fn1201 = PrepareDictionaryGet(s->LocalAt(19)); Arguments args1202; args1202.positional.reserve(2); args1202.Add(s->LocalAt(1), false); args1202.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn1201, std::move(args1202)); }()), false); args1200.Add(Unary("USub", Get(s->LocalAt(18), s->LocalAt(1))), false); return Call(c, fn1199, std::move(args1200)); }());
Put(s->LocalAt(19), s->LocalAt(1), v1198);
}
else {
if (static_cast<bool>(([&]() -> Value { auto v1203 = s->LocalAt(14); Value v1204; v1204 = Value("FEED"); if (!static_cast<bool>(Binary("Eq", v1203, v1204))) return Value(false); v1203 = v1204; return Value(true); }()))) {
auto v1205 = ([&]() -> Value { auto v1206 = ([&]() -> Value { auto fn1207 = PrepareDictionaryGet(s->LocalAt(9)); Arguments args1208; args1208.positional.reserve(2); args1208.Add(Value("WHEAT"), false); args1208.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn1207, std::move(args1208)); }()); return Binary("Sub", v1206, Value(int64_t{1})); }());
Put(s->LocalAt(9), Value("WHEAT"), v1205);
auto v1209 = ([&]() -> Value { auto fn1210 = s->Global("max"); Arguments args1211; args1211.positional.reserve(2); args1211.Add(([&]() -> Value { auto fn1212 = PrepareDictionaryGet(s->LocalAt(10)); Arguments args1213; args1213.positional.reserve(2); args1213.Add(Value("WHEAT"), false); args1213.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn1212, std::move(args1213)); }()), false); args1211.Add(Unary("USub", Get(s->LocalAt(9), Value("WHEAT"))), false); return Call(c, fn1210, std::move(args1211)); }());
Put(s->LocalAt(10), Value("WHEAT"), v1209);
}
else {
if (static_cast<bool>(([&]() -> Value { auto v1214 = s->LocalAt(14); Value v1215; v1215 = Value("FERTILIZE"); if (!static_cast<bool>(Binary("Eq", v1214, v1215))) return Value(false); v1214 = v1215; return Value(true); }()))) {
auto v1216 = ([&]() -> Value { auto v1217 = ([&]() -> Value { auto fn1218 = PrepareDictionaryGet(s->LocalAt(9)); Arguments args1219; args1219.positional.reserve(2); args1219.Add(Value("FERTILIZER"), false); args1219.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn1218, std::move(args1219)); }()); return Binary("Sub", v1217, Value(int64_t{1})); }());
Put(s->LocalAt(9), Value("FERTILIZER"), v1216);
auto v1220 = ([&]() -> Value { auto fn1221 = s->Global("max"); Arguments args1222; args1222.positional.reserve(2); args1222.Add(([&]() -> Value { auto fn1223 = PrepareDictionaryGet(s->LocalAt(10)); Arguments args1224; args1224.positional.reserve(2); args1224.Add(Value("FERTILIZER"), false); args1224.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn1223, std::move(args1224)); }()), false); args1222.Add(Unary("USub", Get(s->LocalAt(9), Value("FERTILIZER"))), false); return Call(c, fn1221, std::move(args1222)); }());
Put(s->LocalAt(10), Value("FERTILIZER"), v1220);
}
else {
if (static_cast<bool>(([&]() -> Value { auto v1225 = ([&]() -> Value { auto v1226 = s->LocalAt(14); Value v1227; v1227 = Value("PLACE"); if (!static_cast<bool>(Binary("Eq", v1226, v1227))) return Value(false); v1226 = v1227; return Value(true); }()); if (!static_cast<bool>(v1225)) return v1225; v1225 = ([&]() -> Value { auto v1228 = s->LocalAt(1); Value v1229; v1229 = Value{}; if (!static_cast<bool>(Binary("IsNot", v1228, v1229))) return Value(false); v1228 = v1229; return Value(true); }()); return v1225; }()))) {
auto v1230 = ([&]() -> Value { auto v1231 = ([&]() -> Value { auto fn1232 = PrepareDictionaryGet(s->LocalAt(9)); Arguments args1233; args1233.positional.reserve(2); args1233.Add(s->LocalAt(1), false); args1233.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn1232, std::move(args1233)); }()); return Binary("Sub", v1231, s->LocalAt(15)); }());
Put(s->LocalAt(9), s->LocalAt(1), v1230);
auto v1234 = ([&]() -> Value { auto fn1235 = s->Global("max"); Arguments args1236; args1236.positional.reserve(2); args1236.Add(([&]() -> Value { auto fn1237 = PrepareDictionaryGet(s->LocalAt(10)); Arguments args1238; args1238.positional.reserve(2); args1238.Add(s->LocalAt(1), false); args1238.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn1237, std::move(args1238)); }()), false); args1236.Add(Unary("USub", Get(s->LocalAt(9), s->LocalAt(1))), false); return Call(c, fn1235, std::move(args1236)); }());
Put(s->LocalAt(10), s->LocalAt(1), v1234);
}
}
}
}
}
for (const auto& item1239 : Iterate(([&]() -> Value { auto v1240 = ([&]() -> Value { auto fn1241 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args1242; args1242.Add(Value("market"), false); return CallDictionaryGet(c, fn1241, std::move(args1242)); }()); if (static_cast<bool>(v1240)) return v1240; v1240 = List({}); return v1240; }()))) {
s->SetAt(13, item1239);
if (static_cast<bool>(Unary("Not", s->LocalAt(13)))) {
continue;
}
auto v1243 = Get(s->LocalAt(13), Value(int64_t{0}));
s->SetAt(14, v1243);
auto v1244 = (static_cast<bool>(([&]() -> Value { auto v1245 = ([&]() -> Value { auto fn1247 = s->Global("len"); Arguments args1248; args1248.Add(s->LocalAt(13), false); return Call(c, fn1247, std::move(args1248)); }()); Value v1246; v1246 = Value(int64_t{1}); if (!static_cast<bool>(Binary("Gt", v1245, v1246))) return Value(false); v1245 = v1246; return Value(true); }())) ? Get(s->LocalAt(13), Value(int64_t{1})) : Value{});
s->SetAt(8, v1244);
auto v1249 = ([&]() -> Value { auto fn1250 = s->Global("max"); Arguments args1251; args1251.positional.reserve(2); args1251.Add(Value(int64_t{1}), false); args1251.Add((static_cast<bool>(([&]() -> Value { auto v1252 = ([&]() -> Value { auto fn1254 = s->Global("len"); Arguments args1255; args1255.Add(s->LocalAt(13), false); return Call(c, fn1254, std::move(args1255)); }()); Value v1253; v1253 = Value(int64_t{2}); if (!static_cast<bool>(Binary("Gt", v1252, v1253))) return Value(false); v1252 = v1253; return Value(true); }())) ? ([&]() -> Value { auto fn1256 = s->Global("_int"); Arguments args1257; args1257.Add(Get(s->LocalAt(13), Value(int64_t{2})), false); return Call(c, fn1256, std::move(args1257)); }()) : Value(int64_t{1})), false); return Call(c, fn1250, std::move(args1251)); }());
s->SetAt(15, v1249);
if (static_cast<bool>(([&]() -> Value { auto v1258 = s->LocalAt(14); Value v1259; v1259 = Value("HIRE"); if (!static_cast<bool>(Binary("Eq", v1258, v1259))) return Value(false); v1258 = v1259; return Value(true); }()))) {
auto v1260 = ([&]() -> Value { auto v1261 = ([&]() -> Value { auto v1262 = s->LocalAt(22); return Binary("Sub", v1262, s->LocalAt(21)); }()); return Binary("FloorDiv", v1261, Get(Attribute(s->LocalAt(20), "cfg"), Value("turns_per_day"))); }());
s->SetAt(3, v1260);
auto v1263 = ([&]() -> Value { auto v1264 = ([&]() -> Value { auto fn1265 = PrepareDictionaryGet(s->LocalAt(7)); Arguments args1266; args1266.positional.reserve(2); args1266.Add(s->LocalAt(3), false); args1266.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn1265, std::move(args1266)); }()); return Binary("Add", v1264, Value(int64_t{1})); }());
Put(s->LocalAt(7), s->LocalAt(3), v1263);
}
else {
if (static_cast<bool>(([&]() -> Value { auto v1267 = s->LocalAt(14); Value v1268; v1268 = Value("BUY_LAND"); if (!static_cast<bool>(Binary("Eq", v1267, v1268))) return Value(false); v1267 = v1268; return Value(true); }()))) {
auto v1269 = ([&]() -> Value { auto v1270 = s->LocalAt(16); return Binary("Sub", v1270, Value(int64_t{1})); }());
s->SetAt(5, v1269);
if (static_cast<bool>(([&]() -> Value { auto v1271 = Value(int64_t{0}); Value v1272; v1272 = s->LocalAt(5); if (!static_cast<bool>(Binary("LtE", v1271, v1272))) return Value(false); v1271 = v1272; v1272 = ([&]() -> Value { auto fn1273 = s->Global("len"); Arguments args1274; args1274.Add(s->Global("LAND_PRICES"), false); return Call(c, fn1273, std::move(args1274)); }()); if (!static_cast<bool>(Binary("Lt", v1271, v1272))) return Value(false); v1271 = v1272; return Value(true); }()))) {
auto v1275 = s->LocalAt(2);
s->SetAt(2, Inplace("Add", v1275, Get(s->Global("LAND_PRICES"), s->LocalAt(5))));
auto v1276 = s->LocalAt(16);
s->SetAt(16, Inplace("Add", v1276, Value(int64_t{1})));
}
}
else {
if (static_cast<bool>(([&]() -> Value { auto v1277 = ([&]() -> Value { auto v1278 = s->LocalAt(14); Value v1279; v1279 = Value("BUY_SEED"); if (!static_cast<bool>(Binary("Eq", v1278, v1279))) return Value(false); v1278 = v1279; return Value(true); }()); if (!static_cast<bool>(v1277)) return v1277; v1277 = ([&]() -> Value { auto v1280 = s->LocalAt(8); Value v1281; v1281 = s->Global("SEED_PRICE"); if (!static_cast<bool>(Binary("In", v1280, v1281))) return Value(false); v1280 = v1281; return Value(true); }()); return v1277; }()))) {
auto v1282 = s->LocalAt(2);
s->SetAt(2, Inplace("Add", v1282, ([&]() -> Value { auto v1283 = Get(s->Global("SEED_PRICE"), s->LocalAt(8)); return Binary("Mult", v1283, s->LocalAt(15)); }())));
auto v1284 = ([&]() -> Value { auto v1285 = ([&]() -> Value { auto fn1286 = PrepareDictionaryGet(s->LocalAt(18)); Arguments args1287; args1287.positional.reserve(2); args1287.Add(s->LocalAt(8), false); args1287.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn1286, std::move(args1287)); }()); return Binary("Add", v1285, s->LocalAt(15)); }());
Put(s->LocalAt(18), s->LocalAt(8), v1284);
}
else {
if (static_cast<bool>(([&]() -> Value { auto v1288 = ([&]() -> Value { auto v1289 = s->LocalAt(14); Value v1290; v1290 = Value("BUY_PRODUCT"); if (!static_cast<bool>(Binary("Eq", v1289, v1290))) return Value(false); v1289 = v1290; return Value(true); }()); if (!static_cast<bool>(v1288)) return v1288; v1288 = ([&]() -> Value { auto v1291 = s->LocalAt(8); Value v1292; v1292 = Tuple({Value("WHEAT"), Value("FERTILIZER")}); if (!static_cast<bool>(Binary("In", v1291, v1292))) return Value(false); v1291 = v1292; return Value(true); }()); return v1288; }()))) {
auto v1293 = s->LocalAt(2);
s->SetAt(2, Inplace("Add", v1293, ([&]() -> Value { auto v1294 = ([&]() -> Value { auto fn1295 = PrepareDictionaryGet(Attribute(s->LocalAt(25), "prices")); Arguments args1296; args1296.positional.reserve(2); args1296.Add(s->LocalAt(8), false); args1296.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn1295, std::move(args1296)); }()); return Binary("Mult", v1294, s->LocalAt(15)); }())));
auto v1297 = ([&]() -> Value { auto v1298 = ([&]() -> Value { auto fn1299 = PrepareDictionaryGet(s->LocalAt(9)); Arguments args1300; args1300.positional.reserve(2); args1300.Add(s->LocalAt(8), false); args1300.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn1299, std::move(args1300)); }()); return Binary("Add", v1298, s->LocalAt(15)); }());
Put(s->LocalAt(9), s->LocalAt(8), v1297);
}
else {
if (static_cast<bool>(([&]() -> Value { auto v1301 = ([&]() -> Value { auto v1302 = s->LocalAt(14); Value v1303; v1303 = Value("BUY_ANIMAL"); if (!static_cast<bool>(Binary("Eq", v1302, v1303))) return Value(false); v1302 = v1303; return Value(true); }()); if (!static_cast<bool>(v1301)) return v1301; v1301 = ([&]() -> Value { auto v1304 = s->LocalAt(8); Value v1305; v1305 = s->Global("ANIMAL_COST"); if (!static_cast<bool>(Binary("In", v1304, v1305))) return Value(false); v1304 = v1305; return Value(true); }()); return v1301; }()))) {
auto v1306 = s->LocalAt(2);
s->SetAt(2, Inplace("Add", v1306, ([&]() -> Value { auto v1307 = Get(s->Global("ANIMAL_COST"), s->LocalAt(8)); return Binary("Mult", v1307, s->LocalAt(15)); }())));
auto v1308 = ([&]() -> Value { auto v1309 = ([&]() -> Value { auto fn1310 = PrepareDictionaryGet(s->LocalAt(9)); Arguments args1311; args1311.positional.reserve(2); args1311.Add(s->LocalAt(8), false); args1311.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn1310, std::move(args1311)); }()); return Binary("Add", v1309, s->LocalAt(15)); }());
Put(s->LocalAt(9), s->LocalAt(8), v1308);
}
}
}
}
}
}
}
for (const auto& item1312 : Iterate(([&]() -> Value { auto fn1313 = Attribute(s->LocalAt(7), "items"); Arguments args1314; return Call(c, fn1313, std::move(args1314)); }()))) {
auto unpack1315 = Iterate(item1312);
ValidateUnpack(unpack1315, 2, false);
s->SetAt(3, unpack1315.at(0));
s->SetAt(12, unpack1315.at(1));
auto v1316 = (static_cast<bool>(([&]() -> Value { auto v1317 = s->LocalAt(3); Value v1318; v1318 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v1317, v1318))) return Value(false); v1317 = v1318; return Value(true); }())) ? Attribute(s->LocalAt(25), "hires_today") : Value(int64_t{0}));
s->SetAt(6, v1316);
for (const auto& item1319 : Iterate(([&]() -> Value { auto fn1320 = s->Global("range"); Arguments args1321; args1321.Add(s->LocalAt(12), false); return Call(c, fn1320, std::move(args1321)); }()))) {
s->SetAt(11, item1319);
auto v1322 = s->LocalAt(2);
s->SetAt(2, Inplace("Add", v1322, ([&]() -> Value { auto fn1323 = s->Global("_fib"); Arguments args1324; args1324.Add(([&]() -> Value { auto v1325 = s->LocalAt(6); return Binary("Add", v1325, s->LocalAt(11)); }()), false); return Call(c, fn1323, std::move(args1324)); }())));
}
}
return Tuple({s->LocalAt(2), s->LocalAt(10)});
return {};
}
}  // namespace kagg::opponents::compiled
