// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_403c8f8a6bada6d3e6f5(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"committed", "guard", "i", "inv", "inv0", "item", "n", "o", "op", "orders_me", "orders_opp", "p", "params", "price", "q", "queues", "quoted", "r", "rem", "rev", "stock", "stock_me", "stock_opp"};
s->PrepareSlots(s_names);
auto v19209 = ([&]() -> Value { auto fn19210 = s->Global("dict"); Arguments args19211; args19211.Add(s->LocalAt(4), false); return Call(c, fn19210, std::move(args19211)); }());
s->SetAt(3, v19209);
auto v19212 = List({([&]() -> Value { auto fn19213 = s->Global("dict"); Arguments args19214; args19214.Add(s->LocalAt(21), false); return Call(c, fn19213, std::move(args19214)); }()), ([&]() -> Value { auto fn19215 = s->Global("dict"); Arguments args19216; args19216.Add(s->LocalAt(22), false); return Call(c, fn19215, std::move(args19216)); }())});
s->SetAt(20, v19212);
auto v19217 = List({Value(0.0), Value(0.0)});
s->SetAt(19, v19217);
auto v19218 = List({([&]() -> Value { auto fn19219 = s->Global("list"); Arguments args19220; args19220.Add(s->LocalAt(9), false); return Call(c, fn19219, std::move(args19220)); }()), ([&]() -> Value { auto fn19221 = s->Global("list"); Arguments args19222; args19222.Add(s->LocalAt(10), false); return Call(c, fn19221, std::move(args19222)); }())});
s->SetAt(15, v19218);
for (const auto& item19223 : Iterate(([&]() -> Value { auto fn19224 = s->Global("range"); Arguments args19225; args19225.Add(([&]() -> Value { auto fn19226 = s->Global("max"); Arguments args19227; args19227.positional.reserve(2); args19227.Add(([&]() -> Value { auto fn19228 = s->Global("len"); Arguments args19229; args19229.Add(Get(s->LocalAt(15), Value(int64_t{0})), false); return Call(c, fn19228, std::move(args19229)); }()), false); args19227.Add(([&]() -> Value { auto fn19230 = s->Global("len"); Arguments args19231; args19231.Add(Get(s->LocalAt(15), Value(int64_t{1})), false); return Call(c, fn19230, std::move(args19231)); }()), false); return Call(c, fn19226, std::move(args19227)); }()), false); return Call(c, fn19224, std::move(args19225)); }()))) {
s->SetAt(2, item19223);
auto v19232 = List({Value{}, Value{}});
s->SetAt(18, v19232);
for (const auto& item19233 : Iterate(Tuple({Value(int64_t{0}), Value(int64_t{1})}))) {
s->SetAt(11, item19233);
if (static_cast<bool>(([&]() -> Value { auto v19234 = s->LocalAt(2); Value v19235; v19235 = ([&]() -> Value { auto fn19236 = s->Global("len"); Arguments args19237; args19237.Add(Get(s->LocalAt(15), s->LocalAt(11)), false); return Call(c, fn19236, std::move(args19237)); }()); if (!static_cast<bool>(Binary("Lt", v19234, v19235))) return Value(false); v19234 = v19235; return Value(true); }()))) {
auto v19238 = Get(Get(s->LocalAt(15), s->LocalAt(11)), s->LocalAt(2));
s->SetAt(7, v19238);
if (static_cast<bool>(([&]() -> Value { auto v19239 = s->LocalAt(7); if (!static_cast<bool>(v19239)) return v19239; v19239 = ([&]() -> Value { auto v19240 = ([&]() -> Value { auto fn19242 = s->Global("len"); Arguments args19243; args19243.Add(s->LocalAt(7), false); return Call(c, fn19242, std::move(args19243)); }()); Value v19241; v19241 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v19240, v19241))) return Value(false); v19240 = v19241; return Value(true); }()); if (!static_cast<bool>(v19239)) return v19239; v19239 = ([&]() -> Value { auto v19244 = Get(s->LocalAt(7), Value(int64_t{0})); Value v19245; v19245 = Tuple({Value("SELL"), Value("BUY_PRODUCT")}); if (!static_cast<bool>(Binary("In", v19244, v19245))) return Value(false); v19244 = v19245; return Value(true); }()); if (!static_cast<bool>(v19239)) return v19239; v19239 = ([&]() -> Value { auto v19246 = Get(s->LocalAt(7), Value(int64_t{1})); Value v19247; v19247 = s->LocalAt(12); if (!static_cast<bool>(Binary("In", v19246, v19247))) return Value(false); v19246 = v19247; return Value(true); }()); return v19239; }()))) {
try {
auto v19249 = ([&]() -> Value { auto fn19250 = s->Global("int"); Arguments args19251; args19251.Add(Get(s->LocalAt(7), Value(int64_t{2})), false); return Call(c, fn19250, std::move(args19251)); }());
s->SetAt(6, v19249);
} catch (const Error& error19248) {
if (Matches(error19248, s->Global("Exception"))) {
auto v19252 = Value(int64_t{0});
s->SetAt(6, v19252);
}
else { throw; }
}
if (static_cast<bool>(([&]() -> Value { auto v19253 = s->LocalAt(6); Value v19254; v19254 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v19253, v19254))) return Value(false); v19253 = v19254; return Value(true); }()))) {
auto v19255 = List({Get(s->LocalAt(7), Value(int64_t{0})), Get(s->LocalAt(7), Value(int64_t{1})), s->LocalAt(6)});
Put(s->LocalAt(18), s->LocalAt(11), v19255);
}
}
}
}
auto v19256 = Value(int64_t{0});
s->SetAt(1, v19256);
while (static_cast<bool>(Value(true))) {
auto v19257 = s->LocalAt(1);
s->SetAt(1, Inplace("Add", v19257, Value(int64_t{1})));
if (static_cast<bool>(([&]() -> Value { auto v19258 = s->LocalAt(1); Value v19259; v19259 = Value(int64_t{5000}); if (!static_cast<bool>(Binary("Gt", v19258, v19259))) return Value(false); v19258 = v19259; return Value(true); }()))) {
break;
}
auto v19260 = List({Value{}, Value{}});
s->SetAt(16, v19260);
for (const auto& item19261 : Iterate(Tuple({Value(int64_t{0}), Value(int64_t{1})}))) {
s->SetAt(11, item19261);
auto v19262 = Get(s->LocalAt(18), s->LocalAt(11));
s->SetAt(17, v19262);
if (static_cast<bool>(([&]() -> Value { auto v19263 = ([&]() -> Value { auto v19264 = s->LocalAt(17); Value v19265; v19265 = Value{}; if (!static_cast<bool>(Binary("Is", v19264, v19265))) return Value(false); v19264 = v19265; return Value(true); }()); if (static_cast<bool>(v19263)) return v19263; v19263 = ([&]() -> Value { auto v19266 = Get(s->LocalAt(17), Value(int64_t{2})); Value v19267; v19267 = Value(int64_t{0}); if (!static_cast<bool>(Binary("LtE", v19266, v19267))) return Value(false); v19266 = v19267; return Value(true); }()); return v19263; }()))) {
continue;
}
if (static_cast<bool>(([&]() -> Value { auto v19268 = Get(s->LocalAt(17), Value(int64_t{0})); Value v19269; v19269 = Value("SELL"); if (!static_cast<bool>(Binary("Eq", v19268, v19269))) return Value(false); v19268 = v19269; return Value(true); }()))) {
auto v19270 = Tuple({Value("SELL"), Get(s->LocalAt(17), Value(int64_t{1})), ([&]() -> Value { auto fn19271 = s->Global("_v44y_price"); Arguments args19272; args19272.positional.reserve(3); args19272.Add(Get(s->LocalAt(17), Value(int64_t{1})), false); args19272.Add(Get(s->LocalAt(3), Get(s->LocalAt(17), Value(int64_t{1}))), false); args19272.Add(s->LocalAt(12), false); return Call(c, fn19271, std::move(args19272)); }())});
Put(s->LocalAt(16), s->LocalAt(11), v19270);
}
else {
if (static_cast<bool>(([&]() -> Value { auto v19273 = Get(s->LocalAt(17), Value(int64_t{1})); Value v19274; v19274 = Tuple({Value("WHEAT"), Value("FERTILIZER")}); if (!static_cast<bool>(Binary("In", v19273, v19274))) return Value(false); v19273 = v19274; return Value(true); }()))) {
auto v19275 = Tuple({Value("BUY_PRODUCT"), Get(s->LocalAt(17), Value(int64_t{1})), ([&]() -> Value { auto fn19276 = s->Global("_v44y_price"); Arguments args19277; args19277.positional.reserve(3); args19277.Add(Get(s->LocalAt(17), Value(int64_t{1})), false); args19277.Add(([&]() -> Value { auto v19278 = Get(s->LocalAt(3), Get(s->LocalAt(17), Value(int64_t{1}))); return Binary("Sub", v19278, Value(int64_t{1})); }()), false); args19277.Add(s->LocalAt(12), false); return Call(c, fn19276, std::move(args19277)); }())});
Put(s->LocalAt(16), s->LocalAt(11), v19275);
}
else {
auto v19279 = Value{};
Put(s->LocalAt(18), s->LocalAt(11), v19279);
}
}
}
if (static_cast<bool>(([&]() -> Value { auto v19280 = ([&]() -> Value { auto v19281 = Get(s->LocalAt(16), Value(int64_t{0})); Value v19282; v19282 = Value{}; if (!static_cast<bool>(Binary("Is", v19281, v19282))) return Value(false); v19281 = v19282; return Value(true); }()); if (!static_cast<bool>(v19280)) return v19280; v19280 = ([&]() -> Value { auto v19283 = Get(s->LocalAt(16), Value(int64_t{1})); Value v19284; v19284 = Value{}; if (!static_cast<bool>(Binary("Is", v19283, v19284))) return Value(false); v19283 = v19284; return Value(true); }()); return v19280; }()))) {
break;
}
auto v19285 = Value(false);
s->SetAt(0, v19285);
for (const auto& item19286 : Iterate(Tuple({Value(int64_t{0}), Value(int64_t{1})}))) {
s->SetAt(11, item19286);
auto v19287 = Get(s->LocalAt(16), s->LocalAt(11));
s->SetAt(14, v19287);
if (static_cast<bool>(([&]() -> Value { auto v19288 = s->LocalAt(14); Value v19289; v19289 = Value{}; if (!static_cast<bool>(Binary("Is", v19288, v19289))) return Value(false); v19288 = v19289; return Value(true); }()))) {
continue;
}
auto v19290 = s->LocalAt(14);
auto unpack19291 = Iterate(v19290);
ValidateUnpack(unpack19291, 3, false);
s->SetAt(8, unpack19291.at(0));
s->SetAt(5, unpack19291.at(1));
s->SetAt(13, unpack19291.at(2));
if (static_cast<bool>(([&]() -> Value { auto v19292 = s->LocalAt(8); Value v19293; v19293 = Value("SELL"); if (!static_cast<bool>(Binary("Eq", v19292, v19293))) return Value(false); v19292 = v19293; return Value(true); }()))) {
if (static_cast<bool>(([&]() -> Value { auto v19294 = ([&]() -> Value { auto fn19296 = PrepareDictionaryGet(Get(s->LocalAt(20), s->LocalAt(11))); Arguments args19297; args19297.positional.reserve(2); args19297.Add(s->LocalAt(5), false); args19297.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn19296, std::move(args19297)); }()); Value v19295; v19295 = Value(int64_t{0}); if (!static_cast<bool>(Binary("LtE", v19294, v19295))) return Value(false); v19294 = v19295; return Value(true); }()))) {
auto v19298 = Value{};
Put(s->LocalAt(18), s->LocalAt(11), v19298);
continue;
}
auto v19299 = Get(s->LocalAt(20), s->LocalAt(11));
auto v19300 = s->LocalAt(5);
auto v19301 = Get(v19299, v19300);
Put(v19299, v19300, Inplace("Sub", v19301, Value(int64_t{1})));
auto v19302 = s->LocalAt(19);
auto v19303 = s->LocalAt(11);
auto v19304 = Get(v19302, v19303);
Put(v19302, v19303, Inplace("Add", v19304, s->LocalAt(13)));
if (static_cast<bool>(([&]() -> Value { auto v19305 = s->LocalAt(13); Value v19306; v19306 = Value(int64_t{1}); if (!static_cast<bool>(Binary("Gt", v19305, v19306))) return Value(false); v19305 = v19306; return Value(true); }()))) {
auto v19307 = s->LocalAt(3);
auto v19308 = s->LocalAt(5);
auto v19309 = Get(v19307, v19308);
Put(v19307, v19308, Inplace("Add", v19309, Value(int64_t{1})));
}
}
else {
auto v19310 = ([&]() -> Value { auto v19311 = ([&]() -> Value { auto fn19312 = PrepareDictionaryGet(Get(s->LocalAt(20), s->LocalAt(11))); Arguments args19313; args19313.positional.reserve(2); args19313.Add(s->LocalAt(5), false); args19313.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn19312, std::move(args19313)); }()); return Binary("Add", v19311, Value(int64_t{1})); }());
Put(Get(s->LocalAt(20), s->LocalAt(11)), s->LocalAt(5), v19310);
auto v19314 = s->LocalAt(19);
auto v19315 = s->LocalAt(11);
auto v19316 = Get(v19314, v19315);
Put(v19314, v19315, Inplace("Sub", v19316, s->LocalAt(13)));
auto v19317 = s->LocalAt(3);
auto v19318 = s->LocalAt(5);
auto v19319 = Get(v19317, v19318);
Put(v19317, v19318, Inplace("Sub", v19319, Value(int64_t{1})));
}
auto v19320 = Get(s->LocalAt(18), s->LocalAt(11));
auto v19321 = Value(int64_t{2});
auto v19322 = Get(v19320, v19321);
Put(v19320, v19321, Inplace("Sub", v19322, Value(int64_t{1})));
auto v19323 = Value(true);
s->SetAt(0, v19323);
}
if (static_cast<bool>(Unary("Not", s->LocalAt(0)))) {
break;
}
}
}
return Tuple({Get(s->LocalAt(19), Value(int64_t{0})), Get(s->LocalAt(19), Value(int64_t{1}))});
return {};
}
}  // namespace kagg::opponents::compiled
