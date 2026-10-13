// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_f20ba95e632e3b1e6e51(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"item"};
s->PrepareSlots(s_names);
return ([&]() -> Value { auto v24217 = ([&]() -> Value { auto fn24218 = s->Global("sum"); Arguments args24219; args24219.Add(([&]() -> Value { auto comp24220 = std::make_shared<Scope>(); comp24220->globals = s->globals; comp24220->parent = s; static constexpr const char* comp24220_names[] = {"p"}; comp24220->PrepareSlots(comp24220_names); auto result24221 = List(); for (const auto& item24222 : Iterate(([&]() -> Value { auto fn24223 = Attribute(s->Global("_HD2_SHOP_TYPES"), "values"); Arguments args24224; return Call(c, fn24223, std::move(args24224)); }()))) { comp24220->SetAt(0, item24222); if (!static_cast<bool>(([&]() -> Value { auto v24225 = comp24220->Captured("item"); Value v24226; v24226 = comp24220->LocalAt(0); if (!static_cast<bool>(Binary("In", v24225, v24226))) return Value(false); v24225 = v24226; return Value(true); }()))) continue; result24221.node()->sequence.push_back(([&]() -> Value { auto v24227 = Value(6.0); return Binary("Mult", v24227, (static_cast<bool>(([&]() -> Value { auto v24228 = ([&]() -> Value { auto fn24230 = comp24220->Global("len"); Arguments args24231; args24231.Add(comp24220->LocalAt(0), false); return Call(c, fn24230, std::move(args24231)); }()); Value v24229; v24229 = Value(int64_t{1}); if (!static_cast<bool>(Binary("Eq", v24228, v24229))) return Value(false); v24228 = v24229; return Value(true); }())) ? Value(int64_t{2}) : Value(int64_t{1}))); }())); } return result24221; }()), false); return Call(c, fn24218, std::move(args24219)); }()); return Binary("Div", v24217, ([&]() -> Value { auto fn24232 = s->Global("len"); Arguments args24233; args24233.Add(s->Global("_HD2_SHOP_TYPES"), false); return Call(c, fn24232, std::move(args24233)); }())); }());
return {};
}
}  // namespace kagg::opponents::compiled
