// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_1d76172b008baac8d640(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "actor", "bonus", "changed", "command", "commands", "day", "expected", "farm", "item", "native", "obs", "player", "positions", "prices", "result", "step", "tape", "tile"};
s->PrepareSlots(s_names);
auto v9366 = ([&]() -> Value { auto fn9367 = s->Global("int"); Arguments args9368; args9368.Add(Get(s->LocalAt(11), Value("step")), false); return Call(c, fn9367, std::move(args9368)); }());
s->SetAt(16, v9366);
auto v9369 = ([&]() -> Value { auto v9370 = s->LocalAt(16); return Binary("FloorDiv", v9370, Value(int64_t{24})); }());
s->SetAt(6, v9369);
if (static_cast<bool>(([&]() -> Value { auto v9371 = Unary("Not", ([&]() -> Value { auto v9372 = Value(int64_t{10}); Value v9373; v9373 = s->LocalAt(6); if (!static_cast<bool>(Binary("LtE", v9372, v9373))) return Value(false); v9372 = v9373; v9373 = Value(int64_t{28}); if (!static_cast<bool>(Binary("LtE", v9372, v9373))) return Value(false); v9372 = v9373; return Value(true); }())); if (static_cast<bool>(v9371)) return v9371; v9371 = ([&]() -> Value { auto v9374 = ([&]() -> Value { auto v9376 = s->LocalAt(16); return Binary("Mod", v9376, Value(int64_t{24})); }()); Value v9375; v9375 = Value(int64_t{21}); if (!static_cast<bool>(Binary("Gt", v9374, v9375))) return Value(false); v9374 = v9375; return Value(true); }()); return v9371; }()))) {
return s->LocalAt(0);
}
auto v9377 = ([&]() -> Value { auto fn9378 = s->Global("int"); Arguments args9379; args9379.Add(Get(s->LocalAt(11), Value("player")), false); return Call(c, fn9378, std::move(args9379)); }());
s->SetAt(12, v9377);
auto v9380 = Get(Attribute(Attribute(s->Global("_IMPL"), "chassis"), "players"), s->LocalAt(12));
s->SetAt(10, v9380);
auto v9381 = ([&]() -> Value { auto fn9382 = s->Global("_v219_native_day"); Arguments args9383; args9383.positional.reserve(2); args9383.Add(s->LocalAt(10), false); args9383.Add(s->LocalAt(6), false); return Call(c, fn9382, std::move(args9383)); }());
s->SetAt(17, v9381);
auto v9384 = ([&]() -> Value { auto fn9385 = s->Global("max"); Arguments args9386; args9386.Add(([&]() -> Value { auto comp9387 = std::make_shared<Scope>(); comp9387->globals = s->globals; comp9387->parent = s; static constexpr const char* comp9387_names[] = {"a"}; comp9387->PrepareSlots(comp9387_names); auto result9388 = List(); for (const auto& item9389 : Iterate(s->LocalAt(17))) { comp9387->SetAt(0, item9389); result9388.node()->sequence.push_back(([&]() -> Value { auto fn9390 = comp9387->Global("len"); Arguments args9391; args9391.Add(([&]() -> Value { auto fn9392 = PrepareDictionaryGet(comp9387->LocalAt(0)); Arguments args9393; args9393.positional.reserve(2); args9393.Add(Value("hands"), false); args9393.Add(List({}), false); return CallDictionaryGet(c, fn9392, std::move(args9393)); }()), false); return Call(c, fn9390, std::move(args9391)); }())); } return result9388; }()), false); return Call(c, fn9385, std::move(args9386)); }());
s->SetAt(7, v9384);
auto v9394 = Get(Get(s->LocalAt(11), Value("farms")), s->LocalAt(12));
s->SetAt(8, v9394);
auto v9395 = ([&]() -> Value { Arguments args9396; args9396.Add(Get(s->LocalAt(8), Value("farmer")), false); args9396.Add(Get(s->LocalAt(8), Value("hands")), true); return List(std::move(args9396.positional)); }());
s->SetAt(13, v9395);
auto v9397 = ([&]() -> Value { Arguments args9398; args9398.Add(([&]() -> Value { auto v9399 = ([&]() -> Value { auto fn9400 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args9401; args9401.Add(Value("farmer"), false); return CallDictionaryGet(c, fn9400, std::move(args9401)); }()); if (static_cast<bool>(v9399)) return v9399; v9399 = List({Value("PASS")}); return v9399; }()), false); args9398.Add(([&]() -> Value { auto v9402 = ([&]() -> Value { auto fn9403 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args9404; args9404.Add(Value("hands"), false); return CallDictionaryGet(c, fn9403, std::move(args9404)); }()); if (static_cast<bool>(v9402)) return v9402; v9402 = List({}); return v9402; }()), true); return List(std::move(args9398.positional)); }());
s->SetAt(5, v9397);
auto v9405 = Get(Get(s->LocalAt(11), Value("market")), Value("prices"));
s->SetAt(14, v9405);
auto v9406 = Value(false);
s->SetAt(3, v9406);
for (const auto& item9407 : Iterate(([&]() -> Value { auto fn9408 = s->Global("enumerate"); Arguments args9409; args9409.Add(Slice(s->LocalAt(5), Value{}, ([&]() -> Value { auto v9410 = s->LocalAt(7); return Binary("Add", v9410, Value(int64_t{1})); }()), Value{}), false); return Call(c, fn9408, std::move(args9409)); }()))) {
auto unpack9411 = Iterate(item9407);
ValidateUnpack(unpack9411, 2, false);
s->SetAt(1, unpack9411.at(0));
s->SetAt(4, unpack9411.at(1));
if (static_cast<bool>(([&]() -> Value { auto v9412 = ([&]() -> Value { auto v9413 = s->LocalAt(4); Value v9414; v9414 = List({Value("FEED")}); if (!static_cast<bool>(Binary("NotEq", v9413, v9414))) return Value(false); v9413 = v9414; return Value(true); }()); if (static_cast<bool>(v9412)) return v9412; v9412 = ([&]() -> Value { auto v9415 = s->LocalAt(1); Value v9416; v9416 = ([&]() -> Value { auto fn9417 = s->Global("len"); Arguments args9418; args9418.Add(s->LocalAt(13), false); return Call(c, fn9417, std::move(args9418)); }()); if (!static_cast<bool>(Binary("GtE", v9415, v9416))) return Value(false); v9415 = v9416; return Value(true); }()); return v9412; }()))) {
continue;
}
auto v9419 = ([&]() -> Value { auto fn9420 = s->Global("_tile_at"); Arguments args9421; args9421.positional.reserve(2); args9421.Add(Get(s->LocalAt(8), Value("tiles")), false); args9421.Add(Get(s->LocalAt(13), s->LocalAt(1)), false); return Call(c, fn9420, std::move(args9421)); }());
s->SetAt(18, v9419);
if (static_cast<bool>(([&]() -> Value { auto v9422 = Unary("Not", ([&]() -> Value { auto fn9423 = s->Global("isinstance"); Arguments args9424; args9424.positional.reserve(2); args9424.Add(s->LocalAt(18), false); args9424.Add(s->Global("dict"), false); return Call(c, fn9423, std::move(args9424)); }())); if (static_cast<bool>(v9422)) return v9422; v9422 = ([&]() -> Value { auto v9425 = ([&]() -> Value { auto fn9427 = PrepareDictionaryGet(s->LocalAt(18)); Arguments args9428; args9428.Add(Value("animal"), false); return CallDictionaryGet(c, fn9427, std::move(args9428)); }()); Value v9426; v9426 = Tuple({Value("GOOSE"), Value("COW"), Value("SHEEP")}); if (!static_cast<bool>(Binary("NotIn", v9425, v9426))) return Value(false); v9425 = v9426; return Value(true); }()); return v9422; }()))) {
continue;
}
if (static_cast<bool>(([&]() -> Value { auto v9429 = ([&]() -> Value { auto fn9430 = PrepareDictionaryGet(s->LocalAt(18)); Arguments args9431; args9431.Add(Value("fed_today"), false); return CallDictionaryGet(c, fn9430, std::move(args9431)); }()); if (static_cast<bool>(v9429)) return v9429; v9429 = ([&]() -> Value { auto v9432 = ([&]() -> Value { auto fn9434 = s->Global("int"); Arguments args9435; args9435.Add(([&]() -> Value { auto fn9436 = PrepareDictionaryGet(s->LocalAt(18)); Arguments args9437; args9437.positional.reserve(2); args9437.Add(Value("consecutive_unfed"), false); args9437.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn9436, std::move(args9437)); }()), false); return Call(c, fn9434, std::move(args9435)); }()); Value v9433; v9433 = Value(int64_t{0}); if (!static_cast<bool>(Binary("NotEq", v9432, v9433))) return Value(false); v9432 = v9433; return Value(true); }()); return v9429; }()))) {
continue;
}
if (static_cast<bool>(([&]() -> Value { auto v9438 = ([&]() -> Value { auto fn9440 = s->Global("int"); Arguments args9441; args9441.Add(([&]() -> Value { auto fn9442 = PrepareDictionaryGet(Get(Get(Get(s->LocalAt(11), Value("private")), Value("inventories")), s->LocalAt(1))); Arguments args9443; args9443.positional.reserve(2); args9443.Add(Value("WHEAT"), false); args9443.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn9442, std::move(args9443)); }()), false); return Call(c, fn9440, std::move(args9441)); }()); Value v9439; v9439 = Value(int64_t{0}); if (!static_cast<bool>(Binary("LtE", v9438, v9439))) return Value(false); v9438 = v9439; return Value(true); }()))) {
continue;
}
auto v9444 = Get(([&]() -> Value { auto dict9445 = Dict(); auto key9446 = Value("GOOSE"); Put(dict9445, key9446, Value("EGG")); auto key9447 = Value("COW"); Put(dict9445, key9447, Value("MILK")); auto key9448 = Value("SHEEP"); Put(dict9445, key9448, Value("WOOL")); return dict9445; }()), Get(s->LocalAt(18), Value("animal")));
s->SetAt(9, v9444);
auto v9449 = ([&]() -> Value { auto fn9450 = s->Global("_r88_feed_bonus_cost"); Arguments args9451; args9451.positional.reserve(2); args9451.Add(s->LocalAt(18), false); args9451.Add(s->LocalAt(6), false); return Call(c, fn9450, std::move(args9451)); }());
s->SetAt(2, v9449);
if (static_cast<bool>(([&]() -> Value { auto v9452 = ([&]() -> Value { auto v9454 = ([&]() -> Value { auto v9455 = s->LocalAt(2); return Binary("Mult", v9455, ([&]() -> Value { auto v9456 = ([&]() -> Value { auto fn9457 = s->Global("float"); Arguments args9458; args9458.Add(Get(s->LocalAt(14), s->LocalAt(9)), false); return Call(c, fn9457, std::move(args9458)); }()); return Binary("Add", v9456, Value(int64_t{5})); }())); }()); return Binary("Mult", v9454, Value(1.25)); }()); Value v9453; v9453 = ([&]() -> Value { auto fn9459 = s->Global("float"); Arguments args9460; args9460.Add(Get(s->LocalAt(14), Value("WHEAT")), false); return Call(c, fn9459, std::move(args9460)); }()); if (!static_cast<bool>(Binary("GtE", v9452, v9453))) return Value(false); v9452 = v9453; return Value(true); }()))) {
continue;
}
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto fn9461 = s->Global("_r86_next_feed"); Arguments args9462; args9462.positional.reserve(2); args9462.Add(s->LocalAt(11), false); args9462.Add(Get(s->LocalAt(13), s->LocalAt(1)), false); return Call(c, fn9461, std::move(args9462)); }())))) {
continue;
}
auto v9463 = List({Value("PASS")});
Put(s->LocalAt(5), s->LocalAt(1), v9463);
auto v9464 = Value(true);
s->SetAt(3, v9464);
auto v9465 = s->Global("_R85_REPORT");
auto v9466 = Value("feed_skips");
auto v9467 = Get(v9465, v9466);
Put(v9465, v9466, Inplace("Add", v9467, Value(int64_t{1})));
}
if (static_cast<bool>(Unary("Not", s->LocalAt(3)))) {
return s->LocalAt(0);
}
auto v9468 = ([&]() -> Value { auto fn9469 = Attribute(s->Global("copy"), "deepcopy"); Arguments args9470; args9470.Add(s->LocalAt(0), false); return Call(c, fn9469, std::move(args9470)); }());
s->SetAt(15, v9468);
auto v9471 = Tuple({Get(s->LocalAt(5), Value(int64_t{0})), Slice(s->LocalAt(5), Value(int64_t{1}), Value{}, Value{})});
auto unpack9472 = Iterate(v9471);
ValidateUnpack(unpack9472, 2, false);
Put(s->LocalAt(15), Value("farmer"), unpack9472.at(0));
Put(s->LocalAt(15), Value("hands"), unpack9472.at(1));
return s->LocalAt(15);
return {};
}
}  // namespace kagg::opponents::compiled
