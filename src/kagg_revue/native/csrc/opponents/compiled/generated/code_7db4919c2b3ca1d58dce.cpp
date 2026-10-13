// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_7db4919c2b3ca1d58dce(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"board_size", "pos"};
s->PrepareSlots(s_names);
return ([&]() -> Value { auto v2097 = ([&]() -> Value { auto fn2099 = s->Global("tuple"); Arguments args2100; args2100.Add(s->LocalAt(1), false); return Call(c, fn2099, std::move(args2100)); }()); Value v2098; v2098 = ([&]() -> Value { auto comp2101 = std::make_shared<Scope>(); comp2101->globals = s->globals; comp2101->parent = s; static constexpr const char* comp2101_names[] = {"x", "y"}; comp2101->PrepareSlots(comp2101_names); auto result2102 = List(); for (const auto& item2103 : Iterate(([&]() -> Value { auto fn2104 = s->Global("_shed_access_tiles"); Arguments args2105; args2105.Add(s->LocalAt(0), false); return Call(c, fn2104, std::move(args2105)); }()))) { auto unpack2106 = Iterate(item2103); ValidateUnpack(unpack2106, 2, false); comp2101->SetAt(0, unpack2106.at(0)); comp2101->SetAt(1, unpack2106.at(1)); result2102.node()->sequence.push_back(Tuple({comp2101->LocalAt(0), comp2101->LocalAt(1)})); } return Set(result2102.node()->sequence); }()); if (!static_cast<bool>(Binary("In", v2097, v2098))) return Value(false); v2097 = v2098; return Value(true); }());
return {};
}
}  // namespace kagg::opponents::compiled
