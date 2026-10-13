// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_33cf1e95c87cc8c1b9ff(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "actor", "command", "commands", "configuration", "count", "day", "farm", "funded", "gained", "i", "item", "observation", "pending", "player", "previous", "private", "result", "scheduled", "state", "step", "stock", "targets"};
s->PrepareSlots(s_names);
auto v7224 = ([&]() -> Value { auto fn7225 = s->Global("_V233_PARENT"); Arguments args7226; args7226.positional.reserve(2); args7226.Add(s->LocalAt(12), false); args7226.Add(s->LocalAt(4), false); return Call(c, fn7225, std::move(args7226)); }());
s->SetAt(0, v7224);
auto v7227 = ([&]() -> Value { auto fn7228 = s->Global("int"); Arguments args7229; args7229.Add(Get(s->LocalAt(12), Value("step")), false); return Call(c, fn7228, std::move(args7229)); }());
s->SetAt(20, v7227);
auto v7230 = ([&]() -> Value { auto fn7231 = s->Global("int"); Arguments args7232; args7232.Add(Get(s->LocalAt(12), Value("player")), false); return Call(c, fn7231, std::move(args7232)); }());
s->SetAt(14, v7230);
auto v7233 = ([&]() -> Value { auto v7234 = s->LocalAt(20); return Binary("FloorDiv", v7234, Value(int64_t{24})); }());
s->SetAt(6, v7233);
auto v7235 = ([&]() -> Value { auto fn7236 = PrepareDictionaryGet(s->Global("_V233_STATES")); Arguments args7237; args7237.Add(s->LocalAt(14), false); return CallDictionaryGet(c, fn7236, std::move(args7237)); }());
s->SetAt(19, v7235);
if (static_cast<bool>(([&]() -> Value { auto v7238 = ([&]() -> Value { auto v7239 = s->LocalAt(19); Value v7240; v7240 = Value{}; if (!static_cast<bool>(Binary("Is", v7239, v7240))) return Value(false); v7239 = v7240; return Value(true); }()); if (static_cast<bool>(v7238)) return v7238; v7238 = ([&]() -> Value { auto v7241 = s->LocalAt(20); Value v7242; v7242 = Get(s->LocalAt(19), Value("last_step")); if (!static_cast<bool>(Binary("LtE", v7241, v7242))) return Value(false); v7241 = v7242; return Value(true); }()); return v7238; }()))) {
auto v7243 = ([&]() -> Value { auto dict7244 = Dict(); auto key7245 = Value("last_step"); Put(dict7244, key7245, s->LocalAt(20)); auto key7246 = Value("day"); Put(dict7244, key7246, Unary("USub", Value(int64_t{1}))); auto key7247 = Value("workers"); Put(dict7244, key7247, ([&]() -> Value { auto dict7248 = Dict(); return dict7248; }())); auto key7249 = Value("work"); Put(dict7244, key7249, ([&]() -> Value { auto dict7250 = Dict(); return dict7250; }())); auto key7251 = Value("credit"); Put(dict7244, key7251, ([&]() -> Value { auto dict7252 = Dict(); auto key7253 = Value("WOOL"); Put(dict7252, key7253, Value(int64_t{0})); auto key7254 = Value("FERTILIZER"); Put(dict7252, key7254, Value(int64_t{0})); return dict7252; }())); return dict7244; }());
s->SetAt(19, v7243);
auto v7255 = s->LocalAt(19);
Put(s->Global("_V233_STATES"), s->LocalAt(14), v7255);
}
auto v7256 = s->LocalAt(20);
Put(s->LocalAt(19), Value("last_step"), v7256);
if (static_cast<bool>(([&]() -> Value { auto v7257 = ([&]() -> Value { auto v7258 = s->LocalAt(4); Value v7259; v7259 = Value{}; if (!static_cast<bool>(Binary("IsNot", v7258, v7259))) return Value(false); v7258 = v7259; return Value(true); }()); if (!static_cast<bool>(v7257)) return v7257; v7257 = ([&]() -> Value { auto comp7260 = std::make_shared<Scope>(); comp7260->globals = s->globals; comp7260->parent = s; static constexpr const char* comp7260_names[] = {"k", "v"}; comp7260->PrepareSlots(comp7260_names); auto result7261 = List(); for (const auto& item7262 : Iterate(Tuple({Tuple({Value("boardSize"), Value(int64_t{10})}), Tuple({Value("turnsPerDay"), Value(int64_t{24})}), Tuple({Value("shedCapacity"), Value(int64_t{100})}), Tuple({Value("maxMarketOrdersPerTurn"), Value(int64_t{10})})}))) { auto unpack7263 = Iterate(item7262); ValidateUnpack(unpack7263, 2, false); comp7260->SetAt(0, unpack7263.at(0)); comp7260->SetAt(1, unpack7263.at(1)); if (static_cast<bool>(([&]() -> Value { auto v7264 = ([&]() -> Value { auto fn7266 = PrepareDictionaryGet(comp7260->Captured("configuration")); Arguments args7267; args7267.positional.reserve(2); args7267.Add(comp7260->LocalAt(0), false); args7267.Add(comp7260->LocalAt(1), false); return CallDictionaryGet(c, fn7266, std::move(args7267)); }()); Value v7265; v7265 = comp7260->LocalAt(1); if (!static_cast<bool>(Binary("NotEq", v7264, v7265))) return Value(false); v7264 = v7265; return Value(true); }()))) return Value(true); } return Value(false); }()); return v7257; }()))) {
return s->LocalAt(0);
}
if (static_cast<bool>(([&]() -> Value { auto v7268 = s->LocalAt(6); Value v7269; v7269 = Value(int64_t{12}); if (!static_cast<bool>(Binary("Lt", v7268, v7269))) return Value(false); v7268 = v7269; return Value(true); }()))) {
return s->LocalAt(0);
}
auto v7270 = Get(Get(s->LocalAt(12), Value("farms")), s->LocalAt(14));
s->SetAt(7, v7270);
auto v7271 = Get(s->LocalAt(12), Value("private"));
s->SetAt(16, v7271);
if (static_cast<bool>(([&]() -> Value { auto v7272 = Get(s->LocalAt(19), Value("day")); Value v7273; v7273 = s->LocalAt(6); if (!static_cast<bool>(Binary("NotEq", v7272, v7273))) return Value(false); v7272 = v7273; return Value(true); }()))) {
auto v7274 = s->LocalAt(6);
Put(s->LocalAt(19), Value("day"), v7274);
auto v7275 = ([&]() -> Value { auto dict7276 = Dict(); return dict7276; }());
Put(s->LocalAt(19), Value("workers"), v7275);
auto v7277 = ([&]() -> Value { auto dict7278 = Dict(); return dict7278; }());
Put(s->LocalAt(19), Value("work"), v7277);
auto v7279 = Value(int64_t{0});
Put(s->LocalAt(19), Value("rescue_today"), v7279);
}
for (const auto& item7280 : Iterate(([&]() -> Value { auto fn7281 = Attribute(Get(s->LocalAt(19), Value("work")), "items"); Arguments args7282; return Call(c, fn7281, std::move(args7282)); }()))) {
auto unpack7283 = Iterate(item7280);
ValidateUnpack(unpack7283, 2, false);
s->SetAt(1, unpack7283.at(0));
s->SetAt(15, unpack7283.at(1));
if (static_cast<bool>(([&]() -> Value { auto v7284 = ([&]() -> Value { auto v7285 = Get(s->LocalAt(15), Value("step")); Value v7286; v7286 = ([&]() -> Value { auto v7287 = s->LocalAt(20); return Binary("Sub", v7287, Value(int64_t{1})); }()); if (!static_cast<bool>(Binary("NotEq", v7285, v7286))) return Value(false); v7285 = v7286; return Value(true); }()); if (static_cast<bool>(v7284)) return v7284; v7284 = ([&]() -> Value { auto v7288 = s->LocalAt(1); Value v7289; v7289 = ([&]() -> Value { auto fn7290 = s->Global("len"); Arguments args7291; args7291.Add(Get(s->LocalAt(16), Value("inventories")), false); return Call(c, fn7290, std::move(args7291)); }()); if (!static_cast<bool>(Binary("GtE", v7288, v7289))) return Value(false); v7288 = v7289; return Value(true); }()); return v7284; }()))) {
continue;
}
auto v7292 = ([&]() -> Value { auto fn7293 = PrepareDictionaryGet(([&]() -> Value { auto dict7295 = Dict(); auto key7296 = Value("HARVEST"); Put(dict7295, key7296, Value("WOOL")); auto key7297 = Value("COLLECT_FERTILIZER"); Put(dict7295, key7297, Value("FERTILIZER")); return dict7295; }())); Arguments args7294; args7294.Add(Get(Get(s->LocalAt(15), Value("command")), Value(int64_t{0})), false); return CallDictionaryGet(c, fn7293, std::move(args7294)); }());
s->SetAt(11, v7292);
if (static_cast<bool>(s->LocalAt(11))) {
auto v7298 = ([&]() -> Value { auto fn7299 = s->Global("max"); Arguments args7300; args7300.positional.reserve(2); args7300.Add(Value(int64_t{0}), false); args7300.Add(([&]() -> Value { auto v7301 = ([&]() -> Value { auto fn7302 = PrepareDictionaryGet(Get(Get(s->LocalAt(16), Value("inventories")), s->LocalAt(1))); Arguments args7303; args7303.positional.reserve(2); args7303.Add(s->LocalAt(11), false); args7303.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn7302, std::move(args7303)); }()); return Binary("Sub", v7301, ([&]() -> Value { auto fn7304 = PrepareDictionaryGet(Get(s->LocalAt(15), Value("inventory"))); Arguments args7305; args7305.positional.reserve(2); args7305.Add(s->LocalAt(11), false); args7305.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn7304, std::move(args7305)); }())); }()), false); return Call(c, fn7299, std::move(args7300)); }());
s->SetAt(9, v7298);
auto v7306 = Get(s->LocalAt(19), Value("credit"));
auto v7307 = s->LocalAt(11);
auto v7308 = Get(v7306, v7307);
Put(v7306, v7307, Inplace("Add", v7308, s->LocalAt(9)));
auto v7309 = s->Global("_V233_REPORT");
auto v7310 = (static_cast<bool>(([&]() -> Value { auto v7312 = s->LocalAt(11); Value v7313; v7313 = Value("WOOL"); if (!static_cast<bool>(Binary("Eq", v7312, v7313))) return Value(false); v7312 = v7313; return Value(true); }())) ? Value("sheep_wool_harvested") : Value("sheep_fert_collected"));
auto v7311 = Get(v7309, v7310);
Put(v7309, v7310, Inplace("Add", v7311, s->LocalAt(9)));
}
}
auto v7314 = ([&]() -> Value { auto fn7315 = Attribute(s->LocalAt(19), "pop"); Arguments args7316; args7316.positional.reserve(2); args7316.Add(Value("pending"), false); args7316.Add(Value{}, false); return Call(c, fn7315, std::move(args7316)); }());
s->SetAt(13, v7314);
if (static_cast<bool>(s->LocalAt(13))) {
auto v7317 = ([&]() -> Value { auto v7318 = ([&]() -> Value { auto v7319 = Value("SE"); Value v7320; v7320 = Get(s->LocalAt(7), Value("unlocked_quadrants")); if (!static_cast<bool>(Binary("In", v7319, v7320))) return Value(false); v7319 = v7320; return Value(true); }()); if (!static_cast<bool>(v7318)) return v7318; v7318 = ([&]() -> Value { auto v7321 = Unary("Not", Get(s->LocalAt(13), Value("initial"))); if (static_cast<bool>(v7321)) return v7321; v7321 = ([&]() -> Value { auto v7322 = ([&]() -> Value { auto fn7324 = PrepareDictionaryGet(Get(s->LocalAt(16), Value("shed"))); Arguments args7325; args7325.positional.reserve(2); args7325.Add(Value("SHEEP"), false); args7325.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn7324, std::move(args7325)); }()); Value v7323; v7323 = Value(int64_t{6}); if (!static_cast<bool>(Binary("GtE", v7322, v7323))) return Value(false); v7322 = v7323; return Value(true); }()); return v7321; }()); return v7318; }());
s->SetAt(8, v7317);
if (static_cast<bool>(Unary("Not", s->LocalAt(8)))) {
auto v7326 = s->Global("_V233_REPORT");
auto v7327 = Value("sheep_purchase_shortfalls");
auto v7328 = Get(v7326, v7327);
Put(v7326, v7327, Inplace("Add", v7328, Value(int64_t{1})));
}
else {
if (static_cast<bool>(([&]() -> Value { auto v7329 = ([&]() -> Value { auto fn7331 = s->Global("len"); Arguments args7332; args7332.Add(Get(s->LocalAt(7), Value("hands")), false); return Call(c, fn7331, std::move(args7332)); }()); Value v7330; v7330 = ([&]() -> Value { auto v7333 = Get(s->LocalAt(13), Value("first")); return Binary("Add", v7333, Value(int64_t{1})); }()); if (!static_cast<bool>(Binary("Lt", v7329, v7330))) return Value(false); v7329 = v7330; return Value(true); }()))) {
auto v7334 = s->Global("_V233_REPORT");
auto v7335 = Value("sheep_hire_shortfalls");
auto v7336 = Get(v7334, v7335);
Put(v7334, v7335, Inplace("Add", v7336, Value(int64_t{1})));
}
else {
for (const auto& item7337 : Iterate(([&]() -> Value { auto fn7338 = s->Global("range"); Arguments args7339; args7339.Add(Value(int64_t{2}), false); return Call(c, fn7338, std::move(args7339)); }()))) {
s->SetAt(10, item7337);
auto v7340 = ([&]() -> Value { auto comp7341 = std::make_shared<Scope>(); comp7341->globals = s->globals; comp7341->parent = s; static constexpr const char* comp7341_names[] = {"x"}; comp7341->PrepareSlots(comp7341_names); auto result7342 = List(); for (const auto& item7343 : Iterate(([&]() -> Value { auto fn7344 = s->Global("range"); Arguments args7345; args7345.positional.reserve(2); args7345.Add(Value(int64_t{5}), false); args7345.Add(Value(int64_t{8}), false); return Call(c, fn7344, std::move(args7345)); }()))) { comp7341->SetAt(0, item7343); result7342.node()->sequence.push_back(Tuple({comp7341->LocalAt(0), ([&]() -> Value { auto v7346 = Value(int64_t{5}); return Binary("Add", v7346, comp7341->Captured("i")); }())})); } return result7342; }());
Put(Get(s->LocalAt(19), Value("workers")), ([&]() -> Value { auto v7347 = Get(s->LocalAt(13), Value("first")); return Binary("Add", v7347, s->LocalAt(10)); }()), v7340);
}
auto v7348 = s->Global("_V233_REPORT");
auto v7349 = Value("sheep_workers_confirmed");
auto v7350 = Get(v7348, v7349);
Put(v7348, v7349, Inplace("Add", v7350, Value(int64_t{2})));
if (static_cast<bool>(Get(s->LocalAt(13), Value("initial")))) {
auto v7351 = Value(true);
Put(s->LocalAt(19), Value("committed"), v7351);
auto v7352 = s->Global("_V233_REPORT");
auto v7353 = Value("sheep_committed");
auto v7354 = Get(v7352, v7353);
Put(v7352, v7353, Inplace("Add", v7354, Value(int64_t{1})));
}
}
}
}
auto v7355 = ([&]() -> Value { auto fn7356 = s->Global("_v233_request"); Arguments args7357; args7357.positional.reserve(4); args7357.Add(s->LocalAt(12), false); args7357.Add(s->LocalAt(0), false); args7357.Add(s->LocalAt(19), false); args7357.Add(Get(Attribute(Attribute(s->Global("_IMPL"), "chassis"), "players"), s->LocalAt(14)), false); return Call(c, fn7356, std::move(args7357)); }());
s->SetAt(0, v7355);
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto fn7358 = PrepareDictionaryGet(s->LocalAt(19)); Arguments args7359; args7359.Add(Value("committed"), false); return CallDictionaryGet(c, fn7358, std::move(args7359)); }())))) {
return s->LocalAt(0);
}
auto v7360 = ([&]() -> Value { auto fn7361 = Attribute(s->Global("copy"), "deepcopy"); Arguments args7362; args7362.Add(s->LocalAt(0), false); return Call(c, fn7361, std::move(args7362)); }());
s->SetAt(17, v7360);
auto v7363 = ([&]() -> Value { auto v7364 = List({([&]() -> Value { auto v7365 = ([&]() -> Value { auto fn7366 = PrepareDictionaryGet(s->LocalAt(17)); Arguments args7367; args7367.Add(Value("farmer"), false); return CallDictionaryGet(c, fn7366, std::move(args7367)); }()); if (static_cast<bool>(v7365)) return v7365; v7365 = List({Value("PASS")}); return v7365; }())}); return Binary("Add", v7364, ([&]() -> Value { auto fn7368 = s->Global("list"); Arguments args7369; args7369.Add(([&]() -> Value { auto v7370 = ([&]() -> Value { auto fn7371 = PrepareDictionaryGet(s->LocalAt(17)); Arguments args7372; args7372.Add(Value("hands"), false); return CallDictionaryGet(c, fn7371, std::move(args7372)); }()); if (static_cast<bool>(v7370)) return v7370; v7370 = List({}); return v7370; }()), false); return Call(c, fn7368, std::move(args7369)); }())); }());
s->SetAt(3, v7363);
auto v7373 = s->LocalAt(3);
s->SetAt(3, Inplace("Add", v7373, ([&]() -> Value { auto comp7374 = std::make_shared<Scope>(); comp7374->globals = s->globals; comp7374->parent = s; static constexpr const char* comp7374_names[] = {"_"}; comp7374->PrepareSlots(comp7374_names); auto result7375 = List(); for (const auto& item7376 : Iterate(([&]() -> Value { auto fn7377 = s->Global("range"); Arguments args7378; args7378.Add(([&]() -> Value { auto v7379 = ([&]() -> Value { auto v7380 = ([&]() -> Value { auto fn7381 = s->Global("len"); Arguments args7382; args7382.Add(Get(s->LocalAt(7), Value("hands")), false); return Call(c, fn7381, std::move(args7382)); }()); return Binary("Add", v7380, Value(int64_t{1})); }()); return Binary("Sub", v7379, ([&]() -> Value { auto fn7383 = s->Global("len"); Arguments args7384; args7384.Add(s->LocalAt(3), false); return Call(c, fn7383, std::move(args7384)); }())); }()), false); return Call(c, fn7377, std::move(args7378)); }()))) { comp7374->SetAt(0, item7376); result7375.node()->sequence.push_back(List({Value("PASS")})); } return result7375; }())));
auto v7385 = ([&]() -> Value { auto dict7386 = Dict(); return dict7386; }());
Put(s->LocalAt(19), Value("work"), v7385);
for (const auto& item7387 : Iterate(([&]() -> Value { auto fn7388 = Attribute(Get(s->LocalAt(19), Value("workers")), "items"); Arguments args7389; return Call(c, fn7388, std::move(args7389)); }()))) {
auto unpack7390 = Iterate(item7387);
ValidateUnpack(unpack7390, 2, false);
s->SetAt(1, unpack7390.at(0));
s->SetAt(22, unpack7390.at(1));
auto v7391 = ([&]() -> Value { auto fn7392 = s->Global("_v233_worker"); Arguments args7393; args7393.positional.reserve(3); args7393.Add(s->LocalAt(12), false); args7393.Add(s->LocalAt(1), false); args7393.Add(s->LocalAt(22), false); return Call(c, fn7392, std::move(args7393)); }());
s->SetAt(2, v7391);
auto v7394 = s->LocalAt(2);
Put(s->LocalAt(3), s->LocalAt(1), v7394);
auto v7395 = ([&]() -> Value { auto dict7396 = Dict(); auto key7397 = Value("step"); Put(dict7396, key7397, s->LocalAt(20)); auto key7398 = Value("command"); Put(dict7396, key7398, s->LocalAt(2)); auto key7399 = Value("inventory"); Put(dict7396, key7399, ([&]() -> Value { auto fn7400 = s->Global("dict"); Arguments args7401; args7401.Add(Get(Get(s->LocalAt(16), Value("inventories")), s->LocalAt(1)), false); return Call(c, fn7400, std::move(args7401)); }())); return dict7396; }());
Put(Get(s->LocalAt(19), Value("work")), s->LocalAt(1), v7395);
}
auto v7402 = Tuple({Get(s->LocalAt(3), Value(int64_t{0})), Slice(s->LocalAt(3), Value(int64_t{1}), Value{}, Value{})});
auto unpack7403 = Iterate(v7402);
ValidateUnpack(unpack7403, 2, false);
Put(s->LocalAt(17), Value("farmer"), unpack7403.at(0));
Put(s->LocalAt(17), Value("hands"), unpack7403.at(1));
auto v7404 = ([&]() -> Value { auto fn7405 = s->Global("_v234_rescue"); Arguments args7406; args7406.positional.reserve(3); args7406.Add(s->LocalAt(12), false); args7406.Add(s->LocalAt(17), false); args7406.Add(s->LocalAt(19), false); return Call(c, fn7405, std::move(args7406)); }());
s->SetAt(17, v7404);
auto v7407 = ([&]() -> Value { auto fn7408 = s->Global("projected_shed"); Arguments args7409; args7409.positional.reserve(2); args7409.Add(s->LocalAt(17), false); args7409.Add(([&]() -> Value { auto fn7410 = s->Global("FarmView"); Arguments args7411; args7411.Add(s->LocalAt(12), false); return Call(c, fn7410, std::move(args7411)); }()), false); return Call(c, fn7408, std::move(args7409)); }());
s->SetAt(21, v7407);
for (const auto& item7412 : Iterate(Tuple({Value("WOOL"), Value("FERTILIZER")}))) {
s->SetAt(11, item7412);
auto v7413 = ([&]() -> Value { auto fn7414 = s->Global("sum"); Arguments args7415; args7415.Add(([&]() -> Value { auto comp7416 = std::make_shared<Scope>(); comp7416->globals = s->globals; comp7416->parent = s; static constexpr const char* comp7416_names[] = {"o"}; comp7416->PrepareSlots(comp7416_names); auto result7417 = List(); for (const auto& item7418 : Iterate(Get(s->LocalAt(17), Value("market")))) { comp7416->SetAt(0, item7418); if (!static_cast<bool>(([&]() -> Value { auto v7419 = Slice(comp7416->LocalAt(0), Value{}, Value(int64_t{2}), Value{}); Value v7420; v7420 = List({Value("SELL"), comp7416->Captured("item")}); if (!static_cast<bool>(Binary("Eq", v7419, v7420))) return Value(false); v7419 = v7420; return Value(true); }()))) continue; result7417.node()->sequence.push_back(([&]() -> Value { auto fn7421 = comp7416->Global("int"); Arguments args7422; args7422.Add(Get(comp7416->LocalAt(0), Value(int64_t{2})), false); return Call(c, fn7421, std::move(args7422)); }())); } return result7417; }()), false); return Call(c, fn7414, std::move(args7415)); }());
s->SetAt(18, v7413);
auto v7423 = ([&]() -> Value { auto fn7424 = s->Global("min"); Arguments args7425; args7425.positional.reserve(2); args7425.Add(Get(Get(s->LocalAt(19), Value("credit")), s->LocalAt(11)), false); args7425.Add(([&]() -> Value { auto fn7426 = s->Global("max"); Arguments args7427; args7427.positional.reserve(2); args7427.Add(Value(int64_t{0}), false); args7427.Add(([&]() -> Value { auto v7428 = ([&]() -> Value { auto fn7429 = PrepareDictionaryGet(s->LocalAt(21)); Arguments args7430; args7430.positional.reserve(2); args7430.Add(s->LocalAt(11), false); args7430.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn7429, std::move(args7430)); }()); return Binary("Sub", v7428, s->LocalAt(18)); }()), false); return Call(c, fn7426, std::move(args7427)); }()), false); return Call(c, fn7424, std::move(args7425)); }());
s->SetAt(5, v7423);
if (static_cast<bool>(([&]() -> Value { auto v7431 = s->LocalAt(5); if (!static_cast<bool>(v7431)) return v7431; v7431 = ([&]() -> Value { auto v7432 = ([&]() -> Value { auto fn7434 = s->Global("len"); Arguments args7435; args7435.Add(Get(s->LocalAt(17), Value("market")), false); return Call(c, fn7434, std::move(args7435)); }()); Value v7433; v7433 = s->Global("MAX_ORDERS"); if (!static_cast<bool>(Binary("Lt", v7432, v7433))) return Value(false); v7432 = v7433; return Value(true); }()); return v7431; }()))) {
(void)([&]() -> Value { auto fn7436 = Attribute(Get(s->LocalAt(17), Value("market")), "append"); Arguments args7437; args7437.Add(List({Value("SELL"), s->LocalAt(11), s->LocalAt(5)}), false); return Call(c, fn7436, std::move(args7437)); }());
auto v7438 = Get(s->LocalAt(19), Value("credit"));
auto v7439 = s->LocalAt(11);
auto v7440 = Get(v7438, v7439);
Put(v7438, v7439, Inplace("Sub", v7440, s->LocalAt(5)));
auto v7441 = s->Global("_V233_REPORT");
auto v7442 = (static_cast<bool>(([&]() -> Value { auto v7444 = s->LocalAt(11); Value v7445; v7445 = Value("WOOL"); if (!static_cast<bool>(Binary("Eq", v7444, v7445))) return Value(false); v7444 = v7445; return Value(true); }())) ? Value("sheep_extra_wool_sales") : Value("sheep_extra_fert_sales"));
auto v7443 = Get(v7441, v7442);
Put(v7441, v7442, Inplace("Add", v7443, s->LocalAt(5)));
}
}
return s->LocalAt(17);
return {};
}
}  // namespace kagg::opponents::compiled
