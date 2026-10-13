// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_465f0388e34b6c2dc127(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "actor", "carried", "command", "commands", "farm", "hungry", "obs", "orders", "private", "quote", "result", "shortage", "state", "stock", "targets"};
s->PrepareSlots(s_names);
if (static_cast<bool>(([&]() -> Value { auto v7107 = Unary("Not", Get(s->LocalAt(13), Value("workers"))); if (static_cast<bool>(v7107)) return v7107; v7107 = ([&]() -> Value { auto v7108 = ([&]() -> Value { auto v7110 = ([&]() -> Value { auto fn7111 = s->Global("int"); Arguments args7112; args7112.Add(Get(s->LocalAt(7), Value("step")), false); return Call(c, fn7111, std::move(args7112)); }()); return Binary("Mod", v7110, Value(int64_t{24})); }()); Value v7109; v7109 = Value(int64_t{14}); if (!static_cast<bool>(Binary("Gt", v7108, v7109))) return Value(false); v7108 = v7109; return Value(true); }()); return v7107; }()))) {
return s->LocalAt(0);
}
auto v7113 = ([&]() -> Value { auto fn7114 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args7115; args7115.positional.reserve(2); args7115.Add(Value("market"), false); args7115.Add(List({}), false); return CallDictionaryGet(c, fn7114, std::move(args7115)); }());
s->SetAt(8, v7113);
if (static_cast<bool>(([&]() -> Value { auto v7116 = ([&]() -> Value { auto fn7118 = s->Global("len"); Arguments args7119; args7119.Add(s->LocalAt(8), false); return Call(c, fn7118, std::move(args7119)); }()); Value v7117; v7117 = s->Global("MAX_ORDERS"); if (!static_cast<bool>(Binary("GtE", v7116, v7117))) return Value(false); v7116 = v7117; return Value(true); }()))) {
return s->LocalAt(0);
}
if (static_cast<bool>(([&]() -> Value { auto comp7120 = std::make_shared<Scope>(); comp7120->globals = s->globals; comp7120->parent = s; static constexpr const char* comp7120_names[] = {"o"}; comp7120->PrepareSlots(comp7120_names); auto result7121 = List(); for (const auto& item7122 : Iterate(s->LocalAt(8))) { comp7120->SetAt(0, item7122); if (static_cast<bool>(([&]() -> Value { auto v7123 = comp7120->LocalAt(0); if (!static_cast<bool>(v7123)) return v7123; v7123 = ([&]() -> Value { auto v7124 = ([&]() -> Value { auto v7125 = Get(comp7120->LocalAt(0), Value(int64_t{0})); Value v7126; v7126 = Tuple({Value("HIRE"), Value("BUY_LAND"), Value("BUY_ANIMAL"), Value("BUY_PRODUCT"), Value("BUY_SEED")}); if (!static_cast<bool>(Binary("In", v7125, v7126))) return Value(false); v7125 = v7126; return Value(true); }()); if (static_cast<bool>(v7124)) return v7124; v7124 = ([&]() -> Value { auto v7127 = ([&]() -> Value { auto v7128 = ([&]() -> Value { auto fn7130 = comp7120->Global("len"); Arguments args7131; args7131.Add(comp7120->LocalAt(0), false); return Call(c, fn7130, std::move(args7131)); }()); Value v7129; v7129 = Value(int64_t{1}); if (!static_cast<bool>(Binary("Gt", v7128, v7129))) return Value(false); v7128 = v7129; return Value(true); }()); if (!static_cast<bool>(v7127)) return v7127; v7127 = ([&]() -> Value { auto v7132 = Get(comp7120->LocalAt(0), Value(int64_t{1})); Value v7133; v7133 = Value("WHEAT"); if (!static_cast<bool>(Binary("Eq", v7132, v7133))) return Value(false); v7132 = v7133; return Value(true); }()); return v7127; }()); return v7124; }()); return v7123; }()))) return Value(true); } return Value(false); }()))) {
return s->LocalAt(0);
}
auto v7134 = Get(Get(s->LocalAt(7), Value("farms")), Get(s->LocalAt(7), Value("player")));
s->SetAt(5, v7134);
auto v7135 = Get(s->LocalAt(7), Value("private"));
s->SetAt(9, v7135);
auto v7136 = Value(int64_t{0});
s->SetAt(6, v7136);
s->SetAt(2, v7136);
auto v7137 = ([&]() -> Value { auto v7138 = List({([&]() -> Value { auto v7139 = ([&]() -> Value { auto fn7140 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args7141; args7141.Add(Value("farmer"), false); return CallDictionaryGet(c, fn7140, std::move(args7141)); }()); if (static_cast<bool>(v7139)) return v7139; v7139 = List({Value("PASS")}); return v7139; }())}); return Binary("Add", v7138, ([&]() -> Value { auto fn7142 = s->Global("list"); Arguments args7143; args7143.Add(([&]() -> Value { auto v7144 = ([&]() -> Value { auto fn7145 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args7146; args7146.Add(Value("hands"), false); return CallDictionaryGet(c, fn7145, std::move(args7146)); }()); if (static_cast<bool>(v7144)) return v7144; v7144 = List({}); return v7144; }()), false); return Call(c, fn7142, std::move(args7143)); }())); }());
s->SetAt(4, v7137);
for (const auto& item7147 : Iterate(([&]() -> Value { auto fn7148 = Attribute(Get(s->LocalAt(13), Value("workers")), "items"); Arguments args7149; return Call(c, fn7148, std::move(args7149)); }()))) {
auto unpack7150 = Iterate(item7147);
ValidateUnpack(unpack7150, 2, false);
s->SetAt(1, unpack7150.at(0));
s->SetAt(15, unpack7150.at(1));
auto v7151 = Get(s->LocalAt(4), s->LocalAt(1));
s->SetAt(3, v7151);
if (static_cast<bool>(([&]() -> Value { auto v7152 = ([&]() -> Value { auto v7153 = s->LocalAt(3); Value v7154; v7154 = List({Value("FEED")}); if (!static_cast<bool>(Binary("Eq", v7153, v7154))) return Value(false); v7153 = v7154; return Value(true); }()); if (static_cast<bool>(v7152)) return v7152; v7152 = ([&]() -> Value { auto v7155 = Slice(s->LocalAt(3), Value{}, Value(int64_t{2}), Value{}); Value v7156; v7156 = List({Value("PICKUP"), Value("WHEAT")}); if (!static_cast<bool>(Binary("Eq", v7155, v7156))) return Value(false); v7155 = v7156; return Value(true); }()); return v7152; }()))) {
return s->LocalAt(0);
}
auto v7157 = s->LocalAt(2);
s->SetAt(2, Inplace("Add", v7157, ([&]() -> Value { auto fn7158 = PrepareDictionaryGet(Get(Get(s->LocalAt(9), Value("inventories")), s->LocalAt(1))); Arguments args7159; args7159.positional.reserve(2); args7159.Add(Value("WHEAT"), false); args7159.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn7158, std::move(args7159)); }())));
auto v7160 = s->LocalAt(6);
s->SetAt(6, Inplace("Add", v7160, ([&]() -> Value { auto fn7161 = s->Global("sum"); Arguments args7162; args7162.Add(([&]() -> Value { auto comp7163 = std::make_shared<Scope>(); comp7163->globals = s->globals; comp7163->parent = s; static constexpr const char* comp7163_names[] = {"x", "y"}; comp7163->PrepareSlots(comp7163_names); auto result7164 = List(); for (const auto& item7165 : Iterate(s->LocalAt(15))) { auto unpack7166 = Iterate(item7165); ValidateUnpack(unpack7166, 2, false); comp7163->SetAt(0, unpack7166.at(0)); comp7163->SetAt(1, unpack7166.at(1)); result7164.node()->sequence.push_back(([&]() -> Value { auto v7167 = ([&]() -> Value { auto fn7168 = comp7163->Global("isinstance"); Arguments args7169; args7169.positional.reserve(2); args7169.Add(Get(Get(Get(comp7163->Captured("farm"), Value("tiles")), comp7163->LocalAt(1)), comp7163->LocalAt(0)), false); args7169.Add(comp7163->Global("dict"), false); return Call(c, fn7168, std::move(args7169)); }()); if (!static_cast<bool>(v7167)) return v7167; v7167 = ([&]() -> Value { auto v7170 = ([&]() -> Value { auto fn7172 = PrepareDictionaryGet(Get(Get(Get(comp7163->Captured("farm"), Value("tiles")), comp7163->LocalAt(1)), comp7163->LocalAt(0))); Arguments args7173; args7173.Add(Value("animal"), false); return CallDictionaryGet(c, fn7172, std::move(args7173)); }()); Value v7171; v7171 = Value("SHEEP"); if (!static_cast<bool>(Binary("Eq", v7170, v7171))) return Value(false); v7170 = v7171; return Value(true); }()); if (!static_cast<bool>(v7167)) return v7167; v7167 = Unary("Not", ([&]() -> Value { auto fn7174 = PrepareDictionaryGet(Get(Get(Get(comp7163->Captured("farm"), Value("tiles")), comp7163->LocalAt(1)), comp7163->LocalAt(0))); Arguments args7175; args7175.Add(Value("fed_today"), false); return CallDictionaryGet(c, fn7174, std::move(args7175)); }())); return v7167; }())); } return result7164; }()), false); return Call(c, fn7161, std::move(args7162)); }())));
}
auto v7176 = ([&]() -> Value { auto fn7177 = s->Global("projected_shed"); Arguments args7178; args7178.positional.reserve(2); args7178.Add(s->LocalAt(0), false); args7178.Add(([&]() -> Value { auto fn7179 = s->Global("FarmView"); Arguments args7180; args7180.Add(s->LocalAt(7), false); return Call(c, fn7179, std::move(args7180)); }()), false); return Call(c, fn7177, std::move(args7178)); }());
s->SetAt(14, v7176);
auto v7181 = ([&]() -> Value { auto v7182 = ([&]() -> Value { auto v7183 = s->LocalAt(6); return Binary("Sub", v7183, s->LocalAt(2)); }()); return Binary("Sub", v7182, ([&]() -> Value { auto fn7184 = PrepareDictionaryGet(s->LocalAt(14)); Arguments args7185; args7185.positional.reserve(2); args7185.Add(Value("WHEAT"), false); args7185.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn7184, std::move(args7185)); }())); }());
s->SetAt(12, v7181);
if (static_cast<bool>(([&]() -> Value { auto v7186 = Unary("Not", ([&]() -> Value { auto v7187 = Value(int64_t{0}); Value v7188; v7188 = s->LocalAt(12); if (!static_cast<bool>(Binary("Lt", v7187, v7188))) return Value(false); v7187 = v7188; v7188 = Value(int64_t{6}); if (!static_cast<bool>(Binary("LtE", v7187, v7188))) return Value(false); v7187 = v7188; return Value(true); }())); if (static_cast<bool>(v7186)) return v7186; v7186 = ([&]() -> Value { auto v7189 = ([&]() -> Value { auto v7191 = ([&]() -> Value { auto fn7192 = PrepareDictionaryGet(s->LocalAt(13)); Arguments args7193; args7193.positional.reserve(2); args7193.Add(Value("rescue_today"), false); args7193.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn7192, std::move(args7193)); }()); return Binary("Add", v7191, s->LocalAt(12)); }()); Value v7190; v7190 = Value(int64_t{6}); if (!static_cast<bool>(Binary("Gt", v7189, v7190))) return Value(false); v7189 = v7190; return Value(true); }()); return v7186; }()))) {
return s->LocalAt(0);
}
auto v7194 = ([&]() -> Value { auto fn7195 = s->Global("int"); Arguments args7196; args7196.Add(Get(Get(Get(s->LocalAt(7), Value("market")), Value("prices")), Value("WHEAT")), false); return Call(c, fn7195, std::move(args7196)); }());
s->SetAt(10, v7194);
if (static_cast<bool>(([&]() -> Value { auto v7197 = ([&]() -> Value { auto v7198 = s->LocalAt(10); Value v7199; v7199 = Value(int64_t{1}); if (!static_cast<bool>(Binary("Lt", v7198, v7199))) return Value(false); v7198 = v7199; return Value(true); }()); if (static_cast<bool>(v7197)) return v7197; v7197 = ([&]() -> Value { auto v7200 = Get(s->LocalAt(5), Value("money")); Value v7201; v7201 = ([&]() -> Value { auto v7202 = Value(int64_t{1000}); return Binary("Add", v7202, ([&]() -> Value { auto v7203 = s->LocalAt(12); return Binary("Mult", v7203, ([&]() -> Value { auto v7204 = s->LocalAt(10); return Binary("Add", v7204, Value(int64_t{10})); }())); }())); }()); if (!static_cast<bool>(Binary("Lt", v7200, v7201))) return Value(false); v7200 = v7201; return Value(true); }()); if (static_cast<bool>(v7197)) return v7197; v7197 = ([&]() -> Value { auto v7205 = ([&]() -> Value { auto v7207 = ([&]() -> Value { auto fn7208 = s->Global("sum"); Arguments args7209; args7209.Add(([&]() -> Value { auto fn7210 = Attribute(s->LocalAt(14), "values"); Arguments args7211; return Call(c, fn7210, std::move(args7211)); }()), false); return Call(c, fn7208, std::move(args7209)); }()); return Binary("Add", v7207, s->LocalAt(12)); }()); Value v7206; v7206 = Value(int64_t{100}); if (!static_cast<bool>(Binary("Gt", v7205, v7206))) return Value(false); v7205 = v7206; return Value(true); }()); return v7197; }()))) {
return s->LocalAt(0);
}
auto v7212 = ([&]() -> Value { auto fn7213 = Attribute(s->Global("copy"), "deepcopy"); Arguments args7214; args7214.Add(s->LocalAt(0), false); return Call(c, fn7213, std::move(args7214)); }());
s->SetAt(11, v7212);
(void)([&]() -> Value { auto fn7215 = Attribute(Get(s->LocalAt(11), Value("market")), "append"); Arguments args7216; args7216.Add(List({Value("BUY_PRODUCT"), Value("WHEAT"), s->LocalAt(12)}), false); return Call(c, fn7215, std::move(args7216)); }());
auto v7217 = ([&]() -> Value { auto v7218 = ([&]() -> Value { auto fn7219 = PrepareDictionaryGet(s->LocalAt(13)); Arguments args7220; args7220.positional.reserve(2); args7220.Add(Value("rescue_today"), false); args7220.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn7219, std::move(args7220)); }()); return Binary("Add", v7218, s->LocalAt(12)); }());
Put(s->LocalAt(13), Value("rescue_today"), v7217);
auto v7221 = s->Global("_V233_REPORT");
auto v7222 = Value("sheep_rescue_feed_requests");
auto v7223 = Get(v7221, v7222);
Put(v7221, v7222, Inplace("Add", v7223, s->LocalAt(12)));
return s->LocalAt(11);
return {};
}
}  // namespace kagg::opponents::compiled
