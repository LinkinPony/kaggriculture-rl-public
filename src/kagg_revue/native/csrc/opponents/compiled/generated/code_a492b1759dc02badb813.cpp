// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_a492b1759dc02badb813(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "actor", "animal_orders", "cap", "cargo", "center", "confirmed", "counts", "cow_available", "extra", "farm", "gained", "inventories", "inventory", "line", "market", "milk_shops", "obs", "occupied", "order", "pending", "positions", "prices", "private", "quantity", "result", "seat", "seen_harvest", "shed", "shops", "site", "state", "step", "stock", "stock_animals", "tile", "total_planned", "units", "work", "workers", "x", "y"};
s->PrepareSlots(s_names);
auto v5299 = ([&]() -> Value { auto fn5300 = s->Global("int"); Arguments args5301; args5301.Add(Get(s->LocalAt(17), Value("step")), false); return Call(c, fn5300, std::move(args5301)); }());
s->SetAt(32, v5299);
auto v5302 = ([&]() -> Value { auto fn5303 = s->Global("int"); Arguments args5304; args5304.Add(Get(s->LocalAt(17), Value("player")), false); return Call(c, fn5303, std::move(args5304)); }());
s->SetAt(26, v5302);
auto v5305 = Get(Get(s->LocalAt(17), Value("farms")), s->LocalAt(26));
s->SetAt(10, v5305);
auto v5306 = Get(s->LocalAt(17), Value("private"));
s->SetAt(23, v5306);
auto v5307 = Get(s->LocalAt(23), Value("shed"));
s->SetAt(28, v5307);
auto v5308 = Get(s->LocalAt(23), Value("inventories"));
s->SetAt(12, v5308);
auto v5309 = ([&]() -> Value { Arguments args5310; args5310.Add(Get(s->LocalAt(10), Value("farmer")), false); args5310.Add(Get(s->LocalAt(10), Value("hands")), true); return List(std::move(args5310.positional)); }());
s->SetAt(21, v5309);
auto v5311 = Get(s->LocalAt(31), Value("pending_buy"));
s->SetAt(20, v5311);
if (static_cast<bool>(([&]() -> Value { auto v5312 = s->LocalAt(20); Value v5313; v5313 = Value{}; if (!static_cast<bool>(Binary("IsNot", v5312, v5313))) return Value(false); v5312 = v5313; return Value(true); }()))) {
auto v5314 = ([&]() -> Value { auto fn5315 = s->Global("max"); Arguments args5316; args5316.positional.reserve(2); args5316.Add(Value(int64_t{0}), false); args5316.Add(([&]() -> Value { auto v5317 = ([&]() -> Value { auto fn5318 = s->Global("int"); Arguments args5319; args5319.Add(([&]() -> Value { auto fn5320 = PrepareDictionaryGet(s->LocalAt(28)); Arguments args5321; args5321.positional.reserve(2); args5321.Add(Value("COW"), false); args5321.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn5320, std::move(args5321)); }()), false); return Call(c, fn5318, std::move(args5319)); }()); return Binary("Sub", v5317, Get(s->LocalAt(20), Value("before"))); }()), false); return Call(c, fn5315, std::move(args5316)); }());
s->SetAt(11, v5314);
auto v5322 = ([&]() -> Value { auto fn5323 = s->Global("min"); Arguments args5324; args5324.positional.reserve(2); args5324.Add(Get(s->LocalAt(20), Value("quantity")), false); args5324.Add(s->LocalAt(11), false); return Call(c, fn5323, std::move(args5324)); }());
s->SetAt(6, v5322);
auto v5325 = s->LocalAt(31);
auto v5326 = Value("confirmed");
auto v5327 = Get(v5325, v5326);
Put(v5325, v5326, Inplace("Add", v5327, s->LocalAt(6)));
auto v5328 = s->LocalAt(31);
auto v5329 = Value("reserved");
auto v5330 = Get(v5328, v5329);
Put(v5328, v5329, Inplace("Add", v5330, s->LocalAt(6)));
auto v5331 = s->LocalAt(31);
auto v5332 = Value("failed_purchase_units");
auto v5333 = Get(v5331, v5332);
Put(v5331, v5332, Inplace("Add", v5333, ([&]() -> Value { auto v5334 = Get(s->LocalAt(20), Value("quantity")); return Binary("Sub", v5334, s->LocalAt(6)); }())));
auto v5335 = Value{};
Put(s->LocalAt(31), Value("pending_buy"), v5335);
}
for (const auto& item5336 : Iterate(Get(s->LocalAt(31), Value("pending_places")))) {
s->SetAt(20, item5336);
auto v5337 = Get(s->LocalAt(20), Value("site"));
auto unpack5338 = Iterate(v5337);
ValidateUnpack(unpack5338, 2, false);
s->SetAt(40, unpack5338.at(0));
s->SetAt(41, unpack5338.at(1));
auto v5339 = Get(Get(Get(s->LocalAt(10), Value("tiles")), s->LocalAt(41)), s->LocalAt(40));
s->SetAt(35, v5339);
if (static_cast<bool>(([&]() -> Value { auto v5340 = ([&]() -> Value { auto fn5341 = s->Global("isinstance"); Arguments args5342; args5342.positional.reserve(2); args5342.Add(s->LocalAt(35), false); args5342.Add(s->Global("dict"), false); return Call(c, fn5341, std::move(args5342)); }()); if (!static_cast<bool>(v5340)) return v5340; v5340 = ([&]() -> Value { auto v5343 = ([&]() -> Value { auto fn5345 = PrepareDictionaryGet(s->LocalAt(35)); Arguments args5346; args5346.Add(Value("animal"), false); return CallDictionaryGet(c, fn5345, std::move(args5346)); }()); Value v5344; v5344 = Value("COW"); if (!static_cast<bool>(Binary("Eq", v5343, v5344))) return Value(false); v5343 = v5344; return Value(true); }()); if (!static_cast<bool>(v5340)) return v5340; v5340 = ([&]() -> Value { auto v5347 = ([&]() -> Value { auto fn5349 = PrepareDictionaryGet(s->LocalAt(35)); Arguments args5350; args5350.Add(Value("placed_day"), false); return CallDictionaryGet(c, fn5349, std::move(args5350)); }()); Value v5348; v5348 = Get(s->LocalAt(20), Value("day")); if (!static_cast<bool>(Binary("Eq", v5347, v5348))) return Value(false); v5347 = v5348; return Value(true); }()); return v5340; }()))) {
auto v5351 = Get(s->LocalAt(20), Value("day"));
Put(Get(s->LocalAt(31), Value("sites")), Tuple({s->LocalAt(40), s->LocalAt(41)}), v5351);
auto v5352 = s->LocalAt(31);
auto v5353 = Value("placed");
auto v5354 = Get(v5352, v5353);
Put(v5352, v5353, Inplace("Add", v5354, Value(int64_t{1})));
auto v5355 = Get(s->LocalAt(20), Value("actor"));
s->SetAt(1, v5355);
auto v5356 = ([&]() -> Value { auto fn5357 = s->Global("max"); Arguments args5358; args5358.positional.reserve(2); args5358.Add(Value(int64_t{0}), false); args5358.Add(([&]() -> Value { auto v5359 = ([&]() -> Value { auto fn5360 = PrepareDictionaryGet(Get(s->LocalAt(31), Value("carrying"))); Arguments args5361; args5361.positional.reserve(2); args5361.Add(s->LocalAt(1), false); args5361.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn5360, std::move(args5361)); }()); return Binary("Sub", v5359, Value(int64_t{1})); }()), false); return Call(c, fn5357, std::move(args5358)); }());
Put(Get(s->LocalAt(31), Value("carrying")), s->LocalAt(1), v5356);
}
else {
auto v5362 = s->LocalAt(31);
auto v5363 = Value("failed_placements");
auto v5364 = Get(v5362, v5363);
Put(v5362, v5363, Inplace("Add", v5364, Value(int64_t{1})));
}
}
auto v5365 = List({});
Put(s->LocalAt(31), Value("pending_places"), v5365);
auto v5366 = s->LocalAt(32);
Put(s->LocalAt(31), Value("last"), v5366);
auto v5367 = ([&]() -> Value { auto fn5368 = Attribute(s->Global("copy"), "deepcopy"); Arguments args5369; args5369.Add(s->LocalAt(0), false); return Call(c, fn5368, std::move(args5369)); }());
s->SetAt(25, v5367);
auto v5370 = ([&]() -> Value { Arguments args5371; args5371.Add(([&]() -> Value { auto v5372 = ([&]() -> Value { auto fn5373 = PrepareDictionaryGet(s->LocalAt(25)); Arguments args5374; args5374.Add(Value("farmer"), false); return CallDictionaryGet(c, fn5373, std::move(args5374)); }()); if (static_cast<bool>(v5372)) return v5372; v5372 = List({Value("PASS")}); return v5372; }()), false); args5371.Add(([&]() -> Value { auto v5375 = ([&]() -> Value { auto fn5376 = PrepareDictionaryGet(s->LocalAt(25)); Arguments args5377; args5377.Add(Value("hands"), false); return CallDictionaryGet(c, fn5376, std::move(args5377)); }()); if (static_cast<bool>(v5375)) return v5375; v5375 = List({}); return v5375; }()), true); return List(std::move(args5371.positional)); }());
s->SetAt(39, v5370);
auto v5378 = ([&]() -> Value { auto fn5379 = s->Global("set"); Arguments args5380; return Call(c, fn5379, std::move(args5380)); }());
s->SetAt(27, v5378);
auto v5381 = ([&]() -> Value { auto fn5382 = s->Global("int"); Arguments args5383; args5383.Add(([&]() -> Value { auto fn5384 = PrepareDictionaryGet(s->LocalAt(28)); Arguments args5385; args5385.positional.reserve(2); args5385.Add(Value("COW"), false); args5385.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn5384, std::move(args5385)); }()), false); return Call(c, fn5382, std::move(args5383)); }());
s->SetAt(8, v5381);
auto v5386 = ([&]() -> Value { auto fn5387 = s->Global("set"); Arguments args5388; return Call(c, fn5387, std::move(args5388)); }());
s->SetAt(18, v5386);
for (const auto& item5389 : Iterate(([&]() -> Value { auto fn5390 = s->Global("enumerate"); Arguments args5391; args5391.Add(Slice(s->LocalAt(39), Value{}, ([&]() -> Value { auto fn5392 = s->Global("len"); Arguments args5393; args5393.Add(s->LocalAt(21), false); return Call(c, fn5392, std::move(args5393)); }()), Value{}), false); return Call(c, fn5390, std::move(args5391)); }()))) {
auto unpack5394 = Iterate(item5389);
ValidateUnpack(unpack5394, 2, false);
s->SetAt(1, unpack5394.at(0));
s->SetAt(38, unpack5394.at(1));
auto v5395 = (static_cast<bool>(([&]() -> Value { auto v5396 = s->LocalAt(1); Value v5397; v5397 = ([&]() -> Value { auto fn5398 = s->Global("len"); Arguments args5399; args5399.Add(s->LocalAt(12), false); return Call(c, fn5398, std::move(args5399)); }()); if (!static_cast<bool>(Binary("Lt", v5396, v5397))) return Value(false); v5396 = v5397; return Value(true); }())) ? Get(s->LocalAt(12), s->LocalAt(1)) : ([&]() -> Value { auto dict5400 = Dict(); return dict5400; }()));
s->SetAt(13, v5395);
auto v5401 = Get(s->LocalAt(21), s->LocalAt(1));
auto unpack5402 = Iterate(v5401);
ValidateUnpack(unpack5402, 2, false);
s->SetAt(40, unpack5402.at(0));
s->SetAt(41, unpack5402.at(1));
auto v5403 = Get(Get(Get(s->LocalAt(10), Value("tiles")), s->LocalAt(41)), s->LocalAt(40));
s->SetAt(35, v5403);
auto v5404 = Tuple({s->LocalAt(40), s->LocalAt(41)});
s->SetAt(30, v5404);
if (static_cast<bool>(([&]() -> Value { auto v5405 = ([&]() -> Value { auto v5406 = s->LocalAt(38); Value v5407; v5407 = List({Value("HARVEST")}); if (!static_cast<bool>(Binary("Eq", v5406, v5407))) return Value(false); v5406 = v5407; return Value(true); }()); if (!static_cast<bool>(v5405)) return v5405; v5405 = ([&]() -> Value { auto v5408 = s->LocalAt(30); Value v5409; v5409 = Get(s->LocalAt(31), Value("sites")); if (!static_cast<bool>(Binary("In", v5408, v5409))) return Value(false); v5408 = v5409; return Value(true); }()); if (!static_cast<bool>(v5405)) return v5405; v5405 = ([&]() -> Value { auto v5410 = s->LocalAt(30); Value v5411; v5411 = s->LocalAt(27); if (!static_cast<bool>(Binary("NotIn", v5410, v5411))) return Value(false); v5410 = v5411; return Value(true); }()); if (!static_cast<bool>(v5405)) return v5405; v5405 = ([&]() -> Value { auto fn5412 = s->Global("isinstance"); Arguments args5413; args5413.positional.reserve(2); args5413.Add(s->LocalAt(35), false); args5413.Add(s->Global("dict"), false); return Call(c, fn5412, std::move(args5413)); }()); if (!static_cast<bool>(v5405)) return v5405; v5405 = ([&]() -> Value { auto v5414 = ([&]() -> Value { auto fn5416 = PrepareDictionaryGet(s->LocalAt(35)); Arguments args5417; args5417.Add(Value("animal"), false); return CallDictionaryGet(c, fn5416, std::move(args5417)); }()); Value v5415; v5415 = Value("COW"); if (!static_cast<bool>(Binary("Eq", v5414, v5415))) return Value(false); v5414 = v5415; return Value(true); }()); if (!static_cast<bool>(v5405)) return v5405; v5405 = ([&]() -> Value { auto v5418 = ([&]() -> Value { auto fn5420 = PrepareDictionaryGet(s->LocalAt(35)); Arguments args5421; args5421.Add(Value("placed_day"), false); return CallDictionaryGet(c, fn5420, std::move(args5421)); }()); Value v5419; v5419 = Get(Get(s->LocalAt(31), Value("sites")), s->LocalAt(30)); if (!static_cast<bool>(Binary("Eq", v5418, v5419))) return Value(false); v5418 = v5419; return Value(true); }()); return v5405; }()))) {
auto v5422 = ([&]() -> Value { auto fn5423 = s->Global("max"); Arguments args5424; args5424.positional.reserve(2); args5424.Add(Value(int64_t{0}), false); args5424.Add(([&]() -> Value { auto fn5425 = s->Global("int"); Arguments args5426; args5426.Add(([&]() -> Value { auto fn5427 = PrepareDictionaryGet(s->LocalAt(35)); Arguments args5428; args5428.positional.reserve(2); args5428.Add(Value("yield_units"), false); args5428.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn5427, std::move(args5428)); }()), false); return Call(c, fn5425, std::move(args5426)); }()), false); return Call(c, fn5423, std::move(args5424)); }());
s->SetAt(37, v5422);
auto v5429 = s->LocalAt(31);
auto v5430 = Value("milk_credit");
auto v5431 = Get(v5429, v5430);
Put(v5429, v5430, Inplace("Add", v5431, s->LocalAt(37)));
auto v5432 = s->LocalAt(31);
auto v5433 = Value("extra_milk_harvested");
auto v5434 = Get(v5432, v5433);
Put(v5432, v5433, Inplace("Add", v5434, s->LocalAt(37)));
(void)([&]() -> Value { auto fn5435 = Attribute(s->LocalAt(27), "add"); Arguments args5436; args5436.Add(s->LocalAt(30), false); return Call(c, fn5435, std::move(args5436)); }());
}
if (static_cast<bool>(([&]() -> Value { auto v5437 = ([&]() -> Value { auto v5438 = ([&]() -> Value { auto fn5440 = s->Global("len"); Arguments args5441; args5441.Add(s->LocalAt(38), false); return Call(c, fn5440, std::move(args5441)); }()); Value v5439; v5439 = Value(int64_t{2}); if (!static_cast<bool>(Binary("GtE", v5438, v5439))) return Value(false); v5438 = v5439; return Value(true); }()); if (!static_cast<bool>(v5437)) return v5437; v5437 = ([&]() -> Value { auto v5442 = Slice(s->LocalAt(38), Value{}, Value(int64_t{2}), Value{}); Value v5443; v5443 = List({Value("PICKUP"), Value("SHEEP")}); if (!static_cast<bool>(Binary("Eq", v5442, v5443))) return Value(false); v5442 = v5443; return Value(true); }()); return v5437; }()))) {
auto v5444 = ([&]() -> Value { auto fn5445 = s->Global("max"); Arguments args5446; args5446.positional.reserve(2); args5446.Add(Value(int64_t{0}), false); args5446.Add((static_cast<bool>(([&]() -> Value { auto v5447 = ([&]() -> Value { auto fn5449 = s->Global("len"); Arguments args5450; args5450.Add(s->LocalAt(38), false); return Call(c, fn5449, std::move(args5450)); }()); Value v5448; v5448 = Value(int64_t{2}); if (!static_cast<bool>(Binary("Gt", v5447, v5448))) return Value(false); v5447 = v5448; return Value(true); }())) ? ([&]() -> Value { auto fn5451 = s->Global("int"); Arguments args5452; args5452.Add(Get(s->LocalAt(38), Value(int64_t{2})), false); return Call(c, fn5451, std::move(args5452)); }()) : Value(int64_t{1})), false); return Call(c, fn5445, std::move(args5446)); }());
s->SetAt(24, v5444);
auto v5453 = ([&]() -> Value { auto v5454 = ([&]() -> Value { auto fn5455 = s->Global("len"); Arguments args5456; args5456.Add(Get(s->LocalAt(10), Value("tiles")), false); return Call(c, fn5455, std::move(args5456)); }()); return Binary("FloorDiv", v5454, Value(int64_t{2})); }());
s->SetAt(5, v5453);
if (static_cast<bool>(([&]() -> Value { auto v5457 = s->LocalAt(24); if (!static_cast<bool>(v5457)) return v5457; v5457 = ([&]() -> Value { auto v5458 = Get(s->LocalAt(31), Value("reserved")); Value v5459; v5459 = s->LocalAt(24); if (!static_cast<bool>(Binary("GtE", v5458, v5459))) return Value(false); v5458 = v5459; return Value(true); }()); if (!static_cast<bool>(v5457)) return v5457; v5457 = ([&]() -> Value { auto v5460 = s->LocalAt(8); Value v5461; v5461 = s->LocalAt(24); if (!static_cast<bool>(Binary("GtE", v5460, v5461))) return Value(false); v5460 = v5461; return Value(true); }()); if (!static_cast<bool>(v5457)) return v5457; v5457 = ([&]() -> Value { auto v5462 = s->LocalAt(40); Value v5463; v5463 = Tuple({([&]() -> Value { auto v5464 = s->LocalAt(5); return Binary("Sub", v5464, Value(int64_t{1})); }()), s->LocalAt(5)}); if (!static_cast<bool>(Binary("In", v5462, v5463))) return Value(false); v5462 = v5463; return Value(true); }()); if (!static_cast<bool>(v5457)) return v5457; v5457 = ([&]() -> Value { auto v5465 = s->LocalAt(41); Value v5466; v5466 = Tuple({([&]() -> Value { auto v5467 = s->LocalAt(5); return Binary("Sub", v5467, Value(int64_t{1})); }()), s->LocalAt(5)}); if (!static_cast<bool>(Binary("In", v5465, v5466))) return Value(false); v5465 = v5466; return Value(true); }()); if (!static_cast<bool>(v5457)) return v5457; v5457 = Unary("Not", ([&]() -> Value { auto comp5468 = std::make_shared<Scope>(); comp5468->globals = s->globals; comp5468->parent = s; static constexpr const char* comp5468_names[] = {"a"}; comp5468->PrepareSlots(comp5468_names); auto result5469 = List(); for (const auto& item5470 : Iterate(Tuple({Value("COW"), Value("SHEEP"), Value("GOOSE")}))) { comp5468->SetAt(0, item5470); if (static_cast<bool>(([&]() -> Value { auto fn5471 = PrepareDictionaryGet(comp5468->Captured("inventory")); Arguments args5472; args5472.positional.reserve(2); args5472.Add(comp5468->LocalAt(0), false); args5472.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn5471, std::move(args5472)); }()))) return Value(true); } return Value(false); }())); return v5457; }()))) {
auto v5473 = Value("COW");
Put(s->LocalAt(38), Value(int64_t{1}), v5473);
auto v5474 = s->LocalAt(31);
auto v5475 = Value("reserved");
auto v5476 = Get(v5474, v5475);
Put(v5474, v5475, Inplace("Sub", v5476, s->LocalAt(24)));
auto v5477 = s->LocalAt(8);
s->SetAt(8, Inplace("Sub", v5477, s->LocalAt(24)));
auto v5478 = ([&]() -> Value { auto v5479 = ([&]() -> Value { auto fn5480 = PrepareDictionaryGet(Get(s->LocalAt(31), Value("carrying"))); Arguments args5481; args5481.positional.reserve(2); args5481.Add(s->LocalAt(1), false); args5481.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn5480, std::move(args5481)); }()); return Binary("Add", v5479, s->LocalAt(24)); }());
Put(Get(s->LocalAt(31), Value("carrying")), s->LocalAt(1), v5478);
auto v5482 = s->LocalAt(31);
auto v5483 = Value("picked");
auto v5484 = Get(v5482, v5483);
Put(v5482, v5483, Inplace("Add", v5484, s->LocalAt(24)));
}
}
if (static_cast<bool>(([&]() -> Value { auto v5485 = ([&]() -> Value { auto v5486 = ([&]() -> Value { auto fn5488 = s->Global("len"); Arguments args5489; args5489.Add(s->LocalAt(38), false); return Call(c, fn5488, std::move(args5489)); }()); Value v5487; v5487 = Value(int64_t{2}); if (!static_cast<bool>(Binary("GtE", v5486, v5487))) return Value(false); v5486 = v5487; return Value(true); }()); if (!static_cast<bool>(v5485)) return v5485; v5485 = ([&]() -> Value { auto v5490 = Slice(s->LocalAt(38), Value{}, Value(int64_t{2}), Value{}); Value v5491; v5491 = List({Value("PLACE"), Value("SHEEP")}); if (!static_cast<bool>(Binary("Eq", v5490, v5491))) return Value(false); v5490 = v5491; return Value(true); }()); if (!static_cast<bool>(v5485)) return v5485; v5485 = ([&]() -> Value { auto v5492 = ([&]() -> Value { auto fn5494 = PrepareDictionaryGet(Get(s->LocalAt(31), Value("carrying"))); Arguments args5495; args5495.positional.reserve(2); args5495.Add(s->LocalAt(1), false); args5495.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn5494, std::move(args5495)); }()); Value v5493; v5493 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v5492, v5493))) return Value(false); v5492 = v5493; return Value(true); }()); if (!static_cast<bool>(v5485)) return v5485; v5485 = ([&]() -> Value { auto v5496 = ([&]() -> Value { auto fn5498 = PrepareDictionaryGet(s->LocalAt(13)); Arguments args5499; args5499.positional.reserve(2); args5499.Add(Value("COW"), false); args5499.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn5498, std::move(args5499)); }()); Value v5497; v5497 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v5496, v5497))) return Value(false); v5496 = v5497; return Value(true); }()); if (!static_cast<bool>(v5485)) return v5485; v5485 = ([&]() -> Value { auto fn5500 = s->Global("isinstance"); Arguments args5501; args5501.positional.reserve(2); args5501.Add(s->LocalAt(35), false); args5501.Add(s->Global("dict"), false); return Call(c, fn5500, std::move(args5501)); }()); if (!static_cast<bool>(v5485)) return v5485; v5485 = ([&]() -> Value { auto v5502 = ([&]() -> Value { auto fn5504 = PrepareDictionaryGet(s->LocalAt(35)); Arguments args5505; args5505.Add(Value("kind"), false); return CallDictionaryGet(c, fn5504, std::move(args5505)); }()); Value v5503; v5503 = Value("PASTURE"); if (!static_cast<bool>(Binary("Eq", v5502, v5503))) return Value(false); v5502 = v5503; return Value(true); }()); if (!static_cast<bool>(v5485)) return v5485; v5485 = ([&]() -> Value { auto v5506 = Value("animal"); Value v5507; v5507 = s->LocalAt(35); if (!static_cast<bool>(Binary("NotIn", v5506, v5507))) return Value(false); v5506 = v5507; return Value(true); }()); if (!static_cast<bool>(v5485)) return v5485; v5485 = ([&]() -> Value { auto v5508 = s->LocalAt(30); Value v5509; v5509 = s->LocalAt(18); if (!static_cast<bool>(Binary("NotIn", v5508, v5509))) return Value(false); v5508 = v5509; return Value(true); }()); return v5485; }()))) {
auto v5510 = Value("COW");
Put(s->LocalAt(38), Value(int64_t{1}), v5510);
(void)([&]() -> Value { auto fn5511 = Attribute(Get(s->LocalAt(31), Value("pending_places")), "append"); Arguments args5512; args5512.Add(([&]() -> Value { auto dict5513 = Dict(); auto key5514 = Value("actor"); Put(dict5513, key5514, s->LocalAt(1)); auto key5515 = Value("site"); Put(dict5513, key5515, s->LocalAt(30)); auto key5516 = Value("day"); Put(dict5513, key5516, ([&]() -> Value { auto v5517 = s->LocalAt(32); return Binary("FloorDiv", v5517, Value(int64_t{24})); }())); return dict5513; }()), false); return Call(c, fn5511, std::move(args5512)); }());
}
if (static_cast<bool>(([&]() -> Value { auto v5518 = ([&]() -> Value { auto v5519 = ([&]() -> Value { auto fn5521 = s->Global("len"); Arguments args5522; args5522.Add(s->LocalAt(38), false); return Call(c, fn5521, std::move(args5522)); }()); Value v5520; v5520 = Value(int64_t{2}); if (!static_cast<bool>(Binary("GtE", v5519, v5520))) return Value(false); v5519 = v5520; return Value(true); }()); if (!static_cast<bool>(v5518)) return v5518; v5518 = ([&]() -> Value { auto v5523 = Get(s->LocalAt(38), Value(int64_t{0})); Value v5524; v5524 = Value("PLACE"); if (!static_cast<bool>(Binary("Eq", v5523, v5524))) return Value(false); v5523 = v5524; return Value(true); }()); if (!static_cast<bool>(v5518)) return v5518; v5518 = ([&]() -> Value { auto v5525 = Get(s->LocalAt(38), Value(int64_t{1})); Value v5526; v5526 = Tuple({Value("COW"), Value("SHEEP"), Value("GOOSE")}); if (!static_cast<bool>(Binary("In", v5525, v5526))) return Value(false); v5525 = v5526; return Value(true); }()); if (!static_cast<bool>(v5518)) return v5518; v5518 = ([&]() -> Value { auto v5527 = ([&]() -> Value { auto fn5529 = PrepareDictionaryGet(s->LocalAt(13)); Arguments args5530; args5530.positional.reserve(2); args5530.Add(Get(s->LocalAt(38), Value(int64_t{1})), false); args5530.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn5529, std::move(args5530)); }()); Value v5528; v5528 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v5527, v5528))) return Value(false); v5527 = v5528; return Value(true); }()); return v5518; }()))) {
(void)([&]() -> Value { auto fn5531 = Attribute(s->LocalAt(18), "add"); Arguments args5532; args5532.Add(s->LocalAt(30), false); return Call(c, fn5531, std::move(args5532)); }());
}
}
auto v5533 = Tuple({Get(s->LocalAt(39), Value(int64_t{0})), Slice(s->LocalAt(39), Value(int64_t{1}), Value{}, Value{})});
auto unpack5534 = Iterate(v5533);
ValidateUnpack(unpack5534, 2, false);
Put(s->LocalAt(25), Value("farmer"), unpack5534.at(0));
Put(s->LocalAt(25), Value("hands"), unpack5534.at(1));
auto v5535 = ([&]() -> Value { auto fn5536 = PrepareDictionaryGet(s->LocalAt(25)); Arguments args5537; args5537.positional.reserve(2); args5537.Add(Value("market"), false); args5537.Add(List({}), false); return CallDictionaryGet(c, fn5536, std::move(args5537)); }());
s->SetAt(15, v5535);
auto v5538 = ([&]() -> Value { auto comp5539 = std::make_shared<Scope>(); comp5539->globals = s->globals; comp5539->parent = s; static constexpr const char* comp5539_names[] = {"o"}; comp5539->PrepareSlots(comp5539_names); auto result5540 = List(); for (const auto& item5541 : Iterate(s->LocalAt(15))) { comp5539->SetAt(0, item5541); if (!static_cast<bool>(([&]() -> Value { auto v5542 = ([&]() -> Value { auto v5543 = ([&]() -> Value { auto fn5545 = comp5539->Global("len"); Arguments args5546; args5546.Add(comp5539->LocalAt(0), false); return Call(c, fn5545, std::move(args5546)); }()); Value v5544; v5544 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v5543, v5544))) return Value(false); v5543 = v5544; return Value(true); }()); if (!static_cast<bool>(v5542)) return v5542; v5542 = ([&]() -> Value { auto v5547 = Get(comp5539->LocalAt(0), Value(int64_t{0})); Value v5548; v5548 = Value("BUY_ANIMAL"); if (!static_cast<bool>(Binary("Eq", v5547, v5548))) return Value(false); v5547 = v5548; return Value(true); }()); return v5542; }()))) continue; result5540.node()->sequence.push_back(comp5539->LocalAt(0)); } return result5540; }());
s->SetAt(2, v5538);
auto v5549 = Get(Get(s->LocalAt(17), Value("town")), Value("unlocked_shops"));
s->SetAt(29, v5549);
auto v5550 = Get(Get(s->LocalAt(17), Value("market")), Value("prices"));
s->SetAt(22, v5550);
auto v5551 = ([&]() -> Value { auto dict5552 = Dict(); auto key5553 = Value("COW"); Put(dict5552, key5553, Value(int64_t{0})); auto key5554 = Value("SHEEP"); Put(dict5552, key5554, Value(int64_t{0})); return dict5552; }());
s->SetAt(7, v5551);
for (const auto& item5555 : Iterate(Get(s->LocalAt(10), Value("tiles")))) {
s->SetAt(14, item5555);
for (const auto& item5556 : Iterate(s->LocalAt(14))) {
s->SetAt(35, item5556);
if (static_cast<bool>(([&]() -> Value { auto v5557 = ([&]() -> Value { auto fn5558 = s->Global("isinstance"); Arguments args5559; args5559.positional.reserve(2); args5559.Add(s->LocalAt(35), false); args5559.Add(s->Global("dict"), false); return Call(c, fn5558, std::move(args5559)); }()); if (!static_cast<bool>(v5557)) return v5557; v5557 = ([&]() -> Value { auto v5560 = ([&]() -> Value { auto fn5562 = PrepareDictionaryGet(s->LocalAt(35)); Arguments args5563; args5563.Add(Value("animal"), false); return CallDictionaryGet(c, fn5562, std::move(args5563)); }()); Value v5561; v5561 = s->LocalAt(7); if (!static_cast<bool>(Binary("In", v5560, v5561))) return Value(false); v5560 = v5561; return Value(true); }()); return v5557; }()))) {
auto v5564 = s->LocalAt(7);
auto v5565 = Get(s->LocalAt(35), Value("animal"));
auto v5566 = Get(v5564, v5565);
Put(v5564, v5565, Inplace("Add", v5566, Value(int64_t{1})));
}
}
}
auto v5567 = ([&]() -> Value { auto fn5568 = s->Global("sum"); Arguments args5569; args5569.Add(([&]() -> Value { auto comp5570 = std::make_shared<Scope>(); comp5570->globals = s->globals; comp5570->parent = s; static constexpr const char* comp5570_names[] = {"a", "inv"}; comp5570->PrepareSlots(comp5570_names); auto result5571 = List(); for (const auto& item5572 : Iterate(s->LocalAt(12))) { comp5570->SetAt(1, item5572); for (const auto& item5573 : Iterate(Tuple({Value("COW"), Value("SHEEP"), Value("GOOSE")}))) { comp5570->SetAt(0, item5573); result5571.node()->sequence.push_back(([&]() -> Value { auto fn5574 = comp5570->Global("int"); Arguments args5575; args5575.Add(([&]() -> Value { auto fn5576 = PrepareDictionaryGet(comp5570->LocalAt(1)); Arguments args5577; args5577.positional.reserve(2); args5577.Add(comp5570->LocalAt(0), false); args5577.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn5576, std::move(args5577)); }()), false); return Call(c, fn5574, std::move(args5575)); }())); } } return result5571; }()), false); return Call(c, fn5568, std::move(args5569)); }());
s->SetAt(4, v5567);
auto v5578 = ([&]() -> Value { auto fn5579 = s->Global("sum"); Arguments args5580; args5580.Add(([&]() -> Value { auto comp5581 = std::make_shared<Scope>(); comp5581->globals = s->globals; comp5581->parent = s; static constexpr const char* comp5581_names[] = {"a"}; comp5581->PrepareSlots(comp5581_names); auto result5582 = List(); for (const auto& item5583 : Iterate(Tuple({Value("COW"), Value("SHEEP"), Value("GOOSE")}))) { comp5581->SetAt(0, item5583); result5582.node()->sequence.push_back(([&]() -> Value { auto fn5584 = comp5581->Global("int"); Arguments args5585; args5585.Add(([&]() -> Value { auto fn5586 = PrepareDictionaryGet(comp5581->Captured("shed")); Arguments args5587; args5587.positional.reserve(2); args5587.Add(comp5581->LocalAt(0), false); args5587.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn5586, std::move(args5587)); }()), false); return Call(c, fn5584, std::move(args5585)); }())); } return result5582; }()), false); return Call(c, fn5579, std::move(args5580)); }());
s->SetAt(34, v5578);
auto v5588 = ([&]() -> Value { auto fn5589 = s->Global("sum"); Arguments args5590; args5590.Add(([&]() -> Value { auto comp5591 = std::make_shared<Scope>(); comp5591->globals = s->globals; comp5591->parent = s; static constexpr const char* comp5591_names[] = {"shop"}; comp5591->PrepareSlots(comp5591_names); auto result5592 = List(); for (const auto& item5593 : Iterate(s->LocalAt(29))) { comp5591->SetAt(0, item5593); result5592.node()->sequence.push_back(([&]() -> Value { auto v5594 = comp5591->LocalAt(0); Value v5595; v5595 = Tuple({Value("PIZZA_SHOP"), Value("ICE_CREAM_SHOP"), Value("SMOOTHIE_SHOP")}); if (!static_cast<bool>(Binary("In", v5594, v5595))) return Value(false); v5594 = v5595; return Value(true); }())); } return result5592; }()), false); return Call(c, fn5589, std::move(args5590)); }());
s->SetAt(16, v5588);
if (static_cast<bool>(([&]() -> Value { auto v5596 = ([&]() -> Value { auto v5597 = Value(int64_t{216}); Value v5598; v5598 = s->LocalAt(32); if (!static_cast<bool>(Binary("LtE", v5597, v5598))) return Value(false); v5597 = v5598; v5598 = Value(int64_t{227}); if (!static_cast<bool>(Binary("LtE", v5597, v5598))) return Value(false); v5597 = v5598; return Value(true); }()); if (!static_cast<bool>(v5596)) return v5596; v5596 = ([&]() -> Value { auto v5599 = ([&]() -> Value { auto fn5601 = s->Global("len"); Arguments args5602; args5602.Add(s->LocalAt(29), false); return Call(c, fn5601, std::move(args5602)); }()); Value v5600; v5600 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v5599, v5600))) return Value(false); v5599 = v5600; return Value(true); }()); if (!static_cast<bool>(v5596)) return v5596; v5596 = ([&]() -> Value { auto v5603 = Get(s->LocalAt(31), Value("confirmed")); Value v5604; v5604 = s->LocalAt(3); if (!static_cast<bool>(Binary("Lt", v5603, v5604))) return Value(false); v5603 = v5604; return Value(true); }()); if (!static_cast<bool>(v5596)) return v5596; v5596 = Unary("Not", Get(s->LocalAt(31), Value("reserved"))); if (!static_cast<bool>(v5596)) return v5596; v5596 = Unary("Not", ([&]() -> Value { auto fn5605 = s->Global("any"); Arguments args5606; args5606.Add(([&]() -> Value { auto fn5607 = Attribute(Get(s->LocalAt(31), Value("carrying")), "values"); Arguments args5608; return Call(c, fn5607, std::move(args5608)); }()), false); return Call(c, fn5605, std::move(args5606)); }())); if (!static_cast<bool>(v5596)) return v5596; v5596 = Unary("Not", Get(s->LocalAt(31), Value("pending_places"))); if (!static_cast<bool>(v5596)) return v5596; v5596 = Unary("Not", s->LocalAt(4)); if (!static_cast<bool>(v5596)) return v5596; v5596 = Unary("Not", s->LocalAt(34)); if (!static_cast<bool>(v5596)) return v5596; v5596 = ([&]() -> Value { auto v5609 = ([&]() -> Value { auto fn5611 = s->Global("len"); Arguments args5612; args5612.Add(s->LocalAt(2), false); return Call(c, fn5611, std::move(args5612)); }()); Value v5610; v5610 = Value(int64_t{1}); if (!static_cast<bool>(Binary("Eq", v5609, v5610))) return Value(false); v5609 = v5610; return Value(true); }()); if (!static_cast<bool>(v5596)) return v5596; v5596 = ([&]() -> Value { auto v5613 = Get(Get(s->LocalAt(2), Value(int64_t{0})), Value(int64_t{1})); Value v5614; v5614 = Value("SHEEP"); if (!static_cast<bool>(Binary("Eq", v5613, v5614))) return Value(false); v5613 = v5614; return Value(true); }()); if (!static_cast<bool>(v5596)) return v5596; v5596 = ([&]() -> Value { auto v5615 = s->LocalAt(16); Value v5616; v5616 = Value(int64_t{2}); if (!static_cast<bool>(Binary("GtE", v5615, v5616))) return Value(false); v5615 = v5616; return Value(true); }()); if (!static_cast<bool>(v5596)) return v5596; v5596 = ([&]() -> Value { auto v5617 = Value("YARN_STORE"); Value v5618; v5618 = s->LocalAt(29); if (!static_cast<bool>(Binary("NotIn", v5617, v5618))) return Value(false); v5617 = v5618; return Value(true); }()); if (!static_cast<bool>(v5596)) return v5596; v5596 = ([&]() -> Value { auto v5619 = ([&]() -> Value { auto fn5621 = s->Global("int"); Arguments args5622; args5622.Add(([&]() -> Value { auto fn5623 = PrepareDictionaryGet(s->LocalAt(22)); Arguments args5624; args5624.positional.reserve(2); args5624.Add(Value("MILK"), false); args5624.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn5623, std::move(args5624)); }()), false); return Call(c, fn5621, std::move(args5622)); }()); Value v5620; v5620 = ([&]() -> Value { auto fn5625 = s->Global("int"); Arguments args5626; args5626.Add(([&]() -> Value { auto fn5627 = PrepareDictionaryGet(s->LocalAt(22)); Arguments args5628; args5628.positional.reserve(2); args5628.Add(Value("WOOL"), false); args5628.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn5627, std::move(args5628)); }()), false); return Call(c, fn5625, std::move(args5626)); }()); if (!static_cast<bool>(Binary("GtE", v5619, v5620))) return Value(false); v5619 = v5620; return Value(true); }()); if (!static_cast<bool>(v5596)) return v5596; v5596 = ([&]() -> Value { auto v5629 = Get(s->LocalAt(7), Value("COW")); Value v5630; v5630 = Value(int64_t{4}); if (!static_cast<bool>(Binary("GtE", v5629, v5630))) return Value(false); v5629 = v5630; return Value(true); }()); if (!static_cast<bool>(v5596)) return v5596; v5596 = ([&]() -> Value { auto v5631 = Get(s->LocalAt(7), Value("SHEEP")); Value v5632; v5632 = Value(int64_t{2}); if (!static_cast<bool>(Binary("GtE", v5631, v5632))) return Value(false); v5631 = v5632; return Value(true); }()); return v5596; }()))) {
auto v5633 = Get(s->LocalAt(2), Value(int64_t{0}));
s->SetAt(19, v5633);
auto v5634 = ([&]() -> Value { auto fn5635 = s->Global("int"); Arguments args5636; args5636.Add(Get(s->LocalAt(19), Value(int64_t{2})), false); return Call(c, fn5635, std::move(args5636)); }());
s->SetAt(24, v5634);
if (static_cast<bool>(([&]() -> Value { auto v5637 = ([&]() -> Value { auto v5638 = Value(int64_t{1}); Value v5639; v5639 = s->LocalAt(24); if (!static_cast<bool>(Binary("LtE", v5638, v5639))) return Value(false); v5638 = v5639; v5639 = Value(int64_t{2}); if (!static_cast<bool>(Binary("LtE", v5638, v5639))) return Value(false); v5638 = v5639; return Value(true); }()); if (!static_cast<bool>(v5637)) return v5637; v5637 = ([&]() -> Value { auto v5640 = s->LocalAt(24); Value v5641; v5641 = ([&]() -> Value { auto v5642 = s->LocalAt(3); return Binary("Sub", v5642, Get(s->LocalAt(31), Value("confirmed"))); }()); if (!static_cast<bool>(Binary("LtE", v5640, v5641))) return Value(false); v5640 = v5641; return Value(true); }()); return v5637; }()))) {
auto v5643 = Value("COW");
Put(s->LocalAt(19), Value(int64_t{1}), v5643);
auto v5644 = s->LocalAt(31);
auto v5645 = Value("requested");
auto v5646 = Get(v5644, v5645);
Put(v5644, v5645, Inplace("Add", v5646, s->LocalAt(24)));
auto v5647 = ([&]() -> Value { auto dict5648 = Dict(); auto key5649 = Value("before"); Put(dict5648, key5649, ([&]() -> Value { auto fn5650 = s->Global("int"); Arguments args5651; args5651.Add(([&]() -> Value { auto fn5652 = PrepareDictionaryGet(s->LocalAt(28)); Arguments args5653; args5653.positional.reserve(2); args5653.Add(Value("COW"), false); args5653.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn5652, std::move(args5653)); }()), false); return Call(c, fn5650, std::move(args5651)); }())); auto key5654 = Value("quantity"); Put(dict5648, key5654, s->LocalAt(24)); return dict5648; }());
Put(s->LocalAt(31), Value("pending_buy"), v5647);
}
}
if (static_cast<bool>(([&]() -> Value { auto v5655 = Get(s->LocalAt(31), Value("milk_credit")); Value v5656; v5656 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v5655, v5656))) return Value(false); v5655 = v5656; return Value(true); }()))) {
auto v5657 = ([&]() -> Value { auto fn5658 = s->Global("projected_shed"); Arguments args5659; args5659.positional.reserve(2); args5659.Add(s->LocalAt(25), false); args5659.Add(([&]() -> Value { auto fn5660 = s->Global("FarmView"); Arguments args5661; args5661.Add(s->LocalAt(17), false); return Call(c, fn5660, std::move(args5661)); }()), false); return Call(c, fn5658, std::move(args5659)); }());
s->SetAt(33, v5657);
auto v5662 = ([&]() -> Value { auto fn5663 = s->Global("sum"); Arguments args5664; args5664.Add(([&]() -> Value { auto comp5665 = std::make_shared<Scope>(); comp5665->globals = s->globals; comp5665->parent = s; static constexpr const char* comp5665_names[] = {"o"}; comp5665->PrepareSlots(comp5665_names); auto result5666 = List(); for (const auto& item5667 : Iterate(s->LocalAt(15))) { comp5665->SetAt(0, item5667); if (!static_cast<bool>(([&]() -> Value { auto v5668 = ([&]() -> Value { auto v5669 = ([&]() -> Value { auto fn5671 = comp5665->Global("len"); Arguments args5672; args5672.Add(comp5665->LocalAt(0), false); return Call(c, fn5671, std::move(args5672)); }()); Value v5670; v5670 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v5669, v5670))) return Value(false); v5669 = v5670; return Value(true); }()); if (!static_cast<bool>(v5668)) return v5668; v5668 = ([&]() -> Value { auto v5673 = Slice(comp5665->LocalAt(0), Value{}, Value(int64_t{2}), Value{}); Value v5674; v5674 = List({Value("SELL"), Value("MILK")}); if (!static_cast<bool>(Binary("Eq", v5673, v5674))) return Value(false); v5673 = v5674; return Value(true); }()); return v5668; }()))) continue; result5666.node()->sequence.push_back(([&]() -> Value { auto fn5675 = comp5665->Global("max"); Arguments args5676; args5676.positional.reserve(2); args5676.Add(Value(int64_t{0}), false); args5676.Add(([&]() -> Value { auto fn5677 = comp5665->Global("int"); Arguments args5678; args5678.Add(Get(comp5665->LocalAt(0), Value(int64_t{2})), false); return Call(c, fn5677, std::move(args5678)); }()), false); return Call(c, fn5675, std::move(args5676)); }())); } return result5666; }()), false); return Call(c, fn5663, std::move(args5664)); }());
s->SetAt(36, v5662);
auto v5679 = ([&]() -> Value { auto fn5680 = s->Global("min"); Arguments args5681; args5681.positional.reserve(2); args5681.Add(Get(s->LocalAt(31), Value("milk_credit")), false); args5681.Add(([&]() -> Value { auto fn5682 = s->Global("max"); Arguments args5683; args5683.positional.reserve(2); args5683.Add(Value(int64_t{0}), false); args5683.Add(([&]() -> Value { auto v5684 = ([&]() -> Value { auto fn5685 = s->Global("int"); Arguments args5686; args5686.Add(([&]() -> Value { auto fn5687 = PrepareDictionaryGet(s->LocalAt(33)); Arguments args5688; args5688.positional.reserve(2); args5688.Add(Value("MILK"), false); args5688.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn5687, std::move(args5688)); }()), false); return Call(c, fn5685, std::move(args5686)); }()); return Binary("Sub", v5684, s->LocalAt(36)); }()), false); return Call(c, fn5682, std::move(args5683)); }()), false); return Call(c, fn5680, std::move(args5681)); }());
s->SetAt(9, v5679);
if (static_cast<bool>(s->LocalAt(9))) {
for (const auto& item5689 : Iterate(s->LocalAt(15))) {
s->SetAt(19, item5689);
if (static_cast<bool>(([&]() -> Value { auto v5690 = ([&]() -> Value { auto v5691 = ([&]() -> Value { auto fn5693 = s->Global("len"); Arguments args5694; args5694.Add(s->LocalAt(19), false); return Call(c, fn5693, std::move(args5694)); }()); Value v5692; v5692 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v5691, v5692))) return Value(false); v5691 = v5692; return Value(true); }()); if (!static_cast<bool>(v5690)) return v5690; v5690 = ([&]() -> Value { auto v5695 = Slice(s->LocalAt(19), Value{}, Value(int64_t{2}), Value{}); Value v5696; v5696 = List({Value("SELL"), Value("MILK")}); if (!static_cast<bool>(Binary("Eq", v5695, v5696))) return Value(false); v5695 = v5696; return Value(true); }()); if (!static_cast<bool>(v5690)) return v5690; v5690 = ([&]() -> Value { auto v5697 = ([&]() -> Value { auto fn5699 = s->Global("int"); Arguments args5700; args5700.Add(Get(s->LocalAt(19), Value(int64_t{2})), false); return Call(c, fn5699, std::move(args5700)); }()); Value v5698; v5698 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v5697, v5698))) return Value(false); v5697 = v5698; return Value(true); }()); return v5690; }()))) {
auto v5701 = ([&]() -> Value { auto v5702 = ([&]() -> Value { auto fn5703 = s->Global("int"); Arguments args5704; args5704.Add(Get(s->LocalAt(19), Value(int64_t{2})), false); return Call(c, fn5703, std::move(args5704)); }()); return Binary("Add", v5702, s->LocalAt(9)); }());
Put(s->LocalAt(19), Value(int64_t{2}), v5701);
auto v5705 = s->LocalAt(31);
auto v5706 = Value("milk_credit");
auto v5707 = Get(v5705, v5706);
Put(v5705, v5706, Inplace("Sub", v5707, s->LocalAt(9)));
auto v5708 = s->LocalAt(31);
auto v5709 = Value("extra_milk_sale_requests");
auto v5710 = Get(v5708, v5709);
Put(v5708, v5709, Inplace("Add", v5710, s->LocalAt(9)));
break;
}
}
}
}
auto v5711 = s->LocalAt(15);
Put(s->LocalAt(25), Value("market"), v5711);
return s->LocalAt(25);
return {};
}
}  // namespace kagg::opponents::compiled
