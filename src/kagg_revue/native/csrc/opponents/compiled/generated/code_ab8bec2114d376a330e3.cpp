// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_ab8bec2114d376a330e3(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"path"};
s->PrepareSlots(s_names);
return Tuple({([&]() -> Value { auto v26803 = ([&]() -> Value { auto fn26804 = s->Global("_sl_dist"); Arguments args26805; args26805.positional.reserve(2); args26805.Add(s->Captured("pos"), false); args26805.Add(Get(s->LocalAt(0), Value(int64_t{0})), false); return Call(c, fn26804, std::move(args26805)); }()); return Binary("Add", v26803, ([&]() -> Value { auto fn26806 = s->Global("sum"); Arguments args26807; args26807.Add(([&]() -> Value { auto comp26808 = std::make_shared<Scope>(); comp26808->globals = s->globals; comp26808->parent = s; static constexpr const char* comp26808_names[] = {"a", "b"}; comp26808->PrepareSlots(comp26808_names); auto result26809 = List(); for (const auto& item26810 : Iterate(([&]() -> Value { auto fn26811 = s->Global("zip"); Arguments args26812; args26812.positional.reserve(2); args26812.Add(s->LocalAt(0), false); args26812.Add(Slice(s->LocalAt(0), Value(int64_t{1}), Value{}, Value{}), false); return Call(c, fn26811, std::move(args26812)); }()))) { auto unpack26813 = Iterate(item26810); ValidateUnpack(unpack26813, 2, false); comp26808->SetAt(0, unpack26813.at(0)); comp26808->SetAt(1, unpack26813.at(1)); result26809.node()->sequence.push_back(([&]() -> Value { auto fn26814 = comp26808->Global("_sl_dist"); Arguments args26815; args26815.positional.reserve(2); args26815.Add(comp26808->LocalAt(0), false); args26815.Add(comp26808->LocalAt(1), false); return Call(c, fn26814, std::move(args26815)); }())); } return result26809; }()), false); return Call(c, fn26806, std::move(args26807)); }())); }()), s->LocalAt(0)});
return {};
}
}  // namespace kagg::opponents::compiled
