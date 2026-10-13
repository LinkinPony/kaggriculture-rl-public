// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_0d208f90a6698acd1cad(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"_", "action", "budget", "credit", "extra", "final", "obs", "private", "quantity", "result", "state", "step", "stock"};
s->PrepareSlots(s_names);
auto v12001 = ([&]() -> Value { auto fn12002 = s->Global("int"); Arguments args12003; args12003.Add(Get(s->LocalAt(6), Value("step")), false); return Call(c, fn12002, std::move(args12003)); }());
s->SetAt(11, v12001);
if (static_cast<bool>(([&]() -> Value { auto v12004 = Unary("Not", ([&]() -> Value { auto v12005 = Value(int64_t{144}); Value v12006; v12006 = s->LocalAt(11); if (!static_cast<bool>(Binary("LtE", v12005, v12006))) return Value(false); v12005 = v12006; v12006 = Value(int64_t{695}); if (!static_cast<bool>(Binary("Lt", v12005, v12006))) return Value(false); v12005 = v12006; return Value(true); }())); if (static_cast<bool>(v12004)) return v12004; v12004 = ([&]() -> Value { auto fn12007 = s->Global("_r97_budget"); Arguments args12008; args12008.positional.reserve(2); args12008.Add(s->LocalAt(6), false); args12008.Add(([&]() -> Value { auto v12009 = ([&]() -> Value { auto fn12010 = PrepareDictionaryGet(s->LocalAt(1)); Arguments args12011; args12011.Add(Value("market"), false); return CallDictionaryGet(c, fn12010, std::move(args12011)); }()); if (static_cast<bool>(v12009)) return v12009; v12009 = List({}); return v12009; }()), false); return Call(c, fn12007, std::move(args12008)); }()); return v12004; }()))) {
return s->LocalAt(1);
}
auto v12012 = ([&]() -> Value { auto fn12013 = s->Global("_r128_sale_credit"); Arguments args12014; args12014.positional.reserve(2); args12014.Add(s->LocalAt(6), false); args12014.Add(s->LocalAt(1), false); return Call(c, fn12013, std::move(args12014)); }());
s->SetAt(3, v12012);
if (static_cast<bool>(Unary("Not", s->LocalAt(3)))) {
return s->LocalAt(1);
}
auto v12015 = ([&]() -> Value { auto fn12016 = s->Global("dict"); Arguments args12017; args12017.Add(s->LocalAt(6), false); args12017.Keyword("farms", ([&]() -> Value { auto comp12018 = std::make_shared<Scope>(); comp12018->globals = s->globals; comp12018->parent = s; static constexpr const char* comp12018_names[] = {"f"}; comp12018->PrepareSlots(comp12018_names); auto result12019 = List(); for (const auto& item12020 : Iterate(Get(s->LocalAt(6), Value("farms")))) { comp12018->SetAt(0, item12020); result12019.node()->sequence.push_back(([&]() -> Value { auto fn12021 = comp12018->Global("dict"); Arguments args12022; args12022.Add(comp12018->LocalAt(0), false); return Call(c, fn12021, std::move(args12022)); }())); } return result12019; }())); return Call(c, fn12016, std::move(args12017)); }());
s->SetAt(2, v12015);
auto v12023 = Get(Get(s->LocalAt(2), Value("farms")), Get(s->LocalAt(6), Value("player")));
auto v12024 = Value("money");
auto v12025 = Get(v12023, v12024);
Put(v12023, v12024, Inplace("Add", v12025, s->LocalAt(3)));
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto fn12026 = s->Global("_r97_budget"); Arguments args12027; args12027.positional.reserve(2); args12027.Add(s->LocalAt(2), false); args12027.Add(([&]() -> Value { auto v12028 = ([&]() -> Value { auto fn12029 = PrepareDictionaryGet(s->LocalAt(1)); Arguments args12030; args12030.Add(Value("market"), false); return CallDictionaryGet(c, fn12029, std::move(args12030)); }()); if (static_cast<bool>(v12028)) return v12028; v12028 = List({}); return v12028; }()), false); return Call(c, fn12026, std::move(args12027)); }())))) {
return s->LocalAt(1);
}
auto v12031 = ([&]() -> Value { auto fn12032 = s->Global("_r97_supply"); Arguments args12033; args12033.positional.reserve(2); args12033.Add(s->LocalAt(2), false); args12033.Add(s->LocalAt(1), false); return Call(c, fn12032, std::move(args12033)); }());
s->SetAt(9, v12031);
if (static_cast<bool>(([&]() -> Value { auto v12034 = s->LocalAt(9); Value v12035; v12035 = s->LocalAt(1); if (!static_cast<bool>(Binary("Eq", v12034, v12035))) return Value(false); v12034 = v12035; return Value(true); }()))) {
return s->LocalAt(1);
}
if (!static_cast<bool>(([&]() -> Value { auto v12036 = Get(Get(s->LocalAt(9), Value("market")), Value(int64_t{0})); Value v12037; v12037 = Get(Get(s->LocalAt(1), Value("market")), Value(int64_t{0})); if (!static_cast<bool>(Binary("Eq", v12036, v12037))) return Value(false); v12036 = v12037; return Value(true); }()))) throw Error("AssertionError", "assertion failed");
auto v12038 = ([&]() -> Value { auto fn12039 = s->Global("_r127_fields"); Arguments args12040; args12040.positional.reserve(2); args12040.Add(s->LocalAt(6), false); args12040.Add(s->LocalAt(9), false); return Call(c, fn12039, std::move(args12040)); }());
auto unpack12041 = Iterate(v12038);
ValidateUnpack(unpack12041, 2, false);
s->SetAt(0, unpack12041.at(0));
s->SetAt(7, unpack12041.at(1));
auto v12042 = ([&]() -> Value { auto fn12043 = s->Global("_r97_market_stock"); Arguments args12044; args12044.positional.reserve(2); args12044.Add(Get(s->LocalAt(7), Value("shed")), false); args12044.Add(Get(s->LocalAt(9), Value("market")), false); return Call(c, fn12043, std::move(args12044)); }());
auto unpack12045 = Iterate(v12042);
ValidateUnpack(unpack12045, 3, false);
s->SetAt(12, unpack12045.at(0));
s->SetAt(0, unpack12045.at(1));
s->SetAt(0, unpack12045.at(2));
auto v12046 = ([&]() -> Value { auto fn12047 = s->Global("_r97_delivery"); Arguments args12048; args12048.positional.reserve(3); args12048.Add(s->LocalAt(12), false); args12048.Add(s->LocalAt(7), false); args12048.Add(([&]() -> Value { auto v12049 = ([&]() -> Value { auto v12051 = s->LocalAt(11); return Binary("Mod", v12051, Value(int64_t{24})); }()); Value v12050; v12050 = Value(int64_t{23}); if (!static_cast<bool>(Binary("Eq", v12049, v12050))) return Value(false); v12049 = v12050; return Value(true); }()), false); return Call(c, fn12047, std::move(args12048)); }());
auto unpack12052 = Iterate(v12046);
ValidateUnpack(unpack12052, 2, false);
s->SetAt(5, unpack12052.at(0));
s->SetAt(0, unpack12052.at(1));
auto v12053 = Define(&Code_e404be0f14aa9e45b2ab, s, Signature{{"a"}, {}, {}, {}, "", "", ([]() -> std::span<const char* const> { static constexpr const char* names[] = {"a"}; return names; }())}, true, "<lambda>");
s->SetAt(8, v12053);
auto v12072 = ([&]() -> Value { auto fn12073 = s->Global("max"); Arguments args12074; args12074.positional.reserve(2); args12074.Add(Value(int64_t{0}), false); args12074.Add(([&]() -> Value { auto v12075 = ([&]() -> Value { auto fn12076 = s->LocalAt(8); Arguments args12077; args12077.Add(s->LocalAt(9), false); return Call(c, fn12076, std::move(args12077)); }()); return Binary("Sub", v12075, ([&]() -> Value { auto fn12078 = s->LocalAt(8); Arguments args12079; args12079.Add(s->LocalAt(1), false); return Call(c, fn12078, std::move(args12079)); }())); }()), false); return Call(c, fn12073, std::move(args12074)); }());
s->SetAt(4, v12072);
auto v12080 = Tuple({([&]() -> Value { auto v12081 = s->LocalAt(11); return Binary("Add", v12081, Value(int64_t{1})); }()), ([&]() -> Value { auto fn12082 = PrepareDictionaryGet(s->LocalAt(5)); Arguments args12083; args12083.positional.reserve(2); args12083.Add(Value("WHEAT"), false); args12083.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn12082, std::move(args12083)); }()), s->LocalAt(4)});
Put(s->LocalAt(10), Value("credit_pending"), v12080);
auto v12084 = s->Global("_R128_REPORT");
auto v12085 = Value("sale_credit_orders");
auto v12086 = Get(v12084, v12085);
Put(v12084, v12085, Inplace("Add", v12086, Value(int64_t{1})));
auto v12087 = s->Global("_R128_REPORT");
auto v12088 = Value("sale_credit_lower_bound");
auto v12089 = Get(v12087, v12088);
Put(v12087, v12088, Inplace("Add", v12089, s->LocalAt(3)));
auto v12090 = s->Global("_R128_REPORT");
auto v12091 = Value("sale_credit_grain_units");
auto v12092 = Get(v12090, v12091);
Put(v12090, v12091, Inplace("Add", v12092, s->LocalAt(4)));
return s->LocalAt(9);
return {};
}
}  // namespace kagg::opponents::compiled
