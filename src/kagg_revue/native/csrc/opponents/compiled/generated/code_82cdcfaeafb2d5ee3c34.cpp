// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_82cdcfaeafb2d5ee3c34(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"left", "right"};
s->PrepareSlots(s_names);
return ([&]() -> Value { auto comp3073 = std::make_shared<Scope>(); comp3073->globals = s->globals; comp3073->parent = s; static constexpr const char* comp3073_names[] = {"item", "value"}; comp3073->PrepareSlots(comp3073_names); auto result3074 = List(); for (const auto& item3075 : Iterate(([&]() -> Value { auto fn3076 = Attribute(s->LocalAt(1), "items"); Arguments args3077; return Call(c, fn3076, std::move(args3077)); }()))) { auto unpack3078 = Iterate(item3075); ValidateUnpack(unpack3078, 2, false); comp3073->SetAt(0, unpack3078.at(0)); comp3073->SetAt(1, unpack3078.at(1)); if (!static_cast<bool>(([&]() -> Value { auto v3079 = ([&]() -> Value { auto fn3081 = PrepareDictionaryGet(comp3073->Captured("left")); Arguments args3082; args3082.positional.reserve(2); args3082.Add(comp3073->LocalAt(0), false); args3082.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn3081, std::move(args3082)); }()); Value v3080; v3080 = comp3073->LocalAt(1); if (!static_cast<bool>(Binary("GtE", v3079, v3080))) return Value(false); v3079 = v3080; return Value(true); }()))) return Value(false); } return Value(true); }());
return {};
}
}  // namespace kagg::opponents::compiled
