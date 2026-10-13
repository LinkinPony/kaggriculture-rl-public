// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_356828608889996850bb(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"p"};
s->PrepareSlots(s_names);
return Tuple({([&]() -> Value { auto fn8649 = s->Global("sum"); Arguments args8650; args8650.Add(([&]() -> Value { auto comp8651 = std::make_shared<Scope>(); comp8651->globals = s->globals; comp8651->parent = s; static constexpr const char* comp8651_names[] = {"q"}; comp8651->PrepareSlots(comp8651_names); auto result8652 = List(); for (const auto& item8653 : Iterate(s->Captured("positions"))) { comp8651->SetAt(0, item8653); result8652.node()->sequence.push_back(([&]() -> Value { auto v8654 = ([&]() -> Value { auto fn8656 = comp8651->Global("tuple"); Arguments args8657; args8657.Add(comp8651->LocalAt(0), false); return Call(c, fn8656, std::move(args8657)); }()); Value v8655; v8655 = comp8651->Captured("p"); if (!static_cast<bool>(Binary("Eq", v8654, v8655))) return Value(false); v8654 = v8655; return Value(true); }())); } return result8652; }()), false); return Call(c, fn8649, std::move(args8650)); }()), ([&]() -> Value { auto fn8658 = Attribute(s->Captured("access"), "index"); Arguments args8659; args8659.Add(s->LocalAt(0), false); return Call(c, fn8658, std::move(args8659)); }())});
return {};
}
}  // namespace kagg::opponents::compiled
