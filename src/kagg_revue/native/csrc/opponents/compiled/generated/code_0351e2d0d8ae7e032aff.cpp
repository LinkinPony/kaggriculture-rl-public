// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_0351e2d0d8ae7e032aff(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"farm", "obs", "seat"};
s->PrepareSlots(s_names);
auto v2559 = ([&]() -> Value { auto fn2560 = s->Global("int"); Arguments args2561; args2561.Add(([&]() -> Value { auto fn2562 = s->Global("_get"); Arguments args2563; args2563.positional.reserve(3); args2563.Add(s->LocalAt(1), false); args2563.Add(Value("player"), false); args2563.Add(Value(int64_t{0}), false); return Call(c, fn2562, std::move(args2563)); }()), false); return Call(c, fn2560, std::move(args2561)); }());
s->SetAt(2, v2559);
auto v2564 = Get(([&]() -> Value { auto fn2565 = s->Global("_get"); Arguments args2566; args2566.positional.reserve(2); args2566.Add(s->LocalAt(1), false); args2566.Add(Value("farms"), false); return Call(c, fn2565, std::move(args2566)); }()), s->LocalAt(2));
s->SetAt(0, v2564);
return Tuple({([&]() -> Value { auto comp2567 = std::make_shared<Scope>(); comp2567->globals = s->globals; comp2567->parent = s; static constexpr const char* comp2567_names[] = {"k", "v"}; comp2567->PrepareSlots(comp2567_names); auto result2568 = Dict(); for (const auto& item2569 : Iterate(([&]() -> Value { auto fn2570 = Attribute(s->LocalAt(0), "items"); Arguments args2571; return Call(c, fn2570, std::move(args2571)); }()))) { auto unpack2572 = Iterate(item2569); ValidateUnpack(unpack2572, 2, false); comp2567->SetAt(0, unpack2572.at(0)); comp2567->SetAt(1, unpack2572.at(1)); if (!static_cast<bool>(([&]() -> Value { auto v2573 = comp2567->LocalAt(0); Value v2574; v2574 = Value("money"); if (!static_cast<bool>(Binary("NotEq", v2573, v2574))) return Value(false); v2573 = v2574; return Value(true); }()))) continue; Put(result2568, comp2567->LocalAt(0), comp2567->LocalAt(1)); } return result2568; }()), ([&]() -> Value { auto fn2575 = s->Global("_get"); Arguments args2576; args2576.positional.reserve(2); args2576.Add(s->LocalAt(1), false); args2576.Add(Value("private"), false); return Call(c, fn2575, std::move(args2576)); }())});
return {};
}
}  // namespace kagg::opponents::compiled
