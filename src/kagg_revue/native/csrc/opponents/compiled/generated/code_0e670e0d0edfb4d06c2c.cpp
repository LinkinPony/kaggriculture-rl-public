// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_0e670e0d0edfb4d06c2c(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"_", "actor", "bundles", "carried", "chosen", "cursor", "direct", "distance", "event", "farm", "fertilizer", "first", "future_deposits", "harvest", "horizon", "inventory", "key", "max_per_actor", "obligation", "offset", "operations", "ops", "owners", "pos", "prefix_deposits", "prices", "private", "proposals", "route", "run", "second", "seen", "stops", "value", "variants", "xy"};
s->PrepareSlots(s_names);
auto v18027 = ([&]() -> Value { auto dict18028 = Dict(); return dict18028; }());
s->SetAt(22, v18027);
for (const auto& item18029 : Iterate(Get(s->LocalAt(29), Value("events")))) {
s->SetAt(8, item18029);
if (static_cast<bool>(([&]() -> Value { auto v18030 = Value("acquired"); Value v18031; v18031 = s->LocalAt(8); if (!static_cast<bool>(Binary("In", v18030, v18031))) return Value(false); v18030 = v18031; return Value(true); }()))) {
(void)([&]() -> Value { auto fn18032 = Attribute(([&]() -> Value { auto fn18034 = Attribute(s->LocalAt(22), "setdefault"); Arguments args18035; args18035.positional.reserve(2); args18035.Add(Tuple({([&]() -> Value { auto fn18036 = s->Global("tuple"); Arguments args18037; args18037.Add(Get(s->LocalAt(8), Value("xy")), false); return Call(c, fn18036, std::move(args18037)); }()), Get(s->LocalAt(8), Value("op"))}), false); args18035.Add(([&]() -> Value { auto fn18038 = s->Global("set"); Arguments args18039; return Call(c, fn18038, std::move(args18039)); }()), false); return Call(c, fn18034, std::move(args18035)); }()), "add"); Arguments args18033; args18033.Add(Get(s->LocalAt(8), Value("actor")), false); return Call(c, fn18032, std::move(args18033)); }());
}
}
auto v18040 = List({});
s->SetAt(27, v18040);
auto v18041 = ([&]() -> Value { auto fn18042 = s->Global("set"); Arguments args18043; return Call(c, fn18042, std::move(args18043)); }());
s->SetAt(31, v18041);
auto v18044 = ([&]() -> Value { auto fn18045 = s->Global("len"); Arguments args18046; args18046.Add(Get(s->LocalAt(29), Value("rows")), false); return Call(c, fn18045, std::move(args18046)); }());
s->SetAt(14, v18044);
for (const auto& item18047 : Iterate(([&]() -> Value { auto fn18048 = s->Global("range"); Arguments args18049; args18049.Add(s->LocalAt(14), false); return Call(c, fn18048, std::move(args18049)); }()))) {
s->SetAt(19, item18047);
auto v18050 = Get(Get(s->LocalAt(29), Value("states")), s->LocalAt(19));
auto unpack18051 = Iterate(v18050);
ValidateUnpack(unpack18051, 2, false);
s->SetAt(9, unpack18051.at(0));
s->SetAt(26, unpack18051.at(1));
auto v18052 = ([&]() -> Value { auto fn18053 = s->Global("tuple"); Arguments args18054; args18054.Add((static_cast<bool>(([&]() -> Value { auto v18055 = s->LocalAt(1); Value v18056; v18056 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v18055, v18056))) return Value(false); v18055 = v18056; return Value(true); }())) ? Get(s->LocalAt(9), Value("farmer")) : Get(Get(s->LocalAt(9), Value("hands")), ([&]() -> Value { auto v18057 = s->LocalAt(1); return Binary("Sub", v18057, Value(int64_t{1})); }()))), false); return Call(c, fn18053, std::move(args18054)); }());
s->SetAt(23, v18052);
auto v18058 = Get(Get(s->LocalAt(26), Value("inventories")), s->LocalAt(1));
s->SetAt(15, v18058);
auto v18059 = ([&]() -> Value { auto fn18060 = s->Global("sum"); Arguments args18061; args18061.Add(([&]() -> Value { auto comp18062 = std::make_shared<Scope>(); comp18062->globals = s->globals; comp18062->parent = s; static constexpr const char* comp18062_names[] = {"count", "item"}; comp18062->PrepareSlots(comp18062_names); auto result18063 = List(); for (const auto& item18064 : Iterate(([&]() -> Value { auto fn18065 = Attribute(s->LocalAt(15), "items"); Arguments args18066; return Call(c, fn18065, std::move(args18066)); }()))) { auto unpack18067 = Iterate(item18064); ValidateUnpack(unpack18067, 2, false); comp18062->SetAt(1, unpack18067.at(0)); comp18062->SetAt(0, unpack18067.at(1)); result18063.node()->sequence.push_back(([&]() -> Value { auto v18068 = ([&]() -> Value { auto fn18069 = PrepareDictionaryGet(comp18062->Captured("prices")); Arguments args18070; args18070.positional.reserve(2); args18070.Add(comp18062->LocalAt(1), false); args18070.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn18069, std::move(args18070)); }()); return Binary("Mult", v18068, comp18062->LocalAt(0)); }())); } return result18063; }()), false); return Call(c, fn18060, std::move(args18061)); }());
s->SetAt(3, v18059);
auto v18071 = (static_cast<bool>(s->LocalAt(19)) ? Get(Get(Get(Get(s->LocalAt(29), Value("rows")), ([&]() -> Value { auto v18072 = s->LocalAt(19); return Binary("Sub", v18072, Value(int64_t{1})); }())), Value("deposited_by_actor")), s->LocalAt(1)) : ([&]() -> Value { auto dict18073 = Dict(); return dict18073; }()));
s->SetAt(24, v18071);
auto v18074 = Get(Get(Get(Get(s->LocalAt(29), Value("rows")), Unary("USub", Value(int64_t{1}))), Value("deposited_by_actor")), s->LocalAt(1));
s->SetAt(12, v18074);
auto v18075 = ([&]() -> Value { auto fn18076 = s->Global("sum"); Arguments args18077; args18077.Add(([&]() -> Value { auto comp18078 = std::make_shared<Scope>(); comp18078->globals = s->globals; comp18078->parent = s; static constexpr const char* comp18078_names[] = {"count", "item"}; comp18078->PrepareSlots(comp18078_names); auto result18079 = List(); for (const auto& item18080 : Iterate(([&]() -> Value { auto fn18081 = Attribute(s->LocalAt(12), "items"); Arguments args18082; return Call(c, fn18081, std::move(args18082)); }()))) { auto unpack18083 = Iterate(item18080); ValidateUnpack(unpack18083, 2, false); comp18078->SetAt(1, unpack18083.at(0)); comp18078->SetAt(0, unpack18083.at(1)); result18079.node()->sequence.push_back(([&]() -> Value { auto v18084 = ([&]() -> Value { auto fn18085 = PrepareDictionaryGet(comp18078->Captured("prices")); Arguments args18086; args18086.positional.reserve(2); args18086.Add(comp18078->LocalAt(1), false); args18086.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn18085, std::move(args18086)); }()); return Binary("Mult", v18084, ([&]() -> Value { auto v18087 = comp18078->LocalAt(0); return Binary("Sub", v18087, ([&]() -> Value { auto fn18088 = PrepareDictionaryGet(comp18078->Captured("prefix_deposits")); Arguments args18089; args18089.positional.reserve(2); args18089.Add(comp18078->LocalAt(1), false); args18089.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn18088, std::move(args18089)); }())); }())); }())); } return result18079; }()), false); return Call(c, fn18076, std::move(args18077)); }());
s->SetAt(18, v18075);
auto v18090 = List({});
s->SetAt(2, v18090);
for (const auto& item18091 : Iterate(Get(([&]() -> Value { auto fn18092 = s->Global("_exp303_resources"); Arguments args18093; args18093.positional.reserve(2); args18093.Add(s->LocalAt(29), false); args18093.Add(s->LocalAt(25), false); return Call(c, fn18092, std::move(args18093)); }()), s->LocalAt(19)))) {
auto unpack18094 = Iterate(item18091);
ValidateUnpack(unpack18094, 3, false);
s->SetAt(35, unpack18094.at(0));
s->SetAt(13, unpack18094.at(1));
s->SetAt(10, unpack18094.at(2));
auto v18095 = Tuple({List({}), Value(int64_t{0})});
auto unpack18096 = Iterate(v18095);
ValidateUnpack(unpack18096, 2, false);
s->SetAt(20, unpack18096.at(0));
s->SetAt(33, unpack18096.at(1));
if (static_cast<bool>(([&]() -> Value { auto v18097 = ([&]() -> Value { auto v18098 = s->LocalAt(13); Value v18099; v18099 = Value{}; if (!static_cast<bool>(Binary("IsNot", v18098, v18099))) return Value(false); v18098 = v18099; return Value(true); }()); if (!static_cast<bool>(v18097)) return v18097; v18097 = Unary("Not", ([&]() -> Value { auto v18100 = ([&]() -> Value { auto fn18101 = PrepareDictionaryGet(s->LocalAt(22)); Arguments args18102; args18102.positional.reserve(2); args18102.Add(Tuple({s->LocalAt(35), Value("HARVEST")}), false); args18102.Add(([&]() -> Value { auto fn18103 = s->Global("set"); Arguments args18104; return Call(c, fn18103, std::move(args18104)); }()), false); return CallDictionaryGet(c, fn18101, std::move(args18102)); }()); return Binary("Sub", v18100, Set({s->LocalAt(1)})); }())); return v18097; }()))) {
(void)([&]() -> Value { auto fn18105 = Attribute(s->LocalAt(20), "append"); Arguments args18106; args18106.Add(List({Value("HARVEST")}), false); return Call(c, fn18105, std::move(args18106)); }());
auto v18107 = s->LocalAt(33);
s->SetAt(33, Inplace("Add", v18107, s->LocalAt(13)));
}
if (static_cast<bool>(([&]() -> Value { auto v18108 = ([&]() -> Value { auto v18109 = s->LocalAt(10); Value v18110; v18110 = Value{}; if (!static_cast<bool>(Binary("IsNot", v18109, v18110))) return Value(false); v18109 = v18110; return Value(true); }()); if (!static_cast<bool>(v18108)) return v18108; v18108 = Unary("Not", ([&]() -> Value { auto v18111 = ([&]() -> Value { auto fn18112 = PrepareDictionaryGet(s->LocalAt(22)); Arguments args18113; args18113.positional.reserve(2); args18113.Add(Tuple({s->LocalAt(35), Value("COLLECT_FERTILIZER")}), false); args18113.Add(([&]() -> Value { auto fn18114 = s->Global("set"); Arguments args18115; return Call(c, fn18114, std::move(args18115)); }()), false); return CallDictionaryGet(c, fn18112, std::move(args18113)); }()); return Binary("Sub", v18111, Set({s->LocalAt(1)})); }())); return v18108; }()))) {
(void)([&]() -> Value { auto fn18116 = Attribute(s->LocalAt(20), "append"); Arguments args18117; args18117.Add(List({Value("COLLECT_FERTILIZER")}), false); return Call(c, fn18116, std::move(args18117)); }());
auto v18118 = s->LocalAt(33);
s->SetAt(33, Inplace("Add", v18118, s->LocalAt(10)));
}
if (static_cast<bool>(s->LocalAt(20))) {
auto v18119 = ([&]() -> Value { auto v18120 = ([&]() -> Value { auto v18121 = ([&]() -> Value { auto v18122 = ([&]() -> Value { auto fn18123 = s->Global("abs"); Arguments args18124; args18124.Add(([&]() -> Value { auto v18125 = Get(s->LocalAt(23), Value(int64_t{0})); return Binary("Sub", v18125, Get(s->LocalAt(35), Value(int64_t{0}))); }()), false); return Call(c, fn18123, std::move(args18124)); }()); return Binary("Add", v18122, ([&]() -> Value { auto fn18126 = s->Global("abs"); Arguments args18127; args18127.Add(([&]() -> Value { auto v18128 = Get(s->LocalAt(23), Value(int64_t{1})); return Binary("Sub", v18128, Get(s->LocalAt(35), Value(int64_t{1}))); }()), false); return Call(c, fn18126, std::move(args18127)); }())); }()); return Binary("Add", v18121, ([&]() -> Value { auto fn18129 = s->Global("len"); Arguments args18130; args18130.Add(s->LocalAt(20), false); return Call(c, fn18129, std::move(args18130)); }())); }()); return Binary("Add", v18120, Get(s->Global("_R150_HOME_DISTANCE"), s->LocalAt(35))); }());
s->SetAt(7, v18119);
if (static_cast<bool>(([&]() -> Value { auto v18131 = s->LocalAt(7); Value v18132; v18132 = ([&]() -> Value { auto v18133 = s->LocalAt(14); return Binary("Sub", v18133, s->LocalAt(19)); }()); if (!static_cast<bool>(Binary("LtE", v18131, v18132))) return Value(false); v18131 = v18132; return Value(true); }()))) {
(void)([&]() -> Value { auto fn18134 = Attribute(s->LocalAt(2), "append"); Arguments args18135; args18135.Add(Tuple({s->LocalAt(35), s->LocalAt(20), s->LocalAt(33), s->LocalAt(7)}), false); return Call(c, fn18134, std::move(args18135)); }());
}
}
}
(void)([&]() -> Value { auto fn18136 = Attribute(s->LocalAt(2), "sort"); Arguments args18137; args18137.Keyword("key", Define(&Code_504c8a9f1492e28a8927, s, Signature{{"b"}, {}, {}, {}, "", "", ([]() -> std::span<const char* const> { static constexpr const char* names[] = {"b"}; return names; }())}, true, "<lambda>")); return Call(c, fn18136, std::move(args18137)); }());
auto v18139 = (static_cast<bool>(s->LocalAt(3)) ? List({Tuple({List({}), s->LocalAt(3)})}) : List({}));
s->SetAt(34, v18139);
for (const auto& item18140 : Iterate(Slice(s->LocalAt(2), Value{}, Value(int64_t{6}), Value{}))) {
auto unpack18141 = Iterate(item18140);
ValidateUnpack(unpack18141, 4, false);
s->SetAt(35, unpack18141.at(0));
s->SetAt(21, unpack18141.at(1));
s->SetAt(33, unpack18141.at(2));
s->SetAt(0, unpack18141.at(3));
(void)([&]() -> Value { auto fn18142 = Attribute(s->LocalAt(34), "append"); Arguments args18143; args18143.Add(Tuple({List({Tuple({s->LocalAt(35), s->LocalAt(21)})}), ([&]() -> Value { auto v18144 = s->LocalAt(3); return Binary("Add", v18144, s->LocalAt(33)); }())}), false); return Call(c, fn18142, std::move(args18143)); }());
}
for (const auto& item18145 : Iterate(Slice(s->LocalAt(2), Value{}, Value(int64_t{3}), Value{}))) {
s->SetAt(11, item18145);
for (const auto& item18146 : Iterate(Slice(s->LocalAt(2), Value{}, Value(int64_t{3}), Value{}))) {
s->SetAt(30, item18146);
if (static_cast<bool>(([&]() -> Value { auto v18147 = Get(s->LocalAt(11), Value(int64_t{0})); Value v18148; v18148 = Get(s->LocalAt(30), Value(int64_t{0})); if (!static_cast<bool>(Binary("NotEq", v18147, v18148))) return Value(false); v18147 = v18148; return Value(true); }()))) {
(void)([&]() -> Value { auto fn18149 = Attribute(s->LocalAt(34), "append"); Arguments args18150; args18150.Add(Tuple({List({Tuple({Get(s->LocalAt(11), Value(int64_t{0})), Get(s->LocalAt(11), Value(int64_t{1}))}), Tuple({Get(s->LocalAt(30), Value(int64_t{0})), Get(s->LocalAt(30), Value(int64_t{1}))})}), ([&]() -> Value { auto v18151 = ([&]() -> Value { auto v18152 = s->LocalAt(3); return Binary("Add", v18152, Get(s->LocalAt(11), Value(int64_t{2}))); }()); return Binary("Add", v18151, Get(s->LocalAt(30), Value(int64_t{2}))); }())}), false); return Call(c, fn18149, std::move(args18150)); }());
}
}
}
for (const auto& item18153 : Iterate(s->LocalAt(34))) {
auto unpack18154 = Iterate(item18153);
ValidateUnpack(unpack18154, 2, false);
s->SetAt(32, unpack18154.at(0));
s->SetAt(33, unpack18154.at(1));
auto v18155 = Tuple({List({}), s->LocalAt(23)});
auto unpack18156 = Iterate(v18155);
ValidateUnpack(unpack18156, 2, false);
s->SetAt(28, unpack18156.at(0));
s->SetAt(5, unpack18156.at(1));
for (const auto& item18157 : Iterate(s->LocalAt(32))) {
auto unpack18158 = Iterate(item18157);
ValidateUnpack(unpack18158, 2, false);
s->SetAt(35, unpack18158.at(0));
s->SetAt(21, unpack18158.at(1));
auto v18159 = s->LocalAt(28);
s->SetAt(28, Inplace("Add", v18159, ([&]() -> Value { auto v18160 = ([&]() -> Value { auto fn18161 = s->Global("_walk"); Arguments args18162; args18162.positional.reserve(2); args18162.Add(s->LocalAt(5), false); args18162.Add(s->LocalAt(35), false); return Call(c, fn18161, std::move(args18162)); }()); return Binary("Add", v18160, s->LocalAt(21)); }())));
auto v18163 = s->LocalAt(35);
s->SetAt(5, v18163);
}
auto v18164 = s->LocalAt(28);
s->SetAt(28, Inplace("Add", v18164, ([&]() -> Value { auto fn18165 = s->Global("_return"); Arguments args18166; args18166.Add(s->LocalAt(5), false); return Call(c, fn18165, std::move(args18166)); }())));
if (static_cast<bool>(([&]() -> Value { auto v18167 = ([&]() -> Value { auto fn18169 = s->Global("len"); Arguments args18170; args18170.Add(s->LocalAt(28), false); return Call(c, fn18169, std::move(args18170)); }()); Value v18168; v18168 = ([&]() -> Value { auto v18171 = s->LocalAt(14); return Binary("Sub", v18171, s->LocalAt(19)); }()); if (!static_cast<bool>(Binary("Gt", v18167, v18168))) return Value(false); v18167 = v18168; return Value(true); }()))) {
continue;
}
auto v18172 = s->LocalAt(28);
s->SetAt(28, Inplace("Add", v18172, ([&]() -> Value { auto v18173 = List({List({Value("PASS")})}); return Binary("Mult", v18173, ([&]() -> Value { auto v18174 = ([&]() -> Value { auto v18175 = s->LocalAt(14); return Binary("Sub", v18175, s->LocalAt(19)); }()); return Binary("Sub", v18174, ([&]() -> Value { auto fn18176 = s->Global("len"); Arguments args18177; args18177.Add(s->LocalAt(28), false); return Call(c, fn18176, std::move(args18177)); }())); }())); }())));
auto v18178 = Tuple({s->LocalAt(19), ([&]() -> Value { auto fn18179 = s->Global("tuple"); Arguments args18180; args18180.Add(([&]() -> Value { auto comp18181 = std::make_shared<Scope>(); comp18181->globals = s->globals; comp18181->parent = s; static constexpr const char* comp18181_names[] = {"c"}; comp18181->PrepareSlots(comp18181_names); auto result18182 = List(); for (const auto& item18183 : Iterate(s->LocalAt(28))) { comp18181->SetAt(0, item18183); result18182.node()->sequence.push_back(([&]() -> Value { auto fn18184 = comp18181->Global("tuple"); Arguments args18185; args18185.Add(comp18181->LocalAt(0), false); return Call(c, fn18184, std::move(args18185)); }())); } return result18182; }()), false); return Call(c, fn18179, std::move(args18180)); }())});
s->SetAt(16, v18178);
if (static_cast<bool>(([&]() -> Value { auto v18186 = s->LocalAt(16); Value v18187; v18187 = s->LocalAt(31); if (!static_cast<bool>(Binary("NotIn", v18186, v18187))) return Value(false); v18186 = v18187; return Value(true); }()))) {
(void)([&]() -> Value { auto fn18188 = Attribute(s->LocalAt(31), "add"); Arguments args18189; args18189.Add(s->LocalAt(16), false); return Call(c, fn18188, std::move(args18189)); }());
(void)([&]() -> Value { auto fn18190 = Attribute(s->LocalAt(27), "append"); Arguments args18191; args18191.Add(Tuple({([&]() -> Value { auto v18192 = s->LocalAt(33); return Binary("Sub", v18192, s->LocalAt(18)); }()), s->LocalAt(19), s->LocalAt(28), ([&]() -> Value { auto fn18193 = s->Global("len"); Arguments args18194; args18194.Add(s->LocalAt(32), false); return Call(c, fn18193, std::move(args18194)); }())}), false); return Call(c, fn18190, std::move(args18191)); }());
}
}
}
(void)([&]() -> Value { auto fn18195 = Attribute(s->LocalAt(27), "sort"); Arguments args18196; args18196.Keyword("key", Define(&Code_ec7c35cd6adf702bbe71, s, Signature{{"p"}, {}, {}, {}, "", "", ([]() -> std::span<const char* const> { static constexpr const char* names[] = {"p"}; return names; }())}, true, "<lambda>")); return Call(c, fn18195, std::move(args18196)); }());
auto v18197 = Slice(([&]() -> Value { auto comp18198 = std::make_shared<Scope>(); comp18198->globals = s->globals; comp18198->parent = s; static constexpr const char* comp18198_names[] = {"p"}; comp18198->PrepareSlots(comp18198_names); auto result18199 = List(); for (const auto& item18200 : Iterate(s->LocalAt(27))) { comp18198->SetAt(0, item18200); if (!static_cast<bool>(([&]() -> Value { auto v18201 = ([&]() -> Value { auto v18202 = Get(comp18198->LocalAt(0), Value(int64_t{3})); Value v18203; v18203 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v18202, v18203))) return Value(false); v18202 = v18203; return Value(true); }()); if (!static_cast<bool>(v18201)) return v18201; v18201 = ([&]() -> Value { auto v18204 = Get(comp18198->LocalAt(0), Value(int64_t{0})); Value v18205; v18205 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v18204, v18205))) return Value(false); v18204 = v18205; return Value(true); }()); return v18201; }()))) continue; result18199.node()->sequence.push_back(comp18198->LocalAt(0)); } return result18199; }()), Value{}, Value(int64_t{2}), Value{});
s->SetAt(6, v18197);
auto v18206 = ([&]() -> Value { auto v18207 = s->LocalAt(6); return Binary("Add", v18207, ([&]() -> Value { auto comp18208 = std::make_shared<Scope>(); comp18208->globals = s->globals; comp18208->parent = s; static constexpr const char* comp18208_names[] = {"p"}; comp18208->PrepareSlots(comp18208_names); auto result18209 = List(); for (const auto& item18210 : Iterate(s->LocalAt(27))) { comp18208->SetAt(0, item18210); if (!static_cast<bool>(([&]() -> Value { auto v18211 = comp18208->LocalAt(0); Value v18212; v18212 = comp18208->Captured("direct"); if (!static_cast<bool>(Binary("NotIn", v18211, v18212))) return Value(false); v18211 = v18212; return Value(true); }()))) continue; result18209.node()->sequence.push_back(comp18208->LocalAt(0)); } return result18209; }())); }());
s->SetAt(4, v18206);
return Slice(s->LocalAt(4), Value{}, s->LocalAt(17), Value{});
return {};
}
}  // namespace kagg::opponents::compiled
