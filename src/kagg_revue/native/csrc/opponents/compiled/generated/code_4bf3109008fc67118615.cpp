// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_4bf3109008fc67118615(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "kept", "order", "remaining", "removed", "sell_state", "step"};
s->PrepareSlots(s_names);
if (static_cast<bool>(([&]() -> Value { auto v890 = ([&]() -> Value { auto fn892 = PrepareDictionaryGet(s->LocalAt(5)); Arguments args893; args893.Add(Value("due_step"), false); return CallDictionaryGet(c, fn892, std::move(args893)); }()); Value v891; v891 = s->LocalAt(6); if (!static_cast<bool>(Binary("NotEq", v890, v891))) return Value(false); v890 = v891; return Value(true); }()))) {
return Value{};
}
auto v894 = ([&]() -> Value { auto fn895 = s->Global("dict"); Arguments args896; args896.Add(([&]() -> Value { auto fn897 = PrepareDictionaryGet(s->LocalAt(5)); Arguments args898; args898.positional.reserve(2); args898.Add(Value("suppress"), false); args898.Add(([&]() -> Value { auto dict899 = Dict(); return dict899; }()), false); return CallDictionaryGet(c, fn897, std::move(args898)); }()), false); return Call(c, fn895, std::move(args896)); }());
s->SetAt(3, v894);
auto v900 = List({});
s->SetAt(1, v900);
for (const auto& item901 : Iterate(([&]() -> Value { auto v902 = ([&]() -> Value { auto fn903 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args904; args904.Add(Value("market"), false); return CallDictionaryGet(c, fn903, std::move(args904)); }()); if (static_cast<bool>(v902)) return v902; v902 = List({}); return v902; }()))) {
s->SetAt(2, item901);
auto v905 = ([&]() -> Value { auto fn906 = s->Global("list"); Arguments args907; args907.Add(s->LocalAt(2), false); return Call(c, fn906, std::move(args907)); }());
s->SetAt(2, v905);
if (static_cast<bool>(([&]() -> Value { auto v908 = s->LocalAt(2); if (!static_cast<bool>(v908)) return v908; v908 = ([&]() -> Value { auto v909 = Get(s->LocalAt(2), Value(int64_t{0})); Value v910; v910 = Value("SELL"); if (!static_cast<bool>(Binary("Eq", v909, v910))) return Value(false); v909 = v910; return Value(true); }()); if (!static_cast<bool>(v908)) return v908; v908 = ([&]() -> Value { auto v911 = ([&]() -> Value { auto fn913 = s->Global("len"); Arguments args914; args914.Add(s->LocalAt(2), false); return Call(c, fn913, std::move(args914)); }()); Value v912; v912 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v911, v912))) return Value(false); v911 = v912; return Value(true); }()); if (!static_cast<bool>(v908)) return v908; v908 = ([&]() -> Value { auto v915 = ([&]() -> Value { auto fn917 = PrepareDictionaryGet(s->LocalAt(3)); Arguments args918; args918.positional.reserve(2); args918.Add(Get(s->LocalAt(2), Value(int64_t{1})), false); args918.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn917, std::move(args918)); }()); Value v916; v916 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v915, v916))) return Value(false); v915 = v916; return Value(true); }()); return v908; }()))) {
auto v919 = ([&]() -> Value { auto fn920 = s->Global("min"); Arguments args921; args921.positional.reserve(2); args921.Add(([&]() -> Value { auto fn922 = s->Global("max"); Arguments args923; args923.positional.reserve(2); args923.Add(Value(int64_t{0}), false); args923.Add(([&]() -> Value { auto fn924 = s->Global("_int"); Arguments args925; args925.Add(Get(s->LocalAt(2), Value(int64_t{2})), false); return Call(c, fn924, std::move(args925)); }()), false); return Call(c, fn922, std::move(args923)); }()), false); args921.Add(Get(s->LocalAt(3), Get(s->LocalAt(2), Value(int64_t{1}))), false); return Call(c, fn920, std::move(args921)); }());
s->SetAt(4, v919);
auto v926 = ([&]() -> Value { auto v927 = ([&]() -> Value { auto fn928 = s->Global("_int"); Arguments args929; args929.Add(Get(s->LocalAt(2), Value(int64_t{2})), false); return Call(c, fn928, std::move(args929)); }()); return Binary("Sub", v927, s->LocalAt(4)); }());
Put(s->LocalAt(2), Value(int64_t{2}), v926);
auto v930 = s->LocalAt(3);
auto v931 = Get(s->LocalAt(2), Value(int64_t{1}));
auto v932 = Get(v930, v931);
Put(v930, v931, Inplace("Sub", v932, s->LocalAt(4)));
}
(void)([&]() -> Value { auto fn933 = Attribute(s->LocalAt(1), "append"); Arguments args934; args934.Add(s->LocalAt(2), false); return Call(c, fn933, std::move(args934)); }());
}
auto v935 = s->LocalAt(1);
Put(s->LocalAt(0), Value("market"), v935);
return {};
}
}  // namespace kagg::opponents::compiled
