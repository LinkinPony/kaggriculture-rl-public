// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_3327c37e5ec98da713bb(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"buys", "candidate", "final", "loss", "safe", "sales", "stock"};
s->PrepareSlots(s_names);
auto v10494 = ([&]() -> Value { auto fn10495 = s->Global("_r97_market_stock"); Arguments args10496; args10496.positional.reserve(2); args10496.Add(Get(s->Captured("private"), Value("shed")), false); args10496.Add(s->LocalAt(1), false); return Call(c, fn10495, std::move(args10496)); }());
auto unpack10497 = Iterate(v10494);
ValidateUnpack(unpack10497, 3, false);
s->SetAt(6, unpack10497.at(0));
s->SetAt(0, unpack10497.at(1));
s->SetAt(5, unpack10497.at(2));
auto v10498 = ([&]() -> Value { auto fn10499 = s->Global("_r97_delivery"); Arguments args10500; args10500.positional.reserve(3); args10500.Add(s->LocalAt(6), false); args10500.Add(s->Captured("private"), false); args10500.Add(s->Captured("night"), false); return Call(c, fn10499, std::move(args10500)); }());
auto unpack10501 = Iterate(v10498);
ValidateUnpack(unpack10501, 2, false);
s->SetAt(2, unpack10501.at(0));
s->SetAt(3, unpack10501.at(1));
auto v10502 = ([&]() -> Value { auto v10503 = ([&]() -> Value { auto comp10504 = std::make_shared<Scope>(); comp10504->globals = s->globals; comp10504->parent = s; static constexpr const char* comp10504_names[] = {"i", "q"}; comp10504->PrepareSlots(comp10504_names); auto result10505 = List(); for (const auto& item10506 : Iterate(([&]() -> Value { auto fn10507 = Attribute(s->Captured("original_buys"), "items"); Arguments args10508; return Call(c, fn10507, std::move(args10508)); }()))) { auto unpack10509 = Iterate(item10506); ValidateUnpack(unpack10509, 2, false); comp10504->SetAt(0, unpack10509.at(0)); comp10504->SetAt(1, unpack10509.at(1)); if (!static_cast<bool>(([&]() -> Value { auto v10510 = ([&]() -> Value { auto fn10512 = PrepareDictionaryGet(comp10504->Captured("buys")); Arguments args10513; args10513.positional.reserve(2); args10513.Add(comp10504->LocalAt(0), false); args10513.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn10512, std::move(args10513)); }()); Value v10511; v10511 = comp10504->LocalAt(1); if (!static_cast<bool>(Binary("GtE", v10510, v10511))) return Value(false); v10510 = v10511; return Value(true); }()))) return Value(false); } return Value(true); }()); if (!static_cast<bool>(v10503)) return v10503; v10503 = ([&]() -> Value { auto comp10514 = std::make_shared<Scope>(); comp10514->globals = s->globals; comp10514->parent = s; static constexpr const char* comp10514_names[] = {"item", "q"}; comp10514->PrepareSlots(comp10514_names); auto result10515 = List(); for (const auto& item10516 : Iterate(([&]() -> Value { auto fn10517 = Attribute(s->LocalAt(3), "items"); Arguments args10518; return Call(c, fn10517, std::move(args10518)); }()))) { auto unpack10519 = Iterate(item10516); ValidateUnpack(unpack10519, 2, false); comp10514->SetAt(0, unpack10519.at(0)); comp10514->SetAt(1, unpack10519.at(1)); if (!static_cast<bool>(([&]() -> Value { auto v10520 = comp10514->LocalAt(1); Value v10521; v10521 = ([&]() -> Value { auto fn10522 = PrepareDictionaryGet(comp10514->Captured("original_loss")); Arguments args10523; args10523.positional.reserve(2); args10523.Add(comp10514->LocalAt(0), false); args10523.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn10522, std::move(args10523)); }()); if (!static_cast<bool>(Binary("LtE", v10520, v10521))) return Value(false); v10520 = v10521; return Value(true); }()))) return Value(false); } return Value(true); }()); return v10503; }());
s->SetAt(4, v10502);
return Tuple({s->LocalAt(2), s->LocalAt(5), s->LocalAt(4)});
return {};
}
}  // namespace kagg::opponents::compiled
