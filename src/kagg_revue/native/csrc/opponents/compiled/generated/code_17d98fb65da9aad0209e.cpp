// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_17d98fb65da9aad0209e(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"inventory", "obs", "quantity"};
s->PrepareSlots(s_names);
auto v11197 = ([&]() -> Value { auto fn11198 = s->Global("int"); Arguments args11199; args11199.Add(Get(Get(Get(s->LocalAt(1), Value("market")), Value("inventory")), Value("WHEAT")), false); return Call(c, fn11198, std::move(args11199)); }());
s->SetAt(0, v11197);
return ([&]() -> Value { auto fn11200 = s->Global("sum"); Arguments args11201; args11201.Add(([&]() -> Value { auto comp11202 = std::make_shared<Scope>(); comp11202->globals = s->globals; comp11202->parent = s; static constexpr const char* comp11202_names[] = {"j"}; comp11202->PrepareSlots(comp11202_names); auto result11203 = List(); for (const auto& item11204 : Iterate(([&]() -> Value { auto fn11205 = s->Global("range"); Arguments args11206; args11206.positional.reserve(2); args11206.Add(Value(int64_t{1}), false); args11206.Add(([&]() -> Value { auto v11207 = s->LocalAt(2); return Binary("Add", v11207, Value(int64_t{1})); }()), false); return Call(c, fn11205, std::move(args11206)); }()))) { comp11202->SetAt(0, item11204); result11203.node()->sequence.push_back(([&]() -> Value { auto fn11208 = comp11202->Global("_r37_market_price"); Arguments args11209; args11209.positional.reserve(2); args11209.Add(Value("WHEAT"), false); args11209.Add(([&]() -> Value { auto v11210 = comp11202->Captured("inventory"); return Binary("Sub", v11210, ([&]() -> Value { auto v11211 = ([&]() -> Value { auto v11212 = Value(int64_t{2}); return Binary("Mult", v11212, comp11202->LocalAt(0)); }()); return Binary("Sub", v11211, Value(int64_t{1})); }())); }()), false); return Call(c, fn11208, std::move(args11209)); }())); } return result11203; }()), false); return Call(c, fn11200, std::move(args11201)); }());
return {};
}
}  // namespace kagg::opponents::compiled
