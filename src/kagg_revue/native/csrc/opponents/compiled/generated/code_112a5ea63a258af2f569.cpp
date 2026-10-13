// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_112a5ea63a258af2f569(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"actual", "baseline", "configuration", "observation", "plan", "previous", "result", "seat", "shadow", "states", "step"};
s->PrepareSlots(s_names);
try {
auto v4076 = ([&]() -> Value { auto fn4077 = s->Global("int"); Arguments args4078; args4078.Add(Get(s->LocalAt(3), Value("step")), false); return Call(c, fn4077, std::move(args4078)); }());
s->SetAt(10, v4076);
auto v4079 = ([&]() -> Value { auto fn4080 = s->Global("int"); Arguments args4081; args4081.Add(Get(s->LocalAt(3), Value("player")), false); return Call(c, fn4080, std::move(args4081)); }());
s->SetAt(7, v4079);
} catch (const Error& error4075) {
if (Matches(error4075, s->Global("Exception"))) {
return ([&]() -> Value { auto fn4082 = s->Global("_PRE_TERMINAL_AGENT"); Arguments args4083; args4083.positional.reserve(2); args4083.Add(s->LocalAt(3), false); args4083.Add(s->LocalAt(2), false); return Call(c, fn4082, std::move(args4083)); }());
}
else { throw; }
}
auto v4084 = ([&]() -> Value { auto fn4085 = PrepareDictionaryGet(s->Global("_TERMINAL_PREVIOUS")); Arguments args4086; args4086.Add(s->LocalAt(7), false); return CallDictionaryGet(c, fn4085, std::move(args4086)); }());
s->SetAt(5, v4084);
if (static_cast<bool>(([&]() -> Value { auto v4087 = ([&]() -> Value { auto v4088 = s->LocalAt(10); Value v4089; v4089 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v4088, v4089))) return Value(false); v4088 = v4089; return Value(true); }()); if (static_cast<bool>(v4087)) return v4087; v4087 = ([&]() -> Value { auto v4090 = ([&]() -> Value { auto v4091 = s->LocalAt(5); Value v4092; v4092 = Value{}; if (!static_cast<bool>(Binary("IsNot", v4091, v4092))) return Value(false); v4091 = v4092; return Value(true); }()); if (!static_cast<bool>(v4090)) return v4090; v4090 = ([&]() -> Value { auto v4093 = s->LocalAt(10); Value v4094; v4094 = s->LocalAt(5); if (!static_cast<bool>(Binary("LtE", v4093, v4094))) return Value(false); v4093 = v4094; return Value(true); }()); return v4090; }()); return v4087; }()))) {
(void)([&]() -> Value { auto fn4095 = Attribute(s->Global("_TERMINAL_PLANS"), "pop"); Arguments args4096; args4096.positional.reserve(2); args4096.Add(s->LocalAt(7), false); args4096.Add(Value{}, false); return Call(c, fn4095, std::move(args4096)); }());
}
auto v4097 = s->LocalAt(10);
Put(s->Global("_TERMINAL_PREVIOUS"), s->LocalAt(7), v4097);
auto v4098 = ([&]() -> Value { auto fn4099 = PrepareDictionaryGet(s->Global("_TERMINAL_PLANS")); Arguments args4100; args4100.Add(s->LocalAt(7), false); return CallDictionaryGet(c, fn4099, std::move(args4100)); }());
s->SetAt(4, v4098);
if (static_cast<bool>(([&]() -> Value { auto v4101 = s->LocalAt(4); if (!static_cast<bool>(v4101)) return v4101; v4101 = ([&]() -> Value { auto fn4102 = PrepareDictionaryGet(s->LocalAt(4)); Arguments args4103; args4103.Add(Value("accepted"), false); return CallDictionaryGet(c, fn4102, std::move(args4103)); }()); if (!static_cast<bool>(v4101)) return v4101; v4101 = ([&]() -> Value { auto v4104 = Value(int64_t{712}); Value v4105; v4105 = s->LocalAt(10); if (!static_cast<bool>(Binary("LtE", v4104, v4105))) return Value(false); v4104 = v4105; v4105 = Value(int64_t{718}); if (!static_cast<bool>(Binary("LtE", v4104, v4105))) return Value(false); v4104 = v4105; return Value(true); }()); return v4101; }()))) {
if (static_cast<bool>(([&]() -> Value { auto v4106 = s->LocalAt(5); Value v4107; v4107 = ([&]() -> Value { auto v4108 = s->LocalAt(10); return Binary("Sub", v4108, Value(int64_t{1})); }()); if (!static_cast<bool>(Binary("NotEq", v4106, v4107))) return Value(false); v4106 = v4107; return Value(true); }()))) {
(void)([&]() -> Value { auto fn4109 = Attribute(s->LocalAt(4), "update"); Arguments args4110; args4110.Keyword("abandoned", Value(true)); args4110.Keyword("reason", Value("nonconsecutive callback")); return Call(c, fn4109, std::move(args4110)); }());
}
try {
auto v4112 = ([&]() -> Value { auto fn4113 = Get(s->Global("_PLANNER_NS"), Value("terminal_action")); Arguments args4114; args4114.positional.reserve(4); args4114.Add(s->LocalAt(3), false); args4114.Add(s->LocalAt(2), false); args4114.Add(Get(Get(s->LocalAt(4), Value("baseline")), ([&]() -> Value { auto v4115 = s->LocalAt(10); return Binary("Sub", v4115, Value(int64_t{712})); }())), false); args4114.Add(s->LocalAt(4), false); return Call(c, fn4113, std::move(args4114)); }());
s->SetAt(6, v4112);
if (static_cast<bool>(([&]() -> Value { auto fn4116 = PrepareDictionaryGet(s->LocalAt(4)); Arguments args4117; args4117.Add(Value("abandoned"), false); return CallDictionaryGet(c, fn4116, std::move(args4117)); }()))) {
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto fn4118 = PrepareDictionaryGet(s->LocalAt(4)); Arguments args4119; args4119.Add(Value("abort_counted"), false); return CallDictionaryGet(c, fn4118, std::move(args4119)); }())))) {
auto v4120 = Value(true);
Put(s->LocalAt(4), Value("abort_counted"), v4120);
auto v4121 = s->Global("_UPGRADE_STATS");
auto v4122 = Value("aborted");
auto v4123 = Get(v4121, v4122);
Put(v4121, v4122, Inplace("Add", v4123, Value(int64_t{1})));
}
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto fn4124 = PrepareDictionaryGet(s->LocalAt(4)); Arguments args4125; args4125.Add(Value("deviated"), false); return CallDictionaryGet(c, fn4124, std::move(args4125)); }())))) {
auto v4126 = ([&]() -> Value { auto fn4127 = Attribute(s->Global("copy"), "deepcopy"); Arguments args4128; args4128.Add(Get(Get(s->LocalAt(4), Value("parent_states_before")), ([&]() -> Value { auto v4129 = s->LocalAt(10); return Binary("Sub", v4129, Value(int64_t{712})); }())), false); return Call(c, fn4127, std::move(args4128)); }());
Put(Attribute(Attribute(s->Global("_IMPL"), "chassis"), "players"), s->LocalAt(7), v4126);
(void)([&]() -> Value { auto fn4130 = Attribute(s->Global("_TERMINAL_PLANS"), "pop"); Arguments args4131; args4131.positional.reserve(2); args4131.Add(s->LocalAt(7), false); args4131.Add(Value{}, false); return Call(c, fn4130, std::move(args4131)); }());
return ([&]() -> Value { auto fn4132 = s->Global("_PRE_TERMINAL_AGENT"); Arguments args4133; args4133.positional.reserve(2); args4133.Add(s->LocalAt(3), false); args4133.Add(s->LocalAt(2), false); return Call(c, fn4132, std::move(args4133)); }());
}
}
auto v4134 = s->Global("_UPGRADE_STATS");
auto v4135 = Value("changed_steps");
auto v4136 = Get(v4134, v4135);
Put(v4134, v4135, Inplace("Add", v4136, ([&]() -> Value { auto fn4137 = s->Global("int"); Arguments args4138; args4138.Add(([&]() -> Value { auto v4139 = s->LocalAt(6); Value v4140; v4140 = Get(Get(s->LocalAt(4), Value("baseline")), ([&]() -> Value { auto v4141 = s->LocalAt(10); return Binary("Sub", v4141, Value(int64_t{712})); }())); if (!static_cast<bool>(Binary("NotEq", v4139, v4140))) return Value(false); v4139 = v4140; return Value(true); }()), false); return Call(c, fn4137, std::move(args4138)); }())));
return s->LocalAt(6);
} catch (const Error& error4111) {
if (Matches(error4111, s->Global("Exception"))) {
auto v4142 = s->Global("_UPGRADE_STATS");
auto v4143 = Value("errors");
auto v4144 = Get(v4142, v4143);
Put(v4142, v4143, Inplace("Add", v4144, Value(int64_t{1})));
if (static_cast<bool>(([&]() -> Value { auto fn4145 = PrepareDictionaryGet(s->LocalAt(4)); Arguments args4146; args4146.Add(Value("deviated"), false); return CallDictionaryGet(c, fn4145, std::move(args4146)); }()))) {
try {
return ([&]() -> Value { auto fn4148 = Get(s->Global("_PLANNER_NS"), Value("_recover_observed")); Arguments args4149; args4149.positional.reserve(4); args4149.Add(s->LocalAt(3), false); args4149.Add(s->LocalAt(2), false); args4149.Add(Get(Get(s->LocalAt(4), Value("baseline")), ([&]() -> Value { auto v4150 = s->LocalAt(10); return Binary("Sub", v4150, Value(int64_t{712})); }())), false); args4149.Add(s->LocalAt(4), false); return Call(c, fn4148, std::move(args4149)); }());
} catch (const Error& error4147) {
if (Matches(error4147, s->Global("Exception"))) {
return ([&]() -> Value { auto fn4151 = s->Global("_parent_liquidate"); Arguments args4152; args4152.positional.reserve(3); args4152.Add(Get(Get(s->LocalAt(3), Value("farms")), s->LocalAt(7)), false); args4152.Add(Get(s->LocalAt(3), Value("private")), false); args4152.Add(Get(Get(s->LocalAt(3), Value("market")), Value("prices")), false); return Call(c, fn4151, std::move(args4152)); }());
}
else { throw; }
}
}
}
else { throw; }
}
}
if (static_cast<bool>(([&]() -> Value { auto v4153 = s->LocalAt(10); Value v4154; v4154 = Value(int64_t{712}); if (!static_cast<bool>(Binary("NotEq", v4153, v4154))) return Value(false); v4153 = v4154; return Value(true); }()))) {
return ([&]() -> Value { auto fn4155 = s->Global("_PRE_TERMINAL_AGENT"); Arguments args4156; args4156.positional.reserve(2); args4156.Add(s->LocalAt(3), false); args4156.Add(s->LocalAt(2), false); return Call(c, fn4155, std::move(args4156)); }());
}
auto v4157 = s->Global("_UPGRADE_STATS");
auto v4158 = Value("planning_calls");
auto v4159 = Get(v4157, v4158);
Put(v4157, v4158, Inplace("Add", v4159, Value(int64_t{1})));
try {
auto v4161 = ([&]() -> Value { auto fn4162 = s->Global("_shadow_terminal"); Arguments args4163; args4163.positional.reserve(2); args4163.Add(s->LocalAt(3), false); args4163.Add(s->LocalAt(2), false); return Call(c, fn4162, std::move(args4163)); }());
s->SetAt(8, v4161);
} catch (const Error& error4160) {
if (Matches(error4160, Tuple({s->Global("ValueError"), s->Global("KeyError"), s->Global("TypeError"), s->Global("IndexError")}))) {
auto v4164 = Value{};
s->SetAt(8, v4164);
}
else { throw; }
}
if (static_cast<bool>(([&]() -> Value { auto v4165 = s->LocalAt(8); Value v4166; v4166 = Value{}; if (!static_cast<bool>(Binary("Is", v4165, v4166))) return Value(false); v4165 = v4166; return Value(true); }()))) {
auto v4167 = s->Global("_UPGRADE_STATS");
auto v4168 = Value("shadow_declines");
auto v4169 = Get(v4167, v4168);
Put(v4167, v4168, Inplace("Add", v4169, Value(int64_t{1})));
return ([&]() -> Value { auto fn4170 = s->Global("_PRE_TERMINAL_AGENT"); Arguments args4171; args4171.positional.reserve(2); args4171.Add(s->LocalAt(3), false); args4171.Add(s->LocalAt(2), false); return Call(c, fn4170, std::move(args4171)); }());
}
auto v4172 = s->LocalAt(8);
auto unpack4173 = Iterate(v4172);
ValidateUnpack(unpack4173, 2, false);
s->SetAt(1, unpack4173.at(0));
s->SetAt(9, unpack4173.at(1));
auto v4174 = ([&]() -> Value { auto fn4175 = s->Global("_PRE_TERMINAL_AGENT"); Arguments args4176; args4176.positional.reserve(2); args4176.Add(s->LocalAt(3), false); args4176.Add(s->LocalAt(2), false); return Call(c, fn4175, std::move(args4176)); }());
s->SetAt(0, v4174);
if (static_cast<bool>(([&]() -> Value { auto v4177 = s->LocalAt(0); Value v4178; v4178 = Get(s->LocalAt(1), Value(int64_t{0})); if (!static_cast<bool>(Binary("NotEq", v4177, v4178))) return Value(false); v4177 = v4178; return Value(true); }()))) {
auto v4179 = s->Global("_UPGRADE_STATS");
auto v4180 = Value("shadow_declines");
auto v4181 = Get(v4179, v4180);
Put(v4179, v4180, Inplace("Add", v4181, Value(int64_t{1})));
return s->LocalAt(0);
}
try {
auto v4183 = ([&]() -> Value { auto fn4184 = Get(s->Global("_PLANNER_NS"), Value("plan_terminal")); Arguments args4185; args4185.positional.reserve(3); args4185.Add(s->LocalAt(3), false); args4185.Add(s->LocalAt(2), false); args4185.Add(s->LocalAt(1), false); args4185.Keyword("max_simulations", Value(int64_t{64})); args4185.Keyword("passes", Value(int64_t{1})); args4185.Keyword("proposals_per_actor", Value(int64_t{4})); return Call(c, fn4184, std::move(args4185)); }());
s->SetAt(4, v4183);
auto v4186 = ([&]() -> Value { auto fn4187 = s->Global("max"); Arguments args4188; args4188.positional.reserve(2); args4188.Add(Get(s->Global("_UPGRADE_STATS"), Value("max_planning_ms")), false); args4188.Add(([&]() -> Value { auto fn4189 = PrepareDictionaryGet(s->LocalAt(4)); Arguments args4190; args4190.positional.reserve(2); args4190.Add(Value("planning_ms"), false); args4190.Add(Value(0.0), false); return CallDictionaryGet(c, fn4189, std::move(args4190)); }()), false); return Call(c, fn4187, std::move(args4188)); }());
Put(s->Global("_UPGRADE_STATS"), Value("max_planning_ms"), v4186);
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto fn4191 = PrepareDictionaryGet(s->LocalAt(4)); Arguments args4192; args4192.Add(Value("accepted"), false); return CallDictionaryGet(c, fn4191, std::move(args4192)); }())))) {
return s->LocalAt(0);
}
auto v4193 = s->LocalAt(9);
Put(s->LocalAt(4), Value("parent_states_before"), v4193);
auto v4194 = s->LocalAt(4);
Put(s->Global("_TERMINAL_PLANS"), s->LocalAt(7), v4194);
auto v4195 = s->Global("_UPGRADE_STATS");
auto v4196 = Value("accepted");
auto v4197 = Get(v4195, v4196);
Put(v4195, v4196, Inplace("Add", v4197, Value(int64_t{1})));
auto v4198 = ([&]() -> Value { auto fn4199 = Get(s->Global("_PLANNER_NS"), Value("terminal_action")); Arguments args4200; args4200.positional.reserve(4); args4200.Add(s->LocalAt(3), false); args4200.Add(s->LocalAt(2), false); args4200.Add(s->LocalAt(0), false); args4200.Add(s->LocalAt(4), false); return Call(c, fn4199, std::move(args4200)); }());
s->SetAt(6, v4198);
auto v4201 = s->Global("_UPGRADE_STATS");
auto v4202 = Value("changed_steps");
auto v4203 = Get(v4201, v4202);
Put(v4201, v4202, Inplace("Add", v4203, ([&]() -> Value { auto fn4204 = s->Global("int"); Arguments args4205; args4205.Add(([&]() -> Value { auto v4206 = s->LocalAt(6); Value v4207; v4207 = s->LocalAt(0); if (!static_cast<bool>(Binary("NotEq", v4206, v4207))) return Value(false); v4206 = v4207; return Value(true); }()), false); return Call(c, fn4204, std::move(args4205)); }())));
return s->LocalAt(6);
} catch (const Error& error4182) {
if (Matches(error4182, s->Global("Exception"))) {
auto v4208 = s->Global("_UPGRADE_STATS");
auto v4209 = Value("errors");
auto v4210 = Get(v4208, v4209);
Put(v4208, v4209, Inplace("Add", v4210, Value(int64_t{1})));
return s->LocalAt(0);
}
else { throw; }
}
return {};
}
}  // namespace kagg::opponents::compiled
