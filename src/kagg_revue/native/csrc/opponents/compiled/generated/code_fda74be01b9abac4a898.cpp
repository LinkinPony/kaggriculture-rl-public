// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_fda74be01b9abac4a898(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "commands", "item", "native_need", "next_action", "obs", "offset", "op", "order", "planned", "quantity", "stock"};
s->PrepareSlots(s_names);
auto v9008 = ([&]() -> Value { auto fn9009 = s->Global("dict"); Arguments args9010; args9010.Add(([&]() -> Value { auto fn9011 = s->Global("projected_shed"); Arguments args9012; args9012.positional.reserve(2); args9012.Add(s->LocalAt(0), false); args9012.Add(([&]() -> Value { auto fn9013 = s->Global("FarmView"); Arguments args9014; args9014.Add(s->LocalAt(5), false); return Call(c, fn9013, std::move(args9014)); }()), false); return Call(c, fn9011, std::move(args9012)); }()), false); return Call(c, fn9009, std::move(args9010)); }());
s->SetAt(11, v9008);
for (const auto& item9015 : Iterate(([&]() -> Value { auto fn9016 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args9017; args9017.positional.reserve(2); args9017.Add(Value("market"), false); args9017.Add(List({}), false); return CallDictionaryGet(c, fn9016, std::move(args9017)); }()))) {
s->SetAt(8, item9015);
if (static_cast<bool>(([&]() -> Value { auto v9018 = ([&]() -> Value { auto fn9020 = s->Global("len"); Arguments args9021; args9021.Add(s->LocalAt(8), false); return Call(c, fn9020, std::move(args9021)); }()); Value v9019; v9019 = Value(int64_t{3}); if (!static_cast<bool>(Binary("Lt", v9018, v9019))) return Value(false); v9018 = v9019; return Value(true); }()))) {
continue;
}
auto v9022 = Slice(s->LocalAt(8), Value{}, Value(int64_t{3}), Value{});
auto unpack9023 = Iterate(v9022);
ValidateUnpack(unpack9023, 3, false);
s->SetAt(7, unpack9023.at(0));
s->SetAt(2, unpack9023.at(1));
s->SetAt(10, unpack9023.at(2));
auto v9024 = ([&]() -> Value { auto fn9025 = s->Global("max"); Arguments args9026; args9026.positional.reserve(2); args9026.Add(Value(int64_t{0}), false); args9026.Add(([&]() -> Value { auto fn9027 = s->Global("int"); Arguments args9028; args9028.Add(s->LocalAt(10), false); return Call(c, fn9027, std::move(args9028)); }()), false); return Call(c, fn9025, std::move(args9026)); }());
s->SetAt(10, v9024);
if (static_cast<bool>(([&]() -> Value { auto v9029 = s->LocalAt(7); Value v9030; v9030 = Value("SELL"); if (!static_cast<bool>(Binary("Eq", v9029, v9030))) return Value(false); v9029 = v9030; return Value(true); }()))) {
auto v9031 = ([&]() -> Value { auto fn9032 = s->Global("max"); Arguments args9033; args9033.positional.reserve(2); args9033.Add(Value(int64_t{0}), false); args9033.Add(([&]() -> Value { auto v9034 = ([&]() -> Value { auto fn9035 = PrepareDictionaryGet(s->LocalAt(11)); Arguments args9036; args9036.positional.reserve(2); args9036.Add(s->LocalAt(2), false); args9036.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn9035, std::move(args9036)); }()); return Binary("Sub", v9034, s->LocalAt(10)); }()), false); return Call(c, fn9032, std::move(args9033)); }());
Put(s->LocalAt(11), s->LocalAt(2), v9031);
}
else {
if (static_cast<bool>(([&]() -> Value { auto v9037 = s->LocalAt(7); Value v9038; v9038 = Tuple({Value("BUY_PRODUCT"), Value("BUY_ANIMAL")}); if (!static_cast<bool>(Binary("In", v9037, v9038))) return Value(false); v9037 = v9038; return Value(true); }()))) {
auto v9039 = ([&]() -> Value { auto v9040 = ([&]() -> Value { auto fn9041 = PrepareDictionaryGet(s->LocalAt(11)); Arguments args9042; args9042.positional.reserve(2); args9042.Add(s->LocalAt(2), false); args9042.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn9041, std::move(args9042)); }()); return Binary("Add", v9040, ([&]() -> Value { auto fn9043 = s->Global("min"); Arguments args9044; args9044.positional.reserve(2); args9044.Add(s->LocalAt(10), false); args9044.Add(([&]() -> Value { auto fn9045 = s->Global("max"); Arguments args9046; args9046.positional.reserve(2); args9046.Add(Value(int64_t{0}), false); args9046.Add(([&]() -> Value { auto v9047 = Value(int64_t{100}); return Binary("Sub", v9047, ([&]() -> Value { auto fn9048 = s->Global("sum"); Arguments args9049; args9049.Add(([&]() -> Value { auto fn9050 = Attribute(s->LocalAt(11), "values"); Arguments args9051; return Call(c, fn9050, std::move(args9051)); }()), false); return Call(c, fn9048, std::move(args9049)); }())); }()), false); return Call(c, fn9045, std::move(args9046)); }()), false); return Call(c, fn9043, std::move(args9044)); }())); }());
Put(s->LocalAt(11), s->LocalAt(2), v9039);
}
}
}
auto v9052 = (static_cast<bool>(([&]() -> Value { auto v9053 = ([&]() -> Value { auto v9055 = s->LocalAt(6); return Binary("Add", v9055, Value(int64_t{1})); }()); Value v9054; v9054 = ([&]() -> Value { auto fn9056 = s->Global("len"); Arguments args9057; args9057.Add(s->LocalAt(9), false); return Call(c, fn9056, std::move(args9057)); }()); if (!static_cast<bool>(Binary("Lt", v9053, v9054))) return Value(false); v9053 = v9054; return Value(true); }())) ? Get(s->LocalAt(9), ([&]() -> Value { auto v9058 = s->LocalAt(6); return Binary("Add", v9058, Value(int64_t{1})); }())) : ([&]() -> Value { auto dict9059 = Dict(); return dict9059; }()));
s->SetAt(4, v9052);
auto v9060 = ([&]() -> Value { Arguments args9061; args9061.Add(([&]() -> Value { auto v9062 = ([&]() -> Value { auto fn9063 = PrepareDictionaryGet(s->LocalAt(4)); Arguments args9064; args9064.Add(Value("farmer"), false); return CallDictionaryGet(c, fn9063, std::move(args9064)); }()); if (static_cast<bool>(v9062)) return v9062; v9062 = List({Value("PASS")}); return v9062; }()), false); args9061.Add(([&]() -> Value { auto v9065 = ([&]() -> Value { auto fn9066 = PrepareDictionaryGet(s->LocalAt(4)); Arguments args9067; args9067.Add(Value("hands"), false); return CallDictionaryGet(c, fn9066, std::move(args9067)); }()); if (static_cast<bool>(v9065)) return v9065; v9065 = List({}); return v9065; }()), true); return List(std::move(args9061.positional)); }());
s->SetAt(1, v9060);
auto v9068 = ([&]() -> Value { auto fn9069 = s->Global("sum"); Arguments args9070; args9070.Add(([&]() -> Value { auto comp9071 = std::make_shared<Scope>(); comp9071->globals = s->globals; comp9071->parent = s; static constexpr const char* comp9071_names[] = {"c"}; comp9071->PrepareSlots(comp9071_names); auto result9072 = List(); for (const auto& item9073 : Iterate(s->LocalAt(1))) { comp9071->SetAt(0, item9073); if (!static_cast<bool>(([&]() -> Value { auto v9074 = ([&]() -> Value { auto v9075 = ([&]() -> Value { auto fn9077 = comp9071->Global("len"); Arguments args9078; args9078.Add(comp9071->LocalAt(0), false); return Call(c, fn9077, std::move(args9078)); }()); Value v9076; v9076 = Value(int64_t{1}); if (!static_cast<bool>(Binary("Gt", v9075, v9076))) return Value(false); v9075 = v9076; return Value(true); }()); if (!static_cast<bool>(v9074)) return v9074; v9074 = ([&]() -> Value { auto v9079 = Slice(comp9071->LocalAt(0), Value{}, Value(int64_t{2}), Value{}); Value v9080; v9080 = List({Value("PICKUP"), Value("FERTILIZER")}); if (!static_cast<bool>(Binary("Eq", v9079, v9080))) return Value(false); v9079 = v9080; return Value(true); }()); return v9074; }()))) continue; result9072.node()->sequence.push_back(([&]() -> Value { auto fn9081 = comp9071->Global("max"); Arguments args9082; args9082.positional.reserve(2); args9082.Add(Value(int64_t{0}), false); args9082.Add((static_cast<bool>(([&]() -> Value { auto v9083 = ([&]() -> Value { auto fn9085 = comp9071->Global("len"); Arguments args9086; args9086.Add(comp9071->LocalAt(0), false); return Call(c, fn9085, std::move(args9086)); }()); Value v9084; v9084 = Value(int64_t{2}); if (!static_cast<bool>(Binary("Gt", v9083, v9084))) return Value(false); v9083 = v9084; return Value(true); }())) ? ([&]() -> Value { auto fn9087 = comp9071->Global("int"); Arguments args9088; args9088.Add(Get(comp9071->LocalAt(0), Value(int64_t{2})), false); return Call(c, fn9087, std::move(args9088)); }()) : Value(int64_t{1})), false); return Call(c, fn9081, std::move(args9082)); }())); } return result9072; }()), false); return Call(c, fn9069, std::move(args9070)); }());
s->SetAt(3, v9068);
auto v9089 = ([&]() -> Value { auto fn9090 = s->Global("max"); Arguments args9091; args9091.positional.reserve(2); args9091.Add(Value(int64_t{10}), false); args9091.Add(([&]() -> Value { auto v9092 = ([&]() -> Value { auto v9093 = Value(int64_t{10}); return Binary("Add", v9093, s->LocalAt(3)); }()); return Binary("Sub", v9092, ([&]() -> Value { auto fn9094 = s->Global("max"); Arguments args9095; args9095.positional.reserve(2); args9095.Add(Value(int64_t{0}), false); args9095.Add(([&]() -> Value { auto fn9096 = PrepareDictionaryGet(s->LocalAt(11)); Arguments args9097; args9097.positional.reserve(2); args9097.Add(Value("FERTILIZER"), false); args9097.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn9096, std::move(args9097)); }()), false); return Call(c, fn9094, std::move(args9095)); }())); }()), false); return Call(c, fn9090, std::move(args9091)); }());
s->SetAt(10, v9089);
if (static_cast<bool>(([&]() -> Value { auto v9098 = s->LocalAt(10); Value v9099; v9099 = ([&]() -> Value { auto fn9100 = s->Global("max"); Arguments args9101; args9101.positional.reserve(2); args9101.Add(Value(int64_t{0}), false); args9101.Add(([&]() -> Value { auto v9102 = Value(int64_t{100}); return Binary("Sub", v9102, ([&]() -> Value { auto fn9103 = s->Global("sum"); Arguments args9104; args9104.Add(([&]() -> Value { auto fn9105 = Attribute(s->LocalAt(11), "values"); Arguments args9106; return Call(c, fn9105, std::move(args9106)); }()), false); return Call(c, fn9103, std::move(args9104)); }())); }()), false); return Call(c, fn9100, std::move(args9101)); }()); if (!static_cast<bool>(Binary("Gt", v9098, v9099))) return Value(false); v9098 = v9099; return Value(true); }()))) {
auto v9107 = s->Global("_R70_REPORT");
auto v9108 = Value("parent_input_capacity_declines");
auto v9109 = Get(v9107, v9108);
Put(v9107, v9108, Inplace("Add", v9109, Value(int64_t{1})));
return Value(int64_t{10});
}
if (static_cast<bool>(([&]() -> Value { auto v9110 = s->LocalAt(10); Value v9111; v9111 = Value(int64_t{10}); if (!static_cast<bool>(Binary("Gt", v9110, v9111))) return Value(false); v9110 = v9111; return Value(true); }()))) {
auto v9112 = s->Global("_R70_REPORT");
auto v9113 = Value("parent_input_guard_turns");
auto v9114 = Get(v9112, v9113);
Put(v9112, v9113, Inplace("Add", v9114, Value(int64_t{1})));
auto v9115 = s->Global("_R70_REPORT");
auto v9116 = Value("parent_input_guard_extra_units");
auto v9117 = Get(v9115, v9116);
Put(v9115, v9116, Inplace("Add", v9117, ([&]() -> Value { auto v9118 = s->LocalAt(10); return Binary("Sub", v9118, Value(int64_t{10})); }())));
}
return s->LocalAt(10);
return {};
}
}  // namespace kagg::opponents::compiled
