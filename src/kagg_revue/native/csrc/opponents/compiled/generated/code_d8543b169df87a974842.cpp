// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_d8543b169df87a974842(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"cs"};
s->PrepareSlots(s_names);
return ([&]() -> Value { auto fn10366 = s->Global("sum"); Arguments args10367; args10367.Add(([&]() -> Value { auto comp10368 = std::make_shared<Scope>(); comp10368->globals = s->globals; comp10368->parent = s; static constexpr const char* comp10368_names[] = {"c"}; comp10368->PrepareSlots(comp10368_names); auto result10369 = List(); for (const auto& item10370 : Iterate(s->LocalAt(0))) { comp10368->SetAt(0, item10370); if (!static_cast<bool>(([&]() -> Value { auto v10371 = Slice(comp10368->LocalAt(0), Value{}, Value(int64_t{2}), Value{}); Value v10372; v10372 = List({Value("PICKUP"), Value("WHEAT")}); if (!static_cast<bool>(Binary("Eq", v10371, v10372))) return Value(false); v10371 = v10372; return Value(true); }()))) continue; result10369.node()->sequence.push_back(([&]() -> Value { auto fn10373 = comp10368->Global("max"); Arguments args10374; args10374.positional.reserve(2); args10374.Add(Value(int64_t{0}), false); args10374.Add((static_cast<bool>(([&]() -> Value { auto v10375 = ([&]() -> Value { auto fn10377 = comp10368->Global("len"); Arguments args10378; args10378.Add(comp10368->LocalAt(0), false); return Call(c, fn10377, std::move(args10378)); }()); Value v10376; v10376 = Value(int64_t{2}); if (!static_cast<bool>(Binary("Gt", v10375, v10376))) return Value(false); v10375 = v10376; return Value(true); }())) ? ([&]() -> Value { auto fn10379 = comp10368->Global("int"); Arguments args10380; args10380.Add(Get(comp10368->LocalAt(0), Value(int64_t{2})), false); return Call(c, fn10379, std::move(args10380)); }()) : Value(int64_t{1})), false); return Call(c, fn10373, std::move(args10374)); }())); } return result10369; }()), false); return Call(c, fn10366, std::move(args10367)); }());
return {};
}
}  // namespace kagg::opponents::compiled
