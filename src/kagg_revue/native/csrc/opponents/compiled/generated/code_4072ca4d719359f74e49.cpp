// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_4072ca4d719359f74e49(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "actor", "command", "commands", "configuration", "day", "farm", "fertilizer_worker", "index", "name", "native", "observation", "pending", "player", "quantity", "role", "state", "step", "targets"};
s->PrepareSlots(s_names);
auto v4915 = ([&]() -> Value { auto fn4916 = s->Global("_V219_PARENT"); Arguments args4917; args4917.positional.reserve(2); args4917.Add(s->LocalAt(11), false); args4917.Add(s->LocalAt(4), false); return Call(c, fn4916, std::move(args4917)); }());
s->SetAt(0, v4915);
auto v4918 = ([&]() -> Value { auto fn4919 = s->Global("int"); Arguments args4920; args4920.Add(Get(s->LocalAt(11), Value("step")), false); return Call(c, fn4919, std::move(args4920)); }());
s->SetAt(17, v4918);
auto v4921 = ([&]() -> Value { auto fn4922 = s->Global("int"); Arguments args4923; args4923.Add(Get(s->LocalAt(11), Value("player")), false); return Call(c, fn4922, std::move(args4923)); }());
s->SetAt(13, v4921);
auto v4924 = ([&]() -> Value { auto v4925 = s->LocalAt(17); return Binary("FloorDiv", v4925, Value(int64_t{24})); }());
s->SetAt(5, v4924);
auto v4926 = ([&]() -> Value { auto fn4927 = PrepareDictionaryGet(s->Global("_V219_STATES")); Arguments args4928; args4928.Add(s->LocalAt(13), false); return CallDictionaryGet(c, fn4927, std::move(args4928)); }());
s->SetAt(16, v4926);
if (static_cast<bool>(([&]() -> Value { auto v4929 = ([&]() -> Value { auto v4930 = s->LocalAt(16); Value v4931; v4931 = Value{}; if (!static_cast<bool>(Binary("Is", v4930, v4931))) return Value(false); v4930 = v4931; return Value(true); }()); if (static_cast<bool>(v4929)) return v4929; v4929 = ([&]() -> Value { auto v4932 = s->LocalAt(17); Value v4933; v4933 = Get(s->LocalAt(16), Value("last_step")); if (!static_cast<bool>(Binary("LtE", v4932, v4933))) return Value(false); v4932 = v4933; return Value(true); }()); return v4929; }()))) {
auto v4934 = ([&]() -> Value { auto dict4935 = Dict(); auto key4936 = Value("last_step"); Put(dict4935, key4936, s->LocalAt(17)); auto key4937 = Value("day"); Put(dict4935, key4937, Unary("USub", Value(int64_t{1}))); auto key4938 = Value("workers"); Put(dict4935, key4938, ([&]() -> Value { auto dict4939 = Dict(); return dict4939; }())); auto key4940 = Value("last_work"); Put(dict4935, key4940, ([&]() -> Value { auto dict4941 = Dict(); return dict4941; }())); auto key4942 = Value("seen_plants"); Put(dict4935, key4942, ([&]() -> Value { auto fn4943 = s->Global("set"); Arguments args4944; return Call(c, fn4943, std::move(args4944)); }())); auto key4945 = Value("lost"); Put(dict4935, key4945, ([&]() -> Value { auto fn4946 = s->Global("set"); Arguments args4947; return Call(c, fn4946, std::move(args4947)); }())); auto key4948 = Value("targets"); Put(dict4935, key4948, ([&]() -> Value { auto comp4949 = std::make_shared<Scope>(); comp4949->globals = s->globals; comp4949->parent = s; static constexpr const char* comp4949_names[] = {"x", "y"}; comp4949->PrepareSlots(comp4949_names); auto result4950 = List(); for (const auto& item4951 : Iterate(Tuple({Value(int64_t{5}), Value(int64_t{6})}))) { comp4949->SetAt(1, item4951); for (const auto& item4952 : Iterate(([&]() -> Value { auto fn4953 = comp4949->Global("range"); Arguments args4954; args4954.positional.reserve(2); args4954.Add(Value(int64_t{5}), false); args4954.Add(Value(int64_t{10}), false); return Call(c, fn4953, std::move(args4954)); }()))) { comp4949->SetAt(0, item4952); result4950.node()->sequence.push_back(Tuple({comp4949->LocalAt(0), comp4949->LocalAt(1)})); } } return result4950; }())); return dict4935; }());
s->SetAt(16, v4934);
auto v4955 = s->LocalAt(16);
Put(s->Global("_V219_STATES"), s->LocalAt(13), v4955);
}
auto v4956 = s->LocalAt(17);
Put(s->LocalAt(16), Value("last_step"), v4956);
auto v4957 = Get(Attribute(Attribute(s->Global("_IMPL"), "chassis"), "players"), s->LocalAt(13));
s->SetAt(10, v4957);
if (static_cast<bool>(([&]() -> Value { auto v4958 = s->LocalAt(17); Value v4959; v4959 = Value(int64_t{432}); if (!static_cast<bool>(Binary("Eq", v4958, v4959))) return Value(false); v4958 = v4959; return Value(true); }()))) {
auto v4960 = ([&]() -> Value { auto fn4961 = s->Global("_v219_qualifies"); Arguments args4962; args4962.positional.reserve(2); args4962.Add(s->LocalAt(11), false); args4962.Add(s->LocalAt(10), false); return Call(c, fn4961, std::move(args4962)); }());
Put(s->LocalAt(16), Value("eligible"), v4960);
}
if (static_cast<bool>(([&]() -> Value { auto v4963 = Unary("Not", ([&]() -> Value { auto fn4964 = PrepareDictionaryGet(s->LocalAt(16)); Arguments args4965; args4965.Add(Value("eligible"), false); return CallDictionaryGet(c, fn4964, std::move(args4965)); }())); if (static_cast<bool>(v4963)) return v4963; v4963 = ([&]() -> Value { auto v4966 = s->LocalAt(5); Value v4967; v4967 = Value(int64_t{18}); if (!static_cast<bool>(Binary("Lt", v4966, v4967))) return Value(false); v4966 = v4967; return Value(true); }()); return v4963; }()))) {
return s->LocalAt(0);
}
if (static_cast<bool>(([&]() -> Value { auto v4968 = Get(s->LocalAt(16), Value("day")); Value v4969; v4969 = s->LocalAt(5); if (!static_cast<bool>(Binary("NotEq", v4968, v4969))) return Value(false); v4968 = v4969; return Value(true); }()))) {
auto v4970 = s->LocalAt(5);
Put(s->LocalAt(16), Value("day"), v4970);
auto v4971 = ([&]() -> Value { auto dict4972 = Dict(); return dict4972; }());
Put(s->LocalAt(16), Value("workers"), v4971);
auto v4973 = ([&]() -> Value { auto dict4974 = Dict(); return dict4974; }());
Put(s->LocalAt(16), Value("last_work"), v4973);
}
auto v4975 = Get(Get(s->LocalAt(11), Value("farms")), s->LocalAt(13));
s->SetAt(6, v4975);
auto v4976 = ([&]() -> Value { auto fn4977 = Attribute(s->LocalAt(16), "pop"); Arguments args4978; args4978.positional.reserve(2); args4978.Add(Value("pending"), false); args4978.Add(Value{}, false); return Call(c, fn4977, std::move(args4978)); }());
s->SetAt(12, v4976);
if (static_cast<bool>(s->LocalAt(12))) {
if (static_cast<bool>(([&]() -> Value { auto v4979 = ([&]() -> Value { auto v4980 = ([&]() -> Value { auto v4982 = ([&]() -> Value { auto fn4983 = s->Global("len"); Arguments args4984; args4984.Add(Get(s->LocalAt(6), Value("hands")), false); return Call(c, fn4983, std::move(args4984)); }()); return Binary("Add", v4982, Value(int64_t{1})); }()); Value v4981; v4981 = ([&]() -> Value { auto v4985 = Get(s->LocalAt(12), Value("first_actor")); return Binary("Add", v4985, Get(s->LocalAt(12), Value("count"))); }()); if (!static_cast<bool>(Binary("GtE", v4980, v4981))) return Value(false); v4980 = v4981; return Value(true); }()); if (!static_cast<bool>(v4979)) return v4979; v4979 = ([&]() -> Value { auto v4986 = Value("SE"); Value v4987; v4987 = Get(s->LocalAt(6), Value("unlocked_quadrants")); if (!static_cast<bool>(Binary("In", v4986, v4987))) return Value(false); v4986 = v4987; return Value(true); }()); return v4979; }()))) {
for (const auto& item4988 : Iterate(([&]() -> Value { auto fn4989 = s->Global("range"); Arguments args4990; args4990.Add(Get(s->LocalAt(12), Value("count")), false); return Call(c, fn4989, std::move(args4990)); }()))) {
s->SetAt(8, item4988);
auto v4991 = ([&]() -> Value { auto v4992 = s->LocalAt(8); Value v4993; v4993 = Get(s->LocalAt(12), Value("crop_workers")); if (!static_cast<bool>(Binary("Eq", v4992, v4993))) return Value(false); v4992 = v4993; return Value(true); }());
s->SetAt(7, v4991);
if (static_cast<bool>(s->LocalAt(7))) {
auto v4994 = Get(s->LocalAt(16), Value("targets"));
s->SetAt(18, v4994);
}
else {
if (static_cast<bool>(([&]() -> Value { auto v4995 = Get(s->LocalAt(12), Value("crop_workers")); Value v4996; v4996 = Value(int64_t{1}); if (!static_cast<bool>(Binary("Eq", v4995, v4996))) return Value(false); v4995 = v4996; return Value(true); }()))) {
auto v4997 = Get(s->LocalAt(16), Value("targets"));
s->SetAt(18, v4997);
}
else {
if (static_cast<bool>(([&]() -> Value { auto v4998 = Get(s->LocalAt(12), Value("crop_workers")); Value v4999; v4999 = Value(int64_t{2}); if (!static_cast<bool>(Binary("Eq", v4998, v4999))) return Value(false); v4998 = v4999; return Value(true); }()))) {
auto v5000 = Slice(Get(s->LocalAt(16), Value("targets")), ([&]() -> Value { auto v5001 = s->LocalAt(8); return Binary("Mult", v5001, Value(int64_t{5})); }()), ([&]() -> Value { auto v5002 = ([&]() -> Value { auto v5003 = s->LocalAt(8); return Binary("Mult", v5003, Value(int64_t{5})); }()); return Binary("Add", v5002, Value(int64_t{5})); }()), Value{});
s->SetAt(18, v5000);
}
else {
auto v5004 = Get(List({List({Tuple({Value(int64_t{5}), Value(int64_t{5})}), Tuple({Value(int64_t{6}), Value(int64_t{5})}), Tuple({Value(int64_t{7}), Value(int64_t{5})})}), List({Tuple({Value(int64_t{8}), Value(int64_t{5})}), Tuple({Value(int64_t{9}), Value(int64_t{5})}), Tuple({Value(int64_t{9}), Value(int64_t{6})}), Tuple({Value(int64_t{8}), Value(int64_t{6})})}), List({Tuple({Value(int64_t{5}), Value(int64_t{6})}), Tuple({Value(int64_t{6}), Value(int64_t{6})}), Tuple({Value(int64_t{7}), Value(int64_t{6})})})}), s->LocalAt(8));
s->SetAt(18, v5004);
}
}
}
auto v5005 = ([&]() -> Value { auto dict5006 = Dict(); auto key5007 = Value("kind"); Put(dict5006, key5007, (static_cast<bool>(s->LocalAt(7)) ? Value("fertilizer") : Value("crop"))); auto key5008 = Value("targets"); Put(dict5006, key5008, s->LocalAt(18)); auto key5009 = Value("needs_fertilizer"); Put(dict5006, key5009, ([&]() -> Value { auto v5010 = Get(s->LocalAt(12), Value("fertilizer")); if (!static_cast<bool>(v5010)) return v5010; v5010 = ([&]() -> Value { auto v5011 = ([&]() -> Value { auto v5012 = s->LocalAt(5); Value v5013; v5013 = Value(int64_t{24}); if (!static_cast<bool>(Binary("Eq", v5012, v5013))) return Value(false); v5012 = v5013; return Value(true); }()); if (static_cast<bool>(v5011)) return v5011; v5011 = s->LocalAt(7); return v5011; }()); return v5010; }())); return dict5006; }());
Put(Get(s->LocalAt(16), Value("workers")), ([&]() -> Value { auto v5014 = Get(s->LocalAt(12), Value("first_actor")); return Binary("Add", v5014, s->LocalAt(8)); }()), v5005);
if (static_cast<bool>(([&]() -> Value { auto v5015 = ([&]() -> Value { auto fn5017 = PrepareDictionaryGet(s->LocalAt(12)); Arguments args5018; args5018.Add(Value("labor"), false); return CallDictionaryGet(c, fn5017, std::move(args5018)); }()); Value v5016; v5016 = Value{}; if (!static_cast<bool>(Binary("IsNot", v5015, v5016))) return Value(false); v5015 = v5016; return Value(true); }()))) {
auto v5019 = Get(Get(s->LocalAt(16), Value("workers")), ([&]() -> Value { auto v5020 = Get(s->LocalAt(12), Value("first_actor")); return Binary("Add", v5020, s->LocalAt(8)); }()));
s->SetAt(15, v5019);
auto v5021 = ([&]() -> Value { auto comp5022 = std::make_shared<Scope>(); comp5022->globals = s->globals; comp5022->parent = s; static constexpr const char* comp5022_names[] = {"p"}; comp5022->PrepareSlots(comp5022_names); auto result5023 = List(); for (const auto& item5024 : Iterate(Get(Get(Get(s->LocalAt(12), Value("labor")), Value("paths")), s->LocalAt(8)))) { comp5022->SetAt(0, item5024); result5023.node()->sequence.push_back(([&]() -> Value { auto fn5025 = comp5022->Global("tuple"); Arguments args5026; args5026.Add(comp5022->LocalAt(0), false); return Call(c, fn5025, std::move(args5026)); }())); } return result5023; }());
Put(s->LocalAt(15), Value("targets"), v5021);
auto v5027 = Get(Get(s->LocalAt(12), Value("labor")), Value("fertilizer"));
Put(s->LocalAt(15), Value("needs_fertilizer"), v5027);
auto v5028 = ([&]() -> Value { auto fn5029 = s->Global("len"); Arguments args5030; args5030.Add(Get(s->LocalAt(15), Value("targets")), false); return Call(c, fn5029, std::move(args5030)); }());
Put(s->LocalAt(15), Value("fertilizer_quantity"), v5028);
if (static_cast<bool>(([&]() -> Value { auto v5031 = ([&]() -> Value { auto fn5033 = s->Global("tuple"); Arguments args5034; args5034.Add(Get(Get(s->LocalAt(6), Value("hands")), ([&]() -> Value { auto v5035 = ([&]() -> Value { auto v5036 = Get(s->LocalAt(12), Value("first_actor")); return Binary("Add", v5036, s->LocalAt(8)); }()); return Binary("Sub", v5035, Value(int64_t{1})); }())), false); return Call(c, fn5033, std::move(args5034)); }()); Value v5032; v5032 = ([&]() -> Value { auto fn5037 = s->Global("tuple"); Arguments args5038; args5038.Add(Get(Get(Get(s->LocalAt(12), Value("labor")), Value("spawns")), s->LocalAt(8)), false); return Call(c, fn5037, std::move(args5038)); }()); if (!static_cast<bool>(Binary("NotEq", v5031, v5032))) return Value(false); v5031 = v5032; return Value(true); }()))) {
auto v5039 = s->Global("_R53_LABOR_REPORT");
auto v5040 = Value("labor_spawn_errors");
auto v5041 = Get(v5039, v5040);
Put(v5039, v5040, Inplace("Add", v5041, Value(int64_t{1})));
}
if (static_cast<bool>(([&]() -> Value { auto v5042 = s->LocalAt(8); Value v5043; v5043 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v5042, v5043))) return Value(false); v5042 = v5043; return Value(true); }()))) {
auto v5044 = s->Global("_R53_LABOR_REPORT");
auto v5045 = Value("labor_confirmed");
auto v5046 = Get(v5044, v5045);
Put(v5044, v5045, Inplace("Add", v5046, Value(int64_t{1})));
}
}
}
auto v5047 = s->Global("_V219_REPORT");
auto v5048 = Value("confirmed_workers");
auto v5049 = Get(v5047, v5048);
Put(v5047, v5048, Inplace("Add", v5049, Get(s->LocalAt(12), Value("count"))));
}
else {
auto v5050 = s->Global("_V219_REPORT");
auto v5051 = Value("hire_shortfalls");
auto v5052 = Get(v5050, v5051);
Put(v5050, v5051, Inplace("Add", v5052, Get(s->LocalAt(12), Value("count"))));
}
}
auto v5053 = ([&]() -> Value { auto fn5054 = s->Global("_v219_request"); Arguments args5055; args5055.positional.reserve(4); args5055.Add(s->LocalAt(11), false); args5055.Add(s->LocalAt(0), false); args5055.Add(s->LocalAt(16), false); args5055.Add(s->LocalAt(10), false); return Call(c, fn5054, std::move(args5055)); }());
s->SetAt(0, v5053);
if (static_cast<bool>(Get(s->LocalAt(16), Value("workers")))) {
auto v5056 = ([&]() -> Value { auto v5057 = List({([&]() -> Value { auto v5058 = ([&]() -> Value { auto fn5059 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args5060; args5060.Add(Value("farmer"), false); return CallDictionaryGet(c, fn5059, std::move(args5060)); }()); if (static_cast<bool>(v5058)) return v5058; v5058 = List({Value("PASS")}); return v5058; }())}); return Binary("Add", v5057, ([&]() -> Value { auto fn5061 = s->Global("list"); Arguments args5062; args5062.Add(([&]() -> Value { auto v5063 = ([&]() -> Value { auto fn5064 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args5065; args5065.Add(Value("hands"), false); return CallDictionaryGet(c, fn5064, std::move(args5065)); }()); if (static_cast<bool>(v5063)) return v5063; v5063 = List({}); return v5063; }()), false); return Call(c, fn5061, std::move(args5062)); }())); }());
s->SetAt(3, v5056);
auto v5066 = s->LocalAt(3);
s->SetAt(3, Inplace("Add", v5066, ([&]() -> Value { auto comp5067 = std::make_shared<Scope>(); comp5067->globals = s->globals; comp5067->parent = s; static constexpr const char* comp5067_names[] = {"_"}; comp5067->PrepareSlots(comp5067_names); auto result5068 = List(); for (const auto& item5069 : Iterate(([&]() -> Value { auto fn5070 = s->Global("range"); Arguments args5071; args5071.Add(([&]() -> Value { auto v5072 = ([&]() -> Value { auto v5073 = ([&]() -> Value { auto fn5074 = s->Global("len"); Arguments args5075; args5075.Add(Get(s->LocalAt(6), Value("hands")), false); return Call(c, fn5074, std::move(args5075)); }()); return Binary("Add", v5073, Value(int64_t{1})); }()); return Binary("Sub", v5072, ([&]() -> Value { auto fn5076 = s->Global("len"); Arguments args5077; args5077.Add(s->LocalAt(3), false); return Call(c, fn5076, std::move(args5077)); }())); }()), false); return Call(c, fn5070, std::move(args5071)); }()))) { comp5067->SetAt(0, item5069); result5068.node()->sequence.push_back(List({Value("PASS")})); } return result5068; }())));
for (const auto& item5078 : Iterate(([&]() -> Value { auto fn5079 = Attribute(Get(s->LocalAt(16), Value("workers")), "items"); Arguments args5080; return Call(c, fn5079, std::move(args5080)); }()))) {
auto unpack5081 = Iterate(item5078);
ValidateUnpack(unpack5081, 2, false);
s->SetAt(1, unpack5081.at(0));
s->SetAt(15, unpack5081.at(1));
if (static_cast<bool>(([&]() -> Value { auto v5082 = s->LocalAt(1); Value v5083; v5083 = ([&]() -> Value { auto fn5084 = s->Global("len"); Arguments args5085; args5085.Add(s->LocalAt(3), false); return Call(c, fn5084, std::move(args5085)); }()); if (!static_cast<bool>(Binary("GtE", v5082, v5083))) return Value(false); v5082 = v5083; return Value(true); }()))) {
continue;
}
auto v5086 = ([&]() -> Value { auto fn5087 = s->Global("_v219_worker"); Arguments args5088; args5088.positional.reserve(4); args5088.Add(s->LocalAt(11), false); args5088.Add(s->LocalAt(16), false); args5088.Add(s->LocalAt(1), false); args5088.Add(s->LocalAt(15), false); return Call(c, fn5087, std::move(args5088)); }());
s->SetAt(2, v5086);
auto v5089 = s->LocalAt(2);
Put(s->LocalAt(3), s->LocalAt(1), v5089);
auto v5090 = ([&]() -> Value { auto fn5091 = PrepareDictionaryGet(([&]() -> Value { auto dict5093 = Dict(); auto key5094 = Value("PLANT"); Put(dict5093, key5094, Value("plant_requests")); auto key5095 = Value("WATER"); Put(dict5093, key5095, Value("water_requests")); auto key5096 = Value("FERTILIZE"); Put(dict5093, key5096, Value("fertilize_requests")); auto key5097 = Value("HARVEST"); Put(dict5093, key5097, Value("harvest_requests")); auto key5098 = Value("DROP"); Put(dict5093, key5098, Value("drop_requests")); return dict5093; }())); Arguments args5092; args5092.Add(Get(s->LocalAt(2), Value(int64_t{0})), false); return CallDictionaryGet(c, fn5091, std::move(args5092)); }());
s->SetAt(9, v5090);
if (static_cast<bool>(s->LocalAt(9))) {
auto v5099 = s->Global("_V219_REPORT");
auto v5100 = s->LocalAt(9);
auto v5101 = Get(v5099, v5100);
Put(v5099, v5100, Inplace("Add", v5101, Value(int64_t{1})));
}
auto v5102 = ([&]() -> Value { auto dict5103 = Dict(); auto key5104 = Value("step"); Put(dict5103, key5104, s->LocalAt(17)); auto key5105 = Value("command"); Put(dict5103, key5105, s->LocalAt(2)); auto key5106 = Value("tomatoes"); Put(dict5103, key5106, ([&]() -> Value { auto fn5107 = PrepareDictionaryGet(Get(Get(Get(s->LocalAt(11), Value("private")), Value("inventories")), s->LocalAt(1))); Arguments args5108; args5108.positional.reserve(2); args5108.Add(Value("TOMATO"), false); args5108.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn5107, std::move(args5108)); }())); return dict5103; }());
Put(Get(s->LocalAt(16), Value("last_work")), s->LocalAt(1), v5102);
}
auto v5109 = ([&]() -> Value { auto fn5110 = Attribute(s->Global("copy"), "deepcopy"); Arguments args5111; args5111.Add(s->LocalAt(0), false); return Call(c, fn5110, std::move(args5111)); }());
s->SetAt(0, v5109);
auto v5112 = Tuple({Get(s->LocalAt(3), Value(int64_t{0})), Slice(s->LocalAt(3), Value(int64_t{1}), Value{}, Value{})});
auto unpack5113 = Iterate(v5112);
ValidateUnpack(unpack5113, 2, false);
Put(s->LocalAt(0), Value("farmer"), unpack5113.at(0));
Put(s->LocalAt(0), Value("hands"), unpack5113.at(1));
}
if (static_cast<bool>(([&]() -> Value { auto v5114 = ([&]() -> Value { auto fn5115 = PrepareDictionaryGet(s->LocalAt(16)); Arguments args5116; args5116.Add(Value("committed"), false); return CallDictionaryGet(c, fn5115, std::move(args5116)); }()); if (!static_cast<bool>(v5114)) return v5114; v5114 = ([&]() -> Value { auto v5117 = ([&]() -> Value { auto fn5119 = s->Global("len"); Arguments args5120; args5120.Add(Get(s->LocalAt(0), Value("market")), false); return Call(c, fn5119, std::move(args5120)); }()); Value v5118; v5118 = s->Global("MAX_ORDERS"); if (!static_cast<bool>(Binary("Lt", v5117, v5118))) return Value(false); v5117 = v5118; return Value(true); }()); if (!static_cast<bool>(v5114)) return v5114; v5114 = Unary("Not", ([&]() -> Value { auto comp5121 = std::make_shared<Scope>(); comp5121->globals = s->globals; comp5121->parent = s; static constexpr const char* comp5121_names[] = {"o"}; comp5121->PrepareSlots(comp5121_names); auto result5122 = List(); for (const auto& item5123 : Iterate(Get(s->LocalAt(0), Value("market")))) { comp5121->SetAt(0, item5123); if (static_cast<bool>(([&]() -> Value { auto v5124 = Slice(comp5121->LocalAt(0), Value{}, Value(int64_t{2}), Value{}); Value v5125; v5125 = List({Value("SELL"), Value("TOMATO")}); if (!static_cast<bool>(Binary("Eq", v5124, v5125))) return Value(false); v5124 = v5125; return Value(true); }()))) return Value(true); } return Value(false); }())); return v5114; }()))) {
auto v5126 = ([&]() -> Value { auto fn5127 = PrepareDictionaryGet(([&]() -> Value { auto fn5129 = s->Global("projected_shed"); Arguments args5130; args5130.positional.reserve(2); args5130.Add(s->LocalAt(0), false); args5130.Add(([&]() -> Value { auto fn5131 = s->Global("FarmView"); Arguments args5132; args5132.Add(s->LocalAt(11), false); return Call(c, fn5131, std::move(args5132)); }()), false); return Call(c, fn5129, std::move(args5130)); }())); Arguments args5128; args5128.positional.reserve(2); args5128.Add(Value("TOMATO"), false); args5128.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn5127, std::move(args5128)); }());
s->SetAt(14, v5126);
if (static_cast<bool>(([&]() -> Value { auto v5133 = s->LocalAt(14); Value v5134; v5134 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v5133, v5134))) return Value(false); v5133 = v5134; return Value(true); }()))) {
auto v5135 = ([&]() -> Value { auto fn5136 = Attribute(s->Global("copy"), "deepcopy"); Arguments args5137; args5137.Add(s->LocalAt(0), false); return Call(c, fn5136, std::move(args5137)); }());
s->SetAt(0, v5135);
(void)([&]() -> Value { auto fn5138 = Attribute(Get(s->LocalAt(0), Value("market")), "append"); Arguments args5139; args5139.Add(List({Value("SELL"), Value("TOMATO"), s->LocalAt(14)}), false); return Call(c, fn5138, std::move(args5139)); }());
auto v5140 = s->Global("_V219_REPORT");
auto v5141 = Value("tomato_sale_requests");
auto v5142 = Get(v5140, v5141);
Put(v5140, v5141, Inplace("Add", v5142, s->LocalAt(14)));
}
}
return s->LocalAt(0);
return {};
}
}  // namespace kagg::opponents::compiled
