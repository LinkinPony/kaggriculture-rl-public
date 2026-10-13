// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_f16b59b5213e483c4cef(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "age_days", "available", "board_size", "bonus", "crop", "crop_data", "current", "day", "dx", "dy", "farm", "fx", "fy", "idx", "inv", "item", "n", "nx", "ny", "op", "pos", "private", "room", "shed", "shed_capacity", "take", "tile", "turns_per_day", "units", "window_start"};
s->PrepareSlots(s_names);
if (static_cast<bool>(([&]() -> Value { auto v2168 = Unary("Not", ([&]() -> Value { auto fn2169 = s->Global("isinstance"); Arguments args2170; args2170.positional.reserve(2); args2170.Add(s->LocalAt(0), false); args2170.Add(s->Global("list"), false); return Call(c, fn2169, std::move(args2170)); }())); if (static_cast<bool>(v2168)) return v2168; v2168 = Unary("Not", s->LocalAt(0)); return v2168; }()))) {
return Value{};
}
auto v2171 = Get(s->LocalAt(0), Value(int64_t{0}));
s->SetAt(20, v2171);
auto v2172 = ([&]() -> Value { auto fn2173 = s->Global("_farmer_position"); Arguments args2174; args2174.positional.reserve(2); args2174.Add(s->LocalAt(11), false); args2174.Add(s->LocalAt(14), false); return Call(c, fn2173, std::move(args2174)); }());
s->SetAt(21, v2172);
if (static_cast<bool>(([&]() -> Value { auto v2175 = s->LocalAt(21); Value v2176; v2176 = Value{}; if (!static_cast<bool>(Binary("Is", v2175, v2176))) return Value(false); v2175 = v2176; return Value(true); }()))) {
return Value{};
}
auto v2177 = Tuple({Get(s->LocalAt(21), Value(int64_t{0})), Get(s->LocalAt(21), Value(int64_t{1}))});
auto unpack2178 = Iterate(v2177);
ValidateUnpack(unpack2178, 2, false);
s->SetAt(12, unpack2178.at(0));
s->SetAt(13, unpack2178.at(1));
auto v2179 = ([&]() -> Value { auto fn2180 = s->Global("_farmer_inventory"); Arguments args2181; args2181.positional.reserve(2); args2181.Add(s->LocalAt(22), false); args2181.Add(s->LocalAt(14), false); return Call(c, fn2180, std::move(args2181)); }());
s->SetAt(15, v2179);
if (static_cast<bool>(([&]() -> Value { auto v2182 = s->LocalAt(20); Value v2183; v2183 = s->Global("FARMER_MOVES"); if (!static_cast<bool>(Binary("In", v2182, v2183))) return Value(false); v2182 = v2183; return Value(true); }()))) {
auto v2184 = Get(s->Global("FARMER_MOVES"), s->LocalAt(20));
auto unpack2185 = Iterate(v2184);
ValidateUnpack(unpack2185, 2, false);
s->SetAt(9, unpack2185.at(0));
s->SetAt(10, unpack2185.at(1));
auto v2186 = Tuple({([&]() -> Value { auto v2187 = s->LocalAt(12); return Binary("Add", v2187, s->LocalAt(9)); }()), ([&]() -> Value { auto v2188 = s->LocalAt(13); return Binary("Add", v2188, s->LocalAt(10)); }())});
auto unpack2189 = Iterate(v2186);
ValidateUnpack(unpack2189, 2, false);
s->SetAt(18, unpack2189.at(0));
s->SetAt(19, unpack2189.at(1));
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto v2190 = ([&]() -> Value { auto v2191 = Value(int64_t{0}); Value v2192; v2192 = s->LocalAt(18); if (!static_cast<bool>(Binary("LtE", v2191, v2192))) return Value(false); v2191 = v2192; v2192 = s->LocalAt(3); if (!static_cast<bool>(Binary("Lt", v2191, v2192))) return Value(false); v2191 = v2192; return Value(true); }()); if (!static_cast<bool>(v2190)) return v2190; v2190 = ([&]() -> Value { auto v2193 = Value(int64_t{0}); Value v2194; v2194 = s->LocalAt(19); if (!static_cast<bool>(Binary("LtE", v2193, v2194))) return Value(false); v2193 = v2194; v2194 = s->LocalAt(3); if (!static_cast<bool>(Binary("Lt", v2193, v2194))) return Value(false); v2193 = v2194; return Value(true); }()); return v2190; }())))) {
return Value{};
}
(void)([&]() -> Value { auto fn2195 = s->Global("_set_farmer_position"); Arguments args2196; args2196.positional.reserve(3); args2196.Add(s->LocalAt(11), false); args2196.Add(s->LocalAt(14), false); args2196.Add(Tuple({s->LocalAt(18), s->LocalAt(19)}), false); return Call(c, fn2195, std::move(args2196)); }());
return Value{};
}
if (static_cast<bool>(([&]() -> Value { auto v2197 = s->LocalAt(20); Value v2198; v2198 = Value("PASS"); if (!static_cast<bool>(Binary("Eq", v2197, v2198))) return Value(false); v2197 = v2198; return Value(true); }()))) {
return Value{};
}
auto v2199 = Get(Get(Get(s->LocalAt(11), Value("tiles")), s->LocalAt(13)), s->LocalAt(12));
s->SetAt(27, v2199);
if (static_cast<bool>(([&]() -> Value { auto v2200 = s->LocalAt(20); Value v2201; v2201 = Value("DROP"); if (!static_cast<bool>(Binary("Eq", v2200, v2201))) return Value(false); v2200 = v2201; return Value(true); }()))) {
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto fn2202 = s->Global("_is_shed_adjacent"); Arguments args2203; args2203.positional.reserve(2); args2203.Add(Tuple({s->LocalAt(12), s->LocalAt(13)}), false); args2203.Add(s->LocalAt(3), false); return Call(c, fn2202, std::move(args2203)); }())))) {
return Value{};
}
auto v2204 = Get(s->LocalAt(22), Value("shed"));
s->SetAt(24, v2204);
for (const auto& item2205 : Iterate(([&]() -> Value { auto fn2206 = s->Global("list"); Arguments args2207; args2207.Add(([&]() -> Value { auto fn2208 = Attribute(s->LocalAt(15), "items"); Arguments args2209; return Call(c, fn2208, std::move(args2209)); }()), false); return Call(c, fn2206, std::move(args2207)); }()))) {
auto unpack2210 = Iterate(item2205);
ValidateUnpack(unpack2210, 2, false);
s->SetAt(16, unpack2210.at(0));
s->SetAt(17, unpack2210.at(1));
if (static_cast<bool>(([&]() -> Value { auto v2211 = s->LocalAt(17); Value v2212; v2212 = Value(int64_t{0}); if (!static_cast<bool>(Binary("LtE", v2211, v2212))) return Value(false); v2211 = v2212; return Value(true); }()))) {
Erase(s->LocalAt(15), s->LocalAt(16));
continue;
}
auto v2213 = ([&]() -> Value { auto fn2214 = s->Global("max"); Arguments args2215; args2215.positional.reserve(2); args2215.Add(Value(int64_t{0}), false); args2215.Add(([&]() -> Value { auto v2216 = s->LocalAt(25); return Binary("Sub", v2216, ([&]() -> Value { auto fn2217 = s->Global("sum"); Arguments args2218; args2218.Add(([&]() -> Value { auto fn2219 = Attribute(s->LocalAt(24), "values"); Arguments args2220; return Call(c, fn2219, std::move(args2220)); }()), false); return Call(c, fn2217, std::move(args2218)); }())); }()), false); return Call(c, fn2214, std::move(args2215)); }());
s->SetAt(23, v2213);
auto v2221 = ([&]() -> Value { auto fn2222 = s->Global("min"); Arguments args2223; args2223.positional.reserve(2); args2223.Add(s->LocalAt(17), false); args2223.Add(s->LocalAt(23), false); return Call(c, fn2222, std::move(args2223)); }());
s->SetAt(26, v2221);
if (static_cast<bool>(([&]() -> Value { auto v2224 = s->LocalAt(26); Value v2225; v2225 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v2224, v2225))) return Value(false); v2224 = v2225; return Value(true); }()))) {
auto v2226 = ([&]() -> Value { auto v2227 = ([&]() -> Value { auto fn2228 = PrepareDictionaryGet(s->LocalAt(24)); Arguments args2229; args2229.positional.reserve(2); args2229.Add(s->LocalAt(16), false); args2229.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn2228, std::move(args2229)); }()); return Binary("Add", v2227, s->LocalAt(26)); }());
Put(s->LocalAt(24), s->LocalAt(16), v2226);
}
Erase(s->LocalAt(15), s->LocalAt(16));
}
return Value{};
}
if (static_cast<bool>(([&]() -> Value { auto v2230 = s->LocalAt(20); Value v2231; v2231 = Value("PICKUP"); if (!static_cast<bool>(Binary("Eq", v2230, v2231))) return Value(false); v2230 = v2231; return Value(true); }()))) {
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto fn2232 = s->Global("_is_shed_adjacent"); Arguments args2233; args2233.positional.reserve(2); args2233.Add(Tuple({s->LocalAt(12), s->LocalAt(13)}), false); args2233.Add(s->LocalAt(3), false); return Call(c, fn2232, std::move(args2233)); }())))) {
return Value{};
}
if (static_cast<bool>(([&]() -> Value { auto v2234 = ([&]() -> Value { auto fn2236 = s->Global("len"); Arguments args2237; args2237.Add(s->LocalAt(0), false); return Call(c, fn2236, std::move(args2237)); }()); Value v2235; v2235 = Value(int64_t{2}); if (!static_cast<bool>(Binary("Lt", v2234, v2235))) return Value(false); v2234 = v2235; return Value(true); }()))) {
return Value{};
}
auto v2238 = Get(s->LocalAt(0), Value(int64_t{1}));
s->SetAt(16, v2238);
auto v2239 = (static_cast<bool>(([&]() -> Value { auto v2240 = ([&]() -> Value { auto fn2242 = s->Global("len"); Arguments args2243; args2243.Add(s->LocalAt(0), false); return Call(c, fn2242, std::move(args2243)); }()); Value v2241; v2241 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v2240, v2241))) return Value(false); v2240 = v2241; return Value(true); }())) ? ([&]() -> Value { auto fn2244 = s->Global("int"); Arguments args2245; args2245.Add(Get(s->LocalAt(0), Value(int64_t{2})), false); return Call(c, fn2244, std::move(args2245)); }()) : Value(int64_t{1}));
s->SetAt(17, v2239);
if (static_cast<bool>(([&]() -> Value { auto v2246 = s->LocalAt(17); Value v2247; v2247 = Value(int64_t{0}); if (!static_cast<bool>(Binary("LtE", v2246, v2247))) return Value(false); v2246 = v2247; return Value(true); }()))) {
return Value{};
}
auto v2248 = ([&]() -> Value { auto fn2249 = PrepareDictionaryGet(Get(s->LocalAt(22), Value("shed"))); Arguments args2250; args2250.positional.reserve(2); args2250.Add(s->LocalAt(16), false); args2250.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn2249, std::move(args2250)); }());
s->SetAt(2, v2248);
auto v2251 = ([&]() -> Value { auto fn2252 = s->Global("min"); Arguments args2253; args2253.positional.reserve(2); args2253.Add(s->LocalAt(17), false); args2253.Add(s->LocalAt(2), false); return Call(c, fn2252, std::move(args2253)); }());
s->SetAt(17, v2251);
if (static_cast<bool>(([&]() -> Value { auto v2254 = s->LocalAt(17); Value v2255; v2255 = Value(int64_t{0}); if (!static_cast<bool>(Binary("LtE", v2254, v2255))) return Value(false); v2254 = v2255; return Value(true); }()))) {
return Value{};
}
auto v2256 = Get(s->LocalAt(22), Value("shed"));
auto v2257 = s->LocalAt(16);
auto v2258 = Get(v2256, v2257);
Put(v2256, v2257, Inplace("Sub", v2258, s->LocalAt(17)));
(void)([&]() -> Value { auto fn2259 = s->Global("_inv_add"); Arguments args2260; args2260.positional.reserve(3); args2260.Add(s->LocalAt(15), false); args2260.Add(s->LocalAt(16), false); args2260.Add(s->LocalAt(17), false); return Call(c, fn2259, std::move(args2260)); }());
return Value{};
}
if (static_cast<bool>(([&]() -> Value { auto v2261 = s->LocalAt(20); Value v2262; v2262 = Value("PLACE"); if (!static_cast<bool>(Binary("Eq", v2261, v2262))) return Value(false); v2261 = v2262; return Value(true); }()))) {
if (static_cast<bool>(([&]() -> Value { auto v2263 = ([&]() -> Value { auto fn2265 = s->Global("len"); Arguments args2266; args2266.Add(s->LocalAt(0), false); return Call(c, fn2265, std::move(args2266)); }()); Value v2264; v2264 = Value(int64_t{2}); if (!static_cast<bool>(Binary("Lt", v2263, v2264))) return Value(false); v2263 = v2264; return Value(true); }()))) {
return Value{};
}
auto v2267 = Get(s->LocalAt(0), Value(int64_t{1}));
s->SetAt(16, v2267);
if (static_cast<bool>(([&]() -> Value { auto v2268 = ([&]() -> Value { auto v2269 = s->LocalAt(16); Value v2270; v2270 = s->Global("ANIMALS"); if (!static_cast<bool>(Binary("In", v2269, v2270))) return Value(false); v2269 = v2270; return Value(true); }()); if (!static_cast<bool>(v2268)) return v2268; v2268 = ([&]() -> Value { auto fn2271 = s->Global("isinstance"); Arguments args2272; args2272.positional.reserve(2); args2272.Add(s->LocalAt(27), false); args2272.Add(s->Global("dict"), false); return Call(c, fn2271, std::move(args2272)); }()); if (!static_cast<bool>(v2268)) return v2268; v2268 = ([&]() -> Value { auto v2273 = ([&]() -> Value { auto fn2275 = PrepareDictionaryGet(s->LocalAt(27)); Arguments args2276; args2276.Add(Value("kind"), false); return CallDictionaryGet(c, fn2275, std::move(args2276)); }()); Value v2274; v2274 = Get(Get(s->Global("ANIMALS"), s->LocalAt(16)), Value("structure")); if (!static_cast<bool>(Binary("Eq", v2273, v2274))) return Value(false); v2273 = v2274; return Value(true); }()); if (!static_cast<bool>(v2268)) return v2268; v2268 = ([&]() -> Value { auto v2277 = Value("animal"); Value v2278; v2278 = s->LocalAt(27); if (!static_cast<bool>(Binary("NotIn", v2277, v2278))) return Value(false); v2277 = v2278; return Value(true); }()); return v2268; }()))) {
if (static_cast<bool>(([&]() -> Value { auto fn2279 = s->Global("_inv_take"); Arguments args2280; args2280.positional.reserve(3); args2280.Add(s->LocalAt(15), false); args2280.Add(s->LocalAt(16), false); args2280.Add(Value(int64_t{1}), false); return Call(c, fn2279, std::move(args2280)); }()))) {
auto v2281 = ([&]() -> Value { auto fn2282 = s->Global("_new_animal"); Arguments args2283; args2283.positional.reserve(2); args2283.Add(s->LocalAt(16), false); args2283.Add(s->LocalAt(8), false); return Call(c, fn2282, std::move(args2283)); }());
Put(Get(Get(s->LocalAt(11), Value("tiles")), s->LocalAt(13)), s->LocalAt(12), v2281);
}
return Value{};
}
if (static_cast<bool>(([&]() -> Value { auto fn2284 = s->Global("_is_shed_adjacent"); Arguments args2285; args2285.positional.reserve(2); args2285.Add(Tuple({s->LocalAt(12), s->LocalAt(13)}), false); args2285.Add(s->LocalAt(3), false); return Call(c, fn2284, std::move(args2285)); }()))) {
auto v2286 = (static_cast<bool>(([&]() -> Value { auto v2287 = ([&]() -> Value { auto fn2289 = s->Global("len"); Arguments args2290; args2290.Add(s->LocalAt(0), false); return Call(c, fn2289, std::move(args2290)); }()); Value v2288; v2288 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v2287, v2288))) return Value(false); v2287 = v2288; return Value(true); }())) ? ([&]() -> Value { auto fn2291 = s->Global("int"); Arguments args2292; args2292.Add(Get(s->LocalAt(0), Value(int64_t{2})), false); return Call(c, fn2291, std::move(args2292)); }()) : Value(int64_t{1}));
s->SetAt(17, v2286);
if (static_cast<bool>(([&]() -> Value { auto v2293 = s->LocalAt(17); Value v2294; v2294 = Value(int64_t{0}); if (!static_cast<bool>(Binary("LtE", v2293, v2294))) return Value(false); v2293 = v2294; return Value(true); }()))) {
return Value{};
}
auto v2295 = ([&]() -> Value { auto fn2296 = s->Global("min"); Arguments args2297; args2297.positional.reserve(2); args2297.Add(s->LocalAt(17), false); args2297.Add(([&]() -> Value { auto fn2298 = PrepareDictionaryGet(s->LocalAt(15)); Arguments args2299; args2299.positional.reserve(2); args2299.Add(s->LocalAt(16), false); args2299.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn2298, std::move(args2299)); }()), false); return Call(c, fn2296, std::move(args2297)); }());
s->SetAt(17, v2295);
if (static_cast<bool>(([&]() -> Value { auto v2300 = s->LocalAt(17); Value v2301; v2301 = Value(int64_t{0}); if (!static_cast<bool>(Binary("LtE", v2300, v2301))) return Value(false); v2300 = v2301; return Value(true); }()))) {
return Value{};
}
auto v2302 = ([&]() -> Value { auto fn2303 = s->Global("sum"); Arguments args2304; args2304.Add(([&]() -> Value { auto fn2305 = Attribute(Get(s->LocalAt(22), Value("shed")), "values"); Arguments args2306; return Call(c, fn2305, std::move(args2306)); }()), false); return Call(c, fn2303, std::move(args2304)); }());
s->SetAt(7, v2302);
auto v2307 = ([&]() -> Value { auto fn2308 = s->Global("max"); Arguments args2309; args2309.positional.reserve(2); args2309.Add(Value(int64_t{0}), false); args2309.Add(([&]() -> Value { auto v2310 = s->LocalAt(25); return Binary("Sub", v2310, s->LocalAt(7)); }()), false); return Call(c, fn2308, std::move(args2309)); }());
s->SetAt(23, v2307);
auto v2311 = ([&]() -> Value { auto fn2312 = s->Global("min"); Arguments args2313; args2313.positional.reserve(2); args2313.Add(s->LocalAt(17), false); args2313.Add(s->LocalAt(23), false); return Call(c, fn2312, std::move(args2313)); }());
s->SetAt(17, v2311);
if (static_cast<bool>(([&]() -> Value { auto v2314 = s->LocalAt(17); Value v2315; v2315 = Value(int64_t{0}); if (!static_cast<bool>(Binary("LtE", v2314, v2315))) return Value(false); v2314 = v2315; return Value(true); }()))) {
return Value{};
}
auto v2316 = s->LocalAt(15);
auto v2317 = s->LocalAt(16);
auto v2318 = Get(v2316, v2317);
Put(v2316, v2317, Inplace("Sub", v2318, s->LocalAt(17)));
if (static_cast<bool>(([&]() -> Value { auto v2319 = Get(s->LocalAt(15), s->LocalAt(16)); Value v2320; v2320 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v2319, v2320))) return Value(false); v2319 = v2320; return Value(true); }()))) {
Erase(s->LocalAt(15), s->LocalAt(16));
}
auto v2321 = ([&]() -> Value { auto v2322 = ([&]() -> Value { auto fn2323 = PrepareDictionaryGet(Get(s->LocalAt(22), Value("shed"))); Arguments args2324; args2324.positional.reserve(2); args2324.Add(s->LocalAt(16), false); args2324.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn2323, std::move(args2324)); }()); return Binary("Add", v2322, s->LocalAt(17)); }());
Put(Get(s->LocalAt(22), Value("shed")), s->LocalAt(16), v2321);
}
return Value{};
}
if (static_cast<bool>(([&]() -> Value { auto v2325 = s->LocalAt(27); Value v2326; v2326 = Value("LOCKED"); if (!static_cast<bool>(Binary("Eq", v2325, v2326))) return Value(false); v2325 = v2326; return Value(true); }()))) {
return Value{};
}
if (static_cast<bool>(([&]() -> Value { auto v2327 = s->LocalAt(20); Value v2328; v2328 = Value("PLANT"); if (!static_cast<bool>(Binary("Eq", v2327, v2328))) return Value(false); v2327 = v2328; return Value(true); }()))) {
if (static_cast<bool>(([&]() -> Value { auto v2329 = ([&]() -> Value { auto fn2331 = s->Global("len"); Arguments args2332; args2332.Add(s->LocalAt(0), false); return Call(c, fn2331, std::move(args2332)); }()); Value v2330; v2330 = Value(int64_t{2}); if (!static_cast<bool>(Binary("Lt", v2329, v2330))) return Value(false); v2329 = v2330; return Value(true); }()))) {
return Value{};
}
auto v2333 = Get(s->LocalAt(0), Value(int64_t{1}));
s->SetAt(5, v2333);
if (static_cast<bool>(([&]() -> Value { auto v2334 = s->LocalAt(5); Value v2335; v2335 = s->Global("CROPS"); if (!static_cast<bool>(Binary("NotIn", v2334, v2335))) return Value(false); v2334 = v2335; return Value(true); }()))) {
return Value{};
}
if (static_cast<bool>(([&]() -> Value { auto v2336 = s->LocalAt(27); Value v2337; v2337 = Value{}; if (!static_cast<bool>(Binary("IsNot", v2336, v2337))) return Value(false); v2336 = v2337; return Value(true); }()))) {
return Value{};
}
if (static_cast<bool>(([&]() -> Value { auto v2338 = ([&]() -> Value { auto fn2340 = PrepareDictionaryGet(Get(s->LocalAt(22), Value("seeds"))); Arguments args2341; args2341.positional.reserve(2); args2341.Add(s->LocalAt(5), false); args2341.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn2340, std::move(args2341)); }()); Value v2339; v2339 = Value(int64_t{0}); if (!static_cast<bool>(Binary("LtE", v2338, v2339))) return Value(false); v2338 = v2339; return Value(true); }()))) {
return Value{};
}
auto v2342 = Get(s->LocalAt(22), Value("seeds"));
auto v2343 = s->LocalAt(5);
auto v2344 = Get(v2342, v2343);
Put(v2342, v2343, Inplace("Sub", v2344, Value(int64_t{1})));
auto v2345 = ([&]() -> Value { auto fn2346 = s->Global("_new_plant"); Arguments args2347; args2347.positional.reserve(3); args2347.Add(s->LocalAt(5), false); args2347.Add(s->LocalAt(8), false); args2347.Add(s->LocalAt(28), false); return Call(c, fn2346, std::move(args2347)); }());
Put(Get(Get(s->LocalAt(11), Value("tiles")), s->LocalAt(13)), s->LocalAt(12), v2345);
return Value{};
}
if (static_cast<bool>(([&]() -> Value { auto v2348 = s->LocalAt(20); Value v2349; v2349 = Value("WATER"); if (!static_cast<bool>(Binary("Eq", v2348, v2349))) return Value(false); v2348 = v2349; return Value(true); }()))) {
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto v2350 = ([&]() -> Value { auto fn2351 = s->Global("isinstance"); Arguments args2352; args2352.positional.reserve(2); args2352.Add(s->LocalAt(27), false); args2352.Add(s->Global("dict"), false); return Call(c, fn2351, std::move(args2352)); }()); if (!static_cast<bool>(v2350)) return v2350; v2350 = ([&]() -> Value { auto v2353 = ([&]() -> Value { auto fn2355 = PrepareDictionaryGet(s->LocalAt(27)); Arguments args2356; args2356.Add(Value("kind"), false); return CallDictionaryGet(c, fn2355, std::move(args2356)); }()); Value v2354; v2354 = Value("PLANT"); if (!static_cast<bool>(Binary("Eq", v2353, v2354))) return Value(false); v2353 = v2354; return Value(true); }()); return v2350; }())))) {
return Value{};
}
if (static_cast<bool>(Get(s->LocalAt(27), Value("watered_today")))) {
return Value{};
}
auto v2357 = Value(true);
Put(s->LocalAt(27), Value("watered_today"), v2357);
auto v2358 = Get(s->Global("CROPS"), Get(s->LocalAt(27), Value("crop")));
s->SetAt(6, v2358);
if (static_cast<bool>(Unary("Not", Get(s->LocalAt(6), Value("ongoing"))))) {
auto v2359 = ([&]() -> Value { auto v2360 = s->LocalAt(8); return Binary("Sub", v2360, Get(s->LocalAt(27), Value("planted_day"))); }());
s->SetAt(1, v2359);
auto v2361 = ([&]() -> Value { auto v2362 = ([&]() -> Value { auto v2363 = Get(s->LocalAt(6), Value("max_yield_day")); return Binary("Add", v2363, Value(int64_t{1})); }()); return Binary("FloorDiv", v2362, Value(int64_t{2})); }());
s->SetAt(30, v2361);
if (static_cast<bool>(([&]() -> Value { auto v2364 = s->LocalAt(30); Value v2365; v2365 = s->LocalAt(1); if (!static_cast<bool>(Binary("LtE", v2364, v2365))) return Value(false); v2364 = v2365; v2365 = Get(s->LocalAt(6), Value("max_yield_day")); if (!static_cast<bool>(Binary("LtE", v2364, v2365))) return Value(false); v2364 = v2365; return Value(true); }()))) {
auto v2366 = (static_cast<bool>(([&]() -> Value { auto v2367 = Get(s->LocalAt(27), Value("fertilized_until_day")); Value v2368; v2368 = s->LocalAt(8); if (!static_cast<bool>(Binary("GtE", v2367, v2368))) return Value(false); v2367 = v2368; return Value(true); }())) ? Value(int64_t{2}) : Value(int64_t{1}));
s->SetAt(4, v2366);
auto v2369 = ([&]() -> Value { auto fn2370 = s->Global("min"); Arguments args2371; args2371.positional.reserve(2); args2371.Add(Get(s->LocalAt(6), Value("max_yield")), false); args2371.Add(([&]() -> Value { auto v2372 = Get(s->LocalAt(27), Value("yield_units")); return Binary("Add", v2372, s->LocalAt(4)); }()), false); return Call(c, fn2370, std::move(args2371)); }());
Put(s->LocalAt(27), Value("yield_units"), v2369);
}
}
return Value{};
}
if (static_cast<bool>(([&]() -> Value { auto v2373 = s->LocalAt(20); Value v2374; v2374 = Value("HARVEST"); if (!static_cast<bool>(Binary("Eq", v2373, v2374))) return Value(false); v2373 = v2374; return Value(true); }()))) {
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto fn2375 = s->Global("isinstance"); Arguments args2376; args2376.positional.reserve(2); args2376.Add(s->LocalAt(27), false); args2376.Add(s->Global("dict"), false); return Call(c, fn2375, std::move(args2376)); }())))) {
return Value{};
}
if (static_cast<bool>(([&]() -> Value { auto v2377 = ([&]() -> Value { auto fn2379 = PrepareDictionaryGet(s->LocalAt(27)); Arguments args2380; args2380.positional.reserve(2); args2380.Add(Value("yield_units"), false); args2380.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn2379, std::move(args2380)); }()); Value v2378; v2378 = Value(int64_t{0}); if (!static_cast<bool>(Binary("LtE", v2377, v2378))) return Value(false); v2377 = v2378; return Value(true); }()))) {
return Value{};
}
if (static_cast<bool>(([&]() -> Value { auto v2381 = ([&]() -> Value { auto fn2383 = PrepareDictionaryGet(s->LocalAt(27)); Arguments args2384; args2384.Add(Value("kind"), false); return CallDictionaryGet(c, fn2383, std::move(args2384)); }()); Value v2382; v2382 = Value("PLANT"); if (!static_cast<bool>(Binary("Eq", v2381, v2382))) return Value(false); v2381 = v2382; return Value(true); }()))) {
auto v2385 = Get(s->Global("CROPS"), Get(s->LocalAt(27), Value("crop")));
s->SetAt(6, v2385);
if (static_cast<bool>(([&]() -> Value { auto v2386 = ([&]() -> Value { auto v2388 = s->LocalAt(8); return Binary("Sub", v2388, Get(s->LocalAt(27), Value("planted_day"))); }()); Value v2387; v2387 = Get(s->LocalAt(6), Value("first_yield_day")); if (!static_cast<bool>(Binary("Lt", v2386, v2387))) return Value(false); v2386 = v2387; return Value(true); }()))) {
if (static_cast<bool>(Get(s->LocalAt(6), Value("ongoing")))) {
(void)([&]() -> Value { auto fn2389 = s->Global("print"); Arguments args2390; args2390.Add(Value(Value("WARNING: HARVEST on immature ongoing ").string() + Value(Repr(Get(s->LocalAt(27), Value("crop")))).string() + Value(" (planted day ").string() + Value(Repr(Get(s->LocalAt(27), Value("planted_day")))).string() + Value(", current day ").string() + Value(Repr(s->LocalAt(8))).string() + Value(", first_yield_day ").string() + Value(Repr(Get(s->LocalAt(6), Value("first_yield_day")))).string() + Value(", yield_units ").string() + Value(Repr(Get(s->LocalAt(27), Value("yield_units")))).string() + Value("); should never happen").string()), false); return Call(c, fn2389, std::move(args2390)); }());
}
return Value{};
}
auto v2391 = Get(s->LocalAt(27), Value("yield_units"));
s->SetAt(29, v2391);
auto v2392 = Value(int64_t{0});
Put(s->LocalAt(27), Value("yield_units"), v2392);
(void)([&]() -> Value { auto fn2393 = s->Global("_inv_add"); Arguments args2394; args2394.positional.reserve(3); args2394.Add(s->LocalAt(15), false); args2394.Add(Get(s->LocalAt(27), Value("crop")), false); args2394.Add(s->LocalAt(29), false); return Call(c, fn2393, std::move(args2394)); }());
if (static_cast<bool>(Unary("Not", Get(s->LocalAt(6), Value("ongoing"))))) {
auto v2395 = Value{};
Put(Get(Get(s->LocalAt(11), Value("tiles")), s->LocalAt(13)), s->LocalAt(12), v2395);
}
}
else {
if (static_cast<bool>(([&]() -> Value { auto v2396 = Value("animal"); Value v2397; v2397 = s->LocalAt(27); if (!static_cast<bool>(Binary("In", v2396, v2397))) return Value(false); v2396 = v2397; return Value(true); }()))) {
auto v2398 = Get(s->LocalAt(27), Value("yield_units"));
s->SetAt(29, v2398);
auto v2399 = Value(int64_t{0});
Put(s->LocalAt(27), Value("yield_units"), v2399);
(void)([&]() -> Value { auto fn2400 = s->Global("_inv_add"); Arguments args2401; args2401.positional.reserve(3); args2401.Add(s->LocalAt(15), false); args2401.Add(Get(Get(s->Global("ANIMALS"), Get(s->LocalAt(27), Value("animal"))), Value("product")), false); args2401.Add(s->LocalAt(29), false); return Call(c, fn2400, std::move(args2401)); }());
}
}
return Value{};
}
if (static_cast<bool>(([&]() -> Value { auto v2402 = s->LocalAt(20); Value v2403; v2403 = Value("FERTILIZE"); if (!static_cast<bool>(Binary("Eq", v2402, v2403))) return Value(false); v2402 = v2403; return Value(true); }()))) {
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto v2404 = ([&]() -> Value { auto fn2405 = s->Global("isinstance"); Arguments args2406; args2406.positional.reserve(2); args2406.Add(s->LocalAt(27), false); args2406.Add(s->Global("dict"), false); return Call(c, fn2405, std::move(args2406)); }()); if (!static_cast<bool>(v2404)) return v2404; v2404 = ([&]() -> Value { auto v2407 = ([&]() -> Value { auto fn2409 = PrepareDictionaryGet(s->LocalAt(27)); Arguments args2410; args2410.Add(Value("kind"), false); return CallDictionaryGet(c, fn2409, std::move(args2410)); }()); Value v2408; v2408 = Value("PLANT"); if (!static_cast<bool>(Binary("Eq", v2407, v2408))) return Value(false); v2407 = v2408; return Value(true); }()); return v2404; }())))) {
return Value{};
}
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto fn2411 = s->Global("_inv_take"); Arguments args2412; args2412.positional.reserve(3); args2412.Add(s->LocalAt(15), false); args2412.Add(Value("FERTILIZER"), false); args2412.Add(Value(int64_t{1}), false); return Call(c, fn2411, std::move(args2412)); }())))) {
return Value{};
}
auto v2413 = ([&]() -> Value { auto fn2414 = s->Global("max"); Arguments args2415; args2415.positional.reserve(2); args2415.Add(([&]() -> Value { auto fn2416 = PrepareDictionaryGet(s->LocalAt(27)); Arguments args2417; args2417.positional.reserve(2); args2417.Add(Value("fertilized_until_day"), false); args2417.Add(Unary("USub", Value(int64_t{1})), false); return CallDictionaryGet(c, fn2416, std::move(args2417)); }()), false); args2415.Add(([&]() -> Value { auto v2418 = s->LocalAt(8); return Binary("Add", v2418, Value(int64_t{2})); }()), false); return Call(c, fn2414, std::move(args2415)); }());
Put(s->LocalAt(27), Value("fertilized_until_day"), v2413);
return Value{};
}
if (static_cast<bool>(([&]() -> Value { auto v2419 = s->LocalAt(20); Value v2420; v2420 = Value("DIG"); if (!static_cast<bool>(Binary("Eq", v2419, v2420))) return Value(false); v2419 = v2420; return Value(true); }()))) {
if (static_cast<bool>(([&]() -> Value { auto v2421 = s->LocalAt(27); Value v2422; v2422 = Value{}; if (!static_cast<bool>(Binary("Is", v2421, v2422))) return Value(false); v2421 = v2422; return Value(true); }()))) {
return Value{};
}
if (static_cast<bool>(([&]() -> Value { auto v2423 = ([&]() -> Value { auto fn2424 = s->Global("isinstance"); Arguments args2425; args2425.positional.reserve(2); args2425.Add(s->LocalAt(27), false); args2425.Add(s->Global("dict"), false); return Call(c, fn2424, std::move(args2425)); }()); if (!static_cast<bool>(v2423)) return v2423; v2423 = ([&]() -> Value { auto v2426 = Value("animal"); Value v2427; v2427 = s->LocalAt(27); if (!static_cast<bool>(Binary("In", v2426, v2427))) return Value(false); v2426 = v2427; return Value(true); }()); return v2423; }()))) {
return Value{};
}
auto v2428 = Value{};
Put(Get(Get(s->LocalAt(11), Value("tiles")), s->LocalAt(13)), s->LocalAt(12), v2428);
return Value{};
}
if (static_cast<bool>(([&]() -> Value { auto v2429 = s->LocalAt(20); Value v2430; v2430 = Value("BUILD_COOP"); if (!static_cast<bool>(Binary("Eq", v2429, v2430))) return Value(false); v2429 = v2430; return Value(true); }()))) {
if (static_cast<bool>(([&]() -> Value { auto v2431 = s->LocalAt(27); Value v2432; v2432 = Value{}; if (!static_cast<bool>(Binary("IsNot", v2431, v2432))) return Value(false); v2431 = v2432; return Value(true); }()))) {
return Value{};
}
auto v2433 = ([&]() -> Value { auto dict2434 = Dict(); auto key2435 = Value("kind"); Put(dict2434, key2435, Value("COOP")); return dict2434; }());
Put(Get(Get(s->LocalAt(11), Value("tiles")), s->LocalAt(13)), s->LocalAt(12), v2433);
return Value{};
}
if (static_cast<bool>(([&]() -> Value { auto v2436 = s->LocalAt(20); Value v2437; v2437 = Value("BUILD_PASTURE"); if (!static_cast<bool>(Binary("Eq", v2436, v2437))) return Value(false); v2436 = v2437; return Value(true); }()))) {
if (static_cast<bool>(([&]() -> Value { auto v2438 = s->LocalAt(27); Value v2439; v2439 = Value{}; if (!static_cast<bool>(Binary("IsNot", v2438, v2439))) return Value(false); v2438 = v2439; return Value(true); }()))) {
return Value{};
}
auto v2440 = ([&]() -> Value { auto dict2441 = Dict(); auto key2442 = Value("kind"); Put(dict2441, key2442, Value("PASTURE")); return dict2441; }());
Put(Get(Get(s->LocalAt(11), Value("tiles")), s->LocalAt(13)), s->LocalAt(12), v2440);
return Value{};
}
if (static_cast<bool>(([&]() -> Value { auto v2443 = s->LocalAt(20); Value v2444; v2444 = Value("FEED"); if (!static_cast<bool>(Binary("Eq", v2443, v2444))) return Value(false); v2443 = v2444; return Value(true); }()))) {
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto v2445 = ([&]() -> Value { auto fn2446 = s->Global("isinstance"); Arguments args2447; args2447.positional.reserve(2); args2447.Add(s->LocalAt(27), false); args2447.Add(s->Global("dict"), false); return Call(c, fn2446, std::move(args2447)); }()); if (!static_cast<bool>(v2445)) return v2445; v2445 = ([&]() -> Value { auto v2448 = Value("animal"); Value v2449; v2449 = s->LocalAt(27); if (!static_cast<bool>(Binary("In", v2448, v2449))) return Value(false); v2448 = v2449; return Value(true); }()); return v2445; }())))) {
return Value{};
}
if (static_cast<bool>(Get(s->LocalAt(27), Value("fed_today")))) {
return Value{};
}
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto fn2450 = s->Global("_inv_take"); Arguments args2451; args2451.positional.reserve(3); args2451.Add(s->LocalAt(15), false); args2451.Add(Value("WHEAT"), false); args2451.Add(Value(int64_t{1}), false); return Call(c, fn2450, std::move(args2451)); }())))) {
return Value{};
}
auto v2452 = Value(true);
Put(s->LocalAt(27), Value("fed_today"), v2452);
return Value{};
}
if (static_cast<bool>(([&]() -> Value { auto v2453 = s->LocalAt(20); Value v2454; v2454 = Value("COLLECT_FERTILIZER"); if (!static_cast<bool>(Binary("Eq", v2453, v2454))) return Value(false); v2453 = v2454; return Value(true); }()))) {
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto v2455 = ([&]() -> Value { auto fn2456 = s->Global("isinstance"); Arguments args2457; args2457.positional.reserve(2); args2457.Add(s->LocalAt(27), false); args2457.Add(s->Global("dict"), false); return Call(c, fn2456, std::move(args2457)); }()); if (!static_cast<bool>(v2455)) return v2455; v2455 = ([&]() -> Value { auto v2458 = Value("animal"); Value v2459; v2459 = s->LocalAt(27); if (!static_cast<bool>(Binary("In", v2458, v2459))) return Value(false); v2458 = v2459; return Value(true); }()); return v2455; }())))) {
return Value{};
}
if (static_cast<bool>(Unary("Not", Get(s->LocalAt(27), Value("fertilizer_available"))))) {
return Value{};
}
auto v2460 = Value(false);
Put(s->LocalAt(27), Value("fertilizer_available"), v2460);
(void)([&]() -> Value { auto fn2461 = s->Global("_inv_add"); Arguments args2462; args2462.positional.reserve(3); args2462.Add(s->LocalAt(15), false); args2462.Add(Value("FERTILIZER"), false); args2462.Add(Value(int64_t{1}), false); return Call(c, fn2461, std::move(args2462)); }());
return Value{};
}
if (static_cast<bool>(([&]() -> Value { auto v2463 = s->LocalAt(20); Value v2464; v2464 = Value("CARE"); if (!static_cast<bool>(Binary("Eq", v2463, v2464))) return Value(false); v2463 = v2464; return Value(true); }()))) {
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto v2465 = ([&]() -> Value { auto fn2466 = s->Global("isinstance"); Arguments args2467; args2467.positional.reserve(2); args2467.Add(s->LocalAt(27), false); args2467.Add(s->Global("dict"), false); return Call(c, fn2466, std::move(args2467)); }()); if (!static_cast<bool>(v2465)) return v2465; v2465 = ([&]() -> Value { auto v2468 = Value("animal"); Value v2469; v2469 = s->LocalAt(27); if (!static_cast<bool>(Binary("In", v2468, v2469))) return Value(false); v2468 = v2469; return Value(true); }()); return v2465; }())))) {
return Value{};
}
if (static_cast<bool>(Get(s->LocalAt(27), Value("cared_today")))) {
return Value{};
}
auto v2470 = Value(true);
Put(s->LocalAt(27), Value("cared_today"), v2470);
return Value{};
}
return {};
}
}  // namespace kagg::opponents::compiled
