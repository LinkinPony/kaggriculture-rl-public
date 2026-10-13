// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_a6288f747330a300803f(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"_", "action", "all_units", "choices", "cost", "farm", "first_crop", "i", "item", "mode", "n", "obs", "path", "plans", "purchases", "q", "quote", "remaining", "score", "stock", "subset", "targets", "topup", "total_cost", "total_q", "total_value", "units", "value", "x", "y"};
s->PrepareSlots(s_names);
auto v8867 = Get(Get(s->LocalAt(11), Value("farms")), Get(s->LocalAt(11), Value("player")));
s->SetAt(5, v8867);
auto v8868 = List({});
s->SetAt(3, v8868);
for (const auto& item8869 : Iterate(([&]() -> Value { auto fn8870 = s->Global("enumerate"); Arguments args8871; args8871.Add(Tuple({Value{}, Value("WHEAT"), Value("CARROT")}), false); return Call(c, fn8870, std::move(args8871)); }()))) {
auto unpack8872 = Iterate(item8869);
ValidateUnpack(unpack8872, 2, false);
s->SetAt(9, unpack8872.at(0));
s->SetAt(6, unpack8872.at(1));
auto v8873 = ([&]() -> Value { auto fn8874 = s->Global("dict"); Arguments args8875; args8875.Add(s->LocalAt(21), false); return Call(c, fn8874, std::move(args8875)); }());
s->SetAt(17, v8873);
auto v8876 = List({});
s->SetAt(13, v8876);
auto v8877 = Value(int64_t{0});
s->SetAt(24, v8877);
auto v8878 = Value(int64_t{0});
s->SetAt(23, v8878);
auto v8879 = Value(int64_t{0});
s->SetAt(25, v8879);
auto v8880 = ([&]() -> Value { auto dict8881 = Dict(); auto key8882 = Value("WHEAT"); Put(dict8881, key8882, Value(int64_t{0})); auto key8883 = Value("CARROT"); Put(dict8881, key8883, Value(int64_t{0})); return dict8881; }());
s->SetAt(2, v8880);
for (const auto& item8884 : Iterate(([&]() -> Value { auto fn8885 = s->Global("range"); Arguments args8886; args8886.Add(s->Global("_R51_INPUT_MAX_WORKERS"), false); return Call(c, fn8885, std::move(args8886)); }()))) {
s->SetAt(7, item8884);
auto v8887 = (static_cast<bool>(([&]() -> Value { auto v8888 = ([&]() -> Value { auto v8889 = s->LocalAt(7); Value v8890; v8890 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v8889, v8890))) return Value(false); v8889 = v8890; return Value(true); }()); if (!static_cast<bool>(v8888)) return v8888; v8888 = s->LocalAt(6); return v8888; }())) ? ([&]() -> Value { auto comp8891 = std::make_shared<Scope>(); comp8891->globals = s->globals; comp8891->parent = s; static constexpr const char* comp8891_names[] = {"t", "xy"}; comp8891->PrepareSlots(comp8891_names); auto result8892 = Dict(); for (const auto& item8893 : Iterate(([&]() -> Value { auto fn8894 = Attribute(s->LocalAt(17), "items"); Arguments args8895; return Call(c, fn8894, std::move(args8895)); }()))) { auto unpack8896 = Iterate(item8893); ValidateUnpack(unpack8896, 2, false); comp8891->SetAt(1, unpack8896.at(0)); comp8891->SetAt(0, unpack8896.at(1)); if (!static_cast<bool>(([&]() -> Value { auto v8897 = Get(comp8891->LocalAt(0), Value("crop")); Value v8898; v8898 = comp8891->Captured("first_crop"); if (!static_cast<bool>(Binary("Eq", v8897, v8898))) return Value(false); v8897 = v8898; return Value(true); }()))) continue; Put(result8892, comp8891->LocalAt(1), comp8891->LocalAt(0)); } return result8892; }()) : s->LocalAt(17));
s->SetAt(20, v8887);
auto v8899 = ([&]() -> Value { auto fn8900 = s->Global("_r51_input_path"); Arguments args8901; args8901.positional.reserve(4); args8901.Add(s->LocalAt(11), false); args8901.Add(s->LocalAt(20), false); args8901.Add(s->LocalAt(1), false); args8901.Add(s->LocalAt(7), false); return Call(c, fn8900, std::move(args8901)); }());
auto unpack8902 = Iterate(v8899);
ValidateUnpack(unpack8902, 2, false);
s->SetAt(12, unpack8902.at(0));
s->SetAt(26, unpack8902.at(1));
auto v8903 = ([&]() -> Value { auto fn8904 = s->Global("len"); Arguments args8905; args8905.Add(s->LocalAt(12), false); return Call(c, fn8904, std::move(args8905)); }());
s->SetAt(15, v8903);
if (static_cast<bool>(([&]() -> Value { auto v8906 = ([&]() -> Value { auto v8907 = s->LocalAt(15); Value v8908; v8908 = Value(int64_t{3}); if (!static_cast<bool>(Binary("Lt", v8907, v8908))) return Value(false); v8907 = v8908; return Value(true); }()); if (static_cast<bool>(v8906)) return v8906; v8906 = ([&]() -> Value { auto v8909 = ([&]() -> Value { auto v8911 = ([&]() -> Value { auto v8912 = ([&]() -> Value { auto fn8913 = s->Global("len"); Arguments args8914; args8914.Add(([&]() -> Value { auto fn8915 = PrepareDictionaryGet(s->LocalAt(1)); Arguments args8916; args8916.positional.reserve(2); args8916.Add(Value("market"), false); args8916.Add(List({}), false); return CallDictionaryGet(c, fn8915, std::move(args8916)); }()), false); return Call(c, fn8913, std::move(args8914)); }()); return Binary("Add", v8912, Value(int64_t{2})); }()); return Binary("Add", v8911, s->LocalAt(7)); }()); Value v8910; v8910 = Value(int64_t{10}); if (!static_cast<bool>(Binary("Gt", v8909, v8910))) return Value(false); v8909 = v8910; return Value(true); }()); if (static_cast<bool>(v8906)) return v8906; v8906 = ([&]() -> Value { auto v8917 = ([&]() -> Value { auto v8919 = ([&]() -> Value { auto v8920 = ([&]() -> Value { auto v8921 = ([&]() -> Value { auto v8922 = ([&]() -> Value { auto fn8923 = s->Global("sum"); Arguments args8924; args8924.Add(([&]() -> Value { auto fn8925 = Attribute(s->LocalAt(19), "values"); Arguments args8926; return Call(c, fn8925, std::move(args8926)); }()), false); return Call(c, fn8923, std::move(args8924)); }()); return Binary("Add", v8922, s->LocalAt(14)); }()); return Binary("Add", v8921, s->LocalAt(24)); }()); return Binary("Add", v8920, s->LocalAt(15)); }()); return Binary("Add", v8919, s->LocalAt(22)); }()); Value v8918; v8918 = Value(int64_t{95}); if (!static_cast<bool>(Binary("Gt", v8917, v8918))) return Value(false); v8917 = v8918; return Value(true); }()); return v8906; }()))) {
break;
}
auto v8927 = ([&]() -> Value { auto fn8928 = s->Global("_r37_market_price"); Arguments args8929; args8929.positional.reserve(2); args8929.Add(Value("FERTILIZER"), false); args8929.Add(([&]() -> Value { auto v8930 = ([&]() -> Value { auto v8931 = ([&]() -> Value { auto v8932 = Get(Get(Get(s->LocalAt(11), Value("market")), Value("inventory")), Value("FERTILIZER")); return Binary("Sub", v8932, s->LocalAt(24)); }()); return Binary("Sub", v8931, s->LocalAt(15)); }()); return Binary("Sub", v8930, s->LocalAt(22)); }()), false); return Call(c, fn8928, std::move(args8929)); }());
s->SetAt(16, v8927);
auto v8933 = ([&]() -> Value { auto v8934 = ([&]() -> Value { auto v8935 = ([&]() -> Value { auto v8936 = s->LocalAt(15); return Binary("Add", v8936, (static_cast<bool>(([&]() -> Value { auto v8937 = s->LocalAt(7); Value v8938; v8938 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v8937, v8938))) return Value(false); v8937 = v8938; return Value(true); }())) ? s->LocalAt(22) : Value(int64_t{0}))); }()); return Binary("Mult", v8935, ([&]() -> Value { auto v8939 = s->LocalAt(16); return Binary("Add", v8939, Value(int64_t{2})); }())); }()); return Binary("Add", v8934, ([&]() -> Value { auto fn8940 = s->Global("_v219_fib"); Arguments args8941; args8941.Add(([&]() -> Value { auto v8942 = ([&]() -> Value { auto fn8943 = s->Global("int"); Arguments args8944; args8944.Add(Get(s->LocalAt(5), Value("hires_today")), false); return Call(c, fn8943, std::move(args8944)); }()); return Binary("Add", v8942, s->LocalAt(7)); }()), false); return Call(c, fn8940, std::move(args8941)); }())); }());
s->SetAt(4, v8933);
auto v8945 = ([&]() -> Value { auto fn8946 = s->Global("sum"); Arguments args8947; args8947.Add(([&]() -> Value { auto comp8948 = std::make_shared<Scope>(); comp8948->globals = s->globals; comp8948->parent = s; static constexpr const char* comp8948_names[] = {"item", "n"}; comp8948->PrepareSlots(comp8948_names); auto result8949 = List(); for (const auto& item8950 : Iterate(([&]() -> Value { auto fn8951 = Attribute(s->LocalAt(26), "items"); Arguments args8952; return Call(c, fn8951, std::move(args8952)); }()))) { auto unpack8953 = Iterate(item8950); ValidateUnpack(unpack8953, 2, false); comp8948->SetAt(0, unpack8953.at(0)); comp8948->SetAt(1, unpack8953.at(1)); result8949.node()->sequence.push_back(([&]() -> Value { auto v8954 = comp8948->LocalAt(1); return Binary("Mult", v8954, ([&]() -> Value { auto fn8955 = comp8948->Global("max"); Arguments args8956; args8956.positional.reserve(2); args8956.Add(Value(int64_t{1}), false); args8956.Add(([&]() -> Value { auto v8957 = ([&]() -> Value { auto fn8958 = comp8948->Global("_r37_market_price"); Arguments args8959; args8959.positional.reserve(2); args8959.Add(comp8948->LocalAt(0), false); args8959.Add(([&]() -> Value { auto v8960 = ([&]() -> Value { auto v8961 = Get(Get(Get(comp8948->Captured("obs"), Value("market")), Value("inventory")), comp8948->LocalAt(0)); return Binary("Add", v8961, Get(comp8948->Captured("all_units"), comp8948->LocalAt(0))); }()); return Binary("Add", v8960, comp8948->LocalAt(1)); }()), false); return Call(c, fn8958, std::move(args8959)); }()); return Binary("Sub", v8957, Value(int64_t{2})); }()), false); return Call(c, fn8955, std::move(args8956)); }())); }())); } return result8949; }()), false); return Call(c, fn8946, std::move(args8947)); }());
s->SetAt(27, v8945);
if (static_cast<bool>(([&]() -> Value { auto v8962 = ([&]() -> Value { auto v8963 = s->LocalAt(27); Value v8964; v8964 = ([&]() -> Value { auto v8965 = ([&]() -> Value { auto v8966 = Value(1.5); return Binary("Mult", v8966, s->LocalAt(4)); }()); return Binary("Add", v8965, Value(int64_t{50})); }()); if (!static_cast<bool>(Binary("Lt", v8963, v8964))) return Value(false); v8963 = v8964; return Value(true); }()); if (static_cast<bool>(v8962)) return v8962; v8962 = ([&]() -> Value { auto v8967 = Get(s->LocalAt(5), Value("money")); Value v8968; v8968 = ([&]() -> Value { auto v8969 = ([&]() -> Value { auto v8970 = s->LocalAt(23); return Binary("Add", v8970, s->LocalAt(4)); }()); return Binary("Add", v8969, Value(int64_t{3000})); }()); if (!static_cast<bool>(Binary("Lt", v8967, v8968))) return Value(false); v8967 = v8968; return Value(true); }()); return v8962; }()))) {
break;
}
(void)([&]() -> Value { auto fn8971 = Attribute(s->LocalAt(13), "append"); Arguments args8972; args8972.Add(([&]() -> Value { auto dict8973 = Dict(); auto key8974 = Value("path"); Put(dict8973, key8974, s->LocalAt(12)); auto key8975 = Value("quantity"); Put(dict8973, key8975, s->LocalAt(15)); auto key8976 = Value("loaded"); Put(dict8973, key8976, Value(false)); return dict8973; }()), false); return Call(c, fn8971, std::move(args8972)); }());
auto v8977 = s->LocalAt(24);
s->SetAt(24, Inplace("Add", v8977, s->LocalAt(15)));
auto v8978 = s->LocalAt(23);
s->SetAt(23, Inplace("Add", v8978, s->LocalAt(4)));
auto v8979 = s->LocalAt(25);
s->SetAt(25, Inplace("Add", v8979, s->LocalAt(27)));
for (const auto& item8980 : Iterate(([&]() -> Value { auto fn8981 = Attribute(s->LocalAt(26), "items"); Arguments args8982; return Call(c, fn8981, std::move(args8982)); }()))) {
auto unpack8983 = Iterate(item8980);
ValidateUnpack(unpack8983, 2, false);
s->SetAt(8, unpack8983.at(0));
s->SetAt(10, unpack8983.at(1));
auto v8984 = s->LocalAt(2);
auto v8985 = s->LocalAt(8);
auto v8986 = Get(v8984, v8985);
Put(v8984, v8985, Inplace("Add", v8986, s->LocalAt(10)));
}
for (const auto& item8987 : Iterate(s->LocalAt(12))) {
auto unpack8988 = Iterate(item8987);
ValidateUnpack(unpack8988, 4, false);
s->SetAt(28, unpack8988.at(0));
s->SetAt(29, unpack8988.at(1));
s->SetAt(0, unpack8988.at(2));
s->SetAt(0, unpack8988.at(3));
(void)([&]() -> Value { auto fn8989 = Attribute(s->LocalAt(17), "pop"); Arguments args8990; args8990.positional.reserve(2); args8990.Add(Tuple({s->LocalAt(28), s->LocalAt(29)}), false); args8990.Add(Value{}, false); return Call(c, fn8989, std::move(args8990)); }());
}
}
auto v8991 = Tuple({([&]() -> Value { auto v8992 = s->LocalAt(25); return Binary("Sub", v8992, s->LocalAt(23)); }()), s->LocalAt(25), Unary("USub", s->LocalAt(23)), Unary("USub", ([&]() -> Value { auto fn8993 = s->Global("len"); Arguments args8994; args8994.Add(s->LocalAt(13), false); return Call(c, fn8993, std::move(args8994)); }())), Unary("USub", s->LocalAt(9))});
s->SetAt(18, v8991);
(void)([&]() -> Value { auto fn8995 = Attribute(s->LocalAt(3), "append"); Arguments args8996; args8996.Add(Tuple({s->LocalAt(18), s->LocalAt(13), s->LocalAt(24), s->LocalAt(23), s->LocalAt(2)}), false); return Call(c, fn8995, std::move(args8996)); }());
}
auto v8997 = ([&]() -> Value { auto fn8998 = s->Global("max"); Arguments args8999; args8999.Add(s->LocalAt(3), false); args8999.Keyword("key", Define(&Code_2fa60ca48797f6c5a7bf, s, Signature{{"v"}, {}, {}, {}, "", "", ([]() -> std::span<const char* const> { static constexpr const char* names[] = {"v"}; return names; }())}, true, "<lambda>")); return Call(c, fn8998, std::move(args8999)); }());
auto unpack9000 = Iterate(v8997);
ValidateUnpack(unpack9000, 5, false);
s->SetAt(0, unpack9000.at(0));
s->SetAt(13, unpack9000.at(1));
s->SetAt(24, unpack9000.at(2));
s->SetAt(23, unpack9000.at(3));
s->SetAt(2, unpack9000.at(4));
return Tuple({s->LocalAt(13), s->LocalAt(24), s->LocalAt(23), s->LocalAt(2)});
return {};
}
}  // namespace kagg::opponents::compiled
