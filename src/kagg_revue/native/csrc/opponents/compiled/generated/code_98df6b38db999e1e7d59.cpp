// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_98df6b38db999e1e7d59(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "added", "carried", "configuration", "item", "needed", "o", "observation", "planned", "qty", "result", "step", "view"};
s->PrepareSlots(s_names);
auto v4218 = ([&]() -> Value { auto fn4219 = s->Global("_PRE_ROOM_AGENT"); Arguments args4220; args4220.positional.reserve(2); args4220.Add(s->LocalAt(7), false); args4220.Add(s->LocalAt(3), false); return Call(c, fn4219, std::move(args4220)); }());
s->SetAt(0, v4218);
try {
auto v4222 = ([&]() -> Value { auto fn4223 = s->Global("_step_of"); Arguments args4224; args4224.Add(s->LocalAt(7), false); return Call(c, fn4223, std::move(args4224)); }());
s->SetAt(11, v4222);
if (static_cast<bool>(([&]() -> Value { auto v4225 = ([&]() -> Value { auto v4227 = s->LocalAt(11); return Binary("Mod", v4227, Value(int64_t{24})); }()); Value v4226; v4226 = Value(int64_t{23}); if (!static_cast<bool>(Binary("NotEq", v4225, v4226))) return Value(false); v4225 = v4226; return Value(true); }()))) {
return s->LocalAt(0);
}
auto v4228 = ([&]() -> Value { auto fn4229 = s->Global("_View"); Arguments args4230; args4230.positional.reserve(3); args4230.Add(s->LocalAt(7), false); args4230.Add(([&]() -> Value { auto fn4231 = s->Global("_int"); Arguments args4232; args4232.Add(([&]() -> Value { auto fn4233 = s->Global("_get"); Arguments args4234; args4234.positional.reserve(3); args4234.Add(s->LocalAt(7), false); args4234.Add(Value("player"), false); args4234.Add(Value(int64_t{0}), false); return Call(c, fn4233, std::move(args4234)); }()), false); return Call(c, fn4231, std::move(args4232)); }()), false); args4230.Add(Attribute(Attribute(s->Global("_IMPL"), "chassis"), "cfg"), false); return Call(c, fn4229, std::move(args4230)); }());
s->SetAt(12, v4228);
auto v4235 = ([&]() -> Value { auto fn4236 = s->Global("sum"); Arguments args4237; args4237.Add(([&]() -> Value { auto comp4238 = std::make_shared<Scope>(); comp4238->globals = s->globals; comp4238->parent = s; static constexpr const char* comp4238_names[] = {"inv", "n"}; comp4238->PrepareSlots(comp4238_names); auto result4239 = List(); for (const auto& item4240 : Iterate(Attribute(s->LocalAt(12), "invs"))) { comp4238->SetAt(0, item4240); for (const auto& item4241 : Iterate(([&]() -> Value { auto fn4242 = Attribute(comp4238->LocalAt(0), "values"); Arguments args4243; return Call(c, fn4242, std::move(args4243)); }()))) { comp4238->SetAt(1, item4241); result4239.node()->sequence.push_back(([&]() -> Value { auto fn4244 = comp4238->Global("max"); Arguments args4245; args4245.positional.reserve(2); args4245.Add(Value(int64_t{0}), false); args4245.Add(([&]() -> Value { auto fn4246 = comp4238->Global("int"); Arguments args4247; args4247.Add(comp4238->LocalAt(1), false); return Call(c, fn4246, std::move(args4247)); }()), false); return Call(c, fn4244, std::move(args4245)); }())); } } return result4239; }()), false); return Call(c, fn4236, std::move(args4237)); }());
s->SetAt(2, v4235);
auto v4248 = ([&]() -> Value { auto v4249 = ([&]() -> Value { auto v4250 = ([&]() -> Value { auto fn4251 = s->Global("sum"); Arguments args4252; args4252.Add(([&]() -> Value { auto fn4253 = Attribute(Attribute(s->LocalAt(12), "shed"), "values"); Arguments args4254; return Call(c, fn4253, std::move(args4254)); }()), false); return Call(c, fn4251, std::move(args4252)); }()); return Binary("Add", v4250, s->LocalAt(2)); }()); return Binary("Sub", v4249, Value(int64_t{99})); }());
s->SetAt(5, v4248);
if (static_cast<bool>(([&]() -> Value { auto v4255 = s->LocalAt(5); Value v4256; v4256 = Value(int64_t{0}); if (!static_cast<bool>(Binary("LtE", v4255, v4256))) return Value(false); v4255 = v4256; return Value(true); }()))) {
return s->LocalAt(0);
}
auto v4257 = ([&]() -> Value { auto dict4258 = Dict(); return dict4258; }());
s->SetAt(8, v4257);
for (const auto& item4259 : Iterate(([&]() -> Value { auto fn4260 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args4261; args4261.positional.reserve(2); args4261.Add(Value("market"), false); args4261.Add(List({}), false); return CallDictionaryGet(c, fn4260, std::move(args4261)); }()))) {
s->SetAt(6, item4259);
if (static_cast<bool>(([&]() -> Value { auto v4262 = s->LocalAt(6); if (!static_cast<bool>(v4262)) return v4262; v4262 = ([&]() -> Value { auto v4263 = Get(s->LocalAt(6), Value(int64_t{0})); Value v4264; v4264 = Value("SELL"); if (!static_cast<bool>(Binary("Eq", v4263, v4264))) return Value(false); v4263 = v4264; return Value(true); }()); if (!static_cast<bool>(v4262)) return v4262; v4262 = ([&]() -> Value { auto v4265 = ([&]() -> Value { auto fn4267 = s->Global("len"); Arguments args4268; args4268.Add(s->LocalAt(6), false); return Call(c, fn4267, std::move(args4268)); }()); Value v4266; v4266 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v4265, v4266))) return Value(false); v4265 = v4266; return Value(true); }()); return v4262; }()))) {
auto v4269 = ([&]() -> Value { auto v4270 = ([&]() -> Value { auto fn4271 = PrepareDictionaryGet(s->LocalAt(8)); Arguments args4272; args4272.positional.reserve(2); args4272.Add(Get(s->LocalAt(6), Value(int64_t{1})), false); args4272.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn4271, std::move(args4272)); }()); return Binary("Add", v4270, ([&]() -> Value { auto fn4273 = s->Global("max"); Arguments args4274; args4274.positional.reserve(2); args4274.Add(Value(int64_t{0}), false); args4274.Add(([&]() -> Value { auto fn4275 = s->Global("int"); Arguments args4276; args4276.Add(Get(s->LocalAt(6), Value(int64_t{2})), false); return Call(c, fn4275, std::move(args4276)); }()), false); return Call(c, fn4273, std::move(args4274)); }())); }());
Put(s->LocalAt(8), Get(s->LocalAt(6), Value(int64_t{1})), v4269);
}
}
auto v4277 = ([&]() -> Value { auto fn4278 = Attribute(s->Global("copy"), "deepcopy"); Arguments args4279; args4279.Add(s->LocalAt(0), false); return Call(c, fn4278, std::move(args4279)); }());
s->SetAt(10, v4277);
auto v4280 = Value(int64_t{0});
s->SetAt(1, v4280);
for (const auto& item4281 : Iterate(([&]() -> Value { auto fn4282 = s->Global("sorted"); Arguments args4283; args4283.Add(s->Global("PRODUCTS"), false); args4283.Keyword("key", Define(&Code_f42895de3c72df15e738, s, Signature{{"it"}, {}, {}, {}, "", "", ([]() -> std::span<const char* const> { static constexpr const char* names[] = {"it"}; return names; }())}, true, "<lambda>")); return Call(c, fn4282, std::move(args4283)); }()))) {
s->SetAt(4, item4281);
auto v4288 = ([&]() -> Value { auto fn4289 = s->Global("min"); Arguments args4290; args4290.positional.reserve(2); args4290.Add(s->LocalAt(5), false); args4290.Add(([&]() -> Value { auto fn4291 = s->Global("max"); Arguments args4292; args4292.positional.reserve(2); args4292.Add(Value(int64_t{0}), false); args4292.Add(([&]() -> Value { auto v4293 = ([&]() -> Value { auto fn4294 = PrepareDictionaryGet(Attribute(s->LocalAt(12), "shed")); Arguments args4295; args4295.positional.reserve(2); args4295.Add(s->LocalAt(4), false); args4295.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn4294, std::move(args4295)); }()); return Binary("Sub", v4293, ([&]() -> Value { auto fn4296 = PrepareDictionaryGet(s->LocalAt(8)); Arguments args4297; args4297.positional.reserve(2); args4297.Add(s->LocalAt(4), false); args4297.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn4296, std::move(args4297)); }())); }()), false); return Call(c, fn4291, std::move(args4292)); }()), false); return Call(c, fn4289, std::move(args4290)); }());
s->SetAt(9, v4288);
if (static_cast<bool>(([&]() -> Value { auto v4298 = s->LocalAt(9); Value v4299; v4299 = Value(int64_t{0}); if (!static_cast<bool>(Binary("LtE", v4298, v4299))) return Value(false); v4298 = v4299; return Value(true); }()))) {
continue;
}
if (static_cast<bool>(([&]() -> Value { auto v4300 = ([&]() -> Value { auto fn4302 = s->Global("len"); Arguments args4303; args4303.Add(Get(s->LocalAt(10), Value("market")), false); return Call(c, fn4302, std::move(args4303)); }()); Value v4301; v4301 = Value(int64_t{10}); if (!static_cast<bool>(Binary("GtE", v4300, v4301))) return Value(false); v4300 = v4301; return Value(true); }()))) {
break;
}
(void)([&]() -> Value { auto fn4304 = Attribute(Get(s->LocalAt(10), Value("market")), "append"); Arguments args4305; args4305.Add(List({Value("SELL"), s->LocalAt(4), s->LocalAt(9)}), false); return Call(c, fn4304, std::move(args4305)); }());
auto v4306 = s->LocalAt(5);
s->SetAt(5, Inplace("Sub", v4306, s->LocalAt(9)));
auto v4307 = s->LocalAt(1);
s->SetAt(1, Inplace("Add", v4307, s->LocalAt(9)));
if (static_cast<bool>(([&]() -> Value { auto v4308 = s->LocalAt(5); Value v4309; v4309 = Value(int64_t{0}); if (!static_cast<bool>(Binary("LtE", v4308, v4309))) return Value(false); v4308 = v4309; return Value(true); }()))) {
break;
}
}
if (static_cast<bool>(s->LocalAt(1))) {
auto v4310 = s->Global("_ROOM_STATS");
auto v4311 = Value("changed_turns");
auto v4312 = Get(v4310, v4311);
Put(v4310, v4311, Inplace("Add", v4312, Value(int64_t{1})));
auto v4313 = s->Global("_ROOM_STATS");
auto v4314 = Value("added_units");
auto v4315 = Get(v4313, v4314);
Put(v4313, v4314, Inplace("Add", v4315, s->LocalAt(1)));
}
return s->LocalAt(10);
} catch (const Error& error4221) {
if (Matches(error4221, s->Global("Exception"))) {
auto v4316 = s->Global("_ROOM_STATS");
auto v4317 = Value("errors");
auto v4318 = Get(v4316, v4317);
Put(v4316, v4317, Inplace("Add", v4318, Value(int64_t{1})));
return s->LocalAt(0);
}
else { throw; }
}
return {};
}
}  // namespace kagg::opponents::compiled
