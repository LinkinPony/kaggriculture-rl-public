// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_c0a7cd14516f34cc2bbb(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"_", "actor", "bundles", "carried", "chosen", "cursor", "direct", "distance", "event", "farm", "first", "future_deposits", "horizon", "inventory", "item", "key", "mature", "max_per_actor", "obligation", "offset", "operations", "ops", "owners", "pos", "prefix_deposits", "prices", "private", "proposals", "route", "row", "run", "second", "seen", "stops", "tile", "value", "variants", "x", "xy", "y"};
s->PrepareSlots(s_names);
auto v3152 = ([&]() -> Value { auto dict3153 = Dict(); return dict3153; }());
s->SetAt(22, v3152);
for (const auto& item3154 : Iterate(Get(s->LocalAt(30), Value("events")))) {
s->SetAt(8, item3154);
if (static_cast<bool>(([&]() -> Value { auto v3155 = Value("acquired"); Value v3156; v3156 = s->LocalAt(8); if (!static_cast<bool>(Binary("In", v3155, v3156))) return Value(false); v3155 = v3156; return Value(true); }()))) {
(void)([&]() -> Value { auto fn3157 = Attribute(([&]() -> Value { auto fn3159 = Attribute(s->LocalAt(22), "setdefault"); Arguments args3160; args3160.positional.reserve(2); args3160.Add(Tuple({([&]() -> Value { auto fn3161 = s->Global("tuple"); Arguments args3162; args3162.Add(Get(s->LocalAt(8), Value("xy")), false); return Call(c, fn3161, std::move(args3162)); }()), Get(s->LocalAt(8), Value("op"))}), false); args3160.Add(([&]() -> Value { auto fn3163 = s->Global("set"); Arguments args3164; return Call(c, fn3163, std::move(args3164)); }()), false); return Call(c, fn3159, std::move(args3160)); }()), "add"); Arguments args3158; args3158.Add(Get(s->LocalAt(8), Value("actor")), false); return Call(c, fn3157, std::move(args3158)); }());
}
}
auto v3165 = List({});
s->SetAt(27, v3165);
auto v3166 = ([&]() -> Value { auto fn3167 = s->Global("set"); Arguments args3168; return Call(c, fn3167, std::move(args3168)); }());
s->SetAt(32, v3166);
auto v3169 = ([&]() -> Value { auto fn3170 = s->Global("len"); Arguments args3171; args3171.Add(Get(s->LocalAt(30), Value("rows")), false); return Call(c, fn3170, std::move(args3171)); }());
s->SetAt(12, v3169);
for (const auto& item3172 : Iterate(([&]() -> Value { auto fn3173 = s->Global("range"); Arguments args3174; args3174.Add(s->LocalAt(12), false); return Call(c, fn3173, std::move(args3174)); }()))) {
s->SetAt(19, item3172);
auto v3175 = Get(Get(s->LocalAt(30), Value("states")), s->LocalAt(19));
auto unpack3176 = Iterate(v3175);
ValidateUnpack(unpack3176, 2, false);
s->SetAt(9, unpack3176.at(0));
s->SetAt(26, unpack3176.at(1));
auto v3177 = ([&]() -> Value { auto fn3178 = s->Global("tuple"); Arguments args3179; args3179.Add((static_cast<bool>(([&]() -> Value { auto v3180 = s->LocalAt(1); Value v3181; v3181 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v3180, v3181))) return Value(false); v3180 = v3181; return Value(true); }())) ? Get(s->LocalAt(9), Value("farmer")) : Get(Get(s->LocalAt(9), Value("hands")), ([&]() -> Value { auto v3182 = s->LocalAt(1); return Binary("Sub", v3182, Value(int64_t{1})); }()))), false); return Call(c, fn3178, std::move(args3179)); }());
s->SetAt(23, v3177);
auto v3183 = Get(Get(s->LocalAt(26), Value("inventories")), s->LocalAt(1));
s->SetAt(13, v3183);
auto v3184 = ([&]() -> Value { auto fn3185 = s->Global("sum"); Arguments args3186; args3186.Add(([&]() -> Value { auto comp3187 = std::make_shared<Scope>(); comp3187->globals = s->globals; comp3187->parent = s; static constexpr const char* comp3187_names[] = {"count", "item"}; comp3187->PrepareSlots(comp3187_names); auto result3188 = List(); for (const auto& item3189 : Iterate(([&]() -> Value { auto fn3190 = Attribute(s->LocalAt(13), "items"); Arguments args3191; return Call(c, fn3190, std::move(args3191)); }()))) { auto unpack3192 = Iterate(item3189); ValidateUnpack(unpack3192, 2, false); comp3187->SetAt(1, unpack3192.at(0)); comp3187->SetAt(0, unpack3192.at(1)); result3188.node()->sequence.push_back(([&]() -> Value { auto v3193 = ([&]() -> Value { auto fn3194 = PrepareDictionaryGet(comp3187->Captured("prices")); Arguments args3195; args3195.positional.reserve(2); args3195.Add(comp3187->LocalAt(1), false); args3195.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn3194, std::move(args3195)); }()); return Binary("Mult", v3193, comp3187->LocalAt(0)); }())); } return result3188; }()), false); return Call(c, fn3185, std::move(args3186)); }());
s->SetAt(3, v3184);
auto v3196 = (static_cast<bool>(s->LocalAt(19)) ? Get(Get(Get(Get(s->LocalAt(30), Value("rows")), ([&]() -> Value { auto v3197 = s->LocalAt(19); return Binary("Sub", v3197, Value(int64_t{1})); }())), Value("deposited_by_actor")), s->LocalAt(1)) : ([&]() -> Value { auto dict3198 = Dict(); return dict3198; }()));
s->SetAt(24, v3196);
auto v3199 = Get(Get(Get(Get(s->LocalAt(30), Value("rows")), Unary("USub", Value(int64_t{1}))), Value("deposited_by_actor")), s->LocalAt(1));
s->SetAt(11, v3199);
auto v3200 = ([&]() -> Value { auto fn3201 = s->Global("sum"); Arguments args3202; args3202.Add(([&]() -> Value { auto comp3203 = std::make_shared<Scope>(); comp3203->globals = s->globals; comp3203->parent = s; static constexpr const char* comp3203_names[] = {"count", "item"}; comp3203->PrepareSlots(comp3203_names); auto result3204 = List(); for (const auto& item3205 : Iterate(([&]() -> Value { auto fn3206 = Attribute(s->LocalAt(11), "items"); Arguments args3207; return Call(c, fn3206, std::move(args3207)); }()))) { auto unpack3208 = Iterate(item3205); ValidateUnpack(unpack3208, 2, false); comp3203->SetAt(1, unpack3208.at(0)); comp3203->SetAt(0, unpack3208.at(1)); result3204.node()->sequence.push_back(([&]() -> Value { auto v3209 = ([&]() -> Value { auto fn3210 = PrepareDictionaryGet(comp3203->Captured("prices")); Arguments args3211; args3211.positional.reserve(2); args3211.Add(comp3203->LocalAt(1), false); args3211.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn3210, std::move(args3211)); }()); return Binary("Mult", v3209, ([&]() -> Value { auto v3212 = comp3203->LocalAt(0); return Binary("Sub", v3212, ([&]() -> Value { auto fn3213 = PrepareDictionaryGet(comp3203->Captured("prefix_deposits")); Arguments args3214; args3214.positional.reserve(2); args3214.Add(comp3203->LocalAt(1), false); args3214.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn3213, std::move(args3214)); }())); }())); }())); } return result3204; }()), false); return Call(c, fn3201, std::move(args3202)); }());
s->SetAt(18, v3200);
auto v3215 = List({});
s->SetAt(2, v3215);
for (const auto& item3216 : Iterate(([&]() -> Value { auto fn3217 = s->Global("enumerate"); Arguments args3218; args3218.Add(Get(s->LocalAt(9), Value("tiles")), false); return Call(c, fn3217, std::move(args3218)); }()))) {
auto unpack3219 = Iterate(item3216);
ValidateUnpack(unpack3219, 2, false);
s->SetAt(39, unpack3219.at(0));
s->SetAt(29, unpack3219.at(1));
for (const auto& item3220 : Iterate(([&]() -> Value { auto fn3221 = s->Global("enumerate"); Arguments args3222; args3222.Add(s->LocalAt(29), false); return Call(c, fn3221, std::move(args3222)); }()))) {
auto unpack3223 = Iterate(item3220);
ValidateUnpack(unpack3223, 2, false);
s->SetAt(37, unpack3223.at(0));
s->SetAt(34, unpack3223.at(1));
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto fn3224 = s->Global("isinstance"); Arguments args3225; args3225.positional.reserve(2); args3225.Add(s->LocalAt(34), false); args3225.Add(s->Global("dict"), false); return Call(c, fn3224, std::move(args3225)); }())))) {
continue;
}
auto v3226 = Tuple({Tuple({s->LocalAt(37), s->LocalAt(39)}), List({}), Value(int64_t{0})});
auto unpack3227 = Iterate(v3226);
ValidateUnpack(unpack3227, 3, false);
s->SetAt(38, unpack3227.at(0));
s->SetAt(20, unpack3227.at(1));
s->SetAt(35, unpack3227.at(2));
if (static_cast<bool>(([&]() -> Value { auto v3228 = ([&]() -> Value { auto fn3230 = PrepareDictionaryGet(s->LocalAt(34)); Arguments args3231; args3231.positional.reserve(2); args3231.Add(Value("yield_units"), false); args3231.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn3230, std::move(args3231)); }()); Value v3229; v3229 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v3228, v3229))) return Value(false); v3228 = v3229; return Value(true); }()))) {
auto v3232 = (static_cast<bool>(([&]() -> Value { auto v3233 = ([&]() -> Value { auto fn3235 = PrepareDictionaryGet(s->LocalAt(34)); Arguments args3236; args3236.Add(Value("kind"), false); return CallDictionaryGet(c, fn3235, std::move(args3236)); }()); Value v3234; v3234 = Value("PLANT"); if (!static_cast<bool>(Binary("Eq", v3233, v3234))) return Value(false); v3233 = v3234; return Value(true); }())) ? ([&]() -> Value { auto fn3237 = PrepareDictionaryGet(s->LocalAt(34)); Arguments args3238; args3238.Add(Value("crop"), false); return CallDictionaryGet(c, fn3237, std::move(args3238)); }()) : ([&]() -> Value { auto fn3239 = PrepareDictionaryGet(([&]() -> Value { auto fn3241 = PrepareDictionaryGet(s->Global("ANIMALS")); Arguments args3242; args3242.positional.reserve(2); args3242.Add(([&]() -> Value { auto fn3243 = PrepareDictionaryGet(s->LocalAt(34)); Arguments args3244; args3244.Add(Value("animal"), false); return CallDictionaryGet(c, fn3243, std::move(args3244)); }()), false); args3242.Add(([&]() -> Value { auto dict3245 = Dict(); return dict3245; }()), false); return CallDictionaryGet(c, fn3241, std::move(args3242)); }())); Arguments args3240; args3240.Add(Value("product"), false); return CallDictionaryGet(c, fn3239, std::move(args3240)); }()));
s->SetAt(14, v3232);
auto v3246 = ([&]() -> Value { auto v3247 = s->LocalAt(14); if (!static_cast<bool>(v3247)) return v3247; v3247 = ([&]() -> Value { auto v3248 = ([&]() -> Value { auto v3249 = Value("animal"); Value v3250; v3250 = s->LocalAt(34); if (!static_cast<bool>(Binary("In", v3249, v3250))) return Value(false); v3249 = v3250; return Value(true); }()); if (static_cast<bool>(v3248)) return v3248; v3248 = ([&]() -> Value { auto v3251 = ([&]() -> Value { auto v3253 = ([&]() -> Value { auto v3254 = ([&]() -> Value { auto v3255 = s->Global("START"); return Binary("Add", v3255, s->LocalAt(19)); }()); return Binary("FloorDiv", v3254, Value(int64_t{24})); }()); return Binary("Sub", v3253, Get(s->LocalAt(34), Value("planted_day"))); }()); Value v3252; v3252 = Get(Get(s->Global("CROPS"), s->LocalAt(14)), Value("first_yield_day")); if (!static_cast<bool>(Binary("GtE", v3251, v3252))) return Value(false); v3251 = v3252; return Value(true); }()); return v3248; }()); return v3247; }());
s->SetAt(16, v3246);
if (static_cast<bool>(([&]() -> Value { auto v3256 = s->LocalAt(16); if (!static_cast<bool>(v3256)) return v3256; v3256 = Unary("Not", ([&]() -> Value { auto v3257 = ([&]() -> Value { auto fn3258 = PrepareDictionaryGet(s->LocalAt(22)); Arguments args3259; args3259.positional.reserve(2); args3259.Add(Tuple({s->LocalAt(38), Value("HARVEST")}), false); args3259.Add(([&]() -> Value { auto fn3260 = s->Global("set"); Arguments args3261; return Call(c, fn3260, std::move(args3261)); }()), false); return CallDictionaryGet(c, fn3258, std::move(args3259)); }()); return Binary("Sub", v3257, Set({s->LocalAt(1)})); }())); return v3256; }()))) {
(void)([&]() -> Value { auto fn3262 = Attribute(s->LocalAt(20), "append"); Arguments args3263; args3263.Add(List({Value("HARVEST")}), false); return Call(c, fn3262, std::move(args3263)); }());
auto v3264 = s->LocalAt(35);
s->SetAt(35, Inplace("Add", v3264, ([&]() -> Value { auto v3265 = Get(s->LocalAt(25), s->LocalAt(14)); return Binary("Mult", v3265, Get(s->LocalAt(34), Value("yield_units"))); }())));
}
}
if (static_cast<bool>(([&]() -> Value { auto v3266 = ([&]() -> Value { auto fn3267 = PrepareDictionaryGet(s->LocalAt(34)); Arguments args3268; args3268.Add(Value("fertilizer_available"), false); return CallDictionaryGet(c, fn3267, std::move(args3268)); }()); if (!static_cast<bool>(v3266)) return v3266; v3266 = ([&]() -> Value { auto v3269 = Value("animal"); Value v3270; v3270 = s->LocalAt(34); if (!static_cast<bool>(Binary("In", v3269, v3270))) return Value(false); v3269 = v3270; return Value(true); }()); if (!static_cast<bool>(v3266)) return v3266; v3266 = Unary("Not", ([&]() -> Value { auto v3271 = ([&]() -> Value { auto fn3272 = PrepareDictionaryGet(s->LocalAt(22)); Arguments args3273; args3273.positional.reserve(2); args3273.Add(Tuple({s->LocalAt(38), Value("COLLECT_FERTILIZER")}), false); args3273.Add(([&]() -> Value { auto fn3274 = s->Global("set"); Arguments args3275; return Call(c, fn3274, std::move(args3275)); }()), false); return CallDictionaryGet(c, fn3272, std::move(args3273)); }()); return Binary("Sub", v3271, Set({s->LocalAt(1)})); }())); return v3266; }()))) {
(void)([&]() -> Value { auto fn3276 = Attribute(s->LocalAt(20), "append"); Arguments args3277; args3277.Add(List({Value("COLLECT_FERTILIZER")}), false); return Call(c, fn3276, std::move(args3277)); }());
auto v3278 = s->LocalAt(35);
s->SetAt(35, Inplace("Add", v3278, Get(s->LocalAt(25), Value("FERTILIZER"))));
}
if (static_cast<bool>(s->LocalAt(20))) {
auto v3279 = ([&]() -> Value { auto v3280 = ([&]() -> Value { auto v3281 = ([&]() -> Value { auto fn3282 = s->Global("len"); Arguments args3283; args3283.Add(([&]() -> Value { auto fn3284 = s->Global("_walk"); Arguments args3285; args3285.positional.reserve(2); args3285.Add(s->LocalAt(23), false); args3285.Add(s->LocalAt(38), false); return Call(c, fn3284, std::move(args3285)); }()), false); return Call(c, fn3282, std::move(args3283)); }()); return Binary("Add", v3281, ([&]() -> Value { auto fn3286 = s->Global("len"); Arguments args3287; args3287.Add(s->LocalAt(20), false); return Call(c, fn3286, std::move(args3287)); }())); }()); return Binary("Add", v3280, ([&]() -> Value { auto fn3288 = s->Global("len"); Arguments args3289; args3289.Add(([&]() -> Value { auto fn3290 = s->Global("_return"); Arguments args3291; args3291.Add(s->LocalAt(38), false); return Call(c, fn3290, std::move(args3291)); }()), false); return Call(c, fn3288, std::move(args3289)); }())); }());
s->SetAt(7, v3279);
if (static_cast<bool>(([&]() -> Value { auto v3292 = s->LocalAt(7); Value v3293; v3293 = ([&]() -> Value { auto v3294 = s->LocalAt(12); return Binary("Sub", v3294, s->LocalAt(19)); }()); if (!static_cast<bool>(Binary("LtE", v3292, v3293))) return Value(false); v3292 = v3293; return Value(true); }()))) {
(void)([&]() -> Value { auto fn3295 = Attribute(s->LocalAt(2), "append"); Arguments args3296; args3296.Add(Tuple({s->LocalAt(38), s->LocalAt(20), s->LocalAt(35), s->LocalAt(7)}), false); return Call(c, fn3295, std::move(args3296)); }());
}
}
}
}
(void)([&]() -> Value { auto fn3297 = Attribute(s->LocalAt(2), "sort"); Arguments args3298; args3298.Keyword("key", Define(&Code_7919700657fcef6a8187, s, Signature{{"b"}, {}, {}, {}, "", "", ([]() -> std::span<const char* const> { static constexpr const char* names[] = {"b"}; return names; }())}, true, "<lambda>")); return Call(c, fn3297, std::move(args3298)); }());
auto v3300 = (static_cast<bool>(s->LocalAt(3)) ? List({Tuple({List({}), s->LocalAt(3)})}) : List({}));
s->SetAt(36, v3300);
for (const auto& item3301 : Iterate(Slice(s->LocalAt(2), Value{}, Value(int64_t{6}), Value{}))) {
auto unpack3302 = Iterate(item3301);
ValidateUnpack(unpack3302, 4, false);
s->SetAt(38, unpack3302.at(0));
s->SetAt(21, unpack3302.at(1));
s->SetAt(35, unpack3302.at(2));
s->SetAt(0, unpack3302.at(3));
(void)([&]() -> Value { auto fn3303 = Attribute(s->LocalAt(36), "append"); Arguments args3304; args3304.Add(Tuple({List({Tuple({s->LocalAt(38), s->LocalAt(21)})}), ([&]() -> Value { auto v3305 = s->LocalAt(3); return Binary("Add", v3305, s->LocalAt(35)); }())}), false); return Call(c, fn3303, std::move(args3304)); }());
}
for (const auto& item3306 : Iterate(Slice(s->LocalAt(2), Value{}, Value(int64_t{3}), Value{}))) {
s->SetAt(10, item3306);
for (const auto& item3307 : Iterate(Slice(s->LocalAt(2), Value{}, Value(int64_t{3}), Value{}))) {
s->SetAt(31, item3307);
if (static_cast<bool>(([&]() -> Value { auto v3308 = Get(s->LocalAt(10), Value(int64_t{0})); Value v3309; v3309 = Get(s->LocalAt(31), Value(int64_t{0})); if (!static_cast<bool>(Binary("NotEq", v3308, v3309))) return Value(false); v3308 = v3309; return Value(true); }()))) {
(void)([&]() -> Value { auto fn3310 = Attribute(s->LocalAt(36), "append"); Arguments args3311; args3311.Add(Tuple({List({Tuple({Get(s->LocalAt(10), Value(int64_t{0})), Get(s->LocalAt(10), Value(int64_t{1}))}), Tuple({Get(s->LocalAt(31), Value(int64_t{0})), Get(s->LocalAt(31), Value(int64_t{1}))})}), ([&]() -> Value { auto v3312 = ([&]() -> Value { auto v3313 = s->LocalAt(3); return Binary("Add", v3313, Get(s->LocalAt(10), Value(int64_t{2}))); }()); return Binary("Add", v3312, Get(s->LocalAt(31), Value(int64_t{2}))); }())}), false); return Call(c, fn3310, std::move(args3311)); }());
}
}
}
for (const auto& item3314 : Iterate(s->LocalAt(36))) {
auto unpack3315 = Iterate(item3314);
ValidateUnpack(unpack3315, 2, false);
s->SetAt(33, unpack3315.at(0));
s->SetAt(35, unpack3315.at(1));
auto v3316 = Tuple({List({}), s->LocalAt(23)});
auto unpack3317 = Iterate(v3316);
ValidateUnpack(unpack3317, 2, false);
s->SetAt(28, unpack3317.at(0));
s->SetAt(5, unpack3317.at(1));
for (const auto& item3318 : Iterate(s->LocalAt(33))) {
auto unpack3319 = Iterate(item3318);
ValidateUnpack(unpack3319, 2, false);
s->SetAt(38, unpack3319.at(0));
s->SetAt(21, unpack3319.at(1));
auto v3320 = s->LocalAt(28);
s->SetAt(28, Inplace("Add", v3320, ([&]() -> Value { auto v3321 = ([&]() -> Value { auto fn3322 = s->Global("_walk"); Arguments args3323; args3323.positional.reserve(2); args3323.Add(s->LocalAt(5), false); args3323.Add(s->LocalAt(38), false); return Call(c, fn3322, std::move(args3323)); }()); return Binary("Add", v3321, s->LocalAt(21)); }())));
auto v3324 = s->LocalAt(38);
s->SetAt(5, v3324);
}
auto v3325 = s->LocalAt(28);
s->SetAt(28, Inplace("Add", v3325, ([&]() -> Value { auto fn3326 = s->Global("_return"); Arguments args3327; args3327.Add(s->LocalAt(5), false); return Call(c, fn3326, std::move(args3327)); }())));
if (static_cast<bool>(([&]() -> Value { auto v3328 = ([&]() -> Value { auto fn3330 = s->Global("len"); Arguments args3331; args3331.Add(s->LocalAt(28), false); return Call(c, fn3330, std::move(args3331)); }()); Value v3329; v3329 = ([&]() -> Value { auto v3332 = s->LocalAt(12); return Binary("Sub", v3332, s->LocalAt(19)); }()); if (!static_cast<bool>(Binary("Gt", v3328, v3329))) return Value(false); v3328 = v3329; return Value(true); }()))) {
continue;
}
auto v3333 = s->LocalAt(28);
s->SetAt(28, Inplace("Add", v3333, ([&]() -> Value { auto v3334 = List({List({Value("PASS")})}); return Binary("Mult", v3334, ([&]() -> Value { auto v3335 = ([&]() -> Value { auto v3336 = s->LocalAt(12); return Binary("Sub", v3336, s->LocalAt(19)); }()); return Binary("Sub", v3335, ([&]() -> Value { auto fn3337 = s->Global("len"); Arguments args3338; args3338.Add(s->LocalAt(28), false); return Call(c, fn3337, std::move(args3338)); }())); }())); }())));
auto v3339 = Tuple({s->LocalAt(19), ([&]() -> Value { auto fn3340 = s->Global("tuple"); Arguments args3341; args3341.Add(([&]() -> Value { auto comp3342 = std::make_shared<Scope>(); comp3342->globals = s->globals; comp3342->parent = s; static constexpr const char* comp3342_names[] = {"c"}; comp3342->PrepareSlots(comp3342_names); auto result3343 = List(); for (const auto& item3344 : Iterate(s->LocalAt(28))) { comp3342->SetAt(0, item3344); result3343.node()->sequence.push_back(([&]() -> Value { auto fn3345 = comp3342->Global("tuple"); Arguments args3346; args3346.Add(comp3342->LocalAt(0), false); return Call(c, fn3345, std::move(args3346)); }())); } return result3343; }()), false); return Call(c, fn3340, std::move(args3341)); }())});
s->SetAt(15, v3339);
if (static_cast<bool>(([&]() -> Value { auto v3347 = s->LocalAt(15); Value v3348; v3348 = s->LocalAt(32); if (!static_cast<bool>(Binary("NotIn", v3347, v3348))) return Value(false); v3347 = v3348; return Value(true); }()))) {
(void)([&]() -> Value { auto fn3349 = Attribute(s->LocalAt(32), "add"); Arguments args3350; args3350.Add(s->LocalAt(15), false); return Call(c, fn3349, std::move(args3350)); }());
(void)([&]() -> Value { auto fn3351 = Attribute(s->LocalAt(27), "append"); Arguments args3352; args3352.Add(Tuple({([&]() -> Value { auto v3353 = s->LocalAt(35); return Binary("Sub", v3353, s->LocalAt(18)); }()), s->LocalAt(19), s->LocalAt(28), ([&]() -> Value { auto fn3354 = s->Global("len"); Arguments args3355; args3355.Add(s->LocalAt(33), false); return Call(c, fn3354, std::move(args3355)); }())}), false); return Call(c, fn3351, std::move(args3352)); }());
}
}
}
(void)([&]() -> Value { auto fn3356 = Attribute(s->LocalAt(27), "sort"); Arguments args3357; args3357.Keyword("key", Define(&Code_85a5717568583c703879, s, Signature{{"p"}, {}, {}, {}, "", "", ([]() -> std::span<const char* const> { static constexpr const char* names[] = {"p"}; return names; }())}, true, "<lambda>")); return Call(c, fn3356, std::move(args3357)); }());
auto v3358 = Slice(([&]() -> Value { auto comp3359 = std::make_shared<Scope>(); comp3359->globals = s->globals; comp3359->parent = s; static constexpr const char* comp3359_names[] = {"p"}; comp3359->PrepareSlots(comp3359_names); auto result3360 = List(); for (const auto& item3361 : Iterate(s->LocalAt(27))) { comp3359->SetAt(0, item3361); if (!static_cast<bool>(([&]() -> Value { auto v3362 = ([&]() -> Value { auto v3363 = Get(comp3359->LocalAt(0), Value(int64_t{3})); Value v3364; v3364 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v3363, v3364))) return Value(false); v3363 = v3364; return Value(true); }()); if (!static_cast<bool>(v3362)) return v3362; v3362 = ([&]() -> Value { auto v3365 = Get(comp3359->LocalAt(0), Value(int64_t{0})); Value v3366; v3366 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v3365, v3366))) return Value(false); v3365 = v3366; return Value(true); }()); return v3362; }()))) continue; result3360.node()->sequence.push_back(comp3359->LocalAt(0)); } return result3360; }()), Value{}, Value(int64_t{2}), Value{});
s->SetAt(6, v3358);
auto v3367 = ([&]() -> Value { auto v3368 = s->LocalAt(6); return Binary("Add", v3368, ([&]() -> Value { auto comp3369 = std::make_shared<Scope>(); comp3369->globals = s->globals; comp3369->parent = s; static constexpr const char* comp3369_names[] = {"p"}; comp3369->PrepareSlots(comp3369_names); auto result3370 = List(); for (const auto& item3371 : Iterate(s->LocalAt(27))) { comp3369->SetAt(0, item3371); if (!static_cast<bool>(([&]() -> Value { auto v3372 = comp3369->LocalAt(0); Value v3373; v3373 = comp3369->Captured("direct"); if (!static_cast<bool>(Binary("NotIn", v3372, v3373))) return Value(false); v3372 = v3373; return Value(true); }()))) continue; result3370.node()->sequence.push_back(comp3369->LocalAt(0)); } return result3370; }())); }());
s->SetAt(4, v3367);
return Slice(s->LocalAt(4), Value{}, s->LocalAt(17), Value{});
return {};
}
}  // namespace kagg::opponents::compiled
