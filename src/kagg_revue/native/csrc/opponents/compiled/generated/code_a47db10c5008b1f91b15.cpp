// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_a47db10c5008b1f91b15(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "configuration", "observation", "player", "state", "step"};
s->PrepareSlots(s_names);
try {
auto v8166 = ([&]() -> Value { auto fn8167 = s->Global("int"); Arguments args8168; args8168.Add(Get(s->LocalAt(2), Value("step")), false); return Call(c, fn8167, std::move(args8168)); }());
s->SetAt(5, v8166);
auto v8169 = ([&]() -> Value { auto fn8170 = s->Global("int"); Arguments args8171; args8171.Add(Get(s->LocalAt(2), Value("player")), false); return Call(c, fn8170, std::move(args8171)); }());
s->SetAt(3, v8169);
auto v8172 = ([&]() -> Value { auto fn8173 = PrepareDictionaryGet(s->Global("_R51_INPUT_STATES")); Arguments args8174; args8174.Add(s->LocalAt(3), false); return CallDictionaryGet(c, fn8173, std::move(args8174)); }());
s->SetAt(4, v8172);
if (static_cast<bool>(([&]() -> Value { auto v8175 = ([&]() -> Value { auto v8176 = s->LocalAt(4); Value v8177; v8177 = Value{}; if (!static_cast<bool>(Binary("Is", v8176, v8177))) return Value(false); v8176 = v8177; return Value(true); }()); if (static_cast<bool>(v8175)) return v8175; v8175 = ([&]() -> Value { auto v8178 = s->LocalAt(5); Value v8179; v8179 = Get(s->LocalAt(4), Value("step")); if (!static_cast<bool>(Binary("LtE", v8178, v8179))) return Value(false); v8178 = v8179; return Value(true); }()); return v8175; }()))) {
auto v8180 = ([&]() -> Value { auto dict8181 = Dict(); auto key8182 = Value("step"); Put(dict8181, key8182, Unary("USub", Value(int64_t{1}))); return dict8181; }());
s->SetAt(4, v8180);
Put(s->Global("_R51_INPUT_STATES"), s->LocalAt(3), v8180);
(void)([&]() -> Value { auto fn8183 = Attribute(s->Global("_R51_INPUT_REPORT"), "update"); Arguments args8184; args8184.Keyword("input_hire_requests", Value(int64_t{0})); args8184.Keyword("input_confirmed_hires", Value(int64_t{0})); args8184.Keyword("input_hire_errors", Value(int64_t{0})); args8184.Keyword("input_purchase_requests", Value(int64_t{0})); args8184.Keyword("input_loaded_units", Value(int64_t{0})); args8184.Keyword("input_stock_shortfalls", Value(int64_t{0})); args8184.Keyword("input_application_requests", Value(int64_t{0})); args8184.Keyword("input_confirmed_applications", Value(int64_t{0})); args8184.Keyword("input_application_errors", Value(int64_t{0})); args8184.Keyword("input_errors", Value(int64_t{0})); args8184.Keyword("input_forecast_wheat", Value(int64_t{0})); args8184.Keyword("input_forecast_carrot", Value(int64_t{0})); return Call(c, fn8183, std::move(args8184)); }());
}
auto v8185 = s->LocalAt(5);
Put(s->LocalAt(4), Value("step"), v8185);
auto v8186 = ([&]() -> Value { auto fn8187 = s->Global("_R51_INPUT_PARENT"); Arguments args8188; args8188.positional.reserve(2); args8188.Add(s->LocalAt(2), false); args8188.Add(s->LocalAt(1), false); return Call(c, fn8187, std::move(args8188)); }());
s->SetAt(0, v8186);
if (static_cast<bool>(([&]() -> Value { auto v8189 = ([&]() -> Value { auto v8190 = s->LocalAt(1); Value v8191; v8191 = Value{}; if (!static_cast<bool>(Binary("Is", v8190, v8191))) return Value(false); v8190 = v8191; return Value(true); }()); if (static_cast<bool>(v8189)) return v8189; v8189 = ([&]() -> Value { auto comp8192 = std::make_shared<Scope>(); comp8192->globals = s->globals; comp8192->parent = s; static constexpr const char* comp8192_names[] = {"k", "v"}; comp8192->PrepareSlots(comp8192_names); auto result8193 = List(); for (const auto& item8194 : Iterate(List({Tuple({Value("boardSize"), Value(int64_t{10})}), Tuple({Value("turnsPerDay"), Value(int64_t{24})}), Tuple({Value("shedCapacity"), Value(int64_t{100})}), Tuple({Value("maxMarketOrdersPerTurn"), Value(int64_t{10})})}))) { auto unpack8195 = Iterate(item8194); ValidateUnpack(unpack8195, 2, false); comp8192->SetAt(0, unpack8195.at(0)); comp8192->SetAt(1, unpack8195.at(1)); if (!static_cast<bool>(([&]() -> Value { auto v8196 = ([&]() -> Value { auto fn8198 = PrepareDictionaryGet(comp8192->Captured("configuration")); Arguments args8199; args8199.positional.reserve(2); args8199.Add(comp8192->LocalAt(0), false); args8199.Add(comp8192->LocalAt(1), false); return CallDictionaryGet(c, fn8198, std::move(args8199)); }()); Value v8197; v8197 = comp8192->LocalAt(1); if (!static_cast<bool>(Binary("Eq", v8196, v8197))) return Value(false); v8196 = v8197; return Value(true); }()))) return Value(false); } return Value(true); }()); return v8189; }()))) {
auto v8200 = ([&]() -> Value { auto fn8201 = s->Global("_r51_input_control"); Arguments args8202; args8202.positional.reserve(3); args8202.Add(s->LocalAt(2), false); args8202.Add(s->LocalAt(0), false); args8202.Add(s->LocalAt(4), false); return Call(c, fn8201, std::move(args8202)); }());
s->SetAt(0, v8200);
}
(void)([&]() -> Value { auto fn8203 = Attribute(s->Global("_R51_INPUT_REPORT"), "update"); Arguments args8204; args8204.Add(([&]() -> Value { auto fn8205 = s->Global("getattr"); Arguments args8206; args8206.positional.reserve(3); args8206.Add(s->Global("_R51_INPUT_PARENT"), false); args8206.Add(Value("telemetry"), false); args8206.Add(([&]() -> Value { auto dict8207 = Dict(); return dict8207; }()), false); return Call(c, fn8205, std::move(args8206)); }()), false); return Call(c, fn8203, std::move(args8204)); }());
return s->LocalAt(0);
} catch (const Error& error8165) {
if (Matches(error8165, s->Global("Exception"))) {
auto v8208 = ([&]() -> Value { auto v8209 = ([&]() -> Value { auto fn8210 = PrepareDictionaryGet(s->Global("_R51_INPUT_REPORT")); Arguments args8211; args8211.positional.reserve(2); args8211.Add(Value("input_errors"), false); args8211.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn8210, std::move(args8211)); }()); return Binary("Add", v8209, Value(int64_t{1})); }());
Put(s->Global("_R51_INPUT_REPORT"), Value("input_errors"), v8208);
return ([&]() -> Value { auto dict8212 = Dict(); auto key8213 = Value("farmer"); Put(dict8212, key8213, List({Value("PASS")})); auto key8214 = Value("hands"); Put(dict8212, key8214, List({})); auto key8215 = Value("market"); Put(dict8212, key8215, List({})); return dict8212; }());
}
else { throw; }
}
return {};
}
}  // namespace kagg::opponents::compiled
