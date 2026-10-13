// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_5094eef4970c53f5bc05(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "extra", "native", "obs", "out", "pending", "result", "state", "wool"};
s->PrepareSlots(s_names);
auto v30979 = ([&]() -> Value { auto fn30980 = s->Global("_VT_REQUEST"); Arguments args30981; args30981.positional.reserve(4); args30981.Add(s->LocalAt(3), false); args30981.Add(s->LocalAt(0), false); args30981.Add(s->LocalAt(7), false); args30981.Add(s->LocalAt(2), false); return Call(c, fn30980, std::move(args30981)); }());
s->SetAt(6, v30979);
if (static_cast<bool>(([&]() -> Value { auto v30982 = ([&]() -> Value { auto v30983 = s->LocalAt(6); Value v30984; v30984 = s->LocalAt(0); if (!static_cast<bool>(Binary("Is", v30983, v30984))) return Value(false); v30983 = v30984; return Value(true); }()); if (static_cast<bool>(v30982)) return v30982; v30982 = ([&]() -> Value { auto v30985 = ([&]() -> Value { auto v30987 = ([&]() -> Value { auto fn30988 = s->Global("int"); Arguments args30989; args30989.Add(Get(s->LocalAt(3), Value("step")), false); return Call(c, fn30988, std::move(args30989)); }()); return Binary("FloorDiv", v30987, Value(int64_t{24})); }()); Value v30986; v30986 = Value(int64_t{29}); if (!static_cast<bool>(Binary("NotEq", v30985, v30986))) return Value(false); v30985 = v30986; return Value(true); }()); if (static_cast<bool>(v30982)) return v30982; v30982 = Unary("Not", ([&]() -> Value { auto fn30990 = PrepareDictionaryGet(s->LocalAt(7)); Arguments args30991; args30991.Add(Value("committed"), false); return CallDictionaryGet(c, fn30990, std::move(args30991)); }())); return v30982; }()))) {
return s->LocalAt(6);
}
auto v30992 = ([&]() -> Value { auto fn30993 = PrepareDictionaryGet(s->LocalAt(7)); Arguments args30994; args30994.Add(Value("pending"), false); return CallDictionaryGet(c, fn30993, std::move(args30994)); }());
s->SetAt(5, v30992);
if (static_cast<bool>(([&]() -> Value { auto v30995 = Unary("Not", s->LocalAt(5)); if (static_cast<bool>(v30995)) return v30995; v30995 = ([&]() -> Value { auto fn30996 = PrepareDictionaryGet(s->LocalAt(5)); Arguments args30997; args30997.Add(Value("initial"), false); return CallDictionaryGet(c, fn30996, std::move(args30997)); }()); return v30995; }()))) {
return s->LocalAt(6);
}
auto v30998 = ([&]() -> Value { auto fn30999 = s->Global("_vt_wool_tiles"); Arguments args31000; args31000.Add(s->LocalAt(3), false); return Call(c, fn30999, std::move(args31000)); }());
s->SetAt(8, v30998);
auto v31001 = Slice(Get(s->LocalAt(6), Value("market")), ([&]() -> Value { auto fn31002 = s->Global("len"); Arguments args31003; args31003.Add(([&]() -> Value { auto fn31004 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args31005; args31005.positional.reserve(2); args31005.Add(Value("market"), false); args31005.Add(List({}), false); return CallDictionaryGet(c, fn31004, std::move(args31005)); }()), false); return Call(c, fn31002, std::move(args31003)); }()), Value{}, Value{});
s->SetAt(1, v31001);
if (static_cast<bool>(Unary("Not", s->LocalAt(8)))) {
(void)([&]() -> Value { auto fn31006 = Attribute(s->LocalAt(7), "pop"); Arguments args31007; args31007.positional.reserve(2); args31007.Add(Value("pending"), false); args31007.Add(Value{}, false); return Call(c, fn31006, std::move(args31007)); }());
auto v31008 = s->Global("_V233_REPORT");
auto v31009 = Value("sheep_hire_requests");
auto v31010 = Get(v31008, v31009);
Put(v31008, v31009, Inplace("Sub", v31010, ([&]() -> Value { auto fn31011 = s->Global("sum"); Arguments args31012; args31012.Add(([&]() -> Value { auto comp31013 = std::make_shared<Scope>(); comp31013->globals = s->globals; comp31013->parent = s; static constexpr const char* comp31013_names[] = {"o"}; comp31013->PrepareSlots(comp31013_names); auto result31014 = List(); for (const auto& item31015 : Iterate(s->LocalAt(1))) { comp31013->SetAt(0, item31015); result31014.node()->sequence.push_back(([&]() -> Value { auto v31016 = comp31013->LocalAt(0); Value v31017; v31017 = List({Value("HIRE")}); if (!static_cast<bool>(Binary("Eq", v31016, v31017))) return Value(false); v31016 = v31017; return Value(true); }())); } return result31014; }()), false); return Call(c, fn31011, std::move(args31012)); }())));
auto v31018 = s->Global("_V233_REPORT");
auto v31019 = Value("sheep_feed_buy_requests");
auto v31020 = Get(v31018, v31019);
Put(v31018, v31019, Inplace("Sub", v31020, Value(int64_t{6})));
auto v31021 = s->Global("_VT_REPORT");
auto v31022 = Value("vt_no_hire_days");
auto v31023 = Get(v31021, v31022);
Put(v31021, v31022, Inplace("Add", v31023, Value(int64_t{1})));
return s->LocalAt(0);
}
auto v31024 = ([&]() -> Value { auto fn31025 = Attribute(s->Global("copy"), "deepcopy"); Arguments args31026; args31026.Add(s->LocalAt(0), false); return Call(c, fn31025, std::move(args31026)); }());
s->SetAt(4, v31024);
auto v31027 = ([&]() -> Value { auto v31028 = ([&]() -> Value { auto fn31029 = s->Global("list"); Arguments args31030; args31030.Add(([&]() -> Value { auto fn31031 = PrepareDictionaryGet(s->LocalAt(4)); Arguments args31032; args31032.positional.reserve(2); args31032.Add(Value("market"), false); args31032.Add(List({}), false); return CallDictionaryGet(c, fn31031, std::move(args31032)); }()), false); return Call(c, fn31029, std::move(args31030)); }()); return Binary("Add", v31028, List({List({Value("HIRE")})})); }());
Put(s->LocalAt(4), Value("market"), v31027);
auto v31033 = s->Global("_V233_REPORT");
auto v31034 = Value("sheep_hire_requests");
auto v31035 = Get(v31033, v31034);
Put(v31033, v31034, Inplace("Sub", v31035, ([&]() -> Value { auto v31036 = ([&]() -> Value { auto fn31037 = s->Global("sum"); Arguments args31038; args31038.Add(([&]() -> Value { auto comp31039 = std::make_shared<Scope>(); comp31039->globals = s->globals; comp31039->parent = s; static constexpr const char* comp31039_names[] = {"o"}; comp31039->PrepareSlots(comp31039_names); auto result31040 = List(); for (const auto& item31041 : Iterate(s->LocalAt(1))) { comp31039->SetAt(0, item31041); result31040.node()->sequence.push_back(([&]() -> Value { auto v31042 = comp31039->LocalAt(0); Value v31043; v31043 = List({Value("HIRE")}); if (!static_cast<bool>(Binary("Eq", v31042, v31043))) return Value(false); v31042 = v31043; return Value(true); }())); } return result31040; }()), false); return Call(c, fn31037, std::move(args31038)); }()); return Binary("Sub", v31036, Value(int64_t{1})); }())));
auto v31044 = s->Global("_V233_REPORT");
auto v31045 = Value("sheep_feed_buy_requests");
auto v31046 = Get(v31044, v31045);
Put(v31044, v31045, Inplace("Sub", v31046, Value(int64_t{6})));
(void)([&]() -> Value { auto fn31047 = Attribute(s->LocalAt(5), "update"); Arguments args31048; args31048.Keyword("count", Value(int64_t{1})); args31048.Keyword("targets", ([&]() -> Value { auto fn31049 = s->Global("_sl_path"); Arguments args31050; args31050.positional.reserve(2); args31050.Add(Get(([&]() -> Value { auto fn31051 = s->Global("_r62_input_start"); Arguments args31052; args31052.positional.reserve(3); args31052.Add(s->LocalAt(3), false); args31052.Add(s->LocalAt(0), false); args31052.Add(Value(int64_t{0}), false); return Call(c, fn31051, std::move(args31052)); }()), Value(int64_t{1})), false); args31050.Add(s->LocalAt(8), false); return Call(c, fn31049, std::move(args31050)); }())); return Call(c, fn31047, std::move(args31048)); }());
auto v31053 = s->Global("_VT_REPORT");
auto v31054 = Value("vt_single_harvest_days");
auto v31055 = Get(v31053, v31054);
Put(v31053, v31054, Inplace("Add", v31055, Value(int64_t{1})));
return s->LocalAt(4);
return {};
}
}  // namespace kagg::opponents::compiled
