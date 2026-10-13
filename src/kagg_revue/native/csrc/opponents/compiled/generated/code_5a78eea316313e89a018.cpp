// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_5a78eea316313e89a018(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"a", "d", "day0", "farm", "hires_today", "native", "o", "obs", "prices", "route", "step", "t", "through_day", "total"};
s->PrepareSlots(s_names);
auto v25968 = ([&]() -> Value { auto fn25969 = s->Global("int"); Arguments args25970; args25970.Add(Get(s->LocalAt(7), Value("step")), false); return Call(c, fn25969, std::move(args25970)); }());
s->SetAt(10, v25968);
auto v25971 = Get(Get(s->LocalAt(7), Value("farms")), Get(s->LocalAt(7), Value("player")));
s->SetAt(3, v25971);
auto v25972 = Get(Get(s->LocalAt(7), Value("market")), Value("prices"));
s->SetAt(8, v25972);
auto v25973 = Value(int64_t{0});
s->SetAt(13, v25973);
auto v25974 = ([&]() -> Value { auto fn25975 = s->Global("int"); Arguments args25976; args25976.Add(Get(s->LocalAt(3), Value("hires_today")), false); return Call(c, fn25975, std::move(args25976)); }());
s->SetAt(4, v25974);
auto v25977 = ([&]() -> Value { auto v25978 = s->LocalAt(10); return Binary("FloorDiv", v25978, Value(int64_t{24})); }());
s->SetAt(2, v25977);
auto v25979 = Get(s->LocalAt(5), Value("route"));
s->SetAt(9, v25979);
for (const auto& item25980 : Iterate(([&]() -> Value { auto fn25981 = s->Global("range"); Arguments args25982; args25982.positional.reserve(2); args25982.Add(s->LocalAt(10), false); args25982.Add(([&]() -> Value { auto v25983 = ([&]() -> Value { auto v25984 = s->LocalAt(12); return Binary("Add", v25984, Value(int64_t{1})); }()); return Binary("Mult", v25983, Value(int64_t{24})); }()), false); return Call(c, fn25981, std::move(args25982)); }()))) {
s->SetAt(11, item25980);
auto v25985 = Get(Get(Attribute(Attribute(s->Global("_IMPL"), "chassis"), "routes"), (static_cast<bool>(([&]() -> Value { auto v25986 = s->LocalAt(11); Value v25987; v25987 = Value(int64_t{648}); if (!static_cast<bool>(Binary("GtE", v25986, v25987))) return Value(false); v25986 = v25987; return Value(true); }())) ? Value(int64_t{2}) : s->LocalAt(9))), s->LocalAt(11));
s->SetAt(0, v25985);
auto v25988 = ([&]() -> Value { auto v25989 = s->LocalAt(11); return Binary("FloorDiv", v25989, Value(int64_t{24})); }());
s->SetAt(1, v25988);
if (static_cast<bool>(([&]() -> Value { auto v25990 = ([&]() -> Value { auto v25991 = s->LocalAt(1); Value v25992; v25992 = s->LocalAt(2); if (!static_cast<bool>(Binary("NotEq", v25991, v25992))) return Value(false); v25991 = v25992; return Value(true); }()); if (!static_cast<bool>(v25990)) return v25990; v25990 = ([&]() -> Value { auto v25993 = ([&]() -> Value { auto v25995 = s->LocalAt(11); return Binary("Mod", v25995, Value(int64_t{24})); }()); Value v25994; v25994 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v25993, v25994))) return Value(false); v25993 = v25994; return Value(true); }()); return v25990; }()))) {
auto v25996 = Value(int64_t{0});
s->SetAt(4, v25996);
}
for (const auto& item25997 : Iterate(([&]() -> Value { auto v25998 = ([&]() -> Value { auto fn25999 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args26000; args26000.positional.reserve(2); args26000.Add(Value("market"), false); args26000.Add(List({}), false); return CallDictionaryGet(c, fn25999, std::move(args26000)); }()); if (static_cast<bool>(v25998)) return v25998; v25998 = List({}); return v25998; }()))) {
s->SetAt(6, item25997);
if (static_cast<bool>(Unary("Not", s->LocalAt(6)))) {
continue;
}
if (static_cast<bool>(([&]() -> Value { auto v26001 = Get(s->LocalAt(6), Value(int64_t{0})); Value v26002; v26002 = Value("BUY_SEED"); if (!static_cast<bool>(Binary("Eq", v26001, v26002))) return Value(false); v26001 = v26002; return Value(true); }()))) {
auto v26003 = s->LocalAt(13);
s->SetAt(13, Inplace("Add", v26003, ([&]() -> Value { auto v26004 = ([&]() -> Value { auto fn26005 = s->Global("int"); Arguments args26006; args26006.Add(Get(s->LocalAt(6), Value(int64_t{2})), false); return Call(c, fn26005, std::move(args26006)); }()); return Binary("Mult", v26004, ([&]() -> Value { auto fn26007 = PrepareDictionaryGet(s->Global("_E343_YX_SEED")); Arguments args26008; args26008.positional.reserve(2); args26008.Add(Get(s->LocalAt(6), Value(int64_t{1})), false); args26008.Add(Value(int64_t{50}), false); return CallDictionaryGet(c, fn26007, std::move(args26008)); }())); }())));
}
else {
if (static_cast<bool>(([&]() -> Value { auto v26009 = Get(s->LocalAt(6), Value(int64_t{0})); Value v26010; v26010 = Value("BUY_ANIMAL"); if (!static_cast<bool>(Binary("Eq", v26009, v26010))) return Value(false); v26009 = v26010; return Value(true); }()))) {
auto v26011 = s->LocalAt(13);
s->SetAt(13, Inplace("Add", v26011, ([&]() -> Value { auto v26012 = ([&]() -> Value { auto fn26013 = s->Global("int"); Arguments args26014; args26014.Add(Get(s->LocalAt(6), Value(int64_t{2})), false); return Call(c, fn26013, std::move(args26014)); }()); return Binary("Mult", v26012, ([&]() -> Value { auto fn26015 = PrepareDictionaryGet(s->Global("_E343_YX_ANIMAL")); Arguments args26016; args26016.positional.reserve(2); args26016.Add(Get(s->LocalAt(6), Value(int64_t{1})), false); args26016.Add(Value(int64_t{500}), false); return CallDictionaryGet(c, fn26015, std::move(args26016)); }())); }())));
}
else {
if (static_cast<bool>(([&]() -> Value { auto v26017 = Get(s->LocalAt(6), Value(int64_t{0})); Value v26018; v26018 = Value("BUY_PRODUCT"); if (!static_cast<bool>(Binary("Eq", v26017, v26018))) return Value(false); v26017 = v26018; return Value(true); }()))) {
auto v26019 = s->LocalAt(13);
s->SetAt(13, Inplace("Add", v26019, ([&]() -> Value { auto v26020 = ([&]() -> Value { auto fn26021 = s->Global("int"); Arguments args26022; args26022.Add(Get(s->LocalAt(6), Value(int64_t{2})), false); return Call(c, fn26021, std::move(args26022)); }()); return Binary("Mult", v26020, ([&]() -> Value { auto v26023 = ([&]() -> Value { auto fn26024 = s->Global("int"); Arguments args26025; args26025.Add(([&]() -> Value { auto fn26026 = PrepareDictionaryGet(s->LocalAt(8)); Arguments args26027; args26027.positional.reserve(2); args26027.Add(Get(s->LocalAt(6), Value(int64_t{1})), false); args26027.Add(Value(int64_t{50}), false); return CallDictionaryGet(c, fn26026, std::move(args26027)); }()), false); return Call(c, fn26024, std::move(args26025)); }()); return Binary("Add", v26023, Value(int64_t{10})); }())); }())));
}
else {
if (static_cast<bool>(([&]() -> Value { auto v26028 = Get(s->LocalAt(6), Value(int64_t{0})); Value v26029; v26029 = Value("BUY_LAND"); if (!static_cast<bool>(Binary("Eq", v26028, v26029))) return Value(false); v26028 = v26029; return Value(true); }()))) {
auto v26030 = s->LocalAt(13);
s->SetAt(13, Inplace("Add", v26030, Value(int64_t{4000})));
}
else {
if (static_cast<bool>(([&]() -> Value { auto v26031 = Get(s->LocalAt(6), Value(int64_t{0})); Value v26032; v26032 = Value("HIRE"); if (!static_cast<bool>(Binary("Eq", v26031, v26032))) return Value(false); v26031 = v26032; return Value(true); }()))) {
auto v26033 = s->LocalAt(13);
s->SetAt(13, Inplace("Add", v26033, ([&]() -> Value { auto fn26034 = s->Global("_v219_fib"); Arguments args26035; args26035.Add(s->LocalAt(4), false); return Call(c, fn26034, std::move(args26035)); }())));
auto v26036 = s->LocalAt(4);
s->SetAt(4, Inplace("Add", v26036, Value(int64_t{1})));
}
}
}
}
}
}
}
return s->LocalAt(13);
return {};
}
}  // namespace kagg::opponents::compiled
