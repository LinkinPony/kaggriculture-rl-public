// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_bcb06100ee94f0aee8d0(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"_", "action", "end", "i", "j", "kept", "market", "new", "o", "obs", "order", "p", "private", "q", "quantities", "remaining", "removed", "replacement", "segments", "start"};
s->PrepareSlots(s_names);
auto v20275 = ([&]() -> Value { auto v20276 = ([&]() -> Value { auto fn20277 = PrepareDictionaryGet(s->LocalAt(1)); Arguments args20278; args20278.Add(Value("market"), false); return CallDictionaryGet(c, fn20277, std::move(args20278)); }()); if (static_cast<bool>(v20276)) return v20276; v20276 = List({}); return v20276; }());
s->SetAt(6, v20275);
if (static_cast<bool>(([&]() -> Value { auto v20279 = ([&]() -> Value { auto v20280 = ([&]() -> Value { auto fn20282 = s->Global("int"); Arguments args20283; args20283.Add(Get(s->LocalAt(9), Value("step")), false); return Call(c, fn20282, std::move(args20283)); }()); Value v20281; v20281 = Value(int64_t{144}); if (!static_cast<bool>(Binary("Lt", v20280, v20281))) return Value(false); v20280 = v20281; return Value(true); }()); if (static_cast<bool>(v20279)) return v20279; v20279 = ([&]() -> Value { auto v20284 = ([&]() -> Value { auto fn20286 = s->Global("len"); Arguments args20287; args20287.Add(s->LocalAt(6), false); return Call(c, fn20286, std::move(args20287)); }()); Value v20285; v20285 = Value(int64_t{2}); if (!static_cast<bool>(Binary("Lt", v20284, v20285))) return Value(false); v20284 = v20285; return Value(true); }()); return v20279; }()))) {
return s->LocalAt(1);
}
auto v20288 = List({});
s->SetAt(18, v20288);
auto v20289 = Value(int64_t{0});
s->SetAt(3, v20289);
while (static_cast<bool>(([&]() -> Value { auto v20290 = s->LocalAt(3); Value v20291; v20291 = ([&]() -> Value { auto fn20292 = s->Global("len"); Arguments args20293; args20293.Add(s->LocalAt(6), false); return Call(c, fn20292, std::move(args20293)); }()); if (!static_cast<bool>(Binary("Lt", v20290, v20291))) return Value(false); v20290 = v20291; return Value(true); }()))) {
if (static_cast<bool>(([&]() -> Value { auto v20294 = ([&]() -> Value { auto v20295 = ([&]() -> Value { auto fn20297 = s->Global("len"); Arguments args20298; args20298.Add(Get(s->LocalAt(6), s->LocalAt(3)), false); return Call(c, fn20297, std::move(args20298)); }()); Value v20296; v20296 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v20295, v20296))) return Value(false); v20295 = v20296; return Value(true); }()); if (!static_cast<bool>(v20294)) return v20294; v20294 = ([&]() -> Value { auto v20299 = Get(Get(s->LocalAt(6), s->LocalAt(3)), Value(int64_t{0})); Value v20300; v20300 = Value("SELL"); if (!static_cast<bool>(Binary("Eq", v20299, v20300))) return Value(false); v20299 = v20300; return Value(true); }()); if (!static_cast<bool>(v20294)) return v20294; v20294 = ([&]() -> Value { auto v20301 = Get(Get(s->LocalAt(6), s->LocalAt(3)), Value(int64_t{1})); Value v20302; v20302 = s->Global("_E334_ITEMS"); if (!static_cast<bool>(Binary("In", v20301, v20302))) return Value(false); v20301 = v20302; return Value(true); }()); return v20294; }()))) {
auto v20303 = ([&]() -> Value { auto v20304 = s->LocalAt(3); return Binary("Add", v20304, Value(int64_t{1})); }());
s->SetAt(4, v20303);
while (static_cast<bool>(([&]() -> Value { auto v20305 = ([&]() -> Value { auto v20306 = s->LocalAt(4); Value v20307; v20307 = ([&]() -> Value { auto fn20308 = s->Global("len"); Arguments args20309; args20309.Add(s->LocalAt(6), false); return Call(c, fn20308, std::move(args20309)); }()); if (!static_cast<bool>(Binary("Lt", v20306, v20307))) return Value(false); v20306 = v20307; return Value(true); }()); if (!static_cast<bool>(v20305)) return v20305; v20305 = ([&]() -> Value { auto v20310 = ([&]() -> Value { auto fn20312 = s->Global("len"); Arguments args20313; args20313.Add(Get(s->LocalAt(6), s->LocalAt(4)), false); return Call(c, fn20312, std::move(args20313)); }()); Value v20311; v20311 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v20310, v20311))) return Value(false); v20310 = v20311; return Value(true); }()); if (!static_cast<bool>(v20305)) return v20305; v20305 = ([&]() -> Value { auto v20314 = Get(Get(s->LocalAt(6), s->LocalAt(4)), Value(int64_t{0})); Value v20315; v20315 = Value("SELL"); if (!static_cast<bool>(Binary("Eq", v20314, v20315))) return Value(false); v20314 = v20315; return Value(true); }()); if (!static_cast<bool>(v20305)) return v20305; v20305 = ([&]() -> Value { auto v20316 = Get(Get(s->LocalAt(6), s->LocalAt(4)), Value(int64_t{1})); Value v20317; v20317 = s->Global("_E334_ITEMS"); if (!static_cast<bool>(Binary("In", v20316, v20317))) return Value(false); v20316 = v20317; return Value(true); }()); return v20305; }()))) {
auto v20318 = s->LocalAt(4);
s->SetAt(4, Inplace("Add", v20318, Value(int64_t{1})));
}
if (static_cast<bool>(([&]() -> Value { auto v20319 = ([&]() -> Value { auto v20321 = s->LocalAt(4); return Binary("Sub", v20321, s->LocalAt(3)); }()); Value v20320; v20320 = Value(int64_t{2}); if (!static_cast<bool>(Binary("GtE", v20319, v20320))) return Value(false); v20319 = v20320; return Value(true); }()))) {
(void)([&]() -> Value { auto fn20322 = Attribute(s->LocalAt(18), "append"); Arguments args20323; args20323.Add(Tuple({s->LocalAt(3), s->LocalAt(4)}), false); return Call(c, fn20322, std::move(args20323)); }());
}
auto v20324 = s->LocalAt(4);
s->SetAt(3, v20324);
}
else {
auto v20325 = s->LocalAt(3);
s->SetAt(3, Inplace("Add", v20325, Value(int64_t{1})));
}
}
if (static_cast<bool>(Unary("Not", s->LocalAt(18)))) {
return s->LocalAt(1);
}
auto v20326 = ([&]() -> Value { auto fn20327 = s->Global("_r127_fields"); Arguments args20328; args20328.positional.reserve(2); args20328.Add(s->LocalAt(9), false); args20328.Add(s->LocalAt(1), false); return Call(c, fn20327, std::move(args20328)); }());
auto unpack20329 = Iterate(v20326);
ValidateUnpack(unpack20329, 2, false);
s->SetAt(0, unpack20329.at(0));
s->SetAt(12, unpack20329.at(1));
auto v20330 = ([&]() -> Value { auto fn20331 = s->Global("dict"); Arguments args20332; args20332.Add(Get(s->LocalAt(12), Value("shed")), false); return Call(c, fn20331, std::move(args20332)); }());
s->SetAt(15, v20330);
auto v20333 = ([&]() -> Value { auto comp20334 = std::make_shared<Scope>(); comp20334->globals = s->globals; comp20334->parent = s; static constexpr const char* comp20334_names[] = {"o"}; comp20334->PrepareSlots(comp20334_names); auto result20335 = List(); for (const auto& item20336 : Iterate(s->LocalAt(6))) { comp20334->SetAt(0, item20336); result20335.node()->sequence.push_back(([&]() -> Value { auto fn20337 = comp20334->Global("list"); Arguments args20338; args20338.Add(comp20334->LocalAt(0), false); return Call(c, fn20337, std::move(args20338)); }())); } return result20335; }());
s->SetAt(7, v20333);
auto v20339 = Value(int64_t{0});
s->SetAt(16, v20339);
for (const auto& item20340 : Iterate(s->LocalAt(18))) {
auto unpack20341 = Iterate(item20340);
ValidateUnpack(unpack20341, 2, false);
s->SetAt(19, unpack20341.at(0));
s->SetAt(2, unpack20341.at(1));
auto v20342 = ([&]() -> Value { auto dict20343 = Dict(); return dict20343; }());
s->SetAt(14, v20342);
auto v20344 = List({});
s->SetAt(10, v20344);
for (const auto& item20345 : Iterate(Slice(s->LocalAt(6), s->LocalAt(19), s->LocalAt(2), Value{}))) {
s->SetAt(8, item20345);
auto v20346 = Get(s->LocalAt(8), Value(int64_t{1}));
s->SetAt(11, v20346);
if (static_cast<bool>(([&]() -> Value { auto v20347 = s->LocalAt(11); Value v20348; v20348 = s->LocalAt(14); if (!static_cast<bool>(Binary("NotIn", v20347, v20348))) return Value(false); v20347 = v20348; return Value(true); }()))) {
(void)([&]() -> Value { auto fn20349 = Attribute(s->LocalAt(10), "append"); Arguments args20350; args20350.Add(s->LocalAt(11), false); return Call(c, fn20349, std::move(args20350)); }());
auto v20351 = Value(int64_t{0});
Put(s->LocalAt(14), s->LocalAt(11), v20351);
}
auto v20352 = s->LocalAt(14);
auto v20353 = s->LocalAt(11);
auto v20354 = Get(v20352, v20353);
Put(v20352, v20353, Inplace("Add", v20354, ([&]() -> Value { auto fn20355 = s->Global("max"); Arguments args20356; args20356.positional.reserve(2); args20356.Add(Value(int64_t{0}), false); args20356.Add(([&]() -> Value { auto fn20357 = s->Global("int"); Arguments args20358; args20358.Add(Get(s->LocalAt(8), Value(int64_t{2})), false); return Call(c, fn20357, std::move(args20358)); }()), false); return Call(c, fn20355, std::move(args20356)); }())));
}
auto v20359 = List({});
s->SetAt(5, v20359);
for (const auto& item20360 : Iterate(s->LocalAt(10))) {
s->SetAt(11, item20360);
auto v20361 = ([&]() -> Value { auto fn20362 = s->Global("min"); Arguments args20363; args20363.positional.reserve(2); args20363.Add(Get(s->LocalAt(14), s->LocalAt(11)), false); args20363.Add(([&]() -> Value { auto fn20364 = s->Global("max"); Arguments args20365; args20365.positional.reserve(2); args20365.Add(Value(int64_t{0}), false); args20365.Add(([&]() -> Value { auto fn20366 = s->Global("int"); Arguments args20367; args20367.Add(([&]() -> Value { auto fn20368 = PrepareDictionaryGet(s->LocalAt(15)); Arguments args20369; args20369.positional.reserve(2); args20369.Add(s->LocalAt(11), false); args20369.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn20368, std::move(args20369)); }()), false); return Call(c, fn20366, std::move(args20367)); }()), false); return Call(c, fn20364, std::move(args20365)); }()), false); return Call(c, fn20362, std::move(args20363)); }());
s->SetAt(13, v20361);
if (static_cast<bool>(s->LocalAt(13))) {
(void)([&]() -> Value { auto fn20370 = Attribute(s->LocalAt(5), "append"); Arguments args20371; args20371.Add(List({Value("SELL"), s->LocalAt(11), s->LocalAt(13)}), false); return Call(c, fn20370, std::move(args20371)); }());
auto v20372 = s->LocalAt(15);
auto v20373 = s->LocalAt(11);
auto v20374 = Get(v20372, v20373);
Put(v20372, v20373, Inplace("Sub", v20374, s->LocalAt(13)));
}
}
auto v20375 = ([&]() -> Value { auto v20376 = s->LocalAt(5); return Binary("Add", v20376, ([&]() -> Value { auto comp20377 = std::make_shared<Scope>(); comp20377->globals = s->globals; comp20377->parent = s; static constexpr const char* comp20377_names[] = {"_"}; comp20377->PrepareSlots(comp20377_names); auto result20378 = List(); for (const auto& item20379 : Iterate(([&]() -> Value { auto fn20380 = s->Global("range"); Arguments args20381; args20381.Add(([&]() -> Value { auto v20382 = ([&]() -> Value { auto v20383 = s->LocalAt(2); return Binary("Sub", v20383, s->LocalAt(19)); }()); return Binary("Sub", v20382, ([&]() -> Value { auto fn20384 = s->Global("len"); Arguments args20385; args20385.Add(s->LocalAt(5), false); return Call(c, fn20384, std::move(args20385)); }())); }()), false); return Call(c, fn20380, std::move(args20381)); }()))) { comp20377->SetAt(0, item20379); result20378.node()->sequence.push_back(List({})); } return result20378; }())); }());
s->SetAt(17, v20375);
if (static_cast<bool>(([&]() -> Value { auto v20386 = s->LocalAt(17); Value v20387; v20387 = Slice(s->LocalAt(6), s->LocalAt(19), s->LocalAt(2), Value{}); if (!static_cast<bool>(Binary("NotEq", v20386, v20387))) return Value(false); v20386 = v20387; return Value(true); }()))) {
auto v20388 = s->LocalAt(16);
s->SetAt(16, Inplace("Add", v20388, ([&]() -> Value { auto v20389 = ([&]() -> Value { auto v20390 = s->LocalAt(2); return Binary("Sub", v20390, s->LocalAt(19)); }()); return Binary("Sub", v20389, ([&]() -> Value { auto fn20391 = s->Global("len"); Arguments args20392; args20392.Add(s->LocalAt(5), false); return Call(c, fn20391, std::move(args20392)); }())); }())));
auto v20393 = s->LocalAt(17);
PutSlice(s->LocalAt(7), s->LocalAt(19), s->LocalAt(2), Value{}, v20393);
}
}
if (static_cast<bool>(([&]() -> Value { auto v20394 = s->LocalAt(7); Value v20395; v20395 = s->LocalAt(6); if (!static_cast<bool>(Binary("Eq", v20394, v20395))) return Value(false); v20394 = v20395; return Value(true); }()))) {
return s->LocalAt(1);
}
auto v20396 = s->Global("_E334_REPORT");
auto v20397 = Value("changed");
auto v20398 = Get(v20396, v20397);
Put(v20396, v20397, Inplace("Add", v20398, Value(int64_t{1})));
auto v20399 = s->Global("_E334_REPORT");
auto v20400 = Value("removed");
auto v20401 = Get(v20399, v20400);
Put(v20399, v20400, Inplace("Add", v20401, s->LocalAt(16)));
return ([&]() -> Value { auto fn20402 = s->Global("dict"); Arguments args20403; args20403.Add(s->LocalAt(1), false); args20403.Keyword("market", s->LocalAt(7)); return Call(c, fn20402, std::move(args20403)); }());
return {};
}
}  // namespace kagg::opponents::compiled
