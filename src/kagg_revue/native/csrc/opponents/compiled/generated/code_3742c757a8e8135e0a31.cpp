// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_3742c757a8e8135e0a31(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"age", "best_rescue", "cap", "crop", "day", "dec", "fert_until", "i", "lo", "mls", "myd", "now", "now_step", "op", "planted", "rescue_t", "t", "visits", "watered_day", "y", "y0"};
s->PrepareSlots(s_names);
auto v21884 = Get(s->Global("_CA_CROP"), s->LocalAt(3));
auto unpack21885 = Iterate(v21884);
ValidateUnpack(unpack21885, 2, false);
s->SetAt(10, unpack21885.at(0));
s->SetAt(2, unpack21885.at(1));
auto v21886 = ([&]() -> Value { auto v21887 = ([&]() -> Value { auto v21888 = s->LocalAt(10); return Binary("Add", v21888, Value(int64_t{1})); }()); return Binary("FloorDiv", v21887, Value(int64_t{2})); }());
s->SetAt(8, v21886);
auto v21889 = ([&]() -> Value { auto v21890 = ([&]() -> Value { auto v21891 = ([&]() -> Value { auto v21892 = s->LocalAt(14); return Binary("Add", v21892, s->LocalAt(10)); }()); return Binary("Add", v21891, Value(int64_t{1})); }()); return Binary("Mult", v21890, Value(int64_t{24})); }());
s->SetAt(9, v21889);
auto v21893 = s->LocalAt(20);
s->SetAt(19, v21893);
auto v21894 = Tuple({Value(int64_t{0}), Value{}});
auto unpack21895 = Iterate(v21894);
ValidateUnpack(unpack21895, 2, false);
s->SetAt(1, unpack21895.at(0));
s->SetAt(15, unpack21895.at(1));
for (const auto& item21896 : Iterate(s->LocalAt(17))) {
auto unpack21897 = Iterate(item21896);
ValidateUnpack(unpack21897, 3, false);
s->SetAt(16, unpack21897.at(0));
s->SetAt(7, unpack21897.at(1));
s->SetAt(13, unpack21897.at(2));
auto v21898 = ([&]() -> Value { auto v21899 = s->LocalAt(16); return Binary("FloorDiv", v21899, Value(int64_t{24})); }());
s->SetAt(4, v21898);
auto v21900 = ([&]() -> Value { auto v21901 = s->LocalAt(4); return Binary("Sub", v21901, s->LocalAt(14)); }());
s->SetAt(0, v21900);
auto v21902 = ([&]() -> Value { auto fn21903 = s->Global("_ca_decays"); Arguments args21904; args21904.positional.reserve(3); args21904.Add(s->LocalAt(9), false); args21904.Add(s->LocalAt(12), false); args21904.Add(s->LocalAt(16), false); return Call(c, fn21903, std::move(args21904)); }());
s->SetAt(5, v21902);
auto v21905 = ([&]() -> Value { auto v21906 = s->LocalAt(19); return Binary("Sub", v21906, s->LocalAt(5)); }());
s->SetAt(11, v21905);
if (static_cast<bool>(([&]() -> Value { auto v21907 = ([&]() -> Value { auto v21908 = s->LocalAt(11); Value v21909; v21909 = Value(int64_t{0}); if (!static_cast<bool>(Binary("LtE", v21908, v21909))) return Value(false); v21908 = v21909; return Value(true); }()); if (!static_cast<bool>(v21907)) return v21907; v21907 = ([&]() -> Value { auto v21910 = s->LocalAt(16); Value v21911; v21911 = s->LocalAt(9); if (!static_cast<bool>(Binary("Gt", v21910, v21911))) return Value(false); v21910 = v21911; return Value(true); }()); return v21907; }()))) {
return Tuple({Value(int64_t{0}), s->LocalAt(1), s->LocalAt(15)});
}
if (static_cast<bool>(([&]() -> Value { auto v21912 = s->LocalAt(13); Value v21913; v21913 = Value("HARVEST"); if (!static_cast<bool>(Binary("Eq", v21912, v21913))) return Value(false); v21912 = v21913; return Value(true); }()))) {
return Tuple({(static_cast<bool>(([&]() -> Value { auto v21914 = s->LocalAt(0); Value v21915; v21915 = Value(int64_t{2}); if (!static_cast<bool>(Binary("GtE", v21914, v21915))) return Value(false); v21914 = v21915; return Value(true); }())) ? ([&]() -> Value { auto fn21916 = s->Global("max"); Arguments args21917; args21917.positional.reserve(2); args21917.Add(Value(int64_t{0}), false); args21917.Add(s->LocalAt(11), false); return Call(c, fn21916, std::move(args21917)); }()) : Value(int64_t{0})), s->LocalAt(1), s->LocalAt(15)});
}
if (static_cast<bool>(([&]() -> Value { auto v21918 = s->LocalAt(13); Value v21919; v21919 = Tuple({Value("PLANT"), Value("DIG"), Value("BUILD_COOP"), Value("BUILD_PASTURE")}); if (!static_cast<bool>(Binary("In", v21918, v21919))) return Value(false); v21918 = v21919; return Value(true); }()))) {
return Tuple({Value(int64_t{0}), s->LocalAt(1), s->LocalAt(15)});
}
if (static_cast<bool>(([&]() -> Value { auto v21920 = ([&]() -> Value { auto v21921 = s->LocalAt(0); Value v21922; v21922 = Value(int64_t{2}); if (!static_cast<bool>(Binary("GtE", v21921, v21922))) return Value(false); v21921 = v21922; return Value(true); }()); if (!static_cast<bool>(v21920)) return v21920; v21920 = ([&]() -> Value { auto v21923 = s->LocalAt(11); Value v21924; v21924 = s->LocalAt(1); if (!static_cast<bool>(Binary("Gt", v21923, v21924))) return Value(false); v21923 = v21924; return Value(true); }()); if (!static_cast<bool>(v21920)) return v21920; v21920 = ([&]() -> Value { auto v21925 = s->LocalAt(16); Value v21926; v21926 = s->LocalAt(12); if (!static_cast<bool>(Binary("Gt", v21925, v21926))) return Value(false); v21925 = v21926; return Value(true); }()); return v21920; }()))) {
auto v21927 = Tuple({s->LocalAt(11), s->LocalAt(16)});
auto unpack21928 = Iterate(v21927);
ValidateUnpack(unpack21928, 2, false);
s->SetAt(1, unpack21928.at(0));
s->SetAt(15, unpack21928.at(1));
}
if (static_cast<bool>(([&]() -> Value { auto v21929 = ([&]() -> Value { auto v21930 = s->LocalAt(13); Value v21931; v21931 = Value("WATER"); if (!static_cast<bool>(Binary("Eq", v21930, v21931))) return Value(false); v21930 = v21931; return Value(true); }()); if (!static_cast<bool>(v21929)) return v21929; v21929 = ([&]() -> Value { auto v21932 = s->LocalAt(8); Value v21933; v21933 = s->LocalAt(0); if (!static_cast<bool>(Binary("LtE", v21932, v21933))) return Value(false); v21932 = v21933; v21933 = s->LocalAt(10); if (!static_cast<bool>(Binary("LtE", v21932, v21933))) return Value(false); v21932 = v21933; return Value(true); }()); if (!static_cast<bool>(v21929)) return v21929; v21929 = ([&]() -> Value { auto v21934 = s->LocalAt(4); Value v21935; v21935 = s->LocalAt(18); if (!static_cast<bool>(Binary("NotEq", v21934, v21935))) return Value(false); v21934 = v21935; return Value(true); }()); return v21929; }()))) {
auto v21936 = s->LocalAt(4);
s->SetAt(18, v21936);
auto v21937 = ([&]() -> Value { auto fn21938 = s->Global("min"); Arguments args21939; args21939.positional.reserve(2); args21939.Add(s->LocalAt(2), false); args21939.Add(([&]() -> Value { auto v21940 = s->LocalAt(19); return Binary("Add", v21940, (static_cast<bool>(([&]() -> Value { auto v21941 = s->LocalAt(6); Value v21942; v21942 = s->LocalAt(4); if (!static_cast<bool>(Binary("GtE", v21941, v21942))) return Value(false); v21941 = v21942; return Value(true); }())) ? Value(int64_t{2}) : Value(int64_t{1}))); }()), false); return Call(c, fn21938, std::move(args21939)); }());
s->SetAt(19, v21937);
}
}
return Tuple({Value(int64_t{0}), s->LocalAt(1), s->LocalAt(15)});
return {};
}
}  // namespace kagg::opponents::compiled
