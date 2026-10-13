// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_d0ac5f1ec98e2638dd7f(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "baseline", "chassis", "config", "market", "obs", "projected", "run", "seat", "shadow", "state", "states", "step"};
s->PrepareSlots(s_names);
auto v3977 = ([&]() -> Value { auto fn3978 = s->Global("int"); Arguments args3979; args3979.Add(Get(s->LocalAt(5), Value("player")), false); return Call(c, fn3978, std::move(args3979)); }());
s->SetAt(8, v3977);
auto v3980 = Attribute(s->Global("_IMPL"), "chassis");
s->SetAt(2, v3980);
auto v3981 = ([&]() -> Value { auto fn3982 = PrepareDictionaryGet(Attribute(s->LocalAt(2), "players")); Arguments args3983; args3983.Add(s->LocalAt(8), false); return CallDictionaryGet(c, fn3982, std::move(args3983)); }());
s->SetAt(10, v3981);
if (static_cast<bool>(([&]() -> Value { auto v3984 = Unary("Not", s->LocalAt(10)); if (static_cast<bool>(v3984)) return v3984; v3984 = ([&]() -> Value { auto v3985 = ([&]() -> Value { auto fn3987 = PrepareDictionaryGet(s->LocalAt(10)); Arguments args3988; args3988.Add(Value("last_step"), false); return CallDictionaryGet(c, fn3987, std::move(args3988)); }()); Value v3986; v3986 = Value(int64_t{711}); if (!static_cast<bool>(Binary("NotEq", v3985, v3986))) return Value(false); v3985 = v3986; return Value(true); }()); if (static_cast<bool>(v3984)) return v3984; v3984 = ([&]() -> Value { auto v3989 = ([&]() -> Value { auto fn3991 = PrepareDictionaryGet(s->LocalAt(10)); Arguments args3992; args3992.Add(Value("route"), false); return CallDictionaryGet(c, fn3991, std::move(args3992)); }()); Value v3990; v3990 = Value(int64_t{2}); if (!static_cast<bool>(Binary("NotEq", v3989, v3990))) return Value(false); v3989 = v3990; return Value(true); }()); return v3984; }()))) {
return Value{};
}
if (static_cast<bool>(([&]() -> Value { auto fn3993 = PrepareDictionaryGet(s->LocalAt(10)); Arguments args3994; args3994.Add(Value("pending"), false); return CallDictionaryGet(c, fn3993, std::move(args3994)); }()))) {
return Value{};
}
auto v3995 = ([&]() -> Value { auto fn3996 = Attribute(s->Global("copy"), "copy"); Arguments args3997; args3997.Add(s->LocalAt(2), false); return Call(c, fn3996, std::move(args3997)); }());
s->SetAt(9, v3995);
auto v3998 = ([&]() -> Value { auto fn3999 = Attribute(s->Global("copy"), "deepcopy"); Arguments args4000; args4000.Add(Attribute(s->LocalAt(2), "players"), false); return Call(c, fn3999, std::move(args4000)); }());
SetAttribute(s->LocalAt(9), "players", v3998);
auto v4001 = ([&]() -> Value { auto comp4002 = std::make_shared<Scope>(); comp4002->globals = s->globals; comp4002->parent = s; static constexpr const char* comp4002_names[] = {"k"}; comp4002->PrepareSlots(comp4002_names); auto result4003 = Dict(); for (const auto& item4004 : Iterate(Attribute(s->LocalAt(2), "diagnostics"))) { comp4002->SetAt(0, item4004); Put(result4003, comp4002->LocalAt(0), Value(int64_t{0})); } return result4003; }());
SetAttribute(s->LocalAt(9), "diagnostics", v4001);
auto v4005 = ([&]() -> Value { auto fn4006 = Attribute(s->Global("copy"), "deepcopy"); Arguments args4007; args4007.Add(s->LocalAt(5), false); return Call(c, fn4006, std::move(args4007)); }());
s->SetAt(6, v4005);
auto v4008 = List({});
s->SetAt(1, v4008);
auto v4009 = List({});
s->SetAt(11, v4009);
for (const auto& item4010 : Iterate(([&]() -> Value { auto fn4011 = s->Global("range"); Arguments args4012; args4012.positional.reserve(2); args4012.Add(Value(int64_t{712}), false); args4012.Add(Value(int64_t{719}), false); return Call(c, fn4011, std::move(args4012)); }()))) {
s->SetAt(12, item4010);
auto v4013 = s->LocalAt(12);
Put(s->LocalAt(6), Value("step"), v4013);
auto v4014 = ([&]() -> Value { auto v4015 = s->LocalAt(12); return Binary("FloorDiv", v4015, Value(int64_t{24})); }());
Put(s->LocalAt(6), Value("day"), v4014);
auto v4016 = ([&]() -> Value { auto v4017 = s->LocalAt(12); return Binary("Mod", v4017, Value(int64_t{24})); }());
Put(s->LocalAt(6), Value("hour"), v4016);
(void)([&]() -> Value { auto fn4018 = Attribute(s->LocalAt(11), "append"); Arguments args4019; args4019.Add(([&]() -> Value { auto fn4020 = Attribute(s->Global("copy"), "deepcopy"); Arguments args4021; args4021.Add(Get(Attribute(s->LocalAt(9), "players"), s->LocalAt(8)), false); return Call(c, fn4020, std::move(args4021)); }()), false); return Call(c, fn4018, std::move(args4019)); }());
auto v4022 = ([&]() -> Value { auto fn4023 = Attribute(s->LocalAt(9), "act"); Arguments args4024; args4024.positional.reserve(2); args4024.Add(s->LocalAt(6), false); args4024.Add(s->LocalAt(3), false); return Call(c, fn4023, std::move(args4024)); }());
s->SetAt(0, v4022);
if (static_cast<bool>(([&]() -> Value { auto v4025 = s->LocalAt(12); Value v4026; v4026 = Value(int64_t{718}); if (!static_cast<bool>(Binary("Eq", v4025, v4026))) return Value(false); v4025 = v4026; return Value(true); }()))) {
auto v4027 = ([&]() -> Value { auto fn4028 = s->Global("_parent_liquidate"); Arguments args4029; args4029.positional.reserve(3); args4029.Add(Get(Get(s->LocalAt(6), Value("farms")), s->LocalAt(8)), false); args4029.Add(Get(s->LocalAt(6), Value("private")), false); args4029.Add(Get(Get(s->LocalAt(6), Value("market")), Value("prices")), false); return Call(c, fn4028, std::move(args4029)); }());
s->SetAt(0, v4027);
}
else {
auto v4030 = ([&]() -> Value { auto fn4031 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args4032; args4032.positional.reserve(2); args4032.Add(Value("market"), false); args4032.Add(List({}), false); return CallDictionaryGet(c, fn4031, std::move(args4032)); }());
s->SetAt(4, v4030);
if (static_cast<bool>(([&]() -> Value { auto v4033 = ([&]() -> Value { auto v4034 = ([&]() -> Value { auto fn4036 = s->Global("len"); Arguments args4037; args4037.Add(s->LocalAt(4), false); return Call(c, fn4036, std::move(args4037)); }()); Value v4035; v4035 = Value(int64_t{9}); if (!static_cast<bool>(Binary("NotEq", v4034, v4035))) return Value(false); v4034 = v4035; return Value(true); }()); if (static_cast<bool>(v4033)) return v4033; v4033 = ([&]() -> Value { auto v4038 = ([&]() -> Value { auto comp4040 = std::make_shared<Scope>(); comp4040->globals = s->globals; comp4040->parent = s; static constexpr const char* comp4040_names[] = {"o"}; comp4040->PrepareSlots(comp4040_names); auto result4041 = List(); for (const auto& item4042 : Iterate(s->LocalAt(4))) { comp4040->SetAt(0, item4042); result4041.node()->sequence.push_back(Get(comp4040->LocalAt(0), Value(int64_t{1}))); } return Set(result4041.node()->sequence); }()); Value v4039; v4039 = ([&]() -> Value { auto fn4043 = s->Global("set"); Arguments args4044; args4044.Add(s->Global("PRODUCTS"), false); return Call(c, fn4043, std::move(args4044)); }()); if (!static_cast<bool>(Binary("NotEq", v4038, v4039))) return Value(false); v4038 = v4039; return Value(true); }()); if (static_cast<bool>(v4033)) return v4033; v4033 = ([&]() -> Value { auto comp4045 = std::make_shared<Scope>(); comp4045->globals = s->globals; comp4045->parent = s; static constexpr const char* comp4045_names[] = {"o"}; comp4045->PrepareSlots(comp4045_names); auto result4046 = List(); for (const auto& item4047 : Iterate(s->LocalAt(4))) { comp4045->SetAt(0, item4047); if (static_cast<bool>(([&]() -> Value { auto v4048 = ([&]() -> Value { auto v4049 = Get(comp4045->LocalAt(0), Value(int64_t{0})); Value v4050; v4050 = Value("SELL"); if (!static_cast<bool>(Binary("NotEq", v4049, v4050))) return Value(false); v4049 = v4050; return Value(true); }()); if (static_cast<bool>(v4048)) return v4048; v4048 = ([&]() -> Value { auto v4051 = ([&]() -> Value { auto fn4053 = comp4045->Global("len"); Arguments args4054; args4054.Add(comp4045->LocalAt(0), false); return Call(c, fn4053, std::move(args4054)); }()); Value v4052; v4052 = Value(int64_t{3}); if (!static_cast<bool>(Binary("NotEq", v4051, v4052))) return Value(false); v4051 = v4052; return Value(true); }()); if (static_cast<bool>(v4048)) return v4048; v4048 = ([&]() -> Value { auto v4055 = ([&]() -> Value { auto fn4057 = comp4045->Global("type"); Arguments args4058; args4058.Add(Get(comp4045->LocalAt(0), Value(int64_t{2})), false); return Call(c, fn4057, std::move(args4058)); }()); Value v4056; v4056 = comp4045->Global("int"); if (!static_cast<bool>(Binary("IsNot", v4055, v4056))) return Value(false); v4055 = v4056; return Value(true); }()); if (static_cast<bool>(v4048)) return v4048; v4048 = ([&]() -> Value { auto v4059 = Get(comp4045->LocalAt(0), Value(int64_t{2})); Value v4060; v4060 = Value(int64_t{100}); if (!static_cast<bool>(Binary("Lt", v4059, v4060))) return Value(false); v4059 = v4060; return Value(true); }()); return v4048; }()))) return Value(true); } return Value(false); }()); return v4033; }()))) {
return Value{};
}
}
if (static_cast<bool>(([&]() -> Value { auto fn4061 = s->Global("any"); Arguments args4062; args4062.Add(([&]() -> Value { auto fn4063 = Attribute(Attribute(s->LocalAt(9), "diagnostics"), "values"); Arguments args4064; return Call(c, fn4063, std::move(args4064)); }()), false); return Call(c, fn4061, std::move(args4062)); }()))) {
return Value{};
}
auto v4065 = ([&]() -> Value { auto fn4066 = Get(s->Global("_PLANNER_NS"), Value("simulate")); Arguments args4067; args4067.positional.reserve(3); args4067.Add(s->LocalAt(6), false); args4067.Add(s->LocalAt(3), false); args4067.Add(List({s->LocalAt(0)}), false); return Call(c, fn4066, std::move(args4067)); }());
s->SetAt(7, v4065);
if (static_cast<bool>(([&]() -> Value { auto v4068 = Get(Get(s->LocalAt(7), Value("actions")), Value(int64_t{0})); Value v4069; v4069 = s->LocalAt(0); if (!static_cast<bool>(Binary("NotEq", v4068, v4069))) return Value(false); v4068 = v4069; return Value(true); }()))) {
return Value{};
}
(void)([&]() -> Value { auto fn4070 = Attribute(s->LocalAt(1), "append"); Arguments args4071; args4071.Add(s->LocalAt(0), false); return Call(c, fn4070, std::move(args4071)); }());
auto v4072 = Get(Get(Get(s->LocalAt(6), Value("farms")), s->LocalAt(8)), Value("money"));
Put(Get(s->LocalAt(7), Value("farm")), Value("money"), v4072);
auto v4073 = Get(s->LocalAt(7), Value("farm"));
Put(Get(s->LocalAt(6), Value("farms")), s->LocalAt(8), v4073);
auto v4074 = Get(s->LocalAt(7), Value("private"));
Put(s->LocalAt(6), Value("private"), v4074);
}
return Tuple({s->LocalAt(1), s->LocalAt(11)});
return {};
}
}  // namespace kagg::opponents::compiled
