// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_233952d2513f478389c2(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"a", "b", "cand", "i", "item", "key", "mine", "n", "op", "order", "schedule", "schedules", "theirs", "total", "value"};
s->PrepareSlots(s_names);
auto v19349 = ([&]() -> Value { auto comp19350 = std::make_shared<Scope>(); comp19350->globals = s->globals; comp19350->parent = s; static constexpr const char* comp19350_names[] = {"item"}; comp19350->PrepareSlots(comp19350_names); auto result19351 = Dict(); for (const auto& item19352 : Iterate(s->Captured("opp_schedules"))) { comp19350->SetAt(0, item19352); Put(result19351, comp19350->LocalAt(0), List({})); } return result19351; }());
s->SetAt(11, v19349);
for (const auto& item19353 : Iterate(([&]() -> Value { auto fn19354 = s->Global("enumerate"); Arguments args19355; args19355.Add(s->LocalAt(2), false); return Call(c, fn19354, std::move(args19355)); }()))) {
auto unpack19356 = Iterate(item19353);
ValidateUnpack(unpack19356, 2, false);
s->SetAt(3, unpack19356.at(0));
s->SetAt(9, unpack19356.at(1));
if (static_cast<bool>(([&]() -> Value { auto v19357 = s->LocalAt(9); if (!static_cast<bool>(v19357)) return v19357; v19357 = ([&]() -> Value { auto v19358 = ([&]() -> Value { auto fn19360 = s->Global("len"); Arguments args19361; args19361.Add(s->LocalAt(9), false); return Call(c, fn19360, std::move(args19361)); }()); Value v19359; v19359 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v19358, v19359))) return Value(false); v19358 = v19359; return Value(true); }()); if (!static_cast<bool>(v19357)) return v19357; v19357 = ([&]() -> Value { auto v19362 = Get(s->LocalAt(9), Value(int64_t{0})); Value v19363; v19363 = Tuple({Value("SELL"), Value("BUY_PRODUCT")}); if (!static_cast<bool>(Binary("In", v19362, v19363))) return Value(false); v19362 = v19363; return Value(true); }()); if (!static_cast<bool>(v19357)) return v19357; v19357 = ([&]() -> Value { auto v19364 = Get(s->LocalAt(9), Value(int64_t{1})); Value v19365; v19365 = s->Captured("params"); if (!static_cast<bool>(Binary("In", v19364, v19365))) return Value(false); v19364 = v19365; return Value(true); }()); return v19357; }()))) {
(void)([&]() -> Value { auto fn19366 = Attribute(([&]() -> Value { auto fn19368 = Attribute(s->LocalAt(11), "setdefault"); Arguments args19369; args19369.positional.reserve(2); args19369.Add(Get(s->LocalAt(9), Value(int64_t{1})), false); args19369.Add(List({}), false); return Call(c, fn19368, std::move(args19369)); }()), "append"); Arguments args19367; args19367.Add(Tuple({s->LocalAt(3), Get(s->LocalAt(9), Value(int64_t{0})), ([&]() -> Value { auto fn19370 = s->Global("int"); Arguments args19371; args19371.Add(Get(s->LocalAt(9), Value(int64_t{2})), false); return Call(c, fn19370, std::move(args19371)); }())}), false); return Call(c, fn19366, std::move(args19367)); }());
}
}
auto v19372 = Value(0.0);
s->SetAt(13, v19372);
for (const auto& item19373 : Iterate(([&]() -> Value { auto fn19374 = Attribute(s->LocalAt(11), "items"); Arguments args19375; return Call(c, fn19374, std::move(args19375)); }()))) {
auto unpack19376 = Iterate(item19373);
ValidateUnpack(unpack19376, 2, false);
s->SetAt(4, unpack19376.at(0));
s->SetAt(10, unpack19376.at(1));
auto v19377 = Tuple({s->LocalAt(4), ([&]() -> Value { auto fn19378 = s->Global("tuple"); Arguments args19379; args19379.Add(s->LocalAt(10), false); return Call(c, fn19378, std::move(args19379)); }())});
s->SetAt(5, v19377);
auto v19380 = ([&]() -> Value { auto fn19381 = PrepareDictionaryGet(s->Captured("cache")); Arguments args19382; args19382.Add(s->LocalAt(5), false); return CallDictionaryGet(c, fn19381, std::move(args19382)); }());
s->SetAt(14, v19380);
if (static_cast<bool>(([&]() -> Value { auto v19383 = s->LocalAt(14); Value v19384; v19384 = Value{}; if (!static_cast<bool>(Binary("Is", v19383, v19384))) return Value(false); v19383 = v19384; return Value(true); }()))) {
auto v19385 = ([&]() -> Value { auto comp19386 = std::make_shared<Scope>(); comp19386->globals = s->globals; comp19386->parent = s; static constexpr const char* comp19386_names[] = {"_"}; comp19386->PrepareSlots(comp19386_names); auto result19387 = List(); for (const auto& item19388 : Iterate(s->LocalAt(2))) { comp19386->SetAt(0, item19388); result19387.node()->sequence.push_back(List({})); } return result19387; }());
s->SetAt(6, v19385);
for (const auto& item19389 : Iterate(s->LocalAt(10))) {
auto unpack19390 = Iterate(item19389);
ValidateUnpack(unpack19390, 3, false);
s->SetAt(3, unpack19390.at(0));
s->SetAt(8, unpack19390.at(1));
s->SetAt(7, unpack19390.at(2));
auto v19391 = List({s->LocalAt(8), s->LocalAt(4), s->LocalAt(7)});
Put(s->LocalAt(6), s->LocalAt(3), v19391);
}
auto v19392 = ([&]() -> Value { auto fn19393 = PrepareDictionaryGet(s->Captured("opp_schedules")); Arguments args19394; args19394.positional.reserve(2); args19394.Add(s->LocalAt(4), false); args19394.Add(([&]() -> Value { auto comp19395 = std::make_shared<Scope>(); comp19395->globals = s->globals; comp19395->parent = s; static constexpr const char* comp19395_names[] = {"_"}; comp19395->PrepareSlots(comp19395_names); auto result19396 = List(); for (const auto& item19397 : Iterate(s->Captured("opp"))) { comp19395->SetAt(0, item19397); result19396.node()->sequence.push_back(List({})); } return result19396; }()), false); return CallDictionaryGet(c, fn19393, std::move(args19394)); }());
s->SetAt(12, v19392);
auto v19398 = ([&]() -> Value { auto fn19399 = s->Global("_v44y_lockstep"); Arguments args19400; args19400.positional.reserve(6); args19400.Add(s->LocalAt(6), false); args19400.Add(s->LocalAt(12), false); args19400.Add(([&]() -> Value { auto dict19401 = Dict(); auto key19402 = s->LocalAt(4); Put(dict19401, key19402, Get(s->Captured("inv0"), s->LocalAt(4))); return dict19401; }()), false); args19400.Add(([&]() -> Value { auto dict19403 = Dict(); auto key19404 = s->LocalAt(4); Put(dict19403, key19404, ([&]() -> Value { auto fn19405 = PrepareDictionaryGet(s->Captured("stock")); Arguments args19406; args19406.positional.reserve(2); args19406.Add(s->LocalAt(4), false); args19406.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn19405, std::move(args19406)); }())); return dict19403; }()), false); args19400.Add(([&]() -> Value { auto dict19407 = Dict(); auto key19408 = s->LocalAt(4); Put(dict19407, key19408, ([&]() -> Value { auto fn19409 = PrepareDictionaryGet(s->Captured("stock")); Arguments args19410; args19410.positional.reserve(2); args19410.Add(s->LocalAt(4), false); args19410.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn19409, std::move(args19410)); }())); return dict19407; }()), false); args19400.Add(([&]() -> Value { auto dict19411 = Dict(); auto key19412 = s->LocalAt(4); Put(dict19411, key19412, Get(s->Captured("params"), s->LocalAt(4))); return dict19411; }()), false); return Call(c, fn19399, std::move(args19400)); }());
auto unpack19413 = Iterate(v19398);
ValidateUnpack(unpack19413, 2, false);
s->SetAt(0, unpack19413.at(0));
s->SetAt(1, unpack19413.at(1));
auto v19414 = ([&]() -> Value { auto v19415 = s->LocalAt(0); return Binary("Sub", v19415, s->LocalAt(1)); }());
s->SetAt(14, v19414);
auto v19416 = s->LocalAt(14);
Put(s->Captured("cache"), s->LocalAt(5), v19416);
}
auto v19417 = s->LocalAt(13);
s->SetAt(13, Inplace("Add", v19417, s->LocalAt(14)));
}
return s->LocalAt(13);
return {};
}
}  // namespace kagg::opponents::compiled
