// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_f0ecfc6d5cb8e5937e33(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "configuration", "market", "observation", "standard", "step"};
s->PrepareSlots(s_names);
auto v13238 = ([&]() -> Value { auto fn13239 = s->Global("_OPEN_PARENT"); Arguments args13240; args13240.positional.reserve(2); args13240.Add(s->LocalAt(3), false); args13240.Add(s->LocalAt(1), false); return Call(c, fn13239, std::move(args13240)); }());
s->SetAt(0, v13238);
try {
auto v13242 = ([&]() -> Value { auto fn13243 = s->Global("int"); Arguments args13244; args13244.Add(Get(s->LocalAt(3), Value("step")), false); return Call(c, fn13243, std::move(args13244)); }());
s->SetAt(5, v13242);
if (static_cast<bool>(([&]() -> Value { auto v13245 = s->LocalAt(5); Value v13246; v13246 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v13245, v13246))) return Value(false); v13245 = v13246; return Value(true); }()))) {
(void)([&]() -> Value { auto fn13247 = Attribute(s->Global("_OPEN_REPORT"), "update"); Arguments args13248; args13248.Keyword("open_turns", Value(int64_t{0})); args13248.Keyword("open_errors", Value(int64_t{0})); return Call(c, fn13247, std::move(args13248)); }());
}
auto v13249 = ([&]() -> Value { auto v13250 = ([&]() -> Value { auto v13251 = s->LocalAt(1); Value v13252; v13252 = Value{}; if (!static_cast<bool>(Binary("Is", v13251, v13252))) return Value(false); v13251 = v13252; return Value(true); }()); if (static_cast<bool>(v13250)) return v13250; v13250 = ([&]() -> Value { auto comp13253 = std::make_shared<Scope>(); comp13253->globals = s->globals; comp13253->parent = s; static constexpr const char* comp13253_names[] = {"k", "v"}; comp13253->PrepareSlots(comp13253_names); auto result13254 = List(); for (const auto& item13255 : Iterate(List({Tuple({Value("boardSize"), Value(int64_t{10})}), Tuple({Value("turnsPerDay"), Value(int64_t{24})}), Tuple({Value("shedCapacity"), Value(int64_t{100})}), Tuple({Value("maxMarketOrdersPerTurn"), Value(int64_t{10})}), Tuple({Value("startingMoney"), Value(int64_t{3000})})}))) { auto unpack13256 = Iterate(item13255); ValidateUnpack(unpack13256, 2, false); comp13253->SetAt(0, unpack13256.at(0)); comp13253->SetAt(1, unpack13256.at(1)); if (!static_cast<bool>(([&]() -> Value { auto v13257 = ([&]() -> Value { auto fn13259 = PrepareDictionaryGet(comp13253->Captured("configuration")); Arguments args13260; args13260.positional.reserve(2); args13260.Add(comp13253->LocalAt(0), false); args13260.Add(comp13253->LocalAt(1), false); return CallDictionaryGet(c, fn13259, std::move(args13260)); }()); Value v13258; v13258 = comp13253->LocalAt(1); if (!static_cast<bool>(Binary("Eq", v13257, v13258))) return Value(false); v13257 = v13258; return Value(true); }()))) return Value(false); } return Value(true); }()); return v13250; }());
s->SetAt(4, v13249);
if (static_cast<bool>(([&]() -> Value { auto v13261 = s->LocalAt(4); if (!static_cast<bool>(v13261)) return v13261; v13261 = ([&]() -> Value { auto v13262 = s->LocalAt(5); Value v13263; v13263 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v13262, v13263))) return Value(false); v13262 = v13263; return Value(true); }()); if (!static_cast<bool>(v13261)) return v13261; v13261 = ([&]() -> Value { auto v13264 = ([&]() -> Value { auto fn13266 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args13267; args13267.Add(Value("market"), false); return CallDictionaryGet(c, fn13266, std::move(args13267)); }()); Value v13265; v13265 = List({List({Value("BUY_PRODUCT"), Value("WHEAT"), Value(int64_t{5})}), List({Value("BUY_PRODUCT"), Value("WHEAT"), Value(int64_t{10})}), List({Value("SELL"), Value("WHEAT"), Value(int64_t{60})})}); if (!static_cast<bool>(Binary("Eq", v13264, v13265))) return Value(false); v13264 = v13265; return Value(true); }()); return v13261; }()))) {
auto v13268 = ([&]() -> Value { auto fn13269 = s->Global("dict"); Arguments args13270; args13270.Add(s->LocalAt(0), false); args13270.Keyword("market", List({List({Value("BUY_PRODUCT"), Value("WHEAT"), s->Global("_OPEN_UNITS")}), List({Value("SELL"), Value("WHEAT"), s->Global("_OPEN_UNITS")})})); return Call(c, fn13269, std::move(args13270)); }());
s->SetAt(0, v13268);
auto v13271 = s->Global("_OPEN_REPORT");
auto v13272 = Value("open_turns");
auto v13273 = Get(v13271, v13272);
Put(v13271, v13272, Inplace("Add", v13273, Value(int64_t{1})));
}
else {
if (static_cast<bool>(([&]() -> Value { auto v13274 = s->LocalAt(4); if (!static_cast<bool>(v13274)) return v13274; v13274 = ([&]() -> Value { auto v13275 = s->LocalAt(5); Value v13276; v13276 = Value(int64_t{1}); if (!static_cast<bool>(Binary("Eq", v13275, v13276))) return Value(false); v13275 = v13276; return Value(true); }()); if (!static_cast<bool>(v13274)) return v13274; v13274 = ([&]() -> Value { auto v13277 = s->Global("_OPEN_FEED_STEP1"); Value v13278; v13278 = Value(int64_t{5}); if (!static_cast<bool>(Binary("Lt", v13277, v13278))) return Value(false); v13277 = v13278; return Value(true); }()); return v13274; }()))) {
auto v13279 = ([&]() -> Value { auto comp13280 = std::make_shared<Scope>(); comp13280->globals = s->globals; comp13280->parent = s; static constexpr const char* comp13280_names[] = {"o"}; comp13280->PrepareSlots(comp13280_names); auto result13281 = List(); for (const auto& item13282 : Iterate(([&]() -> Value { auto fn13283 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args13284; args13284.positional.reserve(2); args13284.Add(Value("market"), false); args13284.Add(List({}), false); return CallDictionaryGet(c, fn13283, std::move(args13284)); }()))) { comp13280->SetAt(0, item13282); result13281.node()->sequence.push_back(([&]() -> Value { auto fn13285 = comp13280->Global("list"); Arguments args13286; args13286.Add(comp13280->LocalAt(0), false); return Call(c, fn13285, std::move(args13286)); }())); } return result13281; }());
s->SetAt(2, v13279);
if (static_cast<bool>(([&]() -> Value { auto v13287 = ([&]() -> Value { auto v13288 = ([&]() -> Value { auto fn13290 = s->Global("len"); Arguments args13291; args13291.Add(s->LocalAt(2), false); return Call(c, fn13290, std::move(args13291)); }()); Value v13289; v13289 = Value(int64_t{2}); if (!static_cast<bool>(Binary("GtE", v13288, v13289))) return Value(false); v13288 = v13289; return Value(true); }()); if (!static_cast<bool>(v13287)) return v13287; v13287 = ([&]() -> Value { auto v13292 = Get(s->LocalAt(2), Value(int64_t{0})); Value v13293; v13293 = List({Value("SELL"), Value("WHEAT"), Value(int64_t{13})}); if (!static_cast<bool>(Binary("Eq", v13292, v13293))) return Value(false); v13292 = v13293; return Value(true); }()); if (!static_cast<bool>(v13287)) return v13287; v13287 = ([&]() -> Value { auto v13294 = Get(s->LocalAt(2), Value(int64_t{1})); Value v13295; v13295 = List({Value("BUY_PRODUCT"), Value("WHEAT"), Value(int64_t{5})}); if (!static_cast<bool>(Binary("Eq", v13294, v13295))) return Value(false); v13294 = v13295; return Value(true); }()); return v13287; }()))) {
auto v13296 = List({Value("BUY_PRODUCT"), Value("WHEAT"), s->Global("_OPEN_FEED_STEP1")});
Put(s->LocalAt(2), Value(int64_t{1}), v13296);
auto v13297 = ([&]() -> Value { auto fn13298 = s->Global("dict"); Arguments args13299; args13299.Add(s->LocalAt(0), false); args13299.Keyword("market", s->LocalAt(2)); return Call(c, fn13298, std::move(args13299)); }());
s->SetAt(0, v13297);
auto v13300 = s->Global("_OPEN_REPORT");
auto v13301 = Value("open_turns");
auto v13302 = Get(v13300, v13301);
Put(v13300, v13301, Inplace("Add", v13302, Value(int64_t{1})));
}
}
}
} catch (const Error& error13241) {
if (Matches(error13241, s->Global("Exception"))) {
auto v13303 = s->Global("_OPEN_REPORT");
auto v13304 = Value("open_errors");
auto v13305 = Get(v13303, v13304);
Put(v13303, v13304, Inplace("Add", v13305, Value(int64_t{1})));
}
else { throw; }
}
(void)([&]() -> Value { auto fn13306 = Attribute(s->Global("_OPEN_REPORT"), "update"); Arguments args13307; args13307.Add(([&]() -> Value { auto fn13308 = s->Global("getattr"); Arguments args13309; args13309.positional.reserve(3); args13309.Add(s->Global("_OPEN_PARENT"), false); args13309.Add(Value("telemetry"), false); args13309.Add(([&]() -> Value { auto dict13310 = Dict(); return dict13310; }()), false); return Call(c, fn13308, std::move(args13309)); }()), false); return Call(c, fn13306, std::move(args13307)); }());
return s->LocalAt(0);
return {};
}
}  // namespace kagg::opponents::compiled
