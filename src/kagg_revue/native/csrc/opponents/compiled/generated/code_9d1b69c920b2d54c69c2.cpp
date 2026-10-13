// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_9d1b69c920b2d54c69c2(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"cost", "farm", "hires", "item", "obs", "op", "order", "orders", "prices", "q"};
s->PrepareSlots(s_names);
auto v10256 = Get(Get(s->LocalAt(4), Value("farms")), Get(s->LocalAt(4), Value("player")));
s->SetAt(1, v10256);
auto v10257 = Value(int64_t{0});
s->SetAt(0, v10257);
auto v10258 = ([&]() -> Value { auto fn10259 = s->Global("int"); Arguments args10260; args10260.Add(Get(s->LocalAt(1), Value("hires_today")), false); return Call(c, fn10259, std::move(args10260)); }());
s->SetAt(2, v10258);
auto v10261 = ([&]() -> Value { auto comp10262 = std::make_shared<Scope>(); comp10262->globals = s->globals; comp10262->parent = s; static constexpr const char* comp10262_names[] = {"p"}; comp10262->PrepareSlots(comp10262_names); auto result10263 = Dict(); for (const auto& item10264 : Iterate(Tuple({Value("WHEAT"), Value("FERTILIZER")}))) { comp10262->SetAt(0, item10264); Put(result10263, comp10262->LocalAt(0), ([&]() -> Value { auto fn10265 = comp10262->Global("_r37_market_price"); Arguments args10266; args10266.positional.reserve(2); args10266.Add(comp10262->LocalAt(0), false); args10266.Add(([&]() -> Value { auto v10267 = Get(Get(Get(comp10262->Captured("obs"), Value("market")), Value("inventory")), comp10262->LocalAt(0)); return Binary("Sub", v10267, Value(int64_t{2000})); }()), false); return Call(c, fn10265, std::move(args10266)); }())); } return result10263; }());
s->SetAt(8, v10261);
for (const auto& item10268 : Iterate(s->LocalAt(7))) {
s->SetAt(6, item10268);
if (static_cast<bool>(Unary("Not", s->LocalAt(6)))) {
continue;
}
auto v10269 = Get(s->LocalAt(6), Value(int64_t{0}));
s->SetAt(5, v10269);
if (static_cast<bool>(([&]() -> Value { auto v10270 = s->LocalAt(5); Value v10271; v10271 = Value("HIRE"); if (!static_cast<bool>(Binary("Eq", v10270, v10271))) return Value(false); v10270 = v10271; return Value(true); }()))) {
auto v10272 = s->LocalAt(0);
s->SetAt(0, Inplace("Add", v10272, ([&]() -> Value { auto fn10273 = s->Global("_v219_fib"); Arguments args10274; args10274.Add(s->LocalAt(2), false); return Call(c, fn10273, std::move(args10274)); }())));
auto v10275 = s->LocalAt(2);
s->SetAt(2, Inplace("Add", v10275, Value(int64_t{1})));
}
else {
if (static_cast<bool>(([&]() -> Value { auto v10276 = s->LocalAt(5); Value v10277; v10277 = Value("BUY_LAND"); if (!static_cast<bool>(Binary("Eq", v10276, v10277))) return Value(false); v10276 = v10277; return Value(true); }()))) {
auto v10278 = s->LocalAt(0);
s->SetAt(0, Inplace("Add", v10278, Value(int64_t{4000})));
}
else {
if (static_cast<bool>(([&]() -> Value { auto v10279 = ([&]() -> Value { auto fn10281 = s->Global("len"); Arguments args10282; args10282.Add(s->LocalAt(6), false); return Call(c, fn10281, std::move(args10282)); }()); Value v10280; v10280 = Value(int64_t{2}); if (!static_cast<bool>(Binary("Gt", v10279, v10280))) return Value(false); v10279 = v10280; return Value(true); }()))) {
auto v10283 = Get(s->LocalAt(6), Value(int64_t{1}));
s->SetAt(3, v10283);
auto v10284 = ([&]() -> Value { auto fn10285 = s->Global("max"); Arguments args10286; args10286.positional.reserve(2); args10286.Add(Value(int64_t{0}), false); args10286.Add(([&]() -> Value { auto fn10287 = s->Global("int"); Arguments args10288; args10288.Add(Get(s->LocalAt(6), Value(int64_t{2})), false); return Call(c, fn10287, std::move(args10288)); }()), false); return Call(c, fn10285, std::move(args10286)); }());
s->SetAt(9, v10284);
if (static_cast<bool>(([&]() -> Value { auto v10289 = s->LocalAt(5); Value v10290; v10290 = Value("BUY_PRODUCT"); if (!static_cast<bool>(Binary("Eq", v10289, v10290))) return Value(false); v10289 = v10290; return Value(true); }()))) {
auto v10291 = s->LocalAt(0);
s->SetAt(0, Inplace("Add", v10291, ([&]() -> Value { auto v10292 = s->LocalAt(9); return Binary("Mult", v10292, Get(s->LocalAt(8), s->LocalAt(3))); }())));
}
else {
if (static_cast<bool>(([&]() -> Value { auto v10293 = s->LocalAt(5); Value v10294; v10294 = Value("BUY_ANIMAL"); if (!static_cast<bool>(Binary("Eq", v10293, v10294))) return Value(false); v10293 = v10294; return Value(true); }()))) {
auto v10295 = s->LocalAt(0);
s->SetAt(0, Inplace("Add", v10295, ([&]() -> Value { auto v10296 = s->LocalAt(9); return Binary("Mult", v10296, Get(([&]() -> Value { auto dict10297 = Dict(); auto key10298 = Value("GOOSE"); Put(dict10297, key10298, Value(int64_t{300})); auto key10299 = Value("COW"); Put(dict10297, key10299, Value(int64_t{400})); auto key10300 = Value("SHEEP"); Put(dict10297, key10300, Value(int64_t{500})); return dict10297; }()), s->LocalAt(3))); }())));
}
else {
if (static_cast<bool>(([&]() -> Value { auto v10301 = s->LocalAt(5); Value v10302; v10302 = Value("BUY_SEED"); if (!static_cast<bool>(Binary("Eq", v10301, v10302))) return Value(false); v10301 = v10302; return Value(true); }()))) {
auto v10303 = s->LocalAt(0);
s->SetAt(0, Inplace("Add", v10303, ([&]() -> Value { auto v10304 = s->LocalAt(9); return Binary("Mult", v10304, Get(([&]() -> Value { auto dict10305 = Dict(); auto key10306 = Value("WHEAT"); Put(dict10305, key10306, Value(int64_t{10})); auto key10307 = Value("CARROT"); Put(dict10305, key10307, Value(int64_t{20})); auto key10308 = Value("TOMATO"); Put(dict10305, key10308, Value(int64_t{50})); auto key10309 = Value("STRAWBERRY"); Put(dict10305, key10309, Value(int64_t{100})); auto key10310 = Value("MELON"); Put(dict10305, key10310, Value(int64_t{80})); return dict10305; }()), s->LocalAt(3))); }())));
}
}
}
}
}
}
}
return ([&]() -> Value { auto v10311 = s->LocalAt(0); Value v10312; v10312 = Get(s->LocalAt(1), Value("money")); if (!static_cast<bool>(Binary("LtE", v10311, v10312))) return Value(false); v10311 = v10312; return Value(true); }());
return {};
}
}  // namespace kagg::opponents::compiled
