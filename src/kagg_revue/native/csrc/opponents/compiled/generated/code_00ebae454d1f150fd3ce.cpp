// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_00ebae454d1f150fd3ce(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"_", "d", "inv", "opened", "price", "prices", "revenue", "units", "with_new"};
s->PrepareSlots(s_names);
auto v24475 = ([&]() -> Value { auto fn24476 = s->Global("float"); Arguments args24477; args24477.Add(Get(Get(s->Captured("market"), Value("inventory")), s->Captured("item")), false); return Call(c, fn24476, std::move(args24477)); }());
s->SetAt(2, v24475);
auto v24478 = Tuple({([&]() -> Value { auto dict24479 = Dict(); return dict24479; }()), Value(0.0)});
auto unpack24480 = Iterate(v24478);
ValidateUnpack(unpack24480, 2, false);
s->SetAt(5, unpack24480.at(0));
s->SetAt(6, unpack24480.at(1));
for (const auto& item24481 : Iterate(([&]() -> Value { auto fn24482 = s->Global("range"); Arguments args24483; args24483.positional.reserve(2); args24483.Add(([&]() -> Value { auto v24484 = s->Captured("day"); return Binary("Add", v24484, Value(int64_t{1})); }()), false); args24483.Add(Value(int64_t{30}), false); return Call(c, fn24482, std::move(args24483)); }()))) {
s->SetAt(1, item24481);
auto v24485 = ([&]() -> Value { auto fn24486 = s->Global("min"); Arguments args24487; args24487.positional.reserve(2); args24487.Add(s->Captured("unlocks_left"), false); args24487.Add(([&]() -> Value { auto fn24488 = s->Global("max"); Arguments args24489; args24489.positional.reserve(2); args24489.Add(Value(int64_t{0}), false); args24489.Add(([&]() -> Value { auto v24490 = ([&]() -> Value { auto v24491 = s->LocalAt(1); return Binary("FloorDiv", v24491, Value(int64_t{3})); }()); return Binary("Sub", v24490, ([&]() -> Value { auto v24492 = s->Captured("day"); return Binary("FloorDiv", v24492, Value(int64_t{3})); }())); }()), false); return Call(c, fn24488, std::move(args24489)); }()), false); return Call(c, fn24486, std::move(args24487)); }());
s->SetAt(3, v24485);
auto v24493 = s->LocalAt(2);
s->SetAt(2, Inplace("Sub", v24493, ([&]() -> Value { auto v24494 = s->Captured("base_demand"); return Binary("Add", v24494, ([&]() -> Value { auto v24495 = s->Captured("extra_demand"); return Binary("Mult", v24495, s->LocalAt(3)); }())); }())));
auto v24496 = s->LocalAt(2);
s->SetAt(2, Inplace("Add", v24496, ([&]() -> Value { auto v24497 = ([&]() -> Value { auto fn24498 = PrepareDictionaryGet(s->Captured("ours_existing")); Arguments args24499; args24499.positional.reserve(2); args24499.Add(s->LocalAt(1), false); args24499.Add(Value(0.0), false); return CallDictionaryGet(c, fn24498, std::move(args24499)); }()); return Binary("Add", v24497, ([&]() -> Value { auto fn24500 = PrepareDictionaryGet(s->Captured("rival_existing")); Arguments args24501; args24501.positional.reserve(2); args24501.Add(s->LocalAt(1), false); args24501.Add(Value(0.0), false); return CallDictionaryGet(c, fn24500, std::move(args24501)); }())); }())));
auto v24502 = ([&]() -> Value { auto fn24503 = s->Global("_r37_market_price"); Arguments args24504; args24504.positional.reserve(3); args24504.Add(s->Captured("item"), false); args24504.Add(([&]() -> Value { auto fn24505 = s->Global("int"); Arguments args24506; args24506.Add(([&]() -> Value { auto fn24507 = s->Global("round"); Arguments args24508; args24508.Add(s->LocalAt(2), false); return Call(c, fn24507, std::move(args24508)); }()), false); return Call(c, fn24505, std::move(args24506)); }()), false); args24504.Add(s->Captured("params"), false); return Call(c, fn24503, std::move(args24504)); }());
Put(s->LocalAt(5), s->LocalAt(1), v24502);
if (static_cast<bool>(s->LocalAt(8))) {
auto v24509 = ([&]() -> Value { auto fn24510 = s->Global("int"); Arguments args24511; args24511.Add(([&]() -> Value { auto fn24512 = s->Global("round"); Arguments args24513; args24513.Add(([&]() -> Value { auto fn24514 = PrepareDictionaryGet(s->Captured("new")); Arguments args24515; args24515.positional.reserve(2); args24515.Add(s->LocalAt(1), false); args24515.Add(Value(0.0), false); return CallDictionaryGet(c, fn24514, std::move(args24515)); }()), false); return Call(c, fn24512, std::move(args24513)); }()), false); return Call(c, fn24510, std::move(args24511)); }());
s->SetAt(7, v24509);
for (const auto& item24516 : Iterate(([&]() -> Value { auto fn24517 = s->Global("range"); Arguments args24518; args24518.Add(s->LocalAt(7), false); return Call(c, fn24517, std::move(args24518)); }()))) {
s->SetAt(0, item24516);
auto v24519 = ([&]() -> Value { auto fn24520 = s->Global("_r37_market_price"); Arguments args24521; args24521.positional.reserve(3); args24521.Add(s->Captured("item"), false); args24521.Add(([&]() -> Value { auto fn24522 = s->Global("int"); Arguments args24523; args24523.Add(([&]() -> Value { auto fn24524 = s->Global("round"); Arguments args24525; args24525.Add(s->LocalAt(2), false); return Call(c, fn24524, std::move(args24525)); }()), false); return Call(c, fn24522, std::move(args24523)); }()), false); args24521.Add(s->Captured("params"), false); return Call(c, fn24520, std::move(args24521)); }());
s->SetAt(4, v24519);
auto v24526 = s->LocalAt(6);
s->SetAt(6, Inplace("Add", v24526, s->LocalAt(4)));
if (static_cast<bool>(([&]() -> Value { auto v24527 = s->LocalAt(4); Value v24528; v24528 = Value(int64_t{1}); if (!static_cast<bool>(Binary("Gt", v24527, v24528))) return Value(false); v24527 = v24528; return Value(true); }()))) {
auto v24529 = s->LocalAt(2);
s->SetAt(2, Inplace("Add", v24529, Value(int64_t{1})));
}
}
}
}
return Tuple({s->LocalAt(5), s->LocalAt(6)});
return {};
}
}  // namespace kagg::opponents::compiled
