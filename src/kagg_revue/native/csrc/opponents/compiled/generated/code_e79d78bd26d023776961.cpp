// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_e79d78bd26d023776961(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"observation", "shops", "state", "step"};
s->PrepareSlots(s_names);
if (static_cast<bool>(([&]() -> Value { auto v14133 = ([&]() -> Value { auto v14134 = s->LocalAt(3); Value v14135; v14135 = Value(int64_t{144}); if (!static_cast<bool>(Binary("GtE", v14134, v14135))) return Value(false); v14134 = v14135; return Value(true); }()); if (!static_cast<bool>(v14133)) return v14133; v14133 = Unary("Not", ([&]() -> Value { auto fn14136 = PrepareDictionaryGet(s->LocalAt(2)); Arguments args14137; args14137.Add(Value("day6"), false); return CallDictionaryGet(c, fn14136, std::move(args14137)); }())); return v14133; }()))) {
auto v14138 = ([&]() -> Value { auto v14139 = ([&]() -> Value { auto fn14140 = s->Global("_get"); Arguments args14141; args14141.positional.reserve(3); args14141.Add(([&]() -> Value { auto fn14142 = s->Global("_get"); Arguments args14143; args14143.positional.reserve(3); args14143.Add(s->LocalAt(0), false); args14143.Add(Value("town"), false); args14143.Add(([&]() -> Value { auto dict14144 = Dict(); return dict14144; }()), false); return Call(c, fn14142, std::move(args14143)); }()), false); args14141.Add(Value("unlocked_shops"), false); args14141.Add(List({}), false); return Call(c, fn14140, std::move(args14141)); }()); if (static_cast<bool>(v14139)) return v14139; v14139 = List({}); return v14139; }());
s->SetAt(1, v14138);
auto v14145 = ([&]() -> Value { auto fn14146 = PrepareDictionaryGet(([&]() -> Value { auto dict14148 = Dict(); auto key14149 = Tuple({Value("BAKERY"), Value("YARN_STORE")}); Put(dict14148, key14149, Value(int64_t{3})); auto key14150 = Tuple({Value("BRUNCH_SPOT"), Value("YARN_STORE")}); Put(dict14148, key14150, Value(int64_t{4})); auto key14151 = Tuple({Value("FARMERS_MARKET"), Value("YARN_STORE")}); Put(dict14148, key14151, Value(int64_t{5})); auto key14152 = Tuple({Value("ICE_CREAM_SHOP"), Value("YARN_STORE")}); Put(dict14148, key14152, Value(int64_t{6})); auto key14153 = Tuple({Value("PET_CAFE"), Value("YARN_STORE")}); Put(dict14148, key14153, Value(int64_t{5})); auto key14154 = Tuple({Value("PIZZA_SHOP"), Value("YARN_STORE")}); Put(dict14148, key14154, Value(int64_t{7})); auto key14155 = Tuple({Value("SMOOTHIE_SHOP"), Value("YARN_STORE")}); Put(dict14148, key14155, Value(int64_t{8})); auto key14156 = Tuple({Value("YARN_STORE"), Value("BAKERY")}); Put(dict14148, key14156, Value(int64_t{9})); auto key14157 = Tuple({Value("YARN_STORE"), Value("BRUNCH_SPOT")}); Put(dict14148, key14157, Value(int64_t{9})); auto key14158 = Tuple({Value("YARN_STORE"), Value("FARMERS_MARKET")}); Put(dict14148, key14158, Value(int64_t{1})); auto key14159 = Tuple({Value("YARN_STORE"), Value("ICE_CREAM_SHOP")}); Put(dict14148, key14159, Value(int64_t{9})); auto key14160 = Tuple({Value("YARN_STORE"), Value("PET_CAFE")}); Put(dict14148, key14160, Value(int64_t{10})); auto key14161 = Tuple({Value("YARN_STORE"), Value("PIZZA_SHOP")}); Put(dict14148, key14161, Value(int64_t{6})); auto key14162 = Tuple({Value("YARN_STORE"), Value("SMOOTHIE_SHOP")}); Put(dict14148, key14162, Value(int64_t{11})); auto key14163 = Tuple({Value("YARN_STORE"), Value("YARN_STORE")}); Put(dict14148, key14163, Value(int64_t{12})); return dict14148; }())); Arguments args14147; args14147.positional.reserve(2); args14147.Add(([&]() -> Value { auto fn14164 = s->Global("tuple"); Arguments args14165; args14165.Add(Slice(s->LocalAt(1), Value{}, Value(int64_t{2}), Value{}), false); return Call(c, fn14164, std::move(args14165)); }()), false); args14147.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn14146, std::move(args14147)); }());
Put(s->LocalAt(2), Value("route"), v14145);
auto v14166 = Value(true);
Put(s->LocalAt(2), Value("day6"), v14166);
}
if (static_cast<bool>(([&]() -> Value { auto v14167 = ([&]() -> Value { auto v14168 = s->LocalAt(3); Value v14169; v14169 = Value(int64_t{648}); if (!static_cast<bool>(Binary("GtE", v14168, v14169))) return Value(false); v14168 = v14169; return Value(true); }()); if (!static_cast<bool>(v14167)) return v14167; v14167 = Unary("Not", ([&]() -> Value { auto fn14170 = PrepareDictionaryGet(s->LocalAt(2)); Arguments args14171; args14171.Add(Value("day27"), false); return CallDictionaryGet(c, fn14170, std::move(args14171)); }())); return v14167; }()))) {
auto v14172 = Value(int64_t{2});
Put(s->LocalAt(2), Value("route"), v14172);
auto v14173 = Value(true);
Put(s->LocalAt(2), Value("day27"), v14173);
}
return ([&]() -> Value { auto fn14174 = PrepareDictionaryGet(s->LocalAt(2)); Arguments args14175; args14175.positional.reserve(2); args14175.Add(Value("route"), false); args14175.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn14174, std::move(args14175)); }());
return {};
}
}  // namespace kagg::opponents::compiled
