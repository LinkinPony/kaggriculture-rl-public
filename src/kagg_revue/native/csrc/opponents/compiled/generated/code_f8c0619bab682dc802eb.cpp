// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_f8c0619bab682dc802eb(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "before", "budget", "committed", "day", "expected", "extra", "farm", "hour", "i", "incoming", "m", "market", "native", "o", "obs", "parent_hires", "planned", "result", "state", "step", "stock", "tape_cost", "tiles"};
s->PrepareSlots(s_names);
auto v26150 = ([&]() -> Value { auto fn26151 = s->Global("int"); Arguments args26152; args26152.Add(Get(s->LocalAt(15), Value("step")), false); return Call(c, fn26151, std::move(args26152)); }());
s->SetAt(20, v26150);
auto v26153 = ([&]() -> Value { auto v26154 = s->LocalAt(20); return Binary("FloorDiv", v26154, Value(int64_t{24})); }());
s->SetAt(4, v26153);
auto v26155 = ([&]() -> Value { auto v26156 = s->LocalAt(20); return Binary("Mod", v26156, Value(int64_t{24})); }());
s->SetAt(8, v26155);
auto v26157 = Get(Get(s->LocalAt(15), Value("farms")), Get(s->LocalAt(15), Value("player")));
s->SetAt(7, v26157);
auto v26158 = ([&]() -> Value { auto fn26159 = PrepareDictionaryGet(s->LocalAt(19)); Arguments args26160; args26160.Add(Value("committed"), false); return CallDictionaryGet(c, fn26159, std::move(args26160)); }());
s->SetAt(3, v26158);
if (static_cast<bool>(([&]() -> Value { auto v26161 = s->Global("_E343_YX_DAY11"); if (!static_cast<bool>(v26161)) return v26161; v26161 = Unary("Not", s->LocalAt(3)); if (!static_cast<bool>(v26161)) return v26161; v26161 = ([&]() -> Value { auto v26162 = s->LocalAt(4); Value v26163; v26163 = Value(int64_t{11}); if (!static_cast<bool>(Binary("Eq", v26162, v26163))) return Value(false); v26162 = v26163; return Value(true); }()); return v26161; }()))) {
if (static_cast<bool>(([&]() -> Value { auto v26164 = ([&]() -> Value { auto v26165 = ([&]() -> Value { auto fn26167 = PrepareDictionaryGet(s->LocalAt(19)); Arguments args26168; args26168.Add(Value("requested_day"), false); return CallDictionaryGet(c, fn26167, std::move(args26168)); }()); Value v26166; v26166 = s->LocalAt(4); if (!static_cast<bool>(Binary("Eq", v26165, v26166))) return Value(false); v26165 = v26166; return Value(true); }()); if (static_cast<bool>(v26164)) return v26164; v26164 = ([&]() -> Value { auto v26169 = s->LocalAt(8); Value v26170; v26170 = Value(int64_t{2}); if (!static_cast<bool>(Binary("Lt", v26169, v26170))) return Value(false); v26169 = v26170; return Value(true); }()); if (static_cast<bool>(v26164)) return v26164; v26164 = ([&]() -> Value { auto v26171 = s->LocalAt(8); Value v26172; v26172 = Value(int64_t{12}); if (!static_cast<bool>(Binary("Gt", v26171, v26172))) return Value(false); v26171 = v26172; return Value(true); }()); return v26164; }()))) {
return s->LocalAt(0);
}
auto v26173 = s->Global("_E343_YX_REPORT");
auto v26174 = Value("yx_day11_checks");
auto v26175 = Get(v26173, v26174);
Put(v26173, v26174, Inplace("Add", v26175, Value(int64_t{1})));
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto fn26176 = s->Global("_e343_yx_eligible11"); Arguments args26177; args26177.positional.reserve(2); args26177.Add(s->LocalAt(15), false); args26177.Add(s->LocalAt(13), false); return Call(c, fn26176, std::move(args26177)); }())))) {
return s->LocalAt(0);
}
auto v26178 = ([&]() -> Value { auto fn26179 = s->Global("_v219_native_day"); Arguments args26180; args26180.positional.reserve(2); args26180.Add(s->LocalAt(13), false); args26180.Add(s->LocalAt(4), false); return Call(c, fn26179, std::move(args26180)); }());
s->SetAt(17, v26178);
if (static_cast<bool>(([&]() -> Value { auto comp26181 = std::make_shared<Scope>(); comp26181->globals = s->globals; comp26181->parent = s; static constexpr const char* comp26181_names[] = {"a", "o"}; comp26181->PrepareSlots(comp26181_names); auto result26182 = List(); for (const auto& item26183 : Iterate(Slice(s->LocalAt(17), ([&]() -> Value { auto v26184 = s->LocalAt(8); return Binary("Add", v26184, Value(int64_t{1})); }()), Value{}, Value{}))) { comp26181->SetAt(0, item26183); for (const auto& item26185 : Iterate(([&]() -> Value { auto fn26186 = PrepareDictionaryGet(comp26181->LocalAt(0)); Arguments args26187; args26187.positional.reserve(2); args26187.Add(Value("market"), false); args26187.Add(List({}), false); return CallDictionaryGet(c, fn26186, std::move(args26187)); }()))) { comp26181->SetAt(1, item26185); if (static_cast<bool>(([&]() -> Value { auto v26188 = comp26181->LocalAt(1); if (!static_cast<bool>(v26188)) return v26188; v26188 = ([&]() -> Value { auto v26189 = Get(comp26181->LocalAt(1), Value(int64_t{0})); Value v26190; v26190 = Value("HIRE"); if (!static_cast<bool>(Binary("Eq", v26189, v26190))) return Value(false); v26189 = v26190; return Value(true); }()); return v26188; }()))) return Value(true); } } return Value(false); }()))) {
return s->LocalAt(0);
}
auto v26191 = ([&]() -> Value { auto v26192 = ([&]() -> Value { auto fn26193 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args26194; args26194.positional.reserve(2); args26194.Add(Value("market"), false); args26194.Add(List({}), false); return CallDictionaryGet(c, fn26193, std::move(args26194)); }()); if (static_cast<bool>(v26192)) return v26192; v26192 = List({}); return v26192; }());
s->SetAt(12, v26191);
if (static_cast<bool>(([&]() -> Value { auto comp26195 = std::make_shared<Scope>(); comp26195->globals = s->globals; comp26195->parent = s; static constexpr const char* comp26195_names[] = {"o"}; comp26195->PrepareSlots(comp26195_names); auto result26196 = List(); for (const auto& item26197 : Iterate(s->LocalAt(12))) { comp26195->SetAt(0, item26197); if (static_cast<bool>(([&]() -> Value { auto v26198 = comp26195->LocalAt(0); if (!static_cast<bool>(v26198)) return v26198; v26198 = ([&]() -> Value { auto v26199 = Get(comp26195->LocalAt(0), Value(int64_t{0})); Value v26200; v26200 = Value("BUY_LAND"); if (!static_cast<bool>(Binary("Eq", v26199, v26200))) return Value(false); v26199 = v26200; return Value(true); }()); return v26198; }()))) return Value(true); } return Value(false); }()))) {
return s->LocalAt(0);
}
auto v26201 = ([&]() -> Value { auto fn26202 = s->Global("sum"); Arguments args26203; args26203.Add(([&]() -> Value { auto comp26204 = std::make_shared<Scope>(); comp26204->globals = s->globals; comp26204->parent = s; static constexpr const char* comp26204_names[] = {"o"}; comp26204->PrepareSlots(comp26204_names); auto result26205 = List(); for (const auto& item26206 : Iterate(s->LocalAt(12))) { comp26204->SetAt(0, item26206); result26205.node()->sequence.push_back(([&]() -> Value { auto v26207 = ([&]() -> Value { auto fn26208 = comp26204->Global("bool"); Arguments args26209; args26209.Add(comp26204->LocalAt(0), false); return Call(c, fn26208, std::move(args26209)); }()); if (!static_cast<bool>(v26207)) return v26207; v26207 = ([&]() -> Value { auto v26210 = Get(comp26204->LocalAt(0), Value(int64_t{0})); Value v26211; v26211 = Value("HIRE"); if (!static_cast<bool>(Binary("Eq", v26210, v26211))) return Value(false); v26210 = v26211; return Value(true); }()); return v26207; }())); } return result26205; }()), false); return Call(c, fn26202, std::move(args26203)); }());
s->SetAt(16, v26201);
auto v26212 = ([&]() -> Value { auto fn26213 = s->Global("max"); Arguments args26214; args26214.Add(([&]() -> Value { auto comp26215 = std::make_shared<Scope>(); comp26215->globals = s->globals; comp26215->parent = s; static constexpr const char* comp26215_names[] = {"a"}; comp26215->PrepareSlots(comp26215_names); auto result26216 = List(); for (const auto& item26217 : Iterate(s->LocalAt(17))) { comp26215->SetAt(0, item26217); result26216.node()->sequence.push_back(([&]() -> Value { auto fn26218 = comp26215->Global("len"); Arguments args26219; args26219.Add(([&]() -> Value { auto fn26220 = PrepareDictionaryGet(comp26215->LocalAt(0)); Arguments args26221; args26221.positional.reserve(2); args26221.Add(Value("hands"), false); args26221.Add(List({}), false); return CallDictionaryGet(c, fn26220, std::move(args26221)); }()), false); return Call(c, fn26218, std::move(args26219)); }())); } return result26216; }()), false); return Call(c, fn26213, std::move(args26214)); }());
s->SetAt(5, v26212);
if (static_cast<bool>(([&]() -> Value { auto v26222 = ([&]() -> Value { auto v26224 = ([&]() -> Value { auto fn26225 = s->Global("len"); Arguments args26226; args26226.Add(Get(s->LocalAt(7), Value("hands")), false); return Call(c, fn26225, std::move(args26226)); }()); return Binary("Add", v26224, s->LocalAt(16)); }()); Value v26223; v26223 = s->LocalAt(5); if (!static_cast<bool>(Binary("NotEq", v26222, v26223))) return Value(false); v26222 = v26223; return Value(true); }()))) {
return s->LocalAt(0);
}
auto v26227 = List({List({Value("BUY_LAND")}), List({Value("BUY_ANIMAL"), Value("SHEEP"), Value(int64_t{6})}), List({Value("BUY_PRODUCT"), Value("WHEAT"), Value(int64_t{6})}), List({Value("HIRE")}), List({Value("HIRE")})});
s->SetAt(6, v26227);
if (static_cast<bool>(([&]() -> Value { auto v26228 = ([&]() -> Value { auto v26230 = ([&]() -> Value { auto fn26231 = s->Global("len"); Arguments args26232; args26232.Add(s->LocalAt(12), false); return Call(c, fn26231, std::move(args26232)); }()); return Binary("Add", v26230, ([&]() -> Value { auto fn26233 = s->Global("len"); Arguments args26234; args26234.Add(s->LocalAt(6), false); return Call(c, fn26233, std::move(args26234)); }())); }()); Value v26229; v26229 = s->Global("MAX_ORDERS"); if (!static_cast<bool>(Binary("Gt", v26228, v26229))) return Value(false); v26228 = v26229; return Value(true); }()))) {
return s->LocalAt(0);
}
auto v26235 = ([&]() -> Value { auto fn26236 = s->Global("projected_shed"); Arguments args26237; args26237.positional.reserve(2); args26237.Add(s->LocalAt(0), false); args26237.Add(([&]() -> Value { auto fn26238 = s->Global("FarmView"); Arguments args26239; args26239.Add(s->LocalAt(15), false); return Call(c, fn26238, std::move(args26239)); }()), false); return Call(c, fn26236, std::move(args26237)); }());
s->SetAt(21, v26235);
auto v26240 = Value(int64_t{12});
s->SetAt(10, v26240);
auto v26241 = ([&]() -> Value { auto v26242 = ([&]() -> Value { auto v26243 = Value(int64_t{7000}); return Binary("Add", v26243, ([&]() -> Value { auto v26244 = Value(int64_t{6}); return Binary("Mult", v26244, ([&]() -> Value { auto v26245 = ([&]() -> Value { auto fn26246 = s->Global("int"); Arguments args26247; args26247.Add(Get(Get(Get(s->LocalAt(15), Value("market")), Value("prices")), Value("WHEAT")), false); return Call(c, fn26246, std::move(args26247)); }()); return Binary("Add", v26245, Value(int64_t{10})); }())); }())); }()); return Binary("Add", v26242, ([&]() -> Value { auto fn26248 = s->Global("sum"); Arguments args26249; args26249.Add(([&]() -> Value { auto comp26250 = std::make_shared<Scope>(); comp26250->globals = s->globals; comp26250->parent = s; static constexpr const char* comp26250_names[] = {"n"}; comp26250->PrepareSlots(comp26250_names); auto result26251 = List(); for (const auto& item26252 : Iterate(([&]() -> Value { auto fn26253 = s->Global("range"); Arguments args26254; args26254.positional.reserve(2); args26254.Add(([&]() -> Value { auto v26255 = Get(s->LocalAt(7), Value("hires_today")); return Binary("Add", v26255, s->LocalAt(16)); }()), false); args26254.Add(([&]() -> Value { auto v26256 = ([&]() -> Value { auto v26257 = Get(s->LocalAt(7), Value("hires_today")); return Binary("Add", v26257, s->LocalAt(16)); }()); return Binary("Add", v26256, Value(int64_t{2})); }()), false); return Call(c, fn26253, std::move(args26254)); }()))) { comp26250->SetAt(0, item26252); result26251.node()->sequence.push_back(([&]() -> Value { auto fn26258 = comp26250->Global("_v219_fib"); Arguments args26259; args26259.Add(comp26250->LocalAt(0), false); return Call(c, fn26258, std::move(args26259)); }())); } return result26251; }()), false); return Call(c, fn26248, std::move(args26249)); }())); }());
s->SetAt(2, v26241);
for (const auto& item26260 : Iterate(s->LocalAt(12))) {
s->SetAt(14, item26260);
if (static_cast<bool>(Unary("Not", s->LocalAt(14)))) {
continue;
}
if (static_cast<bool>(([&]() -> Value { auto v26261 = Get(s->LocalAt(14), Value(int64_t{0})); Value v26262; v26262 = Value("BUY_PRODUCT"); if (!static_cast<bool>(Binary("Eq", v26261, v26262))) return Value(false); v26261 = v26262; return Value(true); }()))) {
auto v26263 = s->LocalAt(10);
s->SetAt(10, Inplace("Add", v26263, ([&]() -> Value { auto fn26264 = s->Global("int"); Arguments args26265; args26265.Add(Get(s->LocalAt(14), Value(int64_t{2})), false); return Call(c, fn26264, std::move(args26265)); }())));
auto v26266 = s->LocalAt(2);
s->SetAt(2, Inplace("Add", v26266, ([&]() -> Value { auto v26267 = ([&]() -> Value { auto fn26268 = s->Global("int"); Arguments args26269; args26269.Add(Get(s->LocalAt(14), Value(int64_t{2})), false); return Call(c, fn26268, std::move(args26269)); }()); return Binary("Mult", v26267, ([&]() -> Value { auto v26270 = ([&]() -> Value { auto fn26271 = s->Global("int"); Arguments args26272; args26272.Add(Get(Get(Get(s->LocalAt(15), Value("market")), Value("prices")), Get(s->LocalAt(14), Value(int64_t{1}))), false); return Call(c, fn26271, std::move(args26272)); }()); return Binary("Add", v26270, Value(int64_t{10})); }())); }())));
}
else {
if (static_cast<bool>(([&]() -> Value { auto v26273 = Get(s->LocalAt(14), Value(int64_t{0})); Value v26274; v26274 = Value("BUY_ANIMAL"); if (!static_cast<bool>(Binary("Eq", v26273, v26274))) return Value(false); v26273 = v26274; return Value(true); }()))) {
auto v26275 = s->LocalAt(10);
s->SetAt(10, Inplace("Add", v26275, ([&]() -> Value { auto fn26276 = s->Global("int"); Arguments args26277; args26277.Add(Get(s->LocalAt(14), Value(int64_t{2})), false); return Call(c, fn26276, std::move(args26277)); }())));
auto v26278 = s->LocalAt(2);
s->SetAt(2, Inplace("Add", v26278, ([&]() -> Value { auto v26279 = ([&]() -> Value { auto fn26280 = s->Global("int"); Arguments args26281; args26281.Add(Get(s->LocalAt(14), Value(int64_t{2})), false); return Call(c, fn26280, std::move(args26281)); }()); return Binary("Mult", v26279, Get(s->Global("_E343_YX_ANIMAL"), Get(s->LocalAt(14), Value(int64_t{1})))); }())));
}
else {
if (static_cast<bool>(([&]() -> Value { auto v26282 = Get(s->LocalAt(14), Value(int64_t{0})); Value v26283; v26283 = Value("BUY_SEED"); if (!static_cast<bool>(Binary("Eq", v26282, v26283))) return Value(false); v26282 = v26283; return Value(true); }()))) {
auto v26284 = s->LocalAt(2);
s->SetAt(2, Inplace("Add", v26284, ([&]() -> Value { auto v26285 = ([&]() -> Value { auto fn26286 = s->Global("int"); Arguments args26287; args26287.Add(Get(s->LocalAt(14), Value(int64_t{2})), false); return Call(c, fn26286, std::move(args26287)); }()); return Binary("Mult", v26285, Get(s->Global("_E343_YX_SEED"), Get(s->LocalAt(14), Value(int64_t{1})))); }())));
}
}
}
}
if (static_cast<bool>(([&]() -> Value { auto v26288 = ([&]() -> Value { auto v26290 = ([&]() -> Value { auto fn26291 = s->Global("sum"); Arguments args26292; args26292.Add(([&]() -> Value { auto fn26293 = Attribute(s->LocalAt(21), "values"); Arguments args26294; return Call(c, fn26293, std::move(args26294)); }()), false); return Call(c, fn26291, std::move(args26292)); }()); return Binary("Add", v26290, s->LocalAt(10)); }()); Value v26289; v26289 = Value(int64_t{100}); if (!static_cast<bool>(Binary("Gt", v26288, v26289))) return Value(false); v26288 = v26289; return Value(true); }()))) {
return s->LocalAt(0);
}
auto v26295 = ([&]() -> Value { auto fn26296 = s->Global("_e343_yx_tape_cost"); Arguments args26297; args26297.positional.reserve(3); args26297.Add(s->LocalAt(15), false); args26297.Add(s->LocalAt(13), false); args26297.Add(Value(int64_t{12}), false); return Call(c, fn26296, std::move(args26297)); }());
s->SetAt(22, v26295);
if (static_cast<bool>(([&]() -> Value { auto v26298 = Get(s->LocalAt(7), Value("money")); Value v26299; v26299 = ([&]() -> Value { auto v26300 = ([&]() -> Value { auto v26301 = s->LocalAt(2); return Binary("Add", v26301, Value(int64_t{3000})); }()); return Binary("Add", v26300, s->LocalAt(22)); }()); if (!static_cast<bool>(Binary("Lt", v26298, v26299))) return Value(false); v26298 = v26299; return Value(true); }()))) {
auto v26302 = s->Global("_E343_YX_REPORT");
auto v26303 = Value("yx_day11_declines");
auto v26304 = Get(v26302, v26303);
Put(v26302, v26303, Inplace("Add", v26304, Value(int64_t{1})));
return s->LocalAt(0);
}
auto v26305 = s->LocalAt(4);
Put(s->LocalAt(19), Value("requested_day"), v26305);
auto v26306 = ([&]() -> Value { auto dict26307 = Dict(); auto key26308 = Value("first"); Put(dict26307, key26308, ([&]() -> Value { auto v26309 = s->LocalAt(5); return Binary("Add", v26309, Value(int64_t{1})); }())); auto key26310 = Value("initial"); Put(dict26307, key26310, Value(true)); return dict26307; }());
Put(s->LocalAt(19), Value("pending"), v26306);
auto v26311 = s->Global("_V233_REPORT");
auto v26312 = Value("sheep_hire_requests");
auto v26313 = Get(v26311, v26312);
Put(v26311, v26312, Inplace("Add", v26313, Value(int64_t{2})));
auto v26314 = s->Global("_V233_REPORT");
auto v26315 = Value("sheep_feed_buy_requests");
auto v26316 = Get(v26314, v26315);
Put(v26314, v26315, Inplace("Add", v26316, Value(int64_t{6})));
auto v26317 = s->Global("_V233_REPORT");
auto v26318 = Value("sheep_commit_requests");
auto v26319 = Get(v26317, v26318);
Put(v26317, v26318, Inplace("Add", v26319, Value(int64_t{1})));
auto v26320 = s->Global("_E343_YX_REPORT");
auto v26321 = Value("yx_day11_commits");
auto v26322 = Get(v26320, v26321);
Put(v26320, v26321, Inplace("Add", v26322, Value(int64_t{1})));
auto v26323 = Value(int64_t{11});
Put(s->Global("_E343_YX_REPORT"), Value("yx_commit_day"), v26323);
auto v26324 = ([&]() -> Value { auto fn26325 = Attribute(s->Global("copy"), "deepcopy"); Arguments args26326; args26326.Add(s->LocalAt(0), false); return Call(c, fn26325, std::move(args26326)); }());
s->SetAt(18, v26324);
auto v26327 = ([&]() -> Value { auto v26328 = ([&]() -> Value { auto fn26329 = s->Global("list"); Arguments args26330; args26330.Add(s->LocalAt(12), false); return Call(c, fn26329, std::move(args26330)); }()); return Binary("Add", v26328, s->LocalAt(6)); }());
Put(s->LocalAt(18), Value("market"), v26327);
return s->LocalAt(18);
}
if (static_cast<bool>(([&]() -> Value { auto v26331 = s->Global("_E343_YX_END"); if (!static_cast<bool>(v26331)) return v26331; v26331 = s->LocalAt(3); if (!static_cast<bool>(v26331)) return v26331; v26331 = ([&]() -> Value { auto v26332 = s->LocalAt(4); Value v26333; v26333 = Value(int64_t{29}); if (!static_cast<bool>(Binary("Eq", v26332, v26333))) return Value(false); v26332 = v26333; return Value(true); }()); if (!static_cast<bool>(v26331)) return v26331; v26331 = ([&]() -> Value { auto v26334 = ([&]() -> Value { auto fn26336 = PrepareDictionaryGet(s->LocalAt(19)); Arguments args26337; args26337.Add(Value("requested_day"), false); return CallDictionaryGet(c, fn26336, std::move(args26337)); }()); Value v26335; v26335 = s->LocalAt(4); if (!static_cast<bool>(Binary("NotEq", v26334, v26335))) return Value(false); v26334 = v26335; return Value(true); }()); return v26331; }()))) {
auto v26338 = Get(s->LocalAt(7), Value("tiles"));
s->SetAt(23, v26338);
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto comp26339 = std::make_shared<Scope>(); comp26339->globals = s->globals; comp26339->parent = s; static constexpr const char* comp26339_names[] = {"x", "y"}; comp26339->PrepareSlots(comp26339_names); auto result26340 = List(); for (const auto& item26341 : Iterate(s->Global("_E343_YX_TILES"))) { auto unpack26342 = Iterate(item26341); ValidateUnpack(unpack26342, 2, false); comp26339->SetAt(0, unpack26342.at(0)); comp26339->SetAt(1, unpack26342.at(1)); if (static_cast<bool>(([&]() -> Value { auto v26343 = ([&]() -> Value { auto fn26344 = comp26339->Global("isinstance"); Arguments args26345; args26345.positional.reserve(2); args26345.Add(Get(Get(comp26339->Captured("tiles"), comp26339->LocalAt(1)), comp26339->LocalAt(0)), false); args26345.Add(comp26339->Global("dict"), false); return Call(c, fn26344, std::move(args26345)); }()); if (!static_cast<bool>(v26343)) return v26343; v26343 = ([&]() -> Value { auto v26346 = ([&]() -> Value { auto fn26348 = PrepareDictionaryGet(Get(Get(comp26339->Captured("tiles"), comp26339->LocalAt(1)), comp26339->LocalAt(0))); Arguments args26349; args26349.Add(Value("animal"), false); return CallDictionaryGet(c, fn26348, std::move(args26349)); }()); Value v26347; v26347 = Value("SHEEP"); if (!static_cast<bool>(Binary("Eq", v26346, v26347))) return Value(false); v26346 = v26347; return Value(true); }()); if (!static_cast<bool>(v26343)) return v26343; v26343 = ([&]() -> Value { auto v26350 = ([&]() -> Value { auto fn26352 = comp26339->Global("int"); Arguments args26353; args26353.Add(([&]() -> Value { auto fn26354 = PrepareDictionaryGet(Get(Get(comp26339->Captured("tiles"), comp26339->LocalAt(1)), comp26339->LocalAt(0))); Arguments args26355; args26355.positional.reserve(2); args26355.Add(Value("yield_units"), false); args26355.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn26354, std::move(args26355)); }()), false); return Call(c, fn26352, std::move(args26353)); }()); Value v26351; v26351 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v26350, v26351))) return Value(false); v26350 = v26351; return Value(true); }()); return v26343; }()))) return Value(true); } return Value(false); }())))) {
auto v26356 = s->LocalAt(4);
Put(s->LocalAt(19), Value("requested_day"), v26356);
auto v26357 = s->Global("_E343_YX_REPORT");
auto v26358 = Value("yx_day29_norequest");
auto v26359 = Get(v26357, v26358);
Put(v26357, v26358, Inplace("Add", v26359, Value(int64_t{1})));
return s->LocalAt(0);
}
auto v26360 = ([&]() -> Value { auto fn26361 = s->Global("list"); Arguments args26362; args26362.Add(([&]() -> Value { auto v26363 = ([&]() -> Value { auto fn26364 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args26365; args26365.positional.reserve(2); args26365.Add(Value("market"), false); args26365.Add(List({}), false); return CallDictionaryGet(c, fn26364, std::move(args26365)); }()); if (static_cast<bool>(v26363)) return v26363; v26363 = List({}); return v26363; }()), false); return Call(c, fn26361, std::move(args26362)); }());
s->SetAt(1, v26360);
auto v26366 = ([&]() -> Value { auto fn26367 = s->Global("_E343_YX_ORIG_REQUEST"); Arguments args26368; args26368.positional.reserve(4); args26368.Add(s->LocalAt(15), false); args26368.Add(s->LocalAt(0), false); args26368.Add(s->LocalAt(19), false); args26368.Add(s->LocalAt(13), false); return Call(c, fn26367, std::move(args26368)); }());
s->SetAt(18, v26366);
if (static_cast<bool>(([&]() -> Value { auto v26369 = ([&]() -> Value { auto v26370 = s->LocalAt(18); Value v26371; v26371 = s->LocalAt(0); if (!static_cast<bool>(Binary("IsNot", v26370, v26371))) return Value(false); v26370 = v26371; return Value(true); }()); if (!static_cast<bool>(v26369)) return v26369; v26369 = ([&]() -> Value { auto v26372 = ([&]() -> Value { auto fn26374 = PrepareDictionaryGet(s->LocalAt(19)); Arguments args26375; args26375.Add(Value("requested_day"), false); return CallDictionaryGet(c, fn26374, std::move(args26375)); }()); Value v26373; v26373 = s->LocalAt(4); if (!static_cast<bool>(Binary("Eq", v26372, v26373))) return Value(false); v26372 = v26373; return Value(true); }()); return v26369; }()))) {
auto v26376 = ([&]() -> Value { auto fn26377 = s->Global("list"); Arguments args26378; args26378.Add(Get(s->LocalAt(18), Value("market")), false); return Call(c, fn26377, std::move(args26378)); }());
s->SetAt(11, v26376);
for (const auto& item26379 : Iterate(([&]() -> Value { auto fn26380 = s->Global("range"); Arguments args26381; args26381.positional.reserve(3); args26381.Add(([&]() -> Value { auto v26382 = ([&]() -> Value { auto fn26383 = s->Global("len"); Arguments args26384; args26384.Add(s->LocalAt(11), false); return Call(c, fn26383, std::move(args26384)); }()); return Binary("Sub", v26382, Value(int64_t{1})); }()), false); args26381.Add(([&]() -> Value { auto v26385 = ([&]() -> Value { auto fn26386 = s->Global("len"); Arguments args26387; args26387.Add(s->LocalAt(1), false); return Call(c, fn26386, std::move(args26387)); }()); return Binary("Sub", v26385, Value(int64_t{1})); }()), false); args26381.Add(Unary("USub", Value(int64_t{1})), false); return Call(c, fn26380, std::move(args26381)); }()))) {
s->SetAt(9, item26379);
if (static_cast<bool>(([&]() -> Value { auto v26388 = Slice(Get(s->LocalAt(11), s->LocalAt(9)), Value{}, Value(int64_t{2}), Value{}); Value v26389; v26389 = List({Value("BUY_PRODUCT"), Value("WHEAT")}); if (!static_cast<bool>(Binary("Eq", v26388, v26389))) return Value(false); v26388 = v26389; return Value(true); }()))) {
Erase(s->LocalAt(11), s->LocalAt(9));
auto v26390 = s->Global("_E343_YX_REPORT");
auto v26391 = Value("yx_day29_nowheat");
auto v26392 = Get(v26390, v26391);
Put(v26390, v26391, Inplace("Add", v26392, Value(int64_t{1})));
break;
}
}
auto v26393 = s->LocalAt(11);
Put(s->LocalAt(18), Value("market"), v26393);
}
return s->LocalAt(18);
}
return ([&]() -> Value { auto fn26394 = s->Global("_E343_YX_ORIG_REQUEST"); Arguments args26395; args26395.positional.reserve(4); args26395.Add(s->LocalAt(15), false); args26395.Add(s->LocalAt(0), false); args26395.Add(s->LocalAt(19), false); args26395.Add(s->LocalAt(13), false); return Call(c, fn26394, std::move(args26395)); }());
return {};
}
}  // namespace kagg::opponents::compiled
