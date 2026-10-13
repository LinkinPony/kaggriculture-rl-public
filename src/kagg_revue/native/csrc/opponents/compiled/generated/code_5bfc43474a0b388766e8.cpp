// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_5bfc43474a0b388766e8(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "configuration", "fall", "like", "observation", "prior", "step"};
s->PrepareSlots(s_names);
auto v27869 = ([&]() -> Value { auto fn27870 = s->Global("int"); Arguments args27871; args27871.Add(Get(s->LocalAt(4), Value("step")), false); return Call(c, fn27870, std::move(args27871)); }());
s->SetAt(6, v27869);
if (static_cast<bool>(([&]() -> Value { auto v27872 = s->LocalAt(6); Value v27873; v27873 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v27872, v27873))) return Value(false); v27872 = v27873; return Value(true); }()))) {
(void)([&]() -> Value { auto fn27874 = Attribute(s->Global("_E363_STATE"), "update"); Arguments args27875; args27875.Keyword("prior", Value{}); args27875.Keyword("our_attack", Value(false)); args27875.Keyword("mirror_like", Value(true)); return Call(c, fn27874, std::move(args27875)); }());
(void)([&]() -> Value { auto fn27876 = Attribute(s->Global("_E363_REPORT"), "update"); Arguments args27877; args27877.Keyword("classified", Value(int64_t{0})); args27877.Keyword("mirror_like", Value(int64_t{0})); args27877.Keyword("market_drop", Value(int64_t{0})); args27877.Keyword("errors", Value(int64_t{0})); return Call(c, fn27876, std::move(args27877)); }());
}
if (static_cast<bool>(([&]() -> Value { auto v27878 = s->LocalAt(6); Value v27879; v27879 = Value(int64_t{2}); if (!static_cast<bool>(Binary("Eq", v27878, v27879))) return Value(false); v27878 = v27879; return Value(true); }()))) {
try {
auto v27881 = Get(s->Global("_E363_STATE"), Value("prior"));
s->SetAt(5, v27881);
if (static_cast<bool>(([&]() -> Value { auto v27882 = ([&]() -> Value { auto v27883 = s->LocalAt(5); Value v27884; v27884 = Value{}; if (!static_cast<bool>(Binary("IsNot", v27883, v27884))) return Value(false); v27883 = v27884; return Value(true); }()); if (!static_cast<bool>(v27882)) return v27882; v27882 = Get(s->Global("_E363_STATE"), Value("our_attack")); return v27882; }()))) {
auto v27885 = ([&]() -> Value { auto v27886 = s->LocalAt(5); return Binary("Sub", v27886, ([&]() -> Value { auto fn27887 = s->Global("int"); Arguments args27888; args27888.Add(Get(Get(Get(s->LocalAt(4), Value("market")), Value("inventory")), Value("WHEAT")), false); return Call(c, fn27887, std::move(args27888)); }())); }());
s->SetAt(2, v27885);
auto v27889 = ([&]() -> Value { auto v27890 = s->LocalAt(2); Value v27891; v27891 = Value(int64_t{45}); if (!static_cast<bool>(Binary("GtE", v27890, v27891))) return Value(false); v27890 = v27891; return Value(true); }());
s->SetAt(3, v27889);
auto v27892 = s->LocalAt(3);
Put(s->Global("_E363_STATE"), Value("mirror_like"), v27892);
(void)([&]() -> Value { auto fn27893 = Attribute(s->Global("_E363_REPORT"), "update"); Arguments args27894; args27894.Keyword("classified", Value(int64_t{1})); args27894.Keyword("mirror_like", ([&]() -> Value { auto fn27895 = s->Global("int"); Arguments args27896; args27896.Add(s->LocalAt(3), false); return Call(c, fn27895, std::move(args27896)); }())); args27894.Keyword("market_drop", s->LocalAt(2)); return Call(c, fn27893, std::move(args27894)); }());
}
} catch (const Error& error27880) {
if (Matches(error27880, s->Global("Exception"))) {
auto v27897 = s->Global("_E363_REPORT");
auto v27898 = Value("errors");
auto v27899 = Get(v27897, v27898);
Put(v27897, v27898, Inplace("Add", v27899, Value(int64_t{1})));
}
else { throw; }
}
}
auto v27900 = ([&]() -> Value { auto fn27901 = s->Global("_E363_PARENT"); Arguments args27902; args27902.positional.reserve(2); args27902.Add(s->LocalAt(4), false); args27902.Add(s->LocalAt(1), false); return Call(c, fn27901, std::move(args27902)); }());
s->SetAt(0, v27900);
if (static_cast<bool>(([&]() -> Value { auto v27903 = s->LocalAt(6); Value v27904; v27904 = Value(int64_t{1}); if (!static_cast<bool>(Binary("Eq", v27903, v27904))) return Value(false); v27903 = v27904; return Value(true); }()))) {
try {
auto v27906 = ([&]() -> Value { auto fn27907 = s->Global("int"); Arguments args27908; args27908.Add(Get(Get(Get(s->LocalAt(4), Value("market")), Value("inventory")), Value("WHEAT")), false); return Call(c, fn27907, std::move(args27908)); }());
Put(s->Global("_E363_STATE"), Value("prior"), v27906);
auto v27909 = ([&]() -> Value { auto comp27910 = std::make_shared<Scope>(); comp27910->globals = s->globals; comp27910->parent = s; static constexpr const char* comp27910_names[] = {"o"}; comp27910->PrepareSlots(comp27910_names); auto result27911 = List(); for (const auto& item27912 : Iterate(([&]() -> Value { auto fn27913 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args27914; args27914.positional.reserve(2); args27914.Add(Value("market"), false); args27914.Add(List({}), false); return CallDictionaryGet(c, fn27913, std::move(args27914)); }()))) { comp27910->SetAt(0, item27912); if (static_cast<bool>(([&]() -> Value { auto v27915 = ([&]() -> Value { auto v27916 = ([&]() -> Value { auto fn27918 = comp27910->Global("len"); Arguments args27919; args27919.Add(comp27910->LocalAt(0), false); return Call(c, fn27918, std::move(args27919)); }()); Value v27917; v27917 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v27916, v27917))) return Value(false); v27916 = v27917; return Value(true); }()); if (!static_cast<bool>(v27915)) return v27915; v27915 = ([&]() -> Value { auto v27920 = Slice(comp27910->LocalAt(0), Value{}, Value(int64_t{2}), Value{}); Value v27921; v27921 = List({Value("BUY_PRODUCT"), Value("WHEAT")}); if (!static_cast<bool>(Binary("Eq", v27920, v27921))) return Value(false); v27920 = v27921; return Value(true); }()); if (!static_cast<bool>(v27915)) return v27915; v27915 = ([&]() -> Value { auto v27922 = ([&]() -> Value { auto fn27924 = comp27910->Global("int"); Arguments args27925; args27925.Add(Get(comp27910->LocalAt(0), Value(int64_t{2})), false); return Call(c, fn27924, std::move(args27925)); }()); Value v27923; v27923 = Value(int64_t{30}); if (!static_cast<bool>(Binary("GtE", v27922, v27923))) return Value(false); v27922 = v27923; return Value(true); }()); return v27915; }()))) return Value(true); } return Value(false); }());
Put(s->Global("_E363_STATE"), Value("our_attack"), v27909);
} catch (const Error& error27905) {
if (Matches(error27905, s->Global("Exception"))) {
auto v27926 = s->Global("_E363_REPORT");
auto v27927 = Value("errors");
auto v27928 = Get(v27926, v27927);
Put(v27926, v27927, Inplace("Add", v27928, Value(int64_t{1})));
}
else { throw; }
}
}
return s->LocalAt(0);
return {};
}
}  // namespace kagg::opponents::compiled
