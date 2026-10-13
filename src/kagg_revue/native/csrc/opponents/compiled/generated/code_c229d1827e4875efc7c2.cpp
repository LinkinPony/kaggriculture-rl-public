// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_c229d1827e4875efc7c2(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"animal", "farm"};
s->PrepareSlots(s_names);
return ([&]() -> Value { auto fn16030 = s->Global("sum"); Arguments args16031; args16031.Add(([&]() -> Value { auto comp16032 = std::make_shared<Scope>(); comp16032->globals = s->globals; comp16032->parent = s; static constexpr const char* comp16032_names[] = {"row", "tile"}; comp16032->PrepareSlots(comp16032_names); auto result16033 = List(); for (const auto& item16034 : Iterate(Get(s->LocalAt(1), Value("tiles")))) { comp16032->SetAt(0, item16034); for (const auto& item16035 : Iterate(comp16032->LocalAt(0))) { comp16032->SetAt(1, item16035); if (!static_cast<bool>(([&]() -> Value { auto v16036 = ([&]() -> Value { auto fn16037 = comp16032->Global("isinstance"); Arguments args16038; args16038.positional.reserve(2); args16038.Add(comp16032->LocalAt(1), false); args16038.Add(comp16032->Global("dict"), false); return Call(c, fn16037, std::move(args16038)); }()); if (!static_cast<bool>(v16036)) return v16036; v16036 = ([&]() -> Value { auto v16039 = ([&]() -> Value { auto fn16041 = PrepareDictionaryGet(comp16032->LocalAt(1)); Arguments args16042; args16042.Add(Value("animal"), false); return CallDictionaryGet(c, fn16041, std::move(args16042)); }()); Value v16040; v16040 = comp16032->Captured("animal"); if (!static_cast<bool>(Binary("Eq", v16039, v16040))) return Value(false); v16039 = v16040; return Value(true); }()); return v16036; }()))) continue; result16033.node()->sequence.push_back(Value(int64_t{1})); } } return result16033; }()), false); return Call(c, fn16030, std::move(args16031)); }());
return {};
}
}  // namespace kagg::opponents::compiled
