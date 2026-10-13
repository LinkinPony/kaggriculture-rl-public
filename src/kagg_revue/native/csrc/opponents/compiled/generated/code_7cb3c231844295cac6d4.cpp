// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_7cb3c231844295cac6d4(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "day", "farm", "native", "obs", "safe", "state", "tile", "tomatoes", "x", "y"};
s->PrepareSlots(s_names);
try {
auto v27132 = ([&]() -> Value { auto v27133 = ([&]() -> Value { auto fn27134 = s->Global("int"); Arguments args27135; args27135.Add(Get(s->LocalAt(4), Value("step")), false); return Call(c, fn27134, std::move(args27135)); }()); return Binary("FloorDiv", v27133, Value(int64_t{24})); }());
s->SetAt(1, v27132);
if (static_cast<bool>(([&]() -> Value { auto v27136 = ([&]() -> Value { auto v27137 = s->LocalAt(1); Value v27138; v27138 = s->Global("V13V_SKIP_DAYS"); if (!static_cast<bool>(Binary("In", v27137, v27138))) return Value(false); v27137 = v27138; return Value(true); }()); if (!static_cast<bool>(v27136)) return v27136; v27136 = ([&]() -> Value { auto fn27139 = PrepareDictionaryGet(s->LocalAt(6)); Arguments args27140; args27140.Add(Value("committed"), false); return CallDictionaryGet(c, fn27139, std::move(args27140)); }()); if (!static_cast<bool>(v27136)) return v27136; v27136 = ([&]() -> Value { auto v27141 = ([&]() -> Value { auto fn27143 = PrepareDictionaryGet(s->LocalAt(6)); Arguments args27144; args27144.Add(Value("requested_day"), false); return CallDictionaryGet(c, fn27143, std::move(args27144)); }()); Value v27142; v27142 = s->LocalAt(1); if (!static_cast<bool>(Binary("NotEq", v27141, v27142))) return Value(false); v27141 = v27142; return Value(true); }()); return v27136; }()))) {
auto v27145 = Get(Get(s->LocalAt(4), Value("farms")), ([&]() -> Value { auto fn27146 = s->Global("int"); Arguments args27147; args27147.Add(Get(s->LocalAt(4), Value("player")), false); return Call(c, fn27146, std::move(args27147)); }()));
s->SetAt(2, v27145);
auto v27148 = Value(int64_t{0});
s->SetAt(8, v27148);
auto v27149 = Value(true);
s->SetAt(5, v27149);
for (const auto& item27150 : Iterate(([&]() -> Value { auto fn27151 = PrepareDictionaryGet(s->LocalAt(6)); Arguments args27152; args27152.positional.reserve(2); args27152.Add(Value("targets"), false); args27152.Add(List({}), false); return CallDictionaryGet(c, fn27151, std::move(args27152)); }()))) {
auto unpack27153 = Iterate(item27150);
ValidateUnpack(unpack27153, 2, false);
s->SetAt(9, unpack27153.at(0));
s->SetAt(10, unpack27153.at(1));
auto v27154 = Get(Get(Get(s->LocalAt(2), Value("tiles")), s->LocalAt(10)), s->LocalAt(9));
s->SetAt(7, v27154);
if (static_cast<bool>(([&]() -> Value { auto v27155 = ([&]() -> Value { auto fn27156 = s->Global("isinstance"); Arguments args27157; args27157.positional.reserve(2); args27157.Add(s->LocalAt(7), false); args27157.Add(s->Global("dict"), false); return Call(c, fn27156, std::move(args27157)); }()); if (!static_cast<bool>(v27155)) return v27155; v27155 = ([&]() -> Value { auto v27158 = ([&]() -> Value { auto fn27160 = PrepareDictionaryGet(s->LocalAt(7)); Arguments args27161; args27161.Add(Value("crop"), false); return CallDictionaryGet(c, fn27160, std::move(args27161)); }()); Value v27159; v27159 = Value("TOMATO"); if (!static_cast<bool>(Binary("Eq", v27158, v27159))) return Value(false); v27158 = v27159; return Value(true); }()); return v27155; }()))) {
auto v27162 = s->LocalAt(8);
s->SetAt(8, Inplace("Add", v27162, Value(int64_t{1})));
if (static_cast<bool>(([&]() -> Value { auto v27163 = ([&]() -> Value { auto fn27165 = s->Global("int"); Arguments args27166; args27166.Add(([&]() -> Value { auto fn27167 = PrepareDictionaryGet(s->LocalAt(7)); Arguments args27168; args27168.positional.reserve(2); args27168.Add(Value("consecutive_unwatered"), false); args27168.Add(Value(int64_t{1}), false); return CallDictionaryGet(c, fn27167, std::move(args27168)); }()), false); return Call(c, fn27165, std::move(args27166)); }()); Value v27164; v27164 = Value(int64_t{0}); if (!static_cast<bool>(Binary("NotEq", v27163, v27164))) return Value(false); v27163 = v27164; return Value(true); }()))) {
auto v27169 = Value(false);
s->SetAt(5, v27169);
}
}
}
if (static_cast<bool>(([&]() -> Value { auto v27170 = s->LocalAt(8); if (!static_cast<bool>(v27170)) return v27170; v27170 = s->LocalAt(5); return v27170; }()))) {
auto v27171 = s->LocalAt(1);
Put(s->LocalAt(6), Value("requested_day"), v27171);
auto v27172 = s->Global("_V13V_REPORT");
auto v27173 = Value("v_skipped");
auto v27174 = Get(v27172, v27173);
Put(v27172, v27173, Inplace("Add", v27174, Value(int64_t{1})));
return s->LocalAt(0);
}
if (static_cast<bool>(s->LocalAt(8))) {
auto v27175 = s->Global("_V13V_REPORT");
auto v27176 = Value("v_blocked");
auto v27177 = Get(v27175, v27176);
Put(v27175, v27176, Inplace("Add", v27177, Value(int64_t{1})));
}
}
} catch (const Error& error27131) {
if (Matches(error27131, s->Global("Exception"))) {
auto v27178 = s->Global("_V13V_REPORT");
auto v27179 = Value("v_errors");
auto v27180 = Get(v27178, v27179);
Put(v27178, v27179, Inplace("Add", v27180, Value(int64_t{1})));
}
else { throw; }
}
return ([&]() -> Value { auto fn27181 = s->Global("_V13V_ORIG_REQUEST"); Arguments args27182; args27182.positional.reserve(4); args27182.Add(s->LocalAt(4), false); args27182.Add(s->LocalAt(0), false); args27182.Add(s->LocalAt(6), false); args27182.Add(s->LocalAt(3), false); return Call(c, fn27181, std::move(args27182)); }());
return {};
}
}  // namespace kagg::opponents::compiled
