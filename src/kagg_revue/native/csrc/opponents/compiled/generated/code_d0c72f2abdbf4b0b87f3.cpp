// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_d0c72f2abdbf4b0b87f3(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"observation", "shops", "state", "step", "use_new"};
s->PrepareSlots(s_names);
if (static_cast<bool>(([&]() -> Value { auto v1898 = ([&]() -> Value { auto v1899 = s->LocalAt(3); Value v1900; v1900 = Value(int64_t{144}); if (!static_cast<bool>(Binary("GtE", v1899, v1900))) return Value(false); v1899 = v1900; return Value(true); }()); if (!static_cast<bool>(v1898)) return v1898; v1898 = Unary("Not", ([&]() -> Value { auto fn1901 = PrepareDictionaryGet(s->LocalAt(2)); Arguments args1902; args1902.Add(Value("day6"), false); return CallDictionaryGet(c, fn1901, std::move(args1902)); }())); return v1898; }()))) {
auto v1903 = ([&]() -> Value { auto fn1904 = s->Global("tuple"); Arguments args1905; args1905.Add(Slice(([&]() -> Value { auto v1906 = ([&]() -> Value { auto fn1907 = s->Global("_get"); Arguments args1908; args1908.positional.reserve(3); args1908.Add(([&]() -> Value { auto fn1909 = s->Global("_get"); Arguments args1910; args1910.positional.reserve(3); args1910.Add(s->LocalAt(0), false); args1910.Add(Value("town"), false); args1910.Add(([&]() -> Value { auto dict1911 = Dict(); return dict1911; }()), false); return Call(c, fn1909, std::move(args1910)); }()), false); args1908.Add(Value("unlocked_shops"), false); args1908.Add(List({}), false); return Call(c, fn1907, std::move(args1908)); }()); if (static_cast<bool>(v1906)) return v1906; v1906 = List({}); return v1906; }()), Value{}, Value(int64_t{2}), Value{}), false); return Call(c, fn1904, std::move(args1905)); }());
s->SetAt(1, v1903);
auto v1912 = ([&]() -> Value { auto v1913 = ([&]() -> Value { auto fn1915 = Attribute(s->LocalAt(1), "count"); Arguments args1916; args1916.Add(Value("YARN_STORE"), false); return Call(c, fn1915, std::move(args1916)); }()); Value v1914; v1914 = Value(int64_t{0}); if (!static_cast<bool>(Binary("LtE", v1913, v1914))) return Value(false); v1913 = v1914; return Value(true); }());
s->SetAt(4, v1912);
auto v1917 = (static_cast<bool>(s->LocalAt(4)) ? Value("EXP240") : Value("V39"));
Put(s->LocalAt(2), Value("expert"), v1917);
auto v1918 = (static_cast<bool>(s->LocalAt(4)) ? ([&]() -> Value { auto fn1919 = PrepareDictionaryGet(s->Global("_R108_SHOP_ROUTES")); Arguments args1920; args1920.positional.reserve(2); args1920.Add(s->LocalAt(1), false); args1920.Add(Value(int64_t{100}), false); return CallDictionaryGet(c, fn1919, std::move(args1920)); }()) : ([&]() -> Value { auto fn1921 = PrepareDictionaryGet(s->Global("_R110_OLD_SHOPS")); Arguments args1922; args1922.positional.reserve(2); args1922.Add(s->LocalAt(1), false); args1922.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn1921, std::move(args1922)); }()));
Put(s->LocalAt(2), Value("route"), v1918);
auto v1923 = Value(true);
Put(s->LocalAt(2), Value("day6"), v1923);
}
if (static_cast<bool>(([&]() -> Value { auto v1924 = ([&]() -> Value { auto v1925 = s->LocalAt(3); Value v1926; v1926 = Value(int64_t{648}); if (!static_cast<bool>(Binary("GtE", v1925, v1926))) return Value(false); v1925 = v1926; return Value(true); }()); if (!static_cast<bool>(v1924)) return v1924; v1924 = Unary("Not", ([&]() -> Value { auto fn1927 = PrepareDictionaryGet(s->LocalAt(2)); Arguments args1928; args1928.Add(Value("day27"), false); return CallDictionaryGet(c, fn1927, std::move(args1928)); }())); return v1924; }()))) {
auto v1929 = Value(int64_t{2});
Put(s->LocalAt(2), Value("route"), v1929);
auto v1930 = Value(true);
Put(s->LocalAt(2), Value("day27"), v1930);
}
return ([&]() -> Value { auto fn1931 = PrepareDictionaryGet(s->LocalAt(2)); Arguments args1932; args1932.positional.reserve(2); args1932.Add(Value("route"), false); args1932.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn1931, std::move(args1932)); }());
return {};
}
}  // namespace kagg::opponents::compiled
