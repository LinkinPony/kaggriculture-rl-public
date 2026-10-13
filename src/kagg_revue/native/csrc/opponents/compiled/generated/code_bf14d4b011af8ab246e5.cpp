// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_bf14d4b011af8ab246e5(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"configuration"};
s->PrepareSlots(s_names);
return ([&]() -> Value { auto v15441 = ([&]() -> Value { auto v15442 = s->LocalAt(0); Value v15443; v15443 = Value{}; if (!static_cast<bool>(Binary("Is", v15442, v15443))) return Value(false); v15442 = v15443; return Value(true); }()); if (static_cast<bool>(v15441)) return v15441; v15441 = ([&]() -> Value { auto comp15444 = std::make_shared<Scope>(); comp15444->globals = s->globals; comp15444->parent = s; static constexpr const char* comp15444_names[] = {"key", "value"}; comp15444->PrepareSlots(comp15444_names); auto result15445 = List(); for (const auto& item15446 : Iterate(Tuple({Tuple({Value("boardSize"), Value(int64_t{10})}), Tuple({Value("turnsPerDay"), Value(int64_t{24})}), Tuple({Value("shedCapacity"), Value(int64_t{100})}), Tuple({Value("maxMarketOrdersPerTurn"), Value(int64_t{10})}), Tuple({Value("farmHandCostMult"), Value(int64_t{1})})}))) { auto unpack15447 = Iterate(item15446); ValidateUnpack(unpack15447, 2, false); comp15444->SetAt(0, unpack15447.at(0)); comp15444->SetAt(1, unpack15447.at(1)); if (!static_cast<bool>(([&]() -> Value { auto v15448 = ([&]() -> Value { auto fn15450 = PrepareDictionaryGet(comp15444->Captured("configuration")); Arguments args15451; args15451.positional.reserve(2); args15451.Add(comp15444->LocalAt(0), false); args15451.Add(comp15444->LocalAt(1), false); return CallDictionaryGet(c, fn15450, std::move(args15451)); }()); Value v15449; v15449 = comp15444->LocalAt(1); if (!static_cast<bool>(Binary("Eq", v15448, v15449))) return Value(false); v15448 = v15449; return Value(true); }()))) return Value(false); } return Value(true); }()); return v15441; }());
return {};
}
}  // namespace kagg::opponents::compiled
