// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_dde3d829cd6bba08b5eb(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "configuration", "observation", "standard"};
s->PrepareSlots(s_names);
auto v19145 = ([&]() -> Value { auto fn19146 = s->Global("_PG_HOST"); Arguments args19147; args19147.positional.reserve(2); args19147.Add(s->LocalAt(2), false); args19147.Add(s->LocalAt(1), false); return Call(c, fn19146, std::move(args19147)); }());
s->SetAt(0, v19145);
try {
auto v19149 = ([&]() -> Value { auto v19150 = ([&]() -> Value { auto v19151 = s->LocalAt(1); Value v19152; v19152 = Value{}; if (!static_cast<bool>(Binary("Is", v19151, v19152))) return Value(false); v19151 = v19152; return Value(true); }()); if (static_cast<bool>(v19150)) return v19150; v19150 = ([&]() -> Value { auto comp19153 = std::make_shared<Scope>(); comp19153->globals = s->globals; comp19153->parent = s; static constexpr const char* comp19153_names[] = {"k", "v"}; comp19153->PrepareSlots(comp19153_names); auto result19154 = List(); for (const auto& item19155 : Iterate(List({Tuple({Value("boardSize"), Value(int64_t{10})}), Tuple({Value("turnsPerDay"), Value(int64_t{24})}), Tuple({Value("shedCapacity"), Value(int64_t{100})}), Tuple({Value("maxMarketOrdersPerTurn"), Value(int64_t{10})})}))) { auto unpack19156 = Iterate(item19155); ValidateUnpack(unpack19156, 2, false); comp19153->SetAt(0, unpack19156.at(0)); comp19153->SetAt(1, unpack19156.at(1)); if (!static_cast<bool>(([&]() -> Value { auto v19157 = ([&]() -> Value { auto fn19159 = PrepareDictionaryGet(comp19153->Captured("configuration")); Arguments args19160; args19160.positional.reserve(2); args19160.Add(comp19153->LocalAt(0), false); args19160.Add(comp19153->LocalAt(1), false); return CallDictionaryGet(c, fn19159, std::move(args19160)); }()); Value v19158; v19158 = comp19153->LocalAt(1); if (!static_cast<bool>(Binary("Eq", v19157, v19158))) return Value(false); v19157 = v19158; return Value(true); }()))) return Value(false); } return Value(true); }()); return v19150; }());
s->SetAt(3, v19149);
if (static_cast<bool>(s->LocalAt(3))) {
auto v19161 = ([&]() -> Value { auto fn19162 = s->Global("_y_preguard"); Arguments args19163; args19163.positional.reserve(2); args19163.Add(s->LocalAt(2), false); args19163.Add(s->LocalAt(0), false); return Call(c, fn19162, std::move(args19163)); }());
s->SetAt(0, v19161);
}
} catch (const Error& error19148) {
if (Matches(error19148, s->Global("Exception"))) {
auto v19164 = s->Global("_PG_REPORT");
auto v19165 = Value("preguard_errors");
auto v19166 = Get(v19164, v19165);
Put(v19164, v19165, Inplace("Add", v19166, Value(int64_t{1})));
}
else { throw; }
}
return s->LocalAt(0);
return {};
}
}  // namespace kagg::opponents::compiled
