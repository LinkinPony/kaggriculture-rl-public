// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_3d678d3fab3e30ef5986(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "block", "end", "observation", "orders", "start", "stock"};
s->PrepareSlots(s_names);
auto v6373 = ([&]() -> Value { auto fn6374 = s->Global("projected_shed"); Arguments args6375; args6375.positional.reserve(2); args6375.Add(s->LocalAt(0), false); args6375.Add(([&]() -> Value { auto fn6376 = s->Global("FarmView"); Arguments args6377; args6377.Add(s->LocalAt(3), false); return Call(c, fn6376, std::move(args6377)); }()), false); return Call(c, fn6374, std::move(args6375)); }());
s->SetAt(6, v6373);
auto v6378 = ([&]() -> Value { auto comp6379 = std::make_shared<Scope>(); comp6379->globals = s->globals; comp6379->parent = s; static constexpr const char* comp6379_names[] = {"o"}; comp6379->PrepareSlots(comp6379_names); auto result6380 = List(); for (const auto& item6381 : Iterate(Get(s->LocalAt(0), Value("market")))) { comp6379->SetAt(0, item6381); result6380.node()->sequence.push_back(([&]() -> Value { auto fn6382 = comp6379->Global("list"); Arguments args6383; args6383.Add(comp6379->LocalAt(0), false); return Call(c, fn6382, std::move(args6383)); }())); } return result6380; }());
s->SetAt(4, v6378);
auto v6384 = Value(int64_t{0});
s->SetAt(5, v6384);
while (static_cast<bool>(([&]() -> Value { auto v6385 = s->LocalAt(5); Value v6386; v6386 = ([&]() -> Value { auto fn6387 = s->Global("len"); Arguments args6388; args6388.Add(s->LocalAt(4), false); return Call(c, fn6387, std::move(args6388)); }()); if (!static_cast<bool>(Binary("Lt", v6385, v6386))) return Value(false); v6385 = v6386; return Value(true); }()))) {
if (static_cast<bool>(([&]() -> Value { auto v6389 = Get(Get(s->LocalAt(4), s->LocalAt(5)), Value(int64_t{0})); Value v6390; v6390 = Value("SELL"); if (!static_cast<bool>(Binary("NotEq", v6389, v6390))) return Value(false); v6389 = v6390; return Value(true); }()))) {
auto v6391 = s->LocalAt(5);
s->SetAt(5, Inplace("Add", v6391, Value(int64_t{1})));
continue;
}
auto v6392 = s->LocalAt(5);
s->SetAt(2, v6392);
while (static_cast<bool>(([&]() -> Value { auto v6393 = ([&]() -> Value { auto v6394 = s->LocalAt(2); Value v6395; v6395 = ([&]() -> Value { auto fn6396 = s->Global("len"); Arguments args6397; args6397.Add(s->LocalAt(4), false); return Call(c, fn6396, std::move(args6397)); }()); if (!static_cast<bool>(Binary("Lt", v6394, v6395))) return Value(false); v6394 = v6395; return Value(true); }()); if (!static_cast<bool>(v6393)) return v6393; v6393 = ([&]() -> Value { auto v6398 = Get(Get(s->LocalAt(4), s->LocalAt(2)), Value(int64_t{0})); Value v6399; v6399 = Value("SELL"); if (!static_cast<bool>(Binary("Eq", v6398, v6399))) return Value(false); v6398 = v6399; return Value(true); }()); return v6393; }()))) {
auto v6400 = s->LocalAt(2);
s->SetAt(2, Inplace("Add", v6400, Value(int64_t{1})));
}
auto v6401 = Slice(s->LocalAt(4), s->LocalAt(5), s->LocalAt(2), Value{});
s->SetAt(1, v6401);
if (static_cast<bool>(([&]() -> Value { auto v6402 = ([&]() -> Value { auto fn6404 = s->Global("len"); Arguments args6405; args6405.Add(([&]() -> Value { auto comp6406 = std::make_shared<Scope>(); comp6406->globals = s->globals; comp6406->parent = s; static constexpr const char* comp6406_names[] = {"o"}; comp6406->PrepareSlots(comp6406_names); auto result6407 = List(); for (const auto& item6408 : Iterate(s->LocalAt(1))) { comp6406->SetAt(0, item6408); result6407.node()->sequence.push_back(Get(comp6406->LocalAt(0), Value(int64_t{1}))); } return Set(result6407.node()->sequence); }()), false); return Call(c, fn6404, std::move(args6405)); }()); Value v6403; v6403 = ([&]() -> Value { auto fn6409 = s->Global("len"); Arguments args6410; args6410.Add(s->LocalAt(1), false); return Call(c, fn6409, std::move(args6410)); }()); if (!static_cast<bool>(Binary("Eq", v6402, v6403))) return Value(false); v6402 = v6403; return Value(true); }()))) {
auto v6411 = ([&]() -> Value { auto fn6412 = s->Global("sorted"); Arguments args6413; args6413.Add(s->LocalAt(1), false); args6413.Keyword("key", Define(&Code_440107b0ae95b16749ec, s, Signature{{"o"}, {}, {}, {}, "", "", ([]() -> std::span<const char* const> { static constexpr const char* names[] = {"o"}; return names; }())}, true, "<lambda>")); args6413.Keyword("reverse", Value(true)); return Call(c, fn6412, std::move(args6413)); }());
PutSlice(s->LocalAt(4), s->LocalAt(5), s->LocalAt(2), Value{}, v6411);
}
auto v6416 = s->LocalAt(2);
s->SetAt(5, v6416);
}
if (static_cast<bool>(([&]() -> Value { auto v6417 = s->LocalAt(4); Value v6418; v6418 = Get(s->LocalAt(0), Value("market")); if (!static_cast<bool>(Binary("NotEq", v6417, v6418))) return Value(false); v6417 = v6418; return Value(true); }()))) {
auto v6419 = s->Global("_R37_STATS");
auto v6420 = Value("quote_reordered_turns");
auto v6421 = Get(v6419, v6420);
Put(v6419, v6420, Inplace("Add", v6421, Value(int64_t{1})));
auto v6422 = ([&]() -> Value { auto fn6423 = s->Global("dict"); Arguments args6424; args6424.Add(s->LocalAt(0), false); args6424.Keyword("market", s->LocalAt(4)); return Call(c, fn6423, std::move(args6424)); }());
s->SetAt(0, v6422);
}
return s->LocalAt(0);
return {};
}
}  // namespace kagg::opponents::compiled
