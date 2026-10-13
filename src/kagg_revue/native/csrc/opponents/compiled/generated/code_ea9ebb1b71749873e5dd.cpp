#include "opponents/compiled/typed.hpp"
// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_ea9ebb1b71749873e5dd(Context& c, const ScopePtr& s) {
if (auto result = TypedClone(c, s)) return *result;
static constexpr const char* s_names[] = {"f", "farm", "pr", "private"};
s->PrepareSlots(s_names);
auto v2596 = ([&]() -> Value { auto fn2597 = s->Global("dict"); Arguments args2598; args2598.Add(s->LocalAt(1), false); return Call(c, fn2597, std::move(args2598)); }());
s->SetAt(0, v2596);
auto v2599 = ([&]() -> Value { auto comp2600 = std::make_shared<Scope>(); comp2600->globals = s->globals; comp2600->parent = s; static constexpr const char* comp2600_names[] = {"row"}; comp2600->PrepareSlots(comp2600_names); auto result2601 = List(); for (const auto& item2602 : Iterate(Get(s->LocalAt(1), Value("tiles")))) { comp2600->SetAt(0, item2602); result2601.node()->sequence.push_back(([&]() -> Value { auto comp2603 = std::make_shared<Scope>(); comp2603->globals = comp2600->globals; comp2603->parent = comp2600; static constexpr const char* comp2603_names[] = {"tile"}; comp2603->PrepareSlots(comp2603_names); auto result2604 = List(); for (const auto& item2605 : Iterate(comp2600->LocalAt(0))) { comp2603->SetAt(0, item2605); result2604.node()->sequence.push_back((static_cast<bool>(([&]() -> Value { auto fn2606 = comp2603->Global("isinstance"); Arguments args2607; args2607.positional.reserve(2); args2607.Add(comp2603->LocalAt(0), false); args2607.Add(comp2603->Global("dict"), false); return Call(c, fn2606, std::move(args2607)); }())) ? ([&]() -> Value { auto fn2608 = comp2603->Global("dict"); Arguments args2609; args2609.Add(comp2603->LocalAt(0), false); return Call(c, fn2608, std::move(args2609)); }()) : comp2603->LocalAt(0))); } return result2604; }())); } return result2601; }());
Put(s->LocalAt(0), Value("tiles"), v2599);
auto v2610 = ([&]() -> Value { auto fn2611 = s->Global("list"); Arguments args2612; args2612.Add(Get(s->LocalAt(1), Value("farmer")), false); return Call(c, fn2611, std::move(args2612)); }());
Put(s->LocalAt(0), Value("farmer"), v2610);
auto v2613 = ([&]() -> Value { auto comp2614 = std::make_shared<Scope>(); comp2614->globals = s->globals; comp2614->parent = s; static constexpr const char* comp2614_names[] = {"pos"}; comp2614->PrepareSlots(comp2614_names); auto result2615 = List(); for (const auto& item2616 : Iterate(Get(s->LocalAt(1), Value("hands")))) { comp2614->SetAt(0, item2616); result2615.node()->sequence.push_back(([&]() -> Value { auto fn2617 = comp2614->Global("list"); Arguments args2618; args2618.Add(comp2614->LocalAt(0), false); return Call(c, fn2617, std::move(args2618)); }())); } return result2615; }());
Put(s->LocalAt(0), Value("hands"), v2613);
auto v2619 = ([&]() -> Value { auto fn2620 = s->Global("list"); Arguments args2621; args2621.Add(Get(s->LocalAt(1), Value("unlocked_quadrants")), false); return Call(c, fn2620, std::move(args2621)); }());
Put(s->LocalAt(0), Value("unlocked_quadrants"), v2619);
auto v2622 = ([&]() -> Value { auto fn2623 = s->Global("dict"); Arguments args2624; args2624.Add(s->LocalAt(3), false); return Call(c, fn2623, std::move(args2624)); }());
s->SetAt(2, v2622);
auto v2625 = Tuple({([&]() -> Value { auto fn2626 = s->Global("dict"); Arguments args2627; args2627.Add(Get(s->LocalAt(3), Value("shed")), false); return Call(c, fn2626, std::move(args2627)); }()), ([&]() -> Value { auto fn2628 = s->Global("dict"); Arguments args2629; args2629.Add(Get(s->LocalAt(3), Value("seeds")), false); return Call(c, fn2628, std::move(args2629)); }())});
auto unpack2630 = Iterate(v2625);
ValidateUnpack(unpack2630, 2, false);
Put(s->LocalAt(2), Value("shed"), unpack2630.at(0));
Put(s->LocalAt(2), Value("seeds"), unpack2630.at(1));
auto v2631 = ([&]() -> Value { auto comp2632 = std::make_shared<Scope>(); comp2632->globals = s->globals; comp2632->parent = s; static constexpr const char* comp2632_names[] = {"inv"}; comp2632->PrepareSlots(comp2632_names); auto result2633 = List(); for (const auto& item2634 : Iterate(Get(s->LocalAt(3), Value("inventories")))) { comp2632->SetAt(0, item2634); result2633.node()->sequence.push_back(([&]() -> Value { auto fn2635 = comp2632->Global("dict"); Arguments args2636; args2636.Add(comp2632->LocalAt(0), false); return Call(c, fn2635, std::move(args2636)); }())); } return result2633; }());
Put(s->LocalAt(2), Value("inventories"), v2631);
return Tuple({s->LocalAt(0), s->LocalAt(2)});
return {};
}
}  // namespace kagg::opponents::compiled
