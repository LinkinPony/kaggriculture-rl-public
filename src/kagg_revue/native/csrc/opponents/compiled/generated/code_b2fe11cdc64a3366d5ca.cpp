// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_b2fe11cdc64a3366d5ca(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"key", "shops"};
s->PrepareSlots(s_names);
auto v27728 = ([&]() -> Value { auto fn27729 = Attribute(Value("|"), "join"); Arguments args27730; args27730.Add(s->LocalAt(1), false); return Call(c, fn27729, std::move(args27730)); }());
s->SetAt(0, v27728);
if (static_cast<bool>(([&]() -> Value { auto v27731 = Value("data"); Value v27732; v27732 = s->Global("_E352_LIB"); if (!static_cast<bool>(Binary("NotIn", v27731, v27732))) return Value(false); v27731 = v27732; return Value(true); }()))) {
auto v27733 = c.constants.at(7);
Put(s->Global("_E352_LIB"), Value("data"), v27733);
}
if (static_cast<bool>(([&]() -> Value { auto v27734 = s->LocalAt(0); Value v27735; v27735 = s->Global("_E352_LIB"); if (!static_cast<bool>(Binary("NotIn", v27734, v27735))) return Value(false); v27734 = v27735; return Value(true); }()))) {
auto v27736 = ([&]() -> Value { auto comp27737 = std::make_shared<Scope>(); comp27737->globals = s->globals; comp27737->parent = s; static constexpr const char* comp27737_names[] = {"ev", "src"}; comp27737->PrepareSlots(comp27737_names); auto result27738 = List(); for (const auto& item27739 : Iterate(([&]() -> Value { auto fn27740 = PrepareDictionaryGet(Get(s->Global("_E352_LIB"), Value("data"))); Arguments args27741; args27741.positional.reserve(2); args27741.Add(s->LocalAt(0), false); args27741.Add(List({}), false); return CallDictionaryGet(c, fn27740, std::move(args27741)); }()))) { auto unpack27742 = Iterate(item27739); ValidateUnpack(unpack27742, 2, false); comp27737->SetAt(1, unpack27742.at(0)); comp27737->SetAt(0, unpack27742.at(1)); result27738.node()->sequence.push_back(Tuple({Unary("USub", Value(int64_t{1})), ([&]() -> Value { auto comp27743 = std::make_shared<Scope>(); comp27743->globals = comp27737->globals; comp27743->parent = comp27737; static constexpr const char* comp27743_names[] = {"i", "q", "t"}; comp27743->PrepareSlots(comp27743_names); auto result27744 = Dict(); for (const auto& item27745 : Iterate(comp27737->LocalAt(0))) { auto unpack27746 = Iterate(item27745); ValidateUnpack(unpack27746, 3, false); comp27743->SetAt(2, unpack27746.at(0)); comp27743->SetAt(0, unpack27746.at(1)); comp27743->SetAt(1, unpack27746.at(2)); Put(result27744, Tuple({([&]() -> Value { auto fn27747 = comp27743->Global("int"); Arguments args27748; args27748.Add(comp27743->LocalAt(2), false); return Call(c, fn27747, std::move(args27748)); }()), ([&]() -> Value { auto fn27749 = comp27743->Global("int"); Arguments args27750; args27750.Add(comp27743->LocalAt(0), false); return Call(c, fn27749, std::move(args27750)); }())}), ([&]() -> Value { auto fn27751 = comp27743->Global("int"); Arguments args27752; args27752.Add(comp27743->LocalAt(1), false); return Call(c, fn27751, std::move(args27752)); }())); } return result27744; }())})); } return result27738; }());
Put(s->Global("_E352_LIB"), s->LocalAt(0), v27736);
auto v27753 = s->Global("_E352_REPORT");
auto v27754 = Value("e352_lib_streams");
auto v27755 = Get(v27753, v27754);
Put(v27753, v27754, Inplace("Add", v27755, ([&]() -> Value { auto fn27756 = s->Global("len"); Arguments args27757; args27757.Add(Get(s->Global("_E352_LIB"), s->LocalAt(0)), false); return Call(c, fn27756, std::move(args27757)); }())));
}
return Get(s->Global("_E352_LIB"), s->LocalAt(0));
return {};
}
}  // namespace kagg::opponents::compiled
