// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_92b94fa54d3208567156(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"prices", "run", "shed"};
s->PrepareSlots(s_names);
auto v3099 = Get(Get(s->LocalAt(1), Value("private")), Value("shed"));
s->SetAt(2, v3099);
return ([&]() -> Value { auto fn3100 = s->Global("sum"); Arguments args3101; args3101.Add(([&]() -> Value { auto comp3102 = std::make_shared<Scope>(); comp3102->globals = s->globals; comp3102->parent = s; static constexpr const char* comp3102_names[] = {"item"}; comp3102->PrepareSlots(comp3102_names); auto result3103 = List(); for (const auto& item3104 : Iterate(s->Global("PRODUCTS"))) { comp3102->SetAt(0, item3104); result3103.node()->sequence.push_back(([&]() -> Value { auto v3105 = ([&]() -> Value { auto v3106 = ([&]() -> Value { auto fn3107 = PrepareDictionaryGet(Get(comp3102->Captured("run"), Value("sold"))); Arguments args3108; args3108.positional.reserve(2); args3108.Add(comp3102->LocalAt(0), false); args3108.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn3107, std::move(args3108)); }()); return Binary("Add", v3106, ([&]() -> Value { auto fn3109 = PrepareDictionaryGet(comp3102->Captured("shed")); Arguments args3110; args3110.positional.reserve(2); args3110.Add(comp3102->LocalAt(0), false); args3110.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn3109, std::move(args3110)); }())); }()); return Binary("Mult", v3105, Get(comp3102->Captured("prices"), comp3102->LocalAt(0))); }())); } return result3103; }()), false); return Call(c, fn3100, std::move(args3101)); }());
return {};
}
}  // namespace kagg::opponents::compiled
