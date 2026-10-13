// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_46d03865802e0c74c70c(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "configuration", "observation", "player", "st", "step"};
s->PrepareSlots(s_names);
auto v20868 = Tuple({([&]() -> Value { auto fn20869 = s->Global("int"); Arguments args20870; args20870.Add(Get(s->LocalAt(2), Value("player")), false); return Call(c, fn20869, std::move(args20870)); }()), ([&]() -> Value { auto fn20871 = s->Global("int"); Arguments args20872; args20872.Add(Get(s->LocalAt(2), Value("step")), false); return Call(c, fn20871, std::move(args20872)); }())});
auto unpack20873 = Iterate(v20868);
ValidateUnpack(unpack20873, 2, false);
s->SetAt(3, unpack20873.at(0));
s->SetAt(5, unpack20873.at(1));
auto v20874 = ([&]() -> Value { auto fn20875 = PrepareDictionaryGet(s->Global("_V9_COURIER")); Arguments args20876; args20876.Add(s->LocalAt(3), false); return CallDictionaryGet(c, fn20875, std::move(args20876)); }());
s->SetAt(4, v20874);
if (static_cast<bool>(([&]() -> Value { auto v20877 = ([&]() -> Value { auto v20878 = s->LocalAt(4); Value v20879; v20879 = Value{}; if (!static_cast<bool>(Binary("Is", v20878, v20879))) return Value(false); v20878 = v20879; return Value(true); }()); if (static_cast<bool>(v20877)) return v20877; v20877 = ([&]() -> Value { auto v20880 = s->LocalAt(5); Value v20881; v20881 = Get(s->LocalAt(4), Value("step")); if (!static_cast<bool>(Binary("LtE", v20880, v20881))) return Value(false); v20880 = v20881; return Value(true); }()); return v20877; }()))) {
auto v20882 = ([&]() -> Value { auto dict20883 = Dict(); auto key20884 = Value("step"); Put(dict20883, key20884, Unary("USub", Value(int64_t{1}))); return dict20883; }());
s->SetAt(4, v20882);
Put(s->Global("_V9_COURIER"), s->LocalAt(3), v20882);
if (static_cast<bool>(([&]() -> Value { auto v20885 = s->LocalAt(5); Value v20886; v20886 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v20885, v20886))) return Value(false); v20885 = v20886; return Value(true); }()))) {
(void)([&]() -> Value { auto fn20887 = Attribute(s->Global("_V9_COURIER_REPORT"), "update"); Arguments args20888; args20888.Keyword("courier_trips", Value(int64_t{0})); args20888.Keyword("courier_units", Value(int64_t{0})); args20888.Keyword("courier_errors", Value(int64_t{0})); return Call(c, fn20887, std::move(args20888)); }());
}
}
auto v20889 = s->LocalAt(5);
Put(s->LocalAt(4), Value("step"), v20889);
auto v20890 = ([&]() -> Value { auto fn20891 = s->Global("_V9_COURIER_PARENT"); Arguments args20892; args20892.positional.reserve(2); args20892.Add(s->LocalAt(2), false); args20892.Add(s->LocalAt(1), false); return Call(c, fn20891, std::move(args20892)); }());
s->SetAt(0, v20890);
try {
return ([&]() -> Value { auto fn20894 = s->Global("_v9_courier"); Arguments args20895; args20895.positional.reserve(3); args20895.Add(s->LocalAt(2), false); args20895.Add(s->LocalAt(0), false); args20895.Add(s->LocalAt(4), false); return Call(c, fn20894, std::move(args20895)); }());
} catch (const Error& error20893) {
if (Matches(error20893, s->Global("Exception"))) {
auto v20896 = s->Global("_V9_COURIER_REPORT");
auto v20897 = Value("courier_errors");
auto v20898 = Get(v20896, v20897);
Put(v20896, v20897, Inplace("Add", v20898, Value(int64_t{1})));
return s->LocalAt(0);
}
else { throw; }
}
return {};
}
}  // namespace kagg::opponents::compiled
