// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_cd6bf92dbd8a4cfb947a(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "configuration", "k", "observation", "standard"};
s->PrepareSlots(s_names);
if (static_cast<bool>(([&]() -> Value { auto v25906 = ([&]() -> Value { auto fn25908 = s->Global("int"); Arguments args25909; args25909.Add(([&]() -> Value { auto fn25910 = PrepareDictionaryGet(s->LocalAt(3)); Arguments args25911; args25911.positional.reserve(2); args25911.Add(Value("step"), false); args25911.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn25910, std::move(args25911)); }()), false); return Call(c, fn25908, std::move(args25909)); }()); Value v25907; v25907 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v25906, v25907))) return Value(false); v25906 = v25907; return Value(true); }()))) {
for (const auto& item25912 : Iterate(s->Global("_E343_WL_REPORT"))) {
s->SetAt(2, item25912);
auto v25913 = Value(int64_t{0});
Put(s->Global("_E343_WL_REPORT"), s->LocalAt(2), v25913);
}
(void)([&]() -> Value { auto fn25914 = Attribute(s->Global("_E343_WL_STATE"), "clear"); Arguments args25915; return Call(c, fn25914, std::move(args25915)); }());
}
auto v25916 = ([&]() -> Value { auto fn25917 = s->Global("_E343_WL_BASE"); Arguments args25918; args25918.positional.reserve(2); args25918.Add(s->LocalAt(3), false); args25918.Add(s->LocalAt(1), false); return Call(c, fn25917, std::move(args25918)); }());
s->SetAt(0, v25916);
try {
auto v25920 = ([&]() -> Value { auto v25921 = ([&]() -> Value { auto v25922 = s->LocalAt(1); Value v25923; v25923 = Value{}; if (!static_cast<bool>(Binary("Is", v25922, v25923))) return Value(false); v25922 = v25923; return Value(true); }()); if (static_cast<bool>(v25921)) return v25921; v25921 = ([&]() -> Value { auto comp25924 = std::make_shared<Scope>(); comp25924->globals = s->globals; comp25924->parent = s; static constexpr const char* comp25924_names[] = {"k", "v"}; comp25924->PrepareSlots(comp25924_names); auto result25925 = List(); for (const auto& item25926 : Iterate(List({Tuple({Value("boardSize"), Value(int64_t{10})}), Tuple({Value("turnsPerDay"), Value(int64_t{24})}), Tuple({Value("shedCapacity"), Value(int64_t{100})}), Tuple({Value("maxMarketOrdersPerTurn"), Value(int64_t{10})})}))) { auto unpack25927 = Iterate(item25926); ValidateUnpack(unpack25927, 2, false); comp25924->SetAt(0, unpack25927.at(0)); comp25924->SetAt(1, unpack25927.at(1)); if (!static_cast<bool>(([&]() -> Value { auto v25928 = ([&]() -> Value { auto fn25930 = PrepareDictionaryGet(comp25924->Captured("configuration")); Arguments args25931; args25931.positional.reserve(2); args25931.Add(comp25924->LocalAt(0), false); args25931.Add(comp25924->LocalAt(1), false); return CallDictionaryGet(c, fn25930, std::move(args25931)); }()); Value v25929; v25929 = comp25924->LocalAt(1); if (!static_cast<bool>(Binary("Eq", v25928, v25929))) return Value(false); v25928 = v25929; return Value(true); }()))) return Value(false); } return Value(true); }()); return v25921; }());
s->SetAt(4, v25920);
if (static_cast<bool>(s->LocalAt(4))) {
auto v25932 = ([&]() -> Value { auto fn25933 = s->Global("_e343_weedlag"); Arguments args25934; args25934.positional.reserve(2); args25934.Add(s->LocalAt(3), false); args25934.Add(s->LocalAt(0), false); return Call(c, fn25933, std::move(args25934)); }());
s->SetAt(0, v25932);
}
} catch (const Error& error25919) {
if (Matches(error25919, s->Global("Exception"))) {
auto v25935 = s->Global("_E343_WL_REPORT");
auto v25936 = Value("errors");
auto v25937 = Get(v25935, v25936);
Put(v25935, v25936, Inplace("Add", v25937, Value(int64_t{1})));
}
else { throw; }
}
return s->LocalAt(0);
return {};
}
}  // namespace kagg::opponents::compiled
