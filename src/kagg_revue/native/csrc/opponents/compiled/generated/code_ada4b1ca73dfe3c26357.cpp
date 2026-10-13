// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_ada4b1ca73dfe3c26357(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "changed", "cursor", "index", "order", "orders", "original", "previous"};
s->PrepareSlots(s_names);
auto v5179 = Slice(([&]() -> Value { auto fn5180 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args5181; args5181.positional.reserve(2); args5181.Add(Value("market"), false); args5181.Add(List({}), false); return CallDictionaryGet(c, fn5180, std::move(args5181)); }()), Value{}, s->Global("MAX_ORDERS"), Value{});
s->SetAt(6, v5179);
auto v5182 = ([&]() -> Value { auto comp5183 = std::make_shared<Scope>(); comp5183->globals = s->globals; comp5183->parent = s; static constexpr const char* comp5183_names[] = {"o"}; comp5183->PrepareSlots(comp5183_names); auto result5184 = List(); for (const auto& item5185 : Iterate(s->LocalAt(6))) { comp5183->SetAt(0, item5185); if (!static_cast<bool>(([&]() -> Value { auto v5186 = comp5183->LocalAt(0); if (!static_cast<bool>(v5186)) return v5186; v5186 = ([&]() -> Value { auto v5187 = ([&]() -> Value { auto v5188 = Get(comp5183->LocalAt(0), Value(int64_t{0})); Value v5189; v5189 = Tuple({Value("HIRE"), Value("BUY_LAND")}); if (!static_cast<bool>(Binary("In", v5188, v5189))) return Value(false); v5188 = v5189; return Value(true); }()); if (static_cast<bool>(v5187)) return v5187; v5187 = ([&]() -> Value { auto v5190 = ([&]() -> Value { auto v5191 = ([&]() -> Value { auto fn5193 = comp5183->Global("len"); Arguments args5194; args5194.Add(comp5183->LocalAt(0), false); return Call(c, fn5193, std::move(args5194)); }()); Value v5192; v5192 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v5191, v5192))) return Value(false); v5191 = v5192; return Value(true); }()); if (!static_cast<bool>(v5190)) return v5190; v5190 = ([&]() -> Value { auto v5195 = ([&]() -> Value { auto fn5197 = comp5183->Global("int"); Arguments args5198; args5198.Add(Get(comp5183->LocalAt(0), Value(int64_t{2})), false); return Call(c, fn5197, std::move(args5198)); }()); Value v5196; v5196 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v5195, v5196))) return Value(false); v5195 = v5196; return Value(true); }()); return v5190; }()); return v5187; }()); return v5186; }()))) continue; result5184.node()->sequence.push_back(([&]() -> Value { auto fn5199 = comp5183->Global("list"); Arguments args5200; args5200.Add(comp5183->LocalAt(0), false); return Call(c, fn5199, std::move(args5200)); }())); } return result5184; }());
s->SetAt(5, v5182);
for (const auto& item5201 : Iterate(([&]() -> Value { auto fn5202 = s->Global("range"); Arguments args5203; args5203.Add(([&]() -> Value { auto fn5204 = s->Global("len"); Arguments args5205; args5205.Add(s->LocalAt(5), false); return Call(c, fn5204, std::move(args5205)); }()), false); return Call(c, fn5202, std::move(args5203)); }()))) {
s->SetAt(3, item5201);
auto v5206 = Get(s->LocalAt(5), s->LocalAt(3));
s->SetAt(4, v5206);
if (static_cast<bool>(([&]() -> Value { auto v5207 = Get(s->LocalAt(4), Value(int64_t{0})); Value v5208; v5208 = Value("SELL"); if (!static_cast<bool>(Binary("NotEq", v5207, v5208))) return Value(false); v5207 = v5208; return Value(true); }()))) {
continue;
}
auto v5209 = s->LocalAt(3);
s->SetAt(2, v5209);
while (static_cast<bool>(([&]() -> Value { auto v5210 = s->LocalAt(2); Value v5211; v5211 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v5210, v5211))) return Value(false); v5210 = v5211; return Value(true); }()))) {
auto v5212 = Get(s->LocalAt(5), ([&]() -> Value { auto v5213 = s->LocalAt(2); return Binary("Sub", v5213, Value(int64_t{1})); }()));
s->SetAt(7, v5212);
if (static_cast<bool>(([&]() -> Value { auto v5214 = Get(s->LocalAt(7), Value(int64_t{0})); Value v5215; v5215 = Value("SELL"); if (!static_cast<bool>(Binary("Eq", v5214, v5215))) return Value(false); v5214 = v5215; return Value(true); }()))) {
break;
}
if (static_cast<bool>(([&]() -> Value { auto v5216 = ([&]() -> Value { auto v5217 = Get(s->LocalAt(7), Value(int64_t{0})); Value v5218; v5218 = Tuple({Value("BUY_PRODUCT"), Value("BUY_ANIMAL")}); if (!static_cast<bool>(Binary("In", v5217, v5218))) return Value(false); v5217 = v5218; return Value(true); }()); if (!static_cast<bool>(v5216)) return v5216; v5216 = ([&]() -> Value { auto v5219 = Get(s->LocalAt(7), Value(int64_t{1})); Value v5220; v5220 = Get(s->LocalAt(4), Value(int64_t{1})); if (!static_cast<bool>(Binary("Eq", v5219, v5220))) return Value(false); v5219 = v5220; return Value(true); }()); return v5216; }()))) {
break;
}
auto v5221 = Tuple({Get(s->LocalAt(5), s->LocalAt(2)), Get(s->LocalAt(5), ([&]() -> Value { auto v5222 = s->LocalAt(2); return Binary("Sub", v5222, Value(int64_t{1})); }()))});
auto unpack5223 = Iterate(v5221);
ValidateUnpack(unpack5223, 2, false);
Put(s->LocalAt(5), ([&]() -> Value { auto v5224 = s->LocalAt(2); return Binary("Sub", v5224, Value(int64_t{1})); }()), unpack5223.at(0));
Put(s->LocalAt(5), s->LocalAt(2), unpack5223.at(1));
auto v5225 = s->LocalAt(2);
s->SetAt(2, Inplace("Sub", v5225, Value(int64_t{1})));
}
}
if (static_cast<bool>(([&]() -> Value { auto v5226 = s->LocalAt(5); Value v5227; v5227 = s->LocalAt(6); if (!static_cast<bool>(Binary("Eq", v5226, v5227))) return Value(false); v5226 = v5227; return Value(true); }()))) {
return s->LocalAt(0);
}
auto v5228 = s->Global("_V219_REPORT");
auto v5229 = Value("reordered_market_turns");
auto v5230 = Get(v5228, v5229);
Put(v5228, v5229, Inplace("Add", v5230, Value(int64_t{1})));
auto v5231 = ([&]() -> Value { auto fn5232 = Attribute(s->Global("copy"), "deepcopy"); Arguments args5233; args5233.Add(s->LocalAt(0), false); return Call(c, fn5232, std::move(args5233)); }());
s->SetAt(1, v5231);
auto v5234 = s->LocalAt(5);
Put(s->LocalAt(1), Value("market"), v5234);
return s->LocalAt(1);
return {};
}
}  // namespace kagg::opponents::compiled
