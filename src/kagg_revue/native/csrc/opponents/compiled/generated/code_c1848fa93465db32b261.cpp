// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_c1848fa93465db32b261(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "configuration", "i", "observation", "pos", "projected", "units", "view"};
s->PrepareSlots(s_names);
auto v1958 = ([&]() -> Value { auto fn1959 = s->Global("_SHOP_PARENT"); Arguments args1960; args1960.positional.reserve(2); args1960.Add(s->LocalAt(3), false); args1960.Add(s->LocalAt(1), false); return Call(c, fn1959, std::move(args1960)); }());
s->SetAt(0, v1958);
try {
if (static_cast<bool>(([&]() -> Value { auto v1962 = ([&]() -> Value { auto fn1964 = s->Global("_step_of"); Arguments args1965; args1965.Add(s->LocalAt(3), false); return Call(c, fn1964, std::move(args1965)); }()); Value v1963; v1963 = Value(int64_t{718}); if (!static_cast<bool>(Binary("GtE", v1962, v1963))) return Value(false); v1962 = v1963; return Value(true); }()))) {
auto v1966 = ([&]() -> Value { auto fn1967 = s->Global("_View"); Arguments args1968; args1968.positional.reserve(3); args1968.Add(s->LocalAt(3), false); args1968.Add(([&]() -> Value { auto fn1969 = s->Global("_int"); Arguments args1970; args1970.Add(([&]() -> Value { auto fn1971 = s->Global("_get"); Arguments args1972; args1972.positional.reserve(3); args1972.Add(s->LocalAt(3), false); args1972.Add(Value("player"), false); args1972.Add(Value(int64_t{0}), false); return Call(c, fn1971, std::move(args1972)); }()), false); return Call(c, fn1969, std::move(args1970)); }()), false); args1968.Add(Attribute(Attribute(s->Global("_IMPL"), "chassis"), "cfg"), false); return Call(c, fn1967, std::move(args1968)); }());
s->SetAt(7, v1966);
auto v1973 = List({});
s->SetAt(6, v1973);
for (const auto& item1974 : Iterate(([&]() -> Value { auto fn1975 = s->Global("enumerate"); Arguments args1976; args1976.Add(Attribute(s->LocalAt(7), "positions"), false); return Call(c, fn1975, std::move(args1976)); }()))) {
auto unpack1977 = Iterate(item1974);
ValidateUnpack(unpack1977, 2, false);
s->SetAt(2, unpack1977.at(0));
s->SetAt(4, unpack1977.at(1));
(void)([&]() -> Value { auto fn1978 = Attribute(s->LocalAt(6), "append"); Arguments args1979; args1979.Add((static_cast<bool>(([&]() -> Value { auto v1980 = ([&]() -> Value { auto fn1981 = s->Global("_shed_adjacent"); Arguments args1982; args1982.positional.reserve(2); args1982.Add(s->LocalAt(4), false); args1982.Add(Attribute(s->LocalAt(7), "board"), false); return Call(c, fn1981, std::move(args1982)); }()); if (!static_cast<bool>(v1980)) return v1980; v1980 = ([&]() -> Value { auto fn1983 = Attribute(s->LocalAt(7), "inv"); Arguments args1984; args1984.Add(s->LocalAt(2), false); return Call(c, fn1983, std::move(args1984)); }()); return v1980; }())) ? List({Value("DROP")}) : List({Value("PASS")})), false); return Call(c, fn1978, std::move(args1979)); }());
}
auto v1985 = ([&]() -> Value { auto dict1986 = Dict(); auto key1987 = Value("farmer"); Put(dict1986, key1987, Get(s->LocalAt(6), Value(int64_t{0}))); auto key1988 = Value("hands"); Put(dict1986, key1988, Slice(s->LocalAt(6), Value(int64_t{1}), Value{}, Value{})); auto key1989 = Value("market"); Put(dict1986, key1989, List({})); return dict1986; }());
s->SetAt(0, v1985);
auto v1990 = ([&]() -> Value { auto fn1991 = Attribute(Attribute(s->Global("_IMPL"), "chassis"), "_projected_shed"); Arguments args1992; args1992.positional.reserve(2); args1992.Add(s->LocalAt(0), false); args1992.Add(s->LocalAt(7), false); return Call(c, fn1991, std::move(args1992)); }());
s->SetAt(5, v1990);
auto v1993 = ([&]() -> Value { auto comp1994 = std::make_shared<Scope>(); comp1994->globals = s->globals; comp1994->parent = s; static constexpr const char* comp1994_names[] = {"item"}; comp1994->PrepareSlots(comp1994_names); auto result1995 = List(); for (const auto& item1996 : Iterate(s->Global("PRODUCTS"))) { comp1994->SetAt(0, item1996); if (!static_cast<bool>(([&]() -> Value { auto v1997 = ([&]() -> Value { auto fn1999 = PrepareDictionaryGet(comp1994->Captured("projected")); Arguments args2000; args2000.positional.reserve(2); args2000.Add(comp1994->LocalAt(0), false); args2000.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn1999, std::move(args2000)); }()); Value v1998; v1998 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v1997, v1998))) return Value(false); v1997 = v1998; return Value(true); }()))) continue; result1995.node()->sequence.push_back(List({Value("SELL"), comp1994->LocalAt(0), ([&]() -> Value { auto fn2001 = PrepareDictionaryGet(comp1994->Captured("projected")); Arguments args2002; args2002.positional.reserve(2); args2002.Add(comp1994->LocalAt(0), false); args2002.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn2001, std::move(args2002)); }())})); } return result1995; }());
Put(s->LocalAt(0), Value("market"), v1993);
(void)([&]() -> Value { auto fn2003 = Attribute(Get(s->LocalAt(0), Value("market")), "sort"); Arguments args2004; args2004.Keyword("key", Define(&Code_17afcffb89857c9fd680, s, Signature{{"o"}, {}, {}, {}, "", "", ([]() -> std::span<const char* const> { static constexpr const char* names[] = {"o"}; return names; }())}, true, "<lambda>")); return Call(c, fn2003, std::move(args2004)); }());
}
} catch (const Error& error1961) {
if (Matches(error1961, s->Global("Exception"))) {
auto v2008 = Attribute(Attribute(s->Global("_IMPL"), "chassis"), "diagnostics");
auto v2009 = Value("terminal_rescue_errors");
auto v2010 = Get(v2008, v2009);
Put(v2008, v2009, Inplace("Add", v2010, Value(int64_t{1})));
}
else { throw; }
}
return s->LocalAt(0);
return {};
}
}  // namespace kagg::opponents::compiled
