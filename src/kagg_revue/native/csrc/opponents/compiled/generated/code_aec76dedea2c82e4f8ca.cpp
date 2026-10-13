// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_aec76dedea2c82e4f8ca(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"obs", "out", "st"};
s->PrepareSlots(s_names);
auto v27825 = ([&]() -> Value { auto fn27826 = s->Global("_E361_FORECAST"); Arguments args27827; args27827.positional.reserve(2); args27827.Add(s->LocalAt(0), false); args27827.Add(s->LocalAt(2), false); return Call(c, fn27826, std::move(args27827)); }());
s->SetAt(1, v27825);
if (static_cast<bool>(([&]() -> Value { auto v27828 = s->LocalAt(1); if (!static_cast<bool>(v27828)) return v27828; v27828 = ([&]() -> Value { auto comp27829 = std::make_shared<Scope>(); comp27829->globals = s->globals; comp27829->parent = s; static constexpr const char* comp27829_names[] = {"ev"}; comp27829->PrepareSlots(comp27829_names); auto result27830 = List(); for (const auto& item27831 : Iterate(s->LocalAt(1))) { comp27829->SetAt(0, item27831); if (static_cast<bool>(([&]() -> Value { auto v27832 = ([&]() -> Value { auto fn27834 = comp27829->Global("id"); Arguments args27835; args27835.Add(comp27829->LocalAt(0), false); return Call(c, fn27834, std::move(args27835)); }()); Value v27833; v27833 = comp27829->Global("_E361_IDS"); if (!static_cast<bool>(Binary("In", v27832, v27833))) return Value(false); v27832 = v27833; return Value(true); }()))) return Value(true); } return Value(false); }()); return v27828; }()))) {
auto v27836 = s->Global("_E361_REPORT");
auto v27837 = Value("new_best");
auto v27838 = Get(v27836, v27837);
Put(v27836, v27837, Inplace("Add", v27838, Value(int64_t{1})));
}
return s->LocalAt(1);
return {};
}
}  // namespace kagg::opponents::compiled
