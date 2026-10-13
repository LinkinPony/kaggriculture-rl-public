// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_e3f2f3deb66292d29224(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"p"};
s->PrepareSlots(s_names);
return Tuple({([&]() -> Value { auto fn8846 = s->Global("sum"); Arguments args8847; args8847.Add(([&]() -> Value { auto comp8848 = std::make_shared<Scope>(); comp8848->globals = s->globals; comp8848->parent = s; static constexpr const char* comp8848_names[] = {"q"}; comp8848->PrepareSlots(comp8848_names); auto result8849 = List(); for (const auto& item8850 : Iterate(s->Captured("positions"))) { comp8848->SetAt(0, item8850); result8849.node()->sequence.push_back(([&]() -> Value { auto v8851 = ([&]() -> Value { auto fn8853 = comp8848->Global("tuple"); Arguments args8854; args8854.Add(comp8848->LocalAt(0), false); return Call(c, fn8853, std::move(args8854)); }()); Value v8852; v8852 = comp8848->Captured("p"); if (!static_cast<bool>(Binary("Eq", v8851, v8852))) return Value(false); v8851 = v8852; return Value(true); }())); } return result8849; }()), false); return Call(c, fn8846, std::move(args8847)); }()), ([&]() -> Value { auto fn8855 = Attribute(s->Captured("access"), "index"); Arguments args8856; args8856.Add(s->LocalAt(0), false); return Call(c, fn8855, std::move(args8856)); }())});
return {};
}
}  // namespace kagg::opponents::compiled
