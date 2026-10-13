// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_dba1a6e77d911f30f684(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "configuration", "observation"};
s->PrepareSlots(s_names);
if (static_cast<bool>(([&]() -> Value { auto v6022 = ([&]() -> Value { auto fn6024 = s->Global("int"); Arguments args6025; args6025.Add(([&]() -> Value { auto fn6026 = PrepareDictionaryGet(s->LocalAt(2)); Arguments args6027; args6027.positional.reserve(2); args6027.Add(Value("step"), false); args6027.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn6026, std::move(args6027)); }()), false); return Call(c, fn6024, std::move(args6025)); }()); Value v6023; v6023 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v6022, v6023))) return Value(false); v6022 = v6023; return Value(true); }()))) {
(void)([&]() -> Value { auto fn6028 = Attribute(s->Global("_R36_SALE_REPORT"), "update"); Arguments args6029; args6029.Keyword("sale_reserved_units", Value(int64_t{0})); args6029.Keyword("sale_reservations", Value(int64_t{0})); args6029.Keyword("sale_errors", Value(int64_t{0})); return Call(c, fn6028, std::move(args6029)); }());
}
auto v6030 = ([&]() -> Value { auto fn6031 = s->Global("_R36_SALE_PARENT"); Arguments args6032; args6032.positional.reserve(2); args6032.Add(s->LocalAt(2), false); args6032.Add(s->LocalAt(1), false); return Call(c, fn6031, std::move(args6032)); }());
s->SetAt(0, v6030);
try {
if (static_cast<bool>(([&]() -> Value { auto v6034 = ([&]() -> Value { auto v6035 = s->LocalAt(1); Value v6036; v6036 = Value{}; if (!static_cast<bool>(Binary("Is", v6035, v6036))) return Value(false); v6035 = v6036; return Value(true); }()); if (static_cast<bool>(v6034)) return v6034; v6034 = ([&]() -> Value { auto comp6037 = std::make_shared<Scope>(); comp6037->globals = s->globals; comp6037->parent = s; static constexpr const char* comp6037_names[] = {"k", "v"}; comp6037->PrepareSlots(comp6037_names); auto result6038 = List(); for (const auto& item6039 : Iterate(List({Tuple({Value("boardSize"), Value(int64_t{10})}), Tuple({Value("turnsPerDay"), Value(int64_t{24})}), Tuple({Value("shedCapacity"), Value(int64_t{100})}), Tuple({Value("maxMarketOrdersPerTurn"), Value(int64_t{10})})}))) { auto unpack6040 = Iterate(item6039); ValidateUnpack(unpack6040, 2, false); comp6037->SetAt(0, unpack6040.at(0)); comp6037->SetAt(1, unpack6040.at(1)); if (!static_cast<bool>(([&]() -> Value { auto v6041 = ([&]() -> Value { auto fn6043 = PrepareDictionaryGet(comp6037->Captured("configuration")); Arguments args6044; args6044.positional.reserve(2); args6044.Add(comp6037->LocalAt(0), false); args6044.Add(comp6037->LocalAt(1), false); return CallDictionaryGet(c, fn6043, std::move(args6044)); }()); Value v6042; v6042 = comp6037->LocalAt(1); if (!static_cast<bool>(Binary("Eq", v6041, v6042))) return Value(false); v6041 = v6042; return Value(true); }()))) return Value(false); } return Value(true); }()); return v6034; }()))) {
auto v6045 = ([&]() -> Value { auto fn6046 = s->Global("_r36_reserve"); Arguments args6047; args6047.positional.reserve(2); args6047.Add(s->LocalAt(2), false); args6047.Add(s->LocalAt(0), false); return Call(c, fn6046, std::move(args6047)); }());
s->SetAt(0, v6045);
if (static_cast<bool>(([&]() -> Value { auto v6048 = ([&]() -> Value { auto fn6050 = s->Global("int"); Arguments args6051; args6051.Add(Get(s->LocalAt(2), Value("step")), false); return Call(c, fn6050, std::move(args6051)); }()); Value v6049; v6049 = Value(int64_t{288}); if (!static_cast<bool>(Binary("GtE", v6048, v6049))) return Value(false); v6048 = v6049; return Value(true); }()))) {
auto v6052 = ([&]() -> Value { auto fn6053 = s->Global("_v224_sales_first"); Arguments args6054; args6054.Add(s->LocalAt(0), false); return Call(c, fn6053, std::move(args6054)); }());
s->SetAt(0, v6052);
}
}
} catch (const Error& error6033) {
if (Matches(error6033, s->Global("Exception"))) {
auto v6055 = ([&]() -> Value { auto v6056 = ([&]() -> Value { auto fn6057 = PrepareDictionaryGet(s->Global("_R36_SALE_REPORT")); Arguments args6058; args6058.positional.reserve(2); args6058.Add(Value("sale_errors"), false); args6058.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn6057, std::move(args6058)); }()); return Binary("Add", v6056, Value(int64_t{1})); }());
Put(s->Global("_R36_SALE_REPORT"), Value("sale_errors"), v6055);
}
else { throw; }
}
(void)([&]() -> Value { auto fn6059 = Attribute(s->Global("_R36_SALE_REPORT"), "update"); Arguments args6060; args6060.Add(Attribute(s->Global("_R36_SALE_PARENT"), "telemetry"), false); return Call(c, fn6059, std::move(args6060)); }());
return s->LocalAt(0);
return {};
}
}  // namespace kagg::opponents::compiled
